# Diff: `code/tools/lcc/cpp/macro.c`
**Canonical:** `wolfcamql-src` (sha256 `ba730175e7a9...`, 11204 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `3e9aa696ad70...`, 11189 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\macro.c	2026-04-16 20:02:25.765140100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\macro.c	2026-04-16 22:48:25.945078500 +0100
@@ -470,10 +470,10 @@
 	/* most are strings */
 	tp->type = STRING;
 	if (tp->wslen) {
-		*outbufp++ = ' ';
+		*outp++ = ' ';
 		tp->wslen = 1;
 	}
-	op = outbufp;
+	op = outp;
 	*op++ = '"';
 	switch (biname) {
 
@@ -508,7 +508,7 @@
 	}
 	if (tp->type==STRING)
 		*op++ = '"';
-	tp->t = (uchar*)outbufp;
-	tp->len = op - outbufp;
-	outbufp = op;
+	tp->t = (uchar*)outp;
+	tp->len = op - outp;
+	outp = op;
 }

```

### `openarena-gamecode`  — sha256 `51009ef1b8f3...`, 11199 bytes

_Diff stat: +6 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\macro.c	2026-04-16 20:02:25.765140100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\cpp\macro.c	2026-04-16 22:48:24.200007700 +0100
@@ -218,6 +218,7 @@
 	insertrow(trp, ntokc, &ntr);
 	trp->tp -= rowlen(&ntr);
 	dofree(ntr.bp);
+	return;
 }	
 
 /*
@@ -470,10 +471,10 @@
 	/* most are strings */
 	tp->type = STRING;
 	if (tp->wslen) {
-		*outbufp++ = ' ';
+		*outp++ = ' ';
 		tp->wslen = 1;
 	}
-	op = outbufp;
+	op = outp;
 	*op++ = '"';
 	switch (biname) {
 
@@ -508,7 +509,7 @@
 	}
 	if (tp->type==STRING)
 		*op++ = '"';
-	tp->t = (uchar*)outbufp;
-	tp->len = op - outbufp;
-	outbufp = op;
+	tp->t = (uchar*)outp;
+	tp->len = op - outp;
+	outp = op;
 }

```
