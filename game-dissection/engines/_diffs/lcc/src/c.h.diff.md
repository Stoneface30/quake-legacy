# Diff: `lcc/src/c.h`
**Canonical:** `quake3-source` (sha256 `d55b5ffb3b9e...`, 17394 bytes)

## Variants

### `q3vm`  — sha256 `05472c63004d...`, 17499 bytes

_Diff stat: +10 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\c.h	2026-04-16 20:02:20.080593800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\c.h	2026-04-16 22:48:28.095133400 +0100
@@ -14,7 +14,7 @@
 #define	BUFSIZE 4096
 
 #define istypename(t,tsym) (kind[t] == CHAR \
-	|| t == ID && tsym && tsym->sclass == TYPEDEF)
+	|| (t == ID && tsym && tsym->sclass == TYPEDEF))
 #define sizeop(n) ((n)<<10)
 #define generic(op)  ((op)&0x3F0)
 #define specific(op) ((op)&0x3FF)
@@ -81,7 +81,7 @@
 typedef union value {
 	long i;
 	unsigned long u;
-	long double d;
+	double d;
 	void *p;
 	void (*g)(void);
 } Value;
@@ -98,6 +98,12 @@
 	void *xt;
 } Xtype;
 
+typedef union {
+	float f;
+	int i;
+	unsigned int ui;
+} floatint_t;
+
 #include "config.h"
 typedef struct metrics {
 	unsigned char size, align, outofline;
@@ -571,6 +577,7 @@
 extern Tree consttree(unsigned int, Type);
 extern Tree eqtree(int, Tree, Tree);
 extern int iscallb(Tree);
+extern int isnullptr(Tree);
 extern Tree shtree(int, Tree, Tree);
 extern void typeerror(int, Tree, Tree);
 
@@ -638,7 +645,7 @@
 extern int findfunc(char *, char *);
 extern int findcount(char *, int, int);
 
-extern Tree constexpr(int);
+extern Tree constexpression(int);
 extern int intexpr(int, int);
 extern Tree simplify(int, Type, Tree, Tree);
 extern int ispow2(unsigned long u);

```
