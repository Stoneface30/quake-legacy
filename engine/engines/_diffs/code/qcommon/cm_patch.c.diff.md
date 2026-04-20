# Diff: `code/qcommon/cm_patch.c`
**Canonical:** `wolfcamql-src` (sha256 `5cb4190c4972...`, 45173 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `9fd50664bb46...`, 45530 bytes

_Diff stat: +95 / -87 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_patch.c	2026-04-16 20:02:19.956607700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -39,6 +39,47 @@
 properly.
 */
 
+/*
+#define	MAX_FACETS			1024
+#define	MAX_PATCH_PLANES	2048
+
+typedef struct {
+	float	plane[4];
+	int		signbits;		// signx + (signy<<1) + (signz<<2), used as lookup during collision
+} patchPlane_t;
+
+typedef struct {
+	int			surfacePlane;
+	int			numBorders;		// 3 or four + 6 axial bevels + 4 or 3 * 4 edge bevels
+	int			borderPlanes[4+6+16];
+	int			borderInward[4+6+16];
+	qboolean	borderNoAdjust[4+6+16];
+} facet_t;
+
+typedef struct patchCollide_s {
+	vec3_t	bounds[2];
+	int		numPlanes;			// surface planes plus edge planes
+	patchPlane_t	*planes;
+	int		numFacets;
+	facet_t	*facets;
+} patchCollide_t;
+
+
+#define	MAX_GRID_SIZE	129
+
+typedef struct {
+	int			width;
+	int			height;
+	qboolean	wrapWidth;
+	qboolean	wrapHeight;
+	vec3_t	points[MAX_GRID_SIZE][MAX_GRID_SIZE];	// [width][height]
+} cGrid_t;
+
+#define	SUBDIVIDE_DISTANCE	16	//4	// never more than this units away from curve
+#define	PLANE_TRI_EPSILON	0.1
+#define	WRAP_POINT_EPSILON	0.1
+*/
+
 int	c_totalPatchBlocks;
 int	c_totalPatchSurfaces;
 int	c_totalPatchEdges;
@@ -377,7 +418,7 @@
 static	patchPlane_t	planes[MAX_PATCH_PLANES];
 
 static	int				numFacets;
-static	facet_t			facets[MAX_FACETS];
+static	facet_t			facets[MAX_PATCH_PLANES]; //maybe MAX_FACETS ??
 
 #define	NORMAL_EPSILON	0.0001
 #define	DIST_EPSILON	0.02
@@ -585,9 +626,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i+1][j];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -595,9 +633,6 @@
 		p1 = grid->points[i][j+1];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p2, p1, up );
 
@@ -605,9 +640,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p2, p1, up );
 
