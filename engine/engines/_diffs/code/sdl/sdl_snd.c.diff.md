# Diff: `code/sdl/sdl_snd.c`
**Canonical:** `wolfcamql-src` (sha256 `c9d630013c84...`, 11869 bytes)

## Variants

### `ioquake3`  — sha256 `6c7f593868bf...`, 10814 bytes

_Diff stat: +9 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_snd.c	2026-04-16 20:02:25.266779000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sdl\sdl_snd.c	2026-04-16 20:02:21.618758900 +0100
@@ -32,7 +32,6 @@
 #include "../qcommon/q_shared.h"
 #include "../client/snd_local.h"
 #include "../client/client.h"
-#include "../client/cl_avi.h"
 
 qboolean snd_inited = qfalse;
 
@@ -41,16 +40,11 @@
 cvar_t *s_sdlChannels;
 cvar_t *s_sdlDevSamps;
 cvar_t *s_sdlMixSamps;
-cvar_t *s_sdlWindowsForceDirectSound;
 
 /* The audio callback. All the magic happens here. */
 static int dmapos = 0;
 static int dmasize = 0;
 
-//extern qboolean CL_VideoRecording (void);
-extern cvar_t *cl_freezeDemo;
-extern cvar_t *cl_freezeDemoPauseVideoRecording;
-
 static SDL_AudioDeviceID sdlPlaybackDevice;
 
 #if defined USE_VOIP && SDL_VERSION_ATLEAST( 2, 0, 5 )
@@ -70,11 +64,8 @@
 static void SNDDMA_AudioCallback(void *userdata, Uint8 *stream, int len)
 {
 	int pos = (dmapos * (dma.samplebits/8));
-
-	if (pos >= dmasize) {
-		//Com_Printf("pos (%d) > dmasize (%d)\n", pos, dmasize);
+	if (pos >= dmasize)
 		dmapos = pos = 0;
-	}
 
 	if (!snd_inited)  /* shouldn't happen, but just in case... */
 	{
@@ -92,29 +83,18 @@
 			len1 = tobufend;
 			len2 = len - len1;
 		}
-		if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-			memset(stream, 0, len1);
-		} else {
-			memcpy(stream, dma.buffer + pos, len1);
-		}
-		if (len2 <= 0) {
-			//Com_Printf("len2 <= 0   %d\n", len2);
+		memcpy(stream, dma.buffer + pos, len1);
+		if (len2 <= 0)
 			dmapos += (len1 / (dma.samplebits/8));
-		} else  { /* wraparound? */
-			//Com_Printf("wrap len2 %d\n", len2);
-			if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-				memset(stream + len1, 0, len2);
-			} else {
-				memcpy(stream+len1, dma.buffer, len2);
-			}
+		else  /* wraparound? */
+		{
+			memcpy(stream+len1, dma.buffer, len2);
 			dmapos = (len2 / (dma.samplebits/8));
 		}
 	}
 
-	if (dmapos >= dmasize) {
-		//Com_Printf("dmapos >= dmasize  %d > %d\n", dmapos, dmasize);
+	if (dmapos >= dmasize)
 		dmapos = 0;
-	}
 
 #ifdef USE_SDL_AUDIO_CAPTURE
 	if (sdlMasterGain != 1.0f)
@@ -149,7 +129,6 @@
 		}
 	}
 #endif
-
 }
 
 static struct
@@ -221,14 +200,6 @@
 		s_sdlMixSamps = Cvar_Get("s_sdlMixSamps", "0", CVAR_ARCHIVE);
 	}
 
-	s_sdlWindowsForceDirectSound = Cvar_Get("s_sdlWindowsForceDirectSound", "1", CVAR_ARCHIVE);
-
-#ifdef _WIN32
-	if (s_sdlWindowsForceDirectSound->value) {
-		SDL_setenv("SDL_AUDIODRIVER", "directsound", 1);
-	}
-#endif
-
 	Com_Printf( "SDL_Init( SDL_INIT_AUDIO )... " );
 
 	if (SDL_Init(SDL_INIT_AUDIO) != 0)
@@ -331,7 +302,7 @@
 		spec.samples = VOIP_MAX_PACKET_SAMPLES * 4;
 		sdlCaptureDevice = SDL_OpenAudioDevice(NULL, SDL_TRUE, &spec, NULL, 0);
 		Com_Printf( "SDL capture device %s.\n",
-					(sdlCaptureDevice == 0) ? "failed to open" : "opened");
+				    (sdlCaptureDevice == 0) ? "failed to open" : "opened");
 	}
 
 	sdlMasterGain = 1.0f;
