# Diff: `code/server/sv_ccmds.c`
**Canonical:** `wolfcamql-src` (sha256 `2a089b0abfbb...`, 39874 bytes)

## Variants

### `quake3-source`  — sha256 `255ea7a18b3a...`, 18813 bytes

_Diff stat: +63 / -1037 lines_

_(full diff is 33053 bytes — see files directly)_

### `ioquake3`  — sha256 `66b9c1855790...`, 36119 bytes

_Diff stat: +12 / -154 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_ccmds.c	2026-04-16 20:02:25.268783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_ccmds.c	2026-04-16 20:02:21.618758900 +0100
@@ -156,69 +156,20 @@
 	qboolean	killBots, cheat;
 	char		expanded[MAX_QPATH];
 	char		mapname[MAX_QPATH];
-	char gameType[16];
-	int i;
-	qboolean foundAlternateMap;
-
-#if 0
-	if (com_protocol->integer == PROTOCOL_Q3) {
-		Com_Printf("can't start server with protocol %d\n", PROTOCOL_Q3);
-		return;
-	}
-#endif
 
 	map = Cmd_Argv(1);
 	if ( !map ) {
 		return;
 	}
 
-	if (Cmd_Argv(2)) {
-		Q_strncpyz(gameType, Cmd_Argv(2), sizeof(gameType));
-	} else {
-		gameType[0] = '\0';
-	}
-
-	// check if no map is specified to issue help message
-	if (strlen(map) == 0) {
-		cmd = Cmd_Argv(0);
-
-		//FIXME spdevmap ...
-
-		if ( !Q_stricmp( cmd, "devmap" ) ) {
-			Com_Printf("usage: devmap <map name> [ffa | duel | race | tdm | ca | ctf | oneflag | ob | har | ft | dom | ad | rr]\n");
-			return;
-		}
-	}
-
 	// make sure the level exists before trying to change, so that
 	// a typo at the server console won't end the game
 	Com_sprintf (expanded, sizeof(expanded), "maps/%s.bsp", map);
 	if ( FS_ReadFile (expanded, NULL) == -1 ) {
 		Com_Printf ("Can't find map %s\n", expanded);
-		i = 0;
-		foundAlternateMap = qfalse;
-		while (1) {
-			if (MapNames[i].oldName == NULL) {
-				break;
-			}
-			if (!Q_stricmp(expanded, MapNames[i].oldName)) {
-				foundAlternateMap = qtrue;
-				break;
-			}
-			if (!Q_stricmp(expanded, MapNames[i].newName)) {
-				foundAlternateMap = qtrue;
-				break;
-			}
-			i++;
-		}
-
-		if (!foundAlternateMap) {
-			return;
-		}
+		return;
 	}
 
-	Cvar_Set("protocol", va("%i", SERVER_PROTOCOL));
-
 	// force latched values to get set
 	Cvar_Get ("g_gametype", "0", CVAR_SERVERINFO | CVAR_USERINFO | CVAR_LATCH );
 
@@ -247,38 +198,6 @@
 		if( sv_gametype->integer == GT_SINGLE_PLAYER ) {
 			Cvar_SetValue( "g_gametype", GT_FFA );
 		}
