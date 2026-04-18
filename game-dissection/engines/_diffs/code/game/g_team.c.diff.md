# Diff: `code/game/g_team.c`
**Canonical:** `wolfcamql-src` (sha256 `5bdcf3e0272a...`, 41013 bytes)

## Variants

### `quake3-source`  — sha256 `58005485a306...`, 40989 bytes

_Diff stat: +81 / -90 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_team.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_team.c	2026-04-16 20:02:19.911076800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -45,16 +45,20 @@
 void Team_InitGame( void ) {
 	memset(&teamgame, 0, sizeof teamgame);
 
-	if (g_gametype.integer == GT_CTF) {
-		teamgame.redStatus = -1; // Invalid to force update
+	switch( g_gametype.integer ) {
+	case GT_CTF:
+		teamgame.redStatus = teamgame.blueStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_RED, FLAG_ATBASE );
-		 teamgame.blueStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_BLUE, FLAG_ATBASE );
+		break;
 #ifdef MISSIONPACK
-	} else if (g_gametype.integer == GT_1FCTF) {
+	case GT_1FCTF:
 		teamgame.flagStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_FREE, FLAG_ATBASE );
+		break;
 #endif
+	default:
+		break;
 	}
 }
 
@@ -76,6 +80,16 @@
 	return "FREE";
 }
 
+const char *OtherTeamName(int team) {
+	if (team==TEAM_RED)
+		return "BLUE";
+	else if (team==TEAM_BLUE)
+		return "RED";
+	else if (team==TEAM_SPECTATOR)
+		return "SPECTATOR";
+	return "FREE";
+}
+
 const char *TeamColorString(int team) {
 	if (team==TEAM_RED)
 		return S_COLOR_RED;
@@ -87,13 +101,13 @@
 }
 
 // NULL for everyone
-static Q_PRINTF_FUNC(2, 3)  void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
+void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
 	char		msg[1024];
 	va_list		argptr;
 	char		*p;
 	
 	va_start (argptr,fmt);
-	if (Q_vsnprintf (msg, sizeof(msg), fmt, argptr) >= sizeof(msg)) {
+	if (vsprintf (msg, fmt, argptr) > sizeof(msg)) {
 		G_Error ( "PrintMsg overrun" );
 	}
 	va_end (argptr);
@@ -293,12 +307,9 @@
 		enemy_flag_pw = PW_REDFLAG;
 	}
 
-#if 1  //def MPACK
 	if (g_gametype.integer == GT_1FCTF) {
-		flag_pw = PW_NEUTRALFLAG;
 		enemy_flag_pw = PW_NEUTRALFLAG;
 	} 
-#endif
 
 	// did the attacker frag the flag carrier?
 	tokens = 0;
@@ -353,6 +364,25 @@
 		targ->client->pers.teamState.lasthurtcarrier = 0;
 
 		attacker->client->ps.persistant[PERS_DEFEND_COUNT]++;
