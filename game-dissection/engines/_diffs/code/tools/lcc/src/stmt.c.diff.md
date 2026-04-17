# Diff: `code/tools/lcc/src/stmt.c`
**Canonical:** `wolfcamql-src` (sha256 `5905ca92c9cd...`, 17802 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `16c94fc5cdcb...`, 17799 bytes

_Diff stat: +3 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\stmt.c	2026-04-16 20:02:25.814417700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\stmt.c	2026-04-16 22:48:25.956097500 +0100
@@ -119,7 +119,7 @@
 		       		static char stop[] = { IF, ID, 0 };
 		       		Tree p;
 		       		t = gettok();
-		       		p = constantexpr(0);
+		       		p = constexpr(0);
 		       		if (generic(p->op) == CNST && isint(p->type)) {
 		       			if (swp) {
 		       				needconst++;
@@ -184,9 +184,8 @@
 		       	branch(p->u.l.label);
 		       	t = gettok();
 		       } else
-				error("missing label in goto\n");
-			   expect(';');
-			   break;
+		       	error("missing label in goto\n"); expect(';');
+					  break;
 
 	case ID:       if (getchr() == ':') {
 		       	stmtlabel();

```

### `openarena-gamecode`  — sha256 `7fa6ccb6ec34...`, 17242 bytes

_Diff stat: +278 / -250 lines_

_(full diff is 20596 bytes — see files directly)_
