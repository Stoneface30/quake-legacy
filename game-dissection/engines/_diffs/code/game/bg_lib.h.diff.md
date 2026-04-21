# Diff: `code/game/bg_lib.h`
**Canonical:** `wolfcamql-src` (sha256 `a730c2e46744...`, 4977 bytes)

## Variants

### `quake3-source`  — sha256 `3edd217b9032...`, 3740 bytes

_Diff stat: +15 / -45 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.h	2026-04-16 20:02:25.188640000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\bg_lib.h	2026-04-16 20:02:19.902126400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,14 +23,8 @@
 // compiled for the virtual machine
 
 // This file is NOT included on native builds
-#if !defined( BG_LIB_H ) && defined( Q3_VM )
-#define BG_LIB_H
 
-#ifndef NULL
-#define NULL ((void *)0)
-#endif
-
-typedef unsigned int size_t;
+typedef int size_t;
 
 typedef char *  va_list;
 #define _INTSIZEOF(n)   ( (sizeof(n) + sizeof(int) - 1) & ~(sizeof(int) - 1) )
@@ -38,37 +32,21 @@
 #define va_arg(ap,t)    ( *(t *)((ap += _INTSIZEOF(t)) - _INTSIZEOF(t)) )
 #define va_end(ap)      ( ap = (va_list)0 )
 
-#define CHAR_BIT      8             /* number of bits in a char */
-#define SCHAR_MAX     0x7f          /* maximum signed char value */
-#define SCHAR_MIN   (-SCHAR_MAX - 1) /* minimum signed char value */
-#define UCHAR_MAX     0xff          /* maximum unsigned char value */
+#define CHAR_BIT      8         /* number of bits in a char */
+#define SCHAR_MIN   (-128)      /* minimum signed char value */
+#define SCHAR_MAX     127       /* maximum signed char value */
+#define UCHAR_MAX     0xff      /* maximum unsigned char value */
 
-#define SHRT_MAX      0x7fff        /* maximum (signed) short value */
-#define SHRT_MIN    (-SHRT_MAX - 1) /* minimum (signed) short value */
+#define SHRT_MIN    (-32768)        /* minimum (signed) short value */
+#define SHRT_MAX      32767         /* maximum (signed) short value */
 #define USHRT_MAX     0xffff        /* maximum unsigned short value */
-#define INT_MAX       0x7fffffff    /* maximum (signed) int value */
-#define INT_MIN     (-INT_MAX - 1)  /* minimum (signed) int value */
+#define INT_MIN     (-2147483647 - 1) /* minimum (signed) int value */
+#define INT_MAX       2147483647    /* maximum (signed) int value */
 #define UINT_MAX      0xffffffff    /* maximum unsigned int value */
-#define LONG_MAX      0x7fffffffL   /* maximum (signed) long value */
-#define LONG_MIN    (-LONG_MAX - 1) /* minimum (signed) long value */
+#define LONG_MIN    (-2147483647L - 1) /* minimum (signed) long value */
+#define LONG_MAX      2147483647L   /* maximum (signed) long value */
 #define ULONG_MAX     0xffffffffUL  /* maximum unsigned long value */
 
-#define isalnum(c)  (isalpha(c) || isdigit(c))
-#define isalpha(c)  (isupper(c) || islower(c))
-#define isascii(c)  ((c) > 0 && (c) <= 0x7f)
-#define iscntrl(c)  (((c) >= 0) && (((c) <= 0x1f) || ((c) == 0x7f)))
-#define isdigit(c)  ((c) >= '0' && (c) <= '9')
-#define isgraph(c)  ((c) != ' ' && isprint(c))
-#define islower(c)  ((c) >=  'a' && (c) <= 'z')
-#define isprint(c)  ((c) >= ' ' && (c) <= '~')
-#define ispunct(c)  (((c) > ' ' && (c) <= '~') && !isalnum(c))
-#define isspace(c)  ((c) ==  ' ' || (c) == '\f' || (c) == '\n' || (c) == '\r' || \
-                     (c) == '\t' || (c) == '\v')
-#define isupper(c)  ((c) >=  'A' && (c) <= 'Z')
-#define isxdigit(c) (isxupper(c) || isxlower(c))
-#define isxlower(c) (isdigit(c) || (c >= 'a' && c <= 'f'))
-#define isxupper(c) (isdigit(c) || (c >= 'A' && c <= 'F')) 
-
 // Misc functions
 typedef int cmp_t(const void *, const void *);
 void qsort(void *a, size_t n, size_t es, cmp_t *cmp);
@@ -81,7 +59,6 @@
 char *strcpy( char *strDestination, const char *strSource );
 int strcmp( const char *string1, const char *string2 );
 char *strchr( const char *string, int c );
-char *strrchr(const char *string, int c);
 char *strstr( const char *string, const char *strCharSet );
 char *strncpy( char *strDest, const char *strSource, size_t count );
 int tolower( int c );
@@ -89,14 +66,11 @@
 
 double atof( const char *string );
 double _atof( const char **stringPtr );
-double strtod( const char *nptr, char **endptr );
 int atoi( const char *string );
 int _atoi( const char **stringPtr );
-long strtol( const char *nptr, char **endptr, int base );
 
