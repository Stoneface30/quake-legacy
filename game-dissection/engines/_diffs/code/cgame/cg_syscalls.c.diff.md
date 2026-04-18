# Diff: `code/cgame/cg_syscalls.c`
**Canonical:** `wolfcamql-src` (sha256 `674aff2ebdc7...`, 20268 bytes)

## Variants

### `quake3-source`  — sha256 `b4b00c4ada8a...`, 14274 bytes

_Diff stat: +50 / -301 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_syscalls.c	2026-04-16 20:02:25.155574800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\cgame\cg_syscalls.c	2026-04-16 20:02:19.886589000 +0100
@@ -1,4 +1,24 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Foobar; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_syscalls.c -- this file is only included when building a dll
 // cg_syscalls.asm is included instead when building a qvm
@@ -8,43 +28,30 @@
 
 #include "cg_local.h"
 
-#include "cg_syscalls.h"
+static int (QDECL *syscall)( int arg, ... ) = (int (QDECL *)( int, ...))-1;
 
 
-
-#ifdef CGAME_HARD_LINKED
-#define syscall cgame_syscall
-extern int cgame_syscall (int arg, ...);
-
-#else
-static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
-
-
-Q_EXPORT void dllEntry( intptr_t (QDECL  *syscallptr)( intptr_t arg,... ) ) {
+void dllEntry( int (QDECL  *syscallptr)( int arg,... ) ) {
 	syscall = syscallptr;
 }
-#endif
 
 
-static int PASSFLOAT( float x ) {
-	floatint_t fi;
-	fi.f = x;
-	return fi.i;
+int PASSFLOAT( float x ) {
+	float	floatTemp;
+	floatTemp = x;
+	return *(int *)&floatTemp;
 }
 
 void	trap_Print( const char *fmt ) {
 	syscall( CG_PRINT, fmt );
 }
 
-void trap_Error(const char *fmt)
-{
-	syscall(CG_ERROR, fmt);
-	// shut up GCC warning about returning functions, because we know better
-	exit(1);
+void	trap_Error( const char *fmt ) {
+	syscall( CG_ERROR, fmt );
 }
 
 int		trap_Milliseconds( void ) {
-	return syscall( CG_MILLISECONDS );
+	return syscall( CG_MILLISECONDS ); 
 }
 
 void	trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags ) {
@@ -63,11 +70,6 @@
 	syscall( CG_CVAR_VARIABLESTRINGBUFFER, var_name, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(CG_CVAR_EXISTS, var_name);
-}
-
 int		trap_Argc( void ) {
 	return syscall( CG_ARGC );
 }
@@ -104,10 +106,6 @@
 	syscall( CG_SENDCONSOLECOMMAND, text );
 }
 
-void	trap_SendConsoleCommandNow( const char *text ) {
-	syscall( CG_SENDCONSOLECOMMANDNOW, text );
-}
-
 void	trap_AddCommand( const char *cmdName ) {
 	syscall( CG_ADDCOMMAND, cmdName );
 }
@@ -178,14 +176,14 @@
 	syscall( CG_CM_TRANSFORMEDCAPSULETRACE, results, start, end, mins, maxs, model, brushmask, origin, angles );
 }
 
-int		trap_CM_MarkFragments( int numPoints, const vec3_t *points,
+int		trap_CM_MarkFragments( int numPoints, const vec3_t *points, 
 				const vec3_t projection,
 				int maxPoints, vec3_t pointBuffer,
 				int maxFragments, markFragment_t *fragmentBuffer ) {
 	return syscall( CG_CM_MARKFRAGMENTS, numPoints, points, projection, maxPoints, pointBuffer, maxFragments, fragmentBuffer );
 }
 
-void	trap_S_StartSound( const vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
+void	trap_S_StartSound( vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
 	syscall( CG_S_STARTSOUND, origin, entityNum, entchannel, sfx );
 }
 
@@ -225,11 +223,6 @@
 	syscall( CG_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-void trap_S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	syscall(CG_S_PRINTSFXFILENAME, sfx);
-}
-
 void	trap_R_LoadWorldMap( const char *mapname ) {
 	syscall( CG_R_LOADWORLDMAP, mapname );
 }
@@ -238,10 +231,6 @@
 	return syscall( CG_R_REGISTERMODEL, name );
 }
 
-void trap_R_GetModelName (qhandle_t model, char *modelName, size_t szModelName) {
-       syscall(CG_R_GETMODELNAME, model, modelName, szModelName);
-}
-
 qhandle_t trap_R_RegisterSkin( const char *name ) {
 	return syscall( CG_R_REGISTERSKIN, name );
 }
@@ -250,10 +239,6 @@
 	return syscall( CG_R_REGISTERSHADER, name );
 }
 
-qhandle_t trap_R_RegisterShaderLightMap( const char *name, int lightmap ) {
-	return syscall( CG_R_REGISTERSHADERLIGHTMAP, name, lightmap );
-}
-
 qhandle_t trap_R_RegisterShaderNoMip( const char *name ) {
 	return syscall( CG_R_REGISTERSHADERNOMIP, name );
 }
@@ -270,55 +255,20 @@
 	syscall( CG_R_ADDREFENTITYTOSCENE, re );
 }
 
-void trap_R_AddRefEntityPtrToScene (refEntity_t *re)
-{
-	syscall(CG_R_ADDREFENTITYPTRTOSCENE, re);
-}
-
-void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int lightmap ) {
-	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts, lightmap );
+void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts ) {
+	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts );
 }
 
 void	trap_R_AddPolysToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num ) {
 	syscall( CG_R_ADDPOLYSTOSCENE, hShader, numVerts, verts, num );
 }
 
-int		trap_R_LightForPoint( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
+int		trap_R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
 	return syscall( CG_R_LIGHTFORPOINT, point, ambientLight, directedLight, lightDir );
 }
 
 void	trap_R_AddLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
-	//refEntity_t re;
-
 	syscall( CG_R_ADDLIGHTTOSCENE, org, PASSFLOAT(intensity), PASSFLOAT(r), PASSFLOAT(g), PASSFLOAT(b) );
-
-#if 0  // testing..  take out
-
-	if (SC_Cvar_Get_Int("r_flares") > 1) {
-		return;
-	}
-
-	memset(&re, 0, sizeof(re));
-
-	VectorCopy(org, re.origin);
-	re.shaderTime = cg.time / 1000.0f;
-	re.reType = RT_SPRITE;
-	re.rotation = 0;
-	re.radius = 40;
-	re.customShader = trap_R_RegisterShader("flareShader");
-#if 0
-	re.shaderRGBA[0] = 0xff;
-	re.shaderRGBA[1] = 0xff;
-	re.shaderRGBA[2] = 0xff;
-	re.shaderRGBA[3] = 0xff;
-#endif
-	re.shaderRGBA[0] = 255.0 * r;
-	re.shaderRGBA[1] = 255.0 * g;
-	re.shaderRGBA[2] = 255.0 * b;
-	re.shaderRGBA[3] = 100;
-
-	CG_AddRefEntity(&re);
-#endif
 }
 
 void	trap_R_AddAdditiveLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
