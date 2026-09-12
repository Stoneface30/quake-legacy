/*
 * WHAT PANTHEON FEEDS cgame, AND WHY IT IS NOT A DEMO PLAYER.
 *
 * WolfcamQL plays a recording. It opens a .dm_73, parses each message into
 * cl.snapshots[], and cgame reads whatever the file happened to contain. The
 * camera can only be where the recorder's client was, the entities are only
 * the ones that client was sent, and a moment the recording does not hold
 * cannot be shown.
 *
 * PANTHEON does not play anything. It FEEDS SNAPSHOTS.
 *
 * cgame's whole view of the world is snapshot_t: a serverTime, a
 * playerState_t and an array of entityState_t. That is precisely what
 * FrameTruth already produces from a PerformanceTrace, and precisely what our
 * own dm_73 parser produces from a recording. So a demo becomes ONE SOURCE of
 * snapshots rather than the only one, and the interesting sources are the
 * others:
 *
 *   - a recorded moment, replayed exactly          (parser -> snapshots)
 *   - the same moment from a camera nobody used    (FrameTruth -> snapshots)
 *   - a composed moment that no recording contains (scenario -> snapshots)
 *
 * cgame cannot tell the difference, which is the point. It draws the rockets,
 * the rail trails, the explosions and the marks for any of them.
 *
 * THE FORMAT WE NEED. Two snapshots, always: cgame interpolates between
 * `snap` and `nextSnap`, so a feeder that supplies one frame at a time
 * produces a world that stutters. The ring below holds what a caller pushed
 * and hands out the pair that brackets the requested time.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

#include <string.h>

/* Small by design. A shot is a window, not a match: the feeder is refilled as
 * the window advances, and holding a whole demo in RAM buys nothing. */
#define PANTHEON_SNAP_RING 64

static gameState_t  cg_gs;
static qboolean     cg_gs_set;

static snapshot_t   cg_ring[PANTHEON_SNAP_RING];
static int          cg_ring_num[PANTHEON_SNAP_RING];  /* snapshot number */
static int          cg_ring_count;                    /* how many pushed */
static int          cg_latest;                        /* highest number */

/* Server commands cgame polls for. Configstring changes and prints arrive
 * this way. 64, as MAX_RELIABLE_COMMANDS (clc.serverCommands): a round start
 * can carry more than 32 configstring updates between two snapshots. */
#define PANTHEON_CMD_RING MAX_RELIABLE_COMMANDS
static char cg_cmds[PANTHEON_CMD_RING][BIG_INFO_STRING];
static int  cg_cmd_num[PANTHEON_CMD_RING];   /* which seq owns each slot */
static int  cg_cmd_seq;          /* highest sequence queued */
static int  cg_cmd_executed;     /* CG_GETLASTEXECUTEDSERVERCOMMAND */
static char cg_bigcs[BIG_INFO_STRING];       /* bcs0/1/2 reassembly */


/*
 * WHAT A WHOLE-FILE PRE-SCAN KNOWS.
 *
 * Wolfcam reads a .dm_73 from end to end before it plays a frame, so cgame can
 * ask it questions about the WHOLE recording: when the game started, when it
 * ended, the first and last server time. A feed cannot answer those from the
 * snapshots it has been handed -- the future has not been pushed yet.
 *
 * So the host declares them. A parsed demo knows its own bounds; a composed
 * scenario knows the window it was built for. Left unset, every field is 0 and
 * the map name is empty, which is what cgame sees during a LIVE game and a
 * path it already handles. The one thing never done here is a guess: a
 * game-start time that is merely plausible shifts every clock cgame draws and
 * looks completely correct while doing it.
 */
typedef struct {
    int  gameStartTime, gameEndTime, firstServerTime, lastServerTime;
    char mapName[MAX_QPATH];
} pantheonDemoInfo_t;

static pantheonDemoInfo_t cg_di;

