# Diff: `code/sys/sys_main.c`
**Canonical:** `wolfcamql-src` (sha256 `66a21ff2e3d0...`, 20830 bytes)

## Variants

### `ioquake3`  — sha256 `c0a9a32ff923...`, 19012 bytes

_Diff stat: +85 / -155 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_main.c	2026-04-16 20:02:25.278298700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sys\sys_main.c	2026-04-16 20:02:21.622757900 +0100
@@ -51,10 +51,6 @@
 #include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
 
-qboolean ConsoleIsPassive = qfalse;
-
-int StartTime = 0;
-
 static char binaryPath[ MAX_OSPATH ] = { 0 };
 static char installPath[ MAX_OSPATH ] = { 0 };
 
@@ -271,8 +267,8 @@
 		Q_CleanStr( modName );
 
 		Com_sprintf( message, sizeof (message), "The last time %s ran, "
-					 "it didn't exit properly. This may be due to inappropriate video "
-					 "settings. Would you like to start with \"safe\" video settings?", modName );
+			"it didn't exit properly. This may be due to inappropriate video "
+			"settings. Would you like to start with \"safe\" video settings?", modName );
 
 		if( Sys_Dialog( DT_YES_NO, message, "Abnormal Exit" ) == DR_YES ) {
 			Cvar_Set( "com_abnormalExit", "1" );
@@ -363,13 +359,79 @@
 */
 void Sys_Init(void)
 {
-	Cmd_AddCommand("backtrace", Sys_Backtrace_f);
 	Cmd_AddCommand( "in_restart", Sys_In_Restart_f );
 	Cvar_Set( "arch", OS_STRING " " ARCH_STRING );
 	Cvar_Set( "username", Sys_GetCurrentUser( ) );
 }
 
+/*
+=================
+Sys_AnsiColorPrint
+
+Transform Q3 colour codes to ANSI escape sequences
+=================
+*/
+void Sys_AnsiColorPrint( const char *msg )
+{
+	static char buffer[ MAXPRINTMSG ];
+	int         length = 0;
+	static int  q3ToAnsi[ 8 ] =
+	{
+		7, // COLOR_BLACK
+		31, // COLOR_RED
+		32, // COLOR_GREEN
+		33, // COLOR_YELLOW
+		34, // COLOR_BLUE
+		36, // COLOR_CYAN
+		35, // COLOR_MAGENTA
+		0   // COLOR_WHITE
+	};
+
+	while( *msg )
+	{
+		if( Q_IsColorString( msg ) || *msg == '\n' )
+		{
+			// First empty the buffer
+			if( length > 0 )
+			{
+				buffer[ length ] = '\0';
+				fputs( buffer, stderr );
+				length = 0;
+			}
 
+			if( *msg == '\n' )
+			{
+				// Issue a reset and then the newline
+				fputs( "\033[0m\n", stderr );
+				msg++;
+			}
+			else
+			{
+				// Print the color code (reset first to clear potential inverse (black))
+				Com_sprintf( buffer, sizeof( buffer ), "\033[0m\033[%dm",
+						q3ToAnsi[ ColorIndex( *( msg + 1 ) ) ] );
+				fputs( buffer, stderr );
+				msg += 2;
+			}
+		}
+		else
+		{
+			if( length >= MAXPRINTMSG - 1 )
+				break;
+
+			buffer[ length ] = *msg;
+			length++;
+			msg++;
+		}
+	}
+
+	// Empty anything still left in the buffer
+	if( length > 0 )
+	{
+		buffer[ length ] = '\0';
+		fputs( buffer, stderr );
+	}
+}
 
 /*
 =================
@@ -437,78 +499,6 @@
 	return buf.st_mtime;
 }
 
-qboolean Sys_FileIsDirectory (const char *path)
-{
-	struct stat buf;
-
-	if (stat(path, &buf) != 0) {
-		Com_Printf("WARNING:  couldn't stat file '%s'\n", path);
-		return qfalse;
-	}
-
-	if (buf.st_mode & S_IFDIR) {
-		return qtrue;
-	}
-
-	return qfalse;
-}
-
-qboolean Sys_FileExists (const char *path)
-{
-	struct stat buf;
-
-	if (stat(path, &buf) != 0) {
-		return qfalse;
-	}
-
-	return qtrue;
-}
-
-qboolean Sys_CopyFile (const char *src, const char *dest)
-{
-	char buffer[8192];
-	FILE *in, *out;
-	size_t nbytes;
-	qboolean ret;
-
-	in = fopen(src, "rb");
-	if (!in) {
-		Com_Printf("^1%s:  couldn't open src '%s'\n", __FUNCTION__, src);
-		return qfalse;
-	}
-
-	out = fopen(dest, "wb");
-	if (!out) {
-		Com_Printf("^1%s:  couldn't open dest '%s'\n", __FUNCTION__, dest);
-		fclose(in);
-		return qfalse;
-	}
-
-	while ((nbytes = fread(buffer, 1, sizeof(buffer), in)) > 0)  {
-		int n;
-
-		n = fwrite(buffer, 1, nbytes, out);
-		if (n < nbytes) {
-			Com_Printf("^1%s:  couldn't write to dest %d\n", __FUNCTION__, n);
-			fclose(in);
-			fclose(out);
-			return qfalse;
-		}
-	}
-
-	ret = qtrue;
-
-	if (!feof(in)) {
-		Com_Printf("^1%s:  couldn't read from src %d\n", __FUNCTION__, ferror(in));
-		ret = qfalse;
-	}
-
-	fclose(in);
-	fclose(out);
-
-	return ret;
-}
-
 /*
 =================
 Sys_UnloadDll
@@ -549,7 +539,7 @@
 		Com_Printf("Trying to load \"%s\"...\n", name);
 		dllhandle = Sys_LoadLibrary(name);
 	}
-
+	
 	if(!dllhandle)
 	{
 		const char *topDir;
@@ -609,8 +599,8 @@
 =================
 */
 void *Sys_LoadGameDll(const char *name,
-					  vmMainProc *entryPoint,
-						  intptr_t (*systemcalls)(intptr_t, ...))
+	vmMainProc *entryPoint,
+	intptr_t (*systemcalls)(intptr_t, ...))
 {
 	void *libHandle;
 	void (*dllEntry)(intptr_t (*syscallptr)(intptr_t, ...));
@@ -765,7 +755,6 @@
 {
 	static qboolean signalcaught = qfalse;
 
-	//Com_Printf("signal: %d\n", signal);
 	if( signalcaught )
 	{
 		fprintf( stderr, "DOUBLE SIGNAL FAULT: Received signal %d, exiting...\n",
@@ -788,12 +777,6 @@
 		Sys_Exit( 2 );
 }
 
-#ifdef _WIN32
-#include <windows.h>
-
-extern CRITICAL_SECTION printCriticalSection;
-#endif
-
 /*
 =================
 main
@@ -804,12 +787,8 @@
 	int   i;
 	char  commandLine[ MAX_STRING_CHARS ] = { 0 };
 #ifdef PROTOCOL_HANDLER
-       char *protocolCommand = NULL;
+	char *protocolCommand = NULL;
 #endif
-	qboolean useBacktrace;
-	qboolean useConsoleOutput;
-	qboolean demoNameAsArg;
-	qboolean gotFirstArg;
 
 #ifdef USE_AUTOUPDATER
 	Sys_LaunchAutoupdater(argc, argv);
@@ -827,10 +806,6 @@
 	SDL_version ver;
 	SDL_GetVersion( &ver );
 
-#ifdef _WIN32
-	InitializeCriticalSection(&printCriticalSection);
-#endif
-
 #define MINSDL_VERSION \
 	XSTRING(MINSDL_MAJOR) "." \
 	XSTRING(MINSDL_MINOR) "." \
@@ -840,39 +815,19 @@
 			SDL_VERSIONNUM( MINSDL_MAJOR, MINSDL_MINOR, MINSDL_PATCH ) )
 	{
 		Sys_Dialog( DT_ERROR, va( "SDL version " MINSDL_VERSION " or greater is required, "
-								  "but only version %d.%d.%d was found. You may be able to obtain a more recent copy "
-								  "from https://www.libsdl.org/.", ver.major, ver.minor, ver.patch ), "SDL Library Too Old" );
+			"but only version %d.%d.%d was found. You may be able to obtain a more recent copy "
+			"from https://www.libsdl.org/.", ver.major, ver.minor, ver.patch ), "SDL Library Too Old" );
 
 		Sys_Exit( 1 );
 	}
-
-	// 2019-11-03 problems with Mac OS X console, disable unix tty by default for client
-	ConsoleIsPassive = qtrue;
-
 #endif
 
-	// Set the initial time base
-	StartTime = Sys_Milliseconds();
-
-	useBacktrace = qtrue;
-	useConsoleOutput = qfalse;
-	demoNameAsArg = qtrue;
-	for (i = 1;  i < argc;  i++) {
-		if (!strcmp(argv[i], "--nobacktrace")) {
-			useBacktrace = qfalse;
-		} else if (!strcmp(argv[i], "--console-output")) {
-			useConsoleOutput = qtrue;
-		} else if (!strcmp(argv[i], "--console-active")) {
-			ConsoleIsPassive = qfalse;
-		} else if (!strcmp(argv[i], "--console-passive")) {
-			ConsoleIsPassive = qtrue;
-		} else if (!strcmp(argv[i], "--no-demo-arg")) {
-			demoNameAsArg = qfalse;
-		}
-	}
-	Sys_PlatformInit(useBacktrace, useConsoleOutput);
+	Sys_PlatformInit( );
 	Sys_SetMaxFileLimit( );
 
+	// Set the initial time base
+	Sys_Milliseconds( );
+
 #ifdef __APPLE__
 	// This is passed if we are launched by double-clicking
 	if ( argc >= 2 && Q_strncmp ( argv[1], "-psn", 4 ) == 0 )
@@ -884,7 +839,6 @@
 	Sys_SetDefaultInstallPath( DEFAULT_BASEDIR );
 
 	// Concatenate the command line for passing to Com_Init
-	gotFirstArg = qfalse;
 	for( i = 1; i < argc; i++ )
 	{
 		qboolean containsSpaces;
@@ -902,29 +856,7 @@
 			break;
 		}
 
-		if (!strcmp(argv[i], "--nobacktrace")) {
-			continue;
-		} else if (!strcmp(argv[i], "--console-output")) {
-			continue;
-		} else if (!strcmp(argv[i], "--console-passive")) {
-			continue;
-		} else if (!strcmp(argv[i], "--no-demo-arg")) {
-			continue;
-		}
-
-		if (demoNameAsArg  &&  !gotFirstArg) {
-			if (argv[i][0] != '+'  &&  argv[i][0] != '-') {
-				Q_strcat(commandLine, sizeof(commandLine), "+demo \"");
-				Q_strcat(commandLine, sizeof(commandLine), argv[i]);
-				Q_strcat(commandLine, sizeof(commandLine), "\"");
-				printf("demo: '%s'\n", argv[i]);
-				continue;
-			}
-		}
-
-		gotFirstArg = qtrue;
 		containsSpaces = strchr(argv[i], ' ') != NULL;
-
 		if (containsSpaces)
 			Q_strcat( commandLine, sizeof( commandLine ), "\"" );
 
@@ -949,16 +881,14 @@
 	Com_Init( commandLine );
 	NET_Init( );
 
-	if (!useBacktrace) {
-		signal( SIGILL, Sys_SigHandler );
-		signal( SIGFPE, Sys_SigHandler );
-		signal( SIGSEGV, Sys_SigHandler );
-		signal( SIGTERM, Sys_SigHandler );
-		signal( SIGINT, Sys_SigHandler );
-	}
+	signal( SIGILL, Sys_SigHandler );
+	signal( SIGFPE, Sys_SigHandler );
+	signal( SIGSEGV, Sys_SigHandler );
+	signal( SIGTERM, Sys_SigHandler );
+	signal( SIGINT, Sys_SigHandler );
 
 #ifdef __EMSCRIPTEN__
-       emscripten_set_main_loop( Com_Frame, 0, 1 );
+	emscripten_set_main_loop( Com_Frame, 0, 1 );
 #else
 	while( 1 )
 	{

```

### `openarena-engine`  — sha256 `d05bffdeda06...`, 13753 bytes

_Diff stat: +141 / -432 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_main.c	2026-04-16 20:02:25.278298700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\sys_main.c	2026-04-16 22:48:25.939962600 +0100
@@ -31,12 +31,8 @@
 #include <ctype.h>
 #include <errno.h>
 
-#ifdef __EMSCRIPTEN__
-#include <emscripten/emscripten.h>
-#endif
-
 #ifndef DEDICATED
-#ifdef USE_INTERNAL_SDL_HEADERS
+#ifdef USE_LOCAL_HEADERS
 #	include "SDL.h"
 #	include "SDL_cpuinfo.h"
 #else
@@ -51,10 +47,6 @@
 #include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
 
-qboolean ConsoleIsPassive = qfalse;
-
-int StartTime = 0;
-
 static char binaryPath[ MAX_OSPATH ] = { 0 };
 static char installPath[ MAX_OSPATH ] = { 0 };
 
@@ -120,14 +112,6 @@
 */
 void Sys_In_Restart_f( void )
 {
-#ifndef DEDICATED
-	if( !SDL_WasInit( SDL_INIT_VIDEO ) )
-	{
-		Com_Printf( "in_restart: Cannot restart input while video is shutdown\n" );
-		return;
-	}
-#endif
-
 	IN_Restart( );
 }
 
@@ -143,35 +127,6 @@
 	return CON_Input( );
 }
 
-/*
-==================
-Sys_GetClipboardData
-==================
-*/
-char *Sys_GetClipboardData(void)
-{
-#ifdef DEDICATED
-	return NULL;
-#else
-	char *data = NULL;
-	char *cliptext;
-
-	if ( ( cliptext = SDL_GetClipboardText() ) != NULL ) {
-		if ( cliptext[0] != '\0' ) {
-			size_t bufsize = strlen( cliptext ) + 1;
-
-			data = Z_Malloc( bufsize );
-			Q_strncpyz( data, cliptext, bufsize );
-
-			// find first listed char and set to '\0'
-			strtok( data, "\n\r\b" );
-		}
-		SDL_free( cliptext );
-	}
-	return data;
-#endif
-}
-
 #ifdef DEDICATED
 #	define PID_FILENAME PRODUCT_NAME "_server.pid"
 #else
@@ -183,42 +138,35 @@
 Sys_PIDFileName
 =================
 */
-static char *Sys_PIDFileName( const char *gamedir )
+static char *Sys_PIDFileName( void )
 {
-	const char *homeStatePath = Cvar_VariableString( "fs_homestatepath" );
+	const char *homePath = Sys_DefaultHomePath( );
 
-	if( *homeStatePath != '\0' )
-		return va( "%s/%s/%s", homeStatePath, gamedir, PID_FILENAME );
+	if( *homePath != '\0' )
+		return va( "%s/%s", homePath, PID_FILENAME );
 
 	return NULL;
 }
 
 /*
 =================
-Sys_RemovePIDFile
-=================
-*/
-void Sys_RemovePIDFile( const char *gamedir )
-{
-	char *pidFile = Sys_PIDFileName( gamedir );
-
-	if( pidFile != NULL )
-		remove( pidFile );
-}
-
-/*
-=================
 Sys_WritePIDFile
 
 Return qtrue if there is an existing stale PID file
 =================
 */
-static qboolean Sys_WritePIDFile( const char *gamedir )
+qboolean Sys_WritePIDFile( void )
 {
-	char      *pidFile = Sys_PIDFileName( gamedir );
+	char      *pidFile = Sys_PIDFileName( );
 	FILE      *f;
 	qboolean  stale = qfalse;
 
+#ifdef WINFOUR
+	// leilei - workaround to avoid crashes on WinNT4/W9X
+	if ( pidFiles )
+		return qfalse;
+#endif
+
 	if( pidFile == NULL )
 		return qfalse;
 
@@ -241,10 +189,6 @@
 			stale = qtrue;
 	}
 
-	if( FS_CreatePath( pidFile ) ) {
-		return 0;
-	}
-
 	if( ( f = fopen( pidFile, "w" ) ) != NULL )
 	{
 		fprintf( f, "%d", Sys_PID( ) );
@@ -258,53 +202,12 @@
 
 /*
 =================
-Sys_InitPIDFile
-=================
-*/
-void Sys_InitPIDFile( const char *gamedir ) {
-	if( Sys_WritePIDFile( gamedir ) ) {
-#ifndef DEDICATED
-		char message[1024];
-		char modName[MAX_OSPATH];
-
-		FS_GetModDescription( gamedir, modName, sizeof ( modName ) );
-		Q_CleanStr( modName );
-
-		Com_sprintf( message, sizeof (message), "The last time %s ran, "
-					 "it didn't exit properly. This may be due to inappropriate video "
-					 "settings. Would you like to start with \"safe\" video settings?", modName );
-
-		if( Sys_Dialog( DT_YES_NO, message, "Abnormal Exit" ) == DR_YES ) {
-			Cvar_Set( "com_abnormalExit", "1" );
-		}
-#endif
-	}
-}
-
-/*
-=================
-Sys_OpenFolderInFileManager
-=================
-*/
-qboolean Sys_OpenFolderInFileManager( const char *path, qboolean create )
-{
-	if( create )
-	{
-		if( FS_CreatePath( path ) )
-			return qfalse;
-	}
-
-	return Sys_OpenFolderInPlatformFileManager( path );
-}
-
-/*
-=================
 Sys_Exit
 
 Single exit point (regular exit or in case of error)
 =================
 */
-static Q_NO_RETURN void Sys_Exit( int exitCode )
+static __attribute__ ((noreturn)) void Sys_Exit( int exitCode )
 {
 	CON_Shutdown( );
 
@@ -312,13 +215,14 @@
 	SDL_Quit( );
 #endif
 
-	if( exitCode < 2 && com_fullyInitialized )
+	if( exitCode < 2 )
 	{
 		// Normal exit
-		Sys_RemovePIDFile( FS_GetCurrentGameDir() );
-	}
+		char *pidFile = Sys_PIDFileName( );
 
-	NET_Shutdown( );
+		if( pidFile != NULL )
+			remove( pidFile );
+	}
 
 	Sys_PlatformExit( );
 
@@ -345,12 +249,18 @@
 	cpuFeatures_t features = 0;
 
 #ifndef DEDICATED
-	if( SDL_HasRDTSC( ) )      features |= CF_RDTSC;
-	if( SDL_Has3DNow( ) )      features |= CF_3DNOW;
-	if( SDL_HasMMX( ) )        features |= CF_MMX;
-	if( SDL_HasSSE( ) )        features |= CF_SSE;
-	if( SDL_HasSSE2( ) )       features |= CF_SSE2;
-	if( SDL_HasAltiVec( ) )    features |= CF_ALTIVEC;
+	if( SDL_HasRDTSC( ) )    features |= CF_RDTSC;
+	if( SDL_HasMMX( ) )      features |= CF_MMX;
+#if SDL_MAJOR_VERSION != 2
+	if( SDL_HasMMXExt( ) )   features |= CF_MMX_EXT;
+#endif
+	if( SDL_Has3DNow( ) )    features |= CF_3DNOW;
+#if SDL_MAJOR_VERSION != 2
+	if( SDL_Has3DNowExt( ) ) features |= CF_3DNOW_EXT;
+#endif
+	if( SDL_HasSSE( ) )      features |= CF_SSE;
+	if( SDL_HasSSE2( ) )     features |= CF_SSE2;
+	if( SDL_HasAltiVec( ) )  features |= CF_ALTIVEC;
 #endif
 
 	return features;
@@ -363,13 +273,83 @@
 */
 void Sys_Init(void)
 {
-	Cmd_AddCommand("backtrace", Sys_Backtrace_f);
 	Cmd_AddCommand( "in_restart", Sys_In_Restart_f );
 	Cvar_Set( "arch", OS_STRING " " ARCH_STRING );
 	Cvar_Set( "username", Sys_GetCurrentUser( ) );
 }
 
+/*
+=================
+Sys_AnsiColorPrint
+
+Transform Q3 colour codes to ANSI escape sequences
+=================
+*/
+void Sys_AnsiColorPrint( const char *msg )
+{
+	static char buffer[ MAXPRINTMSG ];
+	int         length = 0;
+	static int  q3ToAnsi[ 8 ] =
+	{
+		30, // COLOR_BLACK
+		31, // COLOR_RED
+		32, // COLOR_GREEN
+		33, // COLOR_YELLOW
+		34, // COLOR_BLUE
+		36, // COLOR_CYAN
+		35, // COLOR_MAGENTA
+		0   // COLOR_WHITE
+	};
+
+	while( *msg )
+	{
+		if( Q_IsColorString( msg ) || *msg == '\n' )
+		{
+			// First empty the buffer
+			if( length > 0 )
+			{
+				buffer[ length ] = '\0';
+				fputs( buffer, stderr );
+				length = 0;
+			}
 
+			if( *msg == '\n' )
+			{
+				// Issue a reset and then the newline
+				fputs( "\033[0m\n", stderr );
+				msg++;
+			}
+			else
+			{
+				// Print the color code
+				Com_sprintf( buffer, sizeof( buffer ), "\033[%dm",
+						q3ToAnsi[ ColorIndex( *( msg + 1 ) ) ] );
+				fputs( buffer, stderr );
+				msg += 2;
+			}
+		}
+		else
+		{
+			if( length >= MAXPRINTMSG - 1 )
+				break;
+
+			buffer[ length ] = *msg;
+			length++;
+			msg++;
+		}
+	}
+
+	// Empty anything still left in the buffer
+	if( length > 0 )
+	{
+		buffer[ length ] = '\0';
+		fputs( buffer, stderr );
+	}
+}
+
+#if defined( _WIN32 ) && defined( USE_CONSOLE_WINDOW )
+void Conbuf_AppendText( const char *pMsg );// leilei - console restoration
+#endif
 
 /*
 =================
@@ -378,6 +358,9 @@
 */
 void Sys_Print( const char *msg )
 {
+#if defined( _WIN32 ) && defined( USE_CONSOLE_WINDOW )
+	Conbuf_AppendText (msg);		// leilei - console restoration
+#endif
 	CON_LogWrite( msg );
 	CON_Print( msg );
 }
@@ -407,7 +390,7 @@
 Sys_Warn
 =================
 */
-static Q_PRINTF_FUNC(1, 2) void Sys_Warn( char *warning, ... )
+static __attribute__ ((format (printf, 1, 2))) void Sys_Warn( char *warning, ... )
 {
 	va_list argptr;
 	char    string[1024];
@@ -437,78 +420,6 @@
 	return buf.st_mtime;
 }
 
-qboolean Sys_FileIsDirectory (const char *path)
-{
-	struct stat buf;
-
-	if (stat(path, &buf) != 0) {
-		Com_Printf("WARNING:  couldn't stat file '%s'\n", path);
-		return qfalse;
-	}
-
-	if (buf.st_mode & S_IFDIR) {
-		return qtrue;
-	}
-
-	return qfalse;
-}
-
-qboolean Sys_FileExists (const char *path)
-{
-	struct stat buf;
-
-	if (stat(path, &buf) != 0) {
-		return qfalse;
-	}
-
-	return qtrue;
-}
-
-qboolean Sys_CopyFile (const char *src, const char *dest)
-{
-	char buffer[8192];
-	FILE *in, *out;
-	size_t nbytes;
-	qboolean ret;
-
-	in = fopen(src, "rb");
-	if (!in) {
-		Com_Printf("^1%s:  couldn't open src '%s'\n", __FUNCTION__, src);
-		return qfalse;
-	}
-
-	out = fopen(dest, "wb");
-	if (!out) {
-		Com_Printf("^1%s:  couldn't open dest '%s'\n", __FUNCTION__, dest);
-		fclose(in);
-		return qfalse;
-	}
-
-	while ((nbytes = fread(buffer, 1, sizeof(buffer), in)) > 0)  {
-		int n;
-
-		n = fwrite(buffer, 1, nbytes, out);
-		if (n < nbytes) {
-			Com_Printf("^1%s:  couldn't write to dest %d\n", __FUNCTION__, n);
-			fclose(in);
-			fclose(out);
-			return qfalse;
-		}
-	}
-
-	ret = qtrue;
-
-	if (!feof(in)) {
-		Com_Printf("^1%s:  couldn't read from src %d\n", __FUNCTION__, ferror(in));
-		ret = qfalse;
-	}
-
-	fclose(in);
-	fclose(out);
-
-	return ret;
-}
-
 /*
 =================
 Sys_UnloadDll
@@ -536,43 +447,25 @@
 
 void *Sys_LoadDll(const char *name, qboolean useSystemLib)
 {
-	void *dllhandle = NULL;
-
-	if(!Sys_DllExtension(name))
-	{
-		Com_Printf("Refusing to attempt to load library \"%s\": Extension not allowed.\n", name);
-		return NULL;
-	}
-
+	void *dllhandle;
+	
 	if(useSystemLib)
-	{
 		Com_Printf("Trying to load \"%s\"...\n", name);
-		dllhandle = Sys_LoadLibrary(name);
-	}
-
-	if(!dllhandle)
+	
+	if(!useSystemLib || !(dllhandle = Sys_LoadLibrary(name)))
 	{
 		const char *topDir;
 		char libPath[MAX_OSPATH];
-		int len;
 
 		topDir = Sys_BinaryPath();
 
 		if(!*topDir)
 			topDir = ".";
 
-		len = Com_sprintf(libPath, sizeof(libPath), "%s%c%s", topDir, PATH_SEP, name);
-		if(len < sizeof(libPath))
-		{
-			Com_Printf("Trying to load \"%s\" from \"%s\"...\n", name, topDir);
-			dllhandle = Sys_LoadLibrary(libPath);
-		}
-		else
-		{
-			Com_Printf("Skipping trying to load \"%s\" from \"%s\", file name is too long.\n", name, topDir);
-		}
+		Com_Printf("Trying to load \"%s\" from \"%s\"...\n", name, topDir);
+		Com_sprintf(libPath, sizeof(libPath), "%s%c%s", topDir, PATH_SEP, name);
 
-		if(!dllhandle)
+		if(!(dllhandle = Sys_LoadLibrary(libPath)))
 		{
 			const char *basePath = Cvar_VariableString("fs_basepath");
 			
@@ -581,16 +474,9 @@
 			
 			if(FS_FilenameCompare(topDir, basePath))
 			{
-				len = Com_sprintf(libPath, sizeof(libPath), "%s%c%s", basePath, PATH_SEP, name);
-				if(len < sizeof(libPath))
-				{
-					Com_Printf("Trying to load \"%s\" from \"%s\"...\n", name, basePath);
-					dllhandle = Sys_LoadLibrary(libPath);
-				}
-				else
-				{
-					Com_Printf("Skipping trying to load \"%s\" from \"%s\", file name is too long.\n", name, basePath);
-				}
+				Com_Printf("Trying to load \"%s\" from \"%s\"...\n", name, basePath);
+				Com_sprintf(libPath, sizeof(libPath), "%s%c%s", basePath, PATH_SEP, name);
+				dllhandle = Sys_LoadLibrary(libPath);
 			}
 			
 			if(!dllhandle)
@@ -609,20 +495,14 @@
 =================
 */
 void *Sys_LoadGameDll(const char *name,
-					  vmMainProc *entryPoint,
-						  intptr_t (*systemcalls)(intptr_t, ...))
+	intptr_t (QDECL **entryPoint)(int, ...),
+	intptr_t (*systemcalls)(intptr_t, ...))
 {
 	void *libHandle;
 	void (*dllEntry)(intptr_t (*syscallptr)(intptr_t, ...));
 
 	assert(name);
 
-	if(!Sys_DllExtension(name))
-	{
-		Com_Printf("Refusing to attempt to load library \"%s\": Extension not allowed.\n", name);
-		return NULL;
-	}
-
 	Com_Printf( "Loading DLL file: %s\n", name);
 	libHandle = Sys_LoadLibrary(name);
 
@@ -661,7 +541,7 @@
 		if( !strcmp( argv[1], "--version" ) ||
 				!strcmp( argv[1], "-v" ) )
 		{
-			const char* date = PRODUCT_DATE;
+			const char* date = __DATE__;
 #ifdef DEDICATED
 			fprintf( stdout, Q3_VERSION " dedicated server (%s)\n", date );
 #else
@@ -672,84 +552,8 @@
 	}
 }
 
-#ifdef PROTOCOL_HANDLER
-/*
-=================
-Sys_ParseProtocolUri
-
-This parses a protocol URI, e.g. "quake3://connect/example.com:27950"
-to a string that can be run in the console, or a null pointer if the
-operation is invalid or unsupported.
-At the moment only the "connect" command is supported.
-=================
-*/
-char *Sys_ParseProtocolUri( const char *uri )
-{
-	// Both "quake3://" and "quake3:" can be used
-	if ( Q_strncmp( uri, PROTOCOL_HANDLER ":", strlen( PROTOCOL_HANDLER ":" ) ) )
-	{
-		Com_Printf( "Sys_ParseProtocolUri: unsupported protocol.\n" );
-		return NULL;
-	}
-	uri += strlen( PROTOCOL_HANDLER ":" );
-	if ( !Q_strncmp( uri, "//", strlen( "//" ) ) )
-	{
-		uri += strlen( "//" );
-	}
-	Com_Printf( "Sys_ParseProtocolUri: %s\n", uri );
-
-	// At the moment, only "connect/hostname:port" is supported
-	if ( !Q_strncmp( uri, "connect/", strlen( "connect/" ) ) )
-	{
-		int i, bufsize;
-		char *out;
-
-		uri += strlen( "connect/" );
-		if ( *uri == '\0' || *uri == '?' )
-		{
-			Com_Printf( "Sys_ParseProtocolUri: missing argument.\n" );
-			return NULL;
-		}
-
-		// Check for any unsupported characters
-		// For safety reasons, the "hostname:port" part can only
-		// contain characters from: a-zA-Z0-9.:-[]
-		for ( i=0; uri[i] != '\0'; i++ )
-		{
-			if ( uri[i] == '?' )
-			{
-				// For forwards compatibility, any query string parameters are ignored (e.g. "?password=abcd")
-				// However, these are not passed on macOS, so it may be a bad idea to add them.
-				break;
-			}
-
-			if ( isalpha( uri[i] ) == 0 && isdigit( uri[i] ) == 0
-				&& uri[i] != '.' && uri[i] != ':' && uri[i] != '-'
-				&& uri[i] != '[' && uri[i] != ']' )
-			{
-				Com_Printf( "Sys_ParseProtocolUri: hostname contains unsupported character.\n" );
-				return NULL;
-			}
-		}
-
-		bufsize = strlen( "connect " ) + i + 1;
-		out = malloc( bufsize );
-		strcpy( out, "connect " );
-		strncat( out, uri, i );
-		return out;
-	}
-	else
-	{
-		Com_Printf( "Sys_ParseProtocolUri: unsupported command.\n" );
-		return NULL;
-	}
-}
-#endif
-
 #ifndef DEFAULT_BASEDIR
-#	if defined(DEFAULT_RELATIVE_BASEDIR)
-#		define DEFAULT_BASEDIR Sys_BinaryPathRelative(DEFAULT_RELATIVE_BASEDIR)
-#	elif defined(__APPLE__)
+#	ifdef MACOS_X
 #		define DEFAULT_BASEDIR Sys_StripAppBundle(Sys_BinaryPath())
 #	else
 #		define DEFAULT_BASEDIR Sys_BinaryPath()
@@ -765,7 +569,6 @@
 {
 	static qboolean signalcaught = qfalse;
 
-	//Com_Printf("signal: %d\n", signal);
 	if( signalcaught )
 	{
 		fprintf( stderr, "DOUBLE SIGNAL FAULT: Received signal %d, exiting...\n",
@@ -788,12 +591,6 @@
 		Sys_Exit( 2 );
 }
 
-#ifdef _WIN32
-#include <windows.h>
-
-extern CRITICAL_SECTION printCriticalSection;
-#endif
-
 /*
 =================
 main
@@ -803,17 +600,6 @@
 {
 	int   i;
 	char  commandLine[ MAX_STRING_CHARS ] = { 0 };
-#ifdef PROTOCOL_HANDLER
-       char *protocolCommand = NULL;
-#endif
-	qboolean useBacktrace;
-	qboolean useConsoleOutput;
-	qboolean demoNameAsArg;
-	qboolean gotFirstArg;
-
-#ifdef USE_AUTOUPDATER
-	Sys_LaunchAutoupdater(argc, argv);
-#endif
 
 #ifndef DEDICATED
 	// SDL version check
@@ -824,11 +610,11 @@
 #	endif
 
 	// Run time
-	SDL_version ver;
-	SDL_GetVersion( &ver );
-
-#ifdef _WIN32
-	InitializeCriticalSection(&printCriticalSection);
+#if SDL_MAJOR_VERSION == 2
+	SDL_version ver[1];
+	SDL_GetVersion( ver );
+#else
+	const SDL_version *ver = SDL_Linked_Version( );
 #endif
 
 #define MINSDL_VERSION \
@@ -836,95 +622,30 @@
 	XSTRING(MINSDL_MINOR) "." \
 	XSTRING(MINSDL_PATCH)
 
-	if( SDL_VERSIONNUM( ver.major, ver.minor, ver.patch ) <
+	if( SDL_VERSIONNUM( ver->major, ver->minor, ver->patch ) <
 			SDL_VERSIONNUM( MINSDL_MAJOR, MINSDL_MINOR, MINSDL_PATCH ) )
 	{
 		Sys_Dialog( DT_ERROR, va( "SDL version " MINSDL_VERSION " or greater is required, "
-								  "but only version %d.%d.%d was found. You may be able to obtain a more recent copy "
-								  "from https://www.libsdl.org/.", ver.major, ver.minor, ver.patch ), "SDL Library Too Old" );
+			"but only version %d.%d.%d was found. You may be able to obtain a more recent copy "
+			"from http://www.libsdl.org/.", ver->major, ver->minor, ver->patch ), "SDL Library Too Old" );
 
 		Sys_Exit( 1 );
 	}
-
-	// 2019-11-03 problems with Mac OS X console, disable unix tty by default for client
-	ConsoleIsPassive = qtrue;
-
 #endif
 
-	// Set the initial time base
-	StartTime = Sys_Milliseconds();
+	Sys_PlatformInit( );
 
-	useBacktrace = qtrue;
-	useConsoleOutput = qfalse;
-	demoNameAsArg = qtrue;
-	for (i = 1;  i < argc;  i++) {
-		if (!strcmp(argv[i], "--nobacktrace")) {
-			useBacktrace = qfalse;
-		} else if (!strcmp(argv[i], "--console-output")) {
-			useConsoleOutput = qtrue;
-		} else if (!strcmp(argv[i], "--console-active")) {
-			ConsoleIsPassive = qfalse;
-		} else if (!strcmp(argv[i], "--console-passive")) {
-			ConsoleIsPassive = qtrue;
-		} else if (!strcmp(argv[i], "--no-demo-arg")) {
-			demoNameAsArg = qfalse;
-		}
-	}
-	Sys_PlatformInit(useBacktrace, useConsoleOutput);
-	Sys_SetMaxFileLimit( );
-
-#ifdef __APPLE__
-	// This is passed if we are launched by double-clicking
-	if ( argc >= 2 && Q_strncmp ( argv[1], "-psn", 4 ) == 0 )
-		argc = 1;
-#endif
+	// Set the initial time base
+	Sys_Milliseconds( );
 
 	Sys_ParseArgs( argc, argv );
 	Sys_SetBinaryPath( Sys_Dirname( argv[ 0 ] ) );
 	Sys_SetDefaultInstallPath( DEFAULT_BASEDIR );
 
 	// Concatenate the command line for passing to Com_Init
-	gotFirstArg = qfalse;
 	for( i = 1; i < argc; i++ )
 	{
-		qboolean containsSpaces;
-
-		// For security reasons we always detect --uri, even when PROTOCOL_HANDLER is undefined
-		// Any arguments after "--uri quake3://..." is ignored
-		if ( !strcmp( argv[i], "--uri" ) )
-		{
-#ifdef PROTOCOL_HANDLER
-			if ( argc > i+1 )
-			{
-				protocolCommand = Sys_ParseProtocolUri( argv[i+1] );
-			}
-#endif
-			break;
-		}
-
-		if (!strcmp(argv[i], "--nobacktrace")) {
-			continue;
-		} else if (!strcmp(argv[i], "--console-output")) {
-			continue;
-		} else if (!strcmp(argv[i], "--console-passive")) {
-			continue;
-		} else if (!strcmp(argv[i], "--no-demo-arg")) {
-			continue;
-		}
-
-		if (demoNameAsArg  &&  !gotFirstArg) {
-			if (argv[i][0] != '+'  &&  argv[i][0] != '-') {
-				Q_strcat(commandLine, sizeof(commandLine), "+demo \"");
-				Q_strcat(commandLine, sizeof(commandLine), argv[i]);
-				Q_strcat(commandLine, sizeof(commandLine), "\"");
-				printf("demo: '%s'\n", argv[i]);
-				continue;
-			}
-		}
-
-		gotFirstArg = qtrue;
-		containsSpaces = strchr(argv[i], ' ') != NULL;
-
+		const qboolean containsSpaces = strchr(argv[i], ' ') != NULL;
 		if (containsSpaces)
 			Q_strcat( commandLine, sizeof( commandLine ), "\"" );
 
@@ -936,35 +657,23 @@
 		Q_strcat( commandLine, sizeof( commandLine ), " " );
 	}
 
-#ifdef PROTOCOL_HANDLER
-	if ( protocolCommand != NULL )
-	{
-		Q_strcat( commandLine, sizeof( commandLine ), "+" );
-		Q_strcat( commandLine, sizeof( commandLine ), protocolCommand );
-		free( protocolCommand );
-	}
-#endif
-
-	CON_Init( );
 	Com_Init( commandLine );
 	NET_Init( );
 
-	if (!useBacktrace) {
-		signal( SIGILL, Sys_SigHandler );
-		signal( SIGFPE, Sys_SigHandler );
-		signal( SIGSEGV, Sys_SigHandler );
-		signal( SIGTERM, Sys_SigHandler );
-		signal( SIGINT, Sys_SigHandler );
-	}
+	CON_Init( );
+
+	signal( SIGILL, Sys_SigHandler );
+	signal( SIGFPE, Sys_SigHandler );
+	signal( SIGSEGV, Sys_SigHandler );
+	signal( SIGTERM, Sys_SigHandler );
+	signal( SIGINT, Sys_SigHandler );
 
-#ifdef __EMSCRIPTEN__
-       emscripten_set_main_loop( Com_Frame, 0, 1 );
-#else
 	while( 1 )
 	{
+		IN_Frame( qfalse );	// youurayy input lag fix
 		Com_Frame( );
 	}
-#endif
 
 	return 0;
 }
+

```
