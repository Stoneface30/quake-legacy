# Diff: `code/q3_ui/ui_loadconfig.c`
**Canonical:** `wolfcamql-src` (sha256 `641a149f2a1e...`, 8320 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `cb3c03fe210d...`, 8299 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_loadconfig.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_loadconfig.c	2026-04-16 20:02:19.946829300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `006e55d0bcd6...`, 8436 bytes

_Diff stat: +10 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_loadconfig.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_loadconfig.c	2026-04-16 22:48:24.182499300 +0100
@@ -31,15 +31,15 @@
 #include "ui_local.h"
 
 
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"	
-#define ART_FIGHT0			"menu/art/load_0"
-#define ART_FIGHT1			"menu/art/load_1"
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_ARROWS			"menu/art/arrows_horz_0"
-#define ART_ARROWLEFT		"menu/art/arrows_horz_left"
-#define ART_ARROWRIGHT		"menu/art/arrows_horz_right"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_FIGHT0			"menu/" MENU_ART_DIR "/load_0"
+#define ART_FIGHT1			"menu/" MENU_ART_DIR "/load_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_ARROWS			"menu/" MENU_ART_DIR "/arrows_horz_0"
+#define ART_ARROWLEFT		"menu/" MENU_ART_DIR "/arrows_horz_left"
+#define ART_ARROWRIGHT		"menu/" MENU_ART_DIR "/arrows_horz_right"
 
 #define MAX_CONFIGS			128
 #define NAMEBUFSIZE			( MAX_CONFIGS * 16 )
@@ -225,7 +225,7 @@
 		
 		// strip extension
 		len = strlen( configname );
-		if (!Q_stricmp(configname +  len - 4,".cfg"))
+		if (Q_strequal(configname +  len - 4,".cfg"))
 			configname[len-4] = '\0';
 
 		Q_strupr(configname);

```
