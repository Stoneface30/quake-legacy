# Diff: `code/client/libmumblelink.c`
**Canonical:** `wolfcamql-src` (sha256 `af5608d3b193...`, 4683 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `f18dec539d9d...`, 4665 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\libmumblelink.c	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\libmumblelink.c	2026-04-16 22:48:25.734378800 +0100
@@ -35,7 +35,7 @@
 #endif
 
 #include <fcntl.h>
-#include <stdint.h>
+#include <inttypes.h>
 #include <stdlib.h>
 #include <string.h>
 #include <stdio.h>
@@ -164,11 +164,11 @@
 	size_t len;
 	if (!lm)
 		return;
-	len = MIN(sizeof(lm->description)/sizeof(wchar_t), strlen(description)+1);
+	len = MIN(sizeof(lm->description), strlen(description)+1);
 	mbstowcs(lm->description, description, len);
 }
 
-void mumble_unlink(void)
+void mumble_unlink()
 {
 	if(!lm)
 		return;

```
