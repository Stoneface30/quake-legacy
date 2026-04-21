# Diff: `code/q3_ui/ui_display.c`
**Canonical:** `wolfcamql-src` (sha256 `1c4437c9a3ab...`, 9617 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `cc30716e53c6...`, 9596 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_display.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_display.c	2026-04-16 20:02:19.945826100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `99b327956a8b...`, 9669 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_display.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_display.c	2026-04-16 22:48:24.181495000 +0100
@@ -31,10 +31,10 @@
 #include "ui_local.h"
 
 
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
 
 #define ID_GRAPHICS			10
 #define ID_DISPLAY			11

```
