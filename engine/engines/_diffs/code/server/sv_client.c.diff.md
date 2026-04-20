# Diff: `code/server/sv_client.c`
**Canonical:** `wolfcamql-src` (sha256 `9713bd4a8d74...`, 59275 bytes)

## Variants

### `quake3-source`  — sha256 `a93cb2bbda58...`, 46468 bytes

_Diff stat: +251 / -769 lines_

_(full diff is 48706 bytes — see files directly)_

### `ioquake3`  — sha256 `ea5de89a120d...`, 58523 bytes

_Diff stat: +29 / -56 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_client.c	2026-04-16 20:02:25.268783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_client.c	2026-04-16 20:02:21.619760000 +0100
@@ -55,8 +55,8 @@
 	int		i;
 	int		oldest;
 	int		oldestTime;
-	int oldestClientTime;
-	int clientChallenge;
+	int		oldestClientTime;
+	int		clientChallenge;
 	challenge_t	*challenge;
 	qboolean wasfound = qfalse;
 	char *gameName;
@@ -95,7 +95,7 @@
 	if (gameMismatch)
 	{
 		NET_OutOfBandPrint(NS_SERVER, from, "print\nGame mismatch: This is a %s server\n",
-						   com_gamename->string);
+			com_gamename->string);
 		return;
 	}
 
@@ -111,17 +111,17 @@
 		if(!challenge->connected && NET_CompareAdr(from, challenge->adr))
 		{
 			wasfound = qtrue;
-
+			
 			if(challenge->time < oldestClientTime)
 				oldestClientTime = challenge->time;
 		}
-
+		
 		if(wasfound && i >= MAX_CHALLENGES_MULTI)
 		{
 			i = MAX_CHALLENGES;
 			break;
 		}
-
+		
 		if(challenge->time < oldestTime)
 		{
 			oldestTime = challenge->time;
@@ -179,12 +179,12 @@
 			const char *game;
 
 			Com_DPrintf( "sending getIpAuthorize for %s\n", NET_AdrToString( from ));
-
+		
 			game = Cvar_VariableString( "fs_game" );
 			if (game[0] == 0) {
 				game = BASEGAME;
 			}
-
+			
 			// the 0 is for backwards compatibility with obsolete sv_allowanonymous flags
 			// getIpAuthorize <challenge> <IP> <game> 0 <auth-flag>
 			NET_OutOfBandPrint( NS_SERVER, svs.authorizeAddress,
@@ -198,7 +198,7 @@
 
 	challenge->pingTime = svs.time;
 	NET_OutOfBandPrint(NS_SERVER, challenge->adr, "challengeResponse %d %d %d",
-					   challenge->challenge, clientChallenge, com_protocol->integer);
+			   challenge->challenge, clientChallenge, com_protocol->integer);
 }
 
 #ifndef STANDALONE
@@ -251,7 +251,7 @@
 	}
 	if ( !Q_stricmp( s, "accept" ) ) {
 		NET_OutOfBandPrint(NS_SERVER, challengeptr->adr,
-						   "challengeResponse %d %d %d", challengeptr->challenge, challengeptr->clientChallenge, com_protocol->integer);
+			"challengeResponse %d %d %d", challengeptr->challenge, challengeptr->clientChallenge, com_protocol->integer);
 		return;
 	}
 	if ( !Q_stricmp( s, "unknown" ) ) {
@@ -331,16 +331,15 @@
 	int			challenge;
 	char		*password;
 	int			startIndex;
-	int randIndex;
 	intptr_t		denied;
 	int			count;
 	char		*ip;
 #ifdef LEGACY_PROTOCOL
-	qboolean 	compat = qfalse;
+	qboolean	compat = qfalse;
 #endif
 
 	Com_DPrintf ("SVC_DirectConnect ()\n");
-
+	
 	// Check whether this client is banned.
 	if(SV_IsBanned(&from, qfalse))
 	{
@@ -351,7 +350,7 @@
 	Q_strncpyz( userinfo, Cmd_Argv(1), sizeof(userinfo) );
 
 	version = atoi(Info_ValueForKey(userinfo, "protocol"));
-
+	
 #ifdef LEGACY_PROTOCOL
 	if(version > 0 && com_legacyprotocol->integer == version)
 		compat = qtrue;
@@ -361,7 +360,7 @@
 		if(version != com_protocol->integer)
 		{
 			NET_OutOfBandPrint(NS_SERVER, from, "print\nServer uses protocol version %i "
-								"(yours is %i).\n", com_protocol->integer, version);
+					   "(yours is %i).\n", com_protocol->integer, version);
 			Com_DPrintf("    rejected connect from version %i\n", version);
 			return;
 		}
@@ -494,14 +493,8 @@
 		startIndex = sv_privateClients->integer;
 	}
 