+		team = attacker->client->sess.sessionTeam;
+		// add the sprite over the player's head
+		attacker->client->ps.eFlags &= ~(EF_AWARD_IMPRESSIVE | EF_AWARD_EXCELLENT | EF_AWARD_GAUNTLET | EF_AWARD_ASSIST | EF_AWARD_DEFEND | EF_AWARD_CAP );
+		attacker->client->ps.eFlags |= EF_AWARD_DEFEND;
+		attacker->client->rewardTime = level.time + REWARD_SPRITE_TIME;
+
+		return;
+	}
+
+	if (targ->client->pers.teamState.lasthurtcarrier &&
+		level.time - targ->client->pers.teamState.lasthurtcarrier < CTF_CARRIER_DANGER_PROTECT_TIMEOUT) {
+		// attacker is on the same team as the skull carrier and
+		AddScore(attacker, targ->r.currentOrigin, CTF_CARRIER_DANGER_PROTECT_BONUS);
+
+		attacker->client->pers.teamState.carrierdefense++;
+		targ->client->pers.teamState.lasthurtcarrier = 0;
+
+		attacker->client->ps.persistant[PERS_DEFEND_COUNT]++;
+		team = attacker->client->sess.sessionTeam;
 		// add the sprite over the player's head
 		attacker->client->ps.eFlags &= ~(EF_AWARD_IMPRESSIVE | EF_AWARD_EXCELLENT | EF_AWARD_GAUNTLET | EF_AWARD_ASSIST | EF_AWARD_DEFEND | EF_AWARD_CAP );
 		attacker->client->ps.eFlags |= EF_AWARD_DEFEND;
@@ -441,7 +471,7 @@
 
 	if (carrier && carrier != attacker) {
 		VectorSubtract(targ->r.currentOrigin, carrier->r.currentOrigin, v1);
-		VectorSubtract(attacker->r.currentOrigin, carrier->r.currentOrigin, v2);
+		VectorSubtract(attacker->r.currentOrigin, carrier->r.currentOrigin, v1);
 
 		if ( ( ( VectorLength(v1) < CTF_ATTACKER_PROTECT_RADIUS &&
 			trap_InPVS(carrier->r.currentOrigin, targ->r.currentOrigin ) ) ||
@@ -482,12 +512,6 @@
 	else
 		flag_pw = PW_REDFLAG;
 
-#if 1  //def MPACK
-	if (g_gametype.integer == GT_1FCTF) {
-		flag_pw = PW_NEUTRALFLAG;
-	}
-#endif
-
 	// flags
 	if (targ->client->ps.powerups[flag_pw] &&
 		targ->client->sess.sessionTeam != attacker->client->sess.sessionTeam)
@@ -692,7 +716,7 @@
 	}
 
 	if ( ent->flags & FL_DROPPED_ITEM ) {
-		// hey, it's not home.  return it by teleporting it back
+		// hey, its not home.  return it by teleporting it back
 		PrintMsg( NULL, "%s" S_COLOR_WHITE " returned the %s flag!\n", 
 			cl->pers.netname, TeamName(team));
 		AddScore(other, ent->r.currentOrigin, CTF_RECOVERY_BONUS);
@@ -745,9 +769,7 @@
 	// Ok, let's do the player loop, hand out the bonuses
 	for (i = 0; i < g_maxclients.integer; i++) {
 		player = &g_entities[i];
-
-		// also make sure we don't award assist bonuses to the flag carrier himself.
-		if (!player->inuse || player == other)
+		if (!player->inuse)
 			continue;
 
 		if (player->client->sess.sessionTeam !=
@@ -755,9 +777,8 @@
 			player->client->pers.teamState.lasthurtcarrier = -5;
 		} else if (player->client->sess.sessionTeam ==
 			cl->sess.sessionTeam) {
-#ifdef MISSIONPACK
-			AddScore(player, ent->r.currentOrigin, CTF_TEAM_BONUS);
-#endif
+			if (player != other)
+				AddScore(player, ent->r.currentOrigin, CTF_TEAM_BONUS);
 			// award extra points for capture assists
 			if (player->client->pers.teamState.lastreturnedflag + 
 				CTF_RETURN_FLAG_ASSIST_TIMEOUT > level.time) {
@@ -770,8 +791,7 @@
 				player->client->ps.eFlags |= EF_AWARD_ASSIST;
 				player->client->rewardTime = level.time + REWARD_SPRITE_TIME;
 
-			}
-			if (player->client->pers.teamState.lastfraggedcarrier + 
+			} else if (player->client->pers.teamState.lastfraggedcarrier + 
 				CTF_FRAG_CARRIER_ASSIST_TIMEOUT > level.time) {
 				AddScore(player, ent->r.currentOrigin, CTF_FRAG_CARRIER_ASSIST_BONUS);
 				other->client->pers.teamState.assists++;
@@ -819,9 +839,9 @@
 		Team_SetFlagStatus( team, FLAG_TAKEN );
 #ifdef MISSIONPACK
 	}
+#endif
 
 	AddScore(other, ent->r.currentOrigin, CTF_FLAG_BONUS);
-#endif
 	cl->pers.teamState.flagsince = level.time;
 	Team_TakeFlagSound( ent, team );
 
@@ -954,7 +974,7 @@
 
 /*
 ================
-SelectRandomTeamSpawnPoint
+SelectRandomDeathmatchSpawnPoint
 
 go to a random point that doesn't telefrag
 ================
@@ -1010,13 +1030,13 @@
 
 ============
 */
-gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles, qboolean isbot ) {
+gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles ) {
 	gentity_t	*spot;
 
 	spot = SelectRandomTeamSpawnPoint ( teamstate, team );
 
 	if (!spot) {
-		return SelectSpawnPoint( vec3_origin, origin, angles, isbot );
+		return SelectSpawnPoint( vec3_origin, origin, angles );
 	}
 
 	VectorCopy (spot->s.origin, origin);
@@ -1051,32 +1071,17 @@
 	int			cnt;
 	int			h, a;
 	int			clients[TEAM_MAXOVERLAY];
-	int team;
 
 	if ( ! ent->client->pers.teamInfo )
 		return;
 
-	// send team info to spectator for team of followed client
-	if (ent->client->sess.sessionTeam == TEAM_SPECTATOR) {
-		if ( ent->client->sess.spectatorState != SPECTATOR_FOLLOW
-			 || ent->client->sess.spectatorClient < 0 ) {
-			return;
-		}
-		team = g_entities[ ent->client->sess.spectatorClient ].client->sess.sessionTeam;
-	} else {
-		team = ent->client->sess.sessionTeam;
-	}
-
-	if (team != TEAM_RED && team != TEAM_BLUE) {
-		return;
-	}
-
 	// figure out what client should be on the display
 	// we are limited to 8, but we want to use the top eight players
 	// but in client order (so they don't keep changing position on the overlay)
 	for (i = 0, cnt = 0; i < g_maxclients.integer && cnt < TEAM_MAXOVERLAY; i++) {
 		player = g_entities + level.sortedClients[i];
-		if (player->inuse && player->client->sess.sessionTeam == team ) {
+		if (player->inuse && player->client->sess.sessionTeam == 
+			ent->client->sess.sessionTeam ) {
 			clients[cnt++] = level.sortedClients[i];
 		}
 	}
@@ -1090,7 +1095,8 @@
 
 	for (i = 0, cnt = 0; i < g_maxclients.integer && cnt < TEAM_MAXOVERLAY; i++) {
 		player = g_entities + i;
-		if (player->inuse && player->client->sess.sessionTeam == team ) {
+		if (player->inuse && player->client->sess.sessionTeam == 
+			ent->client->sess.sessionTeam ) {
 
 			h = player->client->ps.stats[STAT_HEALTH];
 			a = player->client->ps.stats[STAT_ARMOR];
@@ -1103,7 +1109,7 @@
 				i, player->client->pers.teamState.location, h, a, 
 				player->client->ps.weapon, player->s.powerups);
 			j = strlen(entry);
-			if (stringlength + j >= sizeof(string))
+			if (stringlength + j > sizeof(string))
 				break;
 			strcpy (string + stringlength, entry);
 			stringlength += j;
@@ -1131,13 +1137,10 @@
 
 			if (ent->inuse && (ent->client->sess.sessionTeam == TEAM_RED ||	ent->client->sess.sessionTeam == TEAM_BLUE)) {
 				loc = Team_GetLocation( ent );
-				if (loc) {
+				if (loc)
 					ent->client->pers.teamState.location = loc->health;
-					// protocol 91
-					ent->client->ps.location = loc->health;
-				} else {
+				else
 					ent->client->pers.teamState.location = 0;
-				}
 			}
 		}
 
@@ -1148,7 +1151,7 @@
 				continue;
 			}
 
-			if (ent->inuse) {
+			if (ent->inuse && (ent->client->sess.sessionTeam == TEAM_RED ||	ent->client->sess.sessionTeam == TEAM_BLUE)) {
 				TeamplayInfoMessage( ent );
 			}
 		}
@@ -1268,8 +1271,8 @@
 		return;
 	}
 
-	PrintMsg(NULL, "%s" S_COLOR_WHITE " brought in %i %s.\n",
-			 other->client->pers.netname, tokens, ( tokens == 1 ) ? "skull" : "skulls" );
+	PrintMsg(NULL, "%s" S_COLOR_WHITE " brought in %i skull%s.\n",
+					other->client->pers.netname, tokens, tokens ? "s" : "" );
 
 	AddTeamScore(self->s.pos.trBase, other->client->sess.sessionTeam, tokens);
 	Team_ForceGesture(other->client->sess.sessionTeam);
@@ -1301,8 +1304,9 @@
 	AddScore(attacker, self->r.currentOrigin, actualDamage);
 }
 
-// spawn invisible damagable obelisk entity / harvester base trigger.
-gentity_t *SpawnObelisk( vec3_t origin, vec3_t mins, vec3_t maxs, int team ) {
+gentity_t *SpawnObelisk( vec3_t origin, int team, int spawnflags) {
+	trace_t		tr;
+	vec3_t		dest;
 	gentity_t	*ent;
 
 	ent = G_Spawn();
@@ -1311,8 +1315,8 @@
 	VectorCopy( origin, ent->s.pos.trBase );
 	VectorCopy( origin, ent->r.currentOrigin );
 
-	VectorCopy( mins, ent->r.mins );
-	VectorCopy( maxs, ent->r.maxs );
+	VectorSet( ent->r.mins, -15, -15, 0 );
+	VectorSet( ent->r.maxs, 15, 15, 87 );
 
 	ent->s.eType = ET_GENERAL;
 	ent->flags = FL_NO_KNOCKBACK;
@@ -1331,26 +1335,7 @@
 		ent->touch = ObeliskTouch;
 	}
 
-	G_SetOrigin( ent, ent->s.origin );
-
-	ent->spawnflags = team;
-
-	trap_LinkEntity( ent );
-
-	return ent;
-}
-
-// setup entity for team base model / obelisk model.
-void ObeliskInit( gentity_t *ent ) {
-	trace_t tr;
-	vec3_t dest;
-
-	ent->s.eType = ET_TEAM;
-
-	VectorSet( ent->r.mins, -15, -15, 0 );
-	VectorSet( ent->r.maxs, 15, 15, 87 );
-
-	if ( ent->spawnflags & 1 ) {
+	if ( spawnflags & 1 ) {
 		// suspended
 		G_SetOrigin( ent, ent->s.origin );
 	} else {
@@ -1374,6 +1359,12 @@
 			G_SetOrigin( ent, tr.endpos );
 		}
 	}
+
+	ent->spawnflags = team;
+
+	trap_LinkEntity( ent );
+
+	return ent;
 }
 
 /*QUAKED team_redobelisk (1 0 0) (-16 -16 0) (16 16 8)
@@ -1385,16 +1376,16 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_OBELISK ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_RED );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_RED, ent->spawnflags );
 		obelisk->activator = ent;
 		// initial obelisk health value
 		ent->s.modelindex2 = 0xff;
 		ent->s.frame = 0;
 	}
 	if ( g_gametype.integer == GT_HARVESTER ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_RED );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_RED, ent->spawnflags );
 		obelisk->activator = ent;
 	}
 	ent->s.modelindex = TEAM_RED;
@@ -1410,16 +1401,16 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_OBELISK ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_BLUE );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_BLUE, ent->spawnflags );
 		obelisk->activator = ent;
 		// initial obelisk health value
 		ent->s.modelindex2 = 0xff;
 		ent->s.frame = 0;
 	}
 	if ( g_gametype.integer == GT_HARVESTER ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_BLUE );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_BLUE, ent->spawnflags );
 		obelisk->activator = ent;
 	}
 	ent->s.modelindex = TEAM_BLUE;
@@ -1433,10 +1424,10 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_HARVESTER) {
-		neutralObelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_FREE );
-		neutralObelisk->activator = ent;
+		neutralObelisk = SpawnObelisk( ent->s.origin, TEAM_FREE, ent->spawnflags);
+		neutralObelisk->spawnflags = TEAM_FREE;
 	}
 	ent->s.modelindex = TEAM_FREE;
 	trap_LinkEntity(ent);

```

### `ioquake3`  — sha256 `1730f9744af7...`, 40956 bytes

_Diff stat: +16 / -14 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_team.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_team.c	2026-04-16 20:02:21.549421400 +0100
@@ -45,16 +45,21 @@
 void Team_InitGame( void ) {
 	memset(&teamgame, 0, sizeof teamgame);
 
-	if (g_gametype.integer == GT_CTF) {
+	switch( g_gametype.integer ) {
+	case GT_CTF:
 		teamgame.redStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_RED, FLAG_ATBASE );
 		 teamgame.blueStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_BLUE, FLAG_ATBASE );
+		break;
 #ifdef MISSIONPACK
-	} else if (g_gametype.integer == GT_1FCTF) {
+	case GT_1FCTF:
 		teamgame.flagStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_FREE, FLAG_ATBASE );
+		break;
 #endif
+	default:
+		break;
 	}
 }
 
@@ -87,7 +92,7 @@
 }
 
 // NULL for everyone
-static Q_PRINTF_FUNC(2, 3)  void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
+static Q_PRINTF_FUNC(2, 3) void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
 	char		msg[1024];
 	va_list		argptr;
 	char		*p;
@@ -293,7 +298,7 @@
 		enemy_flag_pw = PW_REDFLAG;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (g_gametype.integer == GT_1FCTF) {
 		flag_pw = PW_NEUTRALFLAG;
 		enemy_flag_pw = PW_NEUTRALFLAG;
@@ -482,7 +487,7 @@
 	else
 		flag_pw = PW_REDFLAG;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (g_gametype.integer == GT_1FCTF) {
 		flag_pw = PW_NEUTRALFLAG;
 	}
@@ -770,7 +775,7 @@
 				player->client->ps.eFlags |= EF_AWARD_ASSIST;
 				player->client->rewardTime = level.time + REWARD_SPRITE_TIME;
 
-			}
+			} 
 			if (player->client->pers.teamState.lastfraggedcarrier + 
 				CTF_FRAG_CARRIER_ASSIST_TIMEOUT > level.time) {
 				AddScore(player, ent->r.currentOrigin, CTF_FRAG_CARRIER_ASSIST_BONUS);
@@ -1051,7 +1056,7 @@
 	int			cnt;
 	int			h, a;
 	int			clients[TEAM_MAXOVERLAY];
-	int team;
+	int			team;
 
 	if ( ! ent->client->pers.teamInfo )
 		return;
@@ -1059,7 +1064,7 @@
 	// send team info to spectator for team of followed client
 	if (ent->client->sess.sessionTeam == TEAM_SPECTATOR) {
 		if ( ent->client->sess.spectatorState != SPECTATOR_FOLLOW
-			 || ent->client->sess.spectatorClient < 0 ) {
+			|| ent->client->sess.spectatorClient < 0 ) {
 			return;
 		}
 		team = g_entities[ ent->client->sess.spectatorClient ].client->sess.sessionTeam;
@@ -1131,13 +1136,10 @@
 
 			if (ent->inuse && (ent->client->sess.sessionTeam == TEAM_RED ||	ent->client->sess.sessionTeam == TEAM_BLUE)) {
 				loc = Team_GetLocation( ent );
-				if (loc) {
+				if (loc)
 					ent->client->pers.teamState.location = loc->health;
-					// protocol 91
-					ent->client->ps.location = loc->health;
-				} else {
+				else
 					ent->client->pers.teamState.location = 0;
-				}
 			}
 		}
 
@@ -1269,7 +1271,7 @@
 	}
 
 	PrintMsg(NULL, "%s" S_COLOR_WHITE " brought in %i %s.\n",
-			 other->client->pers.netname, tokens, ( tokens == 1 ) ? "skull" : "skulls" );
+					other->client->pers.netname, tokens, ( tokens == 1 ) ? "skull" : "skulls" );
 
 	AddTeamScore(self->s.pos.trBase, other->client->sess.sessionTeam, tokens);
 	Team_ForceGesture(other->client->sess.sessionTeam);

```

### `openarena-engine`  — sha256 `901952fc8876...`, 41277 bytes

_Diff stat: +55 / -55 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_team.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_team.c	2026-04-16 22:48:25.752047200 +0100
@@ -45,16 +45,21 @@
 void Team_InitGame( void ) {
 	memset(&teamgame, 0, sizeof teamgame);
 
-	if (g_gametype.integer == GT_CTF) {
+	switch( g_gametype.integer ) {
+	case GT_CTF:
 		teamgame.redStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_RED, FLAG_ATBASE );
 		 teamgame.blueStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_BLUE, FLAG_ATBASE );
+		break;
 #ifdef MISSIONPACK
-	} else if (g_gametype.integer == GT_1FCTF) {
+	case GT_1FCTF:
 		teamgame.flagStatus = -1; // Invalid to force update
 		Team_SetFlagStatus( TEAM_FREE, FLAG_ATBASE );
+		break;
 #endif
+	default:
+		break;
 	}
 }
 
@@ -87,7 +92,7 @@
 }
 
 // NULL for everyone
-static Q_PRINTF_FUNC(2, 3)  void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
+static __attribute__ ((format (printf, 2, 3))) void QDECL PrintMsg( gentity_t *ent, const char *fmt, ... ) {
 	char		msg[1024];
 	va_list		argptr;
 	char		*p;
@@ -293,9 +298,8 @@
 		enemy_flag_pw = PW_REDFLAG;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (g_gametype.integer == GT_1FCTF) {
-		flag_pw = PW_NEUTRALFLAG;
 		enemy_flag_pw = PW_NEUTRALFLAG;
 	} 
 #endif
@@ -361,6 +365,23 @@
 		return;
 	}
 
+	if (targ->client->pers.teamState.lasthurtcarrier &&
+		level.time - targ->client->pers.teamState.lasthurtcarrier < CTF_CARRIER_DANGER_PROTECT_TIMEOUT) {
+		// attacker is on the same team as the skull carrier and
+		AddScore(attacker, targ->r.currentOrigin, CTF_CARRIER_DANGER_PROTECT_BONUS);
+
+		attacker->client->pers.teamState.carrierdefense++;
+		targ->client->pers.teamState.lasthurtcarrier = 0;
+
+		attacker->client->ps.persistant[PERS_DEFEND_COUNT]++;
+		// add the sprite over the player's head
+		attacker->client->ps.eFlags &= ~(EF_AWARD_IMPRESSIVE | EF_AWARD_EXCELLENT | EF_AWARD_GAUNTLET | EF_AWARD_ASSIST | EF_AWARD_DEFEND | EF_AWARD_CAP );
+		attacker->client->ps.eFlags |= EF_AWARD_DEFEND;
+		attacker->client->rewardTime = level.time + REWARD_SPRITE_TIME;
+
+		return;
+	}
+
 	// flag and flag carrier area defense bonuses
 
 	// we have to find the flag and carrier entities
@@ -441,7 +462,7 @@
 
 	if (carrier && carrier != attacker) {
 		VectorSubtract(targ->r.currentOrigin, carrier->r.currentOrigin, v1);
-		VectorSubtract(attacker->r.currentOrigin, carrier->r.currentOrigin, v2);
+		VectorSubtract(attacker->r.currentOrigin, carrier->r.currentOrigin, v1);
 
 		if ( ( ( VectorLength(v1) < CTF_ATTACKER_PROTECT_RADIUS &&
 			trap_InPVS(carrier->r.currentOrigin, targ->r.currentOrigin ) ) ||
@@ -482,12 +503,6 @@
 	else
 		flag_pw = PW_REDFLAG;
 
-#if 1  //def MPACK
-	if (g_gametype.integer == GT_1FCTF) {
-		flag_pw = PW_NEUTRALFLAG;
-	}
-#endif
-
 	// flags
 	if (targ->client->ps.powerups[flag_pw] &&
 		targ->client->sess.sessionTeam != attacker->client->sess.sessionTeam)
@@ -770,7 +785,7 @@
 				player->client->ps.eFlags |= EF_AWARD_ASSIST;
 				player->client->rewardTime = level.time + REWARD_SPRITE_TIME;
 
-			}
+			} 
 			if (player->client->pers.teamState.lastfraggedcarrier + 
 				CTF_FRAG_CARRIER_ASSIST_TIMEOUT > level.time) {
 				AddScore(player, ent->r.currentOrigin, CTF_FRAG_CARRIER_ASSIST_BONUS);
@@ -1051,7 +1066,7 @@
 	int			cnt;
 	int			h, a;
 	int			clients[TEAM_MAXOVERLAY];
-	int team;
+	int			team;
 
 	if ( ! ent->client->pers.teamInfo )
 		return;
@@ -1059,7 +1074,7 @@
 	// send team info to spectator for team of followed client
 	if (ent->client->sess.sessionTeam == TEAM_SPECTATOR) {
 		if ( ent->client->sess.spectatorState != SPECTATOR_FOLLOW
-			 || ent->client->sess.spectatorClient < 0 ) {
+			|| ent->client->sess.spectatorClient < 0 ) {
 			return;
 		}
 		team = g_entities[ ent->client->sess.spectatorClient ].client->sess.sessionTeam;
@@ -1131,13 +1146,10 @@
 
 			if (ent->inuse && (ent->client->sess.sessionTeam == TEAM_RED ||	ent->client->sess.sessionTeam == TEAM_BLUE)) {
 				loc = Team_GetLocation( ent );
-				if (loc) {
+				if (loc)
 					ent->client->pers.teamState.location = loc->health;
-					// protocol 91
-					ent->client->ps.location = loc->health;
-				} else {
+				else
 					ent->client->pers.teamState.location = 0;
-				}
 			}
 		}
 
@@ -1268,8 +1280,8 @@
 		return;
 	}
 
-	PrintMsg(NULL, "%s" S_COLOR_WHITE " brought in %i %s.\n",
-			 other->client->pers.netname, tokens, ( tokens == 1 ) ? "skull" : "skulls" );
+	PrintMsg(NULL, "%s" S_COLOR_WHITE " brought in %i skull%s.\n",
+					other->client->pers.netname, tokens, tokens ? "s" : "" );
 
 	AddTeamScore(self->s.pos.trBase, other->client->sess.sessionTeam, tokens);
 	Team_ForceGesture(other->client->sess.sessionTeam);
@@ -1301,8 +1313,9 @@
 	AddScore(attacker, self->r.currentOrigin, actualDamage);
 }
 
-// spawn invisible damagable obelisk entity / harvester base trigger.
-gentity_t *SpawnObelisk( vec3_t origin, vec3_t mins, vec3_t maxs, int team ) {
+gentity_t *SpawnObelisk( vec3_t origin, int team, int spawnflags) {
+	trace_t		tr;
+	vec3_t		dest;
 	gentity_t	*ent;
 
 	ent = G_Spawn();
@@ -1311,8 +1324,8 @@
 	VectorCopy( origin, ent->s.pos.trBase );
 	VectorCopy( origin, ent->r.currentOrigin );
 
-	VectorCopy( mins, ent->r.mins );
-	VectorCopy( maxs, ent->r.maxs );
+	VectorSet( ent->r.mins, -15, -15, 0 );
+	VectorSet( ent->r.maxs, 15, 15, 87 );
 
 	ent->s.eType = ET_GENERAL;
 	ent->flags = FL_NO_KNOCKBACK;
@@ -1331,26 +1344,7 @@
 		ent->touch = ObeliskTouch;
 	}
 
-	G_SetOrigin( ent, ent->s.origin );
-
-	ent->spawnflags = team;
-
-	trap_LinkEntity( ent );
-
-	return ent;
-}
-
-// setup entity for team base model / obelisk model.
-void ObeliskInit( gentity_t *ent ) {
-	trace_t tr;
-	vec3_t dest;
-
-	ent->s.eType = ET_TEAM;
-
-	VectorSet( ent->r.mins, -15, -15, 0 );
-	VectorSet( ent->r.maxs, 15, 15, 87 );
-
-	if ( ent->spawnflags & 1 ) {
+	if ( spawnflags & 1 ) {
 		// suspended
 		G_SetOrigin( ent, ent->s.origin );
 	} else {
@@ -1374,6 +1368,12 @@
 			G_SetOrigin( ent, tr.endpos );
 		}
 	}
+
+	ent->spawnflags = team;
+
+	trap_LinkEntity( ent );
+
+	return ent;
 }
 
 /*QUAKED team_redobelisk (1 0 0) (-16 -16 0) (16 16 8)
@@ -1385,16 +1385,16 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_OBELISK ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_RED );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_RED, ent->spawnflags );
 		obelisk->activator = ent;
 		// initial obelisk health value
 		ent->s.modelindex2 = 0xff;
 		ent->s.frame = 0;
 	}
 	if ( g_gametype.integer == GT_HARVESTER ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_RED );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_RED, ent->spawnflags );
 		obelisk->activator = ent;
 	}
 	ent->s.modelindex = TEAM_RED;
@@ -1410,16 +1410,16 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_OBELISK ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_BLUE );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_BLUE, ent->spawnflags );
 		obelisk->activator = ent;
 		// initial obelisk health value
 		ent->s.modelindex2 = 0xff;
 		ent->s.frame = 0;
 	}
 	if ( g_gametype.integer == GT_HARVESTER ) {
-		obelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_BLUE );
+		obelisk = SpawnObelisk( ent->s.origin, TEAM_BLUE, ent->spawnflags );
 		obelisk->activator = ent;
 	}
 	ent->s.modelindex = TEAM_BLUE;
@@ -1433,10 +1433,10 @@
 		G_FreeEntity(ent);
 		return;
 	}
-	ObeliskInit( ent );
+	ent->s.eType = ET_TEAM;
 	if ( g_gametype.integer == GT_HARVESTER) {
-		neutralObelisk = SpawnObelisk( ent->s.origin, ent->r.mins, ent->r.maxs, TEAM_FREE );
-		neutralObelisk->activator = ent;
+		neutralObelisk = SpawnObelisk( ent->s.origin, TEAM_FREE, ent->spawnflags);
+		neutralObelisk->spawnflags = TEAM_FREE;
 	}
 	ent->s.modelindex = TEAM_FREE;
 	trap_LinkEntity(ent);

```

### `openarena-gamecode`  — sha256 `dc97cb7ef6c2...`, 68422 bytes

_Diff stat: +1195 / -289 lines_

_(full diff is 69307 bytes — see files directly)_
