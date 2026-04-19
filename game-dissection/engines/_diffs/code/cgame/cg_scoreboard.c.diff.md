# Diff: `code/cgame/cg_scoreboard.c`
**Canonical:** `wolfcamql-src` (sha256 `fafa2252ccd7...`, 21739 bytes)

## Variants

### `quake3-source`  — sha256 `5ec0df064543...`, 15435 bytes

_Diff stat: +76 / -291 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_scoreboard.c	2026-04-16 20:02:25.152558600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\cgame\cg_scoreboard.c	2026-04-16 20:02:19.885590400 +0100
@@ -1,19 +1,28 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Foobar; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_scoreboard -- draw the scoreboard on top of the game screen
 #include "cg_local.h"
 
-#include "cg_draw.h"
-#include "cg_drawtools.h"
-#include "cg_event.h"
-#include "cg_main.h"
-#include "cg_newdraw.h"  // QLWideScreen
-#include "cg_players.h"
-#include "cg_scoreboard.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-#include "wolfcam_local.h"
 
 #define	SCOREBOARD_X		(0)
 
@@ -64,36 +73,22 @@
 static qboolean localClient; // true if local client has been displayed
 
 
-static void CG_DrawClientScore( int y, const score_t *score, const float *color, float fade, qboolean largeFormat ) {
+							 /*
+=================
+CG_DrawScoreboard
+=================
+*/
+static void CG_DrawClientScore( int y, score_t *score, float *color, float fade, qboolean largeFormat ) {
 	char	string[1024];
 	vec3_t	headAngles;
-	const clientInfo_t *ci;
+	clientInfo_t	*ci;
 	int iconx, headx;
 
-#if 0
-	Com_Printf("----  CG_DrawClientScore()  ------\n");
-		Com_Printf("  client: %d\n", score->client);
-		Com_Printf("  score: %d\n", score->score);
-		Com_Printf("  ping:  %d\n", score->ping);
-		Com_Printf("  time: %d\n", score->time);
-		Com_Printf("  scoreFlags: %d\n", score->scoreFlags);
-		Com_Printf("  powerUps:  %d\n", score->powerUps);
-		Com_Printf("  accuracy:  %d\n", score->accuracy);
-		//		Com_Printf("  ...\n");
-		Com_Printf("  impressiveCount:  %d\n", score->impressiveCount);
-		Com_Printf("  excellentCount:  %d\n", score->excellentCount);
-		Com_Printf("  gauntletCount:  %d\n", score->gauntletCount);
-		Com_Printf("  defendCount:  %d\n", score->defendCount);
-		Com_Printf("  assistCount:  %d\n", score->assistCount);
-		Com_Printf("  perfect:  %d\n", score->perfect);
-		Com_Printf("  team:  %d\n", score->team);
-#endif
-
 	if ( score->client < 0 || score->client >= cgs.maxclients ) {
 		Com_Printf( "Bad score->client: %i\n", score->client );
 		return;
 	}
-
+	
 	ci = &cgs.clientinfo[score->client];
 
 	iconx = SB_BOTICON_X + (SB_RATING_WIDTH / 2);
@@ -133,14 +128,14 @@
 			}
 		} else if ( ci->handicap < 100 ) {
 			Com_sprintf( string, sizeof( string ), "%i", ci->handicap );
-			if ( CG_IsDuelGame(cgs.gametype) )
+			if ( cgs.gametype == GT_TOURNAMENT )
 				CG_DrawSmallStringColor( iconx, y - SMALLCHAR_HEIGHT/2, string, color );
 			else
 				CG_DrawSmallStringColor( iconx, y, string, color );
 		}
 
 		// draw the wins / losses
