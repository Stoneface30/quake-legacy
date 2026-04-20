# Diff: `code/asm/snapvector.c`
**Canonical:** `wolfcamql-src` (sha256 `8c59c5cde85a...`, 2031 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `c507fd0400d1...`, 1989 bytes

_Diff stat: +1 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\asm\snapvector.c	2026-04-16 20:02:25.111324200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\asm\snapvector.c	2026-04-16 22:48:25.705436300 +0100
@@ -23,14 +23,12 @@
 #include "qasm-inline.h"
 #include "../qcommon/q_shared.h"
 
-#if defined (__i386__) || defined(__x86_64__)
-
 /*
  * GNU inline asm version of qsnapvector
  * See MASM snapvector.asm for commentary
  */
 
-static unsigned char ssemask[16] Q_ALIGN(16) =
+static unsigned char ssemask[16] __attribute__((aligned(16))) =
 {
 	"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00"
 };
@@ -73,5 +71,3 @@
 		: "memory"
 	);
 }
-
-#endif

```
