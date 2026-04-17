# Diff: `code/renderercommon/tr_types.h`
**Canonical:** `wolfcamql-src` (sha256 `eb1d1a27e5e7...`, 10346 bytes)

## Variants

### `ioquake3`  — sha256 `d77d2b3aeb32...`, 7646 bytes

_Diff stat: +4 / -92 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_types.h	2026-04-16 20:02:25.238330600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_types.h	2026-04-16 20:02:21.578616700 +0100
@@ -23,30 +23,10 @@
 #ifndef __TR_TYPES_H
 #define __TR_TYPES_H
 
-//FIXME from *opengl.h
-#define GL_CLAMP_TO_EDGE                  0x812F
-//#define GL_CLAMP_TO_EDGE                  0x812D  //0x2900  //0x812F
-#define GL_CLAMP_TO_BORDER                0x812D
-#define GL_CLAMP_TO_BORDER_ARB            0x812D
-#define GL_CLAMP_VERTEX_COLOR_ARB         0x891A
-#define GL_CLAMP_FRAGMENT_COLOR_ARB       0x891B
-#define GL_CLAMP_READ_COLOR_ARB           0x891C
-#define GL_CLAMP_TO_EDGE_SGIS             0x812F
-#define GL_CLAMP_TO_BORDER_SGIS           0x812D
-
-// any change in the LIGHTMAP_* defines here MUST be reflected in
-// R_FindShader() in tr_bsp.c
-#define LIGHTMAP_2D         -4  // shader is for 2D rendering
-#define LIGHTMAP_BY_VERTEX  -3  // pre-lit triangle models
-#define LIGHTMAP_WHITEIMAGE -2
-#define LIGHTMAP_NONE       -1
-
-////////////////
 
 #define	MAX_DLIGHTS		32		// can't be increased, because bit flags are used on surfaces
 
-// wolfcam: increased from 10 to 14
-#define	REFENTITYNUM_BITS	14		// can't be increased without changing drawsurf bit packing
+#define	REFENTITYNUM_BITS	10		// can't be increased without changing drawsurf bit packing
 #define	REFENTITYNUM_MASK	((1<<REFENTITYNUM_BITS) - 1)
 // the last N-bit number (2^REFENTITYNUM_BITS - 1) is reserved for the special world refentity,
 //  and this is reflected by the value of MAX_REFENTITIES (which therefore is not a power-of-2)
@@ -93,21 +73,13 @@
 
 typedef enum {
 	RT_MODEL,
-	RT_MODEL_FX_DIR,
-	RT_MODEL_FX_ANGLES,
-	RT_MODEL_FX_AXIS,
 	RT_POLY,
 	RT_SPRITE,
-	RT_SPRITE_FIXED,
-	RT_SPARK,
 	RT_BEAM,
 	RT_RAIL_CORE,
 	RT_RAIL_RINGS,
 	RT_LIGHTNING,
-	RT_PORTALSURFACE,               // doesn't draw anything, just info for portals
-	RT_BEAM_Q3MME,
-	RT_RAIL_RINGS_Q3MME,
-	RT_GRAPPLE,
+	RT_PORTALSURFACE,		// doesn't draw anything, just info for portals
 
 	RT_MAX_REF_ENTITY_TYPE
 } refEntityType_t;
@@ -141,19 +113,10 @@
 	byte		shaderRGBA[4];		// colors used by rgbgen entity shaders
 	float		shaderTexCoord[2];	// texture coordinates used by tcMod entity modifiers
 	float		shaderTime;			// subtracted from refdef time to control effect start times
-	//float angle;
 
 	// extra sprite information
-	float           radius;
-	float           rotation;
-	qboolean        useScale;
-	float width;
-	float height;
-
-	// stretch sprites
-	//FIXME uses other variables that aren't used
-	qboolean stretch;
-	float s1, t1, s2, t2;
+	float		radius;
+	float		rotation;
 } refEntity_t;
 
 
@@ -219,7 +182,6 @@
 	GLHW_PERMEDIA2			// where you don't have src*dst
 } glHardwareType_t;
 
-#if 0
 typedef struct {
 	char					renderer_string[MAX_STRING_CHARS];
 	char					vendor_string[MAX_STRING_CHARS];
@@ -253,55 +215,5 @@
 	qboolean				stereoEnabled;
 	qboolean				smpActive;		// UNUSED, present for compatibility
 } glconfig_t;
