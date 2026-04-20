# Diff: `code/botlib/l_crc.c`
**Canonical:** `wolfcamql-src` (sha256 `4bb6f6f986f4...`, 6034 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `c9751ef4e914...`, 5998 bytes

_Diff stat: +3 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_crc.c	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_crc.c	2026-04-16 20:02:19.854895300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -33,10 +33,9 @@
 #include <stdio.h>
 #include <string.h>
 
-#include "../qcommon/q_shared.h"
-#include "botlib.h"
+#include "../game/q_shared.h"
+#include "../game/botlib.h"
 #include "be_interface.h"			//for botimport.Print
-#include "l_crc.h"
 
 
 // FIXME: byte swap?

```

### `quake3e`  — sha256 `dd309fd99eb6...`, 6085 bytes

_Diff stat: +7 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_crc.c	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_crc.c	2026-04-16 20:02:26.904499600 +0100
@@ -48,7 +48,7 @@
 #define CRC_INIT_VALUE	0xffff
 #define CRC_XOR_VALUE	0x0000
 
-unsigned short crctable[257] =
+static unsigned short crctable[257] =
 {
 	0x0000,	0x1021,	0x2042,	0x3063,	0x4084,	0x50a5,	0x60c6,	0x70e7,
 	0x8108,	0x9129,	0xa14a,	0xb16b,	0xc18c,	0xd1ad,	0xe1ce,	0xf1ef,
@@ -90,10 +90,11 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void CRC_Init(unsigned short *crcvalue)
+static void CRC_Init(unsigned short *crcvalue)
 {
 	*crcvalue = CRC_INIT_VALUE;
 } //end of the function CRC_Init
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -104,13 +105,14 @@
 {
 	*crcvalue = (*crcvalue << 8) ^ crctable[(*crcvalue >> 8) ^ data];
 } //end of the function CRC_ProcessByte
+#endif
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-unsigned short CRC_Value(unsigned short crcvalue)
+static unsigned short CRC_Value(unsigned short crcvalue)
 {
 	return crcvalue ^ CRC_XOR_VALUE;
 } //end of the function CRC_Value
@@ -135,6 +137,7 @@
 	} //end for
 	return CRC_Value(crcvalue);
 } //end of the function CRC_ProcessString
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -150,3 +153,4 @@
 		*crc = (*crc << 8) ^ crctable[(*crc >> 8) ^ data[i]];
 	} //end for
 } //end of the function CRC_ProcessString
+#endif

```
