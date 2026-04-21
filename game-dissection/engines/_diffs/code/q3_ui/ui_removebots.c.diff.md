# Diff: `code/q3_ui/ui_removebots.c`
**Canonical:** `wolfcamql-src` (sha256 `5bff32f79ebb...`, 10716 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `4b59c5bba730...`, 10695 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_removebots.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_removebots.c	2026-04-16 20:02:19.951678800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `22354e12f0c8...`, 10819 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_removebots.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_removebots.c	2026-04-16 22:48:24.186499300 +0100
@@ -32,14 +32,14 @@
 #include "ui_local.h"
 
 
-#define ART_BACKGROUND		"menu/art/addbotframe"
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"	
-#define ART_DELETE0			"menu/art/delete_0"
-#define ART_DELETE1			"menu/art/delete_1"
-#define ART_ARROWS			"menu/art/arrows_vert_0"
-#define ART_ARROWUP			"menu/art/arrows_vert_top"
-#define ART_ARROWDOWN		"menu/art/arrows_vert_bot"
+#define ART_BACKGROUND		"menu/" MENU_ART_DIR "/addbotframe"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_DELETE0			"menu/" MENU_ART_DIR "/delete_0"
+#define ART_DELETE1			"menu/" MENU_ART_DIR "/delete_1"
+#define ART_ARROWS			"menu/" MENU_ART_DIR "/arrows_vert_0"
+#define ART_ARROWUP			"menu/" MENU_ART_DIR "/arrows_vert_top"
+#define ART_ARROWDOWN		"menu/" MENU_ART_DIR "/arrows_vert_bot"
 
 #define ID_UP				10
 #define ID_DOWN				11

```
