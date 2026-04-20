# Diff: `code/q3_ui/ui_saveconfig.c`
**Canonical:** `wolfcamql-src` (sha256 `a6417398f837...`, 6278 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `d2520d3f0bd4...`, 6238 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_saveconfig.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_saveconfig.c	2026-04-16 20:02:19.951678800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -85,7 +85,7 @@
 		return;
 	}
 
-	COM_StripExtension(saveConfig.savename.field.buffer, configname, sizeof(configname));
+	COM_StripExtension(saveConfig.savename.field.buffer, configname );
 	trap_Cmd_ExecuteText( EXEC_APPEND, va( "writeconfig %s.cfg\n", configname ) );
 	UI_PopMenu();
 }

```

### `openarena-gamecode`  — sha256 `8bf0c382716a...`, 6342 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_saveconfig.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_saveconfig.c	2026-04-16 22:48:24.186499300 +0100
@@ -31,11 +31,11 @@
 #include "ui_local.h"
 
 
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"	
-#define ART_SAVE0			"menu/art/save_0"
-#define ART_SAVE1			"menu/art/save_1"
-#define ART_BACKGROUND		"menu/art/cut_frame"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_SAVE0			"menu/" MENU_ART_DIR "/save_0"
+#define ART_SAVE1			"menu/" MENU_ART_DIR "/save_1"
+#define ART_BACKGROUND		"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_NAME			10
 #define ID_BACK			11

```
