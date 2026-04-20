# Diff: `code/game/ai_dmnet.c`
**Canonical:** `wolfcamql-src` (sha256 `328c14b12999...`, 82510 bytes)

## Variants

### `quake3-source`  — sha256 `e6d3da9189f2...`, 81832 bytes

_Diff stat: +35 / -41 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmnet.c	2026-04-16 20:02:25.181871300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_dmnet.c	2026-04-16 20:02:19.897118800 +0100
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
@@ -56,7 +56,7 @@
 // for the voice chats
 #include "../../ui/menudef.h"
 
-//goal flag, see ../botlib/be_ai_goal.h for the other GFL_*
+//goal flag, see be_ai_goal.h for the other GFL_*
 #define GFL_AIR			128
 
 int numnodeswitches;
@@ -85,9 +85,9 @@
 	ClientName(bs->client, netname, sizeof(netname));
 	BotAI_Print(PRT_MESSAGE, "%s at %1.1f switched more than %d AI nodes\n", netname, FloatTime(), MAX_NODESWITCHES);
 	for (i = 0; i < numnodeswitches; i++) {
-		BotAI_Print(PRT_MESSAGE, "%s", nodeswitch[i]);
+		BotAI_Print(PRT_MESSAGE, nodeswitch[i]);
 	}
-	BotAI_Print(PRT_FATAL, "\n");
+	BotAI_Print(PRT_FATAL, "");
 }
 
 /*
@@ -102,7 +102,7 @@
 	Com_sprintf(nodeswitch[numnodeswitches], 144, "%s at %2.1f entered %s: %s from %s\n", netname, FloatTime(), node, str, s);
 #ifdef DEBUG
 	if (0) {
-		BotAI_Print(PRT_MESSAGE, "%s", nodeswitch[numnodeswitches]);
+		BotAI_Print(PRT_MESSAGE, nodeswitch[numnodeswitches]);
 	}
 #endif //DEBUG
 	numnodeswitches++;
@@ -193,8 +193,8 @@
 
 	//check if the bot should go for air
 	if (BotGoForAir(bs, tfl, ltg, range)) return qtrue;
-	// if the bot is carrying a flag or cubes
-	if (BotCTFCarryingFlag(bs)  ||  Bot1FCTFCarryingFlag(bs)  ||  BotHarvesterCarryingCubes(bs)) {
+	//if the bot is carrying the enemy flag
+	if (BotCTFCarryingFlag(bs)) {
 		//if the bot is just a few secs away from the base 
 		if (trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin,
 				bs->teamgoal.areanum, TFL_DEFAULT) < 300) {
@@ -325,7 +325,7 @@
 ==================
 BotGetLongTermGoal
 
-we could also create a separate AI node for every long term goal type
+we could also create a seperate AI node for every long term goal type
 however this saves us a lot of code
 ==================
 */
@@ -569,10 +569,11 @@
 			bs->teammessage_time = 0;
 		}
 		//
-		if (bs->killedenemy_time > bs->teamgoal_time - TEAM_KILL_SOMEONE && bs->lastkilledplayer == bs->teamgoal.entitynum) {
+		if (bs->lastkilledplayer == bs->teamgoal.entitynum) {
 			EasyClientName(bs->teamgoal.entitynum, buf, sizeof(buf));
 			BotAI_BotInitialChat(bs, "kill_done", buf, NULL);
 			trap_BotEnterChat(bs->cs, bs->decisionmaker, CHAT_TELL);
+			bs->lastkilledplayer = -1;
 			bs->ltgtype = 0;
 		}
 		//
@@ -683,7 +684,9 @@
 				bs->ltgtype = 0;
 			}
 			//
-			//FIXME: move around a bit
+			if (bs->camp_range > 0) {
+				//FIXME: move around a bit
+			}
 			//
 			trap_BotResetAvoidReach(bs->ms);
 			return qfalse;
