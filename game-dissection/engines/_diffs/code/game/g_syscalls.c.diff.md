# Diff: `code/game/g_syscalls.c`
**Canonical:** `wolfcamql-src` (sha256 `3d5d0b24ef10...`, 26020 bytes)

## Variants

### `quake3-source`  — sha256 `7d968854d14b...`, 25947 bytes

_Diff stat: +26 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_syscalls.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_syscalls.c	2026-04-16 20:02:19.910572800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -28,27 +28,25 @@
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
 
-void	trap_Print( const char *text ) {
-	syscall( G_PRINT, text );
+void	trap_Printf( const char *fmt ) {
+	syscall( G_PRINT, fmt );
 }
 
-void trap_Error( const char *text )
-{
-	syscall( G_ERROR, text );
-	exit(1);
+void	trap_Error( const char *fmt ) {
+	syscall( G_ERROR, fmt );
 }
 
 int		trap_Milliseconds( void ) {
@@ -221,12 +219,13 @@
 	syscall( G_DEBUG_POLYGON_DELETE, id );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(G_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime( qtime_t *qtime ) {
+	return syscall( G_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
 	syscall( G_SNAPVECTOR, v );
+	return;
 }
 
 // BotLib traps start here
@@ -291,9 +290,9 @@
 }
 
 float trap_AAS_Time(void) {
-	floatint_t fi;
-	fi.i = syscall( BOTLIB_AAS_TIME );
-	return fi.f;
+	int temp;
+	temp = syscall( BOTLIB_AAS_TIME );
+	return (*(float*)&temp);
 }
 
 int trap_AAS_PointAreaNum(vec3_t point) {
@@ -477,15 +476,15 @@
 }
 
 float trap_Characteristic_Float(int character, int index) {
-	floatint_t fi;
-	fi.i = syscall( BOTLIB_AI_CHARACTERISTIC_FLOAT, character, index );
-	return fi.f;
+	int temp;
+	temp = syscall( BOTLIB_AI_CHARACTERISTIC_FLOAT, character, index );
+	return (*(float*)&temp);
 }
 
 float trap_Characteristic_BFloat(int character, int index, float min, float max) {
-	floatint_t fi;
-	fi.i = syscall( BOTLIB_AI_CHARACTERISTIC_BFLOAT, character, index, PASSFLOAT(min), PASSFLOAT(max) );
-	return fi.f;
+	int temp;
+	temp = syscall( BOTLIB_AI_CHARACTERISTIC_BFLOAT, character, index, PASSFLOAT(min), PASSFLOAT(max) );
+	return (*(float*)&temp);
 }
 
 int trap_Characteristic_Integer(int character, int index) {
@@ -653,9 +652,9 @@
 }
 
 float trap_BotAvoidGoalTime(int goalstate, int number) {
-	floatint_t fi;
-	fi.i = syscall( BOTLIB_AI_AVOID_GOAL_TIME, goalstate, number );
-	return fi.f;
+	int temp;
+	temp = syscall( BOTLIB_AI_AVOID_GOAL_TIME, goalstate, number );
+	return (*(float*)&temp);
 }
 
 void trap_BotSetAvoidGoalTime(int goalstate, int number, float avoidtime) {
@@ -687,7 +686,7 @@
 }
 
 void trap_BotMutateGoalFuzzyLogic(int goalstate, float range) {
-	syscall( BOTLIB_AI_MUTATE_GOAL_FUZZY_LOGIC, goalstate, PASSFLOAT(range) );
+	syscall( BOTLIB_AI_MUTATE_GOAL_FUZZY_LOGIC, goalstate, range );
 }
 
 int trap_BotAllocGoalState(int state) {

```

### `ioquake3`  — sha256 `2bbc01beb93a...`, 26049 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_syscalls.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_syscalls.c	2026-04-16 20:02:21.547849900 +0100
@@ -48,6 +48,7 @@
 void trap_Error( const char *text )
 {
 	syscall( G_ERROR, text );
+	// shut up GCC warning about returning functions, because we know better
 	exit(1);
 }
 
@@ -221,8 +222,8 @@
 	syscall( G_DEBUG_POLYGON_DELETE, id );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(G_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime( qtime_t *qtime ) {
+	return syscall( G_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {

```

### `openarena-engine`  — sha256 `713b1b47e8a5...`, 26038 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_syscalls.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_syscalls.c	2026-04-16 22:48:25.751046300 +0100
@@ -48,6 +48,7 @@
 void trap_Error( const char *text )
 {
 	syscall( G_ERROR, text );
+	// shut up GCC warning about returning functions, because we know better
 	exit(1);
 }
 
@@ -221,8 +222,8 @@
 	syscall( G_DEBUG_POLYGON_DELETE, id );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(G_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime( qtime_t *qtime ) {
+	return syscall( G_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
@@ -687,7 +688,7 @@
 }
 
 void trap_BotMutateGoalFuzzyLogic(int goalstate, float range) {
-	syscall( BOTLIB_AI_MUTATE_GOAL_FUZZY_LOGIC, goalstate, PASSFLOAT(range) );
+	syscall( BOTLIB_AI_MUTATE_GOAL_FUZZY_LOGIC, goalstate, range );
 }
 
 int trap_BotAllocGoalState(int state) {

```

### `openarena-gamecode`  — sha256 `1cfad0d50e49...`, 26034 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_syscalls.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_syscalls.c	2026-04-16 22:48:24.175987200 +0100
@@ -41,14 +41,13 @@
 	return fi.i;
 }
 
-void	trap_Print( const char *text ) {
-	syscall( G_PRINT, text );
+void	trap_Printf( const char *fmt ) {
+	syscall( G_PRINT, fmt );
 }
 
-void trap_Error( const char *text )
-{
-	syscall( G_ERROR, text );
-	exit(1);
+void	trap_Error( const char *fmt ) {
+	syscall( G_ERROR, fmt );
+        exit(0); //Will never be executed. Makes compiler happy
 }
 
 int		trap_Milliseconds( void ) {
@@ -221,12 +220,13 @@
 	syscall( G_DEBUG_POLYGON_DELETE, id );
 }
 
-int trap_RealTime (qtime_t *qtime, qboolean now, int convertTime) {
-	return syscall(G_REAL_TIME, qtime, now, convertTime);
+int trap_RealTime( qtime_t *qtime ) {
+	return syscall( G_REAL_TIME, qtime );
 }
 
 void trap_SnapVector( float *v ) {
 	syscall( G_SNAPVECTOR, v );
+	return;
 }
 
 // BotLib traps start here

```
