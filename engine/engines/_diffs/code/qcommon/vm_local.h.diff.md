# Diff: `code/qcommon/vm_local.h`
**Canonical:** `wolfcamql-src` (sha256 `f78a3725cd88...`, 4363 bytes)

## Variants

### `quake3-source`  — sha256 `abd41bbce534...`, 3563 bytes

_Diff stat: +10 / -33 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_local.h	2026-04-16 20:02:25.229261200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\vm_local.h	2026-04-16 20:02:19.964114200 +0100
@@ -15,31 +15,13 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-#include "q_shared.h"
+#include "../game/q_shared.h"
 #include "qcommon.h"
 
-// Max number of arguments to pass from engine to vm's vmMain function.
-// command number + 12 arguments
-#define MAX_VMMAIN_ARGS 13
-
-// Max number of arguments to pass from a vm to engine's syscall handler function for the vm.
-// syscall number + 15 arguments
-#define MAX_VMSYSCALL_ARGS 16
-
-// don't change, this is hardcoded into x86 VMs, opStack protection relies
-// on this
-#define	OPSTACK_SIZE	1024
-#define	OPSTACK_MASK	(OPSTACK_SIZE-1)
-
-// don't change
-// Hardcoded in q3asm a reserved at end of bss
-#define	PROGRAM_STACK_SIZE	0x10000
-#define	PROGRAM_STACK_MASK	(PROGRAM_STACK_SIZE-1)
-
 typedef enum {
 	OP_UNDEF, 
 
@@ -145,44 +127,40 @@
     // DO NOT MOVE OR CHANGE THESE WITHOUT CHANGING THE VM_OFFSET_* DEFINES
     // USED BY THE ASM CODE
     int			programStack;		// the vm may be recursively entered
-    intptr_t			(*systemCall)( intptr_t *parms );
+    int			(*systemCall)( int *parms );
 
 	//------------------------------------
    
-	char		name[MAX_QPATH];
-	void		*searchPath;				// hint for FS_ReadFileDir()
+    char		name[MAX_QPATH];
 
 	// for dynamic linked modules
 	void		*dllHandle;
-	vmMainProc	entryPoint;
-	void (*destroy)(vm_t* self);
+	int			(QDECL *entryPoint)( int callNum, ... );
 
 	// for interpreted modules
 	qboolean	currentlyInterpreting;
 
 	qboolean	compiled;
 	byte		*codeBase;
-	int			entryOfs;
 	int			codeLength;
 
-	intptr_t	*instructionPointers;
-	int			instructionCount;
+	int			*instructionPointers;
+	int			instructionPointersLength;
 
 	byte		*dataBase;
 	int			dataMask;
-	int			dataAlloc;			// actually allocated
 
 	int			stackBottom;		// if programStack < stackBottom, error
 
 	int			numSymbols;
 	struct vmSymbol_s	*symbols;
 
-	int			callLevel;		// counts recursive VM_Call
+	int			callLevel;			// for debug indenting
 	int			breakFunction;		// increment breakCount on function entry to this
 	int			breakCount;
 
-	byte		*jumpTableTargets;
-	int			numJumpTableTargets;
+// fqpath member added 7/20/02 by T.Ray
+	char		fqpath[MAX_QPATH+1] ;
 };
 
 
@@ -200,4 +178,3 @@
 const char *VM_ValueToSymbol( vm_t *vm, int value );
 void VM_LogSyscalls( int *args );
 
-void VM_BlockCopy(unsigned int dest, unsigned int src, size_t n);

```

### `ioquake3`  — sha256 `28446f80393f...`, 4362 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_local.h	2026-04-16 20:02:25.229261200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\vm_local.h	2026-04-16 20:02:21.573103800 +0100
@@ -150,7 +150,7 @@
 	//------------------------------------
    
 	char		name[MAX_QPATH];
-	void		*searchPath;				// hint for FS_ReadFileDir()
+	void	*searchPath;				// hint for FS_ReadFileDir()
 
 	// for dynamic linked modules
 	void		*dllHandle;

```

### `quake3e`  — sha256 `b5a9f7a19ab9...`, 5836 bytes

_Diff stat: +108 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_local.h	2026-04-16 20:02:25.229261200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\vm_local.h	2026-04-16 20:02:27.310462600 +0100
@@ -19,31 +19,42 @@
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
+#ifndef VM_LOCAL_H
+#define VM_LOCAL_H
+
 #include "q_shared.h"
 #include "qcommon.h"
 
