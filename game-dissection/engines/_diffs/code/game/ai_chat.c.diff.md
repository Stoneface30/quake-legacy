# Diff: `code/game/ai_chat.c`
**Canonical:** `wolfcamql-src` (sha256 `5d709ff0bef0...`, 35515 bytes)

## Variants

### `quake3-source`  — sha256 `9fec6e26440d...`, 35879 bytes

_Diff stat: +60 / -44 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_chat.c	2026-04-16 20:02:25.180825800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_chat.c	2026-04-16 20:02:19.895607000 +0100
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
@@ -53,7 +53,7 @@
 #include "match.h"				//string matching types and vars
 
 // for the voice chats
-#ifdef MISSIONPACK
+#ifdef MISSIONPACK // bk001205
 #include "../../ui/menudef.h"
 #endif
 
@@ -68,9 +68,13 @@
 int BotNumActivePlayers(void) {
 	int i, num;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	num = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -90,17 +94,22 @@
 int BotIsFirstInRankings(bot_state_t *bs) {
 	int i, score;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	score = bs->cur_ps.persistant[PERS_SCORE];
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && score < ps.persistant[PERS_SCORE]) return qfalse;
+		BotAI_GetClientState(i, &ps);
+		if (score < ps.persistant[PERS_SCORE]) return qfalse;
 	}
 	return qtrue;
 }
@@ -113,17 +122,22 @@
 int BotIsLastInRankings(bot_state_t *bs) {
 	int i, score;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	score = bs->cur_ps.persistant[PERS_SCORE];
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && score > ps.persistant[PERS_SCORE]) return qfalse;
+		BotAI_GetClientState(i, &ps);
+		if (score > ps.persistant[PERS_SCORE]) return qfalse;
 	}
 	return qtrue;
 }
@@ -137,18 +151,23 @@
 	int i, bestscore, bestclient;
 	char buf[MAX_INFO_STRING];
 	static char name[32];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	bestscore = -999999;
 	bestclient = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && ps.persistant[PERS_SCORE] > bestscore) {
+		BotAI_GetClientState(i, &ps);
+		if (ps.persistant[PERS_SCORE] > bestscore) {
 			bestscore = ps.persistant[PERS_SCORE];
 			bestclient = i;
 		}
@@ -166,18 +185,23 @@
 	int i, worstscore, bestclient;
 	char buf[MAX_INFO_STRING];
 	static char name[32];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	worstscore = 999999;
 	bestclient = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && ps.persistant[PERS_SCORE] < worstscore) {
+		BotAI_GetClientState(i, &ps);
+		if (ps.persistant[PERS_SCORE] < worstscore) {
 			worstscore = ps.persistant[PERS_SCORE];
 			bestclient = i;
 		}
@@ -195,11 +219,15 @@
 	int i, count;
 	char buf[MAX_INFO_STRING];
 	int opponents[MAX_CLIENTS], numopponents;
+	static int maxclients;
 	static char name[32];
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	numopponents = 0;
 	opponents[0] = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (i == bs->client) continue;
 		//
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
@@ -237,7 +265,8 @@
 
 	trap_GetServerinfo(info, sizeof(info));
 
-	Q_strncpyz(mapname, Info_ValueForKey( info, "mapname" ), sizeof(mapname));
+	strncpy(mapname, Info_ValueForKey( info, "mapname" ), sizeof(mapname)-1);
+	mapname[sizeof(mapname)-1] = '\0';
 
 	return mapname;
 }
@@ -254,7 +283,6 @@
 		case MOD_SHOTGUN: return "Shotgun";
 		case MOD_GAUNTLET: return "Gauntlet";
 		case MOD_MACHINEGUN: return "Machinegun";
-		case MOD_HMG: return "Heavy Machinegun";
 		case MOD_GRENADE:
 		case MOD_GRENADE_SPLASH: return "Grenade Launcher";
 		case MOD_ROCKET:
