# Diff: `code/qcommon/cm_patch.h`
**Canonical:** `wolfcamql-src` (sha256 `9a505cbd3033...`, 3297 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `0282dd0f6a09...`, 3276 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_patch.h	2026-04-16 20:02:19.957606300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -61,7 +61,7 @@
 
 
 #define	MAX_FACETS			1024
-#define	MAX_PATCH_PLANES	4096
+#define	MAX_PATCH_PLANES	2048
 
 typedef struct {
 	float	plane[4];

```

### `quake3e`  — sha256 `0279251d8302...`, 3303 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\cm_patch.h	2026-04-16 20:02:27.299418100 +0100
@@ -61,7 +61,7 @@
 
 
 #define	MAX_FACETS			1024
-#define	MAX_PATCH_PLANES	4096
+#define	MAX_PATCH_PLANES	(2048+128)
 
 typedef struct {
 	float	plane[4];

```

### `openarena-engine`  — sha256 `1534a82149d3...`, 3297 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_patch.h	2026-04-16 20:02:25.217157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_patch.h	2026-04-16 22:48:25.905297700 +0100
@@ -61,7 +61,7 @@
 
 
 #define	MAX_FACETS			1024
-#define	MAX_PATCH_PLANES	4096
+#define	MAX_PATCH_PLANES	2048
 
 typedef struct {
 	float	plane[4];

```
