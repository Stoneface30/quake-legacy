# Diff: `code/game/ai_main.h`
**Canonical:** `wolfcamql-src` (sha256 `13cd1da7276d...`, 13961 bytes)

## Variants

### `quake3-source`  — sha256 `fd8f5487c9ca...`, 14298 bytes

_Diff stat: +11 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.h	2026-04-16 20:02:25.183989500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\ai_main.h	2026-04-16 20:02:19.899125900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -128,7 +128,7 @@
 	playerState_t cur_ps;							//current player state
 	int last_eFlags;								//last ps flags
 	usercmd_t lastucmd;								//usercmd from last frame
-	int entityeventTime[MAX_GENTITIES];                             //last entity event time
+	int entityeventTime[1024];						//last entity event time
 	//
 	bot_settings_t settings;						//several bot settings
 	int (*ainode)(struct bot_state_s *bs);			//current AI node
@@ -192,6 +192,7 @@
 	float lastair_time;								//last time the bot had air
 	float teleport_time;							//last time the bot teleported
 	float camp_time;								//last time camped
+	float camp_range;								//camp range
 	float weaponchange_time;						//time the bot started changing weapons
 	float firethrottlewait_time;					//amount of time to wait
 	float firethrottleshoot_time;					//amount of time to shoot
@@ -227,7 +228,7 @@
 	int decisionmaker;								//player who decided to go for this goal
 	int ordered;									//true if ordered to do something
 	float order_time;								//time ordered to do something
-	int owndecision_time;							//time the bot made its own decision
+	int owndecision_time;							//time the bot made it's own decision
 	bot_goal_t teamgoal;							//the team goal
 	bot_goal_t altroutegoal;						//alternative route goal
 	float reachedaltroutegoal_time;					//time the bot reached the alt route goal
@@ -248,7 +249,7 @@
 	float leadmessage_time;							//last time a messaged was sent to the team mate
 	float leadbackup_time;							//time backing up towards team mate
 	//
-	char teamleader[MAX_NETNAME];							//netname of the team leader
+	char teamleader[32];							//netname of the team leader
 	float askteamleader_time;						//time asked for team leader
 	float becometeamleader_time;					//time the bot will become the team leader
 	float teamgiveorders_time;						//time to give team orders
@@ -263,6 +264,11 @@
 	int ctfstrategy;								//ctf strategy
 	char subteam[32];								//sub team name
 	float formation_dist;							//formation team mate intervening space
+	char formation_teammate[16];					//netname of the team mate the bot uses for relative positioning
+	float formation_angle;							//angle relative to the formation team mate
+	vec3_t formation_dir;							//the direction the formation is moving in
+	vec3_t formation_origin;						//origin the bot uses for relative positioning
+	bot_goal_t formation_goal;						//formation goal
 
 	bot_activategoal_t *activatestack;				//first activate goal on the stack
 	bot_activategoal_t activategoalheap[MAX_ACTIVATESTACK];	//activate goal heap
@@ -284,7 +290,7 @@
 #define FloatTime() floattime
 
 // from the game source