@@ -333,7 +283,7 @@
 	syscall( CG_R_SETCOLOR, rgba );
 }
 
-void	trap_R_DrawStretchPic( float x, float y, float w, float h,
+void	trap_R_DrawStretchPic( float x, float y, float w, float h, 
 							   float s1, float t1, float s2, float t2, qhandle_t hShader ) {
 	syscall( CG_R_DRAWSTRETCHPIC, PASSFLOAT(x), PASSFLOAT(y), PASSFLOAT(w), PASSFLOAT(h), PASSFLOAT(s1), PASSFLOAT(t1), PASSFLOAT(s2), PASSFLOAT(t2), hShader );
 }
@@ -342,18 +292,13 @@
 	syscall( CG_R_MODELBOUNDS, model, mins, maxs );
 }
 
-int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame,
+int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame, 
 					   float frac, const char *tagName ) {
 	return syscall( CG_R_LERPTAG, tag, mod, startFrame, endFrame, PASSFLOAT(frac), tagName );
 }
 
-void trap_R_RemapShader (const char *oldShader, const char *newShader, const char *timeOffset, qboolean keepLightmap, qboolean userSet) {
-	syscall(CG_R_REMAP_SHADER, oldShader, newShader, timeOffset, keepLightmap, userSet);
-}
-
-void trap_R_ClearRemappedShader (const char *shaderName)
-{
-	syscall(CG_R_CLEAR_REMAPPED_SHADER, shaderName);
+void	trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset ) {
+	syscall( CG_R_REMAP_SHADER, oldShader, newShader, timeOffset );
 }
 
 void		trap_GetGlconfig( glconfig_t *glconfig ) {
@@ -372,10 +317,6 @@
 	return syscall( CG_GETSNAPSHOT, snapshotNumber, snapshot );
 }
 
-qboolean	trap_PeekSnapshot( int snapshotNumber, snapshot_t *snapshot ) {
-	return syscall( CG_PEEKSNAPSHOT, snapshotNumber, snapshot );
-}
-
 qboolean	trap_GetServerCommand( int serverCommandNumber ) {
 	return syscall( CG_GETSERVERCOMMAND, serverCommandNumber );
 }
@@ -392,11 +333,11 @@
 	syscall( CG_SETUSERCMDVALUE, stateValue, PASSFLOAT(sensitivityScale) );
 }
 
