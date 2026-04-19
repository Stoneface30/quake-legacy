# Diff: `code/q3_ui/ui_spskill.c`
**Canonical:** `wolfcamql-src` (sha256 `252a81043adc...`, 11599 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `509d8b08b25b...`, 11578 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_spskill.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_spskill.c	2026-04-16 20:02:19.954191600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `74bb409f2190...`, 11661 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_spskill.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_spskill.c	2026-04-16 22:48:24.190003300 +0100
@@ -31,11 +31,11 @@
 #include "ui_local.h"
 
 
-#define ART_FRAME					"menu/art/cut_frame"
-#define ART_BACK					"menu/art/back_0.tga"
-#define ART_BACK_FOCUS				"menu/art/back_1.tga"
-#define ART_FIGHT					"menu/art/fight_0"
-#define ART_FIGHT_FOCUS				"menu/art/fight_1"
+#define ART_FRAME				"menu/" MENU_ART_DIR "/cut_frame"
+#define ART_BACK				"menu/" MENU_ART_DIR "/back_0.tga"
+#define ART_BACK_FOCUS				"menu/" MENU_ART_DIR "/back_1.tga"
+#define ART_FIGHT				"menu/" MENU_ART_DIR "/fight_0"
+#define ART_FIGHT_FOCUS				"menu/" MENU_ART_DIR "/fight_1"
 #define ART_MAP_COMPLETE1			"menu/art/level_complete1"
 #define ART_MAP_COMPLETE2			"menu/art/level_complete2"
 #define ART_MAP_COMPLETE3			"menu/art/level_complete3"

```
