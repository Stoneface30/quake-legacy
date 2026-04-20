# Diff: `code/game/g_main.c`
**Canonical:** `wolfcamql-src` (sha256 `7f5fb44bb7d6...`, 52744 bytes)

## Variants

### `quake3-source`  — sha256 `b98c2b5cb2ed...`, 47805 bytes

_Diff stat: +109 / -251 lines_

_(full diff is 25560 bytes — see files directly)_

### `ioquake3`  — sha256 `23ce80a2ccff...`, 49883 bytes

_Diff stat: +16 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_main.c	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_main.c	2026-04-16 20:02:21.544362900 +0100
@@ -82,7 +82,7 @@
 vmCvar_t	g_rankings;
 vmCvar_t	g_listEntity;
 vmCvar_t	g_localTeamPref;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 vmCvar_t	g_obeliskHealth;
 vmCvar_t	g_obeliskRegenPeriod;
 vmCvar_t	g_obeliskRegenAmount;
@@ -95,17 +95,6 @@
 vmCvar_t	g_enableBreath;
 vmCvar_t	g_proxMineTimeout;
 #endif
-vmCvar_t g_levelStartTime;
-
-vmCvar_t g_weapon_rocket_speed;
-
-vmCvar_t g_weapon_plasma_speed;
-//vmCvar_t g_weapon_plasma_rate;
-
-vmCvar_t g_debugPingValue;
-vmCvar_t g_ammoPack;
-vmCvar_t g_ammoPackHack;
-vmCvar_t g_wolfcamVersion;
 
 static cvarTable_t		gameCvarTable[] = {
 	// don't override the cheat state set by the system
@@ -169,15 +158,15 @@
 	{ &g_allowVote, "g_allowVote", "1", CVAR_ARCHIVE, 0, qfalse },
 	{ &g_listEntity, "g_listEntity", "0", 0, 0, qfalse },
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	{ &g_obeliskHealth, "g_obeliskHealth", "2500", 0, 0, qfalse },
 	{ &g_obeliskRegenPeriod, "g_obeliskRegenPeriod", "1", 0, 0, qfalse },
 	{ &g_obeliskRegenAmount, "g_obeliskRegenAmount", "15", 0, 0, qfalse },
 	{ &g_obeliskRespawnDelay, "g_obeliskRespawnDelay", "10", CVAR_SERVERINFO, 0, qfalse },
 
 	{ &g_cubeTimeout, "g_cubeTimeout", "30", 0, 0, qfalse },
-	{ &g_redteam, "g_redteam", DEFAULT_REDTEAM_NAME, CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue },
-	{ &g_blueteam, "g_blueteam", DEFAULT_BLUETEAM_NAME, CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue  },
+	{ &g_redteam, "g_redteam", "Stroggs", CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue },
+	{ &g_blueteam, "g_blueteam", "Pagans", CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue  },
 	{ &g_singlePlayer, "ui_singlePlayerActive", "", 0, 0, qfalse, qfalse  },
 
 	{ &g_enableDust, "g_enableDust", "0", CVAR_SERVERINFO, 0, qtrue, qfalse },
@@ -189,15 +178,7 @@
 	{ &pmove_msec, "pmove_msec", "8", CVAR_SYSTEMINFO, 0, qfalse},
 
 	{ &g_rankings, "g_rankings", "0", 0, 0, qfalse},
-	{ &g_localTeamPref, "g_localTeamPref", "", 0, 0, qfalse },
-	{ &g_levelStartTime, "g_levelStartTime", "0", CVAR_SERVERINFO, 0, qfalse },
-	{ &g_weapon_rocket_speed, "g_weapon_rocket_speed", "900", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_weapon_plasma_speed, "g_weapon_plasma_speed", "2000", CVAR_ARCHIVE, 0, qfalse },
-	//{ &g_weapon_plasma_rate, "g_weapon_plasma_rate", "100", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_debugPingValue, "g_debugPingValue", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_ammoPack, "g_ammoPack", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_ammoPackHack, "g_ammoPackHack", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_wolfcamVersion, "wolfcamversion", WOLFCAM_VERSION, CVAR_SERVERINFO | CVAR_ROM, 0, qfalse },
+	{ &g_localTeamPref, "g_localTeamPref", "", 0, 0, qfalse }
 
 };
 