-	if (sv_randomClientSlot->integer) {
-		randIndex = rand() % sv_maxclients->integer;
-	} else {
-		randIndex = startIndex;
-	}
-
 	newcl = NULL;
-	for ( i = randIndex; i < sv_maxclients->integer ; i++ ) {
+	for ( i = startIndex; i < sv_maxclients->integer ; i++ ) {
 		cl = &svs.clients[i];
 		if (cl->state == CS_FREE) {
 			newcl = cl;
@@ -509,16 +502,6 @@
 		}
 	}
 
-	if (!newcl  &&  sv_randomClientSlot->integer) {
-		for ( i = startIndex; i < randIndex; i++ ) {
-			cl = &svs.clients[i];
-			if (cl->state == CS_FREE) {
-				newcl = cl;
-				break;
-			}
-		}
-	}
-
 	if ( !newcl ) {
 		if ( NET_IsLocalAddress( from ) ) {
 			count = 0;
@@ -626,14 +609,14 @@
 {
 #ifdef USE_VOIP
 	int index;
-
+	
 	for(index = client->queuedVoipIndex; index < client->queuedVoipPackets; index++)
 	{
 		index %= ARRAY_LEN(client->voipPacket);
-
+		
 		Z_Free(client->voipPacket[index]);
 	}
-
+	
 	client->queuedVoipPackets = 0;
 #endif
 
@@ -1392,9 +1375,9 @@
 			cl->state = CS_ACTIVE;
 			SV_SendClientSnapshot( cl );
 			SV_DropClient( cl, "Unpure Client. "
-                               "You may need to enable in-game downloads "
-                               "to connect to this server (set "
-                               "cl_allowDownload 1)" );
+				"You may need to enable in-game downloads "
+				"to connect to this server (set "
+				"cl_allowDownload 1)" );
 		}
 	}
 }
@@ -1456,11 +1439,11 @@
 
 	// snaps command
 	val = Info_ValueForKey (cl->userinfo, "snaps");
