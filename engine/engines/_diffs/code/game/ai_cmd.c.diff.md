# Diff: `code/game/ai_cmd.c`
**Canonical:** `wolfcamql-src` (sha256 `b924cf15da6f...`, 52122 bytes)

## Variants

### `quake3-source`  — sha256 `00a5ee1d01b8...`, 52326 bytes

_Diff stat: +34 / -22 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_cmd.c	2026-04-16 20:02:25.181346200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_cmd.c	2026-04-16 20:02:19.896613700 +0100
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
@@ -237,12 +237,15 @@
 int FindClientByName(char *name) {
 	int i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 
-	for (i = 0; i < level.maxclients; i++) {
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		ClientName(i, buf, sizeof(buf));
 		if (!Q_stricmp(buf, name)) return i;
 	}
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		ClientName(i, buf, sizeof(buf));
 		if (stristr(buf, name)) return i;
 	}
@@ -257,13 +260,16 @@
 int FindEnemyByName(bot_state_t *bs, char *name) {
 	int i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 
-	for (i = 0; i < level.maxclients; i++) {
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (BotSameTeam(bs, i)) continue;
 		ClientName(i, buf, sizeof(buf));
 		if (!Q_stricmp(buf, name)) return i;
 	}
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (BotSameTeam(bs, i)) continue;
 		ClientName(i, buf, sizeof(buf));
 		if (stristr(buf, name)) return i;
@@ -279,9 +285,13 @@
 int NumPlayersOnSameTeam(bot_state_t *bs) {
 	int i, num;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	num = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, MAX_INFO_STRING);
 		if (strlen(buf)) {
 			if (BotSameTeam(bs, i+1)) num++;
@@ -1105,7 +1115,8 @@
 	//get the sub team name
 	trap_BotMatchVariable(match, TEAMNAME, teammate, sizeof(teammate));
 	//set the sub team name
-	Q_strncpyz(bs->subteam, teammate, sizeof(bs->subteam));
+	strncpy(bs->subteam, teammate, 32);
+	bs->subteam[31] = '\0';
 	//
 	trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
 	BotAI_BotInitialChat(bs, "joinedteam", teammate, NULL);
@@ -1296,7 +1307,8 @@
 	if (match->subtype & ST_I) {
 		//get the team mate that will be the team leader
 		trap_BotMatchVariable(match, NETNAME, teammate, sizeof(teammate));
-		Q_strncpyz(bs->teamleader, teammate, sizeof(bs->teamleader));
+		strncpy(bs->teamleader, teammate, sizeof(bs->teamleader));
+		bs->teamleader[sizeof(bs->teamleader)] = '\0';
 	}
 	//chats for someone else
 	else {
@@ -1516,21 +1528,21 @@
 		"Quad Damage",
 		"Regeneration",
 		"Battle Suit",
-		"Haste",  // changed from "Speed" in q3
+		"Speed",
 		"Invisibility",
 		"Flight",
 		"Armor",
-		"Red Armor",  // changed from "Heavy Armor" in q3
+		"Heavy Armor",
 		"Red Flag",
 		"Blue Flag",
-#if 1  // MPACK
+#ifdef MISSIONPACK
 		"Nailgun",
 		"Prox Launcher",
 		"Chaingun",
 		"Scout",
 		"Guard",
-		"Damage",  // changed from "Doubler" in q3
-		"Armor Regen",  // changed from "Ammo Regen" in q3
+		"Doubler",
+		"Ammo Regen",
 		"Neutral Flag",
 		"Red Obelisk",
 		"Blue Obelisk",

```

### `ioquake3`  — sha256 `a139fa0628e1...`, 51990 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_cmd.c	2026-04-16 20:02:25.181346200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_cmd.c	2026-04-16 20:02:21.535889700 +0100
@@ -1516,21 +1516,21 @@
 		"Quad Damage",
 		"Regeneration",
 		"Battle Suit",
-		"Haste",  // changed from "Speed" in q3
+		"Speed",
 		"Invisibility",
 		"Flight",
 		"Armor",
-		"Red Armor",  // changed from "Heavy Armor" in q3
+		"Heavy Armor",
 		"Red Flag",
 		"Blue Flag",
-#if 1  // MPACK
+#ifdef MISSIONPACK
 		"Nailgun",
 		"Prox Launcher",
 		"Chaingun",
 		"Scout",
 		"Guard",
-		"Damage",  // changed from "Doubler" in q3
-		"Armor Regen",  // changed from "Ammo Regen" in q3
+		"Doubler",
+		"Ammo Regen",
 		"Neutral Flag",
 		"Red Obelisk",
 		"Blue Obelisk",

```

### `openarena-engine`  — sha256 `17f6b69f9ef1...`, 52439 bytes

_Diff stat: +24 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_cmd.c	2026-04-16 20:02:25.181346200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_cmd.c	2026-04-16 22:48:25.739377700 +0100
@@ -237,12 +237,15 @@
 int FindClientByName(char *name) {
 	int i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 
-	for (i = 0; i < level.maxclients; i++) {
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		ClientName(i, buf, sizeof(buf));
 		if (!Q_stricmp(buf, name)) return i;
 	}
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		ClientName(i, buf, sizeof(buf));
 		if (stristr(buf, name)) return i;
 	}
@@ -257,13 +260,16 @@
 int FindEnemyByName(bot_state_t *bs, char *name) {
 	int i;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 
-	for (i = 0; i < level.maxclients; i++) {
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (BotSameTeam(bs, i)) continue;
 		ClientName(i, buf, sizeof(buf));
 		if (!Q_stricmp(buf, name)) return i;
 	}
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (BotSameTeam(bs, i)) continue;
 		ClientName(i, buf, sizeof(buf));
 		if (stristr(buf, name)) return i;
@@ -279,9 +285,13 @@
 int NumPlayersOnSameTeam(bot_state_t *bs) {
 	int i, num;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	num = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, MAX_INFO_STRING);
 		if (strlen(buf)) {
 			if (BotSameTeam(bs, i+1)) num++;
@@ -1105,7 +1115,8 @@
 	//get the sub team name
 	trap_BotMatchVariable(match, TEAMNAME, teammate, sizeof(teammate));
 	//set the sub team name
-	Q_strncpyz(bs->subteam, teammate, sizeof(bs->subteam));
+	strncpy(bs->subteam, teammate, 32);
+	bs->subteam[31] = '\0';
 	//
 	trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
 	BotAI_BotInitialChat(bs, "joinedteam", teammate, NULL);
@@ -1296,7 +1307,8 @@
 	if (match->subtype & ST_I) {
 		//get the team mate that will be the team leader
 		trap_BotMatchVariable(match, NETNAME, teammate, sizeof(teammate));
-		Q_strncpyz(bs->teamleader, teammate, sizeof(bs->teamleader));
+		strncpy(bs->teamleader, teammate, sizeof(bs->teamleader));
+		bs->teamleader[sizeof(bs->teamleader)-1] = '\0';
 	}
 	//chats for someone else
 	else {
@@ -1516,21 +1528,21 @@
 		"Quad Damage",
 		"Regeneration",
 		"Battle Suit",
-		"Haste",  // changed from "Speed" in q3
+		"Speed",
 		"Invisibility",
 		"Flight",
 		"Armor",
-		"Red Armor",  // changed from "Heavy Armor" in q3
+		"Heavy Armor",
 		"Red Flag",
 		"Blue Flag",
-#if 1  // MPACK
+#ifdef MISSIONPACK
 		"Nailgun",
 		"Prox Launcher",
 		"Chaingun",
 		"Scout",
 		"Guard",
-		"Damage",  // changed from "Doubler" in q3
-		"Armor Regen",  // changed from "Ammo Regen" in q3
+		"Doubler",
+		"Ammo Regen",
 		"Neutral Flag",
 		"Red Obelisk",
 		"Blue Obelisk",

```

### `openarena-gamecode`  — sha256 `25029704875b...`, 55452 bytes

_Diff stat: +166 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_cmd.c	2026-04-16 20:02:25.181346200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_cmd.c	2026-04-16 22:48:24.158330100 +0100
@@ -96,7 +96,6 @@
 			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna try to return the flag for %1.0f secs\n", netname, t);
 			break;
 		}
-#ifdef MISSIONPACK
 		case LTG_ATTACKENEMYBASE:
 		{
 			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna attack the enemy base for %1.0f secs\n", netname, t);
@@ -107,7 +106,6 @@
 			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna harvest for %1.0f secs\n", netname, t);
 			break;
 		}
-#endif
 		case LTG_DEFENDKEYAREA:
 		{
 			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna defend a key area for %1.0f secs\n", netname, t);
@@ -134,6 +132,16 @@
 			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna patrol for %1.0f secs\n", netname, t);
 			break;
 		}
+		case LTG_POINTA:
+		{
+			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna take care of point A for %1.0f secs\n", netname, t);
+			break;
+		}
+		case LTG_POINTB:
+		{
+			BotAI_Print(PRT_MESSAGE, "%s: I'm gonna take care of point B for %1.0f secs\n", netname, t);
+			break;
+		}
 		default:
 		{
 			if (bs->ctfroam_time > FloatTime()) {
@@ -240,7 +248,7 @@
 
 	for (i = 0; i < level.maxclients; i++) {
 		ClientName(i, buf, sizeof(buf));
-		if (!Q_stricmp(buf, name)) return i;
+		if (Q_strequal(buf, name)) return i;
 	}
 	for (i = 0; i < level.maxclients; i++) {
 		ClientName(i, buf, sizeof(buf));
@@ -261,7 +269,7 @@
 	for (i = 0; i < level.maxclients; i++) {
 		if (BotSameTeam(bs, i)) continue;
 		ClientName(i, buf, sizeof(buf));
-		if (!Q_stricmp(buf, name)) return i;
+		if (Q_strequal(buf, name)) return i;
 	}
 	for (i = 0; i < level.maxclients; i++) {
 		if (BotSameTeam(bs, i)) continue;
@@ -309,7 +317,7 @@
 	//
 	while(1) {
 		if (!trap_BotFindMatch(keyarea, &keyareamatch, MTCONTEXT_PATROLKEYAREA)) {
-			trap_EA_SayTeam(bs->client, "what do you say?");
+                            trap_EA_SayTeam(bs->client, "what do you say?");
 			BotFreeWaypoints(newpatrolpoints);
 			bs->patrolpoints = NULL;
 			return qfalse;
@@ -642,6 +650,104 @@
 
 /*
 ==================
+BotMatch_TakeA
+For Double Domination
+==================
+*/
+void BotMatch_TakeA(bot_state_t *bs, bot_match_t *match) {
+// 	char itemname[MAX_MESSAGE_SIZE];
+	char netname[MAX_MESSAGE_SIZE];
+	int client;
+
+	if (!TeamPlayIsOn()) return;
+	//if not addressed to this bot
+	if (!BotAddressedToBot(bs, match)) return;
+	//get the match variable
+	/*trap_BotMatchVariable(match, KEYAREA, itemname, sizeof(itemname));
+	//
+	if (!BotGetMessageTeamGoal(bs, itemname, &bs->teamgoal)) {
+		//BotAI_BotInitialChat(bs, "cannotfind", itemname, NULL);
+		//trap_BotEnterChat(bs->cs, bs->client, CHAT_TEAM);
+		return;
+	}*/
+	//
+	trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
+	//
+	client = ClientFromName(netname);
+	//the team mate who ordered
+	bs->decisionmaker = client;
+	bs->ordered = qtrue;
+	bs->order_time = FloatTime();
+	//set the time to send a message to the team mates
+	bs->teammessage_time = FloatTime() + 2 * random();
+	//set the ltg type
+	bs->ltgtype = LTG_POINTA;
+	//get the team goal time
+	bs->teamgoal_time = BotGetTime(match);
+	//set the team goal time
+	if (!bs->teamgoal_time) bs->teamgoal_time = FloatTime() + DD_POINTA;
+	//away from defending
+	bs->defendaway_time = 0;
+	//
+	BotSetTeamStatus(bs);
+	// remember last ordered task
+	BotRememberLastOrderedTask(bs);
+#ifdef DEBUG
+	BotPrintTeamGoal(bs);
+#endif //DEBUG
+}
+
+/*
+==================
+BotMatch_TakeB
+For Double Domination
+==================
+*/
+void BotMatch_TakeB(bot_state_t *bs, bot_match_t *match) {
+// 	char itemname[MAX_MESSAGE_SIZE];
+	char netname[MAX_MESSAGE_SIZE];
+	int client;
+
+	if (!TeamPlayIsOn()) return;
+	//if not addressed to this bot
+	if (!BotAddressedToBot(bs, match)) return;
+	//get the match variable
+	/*trap_BotMatchVariable(match, KEYAREA, itemname, sizeof(itemname));
+	//
+	if (!BotGetMessageTeamGoal(bs, itemname, &bs->teamgoal)) {
+		//BotAI_BotInitialChat(bs, "cannotfind", itemname, NULL);
+		//trap_BotEnterChat(bs->cs, bs->client, CHAT_TEAM);
+		//return;
+	}*/
+	//
+	trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
+	//
+	client = ClientFromName(netname);
+	//the team mate who ordered
+	bs->decisionmaker = client;
+	bs->ordered = qtrue;
+	bs->order_time = FloatTime();
+	//set the time to send a message to the team mates
+	bs->teammessage_time = FloatTime() + 2 * random();
+	//set the ltg type
+	bs->ltgtype = LTG_POINTB;
+	//get the team goal time
+	bs->teamgoal_time = BotGetTime(match);
+	//set the team goal time
+	if (!bs->teamgoal_time) bs->teamgoal_time = FloatTime() + DD_POINTA;
+	//away from defending
+	bs->defendaway_time = 0;
+	//
+	BotSetTeamStatus(bs);
+	// remember last ordered task
+	BotRememberLastOrderedTask(bs);
+#ifdef DEBUG
+	BotPrintTeamGoal(bs);
+#endif //DEBUG
+}
+
+/*
+==================
 BotMatch_GetItem
 ==================
 */
@@ -820,16 +926,18 @@
 	char netname[MAX_MESSAGE_SIZE];
 	int client;
 
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		if (!ctf_redflag.areanum || !ctf_blueflag.areanum)
 			return;
 	}
-#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (!ctf_neutralflag.areanum || !ctf_redflag.areanum || !ctf_blueflag.areanum)
 			return;
 	}
-#endif
+	else if (gametype == GT_POSSESSION) {
+		if (!ctf_neutralflag.areanum)
+			return;
+	}
 	else {
 		return;
 	}
@@ -850,7 +958,7 @@
 	//set the team goal time
 	bs->teamgoal_time = FloatTime() + CTF_GETFLAG_TIME;
 	// get an alternate route in ctf
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_1FCTF || gametype == GT_CTF_ELIMINATION) {
 		//get an alternative route goal towards the enemy base
 		BotGetAlternateRouteGoal(bs, BotOppositeTeam(bs));
 	}
@@ -872,15 +980,13 @@
 	char netname[MAX_MESSAGE_SIZE];
 	int client;
 
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF|| gametype == GT_CTF_ELIMINATION) {
 		BotMatch_GetFlag(bs, match);
 	}
-#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF || gametype == GT_OBELISK || gametype == GT_HARVESTER) {
 		if (!redobelisk.areanum || !blueobelisk.areanum)
 			return;
 	}
-#endif
 	else {
 		return;
 	}
@@ -910,7 +1016,6 @@
 #endif //DEBUG
 }
 
-#ifdef MISSIONPACK
 /*
 ==================
 BotMatch_Harvest
@@ -952,7 +1057,6 @@
 	BotPrintTeamGoal(bs);
 #endif //DEBUG
 }
-#endif
 
 /*
 ==================
@@ -963,16 +1067,14 @@
 	char netname[MAX_MESSAGE_SIZE];
 	int client;
 
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF|| gametype == GT_CTF_ELIMINATION) {
 		if (!ctf_redflag.areanum || !ctf_blueflag.areanum)
 			return;
 	}
-#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF || gametype == GT_HARVESTER) {
 		if (!redobelisk.areanum || !blueobelisk.areanum)
 			return;
 	}
-#endif
 	else {
 		return;
 	}
@@ -1011,7 +1113,9 @@
 	int teammate, preference;
 
 	ClientName(bs->client, netname, sizeof(netname));
-	if (Q_stricmp(netname, bs->teamleader) != 0) return;
+	if ( !Q_strequal(netname, bs->teamleader)) {
+		return;
+	}
 
 	trap_BotMatchVariable(match, NETNAME, teammatename, sizeof(teammatename));
 	teammate = ClientFromName(teammatename);
@@ -1057,12 +1161,7 @@
 	int client;
 
 	//if not in CTF mode
-	if (
-		gametype != GT_CTF
-#ifdef MISSIONPACK
-		&& gametype != GT_1FCTF
-#endif
-		)
+	if (gametype != GT_CTF && gametype != GT_CTF_ELIMINATION && gametype != GT_1FCTF)
 		return;
 	//if not addressed to this bot
 	if (!BotAddressedToBot(bs, match))
@@ -1105,7 +1204,7 @@
 	//get the sub team name
 	trap_BotMatchVariable(match, TEAMNAME, teammate, sizeof(teammate));
 	//set the sub team name
-	Q_strncpyz(bs->subteam, teammate, sizeof(bs->subteam));
+	Q_strncpyz(bs->subteam, teammate, 32);
 	//
 	trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
 	BotAI_BotInitialChat(bs, "joinedteam", teammate, NULL);
@@ -1145,6 +1244,7 @@
 	if (!TeamPlayIsOn()) return;
 	//if not addressed to this bot
 	if (!BotAddressedToBot(bs, match)) return;
+
 	//
 	if (strlen(bs->subteam)) {
 		BotAI_BotInitialChat(bs, "inteam", bs->subteam, NULL);
@@ -1330,7 +1430,7 @@
 		client = FindClientByName(teammate);
 	} //end else
 	if (client >= 0) {
-		if (!Q_stricmp(bs->teamleader, ClientName(client, netname, sizeof(netname)))) {
+		if (Q_strequal(bs->teamleader, ClientName(client, netname, sizeof(netname)))) {
 			bs->teamleader[0] = '\0';
 			notleader[client] = qtrue;
 		}
@@ -1349,7 +1449,7 @@
 
 	ClientName(bs->client, netname, sizeof(netname));
 	//if this bot IS the team leader
-	if (!Q_stricmp(netname, bs->teamleader)) {
+	if (Q_strequal(netname, bs->teamleader)) {
 		trap_EA_SayTeam(bs->client, "I'm the team leader\n");
 	}
 }
@@ -1424,7 +1524,6 @@
 			BotAI_BotInitialChat(bs, "returningflag", NULL);
 			break;
 		}
-#ifdef MISSIONPACK
 		case LTG_ATTACKENEMYBASE:
 		{
 			BotAI_BotInitialChat(bs, "attackingenemybase", NULL);
@@ -1435,7 +1534,17 @@
 			BotAI_BotInitialChat(bs, "harvesting", NULL);
 			break;
 		}
-#endif
+//#endif
+		case LTG_POINTA:
+		{
+			BotAI_BotInitialChat(bs, "dd_pointa", NULL);
+			break;
+		}
+		case LTG_POINTB:
+		{
+			BotAI_BotInitialChat(bs, "dd_pointb", NULL);
+			break;
+		}
 		default:
 		{
 			BotAI_BotInitialChat(bs, "roaming", NULL);
@@ -1457,7 +1566,9 @@
 	char netname[MAX_NETNAME];
 
 	ClientName(bs->client, netname, sizeof(netname));
-	if (Q_stricmp(netname, bs->teamleader) != 0) return;
+	if ( !Q_strequal(netname, bs->teamleader) ) {
+		return;
+	}
 	bs->forceorders = qtrue;
 }
 
@@ -1479,8 +1590,9 @@
 	do {
 		i = trap_BotGetLevelItemGoal(i, itemname, &tmpgoal);
 		trap_BotGoalName(tmpgoal.number, name, sizeof(name));
-		if (Q_stricmp(itemname, name) != 0)
+		if ( !Q_strequal(itemname, name) ) {
 			continue;
+		}
 		VectorSubtract(tmpgoal.origin, bs->origin, dir);
 		dist = VectorLength(dir);
 		if (dist < bestdist) {
@@ -1516,31 +1628,30 @@
 		"Quad Damage",
 		"Regeneration",
 		"Battle Suit",
-		"Haste",  // changed from "Speed" in q3
+		"Speed",
 		"Invisibility",
 		"Flight",
 		"Armor",
-		"Red Armor",  // changed from "Heavy Armor" in q3
+		"Heavy Armor",
 		"Red Flag",
 		"Blue Flag",
-#if 1  // MPACK
 		"Nailgun",
 		"Prox Launcher",
 		"Chaingun",
 		"Scout",
 		"Guard",
-		"Damage",  // changed from "Doubler" in q3
-		"Armor Regen",  // changed from "Ammo Regen" in q3
+		"Doubler",
+		"Ammo Regen",
 		"Neutral Flag",
 		"Red Obelisk",
 		"Blue Obelisk",
 		"Neutral Obelisk",
-#endif
 		NULL
 	};
 	//
 	if (!TeamPlayIsOn())
 		return;
+
 	//if not addressed to this bot
 	if (!BotAddressedToBot(bs, match))
 		return;
@@ -1555,10 +1666,8 @@
 		}
 	}
 	if (bestitem != -1) {
-		if (gametype == GT_CTF
-#ifdef MISSIONPACK
+		if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION
 			|| gametype == GT_1FCTF
-#endif
 			) {
 			redtt = trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin, ctf_redflag.areanum, TFL_DEFAULT);
 			bluett = trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin, ctf_blueflag.areanum, TFL_DEFAULT);
@@ -1572,7 +1681,6 @@
 				BotAI_BotInitialChat(bs, "location", nearbyitems[bestitem], NULL);
 			}
 		}
-#ifdef MISSIONPACK
 		else if (gametype == GT_OBELISK || gametype == GT_HARVESTER) {
 			redtt = trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin, redobelisk.areanum, TFL_DEFAULT);
 			bluett = trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin, blueobelisk.areanum, TFL_DEFAULT);
@@ -1586,7 +1694,6 @@
 				BotAI_BotInitialChat(bs, "location", nearbyitems[bestitem], NULL);
 			}
 		}
-#endif
 		else {
 			BotAI_BotInitialChat(bs, "location", nearbyitems[bestitem], NULL);
 		}
@@ -1712,10 +1819,10 @@
 
 	char flag[128], netname[MAX_NETNAME];
 
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		trap_BotMatchVariable(match, FLAG, flag, sizeof(flag));
 		if (match->subtype & ST_GOTFLAG) {
-			if (!Q_stricmp(flag, "red")) {
+			if (Q_strequal(flag, "red")) {
 				bs->redflagstatus = 1;
 				if (BotTeam(bs) == TEAM_BLUE) {
 					trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
@@ -1739,19 +1846,17 @@
 			bs->flagstatuschanged = 1;
 		}
 		else if (match->subtype & ST_RETURNEDFLAG) {
-			if (!Q_stricmp(flag, "red")) bs->redflagstatus = 0;
+			if (Q_strequal(flag, "red")) bs->redflagstatus = 0;
 			else bs->blueflagstatus = 0;
 			bs->flagstatuschanged = 1;
 		}
 	}
-#ifdef MISSIONPACK
-	else if (gametype == GT_1FCTF) {
+	else if (gametype == GT_1FCTF || gametype == GT_POSSESSION) {
 		if (match->subtype & ST_1FCTFGOTFLAG) {
 			trap_BotMatchVariable(match, NETNAME, netname, sizeof(netname));
 			bs->flagcarrier = ClientFromName(netname);
 		}
 	}
-#endif
 }
 
 void BotMatch_EnterGame(bot_state_t *bs, bot_match_t *match) {
@@ -1790,8 +1895,9 @@
 	match.type = 0;
 	//if it is an unknown message
 	if (!trap_BotFindMatch(message, &match, MTCONTEXT_MISC
-											|MTCONTEXT_INITIALTEAMCHAT
-											|MTCONTEXT_CTF)) {
+	|MTCONTEXT_INITIALTEAMCHAT
+	|MTCONTEXT_CTF
+	|MTCONTEXT_DD)) {
 		return qfalse;
 	}
 	//react to the found message
@@ -1824,7 +1930,6 @@
 			BotMatch_GetFlag(bs, &match);
 			break;
 		}
-#ifdef MISSIONPACK
 		//CTF & 1FCTF & Obelisk & Harvester
 		case MSG_ATTACKENEMYBASE:
 		{
@@ -1837,7 +1942,6 @@
 			BotMatch_Harvest(bs, &match);
 			break;
 		}
-#endif
 		//CTF & 1FCTF & Harvester
 		case MSG_RUSHBASE:				//ctf rush to the base
 		{
@@ -1970,6 +2074,16 @@
 			BotMatch_Suicide(bs, &match);
 			break;
 		}
+		case MSG_TAKEA:
+		{
+			BotMatch_TakeA(bs, &match);
+			break;
+		}
+		case MSG_TAKEB:
+		{
+			BotMatch_TakeB(bs, &match);
+			break;
+		}
 		default:
 		{
 			BotAI_Print(PRT_MESSAGE, "unknown match type\n");

```
