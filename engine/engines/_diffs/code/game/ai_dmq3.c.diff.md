# Diff: `code/game/ai_dmq3.c`
**Canonical:** `wolfcamql-src` (sha256 `4a5b5d5f382f...`, 164225 bytes)

## Variants

### `quake3-source`  — sha256 `13b5a774c366...`, 163507 bytes

_Diff stat: +168 / -202 lines_

_(full diff is 37438 bytes — see files directly)_

### `ioquake3`  — sha256 `25be1fd63bfb...`, 164016 bytes

_Diff stat: +44 / -49 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_dmq3.c	2026-04-16 20:02:25.182951300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_dmq3.c	2026-04-16 20:02:21.536888800 +0100
@@ -91,7 +91,7 @@
 //CTF flag goals
 bot_goal_t ctf_redflag;
 bot_goal_t ctf_blueflag;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 bot_goal_t ctf_neutralflag;
 bot_goal_t redobelisk;
 bot_goal_t blueobelisk;
@@ -142,11 +142,10 @@
 int BotTeam(bot_state_t *bs) {
 
 	if (bs->client < 0 || bs->client >= MAX_CLIENTS) {
-		//BotAI_Print(PRT_ERROR, "BotCTFTeam: client out of range\n");
 		return qfalse;
 	}
 
-	if (level.clients[bs->client].sess.sessionTeam == TEAM_RED) {
+    if (level.clients[bs->client].sess.sessionTeam == TEAM_RED) {
 		return TEAM_RED;
 	} else if (level.clients[bs->client].sess.sessionTeam == TEAM_BLUE) {
 		return TEAM_BLUE;
@@ -226,7 +225,7 @@
 		return qtrue;
 	if ( entinfo->powerups & ( 1 << PW_BLUEFLAG ) )
 		return qtrue;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( entinfo->powerups & ( 1 << PW_NEUTRALFLAG ) )
 		return qtrue;
 #endif
@@ -285,7 +284,7 @@
 	return qfalse;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 EntityHasKamikze
@@ -362,7 +361,7 @@
 ==================
 */
 void BotSetTeamStatus(bot_state_t *bs) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int teamtask;
 	aas_entityinfo_t entinfo;
 
@@ -793,7 +792,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 Bot1FCTFSeekGoals
@@ -1333,7 +1332,7 @@
 		if (gametype == GT_CTF) {
 			BotCTFRetreatGoals(bs);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			Bot1FCTFRetreatGoals(bs);
 		}
@@ -1350,7 +1349,7 @@
 			//decide what to do in CTF mode
 			BotCTFSeekGoals(bs);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (gametype == GT_1FCTF) {
 			Bot1FCTFSeekGoals(bs);
 		}
@@ -1485,7 +1484,7 @@
 	char name[128] = {0};
 
 	ClientName(client, name, sizeof(name));
-
+	
 	for (i = 0; name[i]; i++) name[i] &= 127;
 	//remove all spaces
 	for (ptr = strstr(name, " "); ptr; ptr = strstr(name, " ")) {
@@ -1534,14 +1533,14 @@
 	context = CONTEXT_NORMAL|CONTEXT_NEARBYITEM|CONTEXT_NAMES;
 	//
 	if (gametype == GT_CTF
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		|| gametype == GT_1FCTF
 #endif
 		) {
 		if (BotTeam(bs) == TEAM_RED) context |= CONTEXT_CTFREDTEAM;
 		else context |= CONTEXT_CTFBLUETEAM;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_OBELISK) {
 		if (BotTeam(bs) == TEAM_RED) context |= CONTEXT_OBELISKREDTEAM;
 		else context |= CONTEXT_OBELISKBLUETEAM;
@@ -1618,7 +1617,7 @@
 ==================
 */
 void BotCheckItemPickup(bot_state_t *bs, int *oldinventory) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int offence, leader;
 
 	if (gametype <= GT_TEAM)
@@ -1643,7 +1642,7 @@
 		if (!oldinventory[INVENTORY_DOUBLER] && bs->inventory[INVENTORY_DOUBLER] >= 1) {
 			offence = qfalse;
 		}
-		if (!oldinventory[INVENTORY_ARMORREGEN] && bs->inventory[INVENTORY_ARMORREGEN] >= 1) {
+		if (!oldinventory[INVENTORY_AMMOREGEN] && bs->inventory[INVENTORY_AMMOREGEN] >= 1) {
 			offence = qfalse;
 		}
 	}
@@ -1728,7 +1727,7 @@
 	bs->inventory[INVENTORY_PLASMAGUN] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_PLASMAGUN)) != 0;
 	bs->inventory[INVENTORY_BFG10K] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_BFG)) != 0;
 	bs->inventory[INVENTORY_GRAPPLINGHOOK] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_GRAPPLING_HOOK)) != 0;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	bs->inventory[INVENTORY_NAILGUN] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_NAILGUN)) != 0;;
 	bs->inventory[INVENTORY_PROXLAUNCHER] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_PROX_LAUNCHER)) != 0;;
 	bs->inventory[INVENTORY_CHAINGUN] = (bs->cur_ps.stats[STAT_WEAPONS] & (1 << WP_CHAINGUN)) != 0;;
