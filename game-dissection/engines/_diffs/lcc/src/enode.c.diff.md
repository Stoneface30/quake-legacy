# Diff: `lcc/src/enode.c`
**Canonical:** `quake3-source` (sha256 `9716f94fa26b...`, 14748 bytes)

## Variants

### `q3vm`  — sha256 `9e16069590f2...`, 14812 bytes

_Diff stat: +35 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\enode.c	2026-04-16 20:02:20.081593400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\enode.c	2026-04-16 22:48:28.096133300 +0100
@@ -5,7 +5,6 @@
 static Tree andtree(int, Tree, Tree);
 static Tree cmptree(int, Tree, Tree);
 static int compatible(Type, Type);
-static int isnullptr(Tree e);
 static Tree multree(int, Tree, Tree);
 static Tree subtree(int, Tree, Tree);
 #define isvoidptr(ty) \
@@ -64,7 +63,7 @@
 					else
 						q = cast(q, promote(q->type));
 				}
-			if (!IR->wants_argb && isstruct(q->type))
+			if (!IR->wants_argb && isstruct(q->type)) {
 				if (iscallb(q))
 					q = addrof(q);
 				else {
@@ -73,6 +72,7 @@
 					q = tree(RIGHT, ptr(t1->type),
 						root(q), lvalue(idtree(t1)));
 				}
+			}
 			if (q->type->size == 0)
 				q->type = inttype;
 			if (hascall(q))
@@ -183,7 +183,7 @@
 	switch (ty->op) {
 	case INT:     p->u.v.i = va_arg(ap, long); break;
 	case UNSIGNED:p->u.v.u = va_arg(ap, unsigned long)&ones(8*ty->size); break;
-	case FLOAT:   p->u.v.d = va_arg(ap, long double); break;
+	case FLOAT:   p->u.v.d = va_arg(ap, double); break;
 	case POINTER: p->u.v.p = va_arg(ap, void *); break;
 	default: assert(0);
 	}
@@ -219,19 +219,19 @@
 	    && isptr(ty2) && !isfunc(ty2->type)
 	    && eqtype(unqual(ty1->type), unqual(ty2->type), 0);
 }
