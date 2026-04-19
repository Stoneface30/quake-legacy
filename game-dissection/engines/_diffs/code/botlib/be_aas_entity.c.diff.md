# Diff: `code/botlib/be_aas_entity.c`
**Canonical:** `wolfcamql-src` (sha256 `cf84b02833f5...`, 13396 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `33d01a428e8a...`, 13384 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_entity.c	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_entity.c	2026-04-16 20:02:19.845388400 +0100
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
 #include "l_script.h"
 #include "l_precomp.h"
@@ -37,8 +37,8 @@
 #include "l_utils.h"
 #include "l_log.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_aas_def.h"
@@ -390,9 +390,9 @@
 		ent = &aasworld.entities[i];
 		if (ent->i.modelindex != modelindex) continue;
 		VectorSubtract(ent->i.origin, origin, dir);
-		if (fabsf(dir[0]) < 40)
+		if (abs(dir[0]) < 40)
 		{
-			if (fabsf(dir[1]) < 40)
+			if (abs(dir[1]) < 40)
 			{
 				dist = VectorLength(dir);
 				if (dist < bestdist)

```

### `quake3e`  — sha256 `36b60963549c...`, 13630 bytes

_Diff stat: +15 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_entity.c	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_entity.c	2026-04-16 20:02:26.892281200 +0100
@@ -72,6 +72,12 @@
 		return BLERR_NOAASFILE;
 	} //end if
 
+	if (entnum < 0 || entnum >= aasworld.maxentities)
+	{
+		botimport.Print(PRT_FATAL, "AAS_UpdateEntity: entnum %d out of range\n", entnum);
+		return BLERR_INVALIDENTITYNUMBER;
+	}
+
 	ent = &aasworld.entities[entnum];
 
 	if (!state) {
@@ -186,6 +192,7 @@
 
 	Com_Memcpy(info, &aasworld.entities[entnum].i, sizeof(aas_entityinfo_t));
 } //end of the function AAS_EntityInfo
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -203,6 +210,7 @@
 
 	VectorCopy(aasworld.entities[entnum].i.origin, origin);
 } //end of the function AAS_EntityOrigin
+#endif
 //===========================================================================
 //
 // Parameter:				-
@@ -277,6 +285,7 @@
 	} //end for
 	return qfalse;
 } //end of the function AAS_OriginOfMoverWithModelNum
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -317,6 +326,7 @@
 	entdata->solid = ent->i.solid;
 	entdata->modelnum = ent->i.modelindex - 1;
 } //end of the function AAS_EntityBSPData
+#endif
 //===========================================================================
 //
 // Parameter:				-
@@ -370,6 +380,7 @@
 		} //end for
 	} //end for
 } //end of the function AAS_UnlinkInvalidEntities
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -390,9 +401,9 @@
 		ent = &aasworld.entities[i];
 		if (ent->i.modelindex != modelindex) continue;
 		VectorSubtract(ent->i.origin, origin, dir);
-		if (fabsf(dir[0]) < 40)
+		if (fabs(dir[0]) < 40)
 		{
-			if (fabsf(dir[1]) < 40)
+			if (fabs(dir[1]) < 40)
 			{
 				dist = VectorLength(dir);
 				if (dist < bestdist)
@@ -411,13 +422,14 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_BestReachableEntityArea(int entnum)
+static int AAS_BestReachableEntityArea(int entnum)
 {
 	aas_entity_t *ent;
 
 	ent = &aasworld.entities[entnum];
 	return AAS_BestReachableLinkArea(ent->areas);
 } //end of the function AAS_BestReachableEntityArea
+#endif
 //===========================================================================
 //
 // Parameter:			-

```

### `openarena-engine`  — sha256 `5d2b8b28003d...`, 13392 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_entity.c	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_entity.c	2026-04-16 22:48:25.708437600 +0100
@@ -390,9 +390,9 @@
 		ent = &aasworld.entities[i];
 		if (ent->i.modelindex != modelindex) continue;
 		VectorSubtract(ent->i.origin, origin, dir);
-		if (fabsf(dir[0]) < 40)
+		if (abs(dir[0]) < 40)
 		{
-			if (fabsf(dir[1]) < 40)
+			if (abs(dir[1]) < 40)
 			{
 				dist = VectorLength(dir);
 				if (dist < bestdist)

```
