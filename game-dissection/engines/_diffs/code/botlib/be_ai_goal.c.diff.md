# Diff: `code/botlib/be_ai_goal.c`
**Canonical:** `wolfcamql-src` (sha256 `d2ee56098ba7...`, 54987 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `e180ef01fdd8...`, 55013 bytes

_Diff stat: +35 / -42 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_goal.c	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_goal.c	2026-04-16 20:02:19.852390200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,7 +29,7 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_utils.h"
 #include "l_libvar.h"
 #include "l_memory.h"
@@ -38,13 +38,13 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_ai_weight.h"
-#include "be_ai_goal.h"
-#include "be_ai_move.h"
+#include "../game/be_ai_goal.h"
+#include "../game/be_ai_move.h"
 
 //#define DEBUG_AI_GOAL
 #ifdef RANDOMIZE
@@ -134,7 +134,7 @@
 	int number;							//number of the item info
 } iteminfo_t;
 
-#define ITEMINFO_OFS(x)	(size_t)&(((iteminfo_t *)0)->x)
+#define ITEMINFO_OFS(x)	(int)&(((iteminfo_t *)0)->x)
 
 fielddef_t iteminfo_fields[] =
 {
@@ -146,7 +146,7 @@
 {"respawntime", ITEMINFO_OFS(respawntime), FT_FLOAT},
 {"mins", ITEMINFO_OFS(mins), FT_FLOAT|FT_ARRAY, 3},
 {"maxs", ITEMINFO_OFS(maxs), FT_FLOAT|FT_ARRAY, 3},
-{NULL, 0, 0}
+{0, 0, 0}
 };
 
 structdef_t iteminfo_struct =
@@ -176,22 +176,22 @@
 	float avoidgoaltimes[MAX_AVOIDGOALS];		//times to avoid the goals
 } bot_goalstate_t;
 
-bot_goalstate_t *botgoalstates[MAX_CLIENTS + 1]; // FIXME: init?
+bot_goalstate_t *botgoalstates[MAX_CLIENTS + 1]; // bk001206 - FIXME: init?
 //item configuration
-itemconfig_t *itemconfig = NULL;
+itemconfig_t *itemconfig = NULL; // bk001206 - init
 //level items
-levelitem_t *levelitemheap = NULL;
-levelitem_t *freelevelitems = NULL;
-levelitem_t *levelitems = NULL;
+levelitem_t *levelitemheap = NULL; // bk001206 - init
+levelitem_t *freelevelitems = NULL; // bk001206 - init
+levelitem_t *levelitems = NULL; // bk001206 - init
 int numlevelitems = 0;
 //map locations
-maplocation_t *maplocations = NULL;
+maplocation_t *maplocations = NULL; // bk001206 - init
 //camp spots
-campspot_t *campspots = NULL;
+campspot_t *campspots = NULL; // bk001206 - init
 //the game type
-int g_gametype = 0;
+int g_gametype = 0; // bk001206 - init
 //additional dropped item weight
-libvar_t *droppedweight = NULL;
+libvar_t *droppedweight = NULL; // bk001206 - init
 
 //========================================================================
 //
@@ -227,9 +227,6 @@
 	p2 = BotGoalStateFromHandle(parent2);
 	c = BotGoalStateFromHandle(child);
 
-	if (!p1 || !p2 || !c)
-		return;
-
 	InterbreedWeightConfigs(p1->itemweightconfig, p2->itemweightconfig,
 									c->itemweightconfig);
 } //end of the function BotInterbreedingGoalFuzzyLogic
@@ -241,10 +238,10 @@
 //===========================================================================
 void BotSaveGoalFuzzyLogic(int goalstate, char *filename)
 {
-	//bot_goalstate_t *gs;
+	bot_goalstate_t *gs;
+
+	gs = BotGoalStateFromHandle(goalstate);
 
-	//gs = BotGoalStateFromHandle(goalstate);
-	//if (!gs) return;
 	//WriteWeightConfig(filename, gs->itemweightconfig);
 } //end of the function BotSaveGoalFuzzyLogic
 //===========================================================================
