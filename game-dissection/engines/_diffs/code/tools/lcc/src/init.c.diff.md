# Diff: `code/tools/lcc/src/init.c`
**Canonical:** `wolfcamql-src` (sha256 `2a7fe40708f2...`, 8128 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `52a77061d109...`, 8116 bytes
Also identical in: openarena-gamecode

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\init.c	2026-04-16 20:02:25.811417000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\init.c	2026-04-16 22:48:25.953097500 +0100
@@ -40,7 +40,7 @@
 			if (isarith(e->type))
 				error("cast from `%t' to `%t' is illegal in constant expressions\n",
 					e->kids[0]->type, e->type);
-			/* fall through */
+			/* fall thru */
 		case CVI: case CVU: case CVF:
 			e = e->kids[0];
 			continue;
@@ -192,7 +192,7 @@
 	return n;
 }
 
-/* initializer - constantexpr | { constantexpr ( , constantexpr )* [ , ] } */
+/* initializer - constexpr | { constexpr ( , constexpr )* [ , ] } */
 Type initializer(Type ty, int lev) {
 	int n = 0;
 	Tree e;

```
