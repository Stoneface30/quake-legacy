# Diff: `code/qcommon/cm_trace.c`
**Canonical:** `wolfcamql-src` (sha256 `a4a9cb2b3662...`, 41355 bytes)

## Variants

### `quake3-source`  — sha256 `7d7d1bf3c1f4...`, 39998 bytes

_Diff stat: +51 / -71 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_trace.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_trace.c	2026-04-16 20:02:19.958608400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -41,7 +41,7 @@
 RotatePoint
 ================
 */
-void RotatePoint(vec3_t point, /*const*/ vec3_t matrix[3]) { // FIXME 
+void RotatePoint(vec3_t point, /*const*/ vec3_t matrix[3]) { // bk: FIXME 
 	vec3_t tvec;
 
 	VectorCopy(point, tvec);
@@ -55,7 +55,7 @@
 TransposeMatrix
 ================
 */
-void TransposeMatrix(/*const*/ vec3_t matrix[3], vec3_t transpose[3]) { // FIXME
+void TransposeMatrix(/*const*/ vec3_t matrix[3], vec3_t transpose[3]) { // bk: FIXME
 	int i, j;
 	for (i = 0; i < 3; i++) {
 		for (j = 0; j < 3; j++) {
@@ -76,6 +76,20 @@
 
 /*
 ================
+CM_ProjectPointOntoVector
+================
+*/
+void CM_ProjectPointOntoVector( vec3_t point, vec3_t vStart, vec3_t vDir, vec3_t vProj )
+{
+	vec3_t pVec;
+
+	VectorSubtract( point, vStart, pVec );
+	// project onto the directional vector for this segment
+	VectorMA( vStart, DotProduct( pVec, vDir ), vDir, vProj );
+}
+
+/*
+================
 CM_DistanceFromLineSquared
 ================
 */
@@ -83,8 +97,8 @@
 	vec3_t proj, t;
 	int j;
 
-	ProjectPointOntoVector(p, lp1, dir, proj);
-	for (j = 0; j < 3; j++)
+	CM_ProjectPointOntoVector(p, lp1, dir, proj);
+	for (j = 0; j < 3; j++) 
 		if ((proj[j] > lp1[j] && proj[j] > lp2[j]) ||
 			(proj[j] < lp1[j] && proj[j] < lp2[j]))
 			break;
@@ -117,14 +131,15 @@
 ================
 */
 float SquareRootFloat(float number) {
-	floatint_t t;
+	long i;
 	float x, y;
 	const float f = 1.5F;
 
 	x = number * 0.5F;
-	t.f  = number;
-	t.i  = 0x5f3759df - ( t.i >> 1 );
-	y  = t.f;
+	y  = number;
+	i  = * ( long * ) &y;
+	i  = 0x5f3759df - ( i >> 1 );
+	y  = * ( float * ) &i;
 	y  = y * ( f - ( x * y * y ) );
 	y  = y * ( f - ( x * y * y ) );
 	return number * y;
@@ -175,7 +190,7 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			dist = plane->dist + tw->sphere.radius;
 			// find the closest point on the capsule to the plane
 			t = DotProduct( plane->normal, tw->sphere.offset );
@@ -190,7 +205,6 @@
 			d1 = DotProduct( startp, plane->normal ) - dist;
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s in front\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -201,14 +215,13 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for mins/maxs
+			// adjust the plane distance apropriately for mins/maxs
 			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
 
 			d1 = DotProduct( tw->start, plane->normal ) - dist;
 
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s siz  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 				return;
 			}
 		}
@@ -218,7 +231,6 @@
 	tw->trace.startsolid = tw->trace.allsolid = qtrue;
 	tw->trace.fraction = 0;
 	tw->trace.contents = brush->contents;
-	//Com_Printf("%s inside brush\n", __FUNCTION__);
 }
 
 
@@ -249,7 +261,6 @@
 		
 		CM_TestBoxInBrush( tw, b );
 		if ( tw->trace.allsolid ) {
-			//Com_Printf("%s all solid\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -278,7 +289,6 @@
 				tw->trace.startsolid = tw->trace.allsolid = qtrue;
 				tw->trace.fraction = 0;
 				tw->trace.contents = patch->contents;
-				//Com_Printf("%s patch collide\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -462,9 +472,6 @@
 	if ( tw->trace.fraction < oldFrac ) {
 		tw->trace.surfaceFlags = patch->surfaceFlags;
 		tw->trace.contents = patch->contents;
-		//tw->trace.shaderNum = patch->shaderNum;
-		//Com_Printf("%s patch trace %d  %s\n", __FUNCTION__, patch->shaderNum, cm.shaders[patch->shaderNum].shader);
-		//Com_Printf("patch trace %d\n", patch->shaderNum);
 	}
 }
 
@@ -501,20 +508,17 @@
 
 	leadside = NULL;
 
-	//Com_Printf("brush %s\n", cm.shaders[brush->shaderNum].shader);
-
 	if ( tw->sphere.use ) {
 		//
 		// compare the trace against all planes of the brush
 		// find the latest time the trace crosses a plane towards the interior
 		// and the earliest time the trace crosses a plane towards the exterior
 		//
-		//Com_Printf("%s sphere\n", __FUNCTION__);
 		for (i = 0; i < brush->numsides; i++) {
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			dist = plane->dist + tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -542,11 +546,10 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s completely in front\n", __FUNCTION__);
 				return;
 			}
 
-			// if it doesn't cross the plane, the plane isn't relevant
+			// if it doesn't cross the plane, the plane isn't relevent
 			if (d1 <= 0 && d2 <= 0 ) {
 				continue;
 			}
@@ -582,7 +585,7 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for mins/maxs
+			// adjust the plane distance apropriately for mins/maxs
 			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
 
 			d1 = DotProduct( tw->start, plane->normal ) - dist;
@@ -597,14 +600,10 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s no spehere completely in front  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
-				//if (brush->shaderNum) {  //(tw->trace.shaderNum == 0) {
-				//	tw->trace.shaderNum = brush->shaderNum;
-				//}
 				return;
 			}
 
-			// if it doesn't cross the plane, the plane isn't relevant
+			// if it doesn't cross the plane, the plane isn't relevent
 			if (d1 <= 0 && d2 <= 0 ) {
 				continue;
 			}
@@ -643,7 +642,6 @@
 			tw->trace.fraction = 0;
 			tw->trace.contents = brush->contents;
 		}
-		//Com_Printf("%s done\n", __FUNCTION__);
 		return;
 	}
 	
@@ -653,20 +651,9 @@
 				enterFrac = 0;
 			}
 			tw->trace.fraction = enterFrac;
-			if (clipplane != NULL) {
-				tw->trace.plane = *clipplane;
-			}
-			if (leadside != NULL) {
-				tw->trace.surfaceFlags = leadside->surfaceFlags;
-			}
+			tw->trace.plane = *clipplane;
+			tw->trace.surfaceFlags = leadside->surfaceFlags;
 			tw->trace.contents = brush->contents;
-			//if (tw->trace.shaderNum == 0) {
-			//	tw->trace.shaderNum = brush->shaderNum;
-			//}
-			//Com_Printf("%d\n", 
-			//Com_Printf("yes\n");
-			//Com_Printf("%d %s\n", brush->shaderNum, "");
-			//Com_Printf("%s %d %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 		}
 	}
 }
