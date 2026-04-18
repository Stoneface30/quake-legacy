# Diff: `code/game/ai_main.c`
**Canonical:** `wolfcamql-src` (sha256 `943a04116831...`, 47685 bytes)

## Variants

### `quake3-source`  — sha256 `0d5234a0617d...`, 47208 bytes

_Diff stat: +56 / -84 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.c	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_main.c	2026-04-16 20:02:19.899125900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -32,16 +32,16 @@
 
 
 #include "g_local.h"
-#include "../qcommon/q_shared.h"
-#include "../botlib/botlib.h"		//bot lib interface
-#include "../botlib/be_aas.h"
-#include "../botlib/be_ea.h"
-#include "../botlib/be_ai_char.h"
-#include "../botlib/be_ai_chat.h"
-#include "../botlib/be_ai_gen.h"
-#include "../botlib/be_ai_goal.h"
-#include "../botlib/be_ai_move.h"
-#include "../botlib/be_ai_weap.h"
+#include "q_shared.h"
+#include "botlib.h"		//bot lib interface
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
@@ -55,6 +55,8 @@
 #include "inv.h"
 #include "syn.h"
 
+#define MAX_PATH		144
+
 
 //bot states
 bot_state_t	*botstates[MAX_CLIENTS];
@@ -95,7 +97,7 @@
 	va_list ap;
 
 	va_start(ap, fmt);
-	Q_vsnprintf(str, sizeof(str), fmt, ap);
+	vsprintf(str, fmt, ap);
 	va_end(ap);
 
 	switch(type) {
@@ -145,8 +147,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -252,7 +253,7 @@
 	if (bot_testsolid.integer) {
 		if (!trap_AAS_Initialized()) return;
 		areanum = BotPointAreaNum(origin);
-		if (areanum) BotAI_Print(PRT_MESSAGE, "\rempty area");
+		if (areanum) BotAI_Print(PRT_MESSAGE, "\remtpy area");
 		else BotAI_Print(PRT_MESSAGE, "\r^1SOLID area");
 	}
 	else if (bot_testclusters.integer) {
@@ -288,7 +289,7 @@
 			else strcpy(flagstatus, S_COLOR_BLUE"F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			if (BotTeam(bs) == TEAM_RED) strcpy(flagstatus, S_COLOR_RED"F ");
@@ -388,7 +389,7 @@
 	char buf[MAX_INFO_STRING];
 
 	BotAI_Print(PRT_MESSAGE, S_COLOR_RED"RED\n");
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse ) continue;
 		//
@@ -401,7 +402,7 @@
 		}
 	}
 	BotAI_Print(PRT_MESSAGE, S_COLOR_BLUE"BLUE\n");
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse ) continue;
 		//
@@ -437,7 +438,7 @@
 			strcpy(carrying, "F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			strcpy(carrying, "F ");
@@ -542,7 +543,7 @@
 	int i;
 	char buf[MAX_INFO_STRING];
 
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse )
 			continue;