@@ -258,7 +255,7 @@
 	bot_goalstate_t *gs;
 
 	gs = BotGoalStateFromHandle(goalstate);
-	if (!gs) return;
+
 	EvolveWeightConfig(gs->itemweightconfig);
 } //end of the function BotMutateGoalFuzzyLogic
 //===========================================================================
@@ -271,7 +268,7 @@
 {
 	int max_iteminfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	source_t *source;
 	itemconfig_t *ic;
 	iteminfo_t *ii;
@@ -284,11 +281,11 @@
 		LibVarSet( "max_iteminfo", "256" );
 	}
 
-	Q_strncpyz(path, filename, sizeof(path));
+	strncpy( path, filename, MAX_PATH );
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile( path );
 	if( !source ) {
-		botimport.Print( PRT_ERROR, "couldn't load %s\n", path );
+		botimport.Print( PRT_ERROR, "counldn't load %s\n", path );
 		return NULL;
 	} //end if
 	//initialize item config
@@ -303,7 +300,7 @@
 		{
 			if (ic->numiteminfo >= max_iteminfo)
 			{
-				SourceError(source, "more than %d item info defined", max_iteminfo);
+				SourceError(source, "more than %d item info defined\n", max_iteminfo);
 				FreeMemory(ic);
 				FreeSource(source);
 				return NULL;
@@ -313,11 +310,11 @@
 			if (!PC_ExpectTokenType(source, TT_STRING, 0, &token))
 			{
 				FreeMemory(ic);
-				FreeSource(source);
+				FreeMemory(source);
 				return NULL;
 			} //end if
 			StripDoubleQuotes(token.string);
-			Q_strncpyz(ii->classname, token.string, sizeof(ii->classname));
+			strncpy(ii->classname, token.string, sizeof(ii->classname)-1);
 			if (!ReadStructure(source, &iteminfo_struct, (char *) ii))
 			{
 				FreeMemory(ic);
@@ -329,7 +326,7 @@
 		} //end if
 		else
 		{
-			SourceError(source, "unknown definition %s", token.string);
+			SourceError(source, "unknown definition %s\n", token.string);
 			FreeMemory(ic);
 			FreeSource(source);
 			return NULL;
@@ -525,7 +522,7 @@
 			numcampspots++;
 		} //end else if
 	} //end for
-	if (botDeveloper)
+	if (bot_developer)
 	{
 		botimport.Print(PRT_MESSAGE, "%d map locations\n", numlocations);
 		botimport.Print(PRT_MESSAGE, "%d camp spots\n", numcampspots);
@@ -561,9 +558,10 @@
 	//if there's no AAS file loaded
 	if (!AAS_Loaded()) return;
 
-	//validate the modelindexes of the item info
+	//update the modelindexes of the item info
 	for (i = 0; i < ic->numiteminfo; i++)
 	{
+		//ic->iteminfo[i].modelindex = AAS_IndexFromModel(ic->iteminfo[i].model);
 		if (!ic->iteminfo[i].modelindex)
 		{
 			Log_Write("item %s has modelindex 0", ic->iteminfo[i].classname);
@@ -688,11 +686,13 @@
 	{
 		if (li->number == number)
 		{
-			Q_strncpyz(name, itemconfig->iteminfo[li->iteminfo].name, size);
+			strncpy(name, itemconfig->iteminfo[li->iteminfo].name, size-1);
+			name[size-1] = '\0';
 			return;
 		} //end for
 	} //end for
 	strcpy(name, "");
+	return;
 } //end of the function BotGoalName
 //===========================================================================
 //
@@ -897,7 +897,6 @@
 			goal->number = li->number;
 			goal->flags = GFL_ITEM;
 			if (li->timeout) goal->flags |= GFL_DROPPED;
-			goal->iteminfo = li->iteminfo;
 			//botimport.Print(PRT_MESSAGE, "found li %s\n", itemconfig->iteminfo[li->iteminfo].name);
 			return li->number;
 		} //end if
@@ -924,9 +923,6 @@
 			goal->entitynum = 0;
 			VectorCopy(mins, goal->mins);
 			VectorCopy(maxs, goal->maxs);
-			goal->number = 0;
-			goal->flags = 0;
-			goal->iteminfo = 0;
 			return qtrue;
 		} //end if
 	} //end for
