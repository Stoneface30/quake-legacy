# Diff: `code/qcommon/unzip.h`
**Canonical:** `wolfcamql-src` (sha256 `0432a7acfe47...`, 13362 bytes)

## Variants

### `quake3-source`  — sha256 `94f1bf91c9fc...`, 13863 bytes

_Diff stat: +204 / -223 lines_

_(full diff is 23630 bytes — see files directly)_

### `ioquake3`  — sha256 `9ee2f7606362...`, 13348 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\unzip.h	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\unzip.h	2026-04-16 20:02:21.572103800 +0100
@@ -50,7 +50,7 @@
 #endif
 
 #ifdef USE_INTERNAL_ZLIB
-  #include "../zlib-1.3.1/zlib.h"
+  #include "zlib.h"
 #else
   #include <zlib.h>
 #endif

```

### `quake3e`  — sha256 `8f0a93c5e420...`, 13886 bytes

_Diff stat: +202 / -221 lines_

_(full diff is 23497 bytes — see files directly)_

### `openarena-engine`  — sha256 `8574e28a796c...`, 13358 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\unzip.h	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\unzip.h	2026-04-16 22:48:25.914363000 +0100
@@ -49,8 +49,8 @@
 extern "C" {
 #endif
 
-#ifdef USE_INTERNAL_ZLIB
-  #include "../zlib-1.3.1/zlib.h"
+#ifdef USE_LOCAL_HEADERS
+  #include "../zlib/zlib.h"
 #else
   #include <zlib.h>
 #endif
@@ -125,8 +125,8 @@
                                                  int iCaseSensitivity));
 /*
    Compare two filename (fileName1,fileName2).
-   If iCaseSenisivity = 1, comparison is case sensitivity (like strcmp)
-   If iCaseSenisivity = 2, comparison is not case sensitivity (like strcmpi
+   If iCaseSenisivity = 1, comparision is case sensitivity (like strcmp)
+   If iCaseSenisivity = 2, comparision is not case sensitivity (like strcmpi
                                 or strcasecmp)
    If iCaseSenisivity = 0, case sensitivity is defaut of your operating system
     (like 1 on Unix, 2 on Windows)

```