@@ -615,9 +647,6 @@
 		p1 = grid->points[i+1][j];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -625,9 +654,6 @@
 		p1 = grid->points[i+1][j+1];
 		p2 = grid->points[i][j];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -635,9 +661,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -744,7 +767,6 @@
 	w = BaseWindingForPlane( plane,  plane[3] );
 	for ( j = 0 ; j < facet->numBorders && w ; j++ ) {
 		if ( facet->borderPlanes[j] == -1 ) {
-			FreeWinding( w );
 			return qfalse;
 		}
 		Vector4Copy( planes[ facet->borderPlanes[j] ].plane, plane );
@@ -785,7 +807,7 @@
 void CM_AddFacetBevels( facet_t *facet ) {
 
 	int i, j, k, l;
-	int axis, dir, flipped;
+	int axis, dir, order, flipped;
 	float plane[4], d, newplane[4];
 	winding_t *w, *w2;
 	vec3_t mins, maxs, vec, vec2;
@@ -811,9 +833,10 @@
 	WindingBounds(w, mins, maxs);
 
 	// add the axial planes
+	order = 0;
 	for ( axis = 0 ; axis < 3 ; axis++ )
 	{
-		for ( dir = -1 ; dir <= 1 ; dir += 2 )
+		for ( dir = -1 ; dir <= 1 ; dir += 2, order++ )
 		{
 			VectorClear(plane);
 			plane[axis] = dir;
@@ -827,17 +850,14 @@
 			if (CM_PlaneEqual(&planes[facet->surfacePlane], plane, &flipped)) {
 				continue;
 			}
-			// see if the plane is already present
+			// see if the plane is allready present
 			for ( i = 0 ; i < facet->numBorders ; i++ ) {
 				if (CM_PlaneEqual(&planes[facet->borderPlanes[i]], plane, &flipped))
 					break;
 			}
 
 			if ( i == facet->numBorders ) {
-				if ( facet->numBorders >= 4 + 6 + 16 ) {
-					Com_Printf( "ERROR: too many bevels\n" );
-					continue;
-				}
+				if (facet->numBorders > 4 + 6 + 16) Com_Printf("ERROR: too many bevels\n");
 				facet->borderPlanes[facet->numBorders] = CM_FindPlane2(plane, &flipped);
 				facet->borderNoAdjust[facet->numBorders] = 0;
 				facet->borderInward[facet->numBorders] = flipped;
@@ -891,7 +911,7 @@
 				if (CM_PlaneEqual(&planes[facet->surfacePlane], plane, &flipped)) {
 					continue;
 				}
-				// see if the plane is already present
+				// see if the plane is allready present
 				for ( i = 0 ; i < facet->numBorders ; i++ ) {
 					if (CM_PlaneEqual(&planes[facet->borderPlanes[i]], plane, &flipped)) {
 							break;
@@ -899,10 +919,7 @@
 				}
 
 				if ( i == facet->numBorders ) {
-					if ( facet->numBorders >= 4 + 6 + 16 ) {
-						Com_Printf( "ERROR: too many bevels\n" );
-						continue;
-					}
+					if (facet->numBorders > 4 + 6 + 16) Com_Printf("ERROR: too many bevels\n");
 					facet->borderPlanes[facet->numBorders] = CM_FindPlane2(plane, &flipped);
 
 					for ( k = 0 ; k < facet->numBorders ; k++ ) {
@@ -940,10 +957,6 @@
 
 #ifndef BSPC
 	//add opposite plane
-	if ( facet->numBorders >= 4 + 6 + 16 ) {
-		Com_Printf( "ERROR: too many bevels\n" );
-		return;
-	}
 	facet->borderPlanes[facet->numBorders] = facet->surfacePlane;
 	facet->borderNoAdjust[facet->numBorders] = 0;
 	facet->borderInward[facet->numBorders] = qtrue;
@@ -967,7 +980,7 @@
 static void CM_PatchCollideFromGrid( cGrid_t *grid, patchCollide_t *pf ) {
 	int				i, j;
 	float			*p1, *p2, *p3;
-	int				gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2];
+	MAC_STATIC int				gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2];
 	facet_t			*facet;
 	int				borders[4];
 	int				noAdjust[4];
@@ -1064,7 +1077,7 @@
 					numFacets++;
 				}
 			} else {
-				// two separate triangles
+				// two seperate triangles
 				facet->surfacePlane = gridPlanes[i][j][0];
 				facet->numBorders = 3;
 				facet->borderPlanes[0] = borders[EN_TOP];
@@ -1134,12 +1147,12 @@
 */
 struct patchCollide_s	*CM_GeneratePatchCollide( int width, int height, vec3_t *points ) {
 	patchCollide_t	*pf;
-	cGrid_t			grid;
+	MAC_STATIC cGrid_t			grid;
 	int				i, j;
 
 	if ( width <= 2 || height <= 2 || !points ) {
 		Com_Error( ERR_DROP, "CM_GeneratePatchFacets: bad parameters: (%i, %i, %p)",
-			width, height, (void *)points );
+			width, height, points );
 	}
 
 	if ( !(width & 1) || !(height & 1) ) {
@@ -1173,7 +1186,7 @@
 	CM_RemoveDegenerateColumns( &grid );
 
 	// we now have a grid of points exactly on the curve
-	// the approximate surface defined by these points will be
+	// the aproximate surface defined by these points will be
 	// collided against
 	pf = Hunk_Alloc( sizeof( *pf ), h_high );
 	ClearBounds( pf->bounds[0], pf->bounds[1] );
@@ -1219,7 +1232,7 @@
 	qboolean	frontFacing[MAX_PATCH_PLANES];
 	float		intersection[MAX_PATCH_PLANES];
 	float		intersect;
-	const patchPlane_t	*pcPlanes;
+	const patchPlane_t	*planes;
 	const facet_t	*facet;
 	int			i, j, k;
 	float		offset;
@@ -1235,11 +1248,11 @@
 #endif
 
 	// determine the trace's relationship to all planes
-	pcPlanes = pc->planes;
-	for ( i = 0 ; i < pc->numPlanes ; i++, pcPlanes++ ) {
-		offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-		d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-		d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+	planes = pc->planes;
+	for ( i = 0 ; i < pc->numPlanes ; i++, planes++ ) {
+		offset = DotProduct( tw->offsets[ planes->signbits ], planes->plane );
+		d1 = DotProduct( tw->start, planes->plane ) - planes->plane[3] + offset;
+		d2 = DotProduct( tw->end, planes->plane ) - planes->plane[3] + offset;
 		if ( d1 <= 0 ) {
 			frontFacing[i] = qfalse;
 		} else {
@@ -1292,20 +1305,20 @@
 				debugFacet = facet;
 			}
 #endif //BSPC
-			pcPlanes = &pc->planes[facet->surfacePlane];
+			planes = &pc->planes[facet->surfacePlane];
 
 			// calculate intersection with a slight pushoff
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-			d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-			d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+			offset = DotProduct( tw->offsets[ planes->signbits ], planes->plane );
+			d1 = DotProduct( tw->start, planes->plane ) - planes->plane[3] + offset;
+			d2 = DotProduct( tw->end, planes->plane ) - planes->plane[3] + offset;
 			tw->trace.fraction = ( d1 - SURFACE_CLIP_EPSILON ) / ( d1 - d2 );
 
 			if ( tw->trace.fraction < 0 ) {
 				tw->trace.fraction = 0;
 			}
 
-			VectorCopy( pcPlanes->plane,  tw->trace.plane.normal );
-			tw->trace.plane.dist = pcPlanes->plane[3];
+			VectorCopy( planes->plane,  tw->trace.plane.normal );
+			tw->trace.plane.dist = planes->plane[3];
 		}
 	}
 }
@@ -1328,7 +1341,7 @@
 		return qfalse;
 	}
 
-	// if it doesn't cross the plane, the plane isn't relevant
+	// if it doesn't cross the plane, the plane isn't relevent
 	if (d1 <= 0 && d2 <= 0 ) {
 		return qtrue;
 	}
@@ -1364,19 +1377,14 @@
 void CM_TraceThroughPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j, hit, hitnum;
 	float offset, enterFrac, leaveFrac, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *planes;
 	facet_t	*facet;
-	float plane[4] = {0, 0, 0, 0}, bestplane[4] = {0, 0, 0, 0};
+	float plane[4], bestplane[4];
 	vec3_t startp, endp;
 #ifndef BSPC
 	static cvar_t *cv;
 #endif //BSPC
 
-	if ( !CM_BoundsIntersect( tw->bounds[0], tw->bounds[1],
-				pc->bounds[0], pc->bounds[1] ) ) {
-		return;
-	}
-
 	if (tw->isPoint) {
 		CM_TracePointThroughPatchCollide( tw, pc );
 		return;
@@ -1388,11 +1396,11 @@
 		leaveFrac = 1.0;
 		hitnum = -1;
 		//
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		planes = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(planes->plane, plane);
+		plane[3] = planes->plane[3];
 		if ( tw->sphere.use ) {
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			plane[3] += tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -1407,7 +1415,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 			VectorCopy( tw->end, endp );
@@ -1421,17 +1429,17 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			planes = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(planes->plane, plane);
+				plane[3] = -planes->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(planes->plane, plane);
+				plane[3] = planes->plane[3];
 			}
 			if ( tw->sphere.use ) {
-				// adjust the plane distance appropriately for radius
+				// adjust the plane distance apropriately for radius
 				plane[3] += tw->sphere.radius;
 
 				// find the closest point on the capsule to the plane
@@ -1447,7 +1455,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 				VectorCopy( tw->end, endp );
@@ -1505,7 +1513,7 @@
 qboolean CM_PositionTestInPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j;
 	float offset, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *planes;
 	facet_t	*facet;
 	float plane[4];
 	vec3_t startp;
@@ -1516,11 +1524,11 @@
 	//
 	facet = pc->facets;
 	for ( i = 0 ; i < pc->numFacets ; i++, facet++ ) {
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		planes = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(planes->plane, plane);
+		plane[3] = planes->plane[3];
 		if ( tw->sphere.use ) {
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			plane[3] += tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -1533,7 +1541,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 		}
@@ -1543,17 +1551,17 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			planes = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(planes->plane, plane);
+				plane[3] = -planes->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(planes->plane, plane);
+				plane[3] = planes->plane[3];
 			}
 			if ( tw->sphere.use ) {
-				// adjust the plane distance appropriately for radius
+				// adjust the plane distance apropriately for radius
 				plane[3] += tw->sphere.radius;
 
 				// find the closest point on the capsule to the plane
@@ -1567,7 +1575,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 			}

```

### `quake3e`  — sha256 `ef27f070dd88...`, 46293 bytes

_Diff stat: +156 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_patch.c	2026-04-16 20:02:27.298421900 +0100
@@ -39,9 +39,48 @@
 properly.
 */
 
-int	c_totalPatchBlocks;
-int	c_totalPatchSurfaces;
-int	c_totalPatchEdges;
+/*
+#define	MAX_FACETS			1024
+#define	MAX_PATCH_PLANES	2048
+
+typedef struct {
+	float	plane[4];
+	int		signbits;		// signx + (signy<<1) + (signz<<2), used as lookup during collision
+} patchPlane_t;
+
+typedef struct {
+	int			surfacePlane;
+	int			numBorders;		// 3 or four + 6 axial bevels + 4 or 3 * 4 edge bevels
+	int			borderPlanes[4+6+16];
+	int			borderInward[4+6+16];
+	qboolean	borderNoAdjust[4+6+16];
+} facet_t;
+
+typedef struct patchCollide_s {
+	vec3_t	bounds[2];
+	int		numPlanes;			// surface planes plus edge planes
+	patchPlane_t	*planes;
+	int		numFacets;
+	facet_t	*facets;
+} patchCollide_t;
+
+
+#define	MAX_GRID_SIZE	129
+
+typedef struct {
+	int			width;
+	int			height;
+	qboolean	wrapWidth;
+	qboolean	wrapHeight;
+	vec3_t	points[MAX_GRID_SIZE][MAX_GRID_SIZE];	// [width][height]
+} cGrid_t;
+
+#define	SUBDIVIDE_DISTANCE	16	//4	// never more than this units away from curve
+#define	PLANE_TRI_EPSILON	0.1
+#define	WRAP_POINT_EPSILON	0.1
+*/
+
+static int c_totalPatchBlocks;
 
 static const patchCollide_t	*debugPatchCollide;
 static const facet_t		*debugFacet;
@@ -58,12 +97,13 @@
 	debugFacet = NULL;
 }
 
+
 /*
 =================
 CM_SignbitsForNormal
 =================
 */
-static int CM_SignbitsForNormal( vec3_t normal ) {
+static int CM_SignbitsForNormal( const vec3_t normal ) {
 	int	bits, j;
 
 	bits = 0;
@@ -75,25 +115,25 @@
 	return bits;
 }
 
+
 /*
 =====================
 CM_PlaneFromPoints
 
-Returns false if the triangle is degenrate.
+Returns false if the triangle is degenerate.
 The normal will point out of the clock for clockwise ordered points
 =====================
 */
-static qboolean CM_PlaneFromPoints( vec4_t plane, vec3_t a, vec3_t b, vec3_t c ) {
+static qboolean CM_PlaneFromPoints( vec4_t plane, const vec3_t a, const vec3_t b, const vec3_t c ) {
 	vec3_t	d1, d2;
 
 	VectorSubtract( b, a, d1 );
 	VectorSubtract( c, a, d2 );
-	CrossProduct( d2, d1, plane );
-	if ( VectorNormalize( plane ) == 0 ) {
+	CrossProductDP( d2, d1, plane );
+	if ( VectorNormalizeDP( plane ) == 0.0 )
 		return qfalse;
-	}
 
-	plane[3] = DotProduct( a, plane );
+	plane[3] = DotProductDPf( a, plane );
 	return qtrue;
 }
 
@@ -114,7 +154,7 @@
 collision detection purposes
 =================
 */
-static qboolean	CM_NeedsSubdivision( vec3_t a, vec3_t b, vec3_t c ) {
+static qboolean	CM_NeedsSubdivision( const vec3_t a, const vec3_t b, const vec3_t c ) {
 	vec3_t		cmid;
 	vec3_t		lmid;
 	vec3_t		delta;
@@ -134,10 +174,11 @@
 	// see if the curve is far enough away from the linear mid
 	VectorSubtract( cmid, lmid, delta );
 	dist = VectorLength( delta );
-	
+
 	return dist >= SUBDIVIDE_DISTANCE;
 }
 
+
 /*
 ===============
 CM_Subdivide
@@ -146,7 +187,7 @@
 the subdivided sequence will be: a, out1, out2, out3, c
 ===============
 */
-static void CM_Subdivide( vec3_t a, vec3_t b, vec3_t c, vec3_t out1, vec3_t out2, vec3_t out3 ) {
+static void CM_Subdivide( const vec3_t a, const vec3_t b, const vec3_t c, vec3_t out1, vec3_t out2, vec3_t out3 ) {
 	int		i;
 
 	for ( i = 0 ; i < 3 ; i++ ) {
@@ -156,6 +197,7 @@
 	}
 }
 
+
 /*
 =================
 CM_TransposeGrid
@@ -207,6 +249,7 @@
 	grid->wrapHeight = tempWrap;
 }
 
+
 /*
 ===================
 CM_SetGridWrapWidth
@@ -236,12 +279,13 @@
 	}
 }
 
+
 /*
 =================
 CM_SubdivideGridColumns
 
 Adds columns as necessary to the grid until
-all the aproximating points are within SUBDIVIDE_DISTANCE
+all the approximating points are within SUBDIVIDE_DISTANCE
 from the true curve
 =================
 */
@@ -250,11 +294,11 @@
 
 	for ( i = 0 ; i < grid->width - 2 ;  ) {
 		// grid->points[i][x] is an interpolating control point
-		// grid->points[i+1][x] is an aproximating control point
+		// grid->points[i+1][x] is an approximating control point
 		// grid->points[i+2][x] is an interpolating control point
 
 		//
-		// first see if we can collapse the aproximating collumn away
+		// first see if we can collapse the approximating column away
 		//
 		for ( j = 0 ; j < grid->height ; j++ ) {
 			if ( CM_NeedsSubdivision( grid->points[i][j], grid->points[i+1][j], grid->points[i+2][j] ) ) {
@@ -302,18 +346,19 @@
 
 		grid->width += 2;
 
-		// the new aproximating point at i+1 may need to be removed
+		// the new approximating point at i+1 may need to be removed
 		// or subdivided farther, so don't advance i
 	}
 }
 
+
 /*
 ======================
 CM_ComparePoints
 ======================
 */
 #define	POINT_EPSILON	0.1
-static qboolean CM_ComparePoints( float *a, float *b ) {
+static qboolean CM_ComparePoints( const float *a, const float *b ) {
 	float		d;
 
 	d = a[0] - b[0];
@@ -331,6 +376,7 @@
 	return qtrue;
 }
 
+
 /*
 =================
 CM_RemoveDegenerateColumns
@@ -387,7 +433,7 @@
 CM_PlaneEqual
 ==================
 */
-int CM_PlaneEqual(patchPlane_t *p, float plane[4], int *flipped) {
+static qboolean CM_PlaneEqual( const patchPlane_t *p, const float plane[4], int *flipped ) {
 	float invplane[4];
 
 	if (
@@ -416,12 +462,13 @@
 	return qfalse;
 }
 
+
 /*
 ==================
 CM_SnapVector
 ==================
 */
-void CM_SnapVector(vec3_t normal) {
+static void CM_SnapVector( vec3_t normal ) {
 	int		i;
 
 	for (i=0 ; i<3 ; i++)
@@ -441,12 +488,13 @@
 	}
 }
 
+
 /*
 ==================
 CM_FindPlane2
 ==================
 */
-int CM_FindPlane2(float plane[4], int *flipped) {
+static int CM_FindPlane2( const float plane[4], int *flipped ) {
 	int i;
 
 	// see if the points are close enough to an existing plane
@@ -469,12 +517,13 @@
 	return numPlanes-1;
 }
 
+
 /*
 ==================
 CM_FindPlane
 ==================
 */
-static int CM_FindPlane( float *p1, float *p2, float *p3 ) {
+static int CM_FindPlane( const float *p1, const float *p2, const float *p3 ) {
 	float	plane[4];
 	int		i;
 	float	d;
@@ -521,21 +570,22 @@
 	return numPlanes-1;
 }
 
+
 /*
 ==================
 CM_PointOnPlaneSide
 ==================
 */
-static int CM_PointOnPlaneSide( float *p, int planeNum ) {
-	float	*plane;
-	float	d;
+static int CM_PointOnPlaneSide( const float *p, int planeNum ) {
+	const float *plane;
+	double	d;
 
 	if ( planeNum == -1 ) {
 		return SIDE_ON;
 	}
 	plane = planes[ planeNum ].plane;
 
-	d = DotProduct( p, plane ) - plane[3];
+	d = DotProductDPf( p, plane ) - plane[3];
 
 	if ( d > PLANE_TRI_EPSILON ) {
 		return SIDE_FRONT;
@@ -548,6 +598,7 @@
 	return SIDE_ON;
 }
 
+
 /*
 ==================
 CM_GridPlane
@@ -570,13 +621,14 @@
 	return -1;
 }
 
+
 /*
 ==================
 CM_EdgePlaneNum
 ==================
 */
-static int CM_EdgePlaneNum( cGrid_t *grid, int gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2], int i, int j, int k ) {
-	float	*p1, *p2;
+static int CM_EdgePlaneNum( const cGrid_t *grid, int gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2], int i, int j, int k ) {
+	const float *p1, *p2;
 	vec3_t		up;
 	int			p;
 
@@ -647,15 +699,16 @@
 	return -1;
 }
 
+
 /*
 ===================
 CM_SetBorderInward
 ===================
 */
-static void CM_SetBorderInward( facet_t *facet, cGrid_t *grid, int gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2],
+static void CM_SetBorderInward( facet_t *facet, const cGrid_t *grid, int gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2],
 						  int i, int j, int which ) {
 	int		k, l;
-	float	*points[4];
+	const float *points[4];
 	int		numPoints;
 
 	switch ( which ) {
@@ -696,7 +749,7 @@
 			side = CM_PointOnPlaneSide( points[l], facet->borderPlanes[k] );
 			if ( side == SIDE_FRONT ) {
 				front++;
-			} if ( side == SIDE_BACK ) {
+			} else if ( side == SIDE_BACK ) {
 				back++;
 			}
 		}
@@ -723,6 +776,7 @@
 	}
 }
 
+
 /*
 ==================
 CM_ValidateFacet
@@ -730,7 +784,7 @@
 If the facet isn't bounded by its borders, we screwed up.
 ==================
 */
-static qboolean CM_ValidateFacet( facet_t *facet ) {
+static qboolean CM_ValidateFacet( const facet_t *facet ) {
 	float		plane[4];
 	int			j;
 	winding_t	*w;
@@ -762,7 +816,7 @@
 	// see if the facet is unreasonably large
 	WindingBounds( w, bounds[0], bounds[1] );
 	FreeWinding( w );
-	
+
 	for ( j = 0 ; j < 3 ; j++ ) {
 		if ( bounds[1][j] - bounds[0][j] > MAX_MAP_BOUNDS ) {
 			return qfalse;		// we must be missing a plane
@@ -777,18 +831,20 @@
 	return qtrue;		// winding is fine
 }
 
+
 /*
 ==================
 CM_AddFacetBevels
 ==================
 */
-void CM_AddFacetBevels( facet_t *facet ) {
+static void CM_AddFacetBevels( facet_t *facet ) {
 
 	int i, j, k, l;
-	int axis, dir, flipped;
-	float plane[4], d, newplane[4];
+	int axis, dir, order, flipped;
+	float plane[4], newplane[4];
 	winding_t *w, *w2;
 	vec3_t mins, maxs, vec, vec2;
+	double d, d1[3], d2[3];
 
 	Vector4Copy( planes[ facet->surfacePlane ].plane, plane );
 
@@ -811,9 +867,10 @@
 	WindingBounds(w, mins, maxs);
 
 	// add the axial planes
+	order = 0;
 	for ( axis = 0 ; axis < 3 ; axis++ )
 	{
-		for ( dir = -1 ; dir <= 1 ; dir += 2 )
+		for ( dir = -1 ; dir <= 1 ; dir += 2, order++ )
 		{
 			VectorClear(plane);
 			plane[axis] = dir;
@@ -852,9 +909,11 @@
 	for ( j = 0 ; j < w->numpoints ; j++ )
 	{
 		k = (j+1)%w->numpoints;
-		VectorSubtract (w->p[j], w->p[k], vec);
+		VectorCopy( w->p[j], d1 );
+		VectorCopy( w->p[k], d2 );
+		VectorSubtractDP( d1, d2, vec );
 		//if it's a degenerate edge
-		if (VectorNormalize (vec) < 0.5)
+		if ( VectorNormalizeDP( vec ) < 0.5 )
 			continue;
 		CM_SnapVector(vec);
 		for ( k = 0; k < 3 ; k++ )
@@ -869,19 +928,19 @@
 			for ( dir = -1 ; dir <= 1 ; dir += 2 )
 			{
 				// construct a plane
-				VectorClear (vec2);
+				VectorClear(vec2);
 				vec2[axis] = dir;
-				CrossProduct (vec, vec2, plane);
-				if (VectorNormalize (plane) < 0.5)
+				CrossProductDP( vec, vec2, plane );
+				if ( VectorNormalizeDP( plane ) < 0.5 )
 					continue;
-				plane[3] = DotProduct (w->p[j], plane);
+				plane[3] = DotProductDPf( w->p[j], plane );
 
 				// if all the points of the facet winding are
 				// behind this plane, it is a proper edge bevel
 				for ( l = 0 ; l < w->numpoints ; l++ )
 				{
-					d = DotProduct (w->p[l], plane) - plane[3];
-					if (d > 0.1)
+					d = DotProductDPf( w->p[l], plane ) - plane[3];
+					if ( d > 0.1 )
 						break;	// point in front
 				}
 				if ( l < w->numpoints )
@@ -964,13 +1023,13 @@
 CM_PatchCollideFromGrid
 ==================
 */
-static void CM_PatchCollideFromGrid( cGrid_t *grid, patchCollide_t *pf ) {
+static void CM_PatchCollideFromGrid( const cGrid_t *grid, patchCollide_t *pf ) {
 	int				i, j;
-	float			*p1, *p2, *p3;
+	const float		*p1, *p2, *p3;
 	int				gridPlanes[MAX_GRID_SIZE][MAX_GRID_SIZE][2];
 	facet_t			*facet;
 	int				borders[4];
-	int				noAdjust[4];
+	qboolean		noAdjust[4];
 
 	numPlanes = 0;
 	numFacets = 0;
@@ -993,13 +1052,13 @@
 	// create the borders for each facet
 	for ( i = 0 ; i < grid->width - 1 ; i++ ) {
 		for ( j = 0 ; j < grid->height - 1 ; j++ ) {
-			 
+
 			borders[EN_TOP] = -1;
 			if ( j > 0 ) {
 				borders[EN_TOP] = gridPlanes[i][j-1][1];
 			} else if ( grid->wrapHeight ) {
 				borders[EN_TOP] = gridPlanes[i][grid->height-2][1];
-			} 
+			}
 			noAdjust[EN_TOP] = ( borders[EN_TOP] == gridPlanes[i][j][0] );
 			if ( borders[EN_TOP] == -1 || noAdjust[EN_TOP] ) {
 				borders[EN_TOP] = CM_EdgePlaneNum( grid, gridPlanes, i, j, 0 );
@@ -1046,7 +1105,7 @@
 
 			if ( gridPlanes[i][j][0] == gridPlanes[i][j][1] ) {
 				if ( gridPlanes[i][j][0] == -1 ) {
-					continue;		// degenrate
+					continue;		// degenerate
 				}
 				facet->surfacePlane = gridPlanes[i][j][0];
 				facet->numBorders = 4;
@@ -1129,10 +1188,10 @@
 Creates an internal structure that will be used to perform
 collision detection with a patch mesh.
 
-Points is packed as concatenated rows.
+Points are packed as concatenated rows.
 ===================
 */
-struct patchCollide_s	*CM_GeneratePatchCollide( int width, int height, vec3_t *points ) {
+struct patchCollide_s *CM_GeneratePatchCollide( int width, int height, vec3_t *points ) {
 	patchCollide_t	*pf;
 	cGrid_t			grid;
 	int				i, j;
@@ -1215,11 +1274,11 @@
   special case for point traces because the patch collide "brushes" have no volume
 ====================
 */
-void CM_TracePointThroughPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
+static void CM_TracePointThroughPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	qboolean	frontFacing[MAX_PATCH_PLANES];
 	float		intersection[MAX_PATCH_PLANES];
 	float		intersect;
-	const patchPlane_t	*pcPlanes;
+	const patchPlane_t	*pp;
 	const facet_t	*facet;
 	int			i, j, k;
 	float		offset;
@@ -1235,11 +1294,11 @@
 #endif
 
 	// determine the trace's relationship to all planes
-	pcPlanes = pc->planes;
-	for ( i = 0 ; i < pc->numPlanes ; i++, pcPlanes++ ) {
-		offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-		d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-		d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+	pp = pc->planes;
+	for ( i = 0 ; i < pc->numPlanes ; i++, pp++ ) {
+		offset = DotProduct( tw->offsets[ pp->signbits ], pp->plane );
+		d1 = DotProduct( tw->start, pp->plane ) - pp->plane[3] + offset;
+		d2 = DotProduct( tw->end, pp->plane ) - pp->plane[3] + offset;
 		if ( d1 <= 0 ) {
 			frontFacing[i] = qfalse;
 		} else {
@@ -1292,30 +1351,31 @@
 				debugFacet = facet;
 			}
 #endif //BSPC
-			pcPlanes = &pc->planes[facet->surfacePlane];
+			pp = &pc->planes[facet->surfacePlane];
 
 			// calculate intersection with a slight pushoff
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-			d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-			d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+			offset = DotProduct( tw->offsets[ pp->signbits ], pp->plane );
+			d1 = DotProduct( tw->start, pp->plane ) - pp->plane[3] + offset;
+			d2 = DotProduct( tw->end, pp->plane ) - pp->plane[3] + offset;
 			tw->trace.fraction = ( d1 - SURFACE_CLIP_EPSILON ) / ( d1 - d2 );
 
 			if ( tw->trace.fraction < 0 ) {
 				tw->trace.fraction = 0;
 			}
 
-			VectorCopy( pcPlanes->plane,  tw->trace.plane.normal );
-			tw->trace.plane.dist = pcPlanes->plane[3];
+			VectorCopy( pp->plane, tw->trace.plane.normal );
+			tw->trace.plane.dist = pp->plane[3];
 		}
 	}
 }
 
+
 /*
 ====================
 CM_CheckFacetPlane
 ====================
 */
-int CM_CheckFacetPlane(float *plane, vec3_t start, vec3_t end, float *enterFrac, float *leaveFrac, int *hit) {
+static int CM_CheckFacetPlane( const float *plane, const vec3_t start, const vec3_t end, float *enterFrac, float *leaveFrac, int *hit ) {
 	float d1, d2, f;
 
 	*hit = qfalse;
@@ -1356,6 +1416,7 @@
 	return qtrue;
 }
 
+
 /*
 ====================
 CM_TraceThroughPatchCollide
@@ -1364,9 +1425,9 @@
 void CM_TraceThroughPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j, hit, hitnum;
 	float offset, enterFrac, leaveFrac, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *pp;
 	facet_t	*facet;
-	float plane[4] = {0, 0, 0, 0}, bestplane[4] = {0, 0, 0, 0};
+	float plane[4], bestplane[4];
 	vec3_t startp, endp;
 #ifndef BSPC
 	static cvar_t *cv;
@@ -1382,15 +1443,17 @@
 		return;
 	}
 
+	Vector4Set(bestplane, 0, 0, 0, 0);
+
 	facet = pc->facets;
 	for ( i = 0 ; i < pc->numFacets ; i++, facet++ ) {
 		enterFrac = -1.0;
 		leaveFrac = 1.0;
 		hitnum = -1;
 		//
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		pp = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(pp->plane, plane);
+		plane[3] = pp->plane[3];
 		if ( tw->sphere.use ) {
 			// adjust the plane distance appropriately for radius
 			plane[3] += tw->sphere.radius;
@@ -1407,7 +1470,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ pp->signbits ], plane );
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 			VectorCopy( tw->end, endp );
@@ -1421,14 +1484,14 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			pp = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(pp->plane, plane);
+				plane[3] = -pp->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(pp->plane, plane);
+				plane[3] = pp->plane[3];
 			}
 			if ( tw->sphere.use ) {
 				// adjust the plane distance appropriately for radius
@@ -1447,7 +1510,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ pp->signbits ], plane );
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 				VectorCopy( tw->end, endp );
@@ -1467,9 +1530,9 @@
 
 		if (enterFrac < leaveFrac && enterFrac >= 0) {
 			if (enterFrac < tw->trace.fraction) {
-				if (enterFrac < 0) {
-					enterFrac = 0;
-				}
+				//if (enterFrac < 0) {
+				//	enterFrac = 0;
+				//}
 #ifndef BSPC
 				if (!cv) {
 					cv = Cvar_Get( "r_debugSurfaceUpdate", "1", 0 );
@@ -1505,7 +1568,7 @@
 qboolean CM_PositionTestInPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j;
 	float offset, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *pp;
 	facet_t	*facet;
 	float plane[4];
 	vec3_t startp;
@@ -1516,9 +1579,9 @@
 	//
 	facet = pc->facets;
 	for ( i = 0 ; i < pc->numFacets ; i++, facet++ ) {
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		pp = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(pp->plane, plane);
+		plane[3] = pp->plane[3];
 		if ( tw->sphere.use ) {
 			// adjust the plane distance appropriately for radius
 			plane[3] += tw->sphere.radius;
@@ -1533,7 +1596,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ pp->signbits ], plane);
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 		}
@@ -1543,14 +1606,14 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			pp = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(pp->plane, plane);
+				plane[3] = -pp->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(pp->plane, plane);
+				plane[3] = pp->plane[3];
 			}
 			if ( tw->sphere.use ) {
 				// adjust the plane distance appropriately for radius
@@ -1567,7 +1630,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ pp->signbits ], plane);
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 			}

```

### `openarena-engine`  — sha256 `34467b7fdb85...`, 45704 bytes

_Diff stat: +90 / -76 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_patch.c	2026-04-16 22:48:25.904298500 +0100
@@ -39,6 +39,47 @@
 properly.
 */
 
+/*
+#define	MAX_FACETS			1024
+#define	MAX_PATCH_PLANES	2048
+
+typedef struct {
+	float	plane[4];
+	int		signbits;		// signx + (signy<<1) + (signz<<2), used as lookup during collision
+} patchPlane_t;
+
+typedef struct {
+	int			surfacePlane;
+	int			numBorders;		// 3 or four + 6 axial bevels + 4 or 3 * 4 edge bevels
+	int			borderPlanes[4+6+16];
+	int			borderInward[4+6+16];
+	qboolean	borderNoAdjust[4+6+16];
+} facet_t;
+
+typedef struct patchCollide_s {
+	vec3_t	bounds[2];
+	int		numPlanes;			// surface planes plus edge planes
+	patchPlane_t	*planes;
+	int		numFacets;
+	facet_t	*facets;
+} patchCollide_t;
+
+
+#define	MAX_GRID_SIZE	129
+
+typedef struct {
+	int			width;
+	int			height;
+	qboolean	wrapWidth;
+	qboolean	wrapHeight;
+	vec3_t	points[MAX_GRID_SIZE][MAX_GRID_SIZE];	// [width][height]
+} cGrid_t;
+
+#define	SUBDIVIDE_DISTANCE	16	//4	// never more than this units away from curve
+#define	PLANE_TRI_EPSILON	0.1
+#define	WRAP_POINT_EPSILON	0.1
+*/
+
 int	c_totalPatchBlocks;
 int	c_totalPatchSurfaces;
 int	c_totalPatchEdges;
@@ -377,7 +418,7 @@
 static	patchPlane_t	planes[MAX_PATCH_PLANES];
 
 static	int				numFacets;
-static	facet_t			facets[MAX_FACETS];
+static	facet_t			facets[MAX_PATCH_PLANES]; //maybe MAX_FACETS ??
 
 #define	NORMAL_EPSILON	0.0001
 #define	DIST_EPSILON	0.02
@@ -585,9 +626,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i+1][j];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -595,9 +633,6 @@
 		p1 = grid->points[i][j+1];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p2, p1, up );
 
@@ -605,9 +640,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p2, p1, up );
 
@@ -615,9 +647,6 @@
 		p1 = grid->points[i+1][j];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -625,9 +654,6 @@
 		p1 = grid->points[i+1][j+1];
 		p2 = grid->points[i][j];
 		p = CM_GridPlane( gridPlanes, i, j, 0 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -635,9 +661,6 @@
 		p1 = grid->points[i][j];
 		p2 = grid->points[i+1][j+1];
 		p = CM_GridPlane( gridPlanes, i, j, 1 );
-		if ( p == -1 ) {
-			return -1;
-		}
 		VectorMA( p1, 4, planes[ p ].plane, up );
 		return CM_FindPlane( p1, p2, up );
 
@@ -785,7 +808,7 @@
 void CM_AddFacetBevels( facet_t *facet ) {
 
 	int i, j, k, l;
-	int axis, dir, flipped;
+	int axis, dir, order, flipped;
 	float plane[4], d, newplane[4];
 	winding_t *w, *w2;
 	vec3_t mins, maxs, vec, vec2;
@@ -811,9 +834,10 @@
 	WindingBounds(w, mins, maxs);
 
 	// add the axial planes
+	order = 0;
 	for ( axis = 0 ; axis < 3 ; axis++ )
 	{
-		for ( dir = -1 ; dir <= 1 ; dir += 2 )
+		for ( dir = -1 ; dir <= 1 ; dir += 2, order++ )
 		{
 			VectorClear(plane);
 			plane[axis] = dir;
@@ -827,17 +851,14 @@
 			if (CM_PlaneEqual(&planes[facet->surfacePlane], plane, &flipped)) {
 				continue;
 			}
-			// see if the plane is already present
+			// see if the plane is allready present
 			for ( i = 0 ; i < facet->numBorders ; i++ ) {
 				if (CM_PlaneEqual(&planes[facet->borderPlanes[i]], plane, &flipped))
 					break;
 			}
 
 			if ( i == facet->numBorders ) {
-				if ( facet->numBorders >= 4 + 6 + 16 ) {
-					Com_Printf( "ERROR: too many bevels\n" );
-					continue;
-				}
+				if (facet->numBorders > 4 + 6 + 16) Com_Printf("ERROR: too many bevels\n");
 				facet->borderPlanes[facet->numBorders] = CM_FindPlane2(plane, &flipped);
 				facet->borderNoAdjust[facet->numBorders] = 0;
 				facet->borderInward[facet->numBorders] = flipped;
@@ -891,7 +912,7 @@
 				if (CM_PlaneEqual(&planes[facet->surfacePlane], plane, &flipped)) {
 					continue;
 				}
-				// see if the plane is already present
+				// see if the plane is allready present
 				for ( i = 0 ; i < facet->numBorders ; i++ ) {
 					if (CM_PlaneEqual(&planes[facet->borderPlanes[i]], plane, &flipped)) {
 							break;
@@ -899,10 +920,7 @@
 				}
 
 				if ( i == facet->numBorders ) {
-					if ( facet->numBorders >= 4 + 6 + 16 ) {
-						Com_Printf( "ERROR: too many bevels\n" );
-						continue;
-					}
+					if (facet->numBorders > 4 + 6 + 16) Com_Printf("ERROR: too many bevels\n");
 					facet->borderPlanes[facet->numBorders] = CM_FindPlane2(plane, &flipped);
 
 					for ( k = 0 ; k < facet->numBorders ; k++ ) {
@@ -940,10 +958,6 @@
 
 #ifndef BSPC
 	//add opposite plane
-	if ( facet->numBorders >= 4 + 6 + 16 ) {
-		Com_Printf( "ERROR: too many bevels\n" );
-		return;
-	}
 	facet->borderPlanes[facet->numBorders] = facet->surfacePlane;
 	facet->borderNoAdjust[facet->numBorders] = 0;
 	facet->borderInward[facet->numBorders] = qtrue;
@@ -1064,7 +1078,7 @@
 					numFacets++;
 				}
 			} else {
-				// two separate triangles
+				// two seperate triangles
 				facet->surfacePlane = gridPlanes[i][j][0];
 				facet->numBorders = 3;
 				facet->borderPlanes[0] = borders[EN_TOP];
@@ -1173,7 +1187,7 @@
 	CM_RemoveDegenerateColumns( &grid );
 
 	// we now have a grid of points exactly on the curve
-	// the approximate surface defined by these points will be
+	// the aproximate surface defined by these points will be
 	// collided against
 	pf = Hunk_Alloc( sizeof( *pf ), h_high );
 	ClearBounds( pf->bounds[0], pf->bounds[1] );
@@ -1219,7 +1233,7 @@
 	qboolean	frontFacing[MAX_PATCH_PLANES];
 	float		intersection[MAX_PATCH_PLANES];
 	float		intersect;
-	const patchPlane_t	*pcPlanes;
+	const patchPlane_t	*planes;
 	const facet_t	*facet;
 	int			i, j, k;
 	float		offset;
@@ -1235,11 +1249,11 @@
 #endif
 
 	// determine the trace's relationship to all planes
-	pcPlanes = pc->planes;
-	for ( i = 0 ; i < pc->numPlanes ; i++, pcPlanes++ ) {
-		offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-		d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-		d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+	planes = pc->planes;
+	for ( i = 0 ; i < pc->numPlanes ; i++, planes++ ) {
+		offset = DotProduct( tw->offsets[ planes->signbits ], planes->plane );
+		d1 = DotProduct( tw->start, planes->plane ) - planes->plane[3] + offset;
+		d2 = DotProduct( tw->end, planes->plane ) - planes->plane[3] + offset;
 		if ( d1 <= 0 ) {
 			frontFacing[i] = qfalse;
 		} else {
@@ -1292,20 +1306,20 @@
 				debugFacet = facet;
 			}
 #endif //BSPC
-			pcPlanes = &pc->planes[facet->surfacePlane];
+			planes = &pc->planes[facet->surfacePlane];
 
 			// calculate intersection with a slight pushoff
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], pcPlanes->plane );
-			d1 = DotProduct( tw->start, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
-			d2 = DotProduct( tw->end, pcPlanes->plane ) - pcPlanes->plane[3] + offset;
+			offset = DotProduct( tw->offsets[ planes->signbits ], planes->plane );
+			d1 = DotProduct( tw->start, planes->plane ) - planes->plane[3] + offset;
+			d2 = DotProduct( tw->end, planes->plane ) - planes->plane[3] + offset;
 			tw->trace.fraction = ( d1 - SURFACE_CLIP_EPSILON ) / ( d1 - d2 );
 
 			if ( tw->trace.fraction < 0 ) {
 				tw->trace.fraction = 0;
 			}
 
-			VectorCopy( pcPlanes->plane,  tw->trace.plane.normal );
-			tw->trace.plane.dist = pcPlanes->plane[3];
+			VectorCopy( planes->plane,  tw->trace.plane.normal );
+			tw->trace.plane.dist = planes->plane[3];
 		}
 	}
 }
@@ -1328,7 +1342,7 @@
 		return qfalse;
 	}
 
-	// if it doesn't cross the plane, the plane isn't relevant
+	// if it doesn't cross the plane, the plane isn't relevent
 	if (d1 <= 0 && d2 <= 0 ) {
 		return qtrue;
 	}
@@ -1364,7 +1378,7 @@
 void CM_TraceThroughPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j, hit, hitnum;
 	float offset, enterFrac, leaveFrac, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *planes;
 	facet_t	*facet;
 	float plane[4] = {0, 0, 0, 0}, bestplane[4] = {0, 0, 0, 0};
 	vec3_t startp, endp;
@@ -1388,11 +1402,11 @@
 		leaveFrac = 1.0;
 		hitnum = -1;
 		//
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		planes = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(planes->plane, plane);
+		plane[3] = planes->plane[3];
 		if ( tw->sphere.use ) {
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			plane[3] += tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -1407,7 +1421,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 			VectorCopy( tw->end, endp );
@@ -1421,17 +1435,17 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			planes = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(planes->plane, plane);
+				plane[3] = -planes->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(planes->plane, plane);
+				plane[3] = planes->plane[3];
 			}
 			if ( tw->sphere.use ) {
-				// adjust the plane distance appropriately for radius
+				// adjust the plane distance apropriately for radius
 				plane[3] += tw->sphere.radius;
 
 				// find the closest point on the capsule to the plane
@@ -1447,7 +1461,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 				VectorCopy( tw->end, endp );
@@ -1505,7 +1519,7 @@
 qboolean CM_PositionTestInPatchCollide( traceWork_t *tw, const struct patchCollide_s *pc ) {
 	int i, j;
 	float offset, t;
-	patchPlane_t *pcPlanes;
+	patchPlane_t *planes;
 	facet_t	*facet;
 	float plane[4];
 	vec3_t startp;
@@ -1516,11 +1530,11 @@
 	//
 	facet = pc->facets;
 	for ( i = 0 ; i < pc->numFacets ; i++, facet++ ) {
-		pcPlanes = &pc->planes[ facet->surfacePlane ];
-		VectorCopy(pcPlanes->plane, plane);
-		plane[3] = pcPlanes->plane[3];
+		planes = &pc->planes[ facet->surfacePlane ];
+		VectorCopy(planes->plane, plane);
+		plane[3] = planes->plane[3];
 		if ( tw->sphere.use ) {
-			// adjust the plane distance appropriately for radius
+			// adjust the plane distance apropriately for radius
 			plane[3] += tw->sphere.radius;
 
 			// find the closest point on the capsule to the plane
@@ -1533,7 +1547,7 @@
 			}
 		}
 		else {
-			offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+			offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 			plane[3] -= offset;
 			VectorCopy( tw->start, startp );
 		}
@@ -1543,17 +1557,17 @@
 		}
 
 		for ( j = 0; j < facet->numBorders; j++ ) {
-			pcPlanes = &pc->planes[ facet->borderPlanes[j] ];
+			planes = &pc->planes[ facet->borderPlanes[j] ];
 			if (facet->borderInward[j]) {
-				VectorNegate(pcPlanes->plane, plane);
-				plane[3] = -pcPlanes->plane[3];
+				VectorNegate(planes->plane, plane);
+				plane[3] = -planes->plane[3];
 			}
 			else {
-				VectorCopy(pcPlanes->plane, plane);
-				plane[3] = pcPlanes->plane[3];
+				VectorCopy(planes->plane, plane);
+				plane[3] = planes->plane[3];
 			}
 			if ( tw->sphere.use ) {
-				// adjust the plane distance appropriately for radius
+				// adjust the plane distance apropriately for radius
 				plane[3] += tw->sphere.radius;
 
 				// find the closest point on the capsule to the plane
@@ -1567,7 +1581,7 @@
 			}
 			else {
 				// NOTE: this works even though the plane might be flipped because the bbox is centered
-				offset = DotProduct( tw->offsets[ pcPlanes->signbits ], plane);
+				offset = DotProduct( tw->offsets[ planes->signbits ], plane);
 				plane[3] += fabs(offset);
 				VectorCopy( tw->start, startp );
 			}

```