@@ -466,3 +437,4 @@
 #endif
 }
 #endif
+

```

### `quake3e`  — sha256 `e1c7ac8f3cf5...`, 12286 bytes

_Diff stat: +93 / -86 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_snd.c	2026-04-16 20:02:25.266779000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\sdl\sdl_snd.c	2026-04-16 20:02:27.365920300 +0100
@@ -20,10 +20,7 @@
 ===========================================================================
 */
 
-#include <stdlib.h>
-#include <stdio.h>
-
-#ifdef USE_INTERNAL_SDL_HEADERS
+#ifdef USE_LOCAL_HEADERS
 #	include "SDL.h"
 #else
 #	include <SDL.h>
@@ -32,25 +29,19 @@
 #include "../qcommon/q_shared.h"
 #include "../client/snd_local.h"
 #include "../client/client.h"
-#include "../client/cl_avi.h"
 
 qboolean snd_inited = qfalse;
 
+extern cvar_t *s_khz;
 cvar_t *s_sdlBits;
-cvar_t *s_sdlSpeed;
 cvar_t *s_sdlChannels;
 cvar_t *s_sdlDevSamps;
 cvar_t *s_sdlMixSamps;
-cvar_t *s_sdlWindowsForceDirectSound;
 
 /* The audio callback. All the magic happens here. */
 static int dmapos = 0;
 static int dmasize = 0;
 
-//extern qboolean CL_VideoRecording (void);
-extern cvar_t *cl_freezeDemo;
-extern cvar_t *cl_freezeDemoPauseVideoRecording;
-
 static SDL_AudioDeviceID sdlPlaybackDevice;
 
 #if defined USE_VOIP && SDL_VERSION_ATLEAST( 2, 0, 5 )
@@ -70,11 +61,8 @@
 static void SNDDMA_AudioCallback(void *userdata, Uint8 *stream, int len)
 {
 	int pos = (dmapos * (dma.samplebits/8));
-
-	if (pos >= dmasize) {
-		//Com_Printf("pos (%d) > dmasize (%d)\n", pos, dmasize);
+	if (pos >= dmasize)
 		dmapos = pos = 0;
-	}
 
 	if (!snd_inited)  /* shouldn't happen, but just in case... */
 	{
@@ -92,29 +80,18 @@
 			len1 = tobufend;
 			len2 = len - len1;
 		}
-		if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-			memset(stream, 0, len1);
-		} else {
-			memcpy(stream, dma.buffer + pos, len1);
-		}
-		if (len2 <= 0) {
-			//Com_Printf("len2 <= 0   %d\n", len2);
+		memcpy(stream, dma.buffer + pos, len1);
+		if (len2 <= 0)
 			dmapos += (len1 / (dma.samplebits/8));
-		} else  { /* wraparound? */
-			//Com_Printf("wrap len2 %d\n", len2);
-			if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-				memset(stream + len1, 0, len2);
-			} else {
-				memcpy(stream+len1, dma.buffer, len2);
-			}
+		else  /* wraparound? */
+		{
+			memcpy(stream+len1, dma.buffer, len2);
 			dmapos = (len2 / (dma.samplebits/8));
 		}
 	}
 
-	if (dmapos >= dmasize) {
-		//Com_Printf("dmapos >= dmasize  %d > %d\n", dmapos, dmasize);
+	if (dmapos >= dmasize)
 		dmapos = 0;
-	}
 
 #ifdef USE_SDL_AUDIO_CAPTURE
 	if (sdlMasterGain != 1.0f)
@@ -149,13 +126,12 @@
 		}
 	}
 #endif
-
 }
 
-static struct
+static const struct
 {
-	Uint16	enumFormat;
-	char		*stringFormat;
+	uint16_t	enumFormat;
+	const char	*stringFormat;
 } formatToStringTable[ ] =
 {
 	{ AUDIO_U8,     "AUDIO_U8" },
@@ -177,18 +153,18 @@
 */
 static void SNDDMA_PrintAudiospec(const char *str, const SDL_AudioSpec *spec)
 {
-	int		i;
-	char	*fmt = NULL;
+	const char *fmt = NULL;
+	int i;
 
-	Com_Printf("%s:\n", str);
+	Com_Printf( "%s:\n", str );
 
-	for( i = 0; i < formatToStringTableSize; i++ ) {
+	for ( i = 0; i < formatToStringTableSize; i++ ) {
 		if( spec->format == formatToStringTable[ i ].enumFormat ) {
 			fmt = formatToStringTable[ i ].stringFormat;
 		}
 	}
 
-	if( fmt ) {
+	if ( fmt ) {
 		Com_Printf( "  Format:   %s\n", fmt );
 	} else {
 		Com_Printf( "  Format:   " S_COLOR_RED "UNKNOWN\n");
@@ -199,62 +175,79 @@
 	Com_Printf( "  Channels: %d\n", (int) spec->channels );
 }
 
+
+static int SNDDMA_KHzToHz( int khz )
+{
+	switch ( khz )
+	{
+		default:
+		case 22: return 22050;
+		case 48: return 48000;
+		case 44: return 44100;
+		case 11: return 11025;
+		case  8: return  8000;
+	}
+}
+
+
 /*
 ===============
 SNDDMA_Init
 ===============
 */
-qboolean SNDDMA_Init(void)
+qboolean SNDDMA_Init( void )
 {
 	SDL_AudioSpec desired;
 	SDL_AudioSpec obtained;
 	int tmp;
 
-	if (snd_inited)
+	if ( snd_inited )
 		return qtrue;
 
-	if (!s_sdlBits) {
-		s_sdlBits = Cvar_Get("s_sdlBits", "16", CVAR_ARCHIVE);
-		s_sdlSpeed = Cvar_Get("s_sdlSpeed", "0", CVAR_ARCHIVE);
-		s_sdlChannels = Cvar_Get("s_sdlChannels", "2", CVAR_ARCHIVE);
-		s_sdlDevSamps = Cvar_Get("s_sdlDevSamps", "0", CVAR_ARCHIVE);
-		s_sdlMixSamps = Cvar_Get("s_sdlMixSamps", "0", CVAR_ARCHIVE);
-	}
-
-	s_sdlWindowsForceDirectSound = Cvar_Get("s_sdlWindowsForceDirectSound", "1", CVAR_ARCHIVE);
-
-#ifdef _WIN32
-	if (s_sdlWindowsForceDirectSound->value) {
-		SDL_setenv("SDL_AUDIODRIVER", "directsound", 1);
+	//if ( !s_sdlBits )
+	{
+		s_sdlBits = Cvar_Get( "s_sdlBits", "16", CVAR_ARCHIVE_ND | CVAR_LATCH );
+		Cvar_CheckRange( s_sdlBits, "8", "16", CV_INTEGER );
+		Cvar_SetDescription( s_sdlBits, "Bits per-sample to request for SDL audio output (possible options: 8 or 16). When set to 0 it uses 16." );
+
+		s_sdlChannels = Cvar_Get( "s_sdlChannels", "2", CVAR_ARCHIVE_ND | CVAR_LATCH );
+		Cvar_CheckRange( s_sdlChannels, "1", "2", CV_INTEGER );
+		Cvar_SetDescription( s_sdlChannels, "Number of audio channels to request for SDL audio output. The Quake 3 audio mixer only supports mono and stereo. Additional channels are silent." );
+
+		s_sdlDevSamps = Cvar_Get( "s_sdlDevSamps", "0", CVAR_ARCHIVE_ND | CVAR_LATCH );
+		Cvar_SetDescription( s_sdlDevSamps, "Number of audio samples to provide to the SDL audio output device. When set to 0 it picks a value based on s_sdlSpeed." );
+		s_sdlMixSamps = Cvar_Get( "s_sdlMixSamps", "0", CVAR_ARCHIVE_ND | CVAR_LATCH );
+		Cvar_SetDescription( s_sdlMixSamps, "Number of audio samples for Quake 3's audio mixer when using SDL audio output." );
 	}
-#endif
 
 	Com_Printf( "SDL_Init( SDL_INIT_AUDIO )... " );
 
-	if (SDL_Init(SDL_INIT_AUDIO) != 0)
+	if ( SDL_Init( SDL_INIT_AUDIO ) != 0 )
 	{
-		Com_Printf( "FAILED (%s)\n", SDL_GetError( ) );
+		Com_Printf( "FAILED (%s)\n", SDL_GetError() );
 		return qfalse;
 	}
 
 	Com_Printf( "OK\n" );
 
-	Com_Printf( "SDL audio driver is \"%s\".\n", SDL_GetCurrentAudioDriver( ) );
+	Com_Printf( "SDL audio driver is \"%s\".\n", SDL_GetCurrentAudioDriver() );
 
-	memset(&desired, '\0', sizeof (desired));
-	memset(&obtained, '\0', sizeof (obtained));
+	memset( &desired, '\0', sizeof (desired) );
+	memset( &obtained, '\0', sizeof (obtained) );
 
-	tmp = ((int) s_sdlBits->value);
-	if ((tmp != 16) && (tmp != 8))
-		tmp = 16;
+	desired.freq = SNDDMA_KHzToHz( s_khz->integer );
+	if ( desired.freq == 0 )
+		desired.freq = 22050;
+
+	tmp = s_sdlBits->integer;
+	if ( tmp < 16 )
+		tmp = 8;
 
-	desired.freq = (int) s_sdlSpeed->value;
-	if(!desired.freq) desired.freq = 22050;
 	desired.format = ((tmp == 16) ? AUDIO_S16SYS : AUDIO_U8);
 
 	// I dunno if this is the best idea, but I'll give it a try...
 	//  should probably check a cvar for this...
-	if (s_sdlDevSamps->value)
+	if ( s_sdlDevSamps->integer )
 		desired.samples = s_sdlDevSamps->value;
 	else
 	{
@@ -269,18 +262,18 @@
 			desired.samples = 2048;  // (*shrug*)
 	}
 
-	desired.channels = (int) s_sdlChannels->value;
+	desired.channels = s_sdlChannels->integer;
 	desired.callback = SNDDMA_AudioCallback;
 
-	sdlPlaybackDevice = SDL_OpenAudioDevice(NULL, SDL_FALSE, &desired, &obtained, SDL_AUDIO_ALLOW_ANY_CHANGE);
-	if (sdlPlaybackDevice == 0)
+	sdlPlaybackDevice = SDL_OpenAudioDevice( NULL, SDL_FALSE, &desired, &obtained, SDL_AUDIO_ALLOW_ANY_CHANGE );
+	if ( sdlPlaybackDevice == 0 )
 	{
-		Com_Printf("SDL_OpenAudioDevice() failed: %s\n", SDL_GetError());
-		SDL_QuitSubSystem(SDL_INIT_AUDIO);
+		Com_Printf( "SDL_OpenAudioDevice() failed: %s\n", SDL_GetError() );
+		SDL_QuitSubSystem( SDL_INIT_AUDIO );
 		return qfalse;
 	}
 
-	SNDDMA_PrintAudiospec("SDL_AudioSpec", &obtained);
+	SNDDMA_PrintAudiospec( "SDL_AudioSpec", &obtained );
 
 	// dma.samples needs to be big, or id's mixer will just refuse to
 	//  work at all; we need to keep it significantly bigger than the
@@ -289,16 +282,18 @@
 	// 32768 is what the OSS driver filled in here on my system. I don't
 	//  know if it's a good value overall, but at least we know it's
 	//  reasonable...this is why I let the user override.
-	tmp = s_sdlMixSamps->value;
-	if (!tmp)
+	tmp = s_sdlMixSamps->integer;
+	if ( !tmp )
 		tmp = (obtained.samples * obtained.channels) * 10;
 
 	// samples must be divisible by number of channels
 	tmp -= tmp % obtained.channels;
+	// round up to next power of 2
+	tmp = log2pad( tmp, 1 );
 
 	dmapos = 0;
-	dma.samplebits = SDL_AUDIO_BITSIZE(obtained.format);
-	dma.isfloat = SDL_AUDIO_ISFLOAT(obtained.format);
+	dma.samplebits = SDL_AUDIO_BITSIZE( obtained.format );
+	dma.isfloat = SDL_AUDIO_ISFLOAT( obtained.format );
 	dma.channels = obtained.channels;
 	dma.samples = tmp;
 	dma.fullsamples = dma.samples / dma.channels;
@@ -310,7 +305,13 @@
 #ifdef USE_SDL_AUDIO_CAPTURE
 	// !!! FIXME: some of these SDL_OpenAudioDevice() values should be cvars.
 	s_sdlCapture = Cvar_Get( "s_sdlCapture", "1", CVAR_ARCHIVE | CVAR_LATCH );
-	if (!s_sdlCapture->integer)
+	Cvar_SetDescription( s_sdlCapture, "Set to 1 to enable SDL audio capture." );
+	// !!! FIXME: pulseaudio capture records audio the entire time the program is running. https://bugzilla.libsdl.org/show_bug.cgi?id=4087
+	if (Q_stricmp(SDL_GetCurrentAudioDriver(), "pulseaudio") == 0)
+	{
+		Com_Printf("SDL audio capture support disabled for pulseaudio (https://bugzilla.libsdl.org/show_bug.cgi?id=4087)\n");
+	}
+	else if (!s_sdlCapture->integer)
 	{
 		Com_Printf("SDL audio capture support disabled by user ('+set s_sdlCapture 1' to enable)\n");
 	}
@@ -331,7 +332,7 @@
 		spec.samples = VOIP_MAX_PACKET_SAMPLES * 4;
 		sdlCaptureDevice = SDL_OpenAudioDevice(NULL, SDL_TRUE, &spec, NULL, 0);
 		Com_Printf( "SDL capture device %s.\n",
-					(sdlCaptureDevice == 0) ? "failed to open" : "opened");
+				    (sdlCaptureDevice == 0) ? "failed to open" : "opened");
 	}
 
 	sdlMasterGain = 1.0f;
@@ -346,22 +347,24 @@
 	return qtrue;
 }
 
+
 /*
 ===============
 SNDDMA_GetDMAPos
 ===============
 */
-int SNDDMA_GetDMAPos(void)
+int SNDDMA_GetDMAPos( void )
 {
 	return dmapos;
 }
 
+
 /*
 ===============
 SNDDMA_Shutdown
 ===============
 */
-void SNDDMA_Shutdown(void)
+void SNDDMA_Shutdown( void )
 {
 	if (sdlPlaybackDevice != 0)
 	{
@@ -389,6 +392,7 @@
 	Com_Printf("SDL audio shut down.\n");
 }
 
+
 /*
 ===============
 SNDDMA_Submit
@@ -396,19 +400,20 @@
 Send sound to device if buffer isn't really the dma buffer
 ===============
 */
-void SNDDMA_Submit(void)
+void SNDDMA_Submit( void )
 {
-	SDL_UnlockAudioDevice(sdlPlaybackDevice);
+	SDL_UnlockAudioDevice( sdlPlaybackDevice );
 }
 
+
 /*
 ===============
 SNDDMA_BeginPainting
 ===============
 */
-void SNDDMA_BeginPainting (void)
+void SNDDMA_BeginPainting( void )
 {
-	SDL_LockAudioDevice(sdlPlaybackDevice);
+	SDL_LockAudioDevice( sdlPlaybackDevice );
 }
 
 
@@ -424,6 +429,7 @@
 #endif
 }
 
+
 int SNDDMA_AvailableCaptureSamples(void)
 {
 #ifdef USE_SDL_AUDIO_CAPTURE
@@ -434,6 +440,7 @@
 #endif
 }
 
+
 void SNDDMA_Capture(int samples, byte *data)
 {
 #ifdef USE_SDL_AUDIO_CAPTURE

```