@@ -265,7 +293,7 @@
 		case MOD_LIGHTNING: return "Lightning Gun";
 		case MOD_BFG:
 		case MOD_BFG_SPLASH: return "BFG10K";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case MOD_NAIL: return "Nailgun";
 		case MOD_CHAINGUN: return "Chaingun";
 		case MOD_PROXIMITY_MINE: return "Proximity Launcher";
@@ -285,7 +313,7 @@
 char *BotRandomWeaponName(void) {
 	int rnd;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	rnd = random() * 11.9;
 #else
 	rnd = random() * 8.9;
@@ -299,7 +327,7 @@
 		case 5: return "Plasmagun";
 		case 6: return "Railgun";
 		case 7: return "Lightning Gun";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case 8: return "Nailgun";
 		case 9: return "Chaingun";
 		case 10: return "Proximity Launcher";
@@ -353,7 +381,6 @@
 	if (BotIsDead(bs)) return qtrue;
 	//never start chatting with a powerup
 	if (bs->inventory[INVENTORY_QUAD] ||
-		bs->inventory[INVENTORY_ENVIRONMENTSUIT] ||
 		bs->inventory[INVENTORY_HASTE] ||
 		bs->inventory[INVENTORY_INVISIBILITY] ||
 		bs->inventory[INVENTORY_REGEN] ||
@@ -460,9 +487,7 @@
 	if (bs->lastchat_time > FloatTime() - TIME_BETWEENCHATTING) return qfalse;
 	//don't chat in teamplay
 	if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 	    trap_EA_Command(bs->client, "vtaunt");
-#endif
 	    return qfalse;
 	}
 	// don't chat in tournament mode
@@ -495,11 +520,9 @@
 	// teamplay
 	if (TeamPlayIsOn()) 
 	{
-#ifdef MISSIONPACK
 		if (BotIsFirstInRankings(bs)) {
 			trap_EA_Command(bs->client, "vtaunt");
 		}
-#endif
 		return qtrue;
 	}
 	// don't chat in tournament mode
@@ -576,9 +599,7 @@
 	{
 		//teamplay
 		if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 			trap_EA_Command(bs->client, "vtaunt");
-#endif
 			return qtrue;
 		}
 		//
@@ -599,7 +620,7 @@
 			BotAI_BotInitialChat(bs, "death_suicide", BotRandomOpponentName(bs), NULL);
 		else if (bs->botdeathtype == MOD_TELEFRAG)
 			BotAI_BotInitialChat(bs, "death_telefrag", name, NULL);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "death_kamikaze"))
 			BotAI_BotInitialChat(bs, "death_kamikaze", name, NULL);
 #endif
@@ -680,9 +701,7 @@
 	{
 		//don't chat in teamplay
 		if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 			trap_EA_Command(bs->client, "vtaunt");
-#endif
 			return qfalse;			// don't wait
 		}
 		//
@@ -695,7 +714,7 @@
 		else if (bs->enemydeathtype == MOD_TELEFRAG) {
 			BotAI_BotInitialChat(bs, "kill_telefrag", name, NULL);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "kill_kamikaze"))
 			BotAI_BotInitialChat(bs, "kill_kamikaze", name, NULL);
 #endif
@@ -724,7 +743,7 @@
 	if (bs->lastchat_time > FloatTime() - TIME_BETWEENCHATTING) return qfalse;
 	if (BotNumActivePlayers() <= 1) return qfalse;
 	//
-	rnd = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_CHAT_ENEMYSUICIDE, 0, 1);
+	rnd = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_CHAT_KILL, 0, 1);
 	//don't chat in teamplay
 	if (TeamPlayIsOn()) return qfalse;
 	// don't chat in tournament mode
@@ -776,7 +795,7 @@
 	if (!BotValidChatPosition(bs)) return qfalse;
 	//
 	ClientName(g_entities[bs->client].client->lasthurt_client, name, sizeof(name));
-	weap = BotWeaponNameForMeansOfDeath(g_entities[bs->client].client->lasthurt_mod);
+	weap = BotWeaponNameForMeansOfDeath(g_entities[bs->client].client->lasthurt_client);
 	//
 	BotAI_BotInitialChat(bs, "hit_talking", name, weap, NULL);
 	bs->lastchat_time = FloatTime();
