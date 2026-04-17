# Diff: `code/tools/lcc/src/sym.c`
**Canonical:** `wolfcamql-src` (sha256 `d0a9d52b0595...`, 7182 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `openarena-gamecode`  — sha256 `49a6539775d3...`, 7222 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\sym.c	2026-04-16 20:02:25.814928900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\sym.c	2026-04-16 22:48:24.210588400 +0100
@@ -25,7 +25,7 @@
 Table globals     = &ids;
 Table types       = &tys;
 Table labels;
-int level = GLOBAL;
+int level_lcc = GLOBAL;
 static int tempid;
 List loci, symbols;
 
@@ -55,18 +55,18 @@
 	}
 }
 void enterscope(void) {
-	if (++level == LOCAL)
+	if (++level_lcc == LOCAL)
 		tempid = 0;
 }
 void exitscope(void) {
-	rmtypes(level);
-	if (types->level == level)
+	rmtypes(level_lcc);
+	if (types->level == level_lcc)
 		types = types->previous;
-	if (identifiers->level == level) {
+	if (identifiers->level == level_lcc) {
 		if (Aflag >= 2) {
 			int n = 0;
 			Symbol p;
-			for (p = identifiers->all; p && p->scope == level; p = p->up)
+			for (p = identifiers->all; p && p->scope == level_lcc; p = p->up)
 				if (++n > 127) {
 					warning("more than 127 identifiers declared in a block\n");
 					break;
@@ -74,8 +74,8 @@
 		}
 		identifiers = identifiers->previous;
 	}
-	assert(level >= GLOBAL);
-	--level;
+	assert(level_lcc >= GLOBAL);
+	--level_lcc;
 }
 Symbol install(const char *name, Table *tpp, int level, int arena) {
 	Table tp = *tpp;
@@ -217,7 +217,7 @@
 
 	NEW0(p, FUNC);
 	p->name = stringd(++tempid);
-	p->scope = level < LOCAL ? LOCAL : level;
+	p->scope = level_lcc < LOCAL ? LOCAL : level_lcc;
 	p->sclass = scls;
 	p->type = ty;
 	p->temporary = 1;

```
