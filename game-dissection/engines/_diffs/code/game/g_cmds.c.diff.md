# Diff: `code/game/g_cmds.c`
**Canonical:** `wolfcamql-src` (sha256 `4c023b1ed9fd...`, 52670 bytes)

## Variants

### `quake3-source`  — sha256 `52fa4d7f279f...`, 44395 bytes

_Diff stat: +121 / -422 lines_

_(full diff is 27583 bytes — see files directly)_

### `ioquake3`  — sha256 `58bf00cb9175...`, 47901 bytes

_Diff stat: +27 / -207 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_cmds.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_cmds.c	2026-04-16 20:02:21.543355100 +0100
@@ -72,27 +72,16 @@
 		perfect = ( cl->ps.persistant[PERS_RANK] == 0 && cl->ps.persistant[PERS_KILLED] == 0 ) ? 1 : 0;
 
 		Com_sprintf (entry, sizeof(entry),
-			" %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i",
-					 level.sortedClients[i],
-					 cl->ps.persistant[PERS_SCORE],
-					 g_debugPingValue.integer > 0 ? g_debugPingValue.integer : ping,
-					 (level.time - cl->pers.enterTime)/60000,
-					 scoreFlags, g_entities[level.sortedClients[i]].s.powerups,
-					 accuracy,
-					 cl->ps.persistant[PERS_IMPRESSIVE_COUNT],
-					 cl->ps.persistant[PERS_EXCELLENT_COUNT],
-					 cl->ps.persistant[PERS_GAUNTLET_FRAG_COUNT],
-					 cl->ps.persistant[PERS_DEFEND_COUNT],
-					 cl->ps.persistant[PERS_ASSIST_COUNT],
-					 perfect,
-					 cl->ps.persistant[PERS_CAPTURES],
-					 // new in ql
-					 cl->ps.pm_type == PM_NORMAL,  //0,  //FIXME alive
-					 0,  //FIXME frags
-					 0,  //FIXME deaths  no: self->client->ps.persistant[PERS_KILLED]
-					 WP_MACHINEGUN  //FIXME bestWeapon
-
-					 );
+			" %i %i %i %i %i %i %i %i %i %i %i %i %i %i", level.sortedClients[i],
+			cl->ps.persistant[PERS_SCORE], ping, (level.time - cl->pers.enterTime)/60000,
+			scoreFlags, g_entities[level.sortedClients[i]].s.powerups, accuracy, 
+			cl->ps.persistant[PERS_IMPRESSIVE_COUNT],
+			cl->ps.persistant[PERS_EXCELLENT_COUNT],
+			cl->ps.persistant[PERS_GAUNTLET_FRAG_COUNT], 
+			cl->ps.persistant[PERS_DEFEND_COUNT], 
+			cl->ps.persistant[PERS_ASSIST_COUNT], 
+			perfect,
+			cl->ps.persistant[PERS_CAPTURES]);
 		j = strlen(entry);
 		if (stringlength + j >= sizeof(string))
 			break;
@@ -117,28 +106,7 @@
 	DeathmatchScoreboardMessage( ent );
 }
 
-void DuelScores (gentity_t *ent)
-{
-	int i;
-	char buf[MAX_STRING_CHARS];
-
-	//FIXME just testing ping
-
-	buf[0] = '\0';
 
-	for (i = 0;  i < 2;  i++) {
-		Q_strcat(buf, sizeof(buf), va("%i ", g_debugPingValue.integer));
-		//FIXME
-		//Com_Printf("buf '%s'\n", buf);
-	}
-
-	trap_SendServerCommand(ent-g_entities, va("dscores %s", buf));
-}
-
-void Cmd_DuelScores_f (gentity_t *ent)
-{
-	DuelScores(ent);
-}
 
 /*
 ==================
@@ -197,9 +165,9 @@
 ==================
 */
 qboolean StringIsInteger( const char * s ) {
-	int                     i;
-	int                     len;
-	qboolean        foundDigit;
+	int			i;
+	int			len;
+	qboolean	foundDigit;
 
 	len = strlen( s );
 	foundDigit = qfalse;
@@ -454,7 +422,7 @@
 	if(!ent->client->pers.localClient)
 	{
 		trap_SendServerCommand(ent-g_entities,
-							   "print \"The levelshot command must be executed by a local client\n\"");
+			"print \"The levelshot command must be executed by a local client\n\"");
 		return;
 	}
 
@@ -464,7 +432,7 @@
 	// doesn't work in single player
 	if(g_gametype.integer == GT_SINGLE_PLAYER)
 	{
-		trap_SendServerCommand(ent-g_entities, 
+		trap_SendServerCommand(ent-g_entities,
 			"print \"Must not be in singleplayer mode for levelshot\n\"" );
 		return;
 	}
@@ -893,8 +861,8 @@
 		return;
 	}
 