-
-		// allow game type string like quake live
-		// actf ad ca ctf dom duel oneflag ffa ft har race rr tdm quadhog infected, ...
-		if (gameType[0] != '\0') {
-			if (!Q_stricmp(gameType, "ffa")) {
-				Cvar_SetValue("g_gametype", GT_FFA);
-			} else if (!Q_stricmp(gameType, "duel")) {
-				Cvar_SetValue("g_gametype", GT_TOURNAMENT);
-			} else if (!Q_stricmp(gameType, "race")) {
-				Cvar_SetValue("g_gametype", GT_RACE);
-			} else if (!Q_stricmp(gameType, "tdm")) {
-				Cvar_SetValue("g_gametype", GT_TEAM);
-			} else if (!Q_stricmp(gameType, "ca")) {
-				Cvar_SetValue("g_gametype", GT_CA);
-			} else if (!Q_stricmp(gameType, "ctf")) {
-				Cvar_SetValue("g_gametype", GT_CTF);
-			} else if (!Q_stricmp(gameType, "oneflag")) {
-				Cvar_SetValue("g_gametype", GT_1FCTF);
-			} else if (!Q_stricmp(gameType, "ob")) {
-				Cvar_SetValue("g_gametype", GT_OBELISK);
-			} else if (!Q_stricmp(gameType, "har")) {
-				Cvar_SetValue("g_gametype", GT_HARVESTER);
-			} else if (!Q_stricmp(gameType, "ft")) {
-				Cvar_SetValue("g_gametype", GT_FREEZETAG);
-			} else if (!Q_stricmp(gameType, "dom")) {
-				Cvar_SetValue("g_gametype", GT_DOMINATION);
-			} else if (!Q_stricmp(gameType, "ad")) {
-				Cvar_SetValue("g_gametype", GT_CTFS);
-			} else if (!Q_stricmp(gameType, "rr")) {
-				Cvar_SetValue("g_gametype", GT_RED_ROVER);
-			}
-		}
 	}
 
 	// save the map name here cause on a map restart we reload the q3config.cfg
@@ -299,64 +218,6 @@
 	}
 }
 
-static void SV_DevmapNextOrPrev (qboolean next)
-{
-	char **filenames;
-	int nfiles;
-	int i;
-	char mapname[MAX_QPATH];
-	char currentMapname[MAX_QPATH];
-	qboolean foundCurrentMap;
-	int len;
-
-	Com_sprintf(currentMapname, sizeof(currentMapname), "%s.bsp", Cvar_VariableString("mapname"));
-	Com_Printf("current map: %s\n", currentMapname);
-	len = strlen(currentMapname);
-	filenames = FS_ListFiles("maps", "bsp", &nfiles);
-    FS_SortFileList(filenames, nfiles);
-
-	foundCurrentMap = qfalse;
-	for (i = 0;  i < nfiles;  i++) {
-		//Com_Printf("%s\n", filenames[i]);
-		if (!Q_stricmpn(currentMapname, filenames[i], len)) {
-			foundCurrentMap = qtrue;
-			break;
-		}
-	}
-
-	if (foundCurrentMap) {
-		if (next) {
-			i++;
-		} else {
-			i--;
-		}
-		if (i >= nfiles) {
-			i = 0;
-		} else if (i < 0) {
-			i = nfiles - 1;
-		}
-
-		Q_strncpyz(mapname, filenames[i], sizeof(mapname));
-		len = strlen(mapname);
-		mapname[len - 4] = '\0';
-		Cbuf_ExecuteText(EXEC_NOW, va("devmap %s\n", mapname));
-	} else {
-		Com_Printf("couldn't find map\n");
-	}
-
-	FS_FreeFileList(filenames);
-}
-
-static void SV_DevmapNext_f (void)
-{
-	SV_DevmapNextOrPrev(qtrue);
-}
-
-static void SV_DevmapPrev_f (void)
-{
-	SV_DevmapNextOrPrev(qfalse);
-}
-
 /*
 ================
 SV_MapRestart_f
@@ -777,7 +638,7 @@
 	fileHandle_t readfrom;
 	char *textbuf, *curpos, *maskpos, *newlinepos, *endpos;
 	char filepath[MAX_QPATH];
-
+	
 	serverBansCount = 0;
 	
 	if(!sv_banFile->string || !*sv_banFile->string)
@@ -861,7 +722,7 @@
 	
 	if(!sv_banFile->string || !*sv_banFile->string)
 		return;
-
+	
 	Com_sprintf(filepath, sizeof(filepath), "%s/%s", FS_GetCurrentGameDir(), sv_banFile->string);
 
 	if((writeto = FS_BaseDir_FOpenFileWrite_HomeState(filepath)))
@@ -1003,7 +864,7 @@
 		client_t *cl;
 		
 		// client num.
-
+		
 		cl = SV_GetPlayerByNum();
 
 		if(!cl)
@@ -1107,13 +968,13 @@
 	int index, count = 0, todel, mask;
 	netadr_t ip;
 	char *banstring;
-
+	
 	// make sure server is running
 	if ( !com_sv_running->integer ) {
 		Com_Printf( "Server is not running.\n" );
 		return;
 	}
-
+	
 	if(Cmd_Argc() != 2)
 	{
 		Com_Printf ("Usage: %s (ip[/subnet] | num)\n", Cmd_Argv(0));
@@ -1204,7 +1065,7 @@
 		Com_Printf( "Server is not running.\n" );
 		return;
 	}
-
+	
 	// List all bans
 	for(index = count = 0; index < serverBansCount; index++)
 	{
@@ -1335,10 +1196,10 @@
 		}
 
 		Com_Printf ("%s", cl->name);
-
+		
 		l = 16 - SV_Strlen(cl->name);
 		j = 0;
-
+		
 		do
 		{
 			Com_Printf (" ");
@@ -1351,7 +1212,7 @@
 		Com_Printf ("^7%s", s);
 		l = 39 - strlen(s);
 		j = 0;
-
+		
 		do
 		{
 			Com_Printf(" ");
@@ -1605,7 +1466,7 @@
 */
 static void SV_CompleteMapName( char *args, int argNum ) {
 	if( argNum == 2 ) {
-		Field_CompleteFilename( "maps", "bsp", NULL, qtrue, qfalse, NULL );
+		Field_CompleteFilename( "maps", "bsp", NULL, qtrue, qfalse );
 	}
 }
 