-void		testPrintInt( const char *string, int i ) {
+void		testPrintInt( char *string, int i ) {
 	syscall( CG_TESTPRINTINT, string, i );
 }
 
-void		testPrintFloat( const char *string, float f ) {
+void		testPrintFloat( char *string, float f ) {
 	syscall( CG_TESTPRINTFLOAT, string, PASSFLOAT(f) );
 }
 
@@ -444,8 +385,8 @@
 	syscall( CG_S_STOPBACKGROUNDTRACK );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(CG_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( CG_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
@@ -456,7 +397,7 @@
 int trap_CIN_PlayCinematic( const char *arg0, int xpos, int ypos, int width, int height, int bits) {
   return syscall(CG_CIN_PLAYCINEMATIC, arg0, xpos, ypos, width, height, bits);
 }
-
+ 
 // stops playing the cinematic and ends it.  should always return FMV_EOF
 // cinematics must be stopped in reverse order of when they are started
 e_status trap_CIN_StopCinematic(int handle) {
@@ -468,20 +409,20 @@
 e_status trap_CIN_RunCinematic (int handle) {
   return syscall(CG_CIN_RUNCINEMATIC, handle);
 }
-
+ 
 
 // draws the current frame
 void trap_CIN_DrawCinematic (int handle) {
   syscall(CG_CIN_DRAWCINEMATIC, handle);
 }
-
+ 
 
 // allows you to resize the animation dynamically
 void trap_CIN_SetExtents (int handle, int x, int y, int w, int h) {
   syscall(CG_CIN_SETEXTENTS, handle, x, y, w, h);
 }
 
-
+/*
 qboolean trap_loadCamera( const char *name ) {
 	return syscall( CG_LOADCAMERA, name );
 }
@@ -490,10 +431,10 @@
 	syscall(CG_STARTCAMERA, time);
 }
 
-qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles, float *fov) {
-	return syscall( CG_GETCAMERAINFO, time, origin, angles, fov );
+qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles) {
+	return syscall( CG_GETCAMERAINFO, time, origin, angles );
 }
-
+*/
 
 qboolean trap_GetEntityToken( char *buffer, int bufferSize ) {
 	return syscall( CG_GET_ENTITY_TOKEN, buffer, bufferSize );
@@ -502,195 +443,3 @@
 qboolean trap_R_inPVS( const vec3_t p1, const vec3_t p2 ) {
 	return syscall( CG_R_INPVS, p1, p2 );
 }
-
-void trap_Get_Advertisements (int *num, float *verts, char shaders[][MAX_QPATH]) {
-	syscall(CG_GET_ADVERTISEMENTS, num, verts, shaders);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(CG_R_BEGIN_HUD);
-}
-
-void trap_R_UpdateDof (float viewFocus, float viewRadius)
-{
-	syscall(CG_R_UPDATE_DOF, PASSFLOAT(viewFocus), PASSFLOAT(viewRadius));
-}
-
-void trap_R_DrawConsoleLines (void)
-{
-	syscall(CG_DRAW_CONSOLE_LINES);
-}
-
-void trap_Key_GetBinding (int key, char *buffer)
-{
-	syscall(CG_KEY_GETBINDING, key, buffer);
-}
-
-int trap_GetLastExecutedServerCommand (void)
-{
-	return syscall(CG_GETLASTEXECUTEDSERVERCOMMAND);
-}
-
-qboolean trap_GetNextKiller (int us, int serverTime, int *killer, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTKILLER, us, serverTime, killer, foundServerTime, onlyOtherClient);
-}
-
-qboolean trap_GetNextVictim (int us, int serverTime, int *victim, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTVICTIM, us, serverTime, victim, foundServerTime, onlyOtherClient);
-}
-
-void trap_ReplaceShaderImage (qhandle_t h, const ubyte *data, int width, int height)
-{
-	syscall(CG_REPLACESHADERIMAGE, h, data, width, height);
-}
-
-qhandle_t trap_RegisterShaderFromData (const char *name, const ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex)
-{
-	return syscall(CG_REGISTERSHADERFROMDATA, name, data, width, height, mipmap, allowPicmip, wrapClampMode, lightmapIndex);
-}
-
-void trap_GetShaderImageDimensions (qhandle_t h, int *width, int *height)
-{
-	syscall(CG_GETSHADERIMAGEDIMENSIONS, h, width, height);
-}
-
-void trap_GetShaderImageData (qhandle_t h, ubyte *data)
-{
-	syscall(CG_GETSHADERIMAGEDATA, h, data);
-}
-
-void trap_CalcSpline (int step, float tension, float *out)
-{
-	syscall(CG_CALCSPLINE, step, PASSFLOAT(tension), out);
-}
-
-void trap_SetPathLines (int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color)
-{
-	syscall(CG_SETPATHLINES, numCameraPoints, cameraPoints, numSplinePoints, splinePoints, color);
-}
-
-int trap_GetGameStartTime (void)
-{
-	return syscall(CG_GETGAMESTARTTIME);
-}
-
-int trap_GetGameEndTime (void)
-{
-	return syscall(CG_GETGAMEENDTIME);
-}
-
-int trap_GetFirstServerTime (void)
-{
-	return syscall(CG_GETFIRSTSERVERTIME);
-}
-
-int trap_GetLastServerTime (void)
-{
-	return syscall(CG_GETLASTSERVERTIME);
-}
-
-#if 0
-void trap_AddAt (int serverTime, const char *clockTime, const char *command)
-{
-	syscall(CG_ADDAT, serverTime, clockTime, command);
-}
-#endif
-
-int trap_GetLegsAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETLEGSANIMSTARTTIME, entityNum);
-}
-
-int trap_GetTorsoAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETTORSOANIMSTARTTIME, entityNum);
-}
-
-void trap_autoWriteConfig (qboolean write)
-{
-	syscall(CG_AUTOWRITECONFIG, write);
-}
-
-int trap_GetItemPickupNumber (int pickupTime)
-{
-	return syscall(CG_GETITEMPICKUPNUMBER, pickupTime);
-}
-
-int trap_GetItemPickup (int pickupNumber, itemPickup_t *ip)
-{
-	return syscall(CG_GETITEMPICKUP, pickupNumber, ip);
-}
-
-qhandle_t trap_R_GetSingleShader (void)
-{
-	return syscall(CG_R_GETSINGLESHADER);
-}
-
-void trap_Get_Demo_Timeouts (int *numTimeouts, timeOut_t *timeOuts)
-{
-	syscall(CG_GET_DEMO_TIMEOUTS, numTimeouts, timeOuts);
-}
-
-int trap_GetNumPlayerInfos (void)
-{
-	return syscall(CG_GET_NUM_PLAYER_INFO);
-}
-
-void trap_GetExtraPlayerInfo (int num, char *modelName)
-{
-	syscall(CG_GET_EXTRA_PLAYER_INFO, num, modelName);
-}
-
-void trap_GetRealMapName (char *name, char *realName, size_t szRealName)
-{
-	syscall(CG_GET_REAL_MAP_NAME, name, realName, szRealName);
-}
-
-// ui
-qboolean trap_Key_GetOverstrikeMode (void)
-{
-	return syscall(CG_KEY_GETOVERSTRIKEMODE);
-}
-
-void trap_Key_SetOverstrikeMode (qboolean state)
-{
-	syscall(CG_KEY_SETOVERSTRIKEMODE, state);
-}
-
-void trap_Key_SetBinding (int keynum, const char *binding)
-{
-	syscall(CG_KEY_SETBINDING, keynum, binding);
-}
-
-void trap_Key_GetBindingBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_GETBINDINGBUF, keynum, buf, buflen);
-}
-
-void trap_Key_KeynumToStringBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_KEYNUMTOSTRINGBUF, keynum, buf, buflen);
-}
-
-qboolean trap_R_GetGlyphInfo (const fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut)
-{
-	return syscall(CG_R_GETGLYPHINFO, fontInfo, charValue, glyphOut);
-}
-
-qboolean trap_R_GetFontInfo (int fontId, fontInfo_t *font)
-{
-	return syscall(CG_R_GETFONTINFO, fontId, font);
-}
-
-void trap_GetRoundStartTimes (int *numRoundStarts, int *roundStarts)
-{
-	syscall(CG_GETROUNDSTARTTIMES, numRoundStarts, roundStarts);
-}
-
-qboolean trap_GetTeamSwitchTime (int clientNum, int startTime, int *teamSwitchTime)
-{
-	return syscall(CG_GETTEAMSWITCHTIME, clientNum, startTime, teamSwitchTime);
-}

