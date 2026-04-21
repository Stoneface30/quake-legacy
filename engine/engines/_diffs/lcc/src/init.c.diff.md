# Diff: `lcc/src/init.c`
**Canonical:** `quake3-source` (sha256 `03d7c5077b6b...`, 8106 bytes)

## Variants

### `q3vm`  — sha256 `e40e4aed9f1a...`, 8119 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\init.c	2026-04-16 20:02:20.082592500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\init.c	2026-04-16 22:48:28.097134900 +0100
@@ -40,7 +40,7 @@
 			if (isarith(e->type))
 				error("cast from `%t' to `%t' is illegal in constant expressions\n",
 					e->kids[0]->type, e->type);
-			/* fall thru */
+			/* fall through */
 		case CVI: case CVU: case CVF:
 			e = e->kids[0];
 			continue;
@@ -81,7 +81,7 @@
 	do {
 		initializer(ty, lev);
 		n += ty->size;
-		if (len > 0 && n >= len || t != ',')
+		if ((len > 0 && n >= len) || t != ',')
 			break;
 		t = gettok();
 	} while (t != '}');
@@ -99,7 +99,7 @@
 			(*IR->defstring)(inttype->size, buf);
 			s = buf;
 		}
-		if (len > 0 && n >= len || t != ',')
+		if ((len > 0 && n >= len) || t != ',')
 			break;
 		t = gettok();
 	} while (t != '}');
@@ -123,9 +123,9 @@
 	do {
 		i = initvalue(inttype)->u.v.i;
 		if (fieldsize(p) < 8*p->type->size) {
-			if (p->type == inttype &&
-			   (i < -(int)(fieldmask(p)>>1)-1 || i > (int)(fieldmask(p)>>1))
-			||  p->type == unsignedtype && (i&~fieldmask(p)) !=  0)
+			if ((p->type == inttype &&
+			   (i < -(int)(fieldmask(p)>>1)-1 || i > (int)(fieldmask(p)>>1)))
+			||  (p->type == unsignedtype && (i&~fieldmask(p)) !=  0))
 				warning("initializer exceeds bit-field width\n");
 			i &= fieldmask(p);
 		}
@@ -185,7 +185,7 @@
 			(*IR->space)(a - n%a);
 			n = roundup(n, a);
 		}
-		if (len > 0 && n >= len || t != ',')
+		if ((len > 0 && n >= len) || t != ',')
 			break;
 		t = gettok();
 	} while (t != '}');

```
