# Diff: `code/botlib/l_utils.h`
**Canonical:** `wolfcamql-src` (sha256 `06adcb4a313a...`, 1380 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `e8689dfd6417...`, 1390 bytes

_Diff stat: +2 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_utils.h	2026-04-16 20:02:25.131994300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_utils.h	2026-04-16 20:02:19.858903200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,5 +30,6 @@
  *****************************************************************************/
 
 #define Vector2Angles(v,a)		vectoangles(v,a)
+#define MAX_PATH				MAX_QPATH
 #define Maximum(x,y)			(x > y ? x : y)
 #define Minimum(x,y)			(x < y ? x : y)

```

### `quake3e`  — sha256 `b9887cccd636...`, 1437 bytes
Also identical in: openarena-engine, openarena-gamecode

_Diff stat: +3 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_utils.h	2026-04-16 20:02:25.131994300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_utils.h	2026-04-16 20:02:26.907505100 +0100
@@ -30,5 +30,8 @@
  *****************************************************************************/
 
 #define Vector2Angles(v,a)		vectoangles(v,a)
+#ifndef MAX_PATH
+#define MAX_PATH				MAX_QPATH
+#endif
 #define Maximum(x,y)			(x > y ? x : y)
 #define Minimum(x,y)			(x < y ? x : y)

```
