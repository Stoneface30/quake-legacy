# Diff: `lcc/cpp/getopt.c`
**Canonical:** `quake3-source` (sha256 `98d044ec3aee...`, 1097 bytes)

## Variants

### `q3vm`  — sha256 `f4110c620fd9...`, 1108 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\getopt.c	2026-04-16 20:02:20.042587900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\getopt.c	2026-04-16 22:48:28.089021000 +0100
@@ -1,20 +1,20 @@
 #include	<stdio.h>
+#include	<string.h>
 #define EPR                 fprintf(stderr,
 #define ERR(str, chr)       if(opterr){EPR "%s%c\n", str, chr);}
 int     opterr = 1;
 int     optind = 1;
 int	optopt;
 char    *optarg;
-char    *strchr();
 
 int
-getopt (int argc, char *const argv[], const char *opts)
+lcc_getopt (int argc, char *const argv[], const char *opts)
 {
 	static int sp = 1;
 	int c;
 	char *cp;
 
-	if (sp == 1)
+	if (sp == 1) {
 		if (optind >= argc ||
 		   argv[optind][0] != '-' || argv[optind][1] == '\0')
 			return -1;
@@ -22,6 +22,7 @@
 			optind++;
 			return -1;
 		}
+	}
 	optopt = c = argv[optind][sp];
 	if (c == ':' || (cp=strchr(opts, c)) == 0) {
 		ERR (": illegal option -- ", c);

```
