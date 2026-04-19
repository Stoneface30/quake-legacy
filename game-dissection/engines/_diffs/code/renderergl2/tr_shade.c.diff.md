# Diff: `code/renderergl2/tr_shade.c`
**Canonical:** `wolfcamql-src` (sha256 `8447b7ef429b...`, 54666 bytes)

## Variants

### `ioquake3`  — sha256 `9a039039e466...`, 51376 bytes

_Diff stat: +29 / -157 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_shade.c	2026-04-16 20:02:25.263259600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_shade.c	2026-04-16 20:02:21.614755200 +0100
@@ -38,7 +38,7 @@
 ==================
 */
 
-void R_DrawElements( int numIndexes, int firstIndex)
+void R_DrawElements( int numIndexes, int firstIndex )
 {
 	if (tess.useCacheVao)
 	{
@@ -78,11 +78,6 @@
 		return;
 	}
 
-	if ( bundle->isScreenMap ) {
-		GL_BindToTMU(tr.screenMapImage, tmu);
-		return;
-	}
-
 	if ( bundle->numImageAnimations <= 1 ) {
 		GL_BindToTMU( bundle->image[0], tmu);
 		return;
@@ -117,12 +112,8 @@
 static void DrawTris (shaderCommands_t *input) {
 	GL_BindToTMU( tr.whiteImage, TB_COLORMAP );
 
-	if (r_showtris->integer == 1) {
-		GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
-		qglDepthRange( 0, 0 );
-	} else {
-		GL_State(GLS_POLYMODE_LINE);
-	}
+	GL_State( GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE );
+	qglDepthRange( 0, 0 );
 
 	{
 		shaderProgram_t *sp = &tr.textureColorShader;
@@ -240,12 +231,7 @@
 	qglGetIntegerv(GL_ARRAY_BUFFER_BINDING, &prevArrayBuf);
 
 	GL_BindToTMU(tr.whiteImage, TB_COLORMAP);
-	if (r_shownormals->integer == 1) {
-		GL_State(GLS_POLYMODE_LINE | GLS_DEPTHMASK_TRUE);
-		qglDepthRange( 0, 0 );
-	} else {
-		GL_State(GLS_POLYMODE_LINE);
-	}
+	GL_State(GLS_POLYMODE_LINE);
 	GLboolean prevDepthMask;
 	qglGetBooleanv(GL_DEPTH_WRITEMASK, &prevDepthMask);
 	qglDepthMask(GL_FALSE);
@@ -289,8 +275,6 @@
 	else          qglUseProgram(0);
 
 	ri.Hunk_FreeTempMemory(lineVertices);
-
-	qglDepthRange( 0, 1 );
 }
 
 /*
@@ -304,35 +288,7 @@
 */
 void RB_BeginSurface( shader_t *shader, int fogNum, int cubemapIndex ) {
 
-	//shader_t *state = (shader->remappedShader) ? shader->remappedShader : shader;
-	shader_t *state;
-
-	if (!shader) {
-		ri.Printf(PRINT_WARNING, "RB_BeginSurface null shader\n");
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
 	tess.firstIndex = 0;
@@ -348,12 +304,7 @@
 	tess.useInternalVao = qtrue;
 	tess.useCacheVao = qfalse;
 
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
@@ -378,7 +329,6 @@
 	float currentmatrix[6];
 	float turb[2];
 	textureBundle_t *bundle = &pStage->bundle[bundleNum];
-
 	qboolean hasTurb = qfalse;
 
 	currentmatrix[0] = 1.0f; currentmatrix[2] = 0.0f; currentmatrix[4] = 0.0f;
@@ -625,49 +575,10 @@
 		|| ((blend & GLS_DSTBLEND_BITS) == GLS_DSTBLEND_ONE_MINUS_SRC_COLOR);
 
 	qboolean is2DDraw = backEnd.currentEntity == &backEnd.entity2D;
-	float overbright;
-	fog_t *fog;
-
-	if (r_opengl2_overbright->integer) {
-		//FIXME wc result > 1.0f ?
-		overbright = (isBlend || is2DDraw) ? 1.0f : (float)(1 << tr.overbrightBits);
-	} else {
-		//overbright = (isBlend || is2DDraw) ? 1.0f : 1.0f;  //((float)(1 << tr.overbrightBits) * 2.0);
-		overbright = 1.0f;
-	}
-
-	//overbright = 3.0f;
-	//overbright = 0.5f;
 
-	if (is2DDraw  &&  r_opengl2_overbright->integer == 0) {
-		if (pStage->rgbGen == CGEN_IDENTITY_LIGHTING) {
-			baseColor[0] =
-			baseColor[1] =
-			baseColor[2] = 1.0f / (float)(1 << tr.overbrightBits);
-			baseColor[3] = 1.0f;
-
-			vertColor[0] =
-			vertColor[1] =
-			vertColor[2] =
-			vertColor[3] = 0.0f;
+	float overbright = (isBlend || is2DDraw) ? 1.0f : (float)(1 << tr.overbrightBits);
 
-			return;
-		} else if (pStage->rgbGen == CGEN_VERTEX) {
-			baseColor[0] =
-			baseColor[1] =
-			baseColor[2] =
-			baseColor[3] = 0.0f;
-
-			vertColor[0] =
-			vertColor[1] =
-			vertColor[2] = 1.0f / (float)(1 << tr.overbrightBits);
-			vertColor[3] = 1.0f;
-
-			return;
-		} else {
-			//ri.Printf(PRINT_ALL, "^3handle rgbGen for 2DDraw %d\n", pStage->rgbGen);
-		}
-	}
+	fog_t *fog;
 
 	baseColor[0] = 
 	baseColor[1] =
@@ -1148,10 +1059,6 @@
 	int deformGen;
 	vec5_t deformParams;
 
-	if (!r_fog->integer) {
-		return;
-	}
-
 	ComputeDeformValues(&deformGen, deformParams);
 
 	{
@@ -1164,7 +1071,7 @@
 			index |= FOGDEF_USE_VERTEX_ANIMATION;
 		else if (glState.boneAnimation)
 			index |= FOGDEF_USE_BONE_ANIMATION;
-
+		
 		sp = &tr.fogShader[index];
 	}
 
@@ -1182,7 +1089,7 @@
 	{
 		GLSL_SetUniformMat4BoneMatrix(sp, UNIFORM_BONEMATRIX, glState.boneMatrix, glState.boneAnimation);
 	}
-
+	
 	GLSL_SetUniformInt(sp, UNIFORM_DEFORMGEN, deformGen);
 	if (deformGen != DGEN_NONE)
 	{
@@ -1249,20 +1156,14 @@
 	for ( stage = 0; stage < MAX_SHADER_STAGES; stage++ )
 	{
 		shaderStage_t *pStage = input->xstages[stage];
-		shaderStage_t *pLightStage = pStage;
 		shaderProgram_t *sp;
 		vec4_t texMatrix[8];
-		qboolean isLightmap = qfalse;
 
 		if ( !pStage )
 		{
 			break;
 		}
 
-		if (pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap) {
-			isLightmap = qtrue;
-		}
-
 		if (backEnd.depthFill)
 		{
 			if (pStage->glslShaderGroup == tr.lightallShader)
@@ -1363,7 +1264,7 @@
 		{
 			GLSL_SetUniformMat4BoneMatrix(sp, UNIFORM_BONEMATRIX, glState.boneMatrix, glState.boneAnimation);
 		}
-
+		
 		GLSL_SetUniformInt(sp, UNIFORM_DEFORMGEN, deformGen);
 		if (deformGen != DGEN_NONE)
 		{
@@ -1511,7 +1412,7 @@
 			else if ( pStage->bundle[TB_COLORMAP].image[0] != 0 )
 				R_BindAnimatedImageToTMU( &pStage->bundle[TB_COLORMAP], TB_COLORMAP );
 		}
-		else if ( pLightStage->glslShaderGroup == tr.lightallShader )
+		else if ( pStage->glslShaderGroup == tr.lightallShader )
 		{
 			int i;
 			vec4_t enableTextures;
@@ -1539,65 +1440,36 @@
 			}
 
 			VectorSet4(enableTextures, 0, 0, 0, 0);
-
-			// hereeee
-			if (tess.originalShader  &&  isLightmap) {
-				shaderStage_t *ost;
-				qboolean gotNewLightmap;
-
-				// find lightmap in original shader
-				for (i = 0, gotNewLightmap = qfalse;  i < MAX_SHADER_STAGES;  i++) {
-					ost = tess.originalShader->stages[i];
-					if (!ost) {
-						break;
-					}
-					if (ost->bundle[0].isLightmap  ||  ost->bundle[1].isLightmap) {
-						gotNewLightmap = qtrue;
-						break;
-					}
-				}
-
-				if (!gotNewLightmap) {
-					// pass
-				} else if (ost->bundle[0].isLightmap) {
-					pLightStage = ost;
-				} else if (ost->bundle[1].isLightmap) {
-					pLightStage = ost;
-				} else {
-					// pass
-				}
-			}
-
-			if ((r_lightmap->integer == 1 || r_lightmap->integer == 2) && pLightStage->bundle[TB_LIGHTMAP].image[0])
+			if ((r_lightmap->integer == 1 || r_lightmap->integer == 2) && pStage->bundle[TB_LIGHTMAP].image[0])
 			{
 				for (i = 0; i < NUM_TEXTURE_BUNDLES; i++)
 				{
 					if (i == TB_COLORMAP)
-						R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_LIGHTMAP], i);
+						R_BindAnimatedImageToTMU( &pStage->bundle[TB_LIGHTMAP], i);
 					else
 						GL_BindToTMU( tr.whiteImage, i );
 				}
 			}
-			else if (r_lightmap->integer == 3 && pLightStage->bundle[TB_DELUXEMAP].image[0])
+			else if (r_lightmap->integer == 3 && pStage->bundle[TB_DELUXEMAP].image[0])
 			{
 				for (i = 0; i < NUM_TEXTURE_BUNDLES; i++)
 				{
 					if (i == TB_COLORMAP)
-						R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_DELUXEMAP], i);
+						R_BindAnimatedImageToTMU( &pStage->bundle[TB_DELUXEMAP], i);
 					else
 						GL_BindToTMU( tr.whiteImage, i );
 				}
 			}
 			else
 			{
-				qboolean light = (pLightStage->glslShaderIndex & LIGHTDEF_LIGHTTYPE_MASK) != 0;
+				qboolean light = (pStage->glslShaderIndex & LIGHTDEF_LIGHTTYPE_MASK) != 0;
 				qboolean fastLight = !(r_normalMapping->integer || r_specularMapping->integer);
 
 				if (pStage->bundle[TB_DIFFUSEMAP].image[0])
 					R_BindAnimatedImageToTMU( &pStage->bundle[TB_DIFFUSEMAP], TB_DIFFUSEMAP);
 
-				if (pLightStage->bundle[TB_LIGHTMAP].image[0])
-					R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_LIGHTMAP], TB_LIGHTMAP);
+				if (pStage->bundle[TB_LIGHTMAP].image[0])
+					R_BindAnimatedImageToTMU( &pStage->bundle[TB_LIGHTMAP], TB_LIGHTMAP);
 
 				// bind textures that are sampled and used in the glsl shader, and
 				// bind whiteImage to textures that are sampled but zeroed in the glsl shader
@@ -1610,25 +1482,25 @@
 				//
 				if (light && !fastLight)
 				{
-					if (pLightStage->bundle[TB_NORMALMAP].image[0])
+					if (pStage->bundle[TB_NORMALMAP].image[0])
 					{
-						R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_NORMALMAP], TB_NORMALMAP);
+						R_BindAnimatedImageToTMU( &pStage->bundle[TB_NORMALMAP], TB_NORMALMAP);
 						enableTextures[0] = 1.0f;
 					}
 					else if (r_normalMapping->integer)
 						GL_BindToTMU( tr.whiteImage, TB_NORMALMAP );
 
-					if (pLightStage->bundle[TB_DELUXEMAP].image[0])
+					if (pStage->bundle[TB_DELUXEMAP].image[0])
 					{
-						R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_DELUXEMAP], TB_DELUXEMAP);
+						R_BindAnimatedImageToTMU( &pStage->bundle[TB_DELUXEMAP], TB_DELUXEMAP);
 						enableTextures[1] = 1.0f;
 					}
 					else if (r_deluxeMapping->integer)
 						GL_BindToTMU( tr.whiteImage, TB_DELUXEMAP );
 