### `openarena-engine`  — sha256 `3c5f757e5faf...`, 7562 bytes

_Diff stat: +46 / -205 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_snd.c	2026-04-16 20:02:25.266779000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sdl\sdl_snd.c	2026-04-16 22:48:25.934962600 +0100
@@ -23,7 +23,7 @@
 #include <stdlib.h>
 #include <stdio.h>
 
-#ifdef USE_INTERNAL_SDL_HEADERS
+#ifdef USE_LOCAL_HEADERS
 #	include "SDL.h"
 #else
 #	include <SDL.h>
@@ -31,8 +31,6 @@
 
 #include "../qcommon/q_shared.h"
 #include "../client/snd_local.h"
-#include "../client/client.h"
-#include "../client/cl_avi.h"
 
 qboolean snd_inited = qfalse;
 
@@ -41,26 +39,13 @@
 cvar_t *s_sdlChannels;
 cvar_t *s_sdlDevSamps;
 cvar_t *s_sdlMixSamps;
-cvar_t *s_sdlWindowsForceDirectSound;
 
 /* The audio callback. All the magic happens here. */
 static int dmapos = 0;
 static int dmasize = 0;
 
-//extern qboolean CL_VideoRecording (void);
-extern cvar_t *cl_freezeDemo;
-extern cvar_t *cl_freezeDemoPauseVideoRecording;
-
-static SDL_AudioDeviceID sdlPlaybackDevice;
-
-#if defined USE_VOIP && SDL_VERSION_ATLEAST( 2, 0, 5 )
-#define USE_SDL_AUDIO_CAPTURE
-
-static SDL_AudioDeviceID sdlCaptureDevice;
-static cvar_t *s_sdlCapture;
-static float sdlMasterGain = 1.0f;
-#endif
-
+// leilei - setting correct speed for xmp
+extern int xmpspeed;
 
 /*
 ===============
@@ -70,11 +55,8 @@
 static void SNDDMA_AudioCallback(void *userdata, Uint8 *stream, int len)
 {
 	int pos = (dmapos * (dma.samplebits/8));
-
-	if (pos >= dmasize) {
-		//Com_Printf("pos (%d) > dmasize (%d)\n", pos, dmasize);
+	if (pos >= dmasize)
 		dmapos = pos = 0;
-	}
 
 	if (!snd_inited)  /* shouldn't happen, but just in case... */
 	{
@@ -92,64 +74,18 @@
 			len1 = tobufend;
 			len2 = len - len1;
 		}
