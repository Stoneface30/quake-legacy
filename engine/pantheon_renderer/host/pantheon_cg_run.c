/*
 * CALLING cgame.
 *
 * Everything before this file made cgame reachable. This one makes it run:
 * build a gamestate, push a pair of snapshots, then
 *
 *     vmMain(CG_INIT, ...)              once
 *     vmMain(CG_DRAW_ACTIVE_FRAME, ...) per frame
 *
 * WHY A PAIR OF SNAPSHOTS AND NOT ONE. cgame interpolates between `cg.snap`
 * and `cg.nextSnap`; with a single snapshot it has nothing to interpolate
 * toward and either refuses to run or freezes the world. The feeder enforces
 * this in PANTHEON_CG_Ready() rather than letting a caller discover it as a
 * still frame that never moves.
 *
 * WHY THE CONFIGSTRINGS ARE NOT OPTIONAL. CG_Init reads CS_SERVERINFO for the
 * map name and the gametype before it registers a single shader. A gamestate
 * with an empty CS_SERVERINFO does not produce a plainer picture; it produces
 * a cgame that thinks it is in no map at all.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_types.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/game/bg_public.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

#include <string.h>
#include <stdio.h>

intptr_t PANTHEON_CG_Syscall(intptr_t cmd, ...);
void     dllEntry(intptr_t (QDECL *syscallptr)(intptr_t arg, ...));

intptr_t vmMain(int command, int arg0, int arg1, int arg2, int arg3, int arg4,
                int arg5, int arg6, int arg7, int arg8, int arg9, int arg10,
                int arg11);

void     PANTHEON_CG_SetGameState(const gameState_t *gs);
void     PANTHEON_CG_PushSnapshot(int number, const snapshot_t *snap);
qboolean PANTHEON_CG_Ready(void);
void     PANTHEON_CG_Reset(void);
void     PANTHEON_CG_ProbePrint(const char *when);
void     PANTHEON_CG_RegisterAllWeapons(void);
int      PANTHEON_CG_SoundCallCount(void);

/*
 * Build a gamestate from a map name.
 *
 * gameState_t is a string pool plus offsets, exactly as the server sends it.
 * Writing it by hand is fiddly and worth doing once, here, rather than at
 * every call site.
 */
void PANTHEON_CG_BuildGameState(gameState_t *gs, const char *mapname,
                                int gametype)
{
    char info[MAX_INFO_STRING];
    int  len;

    memset(gs, 0, sizeof(*gs));
    gs->dataCount = 1;          /* index 0 is the empty string */

    info[0] = '\0';
    Info_SetValueForKey(info, "mapname", mapname);
    Info_SetValueForKey(info, "sv_hostname", "PANTHEON");
    Info_SetValueForKey(info, "g_gametype", va("%i", gametype));
    Info_SetValueForKey(info, "sv_maxclients", "16");

    len = strlen(info) + 1;
    gs->stringOffsets[CS_SERVERINFO] = gs->dataCount;
    memcpy(gs->stringData + gs->dataCount, info, len);
    gs->dataCount += len;

    /* CS_PLAYERS + slot is where a player's model, skin and team live. With
     * none of them set, cgame has a world and nobody in it: every clientinfo
     * is "not infoValid", the HUD has no local player to describe and it
     * falls back to the scoreboard. That reads as a bug in the renderer and
     * is not one -- so slot 0 is always populated, even for a shot with no
     * actors, because the CAMERA is a client too. */
    info[0] = '\0';
    Info_SetValueForKey(info, "n", "PANTHEON");
    Info_SetValueForKey(info, "t", "3");        /* TEAM_SPECTATOR */
    Info_SetValueForKey(info, "model", "sarge");
    Info_SetValueForKey(info, "hmodel", "sarge");
    Info_SetValueForKey(info, "c1", "4");
    Info_SetValueForKey(info, "c2", "5");
    Info_SetValueForKey(info, "hc", "100");
    len = strlen(info) + 1;
    gs->stringOffsets[CS_PLAYERS + 0] = gs->dataCount;
    memcpy(gs->stringData + gs->dataCount, info, len);
    gs->dataCount += len;
}

/*
 * A SNAPSHOT IS THE WHOLE PICTURE.
 *
 * This is the shape FrameTruth fills: a serverTime, a playerState_t saying
 * where the eye is, and an array of entityState_t saying what exists. Given
 * those three things cgame draws the rocket, the smoke trail, the explosion,
 * the light it throws, the scorch mark it leaves and the sound intent it
 * carries -- none of which the host has to know anything about.
 *
 * `numEntities` is the reason a world looks empty rather than broken: cgame
 * draws exactly what the snapshot holds and never complains about what it
 * does not.
 */
