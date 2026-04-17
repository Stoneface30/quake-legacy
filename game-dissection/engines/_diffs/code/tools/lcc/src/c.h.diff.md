# Diff: `code/tools/lcc/src/c.h`
**Canonical:** `wolfcamql-src` (sha256 `57247c6b30ed...`, 17496 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `eb86c9be8385...`, 17464 bytes

_Diff stat: +1 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\c.h	2026-04-16 20:02:25.808414500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\c.h	2026-04-16 22:48:25.950077800 +0100
@@ -577,7 +577,6 @@
 extern Tree consttree(unsigned int, Type);
 extern Tree eqtree(int, Tree, Tree);
 extern int iscallb(Tree);
-extern int isnullptr(Tree);
 extern Tree shtree(int, Tree, Tree);
 extern void typeerror(int, Tree, Tree);
 
@@ -645,7 +644,7 @@
 extern int findfunc(char *, char *);
 extern int findcount(char *, int, int);
 
-extern Tree constantexpr(int);
+extern Tree constexpr(int);
 extern int intexpr(int, int);
 extern Tree simplify(int, Type, Tree, Tree);
 extern int ispow2(unsigned long u);

```

### `openarena-gamecode`  — sha256 `3f8df2502b70...`, 17468 bytes

_Diff stat: +2 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\c.h	2026-04-16 20:02:25.808414500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\c.h	2026-04-16 22:48:24.205077500 +0100
@@ -523,7 +523,7 @@
 extern Table identifiers;
 extern Table labels;
 extern Table types;
-extern int level;
+extern int level_lcc;
 
 extern List loci, symbols;
 
@@ -577,7 +577,6 @@
 extern Tree consttree(unsigned int, Type);
 extern Tree eqtree(int, Tree, Tree);
 extern int iscallb(Tree);
-extern int isnullptr(Tree);
 extern Tree shtree(int, Tree, Tree);
 extern void typeerror(int, Tree, Tree);
 
@@ -645,7 +644,7 @@
 extern int findfunc(char *, char *);
 extern int findcount(char *, int, int);
 
-extern Tree constantexpr(int);
+extern Tree constexpr(int);
 extern int intexpr(int, int);
 extern Tree simplify(int, Type, Tree, Tree);
 extern int ispow2(unsigned long u);

```
