# Diff: `code/qcommon/q_platform.h`
**Canonical:** `wolfcamql-src` (sha256 `a2e00eca4dd4...`, 9359 bytes)

## Variants

### `ioquake3`  — sha256 `e0ffe3222746...`, 9358 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_platform.h	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\q_platform.h	2026-04-16 20:02:21.570109000 +0100
@@ -413,7 +413,7 @@
 
 
 //platform string
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING
 #else
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING "-debug"

```

### `quake3e`  — sha256 `5b60e3e9365b...`, 6606 bytes

_Diff stat: +144 / -263 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_platform.h	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\q_platform.h	2026-04-16 20:02:27.306462300 +0100
@@ -19,339 +19,207 @@
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-
+//
 #ifndef __Q_PLATFORM_H
 #define __Q_PLATFORM_H
 
-// this is for determining if we have an asm version of a C function
-#define idx64 0
-
-#ifdef Q3_VM
-
-#define id386 0
-#define idppc 0
-#define idppc_altivec 0
-#define idsparc 0
-
-#else
+#define QDECL
 
-#if (defined _M_IX86 || defined __i386__) && !defined(C_ONLY)
-#define id386 1
-#else
 #define id386 0
-#endif
-
-#if (defined(powerc) || defined(powerpc) || defined(ppc) || \
-	defined(__ppc) || defined(__ppc__)) && !defined(C_ONLY)
-#define idppc 1
-#if defined(__VEC__)
-#define idppc_altivec 1
-#ifdef __APPLE__  // Apple's GCC does this differently than the FSF.
-#define VECCONST_UINT8(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) \
-	(vector unsigned char) (a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p)
-#else
-#define VECCONST_UINT8(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) \
-	(vector unsigned char) {a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p}
-#endif
-#else
-#define idppc_altivec 0
-#endif
-#else
-#define idppc 0
-#define idppc_altivec 0
-#endif
-
-#if defined(__sparc__) && !defined(C_ONLY)
-#define idsparc 1
-#else
-#define idsparc 0
-#endif
-
-#endif
-
-// for windows fastcall option
-#define QDECL
-#define QCALL
+#define idx64 0
+#define arm32 0
+#define arm64 0
 
-//================================================================= WIN64/32 ===
+// ============================== Win32 ====================================
 
-#if defined(_WIN64) || defined(__WIN64__)
+#ifdef _WIN32
 
 #undef QDECL
 #define QDECL __cdecl
+#define Q_NEWLINE "\r\n"
 
-#undef QCALL
-#define QCALL __stdcall
-
-#if defined( _MSC_VER )
-#define OS_STRING "win_msvc64"
-#elif defined __MINGW64__
-#define OS_STRING "win_mingw64"
+#if defined (_WIN32_WINNT)
+#if _WIN32_WINNT < 0x0501
+#undef _WIN32_WINNT
+#define _WIN32_WINNT 0x0501
 #endif
-
-#define ID_INLINE __inline
-#define PATH_SEP '\\'
-
-#if defined(__x86_64__) || defined(_M_X64)
-#undef idx64
-#define idx64 1
-#define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
-#elif defined(__aarch64__) || defined(__ARM64__) || defined (_M_ARM64)
-#define ARCH_STRING "arm64"
+#else
+#define _WIN32_WINNT 0x0501
 #endif
 
-#define Q3_LITTLE_ENDIAN
-
-#define DLL_EXT ".dll"
-
-#elif defined(_WIN32) || defined(__WIN32__)
-
-#undef QDECL
-#define QDECL __cdecl
-
-#undef QCALL
-#define QCALL __stdcall
-
-#if defined( _MSC_VER )
+#if defined( _MSC_VER ) && _MSC_VER >= 1400 // MSVC++ 8.0 at least
 #define OS_STRING "win_msvc"
 #elif defined __MINGW32__
 #define OS_STRING "win_mingw"
+#elif defined __MINGW64__
+#define OS_STRING "win_mingw64"
+#else
+#error "Compiler not supported"
 #endif
 
 #define ID_INLINE __inline
 #define PATH_SEP '\\'
+#define PATH_SEP_FOREIGN '/'
+#define DLL_EXT ".dll"
 
-#if defined( _M_IX86 ) || defined( __i386__ )
+#if defined( _M_IX86 )
 #define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined(__arm__) || defined(_M_ARM)
-#define ARCH_STRING "arm"
+#define Q3_LITTLE_ENDIAN
+#undef id386
+#define id386 1
+#ifndef __WORDSIZE
+#define __WORDSIZE 32
+#endif
 #endif
 
+#if defined( _M_AMD64 )
+#define ARCH_STRING "x86_64"
 #define Q3_LITTLE_ENDIAN
+#undef idx64
+#define idx64 1
+//#define UNICODE
+#ifndef __WORDSIZE
+#define __WORDSIZE 64
+#endif
+#endif
 
-#define DLL_EXT ".dll"
-
+#if defined( _M_ARM64 )
+#define ARCH_STRING "arm64"
+#define Q3_LITTLE_ENDIAN
+#undef arm64
+#define arm64 1
+#ifndef __WORDSIZE
+#define __WORDSIZE 64
+#endif
 #endif
 
+#if defined( _M_ARM )
+#define ARCH_STRING "arm32"
+#define Q3_LITTLE_ENDIAN
+#undef arm32
+#define arm32 1
+#endif
 
-//================================================================ MAC OS ===
+#else // !defined _WIN32
 
-#if defined(__APPLE__) || defined(__APPLE_CC__)
+// common unix platforms parameters
 
-#define OS_STRING "macosx"
-#define ID_INLINE inline
+#define Q_NEWLINE "\n"
 #define PATH_SEP '/'
+#define PATH_SEP_FOREIGN '\\'
+#define DLL_EXT ".so"
 
-#ifdef __ppc__
-#define ARCH_STRING "ppc"
-#define Q3_BIG_ENDIAN
-#define HAVE_VM_COMPILED
-#elif defined __i386__
-#define ARCH_STRING "x86"
+#if defined (__i386__)
+#define ARCH_STRING "i386"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
-#elif defined __x86_64__
-#undef idx64
-#define idx64 1
+#undef id386
+#define id386 1
+#endif // __i386__
+
+#if defined (__x86_64__) || defined (__amd64__)
 #define ARCH_STRING "x86_64"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
-#elif defined __aarch64__
-#define ARCH_STRING "arm64"
+#undef idx64
+#define idx64 1
+#endif // __x86_64__ || __amd64__
+
+#if defined (__arm__)
+#define ARCH_STRING "arm"
 #define Q3_LITTLE_ENDIAN
-#endif
+#undef arm32
+#define arm32 1
+#endif // __arm__
 
-#define DLL_EXT ".dylib"
+#if defined (__aarch64__)
+#define ARCH_STRING "aarch64"
+#define Q3_LITTLE_ENDIAN
+#undef arm64
+#define arm64 1
+#endif // __arm64__
+
+#if defined (__PPC64__)
+#if defined (__LITTLE_ENDIAN__) || defined (__LITTLE_ENDIAN)
+#define ARCH_STRING "ppc64le"
+#define Q3_LITTLE_ENDIAN
+#else
+#define ARCH_STRING "ppc64"
+#define Q3_BIG_ENDIAN
+#endif // !__LITTLE_ENDIAN__
+#endif // __PPC64__
 
-#endif
+#endif // !_WIN32
 
-//================================================================= LINUX ===
+// ============================== Linux ====================================
 
-#if defined(__linux__) || defined(__FreeBSD_kernel__) || defined(__GNU__)
+#ifdef __linux__
 
 #include <endian.h>
 
-#if defined(__linux__)
 #define OS_STRING "linux"
-#elif defined(__FreeBSD_kernel__)
-#define OS_STRING "kFreeBSD"
-#else
-#define OS_STRING "GNU"
-#endif
-
 #define ID_INLINE inline
 
-#define PATH_SEP '/'
-
-#if defined(__x86_64__) || defined(__amd64__)
-# define ARCH_STRING "x86_64"
-# define HAVE_VM_COMPILED
-#elif defined(__i386__)
-# define ARCH_STRING "x86"
-# define HAVE_VM_COMPILED
-#elif defined(__aarch64__)
-# define ARCH_STRING "arm64"
-#elif defined(__arm__)
-# define ARCH_STRING "arm"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc64__) || defined(__ppc64__)
-# define ARCH_STRING "ppc64"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc__) || defined(__ppc__)
-# define ARCH_STRING "ppc"
-# define HAVE_VM_COMPILED
-#elif defined(__alpha__)
-# define ARCH_STRING "alpha"
-#endif
+#endif // __linux___
 
-#if defined __x86_64__
-#undef idx64
-#define idx64 1
-#endif
+// =============================== BSD =====================================
 
-#if __FLOAT_WORD_ORDER == __BIG_ENDIAN
-#define Q3_BIG_ENDIAN
-#else
-#define Q3_LITTLE_ENDIAN
-#endif
-
-#define DLL_EXT ".so"
-
-#endif
-
-//=================================================================== BSD ===
-
-#if defined(__FreeBSD__) || defined(__OpenBSD__) || defined(__NetBSD__)
+#if defined (__FreeBSD__) || defined (__NetBSD__) || defined (__OpenBSD__)
 
 #include <sys/types.h>
 #include <machine/endian.h>
 
-#ifndef __BSD__
-  #define __BSD__
-#endif
 
-#if defined(__FreeBSD__)
+#if defined (__FreeBSD__)
 #define OS_STRING "freebsd"
-#elif defined(__OpenBSD__)
-#define OS_STRING "openbsd"
-#elif defined(__NetBSD__)
+#elif defined (__NetBSD__)
 #define OS_STRING "netbsd"
+#elif defined (__OpenBSD__)
+#define OS_STRING "openbsd"
 #endif
 
 #define ID_INLINE inline
-#define PATH_SEP '/'
-
-#ifdef __i386__
-#define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined __amd64__
-#undef idx64
-#define idx64 1
-#define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
-#elif defined __axp__
-#define ARCH_STRING "alpha"
-#endif
-
 #if BYTE_ORDER == BIG_ENDIAN
 #define Q3_BIG_ENDIAN
 #else
 #define Q3_LITTLE_ENDIAN
 #endif
 
-#define DLL_EXT ".so"
-
-#endif
-
-//================================================================= SUNOS ===
-
-#ifdef __sun
-
-#include <stdint.h>
-#include <sys/byteorder.h>
-
-#define OS_STRING "solaris"
-#define ID_INLINE inline
-#define PATH_SEP '/'
-
-#ifdef __i386__
-#define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined __sparc
-#define ARCH_STRING "sparc"
-#define HAVE_VM_COMPILED
-#endif
-
-#if defined( _BIG_ENDIAN )
-#define Q3_BIG_ENDIAN
-#elif defined( _LITTLE_ENDIAN )
-#define Q3_LITTLE_ENDIAN
-#endif
-
-#define DLL_EXT ".so"
-
-#endif
-
-//================================================================== IRIX ===
-
-#ifdef __sgi
-
-#define OS_STRING "irix"
-#define ID_INLINE __inline
-#define PATH_SEP '/'
-
-#define ARCH_STRING "mips"
+#endif // __FreeBSD__ || __NetBSD__ || __OpenBSD__
 
-#define Q3_BIG_ENDIAN // SGI's MIPS are always big endian
+// ================================ APPLE ===================================
 
-#define DLL_EXT ".so"
-
-#endif
+#ifdef __APPLE__
 
-//============================================================ EMSCRIPTEN ===
-
-#ifdef __EMSCRIPTEN__
-
-#define OS_STRING "emscripten"
+#define OS_STRING "macos"
 #define ID_INLINE inline
-#define PATH_SEP '/'
-
-#define ARCH_STRING "wasm32"
-
-#define Q3_LITTLE_ENDIAN
-
-#define DLL_EXT ".wasm"
+#undef DLL_EXT
+#define DLL_EXT ".dylib"
 
-#endif
+#endif // __APPLE__
 
-//================================================================== Q3VM ===
+// ================================ Q3VM ===================================
 
 #ifdef Q3_VM
 
 #define OS_STRING "q3vm"
 #define ID_INLINE
-#define PATH_SEP '/'
 
 #define ARCH_STRING "bytecode"
+#define Q3_LITTLE_ENDIAN
 
+#undef DLL_EXT
 #define DLL_EXT ".qvm"
 
 #endif
 
-//===========================================================================
+// =========================================================================
 
-// Catch missing defines in above blocks
-
-#ifndef OS_STRING
+//catch missing defines in above blocks
+#if !defined( OS_STRING )
 #error "Operating system not supported"
 #endif
 
-#ifndef ARCH_STRING
-// ARCH_STRING is (mostly) only used for informational purposes, so we allow
-// it to be undefined so that more diverse architectures may be compiled
-#define ARCH_STRING "unknown"
+#if !defined( ARCH_STRING )
+#error "Architecture not supported"
 #endif
 
 #ifndef ID_INLINE
@@ -362,20 +230,20 @@
 #error "PATH_SEP not defined"
 #endif
 
+#ifndef PATH_SEP_FOREIGN
+#error "PATH_SEP_FOREIGN not defined"
+#endif
+
 #ifndef DLL_EXT
 #error "DLL_EXT not defined"
 #endif
 
-
-//endianness
-void CopyShortSwap (void *dest, void *src);
-void CopyLongSwap (void *dest, void *src);
-short ShortSwap (short l);
-int LongSwap (int l);
-float FloatSwap (const float *f);
+// Endianess
 
 #if defined( Q3_BIG_ENDIAN ) && defined( Q3_LITTLE_ENDIAN )
+
 #error "Endianness defined as both big and little"
+
 #elif defined( Q3_BIG_ENDIAN )
 
 #define CopyLittleShort(dest, src) CopyShortSwap(dest, src)
@@ -398,25 +266,38 @@
 #define BigLong(x) LongSwap(x)
 #define BigFloat(x) FloatSwap(&x)
 
-#elif defined( Q3_VM )
-
-#define LittleShort
-#define LittleLong
-#define LittleFloat
-#define BigShort
-#define BigLong
-#define BigFloat
-
 #else
+
 #error "Endianness not defined"
+
 #endif
 
+// Platform string
 
-//platform string
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING
 #else
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING "-debug"
 #endif
 
+#if idx64
+#ifdef _MSC_VER
+#define _MSC_SSE2
+#else
+#define _GCC_SSE2
 #endif
+#endif // idx64
+
+// Modifier for printing size_t values portably
+
+#if (defined _WIN64)
+#define PRIz "I64"
+#elif (defined _WIN32)
+#define PRIz "I32"
+#elif (defined Q3_VM)
+#define PRIz ""
+#else
+#define PRIz "z"
+#endif
+
+#endif // __Q_PLATFORM_H

```

