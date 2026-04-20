# Diff: `code/botlib/be_ai_weight.c`
**Canonical:** `wolfcamql-src` (sha256 `6c480c1eda45...`, 27951 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `00574c186370...`, 27598 bytes

_Diff stat: +25 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_weight.c	2026-04-16 20:02:19.853390000 +0100
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
 #include "l_log.h"
 #include "l_utils.h"
@@ -38,8 +38,8 @@
 #include "l_struct.h"
 #include "l_libvar.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_ai_weight.h"
@@ -63,21 +63,14 @@
 	if (!PC_ExpectAnyToken(source, &token)) return qfalse;
 	if (!strcmp(token.string, "-"))
 	{
-		SourceWarning(source, "negative value set to zero");
-
-		if(!PC_ExpectAnyToken(source, &token))
-		{
-			SourceError(source, "Missing return value");
-			return qfalse;
-		}
-	}
-
+		SourceWarning(source, "negative value set to zero\n");
+		if (!PC_ExpectTokenType(source, TT_NUMBER, 0, &token)) return qfalse;
+	} //end if
 	if (token.type != TT_NUMBER)
 	{
-		SourceError(source, "invalid return value %s", token.string);
+		SourceError(source, "invalid return value %s\n", token.string);
 		return qfalse;
-	}
-	
+	} //end if
 	*value = token.floatvalue;
 	return qtrue;
 } //end of the function ReadValue
@@ -186,7 +179,7 @@
 			{
 				if (founddefault)
 				{
-					SourceError(source, "switch already has a default");
+					SourceError(source, "switch already has a default\n");
 					FreeFuzzySeperators_r(firstfs);
 					return NULL;
 				} //end if
@@ -236,7 +229,7 @@
 			} //end else if
 			else
 			{
-				SourceError(source, "invalid name %s", token.string);
+				SourceError(source, "invalid name %s\n", token.string);
 				return NULL;
 			} //end else
 			if (newindent)
@@ -251,7 +244,7 @@
 		else
 		{
 			FreeFuzzySeperators_r(firstfs);
-			SourceError(source, "invalid name %s", token.string);
+			SourceError(source, "invalid name %s\n", token.string);
 			return NULL;
 		} //end else
 		if (!PC_ExpectAnyToken(source, &token))
@@ -263,7 +256,7 @@
 	//
 	if (!founddefault)
 	{
-		SourceWarning(source, "switch without default");
+		SourceWarning(source, "switch without default\n");
 		fs = (fuzzyseperator_t *) GetClearedMemory(sizeof(fuzzyseperator_t));
 		fs->index = index;
 		fs->value = MAX_INVENTORYVALUE;
@@ -272,6 +265,7 @@
 		fs->child = NULL;
 		if (lastfs) lastfs->next = fs;
 		else firstfs = fs;
+		lastfs = fs;
 	} //end if
 	//
 	return firstfs;
@@ -327,7 +321,7 @@
 	source = LoadSourceFile(filename);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 		return NULL;
 	} //end if
 	//
@@ -341,7 +335,7 @@
 		{
 			if (config->numweights >= MAX_WEIGHTS)
 			{
-				SourceWarning(source, "too many fuzzy weights");
+				SourceWarning(source, "too many fuzzy weights\n");
 				break;
 			} //end if
 			if (!PC_ExpectTokenType(source, TT_STRING, 0, &token))
@@ -399,7 +393,7 @@
 			} //end else if
 			else
 			{
-				SourceError(source, "invalid name %s", token.string);
+				SourceError(source, "invalid name %s\n", token.string);
 				FreeWeightConfig(config);
 				FreeSource(source);
 				return NULL;
@@ -417,7 +411,7 @@
 		} //end if
 		else
 		{
-			SourceError(source, "invalid name %s", token.string);
+			SourceError(source, "invalid name %s\n", token.string);
 			FreeWeightConfig(config);
 			FreeSource(source);
 			return NULL;
@@ -428,7 +422,7 @@
 	//if the file was located in a pak file
 	botimport.Print(PRT_MESSAGE, "loaded %s\n", filename);
 #ifdef DEBUG
-	if (botDeveloper)
+	if (bot_developer)
 	{
 		botimport.Print(PRT_MESSAGE, "weights loaded in %d msec\n", Sys_MilliSeconds() - starttime);
 	} //end if
@@ -599,12 +593,9 @@
 			if (fs->next->child) w2 = FuzzyWeight_r(inventory, fs->next->child);
 			else w2 = fs->next->weight;
 			//the scale factor
-			if(fs->next->value == MAX_INVENTORYVALUE) // is fs->next the default case?
-        		return w2;      // can't interpolate, return default weight
-			else
-				scale = (float) (inventory[fs->index] - fs->value) / (fs->next->value - fs->value);
+			scale = (inventory[fs->index] - fs->value) / (fs->next->value - fs->value);
 			//scale between the two weights
-			return (1 - scale) * w1 + scale * w2;
+			return scale * w1 + (1 - scale) * w2;
 		} //end if
 		return FuzzyWeight_r(inventory, fs->next);
 	} //end else if
