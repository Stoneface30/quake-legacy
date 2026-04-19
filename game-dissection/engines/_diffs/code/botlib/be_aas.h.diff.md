# Diff: `code/botlib/be_aas.h`
**Canonical:** `wolfcamql-src` (sha256 `af751c7a1019...`, 8284 bytes)
Also identical in: ioquake3, quake3e

## Variants

### `openarena-engine`  — sha256 `6cb8d84c89bf...`, 8282 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas.h	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas.h	2026-04-16 22:48:25.706436100 +0100
@@ -217,5 +217,5 @@
 	int endcontents;		//contents at the end of movement prediction
 	int endtravelflags;		//end travel flags
 	int numareas;			//number of areas predicted ahead
-	int time;				//time predicted ahead (in hundredths of a sec)
+	int time;				//time predicted ahead (in hundreth of a sec)
 } aas_predictroute_t;

```