### `openarena-engine`  — sha256 `b52c6e93bafa...`, 9076 bytes

_Diff stat: +65 / -70 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_platform.h	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\q_platform.h	2026-04-16 22:48:25.912364200 +0100
@@ -46,7 +46,7 @@
 #define idppc 1
 #if defined(__VEC__)
 #define idppc_altivec 1
-#ifdef __APPLE__  // Apple's GCC does this differently than the FSF.
+#ifdef MACOS_X  // Apple's GCC does this differently than the FSF.
 #define VECCONST_UINT8(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) \
 	(vector unsigned char) (a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p)
 #else
@@ -69,6 +69,8 @@
 
 #endif
 
+#ifndef __ASM_I386__ // don't include the C bits if included from qasm.h
+
 // for windows fastcall option
 #define QDECL
 #define QCALL
@@ -77,6 +79,9 @@
 
 #if defined(_WIN64) || defined(__WIN64__)
 
+#undef idx64
+#define idx64 1
+
 #undef QDECL
 #define QDECL __cdecl
 
@@ -92,13 +97,10 @@
 #define ID_INLINE __inline
 #define PATH_SEP '\\'
 
-#if defined(__x86_64__) || defined(_M_X64)
-#undef idx64
-#define idx64 1
+#if defined( __WIN64__ ) 
 #define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
