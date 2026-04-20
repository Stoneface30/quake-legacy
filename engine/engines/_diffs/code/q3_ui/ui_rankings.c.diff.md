# Diff: `code/q3_ui/ui_rankings.c`
**Canonical:** `wolfcamql-src` (sha256 `4c29302c4b01...`, 10544 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `d0a59afd3b1b...`, 10523 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_rankings.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_rankings.c	2026-04-16 20:02:19.950618100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `ded67aa91e4d...`, 10557 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_rankings.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_rankings.c	2026-04-16 22:48:24.186499300 +0100
@@ -27,7 +27,7 @@
 #include "ui_local.h"
 
 
-#define RANKINGS_FRAME	"menu/art/cut_frame"
+#define RANKINGS_FRAME	"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_LOGIN		100
 #define ID_LOGOUT		101

```
