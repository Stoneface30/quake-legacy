# Diff: `code/win32/glw_win.h`
**Canonical:** `quake3e` (sha256 `de1e410614d9...`, 1936 bytes)

## Variants

### `quake3-source`  — sha256 `78a2fb52aef5...`, 1548 bytes

_Diff stat: +9 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\win32\glw_win.h	2026-04-16 20:02:27.384477600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\win32\glw_win.h	2026-04-16 20:02:20.004528500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -26,38 +26,24 @@
 #ifndef __GLW_WIN_H__
 #define __GLW_WIN_H__
 
-#include <windows.h>
-
 typedef struct
 {
+	WNDPROC		wndproc;
+
 	HDC     hDC;			// handle to device context
 	HGLRC   hGLRC;			// handle to GL rendering context
 
-	HINSTANCE   OpenGLLib;  // HINSTANCE for the OpenGL library
-	HINSTANCE   VulkanLib;  // HINSTANCE for the Vulkan library
+	HINSTANCE hinstOpenGL;	// HINSTANCE for the OpenGL library
 
-	qboolean	pixelFormatSet;
+	qboolean allowdisplaydepthchange;
+	qboolean pixelFormatSet;
 
-	int			desktopBitsPixel;
-	int			desktopWidth; 
-	int			desktopHeight;
-	int			desktopX;		// can be negative
-	int			desktopY;		// can be negative
-
-	RECT		workArea;
-
-	HMONITOR	hMonitor;		// current monitor
-	TCHAR		displayName[CCHDEVICENAME];
-	qboolean	deviceSupportsGamma;
-	qboolean	gammaSet;
+	int		 desktopBitsPixel;
+	int		 desktopWidth, desktopHeight;
 
 	qboolean	cdsFullscreen;
-	int			monitorCount;
-
-	FILE		*log_fp;	// TODO: implement?
-
-	glconfig_t	*config;	// feedback to renderer module
 
+	FILE *log_fp;
 } glwstate_t;
 
 extern glwstate_t glw_state;

```
