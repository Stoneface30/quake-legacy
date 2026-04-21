# Diff: `lcc/src/simp.c`
**Canonical:** `quake3-source` (sha256 `4489e2ef87f7...`, 16974 bytes)

## Variants

### `q3vm`  — sha256 `db81532bc281...`, 17032 bytes

_Diff stat: +38 / -38 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\simp.c	2026-04-16 20:02:20.086105100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\simp.c	2026-04-16 22:48:28.099132300 +0100
@@ -53,10 +53,10 @@
 int explicitCast;
 static int addi(long x, long y, long min, long max, int needconst) {
 	int cond = x == 0 || y == 0
-	|| x < 0 && y < 0 && x >= min - y
-	|| x < 0 && y > 0
-	|| x > 0 && y < 0
-	|| x > 0 && y > 0 && x <= max - y;
+	|| (x < 0 && y < 0 && x >= min - y)
+	|| (x < 0 && y > 0)
+	|| (x > 0 && y < 0)
+	|| (x > 0 && y > 0 && x <= max - y);
 	if (!cond && needconst) {
 		warning("overflow in constant expression\n");
 		cond = 1;
@@ -68,10 +68,10 @@
 
 static int addd(double x, double y, double min, double max, int needconst) {
 	int cond = x == 0 || y == 0
-	|| x < 0 && y < 0 && x >= min - y
-	|| x < 0 && y > 0
-	|| x > 0 && y < 0
-	|| x > 0 && y > 0 && x <= max - y;
+	|| (x < 0 && y < 0 && x >= min - y)
+	|| (x < 0 && y > 0)
+	|| (x > 0 && y < 0)
+	|| (x > 0 && y > 0 && x <= max - y);
 	if (!cond && needconst) {
 		warning("overflow in constant expression\n");
 		cond = 1;
@@ -146,11 +146,11 @@
 
 /* mul[id] - return 1 if min <= x*y <= max, 0 otherwise */
 static int muli(long x, long y, long min, long max, int needconst) {
-	int cond = x > -1 && x <= 1 || y > -1 && y <= 1
-	|| x < 0 && y < 0 && -x <= max/-y
-	|| x < 0 && y > 0 &&  x >= min/y
-	|| x > 0 && y < 0 &&  y >= min/x
-	|| x > 0 && y > 0 &&  x <= max/y;
+	int cond = (x > -1 && x <= 1) || (y > -1 && y <= 1)
+	|| (x < 0 && y < 0 && -x <= max/-y)
+	|| (x < 0 && y > 0 &&  x >= min/y)
+	|| (x > 0 && y < 0 &&  y >= min/x)
+	|| (x > 0 && y > 0 &&  x <= max/y);
 	if (!cond && needconst) {
 		warning("overflow in constant expression\n");
 		cond = 1;
@@ -161,11 +161,11 @@
 }
 
 static int muld(double x, double y, double min, double max, int needconst) {
-	int cond = x >= -1 && x <= 1 || y >= -1 && y <= 1
-	|| x < 0 && y < 0 && -x <= max/-y
-	|| x < 0 && y > 0 &&  x >= min/y
-	|| x > 0 && y < 0 &&  y >= min/x
-	|| x > 0 && y > 0 &&  x <= max/y;
+	int cond = (x >= -1 && x <= 1) || (y >= -1 && y <= 1)
+	|| (x < 0 && y < 0 && -x <= max/-y)
+	|| (x < 0 && y > 0 &&  x >= min/y)
+	|| (x > 0 && y < 0 &&  y >= min/x)
+	|| (x > 0 && y > 0 &&  x <= max/y);
 	if (!cond && needconst) {
 		warning("overflow in constant expression\n");
 		cond = 1;
@@ -182,7 +182,7 @@
 static int subd(double x, double y, double min, double max, int needconst) {
 	return addd(x, -y, min, max, needconst);
 }
-Tree constexpr(int tok) {
+Tree constexpression(int tok) {
 	Tree p;
 
 	needconst++;
@@ -192,7 +192,7 @@
 }
 
 int intexpr(int tok, int n) {
-	Tree p = constexpr(tok);
+	Tree p = constexpression(tok);
 
 	needconst++;
 	if (p->op == CNST+I || p->op == CNST+U)
@@ -204,7 +204,6 @@
 }
 Tree simplify(int op, Type ty, Tree l, Tree r) {
 	int n;
-	Tree p;
 
 	if (optype(op) == 0)
 		op = mkop(op, ty);
@@ -247,23 +246,24 @@
 			break;
 
 		case CVI+F:
-			xcvtcnst(I,l->u.v.i,ty,d,(long double)l->u.v.i);
+			xcvtcnst(I,l->u.v.i,ty,d,(double)l->u.v.i);
 		case CVU+F:
-			xcvtcnst(U,l->u.v.u,ty,d,(long double)l->u.v.u);
+			xcvtcnst(U,l->u.v.u,ty,d,(double)l->u.v.u);
 			break;
 		case CVF+I:
 			xcvtcnst(F,l->u.v.d,ty,i,(long)l->u.v.d);
 			break;
 		case CVF+F: {
-			float d;
-			if (l->op == CNST+F)
+			float d = 0.0f;
+			if (l->op == CNST+F) {
 				if (l->u.v.d < ty->u.sym->u.limits.min.d)
 					d = ty->u.sym->u.limits.min.d;
 				else if (l->u.v.d > ty->u.sym->u.limits.max.d)
 					d = ty->u.sym->u.limits.max.d;
 				else
 					d = l->u.v.d;
-			xcvtcnst(F,l->u.v.d,ty,d,(long double)d);
+			}
+			xcvtcnst(F,l->u.v.d,ty,d,(double)d);
 			break;
 			}
 		case BAND+U:
@@ -308,14 +308,14 @@
 			identity(r,retype(l,ty),I,i,0);
 			identity(r,retype(l,ty),U,u,0);
 			if (isaddrop(l->op)
-			&& (r->op == CNST+I && r->u.v.i <= longtype->u.sym->u.limits.max.i
-			    && r->u.v.i >= longtype->u.sym->u.limits.min.i
-			|| r->op == CNST+U && r->u.v.u <= longtype->u.sym->u.limits.max.i))
+			&& ((r->op == CNST+I && r->u.v.i <= longtype->u.sym->u.limits.max.i
+			    && r->u.v.i >= longtype->u.sym->u.limits.min.i)
+			|| (r->op == CNST+U && r->u.v.u <= longtype->u.sym->u.limits.max.i)))
 				return addrtree(l, cast(r, longtype)->u.v.i, ty);
 			if (l->op == ADD+P && isaddrop(l->kids[1]->op)
-			&& (r->op == CNST+I && r->u.v.i <= longtype->u.sym->u.limits.max.i
-			    && r->u.v.i >= longtype->u.sym->u.limits.min.i
-			||  r->op == CNST+U && r->u.v.u <= longtype->u.sym->u.limits.max.i))
+			&& ((r->op == CNST+I && r->u.v.i <= longtype->u.sym->u.limits.max.i
+			    && r->u.v.i >= longtype->u.sym->u.limits.min.i)
+			||  (r->op == CNST+U && r->u.v.u <= longtype->u.sym->u.limits.max.i)))
 				return simplify(ADD+P, ty, l->kids[0],
 					addrtree(l->kids[1], cast(r, longtype)->u.v.i, ty));
 			if ((l->op == ADD+I || l->op == SUB+I)
@@ -385,9 +385,9 @@
 			break;
 		case DIV+I:
 			identity(r,l,I,i,1);
-			if (r->op == CNST+I && r->u.v.i == 0
-			||  l->op == CNST+I && l->u.v.i == ty->u.sym->u.limits.min.i
-			&&  r->op == CNST+I && r->u.v.i == -1)
+			if ((r->op == CNST+I && r->u.v.i == 0)
+			||  (l->op == CNST+I && l->u.v.i == ty->u.sym->u.limits.min.i
+			&&  r->op == CNST+I && r->u.v.i == -1))
 				break;
 			xfoldcnst(I,i,/,divi);
 			break;
@@ -465,9 +465,9 @@
 		case MOD+I:
 			if (r->op == CNST+I && r->u.v.i == 1)	/* l%1 => (l,0) */
 				return tree(RIGHT, ty, root(l), cnsttree(ty, 0L));
-			if (r->op == CNST+I && r->u.v.i == 0
-			||  l->op == CNST+I && l->u.v.i == ty->u.sym->u.limits.min.i
-			&&  r->op == CNST+I && r->u.v.i == -1)
+			if ((r->op == CNST+I && r->u.v.i == 0)
+			||  (l->op == CNST+I && l->u.v.i == ty->u.sym->u.limits.min.i
+			&&  r->op == CNST+I && r->u.v.i == -1))
 				break;
 			xfoldcnst(I,i,%,divi);
 			break;

```
