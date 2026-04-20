# Diff: `libs/pak/unzip.h`
**Canonical:** `quake3-source` (sha256 `25a9d031df00...`, 12454 bytes)

## Variants

### `gtkradiant`  — sha256 `410e1216b713...`, 12580 bytes

_Diff stat: +147 / -147 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\libs\pak\unzip.h	2026-04-16 20:02:20.122999800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\gtkradiant\libs\pak\unzip.h	2026-04-16 22:48:36.876832500 +0100
@@ -1,8 +1,8 @@
 
-#if defined(STRICTUNZIP) || defined(STRICTZIPUNZIP)
+#if defined( STRICTUNZIP ) || defined( STRICTZIPUNZIP )
 /* like the STRICT of WIN32, we define a pointer that cannot be converted
     from (void*) without cast */
-typedef struct TagunzFile__ { int unused; } unzFile__; 
+typedef struct TagunzFile__ { int unused; } unzFile__;
 typedef unzFile__ *unzFile;
 #else
 typedef void* unzFile;
@@ -10,7 +10,7 @@
 
 
 /* tm_unz contain date/time info */
-typedef struct tm_unz_s 
+typedef struct tm_unz_s
 {
 	unsigned int tm_sec;            /* seconds after the minute - [0,59] */
 	unsigned int tm_min;            /* minutes after the hour - [0,59] */
@@ -32,55 +32,55 @@
 /* unz_file_info contain information about a file in the zipfile */
 typedef struct unz_file_info_s
 {
-    unsigned long version;              /* version made by                 2 unsigned chars */
-    unsigned long version_needed;       /* version needed to extract       2 unsigned chars */
-    unsigned long flag;                 /* general purpose bit flag        2 unsigned chars */
-    unsigned long compression_method;   /* compression method              2 unsigned chars */
-    unsigned long dosDate;              /* last mod file date in Dos fmt   4 unsigned chars */
-    unsigned long crc;                  /* crc-32                          4 unsigned chars */
-    unsigned long compressed_size;      /* compressed size                 4 unsigned chars */ 
-    unsigned long uncompressed_size;    /* uncompressed size               4 unsigned chars */ 
-    unsigned long size_filename;        /* filename length                 2 unsigned chars */
-    unsigned long size_file_extra;      /* extra field length              2 unsigned chars */
-    unsigned long size_file_comment;    /* file comment length             2 unsigned chars */
-
-    unsigned long disk_num_start;       /* disk number start               2 unsigned chars */
-    unsigned long internal_fa;          /* internal file attributes        2 unsigned chars */
-    unsigned long external_fa;          /* external file attributes        4 unsigned chars */
+	unsigned long version;              /* version made by                 2 unsigned chars */
+	unsigned long version_needed;       /* version needed to extract       2 unsigned chars */
+	unsigned long flag;                 /* general purpose bit flag        2 unsigned chars */
+	unsigned long compression_method;   /* compression method              2 unsigned chars */
+	unsigned long dosDate;              /* last mod file date in Dos fmt   4 unsigned chars */
+	unsigned long crc;                  /* crc-32                          4 unsigned chars */
+	unsigned long compressed_size;      /* compressed size                 4 unsigned chars */
+	unsigned long uncompressed_size;    /* uncompressed size               4 unsigned chars */
+	unsigned long size_filename;        /* filename length                 2 unsigned chars */
+	unsigned long size_file_extra;      /* extra field length              2 unsigned chars */
+	unsigned long size_file_comment;    /* file comment length             2 unsigned chars */
+
+	unsigned long disk_num_start;       /* disk number start               2 unsigned chars */
+	unsigned long internal_fa;          /* internal file attributes        2 unsigned chars */
+	unsigned long external_fa;          /* external file attributes        4 unsigned chars */
 
-    tm_unz tmu_date;
+	tm_unz tmu_date;
 } unz_file_info;
 
 /* unz_file_info_interntal contain internal info about a file in zipfile*/
 typedef struct unz_file_info_internal_s
 {
-    unsigned long offset_curfile;/* relative offset of static header 4 unsigned chars */
+	unsigned long offset_curfile; /* relative offset of static header 4 unsigned chars */
 } unz_file_info_internal;
 
-typedef void* (*alloc_func) (void* opaque, unsigned int items, unsigned int size);
-typedef void   (*free_func) (void* opaque, void* address);
+typedef void* ( *alloc_func )( void* opaque, unsigned int items, unsigned int size );
+typedef void ( *free_func )( void* opaque, void* address );
 
 struct internal_state;
 
 typedef struct z_stream_s {
-    unsigned char    *next_in;  /* next input unsigned char */
-    unsigned int     avail_in;  /* number of unsigned chars available at next_in */
-    unsigned long    total_in;  /* total nb of input unsigned chars read so */
-
-    unsigned char    *next_out; /* next output unsigned char should be put there */
-    unsigned int     avail_out; /* remaining free space at next_out */
-    unsigned long    total_out; /* total nb of unsigned chars output so */
-
-    char     *msg;      /* last error message, NULL if no error */
-    struct internal_state *state; /* not visible by applications */
-
-    alloc_func zalloc;  /* used to allocate the internal state */
-    free_func  zfree;   /* used to free the internal state */
-    unsigned char*     opaque;  /* private data object passed to zalloc and zfree */
-
-    int     data_type;  /* best guess about the data type: ascii or binary */
-    unsigned long   adler;      /* adler32 value of the uncompressed data */
-    unsigned long   reserved;   /* reserved for future use */
+	unsigned char    *next_in;  /* next input unsigned char */
+	unsigned int avail_in;      /* number of unsigned chars available at next_in */
+	unsigned long total_in;     /* total nb of input unsigned chars read so */
+
+	unsigned char    *next_out; /* next output unsigned char should be put there */
+	unsigned int avail_out;     /* remaining free space at next_out */
+	unsigned long total_out;    /* total nb of unsigned chars output so */
+
+	char     *msg;      /* last error message, NULL if no error */
+	struct internal_state *state; /* not visible by applications */
+
+	alloc_func zalloc;  /* used to allocate the internal state */
+	free_func zfree;    /* used to free the internal state */
+	unsigned char*     opaque;  /* private data object passed to zalloc and zfree */
+
+	int data_type;      /* best guess about the data type: ascii or binary */
+	unsigned long adler;        /* adler32 value of the uncompressed data */
+	unsigned long reserved;     /* reserved for future use */
 } z_stream;
 
 typedef z_stream *z_streamp;
@@ -96,27 +96,27 @@
 	unsigned long pos_in_zipfile;       /* position in unsigned char on the zipfile, for fseek*/
 	unsigned long stream_initialised;   /* flag set if stream structure is initialised*/
 
-	unsigned long offset_local_extrafield;/* offset of the static extra field */
-	unsigned int  size_local_extrafield;/* size of the static extra field */
+	unsigned long offset_local_extrafield; /* offset of the static extra field */
+	unsigned int size_local_extrafield; /* size of the static extra field */
 	unsigned long pos_local_extrafield;   /* position in the static extra field in read*/
 
 	unsigned long crc32;                /* crc32 of all data uncompressed */
 	unsigned long crc32_wait;           /* crc32 we must obtain after decompress all */
 	unsigned long rest_read_compressed; /* number of unsigned char to be decompressed */
-	unsigned long rest_read_uncompressed;/*number of unsigned char to be obtained after decomp*/
+	unsigned long rest_read_uncompressed; /*number of unsigned char to be obtained after decomp*/
 	FILE* file;                 /* io structore of the zipfile */
 	unsigned long compression_method;   /* compression method (0==store) */
-	unsigned long byte_before_the_zipfile;/* unsigned char before the zipfile, (>0 for sfx)*/
+	unsigned long byte_before_the_zipfile; /* unsigned char before the zipfile, (>0 for sfx)*/
 } file_in_zip_read_info_s;
 
 
 /* unz_s contain internal information about the zipfile
-*/
+ */
 typedef struct
 {
 	FILE* file;                 /* io structore of the zipfile */
 	unz_global_info gi;       /* public global information */
-	unsigned long byte_before_the_zipfile;/* unsigned char before the zipfile, (>0 for sfx)*/
+	unsigned long byte_before_the_zipfile; /* unsigned char before the zipfile, (>0 for sfx)*/
 	unsigned long num_file;             /* number of the current file in the zipfile*/
 	unsigned long pos_in_central_dir;   /* pos of the current file in the central dir*/
 	unsigned long current_file_ok;      /* flag about the usability of the current file*/
@@ -124,177 +124,177 @@
 
 	unsigned long size_central_dir;     /* size of the central directory  */
 	unsigned long offset_central_dir;   /* offset of start of central directory with
-								   respect to the starting disk number */
+	                                       respect to the starting disk number */
 
 	unz_file_info cur_file_info; /* public info about the current file in zip*/
 	unz_file_info_internal cur_file_info_internal; /* private info about it*/
-    file_in_zip_read_info_s* pfile_in_zip_read; /* structure about the current
-	                                    file if we are decompressing it */
+	file_in_zip_read_info_s* pfile_in_zip_read; /* structure about the current
+	                                               file if we are decompressing it */
 } unz_s;
 