-// Max number of arguments to pass from engine to vm's vmMain function.
-// command number + 12 arguments
-#define MAX_VMMAIN_ARGS 13
-
-// Max number of arguments to pass from a vm to engine's syscall handler function for the vm.
-// syscall number + 15 arguments
-#define MAX_VMSYSCALL_ARGS 16
-
-// don't change, this is hardcoded into x86 VMs, opStack protection relies
-// on this
-#define	OPSTACK_SIZE	1024
-#define	OPSTACK_MASK	(OPSTACK_SIZE-1)
+#define	MAX_OPSTACK_SIZE	512
+#define	PROC_OPSTACK_SIZE	30
 
 // don't change
-// Hardcoded in q3asm a reserved at end of bss
+// Hardcoded in q3asm an reserved at end of bss
 #define	PROGRAM_STACK_SIZE	0x10000
-#define	PROGRAM_STACK_MASK	(PROGRAM_STACK_SIZE-1)
+
+// for some buggy mods
+#define	PROGRAM_STACK_EXTRA	(32*1024)
+
+// reserved space for effective LOCAL+LOAD* checks
+// also to avoid runtime range checks for many small arguments/structs in systemcalls
+#define	VM_DATA_GUARD_SIZE	1024
+
+// guard size must cover at least function arguments area
+#if VM_DATA_GUARD_SIZE < 256
+#undef VM_DATA_GUARD_SIZE
+#define VM_DATA_GUARD_SIZE 256
+#endif
+
+// flags for vm_rtChecks cvar
+#define VM_RTCHECK_PSTACK  1
+#define VM_RTCHECK_OPSTACK 2
+#define VM_RTCHECK_JUMP    4
+#define VM_RTCHECK_DATA    8
 
 typedef enum {
-	OP_UNDEF, 
+	OP_UNDEF,
 
-	OP_IGNORE, 
+	OP_IGNORE,
 
 	OP_BREAK,
 
@@ -124,12 +135,22 @@
 	OP_MULF,
 
 	OP_CVIF,
-	OP_CVFI
-} opcode_t;
-
+	OP_CVFI,
 
+	OP_MAX
+} opcode_t;
 
-typedef int	vmptr_t;
+typedef struct {
+	int32_t	value;     // 32
+	byte	op;        // 8
+	byte	opStack;   // 8
+	unsigned jused:1;  // this instruction is a jump target
+	unsigned swtch:1;  // indirect jump
+	unsigned safe:1;   // non-masked OP_STORE*
+	unsigned endp:1;   // for last OP_LEAVE instruction
+	unsigned fpu:1;    // load into FPU register
+	unsigned njump:1;  // near jump
+} instruction_t;
 
 typedef struct vmSymbol_s {
 	struct vmSymbol_s	*next;
@@ -138,66 +159,101 @@
 	char	symName[1];		// variable sized
 } vmSymbol_t;
 
-#define	VM_OFFSET_PROGRAM_STACK		0
-#define	VM_OFFSET_SYSTEM_CALL		4
+//typedef void(*vmfunc_t)(void);
+
+typedef union vmFunc_u {
+	byte		*ptr;
+	void (*func)(void);
+} vmFunc_t;
 
 struct vm_s {
-    // DO NOT MOVE OR CHANGE THESE WITHOUT CHANGING THE VM_OFFSET_* DEFINES
-    // USED BY THE ASM CODE
-    int			programStack;		// the vm may be recursively entered
-    intptr_t			(*systemCall)( intptr_t *parms );
+
+	syscall_t	systemCall;
+	byte		*dataBase;
+	int32_t		*opStack;			// pointer to local function stack
+	int32_t		*opStackTop;
+
+	int32_t		programStack;		// the vm may be recursively entered
+	int32_t		stackBottom;		// if programStack < stackBottom, error
 
 	//------------------------------------
-   
-	char		name[MAX_QPATH];
-	void		*searchPath;				// hint for FS_ReadFileDir()
+
+	const char	*name;				// module should be bare: "cgame", not "cgame.dll" or "vm/cgame.qvm"
+	vmIndex_t	index;
 
 	// for dynamic linked modules
 	void		*dllHandle;
-	vmMainProc	entryPoint;
+	vmMainFunc_t entryPoint;
+	dllSyscall_t dllSyscall;
 	void (*destroy)(vm_t* self);
 
 	// for interpreted modules
-	qboolean	currentlyInterpreting;
+	//qboolean	currentlyInterpreting;
 
 	qboolean	compiled;
-	byte		*codeBase;
-	int			entryOfs;
-	int			codeLength;
 
-	intptr_t	*instructionPointers;
-	int			instructionCount;
+	vmFunc_t	codeBase;
+	unsigned int codeSize;			// code + jump targets, needed for proper munmap()
+	unsigned int codeLength;		// just for information
 
-	byte		*dataBase;
-	int			dataMask;
-	int			dataAlloc;			// actually allocated
+	int32_t		instructionCount;
+	intptr_t	*instructionPointers;
 
-	int			stackBottom;		// if programStack < stackBottom, error
+	uint32_t	dataMask;
+	uint32_t	dataLength;			// data segment length
+	uint32_t	exactDataLength;	// from qvm header
+	uint32_t	dataAlloc;			// actually allocated, for mmap()/munmap()
+	uint32_t	programStackExtra;
 
 	int			numSymbols;
-	struct vmSymbol_s	*symbols;
+	vmSymbol_t	*symbols;
 
-	int			callLevel;		// counts recursive VM_Call
+	int			callLevel;			// counts recursive VM_Call
 	int			breakFunction;		// increment breakCount on function entry to this
 	int			breakCount;
 
-	byte		*jumpTableTargets;
-	int			numJumpTableTargets;
-};
+	int			syscallCount;		// syscall counter for current VM_Call invocation
 
