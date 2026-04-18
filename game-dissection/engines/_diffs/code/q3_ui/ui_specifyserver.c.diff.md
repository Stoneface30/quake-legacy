# Diff: `code/q3_ui/ui_specifyserver.c`
**Canonical:** `wolfcamql-src` (sha256 `ac4f8a622d81...`, 6916 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `86c3ca834325...`, 6895 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_specifyserver.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_specifyserver.c	2026-04-16 20:02:19.953195000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `233f6098cd69...`, 6992 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_specifyserver.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_specifyserver.c	2026-04-16 22:48:24.188498600 +0100
@@ -26,12 +26,12 @@
 	SPECIFY SERVER
 *********************************************************************************/
 
-#define SPECIFYSERVER_FRAMEL	"menu/art/frame2_l"
-#define SPECIFYSERVER_FRAMER	"menu/art/frame1_r"
-#define SPECIFYSERVER_BACK0		"menu/art/back_0"
-#define SPECIFYSERVER_BACK1		"menu/art/back_1"
-#define SPECIFYSERVER_FIGHT0	"menu/art/fight_0"
-#define SPECIFYSERVER_FIGHT1	"menu/art/fight_1"
+#define SPECIFYSERVER_FRAMEL	"menu/" MENU_ART_DIR "/frame2_l"
+#define SPECIFYSERVER_FRAMER	"menu/" MENU_ART_DIR "/frame1_r"
+#define SPECIFYSERVER_BACK0	"menu/" MENU_ART_DIR "/back_0"
+#define SPECIFYSERVER_BACK1	"menu/" MENU_ART_DIR "/back_1"
+#define SPECIFYSERVER_FIGHT0	"menu/" MENU_ART_DIR "/fight_0"
+#define SPECIFYSERVER_FIGHT1	"menu/" MENU_ART_DIR "/fight_1"
 
 #define ID_SPECIFYSERVERBACK	102
 #define ID_SPECIFYSERVERGO		103

```
