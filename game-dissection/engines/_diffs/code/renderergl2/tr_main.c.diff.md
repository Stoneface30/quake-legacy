# Diff: `code/renderergl2/tr_main.c`
**Canonical:** `wolfcamql-src` (sha256 `a39e331da3ab...`, 79254 bytes)

## Variants

### `ioquake3`  — sha256 `ef6cf85a807c...`, 76686 bytes

_Diff stat: +12 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_main.c	2026-04-16 20:02:25.261257900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_main.c	2026-04-16 20:02:21.613251700 +0100
@@ -501,7 +501,7 @@
 	vec3_t	delta;
 	float	axisLength;
 
-	if (ent->e.reType != RT_MODEL  &&  ent->e.reType != RT_MODEL_FX_DIR  &&  ent->e.reType != RT_MODEL_FX_ANGLES  &&  ent->e.reType != RT_MODEL_FX_AXIS) {
+	if ( ent->e.reType != RT_MODEL ) {
 		*or = viewParms->world;
 		return;
 	}
@@ -605,47 +605,6 @@
 
 }
 
-// q3mme
-void R_RotateForWorld ( const orientationr_t* input, orientationr_t* world ) 
-{
-	float	viewerMatrix[16];
-	const float	*origin = input->origin;
-
-	Com_Memset ( world, 0, sizeof(*world));
-	world->axis[0][0] = 1;
-	world->axis[1][1] = 1;
-	world->axis[2][2] = 1;
-
-	// transform by the camera placement
-	VectorCopy( origin, world->viewOrigin );
-//	VectorCopy( origin, world->viewOrigin );
-
-	viewerMatrix[0] = input->axis[0][0];
-	viewerMatrix[4] = input->axis[0][1];
-	viewerMatrix[8] = input->axis[0][2];
-	viewerMatrix[12] = -origin[0] * viewerMatrix[0] + -origin[1] * viewerMatrix[4] + -origin[2] * viewerMatrix[8];
-
-	viewerMatrix[1] = input->axis[1][0];
-	viewerMatrix[5] = input->axis[1][1];
-	viewerMatrix[9] = input->axis[1][2];
-	viewerMatrix[13] = -origin[0] * viewerMatrix[1] + -origin[1] * viewerMatrix[5] + -origin[2] * viewerMatrix[9];
-
-	viewerMatrix[2] = input->axis[2][0];
-	viewerMatrix[6] = input->axis[2][1];
-	viewerMatrix[10] = input->axis[2][2];
-	viewerMatrix[14] = -origin[0] * viewerMatrix[2] + -origin[1] * viewerMatrix[6] + -origin[2] * viewerMatrix[10];
-
-	viewerMatrix[3] = 0;
-	viewerMatrix[7] = 0;
-	viewerMatrix[11] = 0;
-	viewerMatrix[15] = 1;
-
-	// convert from our coordinate system (looking down X)
-	// to OpenGL's coordinate system (looking down -Z)
-	myGlMultMatrix( viewerMatrix, s_flipMatrix, world->modelMatrix );
-
-}
-
 /*
 ** SetFarClip
 */
@@ -795,8 +754,6 @@
 {
 	float	xmin, xmax, ymin, ymax;
 	float	width, height, stereoSep = r_stereoSeparation->value;
-	float	dx, dy;
-	vec2_t	pixelJitter, eyeJitter;
 
 	/*
 	 * offset the view origin of the viewer for stereo rendering 
@@ -821,29 +778,7 @@
 
 	width = xmax - xmin;
 	height = ymax - ymin;
-
-	if (tr.recordingVideo  ||  mme_dofVisualize->integer) {
-		pixelJitter[0] = pixelJitter[1] = 0;
-		eyeJitter[0] = eyeJitter[1] = 0;
-
-		/* Jitter the view */
-		if (mme_dofFrames->integer > 0) {
-			if (r_anaglyphMode->integer == 19  &&  *ri.SplitVideo  &&  !tr.leftRecorded) {
-				R_MME_JitterView( pixelJitter, eyeJitter, qfalse );
-			} else {
-				R_MME_JitterView( pixelJitter, eyeJitter, qtrue );
-			}
-		}
-
-		dx = ( pixelJitter[0]*width ) / backEnd.viewParms.viewportWidth;
-		dy = ( pixelJitter[1]*height ) / backEnd.viewParms.viewportHeight;
-		dx += eyeJitter[0];
-		dy += eyeJitter[1];
-
-		xmin += dx; xmax += dx;
-		ymin += dy; ymax += dy;
-	}
-
+	
 	dest->projectionMatrix[0] = 2 * zProj / width;
 	dest->projectionMatrix[4] = 0;
 	dest->projectionMatrix[8] = (xmax + xmin + 2 * stereoSep) / width;