-#elif defined(__aarch64__) || defined(__ARM64__) || defined (_M_ARM64)
-#define ARCH_STRING "arm64"
+#elif defined _M_ALPHA
+#define ARCH_STRING "AXP"
 #endif
 
 #define Q3_LITTLE_ENDIAN
@@ -124,9 +126,8 @@
 
 #if defined( _M_IX86 ) || defined( __i386__ )
 #define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined(__arm__) || defined(_M_ARM)
-#define ARCH_STRING "arm"
+#elif defined _M_ALPHA
+#define ARCH_STRING "AXP"
 #endif
 
 #define Q3_LITTLE_ENDIAN
@@ -136,9 +137,14 @@
 #endif
 
 
-//================================================================ MAC OS ===
+//============================================================== MAC OS X ===
 
-#if defined(__APPLE__) || defined(__APPLE_CC__)
+#if defined(MACOS_X) || defined(__APPLE_CC__)
+
+// make sure this is defined, just for sanity's sake...
+#ifndef MACOS_X
+#define MACOS_X
+#endif
 
 #define OS_STRING "macosx"
 #define ID_INLINE inline
@@ -147,19 +153,19 @@
 #ifdef __ppc__
 #define ARCH_STRING "ppc"
 #define Q3_BIG_ENDIAN
