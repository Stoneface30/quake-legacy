# Diff: `code/q3_ui/ui_signup.c`
**Canonical:** `wolfcamql-src` (sha256 `6e79791bea23...`, 8978 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `6b7f8f94aa54...`, 8957 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_signup.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_signup.c	2026-04-16 20:02:19.952185700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `78e45ccd79b5...`, 8986 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_signup.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_signup.c	2026-04-16 22:48:24.187498800 +0100
@@ -27,7 +27,7 @@
 #include "ui_local.h"
 
 
-#define SIGNUP_FRAME		"menu/art/cut_frame"
+#define SIGNUP_FRAME		"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_NAME			100
 #define ID_NAME_BOX		101
@@ -80,7 +80,7 @@
 	switch( ((menucommon_s*)ptr)->id ) {
 	case ID_SIGNUP:
 		if( strcmp(s_signup.password_box.field.buffer, 
-			s_signup.again_box.field.buffer) != 0 )
+			s_signup.again_box.field.buffer) )
 		{
 			// GRANK_FIXME - password mismatch
 			break;

```
