# Diff: `code/botlib/be_aas_bspq3.c`
**Canonical:** `wolfcamql-src` (sha256 `107c74ba3429...`, 15110 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `8bfef7ef7fe7...`, 15132 bytes

_Diff stat: +11 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_bspq3.c	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_bspq3.c	2026-04-16 20:02:19.842867400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,14 +29,14 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
 
@@ -70,7 +70,7 @@
 	bsp_epair_t *epairs;
 } bsp_entity_t;
 
-//id Software BSP data
+//id Sofware BSP data
 typedef struct bsp_s
 {
 	//true when bsp file is loaded
@@ -286,7 +286,8 @@
 	{
 		if (!strcmp(epair->key, key))
 		{
-			Q_strncpyz(value, epair->value, size);
+			strncpy(value, epair->value, size-1);
+			value[size-1] = '\0';
 			return qtrue;
 		} //end if
 	} //end for
@@ -391,7 +392,7 @@
 	{
 		if (strcmp(token.string, "{"))
 		{
-			ScriptError(script, "invalid %s", token.string);
+			ScriptError(script, "invalid %s\n", token.string);
 			AAS_FreeBSPEntities();
 			FreeScript(script);
 			return;
@@ -412,7 +413,7 @@
 			ent->epairs = epair;
 			if (token.type != TT_STRING)
 			{
-				ScriptError(script, "invalid %s", token.string);
+				ScriptError(script, "invalid %s\n", token.string);
 				AAS_FreeBSPEntities();
 				FreeScript(script);
 				return;
@@ -432,7 +433,7 @@
 		} //end while
 		if (strcmp(token.string, "}"))
 		{
-			ScriptError(script, "missing }");
+			ScriptError(script, "missing }\n");
 			AAS_FreeBSPEntities();
 			FreeScript(script);
 			return;
@@ -468,7 +469,7 @@
 	Com_Memset( &bspworld, 0, sizeof(bspworld) );
 } //end of the function AAS_DumpBSPData
 //===========================================================================
-// load a .bsp file
+// load an bsp file
 //
 // Parameter:				-
 // Returns:					-

```

### `quake3e`  — sha256 `0100da99090d...`, 15222 bytes

_Diff stat: +30 / -25 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_bspq3.c	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_bspq3.c	2026-04-16 20:02:26.891282500 +0100
@@ -30,6 +30,7 @@
  *****************************************************************************/
 
 #include "../qcommon/q_shared.h"
+#include "../qcommon/qcommon.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
@@ -48,14 +49,14 @@
 //#define DEG2RAD( a ) (( a * M_PI ) / 180.0F)
 
 #define MAX_BSPENTITIES		2048
-
+#if 0
 typedef struct rgb_s
 {
 	int red;
 	int green;
 	int blue;
 } rgb_t;
-
+#endif
 //bsp entity epair
 typedef struct bsp_epair_s
 {
@@ -84,7 +85,7 @@
 } bsp_t;
 
 //global bsp
-bsp_t bspworld;
+static bsp_t bspworld;
 
 
 #ifdef BSP_DEBUG
@@ -122,7 +123,7 @@
 	{CONTENTS_LADDER,"CONTENTS_LADDER"},
 	{0, 0}
 };
-
+#if 0
 void PrintContents(int contents)
 {
 	int i;
@@ -135,7 +136,7 @@
 		} //end if
 	} //end for
 } //end of the function PrintContents
-
+#endif
 #endif // BSP_DEBUG
 //===========================================================================
 // traces axial boxes of any size through the world
@@ -181,6 +182,7 @@
 	} //end if
 	return qfalse;
 } //end of the function AAS_EntityCollision
+#if 0
 //===========================================================================
 // returns true if in Potentially Hearable Set
 //
@@ -203,6 +205,7 @@
 {
 	return qtrue;
 } //end of the function AAS_inPHS
+#endif
 //===========================================================================
 //
 // Parameter:				-
@@ -233,6 +236,7 @@
 {
 	return NULL;
 } //end of the function AAS_BSPLinkEntity
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -243,6 +247,7 @@
 {
 	return 0;
 } //end of the function AAS_BoxEntities
+#endif
 //===========================================================================
 //
 // Parameter:			-
@@ -261,7 +266,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_BSPEntityInRange(int ent)
+static int AAS_BSPEntityInRange(int ent)
 {
 	if (ent <= 0 || ent >= bspworld.numentities)
 	{
@@ -276,7 +281,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_ValueForBSPEpairKey(int ent, char *key, char *value, int size)
+int AAS_ValueForBSPEpairKey(int ent, const char *key, char *value, int size)
 {
 	bsp_epair_t *epair;
 
@@ -286,7 +291,7 @@
 	{
 		if (!strcmp(epair->key, key))
 		{
-			Q_strncpyz(value, epair->value, size);
+			Q_strncpyz( value, epair->value, size );
 			return qtrue;
 		} //end if
 	} //end for
@@ -298,19 +303,17 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_VectorForBSPEpairKey(int ent, char *key, vec3_t v)
+int AAS_VectorForBSPEpairKey(int ent, const char *key, vec3_t v)
 {
-	char buf[MAX_EPAIRKEY];
-	double v1, v2, v3;
+	char buf[MAX_EPAIRKEY], *s[3];
 
 	VectorClear(v);
-	if (!AAS_ValueForBSPEpairKey(ent, key, buf, MAX_EPAIRKEY)) return qfalse;
+	if (!AAS_ValueForBSPEpairKey(ent, key, buf, sizeof( buf ) )) return qfalse;
 	//scanf into doubles, then assign, so it is vec_t size independent
-	v1 = v2 = v3 = 0;
-	sscanf(buf, "%lf %lf %lf", &v1, &v2, &v3);
-	v[0] = v1;
-	v[1] = v2;
-	v[2] = v3;
+	Com_Split( buf, s, 3, ' ' );
+	v[0] = Q_atof( s[0] );
+	v[1] = Q_atof( s[1] );
+	v[2] = Q_atof( s[2] );
 	return qtrue;
 } //end of the function AAS_VectorForBSPEpairKey
 //===========================================================================
@@ -319,12 +322,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_FloatForBSPEpairKey(int ent, char *key, float *value)
+int AAS_FloatForBSPEpairKey(int ent, const char *key, float *value)
 {
 	char buf[MAX_EPAIRKEY];
 	
 	*value = 0;
-	if (!AAS_ValueForBSPEpairKey(ent, key, buf, MAX_EPAIRKEY)) return qfalse;
+	if (!AAS_ValueForBSPEpairKey(ent, key, buf, sizeof( buf ))) return qfalse;
 	*value = atof(buf);
 	return qtrue;
 } //end of the function AAS_FloatForBSPEpairKey
@@ -334,12 +337,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_IntForBSPEpairKey(int ent, char *key, int *value)
+int AAS_IntForBSPEpairKey(int ent, const char *key, int *value)
 {
 	char buf[MAX_EPAIRKEY];
 	
 	*value = 0;
-	if (!AAS_ValueForBSPEpairKey(ent, key, buf, MAX_EPAIRKEY)) return qfalse;
+	if (!AAS_ValueForBSPEpairKey(ent, key, buf, sizeof( buf ))) return qfalse;
 	*value = atoi(buf);
 	return qtrue;
 } //end of the function AAS_IntForBSPEpairKey
@@ -349,7 +352,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_FreeBSPEntities(void)
+static void AAS_FreeBSPEntities(void)
 {
 	int i;
 	bsp_entity_t *ent;
@@ -375,7 +378,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_ParseBSPEntities(void)
+static void AAS_ParseBSPEntities(void)
 {
 	script_t *script;
 	token_t token;
@@ -440,16 +443,17 @@
 	} //end while
 	FreeScript(script);
 } //end of the function AAS_ParseBSPEntities
+#if 0
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_BSPTraceLight(vec3_t start, vec3_t end, vec3_t endpos, int *red, int *green, int *blue)
+static int AAS_BSPTraceLight(vec3_t start, vec3_t end, vec3_t endpos, int *red, int *green, int *blue)
 {
 	return 0;
-} //end of the function AAS_BSPTraceLight
+#endif
 //===========================================================================
 //
 // Parameter:				-
@@ -484,3 +488,4 @@
 	bspworld.loaded = qtrue;
 	return BLERR_NOERROR;
 } //end of the function AAS_LoadBSPFile
+

```

### `openarena-engine`  — sha256 `3f119c4d2c18...`, 15134 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_bspq3.c	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_bspq3.c	2026-04-16 22:48:25.706436100 +0100
@@ -70,7 +70,7 @@
 	bsp_epair_t *epairs;
 } bsp_entity_t;
 
-//id Software BSP data
+//id Sofware BSP data
 typedef struct bsp_s
 {
 	//true when bsp file is loaded
@@ -286,7 +286,8 @@
 	{
 		if (!strcmp(epair->key, key))
 		{
-			Q_strncpyz(value, epair->value, size);
+			strncpy(value, epair->value, size-1);
+			value[size-1] = '\0';
 			return qtrue;
 		} //end if
 	} //end for

```
