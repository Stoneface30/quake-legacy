# Diff: `code/qcommon/cm_local.h`
**Canonical:** `wolfcamql-src` (sha256 `20d11d28a516...`, 5372 bytes)

## Variants

### `quake3-source`  — sha256 `adaeb753988d...`, 5135 bytes

_Diff stat: +2 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_local.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_local.h	2026-04-16 20:02:19.956607700 +0100
@@ -15,12 +15,12 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "q_shared.h"
+#include "../game/q_shared.h"
 #include "qcommon.h"
 #include "cm_polylib.h"
 
@@ -70,7 +70,6 @@
 	int			checkcount;				// to avoid repeated testings
 	int			surfaceFlags;
 	int			contents;
-	//int shaderNum;
 	struct patchCollide_s	*pc;
 } cPatch_t;
 
@@ -186,8 +185,6 @@
 void CM_BoxLeafnums_r( leafList_t *ll, int nodenum );
 
 cmodel_t	*CM_ClipHandleToModel( clipHandle_t handle );
-qboolean CM_BoundsIntersect( const vec3_t mins, const vec3_t maxs, const vec3_t mins2, const vec3_t maxs2 );
-qboolean CM_BoundsIntersectPoint( const vec3_t mins, const vec3_t maxs, const vec3_t point );
 
 // cm_patch.c
 

```

### `openarena-engine`  — sha256 `7a052475b8ec...`, 5353 bytes
Also identical in: ioquake3

_Diff stat: +0 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_local.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_local.h	2026-04-16 22:48:25.904298500 +0100
@@ -70,7 +70,6 @@
 	int			checkcount;				// to avoid repeated testings
 	int			surfaceFlags;
 	int			contents;
-	//int shaderNum;
 	struct patchCollide_s	*pc;
 } cPatch_t;
 

```

### `quake3e`  — sha256 `39c1a6baad66...`, 6692 bytes

_Diff stat: +47 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_local.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_local.h	2026-04-16 20:02:27.298421900 +0100
@@ -29,6 +29,50 @@
 #define CAPSULE_MODEL_HANDLE	254
 
 
+// forced double-precison functions
+#define DotProductDP(x,y)		((double)(x)[0]*(y)[0]+(double)(x)[1]*(y)[1]+(double)(x)[2]*(y)[2])
+#define VectorSubtractDP(a,b,c)	((c)[0]=(double)((a)[0]-(b)[0]),(c)[1]=(double)((a)[1]-(b)[1]),(c)[2]=(double)((a)[2]-(b)[2]))
+#define VectorAddDP(a,b,c)		((c)[0]=(double)((a)[0]+(b)[0]),(c)[1]=(double)((a)[1]+(b)[1]),(c)[2]=(double)((a)[2]+(b)[2]))
+
+
+static ID_INLINE double DotProductDPf( const float *v1, const float *v2 ) {
+	double x[3], y[3];
+	VectorCopy( v1, x );
+	VectorCopy( v2, y );
+	return x[0]*y[0]+x[1]*y[1]+x[2]*y[2];
+}
+
+
+static ID_INLINE void CrossProductDP( const vec3_t v1, const vec3_t v2, vec3_t cross ) {
+	double d1[3], d2[3];
+	VectorCopy( v1, d1 );
+	VectorCopy( v2, d2 );
+	cross[0] = d1[1]*d2[2] - d1[2]*d2[1];
+	cross[1] = d1[2]*d2[0] - d1[0]*d2[2];
+	cross[2] = d1[0]*d2[1] - d1[1]*d2[0];
+}
+
+
+static ID_INLINE vec_t VectorNormalizeDP( vec3_t v ) {
+	double	length, ilength, d[3];
+
+	VectorCopy( v, d );
+	length = d[0]*d[0] + d[1]*d[1] + d[2]*d[2];
+
+	if ( length ) {
+		/* writing it this way allows gcc to recognize that rsqrt can be used */
+		ilength = 1.0/(double)sqrt( length );
+		/* sqrt(length) = length * (1 / sqrt(length)) */
+		length *= ilength;
+		v[0] = d[0] * ilength;
+		v[1] = d[1] * ilength;
+		v[2] = d[2] * ilength;
+	}
+		
+	return length;
+}
+
+
 typedef struct {
 	cplane_t	*plane;
 	int			children[2];		// negative numbers are leafs
@@ -70,7 +114,6 @@
 	int			checkcount;				// to avoid repeated testings
 	int			surfaceFlags;
 	int			contents;
-	//int shaderNum;
 	struct patchCollide_s	*pc;
 } cPatch_t;
 
@@ -113,7 +156,7 @@
 	int			numClusters;
 	int			clusterBytes;
 	byte		*visibility;
-	qboolean	vised;			// if false, visibility is just a single cluster of ffs
+	byte		*novis;		// clusterBytes of 0xff
 
 	int			numEntityChars;
 	char		*entityString;
@@ -127,6 +170,8 @@
 
 	int			floodvalid;
 	int			checkcount;					// incremented on each trace
+
+	unsigned int checksum;
 } clipMap_t;
 
 

```
