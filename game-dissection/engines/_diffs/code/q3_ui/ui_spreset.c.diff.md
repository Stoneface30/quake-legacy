# Diff: `code/q3_ui/ui_spreset.c`
**Canonical:** `wolfcamql-src` (sha256 `5bef68808c17...`, 5185 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `7ab77688452c...`, 5164 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_spreset.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_spreset.c	2026-04-16 20:02:19.954191600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `76bf2a6b0fcd...`, 5138 bytes

_Diff stat: +0 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_spreset.c	2026-04-16 20:02:25.214501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_spreset.c	2026-04-16 22:48:24.190003300 +0100
@@ -77,9 +77,7 @@
 */
 static sfxHandle_t Reset_MenuKey( int key ) {
 	switch ( key ) {
-	case K_KP_LEFTARROW:
 	case K_LEFTARROW:
-	case K_KP_RIGHTARROW:
 	case K_RIGHTARROW:
 		key = K_TAB;
 		break;

```