@@ -955,9 +951,6 @@
 			goal->entitynum = 0;
 			VectorCopy(mins, goal->mins);
 			VectorCopy(maxs, goal->maxs);
-			goal->number = 0;
-			goal->flags = 0;
-			goal->iteminfo = 0;
 			return num+1;
 		} //end if
 	} //end for
@@ -1025,7 +1018,7 @@
 	for (li = levelitems; li; li = nextli)
 	{
 		nextli = li->next;
-		//if it is an item that will time out
+		//if it is a item that will time out
 		if (li->timeout)
 		{
 			//timeout the item

```

### `quake3e`  — sha256 `b6eea264e9a5...`, 55140 bytes

_Diff stat: +48 / -50 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_goal.c	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_goal.c	2026-04-16 20:02:26.899996300 +0100
@@ -136,7 +136,7 @@
 
 #define ITEMINFO_OFS(x)	(size_t)&(((iteminfo_t *)0)->x)
 
-fielddef_t iteminfo_fields[] =
+static const fielddef_t iteminfo_fields[] =
 {
 {"name", ITEMINFO_OFS(name), FT_STRING},
 {"model", ITEMINFO_OFS(model), FT_STRING},
@@ -149,7 +149,7 @@
 {NULL, 0, 0}
 };
 
-structdef_t iteminfo_struct =
+static const structdef_t iteminfo_struct =
 {
 	sizeof(iteminfo_t), iteminfo_fields
 };
@@ -176,22 +176,22 @@
 	float avoidgoaltimes[MAX_AVOIDGOALS];		//times to avoid the goals
 } bot_goalstate_t;
 
-bot_goalstate_t *botgoalstates[MAX_CLIENTS + 1]; // FIXME: init?
+static bot_goalstate_t *botgoalstates[MAX_CLIENTS + 1]; // FIXME: init?
 //item configuration
-itemconfig_t *itemconfig = NULL;
+static itemconfig_t *itemconfig = NULL;
 //level items
-levelitem_t *levelitemheap = NULL;
-levelitem_t *freelevelitems = NULL;
-levelitem_t *levelitems = NULL;
-int numlevelitems = 0;
+static levelitem_t *levelitemheap = NULL;
+static levelitem_t *freelevelitems = NULL;
+static levelitem_t *levelitems = NULL;
+static int numlevelitems = 0;
 //map locations
-maplocation_t *maplocations = NULL;
+static maplocation_t *maplocations = NULL;
 //camp spots
-campspot_t *campspots = NULL;
+static campspot_t *campspots = NULL;
 //the game type
-int g_gametype = 0;
+static int g_gametype = 0;
 //additional dropped item weight
-libvar_t *droppedweight = NULL;
+static libvar_t *droppedweight = NULL;
 
 //========================================================================
 //
@@ -221,13 +221,13 @@
 //===========================================================================
 void BotInterbreedGoalFuzzyLogic(int parent1, int parent2, int child)
 {
-	bot_goalstate_t *p1, *p2, *c;
+	const bot_goalstate_t *p1, *p2, *c;
 
 	p1 = BotGoalStateFromHandle(parent1);
 	p2 = BotGoalStateFromHandle(parent2);
 	c = BotGoalStateFromHandle(child);
 
-	if (!p1 || !p2 || !c)
+	if ( !p1 || !p2 || !c )
 		return;
 
 	InterbreedWeightConfigs(p1->itemweightconfig, p2->itemweightconfig,
@@ -239,12 +239,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void BotSaveGoalFuzzyLogic(int goalstate, char *filename)
+void BotSaveGoalFuzzyLogic(int goalstate, const char *filename)
 {
 	//bot_goalstate_t *gs;
 
 	//gs = BotGoalStateFromHandle(goalstate);
-	//if (!gs) return;
+
+	// if ( !gs ) return;
 	//WriteWeightConfig(filename, gs->itemweightconfig);
 } //end of the function BotSaveGoalFuzzyLogic
 //===========================================================================
@@ -258,7 +259,8 @@
 	bot_goalstate_t *gs;
 
 	gs = BotGoalStateFromHandle(goalstate);
-	if (!gs) return;
+
+	if ( !gs ) return;
 	EvolveWeightConfig(gs->itemweightconfig);
 } //end of the function BotMutateGoalFuzzyLogic
 //===========================================================================
@@ -267,24 +269,18 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-itemconfig_t *LoadItemConfig(char *filename)
+static itemconfig_t *LoadItemConfig( const char *filename )
 {
 	int max_iteminfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	source_t *source;
 	itemconfig_t *ic;
 	iteminfo_t *ii;
 
-	max_iteminfo = (int) LibVarValue("max_iteminfo", "256");
-	if (max_iteminfo < 0)
-	{
-		botimport.Print(PRT_ERROR, "max_iteminfo = %d\n", max_iteminfo);
-		max_iteminfo = 256;
-		LibVarSet( "max_iteminfo", "256" );
-	}
+	max_iteminfo = LibVarInteger("max_iteminfo", "256", 0, 4096);
 
-	Q_strncpyz(path, filename, sizeof(path));
+	Q_strncpyz( path, filename, sizeof( path ) );
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile( path );
 	if( !source ) {
@@ -317,7 +313,7 @@
 				return NULL;
 			} //end if
 			StripDoubleQuotes(token.string);
-			Q_strncpyz(ii->classname, token.string, sizeof(ii->classname));
+			Q_strncpyz( ii->classname, token.string, sizeof( ii->classname ) );
 			if (!ReadStructure(source, &iteminfo_struct, (char *) ii))
 			{
 				FreeMemory(ic);
@@ -348,7 +344,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int *ItemWeightIndex(weightconfig_t *iwc, itemconfig_t *ic)
+static int *ItemWeightIndex(const weightconfig_t *iwc, const itemconfig_t *ic)
 {
 	int *index, i;
 
@@ -371,13 +367,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void InitLevelItemHeap(void)
+static void InitLevelItemHeap(void)
 {
 	int i, max_levelitems;
 
 	if (levelitemheap) FreeMemory(levelitemheap);
 
-	max_levelitems = (int) LibVarValue("max_levelitems", "256");
+	max_levelitems = LibVarInteger("max_levelitems", "256", 1, 4096);
 	levelitemheap = (levelitem_t *) GetClearedMemory(max_levelitems * sizeof(levelitem_t));
 
 	for (i = 0; i < max_levelitems-1; i++)
@@ -394,7 +390,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-levelitem_t *AllocLevelItem(void)
+static levelitem_t *AllocLevelItem(void)
 {
 	levelitem_t *li;
 
@@ -415,7 +411,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void FreeLevelItem(levelitem_t *li)
+static void FreeLevelItem(levelitem_t *li)
 {
 	li->next = freelevelitems;
 	freelevelitems = li;
@@ -426,7 +422,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AddLevelItemToList(levelitem_t *li)
+static void AddLevelItemToList(levelitem_t *li)
 {
 	if (levelitems) levelitems->prev = li;
 	li->prev = NULL;
@@ -439,7 +435,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void RemoveLevelItemFromList(levelitem_t *li)
+static void RemoveLevelItemFromList(levelitem_t *li)
 {
 	if (li->prev) li->prev->next = li->next;
 	else levelitems = li->next;
@@ -451,7 +447,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void BotFreeInfoEntities(void)
+static void BotFreeInfoEntities(void)
 {
 	maplocation_t *ml, *nextml;
 	campspot_t *cs, *nextcs;
@@ -475,7 +471,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void BotInitInfoEntities(void)
+static void BotInitInfoEntities(void)
 {
 	char classname[MAX_EPAIRKEY];
 	maplocation_t *ml;
@@ -566,7 +562,7 @@
 	{
 		if (!ic->iteminfo[i].modelindex)
 		{
-			Log_Write("item %s has modelindex 0", ic->iteminfo[i].classname);
+			Log_Write("item %s has modelindex 0\n", ic->iteminfo[i].classname);
 		} //end if
 	} //end for
 
@@ -602,8 +598,8 @@
 			{
 				VectorCopy(origin, end);
 				end[2] -= 32;
-				trace = AAS_Trace(origin, ic->iteminfo[i].mins, ic->iteminfo[i].maxs, end, -1, CONTENTS_SOLID|CONTENTS_PLAYERCLIP);
-				//if the item not near the ground
+				trace = AAS_Trace(origin, ic->iteminfo[i].mins, ic->iteminfo[i].maxs, end, ENTITYNUM_NONE, CONTENTS_SOLID|CONTENTS_PLAYERCLIP);
+				//if the item is not near the ground
 				if (trace.fraction >= 1)
 				{
 					//if the item is not reachable from a jumppad
@@ -688,7 +684,7 @@
 	{
 		if (li->number == number)
 		{
-			Q_strncpyz(name, itemconfig->iteminfo[li->iteminfo].name, size);
+			Q_strncpyz( name, itemconfig->iteminfo[li->iteminfo].name, size );
 			return;
 		} //end for
 	} //end for
@@ -739,7 +735,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void BotAddToAvoidGoals(bot_goalstate_t *gs, int number, float avoidtime)
+static void BotAddToAvoidGoals(bot_goalstate_t *gs, int number, float avoidtime)
 {
 	int i;
 
@@ -856,7 +852,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotGetLevelItemGoal(int index, char *name, bot_goal_t *goal)
+int BotGetLevelItemGoal(int index, const char *name, bot_goal_t *goal)
 {
 	levelitem_t *li;
 
@@ -910,7 +906,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotGetMapLocationGoal(char *name, bot_goal_t *goal)
+int BotGetMapLocationGoal(const char *name, bot_goal_t *goal)
 {
 	maplocation_t *ml;
 	vec3_t mins = {-8, -8, -8}, maxs = {8, 8, 8};
@@ -963,13 +959,14 @@
 	} //end for
 	return 0;
 } //end of the function BotGetNextCampSpotGoal
+#if 0
 //===========================================================================
 //
 // Parameter:			-
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void BotFindEntityForLevelItem(levelitem_t *li)
+static void BotFindEntityForLevelItem(levelitem_t *li)
 {
 	int ent, modelindex;
 	itemconfig_t *ic;
@@ -1003,6 +1000,7 @@
 		} //end if
 	} //end for
 } //end of the function BotFindEntityForLevelItem
+#endif
 //===========================================================================
 //
 // Parameter:			-
@@ -1612,13 +1610,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int BotTouchingGoal(vec3_t origin, bot_goal_t *goal)
+int BotTouchingGoal(const vec3_t origin, const bot_goal_t *goal)
 {
 	int i;
 	vec3_t boxmins, boxmaxs;
 	vec3_t absmins, absmaxs;
-	vec3_t safety_maxs = {0, 0, 0}; //{4, 4, 10};
-	vec3_t safety_mins = {0, 0, 0}; //{-4, -4, 0};
+	const vec3_t safety_maxs = {0, 0, 0}; //{4, 4, 10};
+	const vec3_t safety_mins = {0, 0, 0}; //{-4, -4, 0};
 
 	AAS_PresenceTypeBoundingBox(PRESENCE_NORMAL, boxmins, boxmaxs);
 	VectorSubtract(goal->mins, boxmaxs, absmins);
@@ -1694,7 +1692,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int BotLoadItemWeights(int goalstate, char *filename)
+int BotLoadItemWeights(int goalstate, const char *filename)
 {
 	bot_goalstate_t *gs;
 
@@ -1780,7 +1778,7 @@
 //===========================================================================
 int BotSetupGoalAI(void)
 {
-	char *filename;
+	const char *filename;
 
 	//check if teamplay is on
 	g_gametype = LibVarValue("g_gametype", "0");

```

### `openarena-engine`  — sha256 `9ef18204258e...`, 54763 bytes

_Diff stat: +8 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_goal.c	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_goal.c	2026-04-16 22:48:25.713694700 +0100
@@ -227,9 +227,6 @@
 	p2 = BotGoalStateFromHandle(parent2);
 	c = BotGoalStateFromHandle(child);
 
-	if (!p1 || !p2 || !c)
-		return;
-
 	InterbreedWeightConfigs(p1->itemweightconfig, p2->itemweightconfig,
 									c->itemweightconfig);
 } //end of the function BotInterbreedingGoalFuzzyLogic
@@ -244,7 +241,7 @@
 	//bot_goalstate_t *gs;
 
 	//gs = BotGoalStateFromHandle(goalstate);
-	//if (!gs) return;
+
 	//WriteWeightConfig(filename, gs->itemweightconfig);
 } //end of the function BotSaveGoalFuzzyLogic
 //===========================================================================