-
+	
 	if(strlen(val))
 	{
 		i = atoi(val);
-
+		
 		if(i < 1)
 			i = 1;
 		else if(i > sv_fps->integer)
@@ -1475,9 +1458,9 @@
 	{
 		// Reset last sent snapshot so we avoid desync between server frame time and snapshot send time
 		cl->lastSnapshotTime = 0;
-		cl->snapshotMsec = i;
+		cl->snapshotMsec = i;		
 	}
-
+	
 #ifdef USE_VOIP
 #ifdef LEGACY_PROTOCOL
 	if(cl->compat)
@@ -1936,7 +1919,7 @@
 	if (cl->messageAcknowledge < 0) {
 		// usually only hackers create messages like this
 		// it is more annoying for them to let them hanging
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 		SV_DropClient( cl, "DEBUG: illegible client message" );
 #endif
 		return;
@@ -1950,7 +1933,7 @@
 	if ((cl->reliableSequence - cl->reliableAcknowledge >= MAX_RELIABLE_COMMANDS) || (cl->reliableSequence - cl->reliableAcknowledge < 0)) {
 		// usually only hackers create messages like this
 		// it is more annoying for them to let them hanging
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 		SV_DropClient( cl, "DEBUG: illegible client message" );
 #endif
 		cl->reliableAcknowledge = cl->reliableSequence;
@@ -1994,16 +1977,6 @@
 	do {
 		c = MSG_ReadByte( msg );
 
-		// See if this is an extension command after the EOF, which means we
-		//  are using old speex protocol.
-		if ((c == clc_EOF) && (MSG_LookaheadByte( msg ) == clc_extension)) {
-			MSG_ReadByte( msg );  // throw the clc_extension byte away.
-			c = MSG_ReadByte( msg );
-			if (c == -1) {
-				c = clc_EOF;
-			}
-		}
-
 		if ( c == clc_EOF ) {
 			break;
 		}
@@ -2020,7 +1993,7 @@
 	} while ( 1 );
 
 	// skip legacy speex voip data
-	if ( c == clc_extension ) {
+	if ( c == clc_voipSpeex ) {
 #ifdef USE_VOIP
 		SV_UserVoip( cl, msg, qtrue );
 		c = MSG_ReadByte( msg );
@@ -2028,7 +2001,7 @@
 	}
 
 	// read optional voip data
-	if ( c == clc_voip ) {
+	if ( c == clc_voipOpus ) {
 #ifdef USE_VOIP
 		SV_UserVoip( cl, msg, qfalse );
 		c = MSG_ReadByte( msg );

```

### `quake3e`  — sha256 `7b237359f622...`, 67326 bytes

_Diff stat: +1232 / -897 lines_

_(full diff is 89819 bytes — see files directly)_

### `openarena-engine`  — sha256 `d736212d2cfb...`, 57760 bytes

_Diff stat: +50 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_client.c	2026-04-16 20:02:25.268783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_client.c	2026-04-16 22:48:25.936964600 +0100
@@ -55,8 +55,8 @@
 	int		i;
 	int		oldest;
 	int		oldestTime;
-	int oldestClientTime;
-	int clientChallenge;
+	int		oldestClientTime;
+	int		clientChallenge;
 	challenge_t	*challenge;
 	qboolean wasfound = qfalse;
 	char *gameName;
@@ -95,7 +95,7 @@
 	if (gameMismatch)
 	{
 		NET_OutOfBandPrint(NS_SERVER, from, "print\nGame mismatch: This is a %s server\n",
-						   com_gamename->string);
+			com_gamename->string);
 		return;
 	}
 
@@ -111,17 +111,17 @@
 		if(!challenge->connected && NET_CompareAdr(from, challenge->adr))
 		{
 			wasfound = qtrue;
-
+			
 			if(challenge->time < oldestClientTime)
 				oldestClientTime = challenge->time;
 		}
-
+		
 		if(wasfound && i >= MAX_CHALLENGES_MULTI)
 		{
 			i = MAX_CHALLENGES;
 			break;
 		}
-
+		
 		if(challenge->time < oldestTime)
 		{
 			oldestTime = challenge->time;
@@ -140,7 +140,7 @@
 	}
 
 	// always generate a new challenge number, so the client cannot circumvent sv_maxping
-	challenge->challenge = ( ((unsigned int)rand() << 16) ^ (unsigned int)rand() ) ^ svs.time;
+	challenge->challenge = ( (rand() << 16) ^ rand() ) ^ svs.time;
 	challenge->wasrefused = qfalse;
 	challenge->time = svs.time;
 
@@ -176,15 +176,17 @@
 		else
 		{
 			// otherwise send their ip to the authorize server
-			const char *game;
+			cvar_t	*fs;
+			char	game[1024];
 
 			Com_DPrintf( "sending getIpAuthorize for %s\n", NET_AdrToString( from ));
-
-			game = Cvar_VariableString( "fs_game" );
-			if (game[0] == 0) {
-				game = BASEGAME;
+		
+			strcpy(game, BASEGAME);
+			fs = Cvar_Get ("fs_game", "", CVAR_INIT|CVAR_SYSTEMINFO );
+			if (fs && fs->string[0] != 0) {
+				strcpy(game, fs->string);
 			}
-
+			
 			// the 0 is for backwards compatibility with obsolete sv_allowanonymous flags
 			// getIpAuthorize <challenge> <IP> <game> 0 <auth-flag>
 			NET_OutOfBandPrint( NS_SERVER, svs.authorizeAddress,
@@ -198,7 +200,7 @@
 
 	challenge->pingTime = svs.time;
 	NET_OutOfBandPrint(NS_SERVER, challenge->adr, "challengeResponse %d %d %d",
-					   challenge->challenge, clientChallenge, com_protocol->integer);
+			   challenge->challenge, clientChallenge, com_protocol->integer);
 }
 
 #ifndef STANDALONE
@@ -251,7 +253,7 @@
 	}
 	if ( !Q_stricmp( s, "accept" ) ) {
 		NET_OutOfBandPrint(NS_SERVER, challengeptr->adr,
-						   "challengeResponse %d %d %d", challengeptr->challenge, challengeptr->clientChallenge, com_protocol->integer);
+			"challengeResponse %d %d %d", challengeptr->challenge, challengeptr->clientChallenge, com_protocol->integer);
 		return;
 	}
 	if ( !Q_stricmp( s, "unknown" ) ) {
@@ -331,16 +333,15 @@
 	int			challenge;
 	char		*password;
 	int			startIndex;
-	int randIndex;
 	intptr_t		denied;
 	int			count;
 	char		*ip;
 #ifdef LEGACY_PROTOCOL
-	qboolean 	compat = qfalse;
+	qboolean	compat = qfalse;
 #endif
 
 	Com_DPrintf ("SVC_DirectConnect ()\n");
-
+	
 	// Check whether this client is banned.
 	if(SV_IsBanned(&from, qfalse))
 	{
@@ -351,7 +352,7 @@
 	Q_strncpyz( userinfo, Cmd_Argv(1), sizeof(userinfo) );
 
 	version = atoi(Info_ValueForKey(userinfo, "protocol"));
-
+	
 #ifdef LEGACY_PROTOCOL
 	if(version > 0 && com_legacyprotocol->integer == version)
 		compat = qtrue;
@@ -361,7 +362,7 @@
 		if(version != com_protocol->integer)
 		{
 			NET_OutOfBandPrint(NS_SERVER, from, "print\nServer uses protocol version %i "
-								"(yours is %i).\n", com_protocol->integer, version);
+					   "(yours is %i).\n", com_protocol->integer, version);
 			Com_DPrintf("    rejected connect from version %i\n", version);
 			return;
 		}
@@ -487,21 +488,15 @@
 
 	// check for privateClient password
 	password = Info_ValueForKey( userinfo, "password" );
-	if ( *password && !strcmp( password, sv_privatePassword->string ) ) {
+	if ( !strcmp( password, sv_privatePassword->string ) ) {
 		startIndex = 0;
 	} else {
 		// skip past the reserved slots
 		startIndex = sv_privateClients->integer;
 	}
 
-	if (sv_randomClientSlot->integer) {
-		randIndex = rand() % sv_maxclients->integer;
-	} else {
-		randIndex = startIndex;
-	}
-
 	newcl = NULL;
-	for ( i = randIndex; i < sv_maxclients->integer ; i++ ) {
+	for ( i = startIndex; i < sv_maxclients->integer ; i++ ) {
 		cl = &svs.clients[i];
 		if (cl->state == CS_FREE) {
 			newcl = cl;
@@ -509,16 +504,6 @@
 		}
 	}
 
-	if (!newcl  &&  sv_randomClientSlot->integer) {
-		for ( i = startIndex; i < randIndex; i++ ) {
-			cl = &svs.clients[i];
-			if (cl->state == CS_FREE) {
-				newcl = cl;
-				break;
-			}
-		}
-	}
-
 	if ( !newcl ) {
 		if ( NET_IsLocalAddress( from ) ) {
 			count = 0;
@@ -539,7 +524,7 @@
 			}
 		}
 		else {
-			NET_OutOfBandPrint( NS_SERVER, from, "print\nServer is full\n" );
+			NET_OutOfBandPrint( NS_SERVER, from, "print\nServer is full.\n" );
 			Com_DPrintf ("Rejected a connection.\n");
 			return;
 		}
@@ -626,14 +611,14 @@
 {
 #ifdef USE_VOIP
 	int index;
-
+	
 	for(index = client->queuedVoipIndex; index < client->queuedVoipPackets; index++)
 	{
 		index %= ARRAY_LEN(client->voipPacket);
-
+		
 		Z_Free(client->voipPacket[index]);
 	}
-
+	
 	client->queuedVoipPackets = 0;
 #endif
 
@@ -676,16 +661,6 @@
 	// Free all allocated data on the client structure
 	SV_FreeClient(drop);
 
-	// Reset the reliable sequence to the currently acknowledged command
-	// This prevents SV_AddServerCommand() from making another recursive call to SV_DropClient()
-	// if the client lacks sufficient space for another reliable command
-	// it also guarantees that the client receives both the print and disconnect commands
-	drop->reliableSequence = drop->reliableAcknowledge;
-	// Setting the gamestate message number to -1 ensures that SV_AddServerCommand()
-	// will not call SV_DropClient() again, even though it is unlikely the client
-	// will receive many server commands during the drop
-	drop->gamestateMessageNum = -1;
-
 	// tell everyone why they got dropped
 	SV_SendServerCommand( NULL, "print \"%s" S_COLOR_WHITE " %s\n\"", drop->name, reason );
 
@@ -698,7 +673,12 @@
 
 	if ( isBot ) {
 		SV_BotFreeClient( drop - svs.clients );
+	}
 
+	// nuke user info
+	SV_SetUserinfo( drop - svs.clients, "" );
+	
+	if ( isBot ) {
 		// bots shouldn't go zombie, as there's no real net connection.
 		drop->state = CS_FREE;
 	} else {
@@ -706,9 +686,6 @@
 		drop->state = CS_ZOMBIE;		// become free in a few seconds
 	}
 
-	// nuke user info
-	SV_SetUserinfo( drop - svs.clients, "" );
-
 	// if this was the last client on the server, send a heartbeat
 	// to the master so it is known the server is empty
 	// send a heartbeat now so the master will get up to date info
@@ -1015,7 +992,7 @@
 		if ( !(sv_allowDownload->integer & DLF_ENABLE) ||
 			(sv_allowDownload->integer & DLF_NO_UDP) ||
 			idPack || unreferenced ||
-			( cl->downloadSize = FS_BaseDir_FOpenFileRead( cl->downloadName, &cl->download ) ) < 0 ) {
+			( cl->downloadSize = FS_SV_FOpenFileRead( cl->downloadName, &cl->download ) ) < 0 ) {
 			// cannot auto-download file
 			if(unreferenced)
 			{
@@ -1391,10 +1368,7 @@
 			cl->lastSnapshotTime = 0;
 			cl->state = CS_ACTIVE;
 			SV_SendClientSnapshot( cl );
-			SV_DropClient( cl, "Unpure Client. "
-                               "You may need to enable in-game downloads "
-                               "to connect to this server (set "
-                               "cl_allowDownload 1)" );
+			SV_DropClient( cl, "Invalid .PK3 files. Enabling auto-download might help." );
 		}
 	}
 }
@@ -1456,11 +1430,11 @@
 
 	// snaps command
 	val = Info_ValueForKey (cl->userinfo, "snaps");
-
+	
 	if(strlen(val))
 	{
 		i = atoi(val);
-
+		
 		if(i < 1)
 			i = 1;
 		else if(i > sv_fps->integer)
@@ -1475,9 +1449,9 @@
 	{
 		// Reset last sent snapshot so we avoid desync between server frame time and snapshot send time
 		cl->lastSnapshotTime = 0;
-		cl->snapshotMsec = i;
+		cl->snapshotMsec = i;		
 	}
-
+	
 #ifdef USE_VOIP
 #ifdef LEGACY_PROTOCOL
 	if(cl->compat)
@@ -1485,8 +1459,8 @@
 	else
 #endif
 	{
-		val = Info_ValueForKey(cl->userinfo, "cl_voipProtocol");
-		cl->hasVoip = !Q_stricmp( val, "opus" );
+		val = Info_ValueForKey(cl->userinfo, "cl_voip");
+		cl->hasVoip = atoi(val);
 	}
 #endif
 
@@ -1605,7 +1579,8 @@
 	if (clientOK) {
 		// pass unknown strings to the game
 		if (!u->name && sv.state == SS_GAME && (cl->state == CS_ACTIVE || cl->state == CS_PRIMED)) {
-			Cmd_Args_Sanitize();
+			if(strcmp(Cmd_Argv(0), "say") && strcmp(Cmd_Argv(0), "say_team") )
+				Cmd_Args_Sanitize(); //remove \n, \r and ; from string. We don't do that for say-commands because it makes people mad (understandebly)
 			VM_Call( gvm, GAME_CLIENT_COMMAND, cl - svs.clients );
 		}
 	}
@@ -1820,7 +1795,7 @@
 }
 
 static
-void SV_UserVoip(client_t *cl, msg_t *msg, qboolean ignoreData)
+void SV_UserVoip(client_t *cl, msg_t *msg)
 {
 	int sender, generation, sequence, frames, packetsize;
 	uint8_t recips[(MAX_CLIENTS + 7) / 8];
@@ -1855,12 +1830,12 @@
 
 	MSG_ReadData(msg, encoded, packetsize);
 
-	if (ignoreData || SV_ShouldIgnoreVoipSender(cl))
+	if (SV_ShouldIgnoreVoipSender(cl))
 		return;   // Blacklisted, disabled, etc.
 
 	// !!! FIXME: see if we read past end of msg...
 
-	// !!! FIXME: reject if not opus data.
+	// !!! FIXME: reject if not speex narrowband codec.
 	// !!! FIXME: decide if this is bogus data?
 
 	// decide who needs this VoIP packet sent to them...
@@ -1936,7 +1911,7 @@
 	if (cl->messageAcknowledge < 0) {
 		// usually only hackers create messages like this
 		// it is more annoying for them to let them hanging
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 		SV_DropClient( cl, "DEBUG: illegible client message" );
 #endif
 		return;
@@ -1947,10 +1922,10 @@
 	// NOTE: when the client message is fux0red the acknowledgement numbers
 	// can be out of range, this could cause the server to send thousands of server
 	// commands which the server thinks are not yet acknowledged in SV_UpdateServerCommandsToClient
-	if ((cl->reliableSequence - cl->reliableAcknowledge >= MAX_RELIABLE_COMMANDS) || (cl->reliableSequence - cl->reliableAcknowledge < 0)) {
+	if (cl->reliableAcknowledge < cl->reliableSequence - MAX_RELIABLE_COMMANDS) {
 		// usually only hackers create messages like this
 		// it is more annoying for them to let them hanging
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 		SV_DropClient( cl, "DEBUG: illegible client message" );
 #endif
 		cl->reliableAcknowledge = cl->reliableSequence;
@@ -1976,7 +1951,7 @@
 		}
 		// if we can tell that the client has dropped the last
 		// gamestate we sent them, resend it
-		if ( cl->state != CS_ACTIVE && cl->messageAcknowledge > cl->gamestateMessageNum ) {
+		if ( cl->messageAcknowledge > cl->gamestateMessageNum ) {
 			Com_DPrintf( "%s : dropped gamestate, resending\n", cl->name );
 			SV_SendClientGameState( cl );
 		}
@@ -1994,16 +1969,6 @@
 	do {
 		c = MSG_ReadByte( msg );
 
-		// See if this is an extension command after the EOF, which means we
-		//  are using old speex protocol.
-		if ((c == clc_EOF) && (MSG_LookaheadByte( msg ) == clc_extension)) {
-			MSG_ReadByte( msg );  // throw the clc_extension byte away.
-			c = MSG_ReadByte( msg );
-			if (c == -1) {
-				c = clc_EOF;
-			}
-		}
-
 		if ( c == clc_EOF ) {
 			break;
 		}
@@ -2019,18 +1984,10 @@
 		}
 	} while ( 1 );
 
-	// skip legacy speex voip data
-	if ( c == clc_extension ) {
-#ifdef USE_VOIP
-		SV_UserVoip( cl, msg, qtrue );
-		c = MSG_ReadByte( msg );
-#endif
-	}
-
 	// read optional voip data
 	if ( c == clc_voip ) {
 #ifdef USE_VOIP
-		SV_UserVoip( cl, msg, qfalse );
+		SV_UserVoip( cl, msg );
 		c = MSG_ReadByte( msg );
 #endif
 	}

```
