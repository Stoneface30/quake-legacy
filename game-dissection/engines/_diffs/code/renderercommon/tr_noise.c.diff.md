# Diff: `code/renderercommon/tr_noise.c`
**Canonical:** `wolfcamql-src` (sha256 `8c82be5a6c8b...`, 2867 bytes)
Also identical in: ioquake3

## Variants

### `quake3e`  — sha256 `42c84a194d3e...`, 2906 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_noise.c	2026-04-16 20:02:25.237331000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_noise.c	2026-04-16 20:02:27.344319500 +0100
@@ -19,8 +19,9 @@
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-// tr_noise.c
-#include "tr_common.h"
+
+#include "../qcommon/q_shared.h"
+#include "../renderercommon/tr_public.h"
 
 #define NOISE_SIZE 256
 #define NOISE_MASK ( NOISE_SIZE - 1 )

```

### `openarena-engine`  — sha256 `cee6803ceec6...`, 2866 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_noise.c	2026-04-16 20:02:25.237331000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_noise.c	2026-04-16 22:48:25.932966000 +0100
@@ -49,7 +49,7 @@
 	}
 }
 
-float R_NoiseGet4f( float x, float y, float z, double t )
+float R_NoiseGet4f( float x, float y, float z, float t )
 {
 	int i;
 	int ix, iy, iz, it;

```