@@ -777,7 +778,7 @@
 		//
 		if (bot_challenge.integer) {
 			//smooth slowdown view model
-			diff = fabs(AngleDifference(bs->viewangles[i], bs->ideal_viewangles[i]));
+			diff = abs(AngleDifference(bs->viewangles[i], bs->ideal_viewangles[i]));
 			anglespeed = diff * factor;
 			if (anglespeed > maxchange) anglespeed = maxchange;
 			bs->viewangles[i] = BotChangeViewAngle(bs->viewangles[i],
@@ -818,7 +819,6 @@
 	vec3_t angles, forward, right;
 	short temp;
 	int j;
-	float f, r, u, m;
 
 	//clear the whole structure
 	memset(ucmd, 0, sizeof(usercmd_t));
@@ -874,38 +874,18 @@
 	//bot input speed is in the range [0, 400]
 	bi->speed = bi->speed * 127 / 400;
 	//set the view independent movement
-	f = DotProduct(forward, bi->dir);
-	r = DotProduct(right, bi->dir);
-	u = fabs(forward[2]) * bi->dir[2];
-	m = fabs(f);
-
-	if (fabs(r) > m) {
-		m = fabs(r);
-	}
-
-	if (fabs(u) > m) {
-		m = fabs(u);
-	}
-
-	if (m > 0) {
-		f *= bi->speed / m;
-		r *= bi->speed / m;
-		u *= bi->speed / m;
-	}
-
-	ucmd->forwardmove = f;
-	ucmd->rightmove = r;
-	ucmd->upmove = u;
-
-	if (bi->actionflags & ACTION_MOVEFORWARD) ucmd->forwardmove = 127;
-	if (bi->actionflags & ACTION_MOVEBACK) ucmd->forwardmove = -127;
-	if (bi->actionflags & ACTION_MOVELEFT) ucmd->rightmove = -127;
-	if (bi->actionflags & ACTION_MOVERIGHT) ucmd->rightmove = 127;
-
+	ucmd->forwardmove = DotProduct(forward, bi->dir) * bi->speed;
+	ucmd->rightmove = DotProduct(right, bi->dir) * bi->speed;
+	ucmd->upmove = abs(forward[2]) * bi->dir[2] * bi->speed;
+	//normal keyboard movement
+	if (bi->actionflags & ACTION_MOVEFORWARD) ucmd->forwardmove += 127;
+	if (bi->actionflags & ACTION_MOVEBACK) ucmd->forwardmove -= 127;
+	if (bi->actionflags & ACTION_MOVELEFT) ucmd->rightmove -= 127;
+	if (bi->actionflags & ACTION_MOVERIGHT) ucmd->rightmove += 127;
 	//jump/moveup
-	if (bi->actionflags & ACTION_JUMP) ucmd->upmove = 127;
+	if (bi->actionflags & ACTION_JUMP) ucmd->upmove += 127;
 	//crouch/movedown
-	if (bi->actionflags & ACTION_CROUCH) ucmd->upmove = -127;
+	if (bi->actionflags & ACTION_CROUCH) ucmd->upmove -= 127;
 	//
 	//Com_Printf("forward = %d right = %d up = %d\n", ucmd.forwardmove, ucmd.rightmove, ucmd.upmove);
 	//Com_Printf("ucmd->serverTime = %d\n", ucmd->serverTime);
@@ -992,10 +972,8 @@
 	}
 
 	//retrieve the current client state
-	if (!BotAI_GetClientState(client, &bs->cur_ps)) {
-		BotAI_Print(PRT_FATAL, "BotAI: failed to get player state for player %d\n", client);
-		return qfalse;
-	}
+	BotAI_GetClientState( client, &bs->cur_ps );
+
 	//retrieve any waiting server commands
 	while( trap_BotGetServerCommand(client, buf, sizeof(buf)) ) {
 		//have buf point to the command and args to the command arguments
@@ -1028,7 +1006,7 @@
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_CHAT, args);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (!Q_stricmp(buf, "vchat")) {
 			BotVoiceChatCommand(bs, SAY_ALL, args);
 		}
@@ -1104,8 +1082,7 @@
 			"%i %i %i %i %i %i %i %i"
 			" %f %f %f"
 			" %f %f %f"
-			" %f %f %f"
-			" %f",
+			" %f %f %f",
 		bs->lastgoal_decisionmaker,
 		bs->lastgoal_ltgtype,
 		bs->lastgoal_teammate,
@@ -1122,8 +1099,7 @@
 		bs->lastgoal_teamgoal.mins[2],
 		bs->lastgoal_teamgoal.maxs[0],
 		bs->lastgoal_teamgoal.maxs[1],
-		bs->lastgoal_teamgoal.maxs[2],
-		bs->formation_dist
+		bs->lastgoal_teamgoal.maxs[2]
 		);
 
 	var = va( "botsession%i", bs->client );
@@ -1147,8 +1123,7 @@
 			"%i %i %i %i %i %i %i %i"
 			" %f %f %f"
 			" %f %f %f"
-			" %f %f %f"
-		    " %f",
+			" %f %f %f",
 		&bs->lastgoal_decisionmaker,
 		&bs->lastgoal_ltgtype,
 		&bs->lastgoal_teammate,
@@ -1165,8 +1140,7 @@
 		&bs->lastgoal_teamgoal.mins[2],
 		&bs->lastgoal_teamgoal.maxs[0],
 		&bs->lastgoal_teamgoal.maxs[1],
-        &bs->lastgoal_teamgoal.maxs[2],
-        &bs->formation_dist
+		&bs->lastgoal_teamgoal.maxs[2]
 		);
 }
 
@@ -1176,18 +1150,13 @@
 ==============
 */
 int BotAISetupClient(int client, struct bot_settings_s *settings, qboolean restart) {
-	char filename[144], name[144], gender[144];
+	char filename[MAX_PATH], name[MAX_PATH], gender[MAX_PATH];
 	bot_state_t *bs;
 	int errnum;
 
 	if (!botstates[client]) botstates[client] = G_Alloc(sizeof(bot_state_t));
 	bs = botstates[client];
 
-	if (!bs) {
-		BotAI_Print(PRT_FATAL, "BotAISetupClient: G_Alloc() failed\n");
-		return qfalse;
-	}
-
 	if (bs && bs->inuse) {
 		BotAI_Print(PRT_FATAL, "BotAISetupClient: client %d already setup\n", client);
 		return qfalse;
@@ -1209,7 +1178,7 @@
 	//allocate a goal state
 	bs->gs = trap_BotAllocGoalState(client);
 	//load the item weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadItemWeights(bs->gs, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1218,7 +1187,7 @@
 	//allocate a weapon state
 	bs->ws = trap_BotAllocWeaponState();
 	//load the weapon weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadWeaponWeights(bs->ws, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1228,8 +1197,8 @@
 	//allocate a chat state
 	bs->cs = trap_BotAllocChatState();
 	//load the chat file
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, sizeof(filename));
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, sizeof(name));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, MAX_PATH);
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, MAX_PATH);
 	errnum = trap_BotLoadChatFile(bs->cs, filename, name);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeChatState(bs->cs);
@@ -1238,7 +1207,7 @@
 		return qfalse;
 	}
 	//get the gender characteristic
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, sizeof(gender));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, MAX_PATH);
 	//set the chat gender
 	if (*gender == 'f' || *gender == 'F') trap_BotSetChatGender(bs->cs, CHAT_GENDERFEMALE);
 	else if (*gender == 'm' || *gender == 'M') trap_BotSetChatGender(bs->cs, CHAT_GENDERMALE);
