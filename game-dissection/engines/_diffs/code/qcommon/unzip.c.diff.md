# Diff: `code/qcommon/unzip.c`
**Canonical:** `wolfcamql-src` (sha256 `4e9deebba658...`, 51793 bytes)

## Variants

### `quake3-source`  — sha256 `965412cb7519...`, 150282 bytes

_Diff stat: +3890 / -1219 lines_

_(full diff is 197126 bytes — see files directly)_

### `ioquake3`  — sha256 `ecfd7119af3b...`, 51148 bytes

_Diff stat: +6 / -26 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\unzip.c	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\unzip.c	2026-04-16 20:02:21.572103800 +0100
@@ -1,7 +1,7 @@
 /* unzip.c -- IO for uncompress .zip files using zlib
 
-   Modified for Quake III Arena to use the Z_Malloc() memory pool.
-   This means a system copy of minizip is not a suitable replacement.
+   Modified for Quake III Arena to use the Z_Malloc() memory pool;
+   this means a system copy of minizip is not a suitable replacement.
 
    Based on minizip:
 
@@ -77,11 +77,9 @@
 #define SIZEZIPLOCALHEADER (0x1e)
 
 
-//FIXME
-void Com_Printf( const char *msg, ... ) Q_PRINTF_FUNC(1, 2);
 
 
-static const char unz_copyright[] =
+const char unz_copyright[] =
    " unzip 1.01 Copyright 1998-2004 Gilles Vollant - http://www.winimage.com/zLibDll";
 
 /* unz_file_info_interntal contain internal info about a file in zipfile*/
@@ -150,15 +148,6 @@
 #include "crypt.h"
 #endif
 
-uLong ZREAD (const zlib_filefunc_def pzlib_filefunc_def, voidpf filestream, void *buf, long size)
-{
-    uLong r;
-
-    r = ZREADX(pzlib_filefunc_def, filestream, buf, size);
-
-    return r;
-}
-
 /* ===========================================================================
      Read a byte from a gz_stream; update next_in and avail_in. Return EOF
    for end of file.
@@ -354,10 +343,8 @@
         uMaxBack = uSizeFile;
 
     buf = (unsigned char*)ALLOC(BUFREADCOMMENT+4);
-    if (buf==NULL) {
-        Com_Printf("^1%s() couldn't allocate memory for buffer\n", __FUNCTION__);
+    if (buf==NULL)
         return 0;
-    }
 
     uBackRead = 4;
     while (uBackRead<uMaxBack)
@@ -499,11 +486,7 @@
 
 
     s=(unz_s*)ALLOC(sizeof(unz_s));
-    if (!s) {
-        Com_Printf("^1%s() couldn't allocate memory\n", __FUNCTION__);
-    } else {
-        *s=us;
-    }
+    *s=us;
     unzGoToFirstFile((unzFile)s);
     return (unzFile)s;
 }
@@ -1108,10 +1091,8 @@
 
     pfile_in_zip_read_info = (file_in_zip_read_info_s*)
                                         ALLOC(sizeof(file_in_zip_read_info_s));
-    if (pfile_in_zip_read_info==NULL) {
-        Com_Printf("^1%s() couldn't allocate info memory\n", __FUNCTION__);
+    if (pfile_in_zip_read_info==NULL)
         return UNZ_INTERNALERROR;
-    }
 
     pfile_in_zip_read_info->read_buffer=(char*)ALLOC(UNZ_BUFSIZE);
     pfile_in_zip_read_info->offset_local_extrafield = offset_local_extrafield;
@@ -1121,7 +1102,6 @@
 
     if (pfile_in_zip_read_info->read_buffer==NULL)
     {
-        Com_Printf("^1%s() couldn't allocate read buffer\n", __FUNCTION__);
         TRYFREE(pfile_in_zip_read_info);
         return UNZ_INTERNALERROR;
     }

```

### `quake3e`  — sha256 `430553215d3c...`, 151874 bytes

_Diff stat: +3948 / -1228 lines_

_(full diff is 198592 bytes — see files directly)_

### `openarena-engine`  — sha256 `29915f14bed3...`, 50982 bytes

_Diff stat: +7 / -33 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\unzip.c	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\unzip.c	2026-04-16 22:48:25.913366000 +0100
@@ -1,10 +1,4 @@
 /* unzip.c -- IO for uncompress .zip files using zlib
-
-   Modified for Quake III Arena to use the Z_Malloc() memory pool.
-   This means a system copy of minizip is not a suitable replacement.
-
-   Based on minizip:
-
    Version 1.01e, February 12th, 2005
 
    Copyright (C) 1998-2005 Gilles Vollant
@@ -77,11 +71,9 @@
 #define SIZEZIPLOCALHEADER (0x1e)
 
 
-//FIXME
-void Com_Printf( const char *msg, ... ) Q_PRINTF_FUNC(1, 2);
 
 
-static const char unz_copyright[] =
+const char unz_copyright[] =
    " unzip 1.01 Copyright 1998-2004 Gilles Vollant - http://www.winimage.com/zLibDll";
 
 /* unz_file_info_interntal contain internal info about a file in zipfile*/
