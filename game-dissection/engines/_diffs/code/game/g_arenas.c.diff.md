# Diff: `code/game/g_arenas.c`
**Canonical:** `wolfcamql-src` (sha256 `2415b9a6b285...`, 11701 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `527f789663bd...`, 11720 bytes

_Diff stat: +5 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_arenas.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_arenas.c	2026-04-16 20:02:19.904124600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -42,7 +42,8 @@
 	gentity_t	*player;
 	int			playerClientNum;
 	int			n, accuracy, perfect,	msglen;
-#ifdef MISSIONPACK
+	int			buflen;
+#ifdef MISSIONPACK // bk001205
   int score1, score2;
 	qboolean won;
 #endif
@@ -125,8 +126,8 @@
 	for( i = 0; i < level.numNonSpectatorClients; i++ ) {
 		n = level.sortedClients[i];
 		Com_sprintf( buf, sizeof(buf), " %i %i %i", n, level.clients[n].ps.persistant[PERS_RANK], level.clients[n].ps.persistant[PERS_SCORE] );
-		msglen += strlen( buf );
-		if( msglen >= sizeof(msg) ) {
+		buflen = strlen( buf );
+		if( msglen + buflen + 1 >= sizeof(msg) ) {
 			break;
 		}
 		strcat( msg, buf );

```

### `openarena-gamecode`  — sha256 `4df3bbbc4b90...`, 11744 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_arenas.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_arenas.c	2026-04-16 22:48:24.167478300 +0100
@@ -42,7 +42,7 @@
 	gentity_t	*player;
 	int			playerClientNum;
 	int			n, accuracy, perfect,	msglen;
-#ifdef MISSIONPACK
+#ifdef MISSIONPACK // bk001205
   int score1, score2;
 	qboolean won;
 #endif
@@ -84,7 +84,7 @@
 		}
 #ifdef MISSIONPACK
 		won = qfalse;
-		if (g_gametype.integer >= GT_CTF) {
+		if (g_gametype.integer >= GT_CTF && g_ffa_gt==0) {
 			score1 = level.teamScores[TEAM_RED];
 			score2 = level.teamScores[TEAM_BLUE];
 			if (level.clients[playerClientNum].sess.sessionTeam	== TEAM_RED) {
@@ -127,6 +127,7 @@
 		Com_sprintf( buf, sizeof(buf), " %i %i %i", n, level.clients[n].ps.persistant[PERS_RANK], level.clients[n].ps.persistant[PERS_SCORE] );
 		msglen += strlen( buf );
 		if( msglen >= sizeof(msg) ) {
+
 			break;
 		}
 		strcat( msg, buf );
@@ -142,7 +143,7 @@
 
 	body = G_Spawn();
 	if ( !body ) {
-		G_Printf( S_COLOR_RED "ERROR: out of gentities\n" );
+                G_Printf( S_COLOR_RED "ERROR: out of gentities\n" );
 		return NULL;
 	}
 

```
