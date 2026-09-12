/*
 * host/pantheon_cgame.h -- the ONLY cgame surface the host uses.
 *
 * The production path (demo -> our parser -> our cgame -> our renderer -> our
 * FBO -> our frames) calls these and nothing else. Every other PANTHEON_CG_*
 * symbol is either the syscall seam's internals or a proof helper
 * (pantheon_cg_compose.h). Classification of every former call site:
 * docs/reference/2026-09-12-cgame-host-interface.md.
 *
 * Include after q_shared.h, tr_public.h and cg_public.h: the host reaches the
 * WolfcamQL tree by relative path, and the two build scripts give it different
 * include directories.
 *
 * Order of a take:
 *   BindRenderer                      once per process
 *   LoadGameState(gs, clientNum)      a new game: clears everything fed before
 *   ApplyServerCommand(seq, text)*    in sequence order
 *   SetSnapshot(n, snap) x2           cgame needs a pair to have a world
 *   SetDemoInfo(...)                  optional; after LoadGameState, which clears it
 *   Init(clientNum, messageNum, commandSequence)
 *   per frame: SetSnapshot ahead of DrawActiveFrame
 *   Shutdown                          ends the take
 */
#ifndef PANTHEON_CGAME_H
#define PANTHEON_CGAME_H

void PANTHEON_CG_BindRenderer(refexport_t *re, const glconfig_t *cfg);
void PANTHEON_CG_LoadGameState(const gameState_t *gs, int clientNum);
void PANTHEON_CG_ApplyServerCommand(int seq, const char *text);
void PANTHEON_CG_SetSnapshot(int messageNum, const snapshot_t *snap);
void PANTHEON_CG_SetDemoInfo(int gameStart, int gameEnd, int firstServerTime,
                             int lastServerTime, const char *mapName);
void PANTHEON_CG_Init(int clientNum, int serverMessageNum, int serverCommandSequence);
void PANTHEON_CG_DrawActiveFrame(int serverTime, qboolean firstFrame);
void PANTHEON_CG_Shutdown(void);

#endif