-#define HAVE_VM_COMPILED
 #elif defined __i386__
 #define ARCH_STRING "x86"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
 #elif defined __x86_64__
 #undef idx64
 #define idx64 1
 #define ARCH_STRING "x86_64"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
 #elif defined __aarch64__
-#define ARCH_STRING "arm64"
+#define ARCH_STRING "aarch64"
+#define Q3_LITTLE_ENDIAN
+#elif defined __arm__
+#define ARCH_STRING "arm"
 #define Q3_LITTLE_ENDIAN
 #endif
 
@@ -169,46 +175,56 @@
 
 //================================================================= LINUX ===
 
-#if defined(__linux__) || defined(__FreeBSD_kernel__) || defined(__GNU__)
+#if defined(__linux__) || defined(__FreeBSD_kernel__)
 
 #include <endian.h>
 
 #if defined(__linux__)
 #define OS_STRING "linux"
-#elif defined(__FreeBSD_kernel__)
-#define OS_STRING "kFreeBSD"
 #else
-#define OS_STRING "GNU"
+#define OS_STRING "kFreeBSD"
 #endif
 
 #define ID_INLINE inline
 
 #define PATH_SEP '/'
 
-#if defined(__x86_64__) || defined(__amd64__)
-# define ARCH_STRING "x86_64"
-# define HAVE_VM_COMPILED
-#elif defined(__i386__)
-# define ARCH_STRING "x86"
-# define HAVE_VM_COMPILED
-#elif defined(__aarch64__)
-# define ARCH_STRING "arm64"
-#elif defined(__arm__)
-# define ARCH_STRING "arm"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc64__) || defined(__ppc64__)
-# define ARCH_STRING "ppc64"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc__) || defined(__ppc__)
-# define ARCH_STRING "ppc"
-# define HAVE_VM_COMPILED
-#elif defined(__alpha__)
-# define ARCH_STRING "alpha"
-#endif
-
-#if defined __x86_64__
+#if defined __i386__
+#define ARCH_STRING "x86"
+#elif defined __x86_64__
 #undef idx64
 #define idx64 1
