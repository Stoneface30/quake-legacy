# Diff: `code/qcommon/cm_test.c`
**Canonical:** `wolfcamql-src` (sha256 `87ed95508bc8...`, 11699 bytes)

## Variants

### `quake3-source`  — sha256 `2e5d1139c88a...`, 10326 bytes

_Diff stat: +4 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_test.c	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_test.c	2026-04-16 20:02:19.957606300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -37,17 +37,15 @@
 	{
 		node = cm.nodes + num;
 		plane = node->plane;
-
+		
 		if (plane->type < 3)
 			d = p[plane->type] - plane->dist;
 		else
 			d = DotProduct (plane->normal, p) - plane->dist;
-		if (d < 0) {  // (0.0) {
+		if (d < 0)
 			num = node->children[1];
-		} else {
+		else
 			num = node->children[0];
-		}
-		//Com_Printf("point %f  nan %d\n", d, IS_NAN(d));
 	}
 
 	c_pointcontents++;		// optimize counter
@@ -174,7 +172,6 @@
 int	CM_BoxLeafnums( const vec3_t mins, const vec3_t maxs, int *list, int listsize, int *lastLeaf) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -200,7 +197,6 @@
 int CM_BoxBrushes( const vec3_t mins, const vec3_t maxs, cbrush_t **list, int listsize ) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -254,10 +250,6 @@
 		brushnum = cm.leafbrushes[leaf->firstLeafBrush+k];
 		b = &cm.brushes[brushnum];
 
-		if ( !CM_BoundsIntersectPoint( b->bounds[0], b->bounds[1], p ) ) {
-			continue;
-		}
-
 		// see if the point is in the brush
 		for ( i = 0 ; i < b->numsides ; i++ ) {
 			d = DotProduct( p, b->sides[i].plane->normal );
@@ -271,7 +263,6 @@
 		if ( i == b->numsides ) {
 			contents |= b->contents;
 		}
-		//Com_Printf("CM_PointContents() %d  %s\n", b->shaderNum, cm.shaders[b->shaderNum].shader);
 	}
 
 	return contents;
@@ -485,42 +476,3 @@
 	return bytes;
 }
 
-/*
-====================
-CM_BoundsIntersect
-====================
-*/
-qboolean CM_BoundsIntersect( const vec3_t mins, const vec3_t maxs, const vec3_t mins2, const vec3_t maxs2 )
-{
-	if (maxs[0] < mins2[0] - SURFACE_CLIP_EPSILON ||
-		maxs[1] < mins2[1] - SURFACE_CLIP_EPSILON ||
-		maxs[2] < mins2[2] - SURFACE_CLIP_EPSILON ||
-		mins[0] > maxs2[0] + SURFACE_CLIP_EPSILON ||
-		mins[1] > maxs2[1] + SURFACE_CLIP_EPSILON ||
-		mins[2] > maxs2[2] + SURFACE_CLIP_EPSILON)
-	{
-		return qfalse;
-	}
-
-	return qtrue;
-}
-
-/*
-====================
-CM_BoundsIntersectPoint
-====================
-*/
-qboolean CM_BoundsIntersectPoint( const vec3_t mins, const vec3_t maxs, const vec3_t point )
-{
-	if (maxs[0] < point[0] - SURFACE_CLIP_EPSILON ||
-		maxs[1] < point[1] - SURFACE_CLIP_EPSILON ||
-		maxs[2] < point[2] - SURFACE_CLIP_EPSILON ||
-		mins[0] > point[0] + SURFACE_CLIP_EPSILON ||
-		mins[1] > point[1] + SURFACE_CLIP_EPSILON ||
-		mins[2] > point[2] + SURFACE_CLIP_EPSILON)
-	{
-		return qfalse;
-	}
-
-	return qtrue;
-}

