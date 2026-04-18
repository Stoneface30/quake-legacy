# Diff: `code/botlib/botlib.h`
**Canonical:** `wolfcamql-src` (sha256 `a65504495a4b...`, 23206 bytes)
Also identical in: ioquake3

## Variants

### `quake3e`  — sha256 `ebdf35391a11...`, 23584 bytes

_Diff stat: +42 / -40 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\botlib.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\botlib.h	2026-04-16 20:02:26.904499600 +0100
@@ -170,7 +170,7 @@
 typedef struct botlib_import_s
 {
 	//print messages from the bot library
-	void		(QDECL *Print)(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void		(QDECL *Print)(int type, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 	//trace a bbox through the world
 	void		(*Trace)(bsp_trace_t *trace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 	//trace a bbox against a specific entity
@@ -184,18 +184,18 @@
 	//
 	void		(*BSPModelMinsMaxsOrigin)(int modelnum, vec3_t angles, vec3_t mins, vec3_t maxs, vec3_t origin);
 	//send a bot client command
-	void		(*BotClientCommand)(int client, char *command);
+	void		(*BotClientCommand)( int client, const char *command );
 	//memory allocation
-	void		*(*GetMemory)(int size);		// allocate from Zone
+	void		*(*GetMemory)(size_t size);		// allocate from Zone
 	void		(*FreeMemory)(void *ptr);		// free memory from Zone
 	int			(*AvailableMemory)(void);		// available Zone memory
-	void		*(*HunkAlloc)(int size);		// allocate from hunk
+	void		*(*HunkAlloc)(size_t size);		// allocate from hunk
 	//file system access
 	int			(*FS_FOpenFile)( const char *qpath, fileHandle_t *file, fsMode_t mode );
 	int			(*FS_Read)( void *buffer, int len, fileHandle_t f );
 	int			(*FS_Write)( const void *buffer, int len, fileHandle_t f );
 	void		(*FS_FCloseFile)( fileHandle_t f );
-	int			(*FS_Seek)( fileHandle_t f, long offset, int origin );
+	int			(*FS_Seek)( fileHandle_t f, long offset, fsOrigin_t origin );
 	//debug visualisation stuff
 	int			(*DebugLineCreate)(void);
 	void		(*DebugLineDelete)(int line);
@@ -203,16 +203,18 @@
 	//
 	int			(*DebugPolygonCreate)(int color, int numPoints, vec3_t *points);
 	void		(*DebugPolygonDelete)(int id);
+
+	int			(*Sys_Milliseconds)(void);
 } botlib_import_t;
 
 typedef struct aas_export_s
 {
 	//-----------------------------------
-	// be_aas_entity.h
+	// be_aas_entity.c
 	//-----------------------------------
 	void		(*AAS_EntityInfo)(int entnum, struct aas_entityinfo_s *info);
 	//-----------------------------------
-	// be_aas_main.h
+	// be_aas_main.c
 	//-----------------------------------
 	int			(*AAS_Initialized)(void);
 	void		(*AAS_PresenceTypeBoundingBox)(int presencetype, vec3_t mins, vec3_t maxs);
@@ -230,10 +232,10 @@
 	//--------------------------------------------
 	int			(*AAS_PointContents)(vec3_t point);
 	int			(*AAS_NextBSPEntity)(int ent);
-	int			(*AAS_ValueForBSPEpairKey)(int ent, char *key, char *value, int size);
-	int			(*AAS_VectorForBSPEpairKey)(int ent, char *key, vec3_t v);
-	int			(*AAS_FloatForBSPEpairKey)(int ent, char *key, float *value);
-	int			(*AAS_IntForBSPEpairKey)(int ent, char *key, int *value);
+	int			(*AAS_ValueForBSPEpairKey)(int ent, const char *key, char *value, int size);
+	int			(*AAS_VectorForBSPEpairKey)(int ent, const char *key, vec3_t v);
+	int			(*AAS_FloatForBSPEpairKey)(int ent, const char *key, float *value);
+	int			(*AAS_IntForBSPEpairKey)(int ent, const char *key, int *value);
 	//--------------------------------------------
 	// be_aas_reach.c
 	//--------------------------------------------
@@ -257,9 +259,9 @@
 	//--------------------------------------------
 	int			(*AAS_Swimming)(vec3_t origin);
 	int			(*AAS_PredictClientMovement)(struct aas_clientmove_s *move,
-											int entnum, vec3_t origin,
+											int entnum, const vec3_t origin,
 											int presencetype, int onground,
-											vec3_t velocity, vec3_t cmdmove,
+											const vec3_t velocity, const vec3_t cmdmove,
 											int cmdframes,
 											int maxframes, float frametime,
 											int stopevent, int stopareanum, int visualize);
@@ -268,9 +270,9 @@
 typedef struct ea_export_s
 {
 	//ClientCommand elementary actions
-	void	(*EA_Command)(int client, char *command );
-	void	(*EA_Say)(int client, char *str);
-	void	(*EA_SayTeam)(int client, char *str);
+	void	(*EA_Command)(int client, const char *command);
+	void	(*EA_Say)(int client, const char *str);
+	void	(*EA_SayTeam)(int client, const char *str);
 	//
 	void	(*EA_Action)(int client, int action);
 	void	(*EA_Gesture)(int client);
@@ -302,7 +304,7 @@
 	//-----------------------------------
 	// be_ai_char.h
 	//-----------------------------------
-	int		(*BotLoadCharacter)(char *charfile, float skill);
+	int		(*BotLoadCharacter)(const char *charfile, float skill);
 	void	(*BotFreeCharacter)(int character);
 	float	(*Characteristic_Float)(int character, int index);
 	float	(*Characteristic_BFloat)(int character, int index, float min, float max);
@@ -314,24 +316,24 @@
 	//-----------------------------------
 	int		(*BotAllocChatState)(void);
 	void	(*BotFreeChatState)(int handle);
-	void	(*BotQueueConsoleMessage)(int chatstate, int type, char *message);
+	void	(*BotQueueConsoleMessage)(int chatstate, int type, const char *message);
 	void	(*BotRemoveConsoleMessage)(int chatstate, int handle);
 	int		(*BotNextConsoleMessage)(int chatstate, struct bot_consolemessage_s *cm);
 	int		(*BotNumConsoleMessages)(int chatstate);
-	void	(*BotInitialChat)(int chatstate, char *type, int mcontext, char *var0, char *var1, char *var2, char *var3, char *var4, char *var5, char *var6, char *var7);
-	int		(*BotNumInitialChats)(int chatstate, char *type);
-	int		(*BotReplyChat)(int chatstate, char *message, int mcontext, int vcontext, char *var0, char *var1, char *var2, char *var3, char *var4, char *var5, char *var6, char *var7);
+	void	(*BotInitialChat)(int chatstate, const char *type, int mcontext, const char *var0, const char *var1, const char *var2, const char *var3, const char *var4, const char *var5, const char *var6, const char *var7);
+	int		(*BotNumInitialChats)(int chatstate, const char *type);
+	int		(*BotReplyChat)(int chatstate, const char *message, int mcontext, int vcontext, const char *var0, const char *var1, const char *var2, const char *var3, const char *var4, const char *var5, const char *var6, const char *var7);
 	int		(*BotChatLength)(int chatstate);
 	void	(*BotEnterChat)(int chatstate, int client, int sendto);
 	void	(*BotGetChatMessage)(int chatstate, char *buf, int size);
-	int		(*StringContains)(char *str1, char *str2, int casesensitive);
-	int		(*BotFindMatch)(char *str, struct bot_match_s *match, unsigned long int context);
+	int		(*StringContains)(const char *str1, const char *str2, int casesensitive);
+	int		(*BotFindMatch)(const char *str, struct bot_match_s *match, unsigned long int context);
 	void	(*BotMatchVariable)(struct bot_match_s *match, int variable, char *buf, int size);
 	void	(*UnifyWhiteSpaces)(char *string);
-	void	(*BotReplaceSynonyms)(char *string, unsigned long int context);
-	int		(*BotLoadChatFile)(int chatstate, char *chatfile, char *chatname);
+	void	(*BotReplaceSynonyms)(char *string, int size, unsigned long int context);
+	int		(*BotLoadChatFile)(int chatstate, const char *chatfile, const char *chatname);
 	void	(*BotSetChatGender)(int chatstate, int gender);
-	void	(*BotSetChatName)(int chatstate, char *name, int client);
+	void	(*BotSetChatName)(int chatstate, const char *name, int client);
 	//-----------------------------------
 	// be_ai_goal.h
 	//-----------------------------------
@@ -349,19 +351,19 @@
 	int		(*BotChooseLTGItem)(int goalstate, vec3_t origin, int *inventory, int travelflags);
 	int		(*BotChooseNBGItem)(int goalstate, vec3_t origin, int *inventory, int travelflags,
 								struct bot_goal_s *ltg, float maxtime);
-	int		(*BotTouchingGoal)(vec3_t origin, struct bot_goal_s *goal);
+	int		(*BotTouchingGoal)(const vec3_t origin, const struct bot_goal_s *goal);
 	int		(*BotItemGoalInVisButNotVisible)(int viewer, vec3_t eye, vec3_t viewangles, struct bot_goal_s *goal);
-	int		(*BotGetLevelItemGoal)(int index, char *classname, struct bot_goal_s *goal);
+	int		(*BotGetLevelItemGoal)(int index, const char *classname, struct bot_goal_s *goal);
 	int		(*BotGetNextCampSpotGoal)(int num, struct bot_goal_s *goal);
-	int		(*BotGetMapLocationGoal)(char *name, struct bot_goal_s *goal);
+	int		(*BotGetMapLocationGoal)(const char *name, struct bot_goal_s *goal);
 	float	(*BotAvoidGoalTime)(int goalstate, int number);
 	void	(*BotSetAvoidGoalTime)(int goalstate, int number, float avoidtime);
 	void	(*BotInitLevelItems)(void);
 	void	(*BotUpdateEntityItems)(void);
-	int		(*BotLoadItemWeights)(int goalstate, char *filename);
+	int		(*BotLoadItemWeights)(int goalstate, const char *filename);
 	void	(*BotFreeItemWeights)(int goalstate);
 	void	(*BotInterbreedGoalFuzzyLogic)(int parent1, int parent2, int child);
-	void	(*BotSaveGoalFuzzyLogic)(int goalstate, char *filename);
+	void	(*BotSaveGoalFuzzyLogic)(int goalstate, const char *filename);
 	void	(*BotMutateGoalFuzzyLogic)(int goalstate, float range);
 	int		(*BotAllocGoalState)(int client);
 	void	(*BotFreeGoalState)(int handle);
@@ -379,13 +381,13 @@
 	int		(*BotAllocMoveState)(void);
 	void	(*BotFreeMoveState)(int handle);
 	void	(*BotInitMoveState)(int handle, struct bot_initmove_s *initmove);
-	void	(*BotAddAvoidSpot)(int movestate, vec3_t origin, float radius, int type);
+	void	(*BotAddAvoidSpot)(int movestate, const vec3_t origin, float radius, int type);
 	//-----------------------------------
 	// be_ai_weap.h
 	//-----------------------------------
 	int		(*BotChooseBestFightWeapon)(int weaponstate, int *inventory);
 	void	(*BotGetWeaponInfo)(int weaponstate, int weapon, struct weaponinfo_s *weaponinfo);
-	int		(*BotLoadWeaponWeights)(int weaponstate, char *filename);
+	int		(*BotLoadWeaponWeights)(int weaponstate, const char *filename);
 	int		(*BotAllocWeaponState)(void);
 	void	(*BotFreeWeaponState)(int weaponstate);
 	void	(*BotResetWeaponState)(int weaponstate);
@@ -409,12 +411,12 @@
 	//shutdown the bot library, returns BLERR_
 	int (*BotLibShutdown)(void);
 	//sets a library variable returns BLERR_
-	int (*BotLibVarSet)(const char *var_name, const char *value);
+	int (*BotLibVarSet)( const char *var_name, const char *value );
 	//gets a library variable returns BLERR_
-	int (*BotLibVarGet)(const char *var_name, char *value, int size);
+	int (*BotLibVarGet)( const char *var_name, char *value, int size );
 
 	//sets a C-like define returns BLERR_
-	int (*PC_AddGlobalDefine)(char *string);
+	int (*PC_AddGlobalDefine)(const char *string);
 	int (*PC_LoadSourceHandle)(const char *filename);
 	int (*PC_FreeSourceHandle)(int handle);
 	int (*PC_ReadTokenHandle)(int handle, pc_token_t *pc_token);
@@ -437,9 +439,9 @@
 
 name:						default:			module(s):			description:
 
-"basedir"					""					-					base directory
-"gamedir"					""					be_interface.c		mod game directory
-"basegame"					""					be_interface.c		base game directory
+"basedir"					"baseq3"			be_interface.c		base directory
+"gamedir"					""					be_interface.c		game directory
+"homedir"					""					be_interface.c		home directory
 
 "log"						"0"					l_log.c				enable/disable creating a log file
 "maxclients"				"4"					be_interface.c		maximum number of clients
@@ -483,7 +485,7 @@
 "rs_maxjumpfallheight"		"450"				be_aas_move.c
 
 "max_aaslinks"				"4096"				be_aas_sample.c		maximum links in the AAS
-"max_routingcache"			"4096"				be_aas_route.c		maximum routing cache size in KB
+"max_routingcache"			"12288"				be_aas_route.c		maximum routing cache size in KB
 "forceclustering"			"0"					be_aas_main.c		force recalculation of clusters
 "forcereachability"			"0"					be_aas_main.c		force recalculation of reachabilities
 "forcewrite"				"0"					be_aas_main.c		force writing of aas file

```

### `openarena-engine`  — sha256 `9fc3c34f6553...`, 23261 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\botlib.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\botlib.h	2026-04-16 22:48:25.717693900 +0100
@@ -170,7 +170,7 @@
 typedef struct botlib_import_s
 {
 	//print messages from the bot library
-	void		(QDECL *Print)(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void		(QDECL *Print)(int type, char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 	//trace a bbox through the world
 	void		(*Trace)(bsp_trace_t *trace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 	//trace a bbox against a specific entity
@@ -409,9 +409,9 @@
 	//shutdown the bot library, returns BLERR_
 	int (*BotLibShutdown)(void);
 	//sets a library variable returns BLERR_
-	int (*BotLibVarSet)(const char *var_name, const char *value);
+	int (*BotLibVarSet)(char *var_name, char *value);
 	//gets a library variable returns BLERR_
-	int (*BotLibVarGet)(const char *var_name, char *value, int size);
+	int (*BotLibVarGet)(char *var_name, char *value, int size);
 
 	//sets a C-like define returns BLERR_
 	int (*PC_AddGlobalDefine)(char *string);
@@ -438,6 +438,7 @@
 name:						default:			module(s):			description:
 
 "basedir"					""					-					base directory
+"homedir"					""					be_interface.c		home directory
 "gamedir"					""					be_interface.c		mod game directory
 "basegame"					""					be_interface.c		base game directory
 

```

### `openarena-gamecode`  — sha256 `d7284cdc5474...`, 23041 bytes

_Diff stat: +29 / -30 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\botlib.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\botlib.h	2026-04-16 22:48:24.143820800 +0100
@@ -79,30 +79,29 @@
 #define BLERR_CANNOTLOADWEAPONCONFIG	12	//cannot load weapon config
 
 //action flags
-#define ACTION_ATTACK			0x00000001
-#define ACTION_USE			0x00000002
-#define ACTION_RESPAWN			0x00000008
-#define ACTION_JUMP			0x00000010
-#define ACTION_MOVEUP			0x00000020
-#define ACTION_CROUCH			0x00000080
-#define ACTION_MOVEDOWN			0x00000100
-#define ACTION_MOVEFORWARD		0x00000200
-#define ACTION_MOVEBACK			0x00000800
-#define ACTION_MOVELEFT			0x00001000
-#define ACTION_MOVERIGHT		0x00002000
-#define ACTION_DELAYEDJUMP		0x00008000
-#define ACTION_TALK			0x00010000
-#define ACTION_GESTURE			0x00020000
-#define ACTION_WALK			0x00080000
-#define ACTION_AFFIRMATIVE		0x00100000
-#define ACTION_NEGATIVE			0x00200000
-#define ACTION_GETFLAG			0x00800000
-#define ACTION_GUARDBASE		0x01000000
-#define ACTION_PATROL			0x02000000
-#define ACTION_FOLLOWME			0x08000000
-#define ACTION_JUMPEDLASTFRAME		0x10000000
+#define ACTION_ATTACK			0x0000001
+#define ACTION_USE				0x0000002
+#define ACTION_RESPAWN			0x0000008
+#define ACTION_JUMP				0x0000010
+#define ACTION_MOVEUP			0x0000020
+#define ACTION_CROUCH			0x0000080
+#define ACTION_MOVEDOWN			0x0000100
+#define ACTION_MOVEFORWARD		0x0000200
+#define ACTION_MOVEBACK			0x0000800
+#define ACTION_MOVELEFT			0x0001000
+#define ACTION_MOVERIGHT		0x0002000
+#define ACTION_DELAYEDJUMP		0x0008000
+#define ACTION_TALK				0x0010000
+#define ACTION_GESTURE			0x0020000
+#define ACTION_WALK				0x0080000
+#define ACTION_AFFIRMATIVE		0x0100000
+#define ACTION_NEGATIVE			0x0200000
+#define ACTION_GETFLAG			0x0800000
+#define ACTION_GUARDBASE		0x1000000
+#define ACTION_PATROL			0x2000000
+#define ACTION_FOLLOWME			0x8000000
 
-//the bot input, will be converted to a usercmd_t
+//the bot input, will be converted to an usercmd_t
 typedef struct bot_input_s
 {
 	float thinktime;		//time since last output (in seconds)
@@ -170,7 +169,7 @@
 typedef struct botlib_import_s
 {
 	//print messages from the bot library
-	void		(QDECL *Print)(int type, char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+	void		(QDECL *Print)(int type, char *fmt, ...);
 	//trace a bbox through the world
 	void		(*Trace)(bsp_trace_t *trace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask);
 	//trace a bbox against a specific entity
@@ -409,9 +408,9 @@
 	//shutdown the bot library, returns BLERR_
 	int (*BotLibShutdown)(void);
 	//sets a library variable returns BLERR_
-	int (*BotLibVarSet)(const char *var_name, const char *value);
+	int (*BotLibVarSet)(char *var_name, char *value);
 	//gets a library variable returns BLERR_
-	int (*BotLibVarGet)(const char *var_name, char *value, int size);
+	int (*BotLibVarGet)(char *var_name, char *value, int size);
 
 	//sets a C-like define returns BLERR_
 	int (*PC_AddGlobalDefine)(char *string);
@@ -437,14 +436,14 @@
 
 name:						default:			module(s):			description:
 
-"basedir"					""					-					base directory
-"gamedir"					""					be_interface.c		mod game directory
-"basegame"					""					be_interface.c		base game directory
+"basedir"					""					l_utils.c			base directory
+"gamedir"					""					l_utils.c			game directory
+"cddir"						""					l_utils.c			CD directory
 
 "log"						"0"					l_log.c				enable/disable creating a log file
 "maxclients"				"4"					be_interface.c		maximum number of clients
 "maxentities"				"1024"				be_interface.c		maximum number of entities
-"bot_developer"				"0"					be_interface.c		bot developer mode (it's "botDeveloper" in C to prevent symbol clash).
+"bot_developer"				"0"					be_interface.c		bot developer mode
 
 "phys_friction"				"6"					be_aas_move.c		ground friction
 "phys_stopspeed"			"100"				be_aas_move.c		stop speed

```
