# Diff: `lcc/src/lex.c`
**Canonical:** `quake3-source` (sha256 `128114de54f6...`, 22516 bytes)

## Variants

### `q3vm`  — sha256 `970adfc10275...`, 22528 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\lex.c	2026-04-16 20:02:20.084097900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\lex.c	2026-04-16 22:48:28.098133400 +0100
@@ -685,17 +685,18 @@
 			}
 			goto id;
 		default:
-			if ((map[cp[-1]]&BLANK) == 0)
+			if ((map[cp[-1]]&BLANK) == 0) {
 				if (cp[-1] < ' ' || cp[-1] >= 0177)
 					error("illegal character `\\0%o'\n", cp[-1]);
 				else
 					error("illegal character `%c'\n", cp[-1]);
+			}
 		}
 	}
 }
 static Symbol icon(unsigned long n, int overflow, int base) {
-	if ((*cp=='u'||*cp=='U') && (cp[1]=='l'||cp[1]=='L')
-	||  (*cp=='l'||*cp=='L') && (cp[1]=='u'||cp[1]=='U')) {
+	if (((*cp=='u'||*cp=='U') && (cp[1]=='l'||cp[1]=='L'))
+	||  ((*cp=='l'||*cp=='L') && (cp[1]=='u'||cp[1]=='U'))) {
 		tval.type = unsignedlong;
 		cp += 2;
 	} else if (*cp == 'u' || *cp == 'U') {

```
