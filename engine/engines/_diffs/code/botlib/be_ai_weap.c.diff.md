# Diff: `code/botlib/be_ai_weap.c`
**Canonical:** `wolfcamql-src` (sha256 `654cd0ff499d...`, 18562 bytes)

## Variants

### `quake3-source`  — sha256 `675911fe618e...`, 18957 bytes

_Diff stat: +28 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weap.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_weap.c	2026-04-16 20:02:19.853390000 +0100
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
 #include "l_libvar.h"
 #include "l_log.h"
 #include "l_memory.h"
@@ -38,20 +38,20 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_ai_weight.h"		//fuzzy weights
-#include "be_ai_weap.h"
+#include "../game/be_ai_weap.h"
 
 //#define DEBUG_AI_WEAP
 
 //structure field offsets
-#define WEAPON_OFS(x) (size_t)&(((weaponinfo_t *)0)->x)
-#define PROJECTILE_OFS(x) (size_t)&(((projectileinfo_t *)0)->x)
+#define WEAPON_OFS(x) (int)&(((weaponinfo_t *)0)->x)
+#define PROJECTILE_OFS(x) (int)&(((projectileinfo_t *)0)->x)
 
-//weapon definition
+//weapon definition // bk001212 - static
 static fielddef_t weaponinfo_fields[] =
 {
 {"number", WEAPON_OFS(number), FT_INT},						//weapon number
@@ -83,7 +83,7 @@
 static fielddef_t projectileinfo_fields[] =
 {
 {"name", PROJECTILE_OFS(name), FT_STRING},					//name of the projectile
-{"model", PROJECTILE_OFS(model), FT_STRING},						//model of the projectile
+{"model", WEAPON_OFS(model), FT_STRING},						//model of the projectile
 {"flags", PROJECTILE_OFS(flags), FT_INT},						//special flags
 {"gravity", PROJECTILE_OFS(gravity), FT_FLOAT},				//amount of gravity applied to the projectile [0,1]
 {"damage", PROJECTILE_OFS(damage), FT_INT},					//damage of the projectile
@@ -153,12 +153,12 @@
 {
 	if (handle <= 0 || handle > MAX_CLIENTS)
 	{
-		botimport.Print(PRT_FATAL, "weapon state handle %d out of range\n", handle);
+		botimport.Print(PRT_FATAL, "move state handle %d out of range\n", handle);
 		return NULL;
 	} //end if
 	if (!botweaponstates[handle])
 	{
-		botimport.Print(PRT_FATAL, "invalid weapon state %d\n", handle);
+		botimport.Print(PRT_FATAL, "invalid move state %d\n", handle);
 		return NULL;
 	} //end if
 	return botweaponstates[handle];
@@ -199,7 +199,7 @@
 {
 	int max_weaponinfo, max_projectileinfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	int i, j;
 	source_t *source;
 	weaponconfig_t *wc;
@@ -219,12 +219,12 @@
 		max_projectileinfo = 32;
 		LibVarSet("max_projectileinfo", "32");
 	} //end if
-	Q_strncpyz(path, filename, sizeof(path));
+	strncpy(path, filename, MAX_PATH);
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile(path);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", path);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", path);
 		return NULL;
 	} //end if
 	//initialize weapon config
@@ -440,6 +440,18 @@
 //===========================================================================
 void BotResetWeaponState(int weaponstate)
 {
+	struct weightconfig_s *weaponweightconfig;
+	int *weaponweightindex;
+	bot_weaponstate_t *ws;
+
+	ws = BotWeaponStateFromHandle(weaponstate);
+	if (!ws) return;
+	weaponweightconfig = ws->weaponweightconfig;
+	weaponweightindex = ws->weaponweightindex;
+
+	//Com_Memset(ws, 0, sizeof(bot_weaponstate_t));
+	ws->weaponweightconfig = weaponweightconfig;
+	ws->weaponweightindex = weaponweightindex;
 } //end of the function BotResetWeaponState
 //========================================================================
 //
@@ -471,12 +483,12 @@
 {
 	if (handle <= 0 || handle > MAX_CLIENTS)
 	{
-		botimport.Print(PRT_FATAL, "weapon state handle %d out of range\n", handle);
+		botimport.Print(PRT_FATAL, "move state handle %d out of range\n", handle);
 		return;
 	} //end if
 	if (!botweaponstates[handle])
 	{
-		botimport.Print(PRT_FATAL, "invalid weapon state %d\n", handle);
+		botimport.Print(PRT_FATAL, "invalid move state %d\n", handle);
 		return;
 	} //end if
 	BotFreeWeaponWeights(handle);

```

### `ioquake3`  — sha256 `2f88e6375566...`, 18561 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weap.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\botlib\be_ai_weap.c	2026-04-16 20:02:21.510907600 +0100
@@ -83,7 +83,7 @@
 static fielddef_t projectileinfo_fields[] =
 {
 {"name", PROJECTILE_OFS(name), FT_STRING},					//name of the projectile
-{"model", PROJECTILE_OFS(model), FT_STRING},						//model of the projectile
+{"model", PROJECTILE_OFS(model), FT_STRING},					//model of the projectile
 {"flags", PROJECTILE_OFS(flags), FT_INT},						//special flags
 {"gravity", PROJECTILE_OFS(gravity), FT_FLOAT},				//amount of gravity applied to the projectile [0,1]
 {"damage", PROJECTILE_OFS(damage), FT_INT},					//damage of the projectile

```

### `quake3e`  — sha256 `b13ad90a1429...`, 18287 bytes

_Diff stat: +17 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weap.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_weap.c	2026-04-16 20:02:26.901995600 +0100
@@ -52,7 +52,7 @@
 #define PROJECTILE_OFS(x) (size_t)&(((projectileinfo_t *)0)->x)
 
 //weapon definition
-static fielddef_t weaponinfo_fields[] =
+static const fielddef_t weaponinfo_fields[] =
 {
 {"number", WEAPON_OFS(number), FT_INT},						//weapon number
 {"name", WEAPON_OFS(name), FT_STRING},							//name of the weapon
@@ -80,10 +80,10 @@
 };
 
 //projectile definition
-static fielddef_t projectileinfo_fields[] =
+static const fielddef_t projectileinfo_fields[] =
 {
 {"name", PROJECTILE_OFS(name), FT_STRING},					//name of the projectile
-{"model", PROJECTILE_OFS(model), FT_STRING},						//model of the projectile
+{"model", PROJECTILE_OFS(model), FT_STRING},					//model of the projectile
 {"flags", PROJECTILE_OFS(flags), FT_INT},						//special flags
 {"gravity", PROJECTILE_OFS(gravity), FT_FLOAT},				//amount of gravity applied to the projectile [0,1]
 {"damage", PROJECTILE_OFS(damage), FT_INT},					//damage of the projectile
@@ -96,7 +96,7 @@
 {"bounce", PROJECTILE_OFS(bounce), FT_FLOAT},				//amount the projectile bounces
 {"bouncefric", PROJECTILE_OFS(bouncefric), FT_FLOAT}, 	//amount the bounce decreases per bounce
 {"bouncestop", PROJECTILE_OFS(bouncestop), FT_FLOAT},		//minimum bounce value before bouncing stops
-//recurive projectile definition??
+//recursive projectile definition??
 {NULL, 0, 0, 0}
 };
 
@@ -134,7 +134,7 @@
 // Returns:					-
 // Changes Globals:		-
 //========================================================================
-int BotValidWeaponNumber(int weaponnum)
+static int BotValidWeaponNumber(int weaponnum)
 {
 	if (weaponnum <= 0 || weaponnum > weaponconfig->numweapons)
 	{
@@ -149,7 +149,7 @@
 // Returns:					-
 // Changes Globals:		-
 //========================================================================
-bot_weaponstate_t *BotWeaponStateFromHandle(int handle)
+static bot_weaponstate_t *BotWeaponStateFromHandle(int handle)
 {
 	if (handle <= 0 || handle > MAX_CLIENTS)
 	{
@@ -170,7 +170,7 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef DEBUG_AI_WEAP
-void DumpWeaponConfig(weaponconfig_t *wc)
+static void DumpWeaponConfig(weaponconfig_t *wc)
 {
 	FILE *fp;
 	int i;
@@ -195,31 +195,20 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-weaponconfig_t *LoadWeaponConfig(char *filename)
+static weaponconfig_t *LoadWeaponConfig(const char *filename)
 {
 	int max_weaponinfo, max_projectileinfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	int i, j;
 	source_t *source;
 	weaponconfig_t *wc;
 	weaponinfo_t weaponinfo;
 
-	max_weaponinfo = (int) LibVarValue("max_weaponinfo", "32");
-	if (max_weaponinfo < 0)
-	{
-		botimport.Print(PRT_ERROR, "max_weaponinfo = %d\n", max_weaponinfo);
-		max_weaponinfo = 32;
-		LibVarSet("max_weaponinfo", "32");
-	} //end if
-	max_projectileinfo = (int) LibVarValue("max_projectileinfo", "32");
-	if (max_projectileinfo < 0)
-	{
-		botimport.Print(PRT_ERROR, "max_projectileinfo = %d\n", max_projectileinfo);
-		max_projectileinfo = 32;
-		LibVarSet("max_projectileinfo", "32");
-	} //end if
-	Q_strncpyz(path, filename, sizeof(path));
+	max_weaponinfo = LibVarInteger("max_weaponinfo", "32", 0, 4096);
+	max_projectileinfo = LibVarInteger("max_projectileinfo", "32", 0, 4096);
+
+	Q_strncpyz( path, filename, sizeof( path ) );
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile(path);
 	if (!source)
@@ -327,7 +316,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int *WeaponWeightIndex(weightconfig_t *wwc, weaponconfig_t *wc)
+static int *WeaponWeightIndex(const weightconfig_t *wwc, const weaponconfig_t *wc)
 {
 	int *index, i;
 
@@ -346,7 +335,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void BotFreeWeaponWeights(int weaponstate)
+static void BotFreeWeaponWeights(int weaponstate)
 {
 	bot_weaponstate_t *ws;
 
@@ -361,7 +350,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int BotLoadWeaponWeights(int weaponstate, char *filename)
+int BotLoadWeaponWeights(int weaponstate, const char *filename)
 {
 	bot_weaponstate_t *ws;
 
@@ -491,7 +480,7 @@
 //===========================================================================
 int BotSetupWeaponAI(void)
 {
-	char *file;
+	const char *file;
 
 	file = LibVarString("weaponconfig", "weapons.c");
 	weaponconfig = LoadWeaponConfig(file);

```

### `openarena-engine`  — sha256 `49027042e9c1...`, 18554 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weap.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_weap.c	2026-04-16 22:48:25.715695800 +0100
@@ -83,7 +83,7 @@
 static fielddef_t projectileinfo_fields[] =
 {
 {"name", PROJECTILE_OFS(name), FT_STRING},					//name of the projectile
-{"model", PROJECTILE_OFS(model), FT_STRING},						//model of the projectile
+{"model", PROJECTILE_OFS(model), FT_STRING},					//model of the projectile
 {"flags", PROJECTILE_OFS(flags), FT_INT},						//special flags
 {"gravity", PROJECTILE_OFS(gravity), FT_FLOAT},				//amount of gravity applied to the projectile [0,1]
 {"damage", PROJECTILE_OFS(damage), FT_INT},					//damage of the projectile
@@ -199,7 +199,7 @@
 {
 	int max_weaponinfo, max_projectileinfo;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 	int i, j;
 	source_t *source;
 	weaponconfig_t *wc;
@@ -219,12 +219,12 @@
 		max_projectileinfo = 32;
 		LibVarSet("max_projectileinfo", "32");
 	} //end if
-	Q_strncpyz(path, filename, sizeof(path));
+	strncpy(path, filename, MAX_PATH);
 	PC_SetBaseFolder(BOTFILESBASEFOLDER);
 	source = LoadSourceFile(path);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", path);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", path);
 		return NULL;
 	} //end if
 	//initialize weapon config

```
