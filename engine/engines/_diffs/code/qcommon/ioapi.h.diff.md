# Diff: `code/qcommon/ioapi.h`
**Canonical:** `wolfcamql-src` (sha256 `4726ad7b8d12...`, 2713 bytes)

## Variants

### `openarena-engine`  — sha256 `b55b88576d0c...`, 2610 bytes
Also identical in: ioquake3

_Diff stat: +1 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\ioapi.h	2026-04-16 20:02:25.222226900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\ioapi.h	2026-04-16 22:48:25.909298600 +0100
@@ -59,9 +59,7 @@
 
 void fill_fopen_filefunc OF((zlib_filefunc_def* pzlib_filefunc_def));
 
-uLong ZREAD (const zlib_filefunc_def pzlib_filefunc_def, voidpf filestream, void *buf, long size);
-
-#define ZREADX(filefunc,filestream,buf,size) ((*((filefunc).zread_file))((filefunc).opaque,filestream,buf,size))
+#define ZREAD(filefunc,filestream,buf,size) ((*((filefunc).zread_file))((filefunc).opaque,filestream,buf,size))
 #define ZWRITE(filefunc,filestream,buf,size) ((*((filefunc).zwrite_file))((filefunc).opaque,filestream,buf,size))
 #define ZTELL(filefunc,filestream) ((*((filefunc).ztell_file))((filefunc).opaque,filestream))
 #define ZSEEK(filefunc,filestream,pos,mode) ((*((filefunc).zseek_file))((filefunc).opaque,filestream,pos,mode))

```