@@ -258,7 +255,7 @@
 	bot_goalstate_t *gs;
 
 	gs = BotGoalStateFromHandle(goalstate);
-	if (!gs) return;
+
 	EvolveWeightConfig(gs->itemweightconfig);
 } //end of the function BotMutateGoalFuzzyLogic
 //===========================================================================
@@ -271,7 +268,7 @@
 {
 	int max_iteminfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	source_t *source;
 	itemconfig_t *ic;
 	iteminfo_t *ii;
@@ -284,11 +281,11 @@
 		LibVarSet( "max_iteminfo", "256" );
 	}
 
-	Q_strncpyz(path, filename, sizeof(path));
+	strncpy( path, filename, MAX_PATH );
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile( path );
 	if( !source ) {
-		botimport.Print( PRT_ERROR, "couldn't load %s\n", path );
+		botimport.Print( PRT_ERROR, "counldn't load %s\n", path );
 		return NULL;
 	} //end if
 	//initialize item config
@@ -317,7 +314,7 @@
 				return NULL;
 			} //end if
 			StripDoubleQuotes(token.string);
-			Q_strncpyz(ii->classname, token.string, sizeof(ii->classname));
+			strncpy(ii->classname, token.string, sizeof(ii->classname)-1);
 			if (!ReadStructure(source, &iteminfo_struct, (char *) ii))
 			{
 				FreeMemory(ic);
@@ -688,7 +685,8 @@
 	{
 		if (li->number == number)
 		{
-			Q_strncpyz(name, itemconfig->iteminfo[li->iteminfo].name, size);
+			strncpy(name, itemconfig->iteminfo[li->iteminfo].name, size-1);
+			name[size-1] = '\0';
 			return;
 		} //end for
 	} //end for
@@ -897,7 +895,6 @@
 			goal->number = li->number;
 			goal->flags = GFL_ITEM;
 			if (li->timeout) goal->flags |= GFL_DROPPED;
-			goal->iteminfo = li->iteminfo;
 			//botimport.Print(PRT_MESSAGE, "found li %s\n", itemconfig->iteminfo[li->iteminfo].name);
 			return li->number;
 		} //end if
@@ -924,9 +921,6 @@
 			goal->entitynum = 0;
 			VectorCopy(mins, goal->mins);
 			VectorCopy(maxs, goal->maxs);
-			goal->number = 0;
-			goal->flags = 0;
-			goal->iteminfo = 0;
 			return qtrue;
 		} //end if
 	} //end for
@@ -955,9 +949,6 @@
 			goal->entitynum = 0;
 			VectorCopy(mins, goal->mins);
 			VectorCopy(maxs, goal->maxs);
-			goal->number = 0;
-			goal->flags = 0;
-			goal->iteminfo = 0;
 			return num+1;
 		} //end if
 	} //end for

```
