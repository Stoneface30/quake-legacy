# Diff: `code/botlib/be_aas_sample.c`
**Canonical:** `wolfcamql-src` (sha256 `208222f7c023...`, 45523 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `a782401931f6...`, 45545 bytes

_Diff stat: +10 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_sample.c	2026-04-16 20:02:25.120907700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_sample.c	2026-04-16 20:02:19.850388800 +0100
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
@@ -38,12 +38,13 @@
 #include "l_libvar.h"
 #endif
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_interface.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
 
+extern botlib_import_t botimport;
 
 //#define AAS_SAMPLE_DEBUG
 
@@ -150,7 +151,7 @@
 	if (!link)
 	{
 #ifndef BSPC
-		if (botDeveloper)
+		if (bot_developer)
 #endif
 		{
 			botimport.Print(PRT_FATAL, "empty aas link heap\n");
@@ -688,7 +689,7 @@
 			side = front < 0;
 			//first put the end part of the line on the stack (back side)
 			VectorCopy(cur_mid, tstack_p->start);
-			//not necessary to store because still on stack
+			//not necesary to store because still on stack
 			//VectorCopy(cur_end, tstack_p->end);
 			tstack_p->planenum = aasnode->planenum;
 			tstack_p->nodenum = aasnode->children[!side];
@@ -874,7 +875,7 @@
 			side = front < 0;
 			//first put the end part of the line on the stack (back side)
 			VectorCopy(cur_mid, tstack_p->start);
-			//not necessary to store because still on stack
+			//not necesary to store because still on stack
 			//VectorCopy(cur_end, tstack_p->end);
 			tstack_p->planenum = aasnode->planenum;
 			tstack_p->nodenum = aasnode->children[!side];
@@ -959,7 +960,7 @@
 		//edge) and through both the edge vector and the normal vector
 		//of the plane
 		AAS_OrthogonalToVectors(edgevec, pnormal, sepnormal);
-		//check on which side of the above plane the point is
+		//check on wich side of the above plane the point is
 		//this is done by checking the sign of the dot product of the
 		//vector orthogonal vector from above and the vector from the
 		//origin (first vertex of edge) to the point 
@@ -1387,7 +1388,7 @@
 //===========================================================================
 aas_plane_t *AAS_PlaneFromNum(int planenum)
 {
-	if (!aasworld.loaded) return NULL;
+	if (!aasworld.loaded) return 0;
 
 	return &aasworld.planes[planenum];
 } //end of the function AAS_PlaneFromNum

```

### `quake3e`  — sha256 `70063493d688...`, 45577 bytes

_Diff stat: +15 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_sample.c	2026-04-16 20:02:25.120907700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_sample.c	2026-04-16 20:02:26.897995100 +0100
@@ -61,7 +61,7 @@
 	int nodenum;		//node found after splitting with planenum
 } aas_tracestack_t;
 
-int numaaslinks;
+static int numaaslinks;
 
 //===========================================================================
 //
@@ -73,8 +73,8 @@
 {
 	int index;
 	//bounding box size for each presence type
-	vec3_t boxmins[3] = {{0, 0, 0}, {-15, -15, -24}, {-15, -15, -24}};
-	vec3_t boxmaxs[3] = {{0, 0, 0}, { 15,  15,  32}, { 15,  15,   8}};
+	static const vec3_t boxmins[3] = {{0, 0, 0}, {-15, -15, -24}, {-15, -15, -24}};
+	static const vec3_t boxmaxs[3] = {{0, 0, 0}, { 15,  15,  32}, { 15,  15,   8}};
 
 	if (presencetype == PRESENCE_NORMAL) index = 1;
 	else if (presencetype == PRESENCE_CROUCH) index = 2;
@@ -103,9 +103,8 @@
 #ifdef BSPC
 		max_aaslinks = 6144;
 #else
-		max_aaslinks = (int) LibVarValue("max_aaslinks", "6144");
+		max_aaslinks = LibVarInteger("max_aaslinks", "6144", 2, 65536);
 #endif
-		if (max_aaslinks < 0) max_aaslinks = 0;
 		aasworld.linkheapsize = max_aaslinks;
 		aasworld.linkheap = (aas_link_t *) GetHunkMemory(max_aaslinks * sizeof(aas_link_t));
 	} //end if
@@ -168,7 +167,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_DeAllocAASLink(aas_link_t *link)
+static void AAS_DeAllocAASLink(aas_link_t *link)
 {
 	if (aasworld.freelinks) aasworld.freelinks->prev_ent = link;
 	link->prev_ent = NULL;
@@ -347,6 +346,7 @@
 	if (!areanum) return PRESENCE_NONE;
 	return aasworld.areasettings[areanum].presencetype;
 } //end of the function AAS_PointPresenceType
+#if 0
 //===========================================================================
 // calculates the minimum distance between the origin of the box and the
 // given plane when both will collide on the given side of the plane
@@ -396,13 +396,14 @@
 //	VectorNegate(normal, v2);
 	return DotProduct(v1, v2);
 } //end of the function AAS_BoxOriginDistanceFromPlane
+#endif
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean AAS_AreaEntityCollision(int areanum, vec3_t start, vec3_t end,
+static qboolean AAS_AreaEntityCollision(int areanum, vec3_t start, vec3_t end,
 										int presencetype, int passent, aas_trace_t *trace)
 {
 	int collision;
@@ -699,7 +700,7 @@
 				return trace;
 			} //end if
 			//now put the part near the start of the line on the stack so we will
-			//continue with thats part first. This way we'll find the first
+			//continue with that part first. This way we'll find the first
 			//hit of the bbox
 			VectorCopy(cur_start, tstack_p->start);
 			VectorCopy(cur_mid, tstack_p->end);
@@ -885,7 +886,7 @@
 				return numareas;
 			} //end if
 			//now put the part near the start of the line on the stack so we will
-			//continue with thats part first. This way we'll find the first
+			//continue with that part first. This way we'll find the first
 			//hit of the bbox
 			VectorCopy(cur_start, tstack_p->start);
 			VectorCopy(cur_mid, tstack_p->end);
@@ -922,7 +923,7 @@
 // Returns:					qtrue if the point is within the face boundaries
 // Changes Globals:		-
 //===========================================================================
-qboolean AAS_InsideFace(aas_face_t *face, vec3_t pnormal, vec3_t point, float epsilon)
+static qboolean AAS_InsideFace(aas_face_t *face, vec3_t pnormal, vec3_t point, float epsilon)
 {
 	int i, firstvertex, edgenum;
 	vec3_t v0;
@@ -1007,6 +1008,7 @@
 	} //end for
 	return qtrue;
 } //end of the function AAS_PointInsideFace
+#if 0
 //===========================================================================
 // returns the ground face the given point is above in the given area
 //
@@ -1056,6 +1058,7 @@
 	VectorCopy(plane->normal, normal);
 	*dist = plane->dist;
 } //end of the function AAS_FacePlane
+#endif
 //===========================================================================
 // returns the face the trace end position is situated in
 //
@@ -1083,7 +1086,7 @@
 		//if the face is in the same plane as the trace end point
 		if ((face->planenum & ~1) == (trace->planenum & ~1))
 		{
-			//firstface is used for optimization, if theres only one
+			//firstface is used for optimization, if there is only one
 			//face in the plane then it has to be the good one
 			//if there are more faces in the same plane then always
 			//check the one with the fewest edges first
@@ -1123,7 +1126,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_BoxOnPlaneSide2(vec3_t absmins, vec3_t absmaxs, aas_plane_t *p)
+static int AAS_BoxOnPlaneSide2(vec3_t absmins, vec3_t absmaxs, aas_plane_t *p)
 {
 	int i, sides;
 	float dist1, dist2;

```

### `openarena-engine`  — sha256 `ab2b01c35e19...`, 45520 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_sample.c	2026-04-16 20:02:25.120907700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_sample.c	2026-04-16 22:48:25.712695500 +0100
@@ -688,7 +688,7 @@
 			side = front < 0;
 			//first put the end part of the line on the stack (back side)
 			VectorCopy(cur_mid, tstack_p->start);
-			//not necessary to store because still on stack
+			//not necesary to store because still on stack
 			//VectorCopy(cur_end, tstack_p->end);
 			tstack_p->planenum = aasnode->planenum;
 			tstack_p->nodenum = aasnode->children[!side];
@@ -874,7 +874,7 @@
 			side = front < 0;
 			//first put the end part of the line on the stack (back side)
 			VectorCopy(cur_mid, tstack_p->start);
-			//not necessary to store because still on stack
+			//not necesary to store because still on stack
 			//VectorCopy(cur_end, tstack_p->end);
 			tstack_p->planenum = aasnode->planenum;
 			tstack_p->nodenum = aasnode->children[!side];
@@ -959,7 +959,7 @@
 		//edge) and through both the edge vector and the normal vector
 		//of the plane
 		AAS_OrthogonalToVectors(edgevec, pnormal, sepnormal);
-		//check on which side of the above plane the point is
+		//check on wich side of the above plane the point is
 		//this is done by checking the sign of the dot product of the
 		//vector orthogonal vector from above and the vector from the
 		//origin (first vertex of edge) to the point 

```