@@ -1742,7 +1741,7 @@
 	bs->inventory[INVENTORY_ROCKETS] = bs->cur_ps.ammo[WP_ROCKET_LAUNCHER];
 	bs->inventory[INVENTORY_SLUGS] = bs->cur_ps.ammo[WP_RAILGUN];
 	bs->inventory[INVENTORY_BFGAMMO] = bs->cur_ps.ammo[WP_BFG];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	bs->inventory[INVENTORY_NAILS] = bs->cur_ps.ammo[WP_NAILGUN];
 	bs->inventory[INVENTORY_MINES] = bs->cur_ps.ammo[WP_PROX_LAUNCHER];
 	bs->inventory[INVENTORY_BELT] = bs->cur_ps.ammo[WP_CHAINGUN];
@@ -1751,7 +1750,7 @@
 	bs->inventory[INVENTORY_HEALTH] = bs->cur_ps.stats[STAT_HEALTH];
 	bs->inventory[INVENTORY_TELEPORTER] = bs->cur_ps.stats[STAT_HOLDABLE_ITEM] == MODELINDEX_TELEPORTER;
 	bs->inventory[INVENTORY_MEDKIT] = bs->cur_ps.stats[STAT_HOLDABLE_ITEM] == MODELINDEX_MEDKIT;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	bs->inventory[INVENTORY_KAMIKAZE] = bs->cur_ps.stats[STAT_HOLDABLE_ITEM] == MODELINDEX_KAMIKAZE;
 	bs->inventory[INVENTORY_PORTAL] = bs->cur_ps.stats[STAT_HOLDABLE_ITEM] == MODELINDEX_PORTAL;
 	bs->inventory[INVENTORY_INVULNERABILITY] = bs->cur_ps.stats[STAT_HOLDABLE_ITEM] == MODELINDEX_INVULNERABILITY;
@@ -1762,15 +1761,15 @@
 	bs->inventory[INVENTORY_INVISIBILITY] = bs->cur_ps.powerups[PW_INVIS] != 0;
 	bs->inventory[INVENTORY_REGEN] = bs->cur_ps.powerups[PW_REGEN] != 0;
 	bs->inventory[INVENTORY_FLIGHT] = bs->cur_ps.powerups[PW_FLIGHT] != 0;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	bs->inventory[INVENTORY_SCOUT] = bs->cur_ps.stats[STAT_PERSISTANT_POWERUP] == MODELINDEX_SCOUT;
 	bs->inventory[INVENTORY_GUARD] = bs->cur_ps.stats[STAT_PERSISTANT_POWERUP] == MODELINDEX_GUARD;
 	bs->inventory[INVENTORY_DOUBLER] = bs->cur_ps.stats[STAT_PERSISTANT_POWERUP] == MODELINDEX_DOUBLER;
