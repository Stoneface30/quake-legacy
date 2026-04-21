# Diff: `code/win32/win_local.h`
**Canonical:** `quake3e` (sha256 `31c1e75ab45f...`, 4502 bytes)

## Variants

### `quake3-source`  — sha256 `4a852f209b4d...`, 2684 bytes

_Diff stat: +35 / -102 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\win32\win_local.h	2026-04-16 20:02:27.392484400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\win32\win_local.h	2026-04-16 20:02:20.015556400 +0100
@@ -15,97 +15,39 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // win_local.h: Win32-specific Quake3 header file
 
-#define RAW_INPUT
-
-#define FAST_MODE_SWITCH
-
-#ifdef RAW_INPUT
-
-#ifndef HID_USAGE_GENERIC_MOUSE
-#define HID_USAGE_GENERIC_MOUSE        ((USHORT) 0x02)
-#endif
-
-#ifndef HID_USAGE_PAGE_GENERIC
-#define HID_USAGE_PAGE_GENERIC         ((USHORT) 0x01)
-#endif
-
+#if defined (_MSC_VER) && (_MSC_VER >= 1200)
+#pragma warning(disable : 4201)
+#pragma warning( push )
 #endif
-
-//#if defined (_MSC_VER) && (_MSC_VER >= 1200)
-//#pragma warning(disable : 4201)
-//#pragma warning( push )
-//#endif
 #include <windows.h>
-//#if defined (_MSC_VER) && (_MSC_VER >= 1200)
-//#pragma warning( pop )
-//#endif
-
-#define HK_MOD_ALT		0x00100
-#define HK_MOD_CONTROL  0x00200
-#define HK_MOD_SHIFT	0x00400
-#define HK_MOD_WIN		0x00800
-#define HK_MOD_MASK		0x00F00
-#define HK_MOD_LALT		0x01000
-#define HK_MOD_RALT		0x02000
-#define HK_MOD_LCONTROL	0x04000
-#define HK_MOD_RCONTROL	0x08000
-#define HK_MOD_LSHIFT	0x10000
-#define HK_MOD_RSHIFT	0x20000
-#define HK_MOD_LWIN		0x40000
-#define HK_MOD_RWIN		0x80000
-#define HK_MOD_XMASK	0xFF000
+#if defined (_MSC_VER) && (_MSC_VER >= 1200)
+#pragma warning( pop )
+#endif
 
 #define	DIRECTSOUND_VERSION	0x0300
 #define	DIRECTINPUT_VERSION	0x0300
 
-#include <mmsystem.h>
 #include <dinput.h>
 #include <dsound.h>
-#include <shlobj.h>
+#include <winsock.h>
+#include <wsipx.h>
 
-#undef open
-#define open _open
-#undef close
-#define close _close
-#undef write
-#define write _write
+void	IN_MouseEvent (int mstate);
 
-#ifndef MK_XBUTTON1
-#define MK_XBUTTON1         0x0020
-#endif
-#ifndef MK_XBUTTON2
-#define MK_XBUTTON2         0x0040
-#endif
+void Sys_QueEvent( int time, sysEventType_t type, int value, int value2, int ptrLength, void *ptr );
 
-#define	WINDOW_STYLE_NORMAL          (WS_VISIBLE|WS_CLIPCHILDREN|WS_CLIPSIBLINGS|WS_SYSMENU|WS_CAPTION|WS_MINIMIZEBOX|WS_BORDER)
-#define	WINDOW_STYLE_NORMAL_NB       (WS_VISIBLE|WS_CLIPCHILDREN|WS_CLIPSIBLINGS|WS_POPUP)
-#define	WINDOW_ESTYLE_NORMAL         (0)
-#define	WINDOW_STYLE_FULLSCREEN      (WS_VISIBLE|WS_CLIPCHILDREN|WS_CLIPSIBLINGS|WS_POPUP)
-#define	WINDOW_ESTYLE_FULLSCREEN     (0)
-#define	WINDOW_STYLE_FULLSCREEN_MIN  (WS_VISIBLE|WS_CLIPCHILDREN|WS_CLIPSIBLINGS)
-#define	WINDOW_ESTYLE_FULLSCREEN_MIN (0)
-
-#define T TEXT
-#ifdef UNICODE
-LPWSTR AtoW( const char *s );
-const char *WtoA( const LPWSTR s );
-#else
-#define AtoW(S) (S)
-#define WtoA(S) (S)
-#endif
+void	Sys_CreateConsole( void );
+void	Sys_DestroyConsole( void );
 
-qboolean IN_MouseActive( void );
-void	IN_Win32MouseEvent( int mstate );
-void	IN_RawMouseEvent( LPARAM lParam );
+char	*Sys_ConsoleInput (void);
 
-void	Sys_CreateConsole( const char *title, int xPos, int yPos, qboolean usePos );
-void	Sys_DestroyConsole( void );
+qboolean	Sys_GetPacket ( netadr_t *net_from, msg_t *net_message );
 
 // Input subsystem
 
@@ -113,50 +55,41 @@
 void	IN_Shutdown (void);
 void	IN_JoystickCommands (void);
 
-void	IN_Activate( qboolean active );
-void	IN_Frame( void );
+void	IN_Move (usercmd_t *cmd);
+// add additional non keyboard / non mouse movement on top of the keyboard move cmd
+
+void	IN_DeactivateWin32Mouse( void);
 
-void	IN_UpdateWindow( RECT *window_rect, qboolean updateClipRegion );
-void	UpdateMonitorInfo( const RECT *target );
+void	IN_Activate (qboolean active);
+void	IN_Frame (void);
 
 // window procedure
-LRESULT WINAPI MainWndProc( HWND hWnd, UINT uMsg, WPARAM  wParam, LPARAM  lParam );
-void HandleConsoleEvents( void );
+LONG WINAPI MainWndProc (
+    HWND    hWnd,
+    UINT    uMsg,
+    WPARAM  wParam,
+    LPARAM  lParam);
 
 void Conbuf_AppendText( const char *msg );
-void Conbuf_BeginPrint( void );
-void Conbuf_EndPrint( void );
 
 void SNDDMA_Activate( void );
+int  SNDDMA_InitDS ();
 
 typedef struct
 {
-	HINSTANCE		hInstance;
-	HWND			hWnd;
-
-	// Multi-monitor tracking
-	RECT			conRect;
-#ifndef DEDICATED
-	RECT			winRect;
-	qboolean		winRectValid;
+	
+	HINSTANCE		reflib_library;		// Handle to refresh DLL 
+	qboolean		reflib_active;
 
-	int				borderless;
+	HWND			hWnd;
+	HINSTANCE		hInstance;
+	qboolean		activeApp;
+	qboolean		isMinimized;
+	OSVERSIONINFO	osversion;
 
 	// when we get a windows message, we store the time off so keyboard processing
 	// can know the exact time of an event
 	unsigned		sysMsgTime;
-#endif
 } WinVars_t;
 
 extern WinVars_t	g_wv;
-
-void WIN_DisableHook( void );
-void WIN_EnableHook( void );
-
-void WIN_DisableAltTab( void );
-void WIN_EnableAltTab( void );
-
-void WIN_Minimize( void );
-
-void GLW_HideFullscreenWindow( void );
-void GLW_RestoreGamma( void );

```
