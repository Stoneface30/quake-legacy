# Diff: `code/ui/ui_public.h`
**Canonical:** `wolfcamql-src` (sha256 `e83d0d48df1d...`, 4730 bytes)

## Variants

### `quake3-source`  — sha256 `9f6681cdaef0...`, 4495 bytes

_Diff stat: +4 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_public.h	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_public.h	2026-04-16 20:02:19.987145400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -32,7 +32,6 @@
 	char			servername[MAX_STRING_CHARS];
 	char			updateInfoString[MAX_STRING_CHARS];
 	char			messageString[MAX_STRING_CHARS];
-	qboolean demoplaying;
 } uiClientState_t;
 
 typedef enum {
@@ -134,16 +133,7 @@
 	UI_ATAN2,
 	UI_SQRT,
 	UI_FLOOR,
-	UI_CEIL,
-	UI_ACOS,
-
-	UI_OPEN_QUAKE_LIVE_DIRECTORY,
-	UI_OPEN_WOLFCAM_DIRECTORY,
-	UI_DRAW_CONSOLE_LINES_OVER,
-
-	UI_CVAR_EXISTS,
-	UI_R_BEGIN_HUD,
-
+	UI_CEIL
 } uiImport_t;
 
 typedef enum {
@@ -176,7 +166,7 @@
 //	void	UI_KeyEvent( int key );
 
 	UI_MOUSE_EVENT,
-//	void	UI_MouseEvent( int dx, int dy, qboolean active );
+//	void	UI_MouseEvent( int dx, int dy );
 
 	UI_REFRESH,
 //	void	UI_Refresh( int time );
@@ -192,12 +182,10 @@
 
 	UI_DRAW_CONNECT_SCREEN,
 //	void	UI_DrawConnectScreen( qboolean overlay );
-	UI_HASUNIQUECDKEY,
+	UI_HASUNIQUECDKEY
 // if !overlay, the background will be drawn, otherwise it will be
 // overlayed over whatever the cgame has drawn.
 // a GetClientState syscall will be made to get the current strings
-
-	UI_COLOR_TABLE_CHANGE,
 } uiExport_t;
 
 #endif

```

### `openarena-engine`  — sha256 `53dcb4dd9f94...`, 4516 bytes
Also identical in: ioquake3

_Diff stat: +3 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_public.h	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_public.h	2026-04-16 22:48:25.960600200 +0100
@@ -32,7 +32,6 @@
 	char			servername[MAX_STRING_CHARS];
 	char			updateInfoString[MAX_STRING_CHARS];
 	char			messageString[MAX_STRING_CHARS];
-	qboolean demoplaying;
 } uiClientState_t;
 
 typedef enum {
@@ -134,16 +133,7 @@
 	UI_ATAN2,
 	UI_SQRT,
 	UI_FLOOR,
-	UI_CEIL,
-	UI_ACOS,
-
-	UI_OPEN_QUAKE_LIVE_DIRECTORY,
-	UI_OPEN_WOLFCAM_DIRECTORY,
-	UI_DRAW_CONSOLE_LINES_OVER,
-
-	UI_CVAR_EXISTS,
-	UI_R_BEGIN_HUD,
-
+	UI_CEIL
 } uiImport_t;
 
 typedef enum {
@@ -176,7 +166,7 @@
 //	void	UI_KeyEvent( int key );
 
 	UI_MOUSE_EVENT,
-//	void	UI_MouseEvent( int dx, int dy, qboolean active );
+//	void	UI_MouseEvent( int dx, int dy );
 
 	UI_REFRESH,
 //	void	UI_Refresh( int time );
@@ -192,12 +182,10 @@
 
 	UI_DRAW_CONNECT_SCREEN,
 //	void	UI_DrawConnectScreen( qboolean overlay );
-	UI_HASUNIQUECDKEY,
+	UI_HASUNIQUECDKEY
 // if !overlay, the background will be drawn, otherwise it will be
 // overlayed over whatever the cgame has drawn.
 // a GetClientState syscall will be made to get the current strings
-
-	UI_COLOR_TABLE_CHANGE,
 } uiExport_t;
 
 #endif

```

### `quake3e`  — sha256 `b66016a824b4...`, 4620 bytes

_Diff stat: +11 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_public.h	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\ui\ui_public.h	2026-04-16 20:02:27.370600000 +0100
@@ -32,7 +32,6 @@
 	char			servername[MAX_STRING_CHARS];
 	char			updateInfoString[MAX_STRING_CHARS];
 	char			messageString[MAX_STRING_CHARS];
