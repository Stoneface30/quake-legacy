# Diff: `lcc/src/bytecode.c`
**Canonical:** `quake3-source` (sha256 `1127e378e2dc...`, 8466 bytes)

## Variants

### `q3vm`  — sha256 `730441862a69...`, 8488 bytes

_Diff stat: +16 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\bytecode.c	2026-04-16 20:02:20.079593000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\bytecode.c	2026-04-16 22:48:28.094134000 +0100
@@ -40,8 +40,9 @@
 	case P: print("byte %d %U\n", size, (unsigned long)v.p); return;
 	case F:
 		if (size == 4) {
-			float f = v.d;
-			print("byte 4 %u\n", *(unsigned *)&f);
+			floatint_t fi;
+			fi.f = v.d;
+			print("byte 4 %u\n", fi.ui);
 		} else {
 			unsigned *p = (unsigned *)&v.d;
 			print("byte 4 %u\n", p[swap]);
@@ -67,10 +68,10 @@
 		case P: p->x.name = stringf("%U", p->u.c.v.p); break;
 		case F:
 			{	// JDC: added this to get inline floats
-				unsigned temp;
+				floatint_t temp;
 
-				*(float *)&temp = p->u.c.v.d;
-				p->x.name = stringf("%U", temp );
+				temp.f = p->u.c.v.d;
+				p->x.name = stringf("%U", temp.ui );
 			}
 			break;// JDC: added this
 		default: assert(0);
@@ -320,16 +321,16 @@
 #define b_blockend blockend
 
 Interface bytecodeIR = {
-	1, 1, 0,	/* char */
-	2, 2, 0,	/* short */
-	4, 4, 0,	/* int */
-	4, 4, 0,	/* long */
-	4, 4, 0,	/* long long */
-	4, 4, 0,	/* float */				// JDC: use inline floats
-	4, 4, 0,	/* double */			// JDC: don't ever emit 8 byte double code
-	4, 4, 0,	/* long double */		// JDC: don't ever emit 8 byte double code
-	4, 4, 0,	/* T* */
-	0, 4, 0,	/* struct */
+	{1, 1, 0},	/* char */
+	{2, 2, 0},	/* short */
+	{4, 4, 0},	/* int */
+	{4, 4, 0},	/* long */
+	{4, 4, 0},	/* long long */
+	{4, 4, 0},	/* float */				// JDC: use inline floats
+	{4, 4, 0},	/* double */			// JDC: don't ever emit 8 byte double code
+	{4, 4, 0},	/* long double */		// JDC: don't ever emit 8 byte double code
+	{4, 4, 0},	/* T* */
+	{0, 4, 0},	/* struct */
 	0,		/* little_endian */
 	0,		/* mulops_calls */
 	0,		/* wants_callb */

```
