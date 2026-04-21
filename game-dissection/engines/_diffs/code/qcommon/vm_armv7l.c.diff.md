# Diff: `code/qcommon/vm_armv7l.c`
**Canonical:** `wolfcamql-src` (sha256 `69ad90c68109...`, 41373 bytes)

## Variants

### `ioquake3`  — sha256 `a8f8a14f611b...`, 41372 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm_armv7l.c	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\vm_armv7l.c	2026-04-16 20:02:21.572103800 +0100
@@ -217,7 +217,7 @@
 =================
 */
 
-static void Q_NO_RETURN  ErrJump(unsigned num)
+static void Q_NO_RETURN ErrJump(unsigned num)
 {
 	Com_Error(ERR_DROP, "program tried to execute code outside VM (%x)", num);
 }

```

### `quake3e`  — sha256 `a169f5d3cf10...`, 65677 bytes

_Diff stat: +1613 / -821 lines_

_(full diff is 88609 bytes — see files directly)_