@@ -150,19 +142,10 @@
 #include "crypt.h"
 #endif
 
-uLong ZREAD (const zlib_filefunc_def pzlib_filefunc_def, voidpf filestream, void *buf, long size)
-{
-    uLong r;
-
-    r = ZREADX(pzlib_filefunc_def, filestream, buf, size);
-
-    return r;
-}
-
 /* ===========================================================================
      Read a byte from a gz_stream; update next_in and avail_in. Return EOF
    for end of file.
-   IN assertion: the stream s has been successfully opened for reading.
+   IN assertion: the stream s has been sucessfully opened for reading.
 */
 
 
@@ -301,8 +284,8 @@
 
 /*
    Compare two filename (fileName1,fileName2).
-   If iCaseSenisivity = 1, comparison is case sensitivity (like strcmp)
-   If iCaseSenisivity = 2, comparison is not case sensitivity (like strcmpi
+   If iCaseSenisivity = 1, comparision is case sensitivity (like strcmp)
+   If iCaseSenisivity = 2, comparision is not case sensitivity (like strcmpi
                                                                 or strcasecmp)
    If iCaseSenisivity = 0, case sensitivity is defaut of your operating system
         (like 1 on Unix, 2 on Windows)
@@ -354,10 +337,8 @@
         uMaxBack = uSizeFile;
 
     buf = (unsigned char*)ALLOC(BUFREADCOMMENT+4);
-    if (buf==NULL) {
-        Com_Printf("^1%s() couldn't allocate memory for buffer\n", __FUNCTION__);
+    if (buf==NULL)
         return 0;
-    }
 
     uBackRead = 4;
     while (uBackRead<uMaxBack)
@@ -499,11 +480,7 @@
 
 
     s=(unz_s*)ALLOC(sizeof(unz_s));
-    if (!s) {
-        Com_Printf("^1%s() couldn't allocate memory\n", __FUNCTION__);
-    } else {
-        *s=us;
-    }
+    *s=us;
     unzGoToFirstFile((unzFile)s);
     return (unzFile)s;
 }
@@ -1108,10 +1085,8 @@
 
     pfile_in_zip_read_info = (file_in_zip_read_info_s*)
                                         ALLOC(sizeof(file_in_zip_read_info_s));
-    if (pfile_in_zip_read_info==NULL) {
-        Com_Printf("^1%s() couldn't allocate info memory\n", __FUNCTION__);
+    if (pfile_in_zip_read_info==NULL)
         return UNZ_INTERNALERROR;
-    }
 
     pfile_in_zip_read_info->read_buffer=(char*)ALLOC(UNZ_BUFSIZE);
     pfile_in_zip_read_info->offset_local_extrafield = offset_local_extrafield;
@@ -1121,7 +1096,6 @@
 
     if (pfile_in_zip_read_info->read_buffer==NULL)
     {
-        Com_Printf("^1%s() couldn't allocate read buffer\n", __FUNCTION__);
         TRYFREE(pfile_in_zip_read_info);
         return UNZ_INTERNALERROR;
     }

```
