# Diff: `lcc/src/tree.c`
**Canonical:** `quake3-source` (sha256 `4fdd27edbbe3...`, 5356 bytes)

## Variants

### `q3vm`  — sha256 `52335e3a66bc...`, 5359 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\tree.c	2026-04-16 20:02:20.088617200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\tree.c	2026-04-16 22:48:28.101258000 +0100
@@ -86,7 +86,7 @@
 			warning("reference to `%t' elided\n", p->type);
 		if (isptr(p->kids[0]->type) && isvolatile(p->kids[0]->type->type))
 			warning("reference to `volatile %t' elided\n", p->type);
-		/* fall thru */
+		/* fall through */
 	case CVI: case CVF: case CVU: case CVP:
 	case NEG: case BCOM: case FIELD:
 		if (warn++ == 0)

```
