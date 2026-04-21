# Diff: `code/qcommon/vm_sparc.c`
**Canonical:** `wolfcamql-src` (sha256 `3268f90943fd...`, 46405 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `4e34d08e9455...`, 45256 bytes

_Diff stat: +1 / -78 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_sparc.c	2026-04-16 20:02:25.231263800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\vm_sparc.c	2026-04-16 22:48:25.916365000 +0100
@@ -20,8 +20,6 @@
 ===========================================================================
 */
 
-#if defined(__sparc) || defined(__sparc__)
-
 /* This code is based almost entirely upon the vm_powerpc.c code by
  * Przemyslaw Iskra.  All I did was make it work on Sparc :-) -DaveM
  */
@@ -33,80 +31,7 @@
 #include <stddef.h>
 
 #include "vm_local.h"
-
-/* integer regs */
-#define G0	0
-#define G1	1
-#define G2	2
-#define G3	3
-#define G4	4
-#define G5	5
-#define G6	6
-#define G7	7
-#define O0	8
-#define O1	9
-#define O2	10
-#define O3	11
-#define O4	12
-#define O5	13
-#define O6	14
-#define O7	15
-#define L0	16
-#define L1	17
-#define L2	18
-#define L3	19
-#define L4	20
-#define L5	21
-#define L6	22
-#define L7	23
-#define I0	24
-#define I1	25
-#define I2	26
-#define I3	27
-#define I4	28
-#define I5	29
-#define I6	30
-#define I7	31
-
-/* float regs */
-#define F0	0
-#define F1	1
-#define F2	2
-#define F3	3
-#define F4	4
-#define F5	5
-#define F6	6
-#define F7	7
-#define F8	8
-#define F9	9
-#define F10	10
-#define F11	11
-#define F12	12
-#define F13	13
-#define F14	14
-#define F15	15
-#define F16	16
-#define F17	17
-#define F18	18
-#define F19	19
-#define F20	20
-#define F21	21
-#define F22	22
-#define F23	23
-#define F24	24
-#define F25	25
-#define F26	26
-#define F27	27
-#define F28	28
-#define F29	29
-#define F30	30
-#define F31	31
-
-/* state registers */
-#define Y_REG		0
-#define CCR_REG		2
-#define ASI_REG		3
-#define FPRS_REG	6
+#include "vm_sparc.h"
 
 /* exit() won't be called but use it because it is marked with noreturn */
 #define DIE( reason ) \
@@ -1743,5 +1668,3 @@
 
 	return retVal;
 }
-
-#endif // sparc

```
