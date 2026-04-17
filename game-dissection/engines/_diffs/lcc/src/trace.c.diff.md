# Diff: `lcc/src/trace.c`
**Canonical:** `quake3-source` (sha256 `2a3073cd3c10...`, 4782 bytes)

## Variants

### `q3vm`  — sha256 `41943f526197...`, 4789 bytes

_Diff stat: +2 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\trace.c	2026-04-16 20:02:20.087614200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\trace.c	2026-04-16 22:48:28.101258000 +0100
@@ -8,7 +8,7 @@
 /* appendstr - append str to the evolving format string, expanding it if necessary */
 static void appendstr(char *str) {
 	do
-		if (fp == fmtend)
+		if (fp == fmtend) {
 			if (fp) {
 				char *s = allocate(2*(fmtend - fmt), FUNC);
 				strncpy(s, fmt, fmtend - fmt);
@@ -19,6 +19,7 @@
 				fp = fmt = allocate(80, FUNC);
 				fmtend = fmt + 80;
 			}
+		}
 	while ((*fp++ = *str++) != 0);
 	fp--;
 }

```
