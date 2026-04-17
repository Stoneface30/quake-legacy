# Diff: `code/tools/lcc/src/types.c`
**Canonical:** `wolfcamql-src` (sha256 `77087cfe3185...`, 21607 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `openarena-gamecode`  — sha256 `2cb19e9558ba...`, 21623 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\types.c	2026-04-16 20:02:25.815935600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\types.c	2026-04-16 22:48:24.211592100 +0100
@@ -275,14 +275,14 @@
 	if (*tag == 0)
 		tag = stringd(genlabel(1));
 	else
-		if ((p = lookup(tag, types)) != NULL && (p->scope == level
-		|| (p->scope == PARAM && level == PARAM+1))) {
+		if ((p = lookup(tag, types)) != NULL && (p->scope == level_lcc
+		|| (p->scope == PARAM && level_lcc == PARAM+1))) {
 			if (p->type->op == op && !p->defined)
 				return p->type;
 			error("redefinition of `%s' previously defined at %w\n",
 				p->name, &p->src);
 		}
-	p = install(tag, &types, level, PERM);
+	p = install(tag, &types, level_lcc, PERM);
 	p->type = type(op, NULL, 0, 0, p);
 	if (p->scope > maxlevel)
 		maxlevel = p->scope;
@@ -304,7 +304,7 @@
 	p->type = fty;
 	if (xref) {							/* omit */
 		if (ty->u.sym->u.s.ftab == NULL)			/* omit */
-			ty->u.sym->u.s.ftab = table(NULL, level);	/* omit */
+			ty->u.sym->u.s.ftab = table(NULL, level_lcc);	/* omit */
 		install(name, &ty->u.sym->u.s.ftab, 0, PERM)->src = src;/* omit */
 	}								/* omit */
 	return p;

```