@@ -696,14 +683,8 @@
 			continue;
 		}
 
-		if ( !CM_BoundsIntersect( tw->bounds[0], tw->bounds[1],
-					b->bounds[0], b->bounds[1] ) ) {
-			continue;
-		}
-
 		CM_TraceThroughBrush( tw, b );
 		if ( !tw->trace.fraction ) {
-			//Com_Printf("%s no trace fraction\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -730,7 +711,6 @@
 			
 			CM_TraceThroughPatch( tw, patch );
 			if ( !tw->trace.fraction ) {
-				//Com_Printf("%s 2 no trace fraction\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -748,8 +728,7 @@
 */
 void CM_TraceThroughSphere( traceWork_t *tw, vec3_t origin, float radius, vec3_t start, vec3_t end ) {
 	float l1, l2, length, scale, fraction;
-	//float a;
-	float b, c, d, sqrtd;
+	float a, b, c, d, sqrtd;
 	vec3_t v1, dir, intersection;
 
 	// if inside the sphere
@@ -764,7 +743,6 @@
 		if (l1 < Square(radius)) {
 			tw->trace.allsolid = qtrue;
 		}
-		//Com_Printf("%s radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -776,7 +754,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the sphere and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square dist\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -787,7 +764,7 @@
 	//
 	VectorSubtract(start, origin, v1);
 	// dir is normalized so a = 1
-	//a = 1.0f;//dir[0] * dir[0] + dir[1] * dir[1] + dir[2] * dir[2];
+	a = 1.0f;//dir[0] * dir[0] + dir[1] * dir[1] + dir[2] * dir[2];
 	b = 2.0f * (dir[0] * v1[0] + dir[1] * v1[1] + dir[2] * v1[2]);
 	c = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2] - (radius+RADIUS_EPSILON) * (radius+RADIUS_EPSILON);
 
@@ -820,7 +797,6 @@
 			VectorAdd( tw->modelOrigin, intersection, intersection);
 			tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 			tw->trace.contents = CONTENTS_BODY;
-			//Com_Printf("%s fraction less\n", __FUNCTION__);
 		}
 	}
 	else if (d == 0) {
@@ -840,8 +816,7 @@
 */
 void CM_TraceThroughVerticalCylinder( traceWork_t *tw, vec3_t origin, float radius, float halfheight, vec3_t start, vec3_t end) {
 	float length, scale, fraction, l1, l2;
-	//float a;
-	float b, c, d, sqrtd;
+	float a, b, c, d, sqrtd;
 	vec3_t v1, dir, start2d, end2d, org2d, intersection;
 
 	// 2d coordinates
@@ -862,7 +837,6 @@
 			if (l1 < Square(radius)) {
 				tw->trace.allsolid = qtrue;
 			}
-			//Com_Printf("%s radius\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -875,7 +849,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the cylinder and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -889,7 +862,7 @@
 	//
 	VectorSubtract(start, origin, v1);
 	// dir is normalized so we can use a = 1
-	//a = 1.0f;// * (dir[0] * dir[0] + dir[1] * dir[1]);
+	a = 1.0f;// * (dir[0] * dir[0] + dir[1] * dir[1]);
 	b = 2.0f * (v1[0] * dir[0] + v1[1] * dir[1]);
 	c = v1[0] * v1[0] + v1[1] * v1[1] - (radius+RADIUS_EPSILON) * (radius+RADIUS_EPSILON);
 
@@ -927,7 +900,6 @@
 				VectorAdd( tw->modelOrigin, intersection, intersection);
 				tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 				tw->trace.contents = CONTENTS_BODY;
-				//Com_Printf("%s set\n", __FUNCTION__);
 			}
 		}
 	}
@@ -961,7 +933,6 @@
 		|| tw->bounds[1][1] < mins[1] - RADIUS_EPSILON
 		|| tw->bounds[1][2] < mins[2] - RADIUS_EPSILON
 		) {
-		//Com_Printf("%s bounds\n", __FUNCTION__);
 		return;
 	}
 	// top origin and bottom origin of each sphere at start and end of trace
@@ -1062,7 +1033,6 @@
 	float		midf;
 
 	if (tw->trace.fraction <= p1f) {
-		//Com_Printf("%s already hit something\n", __FUNCTION__);
 		return;		// already hit something nearer
 	}
 
@@ -1073,13 +1043,13 @@
 	}
 
 	//
-	// find the point distances to the separating plane
+	// find the point distances to the seperating plane
 	// and the offset for the size of the box
 	//
 	node = cm.nodes + num;
 	plane = node->plane;
 
