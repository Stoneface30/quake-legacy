# Diff: `code/sdl/sdl_gamma.c`
**Canonical:** `wolfcamql-src` (sha256 `f15a997ce08c...`, 2619 bytes)

## Variants

### `ioquake3`  — sha256 `85d75171898e...`, 2444 bytes

_Diff stat: +6 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_gamma.c	2026-04-16 20:02:25.265773300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sdl\sdl_gamma.c	2026-04-16 20:02:21.617760000 +0100
@@ -26,7 +26,7 @@
 #	include <SDL.h>
 #endif
 
-#include "../renderergl1/tr_local.h"
+#include "../renderercommon/tr_common.h"
 #include "../qcommon/qcommon.h"
 
 extern SDL_Window *SDL_window;
@@ -41,11 +41,8 @@
 	Uint16 table[3][256];
 	int i, j;
 
-	if (!r_enablePostProcess->integer  ||  !r_enableColorCorrect->integer  ||  !glConfig.qlGlsl) {
-		if( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer > 0 ) {
-			return;
-		}
-	}
+	if( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer > 0 )
+		return;
 
 	for (i = 0; i < 256; i++)
 	{
@@ -80,11 +77,9 @@
 		}
 	}
 
-	if (!r_enablePostProcess->integer  ||  !glConfig.qlGlsl) {
-		if (SDL_SetWindowGammaRamp(SDL_window, table[0], table[1], table[2]) < 0)
-		{
-			ri.Printf( PRINT_DEVELOPER, "SDL_SetWindowGammaRamp() failed: %s\n", SDL_GetError() );
-		}
+	if (SDL_SetWindowGammaRamp(SDL_window, table[0], table[1], table[2]) < 0)
+	{
+		ri.Printf( PRINT_DEVELOPER, "SDL_SetWindowGammaRamp() failed: %s\n", SDL_GetError() );
 	}
 }
 

```

### `quake3e`  — sha256 `7d7ac757399c...`, 3114 bytes

_Diff stat: +59 / -26 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_gamma.c	2026-04-16 20:02:25.265773300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\sdl\sdl_gamma.c	2026-04-16 20:02:27.364520500 +0100
@@ -20,16 +20,29 @@
 ===========================================================================
 */
 
-#ifdef USE_INTERNAL_SDL_HEADERS
+#ifdef USE_LOCAL_HEADERS
 #	include "SDL.h"
 #else
 #	include <SDL.h>
 #endif
 
-#include "../renderergl1/tr_local.h"
-#include "../qcommon/qcommon.h"
+#include "../client/client.h"
+#include "sdl_glw.h"
+
+static Uint16 r[256];
+static Uint16 g[256];
+static Uint16 b[256];
+
+void GLimp_InitGamma( glconfig_t *config )
+{
+	config->deviceSupportsGamma = qfalse;
+
+	if ( SDL_GetWindowGammaRamp( SDL_window, r, g, b ) == 0 )
+	{
+		config->deviceSupportsGamma = SDL_SetWindowBrightness( SDL_window, 1.0f ) >= 0 ? qtrue : qfalse;
+	}
+}
 
-extern SDL_Window *SDL_window;
 
 /*
 =================
@@ -41,13 +54,7 @@
 	Uint16 table[3][256];
 	int i, j;
 
-	if (!r_enablePostProcess->integer  ||  !r_enableColorCorrect->integer  ||  !glConfig.qlGlsl) {
-		if( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer > 0 ) {
-			return;
-		}
-	}
-
-	for (i = 0; i < 256; i++)
+	for ( i = 0; i < 256; i++ )
 	{
 		table[0][i] = ( ( ( Uint16 ) red[i] ) << 8 ) | red[i];
 		table[1][i] = ( ( ( Uint16 ) green[i] ) << 8 ) | green[i];
@@ -55,23 +62,43 @@
 	}
 
 #ifdef _WIN32
-	// Windows puts this odd restriction on gamma ramps...
-	ri.Printf( PRINT_DEVELOPER, "performing gamma clamp.\n" );
-	for( j = 0 ; j < 3 ; j++ )
+#include <windows.h>
+
+	// Win2K and newer put this odd restriction on gamma ramps...
 	{
-		for( i = 0 ; i < 128 ; i++ )
+		//OSVERSIONINFO	vinfo;
+		//vinfo.dwOSVersionInfoSize = sizeof( vinfo );
+		//GetVersionEx( &vinfo );
+		//if( vinfo.dwMajorVersion >= 5 && vinfo.dwPlatformId == VER_PLATFORM_WIN32_NT )
 		{
-			if( table[ j ][ i ] > ( ( 128 + i ) << 8 ) )
-				table[ j ][ i ] = ( 128 + i ) << 8;
+			qboolean clamped = qfalse;
+			for( j = 0 ; j < 3 ; j++ )
+			{
+				for( i = 0 ; i < 128 ; i++ )
+				{
+					if( table[ j ] [ i] > ( ( 128 + i ) << 8 ) )
+					{
+						table[ j ][ i ] = ( 128 + i ) << 8;
+						clamped = qtrue;
+					}
+				}
+
+				if( table[ j ] [127 ] > 254 << 8 )
+				{
+					table[ j ][ 127 ] = 254 << 8;
+					clamped = qtrue;
+				}
+			}
+			if ( clamped )
+			{
+				Com_DPrintf( "performing gamma clamp.\n" );
+			}
 		}
-
-		if( table[ j ][ 127 ] > 254 << 8 )
-			table[ j ][ 127 ] = 254 << 8;
 	}
 #endif
 
 	// enforce constantly increasing
-	for (j = 0; j < 3; j++)
+	for ( j = 0; j < 3; j++ )
 	{
 		for (i = 1; i < 256; i++)
 		{
@@ -80,11 +107,17 @@
 		}
 	}
 
-	if (!r_enablePostProcess->integer  ||  !glConfig.qlGlsl) {
-		if (SDL_SetWindowGammaRamp(SDL_window, table[0], table[1], table[2]) < 0)
-		{
-			ri.Printf( PRINT_DEVELOPER, "SDL_SetWindowGammaRamp() failed: %s\n", SDL_GetError() );
-		}
+	if ( SDL_SetWindowGammaRamp( SDL_window, table[0], table[1], table[2] ) < 0 )
+	{
+		Com_DPrintf( "SDL_SetWindowGammaRamp() failed: %s\n", SDL_GetError() );
 	}
 }
 
+
+/*
+** GLW_RestoreGamma
+*/
+void GLW_RestoreGamma( void )
+{
+	// automatically handled by SDL?
+}

```