+#define ARCH_STRING "x86_64"
+#elif defined __powerpc64__
+#define ARCH_STRING "ppc64"
+#elif defined __powerpc__
+#define ARCH_STRING "ppc"
+#elif defined __s390__
+#define ARCH_STRING "s390"
+#elif defined __s390x__
+#define ARCH_STRING "s390x"
+#elif defined __ia64__
+#define ARCH_STRING "ia64"
+#elif defined __alpha__
+#define ARCH_STRING "alpha"
+#elif defined __sparc__
+#define ARCH_STRING "sparc"
+#elif defined __arm__
+#define ARCH_STRING "arm"
+#elif defined __aarch64__
+#define ARCH_STRING "aarch64"
+#elif defined __riscv
+#define ARCH_STRING "riscv"
+#elif defined __cris__
+#define ARCH_STRING "cris"
+#elif defined __hppa__
+#define ARCH_STRING "hppa"
+#elif defined __mips__
+#define ARCH_STRING "mips"
+#elif defined __sh__
+#define ARCH_STRING "sh"
+#elif defined __e2k__
+#define ARCH_STRING "e2k"
 #endif
 
 #if __FLOAT_WORD_ORDER == __BIG_ENDIAN
@@ -245,12 +261,10 @@
 
 #ifdef __i386__
 #define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
 #elif defined __amd64__
 #undef idx64
 #define idx64 1
 #define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
 #elif defined __axp__
 #define ARCH_STRING "alpha"
 #endif