@@ -636,12 +627,9 @@
 			if (fs->next->child) w2 = FuzzyWeight_r(inventory, fs->next->child);
 			else w2 = fs->next->minweight + random() * (fs->next->maxweight - fs->next->minweight);
 			//the scale factor
-			if(fs->next->value == MAX_INVENTORYVALUE) // is fs->next the default case?
-        		return w2;      // can't interpolate, return default weight
-			else
-				scale = (float) (inventory[fs->index] - fs->value) / (fs->next->value - fs->value);
+			scale = (inventory[fs->index] - fs->value) / (fs->next->value - fs->value);
 			//scale between the two weights
-			return (1 - scale) * w1 + scale * w2;
+			return scale * w1 + (1 - scale) * w2;
 		} //end if
 		return FuzzyWeightUndecided_r(inventory, fs->next);
 	} //end else if
@@ -726,7 +714,7 @@
 		//every once in a while an evolution leap occurs, mutation
 		if (random() < 0.01) fs->weight += crandom() * (fs->maxweight - fs->minweight);
 		else fs->weight += crandom() * (fs->maxweight - fs->minweight) * 0.5;
-		//modify bounds if necessary because of mutation
+		//modify bounds if necesary because of mutation
 		if (fs->weight < fs->minweight) fs->minweight = fs->weight;
 		else if (fs->weight > fs->maxweight) fs->maxweight = fs->weight;
 	} //end else if
