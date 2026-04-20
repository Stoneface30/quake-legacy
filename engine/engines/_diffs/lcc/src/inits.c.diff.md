# Diff: `lcc/src/inits.c`
**Canonical:** `quake3-source` (sha256 `a22ea19c51dd...`, 442 bytes)

## Variants

### `q3vm`  — sha256 `5fa8cdf7ca5b...`, 369 bytes

_Diff stat: +0 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\inits.c	2026-04-16 20:02:20.082592500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\inits.c	2026-04-16 22:48:28.098133400 +0100
@@ -4,5 +4,4 @@
 	{extern void prof_init(int, char *[]); prof_init(argc, argv);}
 	{extern void trace_init(int, char *[]); trace_init(argc, argv);}
 	{extern void type_init(int, char *[]); type_init(argc, argv);}
-	{extern void x86linux_init(int, char *[]); x86linux_init(argc, argv);}
 }

```