@@ -1267,7 +1236,7 @@
 	if (restart) {
 		BotReadSessionData(bs);
 	}
-	//bot has been setup successfully
+	//bot has been setup succesfully
 	return qtrue;
 }
 
@@ -1294,7 +1263,7 @@
 	}
 
 	trap_BotFreeMoveState(bs->ms);
-	//free the goal state
+	//free the goal state`			
 	trap_BotFreeGoalState(bs->gs);
 	//free the chat file
 	trap_BotFreeChatState(bs->cs);
@@ -1396,7 +1365,7 @@
 	return qtrue;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace );
 #endif
 
@@ -1513,7 +1482,7 @@
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// never link prox mine triggers
 			if (ent->r.contents == CONTENTS_TRIGGER) {
 				if (ent->touch == ProximityMine_Trigger) {
@@ -1602,7 +1571,8 @@
 	char buf[144];
 
 	//set the maxclients and maxentities library variables before calling BotSetupLibrary
-	Com_sprintf(buf, sizeof(buf), "%d", level.maxclients);
+	trap_Cvar_VariableStringBuffer("sv_maxclients", buf, sizeof(buf));
+	if (!strlen(buf)) strcpy(buf, "8");
 	trap_BotLibVarSet("maxclients", buf);
 	Com_sprintf(buf, sizeof(buf), "%d", MAX_GENTITIES);
 	trap_BotLibVarSet("maxentities", buf);
@@ -1621,11 +1591,10 @@
 	trap_BotLibVarSet("g_gametype", buf);
 	//bot developer mode and log file
 	trap_BotLibVarSet("bot_developer", bot_developer.string);
-	trap_Cvar_VariableStringBuffer("logfile", buf, sizeof(buf));
 	trap_BotLibVarSet("log", buf);
 	//no chatting
 	trap_Cvar_VariableStringBuffer("bot_nochat", buf, sizeof(buf));
-	if (strlen(buf)) trap_BotLibVarSet("nochat", buf);
+	if (strlen(buf)) trap_BotLibVarSet("nochat", "0");
 	//visualize jump pads
 	trap_Cvar_VariableStringBuffer("bot_visualizejumppads", buf, sizeof(buf));
 	if (strlen(buf)) trap_BotLibVarSet("bot_visualizejumppads", buf);
@@ -1654,8 +1623,11 @@
 	//game directory
 	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
 	if (strlen(buf)) trap_BotLibVarSet("gamedir", buf);
+	//cd directory
+	trap_Cvar_VariableStringBuffer("fs_cdpath", buf, sizeof(buf));
+	if (strlen(buf)) trap_BotLibVarSet("cddir", buf);
 	//
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	trap_BotLibDefine("MISSIONPACK");
 #endif
 	//setup the bot library

```

### `ioquake3`  — sha256 `a1742d3d7115...`, 47336 bytes

_Diff stat: +9 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.c	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_main.c	2026-04-16 20:02:21.537886300 +0100
@@ -288,7 +288,7 @@
 			else strcpy(flagstatus, S_COLOR_BLUE"F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			if (BotTeam(bs) == TEAM_RED) strcpy(flagstatus, S_COLOR_RED"F ");
@@ -437,7 +437,7 @@
 			strcpy(carrying, "F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			strcpy(carrying, "F ");
@@ -822,8 +822,6 @@
 
 	//clear the whole structure
 	memset(ucmd, 0, sizeof(usercmd_t));
-	//
-	//Com_Printf("dir = %f %f %f speed = %f\n", bi->dir[0], bi->dir[1], bi->dir[2], bi->speed);
 	//the duration for the user command in milli seconds
 	ucmd->serverTime = time;
 	//
@@ -901,14 +899,10 @@
 	if (bi->actionflags & ACTION_MOVEBACK) ucmd->forwardmove = -127;
 	if (bi->actionflags & ACTION_MOVELEFT) ucmd->rightmove = -127;
 	if (bi->actionflags & ACTION_MOVERIGHT) ucmd->rightmove = 127;
-
 	//jump/moveup
 	if (bi->actionflags & ACTION_JUMP) ucmd->upmove = 127;
 	//crouch/movedown
 	if (bi->actionflags & ACTION_CROUCH) ucmd->upmove = -127;
-	//
-	//Com_Printf("forward = %d right = %d up = %d\n", ucmd.forwardmove, ucmd.rightmove, ucmd.upmove);
-	//Com_Printf("ucmd->serverTime = %d\n", ucmd->serverTime);
 }
 
 /*
@@ -1028,7 +1022,7 @@
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_CHAT, args);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (!Q_stricmp(buf, "vchat")) {
 			BotVoiceChatCommand(bs, SAY_ALL, args);
 		}
@@ -1148,7 +1142,7 @@
 			" %f %f %f"
 			" %f %f %f"
 			" %f %f %f"
-		    " %f",
+			" %f",
 		&bs->lastgoal_decisionmaker,
 		&bs->lastgoal_ltgtype,
 		&bs->lastgoal_teammate,
@@ -1165,8 +1159,8 @@
 		&bs->lastgoal_teamgoal.mins[2],
 		&bs->lastgoal_teamgoal.maxs[0],
 		&bs->lastgoal_teamgoal.maxs[1],
-        &bs->lastgoal_teamgoal.maxs[2],
-        &bs->formation_dist
+		&bs->lastgoal_teamgoal.maxs[2],
+		&bs->formation_dist
 		);
 }
 
@@ -1184,7 +1178,6 @@
 	bs = botstates[client];
 
 	if (!bs) {
-		BotAI_Print(PRT_FATAL, "BotAISetupClient: G_Alloc() failed\n");
 		return qfalse;
 	}
 
@@ -1396,7 +1389,7 @@
 	return qtrue;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace );
 #endif
 
@@ -1513,7 +1506,7 @@
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// never link prox mine triggers
 			if (ent->r.contents == CONTENTS_TRIGGER) {
 				if (ent->touch == ProximityMine_Trigger) {
@@ -1655,7 +1648,7 @@
 	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
 	if (strlen(buf)) trap_BotLibVarSet("gamedir", buf);
 	//
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	trap_BotLibDefine("MISSIONPACK");
 #endif
 	//setup the bot library

```

### `openarena-engine`  — sha256 `8a9fcedcff34...`, 47350 bytes

_Diff stat: +36 / -46 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.c	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_main.c	2026-04-16 22:48:25.741537100 +0100
@@ -55,6 +55,10 @@
 #include "inv.h"
 #include "syn.h"
 
+#ifndef MAX_PATH
+#define MAX_PATH		144
+#endif
+
 
 //bot states
 bot_state_t	*botstates[MAX_CLIENTS];
@@ -145,8 +149,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -252,7 +255,7 @@
 	if (bot_testsolid.integer) {
 		if (!trap_AAS_Initialized()) return;
 		areanum = BotPointAreaNum(origin);
-		if (areanum) BotAI_Print(PRT_MESSAGE, "\rempty area");
+		if (areanum) BotAI_Print(PRT_MESSAGE, "\remtpy area");
 		else BotAI_Print(PRT_MESSAGE, "\r^1SOLID area");
 	}
 	else if (bot_testclusters.integer) {
@@ -288,7 +291,7 @@
 			else strcpy(flagstatus, S_COLOR_BLUE"F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			if (BotTeam(bs) == TEAM_RED) strcpy(flagstatus, S_COLOR_RED"F ");
@@ -388,7 +391,7 @@
 	char buf[MAX_INFO_STRING];
 
 	BotAI_Print(PRT_MESSAGE, S_COLOR_RED"RED\n");
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse ) continue;
 		//
@@ -401,7 +404,7 @@
 		}
 	}
 	BotAI_Print(PRT_MESSAGE, S_COLOR_BLUE"BLUE\n");
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse ) continue;
 		//
