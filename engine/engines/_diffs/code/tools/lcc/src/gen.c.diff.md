# Diff: `code/tools/lcc/src/gen.c`
**Canonical:** `wolfcamql-src` (sha256 `b198c024e96d...`, 22241 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `d7b61981a3af...`, 22238 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\gen.c	2026-04-16 20:02:25.811417000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\gen.c	2026-04-16 22:48:25.953097500 +0100
@@ -292,7 +292,7 @@
 			dumptree(p->kids[0]);
 			break;
 		}
-		/* else fall through */
+		/* else fall thru */
 	case EQ: case NE: case GT: case GE: case LE: case LT:
 	case ASGN: case BOR: case BAND: case BXOR: case RSH: case LSH:
 	case ADD: case SUB:  case DIV: case MUL: case MOD:

```
