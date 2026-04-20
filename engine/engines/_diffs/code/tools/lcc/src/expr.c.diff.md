# Diff: `code/tools/lcc/src/expr.c`
**Canonical:** `wolfcamql-src` (sha256 `43f30a787213...`, 19087 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `d1600fd41327...`, 19041 bytes

_Diff stat: +7 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\expr.c	2026-04-16 20:02:25.810416200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\expr.c	2026-04-16 22:48:25.952097400 +0100
@@ -159,8 +159,7 @@
 						  if (isarith(p->type))
 						  	p = cast(p, promote(p->type));
 						  else
-							typeerror(ADD, p, NULL);
-						  break;
+						  	typeerror(ADD, p, NULL);  break;
 	case '-':    t = gettok(); p = unary(); p = pointer(p);
 						  if (isarith(p->type)) {
 						  	Type ty = promote(p->type);
@@ -171,21 +170,18 @@
 						  	} else
 						  		p = simplify(NEG, ty, p, NULL);
 						  } else
-							typeerror(SUB, p, NULL);
-						  break;
+						  	typeerror(SUB, p, NULL); break;
 	case '~':    t = gettok(); p = unary(); p = pointer(p);
 						  if (isint(p->type)) {
 						  	Type ty = promote(p->type);
 						  	p = simplify(BCOM, ty, cast(p, ty), NULL);
 						  } else
-							typeerror(BCOM, p, NULL);
-						  break;
+						  	typeerror(BCOM, p, NULL);  break;
 	case '!':    t = gettok(); p = unary(); p = pointer(p);
 						  if (isscalar(p->type))
 						  	p = simplify(NOT, inttype, cond(p), NULL);
 						  else
-							typeerror(NOT, p, NULL);
-						  break;
+						  	typeerror(NOT, p, NULL); break;
 	case INCR:   t = gettok(); p = unary(); p = incr(INCR, pointer(p), consttree(1, inttype)); break;
 	case DECR:   t = gettok(); p = unary(); p = incr(DECR, pointer(p), consttree(1, inttype)); break;
 	case TYPECODE: case SIZEOF: { int op = t;
@@ -322,8 +318,7 @@
 			    			p->type);
 			    	t = gettok();
 			    } else
-					error("field name expected\n");
-				break;
+			    	error("field name expected\n"); break;
 		case DEREF: t = gettok();
 			    p = pointer(p);
 			    if (t == ID) {
@@ -336,8 +331,7 @@
 
 			    	t = gettok();
 			    } else
-					error("field name expected\n");
-				break;
+			    	error("field name expected\n"); break;
 		default:
 			return p;
 		}
@@ -627,7 +621,7 @@
 			p = simplify(CVP, dst, p, NULL);
 		else {
 			if ((isfunc(src->type) && !isfunc(dst->type))
-			|| (!isnullptr(p) && !isfunc(src->type) && isfunc(dst->type)))
+			|| (!isfunc(src->type) &&  isfunc(dst->type)))
 				warning("conversion from `%t' to `%t' is compiler dependent\n", p->type, type);
 
 			if (src->size != dst->size)

```

### `openarena-gamecode`  — sha256 `5513ec46de5c...`, 18755 bytes

_Diff stat: +403 / -355 lines_

_(full diff is 28094 bytes — see files directly)_
