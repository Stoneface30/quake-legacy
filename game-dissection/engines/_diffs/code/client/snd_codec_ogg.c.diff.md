# Diff: `code/client/snd_codec_ogg.c`
**Canonical:** `wolfcamql-src` (sha256 `4cfb9f2b8667...`, 10135 bytes)

## Variants

### `openarena-engine`  — sha256 `43b1a96ab48c...`, 10139 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec_ogg.c	2026-04-16 20:02:25.176981500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_codec_ogg.c	2026-04-16 22:48:25.735378500 +0100
@@ -447,7 +447,7 @@
 
 	// allocate a buffer
 	// this buffer must be free-ed by the caller of this function
-	buffer = Hunk_AllocateTempMemory(info->size);
+    	buffer = Hunk_AllocateTempMemory(info->size);
 	if(!buffer)
 	{
 		S_OGG_CodecCloseStream(stream);

```

### `quake3e`  — sha256 `4105f442e803...`, 10221 bytes

_Diff stat: +43 / -38 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec_ogg.c	2026-04-16 20:02:25.176981500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_codec_ogg.c	2026-04-16 20:02:26.915520500 +0100
@@ -23,7 +23,7 @@
 */
 
 // OGG support is enabled by this define
-#ifdef USE_CODEC_VORBIS
+#ifdef USE_OGG_VORBIS
 
 // includes for the Q3 sound system
 #include "client.h"
@@ -52,7 +52,7 @@
 // callbacks for vobisfile
 
 // fread() replacement
-size_t S_OGG_Callback_read(void *ptr, size_t size, size_t nmemb, void *datasource)
+size_t S_OGG_Callback_read( void *ptr, size_t size, size_t nmemb, void *datasource )
 {
 	snd_stream_t *stream;
 	int byteSize = 0;
@@ -60,20 +60,20 @@
 	size_t nMembRead = 0;
 
 	// check if input is valid
-	if(!ptr)
+	if (!ptr)
 	{
 		errno = EFAULT; 
 		return 0;
 	}
 	
-	if(!(size && nmemb))
+	if (!(size && nmemb))
 	{
 		// It's not an error, caller just wants zero bytes!
 		errno = 0;
 		return 0;
 	}
  
-	if(!datasource)
+	if (!datasource)
 	{
 		errno = EBADF; 
 		return 0;
@@ -87,6 +87,11 @@
 
 	// read it with the Q3 function FS_Read()
 	bytesRead = FS_Read(ptr, byteSize, stream->file);
+	if (bytesRead < 0)
+	{
+		errno = EIO;
+		return 0;
+	}
 
 	// update the file position
 	stream->pos += bytesRead;
@@ -96,7 +101,7 @@
 
 	// even if the last member is only read partially
 	// it is counted as a whole in the return value	
-	if(bytesRead % size)
+	if (bytesRead % size)
 	{
 		nMembRead++;
 	}
@@ -111,7 +116,7 @@
 	int retVal = 0;
 
 	// check if input is valid
-	if(!datasource)
+	if (!datasource)
 	{
 		errno = EBADF; 
 		return -1;
@@ -121,7 +126,7 @@
 	stream = (snd_stream_t *) datasource;
 
 	// we must map the whence to its Q3 counterpart
-	switch(whence)
+	switch (whence)
 	{
 		case SEEK_SET :
 		{
@@ -129,9 +134,9 @@
 			retVal = FS_Seek(stream->file, (long) offset, FS_SEEK_SET);
 
 			// something has gone wrong, so we return here
-			if(retVal < 0)
+			if (retVal < 0)
 			{
-			 return retVal;
+				return retVal;
 			}
 
 			// keep track of file position
@@ -145,9 +150,9 @@
 			retVal = FS_Seek(stream->file, (long) offset, FS_SEEK_CUR);
 
 			// something has gone wrong, so we return here
-			if(retVal < 0)
+			if (retVal < 0)
 			{
-			 return retVal;
+				return retVal;
 			}
 
 			// keep track of file position
@@ -161,9 +166,9 @@
 			retVal = FS_Seek(stream->file, (long) offset, FS_SEEK_END);
 
 			// something has gone wrong, so we return here
-			if(retVal < 0)
+			if (retVal < 0)
 			{
-			 return retVal;
+				return retVal;
 			}
 
 			// keep track of file position
@@ -199,7 +204,7 @@
 	snd_stream_t   *stream;
 
 	// check if input is valid
-	if(!datasource)
+	if (!datasource)
 	{
 		errno = EBADF;
 		return -1;
@@ -214,10 +219,10 @@
 // the callback structure
 const ov_callbacks S_OGG_Callbacks =
 {
- &S_OGG_Callback_read,
- &S_OGG_Callback_seek,
- &S_OGG_Callback_close,
- &S_OGG_Callback_tell
+	&S_OGG_Callback_read,
+	&S_OGG_Callback_seek,
+	&S_OGG_Callback_close,
+	&S_OGG_Callback_tell
 };
 
 /*
@@ -237,21 +242,21 @@
 	ogg_int64_t numSamples;
 
 	// check if input is valid
-	if(!filename)
+	if (!filename)
 	{
 		return NULL;
 	}
 
 	// Open the stream
 	stream = S_CodecUtilOpen(filename, &ogg_codec);
-	if(!stream)
+	if (!stream)
 	{
 		return NULL;
 	}
 
 	// alloctate the OggVorbis_File
 	vf = Z_Malloc(sizeof(OggVorbis_File));
-	if(!vf)
+	if (!vf)
 	{
 		S_CodecUtilClose(&stream);
 
@@ -259,7 +264,7 @@
 	}
 
 	// open the codec with our callbacks and stream as the generic pointer
-	if(ov_open_callbacks(stream, vf, NULL, 0, S_OGG_Callbacks) != 0)
+	if (ov_open_callbacks(stream, vf, NULL, 0, S_OGG_Callbacks) != 0)
 	{
 		Z_Free(vf);
 
@@ -269,7 +274,7 @@
 	}
 
 	// the stream must be seekable
-	if(!ov_seekable(vf))
+	if (!ov_seekable(vf))
 	{
 		ov_clear(vf);
 
@@ -281,7 +286,7 @@
 	}
  
 	// we only support OGGs with one substream
-	if(ov_streams(vf) != 1)
+	if (ov_streams(vf) != 1)
 	{
 		ov_clear(vf);
 
@@ -294,7 +299,7 @@
 
 	// get the info about channels and rate
 	OGGInfo = ov_info(vf, 0);
-	if(!OGGInfo)
+	if (!OGGInfo)
 	{
 		ov_clear(vf);
 
@@ -333,7 +338,7 @@
 void S_OGG_CodecCloseStream(snd_stream_t *stream)
 {
 	// check if input is valid
-	if(!stream)
+	if (!stream)
 	{
 		return;
 	}
@@ -370,12 +375,12 @@
 #	endif // Q3_BIG_ENDIAN
 
 	// check if input is valid
-	if(!(stream && buffer))
+	if (!(stream && buffer))
 	{
 		return 0;
 	}
 
-	if(bytes <= 0)
+	if (bytes <= 0)
 	{
 		return 0;
 	}
@@ -385,13 +390,13 @@
 	bufPtr = buffer;
 
 	// cycle until we have the requested or all available bytes read
-	while(-1)
+	while (-1)
 	{
 		// read some bytes from the OGG codec
 		c = ov_read((OggVorbis_File *) stream->ptr, bufPtr, bytesLeft, IsBigEndian, OGG_SAMPLEWIDTH, 1, &BS);
 		
 		// no more bytes are left
-		if(c <= 0)
+		if (c <= 0)
 		{
 			break;
 		}
@@ -401,7 +406,7 @@
 		bufPtr += c;
   
 		// we have enough bytes
-		if(bytesLeft <= 0)
+		if (bytesLeft <= 0)
 		{
 			break;
 		}
@@ -425,14 +430,14 @@
 	int bytesRead;
 	
 	// check if input is valid
-	if(!(filename && info))
+	if (!(filename && info))
 	{
 		return NULL;
 	}
 	
 	// open the file as a stream
 	stream = S_OGG_CodecOpenStream(filename);
-	if(!stream)
+	if (!stream)
 	{
 		return NULL;
 	}
@@ -447,8 +452,8 @@
 
 	// allocate a buffer
 	// this buffer must be free-ed by the caller of this function
-	buffer = Hunk_AllocateTempMemory(info->size);
-	if(!buffer)
+    buffer = Hunk_AllocateTempMemory(info->size);
+	if (!buffer)
 	{
 		S_OGG_CodecCloseStream(stream);
 	
@@ -459,7 +464,7 @@
 	bytesRead = S_OGG_CodecReadStream(stream, info->size, buffer);
 	
 	// we don't even have read a single byte
-	if(bytesRead <= 0)
+	if (bytesRead <= 0)
 	{
 		Hunk_FreeTempMemory(buffer);
 		S_OGG_CodecCloseStream(stream);
@@ -472,4 +477,4 @@
 	return buffer;
 }
 
-#endif // USE_CODEC_VORBIS
+#endif // USE_OGG_VORBIS

```
