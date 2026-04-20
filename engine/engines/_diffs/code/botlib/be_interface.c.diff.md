# Diff: `code/botlib/be_interface.c`
**Canonical:** `wolfcamql-src` (sha256 `a537f020dbba...`, 29805 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `361778f6460a...`, 30076 bytes

_Diff stat: +28 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_interface.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_interface.c	2026-04-16 20:02:19.854388000 +0100
@@ -15,13 +15,13 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
 /*****************************************************************************
- * name:		be_interface.c
+ * name:		be_interface.c // bk010221 - FIXME - DEAD code elimination
  *
  * desc:		bot library interface
  *
@@ -29,7 +29,7 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_log.h"
 #include "l_libvar.h"
@@ -37,20 +37,20 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
 #include "be_interface.h"
 
-#include "be_ea.h"
+#include "../game/be_ea.h"
 #include "be_ai_weight.h"
-#include "be_ai_goal.h"
-#include "be_ai_move.h"
-#include "be_ai_weap.h"
-#include "be_ai_chat.h"
-#include "be_ai_char.h"
-#include "be_ai_gen.h"
+#include "../game/be_ai_goal.h"
+#include "../game/be_ai_move.h"
+#include "../game/be_ai_weap.h"
+#include "../game/be_ai_chat.h"
+#include "../game/be_ai_char.h"
+#include "../game/be_ai_gen.h"
 
 //library globals in a structure
 botlib_globals_t botlibglobals;
@@ -58,7 +58,7 @@
 botlib_export_t be_botlib_export;
 botlib_import_t botimport;
 //
-int botDeveloper;
+int bot_developer;
 //qtrue if the library is setup
 int botlibsetup = qfalse;
 
@@ -137,18 +137,14 @@
 {
 	int		errnum;
 	
-	botDeveloper = LibVarGetValue("bot_developer");
- 	memset( &botlibglobals, 0, sizeof(botlibglobals) );
+	bot_developer = LibVarGetValue("bot_developer");
+  memset( &botlibglobals, 0, sizeof(botlibglobals) ); // bk001207 - init
 	//initialize byte swapping (litte endian etc.)
 //	Swap_Init();
-
-	if(botDeveloper)
-	{
-		Log_Open("botlib.log");
-	}
-
+	Log_Open("botlib.log");
+	//
 	botimport.Print(PRT_MESSAGE, "------- BotLib Initialization -------\n");
-
+	//
 	botlibglobals.maxclients = (int) LibVarValue("maxclients", "128");
 	botlibglobals.maxentities = (int) LibVarValue("maxentities", "1024");
 
@@ -219,7 +215,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarSet(const char *var_name, const char *value)
+int Export_BotLibVarSet(char *var_name, char *value)
 {
 	LibVarSet(var_name, value);
 	return BLERR_NOERROR;
@@ -230,12 +226,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarGet(const char *var_name, char *value, int size)
+int Export_BotLibVarGet(char *var_name, char *value, int size)
 {
 	char *varvalue;
 
 	varvalue = LibVarGetString(var_name);
-	Q_strncpyz(value, varvalue, size);
+	strncpy(value, varvalue, size-1);
+	value[size-1] = '\0';
 	return BLERR_NOERROR;
 } //end of the function Export_BotLibVarGet
 //===========================================================================
@@ -303,7 +300,7 @@
 int BotGetReachabilityToGoal(vec3_t origin, int areanum,
 									  int lastgoalareanum, int lastareanum,
 									  int *avoidreach, float *avoidreachtimes, int *avoidreachtries,
-									  bot_goal_t *goal, int travelflags,
+									  bot_goal_t *goal, int travelflags, int movetravelflags,
 									  struct bot_avoidspot_s *avoidspots, int numavoidspots, int *flags);
 
 int AAS_PointLight(vec3_t origin, int *red, int *green, int *blue);
@@ -526,7 +523,7 @@
 		reachnum = BotGetReachabilityToGoal(origin, newarea,
 									  lastgoalareanum, lastareanum,
 									  avoidreach, avoidreachtimes, avoidreachtries,
-									  &goal, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP,
+									  &goal, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP,
 									  NULL, 0, &resultFlags);
 		AAS_ReachabilityFromNum(reachnum, &reach);
 		AAS_ShowReachability(&reach);
@@ -545,7 +542,7 @@
 			reachnum = BotGetReachabilityToGoal(curorigin, curarea,
 										  lastgoalareanum, lastareanum,
 										  avoidreach, avoidreachtimes, avoidreachtries,
-										  &goal, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP,
+										  &goal, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP, TFL_DEFAULT|TFL_FUNCBOB|TFL_ROCKETJUMP,
 										  NULL, 0, &resultFlags);
 			AAS_ReachabilityFromNum(reachnum, &reach);
 			AAS_ShowReachability(&reach);
@@ -849,9 +846,9 @@
 ============
 */
 botlib_export_t *GetBotLibAPI(int apiVersion, botlib_import_t *import) {
-	assert(import);
-	botimport = *import;
-	assert(botimport.Print);
+	assert(import);   // bk001129 - this wasn't set for baseq3/
+  botimport = *import;
+  assert(botimport.Print);   // bk001129 - pars pro toto
 
 	Com_Memset( &be_botlib_export, 0, sizeof( be_botlib_export ) );
 

```

### `quake3e`  — sha256 `8305bb62aa15...`, 29389 bytes

_Diff stat: +34 / -47 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_interface.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_interface.c	2026-04-16 20:02:26.902995100 +0100
@@ -84,26 +84,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean ValidClientNumber(int num, char *str)
+static qboolean ValidEntityNumber(int num, const char *str)
 {
-	if (num < 0 || num > botlibglobals.maxclients)
-	{
-		//weird: the disabled stuff results in a crash
-		botimport.Print(PRT_ERROR, "%s: invalid client number %d, [0, %d]\n",
-										str, num, botlibglobals.maxclients);
-		return qfalse;
-	} //end if
-	return qtrue;
-} //end of the function BotValidateClientNumber
-//===========================================================================
-//
-// Parameter:				-
-// Returns:					-
-// Changes Globals:		-
-//===========================================================================
-qboolean ValidEntityNumber(int num, char *str)
-{
-	if (num < 0 || num > botlibglobals.maxentities)
+	if ( /*num < 0 || */ (unsigned)num > botlibglobals.maxentities )
 	{
 		botimport.Print(PRT_ERROR, "%s: invalid entity number %d, [0, %d]\n",
 										str, num, botlibglobals.maxentities);
@@ -117,7 +100,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean BotLibSetup(char *str)
+static qboolean BotLibSetup(const char *str)
 {
 	if (!botlibglobals.botlibsetup)
 	{
@@ -133,24 +116,25 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibSetup(void)
+static int Export_BotLibSetup( void )
 {
 	int		errnum;
 	
-	botDeveloper = LibVarGetValue("bot_developer");
- 	memset( &botlibglobals, 0, sizeof(botlibglobals) );
-	//initialize byte swapping (litte endian etc.)
-//	Swap_Init();
+	botDeveloper = LibVarGetValue( "bot_developer" );
+ 	memset( &botlibglobals, 0, sizeof( botlibglobals ) );
+
+	// initialize byte swapping (litte endian etc.)
+	// Swap_Init();
 
-	if(botDeveloper)
+	if ( botDeveloper )
 	{
-		Log_Open("botlib.log");
+		Log_Open( "botlib.log" );
 	}
 
-	botimport.Print(PRT_MESSAGE, "------- BotLib Initialization -------\n");
+	botimport.Print( PRT_MESSAGE, "------- BotLib Initialization -------\n" );
 
-	botlibglobals.maxclients = (int) LibVarValue("maxclients", "128");
-	botlibglobals.maxentities = (int) LibVarValue("maxentities", "1024");
+	botlibglobals.maxclients = LibVarInteger( "maxclients", "64", 0, MAX_CLIENTS );
+	botlibglobals.maxentities = LibVarInteger( "maxentities", "1024", 0, MAX_GENTITIES );
 
 	errnum = AAS_Setup();			//be_aas_main.c
 	if (errnum != BLERR_NOERROR) return errnum;
@@ -176,9 +160,10 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibShutdown(void)
+static int Export_BotLibShutdown(void)
 {
-	if (!BotLibSetup("BotLibShutdown")) return BLERR_LIBRARYNOTSETUP;
+	if ( !botlibglobals.botlibsetup )
+		return BLERR_LIBRARYNOTSETUP;
 #ifndef DEMO
 	//DumpFileCRCs();
 #endif //DEMO
@@ -189,9 +174,9 @@
 	BotShutdownWeaponAI();		//be_ai_weap.c
 	BotShutdownWeights();		//be_ai_weight.c
 	BotShutdownCharacters();	//be_ai_char.c
-	//shud down aas
+	//shut down AAS
 	AAS_Shutdown();
-	//shut down bot elemantary actions
+	//shut down bot elementary actions
 	EA_Shutdown();
 	//free all libvars
 	LibVarDeAllocAll();
@@ -219,9 +204,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarSet(const char *var_name, const char *value)
+static int Export_BotLibVarSet( const char *var_name, const char *value )
 {
-	LibVarSet(var_name, value);
+	LibVarSet( var_name, value );
 	return BLERR_NOERROR;
 } //end of the function Export_BotLibVarSet
 //===========================================================================
@@ -230,12 +215,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarGet(const char *var_name, char *value, int size)
+static int Export_BotLibVarGet( const char *var_name, char *value, int size )
 {
-	char *varvalue;
+	const char *varvalue;
 
-	varvalue = LibVarGetString(var_name);
-	Q_strncpyz(value, varvalue, size);
+	varvalue = LibVarGetString( var_name );
+	Q_strncpyz( value, varvalue, size );
 	return BLERR_NOERROR;
 } //end of the function Export_BotLibVarGet
 //===========================================================================
@@ -244,7 +229,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibStartFrame(float time)
+static int Export_BotLibStartFrame(float time)
 {
 	if (!BotLibSetup("BotStartFrame")) return BLERR_LIBRARYNOTSETUP;
 	return AAS_StartFrame(time);
@@ -255,7 +240,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibLoadMap(const char *mapname)
+static int Export_BotLibLoadMap(const char *mapname)
 {
 #ifdef DEBUG
 	int starttime = Sys_MilliSeconds();
@@ -285,7 +270,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibUpdateEntity(int ent, bot_entitystate_t *state)
+static int Export_BotLibUpdateEntity(int ent, bot_entitystate_t *state)
 {
 	if (!BotLibSetup("BotUpdateEntity")) return BLERR_LIBRARYNOTSETUP;
 	if (!ValidEntityNumber(ent, "BotUpdateEntity")) return BLERR_INVALIDENTITYNUMBER;
@@ -298,7 +283,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
+#if 0
 void AAS_TestMovementPrediction(int entnum, vec3_t origin, vec3_t dir);
+#endif
 void ElevatorBottomCenter(aas_reachability_t *reach, vec3_t bottomcenter);
 int BotGetReachabilityToGoal(vec3_t origin, int areanum,
 									  int lastgoalareanum, int lastareanum,
@@ -328,7 +315,7 @@
 	static int line[2];
 	int newarea, i, highlightarea, flood;
 //	int reachnum;
-	vec3_t eye, forward, right, end, origin;
+	vec3_t eye, forward, right, /*end,*/ origin;
 //	vec3_t bottomcenter;
 //	aas_trace_t trace;
 //	aas_face_t *face;
@@ -338,8 +325,8 @@
 //	bot_goal_t goal;
 
 	// clock_t start_time, end_time;
-	vec3_t mins = {-16, -16, -24};
-	vec3_t maxs = {16, 16, 32};
+	//vec3_t mins = {-16, -16, -24};
+	//vec3_t maxs = {16, 16, 32};
 
 //	int areas[10], numareas;
 
@@ -569,7 +556,7 @@
 	//get the eye 24 units up
 	eye[2] += 24;
 	//get the end point for the line to be traced
-	VectorMA(eye, 800, forward, end);
+	//VectorMA(eye, 800, forward, end);
 
 //	AAS_TestMovementPrediction(1, parm2, forward);
 /*

```

### `openarena-engine`  — sha256 `3e482f453a2b...`, 30500 bytes

_Diff stat: +24 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_interface.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_interface.c	2026-04-16 22:48:25.716695400 +0100
@@ -144,7 +144,26 @@
 
 	if(botDeveloper)
 	{
-		Log_Open("botlib.log");
+		char *homedir, *gamedir, *basegame;
+		char logfilename[MAX_OSPATH];
+
+		homedir = LibVarGetString("homedir");
+		gamedir = LibVarGetString("gamedir");
+		basegame = LibVarGetString("basegame");
+
+		if (*homedir)
+		{
+			if(*gamedir)
+				Com_sprintf(logfilename, sizeof(logfilename), "%s%c%s%cbotlib.log", homedir, PATH_SEP, gamedir, PATH_SEP);
+			else if(*basegame)
+				Com_sprintf(logfilename, sizeof(logfilename), "%s%c%s%cbotlib.log", homedir, PATH_SEP, basegame, PATH_SEP);
+			else
+				Com_sprintf(logfilename, sizeof(logfilename), "%s%c" BASEGAME "%cbotlib.log", homedir, PATH_SEP, PATH_SEP);
+		}
+		else
+			Com_sprintf(logfilename, sizeof(logfilename), "botlib.log");
+	
+		Log_Open(logfilename);
 	}
 
 	botimport.Print(PRT_MESSAGE, "------- BotLib Initialization -------\n");
@@ -219,7 +238,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarSet(const char *var_name, const char *value)
+int Export_BotLibVarSet(char *var_name, char *value)
 {
 	LibVarSet(var_name, value);
 	return BLERR_NOERROR;
@@ -230,12 +249,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int Export_BotLibVarGet(const char *var_name, char *value, int size)
+int Export_BotLibVarGet(char *var_name, char *value, int size)
 {
 	char *varvalue;
 
 	varvalue = LibVarGetString(var_name);
-	Q_strncpyz(value, varvalue, size);
+	strncpy(value, varvalue, size-1);
+	value[size-1] = '\0';
 	return BLERR_NOERROR;
 } //end of the function Export_BotLibVarGet
 //===========================================================================

```
