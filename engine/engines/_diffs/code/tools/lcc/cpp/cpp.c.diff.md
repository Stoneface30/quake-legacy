# Diff: `code/tools/lcc/cpp/cpp.c`
**Canonical:** `wolfcamql-src` (sha256 `aa8ceceb119e...`, 6559 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `6537ed934cd7...`, 6311 bytes

_Diff stat: +3 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\cpp.c	2026-04-16 20:02:25.763112200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\cpp.c	2026-04-16 22:48:25.944075800 +0100
@@ -9,7 +9,7 @@
 
 #define	OUTS	16384
 char	outbuf[OUTS];
-char	*outbufp = outbuf;
+char	*outp = outbuf;
 Source	*cursource;
 int	nerrs;
 struct	token nltoken = { NL, 0, 0, 0, 1, (uchar*)"\n" };
@@ -19,15 +19,6 @@
 int	ifsatisfied[NIF];
 int	skipping;
 
-time_t reproducible_time()
-{
-	char *source_date_epoch;
-	time_t t;
-	if ((source_date_epoch = getenv("SOURCE_DATE_EPOCH")) == NULL ||
-		(t = (time_t)strtol(source_date_epoch, NULL, 10)) <= 0)
-		return time(NULL);
-	return t;
-}
 
 int
 main(int argc, char **argv)
@@ -37,7 +28,7 @@
 	char ebuf[BUFSIZ];
 
 	setbuf(stderr, ebuf);
-	t = reproducible_time();
+	t = time(NULL);
 	curtime = ctime(&t);
 	maketokenrow(3, &tr);
 	expandlex();
@@ -60,7 +51,7 @@
 	for (;;) {
 		if (trp->tp >= trp->lp) {
 			trp->tp = trp->lp = trp->bp;
-			outbufp = outbuf;
+			outp = outbuf;
 			anymacros |= gettokens(trp, 1);
 			trp->tp = trp->bp;
 		}

```

### `openarena-gamecode`  — sha256 `15fef7b73718...`, 6321 bytes

_Diff stat: +4 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\cpp.c	2026-04-16 20:02:25.763112200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\cpp\cpp.c	2026-04-16 22:48:24.199008000 +0100
@@ -9,7 +9,7 @@
 
 #define	OUTS	16384
 char	outbuf[OUTS];
-char	*outbufp = outbuf;
+char	*outp = outbuf;
 Source	*cursource;
 int	nerrs;
 struct	token nltoken = { NL, 0, 0, 0, 1, (uchar*)"\n" };
@@ -19,15 +19,6 @@
 int	ifsatisfied[NIF];
 int	skipping;
 
-time_t reproducible_time()
-{
-	char *source_date_epoch;
-	time_t t;
-	if ((source_date_epoch = getenv("SOURCE_DATE_EPOCH")) == NULL ||
-		(t = (time_t)strtol(source_date_epoch, NULL, 10)) <= 0)
-		return time(NULL);
-	return t;
-}
 
 int
 main(int argc, char **argv)
@@ -37,7 +28,7 @@
 	char ebuf[BUFSIZ];
 
 	setbuf(stderr, ebuf);
-	t = reproducible_time();
+	t = time(NULL);
 	curtime = ctime(&t);
 	maketokenrow(3, &tr);
 	expandlex();
@@ -60,7 +51,7 @@
 	for (;;) {
 		if (trp->tp >= trp->lp) {
 			trp->tp = trp->lp = trp->bp;
-			outbufp = outbuf;
+			outp = outbuf;
 			anymacros |= gettokens(trp, 1);
 			trp->tp = trp->bp;
 		}
@@ -259,6 +250,7 @@
 		break;
 	}
 	setempty(trp);
+	return;
 }
 
 void *

```
