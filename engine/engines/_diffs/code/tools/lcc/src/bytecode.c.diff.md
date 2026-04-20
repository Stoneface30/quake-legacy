# Diff: `code/tools/lcc/src/bytecode.c`
**Canonical:** `wolfcamql-src` (sha256 `730441862a69...`, 8488 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `openarena-gamecode`  — sha256 `9fe4f104be4a...`, 8587 bytes

_Diff stat: +5 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\bytecode.c	2026-04-16 20:02:25.807414900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\src\bytecode.c	2026-04-16 22:48:24.205077500 +0100
@@ -261,7 +261,11 @@
 	length = filelength( f );
 	sourceFile = malloc( length + 1 );
 	if ( sourceFile ) {
-		fread( sourceFile, length, 1, f );
+		size_t size;
+		size = fread( sourceFile, length, 1, f );
+		if (size != length) {
+			print( ";error reading %s\n", filename );
+		}
 		sourceFile[length] = 0;
 	}
 

```
