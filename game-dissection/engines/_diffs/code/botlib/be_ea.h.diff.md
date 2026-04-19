# Diff: `code/botlib/be_ea.h`
**Canonical:** `wolfcamql-src` (sha256 `6d41c602bb53...`, 2362 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `65b756e36aa7...`, 2380 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ea.h	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ea.h	2026-04-16 20:02:26.902995100 +0100
@@ -31,9 +31,9 @@
  *****************************************************************************/
 
 //ClientCommand elementary actions
-void EA_Say(int client, char *str);
-void EA_SayTeam(int client, char *str);
-void EA_Command(int client, char *command );
+void EA_Say(int client, const char *str);
+void EA_SayTeam(int client, const char *str);
+void EA_Command(int client, const char *command );
 
 void EA_Action(int client, int action);
 void EA_Crouch(int client);

```
