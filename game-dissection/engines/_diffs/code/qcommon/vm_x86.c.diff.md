# Diff: `code/qcommon/vm_x86.c`
**Canonical:** `wolfcamql-src` (sha256 `5caa6ddfc958...`, 47006 bytes)

## Variants

### `quake3-source`  — sha256 `e352601efc2d...`, 36557 bytes

_Diff stat: +825 / -1441 lines_

_(full diff is 76733 bytes — see files directly)_

### `ioquake3`  — sha256 `1920506376a4...`, 47005 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_x86.c	2026-04-16 20:02:25.231263800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\vm_x86.c	2026-04-16 20:02:21.574609800 +0100
@@ -389,7 +389,7 @@
 =================
 */
 
-static void Q_NO_RETURN  ErrJump(void)
+static void Q_NO_RETURN ErrJump(void)
 { 
 	Com_Error(ERR_DROP, "program tried to execute code outside VM");
 }

```

### `quake3e`  — sha256 `a8a82a5f19c6...`, 99564 bytes

_Diff stat: +3385 / -1429 lines_

_(full diff is 143319 bytes — see files directly)_

### `openarena-engine`  — sha256 `1a21270ff189...`, 46750 bytes

_Diff stat: +17 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_x86.c	2026-04-16 20:02:25.231263800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\vm_x86.c	2026-04-16 22:48:25.917364500 +0100
@@ -21,8 +21,6 @@
 */
 // vm_x86.c -- load time compiler and execution environment for x86
 
-#if defined (__i386__) || defined(__x86_64__) || defined(_M_IX86) || defined(_M_X64)
-
 #include "vm_local.h"
 
 #ifdef _WIN32
@@ -105,7 +103,7 @@
 
 static int NextConstant4(void)
 {
-	return ((unsigned int)code[pc] | ((unsigned int)code[pc+1]<<8) | ((unsigned int)code[pc+2]<<16) | ((unsigned int)code[pc+3]<<24));
+	return (code[pc] | (code[pc+1]<<8) | (code[pc+2]<<16) | (code[pc+3]<<24));
 }
 
 static int	Constant4( void ) {
@@ -205,25 +203,19 @@
 
 
 #define MASK_REG(modrm, mask) \
-	do { \
-		EmitString("81"); \
-		EmitString((modrm)); \
-		Emit4((mask)); \
-	} while(0)
+	EmitString("81"); \
+	EmitString((modrm)); \
+	Emit4((mask))
 
 // add bl, bytes
 #define STACK_PUSH(bytes) \
-	do { \
-		EmitString("80 C3"); \
-		Emit1(bytes); \
-	} while(0)
+	EmitString("80 C3"); \
+	Emit1(bytes)
 
 // sub bl, bytes
 #define STACK_POP(bytes) \
-	do { \
-		EmitString("80 EB"); \
-		Emit1(bytes); \
-	} while(0)
+	EmitString("80 EB"); \
+	Emit1(bytes)
 
 static void EmitCommand(ELastCommand command)
 {
@@ -389,7 +381,7 @@
 =================
 */
 
-static void Q_NO_RETURN  ErrJump(void)
+static void __attribute__((__noreturn__)) ErrJump(void)
 { 
 	Com_Error(ERR_DROP, "program tried to execute code outside VM");
 }
@@ -420,24 +412,23 @@
 
 	if(vm_syscallNum < 0)
 	{
-		int *data, *ret;
+		int *data;
 #if idx64
 		int index;
 		intptr_t args[MAX_VMSYSCALL_ARGS];
 #endif
 		
 		data = (int *) (savedVM->dataBase + vm_programStack + 4);
-		ret = &vm_opStackBase[vm_opStackOfs + 1];
 
 #if idx64
 		args[0] = ~vm_syscallNum;
 		for(index = 1; index < ARRAY_LEN(args); index++)
 			args[index] = data[index];
 			
-		*ret = savedVM->systemCall(args);
+		vm_opStackBase[vm_opStackOfs + 1] = savedVM->systemCall(args);
 #else
 		data[0] = ~vm_syscallNum;
-		*ret = savedVM->systemCall((intptr_t *) data);
+		vm_opStackBase[vm_opStackOfs + 1] = savedVM->systemCall((intptr_t *) data);
 #endif
 	}
 	else
@@ -792,7 +783,7 @@
 		return qtrue;
 
 	case OP_STORE4:
-		EmitMovEAXStack(vm, vm->dataMask);
+		EmitMovEAXStack(vm, (vm->dataMask & ~3));
 #if idx64
 		EmitRexString(0x41, "C7 04 01");		// mov dword ptr [r9 + eax], 0x12345678
 		Emit4(Constant4());
@@ -807,7 +798,7 @@
 		return qtrue;
 
 	case OP_STORE2:
-		EmitMovEAXStack(vm, vm->dataMask);
+		EmitMovEAXStack(vm, (vm->dataMask & ~1));
 #if idx64
 		Emit1(0x66);					// mov word ptr [r9 + eax], 0x1234
 		EmitRexString(0x41, "C7 04 01");
@@ -1096,9 +1087,8 @@
 
 	// ensure that the optimisation pass knows about all the jump
 	// table targets
-	pc = -1; // a bogus value to be printed in out-of-bounds error messages
 	for( i = 0; i < vm->numJumpTableTargets; i++ ) {
-		JUSED( *(int *)(vm->jumpTableTargets + ( i * sizeof( int ) ) ) );
+		jused[ *(int *)(vm->jumpTableTargets + ( i * sizeof( int ) ) ) ] = 1;
 	}
 
 	// Start buffer with x86-VM specific procedures
@@ -1379,7 +1369,7 @@
 		case OP_STORE4:
 			EmitMovEAXStack(vm, 0);	
 			EmitString("8B 54 9F FC");			// mov edx, dword ptr -4[edi + ebx * 4]
-			MASK_REG("E2", vm->dataMask);		// and edx, 0x12345678
+			MASK_REG("E2", vm->dataMask & ~3);		// and edx, 0x12345678
 #if idx64
 			EmitRexString(0x41, "89 04 11");		// mov dword ptr [r9 + edx], eax
 #else
@@ -1391,7 +1381,7 @@
 		case OP_STORE2:
 			EmitMovEAXStack(vm, 0);	
 			EmitString("8B 54 9F FC");			// mov edx, dword ptr -4[edi + ebx * 4]
-			MASK_REG("E2", vm->dataMask);		// and edx, 0x12345678
+			MASK_REG("E2", vm->dataMask & ~1);		// and edx, 0x12345678
 #if idx64
 			Emit1(0x66);					// mov word ptr [r9 + edx], eax
 			EmitRexString(0x41, "89 04 11");
@@ -1809,4 +1799,3 @@
 
 	return opStack[opStackOfs];
 }
-#endif

```
