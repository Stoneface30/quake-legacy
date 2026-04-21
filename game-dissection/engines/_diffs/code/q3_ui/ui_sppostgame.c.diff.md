# Diff: `code/q3_ui/ui_sppostgame.c`
**Canonical:** `wolfcamql-src` (sha256 `31b85a61f8d0...`, 19544 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `2d055bf34f45...`, 19523 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sppostgame.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_sppostgame.c	2026-04-16 20:02:19.954191600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `ba76ba8cf04f...`, 19663 bytes

_Diff stat: +7 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sppostgame.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_sppostgame.c	2026-04-16 22:48:24.190003300 +0100
@@ -34,12 +34,12 @@
 
 #define AWARD_PRESENTATION_TIME		2000
 
-#define ART_MENU0		"menu/art/menu_0"
-#define ART_MENU1		"menu/art/menu_1"
-#define ART_REPLAY0		"menu/art/replay_0"
-#define ART_REPLAY1		"menu/art/replay_1"
-#define ART_NEXT0		"menu/art/next_0"
-#define ART_NEXT1		"menu/art/next_1"
+#define ART_MENU0		"menu/" MENU_ART_DIR "/menu_0"
+#define ART_MENU1		"menu/" MENU_ART_DIR "/menu_1"
+#define ART_REPLAY0		"menu/" MENU_ART_DIR "/replay_0"
+#define ART_REPLAY1		"menu/" MENU_ART_DIR "/replay_1"
+#define ART_NEXT0		"menu/" MENU_ART_DIR "/next_0"
+#define ART_NEXT1		"menu/" MENU_ART_DIR "/next_1"
 
 #define ID_AGAIN		10
 #define ID_NEXT			11
@@ -167,6 +167,7 @@
 		return;
 	}
 	UI_PopMenu();
+        trap_Cvar_Set( "nextmap", "" );
 	trap_Cmd_ExecuteText( EXEC_APPEND, "disconnect; levelselect\n" );
 }
 

```
