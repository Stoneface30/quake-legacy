# Diff: `lcc/src/decl.c`
**Canonical:** `quake3-source` (sha256 `968be3ad1e0b...`, 32417 bytes)

## Variants

### `q3vm`  — sha256 `daa048df0023...`, 32477 bytes

_Diff stat: +22 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\decl.c	2026-04-16 20:02:20.081593400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\decl.c	2026-04-16 22:48:28.096133300 +0100
@@ -115,10 +115,10 @@
 		type = INT;
 		ty = inttype;
 	}
-	if (size == SHORT     && type != INT
-	||  size == LONG+LONG && type != INT
-	||  size == LONG      && type != INT && type != DOUBLE
-	||  sign && type != INT && type != CHAR)
+	if ((size == SHORT     && type != INT)
+	||  (size == LONG+LONG && type != INT)
+	||  (size == LONG      && type != INT && type != DOUBLE)
+	||  (sign && type != INT && type != CHAR))
 		error("invalid type specification\n");
 	if (type == CHAR && sign)
 		ty = sign == UNSIGNED ? unsignedchar : signedchar;
@@ -196,7 +196,7 @@
 		}
 	} else if (ty == NULL
 	|| !(isenum(ty) ||
-	     isstruct(ty) && (*unqual(ty)->u.sym->name < '1' || *unqual(ty)->u.sym->name > '9')))
+	     (isstruct(ty) && (*unqual(ty)->u.sym->name < '1' || *unqual(ty)->u.sym->name > '9'))))
 		error("empty declaration\n");
 	test(';', stop);
 }
@@ -220,9 +220,9 @@
 		if (!isfunc(ty) && p->defined && t == '=')
 			error("redefinition of `%s' previously defined at %w\n", p->name, &p->src);
 
-		if (p->sclass == EXTERN && sclass == STATIC
-		||  p->sclass == STATIC && sclass == AUTO
-		||  p->sclass == AUTO   && sclass == STATIC)
+		if ((p->sclass == EXTERN && sclass == STATIC)
+		||  (p->sclass == STATIC && sclass == AUTO)
+		||  (p->sclass == AUTO   && sclass == STATIC))
 			warning("inconsistent linkage for `%s' previously declared at %w\n", p->name, &p->src);
 
 	}
@@ -416,7 +416,7 @@
 				error("missing parameter type\n");
 			n++;
 			ty = dclr(specifier(&sclass), &id, NULL, 1);
-			if ( ty == voidtype && (ty1 || id)
+			if ( (ty == voidtype && (ty1 || id))
 			||  ty1 == voidtype)
 				error("illegal formal parameter types\n");
 			if (id == NULL)
@@ -736,10 +736,10 @@
 		if (ty->u.f.oldstyle)
 			warning("`%t %s()' is a non-ANSI definition\n", rty, id);
 		else if (!(rty == inttype
-			&& (n == 0 && callee[0] == NULL
-			||  n == 2 && callee[0]->type == inttype
+			&& ((n == 0 && callee[0] == NULL)
+			||  (n == 2 && callee[0]->type == inttype
 			&& isptr(callee[1]->type) && callee[1]->type->type == charptype
-			&& !variadic(ty))))
+			&& !variadic(ty)))))
 			warning("`%s' is a non-ANSI definition\n", typestring(ty, id));
 	}
 	p = lookup(id, identifiers);
@@ -853,7 +853,7 @@
 		registers = append(retv, registers);
 	}
 	while (kind[t] == CHAR || kind[t] == STATIC
-	|| istypename(t, tsym) && getchr() != ':')
+	|| (istypename(t, tsym) && getchr() != ':'))
 		decl(dcllocal);
 	{
 		int i;
@@ -908,7 +908,7 @@
 				p->type, p->name);
 	}
 	if (p->sclass == AUTO
-	&& (p->scope  == PARAM && regcount == 0
+	&& ((p->scope  == PARAM && regcount == 0)
 	 || p->scope  >= LOCAL)
 	&& !p->addressed && isscalar(p->type) && p->ref >= 3.0)
 		p->sclass = REGISTER;
@@ -933,13 +933,14 @@
 		sclass = AUTO;
 	}
 	q = lookup(id, identifiers);
-	if (q && q->scope >= level
-	||  q && q->scope == PARAM && level == LOCAL)
+	if ((q && q->scope >= level)
+	||  (q && q->scope == PARAM && level == LOCAL)) {
 		if (sclass == EXTERN && q->sclass == EXTERN
 		&& eqtype(q->type, ty, 1))
 			ty = compose(ty, q->type);
 		else
 			error("redeclaration of `%s' previously declared at %w\n", q->name, &q->src);
+	}
 
 	assert(level >= LOCAL);
 	p = install(id, &identifiers, level, sclass == STATIC || sclass == EXTERN ? PERM : FUNC);
@@ -964,13 +965,14 @@
 		       p->u.alias = q; break;
 	case STATIC:   (*IR->defsymbol)(p);
 		       initglobal(p, 0);
-		       if (!p->defined)
+		       if (!p->defined) {
 		       	if (p->type->size > 0) {
 		       		defglobal(p, BSS);
 		       		(*IR->space)(p->type->size);
 		       	} else
 		       		error("undefined size for `%t %s'\n",
 		       			p->type, p->name);
+		       }
 		       p->defined = 1; break;
 	case REGISTER: registers = append(p, registers);
 		       regcount++;
@@ -987,7 +989,7 @@
 		t = gettok();
 		definept(NULL);
 		if (isscalar(p->type)
-		||  isstruct(p->type) && t != '{') {
+		||  (isstruct(p->type) && t != '{')) {
 			if (t == '{') {
 				t = gettok();
 				e = expr1(0);
@@ -1027,7 +1029,7 @@
 }
 static void doglobal(Symbol p, void *cl) {
 	if (!p->defined && (p->sclass == EXTERN
-	|| isfunc(p->type) && p->sclass == AUTO))
+	|| (isfunc(p->type) && p->sclass == AUTO)))
 		(*IR->import)(p);
 	else if (!p->defined && !isfunc(p->type)
 	&& (p->sclass == AUTO || p->sclass == STATIC)) {
@@ -1077,7 +1079,7 @@
 Type enumdcl(void) {
 	char *tag;
 	Type ty;
-	Symbol p;
+	Symbol p = {0};
 	Coordinate pos;
 
 	t = gettok();

```
