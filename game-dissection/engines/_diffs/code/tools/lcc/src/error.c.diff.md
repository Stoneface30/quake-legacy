# Diff: `code/tools/lcc/src/error.c`
**Canonical:** `wolfcamql-src` (sha256 `40c36f117b0a...`, 2996 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `88c56798d8f0...`, 2997 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\error.c	2026-04-16 20:02:25.810416200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\error.c	2026-04-16 22:48:25.952097400 +0100
@@ -80,7 +80,7 @@
 	return 0;
 }
 
-/* printtoken - print current token preceded by a space */
+/* printtoken - print current token preceeded by a space */
 static void printtoken(void) {
 	switch (t) {
 	case ID: fprint(stderr, " `%s'", token); break;

```