@@ -335,7 +316,7 @@
 }
 
 void G_RemapTeamShaders( void ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	char string[1024];
 	float f = level.time * 0.001;
 	Com_sprintf( string, sizeof(string), "team_icon/%s_red", g_redteam.string );
@@ -426,13 +407,10 @@
 */
 void G_InitGame( int levelTime, int randomSeed, int restart ) {
 	int					i;
-	int protocol;
-	char buffer[256];
 
 	G_Printf ("------- Game Initialization -------\n");
 	G_Printf ("gamename: %s\n", GAMEVERSION);
 	G_Printf ("gamedate: %s\n", PRODUCT_DATE);
-	G_Printf("version: %s\n", WOLFCAM_VERSION);
 
 	srand( randomSeed );
 
@@ -442,38 +420,6 @@
 
 	G_InitMemory();
 
-	trap_Cvar_VariableStringBuffer("protocol", buffer, sizeof(buffer));
-	protocol = atoi(buffer);
-	G_Printf("protocol %d\n", protocol);
-
-	if (protocol == 91) {
-		// defaults to protocol 91
-		PW_NONE = PW91_NONE;
-		//PW_SPAWNARMOR = PW91_SPAWNARMOR;
-		PW_QUAD = PW91_QUAD;
-		PW_BATTLESUIT = PW91_BATTLESUIT;
-		PW_HASTE = PW91_HASTE;
-		PW_INVIS = PW91_INVIS;
-		PW_REGEN = PW91_REGEN;
-		PW_FLIGHT = PW91_FLIGHT;
-		PW_REDFLAG = PW91_REDFLAG;
-		PW_BLUEFLAG = PW91_BLUEFLAG;
-		PW_NEUTRALFLAG = PW91_NEUTRALFLAG;
-		PW_INVULNERABILITY = PW91_INVULNERABILITY;
-		PW_SCOUT = PW91_SCOUT;
-		PW_GUARD = PW91_GUARD;
-		PW_DOUBLER = PW91_DOUBLER;
-		PW_ARMORREGEN = PW91_ARMORREGEN;
-		PW_FROZEN = PW91_FROZEN;
-		PW_NUM_POWERUPS = PW91_NUM_POWERUPS;
-
-		memcpy(&bg_itemlist, &bg_itemlistQldm91, sizeof(gitem_t) * bg_numItemsQldm91);
-		bg_numItems = bg_numItemsQldm91;
-	} else {
-		//FIXME
-		G_Printf("^3FIXME: game unsupported protocol %d\n", protocol);
-	}
-
 	// set some level globals
 	memset( &level, 0, sizeof( level ) );
 	level.time = levelTime;
@@ -481,8 +427,6 @@
 
 	level.snd_fry = G_SoundIndex("sound/player/fry.wav");	// FIXME standing in lava / slime
 
-	trap_Cvar_Set("g_levelStartTime", va("%i", trap_RealTime(NULL, qtrue, 0)));
-
 	if ( g_gametype.integer != GT_SINGLE_PLAYER && g_logfile.string[0] ) {
 		if ( g_logfileSync.integer ) {
 			trap_FS_FOpenFile( g_logfile.string, &level.logFile, FS_APPEND_SYNC );
@@ -554,8 +498,6 @@
 
 	if( g_gametype.integer == GT_SINGLE_PLAYER || trap_Cvar_VariableIntegerValue( "com_buildScript" ) ) {
 		G_ModelIndex( SP_PODIUM_MODEL );
-		G_SoundIndex( "sound/player/gurp1.wav" );
-		G_SoundIndex( "sound/player/gurp2.wav" );
 	}
 
 	if ( trap_Cvar_VariableIntegerValue( "bot_enable" ) ) {
@@ -668,7 +610,7 @@
 
 		if(!nextInLine || client->sess.spectatorNum > nextInLine->sess.spectatorNum)
 			nextInLine = client;
-		}
+	}
 
 	if ( !nextInLine ) {
 		return;
@@ -692,11 +634,11 @@
 {
 	int index;
 	gclient_t *curclient;
-
+	
 	for(index = 0; index < level.maxclients; index++)
 	{
 		curclient = &level.clients[index];
-
+		
 		if(curclient->pers.connected != CON_DISCONNECTED)
 		{
 			if(curclient == client)
@@ -974,9 +916,6 @@
 	for ( i = 0 ; i < level.maxclients ; i++ ) {
 		if ( level.clients[ i ].pers.connected == CON_CONNECTED ) {
 			DeathmatchScoreboardMessage( g_entities + i );
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				DuelScores(g_entities + i);
-			}
 		}
 	}
 }
@@ -1536,7 +1475,7 @@
 		if ( level.numPlayingClients != 2 ) {
 			if ( level.warmupTime != -1 ) {
 				level.warmupTime = -1;
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 				G_LogPrintf( "Warmup:\n" );
 			}
 			return;
@@ -1562,7 +1501,7 @@
 					level.warmupTime = 0;
 				}
 
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 			}
 			return;
 		}
@@ -1579,7 +1518,7 @@
 		int		counts[TEAM_NUM_TEAMS];
 		qboolean	notEnough = qfalse;
 
-		if ( g_gametype.integer >= GT_TEAM ) {  //FIXME need something like G_IsTeamGame()
+		if ( g_gametype.integer >= GT_TEAM ) {
 			counts[TEAM_BLUE] = TeamCount( -1, TEAM_BLUE );
 			counts[TEAM_RED] = TeamCount( -1, TEAM_RED );
 
@@ -1593,7 +1532,7 @@
 		if ( notEnough ) {
 			if ( level.warmupTime != -1 ) {
 				level.warmupTime = -1;
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 				G_LogPrintf( "Warmup:\n" );
 			}
 			return; // still waiting for team members
@@ -1618,7 +1557,7 @@
 				level.warmupTime = 0;
 			}
 
-			trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+			trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 			return;
 		}
 
@@ -1819,7 +1758,7 @@
 =============
 */
 void G_RunThink (gentity_t *ent) {
-	int thinktime;
+	int	thinktime;
 
 	thinktime = ent->nextthink;
 	if (thinktime <= 0) {
@@ -1828,7 +1767,7 @@
 	if (thinktime > level.time) {
 		return;
 	}
-
+	
 	ent->nextthink = 0;
 	if (!ent->think) {
 		G_Error ( "NULL ent->think");
@@ -1859,22 +1798,6 @@
 	// get any cvar changes
 	G_UpdateCvars();
 
-	if (*level.serverSound) {
-		//gentity_t	*te;
-
-#if 0
-		te = G_TempEntity(level.serverSoundOrigin, EV_GLOBAL_SOUND);
-		te->s.eventParm = G_SoundIndex("sound/items/poweruprespawn.wav");
-		te->r.svFlags |= SVF_BROADCAST;
-		//Com_Printf("playing sound\n");
-#endif
-
-        //te = G_TempEntity(level.serverSoundOrigin, EV_PLAYER_TELEPORT_IN);
-		//te->s.clientNum = level.serverSoundEnt->s.clientNum;
-		//void G_Say( gentity_t *ent, gentity_t *target, int mode, const char *chatText )
-		G_Say(level.serverSoundEnt, level.serverSoundEnt, 0, "test test test");
-	}
-
 	//
 	// go through all allocated objects
 	//

```

### `openarena-engine`  — sha256 `b9d79fa764ad...`, 48792 bytes

_Diff stat: +27 / -133 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_main.c	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_main.c	2026-04-16 22:48:25.747535800 +0100
@@ -81,8 +81,7 @@
 vmCvar_t	pmove_msec;
 vmCvar_t	g_rankings;
 vmCvar_t	g_listEntity;
-vmCvar_t	g_localTeamPref;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 vmCvar_t	g_obeliskHealth;
 vmCvar_t	g_obeliskRegenPeriod;
 vmCvar_t	g_obeliskRegenAmount;
@@ -95,17 +94,6 @@
 vmCvar_t	g_enableBreath;
 vmCvar_t	g_proxMineTimeout;
 #endif
-vmCvar_t g_levelStartTime;
-
-vmCvar_t g_weapon_rocket_speed;
-
-vmCvar_t g_weapon_plasma_speed;
-//vmCvar_t g_weapon_plasma_rate;
-
-vmCvar_t g_debugPingValue;
-vmCvar_t g_ammoPack;
-vmCvar_t g_ammoPackHack;
-vmCvar_t g_wolfcamVersion;
 
 static cvarTable_t		gameCvarTable[] = {
 	// don't override the cheat state set by the system
@@ -113,7 +101,7 @@
 
 	// noset vars
 	{ NULL, "gamename", GAMEVERSION , CVAR_SERVERINFO | CVAR_ROM, 0, qfalse  },
-	{ NULL, "gamedate", PRODUCT_DATE , CVAR_ROM, 0, qfalse  },
+	{ NULL, "gamedate", __DATE__ , CVAR_ROM, 0, qfalse  },
 	{ &g_restarted, "g_restarted", "0", CVAR_ROM, 0, qfalse  },
 
 	// latched vars
@@ -169,15 +157,15 @@
 	{ &g_allowVote, "g_allowVote", "1", CVAR_ARCHIVE, 0, qfalse },
 	{ &g_listEntity, "g_listEntity", "0", 0, 0, qfalse },
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	{ &g_obeliskHealth, "g_obeliskHealth", "2500", 0, 0, qfalse },
 	{ &g_obeliskRegenPeriod, "g_obeliskRegenPeriod", "1", 0, 0, qfalse },
 	{ &g_obeliskRegenAmount, "g_obeliskRegenAmount", "15", 0, 0, qfalse },
 	{ &g_obeliskRespawnDelay, "g_obeliskRespawnDelay", "10", CVAR_SERVERINFO, 0, qfalse },
 
 	{ &g_cubeTimeout, "g_cubeTimeout", "30", 0, 0, qfalse },
-	{ &g_redteam, "g_redteam", DEFAULT_REDTEAM_NAME, CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue },
-	{ &g_blueteam, "g_blueteam", DEFAULT_BLUETEAM_NAME, CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue  },
+	{ &g_redteam, "g_redteam", "Stroggs", CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue },
+	{ &g_blueteam, "g_blueteam", "Pagans", CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_USERINFO , 0, qtrue, qtrue  },
 	{ &g_singlePlayer, "ui_singlePlayerActive", "", 0, 0, qfalse, qfalse  },
 
 	{ &g_enableDust, "g_enableDust", "0", CVAR_SERVERINFO, 0, qtrue, qfalse },
@@ -188,16 +176,7 @@
 	{ &pmove_fixed, "pmove_fixed", "0", CVAR_SYSTEMINFO, 0, qfalse},
 	{ &pmove_msec, "pmove_msec", "8", CVAR_SYSTEMINFO, 0, qfalse},
 
-	{ &g_rankings, "g_rankings", "0", 0, 0, qfalse},
-	{ &g_localTeamPref, "g_localTeamPref", "", 0, 0, qfalse },
-	{ &g_levelStartTime, "g_levelStartTime", "0", CVAR_SERVERINFO, 0, qfalse },
-	{ &g_weapon_rocket_speed, "g_weapon_rocket_speed", "900", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_weapon_plasma_speed, "g_weapon_plasma_speed", "2000", CVAR_ARCHIVE, 0, qfalse },
-	//{ &g_weapon_plasma_rate, "g_weapon_plasma_rate", "100", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_debugPingValue, "g_debugPingValue", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_ammoPack, "g_ammoPack", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_ammoPackHack, "g_ammoPackHack", "0", CVAR_ARCHIVE, 0, qfalse },
-	{ &g_wolfcamVersion, "wolfcamversion", WOLFCAM_VERSION, CVAR_SERVERINFO | CVAR_ROM, 0, qfalse },
+	{ &g_rankings, "g_rankings", "0", 0, 0, qfalse}
 
 };
 
@@ -285,7 +264,7 @@
 Chain together all entities with a matching team field.
 Entity teams are used for item groups and multi-entity mover groups.
 
-All but the first will have the FL_TEAMMEMBER flag set and teammaster field set
+All but the first will have the FL_TEAMSLAVE flag set and teammaster field set
 All but the last will have the teamchain field set to the next one
 ================
 */
@@ -296,12 +275,12 @@
 
 	c = 0;
 	c2 = 0;
-	for ( i=MAX_CLIENTS, e=g_entities+i ; i < level.num_entities ; i++,e++ ) {
+	for ( i=1, e=g_entities+i ; i < level.num_entities ; i++,e++ ){
 		if (!e->inuse)
 			continue;
 		if (!e->team)
 			continue;
-		if (e->flags & FL_TEAMMEMBER)
+		if (e->flags & FL_TEAMSLAVE)
 			continue;
 		e->teammaster = e;
 		c++;
@@ -312,7 +291,7 @@
 				continue;
 			if (!e2->team)
 				continue;
-			if (e2->flags & FL_TEAMMEMBER)
+			if (e2->flags & FL_TEAMSLAVE)
 				continue;
 			if (!strcmp(e->team, e2->team))
 			{
@@ -320,7 +299,7 @@
 				e2->teamchain = e->teamchain;
 				e->teamchain = e2;
 				e2->teammaster = e;
-				e2->flags |= FL_TEAMMEMBER;
+				e2->flags |= FL_TEAMSLAVE;
 
 				// make sure that targets only point at the master
 				if ( e2->targetname ) {
@@ -335,7 +314,7 @@
 }
 
 void G_RemapTeamShaders( void ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	char string[1024];
 	float f = level.time * 0.001;
 	Com_sprintf( string, sizeof(string), "team_icon/%s_red", g_redteam.string );
@@ -426,13 +405,10 @@
 */
 void G_InitGame( int levelTime, int randomSeed, int restart ) {
 	int					i;
-	int protocol;
-	char buffer[256];
 
 	G_Printf ("------- Game Initialization -------\n");
 	G_Printf ("gamename: %s\n", GAMEVERSION);
-	G_Printf ("gamedate: %s\n", PRODUCT_DATE);
-	G_Printf("version: %s\n", WOLFCAM_VERSION);
+	G_Printf ("gamedate: %s\n", __DATE__);
 
 	srand( randomSeed );
 
@@ -442,38 +418,6 @@
 
 	G_InitMemory();
 
-	trap_Cvar_VariableStringBuffer("protocol", buffer, sizeof(buffer));
-	protocol = atoi(buffer);
-	G_Printf("protocol %d\n", protocol);
-
-	if (protocol == 91) {
-		// defaults to protocol 91
-		PW_NONE = PW91_NONE;
-		//PW_SPAWNARMOR = PW91_SPAWNARMOR;
-		PW_QUAD = PW91_QUAD;
-		PW_BATTLESUIT = PW91_BATTLESUIT;
-		PW_HASTE = PW91_HASTE;
-		PW_INVIS = PW91_INVIS;
-		PW_REGEN = PW91_REGEN;
-		PW_FLIGHT = PW91_FLIGHT;
-		PW_REDFLAG = PW91_REDFLAG;
-		PW_BLUEFLAG = PW91_BLUEFLAG;
-		PW_NEUTRALFLAG = PW91_NEUTRALFLAG;
-		PW_INVULNERABILITY = PW91_INVULNERABILITY;
-		PW_SCOUT = PW91_SCOUT;
-		PW_GUARD = PW91_GUARD;
-		PW_DOUBLER = PW91_DOUBLER;
-		PW_ARMORREGEN = PW91_ARMORREGEN;
-		PW_FROZEN = PW91_FROZEN;
-		PW_NUM_POWERUPS = PW91_NUM_POWERUPS;
-
-		memcpy(&bg_itemlist, &bg_itemlistQldm91, sizeof(gitem_t) * bg_numItemsQldm91);
-		bg_numItems = bg_numItemsQldm91;
-	} else {
-		//FIXME
-		G_Printf("^3FIXME: game unsupported protocol %d\n", protocol);
-	}
-
 	// set some level globals
 	memset( &level, 0, sizeof( level ) );
 	level.time = levelTime;
@@ -481,8 +425,6 @@
 
 	level.snd_fry = G_SoundIndex("sound/player/fry.wav");	// FIXME standing in lava / slime
 
-	trap_Cvar_Set("g_levelStartTime", va("%i", trap_RealTime(NULL, qtrue, 0)));
-
 	if ( g_gametype.integer != GT_SINGLE_PLAYER && g_logfile.string[0] ) {
 		if ( g_logfileSync.integer ) {
 			trap_FS_FOpenFile( g_logfile.string, &level.logFile, FS_APPEND_SYNC );
@@ -554,8 +496,6 @@
 
 	if( g_gametype.integer == GT_SINGLE_PLAYER || trap_Cvar_VariableIntegerValue( "com_buildScript" ) ) {
 		G_ModelIndex( SP_PODIUM_MODEL );
-		G_SoundIndex( "sound/player/gurp1.wav" );
-		G_SoundIndex( "sound/player/gurp2.wav" );
 	}
 
 	if ( trap_Cvar_VariableIntegerValue( "bot_enable" ) ) {
@@ -566,7 +506,6 @@
 
 	G_RemapTeamShaders();
 
-	trap_SetConfigstring( CS_INTERMISSION, "" );
 }
 
 
@@ -598,7 +537,7 @@
 
 //===================================================================
 
-void QDECL Com_Error ( int logLevel, const char *error, ... ) {
+void QDECL Com_Error ( int level, const char *error, ... ) {
 	va_list		argptr;
 	char		text[1024];
 
@@ -668,7 +607,7 @@
 
 		if(!nextInLine || client->sess.spectatorNum > nextInLine->sess.spectatorNum)
 			nextInLine = client;
-		}
+	}
 
 	if ( !nextInLine ) {
 		return;
@@ -692,11 +631,11 @@
 {
 	int index;
 	gclient_t *curclient;
-
+	
 	for(index = 0; index < level.maxclients; index++)
 	{
 		curclient = &level.clients[index];
-
+		
 		if(curclient->pers.connected != CON_DISCONNECTED)
 		{
 			if(curclient == client)
@@ -974,9 +913,6 @@
 	for ( i = 0 ; i < level.maxclients ; i++ ) {
 		if ( level.clients[ i ].pers.connected == CON_CONNECTED ) {
 			DeathmatchScoreboardMessage( g_entities + i );
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				DuelScores(g_entities + i);
-			}
 		}
 	}
 }
@@ -1208,7 +1144,6 @@
 	gclient_t		*cl;
 #ifdef MISSIONPACK
 	qboolean won = qtrue;
-	team_t team = TEAM_RED;
 #endif
 	G_LogPrintf( "Exit: %s\n", string );
 
@@ -1245,10 +1180,7 @@
 
 		G_LogPrintf( "score: %i  ping: %i  client: %i %s\n", cl->ps.persistant[PERS_SCORE], ping, level.sortedClients[i],	cl->pers.netname );
 #ifdef MISSIONPACK
-		if (g_singlePlayer.integer && !(g_entities[cl - level.clients].r.svFlags & SVF_BOT)) {
-			team = cl->sess.sessionTeam;
-		}
-		if (g_singlePlayer.integer && g_gametype.integer < GT_TEAM) {
+		if (g_singlePlayer.integer && g_gametype.integer == GT_TOURNAMENT) {
 			if (g_entities[cl - level.clients].r.svFlags & SVF_BOT && cl->ps.persistant[PERS_RANK] == 0) {
 				won = qfalse;
 			}
@@ -1259,12 +1191,8 @@
 
 #ifdef MISSIONPACK
 	if (g_singlePlayer.integer) {
-		if (g_gametype.integer >= GT_TEAM) {
-			if (team == TEAM_BLUE) {
-				won = level.teamScores[TEAM_BLUE] > level.teamScores[TEAM_RED];
-			} else {
-				won = level.teamScores[TEAM_RED] > level.teamScores[TEAM_BLUE];
-			}
+		if (g_gametype.integer >= GT_CTF) {
+			won = level.teamScores[TEAM_RED] > level.teamScores[TEAM_BLUE];
 		}
 		trap_SendConsoleCommand( EXEC_APPEND, (won) ? "spWin\n" : "spLose\n" );
 	}
@@ -1427,12 +1355,6 @@
 		return;
 	}
 
-	if ( g_timelimit.integer < 0 || g_timelimit.integer > INT_MAX / 60000 ) {
-		G_Printf( "timelimit %i is out of range, defaulting to 0\n", g_timelimit.integer );
-		trap_Cvar_Set( "timelimit", "0" );
-		trap_Cvar_Update( &g_timelimit );
-	}
-
 	if ( g_timelimit.integer && !level.warmupTime ) {
 		if ( level.time - level.startTime >= g_timelimit.integer*60000 ) {
 			trap_SendServerCommand( -1, "print \"Timelimit hit.\n\"");
@@ -1441,12 +1363,6 @@
 		}
 	}
 
-	if ( g_fraglimit.integer < 0 ) {
-		G_Printf( "fraglimit %i is out of range, defaulting to 0\n", g_fraglimit.integer );
-		trap_Cvar_Set( "fraglimit", "0" );
-		trap_Cvar_Update( &g_fraglimit );
-	}
-
 	if ( g_gametype.integer < GT_CTF && g_fraglimit.integer ) {
 		if ( level.teamScores[TEAM_RED] >= g_fraglimit.integer ) {
 			trap_SendServerCommand( -1, "print \"Red hit the fraglimit.\n\"" );
@@ -1478,12 +1394,6 @@
 		}
 	}
 
-	if ( g_capturelimit.integer < 0 ) {
-		G_Printf( "capturelimit %i is out of range, defaulting to 0\n", g_capturelimit.integer );
-		trap_Cvar_Set( "capturelimit", "0" );
-		trap_Cvar_Update( &g_capturelimit );
-	}
-
 	if ( g_gametype.integer >= GT_CTF && g_capturelimit.integer ) {
 
 		if ( level.teamScores[TEAM_RED] >= g_capturelimit.integer ) {
@@ -1536,7 +1446,7 @@
 		if ( level.numPlayingClients != 2 ) {
 			if ( level.warmupTime != -1 ) {
 				level.warmupTime = -1;
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 				G_LogPrintf( "Warmup:\n" );
 			}
 			return;
@@ -1562,7 +1472,7 @@
 					level.warmupTime = 0;
 				}
 
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 			}
 			return;
 		}
@@ -1579,7 +1489,7 @@
 		int		counts[TEAM_NUM_TEAMS];
 		qboolean	notEnough = qfalse;
 
-		if ( g_gametype.integer >= GT_TEAM ) {  //FIXME need something like G_IsTeamGame()
+		if ( g_gametype.integer > GT_TEAM ) {
 			counts[TEAM_BLUE] = TeamCount( -1, TEAM_BLUE );
 			counts[TEAM_RED] = TeamCount( -1, TEAM_RED );
 
@@ -1593,7 +1503,7 @@
 		if ( notEnough ) {
 			if ( level.warmupTime != -1 ) {
 				level.warmupTime = -1;
-				trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+				trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 				G_LogPrintf( "Warmup:\n" );
 			}
 			return; // still waiting for team members
@@ -1618,7 +1528,7 @@
 				level.warmupTime = 0;
 			}
 
-			trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+			trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 			return;
 		}
 
@@ -1819,7 +1729,7 @@
 =============
 */
 void G_RunThink (gentity_t *ent) {
-	int thinktime;
+	float	thinktime;
 
 	thinktime = ent->nextthink;
 	if (thinktime <= 0) {
@@ -1828,7 +1738,7 @@
 	if (thinktime > level.time) {
 		return;
 	}
-
+	
 	ent->nextthink = 0;
 	if (!ent->think) {
 		G_Error ( "NULL ent->think");
@@ -1859,22 +1769,6 @@
 	// get any cvar changes
 	G_UpdateCvars();
 
-	if (*level.serverSound) {
-		//gentity_t	*te;
-
-#if 0
-		te = G_TempEntity(level.serverSoundOrigin, EV_GLOBAL_SOUND);
-		te->s.eventParm = G_SoundIndex("sound/items/poweruprespawn.wav");
-		te->r.svFlags |= SVF_BROADCAST;
-		//Com_Printf("playing sound\n");
-#endif
-
-        //te = G_TempEntity(level.serverSoundOrigin, EV_PLAYER_TELEPORT_IN);
-		//te->s.clientNum = level.serverSoundEnt->s.clientNum;
-		//void G_Say( gentity_t *ent, gentity_t *target, int mode, const char *chatText )
-		G_Say(level.serverSoundEnt, level.serverSoundEnt, 0, "test test test");
-	}
-
 	//
 	// go through all allocated objects
 	//

```

### `openarena-gamecode`  — sha256 `e6561244c143...`, 78353 bytes

_Diff stat: +1156 / -344 lines_

_(full diff is 73024 bytes — see files directly)_
