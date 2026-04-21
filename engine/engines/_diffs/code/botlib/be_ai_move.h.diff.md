# Diff: `code/botlib/be_ai_move.h`
**Canonical:** `wolfcamql-src` (sha256 `1817a0a5ad97...`, 6186 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `2b2783d7eefb...`, 6192 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_move.h	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_move.h	2026-04-16 20:02:26.901995600 +0100
@@ -132,7 +132,7 @@
 //initialize movement state before performing any movement
 void BotInitMoveState(int handle, bot_initmove_t *initmove);
 //add a spot to avoid (if type == AVOID_CLEAR all spots are removed)
-void BotAddAvoidSpot(int movestate, vec3_t origin, float radius, int type);
+void BotAddAvoidSpot(int movestate, const vec3_t origin, float radius, int type);
 //must be called every map change
 void BotSetBrushModelTypes(void);
 //setup movement AI

```
