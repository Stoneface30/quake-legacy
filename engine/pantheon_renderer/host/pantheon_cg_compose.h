/*
 * host/pantheon_cg_compose.h -- PROOF helpers, never on the demo path.
 *
 * They compose a gamestate and snapshots by hand: the CLI proofs (--rocket,
 * --explosion, a still camera) and the FrameTruth .shot bridge. A demo carries
 * its own gamestate and snapshots, so the production path never calls these;
 * it feeds cgame through pantheon_cgame.h only. Include after pantheon_cgame.h.
 */
#ifndef PANTHEON_CG_COMPOSE_H
#define PANTHEON_CG_COMPOSE_H

void PANTHEON_CG_BuildGameState(gameState_t *gs, const char *mapname, int gametype);
void PANTHEON_CG_AddPlayerInfo(gameState_t *gs, int slot,
                               const char *model, const char *skin);
void PANTHEON_CG_ComposeSnapshot(snapshot_t *snap, int serverTime, int number,
                                 const vec3_t origin, const vec3_t angles);
void PANTHEON_CG_AddPlayer(snapshot_t *snap, int clientNum,
                           const vec3_t origin, const vec3_t angles,
                           int legsAnim, int torsoAnim, int weapon);
void PANTHEON_CG_AddRocket(snapshot_t *snap, int number, const vec3_t origin,
                           const vec3_t velocity, int trTime);
void PANTHEON_CG_AddExplosion(snapshot_t *snap, int number,
                              const vec3_t origin, const vec3_t normal);
/* Diagnostics: prints what cgame asked of the host. Nothing calls it today. */
void PANTHEON_CG_Report(void);

#endif
