# Diff: `code/renderer/tr_curve.c`
**Canonical:** `quake3e` (sha256 `6a88874ff328...`, 16601 bytes)

## Variants

### `quake3-source`  — sha256 `c4599f0d154d...`, 16446 bytes

_Diff stat: +33 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_curve.c	2026-04-16 20:02:27.315570800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_curve.c	2026-04-16 20:02:19.969123300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -54,10 +54,10 @@
 	out->lightmap[0] = 0.5f * (a->lightmap[0] + b->lightmap[0]);
 	out->lightmap[1] = 0.5f * (a->lightmap[1] + b->lightmap[1]);
 
-	out->color.rgba[0] = (a->color.rgba[0] + b->color.rgba[0]) >> 1;
-	out->color.rgba[1] = (a->color.rgba[1] + b->color.rgba[1]) >> 1;
-	out->color.rgba[2] = (a->color.rgba[2] + b->color.rgba[2]) >> 1;
-	out->color.rgba[3] = (a->color.rgba[3] + b->color.rgba[3]) >> 1;
+	out->color[0] = (a->color[0] + b->color[0]) >> 1;
+	out->color[1] = (a->color[1] + b->color[1]) >> 1;
+	out->color[2] = (a->color[2] + b->color[2]) >> 1;
+	out->color[3] = (a->color[3] + b->color[3]) >> 1;
 }
 
 /*
@@ -113,6 +113,7 @@
 	int		i, j, k, dist;
 	vec3_t	normal;
 	vec3_t	sum;
+	int		count;
 	vec3_t	base;
 	vec3_t	delta;
 	int		x, y;
@@ -121,7 +122,9 @@
 	qboolean	good[8];
 	qboolean	wrapWidth, wrapHeight;
 	float		len;
-	static const int neighbors[8][2] = { {0,1}, {1,1}, {1,0}, {1,-1}, {0,-1}, {-1,-1}, {-1,0}, {-1,1} };
+static	int	neighbors[8][2] = {
+	{0,1}, {1,1}, {1,0}, {1,-1}, {0,-1}, {-1,-1}, {-1,0}, {-1,1}
+	};
 
 	wrapWidth = qfalse;
 	for ( i = 0 ; i < height ; i++ ) {
@@ -150,6 +153,7 @@
 
 	for ( i = 0 ; i < width ; i++ ) {
 		for ( j = 0 ; j < height ; j++ ) {
+			count = 0;
 			dv = &ctrl[j][i];
 			VectorCopy( dv->xyz, base );
 			for ( k = 0 ; k < 8 ; k++ ) {
@@ -178,7 +182,7 @@
 						break;					// edge of patch
 					}
 					VectorSubtract( ctrl[y][x].xyz, base, temp );
-					if ( VectorNormalize( temp ) < 0.001f ) {
+					if ( VectorNormalize2( temp, temp ) == 0 ) {
 						continue;				// degenerate edge, get more dist
 					} else {
 						good[k] = qtrue;
@@ -194,16 +198,17 @@
 					continue;	// didn't get two points
 				}
 				CrossProduct( around[(k+1)&7], around[k], normal );
-				if ( VectorNormalize( normal ) < 0.001f ) {
+				if ( VectorNormalize2( normal, normal ) == 0 ) {
 					continue;
 				}
 				VectorAdd( normal, sum, sum );
+				count++;
 			}
-
-			VectorNormalize2( sum, dv->normal );
-			for ( k = 0; k < 3; k++ ) {
-				dv->normal[k] = R_ClampDenorm( dv->normal[k] );
+			if ( count == 0 ) {
+//printf("bad normal\n");
+				count = 1;
 			}
+			VectorNormalize2( sum, dv->normal );
 		}
 	}
 }
@@ -282,7 +287,7 @@
 R_CreateSurfaceGridMesh
 =================
 */
