# Diff: `code/server/sv_main.c`
**Canonical:** `wolfcamql-src` (sha256 `b78e45879e7f...`, 35235 bytes)

## Variants

### `quake3-source`  — sha256 `8128a9a64c80...`, 24596 bytes

_Diff stat: +100 / -520 lines_

_(full diff is 27637 bytes — see files directly)_

### `ioquake3`  — sha256 `8caa0abca110...`, 35524 bytes

_Diff stat: +31 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_main.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_main.c	2026-04-16 20:02:21.620759400 +0100
@@ -35,13 +35,13 @@
 cvar_t	*sv_timeout;			// seconds without any message
 cvar_t	*sv_zombietime;			// seconds to sink messages after disconnect
 cvar_t	*sv_rconPassword;		// password for remote server commands
-cvar_t	*sv_privatePassword;	// password for the privateClient slots
+cvar_t	*sv_privatePassword;		// password for the privateClient slots
 cvar_t	*sv_allowDownload;
 cvar_t	*sv_maxclients;
 
 cvar_t	*sv_privateClients;		// number of clients reserved for password
 cvar_t	*sv_hostname;
-cvar_t	*sv_master[MAX_MASTER_SERVERS];		// master server ip address
+cvar_t	*sv_master[MAX_MASTER_SERVERS];	// master server ip address
 cvar_t	*sv_reconnectlimit;		// minimum seconds between connect messages
 cvar_t	*sv_showloss;			// report when usercmds are lost
 cvar_t	*sv_padPackets;			// add nop bytes to messages
@@ -63,9 +63,6 @@
 #endif
 cvar_t	*sv_banFile;
 
-cvar_t *sv_broadcastAll;
-cvar_t *sv_randomClientSlot;
-
 serverBan_t serverBans[SERVER_MAXBANS];
 int serverBansCount = 0;
 
