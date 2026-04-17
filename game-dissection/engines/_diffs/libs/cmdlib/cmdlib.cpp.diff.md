# Diff: `libs/cmdlib/cmdlib.cpp`
**Canonical:** `quake3-source` (sha256 `f01e7f5c1911...`, 8288 bytes)

## Variants

### `gtkradiant`  — sha256 `8536456df0c0...`, 9296 bytes

_Diff stat: +296 / -375 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\libs\cmdlib\cmdlib.cpp	2026-04-16 20:02:20.114411700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\gtkradiant\libs\cmdlib\cmdlib.cpp	2026-04-16 22:48:36.868805600 +0100
@@ -1,550 +1,471 @@
-//
-// start of shared cmdlib stuff
-// 
-
-
-#include "cmdlib.h"
-#include "windows.h"
-
-#define PATHSEPERATOR   '/'
-
-// rad additions
-// 11.29.99
-PFN_ERR *g_pfnError = NULL;
-PFN_PRINTF *g_pfnPrintf = NULL;
-PFN_ERR_NUM *g_pfnErrorNum = NULL;
-PFN_PRINTF_NUM *g_pfnPrintfNum = NULL;
-
-
-void Error(const char *pFormat, ...)
-{
-  if (g_pfnError)
-  {
-    va_list arg_ptr;
-    va_start(arg_ptr, pFormat);
-    g_pfnError(pFormat, arg_ptr);
-    va_end(arg_ptr);
-  }
-}
-
-void Printf(const char *pFormat, ...)
-{
-  if (g_pfnPrintf)
-  {
-    va_list arg_ptr;
-    va_start(arg_ptr, pFormat);
-    g_pfnPrintf(pFormat, arg_ptr);
-    va_end(arg_ptr);
-  }
-}
+/*
+   Copyright (C) 1999-2007 id Software, Inc. and contributors.
+   For a list of contributors, see the accompanying CONTRIBUTORS file.
 
-void ErrorNum(int nErr, const char *pFormat, ...)
-{
-  if (g_pfnErrorNum)
-  {
-    va_list arg_ptr;
-    va_start(arg_ptr, pFormat);
-    g_pfnErrorNum(nErr, pFormat, arg_ptr);
-    va_end(arg_ptr);
-  }
-}
+   This file is part of GtkRadiant.
 
-void PrintfNum(int nErr, const char *pFormat, ...)
-{
-  if (g_pfnPrintfNum)
-  {
-    va_list arg_ptr;
-    va_start(arg_ptr, pFormat);
-    g_pfnPrintfNum(nErr, pFormat, arg_ptr);
-    va_end(arg_ptr);
-  }
-}
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
 
+//
+// start of shared cmdlib stuff
+//
 
+#include "cmdlib.h"
 
-void SetErrorHandler(PFN_ERR pe)
-{
-  g_pfnError = pe;
-}
+#ifdef _WIN32
+  #include <windows.h>
+#endif
+#if defined( __linux__ ) || defined( __BSD__ ) || defined( __APPLE__ )
+  #include <unistd.h>
+#endif
 
-void SetPrintfHandler(PFN_PRINTF pe)
-{
-  g_pfnPrintf = pe;
-}
+// FIXME TTimo this should be cleaned up ..
+// NOTE: we don't use this crap .. with the total mess of mixing win32/unix paths we need to recognize both '/' and '\\'
+#define PATHSEPERATOR   '/'
 
-void SetErrorHandlerNum(PFN_ERR_NUM pe)
-{
-  g_pfnErrorNum = pe;
+#if defined( __linux__ ) || defined( __BSD__ ) || defined( __APPLE__ )
+bool Q_Exec( const char *cmd, char *cmdline, const char *execdir, bool bCreateConsole ){
+	char fullcmd[2048];
+	char *pCmd;
+#ifdef _DEBUG
+	printf( "Q_Exec damnit\n" );
+#endif
+	switch ( fork() )
+	{
+	case -1:
+		return true;
+		break;
+	case 0:
+		// always concat the command on linux
+		if ( cmd ) {
+			strcpy( fullcmd, cmd );
+		}
+		else{
+			fullcmd[0] = '\0';
+		}
+		if ( cmdline ) {
+			strcat( fullcmd, " " );
+			strcat( fullcmd, cmdline );
+		}
+		pCmd = fullcmd;
+		while ( *pCmd == ' ' )
+			pCmd++;
+#ifdef _DEBUG
+		printf( "Running system...\n" );
+		printf( "Command: %s\n", pCmd );
+#endif
+		system( pCmd );
+#ifdef _DEBUG
+		printf( "system() returned\n" );
+#endif
+		_exit( 0 );
+		break;
+	}
+	return true;
 }
+#endif
 
-void SetPrintfHandler(PFN_PRINTF_NUM pe)
-{
-  g_pfnPrintfNum = pe;
+#ifdef _WIN32
+// NOTE TTimo windows is VERY nitpicky about the syntax in CreateProcess
+bool Q_Exec( const char *cmd, char *cmdline, const char *execdir, bool bCreateConsole ){
+	PROCESS_INFORMATION ProcessInformation;
+	STARTUPINFO startupinfo = {0};
+	DWORD dwCreationFlags;
+	GetStartupInfo( &startupinfo );
+	if ( bCreateConsole ) {
+		dwCreationFlags = CREATE_NEW_CONSOLE | NORMAL_PRIORITY_CLASS;
+	}
+	else{
+		dwCreationFlags = DETACHED_PROCESS | NORMAL_PRIORITY_CLASS;
+	}
+	const char *pCmd;
+	char *pCmdline;
+	pCmd = cmd;
+	if ( pCmd ) {
+		while ( *pCmd == ' ' )
+			pCmd++;
+	}
+	pCmdline = cmdline;
+	if ( pCmdline ) {
+		while ( *pCmdline == ' ' )
+			pCmdline++;
+	}
+	if ( CreateProcess(
+			 pCmd,
+			 pCmdline,
+			 NULL,
+			 NULL,
+			 FALSE,
+			 dwCreationFlags,
+			 NULL,
+			 execdir,
+			 &startupinfo,
+			 &ProcessInformation
+			 ) ) {
+		// NOTE: the docs suggest we should be closing the handles in PROCESS_INFORMATION here
+		return true;
+	}
+	return false;
 }
-
-
-
-// rad end
+#endif
 
 #define MEM_BLOCKSIZE 4096
-void* qblockmalloc(size_t nSize)
-{
+void* qblockmalloc( size_t nSize ){
 	void *b;
-  // round up to threshold
-  int nAllocSize = nSize % MEM_BLOCKSIZE;
-  if ( nAllocSize > 0)
-  {
-    nSize += MEM_BLOCKSIZE - nAllocSize;
-  }
-	b = malloc(nSize + 1);
-	memset (b, 0, nSize);
+	// round up to threshold
+	int nAllocSize = nSize % MEM_BLOCKSIZE;
+	if ( nAllocSize > 0 ) {
+		nSize += MEM_BLOCKSIZE - nAllocSize;
+	}
+	b = malloc( nSize + 1 );
+	memset( b, 0, nSize );
 	return b;
 }
 
-void* qmalloc (size_t nSize)
-{
+//++timo NOTE: can be replaced by g_malloc0(nSize+1) when moving to glib memory handling
+void* qmalloc( size_t nSize ){
 	void *b;
-	b = malloc(nSize + 1);
-	memset (b, 0, nSize);
+	b = malloc( nSize + 1 );
+	memset( b, 0, nSize );
 	return b;
 }
 
 /*
-================
-Q_filelength
-================
-*/
-int Q_filelength (FILE *f)
-{
-	int		pos;
-	int		end;
-
-	pos = ftell (f);
-	fseek (f, 0, SEEK_END);
-	end = ftell (f);
-	fseek (f, pos, SEEK_SET);
+   ================
+   Q_filelength
+   ================
+ */
+int Q_filelength( FILE *f ){
+	int pos;
+	int end;
+
+	pos = ftell( f );
+	fseek( f, 0, SEEK_END );
+	end = ftell( f );
+	fseek( f, pos, SEEK_SET );
 
 	return end;
 }
 
-
-// FIXME: need error handler
-FILE *SafeOpenWrite (const char *filename)
-{
-	FILE	*f;
-
-	f = fopen(filename, "wb");
-
-	if (!f)
-  {
-		Error ("Error opening %s: %s",filename,strerror(errno));
-  }
-
-	return f;
-}
-
-FILE *SafeOpenRead (const char *filename)
-{
-	FILE	*f;
-
-	f = fopen(filename, "rb");
-
-	if (!f)
-  {
-		Error ("Error opening %s: %s",filename,strerror(errno));
-  }
-
-	return f;
-}
-
-
-void SafeRead (FILE *f, void *buffer, int count)
-{
-	if ( (int)fread (buffer, 1, count, f) != count)
-		Error ("File read failure");
-}
-
-
-void SafeWrite (FILE *f, const void *buffer, int count)
-{
-	if ( (int)fwrite (buffer, 1, count, f) != count)
-		Error ("File read failure");
-}
-
-
-
-/*
-==============
-LoadFile
-==============
-*/
-int LoadFile (const char *filename, void **bufferptr)
-{
-	FILE	*f;
-	int    length;
-	void    *buffer;
-
-  *bufferptr = NULL;
-  
-  if (filename == NULL || strlen(filename) == 0)
-  {
-    return -1;
-  }
-
-	f = fopen (filename, "rb");
-	if (!f)
-	{
-		return -1;
-	}
-	length = Q_filelength (f);
-	buffer = qblockmalloc (length+1);
-	((char *)buffer)[length] = 0;
-	SafeRead (f, buffer, length);
-	fclose (f);
-
-	*bufferptr = buffer;
-	return length;
-}
-
-
-/*
-==============
-LoadFileNoCrash
-
-returns -1 length if not present
-==============
-*/
-int    LoadFileNoCrash (const char *filename, void **bufferptr)
-{
-	FILE	*f;
-	int    length;
-	void    *buffer;
-
-	f = fopen (filename, "rb");
-	if (!f)
-		return -1;
-	length = Q_filelength (f);
-	buffer = qmalloc (length+1);
-	((char *)buffer)[length] = 0;
-	SafeRead (f, buffer, length);
-	fclose (f);
-
-	*bufferptr = buffer;
-	return length;
-}
-
-
-/*
-==============
-SaveFile
-==============
-*/
-void    SaveFile (const char *filename, void *buffer, int count)
-{
-	FILE	*f;
-
-	f = SafeOpenWrite (filename);
-	SafeWrite (f, buffer, count);
-	fclose (f);
-}
-
-
-
-void DefaultExtension (char *path, char *extension)
-{
+void DefaultExtension( char *path, char *extension ){
 	char    *src;
 //
 // if path doesn't have a .EXT, append extension
 // (extension should include the .)
 //
-	src = path + strlen(path) - 1;
+	src = path + strlen( path ) - 1;
 
-	while (*src != PATHSEPERATOR && src != path)
+	while ( *src != PATHSEPERATOR && src != path )
 	{
-		if (*src == '.')
-			return;                 // it has an extension
+		if ( *src == '.' ) {
+			return;           // it has an extension
+		}
 		src--;
 	}
 
-	strcat (path, extension);
+	strcat( path, extension );
 }
 
+void DefaultPath( char *path, char *basepath ){
+	char temp[128];
 
-void DefaultPath (char *path, char *basepath)
-{
-	char    temp[128];
-
-	if (path[0] == PATHSEPERATOR)
-		return;                   // absolute path location
-	strcpy (temp,path);
-	strcpy (path,basepath);
-	strcat (path,temp);
+	if ( path[0] == PATHSEPERATOR ) {
+		return;               // absolute path location
+	}
+	strcpy( temp,path );
+	strcpy( path,basepath );
+	strcat( path,temp );
 }
 
 
-void    StripFilename (char *path)
-{
-	int             length;
+void    StripFilename( char *path ){
+	int length;
 
-	length = strlen(path)-1;
-	while (length > 0 && path[length] != PATHSEPERATOR)
+	length = strlen( path ) - 1;
+	while ( length > 0 && path[length] != PATHSEPERATOR )
 		length--;
 	path[length] = 0;
 }
 
-void    StripExtension (char *path)
-{
-	int             length;
+void    StripExtension( char *path ){
+	int length;
 
-	length = strlen(path)-1;
-	while (length > 0 && path[length] != '.')
+	length = strlen( path ) - 1;
+	while ( length > 0 && path[length] != '.' )
 	{
 		length--;
-		if (path[length] == '/')
-			return;		// no extension
+		if ( path[length] == '/' ) {
+			return; // no extension
+		}
 	}
-	if (length)
+	if ( length ) {
 		path[length] = 0;
+	}
 }
 
 
 /*
-====================
-Extract file parts
-====================
-*/
-void ExtractFilePath (const char *path, char *dest)
-{
+   ====================
+   Extract file parts
+   ====================
+ */
+void ExtractFilePath( const char *path, char *dest ){
 	const char *src;
 
-	src = path + strlen(path) - 1;
+	src = path + strlen( path ) - 1;
 
 //
 // back up until a \ or the start
 //
-	while (src != path && *(src-1) != PATHSEPERATOR)
+	while ( src != path && *( src - 1 ) != '/' && *( src - 1 ) != '\\' )
 		src--;
 
-	memcpy (dest, path, src-path);
-	dest[src-path] = 0;
+	memcpy( dest, path, src - path );
+	dest[src - path] = 0;
 }
 
-void ExtractFileName (const char *path, char *dest)
-{
+void ExtractFileName( const char *path, char *dest ){
 	const char *src;
 
-	src = path + strlen(path) - 1;
+	src = path + strlen( path ) - 1;
 
 //
 // back up until a \ or the start
 //
-	while (src != path && *(src-1) != '/' 
-		 && *(src-1) != '\\' )
+	while ( src != path && *( src - 1 ) != '/'
+			&& *( src - 1 ) != '\\' )
 		src--;
 
-	while (*src)
+	while ( *src )
 	{
 		*dest++ = *src++;
 	}
 	*dest = 0;
 }
 
-void ExtractFileBase (const char *path, char *dest)
-{
-	const char *src;
-
-	src = path + strlen(path) - 1;
-
-//
-// back up until a \ or the start
-//
-	while (src != path && *(src-1) != '/' 
-		 && *(src-1) != '\\' )
-		src--;
+inline const char* path_get_filename_start( const char* path ){
+	{
+		const char* last_forward_slash = strrchr( path, '/' );
+		if ( last_forward_slash != NULL ) {
+			return last_forward_slash + 1;
+		}
+	}
 
-	while (*src && *src != '.')
 	{
-		*dest++ = *src++;
+		const char* last_backward_slash = strrchr( path, '\\' );
+		if ( last_backward_slash != NULL ) {
+			return last_backward_slash + 1;
+		}
 	}
-	*dest = 0;
+
+	return path;
 }
 
-void ExtractFileExtension (const char *path, char *dest)
-{
+inline unsigned int filename_get_base_length( const char* filename ){
+	const char* last_period = strrchr( filename, '.' );
+	return ( last_period != NULL ) ? last_period - filename : strlen( filename );
+}
+
+void ExtractFileBase( const char *path, char *dest ){
+	const char* filename = path_get_filename_start( path );
+	unsigned int length = filename_get_base_length( filename );
+	strncpy( dest, filename, length );
+	dest[length] = '\0';
+}
+
+void ExtractFileExtension( const char *path, char *dest ){
 	const char *src;
 
-	src = path + strlen(path) - 1;
+	src = path + strlen( path ) - 1;
 
 //
 // back up until a . or the start
 //
-	while (src != path && *(src-1) != '.')
+	while ( src != path && *( src - 1 ) != '.' )
 		src--;
-	if (src == path)
-	{
-		*dest = 0;	// no extension
+	if ( src == path ) {
+		*dest = 0; // no extension
 		return;
 	}
 
-	strcpy (dest,src);
+	strcpy( dest,src );
 }
 
 
-void ConvertDOSToUnixName( char *dst, const char *src )
-{
+void ConvertDOSToUnixName( char *dst, const char *src ){
 	while ( *src )
 	{
-		if ( *src == '\\' )
+		if ( *src == '\\' ) {
 			*dst = '/';
-		else
+		}
+		else{
 			*dst = *src;
+		}
 		dst++; src++;
 	}
 	*dst = 0;
 }
 
 
-char* StrDup(char* pStr)
-{ 
-  if (pStr)
-  {
-    return strcpy(new char[strlen(pStr)+1], pStr); 
-  }
-  return NULL;
-}
-
-char* StrDup(const char* pStr)
-{ 
-  if (pStr)
-  {
-    return strcpy(new char[strlen(pStr)+1], pStr); 
-  }
-  return NULL;
+char* StrDup( char* pStr ){
+	if ( pStr ) {
+		return strcpy( new char[strlen( pStr ) + 1], pStr );
+	}
+	return NULL;
 }
 
+char* StrDup( const char* pStr ){
+	if ( pStr ) {
+		return strcpy( new char[strlen( pStr ) + 1], pStr );
+	}
+	return NULL;
+}
+
+void CreateDirectoryPath( const char *path ) {
+	char base[PATH_MAX];
+	char *src;
+	char back;
+
+	ExtractFilePath( path, base );
+
+	src = base + 1;
+	while ( 1 ) {
+		while ( *src != '\0' && *src != '/' && *src != '\\' ) {
+			src++;
+		}
+		if ( *src == '\0' ) {
+			break;
+		}
+		back = *src; *src = '\0';
+		Q_mkdir( base, 0755 );
+		*src = back; src++;
+	}
+}
 
 /*
-============================================================================
+   ============================================================================
 
-					BYTE ORDER FUNCTIONS
+          BYTE ORDER FUNCTIONS
 
-============================================================================
-*/
+   ============================================================================
+ */
 
 #ifdef _SGI_SOURCE
-#define	__BIG_ENDIAN__
+  #define   __BIG_ENDIAN__
 #endif
 
 #ifdef __BIG_ENDIAN__
 
-short   LittleShort (short l)
-{
-	byte    b1,b2;
+short   LittleShort( short l ){
+	byte b1,b2;
 
-	b1 = l&255;
-	b2 = (l>>8)&255;
+	b1 = l & 255;
+	b2 = ( l >> 8 ) & 255;
 
-	return (b1<<8) + b2;
+	return ( b1 << 8 ) + b2;
 }
 
-short   BigShort (short l)
-{
+short   BigShort( short l ){
 	return l;
 }
 
 
-int    LittleLong (int l)
-{
-	byte    b1,b2,b3,b4;
+int    LittleLong( int l ){
+	byte b1,b2,b3,b4;
 
-	b1 = l&255;
-	b2 = (l>>8)&255;
-	b3 = (l>>16)&255;
-	b4 = (l>>24)&255;
+	b1 = l & 255;
+	b2 = ( l >> 8 ) & 255;
+	b3 = ( l >> 16 ) & 255;
+	b4 = ( l >> 24 ) & 255;
 
-	return ((int)b1<<24) + ((int)b2<<16) + ((int)b3<<8) + b4;
+	return ( (int)b1 << 24 ) + ( (int)b2 << 16 ) + ( (int)b3 << 8 ) + b4;
 }
 
-int    BigLong (int l)
-{
+int    BigLong( int l ){
 	return l;
 }
 
 
-float	LittleFloat (float l)
-{
-	union {byte b[4]; float f;} in, out;
-	
+float LittleFloat( float l ){
+	union
+	{
+		byte b[4]; float f;
+	} in, out;
+
 	in.f = l;
 	out.b[0] = in.b[3];
 	out.b[1] = in.b[2];
 	out.b[2] = in.b[1];
 	out.b[3] = in.b[0];
-	
+
 	return out.f;
 }
 
-float	BigFloat (float l)
-{
+float BigFloat( float l ){
 	return l;
 }
 
-
 #else
 
+short   BigShort( short l ){
+	byte b1,b2;
 
-short   BigShort (short l)
-{
-	byte    b1,b2;
+	b1 = l & 255;
+	b2 = ( l >> 8 ) & 255;
 
-	b1 = l&255;
-	b2 = (l>>8)&255;
-
-	return (b1<<8) + b2;
+	return ( b1 << 8 ) + b2;
 }
 
-short   LittleShort (short l)
-{
+short   LittleShort( short l ){
 	return l;
 }
 
 
-int    BigLong (int l)
-{
-	byte    b1,b2,b3,b4;
+int    BigLong( int l ){
+	byte b1,b2,b3,b4;
 
-	b1 = l&255;
-	b2 = (l>>8)&255;
-	b3 = (l>>16)&255;
-	b4 = (l>>24)&255;
+	b1 = l & 255;
+	b2 = ( l >> 8 ) & 255;
+	b3 = ( l >> 16 ) & 255;
+	b4 = ( l >> 24 ) & 255;
 
-	return ((int)b1<<24) + ((int)b2<<16) + ((int)b3<<8) + b4;
+	return ( (int)b1 << 24 ) + ( (int)b2 << 16 ) + ( (int)b3 << 8 ) + b4;
 }
 
-int    LittleLong (int l)
-{
+int    LittleLong( int l ){
 	return l;
 }
 
-float	BigFloat (float l)
-{
-	union {byte b[4]; float f;} in, out;
-	
+float BigFloat( float l ){
+	union
+	{
+		byte b[4]; float f;
+	} in, out;
+
 	in.f = l;
 	out.b[0] = in.b[3];
 	out.b[1] = in.b[2];
 	out.b[2] = in.b[1];
 	out.b[3] = in.b[0];
-	
+
 	return out.f;
 }
 
-float	LittleFloat (float l)
-{
+float LittleFloat( float l ){
 	return l;
 }
 
-
-
 #endif
-

```