@@ -830,7 +833,7 @@
 		}
 	}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (bs->ltgtype == LTG_GETFLAG) {
 			//check for bot typing status message
@@ -1297,16 +1300,12 @@
 		return WEAPONINDEX_PLASMAGUN;
 	else if (bs->inventory[INVENTORY_LIGHTNING] > 0 && bs->inventory[INVENTORY_LIGHTNINGAMMO] > 0)
 		return WEAPONINDEX_LIGHTNING;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (bs->inventory[INVENTORY_CHAINGUN] > 0 && bs->inventory[INVENTORY_BELT] > 0)
 		return WEAPONINDEX_CHAINGUN;
 	else if (bs->inventory[INVENTORY_NAILGUN] > 0 && bs->inventory[INVENTORY_NAILS] > 0)
 		return WEAPONINDEX_NAILGUN;
-	else if (bs->inventory[INVENTORY_PROXLAUNCHER] > 0 && bs->inventory[INVENTORY_MINES] > 0)
-		return WEAPONINDEX_PROXLAUNCHER;
 #endif
-	else if (bs->inventory[INVENTORY_GRENADELAUNCHER] > 0 && bs->inventory[INVENTORY_GRENADES] > 0)
-		return WEAPONINDEX_GRENADE_LAUNCHER;
 	else if (bs->inventory[INVENTORY_RAILGUN] > 0 && bs->inventory[INVENTORY_SLUGS] > 0)
 		return WEAPONINDEX_RAILGUN;
 	else if (bs->inventory[INVENTORY_ROCKETLAUNCHER] > 0 && bs->inventory[INVENTORY_ROCKETS] > 0)
@@ -1353,7 +1352,7 @@
 				moveresult->flags |= MOVERESULT_MOVEMENTWEAPON | MOVERESULT_MOVEMENTVIEW;
 				// if holding the right weapon
 				if (bs->cur_ps.weapon == moveresult->weapon) {
-					// if the bot is pretty close with its aim
+					// if the bot is pretty close with it's aim
 					if (InFieldOfVision(bs->viewangles, 20, moveresult->ideal_viewangles)) {
 						//
 						BotAI_Trace(&bsptrace, bs->eye, NULL, NULL, target, bs->entitynum, MASK_SHOT);
@@ -1410,7 +1409,7 @@
 				moveresult->flags |= MOVERESULT_MOVEMENTWEAPON | MOVERESULT_MOVEMENTVIEW;
 				// if holding the right weapon
 				if (bs->cur_ps.weapon == moveresult->weapon) {
-					// if the bot is pretty close with its aim
+					// if the bot is pretty close with it's aim
 					if (InFieldOfVision(bs->viewangles, 20, moveresult->ideal_viewangles)) {
 						//
 						BotAI_Trace(&bsptrace, bs->eye, NULL, NULL, target, bs->entitynum, MASK_SHOT);
@@ -1496,7 +1495,7 @@
 			if (bs->cur_ps.weapon == bs->activatestack->weapon) {
 				VectorSubtract(bs->activatestack->target, bs->eye, dir);
 				vectoangles(dir, ideal_viewangles);
-				// if the bot is pretty close with its aim
+				// if the bot is pretty close with it's aim
 				if (InFieldOfVision(bs->viewangles, 20, ideal_viewangles)) {
 					trap_EA_Attack(bs->client);
 				}
@@ -1879,7 +1878,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -1965,12 +1964,11 @@
 	BotRecordNodeSwitch(bs, "battle fight", "", s);
 	trap_BotResetLastAvoidReach(bs->ms);
 	bs->ainode = AINode_Battle_Fight;
-	bs->flags &= ~BFL_FIGHTSUICIDAL;
 }
 
 /*
 ==================
-AIEnter_Battle_SuicidalFight
+AIEnter_Battle_Fight
 ==================
 */
 void AIEnter_Battle_SuicidalFight(bot_state_t *bs, char *s) {
@@ -2053,7 +2051,7 @@
 	VectorCopy(entinfo.origin, target);
 	// if not a player enemy
 	if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if attacking an obelisk
 		if ( bs->enemy == redobelisk.entitynum ||
 			bs->enemy == blueobelisk.entitynum ) {
@@ -2087,10 +2085,6 @@
 	}
 	//if the enemy is not visible
 	if (!BotEntityVisible(bs->entitynum, bs->eye, bs->viewangles, 360, bs->enemy)) {
-		if (bs->enemy == redobelisk.entitynum || bs->enemy == blueobelisk.entitynum) {
-			AIEnter_Battle_Chase(bs, "battle fight: obelisk out of sight");
-			return qfalse;
-		}
 		if (BotWantsToChase(bs)) {
 			AIEnter_Battle_Chase(bs, "battle fight: enemy out of sight");
 			return qfalse;
@@ -2355,7 +2349,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
@@ -2403,7 +2397,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -2444,7 +2438,7 @@
 	else if (!(moveresult.flags & MOVERESULT_MOVEMENTVIEWSET)
 				&& !(bs->flags & BFL_IDEALVIEWSET) ) {
 		attack_skill = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_ATTACK_SKILL, 0, 1);
-		//if the bot is skilled enough
+		//if the bot is skilled anough
 		if (attack_skill > 0.3) {
 			BotAimAtEnemy(bs);
 		}
@@ -2532,7 +2526,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
@@ -2590,7 +2584,7 @@
 	else if (!(moveresult.flags & MOVERESULT_MOVEMENTVIEWSET)
 				&& !(bs->flags & BFL_IDEALVIEWSET)) {
 		attack_skill = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_ATTACK_SKILL, 0, 1);
-		//if the bot is skilled enough and the enemy is visible
+		//if the bot is skilled anough and the enemy is visible
 		if (attack_skill > 0.3) {
 			//&& BotEntityVisible(bs->entitynum, bs->eye, bs->viewangles, 360, bs->enemy)
 			BotAimAtEnemy(bs);

```

### `ioquake3`  — sha256 `f910595838d0...`, 82567 bytes

_Diff stat: +15 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmnet.c	2026-04-16 20:02:25.181871300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_dmnet.c	2026-04-16 20:02:21.535889700 +0100
@@ -87,7 +87,7 @@
 	for (i = 0; i < numnodeswitches; i++) {
 		BotAI_Print(PRT_MESSAGE, "%s", nodeswitch[i]);
 	}
-	BotAI_Print(PRT_FATAL, "\n");
+	BotAI_Print(PRT_FATAL, "");
 }
 
 /*
@@ -194,7 +194,11 @@
 	//check if the bot should go for air
 	if (BotGoForAir(bs, tfl, ltg, range)) return qtrue;
 	// if the bot is carrying a flag or cubes
-	if (BotCTFCarryingFlag(bs)  ||  Bot1FCTFCarryingFlag(bs)  ||  BotHarvesterCarryingCubes(bs)) {
+	if (BotCTFCarryingFlag(bs)
+#ifdef MISSIONPACK
+		|| Bot1FCTFCarryingFlag(bs) || BotHarvesterCarryingCubes(bs)
+#endif
+		) {
 		//if the bot is just a few secs away from the base 
 		if (trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin,
 				bs->teamgoal.areanum, TFL_DEFAULT) < 300) {
@@ -830,7 +834,7 @@
 		}
 	}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (bs->ltgtype == LTG_GETFLAG) {
 			//check for bot typing status message
@@ -1297,7 +1301,7 @@
 		return WEAPONINDEX_PLASMAGUN;
 	else if (bs->inventory[INVENTORY_LIGHTNING] > 0 && bs->inventory[INVENTORY_LIGHTNINGAMMO] > 0)
 		return WEAPONINDEX_LIGHTNING;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (bs->inventory[INVENTORY_CHAINGUN] > 0 && bs->inventory[INVENTORY_BELT] > 0)
 		return WEAPONINDEX_CHAINGUN;
 	else if (bs->inventory[INVENTORY_NAILGUN] > 0 && bs->inventory[INVENTORY_NAILS] > 0)
@@ -1879,7 +1883,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -2053,7 +2057,7 @@
 	VectorCopy(entinfo.origin, target);
 	// if not a player enemy
 	if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if attacking an obelisk
 		if ( bs->enemy == redobelisk.entitynum ||
 			bs->enemy == blueobelisk.entitynum ) {
@@ -2087,10 +2091,12 @@
 	}
 	//if the enemy is not visible
 	if (!BotEntityVisible(bs->entitynum, bs->eye, bs->viewangles, 360, bs->enemy)) {
+#ifdef MISSIONPACK
 		if (bs->enemy == redobelisk.entitynum || bs->enemy == blueobelisk.entitynum) {
 			AIEnter_Battle_Chase(bs, "battle fight: obelisk out of sight");
 			return qfalse;
 		}
+#endif
 		if (BotWantsToChase(bs)) {
 			AIEnter_Battle_Chase(bs, "battle fight: enemy out of sight");
 			return qfalse;
@@ -2355,7 +2361,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
@@ -2403,7 +2409,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -2532,7 +2538,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {

```

### `openarena-engine`  — sha256 `26d342ad37ee...`, 82534 bytes

_Diff stat: +18 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmnet.c	2026-04-16 20:02:25.181871300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_dmnet.c	2026-04-16 22:48:25.739377700 +0100
@@ -87,7 +87,7 @@
 	for (i = 0; i < numnodeswitches; i++) {
 		BotAI_Print(PRT_MESSAGE, "%s", nodeswitch[i]);
 	}
-	BotAI_Print(PRT_FATAL, "\n");
+	BotAI_Print(PRT_FATAL, "");
 }
 
 /*
@@ -194,7 +194,11 @@
 	//check if the bot should go for air
 	if (BotGoForAir(bs, tfl, ltg, range)) return qtrue;
 	// if the bot is carrying a flag or cubes
-	if (BotCTFCarryingFlag(bs)  ||  Bot1FCTFCarryingFlag(bs)  ||  BotHarvesterCarryingCubes(bs)) {
+	if (BotCTFCarryingFlag(bs)
+#ifdef MISSIONPACK
+		|| Bot1FCTFCarryingFlag(bs) || BotHarvesterCarryingCubes(bs)
+#endif
+		) {
 		//if the bot is just a few secs away from the base 
 		if (trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin,
 				bs->teamgoal.areanum, TFL_DEFAULT) < 300) {
@@ -325,7 +329,7 @@
 ==================
 BotGetLongTermGoal
 
-we could also create a separate AI node for every long term goal type
+we could also create a seperate AI node for every long term goal type
 however this saves us a lot of code
 ==================
 */
@@ -569,10 +573,11 @@
 			bs->teammessage_time = 0;
 		}
 		//
-		if (bs->killedenemy_time > bs->teamgoal_time - TEAM_KILL_SOMEONE && bs->lastkilledplayer == bs->teamgoal.entitynum) {
+		if (bs->lastkilledplayer == bs->teamgoal.entitynum) {
 			EasyClientName(bs->teamgoal.entitynum, buf, sizeof(buf));
 			BotAI_BotInitialChat(bs, "kill_done", buf, NULL);
 			trap_BotEnterChat(bs->cs, bs->decisionmaker, CHAT_TELL);
+			bs->lastkilledplayer = -1;
 			bs->ltgtype = 0;
 		}
 		//
@@ -830,7 +835,7 @@
 		}
 	}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (bs->ltgtype == LTG_GETFLAG) {
 			//check for bot typing status message
@@ -1297,7 +1302,7 @@
 		return WEAPONINDEX_PLASMAGUN;
 	else if (bs->inventory[INVENTORY_LIGHTNING] > 0 && bs->inventory[INVENTORY_LIGHTNINGAMMO] > 0)
 		return WEAPONINDEX_LIGHTNING;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (bs->inventory[INVENTORY_CHAINGUN] > 0 && bs->inventory[INVENTORY_BELT] > 0)
 		return WEAPONINDEX_CHAINGUN;
 	else if (bs->inventory[INVENTORY_NAILGUN] > 0 && bs->inventory[INVENTORY_NAILS] > 0)
@@ -1879,7 +1884,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -2053,7 +2058,7 @@
 	VectorCopy(entinfo.origin, target);
 	// if not a player enemy
 	if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if attacking an obelisk
 		if ( bs->enemy == redobelisk.entitynum ||
 			bs->enemy == blueobelisk.entitynum ) {
@@ -2087,10 +2092,12 @@
 	}
 	//if the enemy is not visible
 	if (!BotEntityVisible(bs->entitynum, bs->eye, bs->viewangles, 360, bs->enemy)) {
+#ifdef MISSIONPACK
 		if (bs->enemy == redobelisk.entitynum || bs->enemy == blueobelisk.entitynum) {
 			AIEnter_Battle_Chase(bs, "battle fight: obelisk out of sight");
 			return qfalse;
 		}
+#endif
 		if (BotWantsToChase(bs)) {
 			AIEnter_Battle_Chase(bs, "battle fight: enemy out of sight");
 			return qfalse;
@@ -2355,7 +2362,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
@@ -2403,7 +2410,7 @@
 				range = 50;
 		}
 #endif //CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
@@ -2532,7 +2539,7 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {

```

### `openarena-gamecode`  — sha256 `6c67f2e5b212...`, 85575 bytes

_Diff stat: +108 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmnet.c	2026-04-16 20:02:25.181871300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_dmnet.c	2026-04-16 22:48:24.158330100 +0100
@@ -64,6 +64,8 @@
 
 #define LOOKAHEAD_DISTANCE			300
 
+extern bot_goal_t dom_points_bot[MAX_DOMINATION_POINTS];
+
 /*
 ==================
 BotResetNodeSwitches
@@ -87,7 +89,7 @@
 	for (i = 0; i < numnodeswitches; i++) {
 		BotAI_Print(PRT_MESSAGE, "%s", nodeswitch[i]);
 	}
-	BotAI_Print(PRT_FATAL, "\n");
+	BotAI_Print(PRT_FATAL, "");
 }
 
 /*
@@ -194,7 +196,7 @@
 	//check if the bot should go for air
 	if (BotGoForAir(bs, tfl, ltg, range)) return qtrue;
 	// if the bot is carrying a flag or cubes
-	if (BotCTFCarryingFlag(bs)  ||  Bot1FCTFCarryingFlag(bs)  ||  BotHarvesterCarryingCubes(bs)) {
+	if (BotCTFCarryingFlag(bs) || Bot1FCTFCarryingFlag(bs) || BotHarvesterCarryingCubes(bs)) {
 		//if the bot is just a few secs away from the base 
 		if (trap_AAS_AreaTravelTimeToGoalArea(bs->areanum, bs->origin,
 				bs->teamgoal.areanum, TFL_DEFAULT) < 300) {
@@ -325,7 +327,7 @@
 ==================
 BotGetLongTermGoal
 
-we could also create a separate AI node for every long term goal type
+we could also create a seperate AI node for every long term goal type
 however this saves us a lot of code
 ==================
 */
@@ -525,6 +527,90 @@
 			bs->defendaway_time = 0;
 		}
 	}
+	//For double domination
+	if (bs->ltgtype == LTG_POINTA &&
+				bs->defendaway_time < FloatTime()) {
+		//check for bot typing status message
+		if (bs->teammessage_time && bs->teammessage_time < FloatTime()) {
+			trap_BotGoalName(bs->teamgoal.number, buf, sizeof(buf));
+			BotAI_BotInitialChat(bs, "dd_start_pointa", buf, NULL);
+			trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
+			//BotVoiceChatOnly(bs, -1, VOICECHAT_ONDEFENSE);
+			bs->teammessage_time = 0;
+		}
+		//set the bot goal
+		memcpy(goal, &ctf_redflag, sizeof(bot_goal_t));
+		//if very close... go away for some time
+		VectorSubtract(goal->origin, bs->origin, dir);
+		if (VectorLengthSquared(dir) < Square(70)) {
+			trap_BotResetAvoidReach(bs->ms);
+			bs->defendaway_time = FloatTime() + 3 + 3 * random();
+			if (BotHasPersistantPowerupAndWeapon(bs)) {
+				bs->defendaway_range = 100;
+			}
+			else {
+				bs->defendaway_range = 350;
+			}
+		}
+		return qtrue;
+	}
+	if (bs->ltgtype == LTG_POINTB &&
+				bs->defendaway_time < FloatTime()) {
+		//check for bot typing status message
+		if (bs->teammessage_time && bs->teammessage_time < FloatTime()) {
+			trap_BotGoalName(bs->teamgoal.number, buf, sizeof(buf));
+			BotAI_BotInitialChat(bs, "dd_start_pointb", buf, NULL);
+			trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
+			//BotVoiceChatOnly(bs, -1, VOICECHAT_ONDEFENSE);
+			bs->teammessage_time = 0;
+		}
+		//set the bot goal
+		memcpy(goal, &ctf_blueflag, sizeof(bot_goal_t));
+		//if very close... go away for some time
+		VectorSubtract(goal->origin, bs->origin, dir);
+		if (VectorLengthSquared(dir) < Square(70)) {
+			trap_BotResetAvoidReach(bs->ms);
+			bs->defendaway_time = FloatTime() + 3 + 3 * random();
+			if (BotHasPersistantPowerupAndWeapon(bs)) {
+				bs->defendaway_range = 100;
+			}
+			else {
+				bs->defendaway_range = 350;
+			}
+		}
+		return qtrue;
+	}
+        //if (bs->ltgtype == LTG_DOMHOLD &&
+	//			bs->defendaway_time < FloatTime()) {
+            //check for bot typing status message
+		/*if (bs->teammessage_time && bs->teammessage_time < FloatTime()) {
+			trap_BotGoalName(bs->teamgoal.number, buf, sizeof(buf));
+			BotAI_BotInitialChat(bs, "dd_start_pointb", buf, NULL);
+			trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
+			//BotVoiceChatOnly(bs, -1, VOICECHAT_ONDEFENSE);
+			bs->teammessage_time = 0;
+		}*/
+		//set the bot goal
+	//	memcpy(goal, &bs->teamgoal, sizeof(bot_goal_t));
+		//if very close... go away for some time
+	//	VectorSubtract(goal->origin, bs->origin, dir);
+	//	if (VectorLengthSquared(dir) < Square(30)) {
+			/*trap_BotResetAvoidReach(bs->ms);
+			bs->defendaway_time = FloatTime() + 3 + 3 * random();
+			if (BotHasPersistantPowerupAndWeapon(bs)) {
+				bs->defendaway_range = 100;
+			}
+			else {
+				bs->defendaway_range = 350;
+			}*/
+          //              memcpy(&bs->teamgoal, &dom_points_bot[((rand()) % (level.domination_points_count))], sizeof(bot_goal_t));
+            //            BotAlternateRoute(bs, &bs->teamgoal);
+              //          BotSetTeamStatus(bs);
+
+		//}
+		//return qtrue;
+
+       // }
 	//if defending a key area
 	if (bs->ltgtype == LTG_DEFENDKEYAREA && !retreat &&
 				bs->defendaway_time < FloatTime()) {
@@ -683,7 +769,9 @@
 				bs->ltgtype = 0;
 			}
 			//
-			//FIXME: move around a bit
+			if (bs->camp_range > 0) {
+				//FIXME: move around a bit
+			}
 			//
 			trap_BotResetAvoidReach(bs->ms);
 			return qfalse;
@@ -744,8 +832,8 @@
 		memcpy(goal, &bs->curpatrolpoint->goal, sizeof(bot_goal_t));
 		return qtrue;
 	}
-#ifdef CTF
-	if (gametype == GT_CTF) {
+	
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		//if going for enemy flag
 		if (bs->ltgtype == LTG_GETFLAG) {
 			//check for bot typing status message
@@ -829,8 +917,6 @@
 			return qtrue;
 		}
 	}
-#endif //CTF
-#if 1  //def MPACK
 	else if (gametype == GT_1FCTF) {
 		if (bs->ltgtype == LTG_GETFLAG) {
 			//check for bot typing status message
@@ -1026,7 +1112,7 @@
 			return qtrue;
 		}
 	}
-#endif
+//#endif
 	//normal goal stuff
 	return BotGetItemLongTermGoal(bs, tfl, goal);
 }
@@ -1297,14 +1383,12 @@
 		return WEAPONINDEX_PLASMAGUN;
 	else if (bs->inventory[INVENTORY_LIGHTNING] > 0 && bs->inventory[INVENTORY_LIGHTNINGAMMO] > 0)
 		return WEAPONINDEX_LIGHTNING;
-#if 1  //def MPACK
 	else if (bs->inventory[INVENTORY_CHAINGUN] > 0 && bs->inventory[INVENTORY_BELT] > 0)
 		return WEAPONINDEX_CHAINGUN;
 	else if (bs->inventory[INVENTORY_NAILGUN] > 0 && bs->inventory[INVENTORY_NAILS] > 0)
 		return WEAPONINDEX_NAILGUN;
 	else if (bs->inventory[INVENTORY_PROXLAUNCHER] > 0 && bs->inventory[INVENTORY_MINES] > 0)
 		return WEAPONINDEX_PROXLAUNCHER;
-#endif
 	else if (bs->inventory[INVENTORY_GRENADELAUNCHER] > 0 && bs->inventory[INVENTORY_GRENADES] > 0)
 		return WEAPONINDEX_GRENADE_LAUNCHER;
 	else if (bs->inventory[INVENTORY_RAILGUN] > 0 && bs->inventory[INVENTORY_SLUGS] > 0)
@@ -1353,7 +1437,7 @@
 				moveresult->flags |= MOVERESULT_MOVEMENTWEAPON | MOVERESULT_MOVEMENTVIEW;
 				// if holding the right weapon
 				if (bs->cur_ps.weapon == moveresult->weapon) {
-					// if the bot is pretty close with its aim
+					// if the bot is pretty close with it's aim
 					if (InFieldOfVision(bs->viewangles, 20, moveresult->ideal_viewangles)) {
 						//
 						BotAI_Trace(&bsptrace, bs->eye, NULL, NULL, target, bs->entitynum, MASK_SHOT);
@@ -1410,7 +1494,7 @@
 				moveresult->flags |= MOVERESULT_MOVEMENTWEAPON | MOVERESULT_MOVEMENTVIEW;
 				// if holding the right weapon
 				if (bs->cur_ps.weapon == moveresult->weapon) {
-					// if the bot is pretty close with its aim
+					// if the bot is pretty close with it's aim
 					if (InFieldOfVision(bs->viewangles, 20, moveresult->ideal_viewangles)) {
 						//
 						BotAI_Trace(&bsptrace, bs->eye, NULL, NULL, target, bs->entitynum, MASK_SHOT);
@@ -1496,7 +1580,7 @@
 			if (bs->cur_ps.weapon == bs->activatestack->weapon) {
 				VectorSubtract(bs->activatestack->target, bs->eye, dir);
 				vectoangles(dir, ideal_viewangles);
-				// if the bot is pretty close with its aim
+				// if the bot is pretty close with it's aim
 				if (InFieldOfVision(bs->viewangles, 20, ideal_viewangles)) {
 					trap_EA_Attack(bs->client);
 				}
@@ -1872,15 +1956,14 @@
 		if (bs->ltgtype == LTG_DEFENDKEYAREA) range = 400;
 		else range = 150;
 		//
-#ifdef CTF
-		if (gametype == GT_CTF) {
+		
+		if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 			//if carrying a flag the bot shouldn't be distracted too much
 			if (BotCTFCarryingFlag(bs))
 				range = 50;
 		}
-#endif //CTF
-#if 1  //def MPACK
-		else if (gametype == GT_1FCTF) {
+
+		else if (gametype == GT_1FCTF || GT_POSSESSION) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
 		}
@@ -1888,7 +1971,6 @@
 			if (BotHarvesterCarryingCubes(bs))
 				range = 80;
 		}
-#endif
 		//
 		if (BotNearbyGoal(bs, bs->tfl, &goal, range)) {
 			trap_BotResetLastAvoidReach(bs->ms);
@@ -2053,13 +2135,11 @@
 	VectorCopy(entinfo.origin, target);
 	// if not a player enemy
 	if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
 		// if attacking an obelisk
 		if ( bs->enemy == redobelisk.entitynum ||
 			bs->enemy == blueobelisk.entitynum ) {
 			target[2] += 16;
 		}
-#endif
 	}
 	//update the reachability area and origin if possible
 	areanum = BotPointAreaNum(target);
@@ -2355,13 +2435,11 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
 				target[2] += 16;
 			}
-#endif
 		}
 		//update the reachability area and origin if possible
 		areanum = BotPointAreaNum(target);
@@ -2396,15 +2474,14 @@
 	if (bs->check_time < FloatTime()) {
 		bs->check_time = FloatTime() + 1;
 		range = 150;
-#ifdef CTF
-		if (gametype == GT_CTF) {
+		
+		if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 			//if carrying a flag the bot shouldn't be distracted too much
 			if (BotCTFCarryingFlag(bs))
 				range = 50;
 		}
-#endif //CTF
-#if 1  //def MPACK
-		else if (gametype == GT_1FCTF) {
+		
+		else if (gametype == GT_1FCTF || gametype == GT_POSSESSION) {
 			if (Bot1FCTFCarryingFlag(bs))
 				range = 50;
 		}
@@ -2412,7 +2489,6 @@
 			if (BotHarvesterCarryingCubes(bs))
 				range = 80;
 		}
-#endif
 		//
 		if (BotNearbyGoal(bs, bs->tfl, &goal, range)) {
 			trap_BotResetLastAvoidReach(bs->ms);
@@ -2444,7 +2520,7 @@
 	else if (!(moveresult.flags & MOVERESULT_MOVEMENTVIEWSET)
 				&& !(bs->flags & BFL_IDEALVIEWSET) ) {
 		attack_skill = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_ATTACK_SKILL, 0, 1);
-		//if the bot is skilled enough
+		//if the bot is skilled anough
 		if (attack_skill > 0.3) {
 			BotAimAtEnemy(bs);
 		}
@@ -2532,13 +2608,11 @@
 		VectorCopy(entinfo.origin, target);
 		// if not a player enemy
 		if (bs->enemy >= MAX_CLIENTS) {
-#if 1  //def MPACK
 			// if attacking an obelisk
 			if ( bs->enemy == redobelisk.entitynum ||
 				bs->enemy == blueobelisk.entitynum ) {
 				target[2] += 16;
 			}
-#endif
 		}
 		//update the reachability area and origin if possible
 		areanum = BotPointAreaNum(target);
@@ -2590,7 +2664,7 @@
 	else if (!(moveresult.flags & MOVERESULT_MOVEMENTVIEWSET)
 				&& !(bs->flags & BFL_IDEALVIEWSET)) {
 		attack_skill = trap_Characteristic_BFloat(bs->character, CHARACTERISTIC_ATTACK_SKILL, 0, 1);
-		//if the bot is skilled enough and the enemy is visible
+		//if the bot is skilled anough and the enemy is visible
 		if (attack_skill > 0.3) {
 			//&& BotEntityVisible(bs->entitynum, bs->eye, bs->viewangles, 360, bs->enemy)
 			BotAimAtEnemy(bs);

```
