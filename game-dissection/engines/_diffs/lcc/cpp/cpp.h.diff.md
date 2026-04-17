# Diff: `lcc/cpp/cpp.h`
**Canonical:** `quake3-source` (sha256 `c0a0c26a7ab2...`, 4921 bytes)

## Variants

### `q3vm`  — sha256 `b3f11a6ada40...`, 4906 bytes

_Diff stat: +11 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\cpp.h	2026-04-16 20:02:20.042587900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\cpp.h	2026-04-16 22:48:28.088019500 +0100
@@ -24,7 +24,7 @@
 		DSHARP1, NAME1, DEFINED, UMINUS };
 
 enum kwtype { KIF, KIFDEF, KIFNDEF, KELIF, KELSE, KENDIF, KINCLUDE, KDEFINE,
-		KUNDEF, KLINE, KERROR, KPRAGMA, KDEFINED,
+		KUNDEF, KLINE, KWARNING, KERROR, KPRAGMA, KDEFINED,
 		KLINENO, KFILE, KDATE, KTIME, KSTDC, KEVAL };
 
 #define	ISDEFINED	01	/* has #defined value */
@@ -108,6 +108,7 @@
 void	dodefine(Tokenrow *);
 void	doadefine(Tokenrow *, int);
 void	doinclude(Tokenrow *);
+void	appendDirToIncludeList( char *dir );
 void	doif(Tokenrow *, enum kwtype);
 void	expand(Tokenrow *, Nlist *);
 void	builtin(Tokenrow *, int);
@@ -140,7 +141,9 @@
 void	setobjname(char *);
 #define	rowlen(tokrow)	((tokrow)->lp - (tokrow)->bp)
 
-extern	char *outp;
+char *basepath( char *fname );
+
+extern	char *outbufp;
 extern	Token	nltoken;
 extern	Source *cursource;
 extern	char *curtime;
@@ -155,9 +158,9 @@
 extern	Includelist includelist[NINCLUDE];
 extern	char wd[];
 
-extern int creat(char *, int);
-extern int open(char *, int);
-extern int close(int);
-extern int dup2(int, int);
-extern int write(int, char *, size_t);
-extern int read(int, char *, size_t);
+#ifndef _WIN32
+#include <unistd.h>
+#else
+#include <io.h>
+#endif
+#include <fcntl.h>

```