-#define UNZ_OK                                  (0)
-#define UNZ_END_OF_LIST_OF_FILE (-100)
-#define UNZ_ERRNO               (Z_ERRNO)
-#define UNZ_EOF                 (0)
-#define UNZ_PARAMERROR                  (-102)
-#define UNZ_BADZIPFILE                  (-103)
-#define UNZ_INTERNALERROR               (-104)
-#define UNZ_CRCERROR                    (-105)
-
-#define UNZ_CASESENSITIVE		1
-#define UNZ_NOTCASESENSITIVE	2
-#define UNZ_OSDEFAULTCASE		0
+#define UNZ_OK                                  ( 0 )
+#define UNZ_END_OF_LIST_OF_FILE ( -100 )
+#define UNZ_ERRNO               ( Z_ERRNO )
+#define UNZ_EOF                 ( 0 )
+#define UNZ_PARAMERROR                  ( -102 )
+#define UNZ_BADZIPFILE                  ( -103 )
+#define UNZ_INTERNALERROR               ( -104 )
+#define UNZ_CRCERROR                    ( -105 )
+
+#define UNZ_CASESENSITIVE       1
+#define UNZ_NOTCASESENSITIVE    2
+#define UNZ_OSDEFAULTCASE       0
 
-extern int unzStringFileNameCompare (const char* fileName1, const char* fileName2, int iCaseSensitivity);
+extern int unzStringFileNameCompare( const char* fileName1, const char* fileName2, int iCaseSensitivity );
 
 /*
    Compare two filename (fileName1,fileName2).
    If iCaseSenisivity = 1, comparision is case sensitivity (like strcmp)
    If iCaseSenisivity = 2, comparision is not case sensitivity (like strcmpi
-								or strcasecmp)
+                                or strcasecmp)
    If iCaseSenisivity = 0, case sensitivity is defaut of your operating system
-	(like 1 on Unix, 2 on Windows)
-*/
+    (like 1 on Unix, 2 on Windows)
+ */
 
