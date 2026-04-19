# Diff: `libs/pakstuff.h`
**Canonical:** `quake3-source` (sha256 `151441c0edb0...`, 4737 bytes)

## Variants

### `gtkradiant`  — sha256 `02c15203ef55...`, 4804 bytes

_Diff stat: +81 / -74 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\libs\pakstuff.h	2026-04-16 20:02:20.122999800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\gtkradiant\libs\pakstuff.h	2026-04-16 22:48:36.876832500 +0100
@@ -1,45 +1,52 @@
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
 #ifndef _PAKSTUFF_H_
 #define _PAKSTUFF_H_
 
+#ifndef _WIN32
+#define WINAPI
+#else
 #include <windows.h>
+#endif
+
+#include "bytebool.h"
+
 #ifdef __cplusplus
 extern "C"
 {
 #endif
 
-typedef char           Int8;
-typedef short          Int16;
-typedef long           Int32;
-typedef unsigned char  UInt8;
+typedef char Int8;
+typedef short Int16;
+typedef long Int32;
+typedef unsigned char UInt8;
 typedef unsigned short UInt16;
-typedef unsigned long  UInt32;
-typedef float          Float32;
-typedef double         Float64;
-#define MAX(a, b)              (((a) > (b)) ? (a) : (b))
-#define MIN(a, b)              (((a) < (b)) ? (a) : (b))
-#define RANDOM(x)              (random() % (x))
-#define RANDOMIZE()             srand((int) time(NULL))
+typedef unsigned long UInt32;
+typedef float Float32;
+typedef double Float64;
+#define MAX( a, b )              ( ( ( a ) > ( b ) ) ? ( a ) : ( b ) )
+#define MIN( a, b )              ( ( ( a ) < ( b ) ) ? ( a ) : ( b ) )
+#define RANDOM( x )              ( random() % ( x ) )
+#define RANDOMIZE()             srand( (int) time( NULL ) )
 
 #define FTYPE_UNKNOWN 0
 #define FTYPE_IWAD    1    /* .wad  "IWAD" */
@@ -64,75 +71,75 @@
 #define FTYPE_ERROR   -1
 
 #ifdef FAT_ENDIAN
-Bool	ReadInt16		(FILE *file, UInt16 huge *x);
-Bool	ReadInt32		(FILE *file, UInt32 huge *x);
-Bool	ReadFloat32		(FILE *file, Float32 huge *x);
-Bool	WriteInt16		(FILE *file, UInt16 huge *x);
-Bool	WriteInt32		(FILE *file, UInt32 huge *x);
-Bool	WriteFloat32	(FILE *file, Float32 huge *x);
-UInt16	SwapInt16		(UInt16 x);
-UInt32	SwapInt32		(UInt32 x);
-Float32	SwapFloat32		(Float32 x);
+Bool    ReadInt16( FILE *file, UInt16 huge *x );
+Bool    ReadInt32( FILE *file, UInt32 huge *x );
+Bool    ReadFloat32( FILE *file, Float32 huge *x );
+Bool    WriteInt16( FILE *file, UInt16 huge *x );
+Bool    WriteInt32( FILE *file, UInt32 huge *x );
+Bool    WriteFloat32( FILE *file, Float32 huge *x );
+UInt16  SwapInt16( UInt16 x );
+UInt32  SwapInt32( UInt32 x );
+Float32 SwapFloat32( Float32 x );
 #else
-#define ReadInt16(f, p)		ReadBytes((f), (p), 2L)
-#define ReadInt32(f, p)		ReadBytes((f), (p), 4L)
-#define ReadFloat32(f, p)	ReadBytes((f), (p), 4L)
-#define WriteInt16(f, p)	WriteBytes((f), (p), 2L)
-#define WriteInt32(f, p)	WriteBytes((f), (p), 4L)
-#define WriteFloat32(f, p)	WriteBytes((f), (p), 4L)
-#define SwapInt16(x)		(x)
-#define SwapInt32(x)		(x)
-#define SwapFloat32(x)		(x)
+#define ReadInt16( f, p )     ReadBytes( ( f ), ( p ), 2L )
+#define ReadInt32( f, p )     ReadBytes( ( f ), ( p ), 4L )
+#define ReadFloat32( f, p )   ReadBytes( ( f ), ( p ), 4L )
+#define WriteInt16( f, p )    WriteBytes( ( f ), ( p ), 2L )
+#define WriteInt32( f, p )    WriteBytes( ( f ), ( p ), 4L )
+#define WriteFloat32( f, p )  WriteBytes( ( f ), ( p ), 4L )
+#define SwapInt16( x )        ( x )
+#define SwapInt32( x )        ( x )
+#define SwapFloat32( x )      ( x )
 #endif /* FAT_ENDIAN */
 
-#define FROMDISK	-1
+#define FROMDISK    -1
 struct PACKDirectory
 {
-   char   name[56];             /* name of file */
-   UInt32 offset;               /* offset to start of data */
-   UInt32 size;                 /* byte size of data */
+	char name[56];              /* name of file */
+	UInt32 offset;              /* offset to start of data */
+	UInt32 size;                /* byte size of data */
 };
 typedef struct PACKDirectory *PACKDirPtr;
 
 typedef struct DirListStruct
 {
-	char					dirname[1024];
-	int						from;
-	struct	DirListStruct	*next;
+	char dirname[1024];
+	int from;
+	struct  DirListStruct   *next;
 } DIRLIST;
 
 typedef struct FileListStruct
 {
-	char					filename[1024];
-	UInt32					offset;
-	UInt32					size;
-	struct	FileListStruct	*next;
+	char filename[1024];
+	UInt32 offset;
+	UInt32 size;
+	struct  FileListStruct  *next;
 } FILELIST;
 
 typedef struct DirStruct
 {
-	char				name[1024];
-	FILELIST			*files;
-	struct DirStruct	*next;
+	char name[1024];
+	FILELIST            *files;
+	struct DirStruct    *next;
 } DIRECTORY;
 
 
 extern int m_nPAKIndex;
 extern FILE* pakfile[16];
-extern boolean pakopen;
-extern DIRECTORY	*paktextures;
+extern bool pakopen;
+extern DIRECTORY    *paktextures;
 
-void	ClearFileList				(FILELIST **);
-void	ClearDirList				(DIRLIST **);
-boolean		GetPackFileList				(FILELIST **, char *);
-boolean		GetPackTextureDirs			(DIRLIST **);
-boolean	AddToDirListAlphabetized	(DIRLIST **, char *, int);
-boolean	AddToFileListAlphabetized	(FILELIST **t, char *, UInt32, UInt32, boolean);
-boolean	PakLoadFile					(const char *, void **);
-void	OpenPakFile					(const char *);
-void	ClosePakFile				(void);
-int PakLoadAnyFile(const char *filename, void **bufferptr);
-void WINAPI InitPakFile(const char * pBasePath, const char *pName);
+void ClearFileList( FILELIST ** );
+void ClearDirList( DIRLIST ** );
+bool GetPackFileList( FILELIST **, char * );
+bool GetPackTextureDirs( DIRLIST ** );
+bool AddToDirListAlphabetized( DIRLIST **, char *, int );
+bool AddToFileListAlphabetized( FILELIST * *t, char *, UInt32, UInt32, bool );
+bool PakLoadFile( const char *, void ** );
+void OpenPakFile( const char * );
+void ClosePakFile( void );
+int  PakLoadAnyFile( const char *filename, void **bufferptr );
+void WINAPI InitPakFile( const char * pBasePath, const char *pName );
 
 #ifdef __cplusplus
 }

```
