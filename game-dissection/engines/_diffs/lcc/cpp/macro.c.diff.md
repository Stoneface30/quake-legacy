# Diff: `lcc/cpp/macro.c`
**Canonical:** `quake3-source` (sha256 `cb795a848f80...`, 11189 bytes)

## Variants

### `q3vm`  — sha256 `ba730175e7a9...`, 11204 bytes

_Diff stat: +9 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\macro.c	2026-04-16 20:02:20.044692500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\macro.c	2026-04-16 22:48:28.089021000 +0100
@@ -71,7 +71,7 @@
 	if (np->flag&ISDEFINED) {
 		if (comparetokens(def, np->vp)
 		 || (np->ap==NULL) != (args==NULL)
-		 || np->ap && comparetokens(args, np->ap))
+		 || (np->ap && comparetokens(args, np->ap)))
 			error(ERROR, "Macro redefinition of %t", trp->bp+2);
 	}
 	if (args) {
@@ -141,7 +141,7 @@
 		 || quicklook(tp->t[0], tp->len>1?tp->t[1]:0)==0
 		 || (np = lookup(tp, 0))==NULL
 		 || (np->flag&(ISDEFINED|ISMAC))==0
-		 || tp->hideset && checkhideset(tp->hideset, np)) {
+		 || (tp->hideset && checkhideset(tp->hideset, np))) {
 			tp++;
 			continue;
 		}
@@ -218,7 +218,6 @@
 	insertrow(trp, ntokc, &ntr);
 	trp->tp -= rowlen(&ntr);
 	dofree(ntr.bp);
-	return;
 }	
 
 /*
@@ -300,7 +299,7 @@
 			parens--;
 		if (lp->type==DSHARP)
 			lp->type = DSHARP1;	/* ## not special in arg */
-		if (lp->type==COMMA && parens==0 || parens<0 && (lp-1)->type!=LP) {
+		if ((lp->type==COMMA && parens==0) || (parens<0 && (lp-1)->type!=LP)) {
 			if (*narg>=NARG-1)
 				error(FATAL, "Sorry, too many macro arguments");
 			ttr.bp = ttr.tp = bp;
@@ -339,7 +338,7 @@
 		if (rtr->tp->type==NAME
 		 && (argno = lookuparg(np, rtr->tp)) >= 0) {
 			if ((rtr->tp+1)->type==DSHARP
-			 || rtr->tp!=rtr->bp && (rtr->tp-1)->type==DSHARP)
+			 || (rtr->tp!=rtr->bp && (rtr->tp-1)->type==DSHARP))
 				insertrow(rtr, 1, atr[argno]);
 			else {
 				copytokenrow(&tatr, atr[argno]);
@@ -471,10 +470,10 @@
 	/* most are strings */
 	tp->type = STRING;
 	if (tp->wslen) {
-		*outp++ = ' ';
+		*outbufp++ = ' ';
 		tp->wslen = 1;
 	}
-	op = outp;
+	op = outbufp;
 	*op++ = '"';
 	switch (biname) {
 
@@ -509,7 +508,7 @@
 	}
 	if (tp->type==STRING)
 		*op++ = '"';
-	tp->t = (uchar*)outp;
-	tp->len = op - outp;
-	outp = op;
+	tp->t = (uchar*)outbufp;
+	tp->len = op - outbufp;
+	outbufp = op;
 }

```
