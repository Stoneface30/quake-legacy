# Diff: `code/q3_ui/ui_specifyleague.c`
**Canonical:** `wolfcamql-src` (sha256 `04950de0d40b...`, 10908 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `312dd4c07180...`, 10887 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_specifyleague.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_specifyleague.c	2026-04-16 20:02:19.953195000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `2e4c1e6e3489...`, 10999 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_specifyleague.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_specifyleague.c	2026-04-16 22:48:24.188498600 +0100
@@ -30,13 +30,13 @@
 #define MAX_LISTBOXWIDTH		40
 #define MAX_LEAGUENAME			80
 
-#define SPECIFYLEAGUE_FRAMEL	"menu/art/frame2_l"
-#define SPECIFYLEAGUE_FRAMER	"menu/art/frame1_r"
-#define SPECIFYLEAGUE_BACK0		"menu/art/back_0"
-#define SPECIFYLEAGUE_BACK1		"menu/art/back_1"
-#define SPECIFYLEAGUE_ARROWS0	"menu/art/arrows_vert_0"
-#define SPECIFYLEAGUE_UP		"menu/art/arrows_vert_top"
-#define SPECIFYLEAGUE_DOWN		"menu/art/arrows_vert_bot"
+#define SPECIFYLEAGUE_FRAMEL	"menu/" MENU_ART_DIR "/frame2_l"
+#define SPECIFYLEAGUE_FRAMER	"menu/" MENU_ART_DIR "/frame1_r"
+#define SPECIFYLEAGUE_BACK0		"menu/" MENU_ART_DIR "/back_0"
+#define SPECIFYLEAGUE_BACK1		"menu/" MENU_ART_DIR "/back_1"
+#define SPECIFYLEAGUE_ARROWS0	"menu/" MENU_ART_DIR "/arrows_vert_0"
+#define SPECIFYLEAGUE_UP		"menu/" MENU_ART_DIR "/arrows_vert_top"
+#define SPECIFYLEAGUE_DOWN		"menu/" MENU_ART_DIR "/arrows_vert_bot"
 #define GLOBALRANKINGS_LOGO		"menu/art/gr/grlogo"
 #define GLOBALRANKINGS_LETTERS	"menu/art/gr/grletters"
 

```
