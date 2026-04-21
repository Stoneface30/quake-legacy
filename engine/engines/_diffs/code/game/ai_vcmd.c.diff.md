# Diff: `code/game/ai_vcmd.c`
**Canonical:** `wolfcamql-src` (sha256 `4beb610eebb9...`, 15010 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `4d61794d60ab...`, 14905 bytes

_Diff stat: +15 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_vcmd.c	2026-04-16 20:02:25.185049600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_vcmd.c	2026-04-16 20:02:19.900127000 +0100
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
@@ -513,8 +513,7 @@
 };
 
 int BotVoiceChatCommand(bot_state_t *bs, int mode, char *voiceChat) {
-	int i, clientNum;
-	//int voiceOnly, color;
+	int i, voiceOnly, clientNum, color;
 	char *ptr, buf[MAX_MESSAGE_SIZE], *cmd;
 
 	if (!TeamPlayIsOn()) {
@@ -527,15 +526,15 @@
 
 	Q_strncpyz(buf, voiceChat, sizeof(buf));
 	cmd = buf;
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
-	//voiceOnly = atoi(ptr);
+	voiceOnly = atoi(ptr);
 	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
 	clientNum = atoi(ptr);
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
-	//color = atoi(ptr);
+	color = atoi(ptr);
 
 	if (!BotSameTeam(bs, clientNum)) {
 		return qfalse;

```

### `openarena-engine`  — sha256 `f5411fd1e626...`, 15028 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_vcmd.c	2026-04-16 20:02:25.185049600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_vcmd.c	2026-04-16 22:48:25.742535200 +0100
@@ -527,13 +527,13 @@
 
 	Q_strncpyz(buf, voiceChat, sizeof(buf));
 	cmd = buf;
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
 	//voiceOnly = atoi(ptr);
 	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
 	clientNum = atoi(ptr);
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
 	//color = atoi(ptr);
 

```

### `openarena-gamecode`  — sha256 `9f3b0cf97a8f...`, 14967 bytes

_Diff stat: +12 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_vcmd.c	2026-04-16 20:02:25.185049600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_vcmd.c	2026-04-16 22:48:24.162477200 +0100
@@ -71,16 +71,14 @@
 */
 void BotVoiceChat_GetFlag(bot_state_t *bs, int client, int mode) {
 	//
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
 	else {
 		return;
 	}
@@ -95,7 +93,7 @@
 	//set the team goal time
 	bs->teamgoal_time = FloatTime() + CTF_GETFLAG_TIME;
 	// get an alternate route in ctf
-	if (gametype == GT_CTF) {
+	if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION) {
 		//get an alternative route goal towards the enemy base
 		BotGetAlternateRouteGoal(bs, BotOppositeTeam(bs));
 	}
@@ -114,15 +112,10 @@
 ==================
 */
 void BotVoiceChat_Offense(bot_state_t *bs, int client, int mode) {
-	if ( gametype == GT_CTF
-#ifdef MISSIONPACK
-		|| gametype == GT_1FCTF
-#endif
-		) {
+	if ( gametype == GT_CTF || gametype == GT_CTF_ELIMINATION || gametype == GT_1FCTF ) {
 		BotVoiceChat_GetFlag(bs, client, mode);
 		return;
 	}
-#ifdef MISSIONPACK
 	if (gametype == GT_HARVESTER) {
 		//
 		bs->decisionmaker = client;
@@ -141,7 +134,6 @@
 		BotRememberLastOrderedTask(bs);
 	}
 	else
-#endif
 	{
 		//
 		bs->decisionmaker = client;
@@ -170,7 +162,6 @@
 ==================
 */
 void BotVoiceChat_Defend(bot_state_t *bs, int client, int mode) {
-#ifdef MISSIONPACK
 	if ( gametype == GT_OBELISK || gametype == GT_HARVESTER) {
 		//
 		switch(BotTeam(bs)) {
@@ -180,14 +171,9 @@
 		}
 	}
 	else
-#endif
-		if (gametype == GT_CTF
-#ifdef MISSIONPACK
-			|| gametype == GT_1FCTF
-#endif
-			) {
-		//
-		switch(BotTeam(bs)) {
+		if (gametype == GT_CTF || gametype == GT_CTF_ELIMINATION || gametype == GT_1FCTF ) {
+                    //
+                    switch(BotTeam(bs)) {
 			case TEAM_RED: memcpy(&bs->teamgoal, &ctf_redflag, sizeof(bot_goal_t)); break;
 			case TEAM_BLUE: memcpy(&bs->teamgoal, &ctf_blueflag, sizeof(bot_goal_t)); break;
 			default: return;
@@ -382,12 +368,7 @@
 */
 void BotVoiceChat_ReturnFlag(bot_state_t *bs, int client, int mode) {
 	//if not in CTF mode
-	if (
-		gametype != GT_CTF
-#ifdef MISSIONPACK
-		&& gametype != GT_1FCTF
-#endif
-		) {
+	if ( gametype != GT_CTF && gametype != GT_CTF_ELIMINATION && gametype != GT_1FCTF ) {
 		return;
 	}
 	//
@@ -424,7 +405,7 @@
 void BotVoiceChat_StopLeader(bot_state_t *bs, int client, int mode) {
 	char netname[MAX_MESSAGE_SIZE];
 
-	if (!Q_stricmp(bs->teamleader, ClientName(client, netname, sizeof(netname)))) {
+	if (Q_strequal(bs->teamleader, ClientName(client, netname, sizeof(netname)))) {
 		bs->teamleader[0] = '\0';
 		notleader[client] = qtrue;
 	}
@@ -442,7 +423,7 @@
 
 	ClientName(bs->client, netname, sizeof(netname));
 	//if this bot IS the team leader
-	if (!Q_stricmp(netname, bs->teamleader)) {
+	if (Q_strequal(netname, bs->teamleader)) {
 		BotAI_BotInitialChat(bs, "iamteamleader", NULL);
 		trap_BotEnterChat(bs->cs, 0, CHAT_TEAM);
 		BotVoiceChatOnly(bs, -1, VOICECHAT_STARTLEADER);
@@ -514,7 +495,6 @@
 
 int BotVoiceChatCommand(bot_state_t *bs, int mode, char *voiceChat) {
 	int i, clientNum;
-	//int voiceOnly, color;
 	char *ptr, buf[MAX_MESSAGE_SIZE], *cmd;
 
 	if (!TeamPlayIsOn()) {
@@ -527,22 +507,20 @@
 
 	Q_strncpyz(buf, voiceChat, sizeof(buf));
 	cmd = buf;
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
-	//voiceOnly = atoi(ptr);
 	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
 	clientNum = atoi(ptr);
-	for (; *cmd && *cmd > ' '; cmd++);
+	for (ptr = cmd; *cmd && *cmd > ' '; cmd++);
 	while (*cmd && *cmd <= ' ') *cmd++ = '\0';
-	//color = atoi(ptr);
 
 	if (!BotSameTeam(bs, clientNum)) {
 		return qfalse;
 	}
 
 	for (i = 0; voiceCommands[i].cmd; i++) {
-		if (!Q_stricmp(cmd, voiceCommands[i].cmd)) {
+		if (Q_strequal(cmd, voiceCommands[i].cmd)) {
 			voiceCommands[i].func(bs, clientNum, mode);
 			return qtrue;
 		}

```
