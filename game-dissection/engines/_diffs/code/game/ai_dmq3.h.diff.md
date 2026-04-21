# Diff: `code/game/ai_dmq3.h`
**Canonical:** `wolfcamql-src` (sha256 `e7732376e921...`, 8538 bytes)

## Variants

### `quake3-source`  — sha256 `1c9a877cb1d1...`, 8518 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmq3.h	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_dmq3.h	2026-04-16 20:02:19.898125000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -34,7 +34,7 @@
 void BotSetupDeathmatchAI(void);
 //shutdown the deathmatch AI
 void BotShutdownDeathmatchAI(void);
-//let the bot live within its deathmatch AI net
+//let the bot live within it's deathmatch AI net
 void BotDeathmatchAI(bot_state_t *bs, float thinktime);
 //free waypoints
 void BotFreeWaypoints(bot_waypoint_t *wp);
@@ -62,7 +62,7 @@
 qboolean EntityIsInvisible(aas_entityinfo_t *entinfo);
 //returns true if the entity is shooting
 qboolean EntityIsShooting(aas_entityinfo_t *entinfo);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 //returns true if this entity has the kamikaze
 qboolean EntityHasKamikaze(aas_entityinfo_t *entinfo);
 #endif
@@ -72,7 +72,7 @@
 void BotSetTeamStatus(bot_state_t *bs);
 //returns the name of the client
 char *ClientName(int client, char *name, int size);
-//returns a simplified client name
+//returns an simplyfied client name
 char *EasyClientName(int client, char *name, int size);
 //returns the skin used by the client
 char *ClientSkin(int client, char *skin, int size);
@@ -136,7 +136,7 @@
 void BotClearActivateGoalStack(bot_state_t *bs);
 //returns the team the bot is in
 int BotTeam(bot_state_t *bs);
-//returns the opposite team of the bot
+//retuns the opposite team of the bot
 int BotOppositeTeam(bot_state_t *bs);
 //returns the flag the bot is carrying (CTFFLAG_?)
 int BotCTFCarryingFlag(bot_state_t *bs);
@@ -147,7 +147,7 @@
 //set ctf goals (defend base, get enemy flag) during retreat
 void BotCTFRetreatGoals(bot_state_t *bs);
 //
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Bot1FCTFCarryingFlag(bot_state_t *bs);
 int BotHarvesterCarryingCubes(bot_state_t *bs);
 void Bot1FCTFSeekGoals(bot_state_t *bs);
@@ -198,7 +198,7 @@
 
 extern bot_goal_t ctf_redflag;
 extern bot_goal_t ctf_blueflag;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 extern bot_goal_t ctf_neutralflag;
 extern bot_goal_t redobelisk;
 extern bot_goal_t blueobelisk;

```

### `ioquake3`  — sha256 `46fa726eb21d...`, 8538 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmq3.h	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_dmq3.h	2026-04-16 20:02:21.537886300 +0100
@@ -62,7 +62,7 @@
 qboolean EntityIsInvisible(aas_entityinfo_t *entinfo);
 //returns true if the entity is shooting
 qboolean EntityIsShooting(aas_entityinfo_t *entinfo);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 //returns true if this entity has the kamikaze
 qboolean EntityHasKamikaze(aas_entityinfo_t *entinfo);
 #endif
@@ -147,7 +147,7 @@
 //set ctf goals (defend base, get enemy flag) during retreat
 void BotCTFRetreatGoals(bot_state_t *bs);
 //
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Bot1FCTFCarryingFlag(bot_state_t *bs);
 int BotHarvesterCarryingCubes(bot_state_t *bs);
 void Bot1FCTFSeekGoals(bot_state_t *bs);
@@ -198,7 +198,7 @@
 
 extern bot_goal_t ctf_redflag;
 extern bot_goal_t ctf_blueflag;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 extern bot_goal_t ctf_neutralflag;
 extern bot_goal_t redobelisk;
 extern bot_goal_t blueobelisk;

```

### `openarena-engine`  — sha256 `bb141f7750da...`, 8537 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmq3.h	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_dmq3.h	2026-04-16 22:48:25.741537100 +0100
@@ -62,7 +62,7 @@
 qboolean EntityIsInvisible(aas_entityinfo_t *entinfo);
 //returns true if the entity is shooting
 qboolean EntityIsShooting(aas_entityinfo_t *entinfo);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 //returns true if this entity has the kamikaze
 qboolean EntityHasKamikaze(aas_entityinfo_t *entinfo);
 #endif