-extern unzFile unzOpen (const char *path);
-extern unzFile unzReOpen (const char* path, unzFile file);
+extern unzFile unzOpen( const char *path );
+extern unzFile unzReOpen( const char* path, unzFile file );
 
 /*
-  Open a Zip file. path contain the full pathname (by example,
+   Open a Zip file. path contain the full pathname (by example,
      on a Windows NT computer "c:\\zlib\\zlib111.zip" or on an Unix computer
-	 "zlib/zlib111.zip".
-	 If the zipfile cannot be opened (file don't exist or in not valid), the
-	   return value is NULL.
+     "zlib/zlib111.zip".
+     If the zipfile cannot be opened (file don't exist or in not valid), the
+       return value is NULL.
      Else, the return value is a unzFile Handle, usable with other function
-	   of this unzip package.
-*/
+       of this unzip package.
+ */
 
-extern int unzClose (unzFile file);
+extern int unzClose( unzFile file );
 
 /*
-  Close a ZipFile opened with unzipOpen.
-  If there is files inside the .Zip opened with unzOpenCurrentFile (see later),
+   Close a ZipFile opened with unzipOpen.
+   If there is files inside the .Zip opened with unzOpenCurrentFile (see later),
     these files MUST be closed with unzipCloseCurrentFile before call unzipClose.
-  return UNZ_OK if there is no problem. */
+   return UNZ_OK if there is no problem. */
 
