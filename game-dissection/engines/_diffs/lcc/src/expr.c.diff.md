# Diff: `lcc/src/expr.c`
**Canonical:** `quake3-source` (sha256 `e0ea6f6058ff...`, 19016 bytes)

## Variants

### `q3vm`  — sha256 `e0c4d85648c0...`, 19057 bytes

_Diff stat: +13 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\expr.c	2026-04-16 20:02:20.082592500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\expr.c	2026-04-16 22:48:28.097134900 +0100
@@ -230,13 +230,13 @@
 			pty = p->type;
 			if (isenum(pty))
 				pty = pty->type;
-			if (isarith(pty) && isarith(ty)
-			||  isptr(pty)   && isptr(ty)) {
+			if ((isarith(pty) && isarith(ty))
+			||  (isptr(pty)   && isptr(ty))) {
 				explicitCast++;
 				p = cast(p, ty);
 				explicitCast--;
-			} else if (isptr(pty) && isint(ty)
-			||       isint(pty) && isptr(ty)) {
+			} else if ((isptr(pty) && isint(ty))
+			||       (isint(pty) && isptr(ty))) {
 				if (Aflag >= 1 && ty->size < pty->size)
 					warning("conversion from `%t' to `%t' is compiler dependent\n", p->type, ty);
 
@@ -278,11 +278,12 @@
 			    	Tree q;
 			    	t = gettok();
 			    	q = expr(']');
-			    	if (YYnull)
+			    	if (YYnull) {
 			    		if (isptr(p->type))
 			    			p = nullcheck(p);
 			    		else if (isptr(q->type))
 			    			q = nullcheck(q);
+			    	}
 			    	p = (*optree['+'])(ADD, pointer(p), pointer(q));
 			    	if (isptr(p->type) && isarray(p->type->type))
 			    		p = retype(p, p->type->type);
@@ -497,12 +498,13 @@
 	xx(unsignedlonglong);
 	xx(longlong);
 	xx(unsignedlong);
-	if (xty == longtype     && yty == unsignedtype
-	||  xty == unsignedtype && yty == longtype)
+	if ((xty == longtype     && yty == unsignedtype)
+	||  (xty == unsignedtype && yty == longtype)) {
 		if (longtype->size > unsignedtype->size)
 			return longtype;
 		else
 			return unsignedlong;
+	}
 	xx(longtype);
 	xx(unsignedtype);
 	return inttype;
@@ -569,7 +571,7 @@
 				case UNSIGNED:
 					if (isfloat(dst)) {
 						Type ssrc = signedint(src);
-						Tree two = cnsttree(longdouble, (long double)2.0);
+						Tree two = cnsttree(longdouble, (double)2.0);
 						p = (*optree['+'])(ADD,
 							(*optree['*'])(MUL,
 								two,
@@ -585,7 +587,7 @@
 				case FLOAT:
 					if (isunsigned(dst)) {
 						Type sdst = signedint(dst);
-						Tree c = cast(cnsttree(longdouble, (long double)sdst->u.sym->u.limits.max.i + 1), src);
+						Tree c = cast(cnsttree(longdouble, (double)sdst->u.sym->u.limits.max.i + 1), src);
 						p = condtree(
 							simplify(GE, src, p, c),
 							(*optree['+'])(ADD,
@@ -618,8 +620,8 @@
 		if (src->op != dst->op)
 			p = simplify(CVP, dst, p, NULL);
 		else {
-			if (isfunc(src->type) && !isfunc(dst->type)
-			|| !isfunc(src->type) &&  isfunc(dst->type))
+			if ((isfunc(src->type) && !isfunc(dst->type))
+			|| (!isnullptr(p) && !isfunc(src->type) && isfunc(dst->type)))
 				warning("conversion from `%t' to `%t' is compiler dependent\n", p->type, type);
 
 			if (src->size != dst->size)

```