@@ -278,10 +292,8 @@
 
 #ifdef __i386__
 #define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
 #elif defined __sparc
 #define ARCH_STRING "sparc"
-#define HAVE_VM_COMPILED
 #endif
 
 #if defined( _BIG_ENDIAN )
@@ -310,22 +322,6 @@
 
 #endif
 
-//============================================================ EMSCRIPTEN ===
-
-#ifdef __EMSCRIPTEN__
-
-#define OS_STRING "emscripten"
-#define ID_INLINE inline
-#define PATH_SEP '/'
-
-#define ARCH_STRING "wasm32"
-
-#define Q3_LITTLE_ENDIAN
-
-#define DLL_EXT ".wasm"
-
-#endif
-
 //================================================================== Q3VM ===
 
 #ifdef Q3_VM
@@ -342,16 +338,13 @@
 
 //===========================================================================
 
-// Catch missing defines in above blocks
-
-#ifndef OS_STRING
+//catch missing defines in above blocks
+#if !defined( OS_STRING )
 #error "Operating system not supported"
 #endif
 
-#ifndef ARCH_STRING
-// ARCH_STRING is (mostly) only used for informational purposes, so we allow
-// it to be undefined so that more diverse architectures may be compiled
-#define ARCH_STRING "unknown"
+#if !defined( ARCH_STRING )
+#error "Architecture not supported"
 #endif
 
 #ifndef ID_INLINE
@@ -413,10 +406,12 @@
 
 
 //platform string
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING
 #else
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING "-debug"
 #endif
 
 #endif
+
+#endif