@@ -437,7 +440,7 @@
 			strcpy(carrying, "F ");
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			strcpy(carrying, "F ");
@@ -542,7 +545,7 @@
 	int i;
 	char buf[MAX_INFO_STRING];
 
-	for (i = 0; i < level.maxclients; i++) {
+	for (i = 0; i < maxclients && i < MAX_CLIENTS; i++) {
 		//
 		if ( !botstates[i] || !botstates[i]->inuse )
 			continue;
@@ -777,7 +780,7 @@
 		//
 		if (bot_challenge.integer) {
 			//smooth slowdown view model
-			diff = fabs(AngleDifference(bs->viewangles[i], bs->ideal_viewangles[i]));
+			diff = abs(AngleDifference(bs->viewangles[i], bs->ideal_viewangles[i]));
 			anglespeed = diff * factor;
 			if (anglespeed > maxchange) anglespeed = maxchange;
 			bs->viewangles[i] = BotChangeViewAngle(bs->viewangles[i],
@@ -822,8 +825,6 @@
 
 	//clear the whole structure
 	memset(ucmd, 0, sizeof(usercmd_t));
-	//
-	//Com_Printf("dir = %f %f %f speed = %f\n", bi->dir[0], bi->dir[1], bi->dir[2], bi->speed);
 	//the duration for the user command in milli seconds
 	ucmd->serverTime = time;
 	//
@@ -876,7 +877,7 @@
 	//set the view independent movement
 	f = DotProduct(forward, bi->dir);
 	r = DotProduct(right, bi->dir);
-	u = fabs(forward[2]) * bi->dir[2];
+	u = abs(forward[2]) * bi->dir[2];
 	m = fabs(f);
 
 	if (fabs(r) > m) {
@@ -901,14 +902,10 @@
 	if (bi->actionflags & ACTION_MOVEBACK) ucmd->forwardmove = -127;
 	if (bi->actionflags & ACTION_MOVELEFT) ucmd->rightmove = -127;
 	if (bi->actionflags & ACTION_MOVERIGHT) ucmd->rightmove = 127;
-
 	//jump/moveup
 	if (bi->actionflags & ACTION_JUMP) ucmd->upmove = 127;
 	//crouch/movedown
 	if (bi->actionflags & ACTION_CROUCH) ucmd->upmove = -127;
-	//
-	//Com_Printf("forward = %d right = %d up = %d\n", ucmd.forwardmove, ucmd.rightmove, ucmd.upmove);
-	//Com_Printf("ucmd->serverTime = %d\n", ucmd->serverTime);
 }
 
 /*
@@ -992,10 +989,8 @@
 	}
 
 	//retrieve the current client state
-	if (!BotAI_GetClientState(client, &bs->cur_ps)) {
-		BotAI_Print(PRT_FATAL, "BotAI: failed to get player state for player %d\n", client);
-		return qfalse;
-	}
+	BotAI_GetClientState( client, &bs->cur_ps );
+
 	//retrieve any waiting server commands
 	while( trap_BotGetServerCommand(client, buf, sizeof(buf)) ) {
 		//have buf point to the command and args to the command arguments
@@ -1028,7 +1023,7 @@
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_CHAT, args);
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		else if (!Q_stricmp(buf, "vchat")) {
 			BotVoiceChatCommand(bs, SAY_ALL, args);
 		}
@@ -1104,8 +1099,7 @@
 			"%i %i %i %i %i %i %i %i"
 			" %f %f %f"
 			" %f %f %f"
-			" %f %f %f"
-			" %f",
+			" %f %f %f",
 		bs->lastgoal_decisionmaker,
 		bs->lastgoal_ltgtype,
 		bs->lastgoal_teammate,
@@ -1122,8 +1116,7 @@
 		bs->lastgoal_teamgoal.mins[2],
 		bs->lastgoal_teamgoal.maxs[0],
 		bs->lastgoal_teamgoal.maxs[1],
-		bs->lastgoal_teamgoal.maxs[2],
-		bs->formation_dist
+		bs->lastgoal_teamgoal.maxs[2]
 		);
 
 	var = va( "botsession%i", bs->client );
@@ -1147,8 +1140,7 @@
 			"%i %i %i %i %i %i %i %i"
 			" %f %f %f"
 			" %f %f %f"
-			" %f %f %f"
-		    " %f",
+			" %f %f %f",
 		&bs->lastgoal_decisionmaker,
 		&bs->lastgoal_ltgtype,
 		&bs->lastgoal_teammate,
@@ -1165,8 +1157,7 @@
 		&bs->lastgoal_teamgoal.mins[2],
 		&bs->lastgoal_teamgoal.maxs[0],
 		&bs->lastgoal_teamgoal.maxs[1],
-        &bs->lastgoal_teamgoal.maxs[2],
-        &bs->formation_dist
+		&bs->lastgoal_teamgoal.maxs[2]
 		);
 }
 
@@ -1176,18 +1167,13 @@
 ==============
 */
 int BotAISetupClient(int client, struct bot_settings_s *settings, qboolean restart) {
-	char filename[144], name[144], gender[144];
+	char filename[MAX_PATH], name[MAX_PATH], gender[MAX_PATH];
 	bot_state_t *bs;
 	int errnum;
 
 	if (!botstates[client]) botstates[client] = G_Alloc(sizeof(bot_state_t));
 	bs = botstates[client];
 
-	if (!bs) {
-		BotAI_Print(PRT_FATAL, "BotAISetupClient: G_Alloc() failed\n");
-		return qfalse;
-	}
-
 	if (bs && bs->inuse) {
 		BotAI_Print(PRT_FATAL, "BotAISetupClient: client %d already setup\n", client);
 		return qfalse;
@@ -1209,7 +1195,7 @@
 	//allocate a goal state
 	bs->gs = trap_BotAllocGoalState(client);
 	//load the item weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadItemWeights(bs->gs, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1218,7 +1204,7 @@
 	//allocate a weapon state
 	bs->ws = trap_BotAllocWeaponState();
 	//load the weapon weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadWeaponWeights(bs->ws, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1228,8 +1214,8 @@
 	//allocate a chat state
 	bs->cs = trap_BotAllocChatState();
 	//load the chat file
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, sizeof(filename));
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, sizeof(name));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, MAX_PATH);
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, MAX_PATH);
 	errnum = trap_BotLoadChatFile(bs->cs, filename, name);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeChatState(bs->cs);
@@ -1238,7 +1224,7 @@
 		return qfalse;
 	}
 	//get the gender characteristic
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, sizeof(gender));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, MAX_PATH);
 	//set the chat gender
 	if (*gender == 'f' || *gender == 'F') trap_BotSetChatGender(bs->cs, CHAT_GENDERFEMALE);
 	else if (*gender == 'm' || *gender == 'M') trap_BotSetChatGender(bs->cs, CHAT_GENDERMALE);
