# Diff: `code/renderergl2/tr_flares.c`
**Canonical:** `wolfcamql-src` (sha256 `b825b5b367f6...`, 16571 bytes)

## Variants

### `ioquake3`  — sha256 `090c514a3220...`, 16537 bytes

_Diff stat: +1 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_flares.c	2026-04-16 20:02:25.259258200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_flares.c	2026-04-16 20:02:21.611253900 +0100
@@ -510,9 +510,7 @@
 	backEnd.currentEntity = &tr.worldEntity;
 	backEnd.or = backEnd.viewParms.world;
 
-	if (r_flares->integer > 1) {
-		RB_AddDlightFlares();
-	}
+//	RB_AddDlightFlares();
 
 	// perform z buffer readback on each flare in this view
 	draw = qfalse;

```
