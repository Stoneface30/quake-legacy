# Diff: `code/tools/lcc/src/config.h`
**Canonical:** `wolfcamql-src` (sha256 `b7a09ef80be6...`, 2572 bytes)

## Variants

### `openarena-engine`  — sha256 `69b0e1d90651...`, 2571 bytes
Also identical in: ioquake3, openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\config.h	2026-04-16 20:02:25.808414500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\config.h	2026-04-16 22:48:25.951096500 +0100
@@ -95,7 +95,7 @@
 
 extern unsigned         emitbin(Node, int);
 
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #define debug(x) (void)0
 #else
 #define debug(x) (void)(dflag&&((x),0))

```
