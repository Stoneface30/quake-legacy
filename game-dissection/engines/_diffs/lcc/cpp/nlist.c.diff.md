# Diff: `lcc/cpp/nlist.c`
**Canonical:** `quake3-source` (sha256 `754887e36332...`, 2146 bytes)

## Variants

### `q3vm`  — sha256 `1e2a46190ed5...`, 2163 bytes

_Diff stat: +21 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\cpp\nlist.c	2026-04-16 20:02:20.044692500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\cpp\nlist.c	2026-04-16 22:48:28.089021000 +0100
@@ -3,7 +3,6 @@
 #include <string.h>
 #include "cpp.h"
 
-extern	int getopt(int, char *const *, const char *);
 extern	char	*optarg;
 extern	int	optind;
 extern	int	verbose;
@@ -20,26 +19,27 @@
 	int	val;
 	int	flag;
 } kwtab[] = {
-	"if",		KIF,		ISKW,
-	"ifdef",	KIFDEF,		ISKW,
-	"ifndef",	KIFNDEF,	ISKW,
-	"elif",		KELIF,		ISKW,
-	"else",		KELSE,		ISKW,
-	"endif",	KENDIF,		ISKW,
-	"include",	KINCLUDE,	ISKW,
-	"define",	KDEFINE,	ISKW,
-	"undef",	KUNDEF,		ISKW,
-	"line",		KLINE,		ISKW,
-	"error",	KERROR,		ISKW,
-	"pragma",	KPRAGMA,	ISKW,
-	"eval",		KEVAL,		ISKW,
-	"defined",	KDEFINED,	ISDEFINED+ISUNCHANGE,
-	"__LINE__",	KLINENO,	ISMAC+ISUNCHANGE,
-	"__FILE__",	KFILE,		ISMAC+ISUNCHANGE,
-	"__DATE__",	KDATE,		ISMAC+ISUNCHANGE,
-	"__TIME__",	KTIME,		ISMAC+ISUNCHANGE,
-	"__STDC__",	KSTDC,		ISUNCHANGE,
-	NULL
+	{"if",		KIF,		ISKW},
+	{"ifdef",	KIFDEF,		ISKW},
+	{"ifndef",	KIFNDEF,	ISKW},
+	{"elif",		KELIF,		ISKW},
+	{"else",		KELSE,		ISKW},
+	{"endif",	KENDIF,		ISKW},
+	{"include",	KINCLUDE,	ISKW},
+	{"define",	KDEFINE,	ISKW},
+	{"undef",	KUNDEF,		ISKW},
+	{"line",		KLINE,		ISKW},
+	{"warning",	KWARNING,	ISKW},
+	{"error",	KERROR,		ISKW},
+	{"pragma",	KPRAGMA,	ISKW},
+	{"eval",		KEVAL,		ISKW},
+	{"defined",	KDEFINED,	ISDEFINED+ISUNCHANGE},
+	{"__LINE__",	KLINENO,	ISMAC+ISUNCHANGE},
+	{"__FILE__",	KFILE,		ISMAC+ISUNCHANGE},
+	{"__DATE__",	KDATE,		ISMAC+ISUNCHANGE},
+	{"__TIME__",	KTIME,		ISMAC+ISUNCHANGE},
+	{"__STDC__",	KSTDC,		ISUNCHANGE},
+	{NULL}
 };
 
 unsigned long	namebit[077+1];

```
