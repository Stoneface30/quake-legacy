# Diff: `code/renderercommon/tr_public.h`
**Canonical:** `wolfcamql-src` (sha256 `60ff76189080...`, 10511 bytes)

## Variants

### `ioquake3`  — sha256 `23e2e7e6dd6f...`, 8052 bytes

_Diff stat: +19 / -73 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_public.h	2026-04-16 20:02:25.237331000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_public.h	2026-04-16 20:02:21.577618400 +0100
@@ -23,16 +23,8 @@
 #define __TR_PUBLIC_H
 
 #include "tr_types.h"
-#include "../cgame/cg_camera.h"
-#include "../client/cl_avi.h"
 
-#ifdef USE_LOCAL_HEADERS
-  #include "SDL_opengl.h"
-#else
-  #include <SDL_opengl.h>
-#endif
-
-#define	REF_API_VERSION		601  // wolfcam don't know the point of this, but bumping anyway
+#define	REF_API_VERSION		8
 
 //
 // these are the functions exported by the refresh module
@@ -53,12 +45,9 @@
 	// and height, which can be used by the client to intelligently
 	// size display elements
 	void	(*BeginRegistration)( glconfig_t *config );
-	void (*GetGlConfig)(glconfig_t *config);
 	qhandle_t (*RegisterModel)( const char *name );
-	void (*GetModelName)( qhandle_t index, char *name, int sz );
 	qhandle_t (*RegisterSkin)( const char *name );
 	qhandle_t (*RegisterShader)( const char *name );
-	qhandle_t (*RegisterShaderLightMap)( const char *name, int lightmap );
 	qhandle_t (*RegisterShaderNoMip)( const char *name );
 	void	(*LoadWorld)( const char *name );
 
@@ -74,10 +63,8 @@
 	// Nothing is drawn until R_RenderScene is called.
 	void	(*ClearScene)( void );
 	void	(*AddRefEntityToScene)( const refEntity_t *re );
