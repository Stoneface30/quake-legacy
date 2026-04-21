# Diff: `lcc/src/types.c`
**Canonical:** `quake3-source` (sha256 `10dd49214871...`, 21599 bytes)

## Variants

### `q3vm`  — sha256 `77087cfe3185...`, 21607 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\types.c	2026-04-16 20:02:20.088617200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\types.c	2026-04-16 22:48:28.101258000 +0100
@@ -233,8 +233,8 @@
 			ty->align, NULL);
 	else if (isfunc(ty))
 		warning("qualified function type ignored\n");
-	else if (isconst(ty)    && op == CONST
-	||       isvolatile(ty) && op == VOLATILE)
+	else if ((isconst(ty)    && op == CONST)
+	||       (isvolatile(ty) && op == VOLATILE))
 		error("illegal type `%k %t'\n", op, ty);
 	else {
 		if (isqual(ty)) {
@@ -276,7 +276,7 @@
 		tag = stringd(genlabel(1));
 	else
 		if ((p = lookup(tag, types)) != NULL && (p->scope == level
-		|| p->scope == PARAM && level == PARAM+1)) {
+		|| (p->scope == PARAM && level == PARAM+1))) {
 			if (p->type->op == op && !p->defined)
 				return p->type;
 			error("redefinition of `%s' previously defined at %w\n",
@@ -400,7 +400,7 @@
 	case CONST: case VOLATILE:
 		return qual(ty1->op, compose(ty1->type, ty2->type));
 	case ARRAY:    { Type ty = compose(ty1->type, ty2->type);
-			 if (ty1->size && (ty1->type->size && ty2->size == 0 || ty1->size == ty2->size))
+			 if (ty1->size && ((ty1->type->size && ty2->size == 0) || ty1->size == ty2->size))
 			 	return array(ty, ty1->size/ty1->type->size, ty1->align);
 			 if (ty2->size && ty2->type->size && ty1->size == 0)
 			 	return array(ty, ty2->size/ty2->type->size, ty2->align);

```