-		if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-			memset(stream, 0, len1);
-		} else {
-			memcpy(stream, dma.buffer + pos, len1);
-		}
-		if (len2 <= 0) {
-			//Com_Printf("len2 <= 0   %d\n", len2);
+		memcpy(stream, dma.buffer + pos, len1);
+		if (len2 <= 0)
 			dmapos += (len1 / (dma.samplebits/8));
-		} else  { /* wraparound? */
-			//Com_Printf("wrap len2 %d\n", len2);
-			if (CL_VideoRecording(&afdMain)  &&  (cl_aviNoAudioHWOutput->integer  ||  (cl_freezeDemo->integer  &&  cl_freezeDemoPauseVideoRecording->integer))) {
-				memset(stream + len1, 0, len2);
-			} else {
-				memcpy(stream+len1, dma.buffer, len2);
-			}
+		else  /* wraparound? */
+		{
+			memcpy(stream+len1, dma.buffer, len2);
 			dmapos = (len2 / (dma.samplebits/8));
 		}
 	}
 
-	if (dmapos >= dmasize) {
-		//Com_Printf("dmapos >= dmasize  %d > %d\n", dmapos, dmasize);
+	if (dmapos >= dmasize)
 		dmapos = 0;
-	}
-
-#ifdef USE_SDL_AUDIO_CAPTURE
-	if (sdlMasterGain != 1.0f)
-	{
-		int i;
-		if (dma.isfloat && (dma.samplebits == 32))
-		{
-			float *ptr = (float *) stream;
-			len /= sizeof (*ptr);
-			for (i = 0; i < len; i++, ptr++)
-			{
-				*ptr *= sdlMasterGain;
-			}
-		}
-		else if (dma.samplebits == 16)
-		{
-			Sint16 *ptr = (Sint16 *) stream;
-			len /= sizeof (*ptr);
-			for (i = 0; i < len; i++, ptr++)
-			{
-				*ptr = (Sint16) (((float) *ptr) * sdlMasterGain);
-			}
-		}
-		else if (dma.samplebits == 8)
-		{
-			Uint8 *ptr = (Uint8 *) stream;
-			len /= sizeof (*ptr);
-			for (i = 0; i < len; i++, ptr++)
-			{
-				*ptr = (Uint8) (((float) *ptr) * sdlMasterGain);
-			}
-		}
-	}
-#endif
-
 }
 
 static struct
