# Diff: `code/client/snd_codec_wav.c`
**Canonical:** `wolfcamql-src` (sha256 `3b15bda49945...`, 6115 bytes)

## Variants

### `openarena-engine`  — sha256 `f58ed3aab604...`, 6115 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec_wav.c	2026-04-16 20:02:25.177514900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_codec_wav.c	2026-04-16 22:48:25.735378500 +0100
@@ -145,7 +145,7 @@
 	}
 
 	// Save the parameters
-	FGetLittleShort(file); // wav format
+	FGetLittleShort(file); // wav_format
 	info->channels = FGetLittleShort(file);
 	info->rate = FGetLittleLong(file);
 	FGetLittleLong(file);

```

### `quake3e`  — sha256 `408dbd4ed6cf...`, 6662 bytes

_Diff stat: +27 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec_wav.c	2026-04-16 20:02:25.177514900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_codec_wav.c	2026-04-16 20:02:26.915520500 +0100
@@ -32,7 +32,8 @@
 static int FGetLittleLong( fileHandle_t f ) {
 	int		v;
 
-	FS_Read( &v, sizeof(v), f );
+	if (FS_Read( &v, sizeof(v), f ) != sizeof(v))
+		return -1;
 
 	return LittleLong( v);
 }
@@ -45,7 +46,8 @@
 static short FGetLittleShort( fileHandle_t f ) {
 	short	v;
 
-	FS_Read( &v, sizeof(v), f );
+	if (FS_Read( &v, sizeof(v), f ) != sizeof(v))
+		return -1;
 
 	return LittleShort( v);
 }
@@ -100,9 +102,13 @@
 	return -1;
 }
 
+
 /*
 =================
 S_ByteSwapRawSamples
+
+If raw data has been loaded in little endian binary form, this must be done.
+If raw data was calculated, as with ADPCM, this should not be called.
 =================
 */
 static void S_ByteSwapRawSamples( int samples, int width, int s_channels, const byte *data ) {
@@ -123,6 +129,7 @@
 	}
 }
 
+
 /*
 =================
 S_ReadRIFFHeader
@@ -135,7 +142,11 @@
 	int fmtlen = 0;
 
 	// skip the riff wav header
-	FS_Read(dump, 12, file);
+	if (FS_Read(dump, 12, file) != 12)
+	{
+		Com_Printf( S_COLOR_RED "ERROR: Couldn't read header\n");
+		return qfalse;
+	}
 
 	// Scan for the format chunk
 	if((fmtlen = S_FindRIFFChunk(file, "fmt ")) < 0)
@@ -145,7 +156,7 @@
 	}
 
 	// Save the parameters
-	FGetLittleShort(file); // wav format
+	FGetLittleShort(file); // wav_format
 	info->channels = FGetLittleShort(file);
 	info->rate = FGetLittleLong(file);
 	FGetLittleLong(file);
@@ -202,7 +213,7 @@
 
 	// Try to open the file
 	FS_FOpenFileRead(filename, &file, qtrue);
-	if(!file)
+	if ( file == FS_INVALID_HANDLE )
 	{
 		return NULL;
 	}
@@ -227,7 +238,14 @@
 	}
 
 	// Read, byteswap
-	FS_Read(buffer, info->size, file);
+	if (FS_Read(buffer, info->size, file) != info->size)
+	{
+		Hunk_FreeTempMemory(buffer);
+		FS_FCloseFile(file);
+		Com_Printf( S_COLOR_RED "ERROR: Couldn't read \"%s\"\n", filename);
+		return NULL;
+	}
+
 	S_ByteSwapRawSamples(info->samples, info->width, info->channels, (byte *)buffer);
 
 	// Close and return
@@ -283,9 +301,11 @@
 		return 0;
 	if(bytes > remaining)
 		bytes = remaining;
+	bytes = FS_Read(buffer, bytes, stream->file);
+	if (bytes <= 0)
+		return 0;
 	stream->pos += bytes;
 	samples = (bytes / stream->info.width) / stream->info.channels;
-	FS_Read(buffer, bytes, stream->file);
 	S_ByteSwapRawSamples(samples, stream->info.width, stream->info.channels, buffer);
 	return bytes;
 }

```