@@ -1695,7 +1556,7 @@
 		Cmd_AddCommand ("sayto", SV_ConSayto_f);
 		Cmd_SetCommandCompletionFunc( "sayto", SV_CompletePlayerName );
 	}
-
+	
 	Cmd_AddCommand("rehashbans", SV_RehashBans_f);
 	Cmd_AddCommand("listbans", SV_ListBans_f);
 	Cmd_AddCommand("banaddr", SV_BanAddr_f);
@@ -1703,9 +1564,6 @@
 	Cmd_AddCommand("bandel", SV_BanDel_f);
 	Cmd_AddCommand("exceptdel", SV_ExceptDel_f);
 	Cmd_AddCommand("flushbans", SV_FlushBans_f);
-
-	Cmd_AddCommand("devmapnext", SV_DevmapNext_f);
-	Cmd_AddCommand("devmapprev", SV_DevmapPrev_f);
 }
 
 /*

```

### `quake3e`  — sha256 `f956c94db90d...`, 37481 bytes

_Diff stat: +324 / -426 lines_

_(full diff is 35182 bytes — see files directly)_

### `openarena-engine`  — sha256 `b05ec3d8e213...`, 33911 bytes

_Diff stat: +39 / -293 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_ccmds.c	2026-04-16 20:02:25.268783500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_ccmds.c	2026-04-16 22:48:25.935962700 +0100
@@ -156,72 +156,26 @@
 	qboolean	killBots, cheat;
 	char		expanded[MAX_QPATH];
 	char		mapname[MAX_QPATH];
-	char gameType[16];
-	int i;
-	qboolean foundAlternateMap;
-
-#if 0
-	if (com_protocol->integer == PROTOCOL_Q3) {
-		Com_Printf("can't start server with protocol %d\n", PROTOCOL_Q3);
-		return;
-	}
-#endif
 
 	map = Cmd_Argv(1);
 	if ( !map ) {
 		return;
 	}
 
-	if (Cmd_Argv(2)) {
-		Q_strncpyz(gameType, Cmd_Argv(2), sizeof(gameType));
-	} else {
-		gameType[0] = '\0';
-	}
-
-	// check if no map is specified to issue help message
-	if (strlen(map) == 0) {
-		cmd = Cmd_Argv(0);
-
-		//FIXME spdevmap ...
-
-		if ( !Q_stricmp( cmd, "devmap" ) ) {
-			Com_Printf("usage: devmap <map name> [ffa | duel | race | tdm | ca | ctf | oneflag | ob | har | ft | dom | ad | rr]\n");
-			return;
-		}
-	}
-
 	// make sure the level exists before trying to change, so that
 	// a typo at the server console won't end the game
 	Com_sprintf (expanded, sizeof(expanded), "maps/%s.bsp", map);
 	if ( FS_ReadFile (expanded, NULL) == -1 ) {
 		Com_Printf ("Can't find map %s\n", expanded);
-		i = 0;
-		foundAlternateMap = qfalse;
-		while (1) {
-			if (MapNames[i].oldName == NULL) {
-				break;
-			}
-			if (!Q_stricmp(expanded, MapNames[i].oldName)) {
-				foundAlternateMap = qtrue;
-				break;
-			}
-			if (!Q_stricmp(expanded, MapNames[i].newName)) {
-				foundAlternateMap = qtrue;
-				break;
-			}
-			i++;
-		}
-
-		if (!foundAlternateMap) {
-			return;
-		}
+		return;
 	}
 
-	Cvar_Set("protocol", va("%i", SERVER_PROTOCOL));
-
 	// force latched values to get set
 	Cvar_Get ("g_gametype", "0", CVAR_SERVERINFO | CVAR_USERINFO | CVAR_LATCH );
 
+	//Notice that we have done a restart
+	sv_dorestart->integer = 0;
+
 	cmd = Cmd_Argv(0);
 	if( Q_stricmpn( cmd, "sp", 2 ) == 0 ) {
 		Cvar_SetValue( "g_gametype", GT_SINGLE_PLAYER );
@@ -247,38 +201,6 @@
 		if( sv_gametype->integer == GT_SINGLE_PLAYER ) {
 			Cvar_SetValue( "g_gametype", GT_FFA );
 		}
-
-		// allow game type string like quake live
-		// actf ad ca ctf dom duel oneflag ffa ft har race rr tdm quadhog infected, ...
-		if (gameType[0] != '\0') {
-			if (!Q_stricmp(gameType, "ffa")) {
-				Cvar_SetValue("g_gametype", GT_FFA);
-			} else if (!Q_stricmp(gameType, "duel")) {
-				Cvar_SetValue("g_gametype", GT_TOURNAMENT);
-			} else if (!Q_stricmp(gameType, "race")) {
-				Cvar_SetValue("g_gametype", GT_RACE);
-			} else if (!Q_stricmp(gameType, "tdm")) {
-				Cvar_SetValue("g_gametype", GT_TEAM);
-			} else if (!Q_stricmp(gameType, "ca")) {
-				Cvar_SetValue("g_gametype", GT_CA);
-			} else if (!Q_stricmp(gameType, "ctf")) {
-				Cvar_SetValue("g_gametype", GT_CTF);
-			} else if (!Q_stricmp(gameType, "oneflag")) {
-				Cvar_SetValue("g_gametype", GT_1FCTF);
-			} else if (!Q_stricmp(gameType, "ob")) {
-				Cvar_SetValue("g_gametype", GT_OBELISK);
-			} else if (!Q_stricmp(gameType, "har")) {
-				Cvar_SetValue("g_gametype", GT_HARVESTER);
-			} else if (!Q_stricmp(gameType, "ft")) {
-				Cvar_SetValue("g_gametype", GT_FREEZETAG);
-			} else if (!Q_stricmp(gameType, "dom")) {
-				Cvar_SetValue("g_gametype", GT_DOMINATION);
-			} else if (!Q_stricmp(gameType, "ad")) {
-				Cvar_SetValue("g_gametype", GT_CTFS);
-			} else if (!Q_stricmp(gameType, "rr")) {
-				Cvar_SetValue("g_gametype", GT_RED_ROVER);
-			}
-		}
 	}
 
 	// save the map name here cause on a map restart we reload the q3config.cfg
@@ -299,64 +221,6 @@
 	}
 }
 
-static void SV_DevmapNextOrPrev (qboolean next)
-{
-	char **filenames;
-	int nfiles;
-	int i;
-	char mapname[MAX_QPATH];
-	char currentMapname[MAX_QPATH];
-	qboolean foundCurrentMap;
-	int len;
-
-	Com_sprintf(currentMapname, sizeof(currentMapname), "%s.bsp", Cvar_VariableString("mapname"));
-	Com_Printf("current map: %s\n", currentMapname);
-	len = strlen(currentMapname);
-	filenames = FS_ListFiles("maps", "bsp", &nfiles);
-    FS_SortFileList(filenames, nfiles);
-
-	foundCurrentMap = qfalse;
-	for (i = 0;  i < nfiles;  i++) {
-		//Com_Printf("%s\n", filenames[i]);
-		if (!Q_stricmpn(currentMapname, filenames[i], len)) {
-			foundCurrentMap = qtrue;
-			break;
-		}
-	}
-
-	if (foundCurrentMap) {
-		if (next) {
-			i++;
-		} else {
-			i--;
-		}
-		if (i >= nfiles) {
-			i = 0;
-		} else if (i < 0) {
-			i = nfiles - 1;
-		}
-
-		Q_strncpyz(mapname, filenames[i], sizeof(mapname));
-		len = strlen(mapname);
-		mapname[len - 4] = '\0';
-		Cbuf_ExecuteText(EXEC_NOW, va("devmap %s\n", mapname));
-	} else {
-		Com_Printf("couldn't find map\n");
-	}
-
-	FS_FreeFileList(filenames);
-}
-
-static void SV_DevmapNext_f (void)
-{
-	SV_DevmapNextOrPrev(qtrue);
-}
-
-static void SV_DevmapPrev_f (void)
-{
-	SV_DevmapNextOrPrev(qfalse);
-}
-
 /*
 ================
 SV_MapRestart_f
@@ -401,9 +265,10 @@
 
 	// check for changes in variables that can't just be restarted
 	// check for maxclients change
-	if ( sv_maxclients->modified || sv_gametype->modified ) {
+	if ( sv_maxclients->modified || sv_gametype->modified || sv_dorestart->integer ) {
 		char	mapname[MAX_QPATH];
 
+		sv_dorestart->integer = 0;
 		Com_Printf( "variable change -- restarting.\n" );
 		// restart the map the slow way
 		Q_strncpyz( mapname, Cvar_VariableString( "mapname" ), sizeof( mapname ) );
@@ -777,7 +642,12 @@
 	fileHandle_t readfrom;
 	char *textbuf, *curpos, *maskpos, *newlinepos, *endpos;
 	char filepath[MAX_QPATH];
-
+	
+	// make sure server is running
+	if ( !com_sv_running->integer ) {
+		return;
+	}
+	
 	serverBansCount = 0;
 	
 	if(!sv_banFile->string || !*sv_banFile->string)
@@ -785,7 +655,7 @@
 
 	Com_sprintf(filepath, sizeof(filepath), "%s/%s", FS_GetCurrentGameDir(), sv_banFile->string);
 
-	if((filelen = FS_BaseDir_FOpenFileRead(filepath, &readfrom)) >= 0)
+	if((filelen = FS_SV_FOpenFileRead(filepath, &readfrom)) >= 0)
 	{
 		if(filelen < 2)
 		{
@@ -861,10 +731,10 @@
 	
 	if(!sv_banFile->string || !*sv_banFile->string)
 		return;
-
+	
 	Com_sprintf(filepath, sizeof(filepath), "%s/%s", FS_GetCurrentGameDir(), sv_banFile->string);
 
-	if((writeto = FS_BaseDir_FOpenFileWrite_HomeState(filepath)))
+	if((writeto = FS_SV_FOpenFileWrite(filepath)))
 	{
 		char writebuf[128];
 		serverBan_t *curban;
@@ -980,7 +850,7 @@
 		return;
 	}
 
-	if(serverBansCount >= ARRAY_LEN(serverBans))
+	if(serverBansCount > ARRAY_LEN(serverBans))
 	{
 		Com_Printf ("Error: Maximum number of bans/exceptions exceeded.\n");
 		return;
@@ -1003,7 +873,7 @@
 		client_t *cl;
 		
 		// client num.
-
+		
 		cl = SV_GetPlayerByNum();
 
 		if(!cl)
@@ -1107,13 +977,13 @@
 	int index, count = 0, todel, mask;
 	netadr_t ip;
 	char *banstring;
-
+	
 	// make sure server is running
 	if ( !com_sv_running->integer ) {
 		Com_Printf( "Server is not running.\n" );
 		return;
 	}
-
+	
 	if(Cmd_Argc() != 2)
 	{
 		Com_Printf ("Usage: %s (ip[/subnet] | num)\n", Cmd_Argv(0));
@@ -1204,7 +1074,7 @@
 		Com_Printf( "Server is not running.\n" );
 		return;
 	}
-
+	
 	// List all bans
 	for(index = count = 0; index < serverBansCount; index++)
 	{
@@ -1276,25 +1146,6 @@
 }
 
 /*
-** SV_Strlen -- skips color escape codes
-*/
-static int SV_Strlen( const char *str ) {
-	const char *s = str;
-	int count = 0;
-
-	while ( *s ) {
-		if ( Q_IsColorString( s ) ) {
-			s += 2;
-		} else {
-			count++;
-			s++;
-		}
-	}
-
-	return count;
-}
-
-/*
 ================
 SV_Status_f
 ================
@@ -1314,20 +1165,20 @@
 
 	Com_Printf ("map: %s\n", sv_mapname->string );
 
-	Com_Printf ("cl score ping name            address                                 rate \n");
-	Com_Printf ("-- ----- ---- --------------- --------------------------------------- -----\n");
+	Com_Printf ("num score ping name            lastmsg address               qport rate\n");
+	Com_Printf ("--- ----- ---- --------------- ------- --------------------- ----- -----\n");
 	for (i=0,cl=svs.clients ; i < sv_maxclients->integer ; i++,cl++)
 	{
 		if (!cl->state)
 			continue;
-		Com_Printf ("%2i ", i);
+		Com_Printf ("%3i ", i);
 		ps = SV_GameClientNum( i );
 		Com_Printf ("%5i ", ps->persistant[PERS_SCORE]);
 
 		if (cl->state == CS_CONNECTED)
-			Com_Printf ("CON ");
+			Com_Printf ("CNCT ");
 		else if (cl->state == CS_ZOMBIE)
-			Com_Printf ("ZMB ");
+			Com_Printf ("ZMBI ");
 		else
 		{
 			ping = cl->ping < 9999 ? cl->ping : 9999;
@@ -1335,29 +1186,34 @@
 		}
 
 		Com_Printf ("%s", cl->name);
-
-		l = 16 - SV_Strlen(cl->name);
+		
+		// TTimo adding a ^7 to reset the color
+		// NOTE: colored names in status breaks the padding (WONTFIX)
+		Com_Printf ("^7");
+		l = 14 - strlen(cl->name);
 		j = 0;
-
+		
 		do
 		{
 			Com_Printf (" ");
 			j++;
 		} while(j < l);
 
+		Com_Printf ("%7i ", svs.time - cl->lastPacketTime );
 
-		// TTimo adding a ^7 to reset the color
 		s = NET_AdrToString( cl->netchan.remoteAddress );
-		Com_Printf ("^7%s", s);
-		l = 39 - strlen(s);
+		Com_Printf ("%s", s);
+		l = 22 - strlen(s);
 		j = 0;
-
+		
 		do
 		{
 			Com_Printf(" ");
 			j++;
 		} while(j < l);
 		
+		Com_Printf ("%5i", cl->netchan.qport);
+
 		Com_Printf (" %5i", cl->rate);
 
 		Com_Printf ("\n");
@@ -1394,7 +1250,6 @@
 
 	strcat(text, p);
 
-	Com_Printf("%s\n", text);
 	SV_SendServerCommand(NULL, "chat \"%s\"", text);
 }
 
@@ -1434,79 +1289,12 @@
 
 	strcat(text, p);
 
-	Com_Printf("%s\n", text);
 	SV_SendServerCommand(cl, "chat \"%s\"", text);
 }
 
 
 /*
 ==================
-SV_ConSayto_f
-==================
-*/
-static void SV_ConSayto_f(void) {
-	char		*p;
-	char		text[1024];
-	client_t	*cl;
-	char		*rawname;
-	char		name[MAX_NAME_LENGTH];
-	char		cleanName[MAX_NAME_LENGTH];
-	client_t	*saytocl;
-	int			i;
-
-	// make sure server is running
-	if ( !com_sv_running->integer ) {
-		Com_Printf( "Server is not running.\n" );
-		return;
-	}
-
-	if ( Cmd_Argc() < 3 ) {
-		Com_Printf ("Usage: sayto <player name> <text>\n");
-		return;
-	}
-
-	rawname = Cmd_Argv(1);
-	
-	//allowing special characters in the console 
-	//with hex strings for player names
-	Com_FieldStringToPlayerName( name, MAX_NAME_LENGTH, rawname );
-
-	saytocl = NULL;
-	for ( i=0, cl=svs.clients ; i < sv_maxclients->integer ; i++,cl++ ) {
-		if ( !cl->state ) {
-			continue;
-		}
-		Q_strncpyz( cleanName, cl->name, sizeof(cleanName) );
-		Q_CleanStr( cleanName );
-
-		if ( !Q_stricmp( cleanName, name ) ) {
-			saytocl = cl;
-			break;
-		}
-	}
-	if( !saytocl )
-	{
-		Com_Printf ("No such player name: %s.\n", name);
-		return;
-	}
-
-	strcpy (text, "console_sayto: ");
-	p = Cmd_ArgsFrom(2);
-
-	if ( *p == '"' ) {
-		p++;
-		p[strlen(p)-1] = 0;
-	}
-
-	strcat(text, p);
-
-	Com_Printf("%s\n", text);
-	SV_SendServerCommand(saytocl, "chat \"%s\"", text);
-}
-
-
-/*
-==================
 SV_Heartbeat_f
 
 Also called by SV_DropClient, SV_DirectConnect, and SV_SpawnServer
@@ -1605,44 +1393,7 @@
 */
 static void SV_CompleteMapName( char *args, int argNum ) {
 	if( argNum == 2 ) {
-		Field_CompleteFilename( "maps", "bsp", NULL, qtrue, qfalse, NULL );
-	}
-}
-
-/*
-==================
-SV_CompletePlayerName
-==================
-*/
-static void SV_CompletePlayerName( char *args, int argNum ) {
-	if( argNum == 2 ) {
-		char		names[MAX_CLIENTS][MAX_NAME_LENGTH];
-		const char	*namesPtr[MAX_CLIENTS];
-		client_t	*cl;
-		int			i;
-		int			nameCount;
-		int			clientCount;
-
-		nameCount = 0;
-		clientCount = sv_maxclients->integer;
-
-		for ( i=0, cl=svs.clients ; i < clientCount; i++,cl++ ) {
-			if ( !cl->state ) {
-				continue;
-			}
-			if( i >= MAX_CLIENTS ) {
-				break;
-			}
-			Q_strncpyz( names[nameCount], cl->name, sizeof(names[nameCount]) );
-			Q_CleanStr( names[nameCount] );
-
-			namesPtr[nameCount] = names[nameCount];
-
-			nameCount++;
-		}
-		qsort( (void*)namesPtr, nameCount, sizeof( namesPtr[0] ), Com_strCompare );
-
-		Field_CompletePlayerName( namesPtr, nameCount );
+		Field_CompleteFilename( "maps", "bsp", qtrue, qfalse );
 	}
 }
 
@@ -1692,10 +1443,8 @@
 	if( com_dedicated->integer ) {
 		Cmd_AddCommand ("say", SV_ConSay_f);
 		Cmd_AddCommand ("tell", SV_ConTell_f);
-		Cmd_AddCommand ("sayto", SV_ConSayto_f);
-		Cmd_SetCommandCompletionFunc( "sayto", SV_CompletePlayerName );
 	}
-
+	
 	Cmd_AddCommand("rehashbans", SV_RehashBans_f);
 	Cmd_AddCommand("listbans", SV_ListBans_f);
 	Cmd_AddCommand("banaddr", SV_BanAddr_f);
@@ -1703,9 +1452,6 @@
 	Cmd_AddCommand("bandel", SV_BanDel_f);
 	Cmd_AddCommand("exceptdel", SV_ExceptDel_f);
 	Cmd_AddCommand("flushbans", SV_FlushBans_f);
-
-	Cmd_AddCommand("devmapnext", SV_DevmapNext_f);
-	Cmd_AddCommand("devmapprev", SV_DevmapPrev_f);
 }
 
 /*

```
