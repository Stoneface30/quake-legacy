# Diff: `code/null/mac_net.c`
**Canonical:** `quake3-source` (sha256 `a7616921fc43...`, 1700 bytes)

## Variants

### `openarena-engine`  — sha256 `6caac72357e4...`, 1507 bytes

_Diff stat: +2 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\mac_net.c	2026-04-16 20:02:19.940311700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\mac_net.c	2026-04-16 22:48:25.834145700 +0100
@@ -15,12 +15,12 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "../game/q_shared.h"
+#include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
 
 /*
@@ -52,14 +52,3 @@
 */
 void Sys_SendPacket( int length, void *data, netadr_t to ) {
 }
-
-/*
-==================
-Sys_GetPacket
-
-Never called by the game logic, just the system event queing
-==================
-*/
-qboolean	Sys_GetPacket ( netadr_t *net_from, msg_t *net_message ) {
-	return false;
-}

```
