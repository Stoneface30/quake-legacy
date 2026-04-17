# Diff: `lcc/cpp/eval.c`
**Canonical:** `quake3-source` (sha256 `b4e90626b57c...`, 10335 bytes)

## Variants

### `q3vm`  — sha256 `1056f8074746...`, 10419 bytes

_Diff stat: +4 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\eval.c	2026-04-16 20:02:20.042587900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\eval.c	2026-04-16 22:48:28.088019500 +0100
@@ -219,6 +219,10 @@
 	long rv1, rv2;
 	int rtype, oper;
 
+	/* prevent compiler whining. */
+	v1.val = v2.val = 0;
+	v1.type = v2.type = 0;
+
 	rv2=0;
 	rtype=0;
 	while (pri.pri < priority[op[-1]].pri) {

```