void PANTHEON_CG_SetDemoInfo(int gameStart, int gameEnd,
                             int firstServerTime, int lastServerTime,
                             const char *mapName)
{
    cg_di.gameStartTime   = gameStart;
    cg_di.gameEndTime     = gameEnd;
    cg_di.firstServerTime = firstServerTime;
    cg_di.lastServerTime  = lastServerTime;
    Q_strncpyz(cg_di.mapName, mapName ? mapName : "", sizeof(cg_di.mapName));
}

const pantheonDemoInfo_t *PANTHEON_CG_DemoInfo(void) { return &cg_di; }


static int cg_clientNum;          /* whose eyes: stated with the gamestate */

static void PANTHEON_CG_SetGameState(const gameState_t *gs)
{
    cg_gs = *gs;
    cg_gs_set = qtrue;
}

/*
 * Set one snapshot. `number` must increase: cgame asks for a snapshot BY
 * NUMBER and treats a gap as packet loss, so numbering that jumps around
 * makes it interpolate across holes it invents.
 */
void PANTHEON_CG_SetSnapshot(int number, const snapshot_t *snap)
{
    if (!snap)
        Com_Error(ERR_FATAL, "PANTHEON: snapshot %d is NULL", number);
    cg_ring[number % PANTHEON_SNAP_RING] = *snap;
    cg_ring_num[number % PANTHEON_SNAP_RING] = number;
    if (number > cg_latest) cg_latest = number;
    if (cg_ring_count < PANTHEON_SNAP_RING) cg_ring_count++;
}

/*
 * A server command at ITS OWN sequence number. A demo numbers its commands;
 * cgame asks for them by that number, so the feed stores what it was given
 * rather than counting for itself.
 */
void PANTHEON_CG_ApplyServerCommand(int seq, const char *text)
{
    if (!text || seq <= 0)
        Com_Error(ERR_FATAL, "PANTHEON: server command %d is %s", seq,
                  text ? "not a sequence number" : "NULL");
    Q_strncpyz(cg_cmds[seq % PANTHEON_CMD_RING], text, BIG_INFO_STRING);
    cg_cmd_num[seq % PANTHEON_CMD_RING] = seq;
    if (seq > cg_cmd_seq) cg_cmd_seq = seq;
}

void PANTHEON_CG_QueueServerCommand(const char *text)
{
    PANTHEON_CG_ApplyServerCommand(cg_cmd_seq + 1, text);
}

int  PANTHEON_CG_LatestSnapshot(void) { return cg_latest; }
qboolean PANTHEON_CG_Ready(void)
{
    /* Two snapshots minimum, because cgame interpolates between a pair. */
    return cg_gs_set && cg_ring_count >= 2;
}

static void PANTHEON_CG_Reset(void)
{
    memset(cg_ring_num, -1, sizeof(cg_ring_num));
    cg_ring_count = 0;
    cg_latest = 0;
    cg_cmd_seq = 0;
    memset(cg_cmd_num, 0, sizeof(cg_cmd_num));
    cg_cmd_executed = 0;
    cg_bigcs[0] = 0;
    cg_gs_set = qfalse;
    cg_clientNum = 0;
    memset(&cg_di, 0, sizeof(cg_di));
}

/*
 * A NEW GAME. Replaces Reset + SetGameState: a gamestate starts a game, so
 * every snapshot, command and demo bound fed for the previous one goes with
 * it -- otherwise a take inherits the last take's world. SetDemoInfo, if
 * used, comes after this.
 */
void PANTHEON_CG_LoadGameState(const gameState_t *gs, int clientNum)
{
    if (!gs)
        Com_Error(ERR_FATAL, "PANTHEON: LoadGameState with no gamestate");
    PANTHEON_CG_Reset();
    PANTHEON_CG_SetGameState(gs);
    cg_clientNum = clientNum;
}

int PANTHEON_CG_LoadedClientNum(void) { return cg_clientNum; }