-	void	(*AddRefEntityPtrToScene)(refEntity_t *re);
-	void (*SetPathLines)(int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color);
-	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num, int lightmap );
-	int		(*LightForPoint)( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
+	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num );
+	int		(*LightForPoint)( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
 	void	(*AddLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
 	void	(*AddAdditiveLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
 	void	(*RenderScene)( const refdef_t *fd );
@@ -90,7 +77,7 @@
 	void	(*DrawStretchRaw) (int x, int y, int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
 	void	(*UploadCinematic) (int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
 
-	void	(*BeginFrame)(stereoFrame_t stereoFrame, qboolean recordingVideo);
+	void	(*BeginFrame)( stereoFrame_t stereoFrame );
 
 	// if the pointers are not NULL, timing info will be returned
 	void	(*EndFrame)( int *frontEndMsec, int *backEndMsec );
@@ -107,25 +94,11 @@
 	void    (*A3D_RenderGeometry) (void *pVoidA3D, void *pVoidGeom, void *pVoidMat, void *pVoidGeomStatus);
 #endif
 	void	(*RegisterFont)(const char *fontName, int pointSize, fontInfo_t *font);
-	qboolean (*GetGlyphInfo) (fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut);
-	qboolean (*GetFontInfo) (int fontId, fontInfo_t *font);
-	void (*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime, qboolean keepLightmap, qboolean userSet);
-	void (*ClearRemappedShader)(const char *shaderName);
+	void	(*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime);
 	qboolean (*GetEntityToken)( char *buffer, int size );
 	qboolean (*inPVS)( const vec3_t p1, const vec3_t p2 );
 
-	void (*TakeVideoFrame)(aviFileData_t *afd, int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg, qboolean avi, qboolean tga, qboolean jpg, qboolean png, int picCount, char *givenFileName);
-
-	void (*BeginHud)(void);
-	void (*UpdateDof)(float viewFocus, float viewRadius);
-
-	void (*Get_Advertisements)(int *num, float *verts, char shaders[][MAX_QPATH]);
-	void (*ReplaceShaderImage)(qhandle_t h, const ubyte *data, int width, int height);
-
-	qhandle_t (*RegisterShaderFromData) (const char *name, ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex);
-	void (*GetShaderImageDimensions) (qhandle_t h, int *width, int *height);
-	void (*GetShaderImageData) (qhandle_t h, ubyte *data);
-	qhandle_t (*GetSingleShader) (void);
+	void (*TakeVideoFrame)( int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg );
 } refexport_t;
 
 //
@@ -136,12 +109,11 @@
 	void	(QDECL *Printf)( int printLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
 
 	// abort the game
-	void	(QDECL *Error)( int errorLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void	(QDECL *Error)( int errorLevel, const char *fmt, ...) Q_NO_RETURN Q_PRINTF_FUNC(2, 3);
 
-	// RealMilliseconds should only be used for profiling, never
+	// milliseconds should only be used for profiling, never
 	// for anything game related.  Get time from the refdef
-	int		(*ScaledMilliseconds)( void );
-	int		(*RealMilliseconds) (void);
+	int		(*Milliseconds)( void );
 
 	// stack based memory allocation for per-level things that
 	// won't be freed
@@ -160,14 +132,11 @@
 	cvar_t	*(*Cvar_Get)( const char *name, const char *value, int flags );
 	void	(*Cvar_Set)( const char *name, const char *value );
 	void	(*Cvar_SetValue) (const char *name, float value);
-	void	(*Cvar_ForceReset) (const char *var_name);
-	cvar_t	*(*Cvar_FindVar) (const char *var_name);
 	void	(*Cvar_CheckRange)( cvar_t *cv, float minVal, float maxVal, qboolean shouldBeIntegral );
-	int		(*Cvar_VariableIntegerValue) (const char *var_name);
-	float	(*Cvar_VariableValue) (const char *var_name);
-	void	(*Cvar_VariableStringBuffer) (const char *var_name, char *buffer, int bufsize);
 	void	(*Cvar_SetDescription)( cvar_t *cv, const char *description );
 
+	int		(*Cvar_VariableIntegerValue) (const char *var_name);
+
 	void	(*Cmd_AddCommand)( const char *name, void(*cmd)(void) );
 	void	(*Cmd_RemoveCommand)( const char *name );
 
@@ -184,56 +153,33 @@
 	// a -1 return means the file does not exist
 	// NULL can be passed for buf to just determine existence
 	int		(*FS_FileIsInPAK)( const char *name, int *pCheckSum );
-	long	(*FS_ReadFile)( const char *name, void **buf );
+	long		(*FS_ReadFile)( const char *name, void **buf );
 	void	(*FS_FreeFile)( void *buf );
 	char **	(*FS_ListFiles)( const char *name, const char *extension, int *numfilesfound );
 	void	(*FS_FreeFileList)( char **filelist );
 	void	(*FS_WriteFile)( const char *qpath, const void *buffer, int size );
-	int		(*FS_Write) (const void *buffer, int len, fileHandle_t f);
 	qboolean (*FS_FileExists)( const char *file );
-	const char	*(*FS_FindSystemFile) (const char *file);
-	void	(*FS_FCloseFile) (fileHandle_t f);
-	fileHandle_t	(*FS_FOpenFileWrite) (const char *qpath );
 
 	// cinematic stuff
 	void	(*CIN_UploadCinematic)(int handle);
 	int		(*CIN_PlayCinematic)( const char *arg0, int xpos, int ypos, int width, int height, int bits);
 	e_status (*CIN_RunCinematic) (int handle);
 
-	void	(*CL_WriteAVIVideoFrame)(aviFileData_t *afd, const byte *buffer, int size);
+	void	(*CL_WriteAVIVideoFrame)( const byte *buffer, int size );
 
 	// input event handling
 	void	(*IN_Init)( void *windowData );
-	void    (*IN_Shutdown)( void );
-	void    (*IN_Restart)( void );
+	void	(*IN_Shutdown)( void );
+	void	(*IN_Restart)( void );
 
 	// math
 	long    (*ftol)(float f);
 
 	// system stuff
-	void    (*Sys_SetEnv)( const char *name, const char *value );
-	void    (*Sys_GLimpSafeInit)( void );
-	void    (*Sys_GLimpInit)( void );
+	void	(*Sys_SetEnv)( const char *name, const char *value );
+	void	(*Sys_GLimpSafeInit)( void );
+	void	(*Sys_GLimpInit)( void );
 	qboolean (*Sys_LowPhysicalMemory)( void );
-
-	// video recording stuff
-	qboolean *SplitVideo;
-
-	aviFileData_t *afdMain;
-	aviFileData_t *afdLeft;
-	aviFileData_t *afdRight;
-
-	aviFileData_t *afdDepth;
-	aviFileData_t *afdDepthLeft;
-	aviFileData_t *afdDepthRight;
-
-	GLfloat **Video_DepthBuffer;
-	byte **ExtraVideoBuffer;
-
-	// misc
-	mapNames_t *MapNames;
-
-	qboolean sse2_supported;
 } refimport_t;
 
 
@@ -241,7 +187,7 @@
 // If the module can't init to a valid rendering state, NULL will be
 // returned.
 #ifdef USE_RENDERER_DLOPEN
-typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t *rimp);
+typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t * rimp);
 #else
 refexport_t*GetRefAPI( int apiVersion, refimport_t *rimp );
 #endif

```

### `quake3e`  — sha256 `4c00f8283a78...`, 10091 bytes

_Diff stat: +92 / -98 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_public.h	2026-04-16 20:02:25.237331000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_public.h	2026-04-16 20:02:27.344319500 +0100
@@ -23,25 +23,25 @@
 #define __TR_PUBLIC_H
 
 #include "tr_types.h"
-#include "../cgame/cg_camera.h"
-#include "../client/cl_avi.h"
+#include "vulkan/vulkan.h"
 
-#ifdef USE_LOCAL_HEADERS
-  #include "SDL_opengl.h"
-#else
-  #include <SDL_opengl.h>
-#endif
-
-#define	REF_API_VERSION		601  // wolfcam don't know the point of this, but bumping anyway
+#define	REF_API_VERSION		8
 
 //
 // these are the functions exported by the refresh module
 //
+typedef enum {
+	REF_KEEP_CONTEXT, // don't destroy window and context
+	REF_KEEP_WINDOW,  // destroy context, keep window
+	REF_DESTROY_WINDOW,
+	REF_UNLOAD_DLL
+} refShutdownCode_t;
+
 typedef struct {
 	// called before the library is unloaded
 	// if the system is just reconfiguring, pass destroyWindow = qfalse,
 	// which will keep the screen from flashing to the desktop.
-	void	(*Shutdown)( qboolean destroyWindow );
+	void	(*Shutdown)( refShutdownCode_t code );
 
 	// All data that will be used in a level should be
 	// registered before rendering any frames to prevent disk hits,
@@ -53,12 +53,9 @@
 	// and height, which can be used by the client to intelligently
 	// size display elements
 	void	(*BeginRegistration)( glconfig_t *config );
-	void (*GetGlConfig)(glconfig_t *config);
 	qhandle_t (*RegisterModel)( const char *name );
-	void (*GetModelName)( qhandle_t index, char *name, int sz );
 	qhandle_t (*RegisterSkin)( const char *name );
 	qhandle_t (*RegisterShader)( const char *name );
-	qhandle_t (*RegisterShaderLightMap)( const char *name, int lightmap );
 	qhandle_t (*RegisterShaderNoMip)( const char *name );
 	void	(*LoadWorld)( const char *name );
 
@@ -73,24 +70,23 @@
 	// a scene is built up by calls to R_ClearScene and the various R_Add functions.
 	// Nothing is drawn until R_RenderScene is called.
 	void	(*ClearScene)( void );
-	void	(*AddRefEntityToScene)( const refEntity_t *re );
-	void	(*AddRefEntityPtrToScene)(refEntity_t *re);
-	void (*SetPathLines)(int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color);
-	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num, int lightmap );
-	int		(*LightForPoint)( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
+	void	(*AddRefEntityToScene)( const refEntity_t *re, qboolean intShaderTime );
+	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num );
+	int		(*LightForPoint)( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
 	void	(*AddLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
 	void	(*AddAdditiveLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
+	void	(*AddLinearLightToScene)( const vec3_t start, const vec3_t end, float intensity, float r, float g, float b );
 	void	(*RenderScene)( const refdef_t *fd );
 
 	void	(*SetColor)( const float *rgba );	// NULL = 1,1,1,1
-	void	(*DrawStretchPic) ( float x, float y, float w, float h, 
+	void	(*DrawStretchPic) ( float x, float y, float w, float h,
 		float s1, float t1, float s2, float t2, qhandle_t hShader );	// 0 = white
 
 	// Draw images for cinematic rendering, pass as 32 bit rgba
-	void	(*DrawStretchRaw) (int x, int y, int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
-	void	(*UploadCinematic) (int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
+	void	(*DrawStretchRaw)( int x, int y, int w, int h, int cols, int rows, byte *data, int client, qboolean dirty );
+	void	(*UploadCinematic)( int w, int h, int cols, int rows, byte *data, int client, qboolean dirty );
 
-	void	(*BeginFrame)(stereoFrame_t stereoFrame, qboolean recordingVideo);
+	void	(*BeginFrame)( stereoFrame_t stereoFrame );
 
 	// if the pointers are not NULL, timing info will be returned
 	void	(*EndFrame)( int *frontEndMsec, int *backEndMsec );
@@ -99,7 +95,7 @@
 	int		(*MarkFragments)( int numPoints, const vec3_t *points, const vec3_t projection,
 				   int maxPoints, vec3_t pointBuffer, int maxFragments, markFragment_t *fragmentBuffer );
 
-	int		(*LerpTag)( orientation_t *tag,  qhandle_t model, int startFrame, int endFrame, 
+	int		(*LerpTag)( orientation_t *tag,  qhandle_t model, int startFrame, int endFrame,
 					 float frac, const char *tagName );
 	void	(*ModelBounds)( qhandle_t model, vec3_t mins, vec3_t maxs );
 
@@ -107,25 +103,25 @@
 	void    (*A3D_RenderGeometry) (void *pVoidA3D, void *pVoidGeom, void *pVoidMat, void *pVoidGeomStatus);
 #endif
 	void	(*RegisterFont)(const char *fontName, int pointSize, fontInfo_t *font);
-	qboolean (*GetGlyphInfo) (fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut);
-	qboolean (*GetFontInfo) (int fontId, fontInfo_t *font);
-	void (*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime, qboolean keepLightmap, qboolean userSet);
-	void (*ClearRemappedShader)(const char *shaderName);
+	void	(*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime);
 	qboolean (*GetEntityToken)( char *buffer, int size );
 	qboolean (*inPVS)( const vec3_t p1, const vec3_t p2 );
 
-	void (*TakeVideoFrame)(aviFileData_t *afd, int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg, qboolean avi, qboolean tga, qboolean jpg, qboolean png, int picCount, char *givenFileName);
+	void	(*TakeVideoFrame)( int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg );
+
+	void	(*ThrottleBackend)( void );
+	void	(*FinishBloom)( void );
 
-	void (*BeginHud)(void);
-	void (*UpdateDof)(float viewFocus, float viewRadius);
+	void	(*SetColorMappings)( void );
+
+	qboolean (*CanMinimize)( void ); // == fbo enabled
+
+	const glconfig_t *(*GetConfig)( void );
+
+	void	(*VertexLighting)( qboolean allowed );
+	void	(*SyncRender)( void );
 
-	void (*Get_Advertisements)(int *num, float *verts, char shaders[][MAX_QPATH]);
-	void (*ReplaceShaderImage)(qhandle_t h, const ubyte *data, int width, int height);
 
-	qhandle_t (*RegisterShaderFromData) (const char *name, ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex);
-	void (*GetShaderImageDimensions) (qhandle_t h, int *width, int *height);
-	void (*GetShaderImageData) (qhandle_t h, ubyte *data);
-	qhandle_t (*GetSingleShader) (void);
 } refexport_t;
 
 //
@@ -133,115 +129,113 @@
 //
 typedef struct {
 	// print message on the local console
-	void	(QDECL *Printf)( int printLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void	FORMAT_PRINTF(2, 3) (QDECL *Printf)( printParm_t printLevel, const char *fmt, ... );
 
 	// abort the game
-	void	(QDECL *Error)( int errorLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void	NORETURN_PTR FORMAT_PRINTF(2, 3)(QDECL *Error)( errorParm_t errorLevel, const char *fmt, ... );
 
-	// RealMilliseconds should only be used for profiling, never
+	// milliseconds should only be used for profiling, never
 	// for anything game related.  Get time from the refdef
-	int		(*ScaledMilliseconds)( void );
-	int		(*RealMilliseconds) (void);
+	int		(*Milliseconds)( void );
+
+	int64_t	(*Microseconds)( void );
 
 	// stack based memory allocation for per-level things that
 	// won't be freed
 #ifdef HUNK_DEBUG
-	void	*(*Hunk_AllocDebug)( int size, ha_pref pref, char *label, char *file, int line );
+	void	*(*Hunk_AllocDebug)( size_t size, ha_pref pref, const char *label, const char *file, int line );
 #else
-	void	*(*Hunk_Alloc)( int size, ha_pref pref );
+	void	*(*Hunk_Alloc)( size_t size, ha_pref pref );
 #endif
-	void	*(*Hunk_AllocateTempMemory)( int size );
+	void	*(*Hunk_AllocateTempMemory)( size_t size );
 	void	(*Hunk_FreeTempMemory)( void *block );
 
 	// dynamic memory allocator for things that need to be freed
-	void	*(*Malloc)( int bytes );
+	void	*(*Malloc)( size_t bytes );
 	void	(*Free)( void *buf );
+	void	(*FreeAll)( void );
 
 	cvar_t	*(*Cvar_Get)( const char *name, const char *value, int flags );
 	void	(*Cvar_Set)( const char *name, const char *value );
 	void	(*Cvar_SetValue) (const char *name, float value);
-	void	(*Cvar_ForceReset) (const char *var_name);
-	cvar_t	*(*Cvar_FindVar) (const char *var_name);
-	void	(*Cvar_CheckRange)( cvar_t *cv, float minVal, float maxVal, qboolean shouldBeIntegral );
-	int		(*Cvar_VariableIntegerValue) (const char *var_name);
-	float	(*Cvar_VariableValue) (const char *var_name);
-	void	(*Cvar_VariableStringBuffer) (const char *var_name, char *buffer, int bufsize);
+	void	(*Cvar_CheckRange)( cvar_t *cv, const char *minVal, const char *maxVal, cvarValidator_t type );
 	void	(*Cvar_SetDescription)( cvar_t *cv, const char *description );
 
+	void	(*Cvar_SetGroup)( cvar_t *var, cvarGroup_t group );
+	int		(*Cvar_CheckGroup)( cvarGroup_t group );
+	void	(*Cvar_ResetGroup)( cvarGroup_t group, qboolean resetModifiedFlags );
+
+	void	(*Cvar_VariableStringBuffer)( const char *var_name, char *buffer, int bufsize );
+	const char *(*Cvar_VariableString)( const char *var_name );
+	int		(*Cvar_VariableIntegerValue)( const char *var_name );
+
 	void	(*Cmd_AddCommand)( const char *name, void(*cmd)(void) );
 	void	(*Cmd_RemoveCommand)( const char *name );
 
 	int		(*Cmd_Argc) (void);
-	char	*(*Cmd_Argv) (int i);
+	const char	*(*Cmd_Argv) (int i);
 
-	void	(*Cmd_ExecuteText) (int exec_when, const char *text);
+	void	(*Cmd_ExecuteText)( cbufExec_t exec_when, const char *text );
 
 	byte	*(*CM_ClusterPVS)(int cluster);
 
 	// visualization for debugging collision detection
 	void	(*CM_DrawDebugSurface)( void (*drawPoly)(int color, int numPoints, float *points) );
 
-	// a -1 return means the file does not exist
+	// a qfalse return means the file does not exist
 	// NULL can be passed for buf to just determine existence
-	int		(*FS_FileIsInPAK)( const char *name, int *pCheckSum );
-	long	(*FS_ReadFile)( const char *name, void **buf );
+	//int		(*FS_FileIsInPAK)( const char *name, int *pCheckSum );
+	int		(*FS_ReadFile)( const char *name, void **buf );
 	void	(*FS_FreeFile)( void *buf );
 	char **	(*FS_ListFiles)( const char *name, const char *extension, int *numfilesfound );
 	void	(*FS_FreeFileList)( char **filelist );
 	void	(*FS_WriteFile)( const char *qpath, const void *buffer, int size );
-	int		(*FS_Write) (const void *buffer, int len, fileHandle_t f);
 	qboolean (*FS_FileExists)( const char *file );
-	const char	*(*FS_FindSystemFile) (const char *file);
-	void	(*FS_FCloseFile) (fileHandle_t f);
-	fileHandle_t	(*FS_FOpenFileWrite) (const char *qpath );
 
 	// cinematic stuff
-	void	(*CIN_UploadCinematic)(int handle);
-	int		(*CIN_PlayCinematic)( const char *arg0, int xpos, int ypos, int width, int height, int bits);
-	e_status (*CIN_RunCinematic) (int handle);
-
-	void	(*CL_WriteAVIVideoFrame)(aviFileData_t *afd, const byte *buffer, int size);
-
-	// input event handling
-	void	(*IN_Init)( void *windowData );
-	void    (*IN_Shutdown)( void );
-	void    (*IN_Restart)( void );
-
-	// math
-	long    (*ftol)(float f);
-
-	// system stuff
-	void    (*Sys_SetEnv)( const char *name, const char *value );
-	void    (*Sys_GLimpSafeInit)( void );
-	void    (*Sys_GLimpInit)( void );
-	qboolean (*Sys_LowPhysicalMemory)( void );
-
-	// video recording stuff
-	qboolean *SplitVideo;
-
-	aviFileData_t *afdMain;
-	aviFileData_t *afdLeft;
-	aviFileData_t *afdRight;
-
-	aviFileData_t *afdDepth;
-	aviFileData_t *afdDepthLeft;
-	aviFileData_t *afdDepthRight;
-
-	GLfloat **Video_DepthBuffer;
-	byte **ExtraVideoBuffer;
-
-	// misc
-	mapNames_t *MapNames;
+	void	(*CIN_UploadCinematic)( int handle );
+	int		(*CIN_PlayCinematic)( const char *arg0, int xpos, int ypos, int width, int height, int bits );
+	e_status (*CIN_RunCinematic)( int handle );
+
+	void	(*CL_WriteAVIVideoFrame)( const byte *buffer, int size );
+
+	size_t	(*CL_SaveJPGToBuffer)( byte *buffer, size_t bufSize, int quality, int image_width, int image_height, byte *image_buffer, int padding );
+	void	(*CL_SaveJPG)( const char *filename, int quality, int image_width, int image_height, byte *image_buffer, int padding );
+	void	(*CL_LoadJPG)( const char *filename, unsigned char **pic, int *width, int *height );
+
+	qboolean (*CL_IsMinimized)( void );
+	void	(*CL_SetScaling)( float factor, int captureWidth, int captureHeight );
+
+	void	(*Sys_SetClipboardBitmap)( const byte *bitmap, int size );
+	qboolean(*Sys_LowPhysicalMemory)( void );
+
+	int		(*Com_RealTime)( qtime_t *qtime );
+
+	// platform-dependent functions
+	void(*GLimp_InitGamma)(glconfig_t *config);
+	void(*GLimp_SetGamma)(unsigned char red[256], unsigned char green[256], unsigned char blue[256]);
+
+	// OpenGL
+	void	(*GLimp_Init)( glconfig_t *config );
+	void	(*GLimp_Shutdown)( qboolean unloadDLL );
+	void	(*GLimp_EndFrame)( void );
+	void*	(*GL_GetProcAddress)( const char *name );
+
+	// Vulkan
+	void	(*VKimp_Init)( glconfig_t *config );
+	void	(*VKimp_Shutdown)( qboolean unloadDLL );
+	void*	(*VK_GetInstanceProcAddr)( VkInstance instance, const char *name );
+	qboolean (*VK_CreateSurface)( VkInstance instance, VkSurfaceKHR *pSurface );
 
-	qboolean sse2_supported;
 } refimport_t;
 
+extern	refimport_t	ri;
 
 // this is the only function actually exported at the linker level
 // If the module can't init to a valid rendering state, NULL will be
 // returned.
 #ifdef USE_RENDERER_DLOPEN
-typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t *rimp);
+typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t * rimp);
 #else
 refexport_t*GetRefAPI( int apiVersion, refimport_t *rimp );
 #endif

```

### `openarena-engine`  — sha256 `671ffae52de5...`, 8246 bytes

_Diff stat: +27 / -75 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_public.h	2026-04-16 20:02:25.237331000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_public.h	2026-04-16 22:48:25.932966000 +0100
@@ -23,16 +23,8 @@
 #define __TR_PUBLIC_H
 
 #include "tr_types.h"
-#include "../cgame/cg_camera.h"
-#include "../client/cl_avi.h"
 
-#ifdef USE_LOCAL_HEADERS
-  #include "SDL_opengl.h"
-#else
-  #include <SDL_opengl.h>
-#endif
-
-#define	REF_API_VERSION		601  // wolfcam don't know the point of this, but bumping anyway
+#define	REF_API_VERSION		8
 
 //
 // these are the functions exported by the refresh module
@@ -53,12 +45,9 @@
 	// and height, which can be used by the client to intelligently
 	// size display elements
 	void	(*BeginRegistration)( glconfig_t *config );
-	void (*GetGlConfig)(glconfig_t *config);
 	qhandle_t (*RegisterModel)( const char *name );
-	void (*GetModelName)( qhandle_t index, char *name, int sz );
 	qhandle_t (*RegisterSkin)( const char *name );
 	qhandle_t (*RegisterShader)( const char *name );
-	qhandle_t (*RegisterShaderLightMap)( const char *name, int lightmap );
 	qhandle_t (*RegisterShaderNoMip)( const char *name );
 	void	(*LoadWorld)( const char *name );
 
@@ -74,14 +63,15 @@
 	// Nothing is drawn until R_RenderScene is called.
 	void	(*ClearScene)( void );
 	void	(*AddRefEntityToScene)( const refEntity_t *re );
-	void	(*AddRefEntityPtrToScene)(refEntity_t *re);
-	void (*SetPathLines)(int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color);
-	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num, int lightmap );
-	int		(*LightForPoint)( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
+	void	(*AddPolyToScene)( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num );
+	int		(*LightForPoint)( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir );
 	void	(*AddLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
 	void	(*AddAdditiveLightToScene)( const vec3_t org, float intensity, float r, float g, float b );
 	void	(*RenderScene)( const refdef_t *fd );
 
+	void	(*LFX_ParticleEffect)( int effect, const vec3_t origin, const vec3_t velocity ); // leilei - particles
+	void	(*GetViewPosition)( vec3_t point ); 
+
 	void	(*SetColor)( const float *rgba );	// NULL = 1,1,1,1
 	void	(*DrawStretchPic) ( float x, float y, float w, float h, 
 		float s1, float t1, float s2, float t2, qhandle_t hShader );	// 0 = white
@@ -90,7 +80,7 @@
 	void	(*DrawStretchRaw) (int x, int y, int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
 	void	(*UploadCinematic) (int w, int h, int cols, int rows, const byte *data, int client, qboolean dirty);
 
-	void	(*BeginFrame)(stereoFrame_t stereoFrame, qboolean recordingVideo);
+	void	(*BeginFrame)( stereoFrame_t stereoFrame );
 
 	// if the pointers are not NULL, timing info will be returned
 	void	(*EndFrame)( int *frontEndMsec, int *backEndMsec );
@@ -107,25 +97,11 @@
 	void    (*A3D_RenderGeometry) (void *pVoidA3D, void *pVoidGeom, void *pVoidMat, void *pVoidGeomStatus);
 #endif
 	void	(*RegisterFont)(const char *fontName, int pointSize, fontInfo_t *font);
-	qboolean (*GetGlyphInfo) (fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut);
-	qboolean (*GetFontInfo) (int fontId, fontInfo_t *font);
-	void (*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime, qboolean keepLightmap, qboolean userSet);
-	void (*ClearRemappedShader)(const char *shaderName);
+	void	(*RemapShader)(const char *oldShader, const char *newShader, const char *offsetTime);
 	qboolean (*GetEntityToken)( char *buffer, int size );
 	qboolean (*inPVS)( const vec3_t p1, const vec3_t p2 );
 
-	void (*TakeVideoFrame)(aviFileData_t *afd, int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg, qboolean avi, qboolean tga, qboolean jpg, qboolean png, int picCount, char *givenFileName);
-
-	void (*BeginHud)(void);
-	void (*UpdateDof)(float viewFocus, float viewRadius);
-
-	void (*Get_Advertisements)(int *num, float *verts, char shaders[][MAX_QPATH]);
-	void (*ReplaceShaderImage)(qhandle_t h, const ubyte *data, int width, int height);
-
-	qhandle_t (*RegisterShaderFromData) (const char *name, ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex);
-	void (*GetShaderImageDimensions) (qhandle_t h, int *width, int *height);
-	void (*GetShaderImageData) (qhandle_t h, ubyte *data);
-	qhandle_t (*GetSingleShader) (void);
+	void (*TakeVideoFrame)( int h, int w, byte* captureBuffer, byte *encodeBuffer, qboolean motionJpeg );
 } refexport_t;
 
 //
@@ -133,15 +109,14 @@
 //
 typedef struct {
 	// print message on the local console
-	void	(QDECL *Printf)( int printLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void	(QDECL *Printf)( int printLevel, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 
 	// abort the game
-	void	(QDECL *Error)( int errorLevel, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void	(QDECL *Error)( int errorLevel, const char *fmt, ...) __attribute__ ((noreturn, format (printf, 2, 3)));
 
-	// RealMilliseconds should only be used for profiling, never
+	// milliseconds should only be used for profiling, never
 	// for anything game related.  Get time from the refdef
-	int		(*ScaledMilliseconds)( void );
-	int		(*RealMilliseconds) (void);
+	int		(*Milliseconds)( void );
 
 	// stack based memory allocation for per-level things that
 	// won't be freed
@@ -160,13 +135,9 @@
 	cvar_t	*(*Cvar_Get)( const char *name, const char *value, int flags );
 	void	(*Cvar_Set)( const char *name, const char *value );
 	void	(*Cvar_SetValue) (const char *name, float value);
-	void	(*Cvar_ForceReset) (const char *var_name);
-	cvar_t	*(*Cvar_FindVar) (const char *var_name);
 	void	(*Cvar_CheckRange)( cvar_t *cv, float minVal, float maxVal, qboolean shouldBeIntegral );
+
 	int		(*Cvar_VariableIntegerValue) (const char *var_name);
-	float	(*Cvar_VariableValue) (const char *var_name);
-	void	(*Cvar_VariableStringBuffer) (const char *var_name, char *buffer, int bufsize);
-	void	(*Cvar_SetDescription)( cvar_t *cv, const char *description );
 
 	void	(*Cmd_AddCommand)( const char *name, void(*cmd)(void) );
 	void	(*Cmd_RemoveCommand)( const char *name );
@@ -182,58 +153,39 @@
 	void	(*CM_DrawDebugSurface)( void (*drawPoly)(int color, int numPoints, float *points) );
 
 	// a -1 return means the file does not exist
-	// NULL can be passed for buf to just determine existence
+	// NULL can be passed for buf to just determine existance
 	int		(*FS_FileIsInPAK)( const char *name, int *pCheckSum );
-	long	(*FS_ReadFile)( const char *name, void **buf );
+	long		(*FS_ReadFile)( const char *name, void **buf );
 	void	(*FS_FreeFile)( void *buf );
 	char **	(*FS_ListFiles)( const char *name, const char *extension, int *numfilesfound );
 	void	(*FS_FreeFileList)( char **filelist );
 	void	(*FS_WriteFile)( const char *qpath, const void *buffer, int size );
-	int		(*FS_Write) (const void *buffer, int len, fileHandle_t f);
 	qboolean (*FS_FileExists)( const char *file );
-	const char	*(*FS_FindSystemFile) (const char *file);
-	void	(*FS_FCloseFile) (fileHandle_t f);
-	fileHandle_t	(*FS_FOpenFileWrite) (const char *qpath );
 
 	// cinematic stuff
 	void	(*CIN_UploadCinematic)(int handle);
 	int		(*CIN_PlayCinematic)( const char *arg0, int xpos, int ypos, int width, int height, int bits);
 	e_status (*CIN_RunCinematic) (int handle);
 
-	void	(*CL_WriteAVIVideoFrame)(aviFileData_t *afd, const byte *buffer, int size);
+	void	(*CL_WriteAVIVideoFrame)( const byte *buffer, int size );
 
 	// input event handling
+#if SDL_MAJOR_VERSION == 2
 	void	(*IN_Init)( void *windowData );
-	void    (*IN_Shutdown)( void );
-	void    (*IN_Restart)( void );
+#else
+	void	(*IN_Init)( void );
+#endif
+	void	(*IN_Shutdown)( void );
+	void	(*IN_Restart)( void );
 
 	// math
 	long    (*ftol)(float f);
 
 	// system stuff
-	void    (*Sys_SetEnv)( const char *name, const char *value );
-	void    (*Sys_GLimpSafeInit)( void );
-	void    (*Sys_GLimpInit)( void );
+	void	(*Sys_SetEnv)( const char *name, const char *value );
+	void	(*Sys_GLimpSafeInit)( void );
+	void	(*Sys_GLimpInit)( void );
 	qboolean (*Sys_LowPhysicalMemory)( void );
-
-	// video recording stuff
-	qboolean *SplitVideo;
-
-	aviFileData_t *afdMain;
-	aviFileData_t *afdLeft;
-	aviFileData_t *afdRight;
-
-	aviFileData_t *afdDepth;
-	aviFileData_t *afdDepthLeft;
-	aviFileData_t *afdDepthRight;
-
-	GLfloat **Video_DepthBuffer;
-	byte **ExtraVideoBuffer;
-
-	// misc
-	mapNames_t *MapNames;
-
-	qboolean sse2_supported;
 } refimport_t;
 
 
@@ -241,7 +193,7 @@
 // If the module can't init to a valid rendering state, NULL will be
 // returned.
 #ifdef USE_RENDERER_DLOPEN
-typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t *rimp);
+typedef	refexport_t* (QDECL *GetRefAPI_t) (int apiVersion, refimport_t * rimp);
 #else
 refexport_t*GetRefAPI( int apiVersion, refimport_t *rimp );
 #endif

```