@@ -163,9 +99,7 @@
 	{ AUDIO_U16LSB, "AUDIO_U16LSB" },
 	{ AUDIO_S16LSB, "AUDIO_S16LSB" },
 	{ AUDIO_U16MSB, "AUDIO_U16MSB" },
-	{ AUDIO_S16MSB, "AUDIO_S16MSB" },
-	{ AUDIO_F32LSB, "AUDIO_F32LSB" },
-	{ AUDIO_F32MSB, "AUDIO_F32MSB" }
+	{ AUDIO_S16MSB, "AUDIO_S16MSB" }
 };
 
 static int formatToStringTableSize = ARRAY_LEN( formatToStringTable );
@@ -206,6 +140,9 @@
 */
 qboolean SNDDMA_Init(void)
 {
+#if SDL_MAJOR_VERSION != 2
+	char drivername[128];
+#endif
 	SDL_AudioSpec desired;
 	SDL_AudioSpec obtained;
 	int tmp;
@@ -221,25 +158,26 @@
 		s_sdlMixSamps = Cvar_Get("s_sdlMixSamps", "0", CVAR_ARCHIVE);
 	}
 
-	s_sdlWindowsForceDirectSound = Cvar_Get("s_sdlWindowsForceDirectSound", "1", CVAR_ARCHIVE);
-
-#ifdef _WIN32
-	if (s_sdlWindowsForceDirectSound->value) {
-		SDL_setenv("SDL_AUDIODRIVER", "directsound", 1);
-	}
-#endif
-
 	Com_Printf( "SDL_Init( SDL_INIT_AUDIO )... " );
 
