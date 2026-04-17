# Diff: `code/botlib/be_ai_weap.h`
**Canonical:** `wolfcamql-src` (sha256 `dd56fdb3e355...`, 3336 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `559fc1c25af9...`, 3342 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weap.h	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_weap.h	2026-04-16 20:02:26.901995600 +0100
@@ -95,7 +95,7 @@
 //returns the information of the current weapon
 void BotGetWeaponInfo(int weaponstate, int weapon, weaponinfo_t *weaponinfo);
 //loads the weapon weights
-int BotLoadWeaponWeights(int weaponstate, char *filename);
+int BotLoadWeaponWeights(int weaponstate, const char *filename);
 //returns a handle to a newly allocated weapon state
 int BotAllocWeaponState(void);
 //frees the weapon state

```
