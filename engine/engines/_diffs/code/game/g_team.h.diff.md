# Diff: `code/game/g_team.h`
**Canonical:** `wolfcamql-src` (sha256 `2328ca6d9fbf...`, 4499 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `78e3828ab662...`, 4500 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_team.h	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_team.h	2026-04-16 20:02:19.911076800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -69,6 +69,7 @@
 
 int OtherTeam(int team);
 const char *TeamName(int team);
+const char *OtherTeamName(int team);
 const char *TeamColorString(int team);
 void AddTeamScore(vec3_t origin, int team, int score);
 
@@ -78,7 +79,7 @@
 void Team_InitGame(void);
 void Team_ReturnFlag(int team);
 void Team_FreeEntity(gentity_t *ent);
-gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles, qboolean isbot );
+gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles );
 gentity_t *Team_GetLocation(gentity_t *ent);
 qboolean Team_GetLocationMsg(gentity_t *ent, char *loc, int loclen);
 void TeamplayInfoMessage( gentity_t *ent );

```

### `openarena-gamecode`  — sha256 `25eaf7b49d8e...`, 6362 bytes

_Diff stat: +42 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_team.h	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_team.h	2026-04-16 22:48:24.176987600 +0100
@@ -53,6 +53,32 @@
 
 #endif
 
+#ifdef MISSIONPACK
+
+//For Double Domination:
+#define DD_POINT_DEFENCE_BONUS			10	//Score for fragging someone while either you or target are near a Domination Point
+#define DD_POINT_DEFENCE_CLOSE_BONUS		25	//Score for fragging someone while either you or target are near a Domination Point and have almost scored
+//Following is added togehter:
+#define DD_POINT_CAPTURE			5	//Score for taking a point
+#define DD_POINT_CAPTURE_BREAK			10	//If the enemy was dominating
+#define DD_POINT_CAPTURE_CLOSE			15	//Extra score if the enemy was about to score
+#define DD_AT_POINT_AT_CAPTURE			30	//You was close to a point as capture succeded.	
+
+#else
+
+//For Double Domination:
+#define DD_POINT_DEFENCE_BONUS			1	//Score for fragging someone while either you or target are near a Domination Point
+#define DD_POINT_DEFENCE_CLOSE_BONUS		2	//Score for fragging someone while either you or target are near a Domination Point and have almost scored
+//Following is added togehter:
+#define DD_POINT_CAPTURE			1	//Score for taking a point
+#define DD_POINT_CAPTURE_BREAK			1	//If the enemy was dominating
+#define DD_POINT_CAPTURE_CLOSE			1	//Extra score if the enemy was about to score
+#define DD_AT_POINT_AT_CAPTURE			1	//You was close to a point as capture succeded.	
+
+#endif
+
+#define DD_CLOSE				3	//How many seconds to score is close		
+
 #define CTF_TARGET_PROTECT_RADIUS			1000	// the radius around an object being defended where a target will be worth extra frags
 #define CTF_ATTACKER_PROTECT_RADIUS			1000	// the radius around an object being defended where an attacker will get extra frags when making kills
 
@@ -69,6 +95,7 @@
 
 int OtherTeam(int team);
 const char *TeamName(int team);
+const char *OtherTeamName(int team);
 const char *TeamColorString(int team);
 void AddTeamScore(vec3_t origin, int team, int score);
 
@@ -78,10 +105,24 @@
 void Team_InitGame(void);
 void Team_ReturnFlag(int team);
 void Team_FreeEntity(gentity_t *ent);
-gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles, qboolean isbot );
+gentity_t *SelectCTFSpawnPoint ( team_t team, int teamstate, vec3_t origin, vec3_t angles );
+//For Double_D
+gentity_t *SelectDoubleDominationSpawnPoint ( team_t, vec3_t origin, vec3_t angles );
+//For Standard D
+gentity_t *SelectDominationSpawnPoint ( team_t, vec3_t origin, vec3_t angles );
+void Team_Dom_SpawnPoints( void );
 gentity_t *Team_GetLocation(gentity_t *ent);
 qboolean Team_GetLocationMsg(gentity_t *ent, char *loc, int loclen);
 void TeamplayInfoMessage( gentity_t *ent );
 void CheckTeamStatus(void);
 
 int Pickup_Team( gentity_t *ent, gentity_t *other );
+
+//Double Domination:
+int Team_SpawnDoubleDominationPoints ( void );
+int Team_RemoveDoubleDominationPoints ( void );
+void Team_DD_bonusAtPoints(int team);
+
+//Added to make gcc happy (and because I use it in main)
+void Team_ForceGesture(int team);
+

```
