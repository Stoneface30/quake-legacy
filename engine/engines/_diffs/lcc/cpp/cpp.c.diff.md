# Diff: `lcc/cpp/cpp.c`
**Canonical:** `quake3-source` (sha256 `1313acc530ac...`, 6221 bytes)

## Variants

### `q3vm`  — sha256 `07d81b36ea8c...`, 6317 bytes

_Diff stat: +10 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\cpp.c	2026-04-16 20:02:20.042587900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\cpp.c	2026-04-16 22:48:28.088019500 +0100
@@ -9,7 +9,7 @@
 
 #define	OUTS	16384
 char	outbuf[OUTS];
-char	*outp = outbuf;
+char	*outbufp = outbuf;
 Source	*cursource;
 int	nerrs;
 struct	token nltoken = { NL, 0, 0, 0, 1, (uchar*)"\n" };
@@ -51,7 +51,7 @@
 	for (;;) {
 		if (trp->tp >= trp->lp) {
 			trp->tp = trp->lp = trp->bp;
-			outp = outbuf;
+			outbufp = outbuf;
 			anymacros |= gettokens(trp, 1);
 			trp->tp = trp->bp;
 		}
@@ -100,7 +100,7 @@
 			error(ERROR, "Unidentifiable control line");
 		return;			/* else empty line */
 	}
-	if ((np = lookup(tp, 0))==NULL || (np->flag&ISKW)==0 && !skipping) {
+	if ((np = lookup(tp, 0))==NULL || ((np->flag&ISKW)==0 && !skipping)) {
 		error(WARNING, "Unknown preprocessor control %t", tp);
 		return;
 	}
@@ -204,9 +204,14 @@
 			error(WARNING, "Syntax error in #endif");
 		break;
 
+	case KWARNING:
+		trp->tp = tp+1;
+		error(WARNING, "#warning directive: %r", trp);
+		break;
+
 	case KERROR:
 		trp->tp = tp+1;
-		error(WARNING, "#error directive: %r", trp);
+		error(ERROR, "#error directive: %r", trp);
 		break;
 
 	case KLINE:
@@ -215,7 +220,7 @@
 		tp = trp->bp+2;
 	kline:
 		if (tp+1>=trp->lp || tp->type!=NUMBER || tp+3<trp->lp
-		 || (tp+3==trp->lp && ((tp+1)->type!=STRING)||*(tp+1)->t=='L')){
+		 || ((tp+3==trp->lp && ((tp+1)->type!=STRING))||*(tp+1)->t=='L')){
 			error(ERROR, "Syntax error in #line");
 			return;
 		}
@@ -245,7 +250,6 @@
 		break;
 	}
 	setempty(trp);
-	return;
 }
 
 void *

```
