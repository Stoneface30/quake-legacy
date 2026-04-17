# Diff: `code/win32/win_gamma.c`
**Canonical:** `quake3e` (sha256 `1136ddc1b546...`, 7790 bytes)

## Variants

### `quake3-source`  — sha256 `a3ae5cf212f3...`, 5781 bytes

_Diff stat: +92 / -168 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\win32\win_gamma.c	2026-04-16 20:02:27.390482800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\win32\win_gamma.c	2026-04-16 20:02:20.014550900 +0100
@@ -15,13 +15,14 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 /*
 ** WIN_GAMMA.C
 */
+#include <assert.h>
 #include "../renderer/tr_local.h"
 #include "../qcommon/qcommon.h"
 #include "glw_win.h"
@@ -29,145 +30,74 @@
 
 static unsigned short s_oldHardwareGamma[3][256];
 
-static BOOL IsCurrentSessionRemoteable( void )
-{
-	BOOL fIsRemoteable = FALSE;
-
-	if ( GetSystemMetrics( SM_REMOTESESSION ) )
-	{
-		fIsRemoteable = TRUE;
-	}
-	else
-	{
-		#define TERMINAL_SERVER_KEY TEXT( "SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\" )
-		#define GLASS_SESSION_ID TEXT( "GlassSessionId" )
-
-		HKEY hRegKey = NULL;
-		LONG lResult;
-
-		lResult = RegOpenKeyEx( HKEY_LOCAL_MACHINE,	TERMINAL_SERVER_KEY, 0, KEY_READ, &hRegKey );
-
-		if ( lResult == ERROR_SUCCESS )
-		{
-			DWORD dwGlassSessionId;
-			DWORD cbGlassSessionId = sizeof(dwGlassSessionId);
-			DWORD dwType;
-
-			lResult = RegQueryValueEx( hRegKey, GLASS_SESSION_ID, NULL, &dwType, (BYTE*)&dwGlassSessionId, &cbGlassSessionId );
-
-			if ( lResult == ERROR_SUCCESS )
-			{
-				typedef BOOL (WINAPI *PFN_ProcessIdToSessionId)( DWORD dwProcessId, DWORD *pSessionId );
-				PFN_ProcessIdToSessionId pProcessIdToSessionId;
-				DWORD dwCurrentSessionId;
-				HANDLE hKernel32;
-
-				hKernel32 = GetModuleHandleA( "kernel32" );
-				if ( hKernel32 != NULL )
-				{
-					pProcessIdToSessionId = (PFN_ProcessIdToSessionId) GetProcAddress( hKernel32, "ProcessIdToSessionId" );
-					if ( pProcessIdToSessionId != NULL )
-					{
-						if ( pProcessIdToSessionId( GetCurrentProcessId(), &dwCurrentSessionId  ) )
-						{
-							fIsRemoteable = ( dwCurrentSessionId != dwGlassSessionId );
-						}
-					}
-				}
-			}
-		}
-
-		if ( hRegKey )
-		{
-			RegCloseKey( hRegKey );
-		}
-	}
-
-	return fIsRemoteable;
-}
-
-
 /*
-** GLW_InitGamma
+** WG_CheckHardwareGamma
 **
 ** Determines if the underlying hardware supports the Win32 gamma correction API.
 */
