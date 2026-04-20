# Diff: `lcc/src/bind.c`
**Canonical:** `quake3-source` (sha256 `5ab95994e158...`, 668 bytes)

## Variants

### `q3vm`  — sha256 `13a295bf9384...`, 197 bytes

_Diff stat: +3 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\bind.c	2026-04-16 20:02:20.079593000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\bind.c	2026-04-16 22:48:28.094134000 +0100
@@ -1,23 +1,8 @@
 #include "c.h"
-extern Interface alphaIR;
-extern Interface mipsebIR, mipselIR;
-extern Interface sparcIR, solarisIR;
-extern Interface x86IR, x86linuxIR;
-extern Interface symbolicIR, symbolic64IR;
 extern Interface nullIR;
 extern Interface bytecodeIR;
 Binding bindings[] = {
-	"alpha/osf",     &alphaIR,
-	"mips/irix",     &mipsebIR,
-	"mips/ultrix",   &mipselIR,
-	"sparc/sun",     &sparcIR,
-	"sparc/solaris", &solarisIR,
-	"x86/win32",	 &x86IR,
-	"x86/linux",	 &x86linuxIR,
-	"symbolic/osf",  &symbolic64IR,
-	"symbolic/irix", &symbolicIR,
-	"symbolic",      &symbolicIR,
-	"null",          &nullIR,
-	"bytecode",      &bytecodeIR,
-	NULL,            NULL
+	{ "null",          &nullIR },
+	{ "bytecode",      &bytecodeIR },
+	{ NULL,            NULL },
 };

```
