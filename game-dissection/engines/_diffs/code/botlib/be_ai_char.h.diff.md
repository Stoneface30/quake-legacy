# Diff: `code/botlib/be_ai_char.h`
**Canonical:** `wolfcamql-src` (sha256 `d28bd4024045...`, 2023 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `c6b33036b5b4...`, 2029 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_char.h	2026-04-16 20:02:25.121907000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_char.h	2026-04-16 20:02:26.898996600 +0100
@@ -31,7 +31,7 @@
  *****************************************************************************/
 
 //loads a bot character from a file
-int BotLoadCharacter(char *charfile, float skill);
+int BotLoadCharacter(const char *charfile, float skill);
 //frees a bot character
 void BotFreeCharacter(int character);
 //returns a float characteristic

```