-static srfGridMesh_t *R_CreateSurfaceGridMesh(int width, int height,
+srfGridMesh_t *R_CreateSurfaceGridMesh(int width, int height,
 								drawVert_t ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE], float errorTable[2][MAX_GRID_SIZE] ) {
 	int i, j, size;
 	drawVert_t	*vert;
@@ -355,29 +360,23 @@
 srfGridMesh_t *R_SubdividePatchToGrid( int width, int height,
 								drawVert_t points[MAX_PATCH_SIZE*MAX_PATCH_SIZE] ) {
 	int			i, j, k, l;
-	drawVert_t	prev;
-	drawVert_t	next;
-	drawVert_t	mid;
+	drawVert_t	prev, next, mid;
 	float		len, maxLen;
-	int			n;
+	int			dir;
 	int			t;
-	drawVert_t	ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
+	MAC_STATIC drawVert_t	ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
 	float		errorTable[2][MAX_GRID_SIZE];
 
-	memset( &prev, 0, sizeof( prev ) );
-	memset( &next, 0, sizeof( next ) );
-	memset( &mid, 0, sizeof( mid ) );
-
 	for ( i = 0 ; i < width ; i++ ) {
 		for ( j = 0 ; j < height ; j++ ) {
 			ctrl[j][i] = points[j*width+i];
 		}
 	}
 
-	for ( n = 0 ; n < 2 ; n++ ) {
+	for ( dir = 0 ; dir < 2 ; dir++ ) {
 
 		for ( j = 0 ; j < MAX_GRID_SIZE ; j++ ) {
-			errorTable[n][j] = 0;
+			errorTable[dir][j] = 0;
 		}
 
 		// horizontal subdivisions
@@ -418,26 +417,26 @@
 				}
 			}
 
-			maxLen = sqrtf( maxLen );
+			maxLen = sqrt(maxLen);
 
 			// if all the points are on the lines, remove the entire columns
 			if ( maxLen < 0.1f ) {
-				errorTable[n][j+1] = 999;
+				errorTable[dir][j+1] = 999;
 				continue;
 			}
 
 			// see if we want to insert subdivided columns
 			if ( width + 2 > MAX_GRID_SIZE ) {
-				errorTable[n][j+1] = 1.0f/maxLen;
+				errorTable[dir][j+1] = 1.0f/maxLen;
 				continue;	// can't subdivide any more
 			}
 
 			if ( maxLen <= r_subdivisions->value ) {
-				errorTable[n][j+1] = 1.0f/maxLen;
+				errorTable[dir][j+1] = 1.0f/maxLen;
 				continue;	// didn't need subdivision
 			}
 
-			errorTable[n][j+2] = 1.0f/maxLen;
+			errorTable[dir][j+2] = 1.0f/maxLen;
 
 			// insert two columns and replace the peak
 			width += 2;
@@ -466,7 +465,7 @@
 	}
 
 
-	// put all the approximating points on the curve
+	// put all the aproximating points on the curve
 	PutPointsOnCurve( ctrl, width, height );
 
 	// cull out any rows or columns that are colinear
@@ -524,7 +523,7 @@
 srfGridMesh_t *R_GridInsertColumn( srfGridMesh_t *grid, int column, int row, vec3_t point, float loderror ) {
 	int i, j;
 	int width, height, oldwidth;
-	drawVert_t ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
+	MAC_STATIC drawVert_t ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
 	float errorTable[2][MAX_GRID_SIZE];
 	float lodRadius;
 	vec3_t lodOrigin;
@@ -554,7 +553,7 @@
 	for (j = 0; j < grid->height; j++) {
 		errorTable[1][j] = grid->heightLodError[j];
 	}
-	// put all the approximating points on the curve
+	// put all the aproximating points on the curve
 	//PutPointsOnCurve( ctrl, width, height );
 	// calculate normals
 	MakeMeshNormals( width, height, ctrl );
@@ -578,7 +577,7 @@
 srfGridMesh_t *R_GridInsertRow( srfGridMesh_t *grid, int row, int column, vec3_t point, float loderror ) {
 	int i, j;
 	int width, height, oldheight;
-	drawVert_t ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
+	MAC_STATIC drawVert_t ctrl[MAX_GRID_SIZE][MAX_GRID_SIZE];
 	float errorTable[2][MAX_GRID_SIZE];
 	float lodRadius;
 	vec3_t lodOrigin;
@@ -608,7 +607,7 @@
 	for (j = 0; j < grid->width; j++) {
 		errorTable[0][j] = grid->widthLodError[j];
 	}
-	// put all the approximating points on the curve
+	// put all the aproximating points on the curve
 	//PutPointsOnCurve( ctrl, width, height );
 	// calculate normals
 	MakeMeshNormals( width, height, ctrl );

```
