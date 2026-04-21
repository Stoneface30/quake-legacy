# Diff: `code/splines/util_str.h`
**Canonical:** `wolfcamql-src` (sha256 `bcacc65f7a07...`, 14789 bytes)

## Variants

### `quake3-source`  — sha256 `e79947d93f49...`, 14724 bytes

_Diff stat: +1 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\util_str.h	2026-04-16 20:02:25.275294600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\util_str.h	2026-04-16 20:02:19.984140800 +0100
@@ -29,10 +29,8 @@
 #include <stdio.h>
 
 #ifdef _WIN32
-#ifdef _MSC_VER
 #pragma warning(disable : 4710)     // function 'blah' not inlined
 #endif
-#endif
 
 void TestStringClass ();
 
@@ -142,7 +140,7 @@
 	static   int      cmpn( const char *s1, const char *s2, int n );
 	static   int      cmp( const char *s1, const char *s2 );
 
-	static   void     snprintf ( char *dst, int size, const char *fmt, ... ) __attribute__ ((format (printf, 3, 4)));
+	static   void     snprintf ( char *dst, int size, const char *fmt, ... );
 
 	static   bool	   isNumeric( const char *str );
     bool    isNumeric( void ) const;

```