```

### `openarena-engine`  — sha256 `358647364dc4...`, 14396 bytes
Also identical in: ioquake3

_Diff stat: +43 / -291 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_syscalls.c	2026-04-16 20:02:25.155574800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_syscalls.c	2026-04-16 22:48:25.728204000 +0100
@@ -1,4 +1,24 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_syscalls.c -- this file is only included when building a dll
 // cg_syscalls.asm is included instead when building a qvm
@@ -8,25 +28,15 @@
 
 #include "cg_local.h"
 
-#include "cg_syscalls.h"
-
-
-
-#ifdef CGAME_HARD_LINKED
-#define syscall cgame_syscall
-extern int cgame_syscall (int arg, ...);
-
-#else
 static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
 
 
 Q_EXPORT void dllEntry( intptr_t (QDECL  *syscallptr)( intptr_t arg,... ) ) {
 	syscall = syscallptr;
 }
-#endif
 
 
-static int PASSFLOAT( float x ) {
+int PASSFLOAT( float x ) {
 	floatint_t fi;
 	fi.f = x;
 	return fi.i;
@@ -44,7 +54,7 @@
 }
 
 int		trap_Milliseconds( void ) {
-	return syscall( CG_MILLISECONDS );
+	return syscall( CG_MILLISECONDS ); 
 }
 
 void	trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags ) {
@@ -63,11 +73,6 @@
 	syscall( CG_CVAR_VARIABLESTRINGBUFFER, var_name, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(CG_CVAR_EXISTS, var_name);
-}
-
 int		trap_Argc( void ) {
 	return syscall( CG_ARGC );
 }
@@ -104,10 +109,6 @@
 	syscall( CG_SENDCONSOLECOMMAND, text );
 }
 
-void	trap_SendConsoleCommandNow( const char *text ) {
-	syscall( CG_SENDCONSOLECOMMANDNOW, text );
-}
-
 void	trap_AddCommand( const char *cmdName ) {
 	syscall( CG_ADDCOMMAND, cmdName );
 }
@@ -178,14 +179,14 @@
 	syscall( CG_CM_TRANSFORMEDCAPSULETRACE, results, start, end, mins, maxs, model, brushmask, origin, angles );
 }
 
-int		trap_CM_MarkFragments( int numPoints, const vec3_t *points,
+int		trap_CM_MarkFragments( int numPoints, const vec3_t *points, 
 				const vec3_t projection,
 				int maxPoints, vec3_t pointBuffer,
 				int maxFragments, markFragment_t *fragmentBuffer ) {
 	return syscall( CG_CM_MARKFRAGMENTS, numPoints, points, projection, maxPoints, pointBuffer, maxFragments, fragmentBuffer );
 }
 
-void	trap_S_StartSound( const vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
+void	trap_S_StartSound( vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
 	syscall( CG_S_STARTSOUND, origin, entityNum, entchannel, sfx );
 }
 
@@ -225,11 +226,6 @@
 	syscall( CG_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-void trap_S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	syscall(CG_S_PRINTSFXFILENAME, sfx);
-}
-
 void	trap_R_LoadWorldMap( const char *mapname ) {
 	syscall( CG_R_LOADWORLDMAP, mapname );
 }
@@ -238,10 +234,6 @@
 	return syscall( CG_R_REGISTERMODEL, name );
 }
 
-void trap_R_GetModelName (qhandle_t model, char *modelName, size_t szModelName) {
-       syscall(CG_R_GETMODELNAME, model, modelName, szModelName);
-}
-
 qhandle_t trap_R_RegisterSkin( const char *name ) {
 	return syscall( CG_R_REGISTERSKIN, name );
 }
@@ -250,10 +242,6 @@
 	return syscall( CG_R_REGISTERSHADER, name );
 }
 
-qhandle_t trap_R_RegisterShaderLightMap( const char *name, int lightmap ) {
-	return syscall( CG_R_REGISTERSHADERLIGHTMAP, name, lightmap );
-}
-
 qhandle_t trap_R_RegisterShaderNoMip( const char *name ) {
 	return syscall( CG_R_REGISTERSHADERNOMIP, name );
 }
@@ -270,55 +258,20 @@
 	syscall( CG_R_ADDREFENTITYTOSCENE, re );
 }
 
-void trap_R_AddRefEntityPtrToScene (refEntity_t *re)
-{
-	syscall(CG_R_ADDREFENTITYPTRTOSCENE, re);
-}
-
-void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int lightmap ) {
-	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts, lightmap );
+void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts ) {
+	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts );
 }
 
 void	trap_R_AddPolysToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num ) {
 	syscall( CG_R_ADDPOLYSTOSCENE, hShader, numVerts, verts, num );
 }
 
-int		trap_R_LightForPoint( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
+int		trap_R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
 	return syscall( CG_R_LIGHTFORPOINT, point, ambientLight, directedLight, lightDir );
 }
 
 void	trap_R_AddLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
-	//refEntity_t re;
-
 	syscall( CG_R_ADDLIGHTTOSCENE, org, PASSFLOAT(intensity), PASSFLOAT(r), PASSFLOAT(g), PASSFLOAT(b) );
-
-#if 0  // testing..  take out
-
-	if (SC_Cvar_Get_Int("r_flares") > 1) {
-		return;
-	}
-
-	memset(&re, 0, sizeof(re));
-
-	VectorCopy(org, re.origin);
-	re.shaderTime = cg.time / 1000.0f;
-	re.reType = RT_SPRITE;
-	re.rotation = 0;
-	re.radius = 40;
-	re.customShader = trap_R_RegisterShader("flareShader");
-#if 0
-	re.shaderRGBA[0] = 0xff;
-	re.shaderRGBA[1] = 0xff;
-	re.shaderRGBA[2] = 0xff;
-	re.shaderRGBA[3] = 0xff;
-#endif
-	re.shaderRGBA[0] = 255.0 * r;
-	re.shaderRGBA[1] = 255.0 * g;
-	re.shaderRGBA[2] = 255.0 * b;
-	re.shaderRGBA[3] = 100;
-
-	CG_AddRefEntity(&re);
-#endif
 }
 
 void	trap_R_AddAdditiveLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
@@ -333,7 +286,7 @@
 	syscall( CG_R_SETCOLOR, rgba );
 }
 
-void	trap_R_DrawStretchPic( float x, float y, float w, float h,
+void	trap_R_DrawStretchPic( float x, float y, float w, float h, 
 							   float s1, float t1, float s2, float t2, qhandle_t hShader ) {
 	syscall( CG_R_DRAWSTRETCHPIC, PASSFLOAT(x), PASSFLOAT(y), PASSFLOAT(w), PASSFLOAT(h), PASSFLOAT(s1), PASSFLOAT(t1), PASSFLOAT(s2), PASSFLOAT(t2), hShader );
 }
@@ -342,18 +295,13 @@
 	syscall( CG_R_MODELBOUNDS, model, mins, maxs );
 }
 
-int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame,
+int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame, 
 					   float frac, const char *tagName ) {
 	return syscall( CG_R_LERPTAG, tag, mod, startFrame, endFrame, PASSFLOAT(frac), tagName );
 }
 
-void trap_R_RemapShader (const char *oldShader, const char *newShader, const char *timeOffset, qboolean keepLightmap, qboolean userSet) {
-	syscall(CG_R_REMAP_SHADER, oldShader, newShader, timeOffset, keepLightmap, userSet);
-}
-
-void trap_R_ClearRemappedShader (const char *shaderName)
-{
-	syscall(CG_R_CLEAR_REMAPPED_SHADER, shaderName);
+void	trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset ) {
+	syscall( CG_R_REMAP_SHADER, oldShader, newShader, timeOffset );
 }
 
 void		trap_GetGlconfig( glconfig_t *glconfig ) {
@@ -372,10 +320,6 @@
 	return syscall( CG_GETSNAPSHOT, snapshotNumber, snapshot );
 }
 
-qboolean	trap_PeekSnapshot( int snapshotNumber, snapshot_t *snapshot ) {
-	return syscall( CG_PEEKSNAPSHOT, snapshotNumber, snapshot );
-}
-
 qboolean	trap_GetServerCommand( int serverCommandNumber ) {
 	return syscall( CG_GETSERVERCOMMAND, serverCommandNumber );
 }
@@ -392,11 +336,11 @@
 	syscall( CG_SETUSERCMDVALUE, stateValue, PASSFLOAT(sensitivityScale) );
 }
 
-void		testPrintInt( const char *string, int i ) {
+void		testPrintInt( char *string, int i ) {
 	syscall( CG_TESTPRINTINT, string, i );
 }
 
-void		testPrintFloat( const char *string, float f ) {
+void		testPrintFloat( char *string, float f ) {
 	syscall( CG_TESTPRINTFLOAT, string, PASSFLOAT(f) );
 }
 
@@ -444,8 +388,8 @@
 	syscall( CG_S_STOPBACKGROUNDTRACK );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(CG_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( CG_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
@@ -456,7 +400,7 @@
 int trap_CIN_PlayCinematic( const char *arg0, int xpos, int ypos, int width, int height, int bits) {
   return syscall(CG_CIN_PLAYCINEMATIC, arg0, xpos, ypos, width, height, bits);
 }
-
+ 
 // stops playing the cinematic and ends it.  should always return FMV_EOF
 // cinematics must be stopped in reverse order of when they are started
 e_status trap_CIN_StopCinematic(int handle) {
@@ -468,20 +412,20 @@
 e_status trap_CIN_RunCinematic (int handle) {
   return syscall(CG_CIN_RUNCINEMATIC, handle);
 }
-
+ 
 
 // draws the current frame
 void trap_CIN_DrawCinematic (int handle) {
   syscall(CG_CIN_DRAWCINEMATIC, handle);
 }
-
+ 
 
 // allows you to resize the animation dynamically
 void trap_CIN_SetExtents (int handle, int x, int y, int w, int h) {
   syscall(CG_CIN_SETEXTENTS, handle, x, y, w, h);
 }
 
-
+/*
 qboolean trap_loadCamera( const char *name ) {
 	return syscall( CG_LOADCAMERA, name );
 }
@@ -490,10 +434,10 @@
 	syscall(CG_STARTCAMERA, time);
 }
 
-qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles, float *fov) {
-	return syscall( CG_GETCAMERAINFO, time, origin, angles, fov );
+qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles) {
+	return syscall( CG_GETCAMERAINFO, time, origin, angles );
 }
-
+*/
 
 qboolean trap_GetEntityToken( char *buffer, int bufferSize ) {
 	return syscall( CG_GET_ENTITY_TOKEN, buffer, bufferSize );
@@ -502,195 +446,3 @@
 qboolean trap_R_inPVS( const vec3_t p1, const vec3_t p2 ) {
 	return syscall( CG_R_INPVS, p1, p2 );
 }
-
-void trap_Get_Advertisements (int *num, float *verts, char shaders[][MAX_QPATH]) {
-	syscall(CG_GET_ADVERTISEMENTS, num, verts, shaders);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(CG_R_BEGIN_HUD);
-}
-
-void trap_R_UpdateDof (float viewFocus, float viewRadius)
-{
-	syscall(CG_R_UPDATE_DOF, PASSFLOAT(viewFocus), PASSFLOAT(viewRadius));
-}
-
-void trap_R_DrawConsoleLines (void)
-{
-	syscall(CG_DRAW_CONSOLE_LINES);
-}
-
-void trap_Key_GetBinding (int key, char *buffer)
-{
-	syscall(CG_KEY_GETBINDING, key, buffer);
-}
-
-int trap_GetLastExecutedServerCommand (void)
-{
-	return syscall(CG_GETLASTEXECUTEDSERVERCOMMAND);
-}
-
-qboolean trap_GetNextKiller (int us, int serverTime, int *killer, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTKILLER, us, serverTime, killer, foundServerTime, onlyOtherClient);
-}
-
-qboolean trap_GetNextVictim (int us, int serverTime, int *victim, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTVICTIM, us, serverTime, victim, foundServerTime, onlyOtherClient);
-}
-
-void trap_ReplaceShaderImage (qhandle_t h, const ubyte *data, int width, int height)
-{
-	syscall(CG_REPLACESHADERIMAGE, h, data, width, height);
-}
-
-qhandle_t trap_RegisterShaderFromData (const char *name, const ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex)
-{
-	return syscall(CG_REGISTERSHADERFROMDATA, name, data, width, height, mipmap, allowPicmip, wrapClampMode, lightmapIndex);
-}
-
-void trap_GetShaderImageDimensions (qhandle_t h, int *width, int *height)
-{
-	syscall(CG_GETSHADERIMAGEDIMENSIONS, h, width, height);
-}
-
-void trap_GetShaderImageData (qhandle_t h, ubyte *data)
-{
-	syscall(CG_GETSHADERIMAGEDATA, h, data);
-}
-
-void trap_CalcSpline (int step, float tension, float *out)
-{
-	syscall(CG_CALCSPLINE, step, PASSFLOAT(tension), out);
-}
-
-void trap_SetPathLines (int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color)
-{
-	syscall(CG_SETPATHLINES, numCameraPoints, cameraPoints, numSplinePoints, splinePoints, color);
-}
-
-int trap_GetGameStartTime (void)
-{
-	return syscall(CG_GETGAMESTARTTIME);
-}
-
-int trap_GetGameEndTime (void)
-{
-	return syscall(CG_GETGAMEENDTIME);
-}
-
-int trap_GetFirstServerTime (void)
-{
-	return syscall(CG_GETFIRSTSERVERTIME);
-}
-
-int trap_GetLastServerTime (void)
-{
-	return syscall(CG_GETLASTSERVERTIME);
-}
-
-#if 0
-void trap_AddAt (int serverTime, const char *clockTime, const char *command)
-{
-	syscall(CG_ADDAT, serverTime, clockTime, command);
-}
-#endif
-
-int trap_GetLegsAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETLEGSANIMSTARTTIME, entityNum);
-}
-
-int trap_GetTorsoAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETTORSOANIMSTARTTIME, entityNum);
-}
-
-void trap_autoWriteConfig (qboolean write)
-{
-	syscall(CG_AUTOWRITECONFIG, write);
-}
-
-int trap_GetItemPickupNumber (int pickupTime)
-{
-	return syscall(CG_GETITEMPICKUPNUMBER, pickupTime);
-}
-
-int trap_GetItemPickup (int pickupNumber, itemPickup_t *ip)
-{
-	return syscall(CG_GETITEMPICKUP, pickupNumber, ip);
-}
-
-qhandle_t trap_R_GetSingleShader (void)
-{
-	return syscall(CG_R_GETSINGLESHADER);
-}
-
-void trap_Get_Demo_Timeouts (int *numTimeouts, timeOut_t *timeOuts)
-{
-	syscall(CG_GET_DEMO_TIMEOUTS, numTimeouts, timeOuts);
-}
-
-int trap_GetNumPlayerInfos (void)
-{
-	return syscall(CG_GET_NUM_PLAYER_INFO);
-}
-
-void trap_GetExtraPlayerInfo (int num, char *modelName)
-{
-	syscall(CG_GET_EXTRA_PLAYER_INFO, num, modelName);
-}
-
-void trap_GetRealMapName (char *name, char *realName, size_t szRealName)
-{
-	syscall(CG_GET_REAL_MAP_NAME, name, realName, szRealName);
-}
-
-// ui
-qboolean trap_Key_GetOverstrikeMode (void)
-{
-	return syscall(CG_KEY_GETOVERSTRIKEMODE);
-}
-
-void trap_Key_SetOverstrikeMode (qboolean state)
-{
-	syscall(CG_KEY_SETOVERSTRIKEMODE, state);
-}
-
-void trap_Key_SetBinding (int keynum, const char *binding)
-{
-	syscall(CG_KEY_SETBINDING, keynum, binding);
-}
-
-void trap_Key_GetBindingBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_GETBINDINGBUF, keynum, buf, buflen);
-}
-
-void trap_Key_KeynumToStringBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_KEYNUMTOSTRINGBUF, keynum, buf, buflen);
-}
-
-qboolean trap_R_GetGlyphInfo (const fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut)
-{
-	return syscall(CG_R_GETGLYPHINFO, fontInfo, charValue, glyphOut);
-}
-
-qboolean trap_R_GetFontInfo (int fontId, fontInfo_t *font)
-{
-	return syscall(CG_R_GETFONTINFO, fontId, font);
-}
-
-void trap_GetRoundStartTimes (int *numRoundStarts, int *roundStarts)
-{
-	syscall(CG_GETROUNDSTARTTIMES, numRoundStarts, roundStarts);
-}
-
-qboolean trap_GetTeamSwitchTime (int clientNum, int startTime, int *teamSwitchTime)
-{
-	return syscall(CG_GETTEAMSWITCHTIME, clientNum, startTime, teamSwitchTime);
-}

```

