# Diff: `lcc/cpp/unix.c`
**Canonical:** `quake3-source` (sha256 `e5063128d25e...`, 2448 bytes)

## Variants

### `q3vm`  — sha256 `fac9d282b64f...`, 2878 bytes

_Diff stat: +38 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\unix.c	2026-04-16 20:02:20.044692500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\unix.c	2026-04-16 22:48:28.090019500 +0100
@@ -2,9 +2,10 @@
 #include <stddef.h>
 #include <stdlib.h>
 #include <string.h>
+#include <sys/stat.h>
 #include "cpp.h"
 
-extern	int getopt(int, char *const *, const char *);
+extern	int lcc_getopt(int, char *const *, const char *);
 extern	char	*optarg, rcsid[];
 extern	int	optind;
 int	verbose;
@@ -19,9 +20,11 @@
 	char *fp, *dp;
 	Tokenrow tr;
 	extern void setup_kwtab(void);
+	uchar *includeDirs[ NINCLUDE ] = { 0 };
+	int   numIncludeDirs = 0;
 
 	setup_kwtab();
-	while ((c = getopt(argc, argv, "MNOVv+I:D:U:F:lg")) != -1)
+	while ((c = lcc_getopt(argc, argv, "MNOVv+I:D:U:F:lg")) != -1)
 		switch (c) {
 		case 'N':
 			for (i=0; i<NINCLUDE; i++)
@@ -29,15 +32,7 @@
 					includelist[i].deleted = 1;
 			break;
 		case 'I':
-			for (i=NINCLUDE-2; i>=0; i--) {
-				if (includelist[i].file==NULL) {
-					includelist[i].always = 1;
-					includelist[i].file = optarg;
-					break;
-				}
-			}
-			if (i<0)
-				error(FATAL, "Too many -I directives");
+			includeDirs[ numIncludeDirs++ ] = newstring( (uchar *)optarg, strlen( optarg ), 0 );
 			break;
 		case 'D':
 		case 'U':
@@ -66,17 +61,18 @@
 	fp = "<stdin>";
 	fd = 0;
 	if (optind<argc) {
-		if ((fp = strrchr(argv[optind], '/')) != NULL) {
-			int len = fp - argv[optind];
-			dp = (char*)newstring((uchar*)argv[optind], len+1, 0);
-			dp[len] = '\0';
-		}
+		dp = basepath( argv[optind] );
 		fp = (char*)newstring((uchar*)argv[optind], strlen(argv[optind]), 0);
 		if ((fd = open(fp, 0)) <= 0)
 			error(FATAL, "Can't open input file %s", fp);
 	}
 	if (optind+1<argc) {
-		int fdo = creat(argv[optind+1], 0666);
+		int fdo;
+#ifdef WIN32
+		fdo = creat(argv[optind+1], _S_IREAD | _S_IWRITE);
+#else
+		fdo = creat(argv[optind+1], 0666);
+#endif
 		if (fdo<0)
 			error(FATAL, "Can't open output file %s", argv[optind+1]);
 		dup2(fdo, 1);
@@ -85,20 +81,42 @@
 		setobjname(fp);
 	includelist[NINCLUDE-1].always = 0;
 	includelist[NINCLUDE-1].file = dp;
+
+	for( i = 0; i < numIncludeDirs; i++ )
+		appendDirToIncludeList( (char *)includeDirs[ i ] );
+
 	setsource(fp, fd, NULL);
 }
 
 
+char *basepath( char *fname )
+{
+	char *dp = ".";
+	char *p;
+	if ((p = strrchr(fname, '/')) != NULL) {
+		int dlen = p - fname;
+		dp = (char*)newstring((uchar*)fname, dlen+1, 0);
+		dp[dlen] = '\0';
+	}
+
+	return dp;
+}
 
 /* memmove is defined here because some vendors don't provide it at
    all and others do a terrible job (like calling malloc) */
+// -- ouch, that hurts -- ln
+/* always use the system memmove() on Mac OS X. --ryan. */
+#if !defined(__APPLE__) && !defined(_MSC_VER)
+#ifdef memmove
+#undef memmove
+#endif
 void *
 memmove(void *dp, const void *sp, size_t n)
 {
 	unsigned char *cdp, *csp;
 
 	if (n<=0)
-		return 0;
+		return dp;
 	cdp = dp;
 	csp = (unsigned char *)sp;
 	if (cdp < csp) {
@@ -112,5 +130,6 @@
 			*--cdp = *--csp;
 		} while (--n);
 	}
-	return 0;
+	return dp;
 }
+#endif

```