-		if ( CG_IsDuelGame(cgs.gametype) ) {
+		if ( cgs.gametype == GT_TOURNAMENT ) {
 			Com_sprintf( string, sizeof( string ), "%i/%i", ci->wins, ci->losses );
 			if( ci->handicap < 100 && !ci->botSkill ) {
 				CG_DrawSmallStringColor( iconx, y + SMALLCHAR_HEIGHT/2, string, color );
@@ -156,10 +151,10 @@
 	headAngles[YAW] = 180;
 	if( largeFormat ) {
 		CG_DrawHead( headx, y - ( ICON_SIZE - BIGCHAR_HEIGHT ) / 2, ICON_SIZE, ICON_SIZE, 
-					 score->client, headAngles, qtrue, qfalse, qtrue );
+			score->client, headAngles );
 	}
 	else {
-		CG_DrawHead( headx, y, 16, 16, score->client, headAngles, qtrue, qfalse, qtrue );
+		CG_DrawHead( headx, y, 16, 16, score->client, headAngles );
 	}
 
 #ifdef MISSIONPACK
@@ -177,29 +172,14 @@
 	if ( score->ping == -1 ) {
 		Com_sprintf(string, sizeof(string),
 			" connecting    %s", ci->name);
-	//} else if ( ci->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
-	} else if ( score->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
+	} else if ( ci->team == TEAM_SPECTATOR ) {
 		Com_sprintf(string, sizeof(string),
-			"^3%5i %4i %4i ^7%s", score->score, score->ping, score->time, ci->name);
-	} else if (cg.numScores > 0) {
-#if 1
+			" SPECT %3i %4i %s", score->ping, score->time, ci->name);
+	} else {
 		Com_sprintf(string, sizeof(string),
 			"%5i %4i %4i %s", score->score, score->ping, score->time, ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-			"%5i %4i %4i %i %i %i %i %s %s", score->score, score->ping, score->time, score->alive, score->frags, score->deaths, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %d %s %s", score->score, score->ping, score->time, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-	} else if (cg.demoPlayback) {
-		Com_sprintf(string, sizeof(string),
-					"               %s", ci->name);
 	}
 
-	//FIXME wolfcam
 	// highlight your position
 	if ( score->client == cg.snap->ps.clientNum ) {
 		float	hcolor[4];
@@ -207,8 +187,8 @@
 
 		localClient = qtrue;
 
-		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR
-			 || (CG_IsTeamGame(cgs.gametype)  &&  cgs.gametype != GT_RED_ROVER) ) {
+		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR 
+			|| cgs.gametype >= GT_TEAM ) {
 			rank = -1;
 		} else {
 			rank = cg.snap->ps.persistant[PERS_RANK] & ~RANK_TIED_FLAG;
@@ -244,62 +224,6 @@
 	}
 }
 
-static void CG_DrawClientScoreCpmaMstatsa (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	ds = &cg.duelScores[player];
-
-	// draw the score line
-	if (cg.duelForfeit  &&  player == 1) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
-static void CG_DrawClientScoreQlForfeit (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-	int forfeitPlayer;
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	// indexed at 1
-	forfeitPlayer = cg.duelPlayerForfeit - 1;
-
-	ds = &cg.duelScores[player];
-
-
-	// draw the score line
-	if (player == forfeitPlayer) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
 /*
 =================
 CG_TeamScoreboard
@@ -307,102 +231,15 @@
 */
 static int CG_TeamScoreboard( int y, team_t team, float fade, int maxClients, int lineHeight ) {
 	int		i;
-	const score_t	*score;
+	score_t	*score;
 	float	color[4];
 	int		count;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 
 	color[0] = color[1] = color[2] = 1.0;
 	color[3] = fade;
 
 	count = 0;
-
-	// cpma mstatsa doesn't transmit client numbers
-	if (cgs.cpma  &&  CG_CheckCpmaVersion(1, 50, "")  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cgs.protocolClass == PROTOCOL_QL  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION  &&  cg.duelForfeit) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cg.numScores == 0) {
-		for (i = 0;  i < MAX_CLIENTS;  i++) {
-			score_t sc;
-
-			ci = &cgs.clientinfo[i];
-			if (!ci->infoValid)
-				continue;
-
-			if (team != ci->team)
-				continue;
-
-			memset(&sc, 0, sizeof(sc));
-			sc.client = i;
-			sc.team = ci->team;
-
-			CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-			count++;
-		}
-		return count;
-	}
-
-	count = 0;
-
 	for ( i = 0 ; i < cg.numScores && count < maxClients ; i++ ) {
 		score = &cg.scores[i];
 		ci = &cgs.clientinfo[ score->client ];
@@ -421,7 +258,7 @@
 
 /*
 =================
-CG_DrawOldScoreboard
+CG_DrawScoreboard
 
 Draw the normal in-game scoreboard
 =================
@@ -429,14 +266,12 @@
 qboolean CG_DrawOldScoreboard( void ) {
 	int		x, y, w, i, n1, n2;
 	float	fade;
-	const float	*fadeColor;
-	const char	*s;
+	float	*fadeColor;
+	char	*s;
 	int maxClients;
 	int lineHeight;
 	int topBorderSize, bottomBorderSize;
 
-	QLWideScreen = WIDESCREEN_CENTER;
-
 	// don't draw amuthing if the menu or console is up
 	if ( cg_paused.integer ) {
 		cg.deferredPlayerLoading = 0;
@@ -459,7 +294,7 @@
 		fadeColor = colorWhite;
 	} else {
 		fadeColor = CG_FadeColor( cg.scoreFadeTime, FADE_TIME );
-
+		
 		if ( !fadeColor ) {
 			// next time scoreboard comes up, don't print killer
 			cg.deferredPlayerLoading = 0;
@@ -473,75 +308,22 @@
 	// fragged by ... line
 	if ( cg.killerName[0] ) {
 		s = va("Fragged by %s", cg.killerName );
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 40;
 		CG_DrawBigString( x, y, s, fade );
 	}
 
 	// current rank
-	if (!CG_IsTeamGame(cgs.gametype)) {
-		if (!wolfcam_following  ||  (wolfcam_following  &&  wcg.clientNum == cg.snap->ps.clientNum)) {
-			if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
-				s = va("%s place with %i",
-					   CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
-					   cg.snap->ps.persistant[PERS_SCORE] );
-				w = CG_DrawStrlen( s, &cgs.media.bigchar );
-				x = ( SCREEN_WIDTH - w ) / 2;
-				y = 60;
-				CG_DrawBigString( x, y, s, fade );
-			}
-		} else {  // wolfcam_following
-			if (cgs.clientinfo[wcg.clientNum].team != TEAM_SPECTATOR) {
-				if (CG_IsCpmaMvd()) {
-					int rank;
-					int j;
-
-					rank = 1;
-					for (j = 0;  j < MAX_CLIENTS;  j++) {
-						if (!cgs.clientinfo[j].infoValid) {
-							continue;
-						}
-						if (cgs.clientinfo[j].team == TEAM_SPECTATOR) {
-							continue;
-						}
-						if (cgs.clientinfo[j].score > cgs.clientinfo[wcg.clientNum].score) {
-							rank++;
-						}
-					}
-
-					s = va("%s ^7place with %i", CG_PlaceString(rank), cgs.clientinfo[wcg.clientNum].score);
-
-					w = CG_DrawStrlen( s, &cgs.media.bigchar );
-					x = ( SCREEN_WIDTH - w ) / 2;
-					y = 60;
-					CG_DrawBigString( x, y, s, fade );
-				} else {  // not cpma mvd
-					// following someone who is ingame but not the main demo view
-
-					if (CG_IsDuelGame(cgs.gametype)) {
-						// we are following the other dueler
-						if (cgs.scores1 == cgs.scores2) {
-							s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-						} else {
-							if (cg.snap->ps.persistant[PERS_RANK] == 0) {
-								// we are second
-								s = va("%s ^7place with %i", CG_PlaceString(2), cgs.scores2);
-							} else {
-								// we are first
-								s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-							}
-						}
-						w = CG_DrawStrlen( s, &cgs.media.bigchar );
-						x = ( SCREEN_WIDTH - w ) / 2;
-						y = 60;
-						CG_DrawBigString( x, y, s, fade );
-					} else {
-						// we don't have enough information
-						// pass, don't draw ranking
-					}
-				}
-			}
+	if ( cgs.gametype < GT_TEAM) {
+		if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
+			s = va("%s place with %i",
+				CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
+				cg.snap->ps.persistant[PERS_SCORE] );
+			w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
+			x = ( SCREEN_WIDTH - w ) / 2;
+			y = 60;
+			CG_DrawBigString( x, y, s, fade );
 		}
 	} else {
 		if ( cg.teamScores[0] == cg.teamScores[1] ) {
@@ -552,7 +334,7 @@
 			s = va("Blue leads %i to %i",cg.teamScores[1], cg.teamScores[0] );
 		}
 
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 60;
 		CG_DrawBigString( x, y, s, fade );
@@ -569,7 +351,7 @@
 	y = SB_TOP;
 
 	// If there are more than SB_MAXCLIENTS_NORMAL, use the interleaved scores
-	if (1) {  //( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
+	if ( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
 		maxClients = SB_MAXCLIENTS_INTER;
 		lineHeight = SB_INTER_HEIGHT;
 		topBorderSize = 8;
@@ -583,7 +365,7 @@
 
 	localClient = qfalse;
 
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
@@ -655,9 +437,9 @@
 	color[2] = 1;
 	color[3] = 1;
 
-	x = 0.5 * ( 640 - CG_DrawStrlen( string, &cgs.media.giantchar ) );
+	x = 0.5 * ( 640 - GIANT_WIDTH * CG_DrawStrlen( string ) );
 
-	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 }
 
 /*
@@ -667,11 +449,11 @@
 Draw the oversize scoreboard for tournements
 =================
 */
-void CG_DrawTourneyScoreboard( void ) {
+void CG_DrawOldTourneyScoreboard( void ) {
 	const char		*s;
 	vec4_t			color;
 	int				min, tens, ones;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 	int				y;
 	int				i;
 
@@ -681,16 +463,16 @@
 		trap_SendClientCommand( "score" );
 	}
 
-	// draw the dialog background
-	color[0] = color[1] = color[2] = 0;
-	color[3] = 1;
-	CG_FillRect( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, color );
-
 	color[0] = 1;
 	color[1] = 1;
 	color[2] = 1;
 	color[3] = 1;
 
+	// draw the dialog background
+	color[0] = color[1] = color[2] = 0;
+	color[3] = 1;
+	CG_FillRect( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, color );
+
 	// print the mesage of the day
 	s = CG_ConfigString( CS_MOTD );
 	if ( !s[0] ) {
@@ -714,19 +496,19 @@
 	// print the two scores
 
 	y = 160;
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
-		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[0] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		
 		y += 64;
 
-		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[1] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 	} else {
 		//
 		// free for all scoreboard
@@ -740,10 +522,13 @@
 				continue;
 			}
 
-			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			s = va("%i", ci->score );
-			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			y += 64;
 		}
 	}
+
+
 }
+

```

### `ioquake3`  — sha256 `2f0d2e88ce7b...`, 15453 bytes

_Diff stat: +70 / -285 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_scoreboard.c	2026-04-16 20:02:25.152558600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\cgame\cg_scoreboard.c	2026-04-16 20:02:21.523053400 +0100
@@ -1,19 +1,28 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_scoreboard -- draw the scoreboard on top of the game screen
 #include "cg_local.h"
 
-#include "cg_draw.h"
-#include "cg_drawtools.h"
-#include "cg_event.h"
-#include "cg_main.h"
-#include "cg_newdraw.h"  // QLWideScreen
-#include "cg_players.h"
-#include "cg_scoreboard.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-#include "wolfcam_local.h"
 
 #define	SCOREBOARD_X		(0)
 
@@ -64,36 +73,22 @@
 static qboolean localClient; // true if local client has been displayed
 
 
-static void CG_DrawClientScore( int y, const score_t *score, const float *color, float fade, qboolean largeFormat ) {
+							 /*
+=================
+CG_DrawScoreboard
+=================
+*/
+static void CG_DrawClientScore( int y, score_t *score, float *color, float fade, qboolean largeFormat ) {
 	char	string[1024];
 	vec3_t	headAngles;
-	const clientInfo_t *ci;
+	clientInfo_t	*ci;
 	int iconx, headx;
 
-#if 0
-	Com_Printf("----  CG_DrawClientScore()  ------\n");
-		Com_Printf("  client: %d\n", score->client);
-		Com_Printf("  score: %d\n", score->score);
-		Com_Printf("  ping:  %d\n", score->ping);
-		Com_Printf("  time: %d\n", score->time);
-		Com_Printf("  scoreFlags: %d\n", score->scoreFlags);
-		Com_Printf("  powerUps:  %d\n", score->powerUps);
-		Com_Printf("  accuracy:  %d\n", score->accuracy);
-		//		Com_Printf("  ...\n");
-		Com_Printf("  impressiveCount:  %d\n", score->impressiveCount);
-		Com_Printf("  excellentCount:  %d\n", score->excellentCount);
-		Com_Printf("  gauntletCount:  %d\n", score->gauntletCount);
-		Com_Printf("  defendCount:  %d\n", score->defendCount);
-		Com_Printf("  assistCount:  %d\n", score->assistCount);
-		Com_Printf("  perfect:  %d\n", score->perfect);
-		Com_Printf("  team:  %d\n", score->team);
-#endif
-
 	if ( score->client < 0 || score->client >= cgs.maxclients ) {
 		Com_Printf( "Bad score->client: %i\n", score->client );
 		return;
 	}
-
+	
 	ci = &cgs.clientinfo[score->client];
 
 	iconx = SB_BOTICON_X + (SB_RATING_WIDTH / 2);
@@ -133,14 +128,14 @@
 			}
 		} else if ( ci->handicap < 100 ) {
 			Com_sprintf( string, sizeof( string ), "%i", ci->handicap );
-			if ( CG_IsDuelGame(cgs.gametype) )
+			if ( cgs.gametype == GT_TOURNAMENT )
 				CG_DrawSmallStringColor( iconx, y - SMALLCHAR_HEIGHT/2, string, color );
 			else
 				CG_DrawSmallStringColor( iconx, y, string, color );
 		}
 
 		// draw the wins / losses
-		if ( CG_IsDuelGame(cgs.gametype) ) {
+		if ( cgs.gametype == GT_TOURNAMENT ) {
 			Com_sprintf( string, sizeof( string ), "%i/%i", ci->wins, ci->losses );
 			if( ci->handicap < 100 && !ci->botSkill ) {
 				CG_DrawSmallStringColor( iconx, y + SMALLCHAR_HEIGHT/2, string, color );
@@ -156,10 +151,10 @@
 	headAngles[YAW] = 180;
 	if( largeFormat ) {
 		CG_DrawHead( headx, y - ( ICON_SIZE - BIGCHAR_HEIGHT ) / 2, ICON_SIZE, ICON_SIZE, 
-					 score->client, headAngles, qtrue, qfalse, qtrue );
+			score->client, headAngles );
 	}
 	else {
-		CG_DrawHead( headx, y, 16, 16, score->client, headAngles, qtrue, qfalse, qtrue );
+		CG_DrawHead( headx, y, 16, 16, score->client, headAngles );
 	}
 
 #ifdef MISSIONPACK
@@ -177,29 +172,14 @@
 	if ( score->ping == -1 ) {
 		Com_sprintf(string, sizeof(string),
 			" connecting    %s", ci->name);
-	//} else if ( ci->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
-	} else if ( score->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
+	} else if ( ci->team == TEAM_SPECTATOR ) {
 		Com_sprintf(string, sizeof(string),
-			"^3%5i %4i %4i ^7%s", score->score, score->ping, score->time, ci->name);
-	} else if (cg.numScores > 0) {
-#if 1
+			" SPECT %3i %4i %s", score->ping, score->time, ci->name);
+	} else {
 		Com_sprintf(string, sizeof(string),
 			"%5i %4i %4i %s", score->score, score->ping, score->time, ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-			"%5i %4i %4i %i %i %i %i %s %s", score->score, score->ping, score->time, score->alive, score->frags, score->deaths, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %d %s %s", score->score, score->ping, score->time, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-	} else if (cg.demoPlayback) {
-		Com_sprintf(string, sizeof(string),
-					"               %s", ci->name);
 	}
 
-	//FIXME wolfcam
 	// highlight your position
 	if ( score->client == cg.snap->ps.clientNum ) {
 		float	hcolor[4];
@@ -207,8 +187,8 @@
 
 		localClient = qtrue;
 
-		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR
-			 || (CG_IsTeamGame(cgs.gametype)  &&  cgs.gametype != GT_RED_ROVER) ) {
+		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR 
+			|| cgs.gametype >= GT_TEAM ) {
 			rank = -1;
 		} else {
 			rank = cg.snap->ps.persistant[PERS_RANK] & ~RANK_TIED_FLAG;
@@ -244,62 +224,6 @@
 	}
 }
 
-static void CG_DrawClientScoreCpmaMstatsa (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	ds = &cg.duelScores[player];
-
-	// draw the score line
-	if (cg.duelForfeit  &&  player == 1) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
-static void CG_DrawClientScoreQlForfeit (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-	int forfeitPlayer;
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	// indexed at 1
-	forfeitPlayer = cg.duelPlayerForfeit - 1;
-
-	ds = &cg.duelScores[player];
-
-
-	// draw the score line
-	if (player == forfeitPlayer) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
 /*
 =================
 CG_TeamScoreboard
@@ -307,102 +231,15 @@
 */
 static int CG_TeamScoreboard( int y, team_t team, float fade, int maxClients, int lineHeight ) {
 	int		i;
-	const score_t	*score;
+	score_t	*score;
 	float	color[4];
 	int		count;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 
 	color[0] = color[1] = color[2] = 1.0;
 	color[3] = fade;
 
 	count = 0;
-
-	// cpma mstatsa doesn't transmit client numbers
-	if (cgs.cpma  &&  CG_CheckCpmaVersion(1, 50, "")  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cgs.protocolClass == PROTOCOL_QL  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION  &&  cg.duelForfeit) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cg.numScores == 0) {
-		for (i = 0;  i < MAX_CLIENTS;  i++) {
-			score_t sc;
-
-			ci = &cgs.clientinfo[i];
-			if (!ci->infoValid)
-				continue;
-
-			if (team != ci->team)
-				continue;
-
-			memset(&sc, 0, sizeof(sc));
-			sc.client = i;
-			sc.team = ci->team;
-
-			CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-			count++;
-		}
-		return count;
-	}
-
-	count = 0;
-
 	for ( i = 0 ; i < cg.numScores && count < maxClients ; i++ ) {
 		score = &cg.scores[i];
 		ci = &cgs.clientinfo[ score->client ];
@@ -421,7 +258,7 @@
 
 /*
 =================
-CG_DrawOldScoreboard
+CG_DrawScoreboard
 
 Draw the normal in-game scoreboard
 =================
@@ -429,14 +266,12 @@
 qboolean CG_DrawOldScoreboard( void ) {
 	int		x, y, w, i, n1, n2;
 	float	fade;
-	const float	*fadeColor;
-	const char	*s;
+	float	*fadeColor;
+	char	*s;
 	int maxClients;
 	int lineHeight;
 	int topBorderSize, bottomBorderSize;
 
-	QLWideScreen = WIDESCREEN_CENTER;
-
 	// don't draw amuthing if the menu or console is up
 	if ( cg_paused.integer ) {
 		cg.deferredPlayerLoading = 0;
@@ -459,7 +294,7 @@
 		fadeColor = colorWhite;
 	} else {
 		fadeColor = CG_FadeColor( cg.scoreFadeTime, FADE_TIME );
-
+		
 		if ( !fadeColor ) {
 			// next time scoreboard comes up, don't print killer
 			cg.deferredPlayerLoading = 0;
@@ -473,75 +308,22 @@
 	// fragged by ... line
 	if ( cg.killerName[0] ) {
 		s = va("Fragged by %s", cg.killerName );
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 40;
 		CG_DrawBigString( x, y, s, fade );
 	}
 
 	// current rank
-	if (!CG_IsTeamGame(cgs.gametype)) {
-		if (!wolfcam_following  ||  (wolfcam_following  &&  wcg.clientNum == cg.snap->ps.clientNum)) {
-			if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
-				s = va("%s place with %i",
-					   CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
-					   cg.snap->ps.persistant[PERS_SCORE] );
-				w = CG_DrawStrlen( s, &cgs.media.bigchar );
-				x = ( SCREEN_WIDTH - w ) / 2;
-				y = 60;
-				CG_DrawBigString( x, y, s, fade );
-			}
-		} else {  // wolfcam_following
-			if (cgs.clientinfo[wcg.clientNum].team != TEAM_SPECTATOR) {
-				if (CG_IsCpmaMvd()) {
-					int rank;
-					int j;
-
-					rank = 1;
-					for (j = 0;  j < MAX_CLIENTS;  j++) {
-						if (!cgs.clientinfo[j].infoValid) {
-							continue;
-						}
-						if (cgs.clientinfo[j].team == TEAM_SPECTATOR) {
-							continue;
-						}
-						if (cgs.clientinfo[j].score > cgs.clientinfo[wcg.clientNum].score) {
-							rank++;
-						}
-					}
-
-					s = va("%s ^7place with %i", CG_PlaceString(rank), cgs.clientinfo[wcg.clientNum].score);
-
-					w = CG_DrawStrlen( s, &cgs.media.bigchar );
-					x = ( SCREEN_WIDTH - w ) / 2;
-					y = 60;
-					CG_DrawBigString( x, y, s, fade );
-				} else {  // not cpma mvd
-					// following someone who is ingame but not the main demo view
-
-					if (CG_IsDuelGame(cgs.gametype)) {
-						// we are following the other dueler
-						if (cgs.scores1 == cgs.scores2) {
-							s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-						} else {
-							if (cg.snap->ps.persistant[PERS_RANK] == 0) {
-								// we are second
-								s = va("%s ^7place with %i", CG_PlaceString(2), cgs.scores2);
-							} else {
-								// we are first
-								s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-							}
-						}
-						w = CG_DrawStrlen( s, &cgs.media.bigchar );
-						x = ( SCREEN_WIDTH - w ) / 2;
-						y = 60;
-						CG_DrawBigString( x, y, s, fade );
-					} else {
-						// we don't have enough information
-						// pass, don't draw ranking
-					}
-				}
-			}
+	if ( cgs.gametype < GT_TEAM) {
+		if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
+			s = va("%s place with %i",
+				CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
+				cg.snap->ps.persistant[PERS_SCORE] );
+			w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
+			x = ( SCREEN_WIDTH - w ) / 2;
+			y = 60;
+			CG_DrawBigString( x, y, s, fade );
 		}
 	} else {
 		if ( cg.teamScores[0] == cg.teamScores[1] ) {
@@ -552,7 +334,7 @@
 			s = va("Blue leads %i to %i",cg.teamScores[1], cg.teamScores[0] );
 		}
 
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 60;
 		CG_DrawBigString( x, y, s, fade );
@@ -569,7 +351,7 @@
 	y = SB_TOP;
 
 	// If there are more than SB_MAXCLIENTS_NORMAL, use the interleaved scores
-	if (1) {  //( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
+	if ( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
 		maxClients = SB_MAXCLIENTS_INTER;
 		lineHeight = SB_INTER_HEIGHT;
 		topBorderSize = 8;
@@ -583,7 +365,7 @@
 
 	localClient = qfalse;
 
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
@@ -655,9 +437,9 @@
 	color[2] = 1;
 	color[3] = 1;
 
-	x = 0.5 * ( 640 - CG_DrawStrlen( string, &cgs.media.giantchar ) );
+	x = 0.5 * ( 640 - GIANT_WIDTH * CG_DrawStrlen( string ) );
 
-	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 }
 
 /*
@@ -671,7 +453,7 @@
 	const char		*s;
 	vec4_t			color;
 	int				min, tens, ones;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 	int				y;
 	int				i;
 
@@ -714,19 +496,19 @@
 	// print the two scores
 
 	y = 160;
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
-		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[0] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		
 		y += 64;
 
-		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[1] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 	} else {
 		//
 		// free for all scoreboard
@@ -740,10 +522,13 @@
 				continue;
 			}
 
-			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			s = va("%i", ci->score );
-			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			y += 64;
 		}
 	}
+
+
 }
+

```

### `openarena-engine`  — sha256 `dceae82d5d44...`, 15456 bytes

_Diff stat: +71 / -286 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_scoreboard.c	2026-04-16 20:02:25.152558600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_scoreboard.c	2026-04-16 22:48:25.726201700 +0100
@@ -1,19 +1,28 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_scoreboard -- draw the scoreboard on top of the game screen
 #include "cg_local.h"
 
-#include "cg_draw.h"
-#include "cg_drawtools.h"
-#include "cg_event.h"
-#include "cg_main.h"
-#include "cg_newdraw.h"  // QLWideScreen
-#include "cg_players.h"
-#include "cg_scoreboard.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-#include "wolfcam_local.h"
 
 #define	SCOREBOARD_X		(0)
 
@@ -64,36 +73,22 @@
 static qboolean localClient; // true if local client has been displayed
 
 
-static void CG_DrawClientScore( int y, const score_t *score, const float *color, float fade, qboolean largeFormat ) {
+							 /*
+=================
+CG_DrawScoreboard
+=================
+*/
+static void CG_DrawClientScore( int y, score_t *score, float *color, float fade, qboolean largeFormat ) {
 	char	string[1024];
 	vec3_t	headAngles;
-	const clientInfo_t *ci;
+	clientInfo_t	*ci;
 	int iconx, headx;
 
-#if 0
-	Com_Printf("----  CG_DrawClientScore()  ------\n");
-		Com_Printf("  client: %d\n", score->client);
-		Com_Printf("  score: %d\n", score->score);
-		Com_Printf("  ping:  %d\n", score->ping);
-		Com_Printf("  time: %d\n", score->time);
-		Com_Printf("  scoreFlags: %d\n", score->scoreFlags);
-		Com_Printf("  powerUps:  %d\n", score->powerUps);
-		Com_Printf("  accuracy:  %d\n", score->accuracy);
-		//		Com_Printf("  ...\n");
-		Com_Printf("  impressiveCount:  %d\n", score->impressiveCount);
-		Com_Printf("  excellentCount:  %d\n", score->excellentCount);
-		Com_Printf("  gauntletCount:  %d\n", score->gauntletCount);
-		Com_Printf("  defendCount:  %d\n", score->defendCount);
-		Com_Printf("  assistCount:  %d\n", score->assistCount);
-		Com_Printf("  perfect:  %d\n", score->perfect);
-		Com_Printf("  team:  %d\n", score->team);
-#endif
-
 	if ( score->client < 0 || score->client >= cgs.maxclients ) {
 		Com_Printf( "Bad score->client: %i\n", score->client );
 		return;
 	}
-
+	
 	ci = &cgs.clientinfo[score->client];
 
 	iconx = SB_BOTICON_X + (SB_RATING_WIDTH / 2);
@@ -133,14 +128,14 @@
 			}
 		} else if ( ci->handicap < 100 ) {
 			Com_sprintf( string, sizeof( string ), "%i", ci->handicap );
-			if ( CG_IsDuelGame(cgs.gametype) )
+			if ( cgs.gametype == GT_TOURNAMENT )
 				CG_DrawSmallStringColor( iconx, y - SMALLCHAR_HEIGHT/2, string, color );
 			else
 				CG_DrawSmallStringColor( iconx, y, string, color );
 		}
 
 		// draw the wins / losses
-		if ( CG_IsDuelGame(cgs.gametype) ) {
+		if ( cgs.gametype == GT_TOURNAMENT ) {
 			Com_sprintf( string, sizeof( string ), "%i/%i", ci->wins, ci->losses );
 			if( ci->handicap < 100 && !ci->botSkill ) {
 				CG_DrawSmallStringColor( iconx, y + SMALLCHAR_HEIGHT/2, string, color );
@@ -156,10 +151,10 @@
 	headAngles[YAW] = 180;
 	if( largeFormat ) {
 		CG_DrawHead( headx, y - ( ICON_SIZE - BIGCHAR_HEIGHT ) / 2, ICON_SIZE, ICON_SIZE, 
-					 score->client, headAngles, qtrue, qfalse, qtrue );
+			score->client, headAngles );
 	}
 	else {
-		CG_DrawHead( headx, y, 16, 16, score->client, headAngles, qtrue, qfalse, qtrue );
+		CG_DrawHead( headx, y, 16, 16, score->client, headAngles );
 	}
 
 #ifdef MISSIONPACK
@@ -177,29 +172,14 @@
 	if ( score->ping == -1 ) {
 		Com_sprintf(string, sizeof(string),
 			" connecting    %s", ci->name);
-	//} else if ( ci->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
-	} else if ( score->team == TEAM_SPECTATOR   &&  cg.numScores > 0) {
+	} else if ( ci->team == TEAM_SPECTATOR ) {
 		Com_sprintf(string, sizeof(string),
-			"^3%5i %4i %4i ^7%s", score->score, score->ping, score->time, ci->name);
-	} else if (cg.numScores > 0) {
-#if 1
+			" SPECT %3i %4i %s", score->ping, score->time, ci->name);
+	} else {
 		Com_sprintf(string, sizeof(string),
 			"%5i %4i %4i %s", score->score, score->ping, score->time, ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-			"%5i %4i %4i %i %i %i %i %s %s", score->score, score->ping, score->time, score->alive, score->frags, score->deaths, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-#if 0
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %d %s %s", score->score, score->ping, score->time, score->accuracy, weapNames[score->bestWeapon], ci->name);
-#endif
-	} else if (cg.demoPlayback) {
-		Com_sprintf(string, sizeof(string),
-					"               %s", ci->name);
 	}
 
-	//FIXME wolfcam
 	// highlight your position
 	if ( score->client == cg.snap->ps.clientNum ) {
 		float	hcolor[4];
@@ -207,8 +187,8 @@
 
 		localClient = qtrue;
 
-		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR
-			 || (CG_IsTeamGame(cgs.gametype)  &&  cgs.gametype != GT_RED_ROVER) ) {
+		if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR 
+			|| cgs.gametype >= GT_TEAM ) {
 			rank = -1;
 		} else {
 			rank = cg.snap->ps.persistant[PERS_RANK] & ~RANK_TIED_FLAG;
@@ -244,62 +224,6 @@
 	}
 }
 
-static void CG_DrawClientScoreCpmaMstatsa (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	ds = &cg.duelScores[player];
-
-	// draw the score line
-	if (cg.duelForfeit  &&  player == 1) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
-static void CG_DrawClientScoreQlForfeit (int y, int player, float fade)
-{
-	char	string[1024];
-	const duelScore_t *ds;
-	int forfeitPlayer;
-
-	if (player != 0  &&  player != 1) {
-		Com_Printf("CG_DrawClientScoreCpmaMstatsa():  invalid player %d\n", player);
-		return;
-	}
-
-	// indexed at 1
-	forfeitPlayer = cg.duelPlayerForfeit - 1;
-
-	ds = &cg.duelScores[player];
-
-
-	// draw the score line
-	if (player == forfeitPlayer) {
-		Com_sprintf(string, sizeof(string),
-					"    - %4i %4i %s", ds->ping, ds->time, ds->ci.name);
-
-	} else {
-		Com_sprintf(string, sizeof(string),
-					"%5i %4i %4i %s", ds->score, ds->ping, ds->time, ds->ci.name);
-	}
-
-	CG_DrawBigString( SB_SCORELINE_X + (SB_RATING_WIDTH / 2), y, string, fade );
-}
-
 /*
 =================
 CG_TeamScoreboard
@@ -307,102 +231,15 @@
 */
 static int CG_TeamScoreboard( int y, team_t team, float fade, int maxClients, int lineHeight ) {
 	int		i;
-	const score_t	*score;
+	score_t	*score;
 	float	color[4];
 	int		count;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 
 	color[0] = color[1] = color[2] = 1.0;
 	color[3] = fade;
 
 	count = 0;
-
-	// cpma mstatsa doesn't transmit client numbers
-	if (cgs.cpma  &&  CG_CheckCpmaVersion(1, 50, "")  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreCpmaMstatsa(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cgs.protocolClass == PROTOCOL_QL  &&  CG_IsDuelGame(cgs.gametype)  &&  cg.snap->ps.pm_type == PM_INTERMISSION  &&  cg.duelForfeit) {
-		if (team == TEAM_FREE) {
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 0, fade);
-			count++;
-			CG_DrawClientScoreQlForfeit(y + lineHeight * count, 1, fade);
-			count++;
-
-			return count;
-		} else {  // specs
-			for (i = 0;  i < MAX_CLIENTS;  i++) {
-				score_t sc;
-
-				ci = &cgs.clientinfo[i];
-				if (!ci->infoValid)
-					continue;
-
-				if (team != ci->team)
-					continue;
-
-				memset(&sc, 0, sizeof(sc));
-				sc.client = i;
-				sc.team = ci->team;
-
-				CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-				count++;
-			}
-
-			return count;
-		}
-	}
-
-	if (cg.numScores == 0) {
-		for (i = 0;  i < MAX_CLIENTS;  i++) {
-			score_t sc;
-
-			ci = &cgs.clientinfo[i];
-			if (!ci->infoValid)
-				continue;
-
-			if (team != ci->team)
-				continue;
-
-			memset(&sc, 0, sizeof(sc));
-			sc.client = i;
-			sc.team = ci->team;
-
-			CG_DrawClientScore( y + lineHeight * count, &sc, color, fade, lineHeight == SB_NORMAL_HEIGHT );
-			count++;
-		}
-		return count;
-	}
-
-	count = 0;
-
 	for ( i = 0 ; i < cg.numScores && count < maxClients ; i++ ) {
 		score = &cg.scores[i];
 		ci = &cgs.clientinfo[ score->client ];
@@ -421,7 +258,7 @@
 
 /*
 =================
-CG_DrawOldScoreboard
+CG_DrawScoreboard
 
 Draw the normal in-game scoreboard
 =================
@@ -429,14 +266,12 @@
 qboolean CG_DrawOldScoreboard( void ) {
 	int		x, y, w, i, n1, n2;
 	float	fade;
-	const float	*fadeColor;
-	const char	*s;
+	float	*fadeColor;
+	char	*s;
 	int maxClients;
 	int lineHeight;
 	int topBorderSize, bottomBorderSize;
 
-	QLWideScreen = WIDESCREEN_CENTER;
-
 	// don't draw amuthing if the menu or console is up
 	if ( cg_paused.integer ) {
 		cg.deferredPlayerLoading = 0;
@@ -459,7 +294,7 @@
 		fadeColor = colorWhite;
 	} else {
 		fadeColor = CG_FadeColor( cg.scoreFadeTime, FADE_TIME );
-
+		
 		if ( !fadeColor ) {
 			// next time scoreboard comes up, don't print killer
 			cg.deferredPlayerLoading = 0;
@@ -473,75 +308,22 @@
 	// fragged by ... line
 	if ( cg.killerName[0] ) {
 		s = va("Fragged by %s", cg.killerName );
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 40;
 		CG_DrawBigString( x, y, s, fade );
 	}
 
 	// current rank
-	if (!CG_IsTeamGame(cgs.gametype)) {
-		if (!wolfcam_following  ||  (wolfcam_following  &&  wcg.clientNum == cg.snap->ps.clientNum)) {
-			if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
-				s = va("%s place with %i",
-					   CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
-					   cg.snap->ps.persistant[PERS_SCORE] );
-				w = CG_DrawStrlen( s, &cgs.media.bigchar );
-				x = ( SCREEN_WIDTH - w ) / 2;
-				y = 60;
-				CG_DrawBigString( x, y, s, fade );
-			}
-		} else {  // wolfcam_following
-			if (cgs.clientinfo[wcg.clientNum].team != TEAM_SPECTATOR) {
-				if (CG_IsCpmaMvd()) {
-					int rank;
-					int j;
-
-					rank = 1;
-					for (j = 0;  j < MAX_CLIENTS;  j++) {
-						if (!cgs.clientinfo[j].infoValid) {
-							continue;
-						}
-						if (cgs.clientinfo[j].team == TEAM_SPECTATOR) {
-							continue;
-						}
-						if (cgs.clientinfo[j].score > cgs.clientinfo[wcg.clientNum].score) {
-							rank++;
-						}
-					}
-
-					s = va("%s ^7place with %i", CG_PlaceString(rank), cgs.clientinfo[wcg.clientNum].score);
-
-					w = CG_DrawStrlen( s, &cgs.media.bigchar );
-					x = ( SCREEN_WIDTH - w ) / 2;
-					y = 60;
-					CG_DrawBigString( x, y, s, fade );
-				} else {  // not cpma mvd
-					// following someone who is ingame but not the main demo view
-
-					if (CG_IsDuelGame(cgs.gametype)) {
-						// we are following the other dueler
-						if (cgs.scores1 == cgs.scores2) {
-							s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-						} else {
-							if (cg.snap->ps.persistant[PERS_RANK] == 0) {
-								// we are second
-								s = va("%s ^7place with %i", CG_PlaceString(2), cgs.scores2);
-							} else {
-								// we are first
-								s = va("%s ^7place with %i", CG_PlaceString(1), cgs.scores1);
-							}
-						}
-						w = CG_DrawStrlen( s, &cgs.media.bigchar );
-						x = ( SCREEN_WIDTH - w ) / 2;
-						y = 60;
-						CG_DrawBigString( x, y, s, fade );
-					} else {
-						// we don't have enough information
-						// pass, don't draw ranking
-					}
-				}
-			}
+	if ( cgs.gametype < GT_TEAM) {
+		if (cg.snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR ) {
+			s = va("%s place with %i",
+				CG_PlaceString( cg.snap->ps.persistant[PERS_RANK] + 1 ),
+				cg.snap->ps.persistant[PERS_SCORE] );
+			w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
+			x = ( SCREEN_WIDTH - w ) / 2;
+			y = 60;
+			CG_DrawBigString( x, y, s, fade );
 		}
 	} else {
 		if ( cg.teamScores[0] == cg.teamScores[1] ) {
@@ -552,7 +334,7 @@
 			s = va("Blue leads %i to %i",cg.teamScores[1], cg.teamScores[0] );
 		}
 
-		w = CG_DrawStrlen( s, &cgs.media.bigchar );
+		w = CG_DrawStrlen( s ) * BIGCHAR_WIDTH;
 		x = ( SCREEN_WIDTH - w ) / 2;
 		y = 60;
 		CG_DrawBigString( x, y, s, fade );
@@ -569,7 +351,7 @@
 	y = SB_TOP;
 
 	// If there are more than SB_MAXCLIENTS_NORMAL, use the interleaved scores
-	if (1) {  //( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
+	if ( cg.numScores > SB_MAXCLIENTS_NORMAL ) {
 		maxClients = SB_MAXCLIENTS_INTER;
 		lineHeight = SB_INTER_HEIGHT;
 		topBorderSize = 8;
@@ -583,7 +365,7 @@
 
 	localClient = qfalse;
 
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
@@ -655,9 +437,9 @@
 	color[2] = 1;
 	color[3] = 1;
 
-	x = 0.5 * ( 640 - CG_DrawStrlen( string, &cgs.media.giantchar ) );
+	x = 0.5 * ( 640 - GIANT_WIDTH * CG_DrawStrlen( string ) );
 
-	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+	CG_DrawStringExt( x, y, string, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 }
 
 /*
@@ -667,11 +449,11 @@
 Draw the oversize scoreboard for tournements
 =================
 */
-void CG_DrawTourneyScoreboard( void ) {
+void CG_DrawOldTourneyScoreboard( void ) {
 	const char		*s;
 	vec4_t			color;
 	int				min, tens, ones;
-	const clientInfo_t	*ci;
+	clientInfo_t	*ci;
 	int				y;
 	int				i;
 
@@ -714,19 +496,19 @@
 	// print the two scores
 
 	y = 160;
-	if ( CG_IsTeamGame(cgs.gametype) ) {
+	if ( cgs.gametype >= GT_TEAM ) {
 		//
 		// teamplay scoreboard
 		//
-		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Red Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[0] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		
 		y += 64;
 
-		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 8, y, "Blue Team", color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 		s = va("%i", cg.teamScores[1] );
-		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+		CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 	} else {
 		//
 		// free for all scoreboard
@@ -740,10 +522,13 @@
 				continue;
 			}
 
-			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 8, y, ci->name, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			s = va("%i", ci->score );
-			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0, &cgs.media.giantchar );
+			CG_DrawStringExt( 632 - GIANT_WIDTH * strlen(s), y, s, color, qtrue, qtrue, GIANT_WIDTH, GIANT_HEIGHT, 0 );
 			y += 64;
 		}
 	}
+
+
 }
+

```

### `openarena-gamecode`  — sha256 `e93edeb33eb9...`, 15976 bytes

_Diff stat: +243 / -448 lines_

_(full diff is 32409 bytes — see files directly)_
