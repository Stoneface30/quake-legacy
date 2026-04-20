# Diff: `code/renderercommon/tr_image_pcx.c`
**Canonical:** `wolfcamql-src` (sha256 `8f4cad043706...`, 3942 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3e`  — sha256 `4e35ca7bd45a...`, 3994 bytes

_Diff stat: +2 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_pcx.c	2026-04-16 20:02:25.234262100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_image_pcx.c	2026-04-16 20:02:27.343319600 +0100
@@ -21,7 +21,8 @@
 ===========================================================================
 */
 
-#include "tr_common.h"
+#include "../qcommon/q_shared.h"
+#include "../renderercommon/tr_public.h"
 
 /*
 ========================================================================

```
