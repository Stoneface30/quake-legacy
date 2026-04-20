# Diff: `lcc/cpp/tokens.c`
**Canonical:** `quake3-source` (sha256 `dc40830f2ab1...`, 7170 bytes)

## Variants

### `q3vm`  — sha256 `3fbc2b954d5b...`, 7191 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\tokens.c	2026-04-16 20:02:20.044692500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\tokens.c	2026-04-16 22:48:28.090019500 +0100
@@ -154,14 +154,14 @@
 		return;
 	if (tp->wslen) {
 		if (tp->flag&XPWS
-		 && (wstab[tp->type] || trp->tp>trp->bp && wstab[(tp-1)->type])) {
+		 && (wstab[tp->type] || (trp->tp>trp->bp && wstab[(tp-1)->type]))) {
 			tp->wslen = 0;
 			return;
 		}
 		tp->t[-1] = ' ';
 		return;
 	}
-	if (wstab[tp->type] || trp->tp>trp->bp && wstab[(tp-1)->type])
+	if (wstab[tp->type] || (trp->tp>trp->bp && wstab[(tp-1)->type]))
 		return;
 	tt = newstring(tp->t, tp->len, 1);
 	*tt++ = ' ';
@@ -267,7 +267,7 @@
 	if (str)
 		fprintf(stderr, "%s ", str);
 	if (tp<trp->bp || tp>trp->lp)
-		fprintf(stderr, "(tp offset %d) ", tp-trp->bp);
+		fprintf(stderr, "(tp offset %ld) ", (long int) (tp - trp->bp));
 	for (tp=trp->bp; tp<trp->lp && tp<trp->bp+32; tp++) {
 		if (tp->type!=NL) {
 			int c = tp->t[tp->len];
@@ -315,7 +315,7 @@
 		if (wbp >= &wbuf[OBS]) {
 			write(1, wbuf, OBS);
 			if (wbp > &wbuf[OBS])
-				memcpy(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
+				memmove(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
 			wbp -= OBS;
 		}
 	}

```
