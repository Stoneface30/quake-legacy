# Diff: `code/client/snd_local.h`
**Canonical:** `wolfcamql-src` (sha256 `93a208cd94d1...`, 8849 bytes)

## Variants

### `quake3-source`  — sha256 `7e034bdca966...`, 5595 bytes

_Diff stat: +20 / -109 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_local.h	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\snd_local.h	2026-04-16 20:02:19.894095900 +0100
@@ -15,14 +15,14 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // snd_local.h -- private sound definations
 
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "../qcommon/qcommon.h"
 #include "snd_public.h"
 
@@ -32,13 +32,6 @@
 #define SND_CHUNK_SIZE_FLOAT	(SND_CHUNK_SIZE/2)		// floats
 #define SND_CHUNK_SIZE_BYTE		(SND_CHUNK_SIZE*2)		// floats
 
-typedef enum {
-	SND_COMPRESSION_16BIT = 0,
-	SND_COMPRESSION_ADPCM,
-	SND_COMPRESSION_DAUB4,
-	SND_COMPRESSION_MULAW,
-} compressionMethod_t;
-
 typedef struct {
 	int			left;	// the final values will be clamped to +/- 0x00ffff00 and shifted down
 	int			right;
@@ -61,9 +54,8 @@
 	qboolean		defaultSound;			// couldn't be loaded, so use buzz
 	qboolean		inMemory;				// not in Memory
 	qboolean		soundCompressed;		// not in Memory
-	compressionMethod_t soundCompressionMethod;
+	int				soundCompressionMethod;	
 	int 			soundLength;
-	int				soundChannels;
 	char 			soundName[MAX_QPATH];
 	int				lastTimeUsed;
 	struct sfx_s	*next;
@@ -72,20 +64,14 @@
 typedef struct {
 	int			channels;
 	int			samples;				// mono samples in buffer
-	int			fullsamples;			// samples with all channels in buffer (samples divided by channels)
 	int			submission_chunk;		// don't mix less than this #
 	int			samplebits;
-	int			isfloat;
 	int			speed;
 	byte		*buffer;
 } dma_t;
 
 #define START_SAMPLE_IMMEDIATE	0x7fffffff
 
-#define MAX_DOPPLER_SCALE 50.0f //arbitrary
-
-#define THIRD_PERSON_THRESHOLD_SQ (48.0f*48.0f)
-
 typedef struct loopSound_s {
 	vec3_t		origin;
 	vec3_t		velocity;
@@ -114,7 +100,6 @@
 	qboolean	fixed_origin;	// use origin instead of fetching entnum's origin
 	sfx_t		*thesfx;		// sfx structure
 	qboolean	doppler;
-	qboolean	fullVolume;
 } channel_t;
 
 
@@ -130,40 +115,6 @@
 	int			dataofs;		// chunk starts this many bytes from file start
 } wavinfo_t;
 
