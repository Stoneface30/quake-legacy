# Diff: `code/tools/lcc/src/simp.c`
**Canonical:** `wolfcamql-src` (sha256 `5d185f6c3399...`, 17026 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `59634d9d91d8...`, 17020 bytes
Also identical in: openarena-gamecode

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\simp.c	2026-04-16 20:02:25.813417600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\simp.c	2026-04-16 22:48:25.956097500 +0100
@@ -182,7 +182,7 @@
 static int subd(double x, double y, double min, double max, int needconst) {
 	return addd(x, -y, min, max, needconst);
 }
-Tree constantexpr(int tok) {
+Tree constexpr(int tok) {
 	Tree p;
 
 	needconst++;
@@ -192,7 +192,7 @@
 }
 
 int intexpr(int tok, int n) {
-	Tree p = constantexpr(tok);
+	Tree p = constexpr(tok);
 
 	needconst++;
 	if (p->op == CNST+I || p->op == CNST+U)

```
