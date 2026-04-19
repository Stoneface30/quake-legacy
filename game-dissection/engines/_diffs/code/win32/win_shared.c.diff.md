# Diff: `code/win32/win_shared.c`
**Canonical:** `quake3e` (sha256 `3ffef33fa5e0...`, 6179 bytes)

## Variants

### `quake3-source`  — sha256 `a999fcb8c238...`, 6183 bytes

_Diff stat: +210 / -153 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\win32\win_shared.c	2026-04-16 20:02:27.393481900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\win32\win_shared.c	2026-04-16 20:02:20.017557000 +0100
@@ -15,235 +15,292 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "../qcommon/qcommon.h"
 #include "win_local.h"
+#include <lmerr.h>
+#include <lmcons.h>
+#include <lmwksta.h>
 #include <errno.h>
 #include <fcntl.h>
 #include <stdio.h>
 #include <direct.h>
 #include <io.h>
 #include <conio.h>
-#include <intrin.h>
 
 /*
 ================
 Sys_Milliseconds
 ================
 */
-int Sys_Milliseconds( void )
+int			sys_timeBase;
+int Sys_Milliseconds (void)
 {
+	int			sys_curtime;
 	static qboolean	initialized = qfalse;
-	static DWORD sys_timeBase;
-	int	sys_curtime;
 
-	if ( !initialized ) {
+	if (!initialized) {
 		sys_timeBase = timeGetTime();
 		initialized = qtrue;
 	}
-
 	sys_curtime = timeGetTime() - sys_timeBase;
 
 	return sys_curtime;
 }
 
-
 /*
 ================
-Sys_RandomBytes
+Sys_SnapVector
 ================
 */
-qboolean Sys_RandomBytes( byte *string, int len )
+long fastftol( float f ) {
+	static int tmp;
+	__asm fld f
+	__asm fistp tmp
+	__asm mov eax, tmp
+}
+
+void Sys_SnapVector( float *v )
 {
-	HCRYPTPROV  prov;
+	int i;
+	float f;
 
-	if( !CryptAcquireContext( &prov, NULL, NULL,
-		PROV_RSA_FULL, CRYPT_VERIFYCONTEXT ) )  {
+	f = *v;
+	__asm	fld		f;
+	__asm	fistp	i;
+	*v = i;
+	v++;
+	f = *v;
+	__asm	fld		f;
+	__asm	fistp	i;
+	*v = i;
+	v++;
+	f = *v;
+	__asm	fld		f;
+	__asm	fistp	i;
+	*v = i;
+	/*
+	*v = fastftol(*v);
+	v++;
+	*v = fastftol(*v);
+	v++;
+	*v = fastftol(*v);
+	*/
+}
 
-		return qfalse;
-	}
 
-	if( !CryptGenRandom( prov, len, (BYTE *)string ) )  {
-		CryptReleaseContext( prov, 0 );
-		return qfalse;
+/*
+**
+** Disable all optimizations temporarily so this code works correctly!
+**
+*/
+#pragma optimize( "", off )
+
+/*
+** --------------------------------------------------------------------------------
+**
+** PROCESSOR STUFF
+**
+** --------------------------------------------------------------------------------
+*/
+static void CPUID( int func, unsigned regs[4] )
+{
+	unsigned regEAX, regEBX, regECX, regEDX;
+
+#ifndef __VECTORC
+	__asm mov eax, func
+	__asm __emit 00fh
+	__asm __emit 0a2h
+	__asm mov regEAX, eax
+	__asm mov regEBX, ebx
+	__asm mov regECX, ecx
+	__asm mov regEDX, edx
+
+	regs[0] = regEAX;
+	regs[1] = regEBX;
+	regs[2] = regECX;
+	regs[3] = regEDX;
+#else
+	regs[0] = 0;
+	regs[1] = 0;
+	regs[2] = 0;
+	regs[3] = 0;
+#endif
+}
+
+static int IsPentium( void )
+{
+	__asm 
+	{
+		pushfd						// save eflags
+		pop		eax
+		test	eax, 0x00200000		// check ID bit
+		jz		set21				// bit 21 is not set, so jump to set_21
+		and		eax, 0xffdfffff		// clear bit 21
+		push	eax					// save new value in register
+		popfd						// store new value in flags
+		pushfd
+		pop		eax
+		test	eax, 0x00200000		// check ID bit
+		jz		good
+		jmp		err					// cpuid not supported
+set21:
+		or		eax, 0x00200000		// set ID bit
+		push	eax					// store new value
+		popfd						// store new value in EFLAGS
+		pushfd
+		pop		eax
+		test	eax, 0x00200000		// if bit 21 is on
+		jnz		good
+		jmp		err
 	}
-	CryptReleaseContext( prov, 0 );
+
+err:
+	return qfalse;
+good:
 	return qtrue;
 }
 
-
-#ifdef UNICODE
-LPWSTR AtoW( const char *s ) 
+static int Is3DNOW( void )
 {
-	static WCHAR buffer[MAXPRINTMSG*2];
-	MultiByteToWideChar( CP_ACP, 0, s, strlen( s ) + 1, (LPWSTR) buffer, ARRAYSIZE( buffer ) );
-	return buffer;
+	unsigned regs[4];
+	char pstring[16];
+	char processorString[13];
+
+	// get name of processor
+	CPUID( 0, ( unsigned int * ) pstring );
+	processorString[0] = pstring[4];
+	processorString[1] = pstring[5];
+	processorString[2] = pstring[6];
+	processorString[3] = pstring[7];
+	processorString[4] = pstring[12];
+	processorString[5] = pstring[13];
+	processorString[6] = pstring[14];
+	processorString[7] = pstring[15];
+	processorString[8] = pstring[8];
+	processorString[9] = pstring[9];
+	processorString[10] = pstring[10];
+	processorString[11] = pstring[11];
+	processorString[12] = 0;
+
+//  REMOVED because you can have 3DNow! on non-AMD systems
+//	if ( strcmp( processorString, "AuthenticAMD" ) )
+//		return qfalse;
+
+	// check AMD-specific functions
+	CPUID( 0x80000000, regs );
+	if ( regs[0] < 0x80000000 )
+		return qfalse;
+
+	// bit 31 of EDX denotes 3DNOW! support
+	CPUID( 0x80000001, regs );
+	if ( regs[3] & ( 1 << 31 ) )
+		return qtrue;
+
+	return qfalse;
 }
 
-const char *WtoA( const LPWSTR s ) 
+static int IsKNI( void )
 {
-	static char buffer[MAXPRINTMSG*2];
-	WideCharToMultiByte( CP_ACP, 0, s, -1, buffer, ARRAYSIZE( buffer ), NULL, NULL );
-	return buffer;
-}
-#endif
+	unsigned regs[4];
 
+	// get CPU feature bits
+	CPUID( 1, regs );
 
-/*
-================
-Sys_DefaultHomePath
-================
-*/
-const char *Sys_DefaultHomePath( void ) 
+	// bit 25 of EDX denotes KNI existence
+	if ( regs[3] & ( 1 << 25 ) )
+		return qtrue;
+
+	return qfalse;
+}
+
+static int IsMMX( void )
 {
-#ifdef USE_PROFILES
-	TCHAR szPath[MAX_PATH];
-	static char path[MAX_OSPATH];
-	FARPROC qSHGetFolderPath;
-	HMODULE shfolder = LoadLibrary("shfolder.dll");
-	
-	if(shfolder == NULL) {
-		Com_Printf("Unable to load SHFolder.dll\n");
-		return NULL;
-	}
+	unsigned regs[4];
 
-	qSHGetFolderPath = GetProcAddress(shfolder, "SHGetFolderPathA");
-	if(qSHGetFolderPath == NULL)
-	{
-		Com_Printf("Unable to find SHGetFolderPath in SHFolder.dll\n");
-		FreeLibrary(shfolder);
-		return NULL;
-	}
+	// get CPU feature bits
+	CPUID( 1, regs );
 
-	if( !SUCCEEDED( qSHGetFolderPath( NULL, CSIDL_APPDATA,
-		NULL, 0, szPath ) ) )
-	{
-		Com_Printf("Unable to detect CSIDL_APPDATA\n");
-		FreeLibrary(shfolder);
-		return NULL;
-	}
-	Q_strncpyz( path, szPath, sizeof(path) );
-	Q_strcat( path, sizeof(path), "\\Quake3" );
-	FreeLibrary(shfolder);
-	if( !CreateDirectory( path, NULL ) )
-	{
-		if( GetLastError() != ERROR_ALREADY_EXISTS )
-		{
-			Com_Printf("Unable to create directory \"%s\"\n", path);
-			return NULL;
-		}
-	}
-	return path;
-#else
-    return NULL;
-#endif
+	// bit 23 of EDX denotes MMX existence
+	if ( regs[3] & ( 1 << 23 ) )
+		return qtrue;
+	return qfalse;
 }
 
-
-/*
-================
-Sys_SteamPath
-================
-*/
-const char *Sys_SteamPath( void )
+int Sys_GetProcessorId( void )
 {
-	static TCHAR steamPath[ MAX_OSPATH ]; // will be converted from TCHAR to ANSI
+#if defined _M_ALPHA
+	return CPUID_AXP;
+#elif !defined _M_IX86
+	return CPUID_GENERIC;
+#else
 
-#if defined(STEAMPATH_NAME) || defined(STEAMPATH_APPID)
-	HKEY steamRegKey;
-	DWORD pathLen = MAX_OSPATH;
-	qboolean finishPath = qfalse;
-#endif
+	// verify we're at least a Pentium or 486 w/ CPUID support
+	if ( !IsPentium() )
+		return CPUID_INTEL_UNSUPPORTED;
 
-#ifdef STEAMPATH_APPID
-	// Assuming Steam is a 32-bit app
-	if ( !steamPath[0] && RegOpenKeyEx(HKEY_LOCAL_MACHINE, AtoW("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App " STEAMPATH_APPID), 0, KEY_QUERY_VALUE | KEY_WOW64_32KEY, &steamRegKey ) == ERROR_SUCCESS ) 
+	// check for MMX
+	if ( !IsMMX() )
 	{
-		pathLen = sizeof( steamPath );
-		if ( RegQueryValueEx( steamRegKey, AtoW("InstallLocation"), NULL, NULL, (LPBYTE)steamPath, &pathLen ) != ERROR_SUCCESS )
-			steamPath[ 0 ] = '\0';
-
-		RegCloseKey( steamRegKey );
+		// Pentium or PPro
+		return CPUID_INTEL_PENTIUM;
 	}
 
-#ifdef STEAMPATH_NAME
-	if ( !steamPath[0] && RegOpenKeyEx(HKEY_CURRENT_USER, AtoW("Software\\Valve\\Steam"), 0, KEY_QUERY_VALUE, &steamRegKey ) == ERROR_SUCCESS )
+	// see if we're an AMD 3DNOW! processor
+	if ( Is3DNOW() )
 	{
-		pathLen = sizeof( steamPath );
-		if ( RegQueryValueEx( steamRegKey, AtoW("SteamPath"), NULL, NULL, (LPBYTE)steamPath, &pathLen ) != ERROR_SUCCESS ) {
-			pathLen = sizeof( steamPath );
-			if ( RegQueryValueEx( steamRegKey, AtoW("InstallPath"), NULL, NULL, (LPBYTE)steamPath, &pathLen ) != ERROR_SUCCESS )
-				steamPath[ 0 ] = '\0';
-		}
-
-		if ( steamPath[ 0 ] )
-			finishPath = qtrue;
-
-		RegCloseKey( steamRegKey );
+		return CPUID_AMD_3DNOW;
 	}
-#endif
 
-	if ( steamPath[ 0 ] )
+	// see if we're an Intel Katmai
+	if ( IsKNI() )
 	{
-		if ( pathLen == sizeof( steamPath ) )
-			pathLen--;
-
-		*( ((char*)steamPath) + pathLen )  = '\0';
-#ifdef UNICODE
-		strcpy( (char*)steamPath, WtoA( steamPath ) );
-#endif
-		if ( finishPath )
-			Q_strcat( (char*)steamPath, MAX_OSPATH, "\\SteamApps\\common\\" STEAMPATH_NAME );
+		return CPUID_INTEL_KATMAI;
 	}
-#endif
 
-	return (const char*)steamPath;
-}
+	// by default we're functionally a vanilla Pentium/MMX or P2/MMX
+	return CPUID_INTEL_MMX;
 
+#endif
+}
 
 /*
-================
-Sys_SetAffinityMask
-================
+**
+** Re-enable optimizations back to what they were
+**
 */