### `openarena-gamecode`  — sha256 `276a325f2ceb...`, 14720 bytes

_Diff stat: +59 / -299 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_syscalls.c	2026-04-16 20:02:25.155574800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\cgame\cg_syscalls.c	2026-04-16 22:48:24.155331200 +0100
@@ -1,4 +1,24 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_syscalls.c -- this file is only included when building a dll
 // cg_syscalls.asm is included instead when building a qvm
@@ -8,43 +28,31 @@
 
 #include "cg_local.h"
 
-#include "cg_syscalls.h"
-
-
-
-#ifdef CGAME_HARD_LINKED
-#define syscall cgame_syscall
-extern int cgame_syscall (int arg, ...);
-
-#else
 static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
 
 
 Q_EXPORT void dllEntry( intptr_t (QDECL  *syscallptr)( intptr_t arg,... ) ) {
 	syscall = syscallptr;
 }
-#endif
 
 
-static int PASSFLOAT( float x ) {
-	floatint_t fi;
-	fi.f = x;
-	return fi.i;
+int PASSFLOAT( float x ) {
+	float	floatTemp;
+	floatTemp = x;
+	return *(int *)&floatTemp;
 }
 
 void	trap_Print( const char *fmt ) {
 	syscall( CG_PRINT, fmt );
 }
 
-void trap_Error(const char *fmt)
-{
-	syscall(CG_ERROR, fmt);
-	// shut up GCC warning about returning functions, because we know better
-	exit(1);
+void	trap_Error( const char *fmt ) {
+	syscall( CG_ERROR, fmt );
+        exit(CG_ERROR); //Will never occour but makes compiler happy
 }
 
 int		trap_Milliseconds( void ) {
-	return syscall( CG_MILLISECONDS );
+	return syscall( CG_MILLISECONDS ); 
 }
 
 void	trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags ) {
@@ -63,11 +71,6 @@
 	syscall( CG_CVAR_VARIABLESTRINGBUFFER, var_name, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(CG_CVAR_EXISTS, var_name);
-}
-
 int		trap_Argc( void ) {
 	return syscall( CG_ARGC );
 }
@@ -104,10 +107,6 @@
 	syscall( CG_SENDCONSOLECOMMAND, text );
 }
 
-void	trap_SendConsoleCommandNow( const char *text ) {
-	syscall( CG_SENDCONSOLECOMMANDNOW, text );
-}
-
 void	trap_AddCommand( const char *cmdName ) {
 	syscall( CG_ADDCOMMAND, cmdName );
 }
@@ -178,14 +177,14 @@
 	syscall( CG_CM_TRANSFORMEDCAPSULETRACE, results, start, end, mins, maxs, model, brushmask, origin, angles );
 }
 