-void	QDECL BotAI_Print(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+void	QDECL BotAI_Print(int type, char *fmt, ...);
 void	QDECL QDECL BotAI_BotInitialChat( bot_state_t *bs, char *type, ... );
 void	BotAI_Trace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 int		BotAI_GetClientState( int clientNum, playerState_t *state );

```

### `ioquake3`  — sha256 `c0f63d6f2cd7...`, 13934 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.h	2026-04-16 20:02:25.183989500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\ai_main.h	2026-04-16 20:02:21.537886300 +0100
@@ -128,7 +128,7 @@
 	playerState_t cur_ps;							//current player state
 	int last_eFlags;								//last ps flags
 	usercmd_t lastucmd;								//usercmd from last frame
-	int entityeventTime[MAX_GENTITIES];                             //last entity event time
+	int entityeventTime[MAX_GENTITIES];				//last entity event time
 	//
 	bot_settings_t settings;						//several bot settings
 	int (*ainode)(struct bot_state_s *bs);			//current AI node
@@ -248,7 +248,7 @@
 	float leadmessage_time;							//last time a messaged was sent to the team mate
 	float leadbackup_time;							//time backing up towards team mate
 	//
-	char teamleader[MAX_NETNAME];							//netname of the team leader
+	char teamleader[MAX_NETNAME];					//netname of the team leader
 	float askteamleader_time;						//time asked for team leader
 	float becometeamleader_time;					//time the bot will become the team leader
 	float teamgiveorders_time;						//time to give team orders

```

### `openarena-engine`  — sha256 `91f2d15989e4...`, 13947 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.h	2026-04-16 20:02:25.183989500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\ai_main.h	2026-04-16 22:48:25.741537100 +0100
@@ -128,7 +128,7 @@
 	playerState_t cur_ps;							//current player state
 	int last_eFlags;								//last ps flags
 	usercmd_t lastucmd;								//usercmd from last frame
-	int entityeventTime[MAX_GENTITIES];                             //last entity event time
+	int entityeventTime[MAX_GENTITIES];				//last entity event time
 	//
 	bot_settings_t settings;						//several bot settings
 	int (*ainode)(struct bot_state_s *bs);			//current AI node
@@ -248,7 +248,7 @@
 	float leadmessage_time;							//last time a messaged was sent to the team mate
 	float leadbackup_time;							//time backing up towards team mate
 	//
-	char teamleader[MAX_NETNAME];							//netname of the team leader
+	char teamleader[32];							//netname of the team leader
 	float askteamleader_time;						//time asked for team leader
 	float becometeamleader_time;					//time the bot will become the team leader
 	float teamgiveorders_time;						//time to give team orders
@@ -284,7 +284,7 @@
 #define FloatTime() floattime
 
 // from the game source
-void	QDECL BotAI_Print(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+void	QDECL BotAI_Print(int type, char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 void	QDECL QDECL BotAI_BotInitialChat( bot_state_t *bs, char *type, ... );
 void	BotAI_Trace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 int		BotAI_GetClientState( int clientNum, playerState_t *state );

```

### `openarena-gamecode`  — sha256 `a6fd60711142...`, 14766 bytes

_Diff stat: +19 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\ai_main.h	2026-04-16 20:02:25.183989500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\ai_main.h	2026-04-16 22:48:24.161478900 +0100
@@ -58,6 +58,12 @@
 #define LTG_ATTACKENEMYBASE			13	//attack the enemy base
 #define LTG_MAKELOVE_UNDER			14
 #define LTG_MAKELOVE_ONTOP			15
+//Long term DD goals
+#define LTG_POINTA				16	//Take/Defend point A
+#define LTG_POINTB				17	//Take/Defend point B
+//Long term DD goals
+#define LTG_DOMROAM                             18      //Go for a non taken point.
+#define LTG_DOMHOLD                             19      //Pick a point and hold it.
 //some goal dedication times
 #define TEAM_HELP_TIME				60	//1 minute teamplay help time
 #define TEAM_ACCOMPANY_TIME			600	//10 minutes teamplay accompany time
@@ -73,6 +79,9 @@
 #define CTF_RUSHBASE_TIME			120	//2 minutes ctf rush base time
 #define CTF_RETURNFLAG_TIME			180	//3 minutes to return the flag
 #define CTF_ROAM_TIME				60	//1 minute ctf roam time
+//Time for Double Domination tasks
+#define DD_POINTA				600
+#define DD_POINTB				600
 //patrol flags
 #define PATROL_LOOP					1
 #define PATROL_REVERSE				2
@@ -128,7 +137,7 @@
 	playerState_t cur_ps;							//current player state
 	int last_eFlags;								//last ps flags
 	usercmd_t lastucmd;								//usercmd from last frame
-	int entityeventTime[MAX_GENTITIES];                             //last entity event time
+	int entityeventTime[1024];						//last entity event time
 	//
 	bot_settings_t settings;						//several bot settings
 	int (*ainode)(struct bot_state_s *bs);			//current AI node
@@ -192,6 +201,7 @@
 	float lastair_time;								//last time the bot had air
 	float teleport_time;							//last time the bot teleported
 	float camp_time;								//last time camped
+	float camp_range;								//camp range
 	float weaponchange_time;						//time the bot started changing weapons
 	float firethrottlewait_time;					//amount of time to wait
 	float firethrottleshoot_time;					//amount of time to shoot
@@ -227,7 +237,7 @@
 	int decisionmaker;								//player who decided to go for this goal
 	int ordered;									//true if ordered to do something
 	float order_time;								//time ordered to do something
-	int owndecision_time;							//time the bot made its own decision
+	int owndecision_time;							//time the bot made it's own decision
 	bot_goal_t teamgoal;							//the team goal
 	bot_goal_t altroutegoal;						//alternative route goal
 	float reachedaltroutegoal_time;					//time the bot reached the alt route goal
@@ -248,7 +258,7 @@
 	float leadmessage_time;							//last time a messaged was sent to the team mate
 	float leadbackup_time;							//time backing up towards team mate
 	//
-	char teamleader[MAX_NETNAME];							//netname of the team leader
+	char teamleader[MAX_NETNAME];					//netname of the team leader
 	float askteamleader_time;						//time asked for team leader
 	float becometeamleader_time;					//time the bot will become the team leader
 	float teamgiveorders_time;						//time to give team orders
@@ -263,6 +273,11 @@
 	int ctfstrategy;								//ctf strategy
 	char subteam[32];								//sub team name
 	float formation_dist;							//formation team mate intervening space
+	char formation_teammate[16];					//netname of the team mate the bot uses for relative positioning
+	float formation_angle;							//angle relative to the formation team mate
+	vec3_t formation_dir;							//the direction the formation is moving in
+	vec3_t formation_origin;						//origin the bot uses for relative positioning
+	bot_goal_t formation_goal;						//formation goal
 
 	bot_activategoal_t *activatestack;				//first activate goal on the stack
 	bot_activategoal_t activategoalheap[MAX_ACTIVATESTACK];	//activate goal heap
@@ -284,7 +299,7 @@
 #define FloatTime() floattime
 
 // from the game source
-void	QDECL BotAI_Print(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+void	QDECL BotAI_Print(int type, const char *fmt, ...) __attribute__((format(printf,2,3)));
 void	QDECL QDECL BotAI_BotInitialChat( bot_state_t *bs, char *type, ... );
 void	BotAI_Trace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 int		BotAI_GetClientState( int clientNum, playerState_t *state );

```
