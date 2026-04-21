# Diff: `code/client/snd_codec.c`
**Canonical:** `wolfcamql-src` (sha256 `d209030598c7...`, 5108 bytes)

## Variants

### `ioquake3`  — sha256 `83cdd42f42a4...`, 5106 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec.c	2026-04-16 20:02:25.176455100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_codec.c	2026-04-16 20:02:21.531570600 +0100
@@ -40,7 +40,7 @@
 	snd_codec_t *orgCodec = NULL;
 	qboolean	orgNameFailed = qfalse;
 	char		localName[ MAX_QPATH ];
-	const char 	*ext;
+	const char	*ext;
 	char		altName[ MAX_QPATH ];
 	void		*rtn = NULL;
 
@@ -103,7 +103,7 @@
 			if( orgNameFailed )
 			{
 				Com_DPrintf(S_COLOR_YELLOW "WARNING: %s not present, using %s instead\n",
-							filename, altName );
+						filename, altName );
 			}
 
 			return rtn;

```

### `quake3e`  — sha256 `958eff369edb...`, 5359 bytes

_Diff stat: +68 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec.c	2026-04-16 20:02:25.176455100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_codec.c	2026-04-16 20:02:26.915520500 +0100
@@ -26,6 +26,8 @@
 
 static snd_codec_t *codecs;
 
+static void S_CodecRegister( snd_codec_t *codec );
+
 /*
 =================
 S_CodecGetSound
@@ -34,40 +36,40 @@
 then tries all supported codecs.
 =================
 */
-static void *S_CodecGetSound(const char *filename, snd_info_t *info)
+static void *S_CodecGetSound( const char *filename, snd_info_t *info )
 {
 	snd_codec_t *codec;
 	snd_codec_t *orgCodec = NULL;
 	qboolean	orgNameFailed = qfalse;
 	char		localName[ MAX_QPATH ];
-	const char 	*ext;
+	const char	*ext;
 	char		altName[ MAX_QPATH ];
 	void		*rtn = NULL;
 
-	Q_strncpyz(localName, filename, MAX_QPATH);
+	Q_strncpyz( localName, filename, sizeof( localName ) );
 
-	ext = COM_GetExtension(localName);
+	ext = COM_GetExtension( localName );
 
-	if( *ext )
+	if ( *ext )
 	{
 		// Look for the correct loader and use it
-		for( codec = codecs; codec; codec = codec->next )
+		for ( codec = codecs; codec; codec = codec->next )
 		{
-			if( !Q_stricmp( ext, codec->ext ) )
+			if ( !Q_stricmp( ext, codec->ext ) )
 			{
 				// Load
-				if( info )
-					rtn = codec->load(localName, info);
+				if ( info )
+					rtn = codec->load( localName, info );
 				else
-					rtn = codec->open(localName);
+					rtn = codec->open( localName );
 				break;
 			}
 		}
 
 		// A loader was found
-		if( codec )
+		if ( codec )
 		{
-			if( !rtn )
+			if ( !rtn )
 			{
 				// Loader failed, most likely because the file isn't there;
 				// try again without the extension
@@ -85,108 +87,122 @@
 
 	// Try and find a suitable match using all
 	// the sound codecs supported
-	for( codec = codecs; codec; codec = codec->next )
+	for ( codec = codecs; codec; codec = codec->next )
 	{
-		if( codec == orgCodec )
+		if ( codec == orgCodec )
 			continue;
 
-		Com_sprintf( altName, sizeof (altName), "%s.%s", localName, codec->ext );
+		Com_sprintf( altName, sizeof( altName ), "%s.%s", localName, codec->ext );
 
 		// Load
-		if( info )
-			rtn = codec->load(altName, info);
+		if ( info )
+			rtn = codec->load( altName, info );
 		else
-			rtn = codec->open(altName);
+			rtn = codec->open( altName );
 
-		if( rtn )
+		if ( rtn )
 		{
-			if( orgNameFailed )
+			if ( orgNameFailed )
 			{
-				Com_DPrintf(S_COLOR_YELLOW "WARNING: %s not present, using %s instead\n",
-							filename, altName );
+				Com_DPrintf( S_COLOR_YELLOW "WARNING: %s not present, using %s instead\n",
+					filename, altName );
 			}
 
 			return rtn;
 		}
 	}
 
-	Com_Printf(S_COLOR_YELLOW "WARNING: Failed to %s sound %s!\n", info ? "load" : "open", filename);
+	Com_DPrintf( S_COLOR_YELLOW "WARNING: Failed to %s sound %s!\n", info ? "load" : "open", filename );
 
 	return NULL;
 }
 
+
 /*
 =================
 S_CodecInit
 =================
 */
-void S_CodecInit(void)
+void S_CodecInit( void )
 {
 	codecs = NULL;
 
-#ifdef USE_CODEC_OPUS
-	S_CodecRegister(&opus_codec);
+#ifdef USE_OGG_VORBIS
+	S_CodecRegister( &ogg_codec );
 #endif
 
-#ifdef USE_CODEC_VORBIS
-	S_CodecRegister(&ogg_codec);
-#endif
-
-// Register wav codec last so that it is always tried first when a file extension was not found
-	S_CodecRegister(&wav_codec);
+	// Register wav codec last so that it is always tried first when a file extension was not found
+	S_CodecRegister( &wav_codec );
 }
 
+
 /*
 =================
 S_CodecShutdown
 =================
 */
-void S_CodecShutdown(void)
+void S_CodecShutdown( void )
 {
 	codecs = NULL;
 }
 
+
 /*
 =================
 S_CodecRegister
 =================
 */
-void S_CodecRegister(snd_codec_t *codec)
+static void S_CodecRegister( snd_codec_t *codec )
 {
 	codec->next = codecs;
 	codecs = codec;
 }
 
+
 /*
 =================
 S_CodecLoad
 =================
 */
-void *S_CodecLoad(const char *filename, snd_info_t *info)
+void *S_CodecLoad( const char *filename, snd_info_t *info )
 {
-	return S_CodecGetSound(filename, info);
+	return S_CodecGetSound( filename, info );
 }
 
+
 /*
 =================
 S_CodecOpenStream
 =================
 */
-snd_stream_t *S_CodecOpenStream(const char *filename)
+snd_stream_t *S_CodecOpenStream( const char *filename )
 {
-	return S_CodecGetSound(filename, NULL);
+	return S_CodecGetSound( filename, NULL );
 }
 
-void S_CodecCloseStream(snd_stream_t *stream)
+
+/*
+=================
+S_CodecCloseStream
+=================
+*/
+void S_CodecCloseStream( snd_stream_t *stream )
 {
-	stream->codec->close(stream);
+	stream->codec->close( stream );
 }
 
-int S_CodecReadStream(snd_stream_t *stream, int bytes, void *buffer)
+
+/*
+=================
+S_CodecReadStream
+=================
+*/
+int S_CodecReadStream( snd_stream_t *stream, int bytes, void *buffer )
 {
-	return stream->codec->read(stream, bytes, buffer);
+	return stream->codec->read( stream, bytes, buffer );
 }
 
+
 //=======================================================================
 // Util functions (used by codecs)
 
@@ -195,25 +211,25 @@
 S_CodecUtilOpen
 =================
 */
-snd_stream_t *S_CodecUtilOpen(const char *filename, snd_codec_t *codec)
+snd_stream_t *S_CodecUtilOpen( const char *filename, snd_codec_t *codec )
 {
 	snd_stream_t *stream;
 	fileHandle_t hnd;
 	int length;
 
 	// Try to open the file
-	length = FS_FOpenFileRead(filename, &hnd, qtrue);
-	if(!hnd)
+	length = FS_FOpenFileRead( filename, &hnd, qtrue );
+	if ( hnd == FS_INVALID_HANDLE )
 	{
-		Com_DPrintf("Can't read sound file %s\n", filename);
+		Com_DPrintf( "Can't read sound file %s\n", filename );
 		return NULL;
 	}
 
 	// Allocate a stream
-	stream = Z_Malloc(sizeof(snd_stream_t));
-	if(!stream)
+	stream = Z_Malloc( sizeof( snd_stream_t ) );
+	if ( !stream )
 	{
-		FS_FCloseFile(hnd);
+		FS_FCloseFile( hnd );
 		return NULL;
 	}
 
@@ -229,9 +245,9 @@
 S_CodecUtilClose
 =================
 */
-void S_CodecUtilClose(snd_stream_t **stream)
+void S_CodecUtilClose( snd_stream_t **stream )
 {
-	FS_FCloseFile((*stream)->file);
-	Z_Free(*stream);
+	FS_FCloseFile( ( *stream )->file );
+	Z_Free( *stream );
 	*stream = NULL;
 }

```

