# Diff: `code/botlib/be_aas_main.c`
**Canonical:** `wolfcamql-src` (sha256 `a7b5bd611d4a...`, 10909 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `944d934e0a99...`, 13967 bytes

_Diff stat: +105 / -14 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_main.c	2026-04-16 20:02:19.846388500 +0100
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
 #include "l_memory.h"
 #include "l_libvar.h"
 #include "l_utils.h"
@@ -38,8 +38,8 @@
 #include "l_struct.h"
 #include "l_log.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_aas_def.h"
@@ -60,9 +60,9 @@
 	va_list arglist;
 
 	va_start(arglist, fmt);
-	Q_vsnprintf(str, sizeof(str), fmt, arglist);
+	vsprintf(str, fmt, arglist);
 	va_end(arglist);
-	botimport.Print(PRT_FATAL, "%s", str);
+	botimport.Print(PRT_FATAL, str);
 } //end of the function AAS_Error
 //===========================================================================
 //
@@ -70,6 +70,96 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
+char *AAS_StringFromIndex(char *indexname, char *stringindex[], int numindexes, int index)
+{
+	if (!aasworld.indexessetup)
+	{
+		botimport.Print(PRT_ERROR, "%s: index %d not setup\n", indexname, index);
+		return "";
+	} //end if
+	if (index < 0 || index >= numindexes)
+	{
+		botimport.Print(PRT_ERROR, "%s: index %d out of range\n", indexname, index);
+		return "";
+	} //end if
+	if (!stringindex[index])
+	{
+		if (index)
+		{
+			botimport.Print(PRT_ERROR, "%s: reference to unused index %d\n", indexname, index);
+		} //end if
+		return "";
+	} //end if
+	return stringindex[index];
+} //end of the function AAS_StringFromIndex
+//===========================================================================
+//
+// Parameter:				-
+// Returns:					-
+// Changes Globals:		-
+//===========================================================================
+int AAS_IndexFromString(char *indexname, char *stringindex[], int numindexes, char *string)
+{
+	int i;
+	if (!aasworld.indexessetup)
+	{
+		botimport.Print(PRT_ERROR, "%s: index not setup \"%s\"\n", indexname, string);
+		return 0;
+	} //end if
+	for (i = 0; i < numindexes; i++)
+	{
+		if (!stringindex[i]) continue;
+		if (!Q_stricmp(stringindex[i], string)) return i;
+	} //end for
+	return 0;
+} //end of the function AAS_IndexFromString
+//===========================================================================
+//
+// Parameter:				-
+// Returns:					-
+// Changes Globals:		-
+//===========================================================================
+char *AAS_ModelFromIndex(int index)
+{
+	return AAS_StringFromIndex("ModelFromIndex", &aasworld.configstrings[CS_MODELS], MAX_MODELS, index);
+} //end of the function AAS_ModelFromIndex
+//===========================================================================
+//
+// Parameter:				-
+// Returns:					-
+// Changes Globals:		-
+//===========================================================================
+int AAS_IndexFromModel(char *modelname)
+{
+	return AAS_IndexFromString("IndexFromModel", &aasworld.configstrings[CS_MODELS], MAX_MODELS, modelname);
+} //end of the function AAS_IndexFromModel
+//===========================================================================
+//
+// Parameter:				-
+// Returns:					-
+// Changes Globals:		-
+//===========================================================================
+void AAS_UpdateStringIndexes(int numconfigstrings, char *configstrings[])
+{
+	int i;
+	//set string pointers and copy the strings
+	for (i = 0; i < numconfigstrings; i++)
+	{
+		if (configstrings[i])
+		{
+			//if (aasworld.configstrings[i]) FreeMemory(aasworld.configstrings[i]);
+			aasworld.configstrings[i] = (char *) GetMemory(strlen(configstrings[i]) + 1);
+			strcpy(aasworld.configstrings[i], configstrings[i]);
+		} //end if
+	} //end for
+	aasworld.indexessetup = qtrue;
+} //end of the function AAS_UpdateStringIndexes
+//===========================================================================
+//
+// Parameter:				-
+// Returns:					-
+// Changes Globals:		-
+//===========================================================================
 int AAS_Loaded(void)
 {
 	return aasworld.loaded;
@@ -126,7 +216,7 @@
 		//save the AAS file
 		if (AAS_WriteAASFile(aasworld.filename))
 		{
-			botimport.Print(PRT_MESSAGE, "%s written successfully\n", aasworld.filename);
+			botimport.Print(PRT_MESSAGE, "%s written succesfully\n", aasworld.filename);
 		} //end if
 		else
 		{
@@ -157,7 +247,7 @@
 	//
 	aasworld.frameroutingupdates = 0;
 	//
-	if (botDeveloper)
+	if (bot_developer)
 	{
 		if (LibVarGetValue("showcacheupdates"))
 		{
@@ -220,9 +310,10 @@
 int AAS_LoadFiles(const char *mapname)
 {
 	int errnum;
-	char aasfile[MAX_QPATH];
+	char aasfile[MAX_PATH];
+//	char bspfile[MAX_PATH];
 
-	Q_strncpyz(aasworld.mapname, mapname, sizeof(aasworld.mapname));
+	strcpy(aasworld.mapname, mapname);
 	//NOTE: first reset the entity links into the AAS areas and BSP leaves
 	// the AAS link heap and BSP link heap are reset after respectively the
 	// AAS file and BSP file are loaded
@@ -231,17 +322,17 @@
 	AAS_LoadBSPFile();
 
 	//load the aas file
-	Com_sprintf(aasfile, sizeof(aasfile), "maps/%s.aas", mapname);
+	Com_sprintf(aasfile, MAX_PATH, "maps/%s.aas", mapname);
 	errnum = AAS_LoadAASFile(aasfile);
 	if (errnum != BLERR_NOERROR)
 		return errnum;
 
 	botimport.Print(PRT_MESSAGE, "loaded %s\n", aasfile);
-	Q_strncpyz(aasworld.filename, aasfile, sizeof(aasworld.filename));
+	strncpy(aasworld.filename, aasfile, MAX_PATH);
 	return BLERR_NOERROR;
 } //end of the function AAS_LoadFiles
 //===========================================================================
-// called every time a map changes
+// called everytime a map changes
 //
 // Parameter:				-
 // Returns:					-
@@ -332,7 +423,7 @@
 	//aas has not been initialized
 	aasworld.initialized = qfalse;
 	//NOTE: as soon as a new .bsp file is loaded the .bsp file memory is
-	// freed and reallocated, so there's no need to free that memory here
+	// freed an reallocated, so there's no need to free that memory here
 	//print shutdown
 	botimport.Print(PRT_MESSAGE, "AAS shutdown.\n");
 } //end of the function AAS_Shutdown

```

### `quake3e`  — sha256 `5dd15bde4225...`, 10980 bytes

_Diff stat: +7 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_main.c	2026-04-16 20:02:26.893283500 +0100
@@ -90,7 +90,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_SetInitialized(void)
+static void AAS_SetInitialized(void)
 {
 	aasworld.initialized = qtrue;
 	botimport.Print(PRT_MESSAGE, "AAS initialized.\n");
@@ -217,10 +217,11 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_LoadFiles(const char *mapname)
+static int AAS_LoadFiles(const char *mapname)
 {
 	int errnum;
-	char aasfile[MAX_QPATH];
+	char aasfile[MAX_PATH];
+//	char bspfile[MAX_PATH];
 
 	Q_strncpyz(aasworld.mapname, mapname, sizeof(aasworld.mapname));
 	//NOTE: first reset the entity links into the AAS areas and BSP leaves
@@ -237,7 +238,7 @@
 		return errnum;
 
 	botimport.Print(PRT_MESSAGE, "loaded %s\n", aasfile);
-	Q_strncpyz(aasworld.filename, aasfile, sizeof(aasworld.filename));
+	Q_strncpyz( aasworld.filename, aasfile, sizeof( aasworld.filename ) );
 	return BLERR_NOERROR;
 } //end of the function AAS_LoadFiles
 //===========================================================================
@@ -291,8 +292,8 @@
 //===========================================================================
 int AAS_Setup(void)
 {
-	aasworld.maxclients = (int) LibVarValue("maxclients", "128");
-	aasworld.maxentities = (int) LibVarValue("maxentities", "1024");
+	aasworld.maxclients = LibVarInteger("maxclients", "128", 0, MAX_CLIENTS);
+	aasworld.maxentities = LibVarInteger("maxentities", "1024", 0, MAX_GENTITIES);
 	// as soon as it's set to 1 the routing cache will be saved
 	saveroutingcache = LibVar("saveroutingcache", "0");
 	//allocate memory for the entities

```

### `openarena-engine`  — sha256 `7b06aea3b361...`, 10878 bytes

_Diff stat: +6 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_main.c	2026-04-16 22:48:25.709437000 +0100
@@ -220,9 +220,10 @@
 int AAS_LoadFiles(const char *mapname)
 {
 	int errnum;
-	char aasfile[MAX_QPATH];
+	char aasfile[MAX_PATH];
+//	char bspfile[MAX_PATH];
 
-	Q_strncpyz(aasworld.mapname, mapname, sizeof(aasworld.mapname));
+	strcpy(aasworld.mapname, mapname);
 	//NOTE: first reset the entity links into the AAS areas and BSP leaves
 	// the AAS link heap and BSP link heap are reset after respectively the
 	// AAS file and BSP file are loaded
@@ -231,17 +232,17 @@
 	AAS_LoadBSPFile();
 
 	//load the aas file
-	Com_sprintf(aasfile, sizeof(aasfile), "maps/%s.aas", mapname);
+	Com_sprintf(aasfile, MAX_PATH, "maps/%s.aas", mapname);
 	errnum = AAS_LoadAASFile(aasfile);
 	if (errnum != BLERR_NOERROR)
 		return errnum;
 
 	botimport.Print(PRT_MESSAGE, "loaded %s\n", aasfile);
-	Q_strncpyz(aasworld.filename, aasfile, sizeof(aasworld.filename));
+	strncpy(aasworld.filename, aasfile, MAX_PATH);
 	return BLERR_NOERROR;
 } //end of the function AAS_LoadFiles
 //===========================================================================
-// called every time a map changes
+// called everytime a map changes
 //
 // Parameter:				-
 // Returns:					-

```
