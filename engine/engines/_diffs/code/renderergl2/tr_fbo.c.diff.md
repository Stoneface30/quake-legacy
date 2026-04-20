# Diff: `code/renderergl2/tr_fbo.c`
**Canonical:** `wolfcamql-src` (sha256 `100c2ce69d2e...`, 20989 bytes)

## Variants

### `ioquake3`  — sha256 `11aa44bd0316...`, 19620 bytes

_Diff stat: +18 / -58 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_fbo.c	2026-04-16 20:02:25.258258100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_fbo.c	2026-04-16 20:02:21.610254400 +0100
@@ -81,8 +81,6 @@
 {
 	FBO_t          *fbo;
 
-	//ri.Printf(PRINT_ALL, "FBO_Create '%s' %d %d\n", name, width, height);
-
 	if(strlen(name) >= MAX_QPATH)
 	{
 		ri.Error(ERR_DROP, "FBO_Create: \"%s\" is too long", name);
@@ -242,17 +240,6 @@
 	}
 
 	GL_BindFramebuffer(GL_FRAMEBUFFER, fbo ? fbo->frameBuffer : 0);
-
-#if 0  //FIXME testing
-	if (fbo == NULL) {
-		GL_BindFramebuffer(GL_FRAMEBUFFER, tr.renderFbo->frameBuffer);
-	} else if (fbo == (void *)-1) {
-		GL_BindFramebuffer(GL_FRAMEBUFFER, 0);
-	} else {
-		GL_BindFramebuffer(GL_FRAMEBUFFER, fbo->frameBuffer);
-	}
-#endif
-
 	glState.currentFBO = fbo;
 }
 
@@ -307,7 +294,7 @@
 		FBO_AttachImage(tr.msaaResolveFbo, tr.renderDepthImage, GL_DEPTH_ATTACHMENT, 0);
 		R_CheckFBO(tr.msaaResolveFbo);
 	}
-	else if (r_hdr->integer  ||  tr.usingFinalFrameBufferObject)
+	else if (r_hdr->integer)
 	{
 		tr.renderFbo = FBO_Create("_render", tr.renderDepthImage->width, tr.renderDepthImage->height);
 		FBO_AttachImage(tr.renderFbo, tr.renderImage, GL_COLOR_ATTACHMENT0, 0);
@@ -315,18 +302,6 @@
 		R_CheckFBO(tr.renderFbo);
 	}
 
-	if (tr.usingFinalFrameBufferObject) {
-		tr.finalFbo = FBO_Create("_final", tr.renderDepthImage->width, tr.renderDepthImage->height);
-		FBO_AttachImage(tr.finalFbo, tr.renderImage, GL_COLOR_ATTACHMENT0, 0);
-		FBO_AttachImage(tr.finalFbo, tr.renderDepthImage, GL_DEPTH_ATTACHMENT, 0);
-		R_CheckFBO(tr.finalFbo);
-
-		GL_BindFramebuffer(GL_FRAMEBUFFER, tr.finalFbo->frameBuffer);
-		qglClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );
-
-		//FIXME multi sample
-	}
-
 	// clear render buffer
 	// this fixes the corrupt screen bug with r_hdr 1 on older hardware
 	if (tr.renderFbo)
@@ -532,11 +507,6 @@
 	width  = dst ? dst->width  : glConfig.vidWidth;
 	height = dst ? dst->height : glConfig.vidHeight;
 
-	if (tr.usingFinalFrameBufferObject  &&  dst == NULL) {
-		width = glConfig.visibleWindowWidth;
-		height = glConfig.visibleWindowHeight;
-	}
-
 	if (inSrcTexCorners)
 	{
 		VectorSet2(texCoords[0], inSrcTexCorners[0], inSrcTexCorners[1]);
@@ -651,7 +621,6 @@
 {
 	ivec4_t srcBoxFinal, dstBoxFinal;
 	GLuint srcFb, dstFb;
-	GLuint oldDrawFramebuffer, oldReadFramebuffer;
 
 	if (!glRefConfig.framebufferBlit)
 	{
@@ -659,9 +628,6 @@
 		return;
 	}
 
-	oldDrawFramebuffer = GL_CurrentDrawFramebuffer();
-	oldReadFramebuffer = GL_CurrentReadFramebuffer();
-
 	srcFb = src ? src->frameBuffer : 0;
 	dstFb = dst ? dst->frameBuffer : 0;
 
@@ -670,9 +636,21 @@
 		int width =  src ? src->width  : glConfig.vidWidth;
 		int height = src ? src->height : glConfig.vidHeight;
 
+		VectorSet4(srcBoxFinal, 0, 0, width, height);
+	}
+	else
+	{
+		VectorSet4(srcBoxFinal, srcBox[0], srcBox[1], srcBox[0] + srcBox[2], srcBox[1] + srcBox[3]);
+	}
+
+	if (!dstBox)
+	{
+		int width  = dst ? dst->width  : glConfig.vidWidth;
+		int height = dst ? dst->height : glConfig.vidHeight;
+
 		qglScissor(0, 0, width, height);
 
-		VectorSet4(srcBoxFinal, 0, 0, width, height);
+		VectorSet4(dstBoxFinal, 0, 0, width, height);
 	}
 	else
 	{
@@ -681,46 +659,28 @@
 		Vector4Copy(dstBox, scissorBox);
 
 		if (scissorBox[2] < 0)
-	   	{
+		{
 			scissorBox[0] += scissorBox[2];
 			scissorBox[2] = abs(scissorBox[2]);
 		}
 
 		if (scissorBox[3] < 0)
-   		{
+		{
 			scissorBox[1] += scissorBox[3];
 			scissorBox[3] = abs(scissorBox[3]);
 		}
 
 		qglScissor(scissorBox[0], scissorBox[1], scissorBox[2], scissorBox[3]);
 
-		VectorSet4(srcBoxFinal, srcBox[0], srcBox[1], srcBox[0] + srcBox[2], srcBox[1] + srcBox[3]);
-	}
-
-	if (!dstBox)
-	{
-		int width  = dst ? dst->width  : glConfig.vidWidth;
-		int height = dst ? dst->height : glConfig.vidHeight;
-
-		if (tr.usingFinalFrameBufferObject  &&  dst == NULL) {
-			width = glConfig.visibleWindowWidth;
-			height = glConfig.visibleWindowHeight;
-		}
-
-		VectorSet4(dstBoxFinal, 0, 0, width, height);
-	}
-	else
-	{
 		VectorSet4(dstBoxFinal, dstBox[0], dstBox[1], dstBox[0] + dstBox[2], dstBox[1] + dstBox[3]);
 	}
 
 	GL_BindFramebuffer(GL_READ_FRAMEBUFFER, srcFb);
 	GL_BindFramebuffer(GL_DRAW_FRAMEBUFFER, dstFb);
-
 	qglBlitFramebuffer(srcBoxFinal[0], srcBoxFinal[1], srcBoxFinal[2], srcBoxFinal[3],
 	                      dstBoxFinal[0], dstBoxFinal[1], dstBoxFinal[2], dstBoxFinal[3],
 						  buffers, filter);
 
-	GL_BindFramebuffer(GL_READ_FRAMEBUFFER, oldReadFramebuffer);
-	GL_BindFramebuffer(GL_DRAW_FRAMEBUFFER, oldDrawFramebuffer);
+	GL_BindFramebuffer(GL_FRAMEBUFFER, 0);
+	glState.currentFBO = NULL;
 }

```