-extern int unzGetGlobalInfo (unzFile file, unz_global_info *pglobal_info);
+extern int unzGetGlobalInfo( unzFile file, unz_global_info *pglobal_info );
 
 /*
-  Write info about the ZipFile in the *pglobal_info structure.
-  No preparation of the structure is needed
-  return UNZ_OK if there is no problem. */
+   Write info about the ZipFile in the *pglobal_info structure.
+   No preparation of the structure is needed
+   return UNZ_OK if there is no problem. */
 
 
-extern int unzGetGlobalComment (unzFile file, char *szComment, unsigned long uSizeBuf);
+extern int unzGetGlobalComment( unzFile file, char *szComment, unsigned long uSizeBuf );
 
 /*
-  Get the global comment string of the ZipFile, in the szComment buffer.
-  uSizeBuf is the size of the szComment buffer.
-  return the number of unsigned char copied or an error code <0
-*/
+   Get the global comment string of the ZipFile, in the szComment buffer.
+   uSizeBuf is the size of the szComment buffer.
+   return the number of unsigned char copied or an error code <0
+ */
 
 
 /***************************************************************************/
 /* Unzip package allow you browse the directory of the zipfile */
 
-extern int unzGoToFirstFile (unzFile file);
+extern int unzGoToFirstFile( unzFile file );
 
 /*
-  Set the current file of the zipfile to the first file.
-  return UNZ_OK if there is no problem
-*/
+   Set the current file of the zipfile to the first file.
+   return UNZ_OK if there is no problem
+ */
 
-extern int unzGoToNextFile (unzFile file);
+extern int unzGoToNextFile( unzFile file );
 
 /*
-  Set the current file of the zipfile to the next file.
-  return UNZ_OK if there is no problem
-  return UNZ_END_OF_LIST_OF_FILE if the actual file was the latest.
-*/
+   Set the current file of the zipfile to the next file.
+   return UNZ_OK if there is no problem
+   return UNZ_END_OF_LIST_OF_FILE if the actual file was the latest.
+ */
 
-extern int unzLocateFile (unzFile file, const char *szFileName, int iCaseSensitivity);
+extern int unzLocateFile( unzFile file, const char *szFileName, int iCaseSensitivity );
 
 /*
-  Try locate the file szFileName in the zipfile.
-  For the iCaseSensitivity signification, see unzStringFileNameCompare
+   Try locate the file szFileName in the zipfile.
+   For the iCaseSensitivity signification, see unzStringFileNameCompare
 
-  return value :
-  UNZ_OK if the file is found. It becomes the current file.
-  UNZ_END_OF_LIST_OF_FILE if the file is not found
-*/
+   return value :
+   UNZ_OK if the file is found. It becomes the current file.
+   UNZ_END_OF_LIST_OF_FILE if the file is not found
+ */
 
 
-extern int unzGetCurrentFileInfo (unzFile file, unz_file_info *pfile_info, char *szFileName, unsigned long fileNameBufferSize, void *extraField, unsigned long extraFieldBufferSize, char *szComment, unsigned long commentBufferSize);
+extern int unzGetCurrentFileInfo( unzFile file, unz_file_info *pfile_info, char *szFileName, unsigned long fileNameBufferSize, void *extraField, unsigned long extraFieldBufferSize, char *szComment, unsigned long commentBufferSize );
 
 /*
-  Get Info about the current file
-  if pfile_info!=NULL, the *pfile_info structure will contain somes info about
-	    the current file
-  if szFileName!=NULL, the filemane string will be copied in szFileName
-			(fileNameBufferSize is the size of the buffer)
-  if extraField!=NULL, the extra field information will be copied in extraField
-			(extraFieldBufferSize is the size of the buffer).
-			This is the Central-header version of the extra field
-  if szComment!=NULL, the comment string of the file will be copied in szComment
-			(commentBufferSize is the size of the buffer)
-*/
+   Get Info about the current file
+   if pfile_info!=NULL, the *pfile_info structure will contain somes info about
+        the current file
+   if szFileName!=NULL, the filemane string will be copied in szFileName
+            (fileNameBufferSize is the size of the buffer)
+   if extraField!=NULL, the extra field information will be copied in extraField
+            (extraFieldBufferSize is the size of the buffer).
+            This is the Central-header version of the extra field
+   if szComment!=NULL, the comment string of the file will be copied in szComment
+            (commentBufferSize is the size of the buffer)
+ */
 
 /***************************************************************************/
 /* for reading the content of the current zipfile, you can open it, read data
    from it, and close it (you can close it before reading all the file)
-   */
+ */
 
