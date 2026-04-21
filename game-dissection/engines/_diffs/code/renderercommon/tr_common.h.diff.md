# Diff: `code/renderercommon/tr_common.h`
**Canonical:** `wolfcamql-src` (sha256 `1392b530171d...`, 6703 bytes)

## Variants

### `ioquake3`  — sha256 `75cb720b3153...`, 6138 bytes

_Diff stat: +0 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_common.h	2026-04-16 20:02:25.233261900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_common.h	2026-04-16 20:02:21.575614600 +0100
@@ -23,7 +23,6 @@
 #define TR_COMMON_H
 
 #include "../qcommon/q_shared.h"
-#include "../qcommon/qfiles.h"
 #include "../renderercommon/tr_public.h"
 #include "qgl.h"
 
@@ -64,14 +63,12 @@
 	struct image_s*	next;
 } image_t;
 
-#if 0
 // any change in the LIGHTMAP_* defines here MUST be reflected in
 // R_FindShader() in tr_bsp.c
 #define LIGHTMAP_2D         -4	// shader is for 2D rendering
 #define LIGHTMAP_BY_VERTEX  -3	// pre-lit triangle models
 #define LIGHTMAP_WHITEIMAGE -2
 #define LIGHTMAP_NONE       -1
-#endif
 
 extern	refimport_t		ri;
 extern glconfig_t	glConfig;		// outside of TR since it shouldn't be cleared during ref re-init
@@ -118,15 +115,6 @@
 
 extern	cvar_t	*r_saveFontData;
 
-extern cvar_t *r_debugFonts;
-extern cvar_t *r_defaultQlFontFallbacks;
-extern cvar_t *r_defaultMSFontFallbacks;
-extern cvar_t *r_defaultSystemFontFallbacks;
-extern cvar_t *r_defaultUnifontFallbacks;
-
-extern cvar_t *r_screenMapTextureSize;
-extern cvar_t *r_weather;
-
 qboolean	R_GetModeInfo( int *width, int *height, float *windowAspect, int mode );
 
 float R_NoiseGet4f( float x, float y, float z, double t );
@@ -145,11 +133,6 @@
 void R_InitFreeType( void );
 void R_DoneFreeType( void );
 void RE_RegisterFont(const char *fontName, int pointSize, fontInfo_t *font);