-	if (SDL_Init(SDL_INIT_AUDIO) != 0)
+	if (!SDL_WasInit(SDL_INIT_AUDIO))
 	{
-		Com_Printf( "FAILED (%s)\n", SDL_GetError( ) );
-		return qfalse;
+		if (SDL_Init(SDL_INIT_AUDIO) == -1)
+		{
+			Com_Printf( "FAILED (%s)\n", SDL_GetError( ) );
+			return qfalse;
+		}
 	}
 
 	Com_Printf( "OK\n" );
 
+#if SDL_MAJOR_VERSION == 2
 	Com_Printf( "SDL audio driver is \"%s\".\n", SDL_GetCurrentAudioDriver( ) );
+#else
+	if (SDL_AudioDriverName(drivername, sizeof (drivername)) == NULL)
+		strcpy(drivername, "(UNKNOWN)");
+	Com_Printf("SDL audio driver is \"%s\".\n", drivername);
+#endif
 
 	memset(&desired, '\0', sizeof (desired));
 	memset(&obtained, '\0', sizeof (obtained));
@@ -252,6 +190,8 @@
 	if(!desired.freq) desired.freq = 22050;
 	desired.format = ((tmp == 16) ? AUDIO_S16SYS : AUDIO_U8);
 
+	xmpspeed = desired.freq; // leilei
+
 	// I dunno if this is the best idea, but I'll give it a try...
 	//  should probably check a cvar for this...
 	if (s_sdlDevSamps->value)
