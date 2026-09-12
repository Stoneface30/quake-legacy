/*
 * host/pantheon_demo_feed.h -- a .dm_73 read with the engine's own decoder.
 *
 * Include after q_shared.h and cg_public.h. The reader parses messages in
 * order and keeps its own gamestate current; the host takes the latest valid
 * snapshot after each message and feeds cgame through pantheon_cgame.h.
 *
 *   Open(path)
 *   while (ReadMessage())   ...   Latest(&snap) when a new one arrived
 *   QueueCommandsAfter(seq) once cgame is started for a pass
 *   Close()
 */
#ifndef PANTHEON_DEMO_FEED_H
#define PANTHEON_DEMO_FEED_H

qboolean PANTHEON_Demo_Open(const char *path);
qboolean PANTHEON_Demo_ReadMessage(void);
qboolean PANTHEON_Demo_Latest(snapshot_t *out);
void     PANTHEON_Demo_QueueCommandsAfter(int seq);
/* G1 diagnostics: a D line per parsed snapshot, valid or not (set after Open). */
void     PANTHEON_Demo_Trace(FILE *f);
int      PANTHEON_Demo_LatestParseEntities(void);   /* clSnapshot_t.parseEntitiesNum */
int      PANTHEON_Demo_EntSlot(int base, int i);    /* ring self-test */
int      PANTHEON_Demo_CommandSequence(void);
int      PANTHEON_Demo_MessageSequence(void);
int      PANTHEON_Demo_ClientNum(void);
int      PANTHEON_Demo_ChecksumFeed(void);
int      PANTHEON_Demo_GamestateCount(void);
const gameState_t *PANTHEON_Demo_GameState(void);
void     PANTHEON_Demo_Close(void);

#endif