-	qboolean demoplaying;
 } uiClientState_t;
 
 typedef enum {
@@ -126,23 +125,14 @@
 	UI_FS_SEEK,
 	UI_SET_PBCLSTATUS,
 
-	UI_MEMSET = 100,
-	UI_MEMCPY,
-	UI_STRNCPY,
-	UI_SIN,
-	UI_COS,
-	UI_ATAN2,
-	UI_SQRT,
-	UI_FLOOR,
+	UI_FLOOR = 107,
 	UI_CEIL,
-	UI_ACOS,
 
-	UI_OPEN_QUAKE_LIVE_DIRECTORY,
-	UI_OPEN_WOLFCAM_DIRECTORY,
-	UI_DRAW_CONSOLE_LINES_OVER,
-
-	UI_CVAR_EXISTS,
-	UI_R_BEGIN_HUD,
+	// engine extensions
+	UI_R_ADDREFENTITYTOSCENE2,
+	UI_R_ADDLINEARLIGHTTOSCENE,
+	UI_CVAR_SETDESCRIPTION,
+	UI_TRAP_GETVALUE = COM_TRAP_GETVALUE,
 
 } uiImport_t;
 
@@ -173,10 +163,10 @@
 //	void	UI_Shutdown( void );
 
 	UI_KEY_EVENT,
-//	void	UI_KeyEvent( int key );
+//	void	UI_KeyEvent( int key, int down );
 
 	UI_MOUSE_EVENT,
-//	void	UI_MouseEvent( int dx, int dy, qboolean active );
+//	void	UI_MouseEvent( int dx, int dy );
 
 	UI_REFRESH,
 //	void	UI_Refresh( int time );
@@ -192,12 +182,13 @@
 
 	UI_DRAW_CONNECT_SCREEN,
 //	void	UI_DrawConnectScreen( qboolean overlay );
+
 	UI_HASUNIQUECDKEY,
 // if !overlay, the background will be drawn, otherwise it will be
 // overlayed over whatever the cgame has drawn.
 // a GetClientState syscall will be made to get the current strings
-
-	UI_COLOR_TABLE_CHANGE,
+	
+	UI_EXPORT_LAST,
 } uiExport_t;
 
 #endif

```

### `openarena-gamecode`  — sha256 `49b2af45a1df...`, 4488 bytes

_Diff stat: +3 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_public.h	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\ui\ui_public.h	2026-04-16 22:48:24.214593500 +0100
@@ -32,7 +32,6 @@
 	char			servername[MAX_STRING_CHARS];
 	char			updateInfoString[MAX_STRING_CHARS];
 	char			messageString[MAX_STRING_CHARS];
-	qboolean demoplaying;
 } uiClientState_t;
 
 typedef enum {
@@ -134,16 +133,7 @@
 	UI_ATAN2,
 	UI_SQRT,
 	UI_FLOOR,
-	UI_CEIL,
-	UI_ACOS,
-
-	UI_OPEN_QUAKE_LIVE_DIRECTORY,
-	UI_OPEN_WOLFCAM_DIRECTORY,
-	UI_DRAW_CONSOLE_LINES_OVER,
-
-	UI_CVAR_EXISTS,
-	UI_R_BEGIN_HUD,
-
+	UI_CEIL
 } uiImport_t;
 
 typedef enum {
@@ -161,7 +151,6 @@
 #define SORT_CLIENTS		2
 #define SORT_GAME			3
 #define SORT_PING			4
-#define SORT_PUNKBUSTER		5
 
 typedef enum {
 	UI_GETAPIVERSION = 0,	// system reserved
@@ -176,7 +165,7 @@
 //	void	UI_KeyEvent( int key );
 
 	UI_MOUSE_EVENT,
-//	void	UI_MouseEvent( int dx, int dy, qboolean active );
+//	void	UI_MouseEvent( int dx, int dy );
 
 	UI_REFRESH,
 //	void	UI_Refresh( int time );
@@ -192,12 +181,10 @@
 
 	UI_DRAW_CONNECT_SCREEN,
 //	void	UI_DrawConnectScreen( qboolean overlay );
-	UI_HASUNIQUECDKEY,
+	UI_HASUNIQUECDKEY
 // if !overlay, the background will be drawn, otherwise it will be
 // overlayed over whatever the cgame has drawn.
 // a GetClientState syscall will be made to get the current strings
-
-	UI_COLOR_TABLE_CHANGE,
 } uiExport_t;
 
 #endif

```
