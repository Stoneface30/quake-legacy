# Diff: `code/tools/lcc/src/tree.c`
**Canonical:** `wolfcamql-src` (sha256 `52335e3a66bc...`, 5359 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `4fdd27edbbe3...`, 5356 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\tree.c	2026-04-16 20:02:25.815935600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\tree.c	2026-04-16 22:48:25.957097700 +0100
@@ -86,7 +86,7 @@
 			warning("reference to `%t' elided\n", p->type);
 		if (isptr(p->kids[0]->type) && isvolatile(p->kids[0]->type->type))
 			warning("reference to `volatile %t' elided\n", p->type);
-		/* fall through */
+		/* fall thru */
 	case CVI: case CVF: case CVU: case CVP:
 	case NEG: case BCOM: case FIELD:
 		if (warn++ == 0)

```