```

### `openarena-engine`  — sha256 `00a0209bf18a...`, 11470 bytes
Also identical in: ioquake3

_Diff stat: +3 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_test.c	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_test.c	2026-04-16 22:48:25.906297600 +0100
@@ -37,17 +37,15 @@
 	{
 		node = cm.nodes + num;
 		plane = node->plane;
-
+		
 		if (plane->type < 3)
 			d = p[plane->type] - plane->dist;
 		else
 			d = DotProduct (plane->normal, p) - plane->dist;
-		if (d < 0) {  // (0.0) {
+		if (d < 0)
 			num = node->children[1];
-		} else {
+		else
 			num = node->children[0];
-		}
-		//Com_Printf("point %f  nan %d\n", d, IS_NAN(d));
 	}
 
 	c_pointcontents++;		// optimize counter
@@ -174,7 +172,6 @@
 int	CM_BoxLeafnums( const vec3_t mins, const vec3_t maxs, int *list, int listsize, int *lastLeaf) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -200,7 +197,6 @@
 int CM_BoxBrushes( const vec3_t mins, const vec3_t maxs, cbrush_t **list, int listsize ) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -271,7 +267,6 @@
 		if ( i == b->numsides ) {
 			contents |= b->contents;
 		}
-		//Com_Printf("CM_PointContents() %d  %s\n", b->shaderNum, cm.shaders[b->shaderNum].shader);
 	}
 
 	return contents;

```

### `quake3e`  — sha256 `4d112c4b5bd2...`, 11614 bytes

_Diff stat: +26 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_test.c	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_test.c	2026-04-16 20:02:27.300418600 +0100
@@ -28,7 +28,7 @@
 
 ==================
 */