+	int32_t		*jumpTableTargets;
+	int32_t		numJumpTableTargets;
 
-extern	vm_t	*currentVM;
-extern	int		vm_debugLevel;
+	uint32_t	crc32sum;
 
-void VM_Compile( vm_t *vm, vmHeader_t *header );
-int	VM_CallCompiled( vm_t *vm, int *args );
+	qboolean	forceDataMask;
 
-void VM_PrepareInterpreter( vm_t *vm, vmHeader_t *header );
-int	VM_CallInterpreted( vm_t *vm, int *args );
+	int			privateFlag;
+};
+
+qboolean VM_Compile( vm_t *vm, vmHeader_t *header );
+int32_t VM_CallCompiled( vm_t *vm, int nargs, int32_t *args );
+
+qboolean VM_PrepareInterpreter2( vm_t *vm, vmHeader_t *header );
+int32_t VM_CallInterpreted2( vm_t *vm, int nargs, int32_t *args );
 
 vmSymbol_t *VM_ValueToFunctionSymbol( vm_t *vm, int value );
 int VM_SymbolToValue( vm_t *vm, const char *symbol );
 const char *VM_ValueToSymbol( vm_t *vm, int value );
 void VM_LogSyscalls( int *args );
 
-void VM_BlockCopy(unsigned int dest, unsigned int src, size_t n);
+const char *VM_LoadInstructions( const byte *code_pos, int codeLength, int instructionCount, instruction_t *buf );
+const char *VM_CheckInstructions( instruction_t *buf, int instructionCount,
+								 const int32_t *jumpTableTargets,
+								 int numJumpTableTargets,
+								 int dataLength );
+
+void VM_ReplaceInstructions( vm_t *vm, instruction_t *buf );
+
+#define JUMP	(1<<0)
+#define FPU		(1<<1)
+
+typedef struct opcode_info_s
+{
+	int	size;
+	int	stack;
+	int	nargs;
+	int	flags;
+} opcode_info_t;
+
+extern opcode_info_t ops[ OP_MAX ];
+
+#endif // VM_LOCAL_H

```

### `openarena-engine`  — sha256 `42f13b932439...`, 4348 bytes

_Diff stat: +2 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_local.h	2026-04-16 20:02:25.229261200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\vm_local.h	2026-04-16 22:48:25.914363000 +0100
@@ -150,11 +150,11 @@
 	//------------------------------------
    
 	char		name[MAX_QPATH];
-	void		*searchPath;				// hint for FS_ReadFileDir()
+	void	*searchPath;				// hint for FS_ReadFileDir()
 
 	// for dynamic linked modules
 	void		*dllHandle;
-	vmMainProc	entryPoint;
+	intptr_t			(QDECL *entryPoint)( int callNum, ... );
 	void (*destroy)(vm_t* self);
 
 	// for interpreted modules
@@ -170,7 +170,6 @@
 
 	byte		*dataBase;
 	int			dataMask;
-	int			dataAlloc;			// actually allocated
 
 	int			stackBottom;		// if programStack < stackBottom, error
 

```
