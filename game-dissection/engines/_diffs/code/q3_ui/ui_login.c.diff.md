# Diff: `code/q3_ui/ui_login.c`
**Canonical:** `wolfcamql-src` (sha256 `e5f5ae6fae44...`, 5950 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `2568f4b0ad5f...`, 5929 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_login.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_login.c	2026-04-16 20:02:19.947828300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `7524352b55d3...`, 5963 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_login.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_login.c	2026-04-16 22:48:24.183498100 +0100
@@ -27,7 +27,7 @@
 #include "ui_local.h"
 
 
-#define LOGIN_FRAME		"menu/art/cut_frame"
+#define LOGIN_FRAME		"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_NAME			100
 #define ID_NAME_BOX		101

```
