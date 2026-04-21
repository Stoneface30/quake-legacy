# Diff: `code/client/cl_ui.c`
**Canonical:** `wolfcamql-src` (sha256 `59db7d0d5ccc...`, 26715 bytes)

## Variants

### `quake3-source`  — sha256 `cc14739b1aa9...`, 27234 bytes

_Diff stat: +167 / -131 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_ui.c	2026-04-16 20:02:25.174216300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\cl_ui.c	2026-04-16 20:02:19.892591600 +0100
@@ -15,15 +15,14 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
 #include "client.h"
-#include "keys.h"
 
-#include "../botlib/botlib.h"
+#include "../game/botlib.h"
 
 extern	botlib_export_t	*botlib_export;
 
@@ -36,12 +35,11 @@
 */
 static void GetClientState( uiClientState_t *state ) {
 	state->connectPacketCount = clc.connectPacketCount;
-	state->connState = clc.state;
-	Q_strncpyz( state->servername, clc.servername, sizeof( state->servername ) );
+	state->connState = cls.state;
+	Q_strncpyz( state->servername, cls.servername, sizeof( state->servername ) );
 	Q_strncpyz( state->updateInfoString, cls.updateInfoString, sizeof( state->updateInfoString ) );
 	Q_strncpyz( state->messageString, clc.serverMessage, sizeof( state->messageString ) );
 	state->clientNum = cl.snap.ps.clientNum;
-	state->demoplaying = clc.demoplaying;
 }
 
 /*
@@ -49,20 +47,22 @@
 LAN_LoadCachedServers
 ====================
 */