@@ -1169,11 +1104,7 @@
 				CrossProduct( camera->axis[0], camera->axis[1], camera->axis[2] );
 			} else {
 				// bobbing rotate, with skinNum being the rotation offset
-				if (r_portalBobbing->integer) {
-					d = sin( tr.refdef.time * 0.003f );
-				} else {
-					d = 0;
-				}
+				d = sin( tr.refdef.time * 0.003f );
 				d = e->e.skinNum + d * 4;
 				VectorCopy( camera->axis[1], transformed );
 				RotatePointAroundVector( camera->axis[1], camera->axis[0], transformed, d );
@@ -1379,7 +1310,7 @@
 		return qfalse;
 	}
 
-	if ( r_noportals->integer ) {  // || (r_fastsky->integer == 1) ) {
+	if ( r_noportals->integer || (r_fastsky->integer == 1) ) {
 		return qfalse;
 	}
 
@@ -1534,8 +1465,8 @@
 	index = tr.refdef.numDrawSurfs & DRAWSURF_MASK;
 	// the sort data is packed into a single 32 bit value so it can be
 	// compared quickly during the qsorting process
-	tr.refdef.drawSurfs[index].sort = ((uint64_t)shader->sortedIndex << QSORT_SHADERNUM_SHIFT) 
-		| (uint64_t)tr.shiftedEntityNum | ( fogIndex << QSORT_FOGNUM_SHIFT ) 
+	tr.refdef.drawSurfs[index].sort = (shader->sortedIndex << QSORT_SHADERNUM_SHIFT) 
+		| tr.shiftedEntityNum | ( fogIndex << QSORT_FOGNUM_SHIFT ) 
 		| ((int)pshadowMap << QSORT_PSHADOW_SHIFT) | (int)dlightMap;
 	tr.refdef.drawSurfs[index].cubemapIndex = cubemap;
 	tr.refdef.drawSurfs[index].surface = surface;
@@ -1547,12 +1478,11 @@
 R_DecomposeSort
 =================
 */
-void R_DecomposeSort( uint64_t sort, int *entityNum, shader_t **shader, 
+void R_DecomposeSort( unsigned sort, int *entityNum, shader_t **shader, 
 					 int *fogNum, int *dlightMap, int *pshadowMap ) {
 	*fogNum = ( sort >> QSORT_FOGNUM_SHIFT ) & 31;
 	*shader = tr.sortedShaders[ ( sort >> QSORT_SHADERNUM_SHIFT ) & (MAX_SHADERS-1) ];
-	//*entityNum = ( sort >> QSORT_REFENTITYNUM_SHIFT ) & REFENTITYNUM_MASK;
-	*entityNum = ( sort >> QSORT_REFENTITYNUM_SHIFT ) & (MAX_REFENTITIES);
+	*entityNum = ( sort >> QSORT_REFENTITYNUM_SHIFT ) & REFENTITYNUM_MASK;
 	*pshadowMap = (sort >> QSORT_PSHADOW_SHIFT ) & 1;
 	*dlightMap = sort & 1;
 }
@@ -1644,15 +1574,10 @@
 	case RT_PORTALSURFACE:
 		break;		// don't draw anything
 	case RT_SPRITE:
-	case RT_SPRITE_FIXED:
-	case RT_SPARK:
 	case RT_BEAM:
 	case RT_LIGHTNING:
 	case RT_RAIL_CORE:
 	case RT_RAIL_RINGS:
-	case RT_BEAM_Q3MME:
-	case RT_RAIL_RINGS_Q3MME:
-	case RT_GRAPPLE:
 		// self blood sprites, talk balloons, etc should not be drawn in the primary
 		// view.  We can't just do this check for all entities, because md3
 		// entities may still want to cast shadows from them
@@ -1664,9 +1589,6 @@
 		break;
 
 	case RT_MODEL:
-	case RT_MODEL_FX_DIR:
-	case RT_MODEL_FX_ANGLES:
-	case RT_MODEL_FX_AXIS:
 		// we must set up parts of tr.or for model culling
 		R_RotateForEntity( ent, &tr.viewParms, &tr.or );
 
@@ -1791,8 +1713,6 @@
 ====================
 */
 void R_DebugGraphics( void ) {
-	debugGraphicsCommand_t *cmd;
-
 	if ( tr.refdef.rdflags & RDF_NOWORLDMODEL ) {
 		return;
 	}
@@ -1800,12 +1720,11 @@
 		return;
 	}
 
-	cmd = R_GetCommandBuffer(sizeof(*cmd));
-	if (!cmd) {
-		return;
-	}
+	R_IssuePendingRenderCommands();
 
-	cmd->commandId = RC_DEBUG_GRAPHICS;
+	GL_BindToTMU(tr.whiteImage, TB_COLORMAP);
+	GL_Cull( CT_FRONT_SIDED );
+	ri.CM_DrawDebugSurface( R_DebugPolygon );
 }
 
 

```
