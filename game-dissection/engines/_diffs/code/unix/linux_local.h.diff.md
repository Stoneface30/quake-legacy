# Diff: `code/unix/linux_local.h`
**Canonical:** `quake3e` (sha256 `88489c1034f2...`, 1566 bytes)

## Variants

### `quake3-source`  — sha256 `9be8b91deb70...`, 1648 bytes

_Diff stat: +9 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\unix\linux_local.h	2026-04-16 20:02:27.371644000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\unix\linux_local.h	2026-04-16 20:02:19.996529900 +0100
@@ -15,12 +15,15 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-#ifndef __LINUX_LOCAL_H__
-#define __LINUX_LOCAL_H__
+// linux_local.h: Linux-specific Quake3 header file
+
+void Sys_QueEvent( int time, sysEventType_t type, int value, int value2, int ptrLength, void *ptr );
+qboolean Sys_GetPacket ( netadr_t *net_from, msg_t *net_message );
+void Sys_SendKeyEvents (void);
 
 // Input subsystem
 
@@ -32,14 +35,10 @@
 void IN_JoyMove( void );
 void IN_StartupJoystick( void );
 
-// OpenGL subsystem
+// GL subsystem
 qboolean QGL_Init( const char *dllname );
-void QGL_Shutdown( qboolean unloadDLL );
-
-// Vulkan subsystem
-qboolean QVK_Init( void );
-void QVK_Shutdown( qboolean unloadDLL );
-
+void QGL_EnableLogging( qboolean enable );
+void QGL_Shutdown( void );
 
 // bk001130 - win32
 // void IN_JoystickCommands (void);
@@ -48,5 +47,3 @@
 
 // signals.c
 void InitSig(void);
-
-#endif // __LINUX_LOCAL_H__

```