-int Q_vsnprintf( char *buffer, size_t length, const char *fmt, va_list argptr ) Q_PRINTF_FUNC(3, 0);
-
-int sscanf( const char *buffer, const char *fmt, ... ) Q_SCANF_FUNC(2, 3);
+int vsprintf( char *buffer, const char *fmt, va_list argptr );
+int sscanf( const char *buffer, const char *fmt, ... );
 
 // Memory functions
 void *memmove( void *dest, const void *src, size_t count );
@@ -113,9 +87,5 @@
 double tan( double x );
 int abs( int n );
 double fabs( double x );
+double acos( double x );
 
-#ifndef Q3_VM
-double acos (double x);
-#endif
-
-#endif // BG_LIB_H

```

### `ioquake3`  — sha256 `41f24c4919bc...`, 4953 bytes

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.h	2026-04-16 20:02:25.188640000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\bg_lib.h	2026-04-16 20:02:21.539886500 +0100
@@ -113,9 +113,6 @@
 double tan( double x );
 int abs( int n );
 double fabs( double x );
-
-#ifndef Q3_VM
-double acos (double x);
-#endif
+double acos( double x );
 
 #endif // BG_LIB_H

```

### `openarena-engine`  — sha256 `d02e31d3c57c...`, 5083 bytes

_Diff stat: +10 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.h	2026-04-16 20:02:25.188640000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\bg_lib.h	2026-04-16 22:48:25.743535300 +0100
@@ -26,6 +26,13 @@
 #if !defined( BG_LIB_H ) && defined( Q3_VM )
 #define BG_LIB_H
 
+//Ignore __attribute__ on non-gcc platforms
+#ifndef __GNUC__
+#ifndef __attribute__
+#define __attribute__(x)
+#endif
+#endif
+
 #ifndef NULL
 #define NULL ((void *)0)
 #endif
@@ -94,9 +101,9 @@
 int _atoi( const char **stringPtr );
 long strtol( const char *nptr, char **endptr, int base );
 
-int Q_vsnprintf( char *buffer, size_t length, const char *fmt, va_list argptr ) Q_PRINTF_FUNC(3, 0);
+int Q_vsnprintf( char *buffer, size_t length, const char *fmt, va_list argptr );
 
-int sscanf( const char *buffer, const char *fmt, ... ) Q_SCANF_FUNC(2, 3);
+int sscanf( const char *buffer, const char *fmt, ... ) __attribute__ ((format (scanf, 2, 3)));
 
 // Memory functions
 void *memmove( void *dest, const void *src, size_t count );
@@ -113,9 +120,6 @@
 double tan( double x );
 int abs( int n );
 double fabs( double x );
-
-#ifndef Q3_VM
-double acos (double x);
-#endif
+double acos( double x );
 
 #endif // BG_LIB_H

```

### `openarena-gamecode`  — sha256 `0789ef64c439...`, 5226 bytes

_Diff stat: +15 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.h	2026-04-16 20:02:25.188640000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\bg_lib.h	2026-04-16 22:48:24.163478100 +0100
@@ -26,11 +26,18 @@
 #if !defined( BG_LIB_H ) && defined( Q3_VM )
 #define BG_LIB_H
 
+//Ignore __attribute__ on non-gcc platforms
+#ifndef __GNUC__
+#ifndef __attribute__
+#define __attribute__(x)
+#endif
+#endif
+
 #ifndef NULL
 #define NULL ((void *)0)
 #endif
 
-typedef unsigned int size_t;
+typedef int size_t;
 
 typedef char *  va_list;
 #define _INTSIZEOF(n)   ( (sizeof(n) + sizeof(int) - 1) & ~(sizeof(int) - 1) )
@@ -52,6 +59,7 @@
 #define LONG_MAX      0x7fffffffL   /* maximum (signed) long value */
 #define LONG_MIN    (-LONG_MAX - 1) /* minimum (signed) long value */
 #define ULONG_MAX     0xffffffffUL  /* maximum unsigned long value */
+#define RAND_MAX      0x7fff
 
 #define isalnum(c)  (isalpha(c) || isdigit(c))
 #define isalpha(c)  (isupper(c) || islower(c))
@@ -89,14 +97,15 @@
 
 double atof( const char *string );
 double _atof( const char **stringPtr );
-double strtod( const char *nptr, char **endptr );
+double strtod( const char *nptr, const char **endptr );
 int atoi( const char *string );
 int _atoi( const char **stringPtr );
-long strtol( const char *nptr, char **endptr, int base );
+long strtol( const char *nptr, const char **endptr, int base );
 
-int Q_vsnprintf( char *buffer, size_t length, const char *fmt, va_list argptr ) Q_PRINTF_FUNC(3, 0);
+int Q_vsnprintf( char *buffer, size_t length, const char *fmt, va_list argptr );
+int Q_snprintf( char *buffer, size_t length, const char *fmt, ... ) __attribute__ ((format (printf, 3, 4)));
 
-int sscanf( const char *buffer, const char *fmt, ... ) Q_SCANF_FUNC(2, 3);
+int sscanf( const char *buffer, const char *fmt, ... ) __attribute__ ((format (scanf, 2, 3)));
 
 // Memory functions
 void *memmove( void *dest, const void *src, size_t count );
@@ -113,9 +122,6 @@
 double tan( double x );
 int abs( int n );
 double fabs( double x );
-
-#ifndef Q3_VM
-double acos (double x);
-#endif
+double acos( double x );
 
 #endif // BG_LIB_H

```
