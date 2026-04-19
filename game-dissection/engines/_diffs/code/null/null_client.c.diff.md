# Diff: `code/null/null_client.c`
**Canonical:** `wolfcamql-src` (sha256 `d68e430d8f77...`, 2316 bytes)

## Variants

### `quake3-source`  — sha256 `110b59442d67...`, 2189 bytes

_Diff stat: +11 / -22 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_client.c	2026-04-16 20:02:25.202155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_client.c	2026-04-16 20:02:19.940311700 +0100
@@ -15,31 +15,29 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
+#include "../client/client.h"
 
 cvar_t *cl_shownet;
 
-void CL_Shutdown(char *finalmsg, qboolean disconnect, qboolean quit)
-{
+void CL_Shutdown( void ) {
 }
 
 void CL_Init( void ) {
 	cl_shownet = Cvar_Get ("cl_shownet", "0", CVAR_TEMP );
 }
 
-void CL_MouseEvent( int dx, int dy, int time, qboolean active ) {
+void CL_MouseEvent( int dx, int dy, int time ) {
 }
 
 void Key_WriteBindings( fileHandle_t f ) {
 }
 
-void CL_Frame (int msec, double fmsec) {
+void CL_Frame ( int msec ) {
 }
 
 void CL_PacketEvent( netadr_t from, msg_t *msg ) {
@@ -55,7 +53,7 @@
 }
 
 qboolean CL_GameCommand( void ) {
-  return qfalse;
+  return qfalse; // bk001204 - non-void
 }
 
 void CL_KeyEvent (int key, qboolean down, unsigned time) {
@@ -80,23 +78,14 @@
 void CL_CDDialog( void ) {
 }
 
-void CL_FlushMemory(void)
-{
+void CL_FlushMemory( void ) {
 }
 
-void CL_ShutdownAll(qboolean shutdownRef)
-{
+void CL_StartHunkUsers( void ) {
 }
 
-void CL_StartHunkUsers( qboolean rendererOnly ) {
-}
-
-void CL_InitRef(void)
-{
-}
-
-void CL_Snd_Shutdown(void)
-{
-}
+// bk001119 - added new dummy for sv_init.c
+void CL_ShutdownAll(void) {};
 
+// bk001208 - added new dummy (RC4)
 qboolean CL_CDKeyValidate( const char *key, const char *checksum ) { return qtrue; }

```

### `openarena-engine`  — sha256 `30f7f5d4fe48...`, 2287 bytes
Also identical in: ioquake3

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_client.c	2026-04-16 20:02:25.202155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_client.c	2026-04-16 22:48:25.834145700 +0100
@@ -33,13 +33,13 @@
 	cl_shownet = Cvar_Get ("cl_shownet", "0", CVAR_TEMP );
 }
 
-void CL_MouseEvent( int dx, int dy, int time, qboolean active ) {
+void CL_MouseEvent( int dx, int dy, int time ) {
 }
 
 void Key_WriteBindings( fileHandle_t f ) {
 }
 
-void CL_Frame (int msec, double fmsec) {
+void CL_Frame ( int msec ) {
 }
 
 void CL_PacketEvent( netadr_t from, msg_t *msg ) {

```
