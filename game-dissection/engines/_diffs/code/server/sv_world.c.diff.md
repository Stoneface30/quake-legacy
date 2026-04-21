# Diff: `code/server/sv_world.c`
**Canonical:** `wolfcamql-src` (sha256 `523ca58ec87f...`, 17256 bytes)

## Variants

### `quake3-source`  — sha256 `d67f952c3749...`, 17250 bytes

_Diff stat: +11 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_world.c	2026-04-16 20:02:25.271784400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_world.c	2026-04-16 20:02:19.979632700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -103,7 +103,7 @@
 Builds a uniformly subdivided tree for the given world size
 ===============
 */
-static worldSector_t *SV_CreateworldSector( int depth, vec3_t mins, vec3_t maxs ) {
+worldSector_t *SV_CreateworldSector( int depth, vec3_t mins, vec3_t maxs ) {
 	worldSector_t	*anode;
 	vec3_t		size;
 	vec3_t		mins1, maxs1, mins2, maxs2;
@@ -257,6 +257,7 @@
 	if ( gEnt->r.bmodel && (angles[0] || angles[1] || angles[2]) ) {
 		// expand for rotation
 		float		max;
+		int			i;
 
 		max = RadiusFromBounds( gEnt->r.mins, gEnt->r.maxs );
 		for (i=0 ; i<3 ; i++) {
@@ -378,9 +379,12 @@
 
 ====================
 */
-static void SV_AreaEntities_r( worldSector_t *node, areaParms_t *ap ) {
+void SV_AreaEntities_r( worldSector_t *node, areaParms_t *ap ) {
 	svEntity_t	*check, *next;
 	sharedEntity_t *gcheck;
+	int			count;
+
+	count = 0;
 
 	for ( check = node->entities  ; check ; check = next ) {
 		next = check->nextEntityInWorldSector;
@@ -404,7 +408,7 @@
 		ap->list[ap->count] = check - sv.svEntities;
 		ap->count++;
 	}
-
+	
 	if (node->axis == -1) {
 		return;		// terminal node
 	}
@@ -503,7 +507,7 @@
 
 ====================
 */
-static void SV_ClipMoveToEntities( moveclip_t *clip ) {
+void SV_ClipMoveToEntities( moveclip_t *clip ) {
 	int			i, num;
 	int			touchlist[MAX_GENTITIES];
 	sharedEntity_t *touch;
@@ -671,12 +675,12 @@
 		hit = SV_GentityNum( touch[i] );
 		// might intersect, so do an exact clip
 		clipHandle = SV_ClipHandleForEntity( hit );
-		angles = hit->r.currentAngles;
+		angles = hit->s.angles;
 		if ( !hit->r.bmodel ) {
 			angles = vec3_origin;	// boxes don't rotate
 		}
 
-		c2 = CM_TransformedPointContents (p, clipHandle, hit->r.currentOrigin, angles);
+		c2 = CM_TransformedPointContents (p, clipHandle, hit->s.origin, hit->s.angles);
 
 		contents |= c2;
 	}

```

### `openarena-engine`  — sha256 `d04aaffcd843...`, 17257 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_world.c	2026-04-16 20:02:25.271784400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_world.c	2026-04-16 22:48:25.938962600 +0100
@@ -404,7 +404,7 @@
 		ap->list[ap->count] = check - sv.svEntities;
 		ap->count++;
 	}
-
+	
 	if (node->axis == -1) {
 		return;		// terminal node
 	}

```

### `quake3e`  — sha256 `29b007f6735e...`, 17421 bytes

_Diff stat: +19 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_world.c	2026-04-16 20:02:25.271784400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\server\sv_world.c	2026-04-16 20:02:27.370076300 +0100
@@ -71,8 +71,8 @@
 #define	AREA_DEPTH	4
 #define	AREA_NODES	64
 
-worldSector_t	sv_worldSectors[AREA_NODES];
-int			sv_numworldSectors;
+static worldSector_t	sv_worldSectors[AREA_NODES];
+static int			sv_numworldSectors;
 
 
 /*
@@ -223,14 +223,14 @@
 	if ( gEnt->r.bmodel ) {
 		gEnt->s.solid = SOLID_BMODEL;		// a solid_box will never create this value
 	} else if ( gEnt->r.contents & ( CONTENTS_SOLID | CONTENTS_BODY ) ) {
-		// assume that x/y are equal and symetric
+		// assume that x/y are equal and symmetric
 		i = gEnt->r.maxs[0];
 		if (i<1)
 			i = 1;
 		if (i>255)
 			i = 255;
 
-		// z is not symetric
+		// z is not symmetric
 		j = (-gEnt->r.mins[2]);
 		if (j<1)
 			j = 1;
@@ -299,7 +299,7 @@
 		area = CM_LeafArea (leafs[i]);
 		if (area != -1) {
 			// doors may legally straggle two areas,
-			// but nothing should evern need more than that
+			// but nothing should ever need more than that
 			if (ent->areanum != -1 && ent->areanum != area) {
 				if (ent->areanum2 != -1 && ent->areanum2 != area && sv.state == SS_LOADING) {
 					Com_DPrintf ("Object %i touching 3 areas at %f %f %f\n",
@@ -404,7 +404,7 @@
 		ap->list[ap->count] = check - sv.svEntities;
 		ap->count++;
 	}
-
+	
 	if (node->axis == -1) {
 		return;		// terminal node
 	}
@@ -461,14 +461,15 @@
 
 ====================
 */
-void SV_ClipToEntity( trace_t *trace, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int entityNum, int contentmask, int capsule ) {
+void SV_ClipToEntity( trace_t *trace, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int entityNum, int contentmask, qboolean capsule ) {
 	sharedEntity_t	*touch;
 	clipHandle_t	clipHandle;
-	float			*origin, *angles;
+	float			*origin;
+	const float *angles;
 
 	touch = SV_GentityNum( entityNum );
 
-	Com_Memset(trace, 0, sizeof(trace_t));
+	Com_Memset( trace, 0, sizeof( *trace ) );
 
 	// if it doesn't have any brushes of a type we
 	// are looking for, ignore it
@@ -510,7 +511,8 @@
 	int			passOwnerNum;
 	trace_t		trace;
 	clipHandle_t	clipHandle;
-	float		*origin, *angles;
+	float		*origin;
+	const float *angles;
 
 	num = SV_AreaEntities( clip->boxmins, clip->boxmaxs, touchlist, MAX_GENTITIES);
 
@@ -593,7 +595,7 @@
 passEntityNum and entities owned by passEntityNum are explicitly not checked.
 ==================
 */
-void SV_Trace( trace_t *results, const vec3_t start, vec3_t mins, vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask, int capsule ) {
+void SV_Trace( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask, qboolean capsule ) {
 	moveclip_t	clip;
 	int			i;
 
@@ -604,7 +606,11 @@
 		maxs = vec3_origin;
 	}
 
-	Com_Memset ( &clip, 0, sizeof ( moveclip_t ) );
+	Com_Memset ( &clip, 0, sizeof ( clip ) );
+
+	if ( (unsigned)passEntityNum > MAX_GENTITIES - 1 ) {
+		passEntityNum = ENTITYNUM_NONE;
+	}
 
 	// clip to world
 	CM_BoxTrace( &clip.trace, start, end, mins, maxs, 0, contentmask, capsule );
@@ -656,7 +662,7 @@
 	int			i, num;
 	int			contents, c2;
 	clipHandle_t	clipHandle;
-	float		*angles;
+	const float		*angles;
 
 	// get base contents from world
 	contents = CM_PointContents( p, 0 );

```
