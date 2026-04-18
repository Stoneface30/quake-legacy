# Diff: `libs/cmdlib.h`
**Canonical:** `quake3-source` (sha256 `168ad358d1ce...`, 3189 bytes)

## Variants

### `gtkradiant`  — sha256 `adf8c189857c...`, 3118 bytes

_Diff stat: +70 / -72 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\libs\cmdlib.h	2026-04-16 20:02:20.114411700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\gtkradiant\libs\cmdlib.h	2026-04-16 22:48:36.868805600 +0100
@@ -1,27 +1,27 @@
 /*
-===========================================================================
-Copyright (C) 1999-2005 Id Software, Inc.
+   Copyright (C) 1999-2007 id Software, Inc. and contributors.
+   For a list of contributors, see the accompanying CONTRIBUTORS file.
 
-This file is part of Quake III Arena source code.
+   This file is part of GtkRadiant.
+
+   GtkRadiant is free software; you can redistribute it and/or modify
+   it under the terms of the GNU General Public License as published by
+   the Free Software Foundation; either version 2 of the License, or
+   (at your option) any later version.
+
+   GtkRadiant is distributed in the hope that it will be useful,
+   but WITHOUT ANY WARRANTY; without even the implied warranty of
+   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+   GNU General Public License for more details.
+
+   You should have received a copy of the GNU General Public License
+   along with GtkRadiant; if not, write to the Free Software
+   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+ */
 
-Quake III Arena source code is free software; you can redistribute it
-and/or modify it under the terms of the GNU General Public License as
-published by the Free Software Foundation; either version 2 of the License,
-or (at your option) any later version.
-
-Quake III Arena source code is distributed in the hope that it will be
-useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
-MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-GNU General Public License for more details.
-
-You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
-Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
-===========================================================================
-*/
 //
 // start of shared cmdlib stuff
-// 
+//
 
 #ifndef __CMDLIB__
 #define __CMDLIB__
@@ -33,65 +33,63 @@
 #include <ctype.h>
 #include <time.h>
 #include <stdarg.h>
-
-#ifndef __BYTEBOOL__
-#define __BYTEBOOL__
-
-#ifndef __cplusplus
-  typedef enum {false, true} boolean;
-#else
-  typedef unsigned char boolean;
+#include <limits.h>
+#ifdef _WIN32
+  #define PATH_MAX 260
 #endif
 
+#include "bytebool.h"
 
-typedef unsigned char byte;
-//typedef unsigned char byte;
+// some easy portability crap
+#ifdef _WIN32
+  #include <direct.h>
+  #define Q_mkdir( a,b ) _mkdir( a )
+#else
+  #include <sys/stat.h>
+  #define Q_mkdir( a,b ) mkdir( a,b )
 #endif
 
-FILE	*SafeOpenWrite (const char *filename);
-FILE	*SafeOpenRead (const char *filename);
-void	SafeRead (FILE *f, void *buffer, int count);
-void	SafeWrite (FILE *f, const void *buffer, int count);
-int		LoadFile (const char *filename, void **bufferptr);
-int		LoadFileNoCrash (const char *filename, void **bufferptr);
-void	SaveFile (const char *filename, void *buffer, int count);
-void 	DefaultExtension (char *path, char *extension);
-void 	DefaultPath (char *path, char *basepath);
-void 	StripFilename (char *path);
-void 	StripExtension (char *path);
-void 	ExtractFilePath (const char *path, char *dest);
-void	ExtractFileName (const char *path, char *dest);
-void 	ExtractFileBase (const char *path, char *dest);
-void	ExtractFileExtension (const char *path, char *dest);
-short	BigShort (short l);
-short	LittleShort (short l);
-int		BigLong (int l);
-int		LittleLong (int l);
-float	BigFloat (float l);
-float	LittleFloat (float l);
-void *qmalloc (size_t size);
-void* qblockmalloc(size_t nSize);
-
-
+void    DefaultExtension( char *path, char *extension );
+void    DefaultPath( char *path, char *basepath );
+void    StripFilename( char *path );
+void    StripExtension( char *path );
+void    ExtractFilePath( const char *path, char *dest );
+void    ExtractFileName( const char *path, char *dest );
+void    ExtractFileBase( const char *path, char *dest );
+void    ExtractFileExtension( const char *path, char *dest );
+/*!
+   \brief create all directories leading to a file path. if you pass a directory, terminate it with a '/'
+ */
+void  CreateDirectoryPath( const char *path );
+
+short   BigShort( short l );
+short   LittleShort( short l );
+int     BigLong( int l );
+int     LittleLong( int l );
+float   BigFloat( float l );
+float   LittleFloat( float l );
+void *qmalloc( size_t size );
+void* qblockmalloc( size_t nSize );
 
-// error and printf functions
-typedef void (PFN_ERR)(const char *pFormat, ...);
-typedef void (PFN_PRINTF)(const char *pFormat, ...);
-typedef void (PFN_ERR_NUM)(int nNum, const char *pFormat, ...);
-typedef void (PFN_PRINTF_NUM)(int nNum, const char *pFormat, ...);
-
-void Error(const char *pFormat, ...);
-void Printf(const char *pFormat, ...);
-void ErrorNum(int n, const char *pFormat, ...);
-void PrintfNum(int n, const char *pFormat, ...);
-
-void SetErrorHandler(PFN_ERR pe);
-void SetPrintfHandler(PFN_PRINTF pe);
-void SetErrorHandlerNum(PFN_ERR_NUM pe);
-void SetPrintfHandlerNum(PFN_PRINTF_NUM pe);
 void ConvertDOSToUnixName( char *dst, const char *src );
-char* StrDup(char* pStr);
-char* StrDup(const char* pStr);
+#ifdef __cplusplus
+char* StrDup( char* pStr );
+#endif
+char* StrDup( const char* pStr );
 
+// TTimo started adding portability code:
+// return true if spawning was successful, false otherwise
+// on win32 we have a bCreateConsole flag to create a new console or run inside the current one
+//boolean Q_Exec(const char* pCmd, boolean bCreateConsole);
+// execute a system command:
+//   cmd: the command to run
+//   cmdline: the command line
+// NOTE TTimo following are win32 specific:
+//   execdir: the directory to execute in
+//   bCreateConsole: spawn a new console or not
+// return values;
+//   if the spawn was fine
+//   TODO TTimo add functionality to track the process until it dies
+bool Q_Exec( const char *cmd, char *cmdline, const char *execdir, bool bCreateConsole );
 
-#endif
\ No newline at end of file
+#endif

```