-#endif
-
-typedef struct {
-	char					renderer_string[MAX_STRING_CHARS];
-	char					vendor_string[MAX_STRING_CHARS];
-	char					version_string[MAX_STRING_CHARS];
-	char					extensions_string[BIG_INFO_STRING * 2];
-
-	int						maxTextureSize;			// queried from GL
-	int						numTextureUnits;		// multitexture ability
-
-	int						colorBits, depthBits, stencilBits;
-
-	glDriverType_t			driverType;
-	glHardwareType_t		hardwareType;
-
-	qboolean				deviceSupportsGamma;
-	textureCompression_t	textureCompression;
-	qboolean				textureEnvAddAvailable;
-	qboolean				textureRectangleAvailable;
-
-	int						vidWidth, vidHeight;
-	// aspect is the screen's physical width / height, which may be different
-	// than scrWidth / scrHeight if the pixels are non-square
-	// normal screens should be 4/3, but wide aspect monitors may be 16/9
-	float					windowAspect;
-
-	// if using framebuffer for video rendering
-
-	int visibleWindowWidth;
-	int visibleWindowHeight;
-	int visibleWindowAspect;
-
-	int						displayFrequency;
-
-	// synonymous with "does rendering consume the entire screen?", therefore
-	// a Voodoo or Voodoo2 will have this set to TRUE, as will a Win32 ICD that
-	// used CDS.
-	qboolean				isFullscreen;
-	qboolean				stereoEnabled;
-	qboolean				smpActive;		// UNUSED
-	qboolean qlGlsl;
-	qboolean fbo;  // framebuffer object
-	qboolean fboStencil;
-	qboolean fboMultiSample;
-	int maxViewPortWidth;
-	int maxViewPortHeight;
-	int maxRenderBufferSize;
-
-} glconfig_t;
 
 #endif	// __TR_TYPES_H

