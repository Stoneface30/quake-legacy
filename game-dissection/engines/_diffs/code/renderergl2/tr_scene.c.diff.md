# Diff: `code/renderergl2/tr_scene.c`
**Canonical:** `wolfcamql-src` (sha256 `f0bdedb2655d...`, 16062 bytes)

## Variants

### `ioquake3`  — sha256 `45b1f5083dea...`, 15842 bytes

_Diff stat: +14 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_scene.c	2026-04-16 20:02:25.263259600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_scene.c	2026-04-16 20:02:21.614755200 +0100
@@ -36,7 +36,15 @@
 int			r_numpolyverts;
 
 
-void R_InitNextFrameNoCommands ( void ) {
+/*
+====================
+R_InitNextFrame
+
+====================
+*/
+void R_InitNextFrame( void ) {
+	backEndData->commands.used = 0;
+
 	r_firstSceneDrawSurf = 0;
 
 	r_numdlights = 0;
@@ -51,17 +59,6 @@
 	r_numpolyverts = 0;
 }
 
-/*
-====================
-R_InitNextFrame
-
-====================
-*/
-void R_InitNextFrame( void ) {
-	R_InitNextFrameNoCommands();
-	backEndData->commands.used = 0;
-}
-
 
 /*
 ====================
@@ -112,7 +109,7 @@
 
 =====================
 */
-void RE_AddPolyToScene( qhandle_t hShader, int numVerts, const polyVert_t *verts, int numPolys, int lightmap ) {
+void RE_AddPolyToScene( qhandle_t hShader, int numVerts, const polyVert_t *verts, int numPolys ) {
 	srfPoly_t	*poly;
 	int			i, j;
 	int			fogIndex;
@@ -190,8 +187,6 @@
 			}
 		}
 		poly->fogIndex = fogIndex;
-		//FIXME wc
-		//poly->lightmap = lightmap;
 	}
 }
 
@@ -215,7 +210,7 @@
 		ri.Printf(PRINT_DEVELOPER, "RE_AddRefEntityToScene: Dropping refEntity, reached MAX_REFENTITIES\n");
 		return;
 	}
-	if ( Q_floatIsNan(ent->origin[0]) || Q_floatIsNan(ent->origin[1]) || Q_floatIsNan(ent->origin[2]) ) {
+	if ( Q_isnan(ent->origin[0]) || Q_isnan(ent->origin[1]) || Q_isnan(ent->origin[2]) ) {
 		static qboolean firstTime = qtrue;
 		if (firstTime) {
 			firstTime = qfalse;
@@ -406,7 +401,6 @@
 	// derived info
 
 	tr.refdef.floatTime = tr.refdef.time * 0.001;
-	tr.refdef.realFloatTime = tr.refdef.realTime * 0.001;
 
 	tr.refdef.numDrawSurfs = r_firstSceneDrawSurf;
 	tr.refdef.drawSurfs = backEndData->drawSurfs;
@@ -426,7 +420,7 @@
 	// turn off dynamic lighting globally by clearing all the
 	// dlights if it needs to be disabled or if vertex lighting is enabled
 	if ( r_dynamiclight->integer == 0 ||
-		 /*r_vertexLight->integer == 1 ||*/
+		 r_vertexLight->integer == 1 ||
 		 glConfig.hardwareType == GLHW_PERMEDIA2 ) {
 		tr.refdef.num_dlights = 0;
 	}
@@ -474,7 +468,7 @@
 		return;
 	}
 
-	startTime = ri.RealMilliseconds();
+	startTime = ri.Milliseconds();
 
 	if (!tr.world && !( fd->rdflags & RDF_NOWORLDMODEL ) ) {
 		ri.Error (ERR_DROP, "R_RenderScene: NULL worldmodel");
@@ -575,5 +569,5 @@
 
 	RE_EndScene();
 
-	tr.frontEndMsec += ri.RealMilliseconds() - startTime;
+	tr.frontEndMsec += ri.Milliseconds() - startTime;
 }

```
