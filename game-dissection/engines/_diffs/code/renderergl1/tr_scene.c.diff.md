# Diff: `code/renderergl1/tr_scene.c`
**Canonical:** `wolfcamql-src` (sha256 `a3e4f6fa21af...`, 12987 bytes)

## Variants

### `ioquake3`  — sha256 `073cb0a727c9...`, 11214 bytes

_Diff stat: +20 / -73 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_scene.c	2026-04-16 20:02:25.246415300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_scene.c	2026-04-16 20:02:21.600740300 +0100
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
@@ -100,7 +97,7 @@
 
 	for ( i = 0, poly = tr.refdef.polys; i < tr.refdef.numPolys ; i++, poly++ ) {
 		sh = R_GetShaderByHandle( poly->hShader );
-		R_AddDrawSurf( ( void * )poly, sh, poly->fogIndex, poly->lightmap );
+		R_AddDrawSurf( ( void * )poly, sh, poly->fogIndex, qfalse );
 	}
 }
 
@@ -110,7 +107,7 @@
 
 =====================
 */
-void RE_AddPolyToScene( qhandle_t hShader, int numVerts, const polyVert_t *verts, int numPolys, int lightmap ) {
+void RE_AddPolyToScene( qhandle_t hShader, int numVerts, const polyVert_t *verts, int numPolys ) {
 	srfPoly_t	*poly;
 	int			i, j;
 	int			fogIndex;
@@ -122,7 +119,7 @@
 	}
 
 	if ( !hShader ) {
-		//ri.Printf( PRINT_WARNING, "WARNING: RE_AddPolyToScene: NULL poly shader\n");
+		ri.Printf( PRINT_WARNING, "WARNING: RE_AddPolyToScene: NULL poly shader\n");
 		return;
 	}
 
@@ -143,7 +140,7 @@
 		poly->hShader = hShader;
 		poly->numVerts = numVerts;
 		poly->verts = &backEndData->polyVerts[r_numpolyverts];
-
+		
 		Com_Memcpy( poly->verts, &verts[numVerts*j], numVerts * sizeof( *verts ) );
 
 		if ( glConfig.hardwareType == GLHW_RAGEPRO ) {
@@ -186,7 +183,6 @@
 			}
 		}
 		poly->fogIndex = fogIndex;
-		poly->lightmap = lightmap;
 	}
 }
 