-// Interface between Q3 sound "api" and the sound backend
-typedef struct
-{
-	void (*Shutdown)(void);
-	void (*StartSound)( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
-	void (*StartLocalSound)( sfxHandle_t sfx, int channelNum );
-	void (*StartBackgroundTrack)( const char *intro, const char *loop );
-	void (*StopBackgroundTrack)( void );
-	void (*RawSamples)(int stream, int samples, int rate, int width, int channels, const byte *data, float volume, int entityNum);
-	void (*StopAllSounds)( void );
-	void (*ClearLoopingSounds)( qboolean killall );
-	void (*AddLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
-	void (*AddRealLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
-	void (*StopLoopingSound)(int entityNum );
-	void (*Respatialize)( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
-	void (*UpdateEntityPosition)( int entityNum, const vec3_t origin );
-	void (*Update)( void );
-	void (*DisableSounds)( void );
-	void (*BeginRegistration)( void );
-	sfxHandle_t (*RegisterSound)( const char *sample, qboolean compressed );
-	void (*ClearSoundBuffer)( void );
-	void (*SoundInfo)( void );
-	void (*SoundList)( void );
-	void (*PrintSfxFilename)(sfxHandle_t sfx);
-
-#ifdef USE_VOIP
-	void (*StartCapture)( void );
-	int (*AvailableCaptureSamples)( void );
-	void (*Capture)( int samples, byte *data );
-	void (*StopCapture)( void );
-	void (*MasterGain)( float gain );
-#endif
-} soundInterface_t;
-
 
 /*
 ====================================================================
@@ -186,15 +137,6 @@
 
 void	SNDDMA_Submit(void);
 
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void);
-int SNDDMA_AvailableCaptureSamples(void);
-void SNDDMA_Capture(int samples, byte *data);
-void SNDDMA_StopCapture(void);
-void SNDDMA_MasterGain(float val);
-#endif
-
-
 //====================================================================
 
 #define	MAX_CHANNELS			96
@@ -204,43 +146,34 @@
 extern	int		numLoopChannels;
 
 extern	int		s_paintedtime;
+extern	int		s_rawend;
 extern	vec3_t	listener_forward;
 extern	vec3_t	listener_right;
 extern	vec3_t	listener_up;
 extern	dma_t	dma;
 
 #define	MAX_RAW_SAMPLES	16384
-#define MAX_RAW_STREAMS (MAX_CLIENTS * 2 + 1)
-extern	portable_samplepair_t s_rawsamples[MAX_RAW_STREAMS][MAX_RAW_SAMPLES];
-extern	int		s_rawend[MAX_RAW_STREAMS];
-
-extern cvar_t *s_volume;
-extern cvar_t *s_musicVolume;
-extern cvar_t *s_muted;
-extern cvar_t *s_doppler;
-
-extern cvar_t *s_testsound;
-extern cvar_t *cl_aviNoAudioHWOutput;
-extern cvar_t *s_announcerVolume;
-extern cvar_t *s_killBeepVolume;
-extern cvar_t *s_useTimescale;
-extern cvar_t *s_forceScale;
-extern cvar_t *s_showMiss;
-extern cvar_t *s_maxSoundRepeatTime;
-extern cvar_t *s_maxSoundInstances;
-extern cvar_t *s_qlAttenuate;
-extern cvar_t *s_debugMissingSounds;
+extern	portable_samplepair_t	s_rawsamples[MAX_RAW_SAMPLES];
+
+extern cvar_t	*s_volume;
+extern cvar_t	*s_nosound;
+extern cvar_t	*s_khz;
+extern cvar_t	*s_show;
+extern cvar_t	*s_mixahead;
+
+extern cvar_t	*s_testsound;
+extern cvar_t	*s_separation;
 
 qboolean S_LoadSound( sfx_t *sfx );
 
 void		SND_free(sndBuffer *v);
-sndBuffer*	SND_malloc( void );
-void		SND_setup( void );
-void		SND_shutdown(void);
+sndBuffer*	SND_malloc();
+void		SND_setup();
 
 void S_PaintChannels(int endtime);
 
-//void S_memoryLoad(sfx_t *sfx);
+void S_memoryLoad(sfx_t *sfx);
+portable_samplepair_t *S_GetRawSamplePointer();
 
 // spatializes a channel
 void S_Spatialize(channel_t *ch);
@@ -248,14 +181,14 @@
 // adpcm functions
 int  S_AdpcmMemoryNeeded( const wavinfo_t *info );
 void S_AdpcmEncodeSound( sfx_t *sfx, short *samples );
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to);
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to);
 
 // wavelet function
 
 #define SENTINEL_MULAW_ZERO_RUN 127
 #define SENTINEL_MULAW_FOUR_BIT_RUN 126
 
-void S_FreeOldestSound( void );
+void S_FreeOldestSound();
 
 #define	NXStream byte
 
@@ -269,25 +202,3 @@
 extern sfx_t *sfxScratchPointer;
 extern int	   sfxScratchIndex;
 
-qboolean S_Base_Init( soundInterface_t *si );
-int S_Milliseconds (void);
-
-// OpenAL stuff
-typedef enum
-{
-	SRCPRI_AMBIENT = 0,	// Ambient sound effects
-	SRCPRI_ENTITY,			// Entity sound effects
-	SRCPRI_ONESHOT,			// One-shot sounds
-	SRCPRI_LOCAL,				// Local sounds
-	SRCPRI_STREAM				// Streams (music, cutscenes)
-} alSrcPriority_t;
-
-typedef int srcHandle_t;
-
-qboolean S_AL_Init( soundInterface_t *si );
-
-#if 0  // disabled wolfcam
-#ifdef idppc_altivec
-void S_PaintChannelFrom16_altivec( portable_samplepair_t paintbuffer[PAINTBUFFER_SIZE], int snd_vol, channel_t *ch, const sfx_t *sc, int count, int sampleOffset, int bufferOffset );
-#endif
-#endif

```

### `ioquake3`  — sha256 `63b90d2ddc2d...`, 8217 bytes

_Diff stat: +6 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_local.h	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_local.h	2026-04-16 20:02:21.533570500 +0100
@@ -32,13 +32,6 @@
 #define SND_CHUNK_SIZE_FLOAT	(SND_CHUNK_SIZE/2)		// floats
 #define SND_CHUNK_SIZE_BYTE		(SND_CHUNK_SIZE*2)		// floats
 
-typedef enum {
-	SND_COMPRESSION_16BIT = 0,
-	SND_COMPRESSION_ADPCM,
-	SND_COMPRESSION_DAUB4,
-	SND_COMPRESSION_MULAW,
-} compressionMethod_t;
-
 typedef struct {
 	int			left;	// the final values will be clamped to +/- 0x00ffff00 and shifted down
 	int			right;
@@ -61,9 +54,9 @@
 	qboolean		defaultSound;			// couldn't be loaded, so use buzz
 	qboolean		inMemory;				// not in Memory
 	qboolean		soundCompressed;		// not in Memory
-	compressionMethod_t soundCompressionMethod;
+	int				soundCompressionMethod;	
 	int 			soundLength;
-	int				soundChannels;
+	int			soundChannels;
 	char 			soundName[MAX_QPATH];
 	int				lastTimeUsed;
 	struct sfx_s	*next;
@@ -134,7 +127,7 @@
 typedef struct
 {
 	void (*Shutdown)(void);
-	void (*StartSound)( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
+	void (*StartSound)( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
 	void (*StartLocalSound)( sfxHandle_t sfx, int channelNum );
 	void (*StartBackgroundTrack)( const char *intro, const char *loop );
 	void (*StopBackgroundTrack)( void );
@@ -144,7 +137,7 @@
 	void (*AddLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*AddRealLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*StopLoopingSound)(int entityNum );
-	void (*Respatialize)( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+	void (*Respatialize)( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 	void (*UpdateEntityPosition)( int entityNum, const vec3_t origin );
 	void (*Update)( void );
 	void (*DisableSounds)( void );
@@ -153,8 +146,6 @@
 	void (*ClearSoundBuffer)( void );
 	void (*SoundInfo)( void );
 	void (*SoundList)( void );
-	void (*PrintSfxFilename)(sfxHandle_t sfx);
-
 #ifdef USE_VOIP
 	void (*StartCapture)( void );
 	int (*AvailableCaptureSamples)( void );
@@ -220,16 +211,6 @@
 extern cvar_t *s_doppler;
 
 extern cvar_t *s_testsound;
-extern cvar_t *cl_aviNoAudioHWOutput;
-extern cvar_t *s_announcerVolume;
-extern cvar_t *s_killBeepVolume;
-extern cvar_t *s_useTimescale;
-extern cvar_t *s_forceScale;
-extern cvar_t *s_showMiss;
-extern cvar_t *s_maxSoundRepeatTime;
-extern cvar_t *s_maxSoundInstances;
-extern cvar_t *s_qlAttenuate;
-extern cvar_t *s_debugMissingSounds;
 
 qboolean S_LoadSound( sfx_t *sfx );
 
@@ -240,7 +221,7 @@
 
 void S_PaintChannels(int endtime);
 
-//void S_memoryLoad(sfx_t *sfx);
+void S_memoryLoad(sfx_t *sfx);
 
 // spatializes a channel
 void S_Spatialize(channel_t *ch);
@@ -248,7 +229,7 @@
 // adpcm functions
 int  S_AdpcmMemoryNeeded( const wavinfo_t *info );
 void S_AdpcmEncodeSound( sfx_t *sfx, short *samples );
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to);
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to);
 
 // wavelet function
 
@@ -270,7 +251,6 @@
 extern int	   sfxScratchIndex;
 
 qboolean S_Base_Init( soundInterface_t *si );
-int S_Milliseconds (void);
 
 // OpenAL stuff
 typedef enum
@@ -286,8 +266,6 @@
 
 qboolean S_AL_Init( soundInterface_t *si );
 
-#if 0  // disabled wolfcam
 #ifdef idppc_altivec
 void S_PaintChannelFrom16_altivec( portable_samplepair_t paintbuffer[PAINTBUFFER_SIZE], int snd_vol, channel_t *ch, const sfx_t *sc, int count, int sampleOffset, int bufferOffset );
 #endif
-#endif

```

### `quake3e`  — sha256 `451db195cb85...`, 7196 bytes

_Diff stat: +22 / -79 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_local.h	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_local.h	2026-04-16 20:02:26.916520900 +0100
@@ -19,7 +19,7 @@
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-// snd_local.h -- private sound definations
+// snd_local.h -- private sound definitions
 
 
 #include "../qcommon/q_shared.h"
@@ -32,27 +32,20 @@
 #define SND_CHUNK_SIZE_FLOAT	(SND_CHUNK_SIZE/2)		// floats
 #define SND_CHUNK_SIZE_BYTE		(SND_CHUNK_SIZE*2)		// floats
 
-typedef enum {
-	SND_COMPRESSION_16BIT = 0,
-	SND_COMPRESSION_ADPCM,
-	SND_COMPRESSION_DAUB4,
-	SND_COMPRESSION_MULAW,
-} compressionMethod_t;
-
 typedef struct {
 	int			left;	// the final values will be clamped to +/- 0x00ffff00 and shifted down
 	int			right;
 } portable_samplepair_t;
 
 typedef struct adpcm_state {
-    short	sample;		/* Previous output value */
-    char	index;		/* Index into stepsize table */
+	short	sample;		/* Previous output value */
+	char	index;		/* Index into stepsize table */
 } adpcm_state_t;
 
 typedef	struct sndBuffer_s {
 	short					sndChunk[SND_CHUNK_SIZE];
 	struct sndBuffer_s		*next;
-    int						size;
+	int						size;
 	adpcm_state_t			adpcm;
 } sndBuffer;
 
@@ -61,7 +54,7 @@
 	qboolean		defaultSound;			// couldn't be loaded, so use buzz
 	qboolean		inMemory;				// not in Memory
 	qboolean		soundCompressed;		// not in Memory
-	compressionMethod_t soundCompressionMethod;
+	int				soundCompressionMethod;
 	int 			soundLength;
 	int				soundChannels;
 	char 			soundName[MAX_QPATH];
@@ -70,22 +63,23 @@
 } sfx_t;
 
 typedef struct {
-	int			channels;
-	int			samples;				// mono samples in buffer
+	unsigned int channels;
+	unsigned int samples;				// mono samples in buffer
 	int			fullsamples;			// samples with all channels in buffer (samples divided by channels)
 	int			submission_chunk;		// don't mix less than this #
 	int			samplebits;
 	int			isfloat;
 	int			speed;
 	byte		*buffer;
+	const char	*driver;
 } dma_t;
 
+extern byte *dma_buffer2;
+
 #define START_SAMPLE_IMMEDIATE	0x7fffffff
 
 #define MAX_DOPPLER_SCALE 50.0f //arbitrary
 
-#define THIRD_PERSON_THRESHOLD_SQ (48.0f*48.0f)
-
 typedef struct loopSound_s {
 	vec3_t		origin;
 	vec3_t		velocity;
@@ -114,12 +108,11 @@
 	qboolean	fixed_origin;	// use origin instead of fetching entnum's origin
 	sfx_t		*thesfx;		// sfx structure
 	qboolean	doppler;
-	qboolean	fullVolume;
 } channel_t;
 
 
-#define	WAV_FORMAT_PCM		1
-
+#define WAV_FORMAT_PCM			0x0001
+#define WAVE_FORMAT_IEEE_FLOAT	0x0003
 
 typedef struct {
 	int			format;
@@ -138,30 +131,21 @@
 	void (*StartLocalSound)( sfxHandle_t sfx, int channelNum );
 	void (*StartBackgroundTrack)( const char *intro, const char *loop );
 	void (*StopBackgroundTrack)( void );
-	void (*RawSamples)(int stream, int samples, int rate, int width, int channels, const byte *data, float volume, int entityNum);
+	void (*RawSamples)(int samples, int rate, int width, int channels, const byte *data, float volume);
 	void (*StopAllSounds)( void );
 	void (*ClearLoopingSounds)( qboolean killall );
 	void (*AddLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*AddRealLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*StopLoopingSound)(int entityNum );
-	void (*Respatialize)( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+	void (*Respatialize)( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 	void (*UpdateEntityPosition)( int entityNum, const vec3_t origin );
-	void (*Update)( void );
+	void (*Update)( int msec );
 	void (*DisableSounds)( void );
 	void (*BeginRegistration)( void );
 	sfxHandle_t (*RegisterSound)( const char *sample, qboolean compressed );
 	void (*ClearSoundBuffer)( void );
 	void (*SoundInfo)( void );
 	void (*SoundList)( void );
-	void (*PrintSfxFilename)(sfxHandle_t sfx);
-
-#ifdef USE_VOIP
-	void (*StartCapture)( void );
-	int (*AvailableCaptureSamples)( void );
-	void (*Capture)( int samples, byte *data );
-	void (*StopCapture)( void );
-	void (*MasterGain)( float gain );
-#endif
 } soundInterface_t;
 
 
@@ -186,15 +170,6 @@
 
 void	SNDDMA_Submit(void);
 
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void);
-int SNDDMA_AvailableCaptureSamples(void);
-void SNDDMA_Capture(int samples, byte *data);
-void SNDDMA_StopCapture(void);
-void SNDDMA_MasterGain(float val);
-#endif
-
-
 //====================================================================
 
 #define	MAX_CHANNELS			96
@@ -203,52 +178,41 @@
 extern	channel_t   loop_channels[MAX_CHANNELS];
 extern	int		numLoopChannels;
 
+extern	int		s_soundtime;
 extern	int		s_paintedtime;
+extern	int		s_rawend;
 extern	vec3_t	listener_forward;
 extern	vec3_t	listener_right;
 extern	vec3_t	listener_up;
 extern	dma_t	dma;
 
 #define	MAX_RAW_SAMPLES	16384
-#define MAX_RAW_STREAMS (MAX_CLIENTS * 2 + 1)
-extern	portable_samplepair_t s_rawsamples[MAX_RAW_STREAMS][MAX_RAW_SAMPLES];
-extern	int		s_rawend[MAX_RAW_STREAMS];
+extern	portable_samplepair_t	s_rawsamples[MAX_RAW_SAMPLES];
 
 extern cvar_t *s_volume;
 extern cvar_t *s_musicVolume;
-extern cvar_t *s_muted;
 extern cvar_t *s_doppler;
+extern cvar_t *s_muteWhenUnfocused;
+extern cvar_t *s_muteWhenMinimized;
 
 extern cvar_t *s_testsound;
-extern cvar_t *cl_aviNoAudioHWOutput;
-extern cvar_t *s_announcerVolume;
-extern cvar_t *s_killBeepVolume;
-extern cvar_t *s_useTimescale;
-extern cvar_t *s_forceScale;
-extern cvar_t *s_showMiss;
-extern cvar_t *s_maxSoundRepeatTime;
-extern cvar_t *s_maxSoundInstances;
-extern cvar_t *s_qlAttenuate;
-extern cvar_t *s_debugMissingSounds;
 
 qboolean S_LoadSound( sfx_t *sfx );
 
 void		SND_free(sndBuffer *v);
 sndBuffer*	SND_malloc( void );
 void		SND_setup( void );
-void		SND_shutdown(void);
+void		SND_shutdown( void );
 
 void S_PaintChannels(int endtime);
 
-//void S_memoryLoad(sfx_t *sfx);
-
 // spatializes a channel
 void S_Spatialize(channel_t *ch);
 
 // adpcm functions
 int  S_AdpcmMemoryNeeded( const wavinfo_t *info );
 void S_AdpcmEncodeSound( sfx_t *sfx, short *samples );
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to);
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to);
 
 // wavelet function
 
@@ -270,24 +234,3 @@
 extern int	   sfxScratchIndex;
 
 qboolean S_Base_Init( soundInterface_t *si );
-int S_Milliseconds (void);
-
-// OpenAL stuff
-typedef enum
-{
-	SRCPRI_AMBIENT = 0,	// Ambient sound effects
-	SRCPRI_ENTITY,			// Entity sound effects
-	SRCPRI_ONESHOT,			// One-shot sounds
-	SRCPRI_LOCAL,				// Local sounds
-	SRCPRI_STREAM				// Streams (music, cutscenes)
-} alSrcPriority_t;
-
-typedef int srcHandle_t;
-
-qboolean S_AL_Init( soundInterface_t *si );
-
-#if 0  // disabled wolfcam
-#ifdef idppc_altivec
-void S_PaintChannelFrom16_altivec( portable_samplepair_t paintbuffer[PAINTBUFFER_SIZE], int snd_vol, channel_t *ch, const sfx_t *sc, int count, int sampleOffset, int bufferOffset );
-#endif
-#endif

```

### `openarena-engine`  — sha256 `229b1427fdf4...`, 7743 bytes

_Diff stat: +10 / -43 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_local.h	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_local.h	2026-04-16 22:48:25.736379700 +0100
@@ -32,13 +32,6 @@
 #define SND_CHUNK_SIZE_FLOAT	(SND_CHUNK_SIZE/2)		// floats
 #define SND_CHUNK_SIZE_BYTE		(SND_CHUNK_SIZE*2)		// floats
 
-typedef enum {
-	SND_COMPRESSION_16BIT = 0,
-	SND_COMPRESSION_ADPCM,
-	SND_COMPRESSION_DAUB4,
-	SND_COMPRESSION_MULAW,
-} compressionMethod_t;
-
 typedef struct {
 	int			left;	// the final values will be clamped to +/- 0x00ffff00 and shifted down
 	int			right;
@@ -61,9 +54,9 @@
 	qboolean		defaultSound;			// couldn't be loaded, so use buzz
 	qboolean		inMemory;				// not in Memory
 	qboolean		soundCompressed;		// not in Memory
-	compressionMethod_t soundCompressionMethod;
+	int				soundCompressionMethod;	
 	int 			soundLength;
-	int				soundChannels;
+	int			soundChannels;
 	char 			soundName[MAX_QPATH];
 	int				lastTimeUsed;
 	struct sfx_s	*next;
@@ -72,10 +65,8 @@
 typedef struct {
 	int			channels;
 	int			samples;				// mono samples in buffer
-	int			fullsamples;			// samples with all channels in buffer (samples divided by channels)
 	int			submission_chunk;		// don't mix less than this #
 	int			samplebits;
-	int			isfloat;
 	int			speed;
 	byte		*buffer;
 } dma_t;
@@ -134,7 +125,7 @@
 typedef struct
 {
 	void (*Shutdown)(void);
-	void (*StartSound)( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
+	void (*StartSound)( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
 	void (*StartLocalSound)( sfxHandle_t sfx, int channelNum );
 	void (*StartBackgroundTrack)( const char *intro, const char *loop );
 	void (*StopBackgroundTrack)( void );
@@ -144,7 +135,7 @@
 	void (*AddLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*AddRealLoopingSound)( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 	void (*StopLoopingSound)(int entityNum );
-	void (*Respatialize)( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+	void (*Respatialize)( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 	void (*UpdateEntityPosition)( int entityNum, const vec3_t origin );
 	void (*Update)( void );
 	void (*DisableSounds)( void );
@@ -153,8 +144,6 @@
 	void (*ClearSoundBuffer)( void );
 	void (*SoundInfo)( void );
 	void (*SoundList)( void );
-	void (*PrintSfxFilename)(sfxHandle_t sfx);
-
 #ifdef USE_VOIP
 	void (*StartCapture)( void );
 	int (*AvailableCaptureSamples)( void );
@@ -186,15 +175,6 @@
 
 void	SNDDMA_Submit(void);
 
-#ifdef USE_VOIP
-void SNDDMA_StartCapture(void);
-int SNDDMA_AvailableCaptureSamples(void);
-void SNDDMA_Capture(int samples, byte *data);
-void SNDDMA_StopCapture(void);
-void SNDDMA_MasterGain(float val);
-#endif
-
-
 //====================================================================
 
 #define	MAX_CHANNELS			96
@@ -219,17 +199,9 @@
 extern cvar_t *s_muted;
 extern cvar_t *s_doppler;
 
+extern cvar_t *s_interrupts;
+
 extern cvar_t *s_testsound;
-extern cvar_t *cl_aviNoAudioHWOutput;
-extern cvar_t *s_announcerVolume;
-extern cvar_t *s_killBeepVolume;
-extern cvar_t *s_useTimescale;
-extern cvar_t *s_forceScale;
-extern cvar_t *s_showMiss;
-extern cvar_t *s_maxSoundRepeatTime;
-extern cvar_t *s_maxSoundInstances;
-extern cvar_t *s_qlAttenuate;
-extern cvar_t *s_debugMissingSounds;
 
 qboolean S_LoadSound( sfx_t *sfx );
 
@@ -240,7 +212,7 @@
 
 void S_PaintChannels(int endtime);
 
-//void S_memoryLoad(sfx_t *sfx);
+void S_memoryLoad(sfx_t *sfx);
 
 // spatializes a channel
 void S_Spatialize(channel_t *ch);
@@ -248,7 +220,7 @@
 // adpcm functions
 int  S_AdpcmMemoryNeeded( const wavinfo_t *info );
 void S_AdpcmEncodeSound( sfx_t *sfx, short *samples );
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to);
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to);
 
 // wavelet function
 
@@ -269,8 +241,9 @@
 extern sfx_t *sfxScratchPointer;
 extern int	   sfxScratchIndex;
 
+extern cvar_t *s_xmp_startPattern;
+
 qboolean S_Base_Init( soundInterface_t *si );
-int S_Milliseconds (void);
 
 // OpenAL stuff
 typedef enum
@@ -285,9 +258,3 @@
 typedef int srcHandle_t;
 
 qboolean S_AL_Init( soundInterface_t *si );
-
-#if 0  // disabled wolfcam
-#ifdef idppc_altivec
-void S_PaintChannelFrom16_altivec( portable_samplepair_t paintbuffer[PAINTBUFFER_SIZE], int snd_vol, channel_t *ch, const sfx_t *sc, int count, int sampleOffset, int bufferOffset );
-#endif
-#endif

```
