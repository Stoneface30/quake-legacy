# Diff: `code/qcommon/cm_polylib.c`
**Canonical:** `wolfcamql-src` (sha256 `df3e7303bd4d...`, 15556 bytes)

## Variants

### `quake3-source`  — sha256 `b1c1cf3a19ad...`, 15479 bytes

_Diff stat: +11 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_polylib.c	2026-04-16 20:02:19.957606300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -27,7 +27,7 @@
 
 
 // counters are only bumped when running single threaded,
-// because they are an awful coherence problem
+// because they are an awefull coherence problem
 int	c_active_windings;
 int	c_peak_windings;
 int	c_winding_allocs;
@@ -272,11 +272,11 @@
 */
 winding_t	*CopyWinding (winding_t *w)
 {
-	intptr_t        size;
+	int			size;
 	winding_t	*c;
 
 	c = AllocWinding (w->numpoints);
-	size = (intptr_t)&(w->p[w->numpoints]) - (intptr_t)w;
+	size = (int)((winding_t *)0)->p[w->numpoints];
 	Com_Memcpy (c, w, size);
 	return c;
 }
@@ -309,8 +309,8 @@
 void	ClipWindingEpsilon (winding_t *in, vec3_t normal, vec_t dist, 
 				vec_t epsilon, winding_t **front, winding_t **back)
 {
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4];
+	int		sides[MAX_POINTS_ON_WINDING+4];
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;
@@ -353,7 +353,7 @@
 		return;
 	}
 
-	maxpts = in->numpoints+4;	// can't use counts[0]+2 because
+	maxpts = in->numpoints+4;	// cant use counts[0]+2 because
 								// of fp grouping errors
 
 	*front = f = AllocWinding (maxpts);
@@ -421,8 +421,8 @@
 void ChopWindingInPlace (winding_t **inout, vec3_t normal, vec_t dist, vec_t epsilon)
 {
 	winding_t	*in;
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4];
+	int		sides[MAX_POINTS_ON_WINDING+4];
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;
@@ -462,7 +462,7 @@
 	if (!counts[1])
 		return;		// inout stays the same
 
-	maxpts = in->numpoints+4;	// can't use counts[0]+2 because
+	maxpts = in->numpoints+4;	// cant use counts[0]+2 because
 								// of fp grouping errors
 
 	f = AllocWinding (maxpts);
@@ -574,7 +574,7 @@
 		if (d < -ON_EPSILON || d > ON_EPSILON)
 			Com_Error (ERR_DROP, "CheckWinding: point off plane");
 	
-	// check the edge isn't degenerate
+	// check the edge isnt degenerate
 		p2 = w->p[j];
 		VectorSubtract (p2, p1, dir);
 		

```

### `ioquake3`  — sha256 `5db1b37e1768...`, 15543 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\cm_polylib.c	2026-04-16 20:02:21.564152500 +0100
@@ -272,7 +272,7 @@
 */
 winding_t	*CopyWinding (winding_t *w)
 {
-	intptr_t        size;
+	intptr_t	size;
 	winding_t	*c;
 
 	c = AllocWinding (w->numpoints);
@@ -309,8 +309,8 @@
 void	ClipWindingEpsilon (winding_t *in, vec3_t normal, vec_t dist, 
 				vec_t epsilon, winding_t **front, winding_t **back)
 {
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4] = { 0 };
+	int		sides[MAX_POINTS_ON_WINDING+4] = { 0 };
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;
@@ -421,8 +421,8 @@
 void ChopWindingInPlace (winding_t **inout, vec3_t normal, vec_t dist, vec_t epsilon)
 {
 	winding_t	*in;
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4] = { 0 };
+	int		sides[MAX_POINTS_ON_WINDING+4] = { 0 };
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;

```

### `quake3e`  — sha256 `3821c67f892b...`, 15950 bytes

_Diff stat: +89 / -73 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_polylib.c	2026-04-16 20:02:27.299418100 +0100
@@ -28,17 +28,19 @@
 
 // counters are only bumped when running single threaded,
 // because they are an awful coherence problem
