/*
 * LOOKING INSIDE cgame.
 *
 * When cgame ran as a DLL behind a virtual machine, its state was
 * unreachable: `cg` and `cgs` lived in the VM's own address space, and the
 * only way to learn anything was to read a printf someone had left in.
 *
 * PANTHEON links cgame statically, so `cg` is simply a global in our own
 * binary. This file is compiled with cgame's headers and reports the handful
 * of fields that decide whether a frame will be the WORLD or the loading
 * screen -- which is otherwise a silent difference: cgame draws something
 * either way, and the something looks deliberate.
 *
 * This is the practical dividend of owning the tree rather than driving it
 * from outside.
 */
#include "cg_local.h"
#include "cg_weapons.h"

void PANTHEON_CG_ProbePrint(const char *when)
{
    Com_Printf("PANTHEON probe [%s]: snap=%s nextSnap=%s "
              "latestSnapshotNum=%i processedSnapshotNum=%i "
              "cg.time=%i infoScreenText=\"%s\" mapname=\"%s\" "
              "gametype=%i clientNum=%i menusLoaded=%i\n",
              when,
              cg.snap ? "SET" : "NULL",
              cg.nextSnap ? "SET" : "NULL",
              cg.latestSnapshotNum,
              cgs.processedSnapshotNum,
              cg.time,
              cg.infoScreenText,
              cgs.mapname,
              cgs.gametype,
              cg.clientNum,
              cg.menusLoaded);

    Com_Printf("PANTHEON probe [%s]: RL registered=%i missileModel=%i "
              "missileTrailFunc=%p explosionShader=%i\n",
              when, cg_weapons[WP_ROCKET_LAUNCHER].registered,
              cg_weapons[WP_ROCKET_LAUNCHER].missileModel,
              (void *)cg_weapons[WP_ROCKET_LAUNCHER].missileTrailFunc,
              cgs.media.rocketExplosionShader);

    if (cg.snap)
        Com_Printf("PANTHEON probe [%s]: snap.serverTime=%i numEntities=%i "
                  "ps.origin=%.1f %.1f %.1f snapFlags=%i\n",
                  when, cg.snap->serverTime, cg.snap->numEntities,
                  cg.snap->ps.origin[0], cg.snap->ps.origin[1],
                  cg.snap->ps.origin[2], cg.snap->snapFlags);
}

/*
 * REGISTER THE WEAPONS WHILE REGISTRATION IS STILL OPEN.
 *
 * cgame loads every weapon during CG_Init and then sets `registered = qfalse`
 * again (cg_main.c, after CG_RegisterWeapon(item->giTag)). The flag is not
 * about whether the models exist -- it drives the "full weapon bar" HUD, which
 * wants to know what the player HOLDS, not what is loaded.
 *
 * The cost lands on a renderer that draws single frames. CG_RegisterWeapon
 * wipes the weaponInfo before refilling it, so after CG_Init the rocket
 * launcher's missileModel is 0, and it is only refilled the first time a
 * rocket is actually drawn -- during the frame. In continuous playback that
 * costs one frame nobody sees. Producing ONE frame, it means the rocket is
 * invisible in the frame that was asked for, and correct in the one after,
 * which does not exist. The image comes out looking like a rocket that was
 * never in the snapshot.
 *
 * So PANTHEON registers them here, inside the registration window, and leaves
 * the flag set. What the weapon bar displays is a HUD decision, made by the
 * cg_draw* cvars; it is not allowed to decide whether a missile has a model.
 */
void PANTHEON_CG_RegisterAllWeapons(void)
{
    int i;
    for (i = 1; i < WP_NUM_WEAPONS; i++)
        CG_RegisterWeapon(i);
}
