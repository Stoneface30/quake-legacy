# Diff: `lcc/src/gen.c`
**Canonical:** `quake3-source` (sha256 `e9fc9ac35965...`, 22236 bytes)

## Variants

### `q3vm`  — sha256 `b198c024e96d...`, 22241 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\gen.c	2026-04-16 20:02:20.082592500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\gen.c	2026-04-16 22:48:28.097134900 +0100
@@ -292,7 +292,7 @@
 			dumptree(p->kids[0]);
 			break;
 		}
-		/* else fall thru */
+		/* else fall through */
 	case EQ: case NE: case GT: case GE: case LE: case LT:
 	case ASGN: case BOR: case BAND: case BXOR: case RSH: case LSH:
 	case ADD: case SUB:  case DIV: case MUL: case MOD:
@@ -368,7 +368,7 @@
 void emit(Node p) {
 	for (; p; p = p->x.next) {
 		assert(p->x.registered);
-		if (p->x.equatable && requate(p) || moveself(p))
+		if ((p->x.equatable && requate(p)) || moveself(p))
 			;
 		else
 			(*emitter)(p, p->x.inst);

```