-	trap_SendServerCommand( other-g_entities, va("%s \"%02d %s%c%c%s\"",
-		mode == SAY_TEAM ? "tchat" : "chat", ent->client->ps.clientNum,
+	trap_SendServerCommand( other-g_entities, va("%s \"%s%c%c%s\"", 
+		mode == SAY_TEAM ? "tchat" : "chat",
 		name, Q_COLOR_ESCAPE, color, message));
 }
 
@@ -1256,10 +1224,10 @@
 static const int numgc_orders = ARRAY_LEN( gc_orders );
 
 void Cmd_GameCommand_f( gentity_t *ent ) {
-	int                     targetNum;
-	gentity_t       *target;
-	int		order;
-	char            arg[MAX_TOKEN_CHARS];
+	int			targetNum;
+	gentity_t	*target;
+	int			order;
+	char		arg[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() != 3 ) {
 		trap_SendServerCommand( ent-g_entities, va( "print \"Usage: gc <player id> <order 0-%d>\n\"", numgc_orders - 1 ) );
@@ -1378,7 +1346,7 @@
 	if ( level.voteExecuteTime ) {
 		// don't start a vote when map change or restart is in progress
 		if ( !Q_stricmpn( level.voteString, "map", 3 )
-			 || !Q_stricmpn( level.voteString, "nextmap", 7 ) ) {
+			|| !Q_stricmpn( level.voteString, "nextmap", 7 ) ) {
 			trap_SendServerCommand( ent-g_entities, "print \"Vote after map change.\n\"" );
 			return;
 		}
@@ -1543,11 +1511,11 @@
 	// check for command separators in arg2
 	for( c = arg2; *c; ++c) {
 		switch(*c) {
-		case '\n':
-		case '\r':
-		case ';':
-			trap_SendServerCommand( ent-g_entities, "print \"Invalid vote string.\n\"" );
-			return;
+			case '\n':
+			case '\r':
+			case ';':
+				trap_SendServerCommand( ent-g_entities, "print \"Invalid vote string.\n\"" );
+				return;
 			break;
 		}
 	}
@@ -1709,29 +1677,6 @@
 	TeleportPlayer( ent, origin, angles );
 }
 
-void Cmd_SetView_f( gentity_t *ent ) {
-	vec3_t		angles;
-	char		buffer[MAX_TOKEN_CHARS];
-	int			i;
-
-	if ( !g_cheats.integer ) {
-		trap_SendServerCommand( ent-g_entities, "print \"Cheats are not enabled on this server.\n\"");
-		return;
-	}
-	if ( trap_Argc() != 4 ) {
-		trap_SendServerCommand( ent-g_entities, "print \"usage: view yaw pitch roll\n\"");
-		return;
-	}
-
-	VectorClear( angles );
-	for ( i = 0 ; i < 3 ; i++ ) {
-		trap_Argv( i + 1, buffer, sizeof( buffer ) );
-		angles[i] = atof( buffer );
-	}
-
-	SetClientViewAngle(ent, angles);
-}
-
 
 
 /*
@@ -1756,117 +1701,6 @@
 */
 }
 
-static void Cmd_Kami_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-		trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-		return;
-	}
-
-	G_StartKamikaze(ent);
-}
-
-static void Cmd_ServerSound_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-
-	trap_Argv(1, level.serverSound, sizeof(level.serverSound));
-	VectorCopy(ent->s.pos.trBase, level.serverSoundOrigin);
-	level.serverSoundEnt = ent;
-}
-
-static void Cmd_Juiced_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-
-	if (1) {  //( player->client->invulnerabilityTime > level.time ) {
-		//G_Damage( player, mine->parent, mine->parent, vec3_origin, mine->s.origin, 1000, DAMAGE_NO_KNOCKBACK, MOD_JUICED );
-		//player->client->invulnerabilityTime = 0;
-		//G_TempEntity( player->client->ps.origin, EV_JUICED );
-		G_TempEntity( ent->s.pos.trBase, EV_JUICED );
-	}
-
-}
-
-static void Cmd_Spawn_f (gentity_t *ent)
-{
-	gentity_t *s;
-	gitem_t *item;
-	vec3_t origin;
-	vec3_t forward;
-	char name[MAX_STRING_CHARS];
-	char valBuffer[128];
-	float f;
-	trace_t trace;
-
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-	if (trap_Argc() < 2) {
-		trap_SendServerCommand(ent-g_entities, "print \"usage: spawn <item classname> [forward amount]\n\"");
-		return;
-	}
-
-	if (trap_Argc() > 2) {
-		trap_Argv(2, valBuffer, sizeof(valBuffer));
-		f = atof(valBuffer);
-	} else {
-		f = 100;
-	}
-
-	trap_Argv(1, name, sizeof(name));
-
-	s = G_Spawn();
-
-	AngleVectors(ent->s.apos.trBase, forward, NULL, NULL);
-	VectorNormalize(forward);
-	VectorCopy(ent->s.pos.trBase, origin);
-	VectorMA(origin, f, forward, origin);
-
-	memset(&trace, 0, sizeof(trace));
-	trap_Trace(&trace, ent->s.pos.trBase, NULL, NULL, origin, ent - g_entities, MASK_SOLID);
-	//VectorCopy(origin, s->s.pos.trBase);
-	//VectorCopy(origin, s->r.currentOrigin);
-	//VectorCopy(origin, s->s.origin);
-	VectorCopy(trace.endpos, s->s.origin);
-
-	item = BG_FindItem (name);
-	if (item) {
-		s->classname = item->classname;
-		G_SpawnItem(s, item);
-		FinishSpawningItem(s);
-		return;
-	}
-
-#if 0
-	// check item spawn functions
-	for ( item=bg_itemlist+1 ; item->classname ; item++ ) {
-		//if ( !strcmp(item->classname, name) ) {
-			s->classname = item->classname;
-
-			G_SpawnItem(s, item);
-			FinishSpawningItem(s);
-			//memset( &trace, 0, sizeof( trace ) );
-			//Touch_Item (it_ent, ent, &trace);
-			//if (it_ent->inuse) {
-			//	G_FreeEntity( it_ent );
-			//}
-
-			return;
-		}
-	}
-#endif
-
-	trap_SendServerCommand(ent - g_entities, "print \"couldn't find item\n\"");
-}
-
 /*
 =================
 ClientCommand
@@ -1938,10 +1772,6 @@
 		Cmd_Score_f (ent);
 		return;
 	}
-	if (Q_stricmp(cmd, "dscores") == 0) {
-		Cmd_DuelScores_f(ent);
-		return;
-	}
 
 	// ignore all other commands when at intermission
 	if (level.intermissiontime) {
@@ -1985,18 +1815,8 @@
 		Cmd_GameCommand_f( ent );
 	else if (Q_stricmp (cmd, "setviewpos") == 0)
 		Cmd_SetViewpos_f( ent );
-	else if (Q_stricmp (cmd, "view") == 0)
-		Cmd_SetView_f (ent);
 	else if (Q_stricmp (cmd, "stats") == 0)
 		Cmd_Stats_f( ent );
-	else if (Q_stricmp(cmd, "kami") == 0)
-		Cmd_Kami_f(ent);
-	else if (Q_stricmp(cmd, "serversound") == 0)
-		Cmd_ServerSound_f(ent);
-	else if (Q_stricmp(cmd, "juiced") == 0)
-		Cmd_Juiced_f(ent);
-	else if (Q_stricmp(cmd, "spawn") == 0)
-		Cmd_Spawn_f(ent);
 	else
 		trap_SendServerCommand( clientNum, va("print \"unknown cmd %s\n\"", cmd ) );
 }

```

### `openarena-engine`  — sha256 `f49f98d0b34d...`, 45600 bytes

_Diff stat: +58 / -313 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_cmds.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_cmds.c	2026-04-16 22:48:25.746535800 +0100
@@ -34,17 +34,12 @@
 */
 void DeathmatchScoreboardMessage( gentity_t *ent ) {
 	char		entry[1024];
-	char		string[1000];
+	char		string[1400];
 	int			stringlength;
 	int			i, j;
 	gclient_t	*cl;
 	int			numSorted, scoreFlags, accuracy, perfect;
 
-	// don't send scores to bots, they don't parse it
-	if ( ent->r.svFlags & SVF_BOT ) {
-		return;
-	}
-
 	// send the latest information on all clients
 	string[0] = 0;
 	stringlength = 0;
@@ -72,27 +67,16 @@
 		perfect = ( cl->ps.persistant[PERS_RANK] == 0 && cl->ps.persistant[PERS_KILLED] == 0 ) ? 1 : 0;
 
 		Com_sprintf (entry, sizeof(entry),
-			" %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i",
-					 level.sortedClients[i],
-					 cl->ps.persistant[PERS_SCORE],
-					 g_debugPingValue.integer > 0 ? g_debugPingValue.integer : ping,
-					 (level.time - cl->pers.enterTime)/60000,
-					 scoreFlags, g_entities[level.sortedClients[i]].s.powerups,
-					 accuracy,
-					 cl->ps.persistant[PERS_IMPRESSIVE_COUNT],
-					 cl->ps.persistant[PERS_EXCELLENT_COUNT],
-					 cl->ps.persistant[PERS_GAUNTLET_FRAG_COUNT],
-					 cl->ps.persistant[PERS_DEFEND_COUNT],
-					 cl->ps.persistant[PERS_ASSIST_COUNT],
-					 perfect,
-					 cl->ps.persistant[PERS_CAPTURES],
-					 // new in ql
-					 cl->ps.pm_type == PM_NORMAL,  //0,  //FIXME alive
-					 0,  //FIXME frags
-					 0,  //FIXME deaths  no: self->client->ps.persistant[PERS_KILLED]
-					 WP_MACHINEGUN  //FIXME bestWeapon
-
-					 );
+			" %i %i %i %i %i %i %i %i %i %i %i %i %i %i", level.sortedClients[i],
+			cl->ps.persistant[PERS_SCORE], ping, (level.time - cl->pers.enterTime)/60000,
+			scoreFlags, g_entities[level.sortedClients[i]].s.powerups, accuracy, 
+			cl->ps.persistant[PERS_IMPRESSIVE_COUNT],
+			cl->ps.persistant[PERS_EXCELLENT_COUNT],
+			cl->ps.persistant[PERS_GAUNTLET_FRAG_COUNT], 
+			cl->ps.persistant[PERS_DEFEND_COUNT], 
+			cl->ps.persistant[PERS_ASSIST_COUNT], 
+			perfect,
+			cl->ps.persistant[PERS_CAPTURES]);
 		j = strlen(entry);
 		if (stringlength + j >= sizeof(string))
 			break;
