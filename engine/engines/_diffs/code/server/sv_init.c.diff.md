# Diff: `code/server/sv_init.c`
**Canonical:** `wolfcamql-src` (sha256 `971dd72a589a...`, 21946 bytes)

## Variants

### `quake3-source`  — sha256 `cc7446cc30bf...`, 19442 bytes

_Diff stat: +88 / -178 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_init.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_init.c	2026-04-16 20:02:19.977635800 +0100
@@ -15,88 +15,13 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
 #include "server.h"
 
-
-/*
-===============
-SV_SendConfigstring
-
-Creates and sends the server command necessary to update the CS index for the
-given client
-===============
-*/
-static void SV_SendConfigstring(client_t *client, int index)
-{
-	int maxChunkSize = MAX_STRING_CHARS - 24;
-	int len;
-
-	len = strlen(sv.configstrings[index]);
-
-	if( len >= maxChunkSize ) {
-		int		sent = 0;
-		int		remaining = len;
-		char	*cmd;
-		char	buf[MAX_STRING_CHARS];
-
-		while (remaining > 0 ) {
-			if ( sent == 0 ) {
-				cmd = "bcs0";
-			}
-			else if( remaining < maxChunkSize ) {
-				cmd = "bcs2";
-			}
-			else {
-				cmd = "bcs1";
-			}
-			Q_strncpyz( buf, &sv.configstrings[index][sent],
-				maxChunkSize );
-
-			SV_SendServerCommand( client, "%s %i \"%s\"\n", cmd,
-				index, buf );
-
-			sent += (maxChunkSize - 1);
-			remaining -= (maxChunkSize - 1);
-		}
-	} else {
-		// standard cs, just send it
-		SV_SendServerCommand( client, "cs %i \"%s\"\n", index,
-			sv.configstrings[index] );
-	}
-}
-
-/*
-===============
-SV_UpdateConfigstrings
-
-Called when a client goes from CS_PRIMED to CS_ACTIVE.  Updates all
-Configstring indexes that have changed while the client was in CS_PRIMED
-===============
-*/
-void SV_UpdateConfigstrings(client_t *client)
-{
-	int index;
-
-	for( index = 0; index < MAX_CONFIGSTRINGS; index++ ) {
-		// if the CS hasn't changed since we went to CS_PRIMED, ignore
-		if(!client->csUpdated[index])
-			continue;
-
-		// do not always send server info to all clients
-		if ( index == CS_SERVERINFO && client->gentity &&
-			(client->gentity->r.svFlags & SVF_NOSERVERINFO) ) {
-			continue;
-		}
-		SV_SendConfigstring(client, index);
-		client->csUpdated[index] = qfalse;
-	}
-}
-
 /*
 ===============
 SV_SetConfigstring
@@ -104,11 +29,12 @@
 ===============
 */
 void SV_SetConfigstring (int index, const char *val) {
-	int		i;
+	int		len, i;
+	int		maxChunkSize = MAX_STRING_CHARS - 24;
 	client_t	*client;
 
 	if ( index < 0 || index >= MAX_CONFIGSTRINGS ) {
-		Com_Error (ERR_DROP, "SV_SetConfigstring: bad index %i", index);
+		Com_Error (ERR_DROP, "SV_SetConfigstring: bad index %i\n", index);
 	}
 
 	if ( !val ) {
@@ -128,23 +54,50 @@
 	// spawning a new server
 	if ( sv.state == SS_GAME || sv.restarting ) {
 
-		// send the data to all relevant clients
+		// send the data to all relevent clients
 		for (i = 0, client = svs.clients; i < sv_maxclients->integer ; i++, client++) {
-			if ( client->state < CS_ACTIVE ) {
-				if ( client->state == CS_PRIMED )
-					client->csUpdated[ index ] = qtrue;
+			if ( client->state < CS_PRIMED ) {
 				continue;
 			}
 			// do not always send server info to all clients
 			if ( index == CS_SERVERINFO && client->gentity && (client->gentity->r.svFlags & SVF_NOSERVERINFO) ) {
 				continue;
 			}
-		
-			SV_SendConfigstring(client, index);
+
+			len = strlen( val );
+			if( len >= maxChunkSize ) {
+				int		sent = 0;
+				int		remaining = len;
+				char	*cmd;
+				char	buf[MAX_STRING_CHARS];
+
+				while (remaining > 0 ) {
+					if ( sent == 0 ) {
+						cmd = "bcs0";
+					}
+					else if( remaining < maxChunkSize ) {
+						cmd = "bcs2";
+					}
+					else {
+						cmd = "bcs1";
+					}
+					Q_strncpyz( buf, &val[sent], maxChunkSize );
+
+					SV_SendServerCommand( client, "%s %i \"%s\"\n", cmd, index, buf );
+
+					sent += (maxChunkSize - 1);
+					remaining -= (maxChunkSize - 1);
+				}
+			} else {
+				// standard cs, just send it
+				SV_SendServerCommand( client, "cs %i \"%s\"\n", index, val );
+			}
 		}
 	}
 }
 
+
+
 /*
 ===============
 SV_GetConfigstring
@@ -156,7 +109,7 @@
 		Com_Error( ERR_DROP, "SV_GetConfigstring: bufferSize == %i", bufferSize );
 	}
 	if ( index < 0 || index >= MAX_CONFIGSTRINGS ) {
-		Com_Error (ERR_DROP, "SV_GetConfigstring: bad index %i", index);
+		Com_Error (ERR_DROP, "SV_GetConfigstring: bad index %i\n", index);
 	}
 	if ( !sv.configstrings[index] ) {
 		buffer[0] = 0;
@@ -175,7 +128,7 @@
 */
 void SV_SetUserinfo( int index, const char *val ) {
 	if ( index < 0 || index >= sv_maxclients->integer ) {
-		Com_Error (ERR_DROP, "SV_SetUserinfo: bad index %i", index);
+		Com_Error (ERR_DROP, "SV_SetUserinfo: bad index %i\n", index);
 	}
 
 	if ( !val ) {
@@ -199,7 +152,7 @@
 		Com_Error( ERR_DROP, "SV_GetUserinfo: bufferSize == %i", bufferSize );
 	}
 	if ( index < 0 || index >= sv_maxclients->integer ) {
-		Com_Error (ERR_DROP, "SV_GetUserinfo: bad index %i", index);
+		Com_Error (ERR_DROP, "SV_GetUserinfo: bad index %i\n", index);
 	}
 	Q_strncpyz( buffer, svs.clients[ index ].userinfo, bufferSize );
 }
@@ -214,7 +167,7 @@
 baseline will be transmitted
 ================
 */
-static void SV_CreateBaseline( void ) {
+void SV_CreateBaseline( void ) {
 	sharedEntity_t *svent;
 	int				entnum;	
 
@@ -239,7 +192,7 @@
 
 ===============
 */
-static void SV_BoundMaxClients( int minimum ) {
+void SV_BoundMaxClients( int minimum ) {
 	// get the current maxclients value
 	Cvar_Get( "sv_maxclients", "8", 0 );
 
@@ -263,7 +216,7 @@
 the menu system first.
 ===============
 */
-static void SV_Startup( void ) {
+void SV_Startup( void ) {
 	if ( svs.initialized ) {
 		Com_Error( ERR_FATAL, "SV_Startup: svs.initialized" );
 	}
@@ -271,22 +224,14 @@
 
 	svs.clients = Z_Malloc (sizeof(client_t) * sv_maxclients->integer );
 	if ( com_dedicated->integer ) {
-		svs.numSnapshotEntities = sv_maxclients->integer * PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES;
+		svs.numSnapshotEntities = sv_maxclients->integer * PACKET_BACKUP * 64;
 	} else {
 		// we don't need nearly as many when playing locally
-		svs.numSnapshotEntities = sv_maxclients->integer * 4 * MAX_SNAPSHOT_ENTITIES;
+		svs.numSnapshotEntities = sv_maxclients->integer * 4 * 64;
 	}
 	svs.initialized = qtrue;
 
-	// Don't respect sv_killserver unless a server is actually running
-	if ( sv_killserver->integer ) {
-		Cvar_Set( "sv_killserver", "0" );
-	}
-
 	Cvar_Set( "sv_running", "1" );
-	
-	// Join the ipv6 multicast group now that a map is running so clients can scan for us on the local network.
-	NET_JoinMulticast6();
 }
 
 
@@ -349,10 +294,10 @@
 	
 	// allocate new snapshot entities
 	if ( com_dedicated->integer ) {
-		svs.numSnapshotEntities = sv_maxclients->integer * PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES;
+		svs.numSnapshotEntities = sv_maxclients->integer * PACKET_BACKUP * 64;
 	} else {
 		// we don't need nearly as many when playing locally
-		svs.numSnapshotEntities = sv_maxclients->integer * 4 * MAX_SNAPSHOT_ENTITIES;
+		svs.numSnapshotEntities = sv_maxclients->integer * 4 * 64;
 	}
 }
 
@@ -361,7 +306,7 @@
 SV_ClearServer
 ================
 */
-static void SV_ClearServer(void) {
+void SV_ClearServer(void) {
 	int i;
 
 	for ( i = 0 ; i < MAX_CONFIGSTRINGS ; i++ ) {
@@ -374,12 +319,16 @@
 
 /*
 ================
-SV_TouchFile
+SV_TouchCGame
+
+  touch the cgame.vm so that a pure client can load it if it's in a seperate pk3
 ================
 */
-static void SV_TouchFile( const char *filename ) {
+void SV_TouchCGame(void) {
 	fileHandle_t	f;
+	char filename[MAX_QPATH];
 
+	Com_sprintf( filename, sizeof(filename), "vm/%s.qvm", "cgame" );
 	FS_FOpenFileRead( filename, &f, qfalse );
 	if ( f ) {
 		FS_FCloseFile( f );
@@ -413,7 +362,7 @@
 	CL_MapLoading();
 
 	// make sure all the client stuff is unloaded
-	CL_ShutdownAll(qfalse);
+	CL_ShutdownAll();
 
 	// clear the whole hunk because we're (re)loading the server
 	Hunk_Clear();
@@ -447,13 +396,6 @@
 	Cvar_Set( "nextmap", "map_restart 0");
 //	Cvar_Set( "nextmap", va("map %s", server) );
 
-	for (i=0 ; i<sv_maxclients->integer ; i++) {
-		// save when the server started for each client already connected
-		if (svs.clients[i].state >= CS_CONNECTED) {
-			svs.clients[i].oldServerTime = sv.time;
-		}
-	}
-
 	// wipe the entire per-level structure
 	SV_ClearServer();
 	for ( i = 0 ; i < MAX_CONFIGSTRINGS ; i++ ) {
@@ -464,7 +406,8 @@
 	Cvar_Set("cl_paused", "0");
 
 	// get a new checksum feed and restart the file system
-	sv.checksumFeed = ( ((unsigned int)rand() << 16) ^ (unsigned int)rand() ) ^ Com_Milliseconds();
+	srand(Com_Milliseconds());
+	sv.checksumFeed = ( ((int) rand() << 16) ^ rand() ) ^ Com_Milliseconds();
 	FS_Restart( sv.checksumFeed );
 
 	CM_LoadMap( va("maps/%s.bsp", server), qfalse, &checksum );
@@ -495,11 +438,9 @@
 	sv_gametype->modified = qfalse;
 
 	// run a few frames to allow everything to settle
-	for (i = 0;i < 3; i++)
-	{
-		VM_Call (gvm, GAME_RUN_FRAME, sv.time);
-		SV_BotFrame (sv.time);
-		sv.time += 100;
+	for ( i = 0 ;i < 3 ; i++ ) {
+		VM_Call( gvm, GAME_RUN_FRAME, svs.time );
+		SV_BotFrame( svs.time );
 		svs.time += 100;
 	}
 
@@ -545,7 +486,7 @@
 					client->gentity = ent;
 
 					client->deltaMessage = -1;
-					client->lastSnapshotTime = 0;	// generate a snapshot immediately
+					client->nextSnapshotTime = svs.time;	// generate a snapshot immediately
 
 					VM_Call( gvm, GAME_CLIENT_BEGIN, i );
 				}
@@ -554,9 +495,8 @@
 	}	
 
 	// run another frame to allow things to look at all the players
-	VM_Call (gvm, GAME_RUN_FRAME, sv.time);
-	SV_BotFrame (sv.time);
-	sv.time += 100;
+	VM_Call( gvm, GAME_RUN_FRAME, svs.time );
+	SV_BotFrame( svs.time );
 	svs.time += 100;
 
 	if ( sv_pure->integer ) {
@@ -570,11 +510,11 @@
 		p = FS_LoadedPakNames();
 		Cvar_Set( "sv_pakNames", p );
 
-		// we need to touch the cgame and ui qvm because they could be in
-		// separate pk3 files and the client will need to download the pk3
-		// files with the latest cgame and ui qvm to pass the pure check
-		SV_TouchFile( "vm/cgame.qvm" );
-		SV_TouchFile( "vm/ui.qvm" );
+		// if a dedicated pure server we need to touch the cgame because it could be in a
+		// seperate pk3 file and the client will need to load the latest cgame.qvm
+		if ( com_dedicated->integer ) {
+			SV_TouchCGame();
+		}
 	}
 	else {
 		Cvar_Set( "sv_paks", "" );
@@ -605,14 +545,6 @@
 
 	Hunk_SetMark();
 
-#ifndef DEDICATED
-	if ( com_dedicated->integer ) {
-		// restart renderer in order to show console for dedicated servers
-		// launched through the regular binary
-		CL_StartHunkUsers( qtrue );
-	}
-#endif
-
 	Com_Printf ("-----------------------------------\n");
 }
 
@@ -623,10 +555,9 @@
 Only called at main exe startup, not for each game
 ===============
 */
-void SV_Init (void)
-{
-	int index;
+void SV_BotInitBotLib(void);
 
+void SV_Init (void) {
 	SV_AddOperatorCommands ();
 
 	// serverinfo vars
@@ -635,14 +566,13 @@
 	Cvar_Get ("timelimit", "0", CVAR_SERVERINFO);
 	sv_gametype = Cvar_Get ("g_gametype", "0", CVAR_SERVERINFO | CVAR_LATCH );
 	Cvar_Get ("sv_keywords", "", CVAR_SERVERINFO);
+	Cvar_Get ("protocol", va("%i", PROTOCOL_VERSION), CVAR_SERVERINFO | CVAR_ROM);
 	sv_mapname = Cvar_Get ("mapname", "nomap", CVAR_SERVERINFO | CVAR_ROM);
 	sv_privateClients = Cvar_Get ("sv_privateClients", "0", CVAR_SERVERINFO);
 	sv_hostname = Cvar_Get ("sv_hostname", "noname", CVAR_SERVERINFO | CVAR_ARCHIVE );
 	sv_maxclients = Cvar_Get ("sv_maxclients", "8", CVAR_SERVERINFO | CVAR_LATCH);
 
-	sv_minRate = Cvar_Get ("sv_minRate", "0", CVAR_ARCHIVE | CVAR_SERVERINFO );
 	sv_maxRate = Cvar_Get ("sv_maxRate", "0", CVAR_ARCHIVE | CVAR_SERVERINFO );
-	sv_dlRate = Cvar_Get("sv_dlRate", "100", CVAR_ARCHIVE | CVAR_SERVERINFO);
 	sv_minPing = Cvar_Get ("sv_minPing", "0", CVAR_ARCHIVE | CVAR_SERVERINFO );
 	sv_maxPing = Cvar_Get ("sv_maxPing", "0", CVAR_ARCHIVE | CVAR_SERVERINFO );
 	sv_floodProtect = Cvar_Get ("sv_floodProtect", "1", CVAR_ARCHIVE | CVAR_SERVERINFO );
@@ -650,11 +580,10 @@
 	// systeminfo
 	Cvar_Get ("sv_cheats", "1", CVAR_SYSTEMINFO | CVAR_ROM );
 	sv_serverid = Cvar_Get ("sv_serverid", "0", CVAR_SYSTEMINFO | CVAR_ROM );
-	sv_pure = Cvar_Get ("sv_pure", "0", CVAR_SYSTEMINFO );
-#ifdef USE_VOIP
-	sv_voip = Cvar_Get("sv_voip", "1", CVAR_LATCH);
-	Cvar_CheckRange(sv_voip, 0, 1, qtrue);
-	sv_voipProtocol = Cvar_Get("sv_voipProtocol", sv_voip->integer ? "opus" : "", CVAR_SYSTEMINFO | CVAR_ROM );
+#ifndef DLL_ONLY // bk010216 - for DLL-only servers
+	sv_pure = Cvar_Get ("sv_pure", "1", CVAR_SYSTEMINFO );
+#else
+	sv_pure = Cvar_Get ("sv_pure", "0", CVAR_SYSTEMINFO | CVAR_INIT | CVAR_ROM );
 #endif
 	Cvar_Get ("sv_paks", "", CVAR_SYSTEMINFO | CVAR_ROM );
 	Cvar_Get ("sv_pakNames", "", CVAR_SYSTEMINFO | CVAR_ROM );
@@ -670,34 +599,24 @@
 	Cvar_Get ("nextmap", "", CVAR_TEMP );
 
 	sv_allowDownload = Cvar_Get ("sv_allowDownload", "0", CVAR_SERVERINFO);
-	Cvar_Get ("sv_dlURL", "", CVAR_SERVERINFO | CVAR_ARCHIVE);
-
-	sv_master[0] = Cvar_Get("sv_master1", MASTER_SERVER_NAME, 0);
-	sv_master[1] = Cvar_Get("sv_master2", "directory.ioquake3.org", 0);
-	for(index = 2; index < MAX_MASTER_SERVERS; index++)
-		sv_master[index] = Cvar_Get(va("sv_master%d", index + 1), "", CVAR_ARCHIVE);
-
+	sv_master[0] = Cvar_Get ("sv_master1", MASTER_SERVER_NAME, 0 );
+	sv_master[1] = Cvar_Get ("sv_master2", "", CVAR_ARCHIVE );
+	sv_master[2] = Cvar_Get ("sv_master3", "", CVAR_ARCHIVE );
+	sv_master[3] = Cvar_Get ("sv_master4", "", CVAR_ARCHIVE );
+	sv_master[4] = Cvar_Get ("sv_master5", "", CVAR_ARCHIVE );
 	sv_reconnectlimit = Cvar_Get ("sv_reconnectlimit", "3", 0);
 	sv_showloss = Cvar_Get ("sv_showloss", "0", 0);
 	sv_padPackets = Cvar_Get ("sv_padPackets", "0", 0);
 	sv_killserver = Cvar_Get ("sv_killserver", "0", 0);
 	sv_mapChecksum = Cvar_Get ("sv_mapChecksum", "", CVAR_ROM);
 	sv_lanForceRate = Cvar_Get ("sv_lanForceRate", "1", CVAR_ARCHIVE );
-#ifndef STANDALONE
-	sv_strictAuth = Cvar_Get ("sv_strictAuth", "0", CVAR_ARCHIVE );
-#endif
-	sv_banFile = Cvar_Get("sv_banFile", "serverbans.dat", CVAR_ARCHIVE);
-	sv_broadcastAll = Cvar_Get("sv_broadcastAll", "0", CVAR_ARCHIVE);
-	sv_randomClientSlot = Cvar_Get("sv_randomClientSlot", "1", CVAR_ARCHIVE);
+	sv_strictAuth = Cvar_Get ("sv_strictAuth", "1", CVAR_ARCHIVE );
 
 	// initialize bot cvars so they are listed and can be set before loading the botlib
 	SV_BotInitCvars();
 
 	// init the botlib here because we need the pre-compiler in the UI
 	SV_BotInitBotLib();
-	
-	// Load saved bans
-	Cbuf_AddText("rehashbans\n");
 }
 
 
@@ -721,11 +640,11 @@
 			if (cl->state >= CS_CONNECTED) {
 				// don't send a disconnect to a local client
 				if ( cl->netchan.remoteAddress.type != NA_LOOPBACK ) {
-					SV_SendServerCommand( cl, "print \"%s\n\"\n", message );
-					SV_SendServerCommand( cl, "disconnect \"%s\"", message );
+					SV_SendServerCommand( cl, "print \"%s\"", message );
+					SV_SendServerCommand( cl, "disconnect" );
 				}
 				// force a snapshot to be sent
-				cl->lastSnapshotTime = 0;
+				cl->nextSnapshotTime = -1;
 				SV_SendClientSnapshot( cl );
 			}
 		}
@@ -746,9 +665,7 @@
 		return;
 	}
 
-	Com_Printf( "----- Server Shutdown (%s) -----\n", finalmsg );
-
-	NET_LeaveMulticast6();
+	Com_Printf( "----- Server Shutdown -----\n" );
 
 	if ( svs.clients && !com_errorEntered ) {
 		SV_FinalMessage( finalmsg );
@@ -762,14 +679,8 @@
 	SV_ClearServer();
 
 	// free server static data
-	if(svs.clients)
-	{
-		int index;
-
-		for(index = 0; index < sv_maxclients->integer; index++)
-			SV_FreeClient(&svs.clients[index]);
-
-		Z_Free(svs.clients);
+	if ( svs.clients ) {
+		Z_Free( svs.clients );
 	}
 	Com_Memset( &svs, 0, sizeof( svs ) );
 
@@ -779,7 +690,6 @@
 	Com_Printf( "---------------------------\n" );
 
 	// disconnect any local clients
-	if( sv_killserver->integer != 2 )
-		CL_Disconnect( qfalse );
+	CL_Disconnect( qfalse );
 }
 

```

### `ioquake3`  — sha256 `a605f1aff5cd...`, 21807 bytes

_Diff stat: +5 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_init.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_init.c	2026-04-16 20:02:21.619760000 +0100
@@ -650,7 +650,7 @@
 	// systeminfo
 	Cvar_Get ("sv_cheats", "1", CVAR_SYSTEMINFO | CVAR_ROM );
 	sv_serverid = Cvar_Get ("sv_serverid", "0", CVAR_SYSTEMINFO | CVAR_ROM );
-	sv_pure = Cvar_Get ("sv_pure", "0", CVAR_SYSTEMINFO );
+	sv_pure = Cvar_Get ("sv_pure", "1", CVAR_SYSTEMINFO );
 #ifdef USE_VOIP
 	sv_voip = Cvar_Get("sv_voip", "1", CVAR_LATCH);
 	Cvar_CheckRange(sv_voip, 0, 1, qtrue);
@@ -671,7 +671,7 @@
 
 	sv_allowDownload = Cvar_Get ("sv_allowDownload", "0", CVAR_SERVERINFO);
 	Cvar_Get ("sv_dlURL", "", CVAR_SERVERINFO | CVAR_ARCHIVE);
-
+	
 	sv_master[0] = Cvar_Get("sv_master1", MASTER_SERVER_NAME, 0);
 	sv_master[1] = Cvar_Get("sv_master2", "directory.ioquake3.org", 0);
 	for(index = 2; index < MAX_MASTER_SERVERS; index++)
@@ -684,11 +684,9 @@
 	sv_mapChecksum = Cvar_Get ("sv_mapChecksum", "", CVAR_ROM);
 	sv_lanForceRate = Cvar_Get ("sv_lanForceRate", "1", CVAR_ARCHIVE );
 #ifndef STANDALONE
-	sv_strictAuth = Cvar_Get ("sv_strictAuth", "0", CVAR_ARCHIVE );
+	sv_strictAuth = Cvar_Get ("sv_strictAuth", "1", CVAR_ARCHIVE );
 #endif
 	sv_banFile = Cvar_Get("sv_banFile", "serverbans.dat", CVAR_ARCHIVE);
-	sv_broadcastAll = Cvar_Get("sv_broadcastAll", "0", CVAR_ARCHIVE);
-	sv_randomClientSlot = Cvar_Get("sv_randomClientSlot", "1", CVAR_ARCHIVE);
 
 	// initialize bot cvars so they are listed and can be set before loading the botlib
 	SV_BotInitCvars();
@@ -765,10 +763,10 @@
 	if(svs.clients)
 	{
 		int index;
-
+		
 		for(index = 0; index < sv_maxclients->integer; index++)
 			SV_FreeClient(&svs.clients[index]);
-
+		
 		Z_Free(svs.clients);
 	}
 	Com_Memset( &svs, 0, sizeof( svs ) );

```

### `quake3e`  — sha256 `78a997889b09...`, 27998 bytes

_Diff stat: +373 / -221 lines_

_(full diff is 33112 bytes — see files directly)_

### `openarena-engine`  — sha256 `5d57145c7dbc...`, 21833 bytes

_Diff stat: +22 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_init.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_init.c	2026-04-16 22:48:25.936964600 +0100
@@ -128,7 +128,7 @@
 	// spawning a new server
 	if ( sv.state == SS_GAME || sv.restarting ) {
 
-		// send the data to all relevant clients
+		// send the data to all relevent clients
 		for (i = 0, client = svs.clients; i < sv_maxclients->integer ; i++, client++) {
 			if ( client->state < CS_ACTIVE ) {
 				if ( client->state == CS_PRIMED )
@@ -374,12 +374,16 @@
 
 /*
 ================
-SV_TouchFile
+SV_TouchCGame
+
+  touch the cgame.vm so that a pure client can load it if it's in a seperate pk3
 ================
 */
-static void SV_TouchFile( const char *filename ) {
+static void SV_TouchCGame(void) {
 	fileHandle_t	f;
+	char filename[MAX_QPATH];
 
+	Com_sprintf( filename, sizeof(filename), "vm/%s.qvm", "cgame" );
 	FS_FOpenFileRead( filename, &f, qfalse );
 	if ( f ) {
 		FS_FCloseFile( f );
@@ -464,7 +468,7 @@
 	Cvar_Set("cl_paused", "0");
 
 	// get a new checksum feed and restart the file system
-	sv.checksumFeed = ( ((unsigned int)rand() << 16) ^ (unsigned int)rand() ) ^ Com_Milliseconds();
+	sv.checksumFeed = ( ((int) rand() << 16) ^ rand() ) ^ Com_Milliseconds();
 	FS_Restart( sv.checksumFeed );
 
 	CM_LoadMap( va("maps/%s.bsp", server), qfalse, &checksum );
@@ -570,11 +574,11 @@
 		p = FS_LoadedPakNames();
 		Cvar_Set( "sv_pakNames", p );
 
-		// we need to touch the cgame and ui qvm because they could be in
-		// separate pk3 files and the client will need to download the pk3
-		// files with the latest cgame and ui qvm to pass the pure check
-		SV_TouchFile( "vm/cgame.qvm" );
-		SV_TouchFile( "vm/ui.qvm" );
+		// if a dedicated pure server we need to touch the cgame because it could be in a
+		// seperate pk3 file and the client will need to load the latest cgame.qvm
+		if ( com_dedicated->integer ) {
+			SV_TouchCGame();
+		}
 	}
 	else {
 		Cvar_Set( "sv_paks", "" );
@@ -634,6 +638,7 @@
 	Cvar_Get ("fraglimit", "20", CVAR_SERVERINFO);
 	Cvar_Get ("timelimit", "0", CVAR_SERVERINFO);
 	sv_gametype = Cvar_Get ("g_gametype", "0", CVAR_SERVERINFO | CVAR_LATCH );
+	sv_dorestart = Cvar_Get ("sv_dorestart", "0",0);
 	Cvar_Get ("sv_keywords", "", CVAR_SERVERINFO);
 	sv_mapname = Cvar_Get ("mapname", "nomap", CVAR_SERVERINFO | CVAR_ROM);
 	sv_privateClients = Cvar_Get ("sv_privateClients", "0", CVAR_SERVERINFO);
@@ -650,11 +655,10 @@
 	// systeminfo
 	Cvar_Get ("sv_cheats", "1", CVAR_SYSTEMINFO | CVAR_ROM );
 	sv_serverid = Cvar_Get ("sv_serverid", "0", CVAR_SYSTEMINFO | CVAR_ROM );
-	sv_pure = Cvar_Get ("sv_pure", "0", CVAR_SYSTEMINFO );
+	sv_pure = Cvar_Get ("sv_pure", "1", CVAR_SYSTEMINFO );
 #ifdef USE_VOIP
-	sv_voip = Cvar_Get("sv_voip", "1", CVAR_LATCH);
+	sv_voip = Cvar_Get("sv_voip", "1", CVAR_SYSTEMINFO | CVAR_LATCH);
 	Cvar_CheckRange(sv_voip, 0, 1, qtrue);
-	sv_voipProtocol = Cvar_Get("sv_voipProtocol", sv_voip->integer ? "opus" : "", CVAR_SYSTEMINFO | CVAR_ROM );
 #endif
 	Cvar_Get ("sv_paks", "", CVAR_SYSTEMINFO | CVAR_ROM );
 	Cvar_Get ("sv_pakNames", "", CVAR_SYSTEMINFO | CVAR_ROM );
@@ -671,10 +675,9 @@
 
 	sv_allowDownload = Cvar_Get ("sv_allowDownload", "0", CVAR_SERVERINFO);
 	Cvar_Get ("sv_dlURL", "", CVAR_SERVERINFO | CVAR_ARCHIVE);
-
+	
 	sv_master[0] = Cvar_Get("sv_master1", MASTER_SERVER_NAME, 0);
-	sv_master[1] = Cvar_Get("sv_master2", "directory.ioquake3.org", 0);
-	for(index = 2; index < MAX_MASTER_SERVERS; index++)
+	for(index = 1; index < MAX_MASTER_SERVERS; index++)
 		sv_master[index] = Cvar_Get(va("sv_master%d", index + 1), "", CVAR_ARCHIVE);
 
 	sv_reconnectlimit = Cvar_Get ("sv_reconnectlimit", "3", 0);
@@ -684,11 +687,10 @@
 	sv_mapChecksum = Cvar_Get ("sv_mapChecksum", "", CVAR_ROM);
 	sv_lanForceRate = Cvar_Get ("sv_lanForceRate", "1", CVAR_ARCHIVE );
 #ifndef STANDALONE
-	sv_strictAuth = Cvar_Get ("sv_strictAuth", "0", CVAR_ARCHIVE );
+	sv_strictAuth = Cvar_Get ("sv_strictAuth", "1", CVAR_ARCHIVE );
 #endif
+	sv_public = Cvar_Get( "sv_public", "0", 0);
 	sv_banFile = Cvar_Get("sv_banFile", "serverbans.dat", CVAR_ARCHIVE);
-	sv_broadcastAll = Cvar_Get("sv_broadcastAll", "0", CVAR_ARCHIVE);
-	sv_randomClientSlot = Cvar_Get("sv_randomClientSlot", "1", CVAR_ARCHIVE);
 
 	// initialize bot cvars so they are listed and can be set before loading the botlib
 	SV_BotInitCvars();
@@ -765,10 +767,10 @@
 	if(svs.clients)
 	{
 		int index;
-
+		
 		for(index = 0; index < sv_maxclients->integer; index++)
 			SV_FreeClient(&svs.clients[index]);
-
+		
 		Z_Free(svs.clients);
 	}
 	Com_Memset( &svs, 0, sizeof( svs ) );

```
