# Diff: `code/client/snd_public.h`
**Canonical:** `wolfcamql-src` (sha256 `43286706c96e...`, 3154 bytes)

## Variants

### `quake3-source`  — sha256 `b40c394f844d...`, 2842 bytes

_Diff stat: +8 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_public.h	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\snd_public.h	2026-04-16 20:02:19.894095900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -25,17 +25,16 @@
 void S_Shutdown( void );
 
 // if origin is NULL, the sound will be dynamically sourced from the entity
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
 void S_StartLocalSound( sfxHandle_t sfx, int channelNum );
 
 void S_StartBackgroundTrack( const char *intro, const char *loop );
 void S_StopBackgroundTrack( void );
-void S_PrintSfxFilename (sfxHandle_t sfx);
 
 // cinematics and voice-over-network will send raw samples
 // 1.0 volume will be direct output of source samples
-void S_RawSamples(int stream, int samples, int rate, int width, int channels,
-				   const byte *data, float volume, int entityNum);
+void S_RawSamples (int samples, int rate, int width, int channels, 
+				   const byte *data, float volume);
 
 // stop all sounds and the background track
 void S_StopAllSounds( void );
@@ -46,9 +45,9 @@
 void S_AddRealLoopingSound( int entityNum, const vec3_t origin, const vec3_t velocity, sfxHandle_t sfx );
 void S_StopLoopingSound(int entityNum );
 
-// recompute the relative volumes for all running sounds
-// relative to the given entityNum / orientation
-void S_Respatialize( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+// recompute the reletive volumes for all running sounds
+// reletive to the given entityNum / orientation
+void S_Respatialize( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 
 // let the sound system know where an entity currently is
 void S_UpdateEntityPosition( int entityNum, const vec3_t origin );
@@ -70,14 +69,4 @@
 
 void SNDDMA_Activate( void );
 
-//void S_UpdateBackgroundTrack( void );
-
-
-#ifdef USE_VOIP
-void S_StartCapture( void );
-int S_AvailableCaptureSamples( void );
-void S_Capture( int samples, byte *data );
-void S_StopCapture( void );
-void S_MasterGain( float gain );
-#endif
-
+void S_UpdateBackgroundTrack( void );

```

### `openarena-engine`  — sha256 `054c355a3a74...`, 3096 bytes
Also identical in: ioquake3

_Diff stat: +3 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_public.h	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_public.h	2026-04-16 22:48:25.738377800 +0100
@@ -25,12 +25,11 @@
 void S_Shutdown( void );
 
 // if origin is NULL, the sound will be dynamically sourced from the entity
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
 void S_StartLocalSound( sfxHandle_t sfx, int channelNum );
 
 void S_StartBackgroundTrack( const char *intro, const char *loop );
 void S_StopBackgroundTrack( void );
-void S_PrintSfxFilename (sfxHandle_t sfx);
 
 // cinematics and voice-over-network will send raw samples
 // 1.0 volume will be direct output of source samples
@@ -48,7 +47,7 @@
 
 // recompute the relative volumes for all running sounds
 // relative to the given entityNum / orientation
-void S_Respatialize( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+void S_Respatialize( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 
 // let the sound system know where an entity currently is
 void S_UpdateEntityPosition( int entityNum, const vec3_t origin );
@@ -70,7 +69,7 @@
 
 void SNDDMA_Activate( void );
 
-//void S_UpdateBackgroundTrack( void );
+void S_UpdateBackgroundTrack( void );
 
 
 #ifdef USE_VOIP

```

### `quake3e`  — sha256 `f6a6a4fc9802...`, 2825 bytes

_Diff stat: +6 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_public.h	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_public.h	2026-04-16 20:02:26.917521900 +0100
@@ -25,17 +25,16 @@
 void S_Shutdown( void );
 
 // if origin is NULL, the sound will be dynamically sourced from the entity
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx );
 void S_StartLocalSound( sfxHandle_t sfx, int channelNum );
 
 void S_StartBackgroundTrack( const char *intro, const char *loop );
 void S_StopBackgroundTrack( void );
-void S_PrintSfxFilename (sfxHandle_t sfx);
 
 // cinematics and voice-over-network will send raw samples
 // 1.0 volume will be direct output of source samples
-void S_RawSamples(int stream, int samples, int rate, int width, int channels,
-				   const byte *data, float volume, int entityNum);
+void S_RawSamples (int samples, int rate, int width, int channels, 
+				   const byte *data, float volume);
 
 // stop all sounds and the background track
 void S_StopAllSounds( void );
@@ -48,18 +47,18 @@
 
 // recompute the relative volumes for all running sounds
 // relative to the given entityNum / orientation
-void S_Respatialize( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater );
+void S_Respatialize( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater );
 
 // let the sound system know where an entity currently is
 void S_UpdateEntityPosition( int entityNum, const vec3_t origin );
 
-void S_Update( void );
+void S_Update( int msec );
 
 void S_DisableSounds( void );
 
 void S_BeginRegistration( void );
 
-// RegisterSound will allways return a valid sample, even if it
+// RegisterSound will always return a valid sample, even if it
 // has to create a placeholder.  This prevents continuous filesystem
 // checks for missing files
 sfxHandle_t	S_RegisterSound( const char *sample, qboolean compressed );
@@ -69,15 +68,3 @@
 void S_ClearSoundBuffer( void );
 
 void SNDDMA_Activate( void );
-
-//void S_UpdateBackgroundTrack( void );
-
-
-#ifdef USE_VOIP
-void S_StartCapture( void );
-int S_AvailableCaptureSamples( void );
-void S_Capture( int samples, byte *data );
-void S_StopCapture( void );
-void S_MasterGain( float gain );
-#endif
-

```