```

### `quake3e`  — sha256 `2aee6d7fe4bc...`, 7506 bytes

_Diff stat: +27 / -109 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_types.h	2026-04-16 20:02:25.238330600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_types.h	2026-04-16 20:02:27.344319500 +0100
@@ -23,53 +23,27 @@
 #ifndef __TR_TYPES_H
 #define __TR_TYPES_H
 
-//FIXME from *opengl.h
-#define GL_CLAMP_TO_EDGE                  0x812F
-//#define GL_CLAMP_TO_EDGE                  0x812D  //0x2900  //0x812F
-#define GL_CLAMP_TO_BORDER                0x812D
-#define GL_CLAMP_TO_BORDER_ARB            0x812D
-#define GL_CLAMP_VERTEX_COLOR_ARB         0x891A
-#define GL_CLAMP_FRAGMENT_COLOR_ARB       0x891B
-#define GL_CLAMP_READ_COLOR_ARB           0x891C
-#define GL_CLAMP_TO_EDGE_SGIS             0x812F
-#define GL_CLAMP_TO_BORDER_SGIS           0x812D
-
-// any change in the LIGHTMAP_* defines here MUST be reflected in
-// R_FindShader() in tr_bsp.c
-#define LIGHTMAP_2D         -4  // shader is for 2D rendering
-#define LIGHTMAP_BY_VERTEX  -3  // pre-lit triangle models
-#define LIGHTMAP_WHITEIMAGE -2
-#define LIGHTMAP_NONE       -1
-
-////////////////
-
-#define	MAX_DLIGHTS		32		// can't be increased, because bit flags are used on surfaces
-
-// wolfcam: increased from 10 to 14
-#define	REFENTITYNUM_BITS	14		// can't be increased without changing drawsurf bit packing
-#define	REFENTITYNUM_MASK	((1<<REFENTITYNUM_BITS) - 1)
-// the last N-bit number (2^REFENTITYNUM_BITS - 1) is reserved for the special world refentity,
-//  and this is reflected by the value of MAX_REFENTITIES (which therefore is not a power-of-2)
-#define	MAX_REFENTITIES		((1<<REFENTITYNUM_BITS) - 1)
-#define	REFENTITYNUM_WORLD	((1<<REFENTITYNUM_BITS) - 1)
+#define MAX_VIDEO_HANDLES	16
+
+#define	MAX_DLIGHTS			32			// can't be increased, because bit flags are used on surfaces
 
 // renderfx flags
-#define	RF_MINLIGHT		0x0001		// allways have some light (viewmodel, some items)
+#define	RF_MINLIGHT			0x0001		// always have some light (viewmodel, some items)
 #define	RF_THIRD_PERSON		0x0002		// don't draw through eyes, only mirrors (player bodies, chat sprites)
 #define	RF_FIRST_PERSON		0x0004		// only draw through eyes (view weapon, damage blood blob)
 #define	RF_DEPTHHACK		0x0008		// for view weapon Z crunching
 
 #define RF_CROSSHAIR		0x0010		// This item is a cross hair and will draw over everything similar to
-						// DEPTHHACK in stereo rendering mode, with the difference that the
-						// projection matrix won't be hacked to reduce the stereo separation as
-						// is done for the gun.
+										// DEPTHHACK in stereo rendering mode, with the difference that the
+										// projection matrix won't be hacked to reduce the stereo separation as
+										// is done for the gun.
 
-#define	RF_NOSHADOW		0x0040		// don't add stencil shadows
+#define	RF_NOSHADOW			0x0040		// don't add stencil shadows
 
 #define RF_LIGHTING_ORIGIN	0x0080		// use refEntity->lightingOrigin instead of refEntity->origin
-						// for lighting.  This allows entities to sink into the floor
-						// with their origin going solid, and allows all parts of a
-						// player to get the same lighting
+										// for lighting.  This allows entities to sink into the floor
+										// with their origin going solid, and allows all parts of a
+										// player to get the same lighting
 
 #define	RF_SHADOW_PLANE		0x0100		// use refEntity->shadowPlane
 #define	RF_WRAP_FRAMES		0x0200		// mod the model frames by the maxframes to allow continuous
@@ -82,7 +56,7 @@
 typedef struct {
 	vec3_t		xyz;
 	float		st[2];
-	byte		modulate[4];
+	color4ub_t	modulate;
 } polyVert_t;
 
 typedef struct poly_s {
@@ -93,21 +67,13 @@
 
 typedef enum {
 	RT_MODEL,
-	RT_MODEL_FX_DIR,
-	RT_MODEL_FX_ANGLES,
-	RT_MODEL_FX_AXIS,
 	RT_POLY,
 	RT_SPRITE,
-	RT_SPRITE_FIXED,
-	RT_SPARK,
 	RT_BEAM,
 	RT_RAIL_CORE,
 	RT_RAIL_RINGS,
 	RT_LIGHTNING,
-	RT_PORTALSURFACE,               // doesn't draw anything, just info for portals
-	RT_BEAM_Q3MME,
-	RT_RAIL_RINGS_Q3MME,
-	RT_GRAPPLE,
+	RT_PORTALSURFACE,		// doesn't draw anything, just info for portals
 
 	RT_MAX_REF_ENTITY_TYPE
 } refEntityType_t;
@@ -138,22 +104,15 @@
 	qhandle_t	customShader;		// use one image for the entire thing
 
 	// misc
-	byte		shaderRGBA[4];		// colors used by rgbgen entity shaders
+	color4ub_t	shader;
 	float		shaderTexCoord[2];	// texture coordinates used by tcMod entity modifiers
-	float		shaderTime;			// subtracted from refdef time to control effect start times
-	//float angle;
+
+	// subtracted from refdef time to control effect start times
+	floatint_t	shaderTime;			// -EC- set to union
 
 	// extra sprite information
-	float           radius;
-	float           rotation;
-	qboolean        useScale;
-	float width;
-	float height;
-
-	// stretch sprites
-	//FIXME uses other variables that aren't used
-	qboolean stretch;
-	float s1, t1, s2, t2;
+	float		radius;
+	float		rotation;
 } refEntity_t;
 
 
@@ -219,7 +178,6 @@
 	GLHW_PERMEDIA2			// where you don't have src*dst
 } glHardwareType_t;
 
-#if 0
 typedef struct {
 	char					renderer_string[MAX_STRING_CHARS];
 	char					vendor_string[MAX_STRING_CHARS];
@@ -253,55 +211,15 @@
 	qboolean				stereoEnabled;
 	qboolean				smpActive;		// UNUSED, present for compatibility
 } glconfig_t;
-#endif
-
-typedef struct {
-	char					renderer_string[MAX_STRING_CHARS];
-	char					vendor_string[MAX_STRING_CHARS];
-	char					version_string[MAX_STRING_CHARS];
-	char					extensions_string[BIG_INFO_STRING * 2];
 
-	int						maxTextureSize;			// queried from GL
-	int						numTextureUnits;		// multitexture ability
-
-	int						colorBits, depthBits, stencilBits;
-
-	glDriverType_t			driverType;
-	glHardwareType_t		hardwareType;
-
-	qboolean				deviceSupportsGamma;
-	textureCompression_t	textureCompression;
-	qboolean				textureEnvAddAvailable;
-	qboolean				textureRectangleAvailable;
+#define	myftol(x) ((int)(x))
 
-	int						vidWidth, vidHeight;
-	// aspect is the screen's physical width / height, which may be different
-	// than scrWidth / scrHeight if the pixels are non-square
-	// normal screens should be 4/3, but wide aspect monitors may be 16/9
-	float					windowAspect;
-
-	// if using framebuffer for video rendering
-
-	int visibleWindowWidth;
-	int visibleWindowHeight;
-	int visibleWindowAspect;
-
-	int						displayFrequency;
-
-	// synonymous with "does rendering consume the entire screen?", therefore
-	// a Voodoo or Voodoo2 will have this set to TRUE, as will a Win32 ICD that
-	// used CDS.
-	qboolean				isFullscreen;
-	qboolean				stereoEnabled;
-	qboolean				smpActive;		// UNUSED
-	qboolean qlGlsl;
-	qboolean fbo;  // framebuffer object
-	qboolean fboStencil;
-	qboolean fboMultiSample;
-	int maxViewPortWidth;
-	int maxViewPortHeight;
-	int maxRenderBufferSize;
-
-} glconfig_t;
+#if defined(_WIN32)
+#define OPENGL_DRIVER_NAME	"opengl32"
+#elif defined(MACOS_X)
+#define OPENGL_DRIVER_NAME	"/System/Library/Frameworks/OpenGL.framework/Libraries/libGL.dylib"
+#else
+#define OPENGL_DRIVER_NAME	"libGL.so.1"
+#endif
 
 #endif	// __TR_TYPES_H

```

