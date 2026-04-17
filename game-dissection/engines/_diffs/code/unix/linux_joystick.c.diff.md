# Diff: `code/unix/linux_joystick.c`
**Canonical:** `quake3e` (sha256 `1218e004b427...`, 5339 bytes)

## Variants

### `quake3-source`  — sha256 `0549509b6280...`, 5285 bytes

_Diff stat: +8 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\unix\linux_joystick.c	2026-04-16 20:02:27.371122200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\unix\linux_joystick.c	2026-04-16 20:02:19.996529900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,8 +30,6 @@
 **
 */
 
-#ifdef USE_JOYSTICK
-
 #include <linux/joystick.h>
 #include <sys/types.h>
 #include <fcntl.h>
@@ -76,7 +74,7 @@
   joy_fd = -1;
 
   if( !in_joystick->integer ) {
-    Com_DPrintf( "Joystick is not active.\n" );
+    Com_Printf( "Joystick is not active.\n" );
     return;
   }
 
@@ -94,7 +92,7 @@
       char name[128];
       int n = -1;
 
-      Com_DPrintf( "Joystick %s found\n", filename );
+      Com_Printf( "Joystick %s found\n", filename );
 
       /* Get rid of initialization messages. */
       do {
@@ -114,9 +112,9 @@
 	strncpy( name, "Unknown", sizeof( name ) );
       }
 
-      Com_DPrintf( "Name:    %s\n", name );
-      Com_DPrintf( "Axes:    %d\n", axes );
-      Com_DPrintf( "Buttons: %d\n", buttons );
+      Com_Printf( "Name:    %s\n", name );
+      Com_Printf( "Axes:    %d\n", axes );
+      Com_Printf( "Buttons: %d\n", buttons );
 
       /* Our work here is done. */
       return;
@@ -126,7 +124,7 @@
 
   /* No soup for you. */
   if( joy_fd == -1 ) {
-    Com_DPrintf( "No joystick found.\n" );
+    Com_Printf( "No joystick found.\n" );
     return;
   }
 
@@ -206,4 +204,4 @@
   old_axes = axes;
 }
 
-#endif
\ No newline at end of file
+

```
