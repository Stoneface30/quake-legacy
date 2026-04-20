# Diff: `code/botlib/be_aas_optimize.c`
**Canonical:** `wolfcamql-src` (sha256 `c8243f0fd904...`, 11313 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `51806ef858e6...`, 11305 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_optimize.c	2026-04-16 20:02:25.117868900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_optimize.c	2026-04-16 20:02:19.847388800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,15 +30,15 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_libvar.h"
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
 #include "be_interface.h"
 #include "be_aas_def.h"

```

### `quake3e`  — sha256 `24d35736a348...`, 11362 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_optimize.c	2026-04-16 20:02:25.117868900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_optimize.c	2026-04-16 20:02:26.895403300 +0100
@@ -75,7 +75,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_KeepEdge(aas_edge_t *edge)
+static int AAS_KeepEdge(aas_edge_t *edge)
 {
 	return 1;
 } //end of the function AAS_KeepFace
@@ -85,7 +85,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_OptimizeEdge(optimized_t *optimized, int edgenum)
+static int AAS_OptimizeEdge(optimized_t *optimized, int edgenum)
 {
 	int i, optedgenum;
 	aas_edge_t *edge, *optedge;
@@ -130,7 +130,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_KeepFace(aas_face_t *face)
+static int AAS_KeepFace(aas_face_t *face)
 {
 	if (!(face->faceflags & FACE_LADDER)) return 0;
 	else return 1;
@@ -141,7 +141,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_OptimizeFace(optimized_t *optimized, int facenum)
+static int AAS_OptimizeFace(optimized_t *optimized, int facenum)
 {
 	int i, edgenum, optedgenum, optfacenum;
 	aas_face_t *face, *optface;
@@ -186,7 +186,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_OptimizeArea(optimized_t *optimized, int areanum)
+static void AAS_OptimizeArea(optimized_t *optimized, int areanum)
 {
 	int i, facenum, optfacenum;
 	aas_area_t *area, *optarea;
@@ -215,7 +215,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_OptimizeAlloc(optimized_t *optimized)
+static void AAS_OptimizeAlloc(optimized_t *optimized)
 {
 	optimized->vertexes = (aas_vertex_t *) GetClearedMemory(aasworld.numvertexes * sizeof(aas_vertex_t));
 	optimized->numvertexes = 0;
@@ -240,7 +240,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_OptimizeStore(optimized_t *optimized)
+static void AAS_OptimizeStore(optimized_t *optimized)
 {
 	//store the optimized vertexes
 	if (aasworld.vertexes) FreeMemory(aasworld.vertexes);

```