### `openarena-engine`  — sha256 `d98746acef22...`, 7794 bytes

_Diff stat: +17 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_types.h	2026-04-16 20:02:25.238330600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_types.h	2026-04-16 22:48:25.932966000 +0100
@@ -23,30 +23,10 @@
 #ifndef __TR_TYPES_H
 #define __TR_TYPES_H
 
-//FIXME from *opengl.h
-#define GL_CLAMP_TO_EDGE                  0x812F
-//#define GL_CLAMP_TO_EDGE                  0x812D  //0x2900  //0x812F
-#define GL_CLAMP_TO_BORDER                0x812D
-#define GL_CLAMP_TO_BORDER_ARB            0x812D
-#define GL_CLAMP_VERTEX_COLOR_ARB         0x891A
-#define GL_CLAMP_FRAGMENT_COLOR_ARB       0x891B
-#define GL_CLAMP_READ_COLOR_ARB           0x891C
-#define GL_CLAMP_TO_EDGE_SGIS             0x812F
-#define GL_CLAMP_TO_BORDER_SGIS           0x812D
-
-// any change in the LIGHTMAP_* defines here MUST be reflected in
-// R_FindShader() in tr_bsp.c
-#define LIGHTMAP_2D         -4  // shader is for 2D rendering
-#define LIGHTMAP_BY_VERTEX  -3  // pre-lit triangle models
-#define LIGHTMAP_WHITEIMAGE -2
-#define LIGHTMAP_NONE       -1
-
-////////////////
 
 #define	MAX_DLIGHTS		32		// can't be increased, because bit flags are used on surfaces
 
-// wolfcam: increased from 10 to 14
-#define	REFENTITYNUM_BITS	14		// can't be increased without changing drawsurf bit packing
+#define	REFENTITYNUM_BITS	10		// can't be increased without changing drawsurf bit packing
 #define	REFENTITYNUM_MASK	((1<<REFENTITYNUM_BITS) - 1)
 // the last N-bit number (2^REFENTITYNUM_BITS - 1) is reserved for the special world refentity,
 //  and this is reflected by the value of MAX_REFENTITIES (which therefore is not a power-of-2)
@@ -73,7 +53,6 @@
 
 #define	RF_SHADOW_PLANE		0x0100		// use refEntity->shadowPlane
 #define	RF_WRAP_FRAMES		0x0200		// mod the model frames by the maxframes to allow continuous
-										// animation without needing to know the frame count
 
 // refdef flags
 #define RDF_NOWORLDMODEL	0x0001		// used for player configuration screen
