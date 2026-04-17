# Diff: `code/game/g_mem.c`
**Canonical:** `wolfcamql-src` (sha256 `ccab405df1f9...`, 1745 bytes)

## Variants

### `quake3-source`  — sha256 `44d12bf19239...`, 1741 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_mem.c	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_mem.c	2026-04-16 20:02:19.907572900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -28,7 +28,7 @@
 #include "g_local.h"
 
 
-#define POOLSIZE	(1024 * 1024 * 3)  //(256 * 1024)
+#define POOLSIZE	(256 * 1024)
 
 static char		memoryPool[POOLSIZE];
 static int		allocPoint;
@@ -41,7 +41,7 @@
 	}
 
 	if ( allocPoint + size > POOLSIZE ) {
-	  G_Error( "G_Alloc: failed on allocation of %i bytes", size );
+	  G_Error( "G_Alloc: failed on allocation of %i bytes\n", size ); // bk010103 - was %u, but is signed
 		return NULL;
 	}
 

```

### `openarena-engine`  — sha256 `aad3e65cda9f...`, 1724 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_mem.c	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_mem.c	2026-04-16 22:48:25.748537400 +0100
@@ -28,7 +28,7 @@
 #include "g_local.h"
 
 
-#define POOLSIZE	(1024 * 1024 * 3)  //(256 * 1024)
+#define POOLSIZE	(256 * 1024)
 
 static char		memoryPool[POOLSIZE];
 static int		allocPoint;

```