@@ -272,10 +212,9 @@
 	desired.channels = (int) s_sdlChannels->value;
 	desired.callback = SNDDMA_AudioCallback;
 
-	sdlPlaybackDevice = SDL_OpenAudioDevice(NULL, SDL_FALSE, &desired, &obtained, SDL_AUDIO_ALLOW_ANY_CHANGE);
-	if (sdlPlaybackDevice == 0)
+	if (SDL_OpenAudio(&desired, &obtained) == -1)
 	{
-		Com_Printf("SDL_OpenAudioDevice() failed: %s\n", SDL_GetError());
+		Com_Printf("SDL_OpenAudio() failed: %s\n", SDL_GetError());
 		SDL_QuitSubSystem(SDL_INIT_AUDIO);
 		return qfalse;
 	}
@@ -293,53 +232,26 @@
 	if (!tmp)
 		tmp = (obtained.samples * obtained.channels) * 10;
 
-	// samples must be divisible by number of channels
-	tmp -= tmp % obtained.channels;
+	if (tmp & (tmp - 1))  // not a power of two? Seems to confuse something.
+	{
+		int val = 1;
+		while (val < tmp)
+			val <<= 1;
+
+		tmp = val;
+	}
 
 	dmapos = 0;
-	dma.samplebits = SDL_AUDIO_BITSIZE(obtained.format);
-	dma.isfloat = SDL_AUDIO_ISFLOAT(obtained.format);
+	dma.samplebits = obtained.format & 0xFF;  // first byte of format is bits.
 	dma.channels = obtained.channels;
 	dma.samples = tmp;
-	dma.fullsamples = dma.samples / dma.channels;
 	dma.submission_chunk = 1;
 	dma.speed = obtained.freq;
 	dmasize = (dma.samples * (dma.samplebits/8));
 	dma.buffer = calloc(1, dmasize);
 
