# Diff: `code/game/ai_team.c`
**Canonical:** `wolfcamql-src` (sha256 `7787bd2a8e44...`, 68668 bytes)

## Variants

### `quake3-source`  — sha256 `9cfbd914ae5a...`, 68814 bytes

_Diff stat: +63 / -53 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_team.c	2026-04-16 20:02:25.184520700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_team.c	2026-04-16 20:02:19.900127000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -31,15 +31,15 @@
  *****************************************************************************/
 
 #include "g_local.h"
-#include "../botlib/botlib.h"
-#include "../botlib/be_aas.h"
-#include "../botlib/be_ea.h"
-#include "../botlib/be_ai_char.h"
-#include "../botlib/be_ai_chat.h"
-#include "../botlib/be_ai_gen.h"
-#include "../botlib/be_ai_goal.h"
-#include "../botlib/be_ai_move.h"
-#include "../botlib/be_ai_weap.h"
+#include "botlib.h"
+#include "be_aas.h"
+#include "be_ea.h"
+#include "be_ai_char.h"
+#include "be_ai_chat.h"
+#include "be_ai_gen.h"
+#include "be_ai_goal.h"
+#include "be_ai_move.h"
+#include "be_ai_weap.h"
 //
 #include "ai_main.h"
 #include "ai_dmq3.h"
@@ -83,9 +83,13 @@
 int BotNumTeamMates(bot_state_t *bs) {
 	int i, numplayers;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	numplayers = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -108,12 +112,8 @@
 	playerState_t ps;
 	int areanum;
 
-	if (BotAI_GetClientState(client, &ps)) {
-		areanum = BotPointAreaNum(ps.origin);
-	} else {
-		areanum = 0;
-	}
-
+	BotAI_GetClientState(client, &ps);
+	areanum = BotPointAreaNum(ps.origin);
 	if (!areanum) return 1;
 	return trap_AAS_AreaTravelTimeToGoalArea(areanum, ps.origin, goal->areanum, TFL_DEFAULT);
 }
@@ -127,21 +127,17 @@
 
 	int i, j, k, numteammates, traveltime;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	int traveltimes[MAX_CLIENTS];
 	bot_goal_t *goal = NULL;
 
