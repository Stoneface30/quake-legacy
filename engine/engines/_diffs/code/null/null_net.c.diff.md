# Diff: `code/null/null_net.c`
**Canonical:** `quake3-source` (sha256 `933e83292104...`, 1669 bytes)

## Variants

### `openarena-engine`  — sha256 `0f5526f02c92...`, 1473 bytes

_Diff stat: +1 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_net.c	2026-04-16 20:02:19.941310900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_net.c	2026-04-16 22:48:25.834145700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -51,14 +51,3 @@
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