-int		trap_CM_MarkFragments( int numPoints, const vec3_t *points,
+int		trap_CM_MarkFragments( int numPoints, const vec3_t *points, 
 				const vec3_t projection,
 				int maxPoints, vec3_t pointBuffer,
 				int maxFragments, markFragment_t *fragmentBuffer ) {
 	return syscall( CG_CM_MARKFRAGMENTS, numPoints, points, projection, maxPoints, pointBuffer, maxFragments, fragmentBuffer );
 }
 
-void	trap_S_StartSound( const vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
+void	trap_S_StartSound( vec3_t origin, int entityNum, int entchannel, sfxHandle_t sfx ) {
 	syscall( CG_S_STARTSOUND, origin, entityNum, entchannel, sfx );
 }
 
@@ -225,11 +224,6 @@
 	syscall( CG_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-void trap_S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	syscall(CG_S_PRINTSFXFILENAME, sfx);
-}
-
 void	trap_R_LoadWorldMap( const char *mapname ) {
 	syscall( CG_R_LOADWORLDMAP, mapname );
 }
@@ -238,10 +232,6 @@
 	return syscall( CG_R_REGISTERMODEL, name );
 }
 
-void trap_R_GetModelName (qhandle_t model, char *modelName, size_t szModelName) {
-       syscall(CG_R_GETMODELNAME, model, modelName, szModelName);
-}
-
 qhandle_t trap_R_RegisterSkin( const char *name ) {
 	return syscall( CG_R_REGISTERSKIN, name );
 }
@@ -250,10 +240,6 @@
 	return syscall( CG_R_REGISTERSHADER, name );
 }
 
-qhandle_t trap_R_RegisterShaderLightMap( const char *name, int lightmap ) {
-	return syscall( CG_R_REGISTERSHADERLIGHTMAP, name, lightmap );
-}
-
 qhandle_t trap_R_RegisterShaderNoMip( const char *name ) {
 	return syscall( CG_R_REGISTERSHADERNOMIP, name );
 }
@@ -270,55 +256,20 @@
 	syscall( CG_R_ADDREFENTITYTOSCENE, re );
 }
 
-void trap_R_AddRefEntityPtrToScene (refEntity_t *re)
-{
-	syscall(CG_R_ADDREFENTITYPTRTOSCENE, re);
-}
-
-void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int lightmap ) {
-	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts, lightmap );
+void	trap_R_AddPolyToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts ) {
+	syscall( CG_R_ADDPOLYTOSCENE, hShader, numVerts, verts );
 }
 
 void	trap_R_AddPolysToScene( qhandle_t hShader , int numVerts, const polyVert_t *verts, int num ) {
 	syscall( CG_R_ADDPOLYSTOSCENE, hShader, numVerts, verts, num );
 }
 
-int		trap_R_LightForPoint( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
+int		trap_R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir ) {
 	return syscall( CG_R_LIGHTFORPOINT, point, ambientLight, directedLight, lightDir );
 }
 
 void	trap_R_AddLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
