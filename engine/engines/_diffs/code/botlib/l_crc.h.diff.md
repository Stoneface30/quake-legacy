# Diff: `code/botlib/l_crc.h`
**Canonical:** `wolfcamql-src` (sha256 `4c9888ce0e4b...`, 1330 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `31e08146bbcd...`, 1309 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_crc.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_crc.h	2026-04-16 20:02:19.854895300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `03eaa4f65629...`, 1249 bytes

_Diff stat: +3 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_crc.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_crc.h	2026-04-16 20:02:26.904499600 +0100
@@ -21,9 +21,8 @@
 */
 
 typedef unsigned short crc_t;
-
-void CRC_Init(unsigned short *crcvalue);
-void CRC_ProcessByte(unsigned short *crcvalue, byte data);
-unsigned short CRC_Value(unsigned short crcvalue);
 unsigned short CRC_ProcessString(unsigned char *data, int length);
+#if 0
+void CRC_ProcessByte(unsigned short *crcvalue, byte data);
 void CRC_ContinueProcessString(unsigned short *crc, char *data, int length);
+#endif

```
