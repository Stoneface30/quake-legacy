# Diff: `code/asm/ftola.c`
**Canonical:** `wolfcamql-src` (sha256 `6e973865e55a...`, 2247 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `4b2e8e2eefe2...`, 2192 bytes

_Diff stat: +0 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\asm\ftola.c	2026-04-16 20:02:25.110324700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\asm\ftola.c	2026-04-16 22:48:25.704436500 +0100
@@ -22,7 +22,6 @@
 
 #include "qasm-inline.h"
 
-#if defined (__i386__) || defined(__x86_64__)
 static const unsigned short fpucw = 0x0C7F;
 
 /*
@@ -98,4 +97,3 @@
   
   return retval;
 }
-#endif

```