@@ -762,7 +750,7 @@
 	else if (fs->type == WT_BALANCE)
 	{
 		//
-		fs->weight = (float) (fs->maxweight + fs->minweight) * scale;
+		fs->weight = (fs->maxweight + fs->minweight) * scale;
 		//get the weight between bounds
 		if (fs->weight < fs->minweight) fs->weight = fs->minweight;
 		else if (fs->weight > fs->maxweight) fs->weight = fs->maxweight;

```

### `quake3e`  — sha256 `558ecbe69c4f...`, 28073 bytes

_Diff stat: +17 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_weight.c	2026-04-16 20:02:26.902995100 +0100
@@ -48,7 +48,7 @@
 #define EVALUATERECURSIVELY
 
 #define MAX_WEIGHT_FILES			128
-weightconfig_t	*weightFileList[MAX_WEIGHT_FILES];
+static weightconfig_t	*weightFileList[MAX_WEIGHT_FILES];
 
 //===========================================================================
 //
@@ -56,7 +56,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int ReadValue(source_t *source, float *value)
+static int ReadValue(source_t *source, float *value)
 {
 	token_t token;
 
@@ -87,7 +87,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int ReadFuzzyWeight(source_t *source, fuzzyseperator_t *fs)
+static int ReadFuzzyWeight(source_t *source, fuzzyseperator_t *fs)
 {
 	if (PC_CheckTokenString(source, "balance"))
 	{
@@ -116,7 +116,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void FreeFuzzySeperators_r(fuzzyseperator_t *fs)
+static void FreeFuzzySeperators_r(fuzzyseperator_t *fs)
 {
 	if (!fs) return;
 	if (fs->child) FreeFuzzySeperators_r(fs->child);
@@ -129,7 +129,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void FreeWeightConfig2(weightconfig_t *config)
+static void FreeWeightConfig2(weightconfig_t *config)
 {
 	int i;
 
@@ -157,7 +157,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-fuzzyseperator_t *ReadFuzzySeperators_r(source_t *source)
+static fuzzyseperator_t *ReadFuzzySeperators_r(source_t *source)
 {
 	int newindent, index, def, founddefault;
 	token_t token;
@@ -282,7 +282,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-weightconfig_t *ReadWeightConfig(char *filename)
+weightconfig_t *ReadWeightConfig(const char *filename)
 {
 	int newindent, avail = 0, n;
 	token_t token;
@@ -448,7 +448,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean WriteFuzzyWeight(FILE *fp, fuzzyseperator_t *fs)
+static qboolean WriteFuzzyWeight(FILE *fp, fuzzyseperator_t *fs)
 {
 	if (fs->type == WT_BALANCE)
 	{
@@ -474,7 +474,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean WriteFuzzySeperators_r(FILE *fp, fuzzyseperator_t *fs, int indent)
+static qboolean WriteFuzzySeperators_r(FILE *fp, fuzzyseperator_t *fs, int indent)
 {
 	if (!WriteIndent(fp, indent)) return qfalse;
 	if (fprintf(fp, "switch(%d)\n", fs->index) < 0) return qfalse;
@@ -531,7 +531,7 @@
 	FILE *fp;
 	weight_t *ifw;
 
-	fp = fopen(filename, "wb");
+	fp = Sys_FOpen( filename, "wb" );
 	if (!fp) return qfalse;
 
 	for (i = 0; i < config->numweights; i++)
@@ -560,7 +560,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int FindFuzzyWeight(weightconfig_t *wc, char *name)
+int FindFuzzyWeight(const weightconfig_t *wc, const char *name)
 {
 	int i;
 
@@ -579,7 +579,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float FuzzyWeight_r(int *inventory, fuzzyseperator_t *fs)
+static float FuzzyWeight_r(int *inventory, fuzzyseperator_t *fs)
 {
 	float scale, w1, w2;
 
@@ -616,7 +616,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float FuzzyWeightUndecided_r(int *inventory, fuzzyseperator_t *fs)
+static float FuzzyWeightUndecided_r(int *inventory, fuzzyseperator_t *fs)
 {
 	float scale, w1, w2;
 
@@ -715,7 +715,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EvolveFuzzySeperator_r(fuzzyseperator_t *fs)
+static void EvolveFuzzySeperator_r(fuzzyseperator_t *fs)
 {
 	if (fs->child)
 	{
@@ -753,7 +753,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void ScaleFuzzySeperator_r(fuzzyseperator_t *fs, float scale)
+static void ScaleFuzzySeperator_r(fuzzyseperator_t *fs, float scale)
 {
 	if (fs->child)
 	{
@@ -796,7 +796,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void ScaleFuzzySeperatorBalanceRange_r(fuzzyseperator_t *fs, float scale)
+static void ScaleFuzzySeperatorBalanceRange_r(fuzzyseperator_t *fs, float scale)
 {
 	if (fs->child)
 	{
@@ -838,7 +838,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int InterbreedFuzzySeperator_r(fuzzyseperator_t *fs1, fuzzyseperator_t *fs2,
+static int InterbreedFuzzySeperator_r(fuzzyseperator_t *fs1, fuzzyseperator_t *fs2,
 								fuzzyseperator_t *fsout)
 {
 	if (fs1->child)

```

### `openarena-engine`  — sha256 `b661b913375f...`, 27951 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.c	2026-04-16 20:02:25.125416700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_weight.c	2026-04-16 22:48:25.715695800 +0100
@@ -327,7 +327,7 @@
 	source = LoadSourceFile(filename);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 		return NULL;
 	} //end if
 	//
@@ -726,7 +726,7 @@
 		//every once in a while an evolution leap occurs, mutation
 		if (random() < 0.01) fs->weight += crandom() * (fs->maxweight - fs->minweight);
 		else fs->weight += crandom() * (fs->maxweight - fs->minweight) * 0.5;
-		//modify bounds if necessary because of mutation
+		//modify bounds if necesary because of mutation
 		if (fs->weight < fs->minweight) fs->minweight = fs->weight;
 		else if (fs->weight > fs->maxweight) fs->maxweight = fs->weight;
 	} //end else if

```
