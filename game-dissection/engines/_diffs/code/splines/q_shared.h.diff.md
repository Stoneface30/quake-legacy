# Diff: `code/splines/q_shared.h`
**Canonical:** `wolfcamql-src` (sha256 `9ae9fea34ca6...`, 23874 bytes)

## Variants

### `quake3-source`  — sha256 `541902ace49e...`, 23539 bytes

_Diff stat: +18 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\q_shared.h	2026-04-16 20:02:25.274288200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\q_shared.h	2026-04-16 20:02:19.981635900 +0100
@@ -37,7 +37,6 @@
 #define	ALIGN_OFF
 
 #ifdef _WIN32
-#ifdef _MSC_VER
 
 #pragma warning(disable : 4018)     // signed/unsigned mismatch
 #pragma warning(disable : 4032)
@@ -58,7 +57,6 @@
 #pragma warning(disable : 4220)		// varargs matches remaining parameters
 
 #endif
-#endif
 
 #include <assert.h>
 #include <math.h>
@@ -99,18 +97,18 @@
 #define	QDECL	__cdecl
 
 // buildstring will be incorporated into the version string
-#ifdef NQDEBUG
-  #ifdef _M_IX86
-  #define CPUSTRING "win-x86"
-  #elif defined _M_ALPHA
-  #define CPUSTRING "win-AXP"
-  #endif
+#ifdef NDEBUG
+#ifdef _M_IX86
+#define	CPUSTRING	"win-x86"
+#elif defined _M_ALPHA
+#define	CPUSTRING	"win-AXP"
+#endif
 #else
-  #ifdef _M_IX86
-  #define CPUSTRING "win-x86-debug"
-  #elif defined _M_ALPHA
-  #define CPUSTRING "win-AXP-debug"
-  #endif
+#ifdef _M_IX86
+#define	CPUSTRING	"win-x86-debug"
+#elif defined _M_ALPHA
+#define	CPUSTRING	"win-AXP-debug"
+#endif
 #endif
 
 
@@ -585,8 +583,8 @@
 void Com_MatchToken( const char *(*buf_p), const char *match, qboolean warning );
 #endif
 
-void Com_ScriptError( const char *msg, ... ) __attribute__ ((format (printf, 1, 2)));
-void Com_ScriptWarning( const char *msg, ... ) __attribute__ ((format (printf, 1, 2)));
+void Com_ScriptError( const char *msg, ... );
+void Com_ScriptWarning( const char *msg, ... );
 
 void Com_SkipBracedSection( const char *(*program) );
 void Com_SkipRestOfLine( const char *(*data) );
@@ -603,7 +601,7 @@
 	extern "C" {
 #endif
 
-void	QDECL Com_sprintf (char *dest, int size, const char *fmt, ...) __attribute__ ((format (printf, 3, 4)));
+void	QDECL Com_sprintf (char *dest, int size, const char *fmt, ...);
 
 
 // mode parm for FS_FOpenFile
@@ -658,7 +656,7 @@
 float	LittleFloat (float l);
 
 void	Swap_Init (void);
-char	* QDECL va(char *format, ...) __attribute__ ((format (printf, 1, 2)));
+char	* QDECL va(char *format, ...);
 
 #ifdef __cplusplus
     }
@@ -761,9 +759,9 @@
 	extern "C" {
 #endif
 
-void	QDECL Com_Error( int level, const char *error, ... ) __attribute__ ((noreturn, format(printf, 2, 3)));
-void	QDECL Com_Printf( const char *msg, ... ) __attribute__ ((format (printf, 1, 2)));
-void	QDECL Com_DPrintf( const char *msg, ... ) __attribute__ ((format (printf, 1, 2)));
+void	QDECL Com_Error( int level, const char *error, ... );
+void	QDECL Com_Printf( const char *msg, ... );
+void	QDECL Com_DPrintf( const char *msg, ... );
 
 #ifdef __cplusplus
 	}

```