@@ -905,9 +924,7 @@
 		EasyClientName(bs->lastkilledplayer, name, sizeof(name));
 	}
 	if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 		trap_EA_Command(bs->client, "vtaunt");
-#endif
 		return qfalse;			// don't wait
 	}
 	//
@@ -942,10 +959,9 @@
 ==================
 */
 float BotChatTime(bot_state_t *bs) {
-	//int cpm;
+	int cpm;
 
-	//cpm = trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
-	trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
+	cpm = trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
 
 	return 2.0;	//(float) trap_BotChatLength(bs->cs) * 30 / cpm;
 }

```

### `ioquake3`  — sha256 `502ba156a21e...`, 35390 bytes

_Diff stat: +5 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_chat.c	2026-04-16 20:02:25.180825800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_chat.c	2026-04-16 20:02:21.534568900 +0100
@@ -254,7 +254,6 @@
 		case MOD_SHOTGUN: return "Shotgun";
 		case MOD_GAUNTLET: return "Gauntlet";
 		case MOD_MACHINEGUN: return "Machinegun";
-		case MOD_HMG: return "Heavy Machinegun";
 		case MOD_GRENADE:
 		case MOD_GRENADE_SPLASH: return "Grenade Launcher";
 		case MOD_ROCKET:
@@ -265,7 +264,7 @@
 		case MOD_LIGHTNING: return "Lightning Gun";
 		case MOD_BFG:
 		case MOD_BFG_SPLASH: return "BFG10K";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case MOD_NAIL: return "Nailgun";
 		case MOD_CHAINGUN: return "Chaingun";
 		case MOD_PROXIMITY_MINE: return "Proximity Launcher";
@@ -285,7 +284,7 @@
 char *BotRandomWeaponName(void) {
 	int rnd;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	rnd = random() * 11.9;
 #else
 	rnd = random() * 8.9;
@@ -299,7 +298,7 @@
 		case 5: return "Plasmagun";
 		case 6: return "Railgun";
 		case 7: return "Lightning Gun";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case 8: return "Nailgun";
 		case 9: return "Chaingun";
 		case 10: return "Proximity Launcher";
@@ -599,7 +598,7 @@
 			BotAI_BotInitialChat(bs, "death_suicide", BotRandomOpponentName(bs), NULL);
 		else if (bs->botdeathtype == MOD_TELEFRAG)
 			BotAI_BotInitialChat(bs, "death_telefrag", name, NULL);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "death_kamikaze"))
 			BotAI_BotInitialChat(bs, "death_kamikaze", name, NULL);
 #endif
@@ -695,7 +694,7 @@
 		else if (bs->enemydeathtype == MOD_TELEFRAG) {
 			BotAI_BotInitialChat(bs, "kill_telefrag", name, NULL);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "kill_kamikaze"))
 			BotAI_BotInitialChat(bs, "kill_kamikaze", name, NULL);
 #endif
@@ -945,7 +944,6 @@
 	//int cpm;
 
 	//cpm = trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
-	trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
 
 	return 2.0;	//(float) trap_BotChatLength(bs->cs) * 30 / cpm;
 }

```

### `openarena-engine`  — sha256 `e51ad70496a7...`, 36174 bytes

_Diff stat: +45 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_chat.c	2026-04-16 20:02:25.180825800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_chat.c	2026-04-16 22:48:25.738377800 +0100
@@ -68,9 +68,13 @@
 int BotNumActivePlayers(void) {
 	int i, num;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
+
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
 
 	num = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
@@ -90,17 +94,22 @@
 int BotIsFirstInRankings(bot_state_t *bs) {
 	int i, score;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	score = bs->cur_ps.persistant[PERS_SCORE];
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && score < ps.persistant[PERS_SCORE]) return qfalse;
+		BotAI_GetClientState(i, &ps);
+		if (score < ps.persistant[PERS_SCORE]) return qfalse;
 	}
 	return qtrue;
 }
