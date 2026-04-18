# Diff: `code/tools/lcc/etc/bytecode.c`
**Canonical:** `wolfcamql-src` (sha256 `d592ec5c95b4...`, 2027 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `b9a0de2107ca...`, 1713 bytes
Also identical in: openarena-gamecode

_Diff stat: +2 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\etc\bytecode.c	2026-04-16 20:02:25.789262900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\etc\bytecode.c	2026-04-16 22:48:25.948078100 +0100
@@ -34,14 +34,9 @@
 {
 	char basepath[ 1024 ];
 	char *p;
-	size_t basepathsz = sizeof( basepath ) - 1;
 
-	strncpy( basepath, lccBinary, basepathsz );
-	basepath[basepathsz] = 0;
-	p = strrchr( basepath, '/' );
-
-	if( !p )
-		p = strrchr( basepath, '\\' );
+	strncpy( basepath, lccBinary, 1024 );
+	p = strrchr( basepath, PATH_SEP );
 
 	if( p )
 	{
@@ -57,10 +52,6 @@
 		cpp[0] = concat(&arg[8], "/q3cpp" BINEXT);
 		include[0] = concat("-I", concat(&arg[8], "/include"));
 		com[0] = concat(&arg[8], "/q3rcc" BINEXT);
-	} else if (strncmp(arg, "-lcppdir=", 9) == 0) {
-		cpp[0] = concat(&arg[9], "/q3cpp" BINEXT);
-	} else if (strncmp(arg, "-lrccdir=", 9) == 0) {
-		com[0] = concat(&arg[9], "/q3rcc" BINEXT);
 	} else if (strcmp(arg, "-p") == 0 || strcmp(arg, "-pg") == 0) {
 		fprintf( stderr, "no profiling supported, %s ignored.\n", arg);
 	} else if (strcmp(arg, "-b") == 0)

```
