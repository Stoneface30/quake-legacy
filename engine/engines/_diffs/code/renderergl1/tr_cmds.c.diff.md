# Diff: `code/renderergl1/tr_cmds.c`
**Canonical:** `wolfcamql-src` (sha256 `1a7604b7521b...`, 15879 bytes)

## Variants

### `ioquake3`  — sha256 `de101bfad972...`, 12840 bytes

_Diff stat: +21 / -129 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_cmds.c	2026-04-16 20:02:25.240836900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_cmds.c	2026-04-16 20:02:21.580615500 +0100
@@ -20,7 +20,6 @@
 ===========================================================================
 */
 #include "tr_local.h"
-#include "../client/cl_avi.h"
 
 /*
 =====================
@@ -81,18 +80,6 @@
 
 	cmdList = &backEndData->commands;
 	assert(cmdList);
-
-	if (cmdList->used == 0) {
-		// nothing to do
-		return;
-	}
-
-	// 2018-08-10 this function used to be R_SyncRenderThread() and it was used mostly to make sure the thread made all its opengl calls before main thread used opengl
-	if (!runPerformanceCounters) {
-		// hack to make sure render command list is complete for each frame, in tr_backend.c we separate the list betwen world and hud so we want everything in the list, this ignores R_IssuePendingRenderCommands()
-		return;
-	}
-
 	// add an end-of-list command
 	*(int *)(cmdList->cmds + cmdList->used) = RC_END_OF_LIST;
 
@@ -140,21 +127,11 @@
 
 	// always leave room for the end of list command
 	if ( cmdList->used + bytes + sizeof( int ) + reservedBytes > MAX_RENDER_COMMANDS ) {
-		static int lastDroppedTime = 0;
-
 		if ( bytes > MAX_RENDER_COMMANDS - sizeof( int ) ) {
 			ri.Error( ERR_FATAL, "R_GetCommandBuffer: bad size %i", bytes );
 		}
-
 		// if we run out of room, just start dropping commands
-		//ri.Printf( PRINT_WARNING, "Failed to allocate render command of size %d\n", bytes );
-
-		// don't spam message since it will make console unresponsive
-		if (ri.RealMilliseconds() - lastDroppedTime > 1000) {
-			ri.Printf(PRINT_ALL, "^3R_GetCommandBuffer() command dropped\n");
-			lastDroppedTime = ri.RealMilliseconds();
-		}
-
+		ri.Printf( PRINT_WARNING, "Failed to allocate render command of size %d\n", bytes );
 		return NULL;
 	}
 
@@ -260,17 +237,13 @@
 #define MODE_RED_CYAN	1
 #define MODE_RED_BLUE	2
 #define MODE_RED_GREEN	3
-#define MODE_GREEN_MAGENTA	4
+#define MODE_GREEN_MAGENTA 4
 #define MODE_MAX	MODE_GREEN_MAGENTA
 
 void R_SetColorMode(GLboolean *rgba, stereoFrame_t stereoFrame, int colormode)
 {
 	rgba[0] = rgba[1] = rgba[2] = rgba[3] = GL_TRUE;
-
-	if (colormode == 19) {
-		return;
-	}
-
+	
 	if(colormode > MODE_MAX)
 	{
 		if(stereoFrame == STEREO_LEFT)
@@ -280,7 +253,7 @@
 		
 		colormode -= MODE_MAX;
 	}
-
+	
 	if(colormode == MODE_GREEN_MAGENTA)
 	{
 		if(stereoFrame == STEREO_LEFT)
@@ -295,7 +268,7 @@
 		else if(stereoFrame == STEREO_RIGHT)
 		{
 			rgba[0] = GL_FALSE;
-
+		
 			if(colormode == MODE_RED_BLUE)
 				rgba[1] = GL_FALSE;
 			else if(colormode == MODE_RED_GREEN)
@@ -313,20 +286,17 @@
 for each RE_EndFrame
 ====================
 */
