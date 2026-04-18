# Diff: `code/renderergl2/tr_glsl.c`
**Canonical:** `wolfcamql-src` (sha256 `a493ba418a41...`, 49638 bytes)

## Variants

### `ioquake3`  — sha256 `1288da72404f...`, 48142 bytes

_Diff stat: +21 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_glsl.c	2026-04-16 20:02:25.259258200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_glsl.c	2026-04-16 20:02:21.611253900 +0100
@@ -42,8 +42,6 @@
 extern const char *fallbackShader_lightall_fp;
 extern const char *fallbackShader_pshadow_vp;
 extern const char *fallbackShader_pshadow_fp;
-extern const char *fallbackShader_rectscreen_vp;
-extern const char *fallbackShader_rectscreen_fp;
 extern const char *fallbackShader_shadowfill_vp;
 extern const char *fallbackShader_shadowfill_fp;
 extern const char *fallbackShader_shadowmask_vp;
@@ -52,8 +50,6 @@
 extern const char *fallbackShader_ssao_fp;
 extern const char *fallbackShader_texturecolor_vp;
 extern const char *fallbackShader_texturecolor_fp;
-extern const char *fallbackShader_texturenocolor_vp;
-extern const char *fallbackShader_texturenocolor_fp;
 extern const char *fallbackShader_tonemap_vp;
 extern const char *fallbackShader_tonemap_fp;
 extern const char* fallbackShader_greyscale_vp;
@@ -165,7 +161,15 @@
 	{ "u_Greyscale", GLSL_FLOAT }
 };
 