@@ -136,7 +136,7 @@
 void BotClearActivateGoalStack(bot_state_t *bs);
 //returns the team the bot is in
 int BotTeam(bot_state_t *bs);
-//returns the opposite team of the bot
+//retuns the opposite team of the bot
 int BotOppositeTeam(bot_state_t *bs);
 //returns the flag the bot is carrying (CTFFLAG_?)
 int BotCTFCarryingFlag(bot_state_t *bs);
@@ -147,7 +147,7 @@
 //set ctf goals (defend base, get enemy flag) during retreat
 void BotCTFRetreatGoals(bot_state_t *bs);
 //
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Bot1FCTFCarryingFlag(bot_state_t *bs);
 int BotHarvesterCarryingCubes(bot_state_t *bs);
 void Bot1FCTFSeekGoals(bot_state_t *bs);
@@ -198,7 +198,7 @@
 
 extern bot_goal_t ctf_redflag;
 extern bot_goal_t ctf_blueflag;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 extern bot_goal_t ctf_neutralflag;
 extern bot_goal_t redobelisk;
 extern bot_goal_t blueobelisk;

```

### `openarena-gamecode`  — sha256 `b9912a750211...`, 8455 bytes

_Diff stat: +3 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmq3.h	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_dmq3.h	2026-04-16 22:48:24.160331200 +0100
@@ -34,7 +34,7 @@
 void BotSetupDeathmatchAI(void);
 //shutdown the deathmatch AI
 void BotShutdownDeathmatchAI(void);
-//let the bot live within its deathmatch AI net
+//let the bot live within it's deathmatch AI net
 void BotDeathmatchAI(bot_state_t *bs, float thinktime);
 //free waypoints
 void BotFreeWaypoints(bot_waypoint_t *wp);
@@ -62,17 +62,15 @@
 qboolean EntityIsInvisible(aas_entityinfo_t *entinfo);
 //returns true if the entity is shooting
 qboolean EntityIsShooting(aas_entityinfo_t *entinfo);
-#if 1  //def MPACK
 //returns true if this entity has the kamikaze
 qboolean EntityHasKamikaze(aas_entityinfo_t *entinfo);
-#endif
 // set a user info key/value pair
 void BotSetUserInfo(bot_state_t *bs, char *key, char *value);
 // set the team status (offense, defense etc.)
 void BotSetTeamStatus(bot_state_t *bs);
 //returns the name of the client
 char *ClientName(int client, char *name, int size);
-//returns a simplified client name
+//returns an simplyfied client name
 char *EasyClientName(int client, char *name, int size);
 //returns the skin used by the client
 char *ClientSkin(int client, char *skin, int size);
@@ -136,7 +134,7 @@
 void BotClearActivateGoalStack(bot_state_t *bs);
 //returns the team the bot is in
 int BotTeam(bot_state_t *bs);
-//returns the opposite team of the bot
+//retuns the opposite team of the bot
 int BotOppositeTeam(bot_state_t *bs);
 //returns the flag the bot is carrying (CTFFLAG_?)
 int BotCTFCarryingFlag(bot_state_t *bs);
@@ -147,7 +145,6 @@
 //set ctf goals (defend base, get enemy flag) during retreat
 void BotCTFRetreatGoals(bot_state_t *bs);
 //
-#if 1  //def MPACK
 int Bot1FCTFCarryingFlag(bot_state_t *bs);
 int BotHarvesterCarryingCubes(bot_state_t *bs);
 void Bot1FCTFSeekGoals(bot_state_t *bs);
@@ -159,7 +156,6 @@
 void BotHarvesterRetreatGoals(bot_state_t *bs);
 int BotTeamCubeCarrierVisible(bot_state_t *bs);
 int BotEnemyCubeCarrierVisible(bot_state_t *bs);
-#endif
 //get a random alternate route goal towards the given base
 int BotGetAlternateRouteGoal(bot_state_t *bs, int base);
 //returns either the alternate route goal or the given goal
@@ -198,9 +194,7 @@
 
 extern bot_goal_t ctf_redflag;
 extern bot_goal_t ctf_blueflag;
-#if 1  //def MPACK
 extern bot_goal_t ctf_neutralflag;
 extern bot_goal_t redobelisk;
 extern bot_goal_t blueobelisk;
 extern bot_goal_t neutralobelisk;
-#endif

```
