# Diff: `code/client/snd_codec.h`
**Canonical:** `wolfcamql-src` (sha256 `43ddb26cd540...`, 3506 bytes)
Also identical in: ioquake3

## Variants

### `quake3e`  — sha256 `d6ba58cb319d...`, 3006 bytes

_Diff stat: +91 / -101 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec.h	2026-04-16 20:02:25.176455100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_codec.h	2026-04-16 20:02:26.915520500 +0100
@@ -1,107 +1,97 @@
-/*
-===========================================================================
-Copyright (C) 1999-2005 Id Software, Inc.
-Copyright (C) 2005 Stuart Dalton (badcdev@gmail.com)
-
-This file is part of Quake III Arena source code.
-
-Quake III Arena source code is free software; you can redistribute it
-and/or modify it under the terms of the GNU General Public License as
-published by the Free Software Foundation; either version 2 of the License,
-or (at your option) any later version.
-
-Quake III Arena source code is distributed in the hope that it will be
-useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
-MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-GNU General Public License for more details.
-
-You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
-Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
-===========================================================================
-*/
-
-#ifndef _SND_CODEC_H_
-#define _SND_CODEC_H_
-
-#include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
-
-typedef struct snd_info_s
-{
-	int rate;
-	int width;
-	int channels;
-	int samples;
-	int size;
-	int dataofs;
-} snd_info_t;
-
-typedef struct snd_codec_s snd_codec_t;
-
-typedef struct snd_stream_s
-{
-	snd_codec_t *codec;
-	fileHandle_t file;
-	snd_info_t info;
-	int length;
-	int pos;
-	void *ptr;
-} snd_stream_t;
-
-// Codec functions
-typedef void *(*CODEC_LOAD)(const char *filename, snd_info_t *info);
-typedef snd_stream_t *(*CODEC_OPEN)(const char *filename);
-typedef int (*CODEC_READ)(snd_stream_t *stream, int bytes, void *buffer);
-typedef void (*CODEC_CLOSE)(snd_stream_t *stream);
-
-// Codec data structure
-struct snd_codec_s
-{
-	char *ext;
-	CODEC_LOAD load;
-	CODEC_OPEN open;
-	CODEC_READ read;
-	CODEC_CLOSE close;
-	snd_codec_t *next;
-};
-
-// Codec management
-void S_CodecInit( void );
-void S_CodecShutdown( void );
-void S_CodecRegister(snd_codec_t *codec);
-void *S_CodecLoad(const char *filename, snd_info_t *info);
-snd_stream_t *S_CodecOpenStream(const char *filename);
-void S_CodecCloseStream(snd_stream_t *stream);
-int S_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
-
-// Util functions (used by codecs)
-snd_stream_t *S_CodecUtilOpen(const char *filename, snd_codec_t *codec);
-void S_CodecUtilClose(snd_stream_t **stream);
-
-// WAV Codec
-extern snd_codec_t wav_codec;
-void *S_WAV_CodecLoad(const char *filename, snd_info_t *info);
-snd_stream_t *S_WAV_CodecOpenStream(const char *filename);
-void S_WAV_CodecCloseStream(snd_stream_t *stream);
-int S_WAV_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
-
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+Copyright (C) 2005 Stuart Dalton (badcdev@gmail.com)
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
+
+#ifndef _SND_CODEC_H_
+#define _SND_CODEC_H_
+
+#include "../qcommon/q_shared.h"
+#include "../qcommon/qcommon.h"
+
+typedef struct snd_info_s
+{
+	int rate;
+	int width;
+	int channels;
+	int samples;
+	int size;
+	int dataofs;
+} snd_info_t;
+
+typedef struct snd_codec_s snd_codec_t;
+
+typedef struct snd_stream_s
+{
+	snd_codec_t *codec;
+	fileHandle_t file;
+	snd_info_t info;
+	int length;
+	int pos;
+	void *ptr;
+} snd_stream_t;
+
+// Codec functions
+typedef void *(*CODEC_LOAD)(const char *filename, snd_info_t *info);
+typedef snd_stream_t *(*CODEC_OPEN)(const char *filename);
+typedef int (*CODEC_READ)(snd_stream_t *stream, int bytes, void *buffer);
+typedef void (*CODEC_CLOSE)(snd_stream_t *stream);
+
+// Codec data structure
+struct snd_codec_s
+{
+	const char *ext;
+	CODEC_LOAD load;
+	CODEC_OPEN open;
+	CODEC_READ read;
+	CODEC_CLOSE close;
+	snd_codec_t *next;
+};
+
+// Codec management
+void S_CodecInit( void );
+void S_CodecShutdown( void );
+void *S_CodecLoad(const char *filename, snd_info_t *info);
+snd_stream_t *S_CodecOpenStream(const char *filename);
+void S_CodecCloseStream(snd_stream_t *stream);
+int S_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
+
+// Util functions (used by codecs)
+snd_stream_t *S_CodecUtilOpen(const char *filename, snd_codec_t *codec);
+void S_CodecUtilClose(snd_stream_t **stream);
+
+// WAV Codec
+extern snd_codec_t wav_codec;
+void *S_WAV_CodecLoad(const char *filename, snd_info_t *info);
+snd_stream_t *S_WAV_CodecOpenStream(const char *filename);
+void S_WAV_CodecCloseStream(snd_stream_t *stream);
+int S_WAV_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
+
 // Ogg Vorbis codec
-#ifdef USE_CODEC_VORBIS
+#ifdef USE_OGG_VORBIS
 extern snd_codec_t ogg_codec;
 void *S_OGG_CodecLoad(const char *filename, snd_info_t *info);
 snd_stream_t *S_OGG_CodecOpenStream(const char *filename);
 void S_OGG_CodecCloseStream(snd_stream_t *stream);
 int S_OGG_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
-#endif // USE_CODEC_VORBIS
-
-// Ogg Opus codec
-#ifdef USE_CODEC_OPUS
-extern snd_codec_t opus_codec;
-void *S_OggOpus_CodecLoad(const char *filename, snd_info_t *info);
-snd_stream_t *S_OggOpus_CodecOpenStream(const char *filename);
-void S_OggOpus_CodecCloseStream(snd_stream_t *stream);
-int S_OggOpus_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
-#endif // USE_CODEC_OPUS
-
-#endif // !_SND_CODEC_H_
+#endif // USE_OGG_VORBIS
+
+#endif // !_SND_CODEC_H_

```

### `openarena-engine`  — sha256 `d67ae500fef5...`, 3754 bytes

_Diff stat: +9 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec.h	2026-04-16 20:02:25.176455100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_codec.h	2026-04-16 22:48:25.735378500 +0100
@@ -104,4 +104,13 @@
 int S_OggOpus_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer);
 #endif // USE_CODEC_OPUS
 
+// XMP (tracker music) codec
+#ifdef USE_CODEC_XMP
+extern snd_codec_t xmp_codec;
+extern snd_codec_t xmp_mod_codec;
+extern snd_codec_t xmp_xm_codec;
+extern snd_codec_t xmp_it_codec;
+extern snd_codec_t xmp_s3m_codec;
+#endif // USE_CODEC_XMP
+
 #endif // !_SND_CODEC_H_

```