```

### `openarena-gamecode`  — sha256 `4cfc4a7ec8a3...`, 7625 bytes

_Diff stat: +37 / -108 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_platform.h	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\qcommon\q_platform.h	2026-04-16 22:48:24.194008900 +0100
@@ -24,14 +24,11 @@
 #define __Q_PLATFORM_H
 
 // this is for determining if we have an asm version of a C function
-#define idx64 0
-
 #ifdef Q3_VM
 
 #define id386 0
 #define idppc 0
 #define idppc_altivec 0
-#define idsparc 0
 
 #else
 
@@ -46,7 +43,7 @@
 #define idppc 1
 #if defined(__VEC__)
 #define idppc_altivec 1
-#ifdef __APPLE__  // Apple's GCC does this differently than the FSF.
+#ifdef MACOS_X  // Apple's GCC does this differently than the FSF.
 #define VECCONST_UINT8(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) \
 	(vector unsigned char) (a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p)
 #else
@@ -61,58 +58,48 @@
 #define idppc_altivec 0
 #endif
 
-#if defined(__sparc__) && !defined(C_ONLY)
-#define idsparc 1
-#else
-#define idsparc 0
 #endif
 
-#endif
+#ifndef __ASM_I386__ // don't include the C bits if included from qasm.h
 
 // for windows fastcall option
 #define QDECL
-#define QCALL
 
-//================================================================= WIN64/32 ===
+//================================================================= WIN32 ===
 
-#if defined(_WIN64) || defined(__WIN64__)
+#ifdef __MINGW32__
 
 #undef QDECL
 #define QDECL __cdecl
 
-#undef QCALL
-#define QCALL __stdcall
-
 #if defined( _MSC_VER )
-#define OS_STRING "win_msvc64"
-#elif defined __MINGW64__
-#define OS_STRING "win_mingw64"
+#define OS_STRING "win_msvc"
+#elif defined __MINGW32__
+#define OS_STRING "win_mingw"
 #endif
 
 #define ID_INLINE __inline
 #define PATH_SEP '\\'
 
-#if defined(__x86_64__) || defined(_M_X64)
-#undef idx64
-#define idx64 1
-#define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
-#elif defined(__aarch64__) || defined(__ARM64__) || defined (_M_ARM64)
-#define ARCH_STRING "arm64"
+#if defined( _M_IX86 ) || defined( __i386__ )
+#define ARCH_STRING "x86"
+#elif defined _M_ALPHA
+#define ARCH_STRING "AXP"
 #endif
 
 #define Q3_LITTLE_ENDIAN
 
 #define DLL_EXT ".dll"
 
-#elif defined(_WIN32) || defined(__WIN32__)
+#endif
+
+//KK-OAX, This is a little hack to be able to build dll's for debugging under Visual Studio
+//Simple copy/paste/rename of the #ifdef __MINGW32__
+#ifdef VSTUDIO
 
 #undef QDECL
 #define QDECL __cdecl
 
-#undef QCALL
-#define QCALL __stdcall
-
 #if defined( _MSC_VER )
 #define OS_STRING "win_msvc"
 #elif defined __MINGW32__
@@ -124,9 +111,8 @@
 
 #if defined( _M_IX86 ) || defined( __i386__ )
 #define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined(__arm__) || defined(_M_ARM)
-#define ARCH_STRING "arm"
+#elif defined _M_ALPHA
+#define ARCH_STRING "AXP"
 #endif
 
 #define Q3_LITTLE_ENDIAN
@@ -134,11 +120,14 @@
 #define DLL_EXT ".dll"
 
 #endif
+//============================================================== MAC OS X ===
 
+#if defined(MACOS_X) || defined(__APPLE_CC__)
 
-//================================================================ MAC OS ===
-
-#if defined(__APPLE__) || defined(__APPLE_CC__)
+// make sure this is defined, just for sanity's sake...
+#ifndef MACOS_X
+#define MACOS_X
+#endif
 
 #define OS_STRING "macosx"
 #define ID_INLINE inline
@@ -147,20 +136,12 @@
 #ifdef __ppc__
 #define ARCH_STRING "ppc"
 #define Q3_BIG_ENDIAN
-#define HAVE_VM_COMPILED
 #elif defined __i386__
-#define ARCH_STRING "x86"
+#define ARCH_STRING "i386"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
 #elif defined __x86_64__
-#undef idx64
-#define idx64 1
 #define ARCH_STRING "x86_64"
 #define Q3_LITTLE_ENDIAN
-#define HAVE_VM_COMPILED
-#elif defined __aarch64__
-#define ARCH_STRING "arm64"
-#define Q3_LITTLE_ENDIAN
 #endif
 
 #define DLL_EXT ".dylib"
@@ -182,33 +163,10 @@
 #endif
 
 #define ID_INLINE inline
-
 #define PATH_SEP '/'
 
-#if defined(__x86_64__) || defined(__amd64__)
-# define ARCH_STRING "x86_64"
-# define HAVE_VM_COMPILED
-#elif defined(__i386__)
-# define ARCH_STRING "x86"
-# define HAVE_VM_COMPILED
-#elif defined(__aarch64__)
-# define ARCH_STRING "arm64"
-#elif defined(__arm__)
-# define ARCH_STRING "arm"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc64__) || defined(__ppc64__)
-# define ARCH_STRING "ppc64"
-# define HAVE_VM_COMPILED
-#elif defined(__powerpc__) || defined(__ppc__)
-# define ARCH_STRING "ppc"
-# define HAVE_VM_COMPILED
-#elif defined(__alpha__)
-# define ARCH_STRING "alpha"
-#endif
-
-#if defined __x86_64__
-#undef idx64
-#define idx64 1
+#if !defined(ARCH_STRING)
+# error ARCH_STRING should be defined by the Makefile
 #endif
 
 #if __FLOAT_WORD_ORDER == __BIG_ENDIAN
@@ -244,13 +202,9 @@
 #define PATH_SEP '/'
 
 #ifdef __i386__
-#define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
-#elif defined __amd64__
-#undef idx64
-#define idx64 1
+#define ARCH_STRING "i386"
+#elif defined __x86_64__ || defined __amd64__
 #define ARCH_STRING "x86_64"
-#define HAVE_VM_COMPILED
 #elif defined __axp__
 #define ARCH_STRING "alpha"
 #endif
@@ -277,11 +231,9 @@
 #define PATH_SEP '/'
 
 #ifdef __i386__
-#define ARCH_STRING "x86"
-#define HAVE_VM_COMPILED
+#define ARCH_STRING "i386"
 #elif defined __sparc
 #define ARCH_STRING "sparc"
-#define HAVE_VM_COMPILED
 #endif
 
 #if defined( _BIG_ENDIAN )
@@ -310,22 +262,6 @@
 
 #endif
 
-//============================================================ EMSCRIPTEN ===
-
-#ifdef __EMSCRIPTEN__
-
-#define OS_STRING "emscripten"
-#define ID_INLINE inline
-#define PATH_SEP '/'
-
-#define ARCH_STRING "wasm32"
-
-#define Q3_LITTLE_ENDIAN
-
-#define DLL_EXT ".wasm"
-
-#endif
-
 //================================================================== Q3VM ===
 
 #ifdef Q3_VM
@@ -342,16 +278,13 @@
 
 //===========================================================================
 
-// Catch missing defines in above blocks
-
-#ifndef OS_STRING
+//catch missing defines in above blocks
+#if !defined( OS_STRING )
 #error "Operating system not supported"
 #endif
 
-#ifndef ARCH_STRING
-// ARCH_STRING is (mostly) only used for informational purposes, so we allow
-// it to be undefined so that more diverse architectures may be compiled
-#define ARCH_STRING "unknown"
+#if !defined( ARCH_STRING )
+#error "Architecture not supported"
 #endif
 
 #ifndef ID_INLINE
@@ -368,8 +301,6 @@
 
 
 //endianness
-void CopyShortSwap (void *dest, void *src);
-void CopyLongSwap (void *dest, void *src);
 short ShortSwap (short l);
 int LongSwap (int l);
 float FloatSwap (const float *f);
@@ -378,8 +309,6 @@
 #error "Endianness defined as both big and little"
 #elif defined( Q3_BIG_ENDIAN )
 
-#define CopyLittleShort(dest, src) CopyShortSwap(dest, src)
-#define CopyLittleLong(dest, src) CopyLongSwap(dest, src)
 #define LittleShort(x) ShortSwap(x)
 #define LittleLong(x) LongSwap(x)
 #define LittleFloat(x) FloatSwap(&x)
@@ -389,8 +318,6 @@
 
 #elif defined( Q3_LITTLE_ENDIAN )
 
-#define CopyLittleShort(dest, src) Com_Memcpy(dest, src, 2)
-#define CopyLittleLong(dest, src) Com_Memcpy(dest, src, 4)
 #define LittleShort
 #define LittleLong
 #define LittleFloat
@@ -413,10 +340,12 @@
 
 
 //platform string
-#ifdef NQDEBUG
+#ifdef NDEBUG
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING
 #else
 #define PLATFORM_STRING OS_STRING "-" ARCH_STRING "-debug"
 #endif
 
 #endif
+
+#endif

```
