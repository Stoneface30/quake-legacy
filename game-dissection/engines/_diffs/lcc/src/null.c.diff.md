# Diff: `lcc/src/null.c`
**Canonical:** `quake3-source` (sha256 `586262179868...`, 1983 bytes)

## Variants

### `q3vm`  — sha256 `a7cb82f1f7c7...`, 2003 bytes

_Diff stat: +10 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\null.c	2026-04-16 20:02:20.084097900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\null.c	2026-04-16 22:48:28.099132300 +0100
@@ -29,16 +29,16 @@
 
 
 Interface nullIR = {
-	1, 1, 0,	/* char */
-	2, 2, 0,	/* short */
-	4, 4, 0,	/* int */
-	8, 8, 1,	/* long */
-	8 ,8, 1,	/* long long */
-	4, 4, 1,	/* float */
-	8, 8, 1,	/* double */
-	16,16,1,	/* long double */
-	4, 4, 0,	/* T* */
-	0, 4, 0,	/* struct */
+	{1, 1, 0},	/* char */
+	{2, 2, 0},	/* short */
+	{4, 4, 0},	/* int */
+	{8, 8, 1},	/* long */
+	{8 ,8, 1},	/* long long */
+	{4, 4, 1},	/* float */
+	{8, 8, 1},	/* double */
+	{16,16,1},	/* long double */
+	{4, 4, 0},	/* T* */
+	{0, 4, 0},	/* struct */
 	1,		/* little_endian */
 	0,		/* mulops_calls */
 	0,		/* wants_callb */

```
