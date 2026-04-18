# Diff: `code/qcommon/cm_public.h`
**Canonical:** `wolfcamql-src` (sha256 `322769bc1938...`, 2731 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `a3c0839d5b9e...`, 3057 bytes

_Diff stat: +10 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_public.h	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_public.h	2026-04-16 20:02:19.957606300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -63,5 +63,14 @@
 
 int			CM_WriteAreaBits( byte *buffer, int area );
 
+// cm_tag.c
+int			CM_LerpTag( orientation_t *tag,  clipHandle_t model, int startFrame, int endFrame, 
+					 float frac, const char *tagName );
+
+
+// cm_marks.c
+int	CM_MarkFragments( int numPoints, const vec3_t *points, const vec3_t projection,
+				   int maxPoints, vec3_t pointBuffer, int maxFragments, markFragment_t *fragmentBuffer );
+
 // cm_patch.c
 void CM_DrawDebugSurface( void (*drawPoly)(int color, int numPoints, float *points) );

```

### `quake3e`  — sha256 `4ab449199a6b...`, 2754 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_public.h	2026-04-16 20:02:25.218162200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_public.h	2026-04-16 20:02:27.300418600 +0100
@@ -38,13 +38,13 @@
 int			CM_PointContents( const vec3_t p, clipHandle_t model );
 int			CM_TransformedPointContents( const vec3_t p, clipHandle_t model, const vec3_t origin, const vec3_t angles );
 
-void		CM_BoxTrace ( trace_t *results, const vec3_t start, const vec3_t end,
-						  vec3_t mins, vec3_t maxs,
-						  clipHandle_t model, int brushmask, int capsule );
+void		CM_BoxTrace( trace_t *results, const vec3_t start, const vec3_t end,
+						const vec3_t mins, const vec3_t maxs,
+						clipHandle_t model, int brushmask, qboolean capsule );
 void		CM_TransformedBoxTrace( trace_t *results, const vec3_t start, const vec3_t end,
-						  vec3_t mins, vec3_t maxs,
-						  clipHandle_t model, int brushmask,
-						  const vec3_t origin, const vec3_t angles, int capsule );
+						const vec3_t mins, const vec3_t maxs,
+						clipHandle_t model, int brushmask,
+						const vec3_t origin, const vec3_t angles, qboolean capsule );
 
 byte		*CM_ClusterPVS (int cluster);
 

```
