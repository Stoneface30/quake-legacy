# Diff: `code/botlib/be_aas_debug.c`
**Canonical:** `wolfcamql-src` (sha256 `c8bcc76182c5...`, 24403 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `03eec0aaca60...`, 24375 bytes

_Diff stat: +4 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_debug.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_debug.c	2026-04-16 20:02:19.844383000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,15 +29,15 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "l_libvar.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_interface.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
@@ -774,5 +774,4 @@
 	areanum = AAS_PointAreaNum(origin);
 	cluster = AAS_AreaCluster(areanum);
 	AAS_FloodAreas_r(areanum, cluster, done);
-	FreeMemory(done);
 }

```

### `quake3e`  — sha256 `3ff42fbc5f29...`, 24449 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_debug.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_debug.c	2026-04-16 20:02:26.892281200 +0100
@@ -45,9 +45,9 @@
 #define MAX_DEBUGLINES				1024
 #define MAX_DEBUGPOLYGONS			8192
 
-int debuglines[MAX_DEBUGLINES];
-int debuglinevisible[MAX_DEBUGLINES];
-int numdebuglines;
+static int debuglines[MAX_DEBUGLINES];
+static int debuglinevisible[MAX_DEBUGLINES];
+static int numdebuglines;
 
 static int debugpolygons[MAX_DEBUGPOLYGONS];
 
@@ -81,7 +81,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_ShowPolygon(int color, int numpoints, vec3_t *points)
+static void AAS_ShowPolygon(int color, int numpoints, vec3_t *points)
 {
 	int i;
 
@@ -346,7 +346,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_ShowFacePolygon(int facenum, int color, int flip)
+static void AAS_ShowFacePolygon(int facenum, int color, int flip)
 {
 	int i, edgenum, numpoints;
 	vec3_t points[128];
@@ -708,9 +708,9 @@
 		botimport.Print(PRT_MESSAGE, "\n");
 	} //end if
 	AAS_ShowReachability(&reach);
-} //end of the function ShowReachableAreas
+} //end of the function AAS_ShowReachableAreas
 
-void AAS_FloodAreas_r(int areanum, int cluster, int *done)
+static void AAS_FloodAreas_r(int areanum, int cluster, int *done)
 {
 	int nextareanum, i, facenum;
 	aas_area_t *area;

```

### `openarena-engine`  — sha256 `1768fd87b215...`, 24383 bytes

_Diff stat: +0 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_debug.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_debug.c	2026-04-16 22:48:25.707438500 +0100
@@ -774,5 +774,4 @@
 	areanum = AAS_PointAreaNum(origin);
 	cluster = AAS_AreaCluster(areanum);
 	AAS_FloodAreas_r(areanum, cluster, done);
-	FreeMemory(done);
 }

```