@@ -93,21 +72,13 @@
 
 typedef enum {
 	RT_MODEL,
-	RT_MODEL_FX_DIR,
-	RT_MODEL_FX_ANGLES,
-	RT_MODEL_FX_AXIS,
 	RT_POLY,
 	RT_SPRITE,
-	RT_SPRITE_FIXED,
-	RT_SPARK,
 	RT_BEAM,
 	RT_RAIL_CORE,
 	RT_RAIL_RINGS,
 	RT_LIGHTNING,
-	RT_PORTALSURFACE,               // doesn't draw anything, just info for portals
-	RT_BEAM_Q3MME,
-	RT_RAIL_RINGS_Q3MME,
-	RT_GRAPPLE,
+	RT_PORTALSURFACE,		// doesn't draw anything, just info for portals
 
 	RT_MAX_REF_ENTITY_TYPE
 } refEntityType_t;
@@ -141,19 +112,21 @@
 	byte		shaderRGBA[4];		// colors used by rgbgen entity shaders
 	float		shaderTexCoord[2];	// texture coordinates used by tcMod entity modifiers
 	float		shaderTime;			// subtracted from refdef time to control effect start times
-	//float angle;
 
 	// extra sprite information
-	float           radius;
-	float           rotation;
-	qboolean        useScale;
-	float width;
-	float height;
-
-	// stretch sprites
-	//FIXME uses other variables that aren't used
-	qboolean stretch;
-	float s1, t1, s2, t2;
+	float		radius;
+	float		rotation;
+
+	// leilei - eyes
+
+	vec3_t		eyepos[2];			// looking from
+	vec3_t		eyelook;			// looking from
+
+	// leilei - glow
+
+	int		glow;				// glow security + fx
+	int		glowcol;			// glow color in hexadecimal
+
 } refEntity_t;
 
 
@@ -176,6 +149,7 @@
 
 	// text messages for deform text shaders
 	char		text[MAX_RENDER_STRINGS][MAX_RENDER_STRING_LENGTH];
+
 } refdef_t;
 
 
@@ -210,7 +184,7 @@
 } glDriverType_t;
 
 typedef enum {
-	GLHW_GENERIC,			// where everything works the way it should
+	GLHW_GENERIC,			// where everthing works the way it should
 	GLHW_3DFX_2D3D,			// Voodoo Banshee or Voodoo3, relevant since if this is
 							// the hardware type then there can NOT exist a secondary
 							// display adapter
@@ -219,7 +193,6 @@
 	GLHW_PERMEDIA2			// where you don't have src*dst
 } glHardwareType_t;
 
-#if 0
 typedef struct {
 	char					renderer_string[MAX_STRING_CHARS];
 	char					vendor_string[MAX_STRING_CHARS];
@@ -252,55 +225,6 @@
 	qboolean				isFullscreen;
 	qboolean				stereoEnabled;
 	qboolean				smpActive;		// UNUSED, present for compatibility
-} glconfig_t;
-#endif
-
-typedef struct {
-	char					renderer_string[MAX_STRING_CHARS];
-	char					vendor_string[MAX_STRING_CHARS];
-	char					version_string[MAX_STRING_CHARS];
-	char					extensions_string[BIG_INFO_STRING * 2];
-
-	int						maxTextureSize;			// queried from GL
-	int						numTextureUnits;		// multitexture ability
-
-	int						colorBits, depthBits, stencilBits;
-
-	glDriverType_t			driverType;
-	glHardwareType_t		hardwareType;
-
-	qboolean				deviceSupportsGamma;
-	textureCompression_t	textureCompression;
-	qboolean				textureEnvAddAvailable;
-	qboolean				textureRectangleAvailable;
-
-	int						vidWidth, vidHeight;
-	// aspect is the screen's physical width / height, which may be different
-	// than scrWidth / scrHeight if the pixels are non-square
-	// normal screens should be 4/3, but wide aspect monitors may be 16/9
-	float					windowAspect;
-
-	// if using framebuffer for video rendering
-
-	int visibleWindowWidth;
-	int visibleWindowHeight;
-	int visibleWindowAspect;
-
-	int						displayFrequency;
-
-	// synonymous with "does rendering consume the entire screen?", therefore
-	// a Voodoo or Voodoo2 will have this set to TRUE, as will a Win32 ICD that
-	// used CDS.
-	qboolean				isFullscreen;
-	qboolean				stereoEnabled;
-	qboolean				smpActive;		// UNUSED
-	qboolean qlGlsl;
-	qboolean fbo;  // framebuffer object
-	qboolean fboStencil;
-	qboolean fboMultiSample;
-	int maxViewPortWidth;
-	int maxViewPortHeight;
-	int maxRenderBufferSize;
 
 } glconfig_t;
 

```
