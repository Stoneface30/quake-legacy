# Diff: `code/server/sv_game.c`
**Canonical:** `wolfcamql-src` (sha256 `c35ee626ec6f...`, 28702 bytes)

## Variants

### `quake3-source`  — sha256 `dda52c608aec...`, 29008 bytes

_Diff stat: +46 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_game.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_game.c	2026-04-16 20:02:19.977635800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,10 +23,18 @@
 
 #include "server.h"
 
-#include "../botlib/botlib.h"
+#include "../game/botlib.h"
 
 botlib_export_t	*botlib_export;
 
+void SV_GameError( const char *string ) {
+	Com_Error( ERR_DROP, "%s", string );
+}
+
+void SV_GamePrint( const char *string ) {
+	Com_Printf( "%s", string );
+}
+
 // these functions must be used instead of pointer arithmetic, because
 // the game allocates gentities with private information after the server shared part
 int	SV_NumForGentity( sharedEntity_t *ent ) {
@@ -177,14 +185,17 @@
 {
 	int		leafnum;
 	int		cluster;
+	int		area1, area2;
 	byte	*mask;
 
 	leafnum = CM_PointLeafnum (p1);
 	cluster = CM_LeafCluster (leafnum);
+	area1 = CM_LeafArea (leafnum);
 	mask = CM_ClusterPVS (cluster);
 
 	leafnum = CM_PointLeafnum (p2);
 	cluster = CM_LeafCluster (leafnum);
+	area2 = CM_LeafArea (leafnum);
 
 	if ( mask && (!(mask[cluster>>3] & (1<<(cluster&7)) ) ) )
 		return qfalse;
@@ -211,7 +222,7 @@
 
 /*
 ==================
-SV_EntityContact
+SV_GameAreaEntities
 ==================
 */
 qboolean	SV_EntityContact( vec3_t mins, vec3_t maxs, const sharedEntity_t *gEnt, int capsule ) {
@@ -277,9 +288,14 @@
 //==============================================
 
 static int	FloatAsInt( float f ) {
-	floatint_t fi;
-	fi.f = f;
-	return fi.i;
+	union
+	{
+	    int i;
+	    float f;
+	} temp;
+	
+	temp.f = f;
+	return temp.i;
 }
 
 /*
@@ -289,13 +305,22 @@
 The module is making a system call
 ====================
 */
-intptr_t SV_GameSystemCalls( intptr_t *args ) {
+//rcg010207 - see my comments in VM_DllSyscall(), in qcommon/vm.c ...
+#if ((defined __linux__) && (defined __powerpc__))
+#define VMA(x) ((void *) args[x])
+#else
+#define	VMA(x) VM_ArgPtr(args[x])
+#endif
+
+#define	VMF(x)	((float *)args)[x]
+
+int SV_GameSystemCalls( int *args ) {
 	switch( args[0] ) {
 	case G_PRINT:
-		Com_Printf( "%s", (const char*)VMA(1) );
+		Com_Printf( "%s", VMA(1) );
 		return 0;
 	case G_ERROR:
-		Com_Error( ERR_DROP, "%s", (const char*)VMA(1) );
+		Com_Error( ERR_DROP, "%s", VMA(1) );
 		return 0;
 	case G_MILLISECONDS:
 		return Sys_Milliseconds();
@@ -306,7 +331,7 @@
 		Cvar_Update( VMA(1) );
 		return 0;
 	case G_CVAR_SET:
-		Cvar_SetSafe( (const char *)VMA(1), (const char *)VMA(2) );
+		Cvar_Set( (const char *)VMA(1), (const char *)VMA(2) );
 		return 0;
 	case G_CVAR_VARIABLE_INTEGER_VALUE:
 		return Cvar_VariableIntegerValue( (const char *)VMA(1) );
@@ -325,7 +350,7 @@
 	case G_FS_FOPEN_FILE:
 		return FS_FOpenFileByMode( VMA(1), VMA(2), args[3] );
 	case G_FS_READ:
-		FS_Read( VMA(1), args[2], args[3] );
+		FS_Read2( VMA(1), args[2], args[3] );
 		return 0;
 	case G_FS_WRITE:
 		FS_Write( VMA(1), args[2], args[3] );
@@ -424,14 +449,11 @@
 		BotImport_DebugPolygonDelete( args[1] );
 		return 0;
 	case G_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 	case G_SNAPVECTOR:
-		Q_SnapVector(VMA(1));
+		Sys_SnapVector( VMA(1) );
 		return 0;
 
-	case 114:  // acos
-		return Q_acos(VMF(1));
-
 		//====================================
 
 	case BOTLIB_SETUP:
@@ -468,13 +490,7 @@
 	case BOTLIB_GET_CONSOLE_MESSAGE:
 		return SV_BotGetConsoleMessage( args[1], VMA(2), args[3] );
 	case BOTLIB_USER_COMMAND:
-		{
-			int clientNum = args[1];
-
-			if ( clientNum >= 0 && clientNum < sv_maxclients->integer ) {
-				SV_ClientThink( &svs.clients[clientNum], VMA(2) );
-			}
-		}
+		SV_ClientThink( &svs.clients[args[1]], VMA(2) );
 		return 0;
 
 	case BOTLIB_AAS_BBOX_AREAS:
@@ -543,7 +559,7 @@
 
 	case BOTLIB_EA_ACTION:
 		botlib_export->ea.EA_Action( args[1], args[2] );
-		return 0;
+		break;
 	case BOTLIB_EA_GESTURE:
 		botlib_export->ea.EA_Gesture( args[1] );
 		return 0;
@@ -812,8 +828,7 @@
 		return 0;
 
 	case TRAP_STRNCPY:
-		strncpy( VMA(1), VMA(2), args[3] );
-		return args[1];
+		return (int)strncpy( VMA(1), VMA(2), args[3] );
 
 	case TRAP_SIN:
 		return FloatAsInt( sin( VMF(1) ) );
@@ -847,9 +862,9 @@
 
 
 	default:
-		Com_Error( ERR_DROP, "Bad game system trap: %ld", (long int) args[0] );
+		Com_Error( ERR_DROP, "Bad game system trap: %i", args[0] );
 	}
-	return 0;
+	return -1;
 }
 
 /*
@@ -891,7 +906,7 @@
 	
 	// use the current msec count for a random seed
 	// init for this gamestate
-	VM_Call (gvm, GAME_INIT, sv.time, Com_Milliseconds(), restart);
+	VM_Call( gvm, GAME_INIT, svs.time, Com_Milliseconds(), restart );
 }
 
 
@@ -910,8 +925,8 @@
 	VM_Call( gvm, GAME_SHUTDOWN, qtrue );
 
 	// do a restart instead of a free
-	gvm = VM_Restart(gvm, qtrue);
-	if ( !gvm ) {
+	gvm = VM_Restart( gvm );
+	if ( !gvm ) { // bk001212 - as done below
 		Com_Error( ERR_FATAL, "VM_Restart on game failed" );
 	}
 

```

### `ioquake3`  — sha256 `42e8337b43f0...`, 28637 bytes

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_game.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_game.c	2026-04-16 20:02:21.619760000 +0100
@@ -424,14 +424,11 @@
 		BotImport_DebugPolygonDelete( args[1] );
 		return 0;
 	case G_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 	case G_SNAPVECTOR:
 		Q_SnapVector(VMA(1));
 		return 0;
 
-	case 114:  // acos
-		return Q_acos(VMF(1));
-
 		//====================================
 
 	case BOTLIB_SETUP:

```

### `quake3e`  — sha256 `2155d48d52c2...`, 33934 bytes

_Diff stat: +245 / -74 lines_

_(full diff is 21014 bytes — see files directly)_

### `openarena-engine`  — sha256 `432412c11630...`, 28523 bytes

_Diff stat: +4 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_game.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_game.c	2026-04-16 22:48:25.936964600 +0100
@@ -325,7 +325,7 @@
 	case G_FS_FOPEN_FILE:
 		return FS_FOpenFileByMode( VMA(1), VMA(2), args[3] );
 	case G_FS_READ:
-		FS_Read( VMA(1), args[2], args[3] );
+		FS_Read2( VMA(1), args[2], args[3] );
 		return 0;
 	case G_FS_WRITE:
 		FS_Write( VMA(1), args[2], args[3] );
@@ -424,14 +424,11 @@
 		BotImport_DebugPolygonDelete( args[1] );
 		return 0;
 	case G_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 	case G_SNAPVECTOR:
 		Q_SnapVector(VMA(1));
 		return 0;
 
-	case 114:  // acos
-		return Q_acos(VMF(1));
-
 		//====================================
 
 	case BOTLIB_SETUP:
@@ -468,13 +465,7 @@
 	case BOTLIB_GET_CONSOLE_MESSAGE:
 		return SV_BotGetConsoleMessage( args[1], VMA(2), args[3] );
 	case BOTLIB_USER_COMMAND:
-		{
-			int clientNum = args[1];
-
-			if ( clientNum >= 0 && clientNum < sv_maxclients->integer ) {
-				SV_ClientThink( &svs.clients[clientNum], VMA(2) );
-			}
-		}
+		SV_ClientThink( &svs.clients[args[1]], VMA(2) );
 		return 0;
 
 	case BOTLIB_AAS_BBOX_AREAS:
@@ -828,7 +819,7 @@
 		return FloatAsInt( sqrt( VMF(1) ) );
 
 	case TRAP_MATRIXMULTIPLY:
-		MatrixMultiply( VMA(1), VMA(2), VMA(3) );
+		Q_MatrixMultiply( VMA(1), VMA(2), VMA(3) );
 		return 0;
 
 	case TRAP_ANGLEVECTORS:

```
