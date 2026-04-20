# Diff: `code/qcommon/cm_polylib.h`
**Canonical:** `wolfcamql-src` (sha256 `1a15997ec5ff...`, 2449 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `f7c0c57f5025...`, 2428 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.h	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_polylib.h	2026-04-16 20:02:19.957606300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `84d0a932ea4e...`, 2249 bytes

_Diff stat: +4 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_polylib.h	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_polylib.h	2026-04-16 20:02:27.299418100 +0100
@@ -44,25 +44,19 @@
 #define	ON_EPSILON	0.1f
 #endif
 
-winding_t	*AllocWinding (int points);
-vec_t	WindingArea (winding_t *w);
 void	WindingCenter (winding_t *w, vec3_t center);
-void	ClipWindingEpsilon (winding_t *in, vec3_t normal, vec_t dist, 
-				vec_t epsilon, winding_t **front, winding_t **back);
 winding_t	*ChopWinding (winding_t *in, vec3_t normal, vec_t dist);
-winding_t	*CopyWinding (winding_t *w);
+winding_t	*CopyWinding (const winding_t *w);
 winding_t	*ReverseWinding (winding_t *w);
 winding_t	*BaseWindingForPlane (vec3_t normal, vec_t dist);
 void	CheckWinding (winding_t *w);
 void	WindingPlane (winding_t *w, vec3_t normal, vec_t *dist);
 void	RemoveColinearPoints (winding_t *w);
-int		WindingOnPlaneSide (winding_t *w, vec3_t normal, vec_t dist);
+int		WindingOnPlaneSide( const winding_t *w, vec3_t normal, vec_t dist );
 void	FreeWinding (winding_t *w);
-void	WindingBounds (winding_t *w, vec3_t mins, vec3_t maxs);
+void	WindingBounds( const winding_t *w, vec3_t mins, vec3_t maxs );
 
 void	AddWindingToConvexHull( winding_t *w, winding_t **hull, vec3_t normal );
 
-void	ChopWindingInPlace (winding_t **w, vec3_t normal, vec_t dist, vec_t epsilon);
+void	ChopWindingInPlace( winding_t **w, const vec3_t normal, vec_t dist, vec_t epsilon );
 // frees the original if clipped
-
-void pw(winding_t *w);

```
