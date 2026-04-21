# Diff: `code/renderer/tr_cmds.c`
**Canonical:** `quake3e` (sha256 `228067781cbf...`, 12742 bytes)

## Variants

### `quake3-source`  — sha256 `3c5336f9bc0c...`, 11260 bytes

_Diff stat: +185 / -279 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_cmds.c	2026-04-16 20:02:27.314462000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_cmds.c	2026-04-16 20:02:19.969123300 +0100
@@ -15,18 +15,23 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 #include "tr_local.h"
 
+volatile renderCommandList_t	*renderCommandList;
+
+volatile qboolean	renderThreadActive;
+
+
 /*
 =====================
 R_PerformanceCounters
 =====================
 */
-static void R_PerformanceCounters( void ) {
+void R_PerformanceCounters( void ) {
 	if ( !r_speeds->integer ) {
 		// clear the counters even if we aren't printing
 		Com_Memset( &tr.pc, 0, sizeof( tr.pc ) );
@@ -72,66 +77,128 @@
 
 /*
 ====================
+R_InitCommandBuffers
+====================
+*/
+void R_InitCommandBuffers( void ) {
+	glConfig.smpActive = qfalse;
+	if ( r_smp->integer ) {
+		ri.Printf( PRINT_ALL, "Trying SMP acceleration...\n" );
+		if ( GLimp_SpawnRenderThread( RB_RenderThread ) ) {
+			ri.Printf( PRINT_ALL, "...succeeded.\n" );
+			glConfig.smpActive = qtrue;
+		} else {
+			ri.Printf( PRINT_ALL, "...failed.\n" );
+		}
+	}
+}
+
+/*
+====================
+R_ShutdownCommandBuffers
+====================
+*/
+void R_ShutdownCommandBuffers( void ) {
+	// kill the rendering thread
+	if ( glConfig.smpActive ) {
+		GLimp_WakeRenderer( NULL );
+		glConfig.smpActive = qfalse;
+	}
+}
+
+/*
+====================
 R_IssueRenderCommands
 ====================
 */
-static void R_IssueRenderCommands( void ) {
-	renderCommandList_t	*cmdList;
+int	c_blockedOnRender;
+int	c_blockedOnMain;
 
-	cmdList = &backEndData->commands;
+void R_IssueRenderCommands( qboolean runPerformanceCounters ) {
+	renderCommandList_t	*cmdList;
 
+	cmdList = &backEndData[tr.smpFrame]->commands;
+	assert(cmdList); // bk001205
 	// add an end-of-list command
 	*(int *)(cmdList->cmds + cmdList->used) = RC_END_OF_LIST;
 
 	// clear it out, in case this is a sync and not a buffer flip
 	cmdList->used = 0;
 
-	if ( backEnd.screenshotMask == 0 ) {
-		if ( ri.CL_IsMinimized() )
-			return; // skip backend when minimized
-		if ( backEnd.throttle )
-			return; // or throttled on demand
+	if ( glConfig.smpActive ) {
+		// if the render thread is not idle, wait for it
+		if ( renderThreadActive ) {
+			c_blockedOnRender++;
+			if ( r_showSmp->integer ) {
+				ri.Printf( PRINT_ALL, "R" );
+			}
+		} else {
+			c_blockedOnMain++;
+			if ( r_showSmp->integer ) {
+				ri.Printf( PRINT_ALL, "." );
+			}
+		}
+
+		// sleep until the renderer has completed
+		GLimp_FrontEndSleep();
+	}
+
+	// at this point, the back end thread is idle, so it is ok
+	// to look at it's performance counters
+	if ( runPerformanceCounters ) {
+		R_PerformanceCounters();
 	}
 
 	// actually start the commands going
 	if ( !r_skipBackEnd->integer ) {
 		// let it start on the new batch
-		RB_ExecuteRenderCommands( cmdList->cmds );
+		if ( !glConfig.smpActive ) {
+			RB_ExecuteRenderCommands( cmdList->cmds );
+		} else {
+			GLimp_WakeRenderer( cmdList );
+		}
 	}
 }
 
 
 /*
 ====================
-R_IssuePendingRenderCommands
+R_SyncRenderThread
 
 Issue any pending commands and wait for them to complete.
+After exiting, the render thread will have completed its work
+and will remain idle and the main thread is free to issue
+OpenGL calls until R_IssueRenderCommands is called.
 ====================
 */
-void R_IssuePendingRenderCommands( void ) {
+void R_SyncRenderThread( void ) {
 	if ( !tr.registered ) {
 		return;
 	}
-	R_IssueRenderCommands();
-}
+	R_IssueRenderCommands( qfalse );
 
+	if ( !glConfig.smpActive ) {
+		return;
+	}
+	GLimp_FrontEndSleep();
+}
 
 /*
 ============
-R_GetCommandBufferReserved
+R_GetCommandBuffer
 
-make sure there is enough command space
+make sure there is enough command space, waiting on the
+render thread if needed.
 ============
 */
-static void *R_GetCommandBufferReserved( int bytes, int reservedBytes ) {
+void *R_GetCommandBuffer( int bytes ) {
 	renderCommandList_t	*cmdList;
 
-	cmdList = &backEndData->commands;
-	bytes = PAD(bytes, sizeof(void *));
+	cmdList = &backEndData[tr.smpFrame]->commands;
 
 	// always leave room for the end of list command
-	if ( cmdList->used + bytes + sizeof( int ) + reservedBytes > MAX_RENDER_COMMANDS ) {
-		if ( bytes > MAX_RENDER_COMMANDS - sizeof( int ) ) {
+	if ( cmdList->used + bytes + 4 > MAX_RENDER_COMMANDS ) {
+		if ( bytes > MAX_RENDER_COMMANDS - 4 ) {
 			ri.Error( ERR_FATAL, "R_GetCommandBuffer: bad size %i", bytes );
 		}
 		// if we run out of room, just start dropping commands
@@ -146,21 +213,11 @@
 
 /*
 =============
-R_GetCommandBuffer
-returns NULL if there is not enough space for important commands
-=============
-*/
-static void *R_GetCommandBuffer( int bytes ) {
-	return R_GetCommandBufferReserved( bytes, PAD( sizeof( swapBuffersCommand_t ), sizeof(void *) ) );
-}
-
-
-/*
-=============
 R_AddDrawSurfCmd
+
 =============
 */
-void R_AddDrawSurfCmd( drawSurf_t *drawSurfs, int numDrawSurfs ) {
+void	R_AddDrawSurfCmd( drawSurf_t *drawSurfs, int numDrawSurfs ) {
 	drawSurfsCommand_t	*cmd;
 
 	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
@@ -184,18 +241,20 @@
 Passing NULL will set the color to white
 =============
 */
-void RE_SetColor( const float *rgba ) {
+void	RE_SetColor( const float *rgba ) {
 	setColorCommand_t	*cmd;
 
-	if ( !tr.registered ) {
-		return;
-	}
+  if ( !tr.registered ) {
+    return;
+  }
 	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
 	if ( !cmd ) {
 		return;
 	}
 	cmd->commandId = RC_SET_COLOR;
 	if ( !rgba ) {
+		static float colorWhite[4] = { 1, 1, 1, 1 };
+
 		rgba = colorWhite;
 	}
 
@@ -211,13 +270,13 @@
 RE_StretchPic
 =============
 */
-void RE_StretchPic( float x, float y, float w, float h,
-					float s1, float t1, float s2, float t2, qhandle_t hShader ) {
+void RE_StretchPic ( float x, float y, float w, float h, 
+					  float s1, float t1, float s2, float t2, qhandle_t hShader ) {
 	stretchPicCommand_t	*cmd;
 
-	if ( !tr.registered ) {
-		return;
-	}
+  if (!tr.registered) {
+    return;
+  }
 	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
 	if ( !cmd ) {
 		return;
@@ -234,49 +293,6 @@
 	cmd->t2 = t2;
 }
 
-#define MODE_RED_CYAN	1
-#define MODE_RED_BLUE	2
-#define MODE_RED_GREEN	3
-#define MODE_GREEN_MAGENTA 4
-#define MODE_MAX	MODE_GREEN_MAGENTA
-
-static void R_SetColorMode(GLboolean *rgba, stereoFrame_t stereoFrame, int colormode)
-{
-	rgba[0] = rgba[1] = rgba[2] = rgba[3] = GL_TRUE;
-
-	if(colormode > MODE_MAX)
-	{
-		if(stereoFrame == STEREO_LEFT)
-			stereoFrame = STEREO_RIGHT;
-		else if(stereoFrame == STEREO_RIGHT)
-			stereoFrame = STEREO_LEFT;
-
-		colormode -= MODE_MAX;
-	}
-
-	if(colormode == MODE_GREEN_MAGENTA)
-	{
-		if(stereoFrame == STEREO_LEFT)
-			rgba[0] = rgba[2] = GL_FALSE;
-		else if(stereoFrame == STEREO_RIGHT)
-			rgba[1] = GL_FALSE;
-	}
-	else
-	{
-		if(stereoFrame == STEREO_LEFT)
-			rgba[1] = rgba[2] = GL_FALSE;
-		else if(stereoFrame == STEREO_RIGHT)
-		{
-			rgba[0] = GL_FALSE;
-
-			if(colormode == MODE_RED_BLUE)
-				rgba[1] = GL_FALSE;
-			else if(colormode == MODE_RED_GREEN)
-				rgba[2] = GL_FALSE;
-		}
-	}
-}
-
 
 /*
 ====================
@@ -287,28 +303,90 @@
 ====================
 */
 void RE_BeginFrame( stereoFrame_t stereoFrame ) {
-	drawBufferCommand_t	*cmd = NULL;
-	colorMaskCommand_t *colcmd = NULL;
-	clearColorCommand_t *clrcmd = NULL;
+	drawBufferCommand_t	*cmd;
 
 	if ( !tr.registered ) {
 		return;
 	}
-
 	glState.finishCalled = qfalse;
 
 	tr.frameCount++;
 	tr.frameSceneNum = 0;
 
-	backEnd.doneBloom = qfalse;
+	//
+	// do overdraw measurement
+	//
+	if ( r_measureOverdraw->integer )
+	{
+		if ( glConfig.stencilBits < 4 )
+		{
+			ri.Printf( PRINT_ALL, "Warning: not enough stencil bits to measure overdraw: %d\n", glConfig.stencilBits );
+			ri.Cvar_Set( "r_measureOverdraw", "0" );
+			r_measureOverdraw->modified = qfalse;
+		}
+		else if ( r_shadows->integer == 2 )
+		{
+			ri.Printf( PRINT_ALL, "Warning: stencil shadows and overdraw measurement are mutually exclusive\n" );
+			ri.Cvar_Set( "r_measureOverdraw", "0" );
+			r_measureOverdraw->modified = qfalse;
+		}
+		else
+		{
+			R_SyncRenderThread();
+			qglEnable( GL_STENCIL_TEST );
+			qglStencilMask( ~0U );
+			qglClearStencil( 0U );
+			qglStencilFunc( GL_ALWAYS, 0U, ~0U );
+			qglStencilOp( GL_KEEP, GL_INCR, GL_INCR );
+		}
+		r_measureOverdraw->modified = qfalse;
+	}
+	else
+	{
+		// this is only reached if it was on and is now off
+		if ( r_measureOverdraw->modified ) {
+			R_SyncRenderThread();
+			qglDisable( GL_STENCIL_TEST );
+		}
+		r_measureOverdraw->modified = qfalse;
+	}
 
-	backEnd.color2D.u32 = ~0U;
+	//
+	// texturemode stuff
+	//
+	if ( r_textureMode->modified ) {
+		R_SyncRenderThread();
+		GL_TextureMode( r_textureMode->string );
+		r_textureMode->modified = qfalse;
+	}
 
-	// check for errors
-	GL_CheckErrors();
+	//
+	// gamma stuff
+	//
+	if ( r_gamma->modified ) {
+		r_gamma->modified = qfalse;
 
-	if ( ( cmd = R_GetCommandBuffer( sizeof( *cmd ) ) ) == NULL )
+		R_SyncRenderThread();
+		R_SetColorMappings();
+	}
+
+    // check for errors
+    if ( !r_ignoreGLErrors->integer ) {
+        int	err;
+
+		R_SyncRenderThread();
+        if ( ( err = qglGetError() ) != GL_NO_ERROR ) {
+            ri.Error( ERR_FATAL, "RE_BeginFrame() - glGetError() failed (0x%x)!\n", err );
+        }
+    }
+
+	//
+	// draw buffer stuff
+	//
+	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
+	if ( !cmd ) {
 		return;
+	}
 	cmd->commandId = RC_DRAW_BUFFER;
 
 	if ( glConfig.stereoEnabled ) {
@@ -319,92 +397,16 @@
 		} else {
 			ri.Error( ERR_FATAL, "RE_BeginFrame: Stereo is enabled, but stereoFrame was %i", stereoFrame );
 		}
-	}
-	else
-	{
-		if ( !Q_stricmp( r_drawBuffer->string, "GL_FRONT" ) )
+	} else {
+		if ( stereoFrame != STEREO_CENTER ) {
+			ri.Error( ERR_FATAL, "RE_BeginFrame: Stereo is disabled, but stereoFrame was %i", stereoFrame );
+		}
+		if ( !Q_stricmp( r_drawBuffer->string, "GL_FRONT" ) ) {
 			cmd->buffer = (int)GL_FRONT;
-		else
+		} else {
 			cmd->buffer = (int)GL_BACK;
-
-		if ( r_anaglyphMode->integer )
-		{
-			if ( r_anaglyphMode->modified )
-			{
-				clrcmd = R_GetCommandBuffer( sizeof( *clrcmd ) );
-				if ( clrcmd ) {
-					Com_Memset( clrcmd, 0, sizeof( *clrcmd ) );
-					clrcmd->commandId = RC_CLEARCOLOR;
-				} else {
-					return;
-				}
-				clrcmd->colorMask = qtrue;
-#ifdef USE_FBO
-				if ( !fboEnabled )
-#endif
-				{
-					// clear both, front and backbuffer.
-					clrcmd->frontAndBack = qtrue;
-				}
-			}
-
-			if ( stereoFrame == STEREO_LEFT )
-			{
-				// first frame
-			}
-			else if ( stereoFrame == STEREO_RIGHT )
-			{
-				clearDepthCommand_t *cldcmd;
-				
-				if ( (cldcmd = R_GetCommandBuffer(sizeof(*cldcmd))) == NULL )
-					return;
-
-				cldcmd->commandId = RC_CLEARDEPTH;
-			}
-			else
-				ri.Error( ERR_FATAL, "RE_BeginFrame: Stereo is enabled, but stereoFrame was %i", stereoFrame );
-
-			if ( (colcmd = R_GetCommandBuffer(sizeof(*colcmd))) == NULL )
-				return;
-
-			R_SetColorMode( colcmd->rgba, stereoFrame, r_anaglyphMode->integer );
-			colcmd->commandId = RC_COLORMASK;
-		}
-		else // !r_anaglyphMode->integer
-		{
-			if ( stereoFrame != STEREO_CENTER )
-				ri.Error( ERR_FATAL, "RE_BeginFrame: Stereo is disabled, but stereoFrame was %i", stereoFrame );
-
-			// reset color mask
-			if ( r_anaglyphMode->modified )	{
-				if ( ( colcmd = R_GetCommandBuffer( sizeof( *colcmd ) ) ) == NULL )
-					return;
-
-				R_SetColorMode( colcmd->rgba, stereoFrame, r_anaglyphMode->integer );
-				colcmd->commandId = RC_COLORMASK;
-			}
-		}
-	}
-
-	if ( r_fastsky->integer ) {
-		if ( stereoFrame != STEREO_RIGHT ) {
-			if ( !clrcmd ) {
-				clrcmd = R_GetCommandBuffer( sizeof( *clrcmd ) );
-				if ( clrcmd ) {
-					Com_Memset( clrcmd, 0, sizeof( *clrcmd ) );
-					clrcmd->commandId = RC_CLEARCOLOR;
-				} else {
-					return;
-				}
-			}
-			clrcmd->fullscreen = qtrue;
-			if ( r_anaglyphMode->integer ) {
-				clrcmd->colorMask = qtrue;
-			}
 		}
 	}
-
-	tr.refdef.stereoFrame = stereoFrame;
 }
 
 
@@ -416,24 +418,22 @@
 =============
 */
 void RE_EndFrame( int *frontEndMsec, int *backEndMsec ) {
-
-	swapBuffersCommand_t *cmd;
+	swapBuffersCommand_t	*cmd;
 
 	if ( !tr.registered ) {
 		return;
 	}
-
-	cmd = R_GetCommandBufferReserved( sizeof( *cmd ), 0 );
+	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
 	if ( !cmd ) {
 		return;
 	}
 	cmd->commandId = RC_SWAP_BUFFERS;
 
-	R_IssueRenderCommands();
-
-	R_PerformanceCounters();
+	R_IssueRenderCommands( qtrue );
 
-	R_InitNextFrame();
+	// use the other buffers next frame, because another CPU
+	// may still be rendering into the current ones
+	R_ToggleSmpFrame();
 
 	if ( frontEndMsec ) {
 		*frontEndMsec = tr.frontEndMsec;
@@ -443,99 +443,5 @@
 		*backEndMsec = backEnd.pc.msec;
 	}
 	backEnd.pc.msec = 0;
-	backEnd.throttle = qfalse;
-
-	// recompile GPU shaders if needed
-	if ( ri.Cvar_CheckGroup( CVG_RENDERER ) )
-	{
-		ARB_UpdatePrograms();
-
-#ifdef USE_FBO
-		if ( r_ext_multisample->modified || r_hdr->modified )
-			QGL_InitFBO();
-#endif
-
-		if ( r_textureMode->modified )
-			GL_TextureMode( r_textureMode->string );
-
-		if ( r_gamma->modified )
-			R_SetColorMappings();
-
-		ri.Cvar_ResetGroup( CVG_RENDERER, qtrue );
-	}
-}
-
-
-/*
-=============
-RE_TakeVideoFrame
-=============
-*/
-void RE_TakeVideoFrame( int width, int height,
-		byte *captureBuffer, byte *encodeBuffer, qboolean motionJpeg )
-{
-	videoFrameCommand_t	*cmd;
-
-	if( !tr.registered ) {
-		return;
-	}
-
-	backEnd.screenshotMask |= SCREENSHOT_AVI;
-
-	cmd = &backEnd.vcmd;
-
-	//cmd->commandId = RC_VIDEOFRAME;
-
-	cmd->width = width;
-	cmd->height = height;
-	cmd->captureBuffer = captureBuffer;
-	cmd->encodeBuffer = encodeBuffer;
-	cmd->motionJpeg = motionJpeg;
-}
-
-
-void RE_ThrottleBackend( void )
-{
-	backEnd.throttle = qtrue;
-}
-
-
-void RE_FinishBloom( void )
-{
-#ifdef USE_FBO
-	finishBloomCommand_t *cmd;
-
-	if ( !tr.registered ) {
-		return;
-	}
-
-	cmd = R_GetCommandBuffer( sizeof( *cmd ) );
-	if ( !cmd ) {
-		return;
-	}
-
-	cmd->commandId = RC_FINISHBLOOM;
-#endif // USE_FBO
-}
-
-
-qboolean RE_CanMinimize( void )
-{
-#ifdef USE_FBO
-	return fboEnabled;
-#else
-	return qfalse;
-#endif
 }
 
-
-const glconfig_t *RE_GetConfig( void )
-{
-	return &glConfig;
-}
-
-
-void RE_VertexLighting( qboolean allowed )
-{
-	tr.vertexLightingAllowed = allowed;
-}

```
