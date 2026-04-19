# Diff: `code/game/g_session.c`
**Canonical:** `wolfcamql-src` (sha256 `7e9eb2f74d31...`, 5031 bytes)

## Variants

### `quake3-source`  — sha256 `2021dc9d4b95...`, 4903 bytes

_Diff stat: +31 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_session.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_session.c	2026-04-16 20:02:19.909574100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -46,7 +46,7 @@
 
 	s = va("%i %i %i %i %i %i %i", 
 		client->sess.sessionTeam,
-		   client->sess.spectatorNum,
+		client->sess.spectatorTime,
 		client->sess.spectatorState,
 		client->sess.spectatorClient,
 		client->sess.wins,
@@ -54,7 +54,7 @@
 		client->sess.teamLeader
 		);
 
-	var = va( "session%i", (int)(client - level.clients) );
+	var = va( "session%i", client - level.clients );
 
 	trap_Cvar_Set( var, s );
 }
@@ -69,23 +69,26 @@
 void G_ReadSessionData( gclient_t *client ) {
 	char	s[MAX_STRING_CHARS];
 	const char	*var;
+
+	// bk001205 - format
 	int teamLeader;
 	int spectatorState;
 	int sessionTeam;
 
-	var = va( "session%i", (int)(client - level.clients) );
+	var = va( "session%i", client - level.clients );
 	trap_Cvar_VariableStringBuffer( var, s, sizeof(s) );
 
 	sscanf( s, "%i %i %i %i %i %i %i",
-		&sessionTeam,
-		&client->sess.spectatorNum,
-		&spectatorState,
+		&sessionTeam,                 // bk010221 - format
+		&client->sess.spectatorTime,
+		&spectatorState,              // bk010221 - format
 		&client->sess.spectatorClient,
 		&client->sess.wins,
 		&client->sess.losses,
-		&teamLeader
+		&teamLeader                   // bk010221 - format
 		);
 
+	// bk001205 - format issues
 	client->sess.sessionTeam = (team_t)sessionTeam;
 	client->sess.spectatorState = (spectatorState_t)spectatorState;
 	client->sess.teamLeader = (qboolean)teamLeader;
@@ -105,52 +108,46 @@
 
 	sess = &client->sess;
 
-	// check for team preference, mainly for bots
-	value = Info_ValueForKey( userinfo, "teampref" );
-
-	// check for human's team preference set by start server menu
-	if ( !value[0] && g_localTeamPref.string[0] && client->pers.localClient ) {
-		value = g_localTeamPref.string;
-
-		// clear team so it's only used once
-		trap_Cvar_Set( "g_localTeamPref", "" );
-	}
-
 	// initial team determination
 	if ( g_gametype.integer >= GT_TEAM ) {
-		// always spawn as spectator in team games
-		sess->sessionTeam = TEAM_SPECTATOR;
-		sess->spectatorState = SPECTATOR_FREE;
-
-		if ( value[0] || g_teamAutoJoin.integer ) {
-			SetTeam( &g_entities[client - level.clients], value );
+		if ( g_teamAutoJoin.integer ) {
+			sess->sessionTeam = PickTeam( -1 );
+			BroadcastTeamChange( client, -1 );
+		} else {
+			// always spawn as spectator in team games
+			sess->sessionTeam = TEAM_SPECTATOR;	
 		}
 	} else {
+		value = Info_ValueForKey( userinfo, "team" );
 		if ( value[0] == 's' ) {
 			// a willing spectator, not a waiting-in-line
 			sess->sessionTeam = TEAM_SPECTATOR;
 		} else {
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				// if the game is full, go into a waiting mode
-				if ( level.numNonSpectatorClients >= 2 ) {
+			switch ( g_gametype.integer ) {
+			default:
+			case GT_FFA:
+			case GT_SINGLE_PLAYER:
+				if ( g_maxGameClients.integer > 0 && 
+					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
-			} else {
-				if ( g_maxGameClients.integer > 0 &&
-					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
+				break;
+			case GT_TOURNAMENT:
+				// if the game is full, go into a waiting mode
+				if ( level.numNonSpectatorClients >= 2 ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
+				break;
 			}
 		}
-
-		sess->spectatorState = SPECTATOR_FREE;
 	}
 
-	AddTournamentQueue(client);
+	sess->spectatorState = SPECTATOR_FREE;
+	sess->spectatorTime = level.time;
 
 	G_WriteClientSessionData( client );
 }

```

### `ioquake3`  — sha256 `f3b91b49ef1d...`, 5110 bytes

_Diff stat: +12 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_session.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_session.c	2026-04-16 20:02:21.546476900 +0100
@@ -46,7 +46,7 @@
 
 	s = va("%i %i %i %i %i %i %i", 
 		client->sess.sessionTeam,
-		   client->sess.spectatorNum,
+		client->sess.spectatorNum,
 		client->sess.spectatorState,
 		client->sess.spectatorClient,
 		client->sess.wins,
@@ -130,20 +130,25 @@
 			// a willing spectator, not a waiting-in-line
 			sess->sessionTeam = TEAM_SPECTATOR;
 		} else {
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				// if the game is full, go into a waiting mode
-				if ( level.numNonSpectatorClients >= 2 ) {
+			switch ( g_gametype.integer ) {
+			default:
+			case GT_FFA:
+			case GT_SINGLE_PLAYER:
+				if ( g_maxGameClients.integer > 0 && 
+					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
-			} else {
-				if ( g_maxGameClients.integer > 0 &&
-					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
+				break;
+			case GT_TOURNAMENT:
+				// if the game is full, go into a waiting mode
+				if ( level.numNonSpectatorClients >= 2 ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
+				break;
 			}
 		}
 

```

### `openarena-engine`  — sha256 `413efbdc495c...`, 4828 bytes

_Diff stat: +20 / -26 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_session.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_session.c	2026-04-16 22:48:25.750042300 +0100
@@ -46,7 +46,7 @@
 
 	s = va("%i %i %i %i %i %i %i", 
 		client->sess.sessionTeam,
-		   client->sess.spectatorNum,
+		client->sess.spectatorNum,
 		client->sess.spectatorState,
 		client->sess.spectatorClient,
 		client->sess.wins,
@@ -105,51 +105,45 @@
 
 	sess = &client->sess;
 
-	// check for team preference, mainly for bots
-	value = Info_ValueForKey( userinfo, "teampref" );
-
-	// check for human's team preference set by start server menu
-	if ( !value[0] && g_localTeamPref.string[0] && client->pers.localClient ) {
-		value = g_localTeamPref.string;
-
-		// clear team so it's only used once
-		trap_Cvar_Set( "g_localTeamPref", "" );
-	}
-
 	// initial team determination
 	if ( g_gametype.integer >= GT_TEAM ) {
-		// always spawn as spectator in team games
-		sess->sessionTeam = TEAM_SPECTATOR;
-		sess->spectatorState = SPECTATOR_FREE;
-
-		if ( value[0] || g_teamAutoJoin.integer ) {
-			SetTeam( &g_entities[client - level.clients], value );
+		if ( g_teamAutoJoin.integer && !(g_entities[ client - level.clients ].r.svFlags & SVF_BOT) ) {
+			sess->sessionTeam = PickTeam( -1 );
+			BroadcastTeamChange( client, -1 );
+		} else {
+			// always spawn as spectator in team games
+			sess->sessionTeam = TEAM_SPECTATOR;	
 		}
 	} else {
+		value = Info_ValueForKey( userinfo, "team" );
 		if ( value[0] == 's' ) {
 			// a willing spectator, not a waiting-in-line
 			sess->sessionTeam = TEAM_SPECTATOR;
 		} else {
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				// if the game is full, go into a waiting mode
-				if ( level.numNonSpectatorClients >= 2 ) {
+			switch ( g_gametype.integer ) {
+			default:
+			case GT_FFA:
+			case GT_SINGLE_PLAYER:
+				if ( g_maxGameClients.integer > 0 && 
+					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
-			} else {
-				if ( g_maxGameClients.integer > 0 &&
-					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
+				break;
+			case GT_TOURNAMENT:
+				// if the game is full, go into a waiting mode
+				if ( level.numNonSpectatorClients >= 2 ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
+				break;
 			}
 		}
-
-		sess->spectatorState = SPECTATOR_FREE;
 	}
 
+	sess->spectatorState = SPECTATOR_FREE;
 	AddTournamentQueue(client);
 
 	G_WriteClientSessionData( client );

```

### `openarena-gamecode`  — sha256 `609b5688f0d6...`, 5404 bytes

_Diff stat: +30 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_session.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_session.c	2026-04-16 22:48:24.173988500 +0100
@@ -40,13 +40,13 @@
 Called on game shutdown
 ================
 */
-void G_WriteClientSessionData( gclient_t *client ) {
+static void G_WriteClientSessionData( const gclient_t *client ) {
 	const char	*s;
 	const char	*var;
 
 	s = va("%i %i %i %i %i %i %i", 
 		client->sess.sessionTeam,
-		   client->sess.spectatorNum,
+		client->sess.spectatorNum,
 		client->sess.spectatorState,
 		client->sess.spectatorClient,
 		client->sess.wins,
@@ -69,6 +69,8 @@
 void G_ReadSessionData( gclient_t *client ) {
 	char	s[MAX_STRING_CHARS];
 	const char	*var;
+
+	// bk001205 - format
 	int teamLeader;
 	int spectatorState;
 	int sessionTeam;
@@ -77,15 +79,16 @@
 	trap_Cvar_VariableStringBuffer( var, s, sizeof(s) );
 
 	sscanf( s, "%i %i %i %i %i %i %i",
-		&sessionTeam,
+		&sessionTeam,                 // bk010221 - format
 		&client->sess.spectatorNum,
-		&spectatorState,
+		&spectatorState,              // bk010221 - format
 		&client->sess.spectatorClient,
 		&client->sess.wins,
 		&client->sess.losses,
-		&teamLeader
+		&teamLeader                   // bk010221 - format
 		);
 
+	// bk001205 - format issues
 	client->sess.sessionTeam = (team_t)sessionTeam;
 	client->sess.spectatorState = (spectatorState_t)spectatorState;
 	client->sess.teamLeader = (qboolean)teamLeader;
@@ -107,50 +110,54 @@
 
 	// check for team preference, mainly for bots
 	value = Info_ValueForKey( userinfo, "teampref" );
-
 	// check for human's team preference set by start server menu
 	if ( !value[0] && g_localTeamPref.string[0] && client->pers.localClient ) {
 		value = g_localTeamPref.string;
-
 		// clear team so it's only used once
 		trap_Cvar_Set( "g_localTeamPref", "" );
 	}
 
 	// initial team determination
-	if ( g_gametype.integer >= GT_TEAM ) {
-		// always spawn as spectator in team games
-		sess->sessionTeam = TEAM_SPECTATOR;
-		sess->spectatorState = SPECTATOR_FREE;
-
-		if ( value[0] || g_teamAutoJoin.integer ) {
-			SetTeam( &g_entities[client - level.clients], value );
+	if ( g_gametype.integer >= GT_TEAM && g_ffa_gt!=1) {
+		if ( g_teamAutoJoin.integer && !(g_entities[ client - level.clients ].r.svFlags & SVF_BOT) ) {
+			sess->sessionTeam = PickTeam( -1 );
+			BroadcastTeamChange( client, -1 );
+		} else {
+			// always spawn as spectator in team games
+			sess->sessionTeam = TEAM_SPECTATOR;	
 		}
 	} else {
+		value = Info_ValueForKey( userinfo, "team" );
 		if ( value[0] == 's' ) {
 			// a willing spectator, not a waiting-in-line
 			sess->sessionTeam = TEAM_SPECTATOR;
 		} else {
-			if (g_gametype.integer == GT_TOURNAMENT) {
-				// if the game is full, go into a waiting mode
-				if ( level.numNonSpectatorClients >= 2 ) {
+			switch ( g_gametype.integer ) {
+			default:
+			case GT_FFA:
+			case GT_LMS:
+			case GT_SINGLE_PLAYER:
+				if ( g_maxGameClients.integer > 0 && 
+					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
-			} else {
-				if ( g_maxGameClients.integer > 0 &&
-					level.numNonSpectatorClients >= g_maxGameClients.integer ) {
+				break;
+			case GT_TOURNAMENT:
+				// if the game is full, go into a waiting mode
+				if ( level.numNonSpectatorClients >= 2 ) {
 					sess->sessionTeam = TEAM_SPECTATOR;
 				} else {
 					sess->sessionTeam = TEAM_FREE;
 				}
+				break;
 			}
 		}
-
-		sess->spectatorState = SPECTATOR_FREE;
 	}
 
-	AddTournamentQueue(client);
+	sess->spectatorState = SPECTATOR_FREE;
+	 AddTournamentQueue(client);
 
 	G_WriteClientSessionData( client );
 }

```
