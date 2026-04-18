# Diff: `code/null/null_snddma.c`
**Canonical:** `wolfcamql-src` (sha256 `0d373bbf9b66...`, 1806 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `687374941c39...`, 1543 bytes

_Diff stat: +3 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_snddma.c	2026-04-16 20:02:25.203156700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_snddma.c	2026-04-16 20:02:19.941310900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,8 +23,7 @@
 // snddma_null.c
 // all other sound mixing is portable
 
-#include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
+#include "../client/client.h"
 
 qboolean SNDDMA_Init(void)
 {
@@ -48,30 +47,7 @@
 {
 }
 
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void)
-{
-}
-
-int SNDDMA_AvailableCaptureSamples(void)
-{
-	return 0;
-}
-
-void SNDDMA_Capture(int samples, byte *data)
-{
-}
-
-void SNDDMA_StopCapture(void)
-{
-}
-
-void SNDDMA_MasterGain( float val )
-{
-}
-#endif
-
-
+// bk001119 - added boolean flag, match client/snd_public.h
 sfxHandle_t S_RegisterSound( const char *name, qboolean compressed ) 
 {
 	return 0;

```

### `openarena-engine`  — sha256 `93ac0a782c7a...`, 1539 bytes

_Diff stat: +0 / -24 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\null\null_snddma.c	2026-04-16 20:02:25.203156700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_snddma.c	2026-04-16 22:48:25.835145300 +0100
@@ -48,30 +48,6 @@
 {
 }
 
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void)
-{
-}
-
-int SNDDMA_AvailableCaptureSamples(void)
-{
-	return 0;
-}
-
-void SNDDMA_Capture(int samples, byte *data)
-{
-}
-
-void SNDDMA_StopCapture(void)
-{
-}
-
-void SNDDMA_MasterGain( float val )
-{
-}
-#endif
-
-
 sfxHandle_t S_RegisterSound( const char *name, qboolean compressed ) 
 {
 	return 0;

```