### `openarena-engine`  — sha256 `0c38cda3864e...`, 3167 bytes

_Diff stat: +48 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_gamma.c	2026-04-16 20:02:25.265773300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sdl\sdl_gamma.c	2026-04-16 22:48:25.933963700 +0100
@@ -20,17 +20,24 @@
 ===========================================================================
 */
 
-#ifdef USE_INTERNAL_SDL_HEADERS
+#ifdef USE_LOCAL_HEADERS
 #	include "SDL.h"
 #else
 #	include <SDL.h>
 #endif
 
-#include "../renderergl1/tr_local.h"
+#include "../renderercommon/tr_common.h"
 #include "../qcommon/qcommon.h"
 
+#if SDL_MAJOR_VERSION == 2
 extern SDL_Window *SDL_window;
+#endif
 
+#ifdef _WIN32
+// leilei - 3dfx gamma fix
+BOOL  ( WINAPI * qwglGetDeviceGammaRamp3DFX)( HDC, LPVOID );
+BOOL  ( WINAPI * qwglSetDeviceGammaRamp3DFX)( HDC, LPVOID );
+#endif
 /*
 =================
 GLimp_SetGamma
@@ -41,11 +48,8 @@
 	Uint16 table[3][256];
 	int i, j;
 
-	if (!r_enablePostProcess->integer  ||  !r_enableColorCorrect->integer  ||  !glConfig.qlGlsl) {
-		if( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer > 0 ) {
-			return;
-		}
-	}
+	if( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer > 0 )
+		return;
 
 	for (i = 0; i < 256; i++)
 	{
@@ -55,18 +59,29 @@
 	}
 
 #ifdef _WIN32
-	// Windows puts this odd restriction on gamma ramps...
-	ri.Printf( PRINT_DEVELOPER, "performing gamma clamp.\n" );
-	for( j = 0 ; j < 3 ; j++ )
+#include <windows.h>
+
+	// Win2K and newer put this odd restriction on gamma ramps...
 	{
-		for( i = 0 ; i < 128 ; i++ )
+		OSVERSIONINFO	vinfo;
+
+		vinfo.dwOSVersionInfoSize = sizeof( vinfo );
+		GetVersionEx( &vinfo );
+		if( vinfo.dwMajorVersion >= 5 && vinfo.dwPlatformId == VER_PLATFORM_WIN32_NT )
 		{
-			if( table[ j ][ i ] > ( ( 128 + i ) << 8 ) )
-				table[ j ][ i ] = ( 128 + i ) << 8;
+			ri.Printf( PRINT_DEVELOPER, "performing gamma clamp.\n" );
+			for( j = 0 ; j < 3 ; j++ )
+			{
+				for( i = 0 ; i < 128 ; i++ )
+				{
+					if( table[ j ] [ i] > ( ( 128 + i ) << 8 ) )
+						table[ j ][ i ] = ( 128 + i ) << 8;
+				}
+
+				if( table[ j ] [127 ] > 254 << 8 )
+					table[ j ][ 127 ] = 254 << 8;
+			}
 		}
-
-		if( table[ j ][ 127 ] > 254 << 8 )
-			table[ j ][ 127 ] = 254 << 8;
 	}
 #endif
 
@@ -80,11 +95,23 @@
 		}
 	}
 
-	if (!r_enablePostProcess->integer  ||  !glConfig.qlGlsl) {
-		if (SDL_SetWindowGammaRamp(SDL_window, table[0], table[1], table[2]) < 0)
-		{
-			ri.Printf( PRINT_DEVELOPER, "SDL_SetWindowGammaRamp() failed: %s\n", SDL_GetError() );
-		}
+	// leilei - 3dfx gamma support
+#ifdef _WIN32
+	if ( qwglSetDeviceGammaRamp3DFX )
+	{
+		HDC hDC;// = GetDC( hWnd );
+		hDC = GetDC( GetForegroundWindow() );
+		qwglSetDeviceGammaRamp3DFX( hDC, table );
+		ReleaseDC( GetForegroundWindow(), hDC );
+	}
+	else
+#endif
+	{
+#if SDL_MAJOR_VERSION == 2
+		SDL_SetWindowGammaRamp(SDL_window, table[0], table[1], table[2]);
+#else
+		SDL_SetGammaRamp(table[0], table[1], table[2]);
+#endif
 	}
 }
 

```
