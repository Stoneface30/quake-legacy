# Diff: `code/null/null_input.c`
**Canonical:** `wolfcamql-src` (sha256 `c57a73c5ac6b...`, 1120 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `0d7d8a05cfd0...`, 1136 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_input.c	2026-04-16 20:02:25.202155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_input.c	2026-04-16 20:02:19.940311700 +0100
@@ -15,10 +15,11 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
+#include "../client/client.h"
 
 void IN_Init( void ) {
 }
@@ -29,6 +30,6 @@
 void IN_Shutdown( void ) {
 }
 
-void IN_Restart( void ) {
+void Sys_SendKeyEvents (void) {
 }
 

```

### `openarena-engine`  — sha256 `64d0bbd96ecf...`, 1158 bytes

_Diff stat: +3 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_input.c	2026-04-16 20:02:25.202155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_input.c	2026-04-16 22:48:25.834145700 +0100
@@ -32,3 +32,6 @@
 void IN_Restart( void ) {
 }
 
+void Sys_SendKeyEvents (void) {
+}
+

```
