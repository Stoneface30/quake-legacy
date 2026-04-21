# Diff: `code/splines/q_shared.hpp`
**Canonical:** `wolfcamql-src` (sha256 `7f69313906f1...`, 23571 bytes)

## Variants

### `quake3-source`  — sha256 `541902ace49e...`, 23539 bytes

_Diff stat: +2 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\q_shared.hpp	2026-04-16 20:02:25.274288200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\q_shared.hpp	2026-04-16 20:02:19.982634200 +0100
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
@@ -99,7 +97,7 @@
 #define	QDECL	__cdecl
 
 // buildstring will be incorporated into the version string
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #ifdef _M_IX86
 #define	CPUSTRING	"win-x86"
 #elif defined _M_ALPHA
@@ -658,7 +656,7 @@
 float	LittleFloat (float l);
 
 void	Swap_Init (void);
-char	* QDECL va(const char *format, ...);
+char	* QDECL va(char *format, ...);
 
 #ifdef __cplusplus
     }

```
