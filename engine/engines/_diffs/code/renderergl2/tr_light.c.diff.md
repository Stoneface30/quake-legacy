# Diff: `code/renderergl2/tr_light.c`
**Canonical:** `wolfcamql-src` (sha256 `fc9b20ad3d01...`, 13509 bytes)

## Variants

### `ioquake3`  — sha256 `e77604c98c5c...`, 13503 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_light.c	2026-04-16 20:02:25.260257400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_light.c	2026-04-16 20:02:21.612253800 +0100
@@ -444,7 +444,7 @@
 R_LightForPoint
 =================
 */
-int R_LightForPoint( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir )
+int R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir )
 {
 	trRefEntity_t ent;
 	

```