@@ -201,23 +197,18 @@
 =====================
 */
 void RE_AddRefEntityToScene( const refEntity_t *ent ) {
-
-	//ri.Printf(PRINT_ALL, "* ^3ent: %d -> %p\n", r_numentities, ent);
-
 	if ( !tr.registered ) {
 		return;
 	}
-
 	if ( r_numentities >= MAX_REFENTITIES ) {
-		//ri.Printf(PRINT_ALL, "RE_AddRefEntityToScene() r_numentities >= MAX_REFENTITIES  %d >= %d\n", r_numentities, MAX_REFENTITIES);
+		ri.Printf(PRINT_DEVELOPER, "RE_AddRefEntityToScene: Dropping refEntity, reached MAX_REFENTITIES\n");
 		return;
 	}
-
-	if (Q_floatIsNan(ent->origin[0])  ||  Q_floatIsNan(ent->origin[1])  ||  Q_floatIsNan(ent->origin[2])) {
+	if ( Q_isnan(ent->origin[0]) || Q_isnan(ent->origin[1]) || Q_isnan(ent->origin[2]) ) {
 		static qboolean firstTime = qtrue;
 		if (firstTime) {
 			firstTime = qfalse;
-			ri.Printf(PRINT_DEVELOPER, S_COLOR_YELLOW "WARNING: RE_AddRefEntityToScene passed a refEntity which has an origin with a NaN component\n");
+			ri.Printf( PRINT_WARNING, "RE_AddRefEntityToScene passed a refEntity which has an origin with a NaN component\n");
 		}
 		return;
 	}
@@ -225,50 +216,7 @@
 		ri.Error( ERR_DROP, "RE_AddRefEntityToScene: bad reType %i", ent->reType );
 	}
 
-	//backEndData->entities[r_numentities].e = *ent;
-	backEndData->entities[r_numentities].ent = *ent;
-	//backEndData->entities[r_numentities].ePtr = ent;
-	backEndData->entities[r_numentities].ePtr = &backEndData->entities[r_numentities].ent;
-	backEndData->entities[r_numentities].lightingCalculated = qfalse;
-
-	r_numentities++;
-}
-
-void RE_AddRefEntityPtrToScene (refEntity_t *ent)
-{
-	//RE_AddRefEntityToScene(ent);
-	//return;
-
-	//ri.Printf(PRINT_ALL, "* ^3ptr: %d -> %p\n", r_numentities, ent);
-
-	if ( !tr.registered ) {
-		return;
-	}
-
-	if ( r_numentities >= MAX_REFENTITIES ) {
-		//ri.Printf(PRINT_ALL, "%s() r_numentities >= MAX_REFENTITIES  %d >= %d\n", __FUNCTION__, r_numentities, MAX_REFENTITIES);
-		return;
-	}
-
-	if (Q_floatIsNan(ent->origin[0])  ||  Q_floatIsNan(ent->origin[1])  ||  Q_floatIsNan(ent->origin[2])) {
-		static qboolean firstTime = qtrue;
-		if (firstTime) {
-			firstTime = qfalse;
-			ri.Printf(PRINT_DEVELOPER, S_COLOR_YELLOW "WARNING: %s passed a refEntity which has an origin with a NaN component\n", __FUNCTION__);
-		}
-		return;
-	}
-	if ( (int)ent->reType < 0 || ent->reType >= RT_MAX_REF_ENTITY_TYPE ) {
-		ri.Error( ERR_DROP, "%s: bad reType %i", __FUNCTION__, ent->reType );
-	}
-
-	//backEndData->entities[r_numentities].ent = *ent;
-
-	backEndData->entities[r_numentities].ePtr = ent;
-	//ri.Printf(PRINT_ALL, "%p\n", ent);
-
-	//backEndData->entities[r_numentities].ePtr = &backEndData->entities[r_numentities].ent;
-
+	backEndData->entities[r_numentities].e = *ent;
 	backEndData->entities[r_numentities].lightingCalculated = qfalse;
 
 	r_numentities++;
@@ -350,7 +298,7 @@
 		return;
 	}
 
-	startTime = ri.RealMilliseconds();
+	startTime = ri.Milliseconds();
 
 	if (!tr.world && !( fd->rdflags & RDF_NOWORLDMODEL ) ) {
 		ri.Error (ERR_DROP, "R_RenderScene: NULL worldmodel");
@@ -397,7 +345,6 @@
 	// derived info
 
 	tr.refdef.floatTime = tr.refdef.time * 0.001;
-	tr.refdef.realFloatTime = tr.refdef.realTime * 0.001;
 
 	tr.refdef.numDrawSurfs = r_firstSceneDrawSurf;
 	tr.refdef.drawSurfs = backEndData->drawSurfs;
@@ -414,7 +361,7 @@
 	// turn off dynamic lighting globally by clearing all the
 	// dlights if it needs to be disabled or if vertex lighting is enabled
 	if ( r_dynamiclight->integer == 0 ||
-		 /*r_vertexLight->integer == 1 ||*/
+		 r_vertexLight->integer == 1 ||
 		 glConfig.hardwareType == GLHW_PERMEDIA2 ) {
 		tr.refdef.num_dlights = 0;
 	}
@@ -460,5 +407,5 @@
 	r_firstSceneDlight = r_numdlights;
 	r_firstScenePoly = r_numpolys;
 
-	tr.frontEndMsec += ri.RealMilliseconds() - startTime;
+	tr.frontEndMsec += ri.Milliseconds() - startTime;
 }

```