@@ -113,17 +122,22 @@
 int BotIsLastInRankings(bot_state_t *bs) {
 	int i, score;
 	char buf[MAX_INFO_STRING];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	score = bs->cur_ps.persistant[PERS_SCORE];
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && score > ps.persistant[PERS_SCORE]) return qfalse;
+		BotAI_GetClientState(i, &ps);
+		if (score > ps.persistant[PERS_SCORE]) return qfalse;
 	}
 	return qtrue;
 }
@@ -137,18 +151,23 @@
 	int i, bestscore, bestclient;
 	char buf[MAX_INFO_STRING];
 	static char name[32];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	bestscore = -999999;
 	bestclient = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && ps.persistant[PERS_SCORE] > bestscore) {
+		BotAI_GetClientState(i, &ps);
+		if (ps.persistant[PERS_SCORE] > bestscore) {
 			bestscore = ps.persistant[PERS_SCORE];
 			bestclient = i;
 		}
@@ -166,18 +185,23 @@
 	int i, worstscore, bestclient;
 	char buf[MAX_INFO_STRING];
 	static char name[32];
+	static int maxclients;
 	playerState_t ps;
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	worstscore = 999999;
 	bestclient = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
 		//if no config string or no name
 		if (!strlen(buf) || !strlen(Info_ValueForKey(buf, "n"))) continue;
 		//skip spectators
 		if (atoi(Info_ValueForKey(buf, "t")) == TEAM_SPECTATOR) continue;
 		//
-		if (BotAI_GetClientState(i, &ps) && ps.persistant[PERS_SCORE] < worstscore) {
+		BotAI_GetClientState(i, &ps);
+		if (ps.persistant[PERS_SCORE] < worstscore) {
 			worstscore = ps.persistant[PERS_SCORE];
 			bestclient = i;
 		}
@@ -195,11 +219,15 @@
 	int i, count;
 	char buf[MAX_INFO_STRING];
 	int opponents[MAX_CLIENTS], numopponents;
+	static int maxclients;
 	static char name[32];
 
+	if (!maxclients)
+		maxclients = trap_Cvar_VariableIntegerValue("sv_maxclients");
+
 	numopponents = 0;
 	opponents[0] = 0;
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		if (i == bs->client) continue;
 		//
 		trap_GetConfigstring(CS_PLAYERS+i, buf, sizeof(buf));
@@ -237,7 +265,8 @@
 
 	trap_GetServerinfo(info, sizeof(info));
 
-	Q_strncpyz(mapname, Info_ValueForKey( info, "mapname" ), sizeof(mapname));
+	strncpy(mapname, Info_ValueForKey( info, "mapname" ), sizeof(mapname)-1);
+	mapname[sizeof(mapname)-1] = '\0';
 
 	return mapname;
 }
@@ -254,7 +283,6 @@
 		case MOD_SHOTGUN: return "Shotgun";
 		case MOD_GAUNTLET: return "Gauntlet";
 		case MOD_MACHINEGUN: return "Machinegun";
-		case MOD_HMG: return "Heavy Machinegun";
 		case MOD_GRENADE:
 		case MOD_GRENADE_SPLASH: return "Grenade Launcher";
 		case MOD_ROCKET:
@@ -265,7 +293,7 @@
 		case MOD_LIGHTNING: return "Lightning Gun";
 		case MOD_BFG:
 		case MOD_BFG_SPLASH: return "BFG10K";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case MOD_NAIL: return "Nailgun";
 		case MOD_CHAINGUN: return "Chaingun";
 		case MOD_PROXIMITY_MINE: return "Proximity Launcher";
@@ -285,7 +313,7 @@
 char *BotRandomWeaponName(void) {
 	int rnd;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	rnd = random() * 11.9;
 #else
 	rnd = random() * 8.9;
@@ -299,7 +327,7 @@
 		case 5: return "Plasmagun";
 		case 6: return "Railgun";
 		case 7: return "Lightning Gun";
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case 8: return "Nailgun";
 		case 9: return "Chaingun";
 		case 10: return "Proximity Launcher";
@@ -599,7 +627,7 @@
 			BotAI_BotInitialChat(bs, "death_suicide", BotRandomOpponentName(bs), NULL);
 		else if (bs->botdeathtype == MOD_TELEFRAG)
 			BotAI_BotInitialChat(bs, "death_telefrag", name, NULL);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "death_kamikaze"))
 			BotAI_BotInitialChat(bs, "death_kamikaze", name, NULL);
 #endif
