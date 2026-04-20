# Diff: `code/renderergl2/tr_mesh.c`
**Canonical:** `wolfcamql-src` (sha256 `766f684fc1e7...`, 11105 bytes)

## Variants

### `ioquake3`  — sha256 `d191412d2515...`, 11059 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_mesh.c	2026-04-16 20:02:25.261257900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_mesh.c	2026-04-16 20:02:21.613251700 +0100
@@ -282,10 +282,10 @@
 */
 void R_AddMD3Surfaces( trRefEntity_t *ent ) {
 	int				i;
-	mdvModel_t              *model;
-	mdvSurface_t    *surface;
-	void                    *drawSurf;
-	shader_t                *shader;
+	mdvModel_t		*model;
+	mdvSurface_t	*surface;
+	void			*drawSurf;
+	shader_t		*shader;
 	int				cull;
 	int				lod;
 	int				fogNum;

```
