# Diff: `code/botlib/l_memory.h`
**Canonical:** `wolfcamql-src` (sha256 `73009e7822a8...`, 3108 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `c06031776cec...`, 3087 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_memory.h	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_memory.h	2026-04-16 20:02:19.856901200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `c1b84dec7e74...`, 3100 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_memory.h	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_memory.h	2026-04-16 20:02:26.905505600 +0100
@@ -35,30 +35,30 @@
 #define GetMemory(size)				GetMemoryDebug(size, #size, __FILE__, __LINE__);
 #define GetClearedMemory(size)		GetClearedMemoryDebug(size, #size, __FILE__, __LINE__);
 //allocate a memory block of the given size
-void *GetMemoryDebug(unsigned long size, char *label, char *file, int line);
+void *GetMemoryDebug(size_t size, const char *label, const char *file, int line);
 //allocate a memory block of the given size and clear it
-void *GetClearedMemoryDebug(unsigned long size, char *label, char *file, int line);
+void *GetClearedMemoryDebug(size_t size, const char *label, const char *file, int line);
 //
 #define GetHunkMemory(size)			GetHunkMemoryDebug(size, #size, __FILE__, __LINE__);
 #define GetClearedHunkMemory(size)	GetClearedHunkMemoryDebug(size, #size, __FILE__, __LINE__);
 //allocate a memory block of the given size
-void *GetHunkMemoryDebug(unsigned long size, char *label, char *file, int line);
+void *GetHunkMemoryDebug(size_t size, const char *label, const char *file, int line);
 //allocate a memory block of the given size and clear it
-void *GetClearedHunkMemoryDebug(unsigned long size, char *label, char *file, int line);
+void *GetClearedHunkMemoryDebug(size_t size, const char *label, const char *file, int line);
 #else
 //allocate a memory block of the given size
-void *GetMemory(unsigned long size);
+void *GetMemory(size_t size);
 //allocate a memory block of the given size and clear it
-void *GetClearedMemory(unsigned long size);
+void *GetClearedMemory(size_t size);
 //
 #ifdef BSPC
 #define GetHunkMemory GetMemory
 #define GetClearedHunkMemory GetClearedMemory
 #else
 //allocate a memory block of the given size
-void *GetHunkMemory(unsigned long size);
+void *GetHunkMemory(size_t size);
 //allocate a memory block of the given size and clear it
-void *GetClearedHunkMemory(unsigned long size);
+void *GetClearedHunkMemory(size_t size);
 #endif
 #endif
 

```
