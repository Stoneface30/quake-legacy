# Diff: `code/tools/lcc/src/trace.c`
**Canonical:** `wolfcamql-src` (sha256 `41943f526197...`, 4789 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `openarena-gamecode`  — sha256 `721417c505be...`, 4793 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\trace.c	2026-04-16 20:02:25.815935600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\trace.c	2026-04-16 22:48:24.210588400 +0100
@@ -128,7 +128,7 @@
 
 	defglobal(counter, BSS);
 	(*IR->space)(counter->type->size);
-	frameno = genident(AUTO, inttype, level);
+	frameno = genident(AUTO, inttype, level_lcc);
 	addlocal(frameno);
 	appendstr(f->name); appendstr("#");
 	tracevalue(asgn(frameno, incr(INCR, idtree(counter), consttree(1, inttype))), 0);

```