-static int isnullptr(Tree e) {
+int isnullptr(Tree e) {
 	Type ty = unqual(e->type);
 
 	return generic(e->op) == CNST
-	    && (ty->op == INT      && e->u.v.i == 0
-	     || ty->op == UNSIGNED && e->u.v.u == 0
-	     || isvoidptr(ty)      && e->u.v.p == NULL);
+	    && ((ty->op == INT      && e->u.v.i == 0)
+	     || (ty->op == UNSIGNED && e->u.v.u == 0)
+	     || (isvoidptr(ty)      && e->u.v.p == NULL));
 }
 Tree eqtree(int op, Tree l, Tree r) {
 	Type xty = l->type, yty = r->type;
 
-	if (isptr(xty) && isnullptr(r)
-	||  isptr(xty) && !isfunc(xty->type) && isvoidptr(yty)
+	if ((isptr(xty) && isnullptr(r))
+	||  (isptr(xty) && !isfunc(xty->type) && isvoidptr(yty))
 	||  (isptr(xty) && isptr(yty)
 	    && eqtype(unqual(xty->type), unqual(yty->type), 1))) {
 		Type ty = unsignedptr;
@@ -239,8 +239,8 @@
 		r = cast(r, ty);
 		return simplify(mkop(op,ty), inttype, l, r);
 	}
-	if (isptr(yty) && isnullptr(l)
-	||  isptr(yty) && !isfunc(yty->type) && isvoidptr(xty))
+	if ((isptr(yty) && isnullptr(l))
+	||  (isptr(yty) && !isfunc(yty->type) && isvoidptr(xty)))
 		return eqtree(op, r, l);
 	return cmptree(op, l, r);
 }
@@ -253,13 +253,13 @@
 		xty = xty->type;
 	if (xty->size == 0 || yty->size == 0)
 		return NULL;
-	if ( isarith(xty) && isarith(yty)
-	||  isstruct(xty) && xty == yty)
+	if ( (isarith(xty) && isarith(yty))
+	||  (isstruct(xty) && xty == yty))
 		return xty;
 	if (isptr(xty) && isnullptr(e))
 		return xty;
-	if ((isvoidptr(xty) && isptr(yty)
-	  || isptr(xty)     && isvoidptr(yty))
+	if (((isvoidptr(xty) && isptr(yty))
+	  || (isptr(xty)     && isvoidptr(yty)))
 	&& (  (isconst(xty->type)    || !isconst(yty->type))
 	   && (isvolatile(xty->type) || !isvolatile(yty->type))))
 		return xty;
@@ -273,8 +273,8 @@
 	&& (  (isconst(xty->type)    || !isconst(yty->type))
 	   && (isvolatile(xty->type) || !isvolatile(yty->type)))) {
 		Type lty = unqual(xty->type), rty = unqual(yty->type);
-		if (isenum(lty) && rty == inttype
-		||  isenum(rty) && lty == inttype) {
+		if ((isenum(lty) && rty == inttype)
+		||  (isenum(rty) && lty == inttype)) {
 			if (Aflag >= 1)
 				warning("assignment between `%t' and `%t' is compiler-dependent\n",
 					xty, yty);
@@ -302,13 +302,14 @@
 	if (isptr(aty))
 		aty = unqual(aty)->type;
 	if ( isconst(aty)
-	||  isstruct(aty) && unqual(aty)->u.sym->u.s.cfields)
+	||  (isstruct(aty) && unqual(aty)->u.sym->u.s.cfields)) {
 		if (isaddrop(l->op)
 		&& !l->u.sym->computed && !l->u.sym->generated)
 			error("assignment to const identifier `%s'\n",
 				l->u.sym->name);
 		else
 			error("assignment to const location\n");
+	}
 	if (l->op == FIELD) {
 		long n = 8*l->u.field->type->size - fieldsize(l->u.field);
 		if (n > 0 && isunsigned(l->u.field->type))
@@ -345,8 +346,8 @@
 		ty = xty;
 	else if (isnullptr(l) && isptr(yty))
 		ty = yty;
-	else if (isptr(xty) && !isfunc(xty->type) && isvoidptr(yty)
-	||       isptr(yty) && !isfunc(yty->type) && isvoidptr(xty))
+	else if ((isptr(xty) && !isfunc(xty->type) && isvoidptr(yty))
+	||       (isptr(yty) && !isfunc(yty->type) && isvoidptr(xty)))
 		ty = voidptype;
 	else if ((isptr(xty) && isptr(yty)
 		 && eqtype(unqual(xty->type), unqual(yty->type), 1)))
@@ -357,11 +358,11 @@
 	}
 	if (isptr(ty)) {
 		ty = unqual(unqual(ty)->type);
-		if (isptr(xty) && isconst(unqual(xty)->type)
-		||  isptr(yty) && isconst(unqual(yty)->type))
+		if ((isptr(xty) && isconst(unqual(xty)->type))
+		||  (isptr(yty) && isconst(unqual(yty)->type)))
 			ty = qual(CONST, ty);
-		if (isptr(xty) && isvolatile(unqual(xty)->type)
-		||  isptr(yty) && isvolatile(unqual(yty)->type))
+		if ((isptr(xty) && isvolatile(unqual(xty)->type))
+		||  (isptr(yty) && isvolatile(unqual(yty)->type)))
 			ty = qual(VOLATILE, ty);
 		ty = ptr(ty);
 	}
@@ -400,7 +401,7 @@
 			Symbol t1 = q->u.sym;
 			q->u.sym = 0;
 			q = idtree(t1);
-			/* fall thru */
+			/* fall through */
 			}
 		case INDIR:
 			if (p == q)
@@ -518,15 +519,15 @@
 void typeerror(int op, Tree l, Tree r) {
 	int i;
 	static struct { int op; char *name; } ops[] = {
-		ASGN, "=",	INDIR, "*",	NEG,  "-",
-		ADD,  "+",	SUB,   "-",	LSH,  "<<",
-		MOD,  "%",	RSH,   ">>",	BAND, "&",
-		BCOM, "~",	BOR,   "|",	BXOR, "^",
-		DIV,  "/",	MUL,   "*",	EQ,   "==",
-		GE,   ">=",	GT,    ">",	LE,   "<=",
-		LT,   "<",	NE,    "!=",	AND,  "&&",
-		NOT,  "!",	OR,    "||",	COND, "?:",
-		0, 0
+		{ASGN, "="},	{INDIR, "*"},	{NEG,  "-"},
+		{ADD,  "+"},	{SUB,   "-"},	{LSH,  "<<"},
+		{MOD,  "%"},	{RSH,   ">>"},	{BAND, "&"},
+		{BCOM, "~"},	{BOR,   "|"},	{BXOR, "^"},
+		{DIV,  "/"},	{MUL,   "*"},	{EQ,   "=="},
+		{GE,   ">="},	{GT,    ">"},	{LE,   "<="},
+		{LT,   "<"},	{NE,    "!="},	{AND,  "&&"},
+		{NOT,  "!"},	{OR,    "||"},	{COND, "?:"},
+		{0, 0}
 	};
 
 	op = generic(op);

```