### `openarena-engine`  — sha256 `b054fcea0837...`, 5303 bytes

_Diff stat: +14 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_codec.c	2026-04-16 20:02:25.176455100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_codec.c	2026-04-16 22:48:25.735378500 +0100
@@ -40,7 +40,7 @@
 	snd_codec_t *orgCodec = NULL;
 	qboolean	orgNameFailed = qfalse;
 	char		localName[ MAX_QPATH ];
-	const char 	*ext;
+	const char	*ext;
 	char		altName[ MAX_QPATH ];
 	void		*rtn = NULL;
 
@@ -103,7 +103,7 @@
 			if( orgNameFailed )
 			{
 				Com_DPrintf(S_COLOR_YELLOW "WARNING: %s not present, using %s instead\n",
-							filename, altName );
+						filename, altName );
 			}
 
 			return rtn;
@@ -120,10 +120,11 @@
 S_CodecInit
 =================
 */
-void S_CodecInit(void)
+void S_CodecInit()
 {
 	codecs = NULL;
 
+
 #ifdef USE_CODEC_OPUS
 	S_CodecRegister(&opus_codec);
 #endif
@@ -134,6 +135,15 @@
 
 // Register wav codec last so that it is always tried first when a file extension was not found
 	S_CodecRegister(&wav_codec);
+
+#ifdef USE_CODEC_XMP
+	S_CodecRegister(&xmp_codec);
+	S_CodecRegister(&xmp_mod_codec);
+	S_CodecRegister(&xmp_s3m_codec);
+	S_CodecRegister(&xmp_xm_codec);
+	S_CodecRegister(&xmp_it_codec);
+#endif
+
 }
 
 /*
@@ -141,7 +151,7 @@
 S_CodecShutdown
 =================
 */
-void S_CodecShutdown(void)
+void S_CodecShutdown()
 {
 	codecs = NULL;
 }

```
