# Diff: `code/qcommon/vm_interpreted.c`
**Canonical:** `wolfcamql-src` (sha256 `9e5ab71b07bf...`, 22041 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `e6c52d25540e...`, 20409 bytes

_Diff stat: +241 / -253 lines_

_(full diff is 24815 bytes — see files directly)_

### `quake3e`  — sha256 `4d42fae65645...`, 13308 bytes

_Diff stat: +402 / -688 lines_

_(full diff is 30397 bytes — see files directly)_

### `openarena-engine`  — sha256 `4ff085318d05...`, 22071 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_interpreted.c	2026-04-16 20:02:25.229261200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\vm_interpreted.c	2026-04-16 22:48:25.914363000 +0100
@@ -317,8 +317,8 @@
 
 int	VM_CallInterpreted( vm_t *vm, int *args ) {
 	byte		stack[OPSTACK_SIZE + 15];
-	int		*opStack;
-	uint8_t 	opStackOfs;
+	register int		*opStack;
+	register uint8_t 	opStackOfs;
 	int		programCounter;
 	int		programStack;
 	int		stackOnEntry;
@@ -436,31 +436,31 @@
 				return 0;
 			}
 #endif
-			r0 = opStack[opStackOfs] = *(int *) &image[ r0 & dataMask ];
+			r0 = opStack[opStackOfs] = *(int *) &image[r0 & dataMask & ~3 ];
 			goto nextInstruction2;
 		case OP_LOAD2:
-			r0 = opStack[opStackOfs] = *(unsigned short *)&image[ r0 & dataMask ];
+			r0 = opStack[opStackOfs] = *(unsigned short *)&image[ r0&dataMask&~1 ];
 			goto nextInstruction2;
 		case OP_LOAD1:
-			r0 = opStack[opStackOfs] = image[ r0 & dataMask ];
+			r0 = opStack[opStackOfs] = image[ r0&dataMask ];
 			goto nextInstruction2;
 
 		case OP_STORE4:
-			*(int *)&image[ r1 & dataMask ] = r0;
+			*(int *)&image[ r1&(dataMask & ~3) ] = r0;
 			opStackOfs -= 2;
 			goto nextInstruction;
 		case OP_STORE2:
-			*(short *)&image[ r1 & dataMask ] = r0;
+			*(short *)&image[ r1&(dataMask & ~1) ] = r0;
 			opStackOfs -= 2;
 			goto nextInstruction;
 		case OP_STORE1:
-			image[ r1 & dataMask ] = r0;
+			image[ r1&dataMask ] = r0;
 			opStackOfs -= 2;
 			goto nextInstruction;
 
 		case OP_ARG:
 			// single byte offset from programStack
-			*(int *)&image[ (codeImage[programCounter] + programStack) & dataMask ] = r0;
+			*(int *)&image[ (codeImage[programCounter] + programStack)&dataMask&~3 ] = r0;
 			opStackOfs--;
 			programCounter += 1;
 			goto nextInstruction;

```
