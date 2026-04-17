# Diff: `lcc/src/stmt.c`
**Canonical:** `quake3-source` (sha256 `889b6782924b...`, 17810 bytes)

## Variants

### `q3vm`  — sha256 `957d427451a8...`, 17805 bytes

_Diff stat: +1 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\stmt.c	2026-04-16 20:02:20.086610400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\stmt.c	2026-04-16 22:48:28.100133100 +0100
@@ -37,7 +37,6 @@
 	return cp;
 }
 int reachable(int kind) {
-	Code cp;
 
 	if (kind > Start) {
 		Code cp;
@@ -120,7 +119,7 @@
 		       		static char stop[] = { IF, ID, 0 };
 		       		Tree p;
 		       		t = gettok();
-		       		p = constexpr(0);
+		       		p = constexpression(0);
 		       		if (generic(p->op) == CNST && isint(p->type)) {
 		       			if (swp) {
 		       				needconst++;

```
