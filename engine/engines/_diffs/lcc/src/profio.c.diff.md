# Diff: `lcc/src/profio.c`
**Canonical:** `quake3-source` (sha256 `d85ebaa64c59...`, 6808 bytes)

## Variants

### `q3vm`  — sha256 `19c3660e6c96...`, 6812 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\profio.c	2026-04-16 20:02:20.085103100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\profio.c	2026-04-16 22:48:28.099132300 +0100
@@ -150,9 +150,9 @@
 		struct count *c = cursor->counts;
 		for (l = 0, u = cursor->count - 1; l <= u; ) {
 			int k = (l + u)/2;
-			if (c[k].y > y || c[k].y == y && c[k].x > x)
+			if (c[k].y > y || (c[k].y == y && c[k].x > x))
 				u = k - 1;
-			else if (c[k].y < y || c[k].y == y && c[k].x < x)
+			else if (c[k].y < y || (c[k].y == y && c[k].x < x))
 				l = k + 1;
 			else
 				return c[k].count;

```