-void GLimp_InitGamma( glconfig_t *config )
+void WG_CheckHardwareGamma( void )
 {
-	HDC		hDC;
+	HDC			hDC;
 
-	config->deviceSupportsGamma = qfalse;
+	glConfig.deviceSupportsGamma = qfalse;
 
-	if ( IsCurrentSessionRemoteable() )
+	if ( qwglSetDeviceGammaRamp3DFX )
 	{
-		glw_state.deviceSupportsGamma = qfalse;
-		return; // no hardware gamma control via RDP
+		glConfig.deviceSupportsGamma = qtrue;
+
+		hDC = GetDC( GetDesktopWindow() );
+		glConfig.deviceSupportsGamma = qwglGetDeviceGammaRamp3DFX( hDC, s_oldHardwareGamma );
+		ReleaseDC( GetDesktopWindow(), hDC );
+
+		return;
 	}
 
-	if ( glw_state.displayName[0] )
+	// non-3Dfx standalone drivers don't support gamma changes, period
+	if ( glConfig.driverType == GLDRV_STANDALONE )
 	{
-		hDC = CreateDC( TEXT( "DISPLAY" ), glw_state.displayName, NULL, NULL );
-		config->deviceSupportsGamma = ( GetDeviceGammaRamp( hDC, s_oldHardwareGamma ) == FALSE ) ? qfalse : qtrue;
-		if ( config->deviceSupportsGamma )
-		{
-			// do test setup
-			if ( SetDeviceGammaRamp( hDC, s_oldHardwareGamma ) == FALSE )
-			{
-				config->deviceSupportsGamma = qfalse;
-			}
-		}
-		DeleteDC( hDC );
+		return;
 	}
-	else
+
+	if ( !r_ignorehwgamma->integer )
 	{
 		hDC = GetDC( GetDesktopWindow() );
-		config->deviceSupportsGamma = ( GetDeviceGammaRamp( hDC, s_oldHardwareGamma ) == FALSE ) ? qfalse : qtrue;
-		if ( config->deviceSupportsGamma )
-		{
-			if ( SetDeviceGammaRamp( hDC, s_oldHardwareGamma ) == FALSE )
-			{
-				config->deviceSupportsGamma = qfalse;
-			}
-		}
+		glConfig.deviceSupportsGamma = GetDeviceGammaRamp( hDC, s_oldHardwareGamma );
 		ReleaseDC( GetDesktopWindow(), hDC );
-	}
 
-	if ( config->deviceSupportsGamma )
-	{
-		//
-		// do a sanity check on the gamma values
-		//
-		if ( ( HIBYTE( s_oldHardwareGamma[0][255] ) <= HIBYTE( s_oldHardwareGamma[0][0] ) ) ||
-			 ( HIBYTE( s_oldHardwareGamma[1][255] ) <= HIBYTE( s_oldHardwareGamma[1][0] ) ) ||
-			 ( HIBYTE( s_oldHardwareGamma[2][255] ) <= HIBYTE( s_oldHardwareGamma[2][0] ) ) )
+		if ( glConfig.deviceSupportsGamma )
 		{
-			config->deviceSupportsGamma = qfalse;
-			Com_Printf( S_COLOR_YELLOW "WARNING: device has broken gamma support\n" );
-		}
+			//
+			// do a sanity check on the gamma values
+			//
+			if ( ( HIBYTE( s_oldHardwareGamma[0][255] ) <= HIBYTE( s_oldHardwareGamma[0][0] ) ) ||
+				 ( HIBYTE( s_oldHardwareGamma[1][255] ) <= HIBYTE( s_oldHardwareGamma[1][0] ) ) ||
+				 ( HIBYTE( s_oldHardwareGamma[2][255] ) <= HIBYTE( s_oldHardwareGamma[2][0] ) ) )
+			{
+				glConfig.deviceSupportsGamma = qfalse;
+				ri.Printf( PRINT_WARNING, "WARNING: device has broken gamma support, generated gamma.dat\n" );
+			}
 
-		//
-		// make sure that we didn't have a prior crash in the game, and if so we need to
-		// restore the gamma values to at least a linear value
-		//
-		if ( ( HIBYTE( s_oldHardwareGamma[0][181] ) == 255 ) )
-		{
-			int g;
+			//
+			// make sure that we didn't have a prior crash in the game, and if so we need to
+			// restore the gamma values to at least a linear value
+			//
+			if ( ( HIBYTE( s_oldHardwareGamma[0][181] ) == 255 ) )
+			{
+				int g;
 
-			Com_Printf( S_COLOR_YELLOW "WARNING: suspicious gamma tables, using linear ramp for restoration\n" );
+				ri.Printf( PRINT_WARNING, "WARNING: suspicious gamma tables, using linear ramp for restoration\n" );
 
-			for ( g = 0; g < 256; g++ )
-			{
-				s_oldHardwareGamma[0][g] = g << 8;
-				s_oldHardwareGamma[1][g] = g << 8;
-				s_oldHardwareGamma[2][g] = g << 8;
+				for ( g = 0; g < 255; g++ )
+				{
+					s_oldHardwareGamma[0][g] = g << 8;
+					s_oldHardwareGamma[1][g] = g << 8;
+					s_oldHardwareGamma[2][g] = g << 8;
+				}
 			}
 		}
-	} // if ( config->deviceSupportsGamma )
-
-	glw_state.deviceSupportsGamma = config->deviceSupportsGamma;
+	}
 }
 
-
 /*
 void mapGammaMax( void ) {
 	int		i, j;
@@ -195,7 +125,6 @@
 }
 */
 
-
 /*
 ** GLimp_SetGamma
 **
@@ -204,11 +133,12 @@
 void GLimp_SetGamma( unsigned char red[256], unsigned char green[256], unsigned char blue[256] ) {
 	unsigned short table[3][256];
 	int		i, j;
-	BOOL	ret;
-	HDC		hDC;
+	int		ret;
+	OSVERSIONINFO	vinfo;
 
-	if ( /*!glw_state.hDC* ||*/ !gw_active )
+	if ( !glConfig.deviceSupportsGamma || r_ignorehwgamma->integer || !glw_state.hDC ) {
 		return;
+	}
 
 //mapGammaMax();
 