-#if 1  //def MPACK
-	if (gametype == GT_CTF || gametype == GT_1FCTF)
-#else
-	if (gametype == GT_CTF)
-#endif
-	{
+	if (gametype == GT_CTF || gametype == GT_1FCTF) {
 		if (BotTeam(bs) == TEAM_RED)
 			goal = &ctf_redflag;
 		else
 			goal = &ctf_blueflag;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else {
 		if (BotTeam(bs) == TEAM_RED)
 			goal = &redobelisk;
@@ -149,15 +145,18 @@
 			goal = &blueobelisk;
 	}
 #endif
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	numteammates = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotSameTeam(bs, i) && goal) {
+		if (BotSameTeam(bs, i)) {
 			//
 			traveltime = BotClientTravelTimeToGoal(i, goal);
 			//
@@ -273,7 +272,7 @@
 ==================
 */
 void BotSayTeamOrder(bot_state_t *bs, int toclient) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// voice chats only
 	char buf[MAX_MESSAGE_SIZE];
 
@@ -289,7 +288,7 @@
 ==================
 */
 void BotVoiceChat(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vsay_team %s", voicechat));
@@ -305,7 +304,7 @@
 ==================
 */
 void BotVoiceChatOnly(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vosay_team %s", voicechat));
@@ -321,7 +320,7 @@
 ==================
 */
 void BotSayVoiceTeamOrder(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	BotVoiceChat(bs, toclient, voicechat);
 #endif
 }
@@ -333,7 +332,7 @@
 */
 void BotCTFOrders_BothFlagsNotAtBase(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i, other;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME], carriername[MAX_NETNAME];
 
 	numteammates = BotSortTeamMatesByBaseTravelTime(bs, teammates, sizeof(teammates));
@@ -459,11 +458,11 @@
 			case 1: break;
 			case 2:
 			{
-				// keep one near the base for when the flag is returned
+				//both will go for the enemy flag
 				ClientName(teammates[0], name, sizeof(name));
 				BotAI_BotInitialChat(bs, "cmd_defendbase", name, NULL);
 				BotSayTeamOrder(bs, teammates[0]);
-				BotSayVoiceTeamOrder(bs, teammates[0], VOICECHAT_DEFEND);
+				BotSayVoiceTeamOrder(bs, teammates[0], VOICECHAT_GETFLAG);
 				//
 				ClientName(teammates[1], name, sizeof(name));
 				BotAI_BotInitialChat(bs, "cmd_getflag", name, NULL);
@@ -495,7 +494,7 @@
 				//keep some people near the base for when the flag is returned
 				defenders = (int) (float) numteammates * 0.3 + 0.5;
 				if (defenders > 3) defenders = 3;
-				attackers = (int) (float) numteammates * 0.6 + 0.5;
+				attackers = (int) (float) numteammates * 0.7 + 0.5;
 				if (attackers > 6) attackers = 6;
 				for (i = 0; i < defenders; i++) {
 					//
@@ -538,7 +537,7 @@
 			{
 				//everyone go for the flag
 				ClientName(teammates[0], name, sizeof(name));
-				BotAI_BotInitialChat(bs, "cmd_getflag", name, NULL);
+				BotAI_BotInitialChat(bs, "cmd_defendbase", name, NULL);
 				BotSayTeamOrder(bs, teammates[0]);
 				BotSayVoiceTeamOrder(bs, teammates[0], VOICECHAT_GETFLAG);
 				//
@@ -691,7 +690,7 @@
 */
 void BotCTFOrders_BothFlagsAtBase(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME];
 
 	//sort team mates by travel time to base
@@ -881,9 +880,13 @@
 	int teammates[MAX_CLIENTS];
 	int numteammates, i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	numteammates = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -933,7 +936,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ==================
@@ -1016,7 +1019,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1202,7 +1205,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1346,7 +1349,7 @@
 				if (defenders > 8) defenders = 8;
 				//10% will try to return the flag
 				attackers = (int) (float) numteammates * 0.1 + 0.5;
-				if (attackers > 1) attackers = 1;
+				if (attackers > 2) attackers = 2;
 				for (i = 0; i < defenders; i++) {
 					//
 					ClientName(teammates[i], name, sizeof(name));
@@ -1366,7 +1369,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1407,7 +1410,7 @@
 			{
 				//70% defend the base
 				defenders = (int) (float) numteammates * 0.7 + 0.5;
-				if (defenders > 7) defenders = 7;
+				if (defenders > 8) defenders = 8;
 				//20% try to return the flag
 				attackers = (int) (float) numteammates * 0.2 + 0.5;
 				if (attackers > 2) attackers = 2;
@@ -1513,7 +1516,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1570,7 +1573,7 @@
 					ClientName(teammates[numteammates - i - 1], name, sizeof(name));
 					BotAI_BotInitialChat(bs, "cmd_getflag", name, NULL);
 					BotSayTeamOrder(bs, teammates[numteammates - i - 1]);
-					BotSayVoiceTeamOrder(bs, teammates[numteammates - i - 1], VOICECHAT_GETFLAG);
+					BotSayVoiceTeamOrder(bs, teammates[numteammates - i - 1], VOICECHAT_DEFEND);
 				}
 				//
 				break;
@@ -1749,7 +1752,7 @@
 */
 void BotHarvesterOrders(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME];
 
 	//sort team mates by travel time to base
@@ -1956,7 +1959,8 @@
 				trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
 				BotSayVoiceTeamOrder(bs, -1, VOICECHAT_STARTLEADER);
 				ClientName(bs->client, netname, sizeof(netname));
-				Q_strncpyz(bs->teamleader, netname, sizeof(bs->teamleader));
+				strncpy(bs->teamleader, netname, sizeof(bs->teamleader));
+				bs->teamleader[sizeof(bs->teamleader)] = '\0';
 				bs->becometeamleader_time = 0;
 			}
 			return;
@@ -1971,7 +1975,8 @@
 	//
 	numteammates = BotNumTeamMates(bs);
 	//give orders
-	if (gametype == GT_TEAM) {
+	switch(gametype) {
+		case GT_TEAM:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -1984,8 +1989,9 @@
 				//give orders again after 120 seconds
 				bs->teamgiveorders_time = FloatTime() + 120;
 			}
+			break;
 		}
-	} else if (gametype == GT_CTF) {
+		case GT_CTF:
 		{
 			//if the number of team mates changed or the flag status changed
 			//or someone wants to know what to do
@@ -2010,9 +2016,10 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-#if 1  //def MPACK
-	} else if (gametype == GT_1FCTF) {
+#ifdef MISSIONPACK
+		case GT_1FCTF:
 		{
 			if (bs->numteammates != numteammates || bs->flagstatuschanged || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2035,8 +2042,9 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-	} else if (gametype == GT_OBELISK) {
+		case GT_OBELISK:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2049,8 +2057,9 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
-	} else if (gametype == GT_HARVESTER) {
+		case GT_HARVESTER:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2063,6 +2072,7 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
 #endif
 	}

```

### `ioquake3`  — sha256 `e98f460c1ab0...`, 68656 bytes

_Diff stat: +19 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_team.c	2026-04-16 20:02:25.184520700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_team.c	2026-04-16 20:02:21.538886200 +0100
@@ -130,7 +130,7 @@
 	int traveltimes[MAX_CLIENTS];
 	bot_goal_t *goal = NULL;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (gametype == GT_CTF || gametype == GT_1FCTF)
 #else
 	if (gametype == GT_CTF)
@@ -141,7 +141,7 @@
 		else
 			goal = &ctf_blueflag;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else {
 		if (BotTeam(bs) == TEAM_RED)
 			goal = &redobelisk;
@@ -273,7 +273,7 @@
 ==================
 */
 void BotSayTeamOrder(bot_state_t *bs, int toclient) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// voice chats only
 	char buf[MAX_MESSAGE_SIZE];
 
@@ -289,7 +289,7 @@
 ==================
 */
 void BotVoiceChat(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vsay_team %s", voicechat));
@@ -305,7 +305,7 @@
 ==================
 */
 void BotVoiceChatOnly(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vosay_team %s", voicechat));
@@ -321,7 +321,7 @@
 ==================
 */
 void BotSayVoiceTeamOrder(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	BotVoiceChat(bs, toclient, voicechat);
 #endif
 }
@@ -933,7 +933,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ==================
@@ -1971,7 +1971,8 @@
 	//
 	numteammates = BotNumTeamMates(bs);
 	//give orders
-	if (gametype == GT_TEAM) {
+	switch(gametype) {
+		case GT_TEAM:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -1984,8 +1985,9 @@
 				//give orders again after 120 seconds
 				bs->teamgiveorders_time = FloatTime() + 120;
 			}
+			break;
 		}
-	} else if (gametype == GT_CTF) {
+		case GT_CTF:
 		{
 			//if the number of team mates changed or the flag status changed
 			//or someone wants to know what to do
@@ -2010,9 +2012,10 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-#if 1  //def MPACK
-	} else if (gametype == GT_1FCTF) {
+#ifdef MISSIONPACK
+		case GT_1FCTF:
 		{
 			if (bs->numteammates != numteammates || bs->flagstatuschanged || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2035,8 +2038,9 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-	} else if (gametype == GT_OBELISK) {
+		case GT_OBELISK:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2049,8 +2053,9 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
-	} else if (gametype == GT_HARVESTER) {
+		case GT_HARVESTER:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2063,6 +2068,7 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
 #endif
 	}

```

### `openarena-engine`  — sha256 `d0fd2f58e9fe...`, 69009 bytes

_Diff stat: +46 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_team.c	2026-04-16 20:02:25.184520700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_team.c	2026-04-16 22:48:25.742535200 +0100
@@ -83,9 +83,13 @@
 int BotNumTeamMates(bot_state_t *bs) {
 	int i, numplayers;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	numplayers = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -108,12 +112,8 @@
 	playerState_t ps;
 	int areanum;
 
-	if (BotAI_GetClientState(client, &ps)) {
-		areanum = BotPointAreaNum(ps.origin);
-	} else {
-		areanum = 0;
-	}
-
+	BotAI_GetClientState(client, &ps);
+	areanum = BotPointAreaNum(ps.origin);
 	if (!areanum) return 1;
 	return trap_AAS_AreaTravelTimeToGoalArea(areanum, ps.origin, goal->areanum, TFL_DEFAULT);
 }
@@ -127,10 +127,11 @@
 
 	int i, j, k, numteammates, traveltime;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	int traveltimes[MAX_CLIENTS];
 	bot_goal_t *goal = NULL;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (gametype == GT_CTF || gametype == GT_1FCTF)
 #else
 	if (gametype == GT_CTF)
@@ -141,7 +142,7 @@
 		else
 			goal = &ctf_blueflag;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else {
 		if (BotTeam(bs) == TEAM_RED)
 			goal = &redobelisk;
@@ -149,15 +150,18 @@
 			goal = &blueobelisk;
 	}
 #endif
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	numteammates = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotSameTeam(bs, i) && goal) {
+		if (BotSameTeam(bs, i)) {
 			//
 			traveltime = BotClientTravelTimeToGoal(i, goal);
 			//
@@ -273,7 +277,7 @@
 ==================
 */
 void BotSayTeamOrder(bot_state_t *bs, int toclient) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// voice chats only
 	char buf[MAX_MESSAGE_SIZE];
 
@@ -289,7 +293,7 @@
 ==================
 */
 void BotVoiceChat(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vsay_team %s", voicechat));
@@ -305,7 +309,7 @@
 ==================
 */
 void BotVoiceChatOnly(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (toclient == -1)
 		// voice only say team
 		trap_EA_Command(bs->client, va("vosay_team %s", voicechat));
@@ -321,7 +325,7 @@
 ==================
 */
 void BotSayVoiceTeamOrder(bot_state_t *bs, int toclient, char *voicechat) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	BotVoiceChat(bs, toclient, voicechat);
 #endif
 }
@@ -333,7 +337,7 @@
 */
 void BotCTFOrders_BothFlagsNotAtBase(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i, other;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME], carriername[MAX_NETNAME];
 
 	numteammates = BotSortTeamMatesByBaseTravelTime(bs, teammates, sizeof(teammates));
@@ -691,7 +695,7 @@
 */
 void BotCTFOrders_BothFlagsAtBase(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME];
 
 	//sort team mates by travel time to base
@@ -881,9 +885,13 @@
 	int teammates[MAX_CLIENTS];
 	int numteammates, i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	numteammates = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -933,7 +941,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ==================
@@ -1016,7 +1024,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1202,7 +1210,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1366,7 +1374,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1513,7 +1521,7 @@
 			}
 		}
 	}
-	else { //aggressive
+	else { //agressive
 		//different orders based on the number of team mates
 		switch(numteammates) {
 			case 1: break;
@@ -1749,7 +1757,7 @@
 */
 void BotHarvesterOrders(bot_state_t *bs) {
 	int numteammates, defenders, attackers, i;
-	int teammates[MAX_CLIENTS] = {0};
+	int teammates[MAX_CLIENTS];
 	char name[MAX_NETNAME];
 
 	//sort team mates by travel time to base
@@ -1956,7 +1964,8 @@
 				trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
 				BotSayVoiceTeamOrder(bs, -1, VOICECHAT_STARTLEADER);
 				ClientName(bs->client, netname, sizeof(netname));
-				Q_strncpyz(bs->teamleader, netname, sizeof(bs->teamleader));
+				strncpy(bs->teamleader, netname, sizeof(bs->teamleader));
+				bs->teamleader[sizeof(bs->teamleader)-1] = '\0';
 				bs->becometeamleader_time = 0;
 			}
 			return;
@@ -1971,7 +1980,8 @@
 	//
 	numteammates = BotNumTeamMates(bs);
 	//give orders
-	if (gametype == GT_TEAM) {
+	switch(gametype) {
+		case GT_TEAM:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -1984,8 +1994,9 @@
 				//give orders again after 120 seconds
 				bs->teamgiveorders_time = FloatTime() + 120;
 			}
+			break;
 		}
-	} else if (gametype == GT_CTF) {
+		case GT_CTF:
 		{
 			//if the number of team mates changed or the flag status changed
 			//or someone wants to know what to do
@@ -2010,9 +2021,10 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-#if 1  //def MPACK
-	} else if (gametype == GT_1FCTF) {
+#ifdef MISSIONPACK
+		case GT_1FCTF:
 		{
 			if (bs->numteammates != numteammates || bs->flagstatuschanged || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2035,8 +2047,9 @@
 				//
 				bs->teamgiveorders_time = 0;
 			}
+			break;
 		}
-	} else if (gametype == GT_OBELISK) {
+		case GT_OBELISK:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2049,8 +2062,9 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
-	} else if (gametype == GT_HARVESTER) {
+		case GT_HARVESTER:
 		{
 			if (bs->numteammates != numteammates || bs->forceorders) {
 				bs->teamgiveorders_time = FloatTime();
@@ -2063,6 +2077,7 @@
 				//give orders again after 30 seconds
 				bs->teamgiveorders_time = FloatTime() + 30;
 			}
+			break;
 		}
 #endif
 	}

```

### `openarena-gamecode`  — sha256 `9617b8d4d467...`, 75117 bytes

_Diff stat: +269 / -65 lines_

_(full diff is 21252 bytes — see files directly)_