/* ---- what the syscalls call ------------------------------------------- */

void PANTHEON_CG_GetGameState(gameState_t *out)
{
    if (!cg_gs_set)
        Com_Error(ERR_FATAL, "PANTHEON: cgame asked for the gamestate before "
                             "one was fed");
    *out = cg_gs;
}

void PANTHEON_CG_GetCurrentSnapshotNumber(int *snapshotNumber, int *serverTime)
{
    *snapshotNumber = cg_latest;
    *serverTime = cg_ring[cg_latest % PANTHEON_SNAP_RING].serverTime;
}

qboolean PANTHEON_CG_GetSnapshot(int snapshotNumber, snapshot_t *out)
{
    int slot = snapshotNumber % PANTHEON_SNAP_RING;

    /* A number we never held is NOT an error -- cgame legitimately probes
     * backwards past the ring -- but a number we hold under a DIFFERENT id is
     * a stale slot, and returning it would hand cgame someone else's world. */
    if (snapshotNumber <= 0 || snapshotNumber > cg_latest) return qfalse;
    if (cg_ring_num[slot] != snapshotNumber) return qfalse;

    *out = cg_ring[slot];
    return qtrue;
}

/* ---- configstrings: ONE implementation for both gamestates ------------- */

/*
 * CL_ConfigstringModified (cl_cgame.c:521), on any gamestate: rebuild the
 * string pool with one index replaced, including its early return when the
 * value is unchanged. The demo reader keeps its own gamestate current with
 * this, and cgame's is updated with it, so the two cannot apply a change
 * differently.
 */
void PANTHEON_GameState_Set(gameState_t *gs, int index, const char *value)
{
    gameState_t *old;
    const char  *dup;
    int          i, len;

    if (index < 0 || index >= MAX_CONFIGSTRINGS)
        Com_Error(ERR_DROP, "PANTHEON: configstring modified with bad index %i", index);
    if (!strcmp(gs->stringData + gs->stringOffsets[index], value))
        return;                                            /* unchanged */

    old = Z_Malloc(sizeof(*old));      /* ~80 KB: not on the stack */
    *old = *gs;
    memset(gs, 0, sizeof(*gs));
    gs->dataCount = 1;                 /* leave the first 0 for empty strings */
    for (i = 0; i < MAX_CONFIGSTRINGS; i++) {
        dup = (i == index) ? value : old->stringData + old->stringOffsets[i];
        if (!dup[0]) continue;
        len = strlen(dup);
        if (len + 1 + gs->dataCount > MAX_GAMESTATE_CHARS)
            Com_Error(ERR_DROP, "PANTHEON: MAX_GAMESTATE_CHARS exceeded applying cs %d", index);
        gs->stringOffsets[i] = gs->dataCount;
        memcpy(gs->stringData + gs->dataCount, dup, len + 1);
        gs->dataCount += len + 1;
    }
    Z_Free(old);
}

/*
 * The configstring half of CL_GetServerCommand (cl_cgame.c:619-663) on an
 * already tokenised command. bcs0/bcs1 are absorbed into `bigcs` (return
 * qfalse: nothing for cgame yet). bcs2 completes the string, which is then
 * RE-SCANNED as the `cs` it assembles. A `cs` updates `gs`. On return with
 * qtrue, `*rescanned` points at the string cgame must see tokenised.
 */
