# Diff: `lcc/src/output.c`
**Canonical:** `quake3-source` (sha256 `ea1b7ba43e3b...`, 3412 bytes)

## Variants

### `q3vm`  — sha256 `a8738953ea99...`, 3427 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\output.c	2026-04-16 20:02:20.085103100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\output.c	2026-04-16 22:48:28.099132300 +0100
@@ -5,7 +5,7 @@
 	if (f)
 		fputs(str, f);
 	else
-		while (*bp = *str++)
+		while ((*bp = *str++))
 			bp++;
 	return bp;
 }
@@ -95,9 +95,10 @@
 			case 'c': if (f) fputc(va_arg(ap, int), f); else *bp++ = va_arg(ap, int); break;
 			case 'S': { char *s = va_arg(ap, char *);
 				    int n = va_arg(ap, int);
-				    if (s)
+				    if (s) {
 				    	for ( ; n-- > 0; s++)
 				    		if (f) (void)putc(*s, f); else *bp++ = *s;
+				    }
  } break;
 			case 'k': { int t = va_arg(ap, int);
 				    static char *tokens[] = {

```
