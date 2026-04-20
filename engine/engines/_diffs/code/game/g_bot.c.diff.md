# Diff: `code/game/g_bot.c`
**Canonical:** `wolfcamql-src` (sha256 `9bb6ab6fb54c...`, 24445 bytes)

## Variants

### `quake3-source`  — sha256 `85c1b3c981fa...`, 23625 bytes

_Diff stat: +123 / -168 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_bot.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_bot.c	2026-04-16 20:02:19.904124600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -43,6 +43,7 @@
 	int		spawnTime;
 } botSpawnQueue_t;
 
+//static int			botBeginDelay = 0;  // bk001206 - unused, init
 static botSpawnQueue_t	botSpawnQueue[BOT_SPAWN_QUEUE_DEPTH];
 
 vmCvar_t bot_minplayers;
@@ -128,12 +129,12 @@
 
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( !f ) {
-		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		trap_Printf( va( S_COLOR_RED "file not found: %s\n", filename ) );
 		return;
 	}
 	if ( len >= MAX_ARENAS_TEXT ) {
+		trap_Printf( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_ARENAS_TEXT ) );
 		trap_FS_FCloseFile( f );
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_ARENAS_TEXT ) );
 		return;
 	}
 
@@ -177,7 +178,7 @@
 		strcat(filename, dirptr);
 		G_LoadArenasFromFile(filename);
 	}