-void LAN_LoadCachedServers( void ) {
+void LAN_LoadCachedServers( ) {
 	int size;
 	fileHandle_t fileIn;
-	cls.numglobalservers = cls.numfavoriteservers = 0;
+	cls.numglobalservers = cls.nummplayerservers = cls.numfavoriteservers = 0;
 	cls.numGlobalServerAddresses = 0;
-	if (FS_BaseDir_FOpenFileRead("servercache.dat", &fileIn)) {
+	if (FS_SV_FOpenFileRead("servercache.dat", &fileIn)) {
 		FS_Read(&cls.numglobalservers, sizeof(int), fileIn);
+		FS_Read(&cls.nummplayerservers, sizeof(int), fileIn);
 		FS_Read(&cls.numfavoriteservers, sizeof(int), fileIn);
 		FS_Read(&size, sizeof(int), fileIn);
-		if (size == sizeof(cls.globalServers) + sizeof(cls.favoriteServers)) {
+		if (size == sizeof(cls.globalServers) + sizeof(cls.favoriteServers) + sizeof(cls.mplayerServers)) {
 			FS_Read(&cls.globalServers, sizeof(cls.globalServers), fileIn);
+			FS_Read(&cls.mplayerServers, sizeof(cls.mplayerServers), fileIn);
 			FS_Read(&cls.favoriteServers, sizeof(cls.favoriteServers), fileIn);
 		} else {
-			cls.numglobalservers = cls.numfavoriteservers = 0;
+			cls.numglobalservers = cls.nummplayerservers = cls.numfavoriteservers = 0;
 			cls.numGlobalServerAddresses = 0;
 		}
 		FS_FCloseFile(fileIn);
@@ -74,14 +74,16 @@
 LAN_SaveServersToCache
 ====================
 */
-void LAN_SaveServersToCache( void ) {
+void LAN_SaveServersToCache( ) {
 	int size;
-	fileHandle_t fileOut = FS_BaseDir_FOpenFileWrite_HomeState("servercache.dat");
+	fileHandle_t fileOut = FS_SV_FOpenFileWrite("servercache.dat");
 	FS_Write(&cls.numglobalservers, sizeof(int), fileOut);
+	FS_Write(&cls.nummplayerservers, sizeof(int), fileOut);
 	FS_Write(&cls.numfavoriteservers, sizeof(int), fileOut);
-	size = sizeof(cls.globalServers) + sizeof(cls.favoriteServers);
+	size = sizeof(cls.globalServers) + sizeof(cls.favoriteServers) + sizeof(cls.mplayerServers);
 	FS_Write(&size, sizeof(int), fileOut);
 	FS_Write(&cls.globalServers, sizeof(cls.globalServers), fileOut);
+	FS_Write(&cls.mplayerServers, sizeof(cls.mplayerServers), fileOut);
 	FS_Write(&cls.favoriteServers, sizeof(cls.favoriteServers), fileOut);
 	FS_FCloseFile(fileOut);
 }
@@ -102,7 +104,10 @@
 			servers = &cls.localServers[0];
 			count = MAX_OTHER_SERVERS;
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			servers = &cls.mplayerServers[0];
+			count = MAX_OTHER_SERVERS;
+			break;
 		case AS_GLOBAL :
 			servers = &cls.globalServers[0];
 			count = MAX_GLOBAL_SERVERS;
@@ -129,14 +134,17 @@
 	netadr_t adr;
 	serverInfo_t *servers = NULL;
 	max = MAX_OTHER_SERVERS;
-	count = NULL;
+	count = 0;
 
 	switch (source) {
 		case AS_LOCAL :
 			count = &cls.numlocalservers;
 			servers = &cls.localServers[0];
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			count = &cls.nummplayerservers;
+			servers = &cls.mplayerServers[0];
+			break;
 		case AS_GLOBAL :
 			max = MAX_GLOBAL_SERVERS;
 			count = &cls.numglobalservers;
@@ -148,7 +156,7 @@
 			break;
 	}
 	if (servers && *count < max) {
-		NET_StringToAdr( address, &adr, NA_UNSPEC );
+		NET_StringToAdr( address, &adr );
 		for ( i = 0; i < *count; i++ ) {
 			if (NET_CompareAdr(servers[i].adr, adr)) {
 				break;
@@ -174,13 +182,16 @@
 static void LAN_RemoveServer(int source, const char *addr) {
 	int *count, i;
 	serverInfo_t *servers = NULL;
-	count = NULL;
+	count = 0;
 	switch (source) {
 		case AS_LOCAL :
 			count = &cls.numlocalservers;
 			servers = &cls.localServers[0];
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			count = &cls.nummplayerservers;
+			servers = &cls.mplayerServers[0];
+			break;
 		case AS_GLOBAL :
 			count = &cls.numglobalservers;
 			servers = &cls.globalServers[0];
@@ -192,7 +203,7 @@
 	}
 	if (servers) {
 		netadr_t comp;
-		NET_StringToAdr( addr, &comp, NA_UNSPEC );
+		NET_StringToAdr( addr, &comp );
 		for (i = 0; i < *count; i++) {
 			if (NET_CompareAdr( comp, servers[i].adr)) {
 				int j = i;
@@ -218,7 +229,9 @@
 		case AS_LOCAL :
 			return cls.numlocalservers;
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			return cls.nummplayerservers;
+			break;
 		case AS_GLOBAL :
 			return cls.numglobalservers;
 			break;
@@ -238,20 +251,25 @@
 	switch (source) {
 		case AS_LOCAL :
 			if (n >= 0 && n < MAX_OTHER_SERVERS) {
-				Q_strncpyz(buf, NET_AdrToStringwPort( cls.localServers[n].adr) , buflen );
+				Q_strncpyz(buf, NET_AdrToString( cls.localServers[n].adr) , buflen );
+				return;
+			}
+			break;
+		case AS_MPLAYER :
+			if (n >= 0 && n < MAX_OTHER_SERVERS) {
+				Q_strncpyz(buf, NET_AdrToString( cls.mplayerServers[n].adr) , buflen );
 				return;
 			}
 			break;
-		case AS_MPLAYER:
 		case AS_GLOBAL :
 			if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
-				Q_strncpyz(buf, NET_AdrToStringwPort( cls.globalServers[n].adr) , buflen );
+				Q_strncpyz(buf, NET_AdrToString( cls.globalServers[n].adr) , buflen );
 				return;
 			}
 			break;
 		case AS_FAVORITES :
 			if (n >= 0 && n < MAX_OTHER_SERVERS) {
-				Q_strncpyz(buf, NET_AdrToStringwPort( cls.favoriteServers[n].adr) , buflen );
+				Q_strncpyz(buf, NET_AdrToString( cls.favoriteServers[n].adr) , buflen );
 				return;
 			}
 			break;
@@ -274,7 +292,11 @@
 				server = &cls.localServers[n];
 			}
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			if (n >= 0 && n < MAX_OTHER_SERVERS) {
+				server = &cls.mplayerServers[n];
+			}
+			break;
 		case AS_GLOBAL :
 			if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
 				server = &cls.globalServers[n];
@@ -298,10 +320,8 @@
 		Info_SetValueForKey( info, "game", server->game);
 		Info_SetValueForKey( info, "gametype", va("%i",server->gameType));
 		Info_SetValueForKey( info, "nettype", va("%i",server->netType));
-		Info_SetValueForKey( info, "addr", NET_AdrToStringwPort(server->adr));
+		Info_SetValueForKey( info, "addr", NET_AdrToString(server->adr));
 		Info_SetValueForKey( info, "punkbuster", va("%i", server->punkbuster));
-		Info_SetValueForKey( info, "g_needpass", va("%i", server->g_needpass));
-		Info_SetValueForKey( info, "g_humanplayers", va("%i", server->g_humanplayers));
 		Q_strncpyz(buf, info, buflen);
 	} else {
 		if (buf) {
@@ -323,7 +343,11 @@
 				server = &cls.localServers[n];
 			}
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			if (n >= 0 && n < MAX_OTHER_SERVERS) {
+				server = &cls.mplayerServers[n];
+			}
+			break;
 		case AS_GLOBAL :
 			if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
 				server = &cls.globalServers[n];
@@ -353,7 +377,11 @@
 				return &cls.localServers[n];
 			}
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			if (n >= 0 && n < MAX_OTHER_SERVERS) {
+				return &cls.mplayerServers[n];
+			}
+			break;
 		case AS_GLOBAL :
 			if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
 				return &cls.globalServers[n];
@@ -376,7 +404,6 @@
 static int LAN_CompareServers( int source, int sortKey, int sortDir, int s1, int s2 ) {
 	int res;
 	serverInfo_t *server1, *server2;
-	int clients1, clients2;
 
 	server1 = LAN_GetServerPtr(source, s1);
 	server2 = LAN_GetServerPtr(source, s2);
@@ -394,19 +421,10 @@
 			res = Q_stricmp( server1->mapName, server2->mapName );
 			break;
 		case SORT_CLIENTS:
-			// sub sort by max clients
-			if ( server1->clients == server2->clients ) {
-				clients1 = server1->maxClients;
-				clients2 = server2->maxClients;
-			} else {
-				clients1 = server1->clients;
-				clients2 = server2->clients;
-			}
-
-			if (clients1 < clients2) {
+			if (server1->clients < server2->clients) {
 				res = -1;
 			}
-			else if (clients1 > clients2) {
+			else if (server1->clients > server2->clients) {
 				res = 1;
 			}
 			else {
@@ -496,7 +514,9 @@
 			case AS_LOCAL :
 				server = &cls.localServers[0];
 				break;
-			case AS_MPLAYER:
+			case AS_MPLAYER :
+				server = &cls.mplayerServers[0];
+				break;
 			case AS_GLOBAL :
 				server = &cls.globalServers[0];
 				count = MAX_GLOBAL_SERVERS;
@@ -518,7 +538,11 @@
 					cls.localServers[n].visible = visible;
 				}
 				break;
-			case AS_MPLAYER:
+			case AS_MPLAYER :
+				if (n >= 0 && n < MAX_OTHER_SERVERS) {
+					cls.mplayerServers[n].visible = visible;
+				}
+				break;
 			case AS_GLOBAL :
 				if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
 					cls.globalServers[n].visible = visible;
@@ -546,7 +570,11 @@
 				return cls.localServers[n].visible;
 			}
 			break;
-		case AS_MPLAYER:
+		case AS_MPLAYER :
+			if (n >= 0 && n < MAX_OTHER_SERVERS) {
+				return cls.mplayerServers[n].visible;
+			}
+			break;
 		case AS_GLOBAL :
 			if (n >= 0 && n < MAX_GLOBAL_SERVERS) {
 				return cls.globalServers[n].visible;
@@ -581,7 +609,7 @@
 
 /*
 ====================
-CL_GetGlconfig
+CL_GetGlConfig
 ====================
 */
 static void CL_GetGlconfig( glconfig_t *config ) {
@@ -590,10 +618,10 @@
 
 /*
 ====================
-CL_GetClipboardData
+GetClipboardData
 ====================
 */
-static void CL_GetClipboardData( char *buf, int buflen ) {
+static void GetClipboardData( char *buf, int buflen ) {
 	char	*cbd;
 
 	cbd = Sys_GetClipboardData();
@@ -608,6 +636,50 @@
 	Z_Free( cbd );
 }
 
+/*
+====================
+Key_KeynumToStringBuf
+====================
+*/
+static void Key_KeynumToStringBuf( int keynum, char *buf, int buflen ) {
+	Q_strncpyz( buf, Key_KeynumToString( keynum ), buflen );
+}
+
+/*
+====================
+Key_GetBindingBuf
+====================
+*/
+static void Key_GetBindingBuf( int keynum, char *buf, int buflen ) {
+	char	*value;
+
+	value = Key_GetBinding( keynum );
+	if ( value ) {
+		Q_strncpyz( buf, value, buflen );
+	}
+	else {
+		*buf = 0;
+	}
+}
+
+/*
+====================
+Key_GetCatcher
+====================
+*/
+int Key_GetCatcher( void ) {
+	return cls.keyCatchers;
+}
+
+/*
+====================
+Ket_SetCatcher
+====================
+*/
+void Key_SetCatcher( int catcher ) {
+	cls.keyCatchers = catcher;
+}
+
 
 /*
 ====================
@@ -615,19 +687,15 @@
 ====================
 */
 static void CLUI_GetCDKey( char *buf, int buflen ) {
-#ifndef STANDALONE
-	const char *gamedir;
-	gamedir = Cvar_VariableString( "fs_game" );
-	if (UI_usesUniqueCDKey() && gamedir[0] != 0) {
+	cvar_t	*fs;
+	fs = Cvar_Get ("fs_game", "", CVAR_INIT|CVAR_SYSTEMINFO );
+	if (UI_usesUniqueCDKey() && fs && fs->string[0] != 0) {
 		Com_Memcpy( buf, &cl_cdkey[16], 16);
 		buf[16] = 0;
 	} else {
 		Com_Memcpy( buf, cl_cdkey, 16);
 		buf[16] = 0;
 	}
-#else
-	*buf = 0;
-#endif
 }
 
 
@@ -636,11 +704,10 @@
 CLUI_SetCDKey
 ====================
 */
-#ifndef STANDALONE
 static void CLUI_SetCDKey( char *buf ) {
-	const char *gamedir;
-	gamedir = Cvar_VariableString( "fs_game" );
-	if (UI_usesUniqueCDKey() && gamedir[0] != 0) {
+	cvar_t	*fs;
+	fs = Cvar_Get ("fs_game", "", CVAR_INIT|CVAR_SYSTEMINFO );
+	if (UI_usesUniqueCDKey() && fs && fs->string[0] != 0) {
 		Com_Memcpy( &cl_cdkey[16], buf, 16 );
 		cl_cdkey[32] = 0;
 		// set the flag so the fle will be written at the next opportunity
@@ -651,7 +718,6 @@
 		cvar_modifiedFlags |= CVAR_ARCHIVE;
 	}
 }
-#endif
 
 /*
 ====================
@@ -674,7 +740,7 @@
 	}
 
 	Q_strncpyz( buf, cl.gameState.stringData+offset, size);
-
+ 
 	return qtrue;
 }
 
@@ -684,11 +750,17 @@
 ====================
 */
 static int FloatAsInt( float f ) {
-	floatint_t fi;
-	fi.f = f;
-	return fi.i;
+	int		temp;
+
+	*(float *)&temp = f;
+
+	return temp;
 }
 
+void *VM_ArgPtr( int intValue );
+#define	VMA(x) VM_ArgPtr(args[x])
+#define	VMF(x)	((float *)args)[x]
+
 /*
 ====================
 CL_UISystemCalls
@@ -696,21 +768,21 @@
 The ui module is making a system call
 ====================
 */
-intptr_t CL_UISystemCalls( intptr_t *args ) {
+int CL_UISystemCalls( int *args ) {
 	switch( args[0] ) {
 	case UI_ERROR:
-		Com_Error( ERR_DROP, "%s", (const char*)VMA(1) );
+		Com_Error( ERR_DROP, "%s", VMA(1) );
 		return 0;
 
 	case UI_PRINT:
-		Com_Printf( "%s", (const char*)VMA(1) );
+		Com_Printf( "%s", VMA(1) );
 		return 0;
 
 	case UI_MILLISECONDS:
 		return Sys_Milliseconds();
 
 	case UI_CVAR_REGISTER:
-		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] );
+		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] ); 
 		return 0;
 
 	case UI_CVAR_UPDATE:
@@ -718,7 +790,7 @@
 		return 0;
 
 	case UI_CVAR_SET:
-		Cvar_SetSafe( VMA(1), VMA(2) );
+		Cvar_Set( VMA(1), VMA(2) );
 		return 0;
 
 	case UI_CVAR_VARIABLEVALUE:
@@ -729,7 +801,7 @@
 		return 0;
 
 	case UI_CVAR_SETVALUE:
-		Cvar_SetValueSafe( VMA(1), VMF(2) );
+		Cvar_SetValue( VMA(1), VMF(2) );
 		return 0;
 
 	case UI_CVAR_RESET:
@@ -737,16 +809,13 @@
 		return 0;
 
 	case UI_CVAR_CREATE:
-		Cvar_Register( NULL, VMA(1), VMA(2), args[3] );
+		Cvar_Get( VMA(1), VMA(2), args[3] );
 		return 0;
 
 	case UI_CVAR_INFOSTRINGBUFFER:
 		Cvar_InfoStringBuffer( args[1], VMA(2), args[3] );
 		return 0;
 
-	case UI_CVAR_EXISTS:
-		return Cvar_Exists(VMA(1));
-
 	case UI_ARGC:
 		return Cmd_Argc();
 
@@ -755,14 +824,6 @@
 		return 0;
 
 	case UI_CMD_EXECUTETEXT:
-		if(args[1] == EXEC_NOW
-		&& (!strncmp(VMA(2), "snd_restart", 11)
-		|| !strncmp(VMA(2), "vid_restart", 11)
-		|| !strncmp(VMA(2), "quit", 5)))
-		{
-			Com_Printf (S_COLOR_YELLOW "turning EXEC_NOW '%.11s' into EXEC_INSERT\n", (const char*)VMA(2));
-			args[1] = EXEC_INSERT;
-		}
 		Cbuf_ExecuteText( args[1], VMA(2) );
 		return 0;
 
@@ -770,7 +831,7 @@
 		return FS_FOpenFileByMode( VMA(1), VMA(2), args[3] );
 
 	case UI_FS_READ:
-		FS_Read( VMA(1), args[2], args[3] );
+		FS_Read2( VMA(1), args[2], args[3] );
 		return 0;
 
 	case UI_FS_WRITE:
@@ -786,7 +847,7 @@
 
 	case UI_FS_SEEK:
 		return FS_Seek( args[1], args[2], args[3] );
-
+	
 	case UI_R_REGISTERMODEL:
 		return re.RegisterModel( VMA(1) );
 
@@ -800,16 +861,12 @@
 		re.ClearScene();
 		return 0;
 
-	case UI_R_BEGIN_HUD:
-		re.BeginHud();
-		return 0;
-
 	case UI_R_ADDREFENTITYTOSCENE:
 		re.AddRefEntityToScene( VMA(1) );
 		return 0;
 
 	case UI_R_ADDPOLYTOSCENE:
-		re.AddPolyToScene( args[1], args[2], VMA(3), 1, qfalse );
+		re.AddPolyToScene( args[1], args[2], VMA(3), 1 );
 		return 0;
 
 	case UI_R_ADDLIGHTTOSCENE:
@@ -877,17 +934,16 @@
 		return Key_GetCatcher();
 
 	case UI_KEY_SETCATCHER:
-		// Don't allow the ui module to close the console
-		Key_SetCatcher( args[1] | ( Key_GetCatcher( ) & KEYCATCH_CONSOLE ) );
+		Key_SetCatcher( args[1] );
 		return 0;
 
 	case UI_GETCLIPBOARDDATA:
-		CL_GetClipboardData( VMA(1), args[2] );
+		GetClipboardData( VMA(1), args[2] );
 		return 0;
 
 	case UI_GETCLIENTSTATE:
 		GetClientState( VMA(1) );
-		return 0;
+		return 0;		
 
 	case UI_GETGLCONFIG:
 		CL_GetGlconfig( VMA(1) );
@@ -968,13 +1024,11 @@
 		return 0;
 
 	case UI_SET_CDKEY:
-#ifndef STANDALONE
 		CLUI_SetCDKey( VMA(1) );
-#endif
 		return 0;
-
+	
 	case UI_SET_PBCLSTATUS:
-		return 0;
+		return 0;	
 
 	case UI_R_REGISTERFONT:
 		re.RegisterFont( VMA(1), args[2], VMA(3));
@@ -989,8 +1043,7 @@
 		return 0;
 
 	case UI_STRNCPY:
-		strncpy( VMA(1), VMA(2), args[3] );
-		return args[1];
+		return (int)strncpy( VMA(1), VMA(2), args[3] );
 
 	case UI_SIN:
 		return FloatAsInt( sin( VMF(1) ) );
@@ -1029,7 +1082,7 @@
 		return 0;
 
 	case UI_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 
 	case UI_CIN_PLAYCINEMATIC:
 	  Com_DPrintf("UI_CIN_PlayCinematic\n");
@@ -1050,26 +1103,16 @@
 	  return 0;
 
 	case UI_R_REMAP_SHADER:
-		re.RemapShader( VMA(1), VMA(2), VMA(3), qfalse, qfalse );
+		re.RemapShader( VMA(1), VMA(2), VMA(3) );
 		return 0;
 
-	case UI_ACOS:
-		return Q_acos(VMF(1));
 	case UI_VERIFY_CDKEY:
 		return CL_CDKeyValidate(VMA(1), VMA(2));
-	case UI_OPEN_QUAKE_LIVE_DIRECTORY:
-		Sys_OpenQuakeLiveDirectory();
-		return 0;
-	case UI_OPEN_WOLFCAM_DIRECTORY:
-		Sys_OpenWolfcamDirectory();
-		return 0;
-	case UI_DRAW_CONSOLE_LINES_OVER:
-		Con_DrawConsoleLinesOver(args[1], args[2], args[3]);
-		return 0;
 
 
+		
 	default:
-		Com_Error( ERR_DROP, "Bad UI system trap: %ld", (long int) args[0] );
+		Com_Error( ERR_DROP, "Bad UI system trap: %i", args[0] );
 
 	}
 
@@ -1082,7 +1125,7 @@
 ====================
 */
 void CL_ShutdownUI( void ) {
-	Key_SetCatcher( Key_GetCatcher( ) & ~KEYCATCH_UI );
+	cls.keyCatchers &= ~KEYCATCH_UI;
 	cls.uiStarted = qfalse;
 	if ( !uivm ) {
 		return;
@@ -1104,14 +1147,13 @@
 	vmInterpret_t		interpret;
 
 	// load the dll or bytecode
-	interpret = Cvar_VariableValue("vm_ui");
-	if(cl_connectedToPureServer)
-	{
+	if ( cl_connectedToPureServer != 0 ) {
 		// if sv_pure is set we only allow qvms to be loaded
-		if(interpret != VMI_COMPILED && interpret != VMI_BYTECODE)
-			interpret = VMI_COMPILED;
+		interpret = VMI_COMPILED;
+	}
+	else {
+		interpret = Cvar_VariableValue( "vm_ui" );
 	}
-
 	uivm = VM_Create( "ui", CL_UISystemCalls, interpret );
 	if ( !uivm ) {
 		Com_Error( ERR_FATAL, "VM_Create on UI failed" );
@@ -1122,31 +1164,25 @@
 	if (v == UI_OLD_API_VERSION) {
 //		Com_Printf(S_COLOR_YELLOW "WARNING: loading old Quake III Arena User Interface version %d\n", v );
 		// init for this gamestate
-		VM_Call( uivm, UI_INIT, (clc.state >= CA_AUTHORIZING && clc.state < CA_ACTIVE));
+		VM_Call( uivm, UI_INIT, (cls.state >= CA_AUTHORIZING && cls.state < CA_ACTIVE));
 	}
 	else if (v != UI_API_VERSION) {
-		// Free uivm now, so UI_SHUTDOWN doesn't get called later.
-		VM_Free( uivm );
-		uivm = NULL;
-
 		Com_Error( ERR_DROP, "User Interface is version %d, expected %d", v, UI_API_VERSION );
 		cls.uiStarted = qfalse;
 	}
 	else {
 		// init for this gamestate
-		VM_Call( uivm, UI_INIT, (clc.state >= CA_AUTHORIZING && clc.state < CA_ACTIVE) );
+		VM_Call( uivm, UI_INIT, (cls.state >= CA_AUTHORIZING && cls.state < CA_ACTIVE) );
 	}
 }
 
-#ifndef STANDALONE
-qboolean UI_usesUniqueCDKey( void ) {
+qboolean UI_usesUniqueCDKey() {
 	if (uivm) {
 		return (VM_Call( uivm, UI_HASUNIQUECDKEY) == qtrue);
 	} else {
 		return qfalse;
 	}
 }
-#endif
 
 /*
 ====================

```

### `ioquake3`  — sha256 `cb759bad7dcb...`, 26698 bytes

_Diff stat: +36 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_ui.c	2026-04-16 20:02:25.174216300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\cl_ui.c	2026-04-16 20:02:21.529570100 +0100
@@ -21,7 +21,6 @@
 */
 
 #include "client.h"
-#include "keys.h"
 
 #include "../botlib/botlib.h"
 
@@ -41,7 +40,6 @@
 	Q_strncpyz( state->updateInfoString, cls.updateInfoString, sizeof( state->updateInfoString ) );
 	Q_strncpyz( state->messageString, clc.serverMessage, sizeof( state->messageString ) );
 	state->clientNum = cl.snap.ps.clientNum;
-	state->demoplaying = clc.demoplaying;
 }
 
 /*
@@ -581,7 +579,7 @@
 
 /*
 ====================
-CL_GetGlconfig
+CL_GetGlConfig
 ====================
 */
 static void CL_GetGlconfig( glconfig_t *config ) {
@@ -608,6 +606,31 @@
 	Z_Free( cbd );
 }
 
+/*
+====================
+Key_KeynumToStringBuf
+====================
+*/
+static void Key_KeynumToStringBuf( int keynum, char *buf, int buflen ) {
+	Q_strncpyz( buf, Key_KeynumToString( keynum ), buflen );
+}
+
+/*
+====================
+Key_GetBindingBuf
+====================
+*/
+static void Key_GetBindingBuf( int keynum, char *buf, int buflen ) {
+	char	*value;
+
+	value = Key_GetBinding( keynum );
+	if ( value ) {
+		Q_strncpyz( buf, value, buflen );
+	}
+	else {
+		*buf = 0;
+	}
+}
 
 /*
 ====================
@@ -674,7 +697,7 @@
 	}
 
 	Q_strncpyz( buf, cl.gameState.stringData+offset, size);
-
+ 
 	return qtrue;
 }
 
@@ -710,7 +733,7 @@
 		return Sys_Milliseconds();
 
 	case UI_CVAR_REGISTER:
-		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] );
+		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] ); 
 		return 0;
 
 	case UI_CVAR_UPDATE:
@@ -744,9 +767,6 @@
 		Cvar_InfoStringBuffer( args[1], VMA(2), args[3] );
 		return 0;
 
-	case UI_CVAR_EXISTS:
-		return Cvar_Exists(VMA(1));
-
 	case UI_ARGC:
 		return Cmd_Argc();
 
@@ -786,7 +806,7 @@
 
 	case UI_FS_SEEK:
 		return FS_Seek( args[1], args[2], args[3] );
-
+	
 	case UI_R_REGISTERMODEL:
 		return re.RegisterModel( VMA(1) );
 
@@ -800,16 +820,12 @@
 		re.ClearScene();
 		return 0;
 
-	case UI_R_BEGIN_HUD:
-		re.BeginHud();
-		return 0;
-
 	case UI_R_ADDREFENTITYTOSCENE:
 		re.AddRefEntityToScene( VMA(1) );
 		return 0;
 
 	case UI_R_ADDPOLYTOSCENE:
-		re.AddPolyToScene( args[1], args[2], VMA(3), 1, qfalse );
+		re.AddPolyToScene( args[1], args[2], VMA(3), 1 );
 		return 0;
 
 	case UI_R_ADDLIGHTTOSCENE:
@@ -887,7 +903,7 @@
 
 	case UI_GETCLIENTSTATE:
 		GetClientState( VMA(1) );
-		return 0;
+		return 0;		
 
 	case UI_GETGLCONFIG:
 		CL_GetGlconfig( VMA(1) );
@@ -972,9 +988,9 @@
 		CLUI_SetCDKey( VMA(1) );
 #endif
 		return 0;
-
+	
 	case UI_SET_PBCLSTATUS:
-		return 0;
+		return 0;	
 
 	case UI_R_REGISTERFONT:
 		re.RegisterFont( VMA(1), args[2], VMA(3));
@@ -1029,7 +1045,7 @@
 		return 0;
 
 	case UI_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 
 	case UI_CIN_PLAYCINEMATIC:
 	  Com_DPrintf("UI_CIN_PlayCinematic\n");
@@ -1050,24 +1066,12 @@
 	  return 0;
 
 	case UI_R_REMAP_SHADER:
-		re.RemapShader( VMA(1), VMA(2), VMA(3), qfalse, qfalse );
+		re.RemapShader( VMA(1), VMA(2), VMA(3) );
 		return 0;
 
-	case UI_ACOS:
-		return Q_acos(VMF(1));
 	case UI_VERIFY_CDKEY:
 		return CL_CDKeyValidate(VMA(1), VMA(2));
-	case UI_OPEN_QUAKE_LIVE_DIRECTORY:
-		Sys_OpenQuakeLiveDirectory();
-		return 0;
-	case UI_OPEN_WOLFCAM_DIRECTORY:
-		Sys_OpenWolfcamDirectory();
-		return 0;
-	case UI_DRAW_CONSOLE_LINES_OVER:
-		Con_DrawConsoleLinesOver(args[1], args[2], args[3]);
-		return 0;
-
-
+		
 	default:
 		Com_Error( ERR_DROP, "Bad UI system trap: %ld", (long int) args[0] );
 

```

### `quake3e`  — sha256 `915413fa71a1...`, 30597 bytes

_Diff stat: +275 / -116 lines_

_(full diff is 23238 bytes — see files directly)_

### `openarena-engine`  — sha256 `3167c4176359...`, 26547 bytes

_Diff stat: +51 / -53 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_ui.c	2026-04-16 20:02:25.174216300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_ui.c	2026-04-16 22:48:25.733378900 +0100
@@ -21,7 +21,6 @@
 */
 
 #include "client.h"
-#include "keys.h"
 
 #include "../botlib/botlib.h"
 
@@ -41,7 +40,6 @@
 	Q_strncpyz( state->updateInfoString, cls.updateInfoString, sizeof( state->updateInfoString ) );
 	Q_strncpyz( state->messageString, clc.serverMessage, sizeof( state->messageString ) );
 	state->clientNum = cl.snap.ps.clientNum;
-	state->demoplaying = clc.demoplaying;
 }
 
 /*
@@ -54,7 +52,7 @@
 	fileHandle_t fileIn;
 	cls.numglobalservers = cls.numfavoriteservers = 0;
 	cls.numGlobalServerAddresses = 0;
-	if (FS_BaseDir_FOpenFileRead("servercache.dat", &fileIn)) {
+	if (FS_SV_FOpenFileRead("servercache.dat", &fileIn)) {
 		FS_Read(&cls.numglobalservers, sizeof(int), fileIn);
 		FS_Read(&cls.numfavoriteservers, sizeof(int), fileIn);
 		FS_Read(&size, sizeof(int), fileIn);
@@ -76,7 +74,7 @@
 */
 void LAN_SaveServersToCache( void ) {
 	int size;
-	fileHandle_t fileOut = FS_BaseDir_FOpenFileWrite_HomeState("servercache.dat");
+	fileHandle_t fileOut = FS_SV_FOpenFileWrite("servercache.dat");
 	FS_Write(&cls.numglobalservers, sizeof(int), fileOut);
 	FS_Write(&cls.numfavoriteservers, sizeof(int), fileOut);
 	size = sizeof(cls.globalServers) + sizeof(cls.favoriteServers);
@@ -376,7 +374,6 @@
 static int LAN_CompareServers( int source, int sortKey, int sortDir, int s1, int s2 ) {
 	int res;
 	serverInfo_t *server1, *server2;
-	int clients1, clients2;
 
 	server1 = LAN_GetServerPtr(source, s1);
 	server2 = LAN_GetServerPtr(source, s2);
@@ -394,19 +391,10 @@
 			res = Q_stricmp( server1->mapName, server2->mapName );
 			break;
 		case SORT_CLIENTS:
-			// sub sort by max clients
-			if ( server1->clients == server2->clients ) {
-				clients1 = server1->maxClients;
-				clients2 = server2->maxClients;
-			} else {
-				clients1 = server1->clients;
-				clients2 = server2->clients;
-			}
-
-			if (clients1 < clients2) {
+			if (server1->clients < server2->clients) {
 				res = -1;
 			}
-			else if (clients1 > clients2) {
+			else if (server1->clients > server2->clients) {
 				res = 1;
 			}
 			else {
@@ -581,7 +569,7 @@
 
 /*
 ====================
-CL_GetGlconfig
+CL_GetGlConfig
 ====================
 */
 static void CL_GetGlconfig( glconfig_t *config ) {
@@ -596,7 +584,11 @@
 static void CL_GetClipboardData( char *buf, int buflen ) {
 	char	*cbd;
 
+#if SDL_MAJOR_VERSION == 2
+	cbd = Sys_GetClipboardData2();
+#else
 	cbd = Sys_GetClipboardData();
+#endif
 
 	if ( !cbd ) {
 		*buf = 0;
@@ -608,6 +600,31 @@
 	Z_Free( cbd );
 }
 
+/*
+====================
+Key_KeynumToStringBuf
+====================
+*/
+static void Key_KeynumToStringBuf( int keynum, char *buf, int buflen ) {
+	Q_strncpyz( buf, Key_KeynumToString( keynum ), buflen );
+}
+
+/*
+====================
+Key_GetBindingBuf
+====================
+*/
+static void Key_GetBindingBuf( int keynum, char *buf, int buflen ) {
+	char	*value;
+
+	value = Key_GetBinding( keynum );
+	if ( value ) {
+		Q_strncpyz( buf, value, buflen );
+	}
+	else {
+		*buf = 0;
+	}
+}
 
 /*
 ====================
@@ -616,9 +633,9 @@
 */
 static void CLUI_GetCDKey( char *buf, int buflen ) {
 #ifndef STANDALONE
-	const char *gamedir;
-	gamedir = Cvar_VariableString( "fs_game" );
-	if (UI_usesUniqueCDKey() && gamedir[0] != 0) {
+	cvar_t	*fs;
+	fs = Cvar_Get ("fs_game", "", CVAR_INIT|CVAR_SYSTEMINFO );
+	if (UI_usesUniqueCDKey() && fs && fs->string[0] != 0) {
 		Com_Memcpy( buf, &cl_cdkey[16], 16);
 		buf[16] = 0;
 	} else {
@@ -638,9 +655,9 @@
 */
 #ifndef STANDALONE
 static void CLUI_SetCDKey( char *buf ) {
-	const char *gamedir;
-	gamedir = Cvar_VariableString( "fs_game" );
-	if (UI_usesUniqueCDKey() && gamedir[0] != 0) {
+	cvar_t	*fs;
+	fs = Cvar_Get ("fs_game", "", CVAR_INIT|CVAR_SYSTEMINFO );
+	if (UI_usesUniqueCDKey() && fs && fs->string[0] != 0) {
 		Com_Memcpy( &cl_cdkey[16], buf, 16 );
 		cl_cdkey[32] = 0;
 		// set the flag so the fle will be written at the next opportunity
@@ -674,7 +691,7 @@
 	}
 
 	Q_strncpyz( buf, cl.gameState.stringData+offset, size);
-
+ 
 	return qtrue;
 }
 
@@ -710,7 +727,7 @@
 		return Sys_Milliseconds();
 
 	case UI_CVAR_REGISTER:
-		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] );
+		Cvar_Register( VMA(1), VMA(2), VMA(3), args[4] ); 
 		return 0;
 
 	case UI_CVAR_UPDATE:
@@ -744,9 +761,6 @@
 		Cvar_InfoStringBuffer( args[1], VMA(2), args[3] );
 		return 0;
 
-	case UI_CVAR_EXISTS:
-		return Cvar_Exists(VMA(1));
-
 	case UI_ARGC:
 		return Cmd_Argc();
 
@@ -770,7 +784,7 @@
 		return FS_FOpenFileByMode( VMA(1), VMA(2), args[3] );
 
 	case UI_FS_READ:
-		FS_Read( VMA(1), args[2], args[3] );
+		FS_Read2( VMA(1), args[2], args[3] );
 		return 0;
 
 	case UI_FS_WRITE:
@@ -786,7 +800,7 @@
 
 	case UI_FS_SEEK:
 		return FS_Seek( args[1], args[2], args[3] );
-
+	
 	case UI_R_REGISTERMODEL:
 		return re.RegisterModel( VMA(1) );
 
@@ -800,16 +814,12 @@
 		re.ClearScene();
 		return 0;
 
-	case UI_R_BEGIN_HUD:
-		re.BeginHud();
-		return 0;
-
 	case UI_R_ADDREFENTITYTOSCENE:
 		re.AddRefEntityToScene( VMA(1) );
 		return 0;
 
 	case UI_R_ADDPOLYTOSCENE:
-		re.AddPolyToScene( args[1], args[2], VMA(3), 1, qfalse );
+		re.AddPolyToScene( args[1], args[2], VMA(3), 1 );
 		return 0;
 
 	case UI_R_ADDLIGHTTOSCENE:
@@ -887,7 +897,7 @@
 
 	case UI_GETCLIENTSTATE:
 		GetClientState( VMA(1) );
-		return 0;
+		return 0;		
 
 	case UI_GETGLCONFIG:
 		CL_GetGlconfig( VMA(1) );
@@ -972,9 +982,9 @@
 		CLUI_SetCDKey( VMA(1) );
 #endif
 		return 0;
-
+	
 	case UI_SET_PBCLSTATUS:
-		return 0;
+		return 0;	
 
 	case UI_R_REGISTERFONT:
 		re.RegisterFont( VMA(1), args[2], VMA(3));
@@ -1029,7 +1039,7 @@
 		return 0;
 
 	case UI_REAL_TIME:
-		return Com_RealTime(VMA(1), args[2], args[3]);
+		return Com_RealTime( VMA(1) );
 
 	case UI_CIN_PLAYCINEMATIC:
 	  Com_DPrintf("UI_CIN_PlayCinematic\n");
@@ -1050,24 +1060,12 @@
 	  return 0;
 
 	case UI_R_REMAP_SHADER:
-		re.RemapShader( VMA(1), VMA(2), VMA(3), qfalse, qfalse );
+		re.RemapShader( VMA(1), VMA(2), VMA(3) );
 		return 0;
 
-	case UI_ACOS:
-		return Q_acos(VMF(1));
 	case UI_VERIFY_CDKEY:
 		return CL_CDKeyValidate(VMA(1), VMA(2));
-	case UI_OPEN_QUAKE_LIVE_DIRECTORY:
-		Sys_OpenQuakeLiveDirectory();
-		return 0;
-	case UI_OPEN_WOLFCAM_DIRECTORY:
-		Sys_OpenWolfcamDirectory();
-		return 0;
-	case UI_DRAW_CONSOLE_LINES_OVER:
-		Con_DrawConsoleLinesOver(args[1], args[2], args[3]);
-		return 0;
-
-
+		
 	default:
 		Com_Error( ERR_DROP, "Bad UI system trap: %ld", (long int) args[0] );
 

```
