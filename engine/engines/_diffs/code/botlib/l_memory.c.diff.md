# Diff: `code/botlib/l_memory.c`
**Canonical:** `wolfcamql-src` (sha256 `6e4df999558c...`, 14049 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `7bc2bc2444ab...`, 14037 bytes

_Diff stat: +4 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_memory.c	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_memory.c	2026-04-16 20:02:19.855902700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,10 +29,9 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
-#include "botlib.h"
+#include "../game/q_shared.h"
+#include "../game/botlib.h"
 #include "l_log.h"
-#include "l_memory.h"
 #include "be_interface.h"
 
 //#define MEMDEBUG
@@ -101,7 +100,7 @@
 {
 	void *ptr;
 	memoryblock_t *block;
-	assert(botimport.GetMemory);
+  assert(botimport.GetMemory); // bk001129 - was NULL'ed
 	ptr = botimport.GetMemory(size + sizeof(memoryblock_t));
 	block = (memoryblock_t *) ptr;
 	block->id = MEM_ID;

```

### `quake3e`  — sha256 `a67c97983d71...`, 14086 bytes

_Diff stat: +68 / -61 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_memory.c	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_memory.c	2026-04-16 20:02:26.905505600 +0100
@@ -36,31 +36,31 @@
 #include "be_interface.h"
 
 //#define MEMDEBUG
-//#define MEMORYMANEGER
+//#define MEMORYMANAGER
 
-#define MEM_ID		0x12345678l
-#define HUNK_ID		0x87654321l
+#define MEM_ID		0x12345678
+#define HUNK_ID		0x87654321
 
-int allocatedmemory;
-int totalmemorysize;
-int numblocks;
+#ifdef MEMORYMANAGER
 
-#ifdef MEMORYMANEGER
+static size_t allocatedmemory;
+static size_t totalmemorysize;
+static size_t numblocks;
 
 typedef struct memoryblock_s
 {
-	unsigned long int id;
+	uintptr_t id;
 	void *ptr;
-	int size;
+	size_t size;
 #ifdef MEMDEBUG
-	char *label;
-	char *file;
+	const char *label;
+	const char *file;
 	int line;
 #endif //MEMDEBUG
 	struct memoryblock_s *prev, *next;
 } memoryblock_t;
 
-memoryblock_t *memory;
+static memoryblock_t *memory;
 
 //===========================================================================
 //
@@ -68,7 +68,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void LinkMemoryBlock(memoryblock_t *block)
+static void LinkMemoryBlock(memoryblock_t *block)
 {
 	block->prev = NULL;
 	block->next = memory;
@@ -81,7 +81,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void UnlinkMemoryBlock(memoryblock_t *block)
+static void UnlinkMemoryBlock(memoryblock_t *block)
 {
 	if (block->prev) block->prev->next = block->next;
 	else memory = block->next;
@@ -94,19 +94,20 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetMemory(unsigned long size)
+void *GetMemory(size_t size)
 #endif //MEMDEBUG
 {
-	void *ptr;
 	memoryblock_t *block;
-	assert(botimport.GetMemory);
-	ptr = botimport.GetMemory(size + sizeof(memoryblock_t));
-	block = (memoryblock_t *) ptr;
+
+	if (size > SIZE_MAX - sizeof(memoryblock_t))
+		botimport.Print(PRT_EXIT, "%s: bad size", __func__);
+
+	block = botimport.GetMemory(size + sizeof(memoryblock_t));
 	block->id = MEM_ID;
-	block->ptr = (char *) ptr + sizeof(memoryblock_t);
-	block->size = size + sizeof(memoryblock_t);
+	block->ptr = block + 1;
+	block->size = size;
 #ifdef MEMDEBUG
 	block->label = label;
 	block->file = file;
@@ -125,9 +126,9 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetClearedMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetClearedMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetClearedMemory(unsigned long size)
+void *GetClearedMemory(size_t size)
 #endif //MEMDEBUG
 {
 	void *ptr;
@@ -146,19 +147,20 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetHunkMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetHunkMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetHunkMemory(unsigned long size)
+void *GetHunkMemory(size_t size)
 #endif //MEMDEBUG
 {
-	void *ptr;
 	memoryblock_t *block;
 
-	ptr = botimport.HunkAlloc(size + sizeof(memoryblock_t));
-	block = (memoryblock_t *) ptr;
+	if (size > SIZE_MAX - sizeof(memoryblock_t))
+		botimport.Print(PRT_EXIT, "%s: bad size", __func__);
+
+	block = botimport.HunkAlloc(size + sizeof(memoryblock_t));
 	block->id = HUNK_ID;
-	block->ptr = (char *) ptr + sizeof(memoryblock_t);
-	block->size = size + sizeof(memoryblock_t);
+	block->ptr = block + 1;
+	block->size = size;
 #ifdef MEMDEBUG
 	block->label = label;
 	block->file = file;
@@ -177,9 +179,9 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetClearedHunkMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetClearedHunkMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetClearedHunkMemory(unsigned long size)
+void *GetClearedHunkMemory(size_t size)
 #endif //MEMDEBUG
 {
 	void *ptr;
@@ -197,7 +199,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-memoryblock_t *BlockFromPointer(void *ptr, char *str)
+static memoryblock_t *BlockFromPointer(void *ptr, char *str)
 {
 	memoryblock_t *block;
 
@@ -277,9 +279,9 @@
 //===========================================================================
 void PrintUsedMemorySize(void)
 {
-	botimport.Print(PRT_MESSAGE, "total allocated memory: %d KB\n", allocatedmemory >> 10);
-	botimport.Print(PRT_MESSAGE, "total botlib memory: %d KB\n", totalmemorysize >> 10);
-	botimport.Print(PRT_MESSAGE, "total memory blocks: %d\n", numblocks);
+	botimport.Print(PRT_MESSAGE, "total allocated memory: %"PRIz"u KB\n", allocatedmemory >> 10);
+	botimport.Print(PRT_MESSAGE, "total botlib memory: %"PRIz"u KB\n", totalmemorysize >> 10);
+	botimport.Print(PRT_MESSAGE, "total memory blocks: %"PRIz"u\n", numblocks);
 } //end of the function PrintUsedMemorySize
 //===========================================================================
 //
@@ -301,11 +303,11 @@
 #ifdef MEMDEBUG
 		if (block->id == HUNK_ID)
 		{
-			Log_Write("%6d, hunk %p, %8d: %24s line %6d: %s\r\n", i, block->ptr, block->size, block->file, block->line, block->label);
+			Log_Write("%6d, hunk %p, %8"PRIz"u: %24s line %6d: %s\r\n", i, block->ptr, block->size, block->file, block->line, block->label);
 		} //end if
 		else
 		{
-			Log_Write("%6d,      %p, %8d: %24s line %6d: %s\r\n", i, block->ptr, block->size, block->file, block->line, block->label);
+			Log_Write("%6d,      %p, %8"PRIz"u: %24s line %6d: %s\r\n", i, block->ptr, block->size, block->file, block->line, block->label);
 		} //end else
 #endif //MEMDEBUG
 		i++;
@@ -338,19 +340,19 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetMemory(unsigned long size)
+void *GetMemory(size_t size)
 #endif //MEMDEBUG
 {
-	void *ptr;
-	unsigned long int *memid;
+	uintptr_t *memid;
+
+	if (size > SIZE_MAX - sizeof(*memid))
+		botimport.Print(PRT_EXIT, "%s: bad size", __func__);
 
-	ptr = botimport.GetMemory(size + sizeof(unsigned long int));
-	if (!ptr) return NULL;
-	memid = (unsigned long int *) ptr;
+	memid = botimport.GetMemory(size + sizeof(*memid));
 	*memid = MEM_ID;
-	return (unsigned long int *) ((char *) ptr + sizeof(unsigned long int));
+	return memid + 1;
 } //end of the function GetMemory
 //===========================================================================
 //
@@ -359,9 +361,9 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetClearedMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetClearedMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetClearedMemory(unsigned long size)
+void *GetClearedMemory(size_t size)
 #endif //MEMDEBUG
 {
 	void *ptr;
@@ -380,19 +382,19 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetHunkMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetHunkMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetHunkMemory(unsigned long size)
+void *GetHunkMemory(size_t size)
 #endif //MEMDEBUG
 {
-	void *ptr;
-	unsigned long int *memid;
+	uintptr_t *memid;
 
-	ptr = botimport.HunkAlloc(size + sizeof(unsigned long int));
-	if (!ptr) return NULL;
-	memid = (unsigned long int *) ptr;
+	if (size > SIZE_MAX - sizeof(*memid))
+		botimport.Print(PRT_EXIT, "%s: bad size", __func__);
+
+	memid = botimport.HunkAlloc(size + sizeof(*memid));
 	*memid = HUNK_ID;
-	return (unsigned long int *) ((char *) ptr + sizeof(unsigned long int));
+	return memid + 1;
 } //end of the function GetHunkMemory
 //===========================================================================
 //
@@ -401,9 +403,9 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef MEMDEBUG
-void *GetClearedHunkMemoryDebug(unsigned long size, char *label, char *file, int line)
+void *GetClearedHunkMemoryDebug(size_t size, const char *label, const char *file, int line)
 #else
-void *GetClearedHunkMemory(unsigned long size)
+void *GetClearedHunkMemory(size_t size)
 #endif //MEMDEBUG
 {
 	void *ptr;
@@ -423,9 +425,14 @@
 //===========================================================================
 void FreeMemory(void *ptr)
 {
-	unsigned long int *memid;
+	uintptr_t *memid;
+
+	if (!ptr) {
+		botimport.Print(PRT_FATAL, "%s: NULL pointer\n", __func__);
+		return;
+	}
 
-	memid = (unsigned long int *) ((char *) ptr - sizeof(unsigned long int));
+	memid = (uintptr_t *) ((char *) ptr - sizeof(*memid));
 
 	if (*memid == MEM_ID)
 	{

```
