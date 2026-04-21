# Diff: `code/renderergl2/tr_dsa.c`
**Canonical:** `wolfcamql-src` (sha256 `443ae3083568...`, 8873 bytes)

## Variants

### `ioquake3`  — sha256 `7fc1f1df7acd...`, 8701 bytes

_Diff stat: +0 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_dsa.c	2026-04-16 20:02:25.257260000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_dsa.c	2026-04-16 20:02:21.609256100 +0100
@@ -35,16 +35,6 @@
 }
 glDsaState;
 
-GLuint GL_CurrentDrawFramebuffer (void)
-{
-	return glDsaState.drawFramebuffer;
-}
-
-GLuint GL_CurrentReadFramebuffer (void)
-{
-	return glDsaState.readFramebuffer;
-}
-
 void GL_BindNullTextures(void)
 {
 	int i;

```