@@ -218,17 +148,23 @@
 		table[2][i] = ( ( ( unsigned short ) blue[i] ) << 8 ) | blue[i];
 	}
 
-	// Win2K and newer put this odd restriction on gamma ramps...
-	Com_DPrintf( "performing gamma clamp.\n" );
-	for ( j = 0 ; j < 3 ; j++ ) {
-		for ( i = 0 ; i < 128 ; i++ ) {
-			if ( table[j][i] > ( (128+i) << 8 ) ) {
-				table[j][i] = (128+i) << 8;
+	// Win2K puts this odd restriction on gamma ramps...
+	vinfo.dwOSVersionInfoSize = sizeof(vinfo);
+	GetVersionEx( &vinfo );
+	if ( vinfo.dwMajorVersion == 5 && vinfo.dwPlatformId == VER_PLATFORM_WIN32_NT ) {
+		Com_DPrintf( "performing W2K gamma clamp.\n" );
+		for ( j = 0 ; j < 3 ; j++ ) {
+			for ( i = 0 ; i < 128 ; i++ ) {
+				if ( table[j][i] > ( (128+i) << 8 ) ) {
+					table[j][i] = (128+i) << 8;
+				}
+			}
+			if ( table[j][127] > 254<<8 ) {
+				table[j][127] = 254<<8;
 			}
 		}
-		if ( table[j][127] > 254<<8 ) {
-			table[j][127] = 254<<8;
-		}
+	} else {
+		Com_DPrintf( "skipping W2K gamma clamp.\n" );
 	}
 
 	// enforce constantly increasing
@@ -240,51 +176,39 @@
 		}
 	}
 
-	if ( glw_state.displayName[0] ) {
-		hDC = CreateDC( TEXT( "DISPLAY" ), glw_state.displayName, NULL, NULL );
-		ret = SetDeviceGammaRamp( hDC, table );
-		DeleteDC( hDC );
-	} else {
-		hDC = GetDC( GetDesktopWindow() );
-		ret = SetDeviceGammaRamp( hDC, table );
-		ReleaseDC( GetDesktopWindow(), hDC );
-	}
 
-	if ( !ret ) {
-		Com_Printf( S_COLOR_YELLOW "SetDeviceGammaRamp failed.\n" );
-	} else {
-		glw_state.gammaSet = qtrue;
+	if ( qwglSetDeviceGammaRamp3DFX )
+	{
+		qwglSetDeviceGammaRamp3DFX( glw_state.hDC, table );
+	}
+	else
+	{
+		ret = SetDeviceGammaRamp( glw_state.hDC, table );
+		if ( !ret ) {
+			Com_Printf( "SetDeviceGammaRamp failed.\n" );
+		}
 	}
 }
 
-
 /*
-** GLW_RestoreGamma
+** WG_RestoreGamma
 */
-void GLW_RestoreGamma( void )
+void WG_RestoreGamma( void )
 {
-	HDC hDC;
-	BOOL ret;
-
-	if ( !glw_state.gammaSet ) {
-		return;
-	}
-
-	if ( !glw_state.deviceSupportsGamma ) {
-		return;
-	}	
-
-	if ( glw_state.displayName[0] ) {
-		hDC = CreateDC( TEXT( "DISPLAY" ), glw_state.displayName, NULL, NULL );
-		ret = SetDeviceGammaRamp( hDC, s_oldHardwareGamma );
-		DeleteDC( hDC);
-	} else {
-		hDC = GetDC( GetDesktopWindow() );
-		ret = SetDeviceGammaRamp( hDC, s_oldHardwareGamma );
-		ReleaseDC( GetDesktopWindow(), hDC );
-	}
-
-	if ( ret ) {
-		glw_state.gammaSet = qfalse;
+	if ( glConfig.deviceSupportsGamma )
+	{
+		if ( qwglSetDeviceGammaRamp3DFX )
+		{
+			qwglSetDeviceGammaRamp3DFX( glw_state.hDC, s_oldHardwareGamma );
+		}
+		else
+		{
+			HDC hDC;
+			
+			hDC = GetDC( GetDesktopWindow() );
+			SetDeviceGammaRamp( hDC, s_oldHardwareGamma );
+			ReleaseDC( GetDesktopWindow(), hDC );
+		}
 	}
 }
+

```
