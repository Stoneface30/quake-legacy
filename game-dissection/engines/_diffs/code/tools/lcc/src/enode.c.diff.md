# Diff: `code/tools/lcc/src/enode.c`
**Canonical:** `wolfcamql-src` (sha256 `9e16069590f2...`, 14812 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `b1e50a500037...`, 14847 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\enode.c	2026-04-16 20:02:25.809415100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\enode.c	2026-04-16 22:48:25.952097400 +0100
@@ -5,6 +5,7 @@
 static Tree andtree(int, Tree, Tree);
 static Tree cmptree(int, Tree, Tree);
 static int compatible(Type, Type);
+static int isnullptr(Tree e);
 static Tree multree(int, Tree, Tree);
 static Tree subtree(int, Tree, Tree);
 #define isvoidptr(ty) \
@@ -219,7 +220,7 @@
 	    && isptr(ty2) && !isfunc(ty2->type)
 	    && eqtype(unqual(ty1->type), unqual(ty2->type), 0);
 }
-int isnullptr(Tree e) {
+static int isnullptr(Tree e) {
 	Type ty = unqual(e->type);
 
 	return generic(e->op) == CNST
@@ -401,7 +402,7 @@
 			Symbol t1 = q->u.sym;
 			q->u.sym = 0;
 			q = idtree(t1);
-			/* fall through */
+			/* fall thru */
 			}
 		case INDIR:
 			if (p == q)

```

### `openarena-gamecode`  — sha256 `001ec1056584...`, 14851 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\enode.c	2026-04-16 20:02:25.809415100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\enode.c	2026-04-16 22:48:24.207078400 +0100
@@ -5,6 +5,7 @@
 static Tree andtree(int, Tree, Tree);
 static Tree cmptree(int, Tree, Tree);
 static int compatible(Type, Type);
+static int isnullptr(Tree e);
 static Tree multree(int, Tree, Tree);
 static Tree subtree(int, Tree, Tree);
 #define isvoidptr(ty) \
@@ -219,7 +220,7 @@
 	    && isptr(ty2) && !isfunc(ty2->type)
 	    && eqtype(unqual(ty1->type), unqual(ty2->type), 0);
 }
-int isnullptr(Tree e) {
+static int isnullptr(Tree e) {
 	Type ty = unqual(e->type);
 
 	return generic(e->op) == CNST
@@ -373,7 +374,7 @@
 	case CNST+F: return cast(e->u.v.d != 0.0 ? l : r, ty);
 	}
 	if (ty != voidtype && ty->size > 0) {
-		t1 = genident(REGISTER, unqual(ty), level);
+		t1 = genident(REGISTER, unqual(ty), level_lcc);
 	/*	t1 = temporary(REGISTER, unqual(ty)); */
 		l = asgn(t1, l);
 		r = asgn(t1, r);
@@ -401,7 +402,7 @@
 			Symbol t1 = q->u.sym;
 			q->u.sym = 0;
 			q = idtree(t1);
-			/* fall through */
+			/* fall thru */
 			}
 		case INDIR:
 			if (p == q)

```