-	// adjust the plane distance appropriately for mins/maxs
+	// adjust the plane distance apropriately for mins/maxs
 	if ( plane->type < 3 ) {
 		t1 = p1[plane->type] - plane->dist;
 		t2 = p2[plane->type] - plane->dist;
@@ -1090,6 +1060,17 @@
 		if ( tw->isPoint ) {
 			offset = 0;
 		} else {
+#if 0 // bk010201 - DEAD
+			// an axial brush right behind a slanted bsp plane
+			// will poke through when expanded, so adjust
+			// by sqrt(3)
+			offset = fabs(tw->extents[0]*plane->normal[0]) +
+				fabs(tw->extents[1]*plane->normal[1]) +
+				fabs(tw->extents[2]*plane->normal[2]);
+
+			offset *= 2;
+			offset = tw->maxOffset;
+#endif
 			// this is silly
 			offset = 2048;
 		}
@@ -1172,7 +1153,6 @@
 	vec3_t		offset;
 	cmodel_t	*cmod;
 
-	//Com_Printf("^3CM_Trace()\n");
 	cmod = CM_ClipHandleToModel( model );
 
 	cm.checkcount++;		// for multi-check avoidance
@@ -1225,7 +1205,7 @@
 
 	tw.maxOffset = tw.size[1][0] + tw.size[1][1] + tw.size[1][2];
 
-	// tw.offsets[signbits] = vector to appropriate corner from origin
+	// tw.offsets[signbits] = vector to apropriate corner from origin
 	tw.offsets[0][0] = tw.size[0][0];
 	tw.offsets[0][1] = tw.size[0][1];
 	tw.offsets[0][2] = tw.size[0][2];
@@ -1289,7 +1269,7 @@
 	//
 	if (start[0] == end[0] && start[1] == end[1] && start[2] == end[2]) {
 		if ( model ) {
-#ifdef ALWAYS_BBOX_VS_BBOX // FIXME - compile time flag?
+#ifdef ALWAYS_BBOX_VS_BBOX // bk010201 - FIXME - compile time flag?
 			if ( model == BOX_MODEL_HANDLE || model == CAPSULE_MODEL_HANDLE) {
 				tw.sphere.use = qfalse;
 				CM_TestInLeaf( &tw, &cmod->leaf );

```

### `ioquake3`  — sha256 `108a15644b5c...`, 39849 bytes

_Diff stat: +16 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_trace.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\cm_trace.c	2026-04-16 20:02:21.565104700 +0100
@@ -76,6 +76,20 @@
 
 /*
 ================
+CM_ProjectPointOntoVector
+================
+*/
+void CM_ProjectPointOntoVector( vec3_t point, vec3_t vStart, vec3_t vDir, vec3_t vProj )
+{
+	vec3_t pVec;
+
+	VectorSubtract( point, vStart, pVec );
+	// project onto the directional vector for this segment
+	VectorMA( vStart, DotProduct( pVec, vDir ), vDir, vProj );
+}
+
+/*
+================
 CM_DistanceFromLineSquared
 ================
 */
@@ -83,8 +97,8 @@
 	vec3_t proj, t;
 	int j;
 
-	ProjectPointOntoVector(p, lp1, dir, proj);
-	for (j = 0; j < 3; j++)
+	CM_ProjectPointOntoVector(p, lp1, dir, proj);
+	for (j = 0; j < 3; j++) 
 		if ((proj[j] > lp1[j] && proj[j] > lp2[j]) ||
 			(proj[j] < lp1[j] && proj[j] < lp2[j]))
 			break;
@@ -190,7 +204,6 @@
 			d1 = DotProduct( startp, plane->normal ) - dist;
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s in front\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -208,7 +221,6 @@
 
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s siz  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 				return;
 			}
 		}
@@ -218,7 +230,6 @@
 	tw->trace.startsolid = tw->trace.allsolid = qtrue;
 	tw->trace.fraction = 0;
 	tw->trace.contents = brush->contents;
-	//Com_Printf("%s inside brush\n", __FUNCTION__);
 }
 
 
@@ -249,7 +260,6 @@
 		
 		CM_TestBoxInBrush( tw, b );
 		if ( tw->trace.allsolid ) {
-			//Com_Printf("%s all solid\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -278,7 +288,6 @@
 				tw->trace.startsolid = tw->trace.allsolid = qtrue;
 				tw->trace.fraction = 0;
 				tw->trace.contents = patch->contents;
-				//Com_Printf("%s patch collide\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -462,9 +471,6 @@
 	if ( tw->trace.fraction < oldFrac ) {
 		tw->trace.surfaceFlags = patch->surfaceFlags;
 		tw->trace.contents = patch->contents;
-		//tw->trace.shaderNum = patch->shaderNum;
-		//Com_Printf("%s patch trace %d  %s\n", __FUNCTION__, patch->shaderNum, cm.shaders[patch->shaderNum].shader);
-		//Com_Printf("patch trace %d\n", patch->shaderNum);
 	}
 }
 
@@ -501,15 +507,12 @@
 
 	leadside = NULL;
 
-	//Com_Printf("brush %s\n", cm.shaders[brush->shaderNum].shader);
-
 	if ( tw->sphere.use ) {
 		//
 		// compare the trace against all planes of the brush
 		// find the latest time the trace crosses a plane towards the interior
 		// and the earliest time the trace crosses a plane towards the exterior
 		//
-		//Com_Printf("%s sphere\n", __FUNCTION__);
 		for (i = 0; i < brush->numsides; i++) {
 			side = brush->sides + i;
 			plane = side->plane;
@@ -542,7 +545,6 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s completely in front\n", __FUNCTION__);
 				return;
 			}
 
@@ -597,10 +599,6 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s no spehere completely in front  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
-				//if (brush->shaderNum) {  //(tw->trace.shaderNum == 0) {
-				//	tw->trace.shaderNum = brush->shaderNum;
-				//}
 				return;
 			}
 
@@ -643,7 +641,6 @@
 			tw->trace.fraction = 0;
 			tw->trace.contents = brush->contents;
 		}
-		//Com_Printf("%s done\n", __FUNCTION__);
 		return;
 	}
 	
@@ -660,13 +657,6 @@
 				tw->trace.surfaceFlags = leadside->surfaceFlags;
 			}
 			tw->trace.contents = brush->contents;
-			//if (tw->trace.shaderNum == 0) {
-			//	tw->trace.shaderNum = brush->shaderNum;
-			//}
-			//Com_Printf("%d\n", 
-			//Com_Printf("yes\n");
-			//Com_Printf("%d %s\n", brush->shaderNum, "");
-			//Com_Printf("%s %d %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 		}
 	}
 }
@@ -703,7 +693,6 @@
 
 		CM_TraceThroughBrush( tw, b );
 		if ( !tw->trace.fraction ) {
-			//Com_Printf("%s no trace fraction\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -730,7 +719,6 @@
 			
 			CM_TraceThroughPatch( tw, patch );
 			if ( !tw->trace.fraction ) {
-				//Com_Printf("%s 2 no trace fraction\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -764,7 +752,6 @@
 		if (l1 < Square(radius)) {
 			tw->trace.allsolid = qtrue;
 		}
-		//Com_Printf("%s radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -776,7 +763,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the sphere and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square dist\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -820,7 +806,6 @@
 			VectorAdd( tw->modelOrigin, intersection, intersection);
 			tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 			tw->trace.contents = CONTENTS_BODY;
-			//Com_Printf("%s fraction less\n", __FUNCTION__);
 		}
 	}
 	else if (d == 0) {
@@ -862,7 +847,6 @@
 			if (l1 < Square(radius)) {
 				tw->trace.allsolid = qtrue;
 			}
-			//Com_Printf("%s radius\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -875,7 +859,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the cylinder and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -927,7 +910,6 @@
 				VectorAdd( tw->modelOrigin, intersection, intersection);
 				tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 				tw->trace.contents = CONTENTS_BODY;
-				//Com_Printf("%s set\n", __FUNCTION__);
 			}
 		}
 	}
@@ -961,7 +943,6 @@
 		|| tw->bounds[1][1] < mins[1] - RADIUS_EPSILON
 		|| tw->bounds[1][2] < mins[2] - RADIUS_EPSILON
 		) {
-		//Com_Printf("%s bounds\n", __FUNCTION__);
 		return;
 	}
 	// top origin and bottom origin of each sphere at start and end of trace
@@ -1062,7 +1043,6 @@
 	float		midf;
 
 	if (tw->trace.fraction <= p1f) {
-		//Com_Printf("%s already hit something\n", __FUNCTION__);
 		return;		// already hit something nearer
 	}
 
@@ -1172,7 +1152,6 @@
 	vec3_t		offset;
 	cmodel_t	*cmod;
 
-	//Com_Printf("^3CM_Trace()\n");
 	cmod = CM_ClipHandleToModel( model );
 
 	cm.checkcount++;		// for multi-check avoidance

```

### `quake3e`  — sha256 `f6eab0926b2d...`, 40006 bytes

_Diff stat: +93 / -116 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_trace.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_trace.c	2026-04-16 20:02:27.300418600 +0100
@@ -41,7 +41,7 @@
 RotatePoint
 ================
 */
-void RotatePoint(vec3_t point, /*const*/ vec3_t matrix[3]) { // FIXME 
+static void RotatePoint( vec3_t point, /*const*/ vec3_t matrix[3] ) {
 	vec3_t tvec;
 
 	VectorCopy(point, tvec);
@@ -50,12 +50,13 @@
 	point[2] = DotProduct(matrix[2], tvec);
 }
 
+
 /*
 ================
 TransposeMatrix
 ================
 */
-void TransposeMatrix(/*const*/ vec3_t matrix[3], vec3_t transpose[3]) { // FIXME
+static void TransposeMatrix( /*const*/ vec3_t matrix[3], vec3_t transpose[3] ) {
 	int i, j;
 	for (i = 0; i < 3; i++) {
 		for (j = 0; j < 3; j++) {
@@ -64,26 +65,43 @@
 	}
 }
 
+
 /*
 ================
 CreateRotationMatrix
 ================
 */
-void CreateRotationMatrix(const vec3_t angles, vec3_t matrix[3]) {
+static void CreateRotationMatrix( const vec3_t angles, vec3_t matrix[3] ) {
 	AngleVectors(angles, matrix[0], matrix[1], matrix[2]);
 	VectorInverse(matrix[1]);
 }
 
+
+/*
+================
+CM_ProjectPointOntoVector
+================
+*/
+static void CM_ProjectPointOntoVector( const vec3_t point, const vec3_t vStart, const vec3_t vDir, vec3_t vProj )
+{
+	vec3_t pVec;
+
+	VectorSubtract( point, vStart, pVec );
+	// project onto the directional vector for this segment
+	VectorMA( vStart, DotProduct( pVec, vDir ), vDir, vProj );
+}
+
+
 /*
 ================
 CM_DistanceFromLineSquared
 ================
 */
-float CM_DistanceFromLineSquared(vec3_t p, vec3_t lp1, vec3_t lp2, vec3_t dir) {
+static float CM_DistanceFromLineSquared( const vec3_t p, const vec3_t lp1, const vec3_t lp2, const vec3_t dir ) {
 	vec3_t proj, t;
 	int j;
 
-	ProjectPointOntoVector(p, lp1, dir, proj);
+	CM_ProjectPointOntoVector(p, lp1, dir, proj);
 	for (j = 0; j < 3; j++)
 		if ((proj[j] > lp1[j] && proj[j] > lp2[j]) ||
 			(proj[j] < lp1[j] && proj[j] < lp2[j]))
@@ -99,24 +117,13 @@
 	return VectorLengthSquared(t);
 }
 
-/*
-================
-CM_VectorDistanceSquared
-================
-*/
-float CM_VectorDistanceSquared(vec3_t p1, vec3_t p2) {
-	vec3_t dir;
-
-	VectorSubtract(p2, p1, dir);
-	return VectorLengthSquared(dir);
-}
 
 /*
 ================
 SquareRootFloat
 ================
 */
-float SquareRootFloat(float number) {
+static float SquareRootFloat(float number) {
 	floatint_t t;
 	float x, y;
 	const float f = 1.5F;
@@ -144,13 +151,13 @@
 CM_TestBoxInBrush
 ================
 */
-void CM_TestBoxInBrush( traceWork_t *tw, cbrush_t *brush ) {
+static void CM_TestBoxInBrush( traceWork_t *tw, const cbrush_t *brush ) {
 	int			i;
 	cplane_t	*plane;
-	float		dist;
-	float		d1;
+	double		dist;
+	double		d1;
 	cbrushside_t	*side;
-	float		t;
+	double		t;
 	vec3_t		startp;
 
 	if (!brush->numsides) {
@@ -178,19 +185,18 @@
 			// adjust the plane distance appropriately for radius
 			dist = plane->dist + tw->sphere.radius;
 			// find the closest point on the capsule to the plane
-			t = DotProduct( plane->normal, tw->sphere.offset );
+			t = DotProductDP( plane->normal, tw->sphere.offset );
 			if ( t > 0 )
 			{
-				VectorSubtract( tw->start, tw->sphere.offset, startp );
+				VectorSubtractDP( tw->start, tw->sphere.offset, startp );
 			}
 			else
 			{
-				VectorAdd( tw->start, tw->sphere.offset, startp );
+				VectorAddDP( tw->start, tw->sphere.offset, startp );
 			}
-			d1 = DotProduct( startp, plane->normal ) - dist;
+			d1 = DotProductDP( startp, plane->normal ) - dist;
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s in front\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -204,11 +210,10 @@
 			// adjust the plane distance appropriately for mins/maxs
 			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
 
-			d1 = DotProduct( tw->start, plane->normal ) - dist;
+			d1 = DotProductDP( tw->start, plane->normal ) - dist;
 
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s siz  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 				return;
 			}
 		}
@@ -218,17 +223,15 @@
 	tw->trace.startsolid = tw->trace.allsolid = qtrue;
 	tw->trace.fraction = 0;
 	tw->trace.contents = brush->contents;
-	//Com_Printf("%s inside brush\n", __FUNCTION__);
 }
 
 
-
 /*
 ================
 CM_TestInLeaf
 ================
 */
-void CM_TestInLeaf( traceWork_t *tw, cLeaf_t *leaf ) {
+static void CM_TestInLeaf( traceWork_t *tw, const cLeaf_t *leaf ) {
 	int			k;
 	int			brushnum;
 	cbrush_t	*b;
@@ -246,10 +249,9 @@
 		if ( !(b->contents & tw->contents)) {
 			continue;
 		}
-		
+
 		CM_TestBoxInBrush( tw, b );
 		if ( tw->trace.allsolid ) {
-			//Com_Printf("%s all solid\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -273,18 +275,18 @@
 			if ( !(patch->contents & tw->contents)) {
 				continue;
 			}
-			
+
 			if ( CM_PositionTestInPatchCollide( tw, patch->pc ) ) {
 				tw->trace.startsolid = tw->trace.allsolid = qtrue;
 				tw->trace.fraction = 0;
 				tw->trace.contents = patch->contents;
-				//Com_Printf("%s patch collide\n", __FUNCTION__);
 				return;
 			}
 		}
 	}
 }
 
+
 /*
 ==================
 CM_TestCapsuleInCapsule
@@ -292,7 +294,7 @@
 capsule inside capsule check
 ==================
 */
-void CM_TestCapsuleInCapsule( traceWork_t *tw, clipHandle_t model ) {
+static void CM_TestCapsuleInCapsule( traceWork_t *tw, clipHandle_t model ) {
 	int i;
 	vec3_t mins, maxs;
 	vec3_t top, bottom;
@@ -354,6 +356,7 @@
 	}
 }
 
+
 /*
 ==================
 CM_TestBoundingBoxInCapsule
@@ -361,7 +364,7 @@
 bounding box inside capsule check
 ==================
 */
-void CM_TestBoundingBoxInCapsule( traceWork_t *tw, clipHandle_t model ) {
+static void CM_TestBoundingBoxInCapsule( traceWork_t *tw, clipHandle_t model ) {
 	vec3_t mins, maxs, offset, size[2];
 	clipHandle_t h;
 	cmodel_t *cmod;
@@ -392,13 +395,14 @@
 	CM_TestInLeaf( tw, &cmod->leaf );
 }
 
+
 /*
 ==================
 CM_PositionTest
 ==================
 */
 #define	MAX_POSITION_LEAFS	1024
-void CM_PositionTest( traceWork_t *tw ) {
+static void CM_PositionTest( traceWork_t *tw ) {
 	int		leafs[MAX_POSITION_LEAFS];
 	int		i;
 	leafList_t	ll;
@@ -449,8 +453,7 @@
 CM_TraceThroughPatch
 ================
 */
-
-void CM_TraceThroughPatch( traceWork_t *tw, cPatch_t *patch ) {
+static void CM_TraceThroughPatch( traceWork_t *tw, const cPatch_t *patch ) {
 	float		oldFrac;
 
 	c_patch_traces++;
@@ -462,27 +465,25 @@
 	if ( tw->trace.fraction < oldFrac ) {
 		tw->trace.surfaceFlags = patch->surfaceFlags;
 		tw->trace.contents = patch->contents;
-		//tw->trace.shaderNum = patch->shaderNum;
-		//Com_Printf("%s patch trace %d  %s\n", __FUNCTION__, patch->shaderNum, cm.shaders[patch->shaderNum].shader);
-		//Com_Printf("patch trace %d\n", patch->shaderNum);
 	}
 }
 
+
 /*
 ================
 CM_TraceThroughBrush
 ================
 */
-void CM_TraceThroughBrush( traceWork_t *tw, cbrush_t *brush ) {
+static void CM_TraceThroughBrush( traceWork_t *tw, const cbrush_t *brush ) {
 	int			i;
 	cplane_t	*plane, *clipplane;
-	float		dist;
+	double		dist;
 	float		enterFrac, leaveFrac;
-	float		d1, d2;
+	double		d1, d2;
 	qboolean	getout, startout;
 	float		f;
 	cbrushside_t	*side, *leadside;
-	float		t;
+	double		t;
 	vec3_t		startp;
 	vec3_t		endp;
 
@@ -501,15 +502,12 @@
 
 	leadside = NULL;
 
-	//Com_Printf("brush %s\n", cm.shaders[brush->shaderNum].shader);
-
 	if ( tw->sphere.use ) {
 		//
 		// compare the trace against all planes of the brush
 		// find the latest time the trace crosses a plane towards the interior
 		// and the earliest time the trace crosses a plane towards the exterior
 		//
-		//Com_Printf("%s sphere\n", __FUNCTION__);
 		for (i = 0; i < brush->numsides; i++) {
 			side = brush->sides + i;
 			plane = side->plane;
@@ -518,20 +516,20 @@
 			dist = plane->dist + tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
-			t = DotProduct( plane->normal, tw->sphere.offset );
+			t = DotProductDP( plane->normal, tw->sphere.offset );
 			if ( t > 0 )
 			{
-				VectorSubtract( tw->start, tw->sphere.offset, startp );
-				VectorSubtract( tw->end, tw->sphere.offset, endp );
+				VectorSubtractDP( tw->start, tw->sphere.offset, startp );
+				VectorSubtractDP( tw->end, tw->sphere.offset, endp );
 			}
 			else
 			{
-				VectorAdd( tw->start, tw->sphere.offset, startp );
-				VectorAdd( tw->end, tw->sphere.offset, endp );
+				VectorAddDP( tw->start, tw->sphere.offset, startp );
+				VectorAddDP( tw->end, tw->sphere.offset, endp );
 			}
 
-			d1 = DotProduct( startp, plane->normal ) - dist;
-			d2 = DotProduct( endp, plane->normal ) - dist;
+			d1 = DotProductDP( startp, plane->normal ) - dist;
+			d2 = DotProductDP( endp, plane->normal ) - dist;
 
 			if (d2 > 0) {
 				getout = qtrue;	// endpoint is not in solid
@@ -542,7 +540,6 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s completely in front\n", __FUNCTION__);
 				return;
 			}
 
@@ -583,10 +580,10 @@
 			plane = side->plane;
 
 			// adjust the plane distance appropriately for mins/maxs
-			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
+			dist = plane->dist - DotProductDP( tw->offsets[ plane->signbits ], plane->normal );
 
-			d1 = DotProduct( tw->start, plane->normal ) - dist;
-			d2 = DotProduct( tw->end, plane->normal ) - dist;
+			d1 = DotProductDP( tw->start, plane->normal ) - dist;
+			d2 = DotProductDP( tw->end, plane->normal ) - dist;
 
 			if (d2 > 0) {
 				getout = qtrue;	// endpoint is not in solid
@@ -597,10 +594,6 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s no spehere completely in front  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
-				//if (brush->shaderNum) {  //(tw->trace.shaderNum == 0) {
-				//	tw->trace.shaderNum = brush->shaderNum;
-				//}
 				return;
 			}
 
@@ -643,40 +636,33 @@
 			tw->trace.fraction = 0;
 			tw->trace.contents = brush->contents;
 		}
-		//Com_Printf("%s done\n", __FUNCTION__);
 		return;
 	}
-	
+
 	if (enterFrac < leaveFrac) {
 		if (enterFrac > -1 && enterFrac < tw->trace.fraction) {
 			if (enterFrac < 0) {
 				enterFrac = 0;
 			}
 			tw->trace.fraction = enterFrac;
-			if (clipplane != NULL) {
+			if ( clipplane != NULL ) {
 				tw->trace.plane = *clipplane;
 			}
-			if (leadside != NULL) {
+			if ( leadside != NULL ) {
 				tw->trace.surfaceFlags = leadside->surfaceFlags;
 			}
 			tw->trace.contents = brush->contents;
-			//if (tw->trace.shaderNum == 0) {
-			//	tw->trace.shaderNum = brush->shaderNum;
-			//}
-			//Com_Printf("%d\n", 
-			//Com_Printf("yes\n");
-			//Com_Printf("%d %s\n", brush->shaderNum, "");
-			//Com_Printf("%s %d %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 		}
 	}
 }
 
+
 /*
 ================
 CM_TraceThroughLeaf
 ================
 */
-void CM_TraceThroughLeaf( traceWork_t *tw, cLeaf_t *leaf ) {
+static void CM_TraceThroughLeaf( traceWork_t *tw, const cLeaf_t *leaf ) {
 	int			k;
 	int			brushnum;
 	cbrush_t	*b;
@@ -703,7 +689,6 @@
 
 		CM_TraceThroughBrush( tw, b );
 		if ( !tw->trace.fraction ) {
-			//Com_Printf("%s no trace fraction\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -727,10 +712,9 @@
 			if ( !(patch->contents & tw->contents) ) {
 				continue;
 			}
-			
+
 			CM_TraceThroughPatch( tw, patch );
 			if ( !tw->trace.fraction ) {
-				//Com_Printf("%s 2 no trace fraction\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -746,7 +730,7 @@
 get the first intersection of the ray with the sphere
 ================
 */
-void CM_TraceThroughSphere( traceWork_t *tw, vec3_t origin, float radius, vec3_t start, vec3_t end ) {
+static void CM_TraceThroughSphere( traceWork_t *tw, const vec3_t origin, float radius, const vec3_t start, const vec3_t end ) {
 	float l1, l2, length, scale, fraction;
 	//float a;
 	float b, c, d, sqrtd;
@@ -764,7 +748,6 @@
 		if (l1 < Square(radius)) {
 			tw->trace.allsolid = qtrue;
 		}
-		//Com_Printf("%s radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -776,7 +759,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the sphere and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square dist\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -820,7 +802,6 @@
 			VectorAdd( tw->modelOrigin, intersection, intersection);
 			tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 			tw->trace.contents = CONTENTS_BODY;
-			//Com_Printf("%s fraction less\n", __FUNCTION__);
 		}
 	}
 	else if (d == 0) {
@@ -830,6 +811,7 @@
 	// no intersection at all
 }
 
+
 /*
 ================
 CM_TraceThroughVerticalCylinder
@@ -838,7 +820,7 @@
 the cylinder extends halfheight above and below the origin
 ================
 */
-void CM_TraceThroughVerticalCylinder( traceWork_t *tw, vec3_t origin, float radius, float halfheight, vec3_t start, vec3_t end) {
+static void CM_TraceThroughVerticalCylinder( traceWork_t *tw, const vec3_t origin, float radius, float halfheight, const vec3_t start, const vec3_t end ) {
 	float length, scale, fraction, l1, l2;
 	//float a;
 	float b, c, d, sqrtd;
@@ -848,7 +830,7 @@
 	VectorSet(start2d, start[0], start[1], 0);
 	VectorSet(end2d, end[0], end[1], 0);
 	VectorSet(org2d, origin[0], origin[1], 0);
-	// if between lower and upper cylinder bounds
+	// if start is between lower and upper cylinder bounds
 	if (start[2] <= origin[2] + halfheight &&
 				start[2] >= origin[2] - halfheight) {
 		// if inside the cylinder
@@ -862,7 +844,6 @@
 			if (l1 < Square(radius)) {
 				tw->trace.allsolid = qtrue;
 			}
-			//Com_Printf("%s radius\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -875,7 +856,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the cylinder and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -927,7 +907,6 @@
 				VectorAdd( tw->modelOrigin, intersection, intersection);
 				tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 				tw->trace.contents = CONTENTS_BODY;
-				//Com_Printf("%s set\n", __FUNCTION__);
 			}
 		}
 	}
@@ -938,6 +917,7 @@
 	// no intersection at all
 }
 
+
 /*
 ================
 CM_TraceCapsuleThroughCapsule
@@ -945,7 +925,7 @@
 capsule vs. capsule collision (not rotated)
 ================
 */
-void CM_TraceCapsuleThroughCapsule( traceWork_t *tw, clipHandle_t model ) {
+static void CM_TraceCapsuleThroughCapsule( traceWork_t *tw, clipHandle_t model ) {
 	int i;
 	vec3_t mins, maxs;
 	vec3_t top, bottom, starttop, startbottom, endtop, endbottom;
@@ -961,7 +941,6 @@
 		|| tw->bounds[1][1] < mins[1] - RADIUS_EPSILON
 		|| tw->bounds[1][2] < mins[2] - RADIUS_EPSILON
 		) {
-		//Com_Printf("%s bounds\n", __FUNCTION__);
 		return;
 	}
 	// top origin and bottom origin of each sphere at start and end of trace
@@ -1001,6 +980,7 @@
 	CM_TraceThroughSphere(tw, bottom, radius, starttop, endtop);
 }
 
+
 /*
 ================
 CM_TraceBoundingBoxThroughCapsule
@@ -1008,7 +988,7 @@
 bounding box vs. capsule collision
 ================
 */
-void CM_TraceBoundingBoxThroughCapsule( traceWork_t *tw, clipHandle_t model ) {
+static void CM_TraceBoundingBoxThroughCapsule( traceWork_t *tw, clipHandle_t model ) {
 	vec3_t mins, maxs, offset, size[2];
 	clipHandle_t h;
 	cmodel_t *cmod;
@@ -1051,10 +1031,10 @@
 a smaller intercept fraction.
 ==================
 */
-void CM_TraceThroughTree( traceWork_t *tw, int num, float p1f, float p2f, vec3_t p1, vec3_t p2) {
+static void CM_TraceThroughTree( traceWork_t *tw, int num, float p1f, float p2f, const vec3_t p1, const vec3_t p2 ) {
 	cNode_t		*node;
 	cplane_t	*plane;
-	float		t1, t2, offset;
+	double		t1, t2, offset;
 	float		frac, frac2;
 	float		idist;
 	vec3_t		mid;
@@ -1062,7 +1042,6 @@
 	float		midf;
 
 	if (tw->trace.fraction <= p1f) {
-		//Com_Printf("%s already hit something\n", __FUNCTION__);
 		return;		// already hit something nearer
 	}
 
@@ -1085,8 +1064,8 @@
 		t2 = p2[plane->type] - plane->dist;
 		offset = tw->extents[plane->type];
 	} else {
-		t1 = DotProduct (plane->normal, p1) - plane->dist;
-		t2 = DotProduct (plane->normal, p2) - plane->dist;
+		t1 = DotProductDP( plane->normal, p1 ) - plane->dist;
+		t2 = DotProductDP( plane->normal, p2 ) - plane->dist;
 		if ( tw->isPoint ) {
 			offset = 0;
 		} else {
@@ -1125,11 +1104,10 @@
 	// move up to the node
 	if ( frac < 0 ) {
 		frac = 0;
-	}
-	if ( frac > 1 ) {
+	} else if ( frac > 1 ) {
 		frac = 1;
 	}
-		
+
 	midf = p1f + (p2f - p1f)*frac;
 
 	mid[0] = p1[0] + frac*(p2[0] - p1[0]);
@@ -1138,15 +1116,13 @@
 
 	CM_TraceThroughTree( tw, node->children[side], p1f, midf, p1, mid );
 
-
 	// go past the node
 	if ( frac2 < 0 ) {
 		frac2 = 0;
-	}
-	if ( frac2 > 1 ) {
+	} else if ( frac2 > 1 ) {
 		frac2 = 1;
 	}
-		
+
 	midf = p1f + (p2f - p1f)*frac2;
 
 	mid[0] = p1[0] + frac2*(p2[0] - p1[0]);
@@ -1165,14 +1141,13 @@
 CM_Trace
 ==================
 */
-void CM_Trace( trace_t *results, const vec3_t start, const vec3_t end, vec3_t mins, vec3_t maxs,
-						  clipHandle_t model, const vec3_t origin, int brushmask, int capsule, sphere_t *sphere ) {
+static void CM_Trace( trace_t *results, const vec3_t start, const vec3_t end, const vec3_t mins, const vec3_t maxs,
+						clipHandle_t model, const vec3_t origin, int brushmask, qboolean capsule, const sphere_t *sphere ) {
 	int			i;
 	traceWork_t	tw;
 	vec3_t		offset;
 	cmodel_t	*cmod;
 
-	//Com_Printf("^3CM_Trace()\n");
 	cmod = CM_ClipHandleToModel( model );
 
 	cm.checkcount++;		// for multi-check avoidance
@@ -1201,7 +1176,7 @@
 	// set basic parms
 	tw.contents = brushmask;
 
-	// adjust so that mins and maxs are always symetric, which
+	// adjust so that mins and maxs are always symmetric, which
 	// avoids some complications with plane expanding of rotated
 	// bmodels
 	for ( i = 0 ; i < 3 ; i++ ) {
@@ -1379,29 +1354,31 @@
 	*results = tw.trace;
 }
 
+
 /*
 ==================
 CM_BoxTrace
 ==================
 */
 void CM_BoxTrace( trace_t *results, const vec3_t start, const vec3_t end,
-						  vec3_t mins, vec3_t maxs,
-						  clipHandle_t model, int brushmask, int capsule ) {
+						const vec3_t mins, const vec3_t maxs,
+						clipHandle_t model, int brushmask, qboolean capsule ) {
 	CM_Trace( results, start, end, mins, maxs, model, vec3_origin, brushmask, capsule, NULL );
 }
 
+
 /*
 ==================
 CM_TransformedBoxTrace
 
-Handles offseting and rotation of the end points for moving and
+Handles offsetting and rotation of the end points for moving and
 rotating entities
 ==================
 */
 void CM_TransformedBoxTrace( trace_t *results, const vec3_t start, const vec3_t end,
-						  vec3_t mins, vec3_t maxs,
-						  clipHandle_t model, int brushmask,
-						  const vec3_t origin, const vec3_t angles, int capsule ) {
+						const vec3_t mins, const vec3_t maxs,
+						clipHandle_t model, int brushmask,
+						const vec3_t origin, const vec3_t angles, qboolean capsule ) {
 	trace_t		trace;
 	vec3_t		start_l, end_l;
 	qboolean	rotated;
@@ -1421,7 +1398,7 @@
 		maxs = vec3_origin;
 	}
 
-	// adjust so that mins and maxs are always symetric, which
+	// adjust so that mins and maxs are always symmetric, which
 	// avoids some complications with plane expanding of rotated
 	// bmodels
 	for ( i = 0 ; i < 3 ; i++ ) {
@@ -1437,7 +1414,7 @@
 	VectorSubtract( end_l, origin, end_l );
 
 	// rotate start and end into the models frame of reference
-	if ( model != BOX_MODEL_HANDLE && 
+	if ( model != BOX_MODEL_HANDLE &&
 		(angles[0] || angles[1] || angles[2]) ) {
 		rotated = qtrue;
 	} else {

```

### `openarena-engine`  — sha256 `3c268f5d6040...`, 39843 bytes

_Diff stat: +25 / -46 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_trace.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_trace.c	2026-04-16 22:48:25.906297600 +0100
@@ -76,6 +76,20 @@
 
 /*
 ================
+CM_ProjectPointOntoVector
+================
+*/
+void CM_ProjectPointOntoVector( vec3_t point, vec3_t vStart, vec3_t vDir, vec3_t vProj )
+{
+	vec3_t pVec;
+
+	VectorSubtract( point, vStart, pVec );
+	// project onto the directional vector for this segment
+	VectorMA( vStart, DotProduct( pVec, vDir ), vDir, vProj );
+}
+
+/*
+================
 CM_DistanceFromLineSquared
 ================
 */
@@ -83,8 +97,8 @@
 	vec3_t proj, t;
 	int j;
 
-	ProjectPointOntoVector(p, lp1, dir, proj);
-	for (j = 0; j < 3; j++)
+	CM_ProjectPointOntoVector(p, lp1, dir, proj);
+	for (j = 0; j < 3; j++) 
 		if ((proj[j] > lp1[j] && proj[j] > lp2[j]) ||
 			(proj[j] < lp1[j] && proj[j] < lp2[j]))
 			break;
@@ -175,7 +189,7 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			dist = plane->dist + tw->sphere.radius;
 			// find the closest point on the capsule to the plane
 			t = DotProduct( plane->normal, tw->sphere.offset );
@@ -190,7 +204,6 @@
 			d1 = DotProduct( startp, plane->normal ) - dist;
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s in front\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -201,14 +214,13 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for mins/maxs
+			// adjust the plane distance apropriately for mins/maxs
 			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
 
 			d1 = DotProduct( tw->start, plane->normal ) - dist;
 
 			// if completely in front of face, no intersection
 			if ( d1 > 0 ) {
-				//Com_Printf("%s siz  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 				return;
 			}
 		}
@@ -218,7 +230,6 @@
 	tw->trace.startsolid = tw->trace.allsolid = qtrue;
 	tw->trace.fraction = 0;
 	tw->trace.contents = brush->contents;
-	//Com_Printf("%s inside brush\n", __FUNCTION__);
 }
 
 
@@ -249,7 +260,6 @@
 		
 		CM_TestBoxInBrush( tw, b );
 		if ( tw->trace.allsolid ) {
-			//Com_Printf("%s all solid\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -278,7 +288,6 @@
 				tw->trace.startsolid = tw->trace.allsolid = qtrue;
 				tw->trace.fraction = 0;
 				tw->trace.contents = patch->contents;
-				//Com_Printf("%s patch collide\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -462,9 +471,6 @@
 	if ( tw->trace.fraction < oldFrac ) {
 		tw->trace.surfaceFlags = patch->surfaceFlags;
 		tw->trace.contents = patch->contents;
-		//tw->trace.shaderNum = patch->shaderNum;
-		//Com_Printf("%s patch trace %d  %s\n", __FUNCTION__, patch->shaderNum, cm.shaders[patch->shaderNum].shader);
-		//Com_Printf("patch trace %d\n", patch->shaderNum);
 	}
 }
 
@@ -501,20 +507,17 @@
 
 	leadside = NULL;
 
-	//Com_Printf("brush %s\n", cm.shaders[brush->shaderNum].shader);
-
 	if ( tw->sphere.use ) {
 		//
 		// compare the trace against all planes of the brush
 		// find the latest time the trace crosses a plane towards the interior
 		// and the earliest time the trace crosses a plane towards the exterior
 		//
-		//Com_Printf("%s sphere\n", __FUNCTION__);
 		for (i = 0; i < brush->numsides; i++) {
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			dist = plane->dist + tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -542,11 +545,10 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s completely in front\n", __FUNCTION__);
 				return;
 			}
 
-			// if it doesn't cross the plane, the plane isn't relevant
+			// if it doesn't cross the plane, the plane isn't relevent
 			if (d1 <= 0 && d2 <= 0 ) {
 				continue;
 			}
@@ -582,7 +584,7 @@
 			side = brush->sides + i;
 			plane = side->plane;
 
-			// adjust the plane distance appropriately for mins/maxs
+			// adjust the plane distance apropriately for mins/maxs
 			dist = plane->dist - DotProduct( tw->offsets[ plane->signbits ], plane->normal );
 
 			d1 = DotProduct( tw->start, plane->normal ) - dist;
@@ -597,14 +599,10 @@
 
 			// if completely in front of face, no intersection with the entire brush
 			if (d1 > 0 && ( d2 >= SURFACE_CLIP_EPSILON || d2 >= d1 )  ) {
-				//Com_Printf("%s no spehere completely in front  %d  %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
-				//if (brush->shaderNum) {  //(tw->trace.shaderNum == 0) {
-				//	tw->trace.shaderNum = brush->shaderNum;
-				//}
 				return;
 			}
 
-			// if it doesn't cross the plane, the plane isn't relevant
+			// if it doesn't cross the plane, the plane isn't relevent
 			if (d1 <= 0 && d2 <= 0 ) {
 				continue;
 			}
@@ -643,7 +641,6 @@
 			tw->trace.fraction = 0;
 			tw->trace.contents = brush->contents;
 		}
-		//Com_Printf("%s done\n", __FUNCTION__);
 		return;
 	}
 	
@@ -660,13 +657,6 @@
 				tw->trace.surfaceFlags = leadside->surfaceFlags;
 			}
 			tw->trace.contents = brush->contents;
-			//if (tw->trace.shaderNum == 0) {
-			//	tw->trace.shaderNum = brush->shaderNum;
-			//}
-			//Com_Printf("%d\n", 
-			//Com_Printf("yes\n");
-			//Com_Printf("%d %s\n", brush->shaderNum, "");
-			//Com_Printf("%s %d %s\n", __FUNCTION__, brush->shaderNum, cm.shaders[brush->shaderNum].shader);
 		}
 	}
 }
@@ -703,7 +693,6 @@
 
 		CM_TraceThroughBrush( tw, b );
 		if ( !tw->trace.fraction ) {
-			//Com_Printf("%s no trace fraction\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -730,7 +719,6 @@
 			
 			CM_TraceThroughPatch( tw, patch );
 			if ( !tw->trace.fraction ) {
-				//Com_Printf("%s 2 no trace fraction\n", __FUNCTION__);
 				return;
 			}
 		}
@@ -764,7 +752,6 @@
 		if (l1 < Square(radius)) {
 			tw->trace.allsolid = qtrue;
 		}
-		//Com_Printf("%s radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -776,7 +763,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the sphere and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square dist\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -820,7 +806,6 @@
 			VectorAdd( tw->modelOrigin, intersection, intersection);
 			tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 			tw->trace.contents = CONTENTS_BODY;
-			//Com_Printf("%s fraction less\n", __FUNCTION__);
 		}
 	}
 	else if (d == 0) {
@@ -862,7 +847,6 @@
 			if (l1 < Square(radius)) {
 				tw->trace.allsolid = qtrue;
 			}
-			//Com_Printf("%s radius\n", __FUNCTION__);
 			return;
 		}
 	}
@@ -875,7 +859,6 @@
 	l2 = VectorLengthSquared(v1);
 	// if no intersection with the cylinder and the end point is at least an epsilon away
 	if (l1 >= Square(radius) && l2 > Square(radius+SURFACE_CLIP_EPSILON)) {
-		//Com_Printf("%s square radius\n", __FUNCTION__);
 		return;
 	}
 	//
@@ -927,7 +910,6 @@
 				VectorAdd( tw->modelOrigin, intersection, intersection);
 				tw->trace.plane.dist = DotProduct(tw->trace.plane.normal, intersection);
 				tw->trace.contents = CONTENTS_BODY;
-				//Com_Printf("%s set\n", __FUNCTION__);
 			}
 		}
 	}
@@ -961,7 +943,6 @@
 		|| tw->bounds[1][1] < mins[1] - RADIUS_EPSILON
 		|| tw->bounds[1][2] < mins[2] - RADIUS_EPSILON
 		) {
-		//Com_Printf("%s bounds\n", __FUNCTION__);
 		return;
 	}
 	// top origin and bottom origin of each sphere at start and end of trace
@@ -1062,7 +1043,6 @@
 	float		midf;
 
 	if (tw->trace.fraction <= p1f) {
-		//Com_Printf("%s already hit something\n", __FUNCTION__);
 		return;		// already hit something nearer
 	}
 
@@ -1073,13 +1053,13 @@
 	}
 
 	//
-	// find the point distances to the separating plane
+	// find the point distances to the seperating plane
 	// and the offset for the size of the box
 	//
 	node = cm.nodes + num;
 	plane = node->plane;
 
-	// adjust the plane distance appropriately for mins/maxs
+	// adjust the plane distance apropriately for mins/maxs
 	if ( plane->type < 3 ) {
 		t1 = p1[plane->type] - plane->dist;
 		t2 = p2[plane->type] - plane->dist;
@@ -1172,7 +1152,6 @@
 	vec3_t		offset;
 	cmodel_t	*cmod;
 
-	//Com_Printf("^3CM_Trace()\n");
 	cmod = CM_ClipHandleToModel( model );
 
 	cm.checkcount++;		// for multi-check avoidance
@@ -1225,7 +1204,7 @@
 
 	tw.maxOffset = tw.size[1][0] + tw.size[1][1] + tw.size[1][2];
 
-	// tw.offsets[signbits] = vector to appropriate corner from origin
+	// tw.offsets[signbits] = vector to apropriate corner from origin
 	tw.offsets[0][0] = tw.size[0][0];
 	tw.offsets[0][1] = tw.size[0][1];
 	tw.offsets[0][2] = tw.size[0][2];

```