-#ifdef USE_SDL_AUDIO_CAPTURE
-	// !!! FIXME: some of these SDL_OpenAudioDevice() values should be cvars.
-	s_sdlCapture = Cvar_Get( "s_sdlCapture", "1", CVAR_ARCHIVE | CVAR_LATCH );
-	if (!s_sdlCapture->integer)
-	{
-		Com_Printf("SDL audio capture support disabled by user ('+set s_sdlCapture 1' to enable)\n");
-	}
-#if USE_MUMBLE
-	else if (cl_useMumble->integer)
-	{
-		Com_Printf("SDL audio capture support disabled for Mumble support\n");
-	}
-#endif
-	else
-	{
-		/* !!! FIXME: list available devices and let cvar specify one, like OpenAL does */
-		SDL_AudioSpec spec;
-		SDL_zero(spec);
-		spec.freq = 48000;
-		spec.format = AUDIO_S16SYS;
-		spec.channels = 1;
-		spec.samples = VOIP_MAX_PACKET_SAMPLES * 4;
-		sdlCaptureDevice = SDL_OpenAudioDevice(NULL, SDL_TRUE, &spec, NULL, 0);
-		Com_Printf( "SDL capture device %s.\n",
-					(sdlCaptureDevice == 0) ? "failed to open" : "opened");
-	}
-
-	sdlMasterGain = 1.0f;
-#endif
-
 	Com_Printf("Starting SDL audio callback...\n");
-	SDL_PauseAudioDevice(sdlPlaybackDevice, 0);  // start callback.
-	// don't unpause the capture device; we'll do that in StartCapture.
+	SDL_PauseAudio(0);  // start callback.
 
 	Com_Printf("SDL audio initialized.\n");
 	snd_inited = qtrue;
@@ -363,30 +275,15 @@
 */
 void SNDDMA_Shutdown(void)
 {
-	if (sdlPlaybackDevice != 0)
-	{
-		Com_Printf("Closing SDL audio playback device...\n");
-		SDL_CloseAudioDevice(sdlPlaybackDevice);
-		Com_Printf("SDL audio playback device closed.\n");
-		sdlPlaybackDevice = 0;
-	}
-
-#ifdef USE_SDL_AUDIO_CAPTURE
-	if (sdlCaptureDevice)
-	{
-		Com_Printf("Closing SDL audio capture device...\n");
-		SDL_CloseAudioDevice(sdlCaptureDevice);
-		Com_Printf("SDL audio capture device closed.\n");
-		sdlCaptureDevice = 0;
-	}
-#endif
-
+	Com_Printf("Closing SDL audio device...\n");
+	SDL_PauseAudio(1);
+	SDL_CloseAudio();
 	SDL_QuitSubSystem(SDL_INIT_AUDIO);
 	free(dma.buffer);
 	dma.buffer = NULL;
 	dmapos = dmasize = 0;
 	snd_inited = qfalse;
-	Com_Printf("SDL audio shut down.\n");
+	Com_Printf("SDL audio device shut down.\n");
 }
 
 /*
@@ -398,7 +295,7 @@
 */
 void SNDDMA_Submit(void)
 {
-	SDL_UnlockAudioDevice(sdlPlaybackDevice);
+	SDL_UnlockAudio();
 }
 
 /*
@@ -408,61 +305,5 @@
 */
 void SNDDMA_BeginPainting (void)
 {
-	SDL_LockAudioDevice(sdlPlaybackDevice);
-}
-
-
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void)
-{
-#ifdef USE_SDL_AUDIO_CAPTURE
-	if (sdlCaptureDevice)
-	{
-		SDL_ClearQueuedAudio(sdlCaptureDevice);
-		SDL_PauseAudioDevice(sdlCaptureDevice, 0);
-	}
-#endif
-}
-
-int SNDDMA_AvailableCaptureSamples(void)
-{
-#ifdef USE_SDL_AUDIO_CAPTURE
-	// divided by 2 to convert from bytes to (mono16) samples.
-	return sdlCaptureDevice ? (SDL_GetQueuedAudioSize(sdlCaptureDevice) / 2) : 0;
-#else
-	return 0;
-#endif
+	SDL_LockAudio();
 }
-
-void SNDDMA_Capture(int samples, byte *data)
-{
-#ifdef USE_SDL_AUDIO_CAPTURE
-	// multiplied by 2 to convert from (mono16) samples to bytes.
-	if (sdlCaptureDevice)
-	{
-		SDL_DequeueAudio(sdlCaptureDevice, data, samples * 2);
-	}
-	else
-#endif
-	{
-		SDL_memset(data, '\0', samples * 2);
-	}
-}
-
-void SNDDMA_StopCapture(void)
-{
-#ifdef USE_SDL_AUDIO_CAPTURE
-	if (sdlCaptureDevice)
-	{
-		SDL_PauseAudioDevice(sdlCaptureDevice, 1);
-	}
-#endif
-}
-
-void SNDDMA_MasterGain( float val )
-{
-#ifdef USE_SDL_AUDIO_CAPTURE
-	sdlMasterGain = val;
-#endif
-}
-#endif

```
