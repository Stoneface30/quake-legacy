# Diff: `q3asm/cmdlib.h`
**Canonical:** `quake3-source` (sha256 `076846b4c770...`, 4503 bytes)

## Variants

### `q3vm`  — sha256 `2382e6566072...`, 4291 bytes

_Diff stat: +67 / -80 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\q3asm\cmdlib.h	2026-04-16 20:02:20.124514000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\q3asm\cmdlib.h	2026-04-16 22:48:28.103253600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -24,13 +24,14 @@
 #ifndef __CMDLIB__
 #define __CMDLIB__
 
-#ifdef _WIN32
-#pragma warning(disable : 4244)     // MIPS
-#pragma warning(disable : 4136)     // X86
-#pragma warning(disable : 4051)     // ALPHA
+#ifdef _MSC_VER
+#define _CRT_SECURE_NO_WARNINGS
+#pragma warning(disable : 4244) // MIPS
+#pragma warning(disable : 4136) // X86
+#pragma warning(disable : 4051) // ALPHA
 
-#pragma warning(disable : 4018)     // signed/unsigned mismatch
-#pragma warning(disable : 4305)     // truncate from double to float
+#pragma warning(disable : 4018) // signed/unsigned mismatch
+#pragma warning(disable : 4305) // truncate from double to float
 
 #pragma check_stack(off)
 
@@ -44,9 +45,9 @@
 #include <time.h>
 #include <stdarg.h>
 
-#ifdef _WIN32
+#ifdef _MSC_VER
 
-#pragma intrinsic( memset, memcpy )
+#pragma intrinsic(memset, memcpy)
 
 #endif
 
@@ -56,105 +57,91 @@
 typedef unsigned char byte;
 #endif
 
-#define	MAX_OS_PATH		1024
+#define MAX_OS_PATH 1024
 #define MEM_BLOCKSIZE 4096
 
-// the dec offsetof macro doesnt work very well...
-#define myoffsetof(type,identifier) ((size_t)&((type *)0)->identifier)
-
+// the dec offsetof macro doesn't work very well...
+#define myoffsetof(type, identifier) ((size_t) & ((type*)0)->identifier)
 
 // set these before calling CheckParm
-extern int myargc;
-extern char **myargv;
-
-char *strupr (char *in);
-char *strlower (char *in);
-int Q_strncasecmp( const char *s1, const char *s2, int n );
-int Q_stricmp( const char *s1, const char *s2 );
-void Q_getwd( char *out );
-
-int Q_filelength (FILE *f);
-int	FileTime( const char *path );
-
-void	Q_mkdir( const char *path );
+extern int    myargc;
+extern char** myargv;
 
-extern	char		qdir[1024];
-extern	char		gamedir[1024];
-extern  char		writedir[1024];
-void SetQdirFromPath( const char *path );
-char *ExpandArg( const char *path );	// from cmd line
-char *ExpandPath( const char *path );	// from scripts
-char *ExpandGamePath (const char *path);
-char *ExpandPathAndArchive( const char *path );
+char* strupr(char* in);
+char* strlower(char* in);
+int Q_strncasecmp(const char* s1, const char* s2, int n);
+int Q_stricmp(const char* s1, const char* s2);
+void Q_getwd(char* out);
 
+int Q_filelength(FILE* f);
+int FileTime(const char* path);
 
-double I_FloatTime( void );
+void Q_mkdir(const char* path);
 
-void	Error( const char *error, ... );
-int		CheckParm( const char *check );
+extern char qdir[1024];
+extern char gamedir[1024];
+extern char writedir[1024];
+void SetQdirFromPath(const char* path);
+char* ExpandArg(const char* path);  // from cmd line
+char* ExpandPath(const char* path); // from scripts
+char* ExpandGamePath(const char* path);
+char* ExpandPathAndArchive(const char* path);
 
-FILE	*SafeOpenWrite( const char *filename );
-FILE	*SafeOpenRead( const char *filename );
-void	SafeRead (FILE *f, void *buffer, int count);
-void	SafeWrite (FILE *f, const void *buffer, int count);
+double I_FloatTime(void);
 
-int		LoadFile( const char *filename, void **bufferptr );
-int   LoadFileBlock( const char *filename, void **bufferptr );
-int		TryLoadFile( const char *filename, void **bufferptr );
-void	SaveFile( const char *filename, const void *buffer, int count );
-qboolean	FileExists( const char *filename );
+void Error(const char* error, ...);
+int CheckParm(const char* check);
 
-void 	DefaultExtension( char *path, const char *extension );
-void 	DefaultPath( char *path, const char *basepath );
-void 	StripFilename( char *path );
-void 	StripExtension( char *path );
+FILE* SafeOpenWrite(const char* filename);
+FILE* SafeOpenRead(const char* filename);
+void SafeRead(FILE* f, void* buffer, int count);
+void SafeWrite(FILE* f, const void* buffer, int count);
 
-void 	ExtractFilePath( const char *path, char *dest );
-void 	ExtractFileBase( const char *path, char *dest );
-void	ExtractFileExtension( const char *path, char *dest );
+int LoadFile(const char* filename, void** bufferptr);
+int LoadFileBlock(const char* filename, void** bufferptr);
+int TryLoadFile(const char* filename, void** bufferptr);
+void SaveFile(const char* filename, const void* buffer, int count);
+qboolean FileExists(const char* filename);
 
-int 	ParseNum (const char *str);
+void DefaultExtension(char* path, const char* extension);
+void DefaultPath(char* path, const char* basepath);
+void StripFilename(char* path);
+void StripExtension(char* path);
 
-short	BigShort (short l);
-short	LittleShort (short l);
-int		BigLong (int l);
-int		LittleLong (int l);
-float	BigFloat (float l);
-float	LittleFloat (float l);
+void ExtractFilePath(const char* path, char* dest);
+void ExtractFileBase(const char* path, char* dest);
+void ExtractFileExtension(const char* path, char* dest);
 
+int ParseNum(const char* str);
 
-char *COM_Parse (char *data);
+char* COM_Parse(char* data);
 
-extern	char		com_token[1024];
-extern	qboolean	com_eof;
+extern char     com_token[1024];
+extern qboolean com_eof;
 
-char *copystring(const char *s);
+char* copystring(const char* s);
 
-
-void CRC_Init(unsigned short *crcvalue);
-void CRC_ProcessByte(unsigned short *crcvalue, byte data);
+void CRC_Init(unsigned short* crcvalue);
+void CRC_ProcessByte(unsigned short* crcvalue, byte data);
 unsigned short CRC_Value(unsigned short crcvalue);
 
-void	CreatePath( const char *path );
-void	QCopyFile( const char *from, const char *to );
-
-extern	qboolean		archive;
-extern	char			archivedir[1024];
+void CreatePath(const char* path);
+void QCopyFile(const char* from, const char* to);
 
+extern qboolean archive;
+extern char     archivedir[1024];
 
-extern	qboolean verbose;
-void qprintf( const char *format, ... );
-void _printf( const char *format, ... );
-
-void ExpandWildcards( int *argc, char ***argv );
+extern qboolean verbose;
+void qprintf(const char* format, ...);
+void _printf(const char* format, ...);
 
+void ExpandWildcards(int* argc, char*** argv);
 
 // for compression routines
 typedef struct
 {
-	void	*data;
-	int		count, width, height;
+    void* data;
+    int   count, width, height;
 } cblock_t;
 
-
 #endif

```
