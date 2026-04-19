# Diff: `code/tools/lcc/cpp/unix.c`
**Canonical:** `wolfcamql-src` (sha256 `6815e4e3e1ca...`, 2979 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `a9af1a0b29e5...`, 2735 bytes
Also identical in: openarena-gamecode

_Diff stat: +2 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\unix.c	2026-04-16 20:02:25.766695400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\unix.c	2026-04-16 22:48:25.946077500 +0100
@@ -2,7 +2,6 @@
 #include <stddef.h>
 #include <stdlib.h>
 #include <string.h>
-#include <sys/stat.h>
 #include "cpp.h"
 
 extern	int lcc_getopt(int, char *const *, const char *);
@@ -65,22 +64,11 @@
 		fp = (char*)newstring((uchar*)argv[optind], strlen(argv[optind]), 0);
 		if ((fd = open(fp, 0)) <= 0)
 			error(FATAL, "Can't open input file %s", fp);
-#ifdef WIN32
-		_setmode(fd, _O_BINARY);
-#endif
 	}
 	if (optind+1<argc) {
-		int fdo;
-#ifdef WIN32
-		fdo = creat(argv[optind+1], _S_IREAD | _S_IWRITE);
-#else
-		fdo = creat(argv[optind+1], 0666);
-#endif
+		int fdo = creat(argv[optind+1], 0666);
 		if (fdo<0)
 			error(FATAL, "Can't open output file %s", argv[optind+1]);
-#ifdef WIN32
-		_setmode(fdo, _O_BINARY);
-#endif
 		dup2(fdo, 1);
 	}
 	if(Mflag)
@@ -111,8 +99,7 @@
 /* memmove is defined here because some vendors don't provide it at
    all and others do a terrible job (like calling malloc) */
 // -- ouch, that hurts -- ln
-/* always use the system memmove() on Mac OS X. --ryan. */
-#if !defined(__APPLE__) && !defined(_MSC_VER)
+#ifndef MACOS_X   /* always use the system memmove() on Mac OS X. --ryan. */
 #ifdef memmove
 #undef memmove
 #endif

```
