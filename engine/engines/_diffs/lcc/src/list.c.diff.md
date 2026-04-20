# Diff: `lcc/src/list.c`
**Canonical:** `quake3-source` (sha256 `444e1857cc13...`, 1031 bytes)

## Variants

### `q3vm`  — sha256 `5b0749a4819e...`, 1030 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\src\list.c	2026-04-16 20:02:20.084097900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\src\list.c	2026-04-16 22:48:28.098133400 +0100
@@ -33,7 +33,7 @@
 	return n;
 }
 
-/* ltov - convert list to an NULL-terminated vector allocated in arena */
+/* ltov - convert list to a NULL-terminated vector allocated in arena */
 void *ltov(List *list, unsigned arena) {
 	int i = 0;
 	void **array = newarray(length(*list) + 1, sizeof array[0], arena);

```
