# Diff: `code/asm/qasm.h`
**Canonical:** `quake3e` (sha256 `09103808bd1b...`, 1300 bytes)

## Variants

### `openarena-engine`  — sha256 `f89a6d6c9c76...`, 1264 bytes

_Diff stat: +1 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\asm\qasm.h	2026-04-16 20:02:26.889279200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\asm\qasm.h	2026-04-16 22:48:25.704436500 +0100
@@ -24,15 +24,11 @@
 
 #include "../qcommon/q_platform.h"
 
-#if defined(__MINGW32__) || defined(MACOS_X)
-#undef ELF
-#endif
-
 #ifdef __ELF__
 .section .note.GNU-stack,"",@progbits
 #endif
 
-#ifdef ELF
+#if defined(__ELF__) || defined(__WIN64__)
 #define C(label) label
 #else
 #define C(label) _##label

```