-int	c_active_windings;
-int	c_peak_windings;
-int	c_winding_allocs;
-int	c_winding_points;
-
-void pw(winding_t *w)
-{
-	int		i;
-	for (i=0 ; i<w->numpoints ; i++)
-		printf ("(%5.1f, %5.1f, %5.1f)\n",w->p[i][0], w->p[i][1],w->p[i][2]);
+static int c_active_windings;
+static int c_peak_windings;
+static int c_winding_allocs;
+static int c_winding_points;
+
+#if 0
+static void pw(winding_t *w)
+{
+	int	i;
+	for ( i = 0 ; i < w->numpoints ; i++ )
+		Com_Printf( "%f, %f, %f\n", w->p[i][0], w->p[i][1], w->p[i][2] );
 }
+#endif
 
 
 /*
@@ -46,23 +48,24 @@
 AllocWinding
 =============
 */
-winding_t	*AllocWinding (int points)
+static winding_t *AllocWinding( int points )
 {
 	winding_t	*w;
-	int			s;
+	size_t		s;
 
 	c_winding_allocs++;
 	c_winding_points += points;
 	c_active_windings++;
-	if (c_active_windings > c_peak_windings)
+	if ( c_active_windings > c_peak_windings )
 		c_peak_windings = c_active_windings;
 
-	s = sizeof(vec_t)*3*points + sizeof(int);
-	w = Z_Malloc (s);
-	Com_Memset (w, 0, s); 
+	s = sizeof( *w ) - sizeof( w->p ) + sizeof( w->p[0] ) * points;
+	w = Z_Malloc( s );
+	Com_Memset( w, 0, s );
 	return w;
 }
 
+
 void FreeWinding (winding_t *w)
 {
 	if (*(unsigned *)w == 0xdeaddead)
@@ -78,7 +81,7 @@
 RemoveColinearPoints
 ============
 */
-int	c_removed;
+//static int c_removed;
 
 void	RemoveColinearPoints (winding_t *w)
 {
@@ -106,7 +109,8 @@
 	if (nump == w->numpoints)
 		return;
 
-	c_removed += w->numpoints - nump;
+	//c_removed += w->numpoints - nump;
+
 	w->numpoints = nump;
 	Com_Memcpy (w->p, p, nump*sizeof(p[0]));
 }
@@ -133,7 +137,7 @@
 WindingArea
 =============
 */
-vec_t	WindingArea (winding_t *w)
+static vec_t WindingArea( winding_t *w )
 {
 	int		i;
 	vec3_t	d1, d2, cross;
@@ -150,12 +154,13 @@
 	return total;
 }
 
+
 /*
 =============
 WindingBounds
 =============
 */
-void	WindingBounds (winding_t *w, vec3_t mins, vec3_t maxs)
+void WindingBounds( const winding_t *w, vec3_t mins, vec3_t maxs )
 {
 	vec_t	v;
 	int		i,j;
@@ -205,42 +210,43 @@
 	vec_t	max, v;
 	vec3_t	org, vright, vup;
 	winding_t	*w;
+	double	dot;
 	
-// find the major axis
-
+	// find the major axis
 	max = -MAX_MAP_BOUNDS;
 	x = -1;
 	for (i=0 ; i<3; i++)
 	{
-		v = fabs(normal[i]);
+		v = fabsf( normal[i] );
 		if (v > max)
 		{
 			x = i;
 			max = v;
 		}
 	}
-	if (x==-1)
-		Com_Error (ERR_DROP, "BaseWindingForPlane: no axis found");
+
+	if ( x < 0 )
+		Com_Error( ERR_DROP, "BaseWindingForPlane: no axis found" );
 		
-	VectorCopy (vec3_origin, vup);	
+	VectorCopy (vec3_origin, vup);
 	switch (x)
 	{
 	case 0:
 	case 1:
 		vup[2] = 1;
-		break;		
+		break;
 	case 2:
 		vup[0] = 1;
-		break;		
+		break;
 	}
 
-	v = DotProduct (vup, normal);
-	VectorMA (vup, -v, normal, vup);
-	VectorNormalize2(vup, vup);
+	dot = DotProductDP( vup, normal );
+	VectorMA( vup, -dot, normal, vup );
+	VectorNormalizeDP( vup );
 		
 	VectorScale (normal, dist, org);
 	
-	CrossProduct (vup, normal, vright);
+	CrossProductDP( vup, normal, vright );
 	
 	VectorScale (vup, MAX_MAP_BOUNDS, vup);
 	VectorScale (vright, MAX_MAP_BOUNDS, vright);
@@ -261,23 +267,24 @@
 	VectorSubtract (w->p[3], vup, w->p[3]);
 	
 	w->numpoints = 4;
-	
-	return w;	
+
+	return w;
 }
 
+
 /*
 ==================
 CopyWinding
 ==================
 */
-winding_t	*CopyWinding (winding_t *w)
+winding_t *CopyWinding( const winding_t *w )
 {
-	intptr_t        size;
+	size_t		size;
 	winding_t	*c;
 
-	c = AllocWinding (w->numpoints);
-	size = (intptr_t)&(w->p[w->numpoints]) - (intptr_t)w;
-	Com_Memcpy (c, w, size);
+	c = AllocWinding( w->numpoints );
+	size = sizeof( *w ) - sizeof( w->p ) + sizeof( w->p[0] )* w->numpoints;
+	Com_Memcpy( c, w, size );
 	return c;
 }
 
@@ -306,26 +313,28 @@
 ClipWindingEpsilon
 =============
 */
-void	ClipWindingEpsilon (winding_t *in, vec3_t normal, vec_t dist, 
-				vec_t epsilon, winding_t **front, winding_t **back)
+static void ClipWindingEpsilon( winding_t *in, vec3_t normal, vec_t dist, vec_t epsilon, winding_t **front, winding_t **back )
 {
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4];
+	int		sides[MAX_POINTS_ON_WINDING+4];
 	int		counts[3];
-	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
+	double	dot;
 	int		i, j;
 	vec_t	*p1, *p2;
+	double	d1, d2;
 	vec3_t	mid;
 	winding_t	*f, *b;
 	int		maxpts;
 	
 	counts[0] = counts[1] = counts[2] = 0;
+	Com_Memset( dists, 0, sizeof( dists ) );
+	Com_Memset( sides, 0, sizeof( sides ) );
 
-// determine sides for each point
+	// determine sides for each point
 	for (i=0 ; i<in->numpoints ; i++)
 	{
-		dot = DotProduct (in->p[i], normal);
-		dot -= dist;
+		dot = DotProductDPf( in->p[i], normal ) - dist;
+		//dot -= dist;
 		dists[i] = dot;
 		if (dot > epsilon)
 			sides[i] = SIDE_FRONT;
@@ -386,18 +395,20 @@
 		if (sides[i+1] == SIDE_ON || sides[i+1] == sides[i])
 			continue;
 			
-	// generate a split point
+		// generate a split point
 		p2 = in->p[(i+1)%in->numpoints];
-		
-		dot = dists[i] / (dists[i]-dists[i+1]);
+		d1 = dists[i]; d2 = dists[i+1];
+		dot = d1 / ( d1 - d2 );
 		for (j=0 ; j<3 ; j++)
 		{	// avoid round off error when possible
-			if (normal[j] == 1)
+			if (normal[j] == 1.0)
 				mid[j] = dist;
-			else if (normal[j] == -1)
+			else if (normal[j] == -1.0)
 				mid[j] = -dist;
-			else
-				mid[j] = p1[j] + dot*(p2[j]-p1[j]);
+			else {
+				d1 = p1[j]; d2 = p2[j];
+				mid[j] = d1 + dot * ( d2 - d1 );
+			}
 		}
 			
 		VectorCopy (mid, f->p[f->numpoints]);
@@ -418,13 +429,14 @@
 ChopWindingInPlace
 =============
 */
-void ChopWindingInPlace (winding_t **inout, vec3_t normal, vec_t dist, vec_t epsilon)
+void ChopWindingInPlace( winding_t **inout, const vec3_t normal, vec_t dist, vec_t epsilon )
 {
 	winding_t	*in;
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4];
+	int		sides[MAX_POINTS_ON_WINDING+4];
 	int		counts[3];
-	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
+	double	d1, d2;
+	double	dot;
 	int		i, j;
 	vec_t	*p1, *p2;
 	vec3_t	mid;
@@ -433,12 +445,14 @@
 
 	in = *inout;
 	counts[0] = counts[1] = counts[2] = 0;
+	Com_Memset( dists, 0, sizeof( dists ) );
+	Com_Memset( sides, 0, sizeof( sides ) );
 
-// determine sides for each point
+	// determine sides for each point
 	for (i=0 ; i<in->numpoints ; i++)
 	{
-		dot = DotProduct (in->p[i], normal);
-		dot -= dist;
+		dot = DotProductDPf( in->p[i], normal ) - dist;
+		//dot -= dist;
 		dists[i] = dot;
 		if (dot > epsilon)
 			sides[i] = SIDE_FRONT;
@@ -487,18 +501,22 @@
 		if (sides[i+1] == SIDE_ON || sides[i+1] == sides[i])
 			continue;
 			
-	// generate a split point
+		// generate a split point
 		p2 = in->p[(i+1)%in->numpoints];
-		
-		dot = dists[i] / (dists[i]-dists[i+1]);
+		d1 = dists[i];
+		d2 = dists[i+1];
+		dot = d1 / ( d1 - d2 );
+
 		for (j=0 ; j<3 ; j++)
 		{	// avoid round off error when possible
-			if (normal[j] == 1)
+			if (normal[j] == 1.0)
 				mid[j] = dist;
-			else if (normal[j] == -1)
+			else if (normal[j] == -1.0)
 				mid[j] = -dist;
-			else
-				mid[j] = p1[j] + dot*(p2[j]-p1[j]);
+			else {
+				d1 = p1[j]; d2 = p2[j];
+				mid[j] = d1 + dot * ( d2 - d1 );
+			}
 		}
 			
 		VectorCopy (mid, f->p[f->numpoints]);
@@ -520,7 +538,7 @@
 ChopWinding
 
 Returns the fragment of in that is on the front side
-of the cliping plane.  The original is freed.
+of the clipping plane.  The original is freed.
 =================
 */
 winding_t	*ChopWinding (winding_t *in, vec3_t normal, vec_t dist)
@@ -574,7 +592,7 @@
 		if (d < -ON_EPSILON || d > ON_EPSILON)
 			Com_Error (ERR_DROP, "CheckWinding: point off plane");
 	
-	// check the edge isn't degenerate
+	// check the edge is not degenerate
 		p2 = w->p[j];
 		VectorSubtract (p2, p1, dir);
 		
@@ -604,7 +622,7 @@
 WindingOnPlaneSide
 ============
 */
-int		WindingOnPlaneSide (winding_t *w, vec3_t normal, vec_t dist)
+int WindingOnPlaneSide( const winding_t *w, vec3_t normal, vec_t dist )
 {
 	qboolean	front, back;
 	int			i;
@@ -733,5 +751,3 @@
 	*hull = w;
 	Com_Memcpy( w->p, hullPoints, numHullPoints * sizeof(vec3_t) );
 }
-
-

```

### `openarena-engine`  — sha256 `7103892cc09e...`, 15539 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.c	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_polylib.c	2026-04-16 22:48:25.905297700 +0100
@@ -272,11 +272,11 @@
 */
 winding_t	*CopyWinding (winding_t *w)
 {
-	intptr_t        size;
+	intptr_t	size;
 	winding_t	*c;
 
 	c = AllocWinding (w->numpoints);
-	size = (intptr_t)&(w->p[w->numpoints]) - (intptr_t)w;
+	size = (intptr_t) ((winding_t *)0)->p[w->numpoints];
 	Com_Memcpy (c, w, size);
 	return c;
 }
@@ -309,8 +309,8 @@
 void	ClipWindingEpsilon (winding_t *in, vec3_t normal, vec_t dist, 
 				vec_t epsilon, winding_t **front, winding_t **back)
 {
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4] = { 0 };
+	int		sides[MAX_POINTS_ON_WINDING+4] = { 0 };
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;
@@ -353,7 +353,7 @@
 		return;
 	}
 
-	maxpts = in->numpoints+4;	// can't use counts[0]+2 because
+	maxpts = in->numpoints+4;	// cant use counts[0]+2 because
 								// of fp grouping errors
 
 	*front = f = AllocWinding (maxpts);
@@ -421,8 +421,8 @@
 void ChopWindingInPlace (winding_t **inout, vec3_t normal, vec_t dist, vec_t epsilon)
 {
 	winding_t	*in;
-	vec_t  dists[MAX_POINTS_ON_WINDING+4] = { 0 };
-	int    sides[MAX_POINTS_ON_WINDING+4] = { 0 };
+	vec_t	dists[MAX_POINTS_ON_WINDING+4] = { 0 };
+	int		sides[MAX_POINTS_ON_WINDING+4] = { 0 };
 	int		counts[3];
 	static	vec_t	dot;		// VC 4.2 optimizer bug if not static
 	int		i, j;
@@ -462,7 +462,7 @@
 	if (!counts[1])
 		return;		// inout stays the same
 
-	maxpts = in->numpoints+4;	// can't use counts[0]+2 because
+	maxpts = in->numpoints+4;	// cant use counts[0]+2 because
 								// of fp grouping errors
 
 	f = AllocWinding (maxpts);
@@ -574,7 +574,7 @@
 		if (d < -ON_EPSILON || d > ON_EPSILON)
 			Com_Error (ERR_DROP, "CheckWinding: point off plane");
 	
-	// check the edge isn't degenerate
+	// check the edge isnt degenerate
 		p2 = w->p[j];
 		VectorSubtract (p2, p1, dir);
 		

```