@@ -163,7 +160,7 @@
 	// doesn't cause a recursive drop client
 	if ( client->reliableSequence - client->reliableAcknowledge == MAX_RELIABLE_COMMANDS + 1 ) {
 		if ( client->gamestateMessageNum == -1 )  {
-			// invalid game state message
+			// invalid game state message 
 			// this can occur in SV_DropClient() to avoid calling it more than once
 			return;
 		}
@@ -280,7 +277,7 @@
 		{
 			sv_master[i]->modified = qfalse;
 			svs.masterResolveTime[i] = svs.time + MASTERDNS_MSEC;
-
+			
 			if(netenabled & NET_ENABLEV4)
 			{
 				Com_Printf("Resolving %s (IPv4)\n", sv_master[i]->string);
@@ -437,8 +434,8 @@
 		interval = now - bucket->lastTime;
 
 		// Reclaim expired buckets
-		if ( bucket->lastTime > 0 && ( interval > ( burst * period )  ||
-									  interval < 0 ) ) {
+		if ( bucket->lastTime > 0 && ( interval > ( burst * period ) ||
+					interval < 0 ) ) {
 			if ( bucket->prev != NULL ) {
 				bucket->prev->next = bucket->next;
 			} else {
@@ -614,7 +611,7 @@
 	// Prevent using getinfo as an amplifier
 	if ( SVC_RateLimitAddress( from, 10, 1000 ) ) {
 		Com_DPrintf( "SVC_Info: rate limit from %s exceeded, dropping request\n",
-					 NET_AdrToString( from ) );
+			NET_AdrToString( from ) );
 		return;
 	}
 
@@ -1026,13 +1023,36 @@
 
 /*
 ==================
+SV_FrameMsec
+Return time in millseconds until processing of the next server frame.
+==================
+*/
+int SV_FrameMsec(void)
+{
+	if(sv_fps)
+	{
+		int frameMsec;
+		
+		frameMsec = 1000.0f / sv_fps->value;
+		
+		if(frameMsec < sv.timeResidual)
+			return 0;
+		else
+			return frameMsec - sv.timeResidual;
+	}
+	else
+		return 1;
+}
+
+/*
+==================
 SV_Frame
 
 Player movement occurs as a result of packet events, which
 happen before SV_Frame is called
 ==================
 */
-void SV_Frame( int msec, double fmsec ) {
+void SV_Frame( int msec ) {
 	int		frameMsec;
 	int		startTime;
 
@@ -1143,7 +1163,6 @@
 	SV_MasterHeartbeat(HEARTBEAT_FOR_MASTER);
 }
 
-
 /*
 ====================
 SV_RateMsec

```

### `quake3e`  — sha256 `be6f925e85de...`, 40407 bytes

_Diff stat: +565 / -313 lines_

_(full diff is 45231 bytes — see files directly)_

### `openarena-engine`  — sha256 `0df972d9a84a...`, 35487 bytes

_Diff stat: +51 / -33 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_main.c	2026-04-16 20:02:25.269783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_main.c	2026-04-16 22:48:25.937963500 +0100
@@ -24,7 +24,6 @@
 
 #ifdef USE_VOIP
 cvar_t *sv_voip;
-cvar_t *sv_voipProtocol;
 #endif
 
 serverStatic_t	svs;				// persistant server info
@@ -35,13 +34,13 @@
 cvar_t	*sv_timeout;			// seconds without any message
 cvar_t	*sv_zombietime;			// seconds to sink messages after disconnect
 cvar_t	*sv_rconPassword;		// password for remote server commands
-cvar_t	*sv_privatePassword;	// password for the privateClient slots
+cvar_t	*sv_privatePassword;		// password for the privateClient slots
 cvar_t	*sv_allowDownload;
 cvar_t	*sv_maxclients;
 
 cvar_t	*sv_privateClients;		// number of clients reserved for password
 cvar_t	*sv_hostname;
-cvar_t	*sv_master[MAX_MASTER_SERVERS];		// master server ip address
+cvar_t	*sv_master[MAX_MASTER_SERVERS];	// master server ip address
 cvar_t	*sv_reconnectlimit;		// minimum seconds between connect messages
 cvar_t	*sv_showloss;			// report when usercmds are lost
 cvar_t	*sv_padPackets;			// add nop bytes to messages
@@ -55,17 +54,16 @@
 cvar_t	*sv_minPing;
 cvar_t	*sv_maxPing;
 cvar_t	*sv_gametype;
+cvar_t	*sv_dorestart;
 cvar_t	*sv_pure;
 cvar_t	*sv_floodProtect;
 cvar_t	*sv_lanForceRate; // dedicated 1 (LAN) server forces local client rates to 99999 (bug #491)
 #ifndef STANDALONE
 cvar_t	*sv_strictAuth;
 #endif
+cvar_t	*sv_public;
 cvar_t	*sv_banFile;
 
-cvar_t *sv_broadcastAll;
-cvar_t *sv_randomClientSlot;
-
 serverBan_t serverBans[SERVER_MAXBANS];
 int serverBansCount = 0;
 
@@ -162,12 +160,6 @@
 	// we check == instead of >= so a broadcast print added by SV_DropClient()
 	// doesn't cause a recursive drop client
 	if ( client->reliableSequence - client->reliableAcknowledge == MAX_RELIABLE_COMMANDS + 1 ) {
-		if ( client->gamestateMessageNum == -1 )  {
-			// invalid game state message
-			// this can occur in SV_DropClient() to avoid calling it more than once
-			return;
-		}
-
 		Com_Printf( "===== pending server commands =====\n" );
 		for ( i = client->reliableAcknowledge + 1 ; i <= client->reliableSequence ; i++ ) {
 			Com_Printf( "cmd %5d: %s\n", i, client->reliableCommands[ i & (MAX_RELIABLE_COMMANDS-1) ] );
@@ -218,7 +210,7 @@
 		Com_Printf ("broadcast: %s\n", SV_ExpandNewlines((char *)message) );
 	}
 
-	// send the data to all relevant clients
+	// send the data to all relevent clients
 	for (j = 0, client = svs.clients; j < sv_maxclients->integer ; j++, client++) {
 		SV_AddServerCommand( client, (char *)message );
 	}
@@ -245,7 +237,6 @@
 ================
 */
 #define	HEARTBEAT_MSEC	300*1000
-#define	MASTERDNS_MSEC	24*60*60*1000
 void SV_MasterHeartbeat(const char *message)
 {
 	static netadr_t	adr[MAX_MASTER_SERVERS][2]; // [2] for v4 and v6 address for the same address string.
@@ -256,7 +247,7 @@
 	netenabled = Cvar_VariableIntegerValue("net_enabled");
 
 	// "dedicated 1" is for lan play, "dedicated 2" is for inet public play
-	if (!com_dedicated || com_dedicated->integer != 2 || !(netenabled & (NET_ENABLEV4 | NET_ENABLEV6)))
+	if ( ( (!com_dedicated || com_dedicated->integer != 2) && !(sv_public->integer) ) || !(netenabled & (NET_ENABLEV4 | NET_ENABLEV6)))
 		return;		// only dedicated servers send heartbeats
 
 	// if not time yet, don't send anything
@@ -274,13 +265,13 @@
 		if(!sv_master[i]->string[0])
 			continue;
 
-		// see if we haven't already resolved the name or if it's been over 24 hours
-		// resolving usually causes hitches on win95, so only do it when needed
-		if (sv_master[i]->modified || svs.time > svs.masterResolveTime[i])
+		// see if we haven't already resolved the name
+		// resolving usually causes hitches on win95, so only
+		// do it when needed
+		if(sv_master[i]->modified || (adr[i][0].type == NA_BAD && adr[i][1].type == NA_BAD))
 		{
 			sv_master[i]->modified = qfalse;
-			svs.masterResolveTime[i] = svs.time + MASTERDNS_MSEC;
-
+			
 			if(netenabled & NET_ENABLEV4)
 			{
 				Com_Printf("Resolving %s (IPv4)\n", sv_master[i]->string);
@@ -314,11 +305,16 @@
 				else
 					Com_Printf( "%s has no IPv6 address.\n", sv_master[i]->string);
 			}
-		}
 
-		if(adr[i][0].type == NA_BAD && adr[i][1].type == NA_BAD)
-		{
-			continue;
+			if(adr[i][0].type == NA_BAD && adr[i][1].type == NA_BAD)
+			{
+				// if the address failed to resolve, clear it
+				// so we don't take repeated dns hits
+				Com_Printf("Couldn't resolve address: %s\n", sv_master[i]->string);
+				Cvar_Set(sv_master[i]->name, "");
+				sv_master[i]->modified = qfalse;
+				continue;
+			}
 		}
 
 
@@ -437,8 +433,8 @@
 		interval = now - bucket->lastTime;
 
 		// Reclaim expired buckets
-		if ( bucket->lastTime > 0 && ( interval > ( burst * period )  ||
-									  interval < 0 ) ) {
+		if ( bucket->lastTime > 0 && ( interval > ( burst * period ) ||
+					interval < 0 ) ) {
 			if ( bucket->prev != NULL ) {
 				bucket->prev->next = bucket->next;
 			} else {
@@ -493,7 +489,7 @@
 		int expired = interval / period;
 		int expiredRemainder = interval % period;
 
-		if ( expired > bucket->burst || interval < 0 ) {
+		if ( expired > bucket->burst ) {
 			bucket->burst = 0;
 			bucket->lastTime = now;
 		} else {
@@ -614,7 +610,7 @@
 	// Prevent using getinfo as an amplifier
 	if ( SVC_RateLimitAddress( from, 10, 1000 ) ) {
 		Com_DPrintf( "SVC_Info: rate limit from %s exceeded, dropping request\n",
-					 NET_AdrToString( from ) );
+			NET_AdrToString( from ) );
 		return;
 	}
 
@@ -671,8 +667,8 @@
 	Info_SetValueForKey(infostring, "g_needpass", va("%d", Cvar_VariableIntegerValue("g_needpass")));
 
 #ifdef USE_VOIP
-	if (sv_voipProtocol->string && *sv_voipProtocol->string) {
-		Info_SetValueForKey( infostring, "voip", sv_voipProtocol->string );
+	if (sv_voip->integer) {
+		Info_SetValueForKey( infostring, "voip", va("%i", sv_voip->integer ) );
 	}
 #endif
 
@@ -1026,13 +1022,36 @@
 
 /*
 ==================
+SV_FrameMsec
+Return time in millseconds until processing of the next server frame.
+==================
+*/
+int SV_FrameMsec()
+{
+	if(sv_fps)
+	{
+		int frameMsec;
+		
+		frameMsec = 1000.0f / sv_fps->value;
+		
+		if(frameMsec < sv.timeResidual)
+			return 0;
+		else
+			return frameMsec - sv.timeResidual;
+	}
+	else
+		return 1;
+}
+
+/*
+==================
 SV_Frame
 
 Player movement occurs as a result of packet events, which
 happen before SV_Frame is called
 ==================
 */
-void SV_Frame( int msec, double fmsec ) {
+void SV_Frame( int msec ) {
 	int		frameMsec;
 	int		startTime;
 
@@ -1143,7 +1162,6 @@
 	SV_MasterHeartbeat(HEARTBEAT_FOR_MASTER);
 }
 
-
 /*
 ====================
 SV_RateMsec
@@ -1204,7 +1222,7 @@
 ====================
 */
 
-int SV_SendQueuedPackets(void)
+int SV_SendQueuedPackets()
 {
 	int numBlocks;
 	int dlStart, deltaT, delayT;

```