-					if (pLightStage->bundle[TB_SPECULARMAP].image[0])
+					if (pStage->bundle[TB_SPECULARMAP].image[0])
 					{
-						R_BindAnimatedImageToTMU( &pLightStage->bundle[TB_SPECULARMAP], TB_SPECULARMAP);
+						R_BindAnimatedImageToTMU( &pStage->bundle[TB_SPECULARMAP], TB_SPECULARMAP);
 						enableTextures[2] = 1.0f;
 					}
 					else if (r_specularMapping->integer)
@@ -1640,12 +1512,12 @@
 
 			GLSL_SetUniformVec4(sp, UNIFORM_ENABLETEXTURES, enableTextures);
 		}
-		else if ( pLightStage->bundle[1].image[0] != 0 )
+		else if ( pStage->bundle[1].image[0] != 0 )
 		{
 			R_BindAnimatedImageToTMU( &pStage->bundle[0], 0 );
-			R_BindAnimatedImageToTMU( &pLightStage->bundle[1], 1 );
+			R_BindAnimatedImageToTMU( &pStage->bundle[1], 1 );
 		}
-		else
+		else 
 		{
 			//
 			// set state
@@ -1679,7 +1551,7 @@
 		R_DrawElements(input->numIndexes, input->firstIndex);
 
 		// allow skipping out to show just lightmaps during development
-		if ( r_lightmap->integer && ( pLightStage->bundle[0].isLightmap || pLightStage->bundle[1].isLightmap ) )
+		if ( r_lightmap->integer && ( pStage->bundle[0].isLightmap || pStage->bundle[1].isLightmap ) )
 		{
 			break;
 		}

```
