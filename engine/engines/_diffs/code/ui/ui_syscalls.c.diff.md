# Diff: `code/ui/ui_syscalls.c`
**Canonical:** `wolfcamql-src` (sha256 `f3047890e09c...`, 12681 bytes)

## Variants

### `quake3-source`  — sha256 `0c85a01411a0...`, 12105 bytes

_Diff stat: +15 / -42 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_syscalls.c	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_syscalls.c	2026-04-16 20:02:19.989149800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -28,26 +28,24 @@
 #error "Do not use in VM build"
 #endif
 
-static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
+static int (QDECL *syscall)( int arg, ... ) = (int (QDECL *)( int, ...))-1;
 
-Q_EXPORT void dllEntry( intptr_t (QDECL *syscallptr)( intptr_t arg,... ) ) {
+void dllEntry( int (QDECL *syscallptr)( int arg,... ) ) {
 	syscall = syscallptr;
 }
 
 int PASSFLOAT( float x ) {
-	floatint_t fi;
-	fi.f = x;
-	return fi.i;
+	float	floatTemp;
+	floatTemp = x;
+	return *(int *)&floatTemp;
 }
 
 void trap_Print( const char *string ) {
 	syscall( UI_PRINT, string );
 }
 
-void trap_Error(const char *string)
-{
-	syscall(UI_ERROR, string);
-	exit(1);
+void trap_Error( const char *string ) {
+	syscall( UI_ERROR, string );
 }
 
 int trap_Milliseconds( void ) {
@@ -67,9 +65,9 @@
 }
 
 float trap_Cvar_VariableValue( const char *var_name ) {
-	floatint_t fi;
-	fi.i = syscall( UI_CVAR_VARIABLEVALUE, var_name );
-	return fi.f;
+	int temp;
+	temp = syscall( UI_CVAR_VARIABLEVALUE, var_name );
+	return (*(float*)&temp);
 }
 
 void trap_Cvar_VariableStringBuffer( const char *var_name, char *buffer, int bufsize ) {
@@ -92,11 +90,6 @@
 	syscall( UI_CVAR_INFOSTRINGBUFFER, bit, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(UI_CVAR_EXISTS, var_name);
-}
-
 int trap_Argc( void ) {
 	return syscall( UI_ARGC );
 }
@@ -273,11 +266,11 @@
 	return syscall( UI_LAN_SERVERSTATUS, serverAddress, serverStatus, maxLen );
 }
 
-void trap_LAN_SaveCachedServers( void ) {
+void trap_LAN_SaveCachedServers() {
 	syscall( UI_LAN_SAVECACHEDSERVERS );
 }
 
-void trap_LAN_LoadCachedServers( void ) {
+void trap_LAN_LoadCachedServers() {
 	syscall( UI_LAN_LOADCACHEDSERVERS );
 }
 
@@ -361,8 +354,8 @@
 	syscall( UI_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-int trap_RealTime(qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(UI_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( UI_REAL_TIME, qtime );
 }
 
 // this returns a handle.  arg0 is the name in the format "idlogo.roq", set arg1 to NULL, alteredstates to qfalse (do not alter gamestate)
@@ -406,23 +399,3 @@
 void trap_SetPbClStatus( int status ) {
 	syscall( UI_SET_PBCLSTATUS, status );
 }
-
-void trap_OpenQuakeLiveDirectory (void)
-{
-	syscall(UI_OPEN_QUAKE_LIVE_DIRECTORY);
-}
-
-void trap_OpenWolfcamDirectory (void)
-{
-	syscall(UI_OPEN_WOLFCAM_DIRECTORY);
-}
-
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines)
-{
-	syscall(UI_DRAW_CONSOLE_LINES_OVER, xpos, ypos, numLines);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(UI_R_BEGIN_HUD);
-}

```

### `openarena-engine`  — sha256 `b8d6d73fe707...`, 12232 bytes
Also identical in: ioquake3

_Diff stat: +3 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_syscalls.c	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_syscalls.c	2026-04-16 22:48:25.961607400 +0100
@@ -47,6 +47,7 @@
 void trap_Error(const char *string)
 {
 	syscall(UI_ERROR, string);
+	// shut up GCC warning about returning functions, because we know better
 	exit(1);
 }
 
@@ -92,11 +93,6 @@
 	syscall( UI_CVAR_INFOSTRINGBUFFER, bit, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(UI_CVAR_EXISTS, var_name);
-}
-
 int trap_Argc( void ) {
 	return syscall( UI_ARGC );
 }
@@ -361,8 +357,8 @@
 	syscall( UI_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-int trap_RealTime(qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(UI_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( UI_REAL_TIME, qtime );
 }
 
 // this returns a handle.  arg0 is the name in the format "idlogo.roq", set arg1 to NULL, alteredstates to qfalse (do not alter gamestate)
@@ -406,23 +402,3 @@
 void trap_SetPbClStatus( int status ) {
 	syscall( UI_SET_PBCLSTATUS, status );
 }
-
-void trap_OpenQuakeLiveDirectory (void)
-{
-	syscall(UI_OPEN_QUAKE_LIVE_DIRECTORY);
-}
-
-void trap_OpenWolfcamDirectory (void)
-{
-	syscall(UI_OPEN_WOLFCAM_DIRECTORY);
-}
-
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines)
-{
-	syscall(UI_DRAW_CONSOLE_LINES_OVER, xpos, ypos, numLines);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(UI_R_BEGIN_HUD);
-}

```

### `openarena-gamecode`  — sha256 `ad3431366f3d...`, 12432 bytes

_Diff stat: +23 / -43 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_syscalls.c	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\ui\ui_syscalls.c	2026-04-16 22:48:24.216591700 +0100
@@ -30,24 +30,29 @@
 
 static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
 
-Q_EXPORT void dllEntry( intptr_t (QDECL *syscallptr)( intptr_t arg,... ) ) {
+Q_EXPORT void dllEntry( long (QDECL *syscallptr)( long arg,... ) ) {
 	syscall = syscallptr;
 }
 
+//static intptr_t (QDECL *syscall)( intptr_t arg, ... ) = (intptr_t (QDECL *)( intptr_t, ...))-1;
+
+//void dllEntry( intptr_t (QDECL *syscallptr)( intptr_t arg,... ) ) {
+	//syscall = syscallptr;
+//}
+
 int PASSFLOAT( float x ) {
-	floatint_t fi;
-	fi.f = x;
-	return fi.i;
+	float	floatTemp;
+	floatTemp = x;
+	return *(int *)&floatTemp;
 }
 
 void trap_Print( const char *string ) {
 	syscall( UI_PRINT, string );
 }
 
-void trap_Error(const char *string)
-{
-	syscall(UI_ERROR, string);
-	exit(1);
+void trap_Error( const char *string ) {
+	syscall( UI_ERROR, string );
+	exit(UI_ERROR); //Will never occour but makes compiler happy
 }
 
 int trap_Milliseconds( void ) {
@@ -67,9 +72,9 @@
 }
 
 float trap_Cvar_VariableValue( const char *var_name ) {
-	floatint_t fi;
-	fi.i = syscall( UI_CVAR_VARIABLEVALUE, var_name );
-	return fi.f;
+	int temp;
+	temp = syscall( UI_CVAR_VARIABLEVALUE, var_name );
+	return (*(float*)&temp);
 }
 
 void trap_Cvar_VariableStringBuffer( const char *var_name, char *buffer, int bufsize ) {
@@ -92,11 +97,6 @@
 	syscall( UI_CVAR_INFOSTRINGBUFFER, bit, buffer, bufsize );
 }
 
-qboolean trap_Cvar_Exists (const char *var_name)
-{
-	return syscall(UI_CVAR_EXISTS, var_name);
-}
-
 int trap_Argc( void ) {
 	return syscall( UI_ARGC );
 }
@@ -361,37 +361,37 @@
 	syscall( UI_S_STARTBACKGROUNDTRACK, intro, loop );
 }
 
-int trap_RealTime(qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(UI_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime(qtime_t *qtime) {
+	return syscall( UI_REAL_TIME, qtime );
 }
 
 // this returns a handle.  arg0 is the name in the format "idlogo.roq", set arg1 to NULL, alteredstates to qfalse (do not alter gamestate)
 int trap_CIN_PlayCinematic( const char *arg0, int xpos, int ypos, int width, int height, int bits) {
-  return syscall(UI_CIN_PLAYCINEMATIC, arg0, xpos, ypos, width, height, bits);
+	return syscall(UI_CIN_PLAYCINEMATIC, arg0, xpos, ypos, width, height, bits);
 }
  
 // stops playing the cinematic and ends it.  should always return FMV_EOF
 // cinematics must be stopped in reverse order of when they are started
 e_status trap_CIN_StopCinematic(int handle) {
-  return syscall(UI_CIN_STOPCINEMATIC, handle);
+	return syscall(UI_CIN_STOPCINEMATIC, handle);
 }
 
 
 // will run a frame of the cinematic but will not draw it.  Will return FMV_EOF if the end of the cinematic has been reached.
 e_status trap_CIN_RunCinematic (int handle) {
-  return syscall(UI_CIN_RUNCINEMATIC, handle);
+	return syscall(UI_CIN_RUNCINEMATIC, handle);
 }
  
 
 // draws the current frame
 void trap_CIN_DrawCinematic (int handle) {
-  syscall(UI_CIN_DRAWCINEMATIC, handle);
+	syscall(UI_CIN_DRAWCINEMATIC, handle);
 }
  
 
 // allows you to resize the animation dynamically
 void trap_CIN_SetExtents (int handle, int x, int y, int w, int h) {
-  syscall(UI_CIN_SETEXTENTS, handle, x, y, w, h);
+	syscall(UI_CIN_SETEXTENTS, handle, x, y, w, h);
 }
 
 
@@ -406,23 +406,3 @@
 void trap_SetPbClStatus( int status ) {
 	syscall( UI_SET_PBCLSTATUS, status );
 }
-
-void trap_OpenQuakeLiveDirectory (void)
-{
-	syscall(UI_OPEN_QUAKE_LIVE_DIRECTORY);
-}
-
-void trap_OpenWolfcamDirectory (void)
-{
-	syscall(UI_OPEN_WOLFCAM_DIRECTORY);
-}
-
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines)
-{
-	syscall(UI_DRAW_CONSOLE_LINES_OVER, xpos, ypos, numLines);
-}
-
-void trap_R_BeginHud (void)
-{
-	syscall(UI_R_BEGIN_HUD);
-}

```
