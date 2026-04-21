# Diff: `code/renderergl2/tr_cmds.c`
**Canonical:** `wolfcamql-src` (sha256 `677bbbda5b6f...`, 18361 bytes)

## Variants

### `ioquake3`  — sha256 `9f32f617f17e...`, 15005 bytes

_Diff stat: +8 / -129 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_cmds.c	2026-04-16 20:02:25.257260000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_cmds.c	2026-04-16 20:02:21.609256100 +0100
@@ -87,18 +87,6 @@
 
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
 
@@ -146,20 +134,11 @@
 
 	// always leave room for the end of list command
 	if ( cmdList->used + bytes + sizeof( int ) + reservedBytes > MAX_RENDER_COMMANDS ) {
-		static int lastDroppedTime = 0;
-
 		if ( bytes > MAX_RENDER_COMMANDS - sizeof( int ) ) {
 			ri.Error( ERR_FATAL, "R_GetCommandBuffer: bad size %i", bytes );
 		}
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
 
@@ -310,11 +289,7 @@
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
@@ -357,7 +332,7 @@
 for each RE_EndFrame
 ====================
 */
-void RE_BeginFrame( stereoFrame_t stereoFrame, qboolean recordingVideo ) {
+void RE_BeginFrame( stereoFrame_t stereoFrame ) {
 	drawBufferCommand_t	*cmd = NULL;
 	colorMaskCommand_t *colcmd = NULL;
 
@@ -368,9 +343,6 @@
 
 	tr.frameCount++;
 	tr.frameSceneNum = 0;
-	tr.recordingVideo = recordingVideo;
-
-	//ri.Printf(PRINT_ALL, " ----  begin frame ---\n");
 
 	//
 	// do overdraw measurement
@@ -494,21 +466,13 @@
 						qglClear(GL_COLOR_BUFFER_BIT);
 					}
 
-					if (tr.usingFinalFrameBufferObject) {
-						FBO_Bind(tr.finalFbo);
-					} else {
-						FBO_Bind(NULL);
-					}
+					FBO_Bind(NULL);
 				}
 
-				if (!tr.usingFinalFrameBufferObject) {
-					qglDrawBuffer(GL_FRONT);
-					qglClear(GL_COLOR_BUFFER_BIT);
-					qglDrawBuffer(GL_BACK);
-					qglClear(GL_COLOR_BUFFER_BIT);
-				} else {
-					qglClear(GL_COLOR_BUFFER_BIT);
-				}
+				qglDrawBuffer(GL_FRONT);
+				qglClear(GL_COLOR_BUFFER_BIT);
+				qglDrawBuffer(GL_BACK);
+				qglClear(GL_COLOR_BUFFER_BIT);
 
 				r_anaglyphMode->modified = qfalse;
 			}
@@ -611,7 +575,6 @@
 RE_TakeVideoFrame
 =============
 */
-#if 0
 void RE_TakeVideoFrame( int width, int height,
 		byte *captureBuffer, byte *encodeBuffer, qboolean motionJpeg )
 {
@@ -634,87 +597,3 @@
 	cmd->encodeBuffer = encodeBuffer;
 	cmd->motionJpeg = motionJpeg;
 }
-#endif
-
-void RE_TakeVideoFrame (aviFileData_t *afd, int width, int height, byte *captureBuffer, byte *encodeBuffer, qboolean motionJpeg, qboolean avi, qboolean tga, qboolean jpg, qboolean png, int picCount, char *givenFileName)
-{
-	videoFrameCommand_t	*cmd;
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
-	cmd->commandId = RC_VIDEOFRAME;
-
-	cmd->width = width;
-	cmd->height = height;
-	cmd->captureBuffer = captureBuffer;
-	cmd->encodeBuffer = encodeBuffer;
-	cmd->motionJpeg = motionJpeg;
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
-}

```