@@ -695,7 +723,7 @@
 		else if (bs->enemydeathtype == MOD_TELEFRAG) {
 			BotAI_BotInitialChat(bs, "kill_telefrag", name, NULL);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "kill_kamikaze"))
 			BotAI_BotInitialChat(bs, "kill_kamikaze", name, NULL);
 #endif
@@ -945,7 +973,6 @@
 	//int cpm;
 
 	//cpm = trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
-	trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
 
 	return 2.0;	//(float) trap_BotChatLength(bs->cs) * 30 / cpm;
 }

```

### `openarena-gamecode`  — sha256 `9d9d8f6fb4e2...`, 35109 bytes

_Diff stat: +6 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_chat.c	2026-04-16 20:02:25.180825800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_chat.c	2026-04-16 22:48:24.157330500 +0100
@@ -53,7 +53,7 @@
 #include "match.h"				//string matching types and vars
 
 // for the voice chats
-#ifdef MISSIONPACK
+#ifdef MISSIONPACK // bk001205
 #include "../../ui/menudef.h"
 #endif
 
@@ -254,7 +254,6 @@
 		case MOD_SHOTGUN: return "Shotgun";
 		case MOD_GAUNTLET: return "Gauntlet";
 		case MOD_MACHINEGUN: return "Machinegun";
-		case MOD_HMG: return "Heavy Machinegun";
 		case MOD_GRENADE:
 		case MOD_GRENADE_SPLASH: return "Grenade Launcher";
 		case MOD_ROCKET:
@@ -265,13 +264,11 @@
 		case MOD_LIGHTNING: return "Lightning Gun";
 		case MOD_BFG:
 		case MOD_BFG_SPLASH: return "BFG10K";
-#if 1  //def MPACK
 		case MOD_NAIL: return "Nailgun";
 		case MOD_CHAINGUN: return "Chaingun";
 		case MOD_PROXIMITY_MINE: return "Proximity Launcher";
 		case MOD_KAMIKAZE: return "Kamikaze";
 		case MOD_JUICED: return "Prox mine";
-#endif
 		case MOD_GRAPPLE: return "Grapple";
 		default: return "[unknown weapon]";
 	}
@@ -285,11 +282,7 @@
 char *BotRandomWeaponName(void) {
 	int rnd;
 
-#if 1  //def MPACK
 	rnd = random() * 11.9;
-#else
-	rnd = random() * 8.9;
-#endif
 	switch(rnd) {
 		case 0: return "Gauntlet";
 		case 1: return "Shotgun";
@@ -299,11 +292,9 @@
 		case 5: return "Plasmagun";
 		case 6: return "Railgun";
 		case 7: return "Lightning Gun";
-#if 1  //def MPACK
 		case 8: return "Nailgun";
 		case 9: return "Chaingun";
 		case 10: return "Proximity Launcher";
-#endif
 		default: return "BFG10K";
 	}
 }
@@ -351,6 +342,7 @@
 
 	//if the bot is dead all positions are valid
 	if (BotIsDead(bs)) return qtrue;
+        if (BotIsObserver(bs)) return qtrue;
 	//never start chatting with a powerup
 	if (bs->inventory[INVENTORY_QUAD] ||
 		bs->inventory[INVENTORY_ENVIRONMENTSUIT] ||
@@ -460,9 +452,7 @@
 	if (bs->lastchat_time > FloatTime() - TIME_BETWEENCHATTING) return qfalse;
 	//don't chat in teamplay
 	if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 	    trap_EA_Command(bs->client, "vtaunt");
-#endif
 	    return qfalse;
 	}
 	// don't chat in tournament mode
@@ -495,11 +485,9 @@
 	// teamplay
 	if (TeamPlayIsOn()) 
 	{
-#ifdef MISSIONPACK
 		if (BotIsFirstInRankings(bs)) {
 			trap_EA_Command(bs->client, "vtaunt");
 		}
-#endif
 		return qtrue;
 	}
 	// don't chat in tournament mode
@@ -576,9 +564,7 @@
 	{
 		//teamplay
 		if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 			trap_EA_Command(bs->client, "vtaunt");
-#endif
 			return qtrue;
 		}
 		//
@@ -599,10 +585,8 @@
 			BotAI_BotInitialChat(bs, "death_suicide", BotRandomOpponentName(bs), NULL);
 		else if (bs->botdeathtype == MOD_TELEFRAG)
 			BotAI_BotInitialChat(bs, "death_telefrag", name, NULL);
-#if 1  //def MPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "death_kamikaze"))
 			BotAI_BotInitialChat(bs, "death_kamikaze", name, NULL);
-#endif
 		else {
 			if ((bs->botdeathtype == MOD_GAUNTLET ||
 				bs->botdeathtype == MOD_RAILGUN ||
@@ -680,9 +664,7 @@
 	{
 		//don't chat in teamplay
 		if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 			trap_EA_Command(bs->client, "vtaunt");
-#endif
 			return qfalse;			// don't wait
 		}
 		//
@@ -695,10 +677,8 @@
 		else if (bs->enemydeathtype == MOD_TELEFRAG) {
 			BotAI_BotInitialChat(bs, "kill_telefrag", name, NULL);
 		}
-#if 1  //def MPACK
 		else if (bs->botdeathtype == MOD_KAMIKAZE && trap_BotNumInitialChats(bs->cs, "kill_kamikaze"))
 			BotAI_BotInitialChat(bs, "kill_kamikaze", name, NULL);
-#endif
 		//choose between insult and praise
 		else if (random() < trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_CHAT_INSULT, 0, 1)) {
 			BotAI_BotInitialChat(bs, "kill_insult", name, NULL);
@@ -899,15 +879,13 @@
 	if (BotVisibleEnemies(bs)) return qfalse;
 	//
 	if (bs->lastkilledplayer == bs->client) {
-		strcpy(name, BotRandomOpponentName(bs));
+		Q_strncpyz(name, BotRandomOpponentName(bs),sizeof(name));
 	}
 	else {
 		EasyClientName(bs->lastkilledplayer, name, sizeof(name));
 	}
 	if (TeamPlayIsOn()) {
-#ifdef MISSIONPACK
 		trap_EA_Command(bs->client, "vtaunt");
-#endif
 		return qfalse;			// don't wait
 	}
 	//
@@ -942,11 +920,6 @@
 ==================
 */
 float BotChatTime(bot_state_t *bs) {
-	//int cpm;
-
-	//cpm = trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
-	trap_Characteristic_BInteger(bs->character, CHARACTERISTIC_CHAT_CPM, 1, 4000);
-
 	return 2.0;	//(float) trap_BotChatLength(bs->cs) * 30 / cpm;
 }
 
@@ -961,6 +934,8 @@
 	char *weap;
 	int num, i;
 
+        if (bot_nochat.integer) return;
+
 	num = trap_BotNumInitialChats(bs->cs, "game_enter");
 	for (i = 0; i < num; i++)
 	{
@@ -1174,7 +1149,7 @@
 	}
 	//
 	if (bs->lastkilledplayer == bs->client) {
-		strcpy(name, BotRandomOpponentName(bs));
+		Q_strncpyz(name, BotRandomOpponentName(bs), sizeof(name));
 	}
 	else {
 		EasyClientName(bs->lastkilledplayer, name, sizeof(name));

```
