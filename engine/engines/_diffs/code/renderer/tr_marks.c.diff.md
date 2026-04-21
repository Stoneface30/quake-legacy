# Diff: `code/renderer/tr_marks.c`
**Canonical:** `quake3e` (sha256 `2f3eb526299a...`, 14645 bytes)

## Variants

### `quake3-source`  — sha256 `66d25d4d087c...`, 14224 bytes

_Diff stat: +23 / -40 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_marks.c	2026-04-16 20:02:27.318608500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_marks.c	2026-04-16 20:02:19.972123600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -39,7 +39,7 @@
 #define	SIDE_BACK	1
 #define	SIDE_ON		2
 static void R_ChopPolyBehindPlane( int numInPoints, vec3_t inPoints[MAX_VERTS_ON_POLY],
-								int *numOutPoints, vec3_t outPoints[MAX_VERTS_ON_POLY],
+								   int *numOutPoints, vec3_t outPoints[MAX_VERTS_ON_POLY], 
 							vec3_t normal, vec_t dist, vec_t epsilon) {
 	float		dists[MAX_VERTS_ON_POLY+4];
 	int			sides[MAX_VERTS_ON_POLY+4];
@@ -56,8 +56,6 @@
 	}
 
 	counts[0] = counts[1] = counts[2] = 0;
-	dists[0] = 0.0;
-	sides[0] = 0;
 
 	// determine sides for each point
 	for ( i = 0 ; i < numInPoints ; i++ ) {
@@ -133,13 +131,13 @@
 
 =================
 */
-static void R_BoxSurfaces_r(mnode_t *node, vec3_t mins, vec3_t maxs, surfaceType_t **list, int listsize, int *listlength, vec3_t dir) {
+void R_BoxSurfaces_r(mnode_t *node, vec3_t mins, vec3_t maxs, surfaceType_t **list, int listsize, int *listlength, vec3_t dir) {
 
 	int			s, c;
 	msurface_t	*surf, **mark;
 
 	// do the tail recursion in a loop
-	while ( node->contents == CONTENTS_NODE ) {
+	while ( node->contents == -1 ) {
 		s = BoxOnPlaneSide( mins, maxs, node->plane );
 		if (s == 1) {
 			node = node->children[0];
@@ -175,9 +173,7 @@
 				surf->viewCount = tr.viewCount;
 			}
 		}
-		else if (*(surfaceType_t *) (surf->data) != SF_GRID &&
-			 *(surfaceType_t *) (surf->data) != SF_TRIANGLES)
-			surf->viewCount = tr.viewCount;
+		else if (*(surfaceType_t *) (surf->data) != SF_GRID) surf->viewCount = tr.viewCount;
 		// check the viewCount because the surface may have
 		// already been added if it spans multiple leafs
 		if (surf->viewCount != tr.viewCount) {
@@ -195,7 +191,7 @@
 
 =================
 */
-static void R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
+void R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
 				   int numPlanes, vec3_t *normals, float *dists,
 				   int maxPoints, vec3_t pointBuffer,
 				   int maxFragments, markFragment_t *fragmentBuffer,
@@ -267,6 +263,7 @@
 	vec3_t			clipPoints[2][MAX_VERTS_ON_POLY];
 	int				numClipPoints;
 	float			*v;
+	srfSurfaceFace_t *surf;
 	srfGridMesh_t	*cv;
 	drawVert_t		*dv;
 	vec3_t			normal;
@@ -274,10 +271,6 @@
 	vec3_t			v1, v2;
 	int				*indexes;
 
-	if (numPoints <= 0) {
-		return 0;
-	}
-
 	//increment view count for double check prevention
 	tr.viewCount++;
 
@@ -406,20 +399,25 @@
 		}
 		else if (*surfaces[i] == SF_FACE) {
 
-			srfSurfaceFace_t *surf = ( srfSurfaceFace_t * ) surfaces[i];
-
+			surf = ( srfSurfaceFace_t * ) surfaces[i];
 			// check the normal of this face
 			if (DotProduct(surf->plane.normal, projectionDir) > -0.5) {
 				continue;
 			}
 
+			/*
+			VectorSubtract(clipPoints[0][0], clipPoints[0][1], v1);
+			VectorSubtract(clipPoints[0][2], clipPoints[0][1], v2);
+			CrossProduct(v1, v2, normal);
+			VectorNormalize(normal);
+			if (DotProduct(normal, projectionDir) > -0.5) continue;
+			*/
 			indexes = (int *)( (byte *)surf + surf->ofsIndices );
 			for ( k = 0 ; k < surf->numIndices ; k += 3 ) {
 				for ( j = 0 ; j < 3 ; j++ ) {
-					v = &surf->points[0][0] + VERTEXSIZE * indexes[k+j];
+					v = surf->points[0] + VERTEXSIZE * indexes[k+j];;
 					VectorMA( v, MARKER_OFFSET, surf->plane.normal, clipPoints[0][j] );
 				}
-
 				// add the fragments of this face
 				R_AddMarkFragments( 3 , clipPoints,
 								   numPlanes, normals, dists,
@@ -430,29 +428,14 @@
 					return returnedFragments;	// not enough space for more fragments
 				}
 			}
+			continue;
 		}
-		else if(*surfaces[i] == SF_TRIANGLES && r_marksOnTriangleMeshes->integer) {
-
-			srfTriangles_t *surf = (srfTriangles_t *) surfaces[i];
-
-			for (k = 0; k < surf->numIndexes; k += 3)
-			{
-				for(j = 0; j < 3; j++)
-				{
-					v = surf->verts[surf->indexes[k + j]].xyz;
-					VectorMA(v, MARKER_OFFSET, surf->verts[surf->indexes[k + j]].normal, clipPoints[0][j]);
-				}
-
-				// add the fragments of this face
-				R_AddMarkFragments(3, clipPoints,
-								   numPlanes, normals, dists,
-								   maxPoints, pointBuffer,
-								   maxFragments, fragmentBuffer, &returnedPoints, &returnedFragments, mins, maxs);
-				if(returnedFragments == maxFragments)
-				{
-					return returnedFragments;	// not enough space for more fragments
-				}
-			}
+		else {
+			// ignore all other world surfaces
+			// might be cool to also project polygons on a triangle soup
+			// however this will probably create huge amounts of extra polys
+			// even more than the projection onto curves
+			continue;
 		}
 	}
 	return returnedFragments;

```