-void RE_BeginFrame (stereoFrame_t stereoFrame, qboolean recordingVideo)
-{
+void RE_BeginFrame( stereoFrame_t stereoFrame ) {
 	drawBufferCommand_t	*cmd = NULL;
 	colorMaskCommand_t *colcmd = NULL;
 
 	if ( !tr.registered ) {
 		return;
 	}
-
 	glState.finishCalled = qfalse;
 
 	tr.frameCount++;
 	tr.frameSceneNum = 0;
-	tr.recordingVideo = recordingVideo;
 
 	//
 	// do overdraw measurement
@@ -383,7 +353,6 @@
 
 		R_IssuePendingRenderCommands();
 		R_SetColorMappings();
-		R_SetLightMapColorMappings();
 	}
 
 	// check for errors
@@ -391,10 +360,7 @@
 	{
 		int	err;
 
-		if (r_ignoreGLErrors->integer == 1) {
-			R_IssuePendingRenderCommands();
-		}
-
+		R_IssuePendingRenderCommands();
 		if ((err = qglGetError()) != GL_NO_ERROR)
 			ri.Error(ERR_FATAL, "RE_BeginFrame() - glGetError() failed (0x%x)!", err);
 	}
@@ -402,9 +368,9 @@
 	if (glConfig.stereoEnabled) {
 		if( !(cmd = R_GetCommandBuffer(sizeof(*cmd))) )
 			return;
-
+			
 		cmd->commandId = RC_DRAW_BUFFER;
-
+		
 		if ( stereoFrame == STEREO_LEFT ) {
 			cmd->buffer = (int)GL_BACK_LEFT;
 		} else if ( stereoFrame == STEREO_RIGHT ) {
@@ -420,41 +386,29 @@
 			if(r_anaglyphMode->modified)
 			{
 				// clear both, front and backbuffer.
-
 				qglColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
 				qglClearColor(0.0f, 0.0f, 0.0f, 1.0f);
-
-				if (!tr.usingFinalFrameBufferObject) {
-					qglDrawBuffer(GL_FRONT);
-					qglClear(GL_COLOR_BUFFER_BIT);
-					qglDrawBuffer(GL_BACK);
-					qglClear(GL_COLOR_BUFFER_BIT);
-				} else {
-					qglClear(GL_COLOR_BUFFER_BIT);
-				}
-
-#if 0
-				if (tr.usingFinalFrameBufferObject) {
-					qglDrawBuffer(GL_COLOR_ATTACHMENT0_EXT);
-					qglReadBuffer(GL_COLOR_ATTACHMENT0_EXT);
-				}
-#endif
-
+				
+				qglDrawBuffer(GL_FRONT);
+				qglClear(GL_COLOR_BUFFER_BIT);
+				qglDrawBuffer(GL_BACK);
+				qglClear(GL_COLOR_BUFFER_BIT);
+				
 				r_anaglyphMode->modified = qfalse;
 			}
-
+			
 			if(stereoFrame == STEREO_LEFT)
 			{
 				if( !(cmd = R_GetCommandBuffer(sizeof(*cmd))) )
 					return;
-
+				
 				if( !(colcmd = R_GetCommandBuffer(sizeof(*colcmd))) )
 					return;
 			}
 			else if(stereoFrame == STEREO_RIGHT)
 			{
 				clearDepthCommand_t *cldcmd;
-
+				
 				if( !(cldcmd = R_GetCommandBuffer(sizeof(*cldcmd))) )
 					return;
 
@@ -488,14 +442,13 @@
 				r_anaglyphMode->modified = qfalse;
 			}
 
-			//ri.Printf(PRINT_ALL, "%s\n", r_drawBuffer->string);
 			if (!Q_stricmp(r_drawBuffer->string, "GL_FRONT"))
 				cmd->buffer = (int)GL_FRONT;
 			else
 				cmd->buffer = (int)GL_BACK;
 		}
 	}
-
+	
 	tr.refdef.stereoFrame = stereoFrame;
 }
 
@@ -513,7 +466,6 @@
 	if ( !tr.registered ) {
 		return;
 	}
-
 	cmd = R_GetCommandBufferReserved( sizeof( *cmd ), 0 );
 	if ( !cmd ) {
 		return;
@@ -539,7 +491,8 @@
 RE_TakeVideoFrame
 =============
 */
-void RE_TakeVideoFrame (aviFileData_t *afd, int width, int height, byte *captureBuffer, byte *encodeBuffer, qboolean motionJpeg, qboolean avi, qboolean tga, qboolean jpg, qboolean png, int picCount, char *givenFileName)
+void RE_TakeVideoFrame( int width, int height,
+		byte *captureBuffer, byte *encodeBuffer, qboolean motionJpeg )
 {
 	videoFrameCommand_t	*cmd;
 
@@ -559,65 +512,4 @@
 	cmd->captureBuffer = captureBuffer;
 	cmd->encodeBuffer = encodeBuffer;
 	cmd->motionJpeg = motionJpeg;
-	cmd->avi = avi;
-	cmd->tga = tga;
-	cmd->jpg = jpg;
-	cmd->png = png;
-	cmd->picCount = picCount;
-	Q_strncpyz(cmd->givenFileName, givenFileName, MAX_QPATH);
-}
-
-void RE_BeginHud (void)
-{
-	beginHudCommand_t *cmd;
-
-	if( !tr.registered ) {
-		return;
-	}
-
-	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
-	if( !cmd ) {
-		return;
-	}
-
-	cmd->commandId = RC_BEGIN_HUD;
-}
-
-void RE_Get_Advertisements (int *num, float *verts, char shaders[][MAX_QPATH])
-{
-	int i;
-	float *pts;
-
-	if( !tr.registered ) {
-		return;
-	}
-
-	pts = verts;
-
-	for (i = 0;  i < tr.world->numAds;  i++) {
-		pts[0 + i * 16] = tr.world->ads[i].rect[0][0];
-		pts[1 + i * 16] = tr.world->ads[i].rect[0][1];
-		pts[2 + i * 16] = tr.world->ads[i].rect[0][2];
-		pts[3 + i * 16] = tr.world->ads[i].rect[1][0];
-		pts[4 + i * 16] = tr.world->ads[i].rect[1][1];
-		pts[5 + i * 16] = tr.world->ads[i].rect[1][2];
-		pts[6 + i * 16] = tr.world->ads[i].rect[2][0];
-		pts[7 + i * 16] = tr.world->ads[i].rect[2][1];
-		pts[8 + i * 16] = tr.world->ads[i].rect[2][2];
-		pts[9 + i * 16] = tr.world->ads[i].rect[3][0];
-		pts[10 + i * 16] = tr.world->ads[i].rect[3][1];
-		pts[11 + i * 16] = tr.world->ads[i].rect[3][2];
-
-		pts[12 + i * 16] = tr.world->ads[i].normal[0];
-		pts[13 + i * 16] = tr.world->ads[i].normal[1];
-		pts[14 + i * 16] = tr.world->ads[i].normal[2];
-		//FIXME hack
-		//pts[14 + i * 16] = tr.world->adsLightmap[i];
-
-		pts[15 + i * 16] = (float)tr.world->ads[i].cellId;
-		//Q_strncpy(shaders[i], s_worldData.adShaders[i], MAX_QPATH);
-		Q_strncpyz(&(shaders[i][0]), tr.world->adShaders[i], MAX_QPATH);
-	}
-
-	*num = tr.world->numAds;
 }

```