-	//refEntity_t re;
-
 	syscall( CG_R_ADDLIGHTTOSCENE, org, PASSFLOAT(intensity), PASSFLOAT(r), PASSFLOAT(g), PASSFLOAT(b) );
-
-#if 0  // testing..  take out
-
-	if (SC_Cvar_Get_Int("r_flares") > 1) {
-		return;
-	}
-
-	memset(&re, 0, sizeof(re));
-
-	VectorCopy(org, re.origin);
-	re.shaderTime = cg.time / 1000.0f;
-	re.reType = RT_SPRITE;
-	re.rotation = 0;
-	re.radius = 40;
-	re.customShader = trap_R_RegisterShader("flareShader");
-#if 0
-	re.shaderRGBA[0] = 0xff;
-	re.shaderRGBA[1] = 0xff;
-	re.shaderRGBA[2] = 0xff;
-	re.shaderRGBA[3] = 0xff;
-#endif
-	re.shaderRGBA[0] = 255.0 * r;
-	re.shaderRGBA[1] = 255.0 * g;
-	re.shaderRGBA[2] = 255.0 * b;
-	re.shaderRGBA[3] = 100;
-
-	CG_AddRefEntity(&re);
-#endif
 }
 
 void	trap_R_AddAdditiveLightToScene( const vec3_t org, float intensity, float r, float g, float b ) {
@@ -333,7 +284,7 @@
 	syscall( CG_R_SETCOLOR, rgba );
 }
 
-void	trap_R_DrawStretchPic( float x, float y, float w, float h,
+void	trap_R_DrawStretchPic( float x, float y, float w, float h, 
 							   float s1, float t1, float s2, float t2, qhandle_t hShader ) {
 	syscall( CG_R_DRAWSTRETCHPIC, PASSFLOAT(x), PASSFLOAT(y), PASSFLOAT(w), PASSFLOAT(h), PASSFLOAT(s1), PASSFLOAT(t1), PASSFLOAT(s2), PASSFLOAT(t2), hShader );
 }
@@ -342,18 +293,13 @@
 	syscall( CG_R_MODELBOUNDS, model, mins, maxs );
 }
 
-int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame,
+int		trap_R_LerpTag( orientation_t *tag, clipHandle_t mod, int startFrame, int endFrame, 
 					   float frac, const char *tagName ) {
 	return syscall( CG_R_LERPTAG, tag, mod, startFrame, endFrame, PASSFLOAT(frac), tagName );
 }
 
-void trap_R_RemapShader (const char *oldShader, const char *newShader, const char *timeOffset, qboolean keepLightmap, qboolean userSet) {
-	syscall(CG_R_REMAP_SHADER, oldShader, newShader, timeOffset, keepLightmap, userSet);
-}
-
-void trap_R_ClearRemappedShader (const char *shaderName)
-{
-	syscall(CG_R_CLEAR_REMAPPED_SHADER, shaderName);
+void	trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset ) {
+	syscall( CG_R_REMAP_SHADER, oldShader, newShader, timeOffset );
 }
 
 void		trap_GetGlconfig( glconfig_t *glconfig ) {
@@ -372,10 +318,6 @@
 	return syscall( CG_GETSNAPSHOT, snapshotNumber, snapshot );
 }
 
-qboolean	trap_PeekSnapshot( int snapshotNumber, snapshot_t *snapshot ) {
-	return syscall( CG_PEEKSNAPSHOT, snapshotNumber, snapshot );
-}
-
 qboolean	trap_GetServerCommand( int serverCommandNumber ) {
 	return syscall( CG_GETSERVERCOMMAND, serverCommandNumber );
 }
@@ -392,11 +334,11 @@
 	syscall( CG_SETUSERCMDVALUE, stateValue, PASSFLOAT(sensitivityScale) );
 }
 
