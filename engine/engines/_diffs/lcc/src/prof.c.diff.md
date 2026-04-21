# Diff: `lcc/src/prof.c`
**Canonical:** `quake3-source` (sha256 `0edbe7e830a3...`, 6614 bytes)

## Variants

### `q3vm`  — sha256 `087913293f87...`, 6621 bytes

_Diff stat: +2 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\prof.c	2026-04-16 20:02:20.085103100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\prof.c	2026-04-16 22:48:28.099132300 +0100
@@ -203,7 +203,7 @@
 		return;
 	inited = 1;
 	type_init(argc, argv);
-	if (IR)
+	if (IR) {
 		for (i = 1; i < argc; i++)
 			if (strncmp(argv[i], "-a", 2) == 0) {
 				if (ncalled == -1
@@ -224,4 +224,5 @@
 					attach((Apply)bbincr, YYcounts, &events.points);
 				}
 			}
+  }
 }

```