-	bs->inventory[INVENTORY_ARMORREGEN] = bs->cur_ps.stats[STAT_PERSISTANT_POWERUP] == MODELINDEX_ARMORREGEN;
+	bs->inventory[INVENTORY_AMMOREGEN] = bs->cur_ps.stats[STAT_PERSISTANT_POWERUP] == MODELINDEX_AMMOREGEN;
 #endif
 	bs->inventory[INVENTORY_REDFLAG] = bs->cur_ps.powerups[PW_REDFLAG] != 0;
 	bs->inventory[INVENTORY_BLUEFLAG] = bs->cur_ps.powerups[PW_BLUEFLAG] != 0;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	bs->inventory[INVENTORY_NEUTRALFLAG] = bs->cur_ps.powerups[PW_NEUTRALFLAG] != 0;
 	if (BotTeam(bs) == TEAM_RED) {
 		bs->inventory[INVENTORY_REDCUBE] = bs->cur_ps.generic1;
@@ -1801,7 +1800,7 @@
 	//FIXME: add num visible enemies and num visible team mates to the inventory
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 BotUseKamikaze
@@ -1924,12 +1923,8 @@
 	bsp_trace_t trace;
 
 	//if the bot has no invulnerability
-	if (bs->inventory[INVENTORY_INVULNERABILITY] <= 0) {
-		//G_Printf("no invuln %d  item %d\n", level.time, bs->cur_ps.stats[STAT_HOLDABLE_ITEM]);
-		//trap_EA_Use(bs->client);
+	if (bs->inventory[INVENTORY_INVULNERABILITY] <= 0)
 		return;
-	}
-
 	if (bs->invulnerability_time > FloatTime())
 		return;
 	bs->invulnerability_time = FloatTime() + 0.2;
@@ -2021,8 +2016,6 @@
 				return;
 			}
 		}
-	} else {
-		trap_EA_Use(bs->client);
 	}
 }
 #endif