void PANTHEON_CG_ComposeSnapshot(snapshot_t *snap, int serverTime, int number,
                                 const vec3_t origin, const vec3_t angles)
{
    memset(snap, 0, sizeof(*snap));
    snap->serverTime = serverTime;
    snap->messageNum = number;
    snap->snapFlags  = 0;
    snap->ps.clientNum   = 0;
    snap->ps.pm_type     = PM_SPECTATOR;
    snap->ps.pm_flags    = 0;
    /* A spectator camera with zero health reads to cgame as a corpse, and a
     * corpse gets the death view and the scoreboard. */
    snap->ps.stats[STAT_HEALTH]     = 100;
    snap->ps.stats[STAT_MAX_HEALTH] = 100;
    snap->ps.persistant[PERS_TEAM]  = TEAM_SPECTATOR;
    snap->ps.weapon      = WP_NONE;
    snap->ps.weaponstate = WEAPON_READY;
    VectorCopy(origin, snap->ps.origin);
    VectorCopy(angles, snap->ps.viewangles);
    snap->numEntities = 0;
}

/* A rocket in flight. TR_LINEAR with a trTime in the past is what makes cgame
 * lay a smoke trail BEHIND it rather than draw a sphere sitting still. */
void PANTHEON_CG_AddRocket(snapshot_t *snap, int number,
                           const vec3_t origin, const vec3_t velocity,
                           int trTime)
{
    entityState_t *es;

    if (snap->numEntities >= MAX_ENTITIES_IN_SNAPSHOT) return;
    es = &snap->entities[snap->numEntities++];
    memset(es, 0, sizeof(*es));
    es->number  = number;
    es->eType   = ET_MISSILE;
    es->weapon  = WP_ROCKET_LAUNCHER;
    es->clientNum = 0;
    es->pos.trType = TR_LINEAR;
    es->pos.trTime = trTime;
    VectorCopy(origin, es->pos.trBase);
    VectorCopy(velocity, es->pos.trDelta);
    es->apos.trType = TR_STATIONARY;
    vectoangles((float *)velocity, es->apos.trBase);
}

/* An explosion. Not an entity that persists -- a TEMP EVENT, which is how
 * Quake says "this happened here, once". eventParm carries the surface normal
 * packed into a byte, which is what orients the scorch mark. */
void PANTHEON_CG_AddExplosion(snapshot_t *snap, int number,
                              const vec3_t origin, const vec3_t normal)
{
    entityState_t *es;

    if (snap->numEntities >= MAX_ENTITIES_IN_SNAPSHOT) return;
    es = &snap->entities[snap->numEntities++];
    memset(es, 0, sizeof(*es));
    es->number = number;
    es->eType  = ET_EVENTS + EV_MISSILE_MISS;
    es->weapon = WP_ROCKET_LAUNCHER;
    es->eventParm = DirToByte((float *)normal);
    es->clientNum = 0;
    es->pos.trType = TR_STATIONARY;
    VectorCopy(origin, es->pos.trBase);
    VectorCopy(origin, es->origin);
}

/*
 * Run cgame for one instant.
 *
 * `serverTime` must sit BETWEEN the two snapshots' times. cgame clamps
 * outside that range, so asking for a time past nextSnap silently gives the
 * nextSnap pose rather than the one requested -- a frame that looks right and
 * is not.
 */
/*
 * CG_Init MUST run inside the renderer's registration window.
 *
 * cgame registers every model, skin, shader and font it will ever draw during
 * CG_Init. Called after EndRegistration those handles come back 0 and the
 * frame renders with silent holes where the weapons and effects should be --
 * which is why this is a separate call the host places deliberately, rather
 * than something PANTHEON_CG_Frame does on its first invocation.
 *
 * demoPlayback is TRUE: it is what tells cgame nobody is playing, so it skips
 * prediction and input entirely. That is our situation whether the snapshots
 * came from a recording or were composed.
 */
void PANTHEON_CG_Init(void)
{
    if (!PANTHEON_CG_Ready())
        Com_Error(ERR_FATAL, "PANTHEON: CG_Init before a gamestate and two "
                             "snapshots were fed");
    /* Install the seam the way the DLL loader would. Without this cg_syscalls.c
     * still holds its initialiser, (void *)-1, and the first trap_ call jumps
     * to 0xffffffff. */
    dllEntry(PANTHEON_CG_Syscall);
    /* serverMessageNum, serverCommandSequence, clientNum, demoPlayback */
    vmMain(CG_INIT, 1, 0, 0, qtrue, 0, 0, 0, 0, 0, 0, 0, 0);
    PANTHEON_CG_RegisterAllWeapons();
    PANTHEON_CG_ProbePrint("after CG_INIT");
}

void PANTHEON_CG_Frame(int serverTime, qboolean firstFrame)
{
    if (!PANTHEON_CG_Ready())
        Com_Error(ERR_FATAL, "PANTHEON: cgame asked to draw before a "
                             "gamestate and two snapshots were fed");

    (void)firstFrame;

    /* serverTime, stereoView, demoPlayback, videoRecording, ioverf, draw */
    vmMain(CG_DRAW_ACTIVE_FRAME, serverTime, STEREO_CENTER, qtrue,
           qfalse, 0, qtrue, 0, 0, 0, 0, 0, 0);
    PANTHEON_CG_ProbePrint("after CG_DRAW_ACTIVE_FRAME");
}

void PANTHEON_CG_Report(void)
{
    int s = PANTHEON_CG_SoundCallCount();
    if (s)
        Com_Printf("PANTHEON: cgame asked for sound %i times "
                   "(no mixer is linked)\n", s);
}