@@ -117,28 +101,7 @@
 	DeathmatchScoreboardMessage( ent );
 }
 
-void DuelScores (gentity_t *ent)
-{
-	int i;
-	char buf[MAX_STRING_CHARS];
-
-	//FIXME just testing ping
-
-	buf[0] = '\0';
 
-	for (i = 0;  i < 2;  i++) {
-		Q_strcat(buf, sizeof(buf), va("%i ", g_debugPingValue.integer));
-		//FIXME
-		//Com_Printf("buf '%s'\n", buf);
-	}
-
-	trap_SendServerCommand(ent-g_entities, va("dscores %s", buf));
-}
-
-void Cmd_DuelScores_f (gentity_t *ent)
-{
-	DuelScores(ent);
-}
 
 /*
 ==================
@@ -197,9 +160,9 @@
 ==================
 */
 qboolean StringIsInteger( const char * s ) {
-	int                     i;
-	int                     len;
-	qboolean        foundDigit;
+	int			i;
+	int			len;
+	qboolean	foundDigit;
 
 	len = strlen( s );
 	foundDigit = qfalse;
@@ -224,35 +187,31 @@
 Returns -1 if invalid
 ==================
 */
-int ClientNumberFromString( gentity_t *to, char *s, qboolean checkNums, qboolean checkNames ) {
+int ClientNumberFromString( gentity_t *to, char *s ) {
 	gclient_t	*cl;
 	int			idnum;
 	char		cleanName[MAX_STRING_CHARS];
 
-	if ( checkNums ) {
-		// numeric values could be slot numbers
-		if ( StringIsInteger( s ) ) {
-			idnum = atoi( s );
-			if ( idnum >= 0 && idnum < level.maxclients ) {
-				cl = &level.clients[idnum];
-				if ( cl->pers.connected == CON_CONNECTED ) {
-					return idnum;
-				}
+	// numeric values could be slot numbers
+	if ( StringIsInteger( s ) ) {
+		idnum = atoi( s );
+		if ( idnum >= 0 && idnum < level.maxclients ) {
+			cl = &level.clients[idnum];
+			if ( cl->pers.connected == CON_CONNECTED ) {
+				return idnum;
 			}
 		}
 	}
 
-	if ( checkNames ) {
-		// check for a name match
-		for ( idnum=0,cl=level.clients ; idnum < level.maxclients ; idnum++,cl++ ) {
-			if ( cl->pers.connected != CON_CONNECTED ) {
-				continue;
-			}
-			Q_strncpyz(cleanName, cl->pers.netname, sizeof(cleanName));
-			Q_CleanStr(cleanName);
-			if ( !Q_stricmp( cleanName, s ) ) {
-				return idnum;
-			}
+	// check for a name match
+	for ( idnum=0,cl=level.clients ; idnum < level.maxclients ; idnum++,cl++ ) {
+		if ( cl->pers.connected != CON_CONNECTED ) {
+			continue;
+		}
+		Q_strncpyz(cleanName, cl->pers.netname, sizeof(cleanName));
+		Q_CleanStr(cleanName);
+		if ( !Q_stricmp( cleanName, s ) ) {
+			return idnum;
 		}
 	}
 
@@ -454,7 +413,7 @@
 	if(!ent->client->pers.localClient)
 	{
 		trap_SendServerCommand(ent-g_entities,
-							   "print \"The levelshot command must be executed by a local client\n\"");
+			"print \"The levelshot command must be executed by a local client\n\"");
 		return;
 	}
 
@@ -464,7 +423,7 @@
 	// doesn't work in single player
 	if(g_gametype.integer == GT_SINGLE_PLAYER)
 	{
-		trap_SendServerCommand(ent-g_entities, 
+		trap_SendServerCommand(ent-g_entities,
 			"print \"Must not be in singleplayer mode for levelshot\n\"" );
 		return;
 	}
@@ -517,7 +476,7 @@
 
 /*
 =================
-BroadcastTeamChange
+BroadCastTeamChange
 
 Let everyone know about a team change
 =================
@@ -544,7 +503,7 @@
 SetTeam
 =================
 */
-void SetTeam( gentity_t *ent, const char *s ) {
+void SetTeam( gentity_t *ent, char *s ) {
 	int					team, oldTeam;
 	gclient_t			*client;
 	int					clientNum;
@@ -586,7 +545,7 @@
 			team = PickTeam( clientNum );
 		}
 
-		if ( g_teamForceBalance.integer && !client->pers.localClient && !( ent->r.svFlags & SVF_BOT ) ) {
+		if ( g_teamForceBalance.integer  ) {
 			int		counts[TEAM_NUM_TEAMS];
 
 			counts[TEAM_BLUE] = TeamCount( clientNum, TEAM_BLUE );
@@ -633,8 +592,8 @@
 	// execute the team change
 	//
 
-	// if the player was dead leave the body, but only if they're actually in game
-	if ( client->ps.stats[STAT_HEALTH] <= 0 && client->pers.connected == CON_CONNECTED ) {
+	// if the player was dead leave the body
+	if ( client->ps.stats[STAT_HEALTH] <= 0 ) {
 		CopyToBodyQue(ent);
 	}
 
@@ -669,16 +628,11 @@
 		CheckTeamLeader( oldTeam );
 	}
 
-	// get and distribute relevant parameters
-	ClientUserinfoChanged( clientNum );
-
-	// client hasn't spawned yet, they sent an early team command, teampref userinfo, or g_teamAutoJoin is enabled
-	if ( client->pers.connected != CON_CONNECTED ) {
-		return;
-	}
-
 	BroadcastTeamChange( client, oldTeam );
 
+	// get and distribute relevent paramters
+	ClientUserinfoChanged( clientNum );
+
 	ClientBegin( clientNum );
 }
 
@@ -697,13 +651,6 @@
 	ent->client->ps.pm_flags &= ~PMF_FOLLOW;
 	ent->r.svFlags &= ~SVF_BOT;
 	ent->client->ps.clientNum = ent - g_entities;
-
-	SetClientViewAngle( ent, ent->client->ps.viewangles );
-
-	// don't use dead view angles
-	if ( ent->client->ps.stats[STAT_HEALTH] <= 0 ) {
-		ent->client->ps.stats[STAT_HEALTH] = 1;
-	}
 }
 
 /*
@@ -770,7 +717,7 @@
 	}
 
 	trap_Argv( 1, arg, sizeof( arg ) );
-	i = ClientNumberFromString( ent, arg, qtrue, qtrue );
+	i = ClientNumberFromString( ent, arg );
 	if ( i == -1 ) {
 		return;
 	}
@@ -893,8 +840,8 @@
 		return;
 	}
 
-	trap_SendServerCommand( other-g_entities, va("%s \"%02d %s%c%c%s\"",
-		mode == SAY_TEAM ? "tchat" : "chat", ent->client->ps.clientNum,
+	trap_SendServerCommand( other-g_entities, va("%s \"%s%c%c%s\"", 
+		mode == SAY_TEAM ? "tchat" : "chat",
 		name, Q_COLOR_ESCAPE, color, message));
 }
 
@@ -953,23 +900,13 @@
 		G_Printf( "%s%s\n", name, text);
 	}
 
-	// send it to all the appropriate clients
+	// send it to all the apropriate clients
 	for (j = 0; j < level.maxclients; j++) {
 		other = &g_entities[j];
 		G_SayTo( ent, other, mode, color, name, text );
 	}
 }
 
-static void SanitizeChatText( char *text ) {
-	int i;
-
-	for ( i = 0; text[i]; i++ ) {
-		if ( text[i] == '\n' || text[i] == '\r' ) {
-			text[i] = ' ';
-		}
-	}
-}
-
 
 /*
 ==================
@@ -992,8 +929,6 @@
 		p = ConcatArgs( 1 );
 	}
 
-	SanitizeChatText( p );
-
 	G_Say( ent, NULL, mode, p );
 }
 
@@ -1014,7 +949,7 @@
 	}
 
 	trap_Argv( 1, arg, sizeof( arg ) );
-	targetNum = ClientNumberFromString( ent, arg, qtrue, qtrue );
+	targetNum = ClientNumberFromString( ent, arg );
 	if ( targetNum == -1 ) {
 		return;
 	}
@@ -1026,8 +961,6 @@
 
 	p = ConcatArgs( 2 );
 
-	SanitizeChatText( p );
-
 	G_LogPrintf( "tell: %s to %s: %s\n", ent->client->pers.netname, target->client->pers.netname, p );
 	G_Say( ent, target, SAY_TELL, p );
 	// don't tell to the player self if it was already directed to this player
@@ -1094,7 +1027,7 @@
 		G_Printf( "voice: %s %s\n", ent->client->pers.netname, id);
 	}
 
-	// send it to all the appropriate clients
+	// send it to all the apropriate clients
 	for (j = 0; j < level.maxclients; j++) {
 		other = &g_entities[j];
 		G_VoiceTo( ent, other, mode, id, voiceonly );
@@ -1122,8 +1055,6 @@
 		p = ConcatArgs( 1 );
 	}
 
-	SanitizeChatText( p );
-
 	G_Voice( ent, NULL, mode, p, voiceonly );
 }
 
@@ -1144,7 +1075,7 @@
 	}
 
 	trap_Argv( 1, arg, sizeof( arg ) );
-	targetNum = ClientNumberFromString( ent, arg, qtrue, qtrue );
+	targetNum = ClientNumberFromString( ent, arg );
 	if ( targetNum == -1 ) {
 		return;
 	}
@@ -1156,8 +1087,6 @@
 
 	id = ConcatArgs( 2 );
 
-	SanitizeChatText( id );
-
 	G_LogPrintf( "vtell: %s to %s: %s\n", ent->client->pers.netname, target->client->pers.netname, id );
 	G_Voice( ent, target, SAY_TELL, id, voiceonly );
 	// don't tell to the player self if it was already directed to this player
@@ -1256,10 +1185,10 @@
 static const int numgc_orders = ARRAY_LEN( gc_orders );
 
 void Cmd_GameCommand_f( gentity_t *ent ) {
-	int                     targetNum;
-	gentity_t       *target;
-	int		order;
-	char            arg[MAX_TOKEN_CHARS];
+	int			targetNum;
+	gentity_t	*target;
+	int			order;
+	char		arg[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() != 3 ) {
 		trap_SendServerCommand( ent-g_entities, va( "print \"Usage: gc <player id> <order 0-%d>\n\"", numgc_orders - 1 ) );
@@ -1275,7 +1204,7 @@
 	}
 
 	trap_Argv( 1, arg, sizeof( arg ) );
-	targetNum = ClientNumberFromString( ent, arg, qtrue, qtrue );
+	targetNum = ClientNumberFromString( ent, arg );
 	if ( targetNum == -1 ) {
 		return;
 	}
@@ -1376,13 +1305,6 @@
 
 	// if there is still a vote to be executed
 	if ( level.voteExecuteTime ) {
-		// don't start a vote when map change or restart is in progress
-		if ( !Q_stricmpn( level.voteString, "map", 3 )
-			 || !Q_stricmpn( level.voteString, "nextmap", 7 ) ) {
-			trap_SendServerCommand( ent-g_entities, "print \"Vote after map change.\n\"" );
-			return;
-		}
-
 		level.voteExecuteTime = 0;
 		trap_SendConsoleCommand( EXEC_APPEND, va("%s\n", level.voteString ) );
 	}
@@ -1419,19 +1341,6 @@
 		}
 		Com_sprintf( level.voteString, sizeof( level.voteString ), "vstr nextmap");
 		Com_sprintf( level.voteDisplayString, sizeof( level.voteDisplayString ), "%s", level.voteString );
-	} else if ( !Q_stricmp( arg1, "clientkick" ) || !Q_stricmp( arg1, "kick" ) ) {
-		i = ClientNumberFromString( ent, arg2, !Q_stricmp( arg1, "clientkick" ), !Q_stricmp( arg1, "kick" ) );
-		if ( i == -1 ) {
-			return;
-		}
-
-		if ( level.clients[i].pers.localClient ) {
-			trap_SendServerCommand( ent - g_entities, "print \"Cannot kick host player.\n\"" );
-			return;
-		}
-
-		Com_sprintf( level.voteString, sizeof( level.voteString ), "clientkick %d", i );
-		Com_sprintf( level.voteDisplayString, sizeof( level.voteDisplayString ), "kick %s", level.clients[i].pers.netname );
 	} else {
 		Com_sprintf( level.voteString, sizeof( level.voteString ), "%s \"%s\"", arg1, arg2 );
 		Com_sprintf( level.voteDisplayString, sizeof( level.voteDisplayString ), "%s", level.voteString );
@@ -1439,7 +1348,7 @@
 
 	trap_SendServerCommand( -1, va("print \"%s called a vote.\n\"", ent->client->pers.netname ) );
 
-	// start the voting, the caller automatically votes yes
+	// start the voting, the caller autoamtically votes yes
 	level.voteTime = level.time;
 	level.voteYes = 1;
 	level.voteNo = 0;
@@ -1500,7 +1409,6 @@
 ==================
 */
 void Cmd_CallTeamVote_f( gentity_t *ent ) {
-	char*	c;
 	int		i, team, cs_offset;
 	char	arg1[MAX_STRING_TOKENS];
 	char	arg2[MAX_STRING_TOKENS];
@@ -1540,16 +1448,9 @@
 		trap_Argv( i, &arg2[strlen(arg2)], sizeof( arg2 ) - strlen(arg2) );
 	}
 
-	// check for command separators in arg2
-	for( c = arg2; *c; ++c) {
-		switch(*c) {
-		case '\n':
-		case '\r':
-		case ';':
-			trap_SendServerCommand( ent-g_entities, "print \"Invalid vote string.\n\"" );
-			return;
-			break;
-		}
+	if( strchr( arg1, ';' ) || strchr( arg2, ';' ) ) {
+		trap_SendServerCommand( ent-g_entities, "print \"Invalid vote string.\n\"" );
+		return;
 	}
 
 	if ( !Q_stricmp( arg1, "leader" ) ) {
@@ -1612,7 +1513,7 @@
 			trap_SendServerCommand( i, va("print \"%s called a team vote.\n\"", ent->client->pers.netname ) );
 	}
 
-	// start the voting, the caller automatically votes yes
+	// start the voting, the caller autoamtically votes yes
 	level.teamVoteTime[cs_offset] = level.time;
 	level.teamVoteYes[cs_offset] = 1;
 	level.teamVoteNo[cs_offset] = 0;
@@ -1709,29 +1610,6 @@
 	TeleportPlayer( ent, origin, angles );
 }
 
-void Cmd_SetView_f( gentity_t *ent ) {
-	vec3_t		angles;
-	char		buffer[MAX_TOKEN_CHARS];
-	int			i;
-
-	if ( !g_cheats.integer ) {
-		trap_SendServerCommand( ent-g_entities, "print \"Cheats are not enabled on this server.\n\"");
-		return;
-	}
-	if ( trap_Argc() != 4 ) {
-		trap_SendServerCommand( ent-g_entities, "print \"usage: view yaw pitch roll\n\"");
-		return;
-	}
-
-	VectorClear( angles );
-	for ( i = 0 ; i < 3 ; i++ ) {
-		trap_Argv( i + 1, buffer, sizeof( buffer ) );
-		angles[i] = atof( buffer );
-	}
-
-	SetClientViewAngle(ent, angles);
-}
-
 
 
 /*
@@ -1756,117 +1634,6 @@
 */
 }
 
-static void Cmd_Kami_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-		trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-		return;
-	}
-
-	G_StartKamikaze(ent);
-}
-
-static void Cmd_ServerSound_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-
-	trap_Argv(1, level.serverSound, sizeof(level.serverSound));
-	VectorCopy(ent->s.pos.trBase, level.serverSoundOrigin);
-	level.serverSoundEnt = ent;
-}
-
-static void Cmd_Juiced_f (gentity_t *ent)
-{
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-
-	if (1) {  //( player->client->invulnerabilityTime > level.time ) {
-		//G_Damage( player, mine->parent, mine->parent, vec3_origin, mine->s.origin, 1000, DAMAGE_NO_KNOCKBACK, MOD_JUICED );
-		//player->client->invulnerabilityTime = 0;
-		//G_TempEntity( player->client->ps.origin, EV_JUICED );
-		G_TempEntity( ent->s.pos.trBase, EV_JUICED );
-	}
-
-}
-
-static void Cmd_Spawn_f (gentity_t *ent)
-{
-	gentity_t *s;
-	gitem_t *item;
-	vec3_t origin;
-	vec3_t forward;
-	char name[MAX_STRING_CHARS];
-	char valBuffer[128];
-	float f;
-	trace_t trace;
-
-	if (!g_cheats.integer) {
-        trap_SendServerCommand(ent-g_entities, va("print \"Cheats are not enabled on this server.\n\""));
-        return;
-    }
-	if (trap_Argc() < 2) {
-		trap_SendServerCommand(ent-g_entities, "print \"usage: spawn <item classname> [forward amount]\n\"");
-		return;
-	}
-
-	if (trap_Argc() > 2) {
-		trap_Argv(2, valBuffer, sizeof(valBuffer));
-		f = atof(valBuffer);
-	} else {
-		f = 100;
-	}
-
-	trap_Argv(1, name, sizeof(name));
-
-	s = G_Spawn();
-
-	AngleVectors(ent->s.apos.trBase, forward, NULL, NULL);
-	VectorNormalize(forward);
-	VectorCopy(ent->s.pos.trBase, origin);
-	VectorMA(origin, f, forward, origin);
-
-	memset(&trace, 0, sizeof(trace));
-	trap_Trace(&trace, ent->s.pos.trBase, NULL, NULL, origin, ent - g_entities, MASK_SOLID);
-	//VectorCopy(origin, s->s.pos.trBase);
-	//VectorCopy(origin, s->r.currentOrigin);
-	//VectorCopy(origin, s->s.origin);
-	VectorCopy(trace.endpos, s->s.origin);
-
-	item = BG_FindItem (name);
-	if (item) {
-		s->classname = item->classname;
-		G_SpawnItem(s, item);
-		FinishSpawningItem(s);
-		return;
-	}
-
-#if 0
-	// check item spawn functions
-	for ( item=bg_itemlist+1 ; item->classname ; item++ ) {
-		//if ( !strcmp(item->classname, name) ) {
-			s->classname = item->classname;
-
-			G_SpawnItem(s, item);
-			FinishSpawningItem(s);
-			//memset( &trace, 0, sizeof( trace ) );
-			//Touch_Item (it_ent, ent, &trace);
-			//if (it_ent->inuse) {
-			//	G_FreeEntity( it_ent );
-			//}
-
-			return;
-		}
-	}
-#endif
-
-	trap_SendServerCommand(ent - g_entities, "print \"couldn't find item\n\"");
-}
-
 /*
 =================
 ClientCommand
@@ -1878,14 +1645,6 @@
 
 	ent = g_entities + clientNum;
 	if (!ent->client || ent->client->pers.connected != CON_CONNECTED) {
-		if (ent->client && ent->client->pers.localClient) {
-			// Handle early team command sent by UI when starting a local
-			// team play game.
-			trap_Argv( 0, cmd, sizeof( cmd ) );
-			if (Q_stricmp (cmd, "team") == 0) {
-				Cmd_Team_f (ent);
-			}
-		}
 		return;		// not fully in game yet
 	}
 
@@ -1938,10 +1697,6 @@
 		Cmd_Score_f (ent);
 		return;
 	}
-	if (Q_stricmp(cmd, "dscores") == 0) {
-		Cmd_DuelScores_f(ent);
-		return;
-	}
 
 	// ignore all other commands when at intermission
 	if (level.intermissiontime) {
@@ -1985,18 +1740,8 @@
 		Cmd_GameCommand_f( ent );
 	else if (Q_stricmp (cmd, "setviewpos") == 0)
 		Cmd_SetViewpos_f( ent );
-	else if (Q_stricmp (cmd, "view") == 0)
-		Cmd_SetView_f (ent);
 	else if (Q_stricmp (cmd, "stats") == 0)
 		Cmd_Stats_f( ent );
-	else if (Q_stricmp(cmd, "kami") == 0)
-		Cmd_Kami_f(ent);
-	else if (Q_stricmp(cmd, "serversound") == 0)
-		Cmd_ServerSound_f(ent);
-	else if (Q_stricmp(cmd, "juiced") == 0)
-		Cmd_Juiced_f(ent);
-	else if (Q_stricmp(cmd, "spawn") == 0)
-		Cmd_Spawn_f(ent);
 	else
 		trap_SendServerCommand( clientNum, va("print \"unknown cmd %s\n\"", cmd ) );
 }

```

### `openarena-gamecode`  — sha256 `91d41942990a...`, 68432 bytes

_Diff stat: +920 / -517 lines_

_(full diff is 68463 bytes — see files directly)_
