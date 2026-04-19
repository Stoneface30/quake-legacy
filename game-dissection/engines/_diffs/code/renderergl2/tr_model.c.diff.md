# Diff: `code/renderergl2/tr_model.c`
**Canonical:** `wolfcamql-src` (sha256 `e2a923e2f4b7...`, 39359 bytes)

## Variants

### `ioquake3`  — sha256 `36ee6e440799...`, 39086 bytes

_Diff stat: +0 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_model.c	2026-04-16 20:02:25.262261400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_model.c	2026-04-16 20:02:21.614251500 +0100
@@ -218,19 +218,6 @@
 	return mod;
 }
 
-void R_GetModelName (qhandle_t index, char *name, int sz) {
-	model_t *mod;
-
-	// out of range gets the defualt model
-	if ( index < 1 || index >= tr.numModels ) {
-		mod = tr.models[0];
-	} else {
-		mod = tr.models[index];
-	}
-
-	Q_strncpyz(name, mod->name, sz);
-}
-
 //===============================================================================
 
 /*

```
