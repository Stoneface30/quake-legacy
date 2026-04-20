# Diff: `code/botlib/be_aas_routealt.c`
**Canonical:** `wolfcamql-src` (sha256 `40bf0cfe1555...`, 8523 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `e88529d98170...`, 8515 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_routealt.c	2026-04-16 20:02:25.119908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_routealt.c	2026-04-16 20:02:19.849387000 +0100
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
 #include "l_memory.h"
 #include "l_log.h"
@@ -37,8 +37,8 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_aas_def.h"

```

### `quake3e`  — sha256 `7fc6c82438d8...`, 8552 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_routealt.c	2026-04-16 20:02:25.119908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_routealt.c	2026-04-16 20:02:26.897995100 +0100
@@ -53,9 +53,9 @@
 	unsigned short goaltime;
 } midrangearea_t;
 
-midrangearea_t *midrangeareas;
-int *clusterareas;
-int numclusterareas;
+static midrangearea_t *midrangeareas;
+static int *clusterareas;
+static int numclusterareas;
 
 //===========================================================================
 //
@@ -63,7 +63,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_AltRoutingFloodCluster_r(int areanum)
+static void AAS_AltRoutingFloodCluster_r(int areanum)
 {
 	int i, otherareanum;
 	aas_area_t *area;
@@ -139,7 +139,7 @@
 		} //end if
 		//if the area has no reachabilities
 		if (!AAS_AreaReachability(i)) continue;
-		//tavel time from the area to the start area
+		//travel time from the area to the start area
 		starttime = AAS_AreaTravelTimeToGoalArea(startareanum, start, i, travelflags);
 		if (!starttime) continue;
 		//if the travel time from the start to the area is greater than the shortest goal travel time

```
