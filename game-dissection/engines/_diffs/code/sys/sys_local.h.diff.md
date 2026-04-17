# Diff: `code/sys/sys_local.h`
**Canonical:** `wolfcamql-src` (sha256 `e2795646137b...`, 3515 bytes)

## Variants

### `ioquake3`  — sha256 `6bdfb4842ac7...`, 2421 bytes

_Diff stat: +3 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_local.h	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sys\sys_local.h	2026-04-16 20:02:21.622757900 +0100
@@ -20,17 +20,14 @@
 ===========================================================================
 */
 
-#ifndef sys_local_h_included
-#define sys_local_h_included
-
 #include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
 
 #ifndef DEDICATED
 #ifdef USE_INTERNAL_SDL_HEADERS
-#      include "SDL_version.h"
+#	include "SDL_version.h"
 #else
-#      include <SDL_version.h>
+#	include <SDL_version.h>
 #endif
 
 // Require a minimum version of SDL
@@ -62,7 +59,7 @@
 
 void Sys_GLimpSafeInit( void );
 void Sys_GLimpInit( void );
-void Sys_PlatformInit (qboolean useBacktrace, qboolean useConsoleOutput);
+void Sys_PlatformInit( void );
 void Sys_PlatformExit( void );
 void Sys_SigHandler( int signal ) Q_NO_RETURN;
 void Sys_ErrorDialog( const char *error );
@@ -82,34 +79,3 @@
 #ifdef USE_AUTOUPDATER
 void Sys_LaunchAutoupdater(int argc, char **argv);
 #endif
-
-void Sys_Backtrace_f (void);
-qboolean Sys_FileIsDirectory (const char *path);
-qboolean Sys_FileExists (const char *path);
-qboolean Sys_CopyFile (const char *src, const char *dest);
-
-/* Strange naming like PopenClose() used to make it different from other 'pipe'
-   uses.  See ioquake3 com_pipefile which is mkfifo based and doesn't work in
-   Windows.  This uses popen() in Unix and CreatePipe() in Windows.  Just added
-   q3mme ffmpeg avi pipe and that uses popen() for both Unix and Windows.
-*/
-
-typedef struct {
-    void *data;
-} popenData_t;
-
-// need to free() returned data
-popenData_t *Sys_PopenAsync (const char *command);
-void Sys_PopenClose (popenData_t *p);
-
-// like fgets()
-char *Sys_PopenGetLine (popenData_t *p, char *buffer, int size);
-
-// check after call to Sys_PopenGetLine()
-qboolean Sys_PopenIsDone (popenData_t *p);
-
-const char *Sys_GetSteamCmd (void);
-
-void Sys_DisableScreenBlanking (void);
-
-#endif  //  sys_local_h_included

```

### `openarena-engine`  — sha256 `1c209828d4ef...`, 2105 bytes

_Diff stat: +14 / -65 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_local.h	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\sys_local.h	2026-04-16 22:48:25.939962600 +0100
@@ -20,28 +20,23 @@
 ===========================================================================
 */
 
-#ifndef sys_local_h_included
-#define sys_local_h_included
-
 #include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
 
-#ifndef DEDICATED
-#ifdef USE_INTERNAL_SDL_HEADERS
-#      include "SDL_version.h"
-#else
-#      include <SDL_version.h>
-#endif
-
 // Require a minimum version of SDL
-#define MINSDL_MAJOR 2
-#define MINSDL_MINOR 0
-#if SDL_VERSION_ATLEAST( 2, 0, 5 )
-#define MINSDL_PATCH 5
+#define MINSDL_MAJOR 1
+#define MINSDL_MINOR 2
+#define MINSDL_PATCH 10
+
+// Input subsystem
+#if SDL_MAJOR_VERSION == 2
+void IN_Init( void *windowData );
 #else
-#define MINSDL_PATCH 0
-#endif
+void IN_Init( void );
 #endif
+void IN_Frame( qboolean in_com_frame );	// youurayy input lag fix
+void IN_Shutdown( void );
+void IN_Restart( void );
 
 // Console
 void CON_Shutdown( void );
@@ -53,63 +48,17 @@
 unsigned int CON_LogWrite( const char *in );
 unsigned int CON_LogRead( char *out, unsigned int outSize );
 
-char *Sys_BinaryPath( void );
-char *Sys_BinaryPathRelative( const char *relative );
-
-#ifdef __APPLE__
+#ifdef MACOS_X
 char *Sys_StripAppBundle( char *pwd );
 #endif
 
 void Sys_GLimpSafeInit( void );
 void Sys_GLimpInit( void );
-void Sys_PlatformInit (qboolean useBacktrace, qboolean useConsoleOutput);
+void Sys_PlatformInit( void );
 void Sys_PlatformExit( void );
-void Sys_SigHandler( int signal ) Q_NO_RETURN;
+void Sys_SigHandler( int signal ) __attribute__ ((noreturn));
 void Sys_ErrorDialog( const char *error );
 void Sys_AnsiColorPrint( const char *msg );
 
 int Sys_PID( void );
 qboolean Sys_PIDIsRunning( int pid );
-
-qboolean Sys_OpenFolderInPlatformFileManager( const char *path );
-
-qboolean Sys_SetMaxFileLimit( void );
-
-#ifdef PROTOCOL_HANDLER
-char *Sys_ParseProtocolUri( const char *uri );
-#endif
-
-#ifdef USE_AUTOUPDATER
-void Sys_LaunchAutoupdater(int argc, char **argv);
-#endif
-
-void Sys_Backtrace_f (void);
-qboolean Sys_FileIsDirectory (const char *path);
-qboolean Sys_FileExists (const char *path);
-qboolean Sys_CopyFile (const char *src, const char *dest);
-
-/* Strange naming like PopenClose() used to make it different from other 'pipe'
-   uses.  See ioquake3 com_pipefile which is mkfifo based and doesn't work in
-   Windows.  This uses popen() in Unix and CreatePipe() in Windows.  Just added
-   q3mme ffmpeg avi pipe and that uses popen() for both Unix and Windows.
-*/
-
-typedef struct {
-    void *data;
-} popenData_t;
-
-// need to free() returned data
-popenData_t *Sys_PopenAsync (const char *command);
-void Sys_PopenClose (popenData_t *p);
-
-// like fgets()
-char *Sys_PopenGetLine (popenData_t *p, char *buffer, int size);
-
-// check after call to Sys_PopenGetLine()
-qboolean Sys_PopenIsDone (popenData_t *p);
-
-const char *Sys_GetSteamCmd (void);
-
-void Sys_DisableScreenBlanking (void);
-
-#endif  //  sys_local_h_included

```
