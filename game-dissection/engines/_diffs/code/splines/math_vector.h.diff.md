# Diff: `code/splines/math_vector.h`
**Canonical:** `wolfcamql-src` (sha256 `151556e82cf1...`, 14123 bytes)

## Variants

### `quake3-source`  — sha256 `f44f82f3b64d...`, 14098 bytes

_Diff stat: +0 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\math_vector.h	2026-04-16 20:02:25.272780200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\math_vector.h	2026-04-16 20:02:19.981635900 +0100
@@ -23,10 +23,8 @@
 #define __MATH_VECTOR_H__
 
 #if defined(_WIN32)
-#ifdef _MSC_VER
 #pragma warning(disable : 4244)
 #endif
-#endif
 
 #include <math.h>
 #include <assert.h>

```
