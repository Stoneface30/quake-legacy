# Diff: `code/splines/util_str.cpp`
**Canonical:** `wolfcamql-src` (sha256 `2bdf8a1ab2b7...`, 12220 bytes)

## Variants

### `quake3-source`  — sha256 `f8694144c459...`, 12106 bytes

_Diff stat: +3 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\util_str.cpp	2026-04-16 20:02:25.275294600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\util_str.cpp	2026-04-16 20:02:19.982634200 +0100
@@ -28,11 +28,9 @@
 #include <stdarg.h>
 
 #ifdef _WIN32
-#ifdef _MSC_VER
 #pragma warning(disable : 4244)     // 'conversion' conversion from 'type1' to 'type2', possible loss of data
 #pragma warning(disable : 4710)     // function 'blah' not inlined
 #endif
-#endif
 
 static const int STR_ALLOC_GRAN = 20;
 
@@ -497,10 +495,8 @@
    }
 
 #ifdef _WIN32
-#ifdef _MSC_VER
 #pragma warning(disable : 4189)		// local variable is initialized but not referenced
 #endif
-#endif
 
 /*
 =================
@@ -519,8 +515,7 @@
 	)
 
 	{
-#if 0
-        //char	ch;							// ch == ?
+	char	ch;							// ch == ?
 	idStr	*t;							// t == ?
 	idStr	a;								// a.len == 0, a.data == "\0"
 	idStr	b;								// b.len == 0, b.data == "\0"
@@ -531,7 +526,7 @@
 	int	i;								// i == ?
 
 	i = a.length();					// i == 0
-	//i = c.length();					// i == 4
+	i = c.length();					// i == 4
 
     // TTimo: not used
 //	const char *s1 = a.c_str();	// s1 == "\0"
@@ -560,7 +555,6 @@
                                  // a.len == 11, a.data == "testtestwow\0"	ASSERT!
 
 	a = "test";							// a.len == 4, a.data == "test\0"
-#if 0
 	ch = a[ 0 ];						// ch == 't'
 	ch = a[ -1 ];						// ch == 0											ASSERT!
 	ch = a[ 1000 ];					// ch == 0											ASSERT!
@@ -570,7 +564,7 @@
 	ch = a[ 3 ];						// ch == 't'
 	ch = a[ 4 ];						// ch == '\0'										ASSERT!
 	ch = a[ 5 ];						// ch == '\0'										ASSERT!
-#endif
+
 	a[ 1 ] = 'b';						// a.len == 4, a.data == "tbst\0"
 	a[ -1 ] = 'b';						// a.len == 4, a.data == "tbst\0"			ASSERT!
 	a[ 0 ] = '0';						// a.len == 4, a.data == "0bst\0"
@@ -618,12 +612,9 @@
    a = b;
 
    a[1] = '1';                   // a.data = "t1st", b.data = "test"
-#endif
 	}
 
 #ifdef _WIN32
-#ifdef _MSC_VER
 #pragma warning(default : 4189)		// local variable is initialized but not referenced
 #pragma warning(disable : 4514)     // unreferenced inline function has been removed
 #endif
-#endif

```
