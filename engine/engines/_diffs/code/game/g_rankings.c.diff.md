# Diff: `code/game/g_rankings.c`
**Canonical:** `wolfcamql-src` (sha256 `ffa6e41c8d48...`, 28142 bytes)

## Variants

### `quake3-source`  — sha256 `b89112e3f833...`, 28036 bytes

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.c	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_rankings.c	2026-04-16 20:02:19.908574000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -131,9 +131,6 @@
 						// send current scores so the player's rank will show 
 						// up under the crosshair immediately
 						DeathmatchScoreboardMessage( ent2 );
-						if (g_gametype.integer == GT_TOURNAMENT) {
-							DuelScores(ent2);
-						}
 					}
 				}
 				break;

```

### `openarena-engine`  — sha256 `2d69a5ec7683...`, 28057 bytes
Also identical in: ioquake3

_Diff stat: +0 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.c	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_rankings.c	2026-04-16 22:48:25.750042300 +0100
@@ -131,9 +131,6 @@
 						// send current scores so the player's rank will show 
 						// up under the crosshair immediately
 						DeathmatchScoreboardMessage( ent2 );
-						if (g_gametype.integer == GT_TOURNAMENT) {
-							DuelScores(ent2);
-						}
 					}
 				}
 				break;

```

### `openarena-gamecode`  — sha256 `abf4c8842d47...`, 28083 bytes

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.c	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_rankings.c	2026-04-16 22:48:24.173988500 +0100
@@ -104,7 +104,7 @@
 				}
 				break;
 			case QGR_STATUS_ACTIVE:
-				if( (ent->client->sess.sessionTeam == TEAM_SPECTATOR) &&
+				if( (ent->client->sess.sessionTeam == TEAM_SPECTATOR || (client->isEliminated)) &&
 					(g_gametype.integer < GT_TEAM) )
 				{
 					SetTeam( ent, "free" );
@@ -131,9 +131,6 @@
 						// send current scores so the player's rank will show 
 						// up under the crosshair immediately
 						DeathmatchScoreboardMessage( ent2 );
-						if (g_gametype.integer == GT_TOURNAMENT) {
-							DuelScores(ent2);
-						}
 					}
 				}
 				break;

```
