# Diff: `code/q3_ui/ui_confirm.c`
**Canonical:** `wolfcamql-src` (sha256 `58b4f6b8b38f...`, 7081 bytes)

## Variants

### `quake3-source`  — sha256 `bd40fbabaaec...`, 7058 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_confirm.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_confirm.c	2026-04-16 20:02:19.944820100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -143,7 +143,7 @@
 =================
 */
 static void ConfirmMenu_Draw( void ) {
-	//UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
+	UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
 	UI_DrawProportionalString( 320, 204, s_confirm.question, s_confirm.style, color_red );
 	UI_DrawProportionalString( s_confirm.slashX, 265, "/", UI_LEFT|UI_INVERSE, color_red );
 

```

### `openarena-engine`  — sha256 `09b1563e1faa...`, 7079 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_confirm.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_confirm.c	2026-04-16 22:48:25.893195200 +0100
@@ -143,7 +143,7 @@
 =================
 */
 static void ConfirmMenu_Draw( void ) {
-	//UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
+	UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
 	UI_DrawProportionalString( 320, 204, s_confirm.question, s_confirm.style, color_red );
 	UI_DrawProportionalString( s_confirm.slashX, 265, "/", UI_LEFT|UI_INVERSE, color_red );
 

```

### `openarena-gamecode`  — sha256 `3b00f37023fb...`, 7092 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_confirm.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_confirm.c	2026-04-16 22:48:24.180490100 +0100
@@ -32,7 +32,7 @@
 #include "ui_local.h"
 
 
-#define ART_CONFIRM_FRAME	"menu/art/cut_frame"
+#define ART_CONFIRM_FRAME	"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_CONFIRM_NO		10
 #define ID_CONFIRM_YES		11
@@ -143,7 +143,7 @@
 =================
 */
 static void ConfirmMenu_Draw( void ) {
-	//UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
+	UI_DrawNamedPic( 142, 118, 359, 256, ART_CONFIRM_FRAME );
 	UI_DrawProportionalString( 320, 204, s_confirm.question, s_confirm.style, color_red );
 	UI_DrawProportionalString( s_confirm.slashX, 265, "/", UI_LEFT|UI_INVERSE, color_red );
 

```