-void		testPrintInt( const char *string, int i ) {
+void		testPrintInt( char *string, int i ) {
 	syscall( CG_TESTPRINTINT, string, i );
 }
 
-void		testPrintFloat( const char *string, float f ) {
+void		testPrintFloat( char *string, float f ) {
 	syscall( CG_TESTPRINTFLOAT, string, PASSFLOAT(f) );
 }
 
@@ -444,19 +386,29 @@
 	syscall( CG_S_STOPBACKGROUNDTRACK );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(CG_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( CG_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
 	syscall( CG_SNAPVECTOR, v );
 }
 
+// leilei - particles!
+void	trap_R_LFX_ParticleEffect( int effect, const vec3_t origin, const vec3_t velocity ) {
+	syscall( CG_R_LFX_PARTICLEEFFECT, effect, origin, velocity );
+}
+
+// leilei - get viewmatrix from value
+void	trap_R_GetViewPosition( vec3_t point ) {
+	 syscall( CG_R_VIEWPOSITION, point );
+}
+
 // this returns a handle.  arg0 is the name in the format "idlogo.roq", set arg1 to NULL, alteredstates to qfalse (do not alter gamestate)
 int trap_CIN_PlayCinematic( const char *arg0, int xpos, int ypos, int width, int height, int bits) {
   return syscall(CG_CIN_PLAYCINEMATIC, arg0, xpos, ypos, width, height, bits);
 }
-
+ 
 // stops playing the cinematic and ends it.  should always return FMV_EOF
 // cinematics must be stopped in reverse order of when they are started
 e_status trap_CIN_StopCinematic(int handle) {
@@ -468,20 +420,20 @@
 e_status trap_CIN_RunCinematic (int handle) {
   return syscall(CG_CIN_RUNCINEMATIC, handle);
 }
-
+ 
 
 // draws the current frame
 void trap_CIN_DrawCinematic (int handle) {
   syscall(CG_CIN_DRAWCINEMATIC, handle);
 }
-
+ 
 
 // allows you to resize the animation dynamically
 void trap_CIN_SetExtents (int handle, int x, int y, int w, int h) {
   syscall(CG_CIN_SETEXTENTS, handle, x, y, w, h);
 }
 
-
+/*
 qboolean trap_loadCamera( const char *name ) {
 	return syscall( CG_LOADCAMERA, name );
 }
@@ -490,10 +442,10 @@
 	syscall(CG_STARTCAMERA, time);
 }
 
-qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles, float *fov) {
-	return syscall( CG_GETCAMERAINFO, time, origin, angles, fov );
+qboolean trap_getCameraInfo( int time, vec3_t *origin, vec3_t *angles) {
+	return syscall( CG_GETCAMERAINFO, time, origin, angles );
 }
-
+*/
 
 qboolean trap_GetEntityToken( char *buffer, int bufferSize ) {
 	return syscall( CG_GET_ENTITY_TOKEN, buffer, bufferSize );
@@ -502,195 +454,3 @@
 qboolean trap_R_inPVS( const vec3_t p1, const vec3_t p2 ) {
 	return syscall( CG_R_INPVS, p1, p2 );
 }
-
-void trap_Get_Advertisements (int *num, float *verts, char shaders[][MAX_QPATH]) {
-	syscall(CG_GET_ADVERTISEMENTS, num, verts, shaders);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(CG_R_BEGIN_HUD);
-}
-
-void trap_R_UpdateDof (float viewFocus, float viewRadius)
-{
-	syscall(CG_R_UPDATE_DOF, PASSFLOAT(viewFocus), PASSFLOAT(viewRadius));
-}
-
-void trap_R_DrawConsoleLines (void)
-{
-	syscall(CG_DRAW_CONSOLE_LINES);
-}
-
-void trap_Key_GetBinding (int key, char *buffer)
-{
-	syscall(CG_KEY_GETBINDING, key, buffer);
-}
-
-int trap_GetLastExecutedServerCommand (void)
-{
-	return syscall(CG_GETLASTEXECUTEDSERVERCOMMAND);
-}
-
-qboolean trap_GetNextKiller (int us, int serverTime, int *killer, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTKILLER, us, serverTime, killer, foundServerTime, onlyOtherClient);
-}
-
-qboolean trap_GetNextVictim (int us, int serverTime, int *victim, int *foundServerTime, qboolean onlyOtherClient)
-{
-	return syscall(CG_GETNEXTVICTIM, us, serverTime, victim, foundServerTime, onlyOtherClient);
-}
-
-void trap_ReplaceShaderImage (qhandle_t h, const ubyte *data, int width, int height)
-{
-	syscall(CG_REPLACESHADERIMAGE, h, data, width, height);
-}
-
-qhandle_t trap_RegisterShaderFromData (const char *name, const ubyte *data, int width, int height, qboolean mipmap, qboolean allowPicmip, int wrapClampMode, int lightmapIndex)
-{
-	return syscall(CG_REGISTERSHADERFROMDATA, name, data, width, height, mipmap, allowPicmip, wrapClampMode, lightmapIndex);
-}
-
-void trap_GetShaderImageDimensions (qhandle_t h, int *width, int *height)
-{
-	syscall(CG_GETSHADERIMAGEDIMENSIONS, h, width, height);
-}
-
-void trap_GetShaderImageData (qhandle_t h, ubyte *data)
-{
-	syscall(CG_GETSHADERIMAGEDATA, h, data);
-}
-
-void trap_CalcSpline (int step, float tension, float *out)
-{
-	syscall(CG_CALCSPLINE, step, PASSFLOAT(tension), out);
-}
-
-void trap_SetPathLines (int *numCameraPoints, cameraPoint_t *cameraPoints, int *numSplinePoints, vec3_t *splinePoints, const vec4_t color)
-{
-	syscall(CG_SETPATHLINES, numCameraPoints, cameraPoints, numSplinePoints, splinePoints, color);
-}
-
-int trap_GetGameStartTime (void)
-{
-	return syscall(CG_GETGAMESTARTTIME);
-}
-
-int trap_GetGameEndTime (void)
-{
-	return syscall(CG_GETGAMEENDTIME);
-}
-
-int trap_GetFirstServerTime (void)
-{
-	return syscall(CG_GETFIRSTSERVERTIME);
-}
-
-int trap_GetLastServerTime (void)
-{
-	return syscall(CG_GETLASTSERVERTIME);
-}
-
-#if 0
-void trap_AddAt (int serverTime, const char *clockTime, const char *command)
-{
-	syscall(CG_ADDAT, serverTime, clockTime, command);
-}
-#endif
-
-int trap_GetLegsAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETLEGSANIMSTARTTIME, entityNum);
-}
-
-int trap_GetTorsoAnimStartTime (int entityNum)
-{
-	return syscall(CG_GETTORSOANIMSTARTTIME, entityNum);
-}
-
-void trap_autoWriteConfig (qboolean write)
-{
-	syscall(CG_AUTOWRITECONFIG, write);
-}
-
-int trap_GetItemPickupNumber (int pickupTime)
-{
-	return syscall(CG_GETITEMPICKUPNUMBER, pickupTime);
-}
-
-int trap_GetItemPickup (int pickupNumber, itemPickup_t *ip)
-{
-	return syscall(CG_GETITEMPICKUP, pickupNumber, ip);
-}
-
-qhandle_t trap_R_GetSingleShader (void)
-{
-	return syscall(CG_R_GETSINGLESHADER);
-}
-
-void trap_Get_Demo_Timeouts (int *numTimeouts, timeOut_t *timeOuts)
-{
-	syscall(CG_GET_DEMO_TIMEOUTS, numTimeouts, timeOuts);
-}
-
-int trap_GetNumPlayerInfos (void)
-{
-	return syscall(CG_GET_NUM_PLAYER_INFO);
-}
-
-void trap_GetExtraPlayerInfo (int num, char *modelName)
-{
-	syscall(CG_GET_EXTRA_PLAYER_INFO, num, modelName);
-}
-
-void trap_GetRealMapName (char *name, char *realName, size_t szRealName)
-{
-	syscall(CG_GET_REAL_MAP_NAME, name, realName, szRealName);
-}
-
-// ui
-qboolean trap_Key_GetOverstrikeMode (void)
-{
-	return syscall(CG_KEY_GETOVERSTRIKEMODE);
-}
-
-void trap_Key_SetOverstrikeMode (qboolean state)
-{
-	syscall(CG_KEY_SETOVERSTRIKEMODE, state);
-}
-
-void trap_Key_SetBinding (int keynum, const char *binding)
-{
-	syscall(CG_KEY_SETBINDING, keynum, binding);
-}
-
-void trap_Key_GetBindingBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_GETBINDINGBUF, keynum, buf, buflen);
-}
-
-void trap_Key_KeynumToStringBuf (int keynum, char *buf, int buflen)
-{
-	syscall(CG_KEY_KEYNUMTOSTRINGBUF, keynum, buf, buflen);
-}
-
-qboolean trap_R_GetGlyphInfo (const fontInfo_t *fontInfo, int charValue, glyphInfo_t *glyphOut)
-{
-	return syscall(CG_R_GETGLYPHINFO, fontInfo, charValue, glyphOut);
-}
-
-qboolean trap_R_GetFontInfo (int fontId, fontInfo_t *font)
-{
-	return syscall(CG_R_GETFONTINFO, fontId, font);
-}
-
-void trap_GetRoundStartTimes (int *numRoundStarts, int *roundStarts)
-{
-	syscall(CG_GETROUNDSTARTTIMES, numRoundStarts, roundStarts);
-}
-
-qboolean trap_GetTeamSwitchTime (int clientNum, int startTime, int *teamSwitchTime)
-{
-	return syscall(CG_GETTEAMSWITCHTIME, clientNum, startTime, teamSwitchTime);
-}

```
