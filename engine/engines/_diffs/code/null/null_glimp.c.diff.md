# Diff: `code/null/null_glimp.c`
**Canonical:** `quake3-source` (sha256 `d0d9b7e8c1cf...`, 1638 bytes)

## Variants

### `openarena-engine`  — sha256 `15e5aa3cc289...`, 1648 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_glimp.c	2026-04-16 20:02:19.940311700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_glimp.c	2026-04-16 22:48:25.834145700 +0100
@@ -15,11 +15,11 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-#include "../renderer/tr_local.h"
+#include "tr_common.h"
 
 
 qboolean ( * qwglSwapIntervalEXT)( int interval );

```
