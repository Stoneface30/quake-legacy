# Diff: `code/renderercommon/qgl.h`
**Canonical:** `wolfcamql-src` (sha256 `bb1005013788...`, 21464 bytes)

## Variants

### `ioquake3`  — sha256 `1ac7ab182794...`, 18435 bytes

_Diff stat: +10 / -50 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\qgl.h	2026-04-16 20:02:25.233261900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\qgl.h	2026-04-16 20:02:21.575614600 +0100
@@ -35,43 +35,10 @@
 extern void (APIENTRYP qglActiveTextureARB) (GLenum texture);
 extern void (APIENTRYP qglClientActiveTextureARB) (GLenum texture);
 extern void (APIENTRYP qglMultiTexCoord2fARB) (GLenum target, GLfloat s, GLfloat t);
-extern void (APIENTRYP qglMultiTexCoord2iARB) (GLenum target, GLint s, GLint t);
 
 extern void (APIENTRYP qglLockArraysEXT) (GLint first, GLsizei count);
 extern void (APIENTRYP qglUnlockArraysEXT) (void);
 
-// glsl
-extern GLhandleARB (APIENTRYP qglCreateShaderObjectARB) (GLenum shaderType);
-extern void (APIENTRYP qglShaderSourceARB) (GLhandleARB shader, int numOfStrings, const char **strings, int *lenOfStrings);
-extern void (APIENTRYP qglCompileShaderARB) (GLhandleARB shader);
-extern GLhandleARB (APIENTRYP qglCreateProgramObjectARB) (void);
-extern void (APIENTRYP qglAttachObjectARB) (GLhandleARB program, GLhandleARB shader);
-extern void (APIENTRYP qglLinkProgramARB) (GLhandleARB program);
-extern void (APIENTRYP qglUseProgramObjectARB) (GLhandleARB prog);
-extern void (APIENTRYP qglGetObjectParameterivARB) (GLhandleARB object, GLenum type, int *param);
-extern void (APIENTRYP qglGetInfoLogARB) (GLhandleARB object, int maxLen, int *len, char *log);
-
-extern void (APIENTRYP qglDetachObjectARB) (GLhandleARB program, GLhandleARB shader);
-extern void (APIENTRYP qglDeleteObjectARB) (GLhandleARB id);
-
-extern GLint (APIENTRYP qglGetUniformLocationARB) (GLhandleARB program, const char *name);
-extern void (APIENTRYP qglUniform1fARB) (GLint location, GLfloat v0);
-extern void (APIENTRYP qglUniform1iARB) (GLint location, GLint v0);
-
-// frame and render buffer
-extern void (APIENTRYP qglGenFramebuffersEXT) (GLsizei n, GLuint *framebuffers);
-extern void (APIENTRYP qglDeleteFramebuffersEXT) (GLsizei n, const GLuint *framebuffers);
-extern GLvoid (APIENTRYP qglBindFramebufferEXT) (GLenum target, GLuint framebuffer);
-extern GLvoid (APIENTRYP qglFramebufferTexture2DEXT) (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level);
-extern GLenum (APIENTRYP qglCheckFramebufferStatusEXT) (GLenum target);
-
-extern void (APIENTRYP qglGenRenderbuffersEXT) (GLsizei n, GLuint *renderbuffers);
-extern void (APIENTRYP qglDeleteRenderbuffersEXT) (GLsizei n, const GLuint *renderbuffers);
-extern void (APIENTRYP qglBindRenderbufferEXT) (GLenum target, GLuint renderbuffer);
-extern GLvoid (APIENTRYP qglFramebufferRenderbufferEXT) (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer);
-extern GLvoid (APIENTRYP qglRenderbufferStorageEXT) (GLenum target, GLenum internalformat, GLsizei width, GLsizei height);
-extern GLvoid (APIENTRYP qglRenderbufferStorageMultisampleEXT) (GLenum target, GLsizei samples, GLenum internalformat, GLsizei width, GLsizei height);
-extern GLvoid (APIENTRYP qglBlitFramebufferEXT) (GLint srcX0, GLint srcY0, GLint srcX1, GLint srcY1, GLint dstX0, GLint dstY0, GLint dstX1, GLint dstY1, GLbitfield mask, GLenum filter);
 
 //===========================================================================
 