-qboolean RE_GetGlyphInfo (fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut);
-qboolean RE_GetFontInfo (int fontId, fontInfo_t *font);
-
-void R_LoadAdvertisements( lump_t *l );
-void RE_UpdateDof (float viewFocus, float viewRadius);
 
 /*
 =============================================================

```

### `openarena-engine`  — sha256 `8fcc18c974eb...`, 6232 bytes

_Diff stat: +34 / -36 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_common.h	2026-04-16 20:02:25.233261900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_common.h	2026-04-16 22:48:25.930957100 +0100
@@ -23,7 +23,6 @@
 #define TR_COMMON_H
 
 #include "../qcommon/q_shared.h"
-#include "../qcommon/qfiles.h"
 #include "../renderercommon/tr_public.h"
 #include "qgl.h"
 
@@ -44,9 +43,30 @@
 	IMGFLAG_NO_COMPRESSION = 0x0010,
 	IMGFLAG_NOLIGHTSCALE   = 0x0020,
 	IMGFLAG_CLAMPTOEDGE    = 0x0040,
-	IMGFLAG_GENNORMALMAP   = 0x0080,
+	IMGFLAG_SRGB           = 0x0080,
+	IMGFLAG_GENNORMALMAP   = 0x0100,
 } imgFlags_t;
 
+// DDS stuff
+
+
+typedef enum
+{
+    FT_DEFAULT,
+    FT_LINEAR,
+    FT_NEAREST
+} filterType_t;
+
+typedef enum
+{
+    WT_REPEAT,
+    WT_CLAMP,					// don't repeat the texture for texture coords outside [0, 1]
+    WT_EDGE_CLAMP,
+    WT_ZERO_CLAMP,				// guarantee 0,0,0,255 edge for projected textures
+    WT_ALPHA_ZERO_CLAMP			// guarante 0 alpha edge for projected textures
+} wrapType_t;
+
+
 typedef struct image_s {
 	char		imgName[MAX_QPATH];		// game path, including extension
 	int			width, height;				// source image
@@ -62,16 +82,24 @@
 	imgFlags_t  flags;
 
 	struct image_s*	next;
+
+	qboolean			maptexture;	// leilei - map texture listing hack
+
+	float				loadTime;	// leilei - time taken loading image
+	float				procTime;	// leilei - time taken processing image/uploading to vram
+
+	// DXT/DDS stuff
+	GLenum          ddsType;
+   	filterType_t	filterType; 	
+   	wrapType_t	wrapType;
 } image_t;
 
-#if 0
 // any change in the LIGHTMAP_* defines here MUST be reflected in
 // R_FindShader() in tr_bsp.c
 #define LIGHTMAP_2D         -4	// shader is for 2D rendering
 #define LIGHTMAP_BY_VERTEX  -3	// pre-lit triangle models
 #define LIGHTMAP_WHITEIMAGE -2
 #define LIGHTMAP_NONE       -1
-#endif
 
 extern	refimport_t		ri;
 extern glconfig_t	glConfig;		// outside of TR since it shouldn't be cleared during ref re-init
@@ -83,7 +111,6 @@
 extern qboolean  textureFilterAnisotropic;
 extern int       maxAnisotropy;
 extern float     displayAspect;
-extern qboolean  haveClampToEdge;
 
 //
 // cvars
@@ -118,18 +145,9 @@
 
 extern	cvar_t	*r_saveFontData;
 
-extern cvar_t *r_debugFonts;
-extern cvar_t *r_defaultQlFontFallbacks;
-extern cvar_t *r_defaultMSFontFallbacks;
-extern cvar_t *r_defaultSystemFontFallbacks;
-extern cvar_t *r_defaultUnifontFallbacks;
-
-extern cvar_t *r_screenMapTextureSize;
-extern cvar_t *r_weather;
-
 qboolean	R_GetModeInfo( int *width, int *height, float *windowAspect, int mode );
 
-float R_NoiseGet4f( float x, float y, float z, double t );
+float R_NoiseGet4f( float x, float y, float z, float t );
 void  R_NoiseInit( void );
 
 image_t     *R_FindImageFile( const char *name, imgType_t type, imgFlags_t flags );
@@ -145,26 +163,6 @@
 void R_InitFreeType( void );
 void R_DoneFreeType( void );
 void RE_RegisterFont(const char *fontName, int pointSize, fontInfo_t *font);
-qboolean RE_GetGlyphInfo (fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut);
-qboolean RE_GetFontInfo (int fontId, fontInfo_t *font);
-
-void R_LoadAdvertisements( lump_t *l );
-void RE_UpdateDof (float viewFocus, float viewRadius);
-
-/*
-=============================================================
-
-IMAGE LOADERS
-
-=============================================================
-*/
-
-void R_LoadBMP( const char *name, byte **pic, int *width, int *height );
-void R_LoadJPG( const char *name, byte **pic, int *width, int *height );
-void R_LoadPCX( const char *name, byte **pic, int *width, int *height );
-void R_LoadPNG( const char *name, byte **pic, int *width, int *height );
-void R_LoadPVR( const char *name, byte **pic, int *width, int *height );
-void R_LoadTGA( const char *name, byte **pic, int *width, int *height );
 
 /*
 ====================================================================
@@ -174,7 +172,7 @@
 ====================================================================
 */
 
-void		GLimp_Init( qboolean fixedFunction );
+void		GLimp_Init( void );
 void		GLimp_Shutdown( void );
 void		GLimp_EndFrame( void );
 

```
