# Diff: `lcc/cpp/include.c`
**Canonical:** `quake3-source` (sha256 `327af518d3dd...`, 2750 bytes)

## Variants

### `q3vm`  — sha256 `5bd80a8a2cfc...`, 3401 bytes

_Diff stat: +36 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\include.c	2026-04-16 20:02:20.044095300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\include.c	2026-04-16 22:48:28.089021000 +0100
@@ -1,3 +1,4 @@
+#include <stdio.h>
 #include <stdlib.h>
 #include <string.h>
 #include "cpp.h"
@@ -6,6 +7,34 @@
 
 extern char	*objname;
 
+void appendDirToIncludeList( char *dir )
+{
+	int i;
+	char *fqdir;
+
+	fqdir = (char *)newstring( (uchar *)includelist[NINCLUDE-1].file, 256, 0 );
+	strcat( fqdir, "/" );
+	strcat( fqdir, dir );
+
+	//avoid adding it more than once
+	for (i=NINCLUDE-2; i>=0; i--) {
+		if (includelist[i].file &&
+				!strcmp (includelist[i].file, fqdir)) {
+			return;
+		}
+	}
+
+	for (i=NINCLUDE-2; i>=0; i--) {
+		if (includelist[i].file==NULL) {
+			includelist[i].always = 1;
+			includelist[i].file = fqdir;
+			break;
+		}
+	}
+	if (i<0)
+		error(FATAL, "Too many -I directives");
+}
+
 void
 doinclude(Tokenrow *trp)
 {
@@ -44,6 +73,9 @@
 	if (trp->tp < trp->lp || len==0)
 		goto syntax;
 	fname[len] = '\0';
+
+	appendDirToIncludeList( basepath( fname ) );
+
 	if (fname[0]=='/') {
 		fd = open(fname, 0);
 		strcpy(iname, fname);
@@ -59,7 +91,7 @@
 		if ((fd = open(iname, 0)) >= 0)
 			break;
 	}
-	if ( Mflag>1 || !angled&&Mflag==1 ) {
+	if ( Mflag>1 || (!angled&&Mflag==1) ) {
 		write(1,objname,strlen(objname));
 		write(1,iname,strlen(iname));
 		write(1,"\n",1);
@@ -76,7 +108,6 @@
 	return;
 syntax:
 	error(ERROR, "Syntax error in #include");
-	return;
 }
 
 /*
@@ -89,7 +120,7 @@
 	static Tokenrow tr = { &ta, &ta, &ta+1, 1 };
 	uchar *p;
 
-	ta.t = p = (uchar*)outp;
+	ta.t = p = (uchar*)outbufp;
 	strcpy((char*)p, "#line ");
 	p += sizeof("#line ")-1;
 	p = (uchar*)outnum((char*)p, cursource->line);
@@ -102,8 +133,8 @@
 	strcpy((char*)p, cursource->filename);
 	p += strlen((char*)p);
 	*p++ = '"'; *p++ = '\n';
-	ta.len = (char*)p-outp;
-	outp = (char*)p;
+	ta.len = (char*)p-outbufp;
+	outbufp = (char*)p;
 	tr.tp = tr.bp;
 	puttokens(&tr);
 }

```
