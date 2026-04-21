# Diff: `code/tools/asm/cmdlib.h`
**Canonical:** `wolfcamql-src` (sha256 `6a694e0da83c...`, 4366 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `3c9ad1350e26...`, 4361 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\cmdlib.h	2026-04-16 20:02:25.757603800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\asm\cmdlib.h	2026-04-16 22:48:25.942077400 +0100
@@ -59,7 +59,7 @@
 #define	MAX_OS_PATH		1024
 #define MEM_BLOCKSIZE 4096
 
-// the dec offsetof macro doesn't work very well...
+// the dec offsetof macro doesnt work very well...
 #define myoffsetof(type,identifier) ((size_t)&((type *)0)->identifier)
 
 
@@ -67,8 +67,8 @@
 extern int myargc;
 extern char **myargv;
 
-char *Q_strupr (char *in);
-char *Q_strlower (char *in);
+char *strupr (char *in);
+char *strlower (char *in);
 int Q_strncasecmp( const char *s1, const char *s2, int n );
 int Q_stricmp( const char *s1, const char *s2 );
 void Q_getwd( char *out );

```

### `openarena-gamecode`  — sha256 `a28ece3c3180...`, 4410 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\cmdlib.h	2026-04-16 20:02:25.757603800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\asm\cmdlib.h	2026-04-16 22:48:24.196008800 +0100
@@ -59,7 +59,7 @@
 #define	MAX_OS_PATH		1024
 #define MEM_BLOCKSIZE 4096
 
-// the dec offsetof macro doesn't work very well...
+// the dec offsetof macro doesnt work very well...
 #define myoffsetof(type,identifier) ((size_t)&((type *)0)->identifier)
 
 
@@ -67,10 +67,11 @@
 extern int myargc;
 extern char **myargv;
 
-char *Q_strupr (char *in);
-char *Q_strlower (char *in);
+char *strupr (char *in);
+char *strlower (char *in);
 int Q_strncasecmp( const char *s1, const char *s2, int n );
 int Q_stricmp( const char *s1, const char *s2 );
+#define Q_strequal(s1,s2) (Q_stricmp(s1,s2)==0)
 void Q_getwd( char *out );
 
 int Q_filelength (FILE *f);

```