-void GLSL_PrintLog(GLuint programOrShader, glslPrintLog_t type, qboolean developerOnly)
+typedef enum
+{
+	GLSL_PRINTLOG_PROGRAM_INFO,
+	GLSL_PRINTLOG_SHADER_INFO,
+	GLSL_PRINTLOG_SHADER_SOURCE
+}
+glslPrintLog_t;
+
+static void GLSL_PrintLog(GLuint programOrShader, glslPrintLog_t type, qboolean developerOnly)
 {
 	char           *msg;
 	static char     msgPart[1024];
@@ -255,8 +259,6 @@
 		else
 			Q_strcat(dest, size, "#version 130\n");
 
-		Q_strcat(dest, size, "#extension GL_ARB_texture_rectangle : enable\n");
-
 		// `extra' may contain #extension which must be directly after #version
 		if (extra)
 		{
@@ -281,7 +283,6 @@
 			Q_strcat(dest, size, "out vec4 out_Color;\n");
 			Q_strcat(dest, size, "#define gl_FragColor out_Color\n");
 			Q_strcat(dest, size, "#define texture2D texture\n");
-			Q_strcat(dest, size, "#define texture2DRect texture\n");
 			Q_strcat(dest, size, "#define textureCubeLod textureLod\n");
 			Q_strcat(dest, size, "#define shadow2D texture\n");
 		}
@@ -291,7 +292,6 @@
 		if (qglesMajorVersion >= 2)
 		{
 			Q_strcat(dest, size, "#version 100\n");
-			Q_strcat(dest, size, "#extension GL_ARB_texture_rectangle : enable\n");
 
 			if (extra)
 			{
@@ -309,7 +309,6 @@
 		else
 		{
 			Q_strcat(dest, size, "#version 120\n");
-			Q_strcat(dest, size, "#extension GL_ARB_texture_rectangle : enable\n");
 
 			if (extra)
 			{
@@ -970,7 +969,7 @@
 
 	R_IssuePendingRenderCommands();
 
-	startTime = ri.RealMilliseconds();
+	startTime = ri.Milliseconds();
 
 	// OpenGL ES may not have enough attributes to fit ones used for vertex animation
 	if ( glRefConfig.maxVertexAttribs > ATTR_INDEX_NORMAL2 ) {
@@ -982,7 +981,7 @@
 	}
 
 	for (i = 0; i < GENERICDEF_COUNT; i++)
-	{
+	{	
 		if ((i & GENERICDEF_USE_VERTEX_ANIMATION) && (i & GENERICDEF_USE_BONE_ANIMATION))
 			continue;
 
@@ -1052,34 +1051,6 @@
 
 	numEtcShaders++;
 
-	if (!GLSL_InitGPUShader(&tr.textureNoColorShader, "texturenocolor", attribs, qtrue, extradefines, qtrue, fallbackShader_texturenocolor_vp, fallbackShader_texturenocolor_fp))
-	{
-		ri.Error(ERR_FATAL, "Could not load texturenocolor shader!");
-	}
-	
-	GLSL_InitUniforms(&tr.textureNoColorShader);
-
-	GLSL_SetUniformInt(&tr.textureNoColorShader, UNIFORM_TEXTUREMAP, TB_DIFFUSEMAP);
-
-	GLSL_FinishGPUShader(&tr.textureNoColorShader);
-
-	numEtcShaders++;
-
-	if (!qglesMajorVersion) {
-		if (!GLSL_InitGPUShader(&tr.rectScreenShader, "rectscreen", attribs, qtrue, extradefines, qtrue, fallbackShader_rectscreen_vp, fallbackShader_rectscreen_fp))
-			{
-				ri.Error(ERR_FATAL, "Could not load rectscreen shader!");
-			}
-
-		GLSL_InitUniforms(&tr.rectScreenShader);
-
-		GLSL_SetUniformInt(&tr.rectScreenShader, UNIFORM_TEXTUREMAP, TB_DIFFUSEMAP);
-
-		GLSL_FinishGPUShader(&tr.rectScreenShader);
-
-		numEtcShaders++;
-	}
-
 	for (i = 0; i < FOGDEF_COUNT; i++)
 	{
 		if ((i & FOGDEF_USE_VERTEX_ANIMATION) && (i & FOGDEF_USE_BONE_ANIMATION))
@@ -1442,7 +1413,7 @@
 
 	// GLSL 1.10+ or GL_EXT_shadow_samplers extension are required for sampler2DShadow type
 	if (glRefConfig.glslMajorVersion > 1 || (glRefConfig.glslMajorVersion == 1 && glRefConfig.glslMinorVersion >= 10)
-		|| glRefConfig.shadowSamplers)
+	    || glRefConfig.shadowSamplers)
 	{
 		attribs = ATTR_POSITION | ATTR_TEXCOORD;
 		extradefines[0] = '\0';
@@ -1468,7 +1439,7 @@
 		{
 			ri.Error(ERR_FATAL, "Could not load shadowmask shader!");
 		}
-
+	
 		GLSL_InitUniforms(&tr.shadowmaskShader);
 
 		GLSL_SetUniformInt(&tr.shadowmaskShader, UNIFORM_SCREENDEPTHMAP, TB_COLORMAP);
@@ -1482,8 +1453,9 @@
 		numEtcShaders++;
 	}
 
+
 	if (!GLSL_InitGPUShader(&tr.greyscaleShader, "greyscale", attribs, qtrue, extradefines, qtrue,
-			fallbackShader_greyscale_vp, fallbackShader_greyscale_fp))
+		fallbackShader_greyscale_vp, fallbackShader_greyscale_fp))
 	{
 		ri.Error(ERR_FATAL, "Unable to load greyscale shader");
 	}
@@ -1494,9 +1466,9 @@
 
 	numEtcShaders++;
 
-    // GLSL 1.10+ or GL_OES_standard_derivatives extension are required for dFdx() and dFdy() GLSL functions
-     if (glRefConfig.glslMajorVersion > 1 || (glRefConfig.glslMajorVersion == 1 && glRefConfig.glslMinorVersion >= 10)
-		 || glRefConfig.standardDerivatives)
+	// GLSL 1.10+ or GL_OES_standard_derivatives extension are required for dFdx() and dFdy() GLSL functions
+	if (glRefConfig.glslMajorVersion > 1 || (glRefConfig.glslMajorVersion == 1 && glRefConfig.glslMinorVersion >= 10)
+	    || glRefConfig.standardDerivatives)
 	{
 		attribs = ATTR_POSITION | ATTR_TEXCOORD;
 		extradefines[0] = '\0';
@@ -1519,6 +1491,7 @@
 
 		numEtcShaders++;
 
+
 		for (i = 0; i < 4; i++)
 		{
 			attribs = ATTR_POSITION | ATTR_TEXCOORD;
@@ -1542,7 +1515,7 @@
 			{
 				ri.Error(ERR_FATAL, "Could not load depthBlur shader!");
 			}
-
+		
 			GLSL_InitUniforms(&tr.depthBlurShader[i]);
 
 			GLSL_SetUniformInt(&tr.depthBlurShader[i], UNIFORM_SCREENIMAGEMAP, TB_COLORMAP);
@@ -1573,7 +1546,7 @@
 #endif
 
 
-	endTime = ri.RealMilliseconds();
+	endTime = ri.Milliseconds();
 
 	ri.Printf(PRINT_ALL, "loaded %i GLSL shaders (%i gen %i light %i etc) in %5.2f seconds\n", 
 		numGenShaders + numLightShaders + numEtcShaders, numGenShaders, numLightShaders, 
@@ -1586,10 +1559,8 @@
 
 	ri.Printf(PRINT_ALL, "------- GLSL_ShutdownGPUShaders -------\n");
 
-#if 0  // wc: not valid, called after R_ShutdownVaos()  -- FIXME 2024-09-25 is this still valid?
 	for (i = 0; i < ATTR_INDEX_COUNT && i < glRefConfig.maxVertexAttribs; i++)
 		qglDisableVertexAttribArray(i);
-#endif
 
 	GL_BindNullProgram();
 
@@ -1597,8 +1568,6 @@
 		GLSL_DeleteGPUShader(&tr.genericShader[i]);
 
 	GLSL_DeleteGPUShader(&tr.textureColorShader);
-	GLSL_DeleteGPUShader(&tr.textureNoColorShader);
-	GLSL_DeleteGPUShader(&tr.rectScreenShader);
 
 	for ( i = 0; i < FOGDEF_COUNT; i++)
 		GLSL_DeleteGPUShader(&tr.fogShader[i]);

```