-int CM_PointLeafnum_r( const vec3_t p, int num ) {
+static int CM_PointLeafnum_r( const vec3_t p, int num ) {
 	float		d;
 	cNode_t		*node;
 	cplane_t	*plane;
@@ -37,17 +37,15 @@
 	{
 		node = cm.nodes + num;
 		plane = node->plane;
-
+		
 		if (plane->type < 3)
 			d = p[plane->type] - plane->dist;
 		else
 			d = DotProduct (plane->normal, p) - plane->dist;
-		if (d < 0) {  // (0.0) {
+		if (d < 0)
 			num = node->children[1];
-		} else {
+		else
 			num = node->children[0];
-		}
-		//Com_Printf("point %f  nan %d\n", d, IS_NAN(d));
 	}
 
 	c_pointcontents++;		// optimize counter
@@ -174,7 +172,6 @@
 int	CM_BoxLeafnums( const vec3_t mins, const vec3_t maxs, int *list, int listsize, int *lastLeaf) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -200,7 +197,6 @@
 int CM_BoxBrushes( const vec3_t mins, const vec3_t maxs, cbrush_t **list, int listsize ) {
 	leafList_t	ll;
 
-	memset(&ll, 0, sizeof(ll));
 	cm.checkcount++;
 
 	VectorCopy( mins, ll.bounds[0] );
@@ -271,7 +267,6 @@
 		if ( i == b->numsides ) {
 			contents |= b->contents;
 		}
-		//Com_Printf("CM_PointContents() %d  %s\n", b->shaderNum, cm.shaders[b->shaderNum].shader);
 	}
 
 	return contents;
@@ -281,7 +276,7 @@
 ==================
 CM_TransformedPointContents
 
-Handles offseting and rotation of the end points for moving and
+Handles offsetting and rotation of the end points for moving and
 rotating entities
 ==================
 */
@@ -319,8 +314,8 @@
 */
 
 byte	*CM_ClusterPVS (int cluster) {
-	if (cluster < 0 || cluster >= cm.numClusters || !cm.vised ) {
-		return cm.visibility;
+	if (cluster < 0 || cluster >= cm.numClusters || !cm.visibility ) {
+		return cm.novis;
 	}
 
 	return cm.visibility + cluster * cm.clusterBytes;
@@ -336,7 +331,7 @@
 ===============================================================================
 */
 
-void CM_FloodArea_r( int areaNum, int floodnum) {
+static void CM_FloodArea_r( int areaNum, int floodnum) {
 	int		i;
 	cArea_t *area;
 	int		*con;
@@ -467,7 +462,7 @@
 #ifndef BSPC
 	if (cm_noAreas->integer || area == -1)
 #else
-	if ( area == -1)
+	if (area == -1)
 #endif
 	{	// for debugging, send everything
 		Com_Memset (buffer, 255, bytes);
@@ -477,7 +472,7 @@
 		floodnum = cm.areas[area].floodnum;
 		for (i=0 ; i<cm.numAreas ; i++)
 		{
-			if (cm.areas[i].floodnum == floodnum || area == -1)
+			if (cm.areas[i].floodnum == floodnum)
 				buffer[i>>3] |= 1<<(i&7);
 		}
 	}
@@ -485,6 +480,9 @@
 	return bytes;
 }
 
+
+#define BOUNDS_CLIP_EPSILON 0.25f // assume single precision and slightly increase to compensate potential SIMD precision loss in 64-bit environment
+
 /*
 ====================
 CM_BoundsIntersect
@@ -492,12 +490,12 @@
 */
 qboolean CM_BoundsIntersect( const vec3_t mins, const vec3_t maxs, const vec3_t mins2, const vec3_t maxs2 )
 {
-	if (maxs[0] < mins2[0] - SURFACE_CLIP_EPSILON ||
-		maxs[1] < mins2[1] - SURFACE_CLIP_EPSILON ||
-		maxs[2] < mins2[2] - SURFACE_CLIP_EPSILON ||
-		mins[0] > maxs2[0] + SURFACE_CLIP_EPSILON ||
-		mins[1] > maxs2[1] + SURFACE_CLIP_EPSILON ||
-		mins[2] > maxs2[2] + SURFACE_CLIP_EPSILON)
+	if (maxs[0] < mins2[0] - BOUNDS_CLIP_EPSILON ||
+		maxs[1] < mins2[1] - BOUNDS_CLIP_EPSILON ||
+		maxs[2] < mins2[2] - BOUNDS_CLIP_EPSILON ||
+		mins[0] > maxs2[0] + BOUNDS_CLIP_EPSILON ||
+		mins[1] > maxs2[1] + BOUNDS_CLIP_EPSILON ||
+		mins[2] > maxs2[2] + BOUNDS_CLIP_EPSILON)
 	{
 		return qfalse;
 	}
@@ -505,6 +503,7 @@
 	return qtrue;
 }
 
+
 /*
 ====================
 CM_BoundsIntersectPoint
@@ -512,12 +511,12 @@
 */
 qboolean CM_BoundsIntersectPoint( const vec3_t mins, const vec3_t maxs, const vec3_t point )
 {
-	if (maxs[0] < point[0] - SURFACE_CLIP_EPSILON ||
-		maxs[1] < point[1] - SURFACE_CLIP_EPSILON ||
-		maxs[2] < point[2] - SURFACE_CLIP_EPSILON ||
-		mins[0] > point[0] + SURFACE_CLIP_EPSILON ||
-		mins[1] > point[1] + SURFACE_CLIP_EPSILON ||
-		mins[2] > point[2] + SURFACE_CLIP_EPSILON)
+	if (maxs[0] < point[0] - BOUNDS_CLIP_EPSILON ||
+		maxs[1] < point[1] - BOUNDS_CLIP_EPSILON ||
+		maxs[2] < point[2] - BOUNDS_CLIP_EPSILON ||
+		mins[0] > point[0] + BOUNDS_CLIP_EPSILON ||
+		mins[1] > point[1] + BOUNDS_CLIP_EPSILON ||
+		mins[2] > point[2] + BOUNDS_CLIP_EPSILON)
 	{
 		return qfalse;
 	}

```
