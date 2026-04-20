# Diff: `lcc/src/error.c`
**Canonical:** `quake3-source` (sha256 `88c56798d8f0...`, 2997 bytes)

## Variants

### `q3vm`  — sha256 `40c36f117b0a...`, 2996 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\error.c	2026-04-16 20:02:20.081593400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\error.c	2026-04-16 22:48:28.097134900 +0100
@@ -80,7 +80,7 @@
 	return 0;
 }
 
-/* printtoken - print current token preceeded by a space */
+/* printtoken - print current token preceded by a space */
 static void printtoken(void) {
 	switch (t) {
 	case ID: fprint(stderr, " `%s'", token); break;

```
