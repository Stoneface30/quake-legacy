# Diff: `lcc/src/sym.c`
**Canonical:** `quake3-source` (sha256 `c715f35a32a2...`, 7198 bytes)

## Variants

### `q3vm`  — sha256 `d0a9d52b0595...`, 7182 bytes

_Diff stat: +0 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\sym.c	2026-04-16 20:02:20.087614200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\sym.c	2026-04-16 22:48:28.100133100 +0100
@@ -296,7 +296,6 @@
 
 /* vtoa - return string for the constant v of type ty */
 char *vtoa(Type ty, Value v) {
-	char buf[50];
 
 	ty = unqual(ty);
 	switch (ty->op) {

```
