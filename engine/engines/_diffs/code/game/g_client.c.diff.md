# Diff: `code/game/g_client.c`
**Canonical:** `wolfcamql-src` (sha256 `79de525d6516...`, 35562 bytes)

## Variants

### `quake3-source`  — sha256 `52a3c908aeff...`, 35166 bytes

_Diff stat: +236 / -234 lines_

_(full diff is 23663 bytes — see files directly)_

### `ioquake3`  — sha256 `e805a3efbd6b...`, 35465 bytes

_Diff stat: +23 / -29 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_client.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_client.c	2026-04-16 20:02:21.542851200 +0100
@@ -21,10 +21,12 @@
 */
 //
 #include "g_local.h"
-#include "bg_local.h"
 
 // g_client.c -- client functions that don't happen every frame
 
+static vec3_t	playerMins = {-15, -15, -24};
+static vec3_t	playerMaxs = {15, 15, 32};
+
 /*QUAKED info_player_deathmatch (1 0 1) (-16 -16 -24) (16 16 32) initial
 potential spawning position for deathmatch games.
 The first time a player enters the game, they will be at an 'initial' spot.
@@ -82,8 +84,8 @@
 	gentity_t	*hit;
 	vec3_t		mins, maxs;
 
-	VectorAdd( spot->s.origin, bg_playerMins, mins );
-	VectorAdd( spot->s.origin, bg_playerMaxs, maxs );
+	VectorAdd( spot->s.origin, playerMins, mins );
+	VectorAdd( spot->s.origin, playerMaxs, maxs );
 	num = trap_EntitiesInBox( mins, maxs, touch, MAX_GENTITIES );
 
 	for (i=0 ; i<num ; i++) {
@@ -398,7 +400,7 @@
 =============
 */
 void CopyToBodyQue( gentity_t *ent ) {
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	gentity_t	*e;
 	int i;
 #endif
@@ -419,7 +421,7 @@
 
 	body->s = ent->s;
 	body->s.eFlags = EF_DEAD;		// clear EF_TALK, etc
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if ( ent->s.eFlags & EF_KAMIKAZE ) {
 		body->s.eFlags |= EF_KAMIKAZE;
 
@@ -708,8 +710,8 @@
 	gclient_t	*client;
 	char	c1[MAX_INFO_STRING];
 	char	c2[MAX_INFO_STRING];
-	//char	redTeam[MAX_INFO_STRING];
-	//char	blueTeam[MAX_INFO_STRING];
+	char	redTeam[MAX_INFO_STRING];
+	char	blueTeam[MAX_INFO_STRING];
 	char	userinfo[MAX_INFO_STRING];
 
 	ent = g_entities + clientNum;
@@ -751,7 +753,7 @@
 	}
 
 	// set max health
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if (client->ps.powerups[PW_GUARD]) {
 		client->pers.maxHealth = 200;
 	} else {
@@ -771,15 +773,13 @@
 	client->ps.stats[STAT_MAX_HEALTH] = client->pers.maxHealth;
 
 	// set model
-#if 0
 	if( g_gametype.integer >= GT_TEAM ) {
 		Q_strncpyz( model, Info_ValueForKey (userinfo, "team_model"), sizeof( model ) );
 		Q_strncpyz( headModel, Info_ValueForKey (userinfo, "team_headmodel"), sizeof( headModel ) );
 	} else {
-#endif
 		Q_strncpyz( model, Info_ValueForKey (userinfo, "model"), sizeof( model ) );
 		Q_strncpyz( headModel, Info_ValueForKey (userinfo, "headmodel"), sizeof( headModel ) );
-		//}
+	}
 
 /*	NOTE: all client side now
 
@@ -802,7 +802,7 @@
 	}
 */
 
-#if 1  //MISSIONPACK
+#ifdef MISSIONPACK
 	if (g_gametype.integer >= GT_TEAM && !(ent->r.svFlags & SVF_BOT)) {
 		client->pers.teamInfo = qtrue;
 	} else {
@@ -841,22 +841,22 @@
 	Q_strncpyz(c1, Info_ValueForKey( userinfo, "color1" ), sizeof( c1 ));
 	Q_strncpyz(c2, Info_ValueForKey( userinfo, "color2" ), sizeof( c2 ));
 
-	//Q_strncpyz(redTeam, Info_ValueForKey( userinfo, "g_redteam" ), sizeof( redTeam ));
-	//Q_strncpyz(blueTeam, Info_ValueForKey( userinfo, "g_blueteam" ), sizeof( blueTeam ));
-
+	Q_strncpyz(redTeam, Info_ValueForKey( userinfo, "g_redteam" ), sizeof( redTeam ));
+	Q_strncpyz(blueTeam, Info_ValueForKey( userinfo, "g_blueteam" ), sizeof( blueTeam ));
+	
 	// send over a subset of the userinfo keys so other clients can
 	// print scoreboards, display models, and play custom sounds
 	if (ent->r.svFlags & SVF_BOT)
 	{
 		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\skill\\%s\\tt\\%d\\tl\\%d",
-			   client->pers.netname, client->sess.sessionTeam, model, headModel, c1, c2,
+			client->pers.netname, client->sess.sessionTeam, model, headModel, c1, c2,
 			client->pers.maxHealth, client->sess.wins, client->sess.losses,
 			Info_ValueForKey( userinfo, "skill" ), teamTask, teamLeader );
 	}
 	else
 	{
-		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\tt\\%d\\tl\\%d\\su\\1",
-			   client->pers.netname, client->sess.sessionTeam, model, headModel, c1, c2,
+		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\g_redteam\\%s\\g_blueteam\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\tt\\%d\\tl\\%d",
+			client->pers.netname, client->sess.sessionTeam, model, headModel, redTeam, blueTeam, c1, c2, 
 			client->pers.maxHealth, client->sess.wins, client->sess.losses, teamTask, teamLeader);
 	}
 
@@ -1158,9 +1158,9 @@
 	ent->waterlevel = 0;
 	ent->watertype = 0;
 	ent->flags = 0;
-
-	VectorCopy (bg_playerMins, ent->r.mins);
-	VectorCopy (bg_playerMaxs, ent->r.maxs);
+	
+	VectorCopy (playerMins, ent->r.mins);
+	VectorCopy (playerMaxs, ent->r.maxs);
 
 	client->ps.clientNum = index;
 
@@ -1168,7 +1168,7 @@
 	if ( g_gametype.integer == GT_TEAM ) {
 		client->ps.ammo[WP_MACHINEGUN] = 50;
 	} else {
-		client->ps.ammo[WP_MACHINEGUN] = 150;
+		client->ps.ammo[WP_MACHINEGUN] = 100;
 	}
 
 	client->ps.stats[STAT_WEAPONS] |= ( 1 << WP_GAUNTLET );
@@ -1178,12 +1178,6 @@
 	// health will count down towards max_health
 	ent->health = client->ps.stats[STAT_HEALTH] = client->ps.stats[STAT_MAX_HEALTH] + 25;
 
-#if 0  // hack to match quake live
-	if (client->sess.spectatorState == SPECTATOR_FREE) {
-		//ent->health = client->ps.stats[STAT_HEALTH] = 0;
-	}
-#endif
-
 	G_SetOrigin( ent, spawn_origin );
 	VectorCopy( spawn_origin, client->ps.origin );
 
@@ -1293,7 +1287,7 @@
 		// They don't get to take powerups with them!
 		// Especially important for stuff like CTF flags
 		TossClientItems( ent );
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 		TossClientPersistantPowerups( ent );
 		if( g_gametype.integer == GT_HARVESTER ) {
 			TossClientCubes( ent );

```

### `openarena-engine`  — sha256 `79a8e9999be6...`, 35831 bytes

_Diff stat: +57 / -47 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_client.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_client.c	2026-04-16 22:48:25.745536200 +0100
@@ -21,10 +21,12 @@
 */
 //
 #include "g_local.h"
-#include "bg_local.h"
 
 // g_client.c -- client functions that don't happen every frame
 
+static vec3_t	playerMins = {-15, -15, -24};
+static vec3_t	playerMaxs = {15, 15, 32};
+
 /*QUAKED info_player_deathmatch (1 0 1) (-16 -16 -24) (16 16 32) initial
 potential spawning position for deathmatch games.
 The first time a player enters the game, they will be at an 'initial' spot.
@@ -46,7 +48,7 @@
 }
 
 /*QUAKED info_player_start (1 0 0) (-16 -16 -24) (16 16 32)
-equivalent to info_player_deathmatch
+equivelant to info_player_deathmatch
 */
 void SP_info_player_start(gentity_t *ent) {
 	ent->classname = "info_player_deathmatch";
@@ -82,8 +84,8 @@
 	gentity_t	*hit;
 	vec3_t		mins, maxs;
 
-	VectorAdd( spot->s.origin, bg_playerMins, mins );
-	VectorAdd( spot->s.origin, bg_playerMaxs, maxs );
+	VectorAdd( spot->s.origin, playerMins, mins );
+	VectorAdd( spot->s.origin, playerMaxs, maxs );
 	num = trap_EntitiesInBox( mins, maxs, touch, MAX_GENTITIES );
 
 	for (i=0 ; i<num ; i++) {
@@ -375,7 +377,7 @@
 =============
 BodySink
 
-After sitting around for five seconds, fall into the ground and disappear
+After sitting around for five seconds, fall into the ground and dissapear
 =============
 */
 void BodySink( gentity_t *ent ) {
@@ -398,7 +400,7 @@
 =============
 */
 void CopyToBodyQue( gentity_t *ent ) {
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	gentity_t	*e;
 	int i;
 #endif
@@ -419,7 +421,7 @@
 
 	body->s = ent->s;
 	body->s.eFlags = EF_DEAD;		// clear EF_TALK, etc
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if ( ent->s.eFlags & EF_KAMIKAZE ) {
 		body->s.eFlags |= EF_KAMIKAZE;
 
@@ -628,7 +630,7 @@
 
 /*
 ===========
-ClientCleanName
+ClientCheckName
 ============
 */
 static void ClientCleanName(const char *in, char *out, int outSize)
@@ -700,7 +702,7 @@
 */
 void ClientUserinfoChanged( int clientNum ) {
 	gentity_t *ent;
-	int		teamTask, teamLeader, health;
+	int		teamTask, teamLeader, team, health;
 	char	*s;
 	char	model[MAX_QPATH];
 	char	headModel[MAX_QPATH];
@@ -708,8 +710,8 @@
 	gclient_t	*client;
 	char	c1[MAX_INFO_STRING];
 	char	c2[MAX_INFO_STRING];
-	//char	redTeam[MAX_INFO_STRING];
-	//char	blueTeam[MAX_INFO_STRING];
+	char	redTeam[MAX_INFO_STRING];
+	char	blueTeam[MAX_INFO_STRING];
 	char	userinfo[MAX_INFO_STRING];
 
 	ent = g_entities + clientNum;
@@ -724,6 +726,12 @@
 		trap_DropClient(clientNum, "Invalid userinfo");
 	}
 
+	// check for local client
+	s = Info_ValueForKey( userinfo, "ip" );
+	if ( !strcmp( s, "localhost" ) ) {
+		client->pers.localClient = qtrue;
+	}
+
 	// check the item prediction
 	s = Info_ValueForKey( userinfo, "cg_predictItems" );
 	if ( !atoi( s ) ) {
@@ -751,7 +759,7 @@
 	}
 
 	// set max health
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if (client->ps.powerups[PW_GUARD]) {
 		client->pers.maxHealth = 200;
 	} else {
@@ -771,15 +779,29 @@
 	client->ps.stats[STAT_MAX_HEALTH] = client->pers.maxHealth;
 
 	// set model
-#if 0
 	if( g_gametype.integer >= GT_TEAM ) {
 		Q_strncpyz( model, Info_ValueForKey (userinfo, "team_model"), sizeof( model ) );
 		Q_strncpyz( headModel, Info_ValueForKey (userinfo, "team_headmodel"), sizeof( headModel ) );
 	} else {
-#endif
 		Q_strncpyz( model, Info_ValueForKey (userinfo, "model"), sizeof( model ) );
 		Q_strncpyz( headModel, Info_ValueForKey (userinfo, "headmodel"), sizeof( headModel ) );
-		//}
+	}
+
+	// bots set their team a few frames later
+	if (g_gametype.integer >= GT_TEAM && g_entities[clientNum].r.svFlags & SVF_BOT) {
+		s = Info_ValueForKey( userinfo, "team" );
+		if ( !Q_stricmp( s, "red" ) || !Q_stricmp( s, "r" ) ) {
+			team = TEAM_RED;
+		} else if ( !Q_stricmp( s, "blue" ) || !Q_stricmp( s, "b" ) ) {
+			team = TEAM_BLUE;
+		} else {
+			// pick the team with the least number of players
+			team = PickTeam( clientNum );
+		}
+	}
+	else {
+		team = client->sess.sessionTeam;
+	}
 
 /*	NOTE: all client side now
 
@@ -802,8 +824,8 @@
 	}
 */
 
-#if 1  //MISSIONPACK
-	if (g_gametype.integer >= GT_TEAM && !(ent->r.svFlags & SVF_BOT)) {
+#ifdef MISSIONPACK
+	if (g_gametype.integer >= GT_TEAM) {
 		client->pers.teamInfo = qtrue;
 	} else {
 		s = Info_ValueForKey( userinfo, "teamoverlay" );
@@ -838,25 +860,25 @@
 	teamLeader = client->sess.teamLeader;
 
 	// colors
-	Q_strncpyz(c1, Info_ValueForKey( userinfo, "color1" ), sizeof( c1 ));
-	Q_strncpyz(c2, Info_ValueForKey( userinfo, "color2" ), sizeof( c2 ));
-
-	//Q_strncpyz(redTeam, Info_ValueForKey( userinfo, "g_redteam" ), sizeof( redTeam ));
-	//Q_strncpyz(blueTeam, Info_ValueForKey( userinfo, "g_blueteam" ), sizeof( blueTeam ));
+	strcpy(c1, Info_ValueForKey( userinfo, "color1" ));
+	strcpy(c2, Info_ValueForKey( userinfo, "color2" ));
 
+	strcpy(redTeam, Info_ValueForKey( userinfo, "g_redteam" ));
+	strcpy(blueTeam, Info_ValueForKey( userinfo, "g_blueteam" ));
+	
 	// send over a subset of the userinfo keys so other clients can
 	// print scoreboards, display models, and play custom sounds
 	if (ent->r.svFlags & SVF_BOT)
 	{
 		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\skill\\%s\\tt\\%d\\tl\\%d",
-			   client->pers.netname, client->sess.sessionTeam, model, headModel, c1, c2,
+			client->pers.netname, team, model, headModel, c1, c2, 
 			client->pers.maxHealth, client->sess.wins, client->sess.losses,
 			Info_ValueForKey( userinfo, "skill" ), teamTask, teamLeader );
 	}
 	else
 	{
-		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\tt\\%d\\tl\\%d\\su\\1",
-			   client->pers.netname, client->sess.sessionTeam, model, headModel, c1, c2,
+		s = va("n\\%s\\t\\%i\\model\\%s\\hmodel\\%s\\g_redteam\\%s\\g_blueteam\\%s\\c1\\%s\\c2\\%s\\hc\\%i\\w\\%i\\l\\%i\\tt\\%d\\tl\\%d",
+			client->pers.netname, client->sess.sessionTeam, model, headModel, redTeam, blueTeam, c1, c2, 
 			client->pers.maxHealth, client->sess.wins, client->sess.losses, teamTask, teamLeader);
 	}
 
@@ -934,11 +956,11 @@
 
 	client->pers.connected = CON_CONNECTING;
 
-	// check for local client
-	value = Info_ValueForKey( userinfo, "ip" );
-	if ( !strcmp( value, "localhost" ) ) {
-		client->pers.localClient = qtrue;
+	// read or initialize the session data
+	if ( firstTime || level.newSession ) {
+		G_InitSessionData( client, userinfo );
 	}
+	G_ReadSessionData( client );
 
 	if( isBot ) {
 		ent->r.svFlags |= SVF_BOT;
@@ -948,13 +970,7 @@
 		}
 	}
 
-	// read or initialize the session data
-	if ( firstTime || level.newSession ) {
-		G_InitSessionData( client, userinfo );
-	}
-	G_ReadSessionData( client );
-
-	// get and distribute relevant parameters
+	// get and distribute relevent paramters
 	G_LogPrintf( "ClientConnect: %i\n", clientNum );
 	ClientUserinfoChanged( clientNum );
 
@@ -1158,9 +1174,9 @@
 	ent->waterlevel = 0;
 	ent->watertype = 0;
 	ent->flags = 0;
-
-	VectorCopy (bg_playerMins, ent->r.mins);
-	VectorCopy (bg_playerMaxs, ent->r.maxs);
+	
+	VectorCopy (playerMins, ent->r.mins);
+	VectorCopy (playerMaxs, ent->r.maxs);
 
 	client->ps.clientNum = index;
 
@@ -1168,7 +1184,7 @@
 	if ( g_gametype.integer == GT_TEAM ) {
 		client->ps.ammo[WP_MACHINEGUN] = 50;
 	} else {
-		client->ps.ammo[WP_MACHINEGUN] = 150;
+		client->ps.ammo[WP_MACHINEGUN] = 100;
 	}
 
 	client->ps.stats[STAT_WEAPONS] |= ( 1 << WP_GAUNTLET );
@@ -1178,12 +1194,6 @@
 	// health will count down towards max_health
 	ent->health = client->ps.stats[STAT_HEALTH] = client->ps.stats[STAT_MAX_HEALTH] + 25;
 
-#if 0  // hack to match quake live
-	if (client->sess.spectatorState == SPECTATOR_FREE) {
-		//ent->health = client->ps.stats[STAT_HEALTH] = 0;
-	}
-#endif
-
 	G_SetOrigin( ent, spawn_origin );
 	VectorCopy( spawn_origin, client->ps.origin );
 
@@ -1293,7 +1303,7 @@
 		// They don't get to take powerups with them!
 		// Especially important for stuff like CTF flags
 		TossClientItems( ent );
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 		TossClientPersistantPowerups( ent );
 		if( g_gametype.integer == GT_HARVESTER ) {
 			TossClientCubes( ent );

```

### `openarena-gamecode`  — sha256 `b66cbf78e6cd...`, 59228 bytes

_Diff stat: +1119 / -377 lines_

_(full diff is 60642 bytes — see files directly)_