qboolean PANTHEON_GameState_Command(gameState_t *gs, char *bigcs, int bigcsSize,
                                    const char *text, const char **rescanned)
{
    const char *cmd = Cmd_Argv(0), *s;

    *rescanned = text;
    if (!strcmp(cmd, "bcs0")) {
        Com_sprintf(bigcs, bigcsSize, "cs %s \"%s", Cmd_Argv(1), Cmd_Argv(2));
        return qfalse;
    }
    if (!strcmp(cmd, "bcs1")) {
        s = Cmd_Argv(2);
        if ((int)(strlen(bigcs) + strlen(s)) >= bigcsSize)
            Com_Error(ERR_DROP, "PANTHEON: bcs exceeded BIG_INFO_STRING");
        strcat(bigcs, s);
        return qfalse;
    }
    if (!strcmp(cmd, "bcs2")) {
        s = Cmd_Argv(2);
        if ((int)(strlen(bigcs) + strlen(s) + 1) >= bigcsSize)
            Com_Error(ERR_DROP, "PANTHEON: bcs exceeded BIG_INFO_STRING");
        strcat(bigcs, s);
        strcat(bigcs, "\"");
        *rescanned = bigcs;
        Cmd_TokenizeString(bigcs);                      /* goto rescan */
        cmd = Cmd_Argv(0);
    }
    if (!strcmp(cmd, "cs")) {
        PANTHEON_GameState_Set(gs, atoi(Cmd_Argv(1)), Cmd_ArgsFrom(2));
        /* CL_ConfigstringModified may have re-tokenised: reparse. */
        Cmd_TokenizeString(*rescanned);
    }
    return qtrue;
}

/*
 * CL_GetServerCommand (cl_cgame.c:588), for a demo client.
 */
qboolean PANTHEON_CG_GetServerCommand(int seq)
{
    const char *text, *s, *cmd;

    /* :597 -- a command cycled out of the ring. Wolfcam prints and returns
     * qfalse while a demo plays; so do we. */
    if (seq <= cg_cmd_seq - PANTHEON_CMD_RING) {
        Com_Printf("PANTHEON: server command %d was cycled out (latest %d)\n",
                   seq, cg_cmd_seq);
        return qfalse;
    }
    /* :608 */
    if (seq > cg_cmd_seq)
        Com_Error(ERR_DROP, "PANTHEON: cgame requested server command %d, "
                            "latest received %d", seq, cg_cmd_seq);
    /* No counterpart in the client, whose ring is filled contiguously: the
     * feed is handed commands by number, so a slot it never received is a
     * host bug, never a quiet "no command". */
    if (cg_cmd_num[seq % PANTHEON_CMD_RING] != seq)
        Com_Error(ERR_DROP, "PANTHEON: server command %d was never fed", seq);

    text = cg_cmds[seq % PANTHEON_CMD_RING];
    cg_cmd_executed = seq;                                /* :614 */

    Cmd_TokenizeString(text);
    cmd = Cmd_Argv(0);
    if (!strcmp(cmd, "disconnect")) {                     /* :624 */
        if (Cmd_Argc() >= 2)
            Com_Error(ERR_SERVERDISCONNECT, "Server disconnected - %s", Cmd_Argv(1));
        Com_Error(ERR_SERVERDISCONNECT, "Server disconnected");
    }
    if (!PANTHEON_GameState_Command(&cg_gs, cg_bigcs, sizeof(cg_bigcs), text, &s))
        return qfalse;                                    /* bcs0 / bcs1 */
    cmd = Cmd_Argv(0);
    if (!strcmp(cmd, "map_restart")) {                    /* :665 */
        /* No console and no usercmds to clear; reparse as the client does. */
        Cmd_TokenizeString(s);
        return qtrue;
    }
    if (!strcmp(cmd, "clientLevelShot"))                  /* :680, no local server */
        return qfalse;
    return qtrue;
}

int PANTHEON_CG_ServerCommandSequence(void) { return cg_cmd_seq; }
int PANTHEON_CG_LastExecutedServerCommand(void) { return cg_cmd_executed; }
/* Which sequence owns the ring slot `seq` maps to -- for the ring self-test. */
int PANTHEON_CG_CommandSlotOwner(int seq) { return cg_cmd_num[seq % PANTHEON_CMD_RING]; }
/* cgame's copy of one configstring -- for the ring self-test. */
const char *PANTHEON_CG_ConfigString(int index)
{
    return cg_gs.stringData + cg_gs.stringOffsets[index];
}
