# Diff: `lcc/src/symbolic.c`
**Canonical:** `quake3-source` (sha256 `2ba1951eb05c...`, 12005 bytes)

## Variants

### `q3vm`  — sha256 `d146060c501e...`, 12045 bytes

_Diff stat: +20 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\symbolic.c	2026-04-16 20:02:20.087614200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\symbolic.c	2026-04-16 22:48:28.100133100 +0100
@@ -404,16 +404,16 @@
 static void I(stabtype)(Symbol p) {}
 
 Interface symbolicIR = {
-	1, 1, 0,	/* char */
-	2, 2, 0,	/* short */
-	4, 4, 0,	/* int */
-	4, 4, 0,	/* long */
-	4, 4, 0,	/* long long */
-	4, 4, 1,	/* float */
-	8, 8, 1,	/* double */
-	8, 8, 1,	/* long double */
-	4, 4, 0,	/* T* */
-	0, 4, 0,	/* struct */
+	{1, 1, 0},	/* char */
+	{2, 2, 0},	/* short */
+	{4, 4, 0},	/* int */
+	{4, 4, 0},	/* long */
+	{4, 4, 0},	/* long long */
+	{4, 4, 1},	/* float */
+	{8, 8, 1},	/* double */
+	{8, 8, 1},	/* long double */
+	{4, 4, 0},	/* T* */
+	{0, 4, 0},	/* struct */
 	0,		/* little_endian */
 	0,		/* mulops_calls */
 	0,		/* wants_callb */
@@ -449,16 +449,16 @@
 };
 
 Interface symbolic64IR = {
-	1, 1, 0,	/* char */
-	2, 2, 0,	/* short */
-	4, 4, 0,	/* int */
-	8, 8, 0,	/* long */
-	8, 8, 0,	/* long long */
-	4, 4, 1,	/* float */
-	8, 8, 1,	/* double */
-	8, 8, 1,	/* long double */
-	8, 8, 0,	/* T* */
-	0, 1, 0,	/* struct */
+	{1, 1, 0},	/* char */
+	{2, 2, 0},	/* short */
+	{4, 4, 0},	/* int */
+	{8, 8, 0},	/* long */
+	{8, 8, 0},	/* long long */
+	{4, 4, 1},	/* float */
+	{8, 8, 1},	/* double */
+	{8, 8, 1},	/* long double */
+	{8, 8, 0},	/* T* */
+	{0, 1, 0},	/* struct */
 	1,		/* little_endian */
 	0,		/* mulops_calls */
 	0,		/* wants_callb */

```