-extern int unzOpenCurrentFile (unzFile file);
+extern int unzOpenCurrentFile( unzFile file );
 
 /*
-  Open for reading data the current file in the zipfile.
-  If there is no error, the return value is UNZ_OK.
-*/
+   Open for reading data the current file in the zipfile.
+   If there is no error, the return value is UNZ_OK.
+ */
 
-extern int unzCloseCurrentFile (unzFile file);
+extern int unzCloseCurrentFile( unzFile file );
 
 /*
-  Close the file in zip opened with unzOpenCurrentFile
-  Return UNZ_CRCERROR if all the file was read but the CRC is not good
-*/
+   Close the file in zip opened with unzOpenCurrentFile
+   Return UNZ_CRCERROR if all the file was read but the CRC is not good
+ */
 
-												
-extern int unzReadCurrentFile (unzFile file, void* buf, unsigned len);
+
+extern int unzReadCurrentFile( unzFile file, void* buf, unsigned len );
 
 /*
-  Read unsigned chars from the current file (opened by unzOpenCurrentFile)
-  buf contain buffer where data must be copied
-  len the size of buf.
+   Read unsigned chars from the current file (opened by unzOpenCurrentFile)
+   buf contain buffer where data must be copied
+   len the size of buf.
 
-  return the number of unsigned char copied if somes unsigned chars are copied
-  return 0 if the end of file was reached
-  return <0 with error code if there is an error
+   return the number of unsigned char copied if somes unsigned chars are copied
+   return 0 if the end of file was reached
+   return <0 with error code if there is an error
     (UNZ_ERRNO for IO error, or zLib error for uncompress error)
-*/
+ */
 
-extern long unztell(unzFile file);
+extern long unztell( unzFile file );
 
 /*
-  Give the current position in uncompressed data
-*/
+   Give the current position in uncompressed data
+ */
 
-extern int unzeof (unzFile file);
+extern int unzeof( unzFile file );
 
 /*
-  return 1 if the end of file was reached, 0 elsewhere 
-*/
+   return 1 if the end of file was reached, 0 elsewhere
+ */
 
-extern int unzGetLocalExtrafield (unzFile file, void* buf, unsigned len);
+extern int unzGetLocalExtrafield( unzFile file, void* buf, unsigned len );
 
 /*
-  Read extra field from the current file (opened by unzOpenCurrentFile)
-  This is the local-header version of the extra field (sometimes, there is
+   Read extra field from the current file (opened by unzOpenCurrentFile)
+   This is the local-header version of the extra field (sometimes, there is
     more info in the local-header version than in the central-header)
 
-  if buf==NULL, it return the size of the local extra field
+   if buf==NULL, it return the size of the local extra field
 
-  if buf!=NULL, len is the size of the buffer, the extra header is copied in
-	buf.
-  the return value is the number of unsigned chars copied in buf, or (if <0) 
-	the error code
-*/
+   if buf!=NULL, len is the size of the buffer, the extra header is copied in
+    buf.
+   the return value is the number of unsigned chars copied in buf, or (if <0)
+    the error code
+ */

```
