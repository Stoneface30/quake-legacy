# Diff: `code/renderergl1/tr_shade.c`
**Canonical:** `wolfcamql-src` (sha256 `a16eadcd86b6...`, 36980 bytes)

## Variants

### `ioquake3`  — sha256 `ea057f87a935...`, 32447 bytes

_Diff stat: +52 / -206 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_shade.c	2026-04-16 20:02:25.246936200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_shade.c	2026-04-16 20:02:21.601742100 +0100
@@ -21,7 +21,7 @@
 */
 // tr_shade.c
 
-#include "tr_local.h"
+#include "tr_local.h" 
 
 /*
 
@@ -176,7 +176,7 @@
 
 
 	if ( primitives == 2 ) {
-		qglDrawElements( GL_TRIANGLES,
+		qglDrawElements( GL_TRIANGLES, 
 						numIndexes,
 						GL_INDEX_TYPE,
 						indexes );
@@ -187,7 +187,7 @@
 		R_DrawStripElements( numIndexes,  indexes, qglArrayElement );
 		return;
 	}
-
+	
 	if ( primitives == 3 ) {
 		R_DrawStripElements( numIndexes,  indexes, R_ArrayElementDiscrete );
 		return;
@@ -215,7 +215,7 @@
 =================
 */
 static void R_BindAnimatedImage( textureBundle_t *bundle ) {
-	int64_t	index;
+	int64_t index;
 
 	if ( bundle->isVideoMap ) {
 		ri.CIN_RunCinematic(bundle->videoMapHandle);
@@ -223,15 +223,8 @@
 		return;
 	}
 
-	if ( bundle->isScreenMap ) {
-		GL_Bind(tr.screenMapImage);
-		return;
-	}
-
 	if ( bundle->numImageAnimations <= 1 ) {
-		if (bundle->image[0]) {
-			GL_Bind( bundle->image[0] );
-		}
+		GL_Bind( bundle->image[0] );
 		return;
 	}
 
@@ -264,27 +257,22 @@
 	GL_Bind( tr.whiteImage );
 	qglColor3f (1,1,1);
 
-	if (r_showtris->integer == 1) {
-		GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
-		GL_State(GLS_POLYMODE_LINE);
-		qglDepthRange( 0, 0 );
-	} else {
-		GL_State(GLS_POLYMODE_LINE);
-	}
+	GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
+	qglDepthRange( 0, 0 );
 
 	qglDisableClientState (GL_COLOR_ARRAY);
 	qglDisableClientState (GL_TEXTURE_COORD_ARRAY);
 
 	qglVertexPointer (3, GL_FLOAT, 16, input->xyz);	// padded for SIMD
 
-	if (qglLockArraysEXT  &&  input->numVertexes) {
+	if (qglLockArraysEXT) {
 		qglLockArraysEXT(0, input->numVertexes);
 		GLimp_LogComment( "glLockArraysEXT\n" );
 	}
 
 	R_DrawElements( input->numIndexes, input->indexes );
 
-	if (qglUnlockArraysEXT  &&  input->numVertexes) {
+	if (qglUnlockArraysEXT) {
 		qglUnlockArraysEXT();
 		GLimp_LogComment( "glUnlockArraysEXT\n" );
 	}
@@ -305,24 +293,11 @@
 
 	GL_Bind( tr.whiteImage );
 	qglColor3f (1,1,1);
-	if (r_shownormals->integer == 1) {
-		qglDepthRange( 0, 0 );	// never occluded
-		GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
-	} else {
-		GL_State(GLS_POLYMODE_LINE);
-	}
+	qglDepthRange( 0, 0 );	// never occluded
+	GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
 
 	qglBegin (GL_LINES);
 	for (i = 0 ; i < input->numVertexes ; i++) {
-		if (r_shownormals->integer == 3) {
-			if (i == 0) {
-				qglColor3f(0, 1, 0);
-			} else if (i == 1) {
-				qglColor3f(0, 1, 1);
-			} else {
-				qglColor3f(1, 1, 1);
-			}
-		}
 		qglVertex3fv (input->xyz[i]);
 		VectorMA (input->xyz[i], 2, input->normal[i], temp);
 		qglVertex3fv (temp);
@@ -332,7 +307,6 @@
 	qglDepthRange( 0, 1 );
 }
 
-
 /*
 ==============
 RB_BeginSurface
@@ -344,33 +318,7 @@
 */
 void RB_BeginSurface( shader_t *shader, int fogNum ) {
 
-	shader_t *state;
-
-	if (!shader) {
-		return;
-	}
-
-	tess.originalShader = NULL;
-
-	if (r_singleShader->integer  &&  shader->mapShader  &&  !shader->isSky) {
-		if (r_singleShader->integer == 2  ||  r_singleShader->integer == 4) {
-			tess.originalShader = shader;
-		}
-		state = tr.singleShader;
-	} else if (shader->userRemappedShader) {
-		if (shader->remappedShaderKeepLightmap) {
-			tess.originalShader = shader;  // use lightmap of original shader
-			//ri.Printf(PRINT_ALL, "keep lightmap\n");
-		} else {
-			tess.originalShader = NULL;
-		}
-		state = shader->userRemappedShader;
-	} else if (shader->gameRemappedShader) {
-		tess.originalShader = NULL;  // don't use lightmap of original shader, game remapped never use old lightmap
-		state = shader->gameRemappedShader;
-	} else {
-		state = shader;
-	}
+	shader_t *state = (shader->remappedShader) ? shader->remappedShader : shader;
 
 	tess.numIndexes = 0;
 	tess.numVertexes = 0;
@@ -381,12 +329,7 @@
 	tess.numPasses = state->numUnfoggedPasses;
 	tess.currentStageIteratorFunc = state->optimalStageIteratorFunc;
 
-	if (tess.shader->useRealTime) {
-		tess.shaderTime = backEnd.refdef.realFloatTime - tess.shader->timeOffset;
-	} else {
-		tess.shaderTime = backEnd.refdef.floatTime - tess.shader->timeOffset;
-	}
-
+	tess.shaderTime = backEnd.refdef.floatTime - tess.shader->timeOffset;
 	if (tess.shader->clampTime && tess.shaderTime >= tess.shader->clampTime) {
 		tess.shaderTime = tess.shader->clampTime;
 	}
@@ -406,91 +349,40 @@
 */
 static void DrawMultitextured( shaderCommands_t *input, int stage ) {
 	shaderStage_t	*pStage;
-	qboolean isLightmap = qfalse;
-	int i;
 
 	pStage = tess.xstages[stage];
 
-	if (pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap) {
-		isLightmap = qtrue;
-	}
-
 	GL_State( pStage->stateBits );
 
 	// this is an ugly hack to work around a GeForce driver
 	// bug with multitexture and clip planes
 	if ( backEnd.viewParms.isPortal ) {
-		//ri.Printf(PRINT_ALL, "portal geforce hack\n");
 		qglPolygonMode( GL_FRONT_AND_BACK, GL_FILL );
 	}
 
 	//
 	// base
 	//
-	GL_SelectTextureUnit( 0 );
+	GL_SelectTexture( 0 );
 	qglTexCoordPointer( 2, GL_FLOAT, 0, input->svars.texcoords[0] );
 	R_BindAnimatedImage( &pStage->bundle[0] );
 
 	//
-	// lightmap/secondary pass  //FIXME or detail textures???
+	// lightmap/secondary pass
 	//
-	GL_SelectTextureUnit( 1 );
+	GL_SelectTexture( 1 );
 	qglEnable( GL_TEXTURE_2D );
 	qglEnableClientState( GL_TEXTURE_COORD_ARRAY );
 
 	if ( r_lightmap->integer ) {
 		GL_TexEnv( GL_REPLACE );
 	} else {
-		if (0) {  //(tess.originalShader) {
-		//if (tess.originalShader) {
-			GL_TexEnv(tess.originalShader->multitextureEnv);
-		} else {
-			GL_TexEnv( tess.shader->multitextureEnv );
-		}
-		//qglTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_ADD);
+		GL_TexEnv( tess.shader->multitextureEnv );
 	}
 
 	qglTexCoordPointer( 2, GL_FLOAT, 0, input->svars.texcoords[1] );
 
-	//if (tess.originalShader  &&  tess.originalShader->lightmapIndex > LIGHTMAP_NONE) {
-	//if (tess.originalShader  &&  tess.originalShader->stages[stage]) {
-	if (tess.originalShader  &&  isLightmap) {
-		shaderStage_t *ost;
-		qboolean gotNewLightmap;
-		//ri.Printf(PRINT_ALL, "lightmap %d  stage %d\n", tess.originalShader->lightmapIndex, stage);
-		// pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap || pStage->bundle[0].vertexLightmap
-
-		// find lightmap in original shader
-		for (i = 0, gotNewLightmap = qfalse;  i < MAX_SHADER_STAGES;  i++) {
-			ost = tess.originalShader->stages[i];
-			if (!ost) {
-				break;
-			}
-			if (ost->bundle[0].isLightmap  ||  ost->bundle[1].isLightmap) {
-				gotNewLightmap = qtrue;
-				break;
-			}
-		}
-
-		if (!gotNewLightmap) {
-			//ri.Printf(PRINT_ALL, "couldn't get new lightmap\n");
-			GL_Bind(tr.whiteImage);
-		} else if (ost->bundle[0].isLightmap) {
-			R_BindAnimatedImage(&ost->bundle[0]);
-		} else if (ost->bundle[1].isLightmap) {
-			R_BindAnimatedImage(&ost->bundle[1]);
-		} else {  // vertexLightmap
-			GL_Bind(tr.whiteImage);
-		}
-
-		//R_DrawElements( input->numIndexes, input->indexes );
-	} else {
-		if (tess.originalShader) {
-			//ri.Printf(PRINT_ALL, "skipping\n");
-		}
-
-		R_BindAnimatedImage( &pStage->bundle[1] );
-	}
+	R_BindAnimatedImage( &pStage->bundle[1] );
 
 	R_DrawElements( input->numIndexes, input->indexes );
 
@@ -500,7 +392,7 @@
 	//qglDisableClientState( GL_TEXTURE_COORD_ARRAY );
 	qglDisable( GL_TEXTURE_2D );
 
-	GL_SelectTextureUnit( 0 );
+	GL_SelectTexture( 0 );
 }
 
 
@@ -512,7 +404,6 @@
 Perform dynamic lighting with another rendering pass
 ===================
 */
-
 static void ProjectDlightTexture_scalar( void ) {
 	int		i, l;
 	vec3_t	origin;
@@ -556,7 +447,7 @@
 		else if(r_greyscale->value)
 		{
 			float luminance;
-
+			
 			luminance = LUMA(dl->color[0], dl->color[1], dl->color[2]) * 255.0f;
 			floatColor[0] = LERP(dl->color[0] * 255.0f, luminance, r_greyscale->value);
 			floatColor[1] = LERP(dl->color[1] * 255.0f, luminance, r_greyscale->value);
@@ -572,7 +463,7 @@
 		for ( i = 0 ; i < tess.numVertexes ; i++, texCoords += 2, colors += 4 ) {
 			int		clip = 0;
 			vec3_t	dist;
-
+			
 			VectorSubtract( origin, tess.xyz[i], dist );
 
 			backEnd.pc.c_dlightVertexes++;
@@ -597,8 +488,8 @@
 				} else if ( texCoords[1] > 1.0f ) {
 					clip |= 8;
 				}
-				//texCoords[0] = texCoords[0];
-				//texCoords[1] = texCoords[1];
+				texCoords[0] = texCoords[0];
+				texCoords[1] = texCoords[1];
 
 				// modulate the strength based on the height and color
 				if ( dist[2] > radius ) {
@@ -608,7 +499,7 @@
 					clip |= 32;
 					modulate = 0.0f;
 				} else {
-					dist[2] = Q_fabs(dist[2]);  //FIXME why?
+					dist[2] = Q_fabs(dist[2]);
 					if ( dist[2] < radius * 0.5f ) {
 						modulate = 1.0f;
 					} else {
@@ -663,9 +554,6 @@
 		backEnd.pc.c_totalIndexes += numIndexes;
 		backEnd.pc.c_dlightIndexes += numIndexes;
 	}
-
-	// 2018-11-09 home desktop: 'Quadro FX 380 LP/PCIe/SSE2' with mme dof multipass flickers (dark fading color) if this isn't set
-	qglColor3f(1, 1, 1);
 }
 
 static void ProjectDlightTexture( void ) {
@@ -691,10 +579,6 @@
 	fog_t		*fog;
 	int			i;
 
-	if (!r_fog->integer) {
-		return;
-	}
-
 	qglEnableClientState( GL_COLOR_ARRAY );
 	qglColorPointer( 4, GL_UNSIGNED_BYTE, 0, tess.svars.colors );
 
@@ -917,17 +801,16 @@
 	if(r_greyscale->integer)
 	{
 		int scale;
-
 		for(i = 0; i < tess.numVertexes; i++)
 		{
 			scale = LUMA(tess.svars.colors[i][0], tess.svars.colors[i][1], tess.svars.colors[i][2]);
-			tess.svars.colors[i][0] = tess.svars.colors[i][1] = tess.svars.colors[i][2] = scale;
+ 			tess.svars.colors[i][0] = tess.svars.colors[i][1] = tess.svars.colors[i][2] = scale;
 		}
 	}
 	else if(r_greyscale->value)
 	{
 		float scale;
-
+		
 		for(i = 0; i < tess.numVertexes; i++)
 		{
 			scale = LUMA(tess.svars.colors[i][0], tess.svars.colors[i][1], tess.svars.colors[i][2]);
@@ -1002,7 +885,7 @@
 				break;
 
 			case TMOD_ENTITY_TRANSLATE:
-				RB_CalcScrollTexCoords( backEnd.currentEntity->ePtr->shaderTexCoord,
+				RB_CalcScrollTexCoords( backEnd.currentEntity->e.shaderTexCoord,
 									 ( float * ) tess.svars.texcoords[b] );
 				break;
 
@@ -1091,7 +974,7 @@
 			R_DrawElements( input->numIndexes, input->indexes );
 		}
 		// allow skipping out to show just lightmaps during development
-		if ( r_lightmap->integer  && ( pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap ) )
+		if ( r_lightmap->integer && ( pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap ) )
 		{
 			break;
 		}
@@ -1105,7 +988,7 @@
 void RB_StageIteratorGeneric( void )
 {
 	shaderCommands_t *input;
-	shader_t	*shader;
+	shader_t		*shader;
 
 	input = &tess;
 	shader = input->shader;
@@ -1115,7 +998,7 @@
 	//
 	// log this call
 	//
-	if ( r_logFile->integer )
+	if ( r_logFile->integer ) 
 	{
 		// don't just call LogComment, or we will get
 		// a call to va() every frame!
@@ -1128,7 +1011,7 @@
 	GL_Cull( shader->cullType );
 
 	// set polygon offset if necessary
-	if (shader->polygonOffset  &&  r_polygonFill->integer)
+	if ( shader->polygonOffset )
 	{
 		qglEnable( GL_POLYGON_OFFSET_FILL );
 		qglPolygonOffset( r_offsetFactor->value, r_offsetUnits->value );
@@ -1161,8 +1044,8 @@
 	// lock XYZ
 	//
 	qglVertexPointer (3, GL_FLOAT, 16, input->xyz);	// padded for SIMD
-
-	if (qglLockArraysEXT  &&  input->numVertexes) {
+	if (qglLockArraysEXT)
+	{
 		qglLockArraysEXT(0, input->numVertexes);
 		GLimp_LogComment( "glLockArraysEXT\n" );
 	}
@@ -1181,7 +1064,7 @@
 	//
 	RB_IterateStagesGeneric( input );
 
-	//
+	// 
 	// now do any dynamic lighting needed
 	//
 	if ( tess.dlightBits && tess.shader->sort <= SS_OPAQUE
@@ -1196,10 +1079,11 @@
 		RB_FogPass();
 	}
 
-	//
+	// 
 	// unlock arrays
 	//
-	if (qglUnlockArraysEXT  &&  input->numVertexes) {
+	if (qglUnlockArraysEXT) 
+	{
 		qglUnlockArraysEXT();
 		GLimp_LogComment( "glUnlockArraysEXT\n" );
 	}
@@ -1207,7 +1091,7 @@
 	//
 	// reset polygon offset
 	//
-	if (shader->polygonOffset  &&  r_polygonFill->integer)
+	if ( shader->polygonOffset )
 	{
 		qglDisable( GL_POLYGON_OFFSET_FILL );
 	}
@@ -1255,7 +1139,7 @@
 	qglTexCoordPointer( 2, GL_FLOAT, 16, tess.texCoords[0][0] );
 	qglVertexPointer (3, GL_FLOAT, 16, input->xyz);
 
-	if ( qglLockArraysEXT  &&  input->numVertexes)
+	if ( qglLockArraysEXT )
 	{
 		qglLockArraysEXT(0, input->numVertexes);
 		GLimp_LogComment( "glLockArraysEXT\n" );
@@ -1268,7 +1152,7 @@
 	GL_State( tess.xstages[0]->stateBits );
 	R_DrawElements( input->numIndexes, input->indexes );
 
-	//
+	// 
 	// now do any dynamic lighting needed
 	//
 	if ( tess.dlightBits && tess.shader->sort <= SS_OPAQUE ) {
@@ -1285,26 +1169,22 @@
 	// 
 	// unlock arrays
 	//
-	if (qglUnlockArraysEXT  &&  input->numVertexes) 
+	if (qglUnlockArraysEXT) 
 	{
 		qglUnlockArraysEXT();
 		GLimp_LogComment( "glUnlockArraysEXT\n" );
 	}
 }
 
-//#define REPLACE_MODE
-
-//FIXME wolfcam is this ok?  always assumes second bundle is lightmap, haven't seen used
+//define	REPLACE_MODE
 
 void RB_StageIteratorLightmappedMultitexture( void ) {
 	shaderCommands_t *input;
-	shader_t	*shader;
+	shader_t		*shader;
 
 	input = &tess;
 	shader = input->shader;
 
-	//ri.Printf(PRINT_ALL, "%s\n", __FUNCTION__);
-
 	//
 	// log this call
 	//
@@ -1337,7 +1217,7 @@
 	//
 	// select base stage
 	//
-	GL_SelectTextureUnit( 0 );
+	GL_SelectTexture( 0 );
 
 	qglEnableClientState( GL_TEXTURE_COORD_ARRAY );
 	R_BindAnimatedImage( &tess.xstages[0]->bundle[0] );
@@ -1346,54 +1226,21 @@
 	//
 	// configure second stage
 	//
-	GL_SelectTextureUnit( 1 );
+	GL_SelectTexture( 1 );
 	qglEnable( GL_TEXTURE_2D );
 	if ( r_lightmap->integer ) {
 		GL_TexEnv( GL_REPLACE );
 	} else {
 		GL_TexEnv( GL_MODULATE );
 	}
-
-	if (tess.originalShader) {
-		qboolean gotNewLightmap;
-		shaderStage_t *ost;
-		int i;
-
-		for (i = 0, gotNewLightmap = qfalse;  i < MAX_SHADER_STAGES;  i++) {
-			ost = tess.originalShader->stages[i];
-			if (!ost) {
-				break;
-			}
-			if (ost->bundle[0].isLightmap  ||  ost->bundle[1].isLightmap) {
-				gotNewLightmap = qtrue;
-				break;
-			}
-		}
-
-		if (!gotNewLightmap) {
-			//ri.Printf(PRINT_ALL, "couldn't get new lightmap\n");
-			GL_Bind(tr.whiteImage);
-		} else if (ost->bundle[0].isLightmap) {
-			R_BindAnimatedImage(&ost->bundle[0]);
-		} else if (ost->bundle[1].isLightmap) {
-			R_BindAnimatedImage(&ost->bundle[1]);
-		} else {  // vertexLightmap
-			GL_Bind(tr.whiteImage);
-		}
-
-		//R_BindAnimatedImage(&tess.originalShader->stages[0]->bundle[1]);
-		//ri.Printf(PRINT_ALL, "ick\n");
-	} else {
-		R_BindAnimatedImage( &tess.xstages[0]->bundle[1] );
-	}
-
+	R_BindAnimatedImage( &tess.xstages[0]->bundle[1] );
 	qglEnableClientState( GL_TEXTURE_COORD_ARRAY );
 	qglTexCoordPointer( 2, GL_FLOAT, 16, tess.texCoords[0][1] );
 
 	//
 	// lock arrays
 	//
-	if ( qglLockArraysEXT  &&  input->numVertexes) {
+	if ( qglLockArraysEXT ) {
 		qglLockArraysEXT(0, input->numVertexes);
 		GLimp_LogComment( "glLockArraysEXT\n" );
 	}
@@ -1406,13 +1253,13 @@
 	qglDisable( GL_TEXTURE_2D );
 	qglDisableClientState( GL_TEXTURE_COORD_ARRAY );
 
-	GL_SelectTextureUnit( 0 );
+	GL_SelectTexture( 0 );
 #ifdef REPLACE_MODE
 	GL_TexEnv( GL_MODULATE );
 	qglShadeModel( GL_SMOOTH );
 #endif
 
-	//
+	// 
 	// now do any dynamic lighting needed
 	//
 	if ( tess.dlightBits && tess.shader->sort <= SS_OPAQUE ) {
@@ -1429,7 +1276,7 @@
 	//
 	// unlock arrays
 	//
-	if ( qglUnlockArraysEXT  &&  input->numVertexes) {
+	if ( qglUnlockArraysEXT ) {
 		qglUnlockArraysEXT();
 		GLimp_LogComment( "glUnlockArraysEXT\n" );
 	}
@@ -1449,7 +1296,7 @@
 
 	if (input->indexes[SHADER_MAX_INDEXES-1] != 0) {
 		ri.Error (ERR_DROP, "RB_EndSurface() - SHADER_MAX_INDEXES hit");
-	}
+	}	
 	if (input->xyz[SHADER_MAX_VERTEXES-1][0] != 0) {
 		ri.Error (ERR_DROP, "RB_EndSurface() - SHADER_MAX_VERTEXES hit");
 	}
@@ -1477,8 +1324,6 @@
 	//
 	tess.currentStageIteratorFunc();
 
-	//RE_DrawPathLines(input);
-
 	//
 	// draw debugging stuff
 	//
@@ -1493,3 +1338,4 @@
 
 	GLimp_LogComment( "----------\n" );
 }
+

```
