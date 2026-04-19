# Diff: `code/tools/lcc/cpp/include.c`
**Canonical:** `wolfcamql-src` (sha256 `5bd80a8a2cfc...`, 3401 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `cd8454f64acf...`, 3392 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\include.c	2026-04-16 20:02:25.764111400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\include.c	2026-04-16 22:48:25.945078500 +0100
@@ -120,7 +120,7 @@
 	static Tokenrow tr = { &ta, &ta, &ta+1, 1 };
 	uchar *p;
 
-	ta.t = p = (uchar*)outbufp;
+	ta.t = p = (uchar*)outp;
 	strcpy((char*)p, "#line ");
 	p += sizeof("#line ")-1;
 	p = (uchar*)outnum((char*)p, cursource->line);
@@ -133,8 +133,8 @@
 	strcpy((char*)p, cursource->filename);
 	p += strlen((char*)p);
 	*p++ = '"'; *p++ = '\n';
-	ta.len = (char*)p-outbufp;
-	outbufp = (char*)p;
+	ta.len = (char*)p-outp;
+	outp = (char*)p;
 	tr.tp = tr.bp;
 	puttokens(&tr);
 }

```

### `openarena-gamecode`  — sha256 `d3a5ca59da8d...`, 3402 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\include.c	2026-04-16 20:02:25.764111400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\cpp\include.c	2026-04-16 22:48:24.200007700 +0100
@@ -108,6 +108,7 @@
 	return;
 syntax:
 	error(ERROR, "Syntax error in #include");
+	return;
 }
 
 /*
@@ -120,7 +121,7 @@
 	static Tokenrow tr = { &ta, &ta, &ta+1, 1 };
 	uchar *p;
 
-	ta.t = p = (uchar*)outbufp;
+	ta.t = p = (uchar*)outp;
 	strcpy((char*)p, "#line ");
 	p += sizeof("#line ")-1;
 	p = (uchar*)outnum((char*)p, cursource->line);
@@ -133,8 +134,8 @@
 	strcpy((char*)p, cursource->filename);
 	p += strlen((char*)p);
 	*p++ = '"'; *p++ = '\n';
-	ta.len = (char*)p-outbufp;
-	outbufp = (char*)p;
+	ta.len = (char*)p-outp;
+	outp = (char*)p;
 	tr.tp = tr.bp;
 	puttokens(&tr);
 }

```
