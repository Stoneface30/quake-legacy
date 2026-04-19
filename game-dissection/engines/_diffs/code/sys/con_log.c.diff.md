# Diff: `code/sys/con_log.c`
**Canonical:** `wolfcamql-src` (sha256 `c171ab40c8ad...`, 3083 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `4d3da986ef6c...`, 3076 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\con_log.c	2026-04-16 20:02:25.276294700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\con_log.c	2026-04-16 22:48:25.938962600 +0100
@@ -121,7 +121,7 @@
 	}
 
 	Com_Memcpy( out, consoleLog + readPos, firstChunk );
-	Com_Memcpy( out + firstChunk, consoleLog, secondChunk );
+	Com_Memcpy( out + firstChunk, out, secondChunk );
 
 	readPos = ( readPos + outSize ) % MAX_LOG;
 

```