@@ -2036,7 +2029,7 @@
 	if (bs->inventory[INVENTORY_HEALTH] < 40) {
 		if (bs->inventory[INVENTORY_TELEPORTER] > 0) {
 			if (!BotCTFCarryingFlag(bs)
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 				&& !Bot1FCTFCarryingFlag(bs)
 				&& !BotHarvesterCarryingCubes(bs)
 #endif
@@ -2050,7 +2043,7 @@
 			trap_EA_Use(bs->client);
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	BotUseKamikaze(bs);
 	BotUseInvulnerability(bs);
 #endif
@@ -2275,7 +2268,7 @@
 		if (BotCTFCarryingFlag(bs))
 			return qtrue;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		//if carrying the flag then always retreat
 		if (Bot1FCTFCarryingFlag(bs))
@@ -2284,7 +2277,7 @@
 	else if (gametype == GT_OBELISK) {
 		//the bots should be dedicated to attacking the enemy obelisk
 		if (bs->ltgtype == LTG_ATTACKENEMYBASE) {
-			if (bs->enemy != redobelisk.entitynum  &&
+			if (bs->enemy != redobelisk.entitynum &&
 						bs->enemy != blueobelisk.entitynum) {
 				return qtrue;
 			}
@@ -2304,8 +2297,10 @@
 		BotEntityInfo(bs->enemy, &entinfo);
 		// if the enemy is carrying a flag
 		if (EntityCarriesFlag(&entinfo)) return qfalse;
+#ifdef MISSIONPACK
 		// if the enemy is carrying cubes
 		if (EntityCarriesCubes(&entinfo)) return qfalse;
+#endif
 	}
 	//if the bot is getting the flag
 	if (bs->ltgtype == LTG_GETFLAG)
@@ -2333,7 +2328,7 @@
 		if (EntityCarriesFlag(&entinfo))
 			return qtrue;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		//never chase if carrying the flag
 		if (Bot1FCTFCarryingFlag(bs))
@@ -2413,12 +2408,12 @@
 ==================
 */
 int BotHasPersistantPowerupAndWeapon(bot_state_t *bs) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// if the bot does not have a persistant powerup
 	if (!bs->inventory[INVENTORY_SCOUT] &&
 		!bs->inventory[INVENTORY_GUARD] &&
 		!bs->inventory[INVENTORY_DOUBLER] &&
-		!bs->inventory[INVENTORY_ARMORREGEN] ) {
+		!bs->inventory[INVENTORY_AMMOREGEN] ) {
 		return qfalse;
 	}
 #endif
@@ -2565,7 +2560,7 @@
 	BotDontAvoid(bs, "Quad Damage");
 	BotDontAvoid(bs, "Regeneration");
 	BotDontAvoid(bs, "Battle Suit");
-	BotDontAvoid(bs, "Haste");
+	BotDontAvoid(bs, "Speed");
 	BotDontAvoid(bs, "Invisibility");
 	//BotDontAvoid(bs, "Flight");
 	//reset the long term goal time so the bot will go for the powerup
@@ -2957,7 +2952,7 @@
 	else {
 		cursquaredist = 0;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (gametype == GT_OBELISK) {
 		vec3_t target;
 		bot_goal_t *goal;
@@ -3201,7 +3196,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 BotTeamCubeCarrierVisible
@@ -3291,7 +3286,7 @@
 	if (bs->enemy >= MAX_CLIENTS) {
 		//if the obelisk is visible
 		VectorCopy(entinfo.origin, target);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if attacking an obelisk
 		if ( bs->enemy == redobelisk.entitynum ||
 			bs->enemy == blueobelisk.entitynum ) {
@@ -3580,7 +3575,7 @@
 	BotEntityInfo(attackentity, &entinfo);
 	// if not attacking a player
 	if (attackentity >= MAX_CLIENTS) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if attacking an obelisk
 		if ( entinfo.number == redobelisk.entitynum ||
 			entinfo.number == blueobelisk.entitynum ) {
@@ -4724,7 +4719,7 @@
 	trap_BotAddAvoidSpot(bs->ms, state->pos.trBase, 160, AVOID_ALWAYS);
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 BotCheckForProxMines
@@ -4777,7 +4772,7 @@
 void BotCheckEvents(bot_state_t *bs, entityState_t *state) {
 	int event;
 	char buf[128];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	aas_entityinfo_t entinfo;
 #endif
 
@@ -4828,7 +4823,7 @@
 				bs->enemysuicide = qtrue;
 			}
 			//
-#if 1  //def MPACK
+#ifdef MISSIONPACK			
 			if (gametype == GT_1FCTF) {
 				//
 				BotEntityInfo(target, &entinfo);
@@ -4861,7 +4856,7 @@
 				bs->flagstatuschanged = qtrue;
 			}
 			else*/
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if (!strcmp(buf, "sound/items/kamikazerespawn.wav" )) {
 				//the kamikaze respawned so don't avoid it
 				BotDontAvoid(bs, "Kamikaze");
@@ -4910,7 +4905,7 @@
 						break; //see BotMatch_CTF
 				}
 			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			else if (gametype == GT_1FCTF) {
 				switch(state->eventParm) {
 					case GTS_RED_CAPTURE:
@@ -5012,7 +5007,7 @@
 		case EV_USE_ITEM12:
 		case EV_USE_ITEM13:
 		case EV_USE_ITEM14:
-	    case EV_USE_ITEM15:
+		case EV_USE_ITEM15:
 			break;
 	}
 }
@@ -5040,7 +5035,7 @@
 		//check for grenades the bot should avoid
 		BotCheckForGrenades(bs, &state);
 		//
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		//check for proximity mines which the bot should deactivate
 		BotCheckForProxMines(bs, &state);
 		//check for dead bodies with the kamikaze effect which should be gibbed
@@ -5141,7 +5136,7 @@
 
 	if (altroutegoals_setup)
 		return;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if (gametype == GT_CTF) {
 		if (trap_BotGetLevelItemGoal(-1, "Neutral Flag", &ctf_neutralflag) < 0)
 			BotAI_Print(PRT_WARNING, "No alt routes without Neutral Flag\n");
@@ -5442,7 +5437,7 @@
 		if (trap_BotGetLevelItemGoal(-1, "Blue Flag", &ctf_blueflag) < 0)
 			BotAI_Print(PRT_WARNING, "CTF without Blue Flag\n");
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (trap_BotGetLevelItemGoal(-1, "Neutral Flag", &ctf_neutralflag) < 0)
 			BotAI_Print(PRT_WARNING, "One Flag CTF without Neutral Flag\n");

```

### `openarena-engine`  — sha256 `d79ac3bf079b...`, 163744 bytes

_Diff stat: +105 / -132 lines_

_(full diff is 25237 bytes — see files directly)_

### `openarena-gamecode`  — sha256 `5fc6bb18975e...`, 169524 bytes

_Diff stat: +876 / -853 lines_

_(full diff is 133604 bytes — see files directly)_