-#ifdef USE_AFFINITY_MASK
-static HANDLE hCurrentProcess = 0;
+#pragma optimize( "", on )
+
+//============================================
 
-uint64_t Sys_GetAffinityMask( void )
+char *Sys_GetCurrentUser( void )
 {
-	DWORD_PTR dwProcessAffinityMask;
-	DWORD_PTR dwSystemAffinityMask;
+	static char s_userName[1024];
+	unsigned long size = sizeof( s_userName );
 
-	if ( hCurrentProcess == 0 )	{
-		hCurrentProcess = GetCurrentProcess();
-	}
 
-	if ( GetProcessAffinityMask( hCurrentProcess, &dwProcessAffinityMask, &dwSystemAffinityMask ) )	{
-		return (uint64_t)dwProcessAffinityMask;
+	if ( !GetUserName( s_userName, &size ) )
+		strcpy( s_userName, "player" );
+
+	if ( !s_userName[0] )
+	{
+		strcpy( s_userName, "player" );
 	}
 
-	return 0;
+	return s_userName;
 }
 
+char	*Sys_DefaultHomePath(void) {
+	return NULL;
+}
 
-qboolean Sys_SetAffinityMask( const uint64_t mask )
+char *Sys_DefaultInstallPath(void)
 {
-	DWORD_PTR dwProcessAffinityMask = (DWORD_PTR)mask;
-
-	if ( hCurrentProcess == 0 ) {
-		hCurrentProcess = GetCurrentProcess();
-	}
-
-	if ( SetProcessAffinityMask( hCurrentProcess, dwProcessAffinityMask ) )	{
-		//Sleep( 0 );
-		return qtrue;
-	}
-
-	return qfalse;
+	return Sys_Cwd();
 }
-#endif // USE_AFFINITY_MASK
+

```
