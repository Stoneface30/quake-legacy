# Diff: `code/botlib/be_aas_reach.c`
**Canonical:** `wolfcamql-src` (sha256 `d3868bfd258d...`, 157583 bytes)

## Variants

### `quake3-source`  — sha256 `293a1a4560c6...`, 157424 bytes

_Diff stat: +58 / -56 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_reach.c	2026-04-16 20:02:25.118908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_reach.c	2026-04-16 20:02:19.848387200 +0100
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
 #include "l_log.h"
 #include "l_memory.h"
 #include "l_script.h"
@@ -37,8 +37,8 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
 
@@ -289,7 +289,7 @@
 //===========================================================================
 int AAS_BestReachableFromJumpPadArea(vec3_t origin, vec3_t mins, vec3_t maxs)
 {
-	int ent, bot_visualizejumppads, bestareanum;
+	int area2num, ent, bot_visualizejumppads, bestareanum;
 	float volume, bestareavolume;
 	vec3_t areastart, cmdmove, bboxmins, bboxmaxs;
 	vec3_t absmins, absmaxs, velocity;
@@ -327,6 +327,7 @@
 		//
 		VectorSet(cmdmove, 0, 0, 0);
 		Com_Memset(&move, 0, sizeof(aas_clientmove_t));
+		area2num = 0;
 		AAS_ClientMovementHitBBox(&move, -1, areastart, PRESENCE_NORMAL, qfalse,
 								velocity, cmdmove, 0, 30, 0.1f, bboxmins, bboxmaxs, bot_visualizejumppads);
 		if (move.frames < 30)
@@ -412,7 +413,7 @@
 		else
 		{
 			//it can very well happen that the AAS_PointAreaNum function tells that
-			//a point is in an area and that starting an AAS_TraceClientBBox from that
+			//a point is in an area and that starting a AAS_TraceClientBBox from that
 			//point will return trace.startsolid qtrue
 #if 0
 			if (AAS_PointAreaNum(start))
@@ -439,7 +440,7 @@
 	//VectorSubtract(absmaxs, bbmins, absmaxs);
 	//link an invalid (-1) entity
 	areas = AAS_LinkEntityClientBBox(absmins, absmaxs, -1, PRESENCE_CROUCH);
-	//get the reachable link area
+	//get the reachable link arae
 	areanum = AAS_BestReachableLinkArea(areas);
 	//unlink the invalid entity
 	AAS_UnlinkFromAreas(areas);
@@ -490,7 +491,7 @@
 
 	if (!nextreachability) return NULL;
 	//make sure the error message only shows up once
-	if (!nextreachability->next) AAS_Error("AAS_MAX_REACHABILITYSIZE\n");
+	if (!nextreachability->next) AAS_Error("AAS_MAX_REACHABILITYSIZE");
 	//
 	r = nextreachability;
 	nextreachability = nextreachability->next;
@@ -523,7 +524,7 @@
 {
 	if (areanum < 0 || areanum >= aasworld.numareas)
 	{
-		AAS_Error("AAS_AreaReachability: areanum %d out of range\n", areanum);
+		AAS_Error("AAS_AreaReachability: areanum %d out of range", areanum);
 		return 0;
 	} //end if
 	return aasworld.areasettings[areanum].numreachableareas;
@@ -836,6 +837,7 @@
 {
 	int i, j, face1num, face2num, side1;
 	aas_area_t *area1, *area2;
+	aas_areasettings_t *areasettings;
 	aas_lreachability_t *lreach;
 	aas_face_t *face1;
 	aas_plane_t *plane;
@@ -848,7 +850,7 @@
 	area1 = &aasworld.areas[area1num];
 	area2 = &aasworld.areas[area2num];
 
-	//if the areas are not near enough
+	//if the areas are not near anough
 	for (i = 0; i < 3; i++)
 	{
 		if (area1->mins[i] > area2->maxs[i] + 10) return qfalse;
@@ -873,6 +875,7 @@
 				{
 					//
 					face1 = &aasworld.faces[face1num];
+					areasettings = &aasworld.areasettings[area1num];
 					//create a new reachability link
 					lreach = AAS_AllocReachability();
 					if (!lreach) return qfalse;
@@ -923,7 +926,7 @@
 
 	area1 = &aasworld.areas[area1num];
 	area2 = &aasworld.areas[area2num];
-	//if the areas are not near enough in the x-y direction
+	//if the areas are not near anough in the x-y direction
 	for (i = 0; i < 2; i++)
 	{
 		if (area1->mins[i] > area2->maxs[i] + 10) return qfalse;
@@ -1059,19 +1062,18 @@
 	int ground_bestarea2groundedgenum, ground_foundreach;
 	int water_bestarea2groundedgenum, water_foundreach;
 	int side1, area1swim, faceside1, groundface1num;
-	float dist, dist1, dist2, diff, ortdot;
-	//float invgravitydot;
+	float dist, dist1, dist2, diff, invgravitydot, ortdot;
 	float x1, x2, x3, x4, y1, y2, y3, y4, tmp, y;
 	float length, ground_bestlength, water_bestlength, ground_bestdist, water_bestdist;
 	vec3_t v1, v2, v3, v4, tmpv, p1area1, p1area2, p2area1, p2area2;
 	vec3_t normal, ort, edgevec, start, end, dir;
-	vec3_t ground_beststart = {0, 0, 0}, ground_bestend = {0, 0, 0}, ground_bestnormal = {0, 0, 0};
-	vec3_t water_beststart = {0, 0, 0}, water_bestend = {0, 0, 0}, water_bestnormal = {0, 0, 0};
+	vec3_t ground_beststart, ground_bestend, ground_bestnormal;
+	vec3_t water_beststart, water_bestend, water_bestnormal;
 	vec3_t invgravity = {0, 0, 1};
 	vec3_t testpoint;
 	aas_plane_t *plane;
 	aas_area_t *area1, *area2;
-	aas_face_t *groundface1, *groundface2;
+	aas_face_t *groundface1, *groundface2, *ground_bestface1, *water_bestface1;
 	aas_edge_t *edge1, *edge2;
 	aas_lreachability_t *lreach;
 	aas_trace_t trace;
@@ -1085,7 +1087,7 @@
 	area2 = &aasworld.areas[area2num];
 	//if the first area contains a liquid
 	area1swim = AAS_AreaSwim(area1num);
-	//if the areas are not near enough in the x-y direction
+	//if the areas are not near anough in the x-y direction
 	for (i = 0; i < 2; i++)
 	{
 		if (area1->mins[i] > area2->maxs[i] + 10) return qfalse;
@@ -1170,7 +1172,7 @@
 					//edges if they overlap in the direction orthogonal to
 					//the gravity direction
 					CrossProduct(invgravity, normal, ort);
-					//invgravitydot = DotProduct(invgravity, invgravity);
+					invgravitydot = DotProduct(invgravity, invgravity);
 					ortdot = DotProduct(ort, ort);
 					//projection into the step plane
 					//NOTE: since gravity is vertical this is just the z coordinate
@@ -1300,6 +1302,7 @@
 							ground_bestlength = length;
 							ground_foundreach = qtrue;
 							ground_bestarea2groundedgenum = edge1num;
+							ground_bestface1 = groundface1;
 							//best point towards area1
 							VectorCopy(start, ground_beststart);
 							//normal is pointing into area2
@@ -1320,6 +1323,7 @@
 							water_bestlength = length;
 							water_foundreach = qtrue;
 							water_bestarea2groundedgenum = edge1num;
+							water_bestface1 = groundface1;
 							//best point towards area1
 							VectorCopy(start, water_beststart);
 							//normal is pointing into area2
@@ -1416,7 +1420,7 @@
 		//if there IS water the sv_maxwaterjump height below the bestend point
 		if (aasworld.areasettings[AAS_PointAreaNum(testpoint)].areaflags & AREA_LIQUID)
 		{
-			//don't create ridiculous water jump reachabilities from areas very far below
+			//don't create rediculous water jump reachabilities from areas very far below
 			//the water surface
 			if (water_bestdist < aassettings.phys_maxwaterjump + 24)
 			{
@@ -1552,7 +1556,7 @@
 					if (AAS_PointAreaNum(trace.endpos) == area2num)
 					{
 						//if not going through a cluster portal
-						numareas = AAS_TraceAreas(start, end, areas, NULL, ARRAY_LEN(areas));
+						numareas = AAS_TraceAreas(start, end, areas, NULL, sizeof(areas) / sizeof(int));
 						for (i = 0; i < numareas; i++)
 							if (AAS_AreaClusterPortal(areas[i]))
 								break;
@@ -2108,7 +2112,7 @@
 	int stopevent, areas[10], numareas;
 	float phys_jumpvel, maxjumpdistance, maxjumpheight, height, bestdist, speed;
 	vec_t *v1, *v2, *v3, *v4;
-	vec3_t beststart = {0}, beststart2 = {0}, bestend = {0}, bestend2 = {0};
+	vec3_t beststart, beststart2, bestend, bestend2;
 	vec3_t teststart, testend, dir, velocity, cmdmove, up = {0, 0, 1}, sidewards;
 	aas_area_t *area1, *area2;
 	aas_face_t *face1, *face2;
@@ -2131,7 +2135,7 @@
 	//maximum height a player can jump with the given initial z velocity
 	maxjumpheight = AAS_MaxJumpHeight(phys_jumpvel);
 
-	//if the areas are not near enough in the x-y direction
+	//if the areas are not near anough in the x-y direction
 	for (i = 0; i < 2; i++)
 	{
 		if (area1->mins[i] > area2->maxs[i] + maxjumpdistance) return qfalse;
@@ -2307,7 +2311,7 @@
 			//because the predicted jump could have rushed through the area
 			VectorMA(move.endpos, -64, dir, teststart);
 			teststart[2] += 1;
-			numareas = AAS_TraceAreas(move.endpos, teststart, areas, NULL, ARRAY_LEN(areas));
+			numareas = AAS_TraceAreas(move.endpos, teststart, areas, NULL, sizeof(areas) / sizeof(int));
 			for (j = 0; j < numareas; j++)
 			{
 				if (areas[j] == area2num)
@@ -2375,15 +2379,15 @@
 //===========================================================================
 int AAS_Reachability_Ladder(int area1num, int area2num)
 {
-	int i, j, k, l, edge1num, edge2num, sharededgenum = 0, lowestedgenum = 0;
-	int face1num, face2num, ladderface1num = 0, ladderface2num = 0;
+	int i, j, k, l, edge1num, edge2num, sharededgenum, lowestedgenum;
+	int face1num, face2num, ladderface1num, ladderface2num;
 	int ladderface1vertical, ladderface2vertical, firstv;
-	float face1area, face2area, bestface1area = -9999, bestface2area = -9999;
+	float face1area, face2area, bestface1area, bestface2area;
 	float phys_jumpvel, maxjumpheight;
 	vec3_t area1point, area2point, v1, v2, up = {0, 0, 1};
-	vec3_t mid, lowestpoint = {0, 0}, start, end, sharededgevec, dir;
+	vec3_t mid, lowestpoint, start, end, sharededgevec, dir;
 	aas_area_t *area1, *area2;
-	aas_face_t *face1, *face2, *ladderface1 = NULL, *ladderface2 = NULL;
+	aas_face_t *face1, *face2, *ladderface1, *ladderface2;
 	aas_plane_t *plane1, *plane2;
 	aas_edge_t *sharededge, *edge1;
 	aas_lreachability_t *lreach;
@@ -2397,7 +2401,16 @@
 
 	area1 = &aasworld.areas[area1num];
 	area2 = &aasworld.areas[area2num];
-	
+	//
+	ladderface1 = NULL;
+	ladderface2 = NULL;
+	ladderface1num = 0; //make compiler happy
+	ladderface2num = 0; //make compiler happy
+	bestface1area = -9999;
+	bestface2area = -9999;
+	sharededgenum = 0; //make compiler happy
+	lowestedgenum = 0; //make compiler happy
+	//
 	for (i = 0; i < area1->numfaces; i++)
 	{
 		face1num = aasworld.faceindex[area1->firstface + i];
@@ -2465,8 +2478,8 @@
 		VectorMA(area1point, -32, dir, area1point);
 		VectorMA(area2point, 32, dir, area2point);
 		//
-		ladderface1vertical = fabsf(DotProduct(plane1->normal, up)) < 0.1;
-		ladderface2vertical = fabsf(DotProduct(plane2->normal, up)) < 0.1;
+		ladderface1vertical = abs(DotProduct(plane1->normal, up)) < 0.1;
+		ladderface2vertical = abs(DotProduct(plane2->normal, up)) < 0.1;
 		//there's only reachability between vertical ladder faces
 		if (!ladderface1vertical && !ladderface2vertical) return qfalse;
 		//if both vertical ladder faces
@@ -2474,7 +2487,7 @@
 					//and the ladder faces do not make a sharp corner
 					&& DotProduct(plane1->normal, plane2->normal) > 0.7
 					//and the shared edge is not too vertical
-					&& fabsf(DotProduct(sharededgevec, up)) < 0.7)
+					&& abs(DotProduct(sharededgevec, up)) < 0.7)
 		{
 			//create a new reachability link
 			lreach = AAS_AllocReachability();
@@ -2599,7 +2612,7 @@
 				if (face2->faceflags & FACE_LADDER)
 				{
 					plane2 = &aasworld.planes[face2->planenum];
-					if (fabsf(DotProduct(plane2->normal, up)) < 0.1) break;
+					if (abs(DotProduct(plane2->normal, up)) < 0.1) break;
 				} //end if
 			} //end for
 			//if from another area without vertical ladder faces
@@ -2848,9 +2861,9 @@
 				botimport.Print(PRT_ERROR, "teleporter destination (%s) in solid\n", target);
 				continue;
 			} //end if
-			/*
 			area2num = AAS_PointAreaNum(trace.endpos);
 			//
+			/*
 			if (!AAS_AreaTeleporter(area2num) &&
 				!AAS_AreaJumpPad(area2num) &&
 				!AAS_AreaGrounded(area2num))
@@ -3054,7 +3067,7 @@
 					bottomorg[2] += 24;
 				} //end else
 				//look at adjacent areas around the top of the plat
-				//make larger steps to outside the plat every time
+				//make larger steps to outside the plat everytime
 				for (n = 0; n < 3; n++)
 				{
 					for (k = 0; k < 3; k++)
@@ -3152,7 +3165,7 @@
 	int facenum, edgenum, bestfacenum;
 	float *v1, *v2, *v3, *v4;
 	float bestdist, speed, hordist, dist;
-	vec3_t beststart = {0}, beststart2 = {0}, bestend = {0}, bestend2 = {0}, tmp, hordir, testpoint;
+	vec3_t beststart, beststart2, bestend, bestend2, tmp, hordir, testpoint;
 	aas_lreachability_t *lreach, *lreachabilities;
 	aas_area_t *area;
 	aas_face_t *face;
@@ -3237,10 +3250,8 @@
 		//
 		if (towardsface) VectorCopy(bestend, testpoint);
 		else VectorCopy(beststart, testpoint);
-		if (bestfaceplane != NULL)
-			testpoint[2] = (bestfaceplane->dist - DotProduct(bestfaceplane->normal, testpoint)) / bestfaceplane->normal[2];
-		else
-			testpoint[2] = 0;
+		testpoint[2] = 0;
+		testpoint[2] = (bestfaceplane->dist - DotProduct(bestfaceplane->normal, testpoint)) / bestfaceplane->normal[2];
 		//
 		if (!AAS_PointInsideFace(bestfacenum, testpoint, 0.1f))
 		{
@@ -3394,6 +3405,7 @@
 		//
 		for (i = 0; i < 2; i++)
 		{
+			firststartreach = firstendreach = NULL;
 			//
 			if (i == 0)
 			{
@@ -3489,8 +3501,7 @@
 	int face2num, i, ret, area2num, visualize, ent, bot_visualizejumppads;
 	//int modelnum, ent2;
 	//float dist, time, height, gravity, forward;
-	float speed, zvel;
-	//float hordist;
+	float speed, zvel, hordist;
 	aas_face_t *face2;
 	aas_area_t *area2;
 	aas_lreachability_t *lreach;
@@ -3712,11 +3723,7 @@
 					//direction towards the face center
 					VectorSubtract(facecenter, areastart, dir);
 					dir[2] = 0;
-
-					// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
-					//hordist = VectorNormalize(dir);
-					VectorNormalize(dir);
+					hordist = VectorNormalize(dir);
 					//if (hordist < 1.6 * facecenter[2] - areastart[2])
 					{
 						//get command movement
@@ -3792,7 +3799,7 @@
 	aas_face_t *face2;
 	aas_area_t *area1, *area2;
 	aas_lreachability_t *lreach;
-	vec3_t areastart = {0, 0, 0}, facecenter, start, end, dir, down = {0, 0, -1};
+	vec3_t areastart, facecenter, start, end, dir, down = {0, 0, -1};
 	vec_t *v;
 
 	//only grapple when on the ground or swimming
@@ -3999,8 +4006,7 @@
 int AAS_Reachability_WeaponJump(int area1num, int area2num)
 {
 	int face2num, i, n, ret, visualize;
-	float speed, zvel;
-	//float hordist;
+	float speed, zvel, hordist;
 	aas_face_t *face2;
 	aas_area_t *area1, *area2;
 	aas_lreachability_t *lreach;
@@ -4060,11 +4066,7 @@
 				//direction towards the face center
 				VectorSubtract(facecenter, areastart, dir);
 				dir[2] = 0;
-
-				// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
-				//hordist = VectorNormalize(dir);
-				VectorNormalize(dir);
+				hordist = VectorNormalize(dir);
 				//if (hordist < 1.6 * (facecenter[2] - areastart[2]))
 				{
 					//get command movement
@@ -4261,7 +4263,7 @@
 							break;
 						} //end if
 						//if not going through a cluster portal
-						numareas = AAS_TraceAreas(mid, testend, areas, NULL, ARRAY_LEN(areas));
+						numareas = AAS_TraceAreas(mid, testend, areas, NULL, sizeof(areas) / sizeof(int));
 						for (p = 0; p < numareas; p++)
 							if (AAS_AreaClusterPortal(areas[p]))
 								break;

```

### `ioquake3`  — sha256 `5279e44e7f46...`, 157123 bytes

_Diff stat: +0 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_reach.c	2026-04-16 20:02:25.118908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\botlib\be_aas_reach.c	2026-04-16 20:02:21.504900800 +0100
@@ -3712,11 +3712,7 @@
 					//direction towards the face center
 					VectorSubtract(facecenter, areastart, dir);
 					dir[2] = 0;
-
-					// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
 					//hordist = VectorNormalize(dir);
-					VectorNormalize(dir);
 					//if (hordist < 1.6 * facecenter[2] - areastart[2])
 					{
 						//get command movement
@@ -4060,11 +4056,7 @@
 				//direction towards the face center
 				VectorSubtract(facecenter, areastart, dir);
 				dir[2] = 0;
-
-				// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
 				//hordist = VectorNormalize(dir);
-				VectorNormalize(dir);
 				//if (hordist < 1.6 * (facecenter[2] - areastart[2]))
 				{
 					//get command movement

```

### `quake3e`  — sha256 `5caf3ac073c6...`, 157854 bytes

_Diff stat: +85 / -80 lines_

_(full diff is 21302 bytes — see files directly)_

### `openarena-engine`  — sha256 `1b4618316305...`, 157241 bytes

_Diff stat: +13 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_reach.c	2026-04-16 20:02:25.118908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_reach.c	2026-04-16 22:48:25.710436800 +0100
@@ -439,7 +439,7 @@
 	//VectorSubtract(absmaxs, bbmins, absmaxs);
 	//link an invalid (-1) entity
 	areas = AAS_LinkEntityClientBBox(absmins, absmaxs, -1, PRESENCE_CROUCH);
-	//get the reachable link area
+	//get the reachable link arae
 	areanum = AAS_BestReachableLinkArea(areas);
 	//unlink the invalid entity
 	AAS_UnlinkFromAreas(areas);
@@ -1416,7 +1416,7 @@
 		//if there IS water the sv_maxwaterjump height below the bestend point
 		if (aasworld.areasettings[AAS_PointAreaNum(testpoint)].areaflags & AREA_LIQUID)
 		{
-			//don't create ridiculous water jump reachabilities from areas very far below
+			//don't create rediculous water jump reachabilities from areas very far below
 			//the water surface
 			if (water_bestdist < aassettings.phys_maxwaterjump + 24)
 			{
@@ -2108,7 +2108,7 @@
 	int stopevent, areas[10], numareas;
 	float phys_jumpvel, maxjumpdistance, maxjumpheight, height, bestdist, speed;
 	vec_t *v1, *v2, *v3, *v4;
-	vec3_t beststart = {0}, beststart2 = {0}, bestend = {0}, bestend2 = {0};
+	vec3_t beststart, beststart2, bestend, bestend2;
 	vec3_t teststart, testend, dir, velocity, cmdmove, up = {0, 0, 1}, sidewards;
 	aas_area_t *area1, *area2;
 	aas_face_t *face1, *face2;
@@ -2141,6 +2141,8 @@
 	if (area2->mins[2] > area1->maxs[2] + maxjumpheight) return qfalse;
 	//
 	bestdist = 999999;
+	memset(&beststart2, 0, sizeof(beststart2));
+	memset(&bestend2,0,sizeof(bestend2));
 	//
 	for (i = 0; i < area1->numfaces; i++)
 	{
@@ -2465,8 +2467,8 @@
 		VectorMA(area1point, -32, dir, area1point);
 		VectorMA(area2point, 32, dir, area2point);
 		//
-		ladderface1vertical = fabsf(DotProduct(plane1->normal, up)) < 0.1;
-		ladderface2vertical = fabsf(DotProduct(plane2->normal, up)) < 0.1;
+		ladderface1vertical = abs(DotProduct(plane1->normal, up)) < 0.1;
+		ladderface2vertical = abs(DotProduct(plane2->normal, up)) < 0.1;
 		//there's only reachability between vertical ladder faces
 		if (!ladderface1vertical && !ladderface2vertical) return qfalse;
 		//if both vertical ladder faces
@@ -2474,7 +2476,7 @@
 					//and the ladder faces do not make a sharp corner
 					&& DotProduct(plane1->normal, plane2->normal) > 0.7
 					//and the shared edge is not too vertical
-					&& fabsf(DotProduct(sharededgevec, up)) < 0.7)
+					&& abs(DotProduct(sharededgevec, up)) < 0.7)
 		{
 			//create a new reachability link
 			lreach = AAS_AllocReachability();
@@ -2599,7 +2601,7 @@
 				if (face2->faceflags & FACE_LADDER)
 				{
 					plane2 = &aasworld.planes[face2->planenum];
-					if (fabsf(DotProduct(plane2->normal, up)) < 0.1) break;
+					if (abs(DotProduct(plane2->normal, up)) < 0.1) break;
 				} //end if
 			} //end for
 			//if from another area without vertical ladder faces
@@ -3054,7 +3056,7 @@
 					bottomorg[2] += 24;
 				} //end else
 				//look at adjacent areas around the top of the plat
-				//make larger steps to outside the plat every time
+				//make larger steps to outside the plat everytime
 				for (n = 0; n < 3; n++)
 				{
 					for (k = 0; k < 3; k++)
@@ -3152,7 +3154,7 @@
 	int facenum, edgenum, bestfacenum;
 	float *v1, *v2, *v3, *v4;
 	float bestdist, speed, hordist, dist;
-	vec3_t beststart = {0}, beststart2 = {0}, bestend = {0}, bestend2 = {0}, tmp, hordir, testpoint;
+	vec3_t beststart, beststart2, bestend, bestend2, tmp, hordir, testpoint;
 	aas_lreachability_t *lreach, *lreachabilities;
 	aas_area_t *area;
 	aas_face_t *face;
@@ -3163,6 +3165,8 @@
 	lreachabilities = NULL;
 	bestfacenum = 0;
 	bestfaceplane = NULL;
+	memset(&beststart2, 0, sizeof(beststart2));
+	memset(&bestend2, 0 , sizeof(bestend2));
 	//
 	for (i = 1; i < aasworld.numareas; i++)
 	{
@@ -3712,11 +3716,7 @@
 					//direction towards the face center
 					VectorSubtract(facecenter, areastart, dir);
 					dir[2] = 0;
-
-					// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
 					//hordist = VectorNormalize(dir);
-					VectorNormalize(dir);
 					//if (hordist < 1.6 * facecenter[2] - areastart[2])
 					{
 						//get command movement
@@ -4060,11 +4060,7 @@
 				//direction towards the face center
 				VectorSubtract(facecenter, areastart, dir);
 				dir[2] = 0;
-
-				// 2017-07-09 below line 'hordist = VectorNormalize(dir)' removed in ioquake3 patch 2104.  Appears to be removed because of hordist not being used, but that will forget to normalize the vector
-
 				//hordist = VectorNormalize(dir);
-				VectorNormalize(dir);
 				//if (hordist < 1.6 * (facecenter[2] - areastart[2]))
 				{
 					//get command movement

```