-	trap_Print( va( "%i arenas parsed\n", g_numArenas ) );
+	trap_Printf( va( "%i arenas parsed\n", g_numArenas ) );
 	
 	for( n = 0; n < g_numArenas; n++ ) {
 		Info_SetValueForKey( g_arenaInfos[n], "num", va( "%i", n ) );
@@ -213,7 +214,7 @@
 	char	*skin;
 
 	Q_strncpyz( model, modelAndSkin, sizeof(model) );
-	skin = strrchr( model, '/' );
+	skin = Q_strrchr( model, '/' );
 	if ( skin ) {
 		*skin++ = '\0';
 	}
@@ -230,101 +231,72 @@
 
 /*
 ===============
-G_CountBotPlayersByName
-
-Check connected and connecting (delay join) bots.
-
-Returns number of bots with name on specified team or whole server if team is -1.
+G_AddRandomBot
 ===============
 */
-int G_CountBotPlayersByName( const char *name, int team ) {
-	int                     i, num;
+void G_AddRandomBot( int team ) {
+	int		i, n, num;
+	float	skill;
+	char	*value, netname[36], *teamstr;
 	gclient_t	*cl;
 
 	num = 0;
-	for ( i=0 ; i< g_maxclients.integer ; i++ ) {
-		cl = level.clients + i;
-		if ( cl->pers.connected == CON_DISCONNECTED ) {
-			continue;
-		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
-			continue;
-		}
-		if ( team >= 0 && cl->sess.sessionTeam != team ) {
-			continue;
+	for ( n = 0; n < g_numBots ; n++ ) {
+		value = Info_ValueForKey( g_botInfos[n], "name" );
+		//
+		for ( i=0 ; i< g_maxclients.integer ; i++ ) {
+			cl = level.clients + i;
+			if ( cl->pers.connected != CON_CONNECTED ) {
+				continue;
+			}
+			if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
+				continue;
+			}
+			if ( team >= 0 && cl->sess.sessionTeam != team ) {
+				continue;
+			}
+			if ( !Q_stricmp( value, cl->pers.netname ) ) {
+				break;
+			}
 		}
-		if ( name && Q_stricmp( name, cl->pers.netname ) ) {
-			continue;
+		if (i >= g_maxclients.integer) {
+			num++;
 		}
-		num++;
-	}
-	return num;
-}
-
-/*
-===============
-G_SelectRandomBotInfo
-
-Get random least used bot info on team or whole server if team is -1.
-===============
-*/
-int G_SelectRandomBotInfo( int team ) {
-	int             selection[MAX_BOTS];
-	int             n, num;
-	int				count, bestCount;
-	char    *value;
-
-	// don't add duplicate bots to the server if there are less bots than bot types
-	if ( team != -1 && G_CountBotPlayersByName( NULL, -1 ) < g_numBots ) {
-		team = -1;
 	}
-
-	num = 0;
-	bestCount = MAX_CLIENTS;
+	num = random() * num;
 	for ( n = 0; n < g_numBots ; n++ ) {
-		value = Info_ValueForKey( g_botInfos[n], "funname" );
-		if ( !value[0] ) {
-			value = Info_ValueForKey( g_botInfos[n], "name" );
-		}
+		value = Info_ValueForKey( g_botInfos[n], "name" );
 		//
-		count = G_CountBotPlayersByName( value, team );
-
-		if ( count < bestCount ) {
-			bestCount = count;
-			num = 0;
-		}
-
-		if ( count == bestCount ) {
-			selection[num++] = n;
-
-			if ( num == MAX_BOTS ) {
+		for ( i=0 ; i< g_maxclients.integer ; i++ ) {
+			cl = level.clients + i;
+			if ( cl->pers.connected != CON_CONNECTED ) {
+				continue;
+			}
+			if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
+				continue;
+			}
+			if ( team >= 0 && cl->sess.sessionTeam != team ) {
+				continue;
+			}
+			if ( !Q_stricmp( value, cl->pers.netname ) ) {
 				break;
 			}
 		}
+		if (i >= g_maxclients.integer) {
+			num--;
+			if (num <= 0) {
+				skill = trap_Cvar_VariableValue( "g_spSkill" );
+				if (team == TEAM_RED) teamstr = "red";
+				else if (team == TEAM_BLUE) teamstr = "blue";
+				else teamstr = "";
+				strncpy(netname, value, sizeof(netname)-1);
+				netname[sizeof(netname)-1] = '\0';
+				Q_CleanStr(netname);
+				trap_SendConsoleCommand( EXEC_INSERT, va("addbot %s %f %s %i\n", netname, skill, teamstr, 0) );
+				return;
+			}
+		}
 	}
-
-	if ( num > 0 ) {
-		num = random() * ( num - 1 );
-		return selection[num];
-	}
-
-	return -1;
-}
-
-/*
-===============
-G_AddRandomBot
-===============
-*/
-void G_AddRandomBot( int team ) {
-	char	*teamstr;
-	float   skill;
-
-	skill = trap_Cvar_VariableValue( "g_spSkill" );
-	if (team == TEAM_RED) teamstr = "red";
-	else if (team == TEAM_BLUE) teamstr = "blue";
-	else teamstr = "free";
-	trap_SendConsoleCommand( EXEC_INSERT, va("addbot random %f %s %i\n", skill, teamstr, 0) );
 }
 
 /*
@@ -334,6 +306,7 @@
 */
 int G_RemoveRandomBot( int team ) {
 	int i;
+	char netname[36];
 	gclient_t	*cl;
 
 	for ( i=0 ; i< g_maxclients.integer ; i++ ) {
@@ -341,13 +314,15 @@
 		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+		if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
 			continue;
 		}
-		trap_SendConsoleCommand( EXEC_INSERT, va("clientkick %d\n", i) );
+		strcpy(netname, cl->pers.netname);
+		Q_CleanStr(netname);
+		trap_SendConsoleCommand( EXEC_INSERT, va("kick %s\n", netname) );
 		return qtrue;
 	}
 	return qfalse;
@@ -368,7 +343,7 @@
 		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
-		if ( g_entities[i].r.svFlags & SVF_BOT ) {
+		if ( g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
@@ -382,21 +357,19 @@
 /*
 ===============
 G_CountBotPlayers
-
-Check connected and connecting (delay join) bots.
 ===============
 */
 int G_CountBotPlayers( int team ) {
-	int i, num;
+	int i, n, num;
 	gclient_t	*cl;
 
 	num = 0;
 	for ( i=0 ; i< g_maxclients.integer ; i++ ) {
 		cl = level.clients + i;
-		if ( cl->pers.connected == CON_DISCONNECTED ) {
+		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+		if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
@@ -404,6 +377,15 @@
 		}
 		num++;
 	}
+	for( n = 0; n < BOT_SPAWN_QUEUE_DEPTH; n++ ) {
+		if( !botSpawnQueue[n].spawnTime ) {
+			continue;
+		}
+		if ( botSpawnQueue[n].spawnTime > level.time ) {
+			continue;
+		}
+		num++;
+	}
 	return num;
 }
 
@@ -565,6 +547,7 @@
 
 	Q_strncpyz( settings.characterfile, Info_ValueForKey( userinfo, "characterfile" ), sizeof(settings.characterfile) );
 	settings.skill = atof( Info_ValueForKey( userinfo, "skill" ) );
+	Q_strncpyz( settings.team, Info_ValueForKey( userinfo, "team" ), sizeof(settings.team) );
 
 	if (!BotAISetupClient( clientNum, &settings, restart )) {
 		trap_DropClient( clientNum, "BotAISetupClient failed" );
@@ -582,9 +565,8 @@
 */
 static void G_AddBot( const char *name, float skill, const char *team, int delay, char *altname) {
 	int				clientNum;
-	int				teamNum;
-	int				botinfoNum;
 	char			*botinfo;
+	gentity_t		*bot;
 	char			*key;
 	char			*s;
 	char			*botname;
@@ -592,61 +574,10 @@
 	char			*headmodel;
 	char			userinfo[MAX_INFO_STRING];
 
-	// have the server allocate a client slot
-	clientNum = trap_BotAllocateClient();
-	if ( clientNum == -1 ) {
-		G_Printf( S_COLOR_RED "Unable to add bot. All player slots are in use.\n" );
-		G_Printf( S_COLOR_RED "Start server with more 'open' slots (or check setting of sv_maxclients cvar).\n" );
-		return;
-	}
-
-	// set default team
-	if( !team || !*team ) {
-		if( g_gametype.integer >= GT_TEAM ) {
-			if( PickTeam(clientNum) == TEAM_RED) {
-				team = "red";
-			}
-			else {
-				team = "blue";
-			}
-		}
-		else {
-			team = "free";
-		}
-	}
-
 	// get the botinfo from bots.txt
-	if ( Q_stricmp( name, "random" ) == 0 ) {
-		if ( Q_stricmp( team, "red" ) == 0 || Q_stricmp( team, "r" ) == 0 ) {
-			teamNum = TEAM_RED;
-		}
-		else if ( Q_stricmp( team, "blue" ) == 0 || Q_stricmp( team, "b" ) == 0 ) {
-			teamNum = TEAM_BLUE;
-		}
-		else if ( !Q_stricmp( team, "spectator" ) || !Q_stricmp( team, "s" ) ) {
-			teamNum = TEAM_SPECTATOR;
-		}
-		else {
-			teamNum = TEAM_FREE;
-		}
-
-		botinfoNum = G_SelectRandomBotInfo( teamNum );
-
-		if ( botinfoNum < 0 ) {
-			G_Printf( S_COLOR_RED "Error: Cannot add random bot, no bot info available.\n" );
-			trap_BotFreeClient( clientNum );
-			return;
-		}
-
-		botinfo = G_GetBotInfoByNumber( botinfoNum );
-	}
-	else {
-		botinfo = G_GetBotInfoByName( name );
-	}
-
+	botinfo = G_GetBotInfoByName( name );
 	if ( !botinfo ) {
 		G_Printf( S_COLOR_RED "Error: Bot '%s' not defined\n", name );
-		trap_BotFreeClient( clientNum );
 		return;
 	}
 
@@ -664,8 +595,7 @@
 	Info_SetValueForKey( userinfo, "name", botname );
 	Info_SetValueForKey( userinfo, "rate", "25000" );
 	Info_SetValueForKey( userinfo, "snaps", "20" );
-	Info_SetValueForKey( userinfo, "skill", va("%.2f", skill) );
-	Info_SetValueForKey( userinfo, "teampref", team );
+	Info_SetValueForKey( userinfo, "skill", va("%1.2f", skill) );
 
 	if ( skill >= 1 && skill < 2 ) {
 		Info_SetValueForKey( userinfo, "handicap", "50" );
@@ -718,14 +648,39 @@
 
 	s = Info_ValueForKey(botinfo, "aifile");
 	if (!*s ) {
-		trap_Print( S_COLOR_RED "Error: bot has no aifile specified\n" );
-		trap_BotFreeClient( clientNum );
+		trap_Printf( S_COLOR_RED "Error: bot has no aifile specified\n" );
+		return;
+	}
+
+	// have the server allocate a client slot
+	clientNum = trap_BotAllocateClient();
+	if ( clientNum == -1 ) {
+		G_Printf( S_COLOR_RED "Unable to add bot.  All player slots are in use.\n" );
+		G_Printf( S_COLOR_RED "Start server with more 'open' slots (or check setting of sv_maxclients cvar).\n" );
 		return;
 	}
-	Info_SetValueForKey( userinfo, "characterfile", s );
 
-	// don't send tinfo to bots, they don't parse it
-	Info_SetValueForKey( userinfo, "teamoverlay", "0" );
+	// initialize the bot settings
+	if( !team || !*team ) {
+		if( g_gametype.integer >= GT_TEAM ) {
+			if( PickTeam(clientNum) == TEAM_RED) {
+				team = "red";
+			}
+			else {
+				team = "blue";
+			}
+		}
+		else {
+			team = "red";
+		}
+	}
+	Info_SetValueForKey( userinfo, "characterfile", Info_ValueForKey( botinfo, "aifile" ) );
+	Info_SetValueForKey( userinfo, "skill", va( "%5.2f", skill ) );
+	Info_SetValueForKey( userinfo, "team", team );
+
+	bot = &g_entities[ clientNum ];
+	bot->r.svFlags |= SVF_BOT;
+	bot->inuse = qtrue;
 
 	// register the userinfo
 	trap_SetUserinfo( clientNum, userinfo );
@@ -765,7 +720,7 @@
 	// name
 	trap_Argv( 1, name, sizeof( name ) );
 	if ( !name[0] ) {
-		trap_Print( "Usage: Addbot <botname> [skill 1-5] [team] [msec delay] [altname]\n" );
+		trap_Printf( "Usage: Addbot <botname> [skill 1-5] [team] [msec delay] [altname]\n" );
 		return;
 	}
 
@@ -775,7 +730,7 @@
 		skill = 4;
 	}
 	else {
-		skill = Com_Clamp( 1, 5, atof( string ) );
+		skill = atof( string );
 	}
 
 	// team
@@ -815,25 +770,25 @@
 	char model[MAX_TOKEN_CHARS];
 	char aifile[MAX_TOKEN_CHARS];
 
-	trap_Print("^1name             model            aifile              funname\n");
+	trap_Printf("^1name             model            aifile              funname\n");
 	for (i = 0; i < g_numBots; i++) {
-		Q_strncpyz(name, Info_ValueForKey( g_botInfos[i], "name" ), sizeof( name ));
+		strcpy(name, Info_ValueForKey( g_botInfos[i], "name" ));
 		if ( !*name ) {
 			strcpy(name, "UnnamedPlayer");
 		}
-		Q_strncpyz(funname, Info_ValueForKey( g_botInfos[i], "funname" ), sizeof( funname ));
+		strcpy(funname, Info_ValueForKey( g_botInfos[i], "funname" ));
 		if ( !*funname ) {
 			strcpy(funname, "");
 		}
-		Q_strncpyz(model, Info_ValueForKey( g_botInfos[i], "model" ), sizeof( model ));
+		strcpy(model, Info_ValueForKey( g_botInfos[i], "model" ));
 		if ( !*model ) {
 			strcpy(model, "visor/default");
 		}
-		Q_strncpyz(aifile, Info_ValueForKey( g_botInfos[i], "aifile"), sizeof( aifile ));
+		strcpy(aifile, Info_ValueForKey( g_botInfos[i], "aifile"));
 		if (!*aifile ) {
 			strcpy(aifile, "bots/default_c.c");
 		}
-		trap_Print(va("%-16s %-16s %-20s %-20s\n", name, model, aifile, funname));
+		trap_Printf(va("%-16s %-16s %-20s %-20s\n", name, model, aifile, funname));
 	}
 }
 
@@ -872,7 +827,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 
@@ -908,11 +863,11 @@
 
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( !f ) {
-		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		trap_Printf( va( S_COLOR_RED "file not found: %s\n", filename ) );
 		return;
 	}
 	if ( len >= MAX_BOTS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_BOTS_TEXT ) );
+		trap_Printf( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_BOTS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -961,7 +916,7 @@
 		strcat(filename, dirptr);
 		G_LoadBotsFromFile(filename);
 	}
-	trap_Print( va( "%i bots parsed\n", g_numBots ) );
+	trap_Printf( va( "%i bots parsed\n", g_numBots ) );
 }
 
 
@@ -973,7 +928,7 @@
 */
 char *G_GetBotInfoByNumber( int num ) {
 	if( num < 0 || num >= g_numBots ) {
-		trap_Print( va( S_COLOR_RED "Invalid bot number: %i\n", num ) );
+		trap_Printf( va( S_COLOR_RED "Invalid bot number: %i\n", num ) );
 		return NULL;
 	}
 	return g_botInfos[num];

```

### `ioquake3`  — sha256 `a8cdfcc18df4...`, 24398 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_bot.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_bot.c	2026-04-16 20:02:21.541889300 +0100
@@ -238,7 +238,7 @@
 ===============
 */
 int G_CountBotPlayersByName( const char *name, int team ) {
-	int                     i, num;
+	int			i, num;
 	gclient_t	*cl;
 
 	num = 0;
@@ -269,10 +269,10 @@
 ===============
 */
 int G_SelectRandomBotInfo( int team ) {
-	int             selection[MAX_BOTS];
-	int             n, num;
-	int				count, bestCount;
-	char    *value;
+	int		selection[MAX_BOTS];
+	int		n, num;
+	int		count, bestCount;
+	char	*value;
 
 	// don't add duplicate bots to the server if there are less bots than bot types
 	if ( team != -1 && G_CountBotPlayersByName( NULL, -1 ) < g_numBots ) {
@@ -318,7 +318,7 @@
 */
 void G_AddRandomBot( int team ) {
 	char	*teamstr;
-	float   skill;
+	float	skill;
 
 	skill = trap_Cvar_VariableValue( "g_spSkill" );
 	if (team == TEAM_RED) teamstr = "red";

```

### `openarena-engine`  — sha256 `46d81b7706b5...`, 23207 bytes

_Diff stat: +84 / -139 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_bot.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_bot.c	2026-04-16 22:48:25.745536200 +0100
@@ -230,101 +230,71 @@
 
 /*
 ===============
-G_CountBotPlayersByName
-
-Check connected and connecting (delay join) bots.
-
-Returns number of bots with name on specified team or whole server if team is -1.
+G_AddRandomBot
 ===============
 */
-int G_CountBotPlayersByName( const char *name, int team ) {
-	int                     i, num;
+void G_AddRandomBot( int team ) {
+	int		i, n, num;
+	float	skill;
+	char	*value, netname[36], *teamstr;
 	gclient_t	*cl;
 
 	num = 0;
-	for ( i=0 ; i< g_maxclients.integer ; i++ ) {
-		cl = level.clients + i;
-		if ( cl->pers.connected == CON_DISCONNECTED ) {
-			continue;
-		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
-			continue;
-		}
-		if ( team >= 0 && cl->sess.sessionTeam != team ) {
-			continue;
+	for ( n = 0; n < g_numBots ; n++ ) {
+		value = Info_ValueForKey( g_botInfos[n], "name" );
+		//
+		for ( i=0 ; i< g_maxclients.integer ; i++ ) {
+			cl = level.clients + i;
+			if ( cl->pers.connected != CON_CONNECTED ) {
+				continue;
+			}
+			if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+				continue;
+			}
+			if ( team >= 0 && cl->sess.sessionTeam != team ) {
+				continue;
+			}
+			if ( !Q_stricmp( value, cl->pers.netname ) ) {
+				break;
+			}
 		}
-		if ( name && Q_stricmp( name, cl->pers.netname ) ) {
-			continue;
+		if (i >= g_maxclients.integer) {
+			num++;
 		}
-		num++;
-	}
-	return num;
-}
-
-/*
-===============
-G_SelectRandomBotInfo
-
-Get random least used bot info on team or whole server if team is -1.
-===============
-*/
-int G_SelectRandomBotInfo( int team ) {
-	int             selection[MAX_BOTS];
-	int             n, num;
-	int				count, bestCount;
-	char    *value;
-
-	// don't add duplicate bots to the server if there are less bots than bot types
-	if ( team != -1 && G_CountBotPlayersByName( NULL, -1 ) < g_numBots ) {
-		team = -1;
 	}
-
-	num = 0;
-	bestCount = MAX_CLIENTS;
+	num = random() * num;
 	for ( n = 0; n < g_numBots ; n++ ) {
-		value = Info_ValueForKey( g_botInfos[n], "funname" );
-		if ( !value[0] ) {
-			value = Info_ValueForKey( g_botInfos[n], "name" );
-		}
+		value = Info_ValueForKey( g_botInfos[n], "name" );
 		//
-		count = G_CountBotPlayersByName( value, team );
-
-		if ( count < bestCount ) {
-			bestCount = count;
-			num = 0;
-		}
-
-		if ( count == bestCount ) {
-			selection[num++] = n;
-
-			if ( num == MAX_BOTS ) {
+		for ( i=0 ; i< g_maxclients.integer ; i++ ) {
+			cl = level.clients + i;
+			if ( cl->pers.connected != CON_CONNECTED ) {
+				continue;
+			}
+			if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+				continue;
+			}
+			if ( team >= 0 && cl->sess.sessionTeam != team ) {
+				continue;
+			}
+			if ( !Q_stricmp( value, cl->pers.netname ) ) {
 				break;
 			}
 		}
+		if (i >= g_maxclients.integer) {
+			num--;
+			if (num <= 0) {
+				skill = trap_Cvar_VariableValue( "g_spSkill" );
+				if (team == TEAM_RED) teamstr = "red";
+				else if (team == TEAM_BLUE) teamstr = "blue";
+				else teamstr = "";
+				Q_strncpyz(netname, value, sizeof(netname));
+				Q_CleanStr(netname);
+				trap_SendConsoleCommand( EXEC_INSERT, va("addbot %s %f %s %i\n", netname, skill, teamstr, 0) );
+				return;
+			}
+		}
 	}
-
-	if ( num > 0 ) {
-		num = random() * ( num - 1 );
-		return selection[num];
-	}
-
-	return -1;
-}
-
-/*
-===============
-G_AddRandomBot
-===============
-*/
-void G_AddRandomBot( int team ) {
-	char	*teamstr;
-	float   skill;
-
-	skill = trap_Cvar_VariableValue( "g_spSkill" );
-	if (team == TEAM_RED) teamstr = "red";
-	else if (team == TEAM_BLUE) teamstr = "blue";
-	else teamstr = "free";
-	trap_SendConsoleCommand( EXEC_INSERT, va("addbot random %f %s %i\n", skill, teamstr, 0) );
 }
 
 /*
@@ -382,18 +352,16 @@
 /*
 ===============
 G_CountBotPlayers
-
-Check connected and connecting (delay join) bots.
 ===============
 */
 int G_CountBotPlayers( int team ) {
-	int i, num;
+	int i, n, num;
 	gclient_t	*cl;
 
 	num = 0;
 	for ( i=0 ; i< g_maxclients.integer ; i++ ) {
 		cl = level.clients + i;
-		if ( cl->pers.connected == CON_DISCONNECTED ) {
+		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
 		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
@@ -404,6 +372,15 @@
 		}
 		num++;
 	}
+	for( n = 0; n < BOT_SPAWN_QUEUE_DEPTH; n++ ) {
+		if( !botSpawnQueue[n].spawnTime ) {
+			continue;
+		}
+		if ( botSpawnQueue[n].spawnTime > level.time ) {
+			continue;
+		}
+		num++;
+	}
 	return num;
 }
 
@@ -565,6 +542,7 @@
 
 	Q_strncpyz( settings.characterfile, Info_ValueForKey( userinfo, "characterfile" ), sizeof(settings.characterfile) );
 	settings.skill = atof( Info_ValueForKey( userinfo, "skill" ) );
+	Q_strncpyz( settings.team, Info_ValueForKey( userinfo, "team" ), sizeof(settings.team) );
 
 	if (!BotAISetupClient( clientNum, &settings, restart )) {
 		trap_DropClient( clientNum, "BotAISetupClient failed" );
@@ -582,8 +560,6 @@
 */
 static void G_AddBot( const char *name, float skill, const char *team, int delay, char *altname) {
 	int				clientNum;
-	int				teamNum;
-	int				botinfoNum;
 	char			*botinfo;
 	char			*key;
 	char			*s;
@@ -600,50 +576,8 @@
 		return;
 	}
 
-	// set default team
-	if( !team || !*team ) {
-		if( g_gametype.integer >= GT_TEAM ) {
-			if( PickTeam(clientNum) == TEAM_RED) {
-				team = "red";
-			}
-			else {
-				team = "blue";
-			}
-		}
-		else {
-			team = "free";
-		}
-	}
-
 	// get the botinfo from bots.txt
-	if ( Q_stricmp( name, "random" ) == 0 ) {
-		if ( Q_stricmp( team, "red" ) == 0 || Q_stricmp( team, "r" ) == 0 ) {
-			teamNum = TEAM_RED;
-		}
-		else if ( Q_stricmp( team, "blue" ) == 0 || Q_stricmp( team, "b" ) == 0 ) {
-			teamNum = TEAM_BLUE;
-		}
-		else if ( !Q_stricmp( team, "spectator" ) || !Q_stricmp( team, "s" ) ) {
-			teamNum = TEAM_SPECTATOR;
-		}
-		else {
-			teamNum = TEAM_FREE;
-		}
-
-		botinfoNum = G_SelectRandomBotInfo( teamNum );
-
-		if ( botinfoNum < 0 ) {
-			G_Printf( S_COLOR_RED "Error: Cannot add random bot, no bot info available.\n" );
-			trap_BotFreeClient( clientNum );
-			return;
-		}
-
-		botinfo = G_GetBotInfoByNumber( botinfoNum );
-	}
-	else {
-		botinfo = G_GetBotInfoByName( name );
-	}
-
+	botinfo = G_GetBotInfoByName( name );
 	if ( !botinfo ) {
 		G_Printf( S_COLOR_RED "Error: Bot '%s' not defined\n", name );
 		trap_BotFreeClient( clientNum );
@@ -665,7 +599,6 @@
 	Info_SetValueForKey( userinfo, "rate", "25000" );
 	Info_SetValueForKey( userinfo, "snaps", "20" );
 	Info_SetValueForKey( userinfo, "skill", va("%.2f", skill) );
-	Info_SetValueForKey( userinfo, "teampref", team );
 
 	if ( skill >= 1 && skill < 2 ) {
 		Info_SetValueForKey( userinfo, "handicap", "50" );
@@ -724,8 +657,20 @@
 	}
 	Info_SetValueForKey( userinfo, "characterfile", s );
 
-	// don't send tinfo to bots, they don't parse it
-	Info_SetValueForKey( userinfo, "teamoverlay", "0" );
+	if( !team || !*team ) {
+		if( g_gametype.integer >= GT_TEAM ) {
+			if( PickTeam(clientNum) == TEAM_RED) {
+				team = "red";
+			}
+			else {
+				team = "blue";
+			}
+		}
+		else {
+			team = "red";
+		}
+	}
+	Info_SetValueForKey( userinfo, "team", team );
 
 	// register the userinfo
 	trap_SetUserinfo( clientNum, userinfo );
@@ -775,7 +720,7 @@
 		skill = 4;
 	}
 	else {
-		skill = Com_Clamp( 1, 5, atof( string ) );
+		skill = atof( string );
 	}
 
 	// team
@@ -817,19 +762,19 @@
 
 	trap_Print("^1name             model            aifile              funname\n");
 	for (i = 0; i < g_numBots; i++) {
-		Q_strncpyz(name, Info_ValueForKey( g_botInfos[i], "name" ), sizeof( name ));
+		strcpy(name, Info_ValueForKey( g_botInfos[i], "name" ));
 		if ( !*name ) {
 			strcpy(name, "UnnamedPlayer");
 		}
-		Q_strncpyz(funname, Info_ValueForKey( g_botInfos[i], "funname" ), sizeof( funname ));
+		strcpy(funname, Info_ValueForKey( g_botInfos[i], "funname" ));
 		if ( !*funname ) {
 			strcpy(funname, "");
 		}
-		Q_strncpyz(model, Info_ValueForKey( g_botInfos[i], "model" ), sizeof( model ));
+		strcpy(model, Info_ValueForKey( g_botInfos[i], "model" ));
 		if ( !*model ) {
 			strcpy(model, "visor/default");
 		}
-		Q_strncpyz(aifile, Info_ValueForKey( g_botInfos[i], "aifile"), sizeof( aifile ));
+		strcpy(aifile, Info_ValueForKey( g_botInfos[i], "aifile"));
 		if (!*aifile ) {
 			strcpy(aifile, "bots/default_c.c");
 		}
@@ -872,7 +817,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 

```

### `openarena-gamecode`  — sha256 `b52e61ad37cc...`, 25546 bytes

_Diff stat: +66 / -41 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_bot.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_bot.c	2026-04-16 22:48:24.168480300 +0100
@@ -43,9 +43,11 @@
 	int		spawnTime;
 } botSpawnQueue_t;
 
+//static int			botBeginDelay = 0;  // bk001206 - unused, init
 static botSpawnQueue_t	botSpawnQueue[BOT_SPAWN_QUEUE_DEPTH];
 
 vmCvar_t bot_minplayers;
+vmCvar_t bot_autominplayers;
 
 extern gentity_t	*podium1;
 extern gentity_t	*podium2;
@@ -78,7 +80,7 @@
 		if ( !token[0] ) {
 			break;
 		}
-		if ( strcmp( token, "{" ) ) {
+		if ( !strequals( token, "{" ) ) {
 			Com_Printf( "Missing { in info file\n" );
 			break;
 		}
@@ -95,7 +97,7 @@
 				Com_Printf( "Unexpected end of info file\n" );
 				break;
 			}
-			if ( !strcmp( token, "}" ) ) {
+			if ( strequals( token, "}" ) ) {
 				break;
 			}
 			Q_strncpyz( key, token, sizeof( key ) );
@@ -106,8 +108,11 @@
 			}
 			Info_SetValueForKey( info, key, token );
 		}
+		if(!BG_CanAlloc(strlen(info) + strlen("\\num\\") + strlen(va("%d", MAX_ARENAS)) + 1))
+			break; //Not enough memory. Don't even try
 		//NOTE: extra space for arena number
-		infos[count] = G_Alloc(strlen(info) + strlen("\\num\\") + strlen(va("%d", MAX_ARENAS)) + 1);
+		//KK-OAX Changed to Tremulous's BG_Alloc
+		infos[count] = BG_Alloc(strlen(info) + strlen("\\num\\") + strlen(va("%d", MAX_ARENAS)) + 1);
 		if (infos[count]) {
 			strcpy(infos[count], info);
 			count++;
@@ -128,12 +133,12 @@
 
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( !f ) {
-		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		trap_Printf( va( S_COLOR_RED "file not found: %s\n", filename ) );
 		return;
 	}
 	if ( len >= MAX_ARENAS_TEXT ) {
+		trap_Printf( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_ARENAS_TEXT ) );
 		trap_FS_FCloseFile( f );
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_ARENAS_TEXT ) );
 		return;
 	}
 
@@ -177,7 +182,7 @@
 		strcat(filename, dirptr);
 		G_LoadArenasFromFile(filename);
 	}
-	trap_Print( va( "%i arenas parsed\n", g_numArenas ) );
+	trap_Printf( va( "%i arenas parsed\n", g_numArenas ) );
 	
 	for( n = 0; n < g_numArenas; n++ ) {
 		Info_SetValueForKey( g_arenaInfos[n], "num", va( "%i", n ) );
@@ -194,7 +199,7 @@
 	int			n;
 
 	for( n = 0; n < g_numArenas; n++ ) {
-		if( Q_stricmp( Info_ValueForKey( g_arenaInfos[n], "map" ), map ) == 0 ) {
+		if( Q_strequal( Info_ValueForKey( g_arenaInfos[n], "map" ), map ) ) {
 			return g_arenaInfos[n];
 		}
 	}
@@ -221,7 +226,7 @@
 		skin = model;
 	}
 
-	if( Q_stricmp( skin, "default" ) == 0 ) {
+	if( Q_strequal( skin, "default" ) ) {
 		skin = model;
 	}
 
@@ -238,7 +243,7 @@
 ===============
 */
 int G_CountBotPlayersByName( const char *name, int team ) {
-	int                     i, num;
+	int			i, num;
 	gclient_t	*cl;
 
 	num = 0;
@@ -269,10 +274,10 @@
 ===============
 */
 int G_SelectRandomBotInfo( int team ) {
-	int             selection[MAX_BOTS];
-	int             n, num;
-	int				count, bestCount;
-	char    *value;
+	int		selection[MAX_BOTS];
+	int		n, num;
+	int		count, bestCount;
+	char	*value;
 
 	// don't add duplicate bots to the server if there are less bots than bot types
 	if ( team != -1 && G_CountBotPlayersByName( NULL, -1 ) < g_numBots ) {
@@ -318,7 +323,7 @@
 */
 void G_AddRandomBot( int team ) {
 	char	*teamstr;
-	float   skill;
+	float	skill;
 
 	skill = trap_Cvar_VariableValue( "g_spSkill" );
 	if (team == TEAM_RED) teamstr = "red";
@@ -341,13 +346,13 @@
 		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+		if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
 			continue;
 		}
-		trap_SendConsoleCommand( EXEC_INSERT, va("clientkick %d\n", i) );
+		trap_SendConsoleCommand( EXEC_INSERT, va("clientkick %d\n", cl->ps.clientNum) );
 		return qtrue;
 	}
 	return qfalse;
@@ -368,7 +373,7 @@
 		if ( cl->pers.connected != CON_CONNECTED ) {
 			continue;
 		}
-		if ( g_entities[i].r.svFlags & SVF_BOT ) {
+		if ( g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
@@ -396,7 +401,7 @@
 		if ( cl->pers.connected == CON_DISCONNECTED ) {
 			continue;
 		}
-		if ( !(g_entities[i].r.svFlags & SVF_BOT) ) {
+		if ( !(g_entities[cl->ps.clientNum].r.svFlags & SVF_BOT) ) {
 			continue;
 		}
 		if ( team >= 0 && cl->sess.sessionTeam != team ) {
@@ -427,7 +432,13 @@
 	minplayers = bot_minplayers.integer;
 	if (minplayers <= 0) return;
 
-	if (g_gametype.integer >= GT_TEAM) {
+	if (!trap_AAS_Initialized()) {
+		minplayers = 0;
+		checkminimumplayers_time = level.time+600*1000;
+		return; //If no AAS then don't even try
+	}
+
+	if (g_gametype.integer >= GT_TEAM && g_ffa_gt!=1) {
 		if (minplayers >= g_maxclients.integer / 2) {
 			minplayers = (g_maxclients.integer / 2) -1;
 		}
@@ -467,7 +478,7 @@
 			}
 		}
 	}
-	else if (g_gametype.integer == GT_FFA) {
+	else {
 		if (minplayers >= g_maxclients.integer) {
 			minplayers = g_maxclients.integer-1;
 		}
@@ -526,8 +537,7 @@
 			return;
 		}
 	}
-
-	G_Printf( S_COLOR_YELLOW "Unable to delay spawn\n" );
+        G_Printf( S_COLOR_YELLOW "Unable to delay spawn\n" );
 	ClientBegin( clientNum );
 }
 
@@ -566,7 +576,7 @@
 	Q_strncpyz( settings.characterfile, Info_ValueForKey( userinfo, "characterfile" ), sizeof(settings.characterfile) );
 	settings.skill = atof( Info_ValueForKey( userinfo, "skill" ) );
 
-	if (!BotAISetupClient( clientNum, &settings, restart )) {
+	if (!trap_AAS_Initialized() || !BotAISetupClient( clientNum, &settings, restart )) {
 		trap_DropClient( clientNum, "BotAISetupClient failed" );
 		return qfalse;
 	}
@@ -602,7 +612,7 @@
 
 	// set default team
 	if( !team || !*team ) {
-		if( g_gametype.integer >= GT_TEAM ) {
+		if( GAMETYPE_IS_A_TEAM_GAME(g_gametype.integer) ) {
 			if( PickTeam(clientNum) == TEAM_RED) {
 				team = "red";
 			}
@@ -616,14 +626,14 @@
 	}
 
 	// get the botinfo from bots.txt
-	if ( Q_stricmp( name, "random" ) == 0 ) {
-		if ( Q_stricmp( team, "red" ) == 0 || Q_stricmp( team, "r" ) == 0 ) {
+	if ( Q_strequal( name, "random" ) ) {
+		if ( Q_strequal( team, "red" ) || Q_strequal( team, "r" ) ) {
 			teamNum = TEAM_RED;
 		}
-		else if ( Q_stricmp( team, "blue" ) == 0 || Q_stricmp( team, "b" ) == 0 ) {
+		else if ( Q_strequal( team, "blue" ) || Q_strequal( team, "b" ) ) {
 			teamNum = TEAM_BLUE;
 		}
-		else if ( !Q_stricmp( team, "spectator" ) || !Q_stricmp( team, "s" ) ) {
+		else if ( Q_strequal( team, "spectator" ) || Q_strequal( team, "s" ) ) {
 			teamNum = TEAM_SPECTATOR;
 		}
 		else {
@@ -680,7 +690,7 @@
 	key = "model";
 	model = Info_ValueForKey( botinfo, key );
 	if ( !*model ) {
-		model = "visor/default";
+		model = "sarge/default";
 	}
 	Info_SetValueForKey( userinfo, key, model );
 	key = "team_model";
@@ -718,7 +728,7 @@
 
 	s = Info_ValueForKey(botinfo, "aifile");
 	if (!*s ) {
-		trap_Print( S_COLOR_RED "Error: bot has no aifile specified\n" );
+		trap_Printf( S_COLOR_RED "Error: bot has no aifile specified\n" );
 		trap_BotFreeClient( clientNum );
 		return;
 	}
@@ -758,14 +768,14 @@
 	char			team[MAX_TOKEN_CHARS];
 
 	// are bots enabled?
-	if ( !trap_Cvar_VariableIntegerValue( "bot_enable" ) ) {
+	if ( !trap_Cvar_VariableIntegerValue( "bot_enable" ) || !trap_AAS_Initialized() ) {
 		return;
 	}
 
 	// name
 	trap_Argv( 1, name, sizeof( name ) );
 	if ( !name[0] ) {
-		trap_Print( "Usage: Addbot <botname> [skill 1-5] [team] [msec delay] [altname]\n" );
+		trap_Printf( "Usage: Addbot <botname> [skill 1-5] [team] [msec delay] [altname]\n" );
 		return;
 	}
 
@@ -815,7 +825,7 @@
 	char model[MAX_TOKEN_CHARS];
 	char aifile[MAX_TOKEN_CHARS];
 
-	trap_Print("^1name             model            aifile              funname\n");
+	trap_Printf("^1name             model            aifile              funname\n");
 	for (i = 0; i < g_numBots; i++) {
 		Q_strncpyz(name, Info_ValueForKey( g_botInfos[i], "name" ), sizeof( name ));
 		if ( !*name ) {
@@ -827,13 +837,13 @@
 		}
 		Q_strncpyz(model, Info_ValueForKey( g_botInfos[i], "model" ), sizeof( model ));
 		if ( !*model ) {
-			strcpy(model, "visor/default");
+			strcpy(model, "sarge/default");
 		}
 		Q_strncpyz(aifile, Info_ValueForKey( g_botInfos[i], "aifile"), sizeof( aifile ));
 		if (!*aifile ) {
 			strcpy(aifile, "bots/default_c.c");
 		}
-		trap_Print(va("%-16s %-16s %-20s %-20s\n", name, model, aifile, funname));
+		trap_Printf(va("%-16s %-16s %-20s %-20s\n", name, model, aifile, funname));
 	}
 }
 
@@ -908,11 +918,11 @@
 
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( !f ) {
-		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		trap_Printf( va( S_COLOR_RED "file not found: %s\n", filename ) );
 		return;
 	}
 	if ( len >= MAX_BOTS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_BOTS_TEXT ) );
+		trap_Printf( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_BOTS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -961,7 +971,7 @@
 		strcat(filename, dirptr);
 		G_LoadBotsFromFile(filename);
 	}
-	trap_Print( va( "%i bots parsed\n", g_numBots ) );
+	trap_Printf( va( "%i bots parsed\n", g_numBots ) );
 }
 
 
@@ -973,7 +983,7 @@
 */
 char *G_GetBotInfoByNumber( int num ) {
 	if( num < 0 || num >= g_numBots ) {
-		trap_Print( va( S_COLOR_RED "Invalid bot number: %i\n", num ) );
+		trap_Printf( va( S_COLOR_RED "Invalid bot number: %i\n", num ) );
 		return NULL;
 	}
 	return g_botInfos[num];
@@ -991,7 +1001,7 @@
 
 	for ( n = 0; n < g_numBots ; n++ ) {
 		value = Info_ValueForKey( g_botInfos[n], "name" );
-		if ( !Q_stricmp( value, name ) ) {
+		if ( Q_strequal( value, name ) ) {
 			return g_botInfos[n];
 		}
 	}
@@ -1017,6 +1027,7 @@
 	G_LoadArenas();
 
 	trap_Cvar_Register( &bot_minplayers, "bot_minplayers", "0", CVAR_SERVERINFO );
+	trap_Cvar_Register( &bot_autominplayers, "bot_autominplayers", "0", CVAR_SERVERINFO );
 
 	if( g_gametype.integer == GT_SINGLE_PLAYER ) {
 		trap_GetServerinfo( serverinfo, sizeof(serverinfo) );
@@ -1051,12 +1062,26 @@
 
 		basedelay = BOT_BEGIN_DELAY_BASE;
 		strValue = Info_ValueForKey( arenainfo, "special" );
-		if( Q_stricmp( strValue, "training" ) == 0 ) {
+		if( Q_strequal( strValue, "training" ) ) {
 			basedelay += 10000;
 		}
 
 		if( !restart ) {
 			G_SpawnBots( Info_ValueForKey( arenainfo, "bots" ), basedelay );
 		}
+	} else {
+	    if(bot_autominplayers.integer) {
+		//Set bot_minplayers
+		if(g_gametype.integer == GT_TOURNAMENT) {
+		    trap_Cvar_Set("bot_minplayers","2"); //Always 2 for Tourney
+		} else {
+			basedelay = MinSpawnpointCount()/2;
+			if(basedelay < 3 && (g_gametype.integer < GT_TEAM || g_ffa_gt) )
+			    basedelay = 3; //Minimum 3 for FFA
+			if(basedelay < 2 && !(g_gametype.integer < GT_TEAM || g_ffa_gt) )
+			    basedelay = 2; //Minimum 2 for TEAM
+			trap_Cvar_Set("bot_minplayers",va("%i",basedelay) );
+		}
+	    }
 	}
 }

```