@@ -102,11 +69,8 @@
 	GLE(GLenum, GetError, void) \
 	GLE(void, GetIntegerv, GLenum pname, GLint *params) \
 	GLE(const GLubyte *, GetString, GLenum name) \
-	GLE(void, GetTexImage, GLenum target, GLint level, GLenum format, GLenum type, GLvoid * pixels) \
 	GLE(void, LineWidth, GLfloat width) \
-	GLE(void, PixelStorei, GLenum pname, GLint param) \
 	GLE(void, PolygonOffset, GLfloat factor, GLfloat units) \
-	GLE(void, ReadBuffer, GLenum mode) \
 	GLE(void, ReadPixels, GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid *pixels) \
 	GLE(void, Scissor, GLint x, GLint y, GLsizei width, GLsizei height) \
 	GLE(void, StencilFunc, GLenum func, GLint ref, GLuint mask) \
@@ -145,28 +109,24 @@
 
 // OpenGL 1.0/1.1 but not OpenGL 3.2 core profile or OpenGL ES 1.x
 #define QGL_DESKTOP_1_1_FIXED_FUNCTION_PROCS \
-	GLE(void, ArrayElement, GLint i)  \
-	GLE(void, Begin, GLenum mode)			  \
-	GLE(void, ClipPlane, GLenum plane, const GLdouble *equation)	 \
-	GLE(void, Color3f, GLfloat red, GLfloat green, GLfloat blue)	 \
-	GLE(void, Color4ubv, const GLubyte *v)							 \
-	GLE(void, End, void)											 \
+	GLE(void, ArrayElement, GLint i) \
+	GLE(void, Begin, GLenum mode) \
+	GLE(void, ClipPlane, GLenum plane, const GLdouble *equation) \
+	GLE(void, Color3f, GLfloat red, GLfloat green, GLfloat blue) \
+	GLE(void, Color4ubv, const GLubyte *v) \
+	GLE(void, End, void) \
 	GLE(void, Frustum, GLdouble left, GLdouble right, GLdouble bottom, GLdouble top, GLdouble near_val, GLdouble far_val) \
 	GLE(void, Ortho, GLdouble left, GLdouble right, GLdouble bottom, GLdouble top, GLdouble near_val, GLdouble far_val) \
-	GLE(void, TexCoord2d, GLdouble s, GLdouble t) \
-	GLE(void, TexCoord2f, GLfloat s, GLfloat t)							\
-	GLE(void, TexCoord2fv, const GLfloat *v)							\
-	GLE(void, TexCoord2i, GLint s, GLint t)  \
-	GLE(void, Vertex2d, GLdouble x,  GLdouble y) \
+	GLE(void, TexCoord2f, GLfloat s, GLfloat t) \
+	GLE(void, TexCoord2fv, const GLfloat *v) \
 	GLE(void, Vertex2f, GLfloat x, GLfloat y) \
-	GLE(void, Vertex2i, GLshort x, GLshort y)			 \
 	GLE(void, Vertex3f, GLfloat x, GLfloat y, GLfloat z) \
 	GLE(void, Vertex3fv, const GLfloat *v) \
 
 // OpenGL ES 1.1 and OpenGL ES 2.0 but not desktop OpenGL 1.x
 #define QGL_ES_1_1_PROCS \
-	GLE(void, ClearDepthf, GLclampf depth)								\
-	GLE(void, DepthRangef, GLclampf near_val, GLclampf far_val)			\
+	GLE(void, ClearDepthf, GLclampf depth) \
+	GLE(void, DepthRangef, GLclampf near_val, GLclampf far_val) \
 
 // OpenGL ES 1.1 but not OpenGL ES 2.0 or desktop OpenGL 1.x
 #define QGL_ES_1_1_FIXED_FUNCTION_PROCS \

```

### `openarena-engine`  — sha256 `820a098132c7...`, 35329 bytes

_Diff stat: +651 / -263 lines_

_(full diff is 49855 bytes — see files directly)_