@@ -1267,7 +1253,7 @@
 	if (restart) {
 		BotReadSessionData(bs);
 	}
-	//bot has been setup successfully
+	//bot has been setup succesfully
 	return qtrue;
 }
 
@@ -1294,7 +1280,7 @@
 	}
 
 	trap_BotFreeMoveState(bs->ms);
-	//free the goal state
+	//free the goal state`			
 	trap_BotFreeGoalState(bs->gs);
 	//free the chat file
 	trap_BotFreeChatState(bs->cs);
@@ -1396,7 +1382,7 @@
 	return qtrue;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace );
 #endif
 
@@ -1513,7 +1499,7 @@
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			// never link prox mine triggers
 			if (ent->r.contents == CONTENTS_TRIGGER) {
 				if (ent->touch == ProximityMine_Trigger) {
@@ -1602,7 +1588,8 @@
 	char buf[144];
 
 	//set the maxclients and maxentities library variables before calling BotSetupLibrary
-	Com_sprintf(buf, sizeof(buf), "%d", level.maxclients);
+	trap_Cvar_VariableStringBuffer("sv_maxclients", buf, sizeof(buf));
+	if (!strlen(buf)) strcpy(buf, "8");
 	trap_BotLibVarSet("maxclients", buf);
 	Com_sprintf(buf, sizeof(buf), "%d", MAX_GENTITIES);
 	trap_BotLibVarSet("maxentities", buf);
@@ -1654,8 +1641,11 @@
 	//game directory
 	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
 	if (strlen(buf)) trap_BotLibVarSet("gamedir", buf);
+	//home directory
+	trap_Cvar_VariableStringBuffer("fs_homepath", buf, sizeof(buf));
+	if (strlen(buf)) trap_BotLibVarSet("homedir", buf);
 	//
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	trap_BotLibDefine("MISSIONPACK");
 #endif
 	//setup the bot library

```

### `openarena-gamecode`  — sha256 `6f5b2f13a3d9...`, 48669 bytes

_Diff stat: +91 / -60 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.c	2026-04-16 20:02:25.183473900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_main.c	2026-04-16 22:48:24.160331200 +0100
@@ -55,6 +55,10 @@
 #include "inv.h"
 #include "syn.h"
 
+#ifndef MAX_PATH
+#define MAX_PATH		144
+#endif
+
 
 //bot states
 bot_state_t	*botstates[MAX_CLIENTS];
@@ -90,7 +94,7 @@
 BotAI_Print
 ==================
 */
-void QDECL BotAI_Print(int type, char *fmt, ...) {
+void QDECL BotAI_Print(int type, const char *fmt, ...) {
 	char str[2048];
 	va_list ap;
 
@@ -145,8 +149,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -185,7 +188,10 @@
 	memset( state, 0, sizeof(entityState_t) );
 	if (!ent->inuse) return qfalse;
 	if (!ent->r.linked) return qfalse;
-	if (ent->r.svFlags & SVF_NOCLIENT) return qfalse;
+	if ( !(g_gametype.integer == GT_ELIMINATION || g_gametype.integer == GT_LMS ||g_instantgib.integer || g_rockets.integer || g_elimination_allgametypes.integer || g_gametype.integer==GT_CTF_ELIMINATION)
+	       && (ent->r.svFlags & SVF_NOCLIENT) ) {
+		return qfalse;
+	}
 	memcpy( state, &ent->s, sizeof(entityState_t) );
 	return qtrue;
 }
@@ -278,17 +284,20 @@
 	char *leader, flagstatus[32];
 	//
 	ClientName(bs->client, netname, sizeof(netname));
-	if (Q_stricmp(netname, bs->teamleader) == 0) leader = "L";
-	else leader = " ";
+	if ( Q_strequal(netname, bs->teamleader) ) {
+		leader = "L";
+	}
+	else {
+		leader = " ";
+	}
 
 	strcpy(flagstatus, "  ");
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		if (BotCTFCarryingFlag(bs)) {
 			if (BotTeam(bs) == TEAM_RED) strcpy(flagstatus, S_COLOR_RED"F ");
 			else strcpy(flagstatus, S_COLOR_BLUE"F ");
 		}
 	}
-#if 1  //def MPACK
 	else if (gametype == GT_1FCTF) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			if (BotTeam(bs) == TEAM_RED) strcpy(flagstatus, S_COLOR_RED"F ");
@@ -301,7 +310,6 @@
 			else Com_sprintf(flagstatus, sizeof(flagstatus), S_COLOR_BLUE"%2d", bs->inventory[INVENTORY_BLUECUBE]);
 		}
 	}
-#endif
 
 	switch(bs->ltgtype) {
 		case LTG_TEAMHELP:
@@ -370,6 +378,16 @@
 			BotAI_Print(PRT_MESSAGE, "%-20s%s%s: harvesting\n", netname, leader, flagstatus);
 			break;
 		}
+		case LTG_POINTA:
+		{
+			BotAI_Print(PRT_MESSAGE, "%-20s%s%s: going for point A\n", netname, leader, flagstatus);
+			break;
+		}
+		case LTG_POINTB:
+		{
+			BotAI_Print(PRT_MESSAGE, "%-20s%s%s: going for point B\n", netname, leader, flagstatus);
+			break;
+		}
 		default:
 		{
 			BotAI_Print(PRT_MESSAGE, "%-20s%s%s: roaming\n", netname, leader, flagstatus);
@@ -428,17 +446,20 @@
 	bot_goal_t goal;
 	//
 	ClientName(bs->client, netname, sizeof(netname));
-	if (Q_stricmp(netname, bs->teamleader) == 0) leader = "L";
-	else leader = " ";
+	if ( Q_strequal(netname, bs->teamleader) ) {
+		leader = "L";
+	}
+	else {
+		leader = " ";
+	}
 
 	strcpy(carrying, "  ");
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		if (BotCTFCarryingFlag(bs)) {
 			strcpy(carrying, "F ");
 		}
 	}
-#if 1  //def MPACK
-	else if (gametype == GT_1FCTF) {
+	else if (gametype == GT_1FCTF || gametype == GT_POSSESSION) {
 		if (Bot1FCTFCarryingFlag(bs)) {
 			strcpy(carrying, "F ");
 		}
@@ -449,7 +470,6 @@
 			else Com_sprintf(carrying, sizeof(carrying), "%2d", bs->inventory[INVENTORY_BLUECUBE]);
 		}
 	}
-#endif
 
 	switch(bs->ltgtype) {
 		case LTG_TEAMHELP:
@@ -518,6 +538,16 @@
 			Com_sprintf(action, sizeof(action), "harvesting");
 			break;
 		}
+		case LTG_POINTA:
+		{
+			Com_sprintf(action, sizeof(action), "going for point A");
+			break;
+		}
+		case LTG_POINTB:
+		{
+			Com_sprintf(action, sizeof(action), "going for point B");
+			break;
+		}
 		default:
 		{
 			trap_BotGetTopGoal(bs->gs, &goal);
@@ -526,11 +556,11 @@
 			break;
 		}
 	}
-  	cs = va("l\\%s\\c\\%s\\a\\%s",
-				leader,
-				carrying,
-				action);
-  	trap_SetConfigstring (CS_BOTINFO + bs->client, cs);
+	cs = va("l\\%s\\c\\%s\\a\\%s",
+	            leader,
+	            carrying,
+	            action);
+	trap_SetConfigstring (CS_BOTINFO + bs->client, cs);
 }
 
 /*
@@ -822,8 +852,6 @@
 
 	//clear the whole structure
 	memset(ucmd, 0, sizeof(usercmd_t));
-	//
-	//Com_Printf("dir = %f %f %f speed = %f\n", bi->dir[0], bi->dir[1], bi->dir[2], bi->speed);
 	//the duration for the user command in milli seconds
 	ucmd->serverTime = time;
 	//
@@ -901,14 +929,10 @@
 	if (bi->actionflags & ACTION_MOVEBACK) ucmd->forwardmove = -127;
 	if (bi->actionflags & ACTION_MOVELEFT) ucmd->rightmove = -127;
 	if (bi->actionflags & ACTION_MOVERIGHT) ucmd->rightmove = 127;
-
 	//jump/moveup
 	if (bi->actionflags & ACTION_JUMP) ucmd->upmove = 127;
 	//crouch/movedown
 	if (bi->actionflags & ACTION_CROUCH) ucmd->upmove = -127;
-	//
-	//Com_Printf("forward = %d right = %d up = %d\n", ucmd.forwardmove, ucmd.rightmove, ucmd.upmove);
-	//Com_Printf("ucmd->serverTime = %d\n", ucmd->serverTime);
 }
 
 /*
@@ -996,6 +1020,7 @@
 		BotAI_Print(PRT_FATAL, "BotAI: failed to get player state for player %d\n", client);
 		return qfalse;
 	}
+
 	//retrieve any waiting server commands
 	while( trap_BotGetServerCommand(client, buf, sizeof(buf)) ) {
 		//have buf point to the command and args to the command arguments
@@ -1006,42 +1031,42 @@
 		//remove color espace sequences from the arguments
 		RemoveColorEscapeSequences( args );
 
-		if (!Q_stricmp(buf, "cp "))
+		if (Q_strequal(buf, "cp "))
 			{ /*CenterPrintf*/ }
-		else if (!Q_stricmp(buf, "cs"))
+		else if (Q_strequal(buf, "cs"))
 			{ /*ConfigStringModified*/ }
-		else if (!Q_stricmp(buf, "print")) {
+		else if (Q_strequal(buf, "print")) {
 			//remove first and last quote from the chat message
 			memmove(args, args+1, strlen(args));
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_NORMAL, args);
 		}
-		else if (!Q_stricmp(buf, "chat")) {
+		else if (Q_strequal(buf, "chat")) {
 			//remove first and last quote from the chat message
 			memmove(args, args+1, strlen(args));
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_CHAT, args);
 		}
-		else if (!Q_stricmp(buf, "tchat")) {
+		else if (Q_strequal(buf, "tchat")) {
 			//remove first and last quote from the chat message
 			memmove(args, args+1, strlen(args));
 			args[strlen(args)-1] = '\0';
 			trap_BotQueueConsoleMessage(bs->cs, CMS_CHAT, args);
 		}
-#if 1  //def MPACK
-		else if (!Q_stricmp(buf, "vchat")) {
+#ifdef MISSIONPACK
+		else if (Q_strequal(buf, "vchat")) {
 			BotVoiceChatCommand(bs, SAY_ALL, args);
 		}
-		else if (!Q_stricmp(buf, "vtchat")) {
+		else if (Q_strequal(buf, "vtchat")) {
 			BotVoiceChatCommand(bs, SAY_TEAM, args);
 		}
-		else if (!Q_stricmp(buf, "vtell")) {
+		else if (Q_strequal(buf, "vtell")) {
 			BotVoiceChatCommand(bs, SAY_TELL, args);
 		}
 #endif
-		else if (!Q_stricmp(buf, "scores"))
+		else if (Q_strequal(buf, "scores"))
 			{ /*FIXME: parse scores?*/ }
-		else if (!Q_stricmp(buf, "clientLevelShot"))
+		else if (Q_strequal(buf, "clientLevelShot"))
 			{ /*ignore*/ }
 	}
 	//add the delta angles to the bot's current view angles
@@ -1148,7 +1173,7 @@
 			" %f %f %f"
 			" %f %f %f"
 			" %f %f %f"
-		    " %f",
+			" %f",
 		&bs->lastgoal_decisionmaker,
 		&bs->lastgoal_ltgtype,
 		&bs->lastgoal_teammate,
@@ -1165,8 +1190,8 @@
 		&bs->lastgoal_teamgoal.mins[2],
 		&bs->lastgoal_teamgoal.maxs[0],
 		&bs->lastgoal_teamgoal.maxs[1],
-        &bs->lastgoal_teamgoal.maxs[2],
-        &bs->formation_dist
+		&bs->lastgoal_teamgoal.maxs[2],
+		&bs->formation_dist
 		);
 }
 
@@ -1176,17 +1201,20 @@
 ==============
 */
 int BotAISetupClient(int client, struct bot_settings_s *settings, qboolean restart) {
-	char filename[144], name[144], gender[144];
+	char filename[MAX_PATH], name[MAX_PATH], gender[MAX_PATH];
 	bot_state_t *bs;
 	int errnum;
-
-	if (!botstates[client]) botstates[client] = G_Alloc(sizeof(bot_state_t));
-	bs = botstates[client];
-
-	if (!bs) {
-		BotAI_Print(PRT_FATAL, "BotAISetupClient: G_Alloc() failed\n");
-		return qfalse;
+	//KK-OAX Changed to Tremulous's BG_Alloc
+	if (!botstates[client]) {
+		if(!BG_CanAlloc(sizeof(bot_state_t))) {
+			//We cannot run BG_Alloc, fail nicely
+			BotAI_Print(PRT_FATAL, "BotAISetupClient: Not enough heap memory\n");
+			return qfalse;
+		}
+		botstates[client] = BG_Alloc(sizeof(bot_state_t));
+		//BG_Allow will succed or terminate
 	}
+	bs = botstates[client];
 
 	if (bs && bs->inuse) {
 		BotAI_Print(PRT_FATAL, "BotAISetupClient: client %d already setup\n", client);
@@ -1209,7 +1237,7 @@
 	//allocate a goal state
 	bs->gs = trap_BotAllocGoalState(client);
 	//load the item weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_ITEMWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadItemWeights(bs->gs, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1218,7 +1246,7 @@
 	//allocate a weapon state
 	bs->ws = trap_BotAllocWeaponState();
 	//load the weapon weights
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, sizeof(filename));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_WEAPONWEIGHTS, filename, MAX_PATH);
 	errnum = trap_BotLoadWeaponWeights(bs->ws, filename);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeGoalState(bs->gs);
@@ -1228,8 +1256,8 @@
 	//allocate a chat state
 	bs->cs = trap_BotAllocChatState();
 	//load the chat file
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, sizeof(filename));
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, sizeof(name));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_FILE, filename, MAX_PATH);
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_CHAT_NAME, name, MAX_PATH);
 	errnum = trap_BotLoadChatFile(bs->cs, filename, name);
 	if (errnum != BLERR_NOERROR) {
 		trap_BotFreeChatState(bs->cs);
@@ -1238,7 +1266,7 @@
 		return qfalse;
 	}
 	//get the gender characteristic
-	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, sizeof(gender));
+	trap_Characteristic_String(bs->character, CHARACTERISTIC_GENDER, gender, MAX_PATH);
 	//set the chat gender
 	if (*gender == 'f' || *gender == 'F') trap_BotSetChatGender(bs->cs, CHAT_GENDERFEMALE);
 	else if (*gender == 'm' || *gender == 'M') trap_BotSetChatGender(bs->cs, CHAT_GENDERMALE);
@@ -1267,7 +1295,7 @@
 	if (restart) {
 		BotReadSessionData(bs);
 	}
-	//bot has been setup successfully
+	//bot has been setup succesfully
 	return qtrue;
 }
 
@@ -1311,6 +1339,7 @@
 	memset(bs, 0, sizeof(bot_state_t));
 	//set the inuse flag to qfalse
 	bs->inuse = qfalse;
+
 	//there's one bot less
 	numbots--;
 	//everything went ok
@@ -1396,9 +1425,7 @@
 	return qtrue;
 }
 
-#if 1  //def MPACK
 void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace );
-#endif
 
 /*
 ==================
@@ -1499,7 +1526,8 @@
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
-			if (ent->r.svFlags & SVF_NOCLIENT) {
+			if ( !(g_gametype.integer == GT_ELIMINATION || g_gametype.integer == GT_LMS ||g_instantgib.integer || g_rockets.integer || g_elimination_allgametypes.integer || g_gametype.integer==GT_CTF_ELIMINATION)
+				   && ent->r.svFlags & SVF_NOCLIENT) {
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
@@ -1513,7 +1541,7 @@
 				trap_BotLibUpdateEntity(i, NULL);
 				continue;
 			}
-#if 1  //def MPACK
+
 			// never link prox mine triggers
 			if (ent->r.contents == CONTENTS_TRIGGER) {
 				if (ent->touch == ProximityMine_Trigger) {
@@ -1521,7 +1549,7 @@
 					continue;
 				}
 			}
-#endif
+
 			//
 			memset(&state, 0, sizeof(bot_entitystate_t));
 			//
@@ -1654,8 +1682,11 @@
 	//game directory
 	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
 	if (strlen(buf)) trap_BotLibVarSet("gamedir", buf);
+	//home directory
+	trap_Cvar_VariableStringBuffer("fs_homepath", buf, sizeof(buf));
+	if (strlen(buf)) trap_BotLibVarSet("homedir", buf);
 	//
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	trap_BotLibDefine("MISSIONPACK");
 #endif
 	//setup the bot library

```
