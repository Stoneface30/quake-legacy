# Diff: `code/client/snd_mem.c`
**Canonical:** `wolfcamql-src` (sha256 `cfe8c6ed9c8f...`, 8187 bytes)

## Variants

### `quake3-source`  — sha256 `ea550ce3c9d5...`, 9498 bytes

_Diff stat: +198 / -85 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_mem.c	2026-04-16 20:02:25.179241900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\snd_mem.c	2026-04-16 20:02:19.894095900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,7 +30,6 @@
  *****************************************************************************/
 
 #include "snd_local.h"
-#include "snd_codec.h"
 
 #define DEF_COMSOUNDMEGS "8"
 
@@ -57,7 +56,7 @@
 	inUse += sizeof(sndBuffer);
 }
 
-sndBuffer*	SND_malloc(void) {
+sndBuffer*	SND_malloc() {
 	sndBuffer *v;
 redo:
 	if (freelist == NULL) {
@@ -74,7 +73,7 @@
 	return v;
 }
 
-void SND_setup(void) {
+void SND_setup() {
 	sndBuffer *p, *q;
 	cvar_t	*cv;
 	int scs;
@@ -84,20 +83,8 @@
 	scs = (cv->integer*1536);
 
 	buffer = malloc(scs*sizeof(sndBuffer) );
-	if (!buffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound memory", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound memory\n", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-
 	// allocate the stack based hunk allocator
 	sfxScratchBuffer = malloc(SND_CHUNK_SIZE * sizeof(short) * 4);	//Hunk_Alloc(SND_CHUNK_SIZE * sizeof(short) * 4);
-	if (!sfxScratchBuffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound scratch buffer", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound scratch buffer\n", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-
 	sfxScratchPointer = NULL;
 
 	inUse = scs*sizeof(sndBuffer);
@@ -112,12 +99,137 @@
 	Com_Printf("Sound memory manager started\n");
 }
 
-void SND_shutdown(void)
+/*
+===============================================================================
+
+WAV loading
+
+===============================================================================
+*/
+
+static	byte	*data_p;
+static	byte 	*iff_end;
+static	byte 	*last_chunk;
+static	byte 	*iff_data;
+static	int 	iff_chunk_len;
+
+static short GetLittleShort(void)
+{
+	short val = 0;
+	val = *data_p;
+	val = val + (*(data_p+1)<<8);
+	data_p += 2;
+	return val;
+}
+
+static int GetLittleLong(void)
+{
+	int val = 0;
+	val = *data_p;
+	val = val + (*(data_p+1)<<8);
+	val = val + (*(data_p+2)<<16);
+	val = val + (*(data_p+3)<<24);
+	data_p += 4;
+	return val;
+}
+
+static void FindNextChunk(char *name)
 {
-	free(sfxScratchBuffer);
-	free(buffer);
+	while (1)
+	{
+		data_p=last_chunk;
+
+		if (data_p >= iff_end)
+		{	// didn't find the chunk
+			data_p = NULL;
+			return;
+		}
+		
+		data_p += 4;
+		iff_chunk_len = GetLittleLong();
+		if (iff_chunk_len < 0)
+		{
+			data_p = NULL;
+			return;
+		}
+		data_p -= 8;
+		last_chunk = data_p + 8 + ( (iff_chunk_len + 1) & ~1 );
+		if (!strncmp((char *)data_p, name, 4))
+			return;
+	}
+}
+
+static void FindChunk(char *name)
+{
+	last_chunk = iff_data;
+	FindNextChunk (name);
+}
+
+/*
+============
+GetWavinfo
+============
+*/
+static wavinfo_t GetWavinfo (char *name, byte *wav, int wavlength)
+{
+	wavinfo_t	info;
+
+	Com_Memset (&info, 0, sizeof(info));
+
+	if (!wav)
+		return info;
+		
+	iff_data = wav;
+	iff_end = wav + wavlength;
+
+// find "RIFF" chunk
+	FindChunk("RIFF");
+	if (!(data_p && !strncmp((char *)data_p+8, "WAVE", 4)))
+	{
+		Com_Printf("Missing RIFF/WAVE chunks\n");
+		return info;
+	}
+
+// get "fmt " chunk
+	iff_data = data_p + 12;
+// DumpChunks ();
+
+	FindChunk("fmt ");
+	if (!data_p)
+	{
+		Com_Printf("Missing fmt chunk\n");
+		return info;
+	}
+	data_p += 8;
+	info.format = GetLittleShort();
+	info.channels = GetLittleShort();
+	info.rate = GetLittleLong();
+	data_p += 4+2;
+	info.width = GetLittleShort() / 8;
+
+	if (info.format != 1)
+	{
+		Com_Printf("Microsoft PCM format only\n");
+		return info;
+	}
+
+
+// find data chunk
+	FindChunk("data");
+	if (!data_p)
+	{
+		Com_Printf("Missing data chunk\n");
+		return info;
+	}
+
+	data_p += 4;
+	info.samples = GetLittleLong () / info.width;
+	info.dataofs = data_p - wav;
+
+	return info;
 }
 
+
 /*
 ================
 ResampleSfx
@@ -125,53 +237,47 @@
 resample / decimate to the current source rate
 ================
 */
-static int ResampleSfx( sfx_t *sfx, int channels, int inrate, int inwidth, int samples, byte *data, qboolean compressed ) {
+static void ResampleSfx( sfx_t *sfx, int inrate, int inwidth, byte *data, qboolean compressed ) {
 	int		outcount;
 	int		srcsample;
 	float	stepscale;
-	int		i, j;
+	int		i;
 	int		sample, samplefrac, fracstep;
 	int			part;
 	sndBuffer	*chunk;
 	
 	stepscale = (float)inrate / dma.speed;	// this is usually 0.5, 1, or 2
 
-	outcount = samples / stepscale;
+	outcount = sfx->soundLength / stepscale;
+	sfx->soundLength = outcount;
 
-	srcsample = 0;
 	samplefrac = 0;
-	fracstep = stepscale * 256 * channels;
+	fracstep = stepscale * 256;
 	chunk = sfx->soundData;
 
 	for (i=0 ; i<outcount ; i++)
 	{
-		srcsample += samplefrac >> 8;
-		samplefrac &= 255;
+		srcsample = samplefrac >> 8;
 		samplefrac += fracstep;
-		for (j=0 ; j<channels ; j++)
-		{
-			if( inwidth == 2 ) {
-				sample = ( ((short *)data)[srcsample+j] );
+		if( inwidth == 2 ) {
+			sample = LittleShort ( ((short *)data)[srcsample] );
+		} else {
+			sample = (int)( (unsigned char)(data[srcsample]) - 128) << 8;
+		}
+		part  = (i&(SND_CHUNK_SIZE-1));
+		if (part == 0) {
+			sndBuffer	*newchunk;
+			newchunk = SND_malloc();
+			if (chunk == NULL) {
+				sfx->soundData = newchunk;
 			} else {
-				sample = (unsigned int)( (unsigned char)(data[srcsample+j]) - 128) << 8;
-			}
-			part = (i*channels+j)&(SND_CHUNK_SIZE-1);
-			if (part == 0) {
-				sndBuffer       *newchunk;
-				newchunk = SND_malloc();
-				if (chunk == NULL) {
-					sfx->soundData = newchunk;
-				} else {
-					chunk->next = newchunk;
-				}
-				chunk = newchunk;
+				chunk->next = newchunk;
 			}
-
-			chunk->sndChunk[part] = sample;
+			chunk = newchunk;
 		}
-	}
 
-	return outcount;
+		chunk->sndChunk[part] = sample;
+	}
 }
 
 /*
@@ -181,39 +287,35 @@
 resample / decimate to the current source rate
 ================
 */
-static int ResampleSfxRaw( short *sfx, int channels, int inrate, int inwidth, int samples, byte *data ) {
+static int ResampleSfxRaw( short *sfx, int inrate, int inwidth, int samples, byte *data ) {
 	int			outcount;
 	int			srcsample;
 	float		stepscale;
-	int			i, j;
+	int			i;
 	int			sample, samplefrac, fracstep;
 	
 	stepscale = (float)inrate / dma.speed;	// this is usually 0.5, 1, or 2
 
 	outcount = samples / stepscale;
 
-	srcsample = 0;
 	samplefrac = 0;
-	fracstep = stepscale * 256 * channels;
+	fracstep = stepscale * 256;
 
 	for (i=0 ; i<outcount ; i++)
 	{
-		srcsample += samplefrac >> 8;
-		samplefrac &= 255;
+		srcsample = samplefrac >> 8;
 		samplefrac += fracstep;
-		for (j=0 ; j<channels ; j++)
-		{
-			if( inwidth == 2 ) {
-				sample = LittleShort ( ((short *)data)[srcsample+j] );
-			} else {
-				sample = (int)( (unsigned char)(data[srcsample+j]) - 128) << 8;
-			}
-			sfx[i*channels+j] = sample;
+		if( inwidth == 2 ) {
+			sample = LittleShort ( ((short *)data)[srcsample] );
+		} else {
+			sample = (int)( (unsigned char)(data[srcsample]) - 128) << 8;
 		}
+		sfx[i] = sample;
 	}
 	return outcount;
 }
 
+
 //=============================================================================
 
 /*
@@ -228,26 +330,38 @@
 {
 	byte	*data;
 	short	*samples;
-	snd_info_t	info;
-//	int		size;
+	wavinfo_t	info;
+	int		size;
+
+	// player specific sounds are never directly loaded
+	if ( sfx->soundName[0] == '*') {
+		return qfalse;
+	}
 
 	// load it in
-	data = S_CodecLoad(sfx->soundName, &info);
-	if(!data)
+	size = FS_ReadFile( sfx->soundName, (void **)&data );
+	if ( !data ) {
 		return qfalse;
+	}
+
+	info = GetWavinfo( sfx->soundName, data, size );
+	if ( info.channels != 1 ) {
+		Com_Printf ("%s is a stereo wav file\n", sfx->soundName);
+		FS_FreeFile (data);
+		return qfalse;
+	}
 
 	if ( info.width == 1 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit sound file\n", sfx->soundName);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit wav file\n", sfx->soundName);
 	}
 
 	if ( info.rate != 22050 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s (%.1fkHz) is not a 22kHz sound file\n", sfx->soundName, (float)info.rate / 1000.0);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is not a 22kHz wav file\n", sfx->soundName);
 	}
 
-	samples = Hunk_AllocateTempMemory(info.channels * info.samples * sizeof(short) * 2);
+	samples = Hunk_AllocateTempMemory(info.samples * sizeof(short) * 2);
 
-	//sfx->lastTimeUsed = Com_Milliseconds()+1;
-	sfx->lastTimeUsed = S_Milliseconds()+1;
+	sfx->lastTimeUsed = Com_Milliseconds()+1;
 
 	// each of these compression schemes works just fine
 	// but the 16bit quality is much nicer and with a local
@@ -255,37 +369,36 @@
 	// manager to do the right thing for us and page
 	// sound in as needed
 
-	if( info.channels == 1 && sfx->soundCompressed == qtrue) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_ADPCM;
+	if( sfx->soundCompressed == qtrue) {
+		sfx->soundCompressionMethod = 1;
 		sfx->soundData = NULL;
-		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, data + info.dataofs );
+		sfx->soundLength = ResampleSfxRaw( samples, info.rate, info.width, info.samples, (data + info.dataofs) );
 		S_AdpcmEncodeSound(sfx, samples);
 #if 0
-	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*16) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_MULAW;
+	} else if (info.samples>(SND_CHUNK_SIZE*16) && info.width >1) {
+		sfx->soundCompressionMethod = 3;
 		sfx->soundData = NULL;
-		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
+		sfx->soundLength = ResampleSfxRaw( samples, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeMuLaw( sfx, samples);
-	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*6400) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_DAUB4;
+	} else if (info.samples>(SND_CHUNK_SIZE*6400) && info.width >1) {
+		sfx->soundCompressionMethod = 2;
 		sfx->soundData = NULL;
-		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
+		sfx->soundLength = ResampleSfxRaw( samples, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeWavelet( sfx, samples);
 #endif
 	} else {
-		sfx->soundCompressionMethod = SND_COMPRESSION_16BIT;
+		sfx->soundCompressionMethod = 0;
+		sfx->soundLength = info.samples;
 		sfx->soundData = NULL;
-		sfx->soundLength = ResampleSfx( sfx, info.channels, info.rate, info.width, info.samples, data + info.dataofs, qfalse );
+		ResampleSfx( sfx, info.rate, info.width, data + info.dataofs, qfalse );
 	}
-
-	sfx->soundChannels = info.channels;
-
+	
 	Hunk_FreeTempMemory(samples);
-	Hunk_FreeTempMemory(data);
+	FS_FreeFile( data );
 
 	return qtrue;
 }
 
-void S_DisplayFreeMemory(void) {
+void S_DisplayFreeMemory() {
 	Com_Printf("%d bytes free sound buffer memory, %d total used\n", inUse, totalInUse);
 }

```

### `ioquake3`  — sha256 `29e517936e51...`, 7471 bytes

_Diff stat: +11 / -24 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_mem.c	2026-04-16 20:02:25.179241900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_mem.c	2026-04-16 20:02:21.533570500 +0100
@@ -84,20 +84,8 @@
 	scs = (cv->integer*1536);
 
 	buffer = malloc(scs*sizeof(sndBuffer) );
-	if (!buffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound memory", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound memory\n", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-
 	// allocate the stack based hunk allocator
 	sfxScratchBuffer = malloc(SND_CHUNK_SIZE * sizeof(short) * 4);	//Hunk_Alloc(SND_CHUNK_SIZE * sizeof(short) * 4);
-	if (!sfxScratchBuffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound scratch buffer", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound scratch buffer\n", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-
 	sfxScratchPointer = NULL;
 
 	inUse = scs*sizeof(sndBuffer);
@@ -114,8 +102,8 @@
 
 void SND_shutdown(void)
 {
-	free(sfxScratchBuffer);
-	free(buffer);
+		free(sfxScratchBuffer);
+		free(buffer);
 }
 
 /*
@@ -157,7 +145,7 @@
 			}
 			part = (i*channels+j)&(SND_CHUNK_SIZE-1);
 			if (part == 0) {
-				sndBuffer       *newchunk;
+				sndBuffer	*newchunk;
 				newchunk = SND_malloc();
 				if (chunk == NULL) {
 					sfx->soundData = newchunk;
@@ -237,17 +225,16 @@
 		return qfalse;
 
 	if ( info.width == 1 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit sound file\n", sfx->soundName);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit audio file\n", sfx->soundName);
 	}
 
 	if ( info.rate != 22050 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s (%.1fkHz) is not a 22kHz sound file\n", sfx->soundName, (float)info.rate / 1000.0);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is not a 22kHz audio file\n", sfx->soundName);
 	}
 
 	samples = Hunk_AllocateTempMemory(info.channels * info.samples * sizeof(short) * 2);
 
-	//sfx->lastTimeUsed = Com_Milliseconds()+1;
-	sfx->lastTimeUsed = S_Milliseconds()+1;
+	sfx->lastTimeUsed = Com_Milliseconds()+1;
 
 	// each of these compression schemes works just fine
 	// but the 16bit quality is much nicer and with a local
@@ -256,30 +243,30 @@
 	// sound in as needed
 
 	if( info.channels == 1 && sfx->soundCompressed == qtrue) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_ADPCM;
+		sfx->soundCompressionMethod = 1;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, data + info.dataofs );
 		S_AdpcmEncodeSound(sfx, samples);
 #if 0
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*16) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_MULAW;
+		sfx->soundCompressionMethod = 3;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeMuLaw( sfx, samples);
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*6400) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_DAUB4;
+		sfx->soundCompressionMethod = 2;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeWavelet( sfx, samples);
 #endif
 	} else {
-		sfx->soundCompressionMethod = SND_COMPRESSION_16BIT;
+		sfx->soundCompressionMethod = 0;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfx( sfx, info.channels, info.rate, info.width, info.samples, data + info.dataofs, qfalse );
 	}
 
 	sfx->soundChannels = info.channels;
-
+	
 	Hunk_FreeTempMemory(samples);
 	Hunk_FreeTempMemory(data);
 

```

### `quake3e`  — sha256 `a9615ad4ec88...`, 8530 bytes

_Diff stat: +77 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_mem.c	2026-04-16 20:02:25.179241900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_mem.c	2026-04-16 20:02:26.917521900 +0100
@@ -51,19 +51,21 @@
 sfx_t *sfxScratchPointer = NULL;
 int	   sfxScratchIndex = 0;
 
-void	SND_free(sndBuffer *v) {
+
+void SND_free( sndBuffer *v )
+{
 	*(sndBuffer **)v = freelist;
 	freelist = (sndBuffer*)v;
 	inUse += sizeof(sndBuffer);
+	totalInUse -= sizeof(sndBuffer); // -EC-
 }
 
-sndBuffer*	SND_malloc(void) {
+
+sndBuffer *SND_malloc( void ) {
 	sndBuffer *v;
-redo:
-	if (freelist == NULL) {
+
+	while ( freelist == NULL )
 		S_FreeOldestSound();
-		goto redo;
-	}
 
 	inUse -= sizeof(sndBuffer);
 	totalInUse += sizeof(sndBuffer);
@@ -74,48 +76,87 @@
 	return v;
 }
 
-void SND_setup(void) {
+
+void SND_setup( void ) 
+{
 	sndBuffer *p, *q;
 	cvar_t	*cv;
-	int scs;
+	int scs, sz;
+	static int old_scs = -1;
 
 	cv = Cvar_Get( "com_soundMegs", DEF_COMSOUNDMEGS, CVAR_LATCH | CVAR_ARCHIVE );
+	Cvar_CheckRange( cv, "1", "512", CV_INTEGER );
+	Cvar_SetDescription( cv, "Amount of memory (RAM) assigned to the sound buffer (in MB)." );
 
-	scs = (cv->integer*1536);
+	scs = ( cv->integer * /*1536*/ 12 * dma.speed ) / 22050;
+	scs *= 128;
 
-	buffer = malloc(scs*sizeof(sndBuffer) );
-	if (!buffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound memory", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-		return;
+	sz = scs * sizeof( sndBuffer );
+
+	// realloc buffer if com_soundMegs changed
+	if ( old_scs != scs ) {
+		if ( buffer != NULL ) {
+			free( buffer );
+			buffer = NULL;
+		}
+		old_scs = scs;
+	}
+
+	if ( buffer == NULL ) {
+		buffer = malloc( sz );
+	}
+
+	// -EC-
+	if ( buffer == NULL ) {
+		Com_Error( ERR_FATAL, "Error allocating %i bytes for sound buffer", sz );
+	} else {
+		Com_Memset( buffer, 0, sz );
 	}
-	Com_Printf("%f MB for sound memory\n", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
+
+	sz = SND_CHUNK_SIZE * sizeof(short) * 4;
 
 	// allocate the stack based hunk allocator
-	sfxScratchBuffer = malloc(SND_CHUNK_SIZE * sizeof(short) * 4);	//Hunk_Alloc(SND_CHUNK_SIZE * sizeof(short) * 4);
-	if (!sfxScratchBuffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound scratch buffer", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-		return;
+	// -EC-
+	if ( sfxScratchBuffer == NULL ) {
+		sfxScratchBuffer = malloc( sz );	//Hunk_Alloc(SND_CHUNK_SIZE * sizeof(short) * 4);
+	}
+
+	// clear scratch buffer -EC-
+	if ( sfxScratchBuffer == NULL ) {
+		Com_Error( ERR_FATAL, "Error allocating %i bytes for sfxScratchBuffer",	sz );
+	} else {
+		Com_Memset( sfxScratchBuffer, 0, sz );
 	}
-	Com_Printf("%f MB for sound scratch buffer\n", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
 
 	sfxScratchPointer = NULL;
 
-	inUse = scs*sizeof(sndBuffer);
-	p = buffer;;
+	inUse = scs * sizeof( sndBuffer );
+	totalInUse = 0; // -EC-
+
+	p = buffer;
 	q = p + scs;
 	while (--q > p)
 		*(sndBuffer **)q = q-1;
-	
+
 	*(sndBuffer **)q = NULL;
 	freelist = p + scs - 1;
 
-	Com_Printf("Sound memory manager started\n");
+	Com_Printf( "Sound memory manager started\n" );
 }
 
-void SND_shutdown(void)
+
+void SND_shutdown( void )
 {
-	free(sfxScratchBuffer);
-	free(buffer);
+	if ( sfxScratchBuffer ) 
+	{
+		free( sfxScratchBuffer );
+		sfxScratchBuffer = NULL;
+	}
+	if ( buffer ) 
+	{
+		free( buffer );
+		buffer = NULL;
+	}
 }
 
 /*
@@ -157,7 +198,7 @@
 			}
 			part = (i*channels+j)&(SND_CHUNK_SIZE-1);
 			if (part == 0) {
-				sndBuffer       *newchunk;
+				sndBuffer	*newchunk;
 				newchunk = SND_malloc();
 				if (chunk == NULL) {
 					sfx->soundData = newchunk;
@@ -237,17 +278,16 @@
 		return qfalse;
 
 	if ( info.width == 1 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit sound file\n", sfx->soundName);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit audio file\n", sfx->soundName);
 	}
 
 	if ( info.rate != 22050 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s (%.1fkHz) is not a 22kHz sound file\n", sfx->soundName, (float)info.rate / 1000.0);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is not a 22kHz audio file\n", sfx->soundName);
 	}
 
-	samples = Hunk_AllocateTempMemory(info.channels * info.samples * sizeof(short) * 2);
+	samples = Hunk_AllocateTempMemory(info.samples * sizeof(short) * 2);
 
-	//sfx->lastTimeUsed = Com_Milliseconds()+1;
-	sfx->lastTimeUsed = S_Milliseconds()+1;
+	sfx->lastTimeUsed = s_soundtime + 1; // Com_Milliseconds()+1
 
 	// each of these compression schemes works just fine
 	// but the 16bit quality is much nicer and with a local
@@ -256,30 +296,30 @@
 	// sound in as needed
 
 	if( info.channels == 1 && sfx->soundCompressed == qtrue) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_ADPCM;
+		sfx->soundCompressionMethod = 1;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, data + info.dataofs );
 		S_AdpcmEncodeSound(sfx, samples);
 #if 0
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*16) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_MULAW;
+		sfx->soundCompressionMethod = 3;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeMuLaw( sfx, samples);
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*6400) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_DAUB4;
+		sfx->soundCompressionMethod = 2;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeWavelet( sfx, samples);
 #endif
 	} else {
-		sfx->soundCompressionMethod = SND_COMPRESSION_16BIT;
+		sfx->soundCompressionMethod = 0;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfx( sfx, info.channels, info.rate, info.width, info.samples, data + info.dataofs, qfalse );
 	}
 
 	sfx->soundChannels = info.channels;
-
+	
 	Hunk_FreeTempMemory(samples);
 	Hunk_FreeTempMemory(data);
 

```

### `openarena-engine`  — sha256 `ddc5c7a01d69...`, 7443 bytes

_Diff stat: +17 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_mem.c	2026-04-16 20:02:25.179241900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_mem.c	2026-04-16 22:48:25.737379400 +0100
@@ -84,20 +84,8 @@
 	scs = (cv->integer*1536);
 
 	buffer = malloc(scs*sizeof(sndBuffer) );
-	if (!buffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound memory", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound memory\n", (float)(scs * sizeof(sndBuffer)) / (1024.0 * 1024.0));
-
 	// allocate the stack based hunk allocator
 	sfxScratchBuffer = malloc(SND_CHUNK_SIZE * sizeof(short) * 4);	//Hunk_Alloc(SND_CHUNK_SIZE * sizeof(short) * 4);
-	if (!sfxScratchBuffer) {
-		Com_Error(ERR_DROP, "couldn't allocate %f MB for sound scratch buffer", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-		return;
-	}
-	Com_Printf("%f MB for sound scratch buffer\n", (float)(SND_CHUNK_SIZE * sizeof(short) * 4) / (1024.0 * 1024.0));
-
 	sfxScratchPointer = NULL;
 
 	inUse = scs*sizeof(sndBuffer);
@@ -114,8 +102,8 @@
 
 void SND_shutdown(void)
 {
-	free(sfxScratchBuffer);
-	free(buffer);
+		free(sfxScratchBuffer);
+		free(buffer);
 }
 
 /*
@@ -138,26 +126,24 @@
 
 	outcount = samples / stepscale;
 
-	srcsample = 0;
 	samplefrac = 0;
 	fracstep = stepscale * 256 * channels;
 	chunk = sfx->soundData;
 
 	for (i=0 ; i<outcount ; i++)
 	{
-		srcsample += samplefrac >> 8;
-		samplefrac &= 255;
+		srcsample = samplefrac >> 8;
 		samplefrac += fracstep;
 		for (j=0 ; j<channels ; j++)
 		{
 			if( inwidth == 2 ) {
 				sample = ( ((short *)data)[srcsample+j] );
 			} else {
-				sample = (unsigned int)( (unsigned char)(data[srcsample+j]) - 128) << 8;
+				sample = (int)( (unsigned char)(data[srcsample+j]) - 128) << 8;
 			}
 			part = (i*channels+j)&(SND_CHUNK_SIZE-1);
 			if (part == 0) {
-				sndBuffer       *newchunk;
+				sndBuffer	*newchunk;
 				newchunk = SND_malloc();
 				if (chunk == NULL) {
 					sfx->soundData = newchunk;
@@ -192,14 +178,12 @@
 
 	outcount = samples / stepscale;
 
-	srcsample = 0;
 	samplefrac = 0;
 	fracstep = stepscale * 256 * channels;
 
 	for (i=0 ; i<outcount ; i++)
 	{
-		srcsample += samplefrac >> 8;
-		samplefrac &= 255;
+		srcsample = samplefrac >> 8;
 		samplefrac += fracstep;
 		for (j=0 ; j<channels ; j++)
 		{
@@ -236,18 +220,19 @@
 	if(!data)
 		return qfalse;
 
+	// leilei - don't be so paranoid about these
+#if 	0
 	if ( info.width == 1 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit sound file\n", sfx->soundName);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is a 8 bit audio file\n", sfx->soundName);
 	}
 
 	if ( info.rate != 22050 ) {
-		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s (%.1fkHz) is not a 22kHz sound file\n", sfx->soundName, (float)info.rate / 1000.0);
+		Com_DPrintf(S_COLOR_YELLOW "WARNING: %s is not a 22kHz audio file\n", sfx->soundName);
 	}
-
+#endif
 	samples = Hunk_AllocateTempMemory(info.channels * info.samples * sizeof(short) * 2);
 
-	//sfx->lastTimeUsed = Com_Milliseconds()+1;
-	sfx->lastTimeUsed = S_Milliseconds()+1;
+	sfx->lastTimeUsed = Com_Milliseconds()+1;
 
 	// each of these compression schemes works just fine
 	// but the 16bit quality is much nicer and with a local
@@ -256,30 +241,30 @@
 	// sound in as needed
 
 	if( info.channels == 1 && sfx->soundCompressed == qtrue) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_ADPCM;
+		sfx->soundCompressionMethod = 1;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, data + info.dataofs );
 		S_AdpcmEncodeSound(sfx, samples);
 #if 0
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*16) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_MULAW;
+		sfx->soundCompressionMethod = 3;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeMuLaw( sfx, samples);
 	} else if (info.channels == 1 && info.samples>(SND_CHUNK_SIZE*6400) && info.width >1) {
-		sfx->soundCompressionMethod = SND_COMPRESSION_DAUB4;
+		sfx->soundCompressionMethod = 2;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfxRaw( samples, info.channels, info.rate, info.width, info.samples, (data + info.dataofs) );
 		encodeWavelet( sfx, samples);
 #endif
 	} else {
-		sfx->soundCompressionMethod = SND_COMPRESSION_16BIT;
+		sfx->soundCompressionMethod = 0;
 		sfx->soundData = NULL;
 		sfx->soundLength = ResampleSfx( sfx, info.channels, info.rate, info.width, info.samples, data + info.dataofs, qfalse );
 	}
 
 	sfx->soundChannels = info.channels;
-
+	
 	Hunk_FreeTempMemory(samples);
 	Hunk_FreeTempMemory(data);
 

```
