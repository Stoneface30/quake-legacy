# Diff: `lcc/src/input.c`
**Canonical:** `quake3-source` (sha256 `dc2f02f85cdb...`, 3062 bytes)

## Variants

### `q3vm`  — sha256 `74620405aaf5...`, 3069 bytes

_Diff stat: +2 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\input.c	2026-04-16 20:02:20.082592500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\input.c	2026-04-16 22:48:28.098133400 +0100
@@ -125,10 +125,11 @@
 	} else if (Aflag >= 2 && *cp != '\n')
 		warning("unrecognized control line\n");
 	while (*cp)
-		if (*cp++ == '\n')
+		if (*cp++ == '\n') {
 			if (cp == limit + 1)
 				nextline();
 			else
 				break;
+		}
 }
 

```
