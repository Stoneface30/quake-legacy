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
 * this way; a shot usually needs none, but silently returning "no command"
 * for a sequence the caller DID queue would lose it. */
#define PANTHEON_CMD_RING 32
static char cg_cmds[PANTHEON_CMD_RING][BIG_INFO_STRING];
static int  cg_cmd_seq;          /* highest sequence queued */


void PANTHEON_CG_SetGameState(const gameState_t *gs)
{
    if (!gs) return;
    cg_gs = *gs;
    cg_gs_set = qtrue;
}

/*
 * Push one snapshot. `number` must increase: cgame asks for a snapshot BY
 * NUMBER and treats a gap as packet loss, so numbering that jumps around
 * makes it interpolate across holes it invents.
 */
void PANTHEON_CG_PushSnapshot(int number, const snapshot_t *snap)
{
    if (!snap) return;
    cg_ring[number % PANTHEON_SNAP_RING] = *snap;
    cg_ring_num[number % PANTHEON_SNAP_RING] = number;
    if (number > cg_latest) cg_latest = number;
    if (cg_ring_count < PANTHEON_SNAP_RING) cg_ring_count++;
}

void PANTHEON_CG_QueueServerCommand(const char *text)
{
    if (!text) return;
    cg_cmd_seq++;
    Q_strncpyz(cg_cmds[cg_cmd_seq % PANTHEON_CMD_RING], text, BIG_INFO_STRING);
}

int  PANTHEON_CG_LatestSnapshot(void) { return cg_latest; }
qboolean PANTHEON_CG_Ready(void)
{
    /* Two snapshots minimum, because cgame interpolates between a pair. */
    return cg_gs_set && cg_ring_count >= 2;
}

void PANTHEON_CG_Reset(void)
{
    memset(cg_ring_num, -1, sizeof(cg_ring_num));
    cg_ring_count = 0;
    cg_latest = 0;
    cg_cmd_seq = 0;
    cg_gs_set = qfalse;
}


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

qboolean PANTHEON_CG_GetServerCommand(int seq)
{
    if (seq <= 0 || seq > cg_cmd_seq) return qfalse;
    /* cgame reads the command through Cmd_Argv, so it has to be tokenised
     * exactly as the client would have done. */
    Cmd_TokenizeString(cg_cmds[seq % PANTHEON_CMD_RING]);
    return qtrue;
}

int PANTHEON_CG_ServerCommandSequence(void) { return cg_cmd_seq; }
