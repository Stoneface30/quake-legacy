# Diff: `code/client/snd_openal.c`
**Canonical:** `wolfcamql-src` (sha256 `7c4d5a937a40...`, 67491 bytes)

## Variants

### `ioquake3`  — sha256 `05127343474c...`, 66755 bytes

_Diff stat: +42 / -66 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_openal.c	2026-04-16 20:02:25.179779600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_openal.c	2026-04-16 20:02:21.534568900 +0100
@@ -135,7 +135,7 @@
 	snd_info_t	info;					// information for this sound like rate, sample count..
 
 	qboolean	isDefault;				// Couldn't be loaded - use default FX
-	qboolean 	isDefaultChecked;  		// Sound has been check if it isDefault
+	qboolean	isDefaultChecked;		// Sound has been check if it isDefault
 	qboolean	inMemory;				// Sound is stored in memory
 	qboolean	isLocked;				// Sound is locked (can not be unloaded)
 	int				lastUsedTime;		// Time last used
@@ -481,9 +481,7 @@
 	numSfx = 0;
 
 	// Load the default sound, and lock it
-	//default_sfx = S_AL_BufferFind("sound/feedback/hit.wav");
-	//default_sfx = S_AL_BufferFind("sound/feedback/hit.ogg");
-	default_sfx = S_AL_BufferFind("silence.wav");
+	default_sfx = S_AL_BufferFind("sound/feedback/hit.wav");
 	S_AL_BufferUse(default_sfx);
 	knownSfx[default_sfx].isLocked = qtrue;
 
@@ -544,7 +542,7 @@
 =================
 S_AL_BufferGet
 
-Returns an sfx's buffer
+Return's a sfx's buffer
 =================
 */
 static
@@ -609,8 +607,7 @@
 	qboolean				startLoopingSound;
 } sentity_t;
 
-// fx scripting uses entities past MAX_GENTITIES
-static sentity_t entityList[MAX_LOOP_SOUNDS];
+static sentity_t entityList[MAX_GENTITIES];
 
 /*
 =================
@@ -620,7 +617,7 @@
 #define S_AL_SanitiseVector(v) _S_AL_SanitiseVector(v,__LINE__)
 static void _S_AL_SanitiseVector( vec3_t v, int line )
 {
-	if( Q_floatIsNan( v[ 0 ] ) || Q_floatIsNan( v[ 1 ] ) || Q_floatIsNan( v[ 2 ] ) )
+	if( Q_isnan( v[ 0 ] ) || Q_isnan( v[ 1 ] ) || Q_isnan( v[ 2 ] ) )
 	{
 		Com_DPrintf( S_COLOR_YELLOW "WARNING: vector with one or more NaN components "
 				"being passed to OpenAL at %s:%d -- zeroing\n", __FILE__, line );
@@ -650,7 +647,7 @@
 =================
 */
 
-static void S_AL_ScaleGain(src_t *chksrc, const vec3_t origin)
+static void S_AL_ScaleGain(src_t *chksrc, vec3_t origin)
 {
 	float distance = 0.0f;
 	
@@ -818,9 +815,9 @@
 	// Set up OpenAL source
 	if(sfx >= 0)
 	{
-		// Mark the SFX as used, and grab the raw AL buffer
-		S_AL_BufferUse(sfx);
-		qalSourcei(curSource->alSource, AL_BUFFER, S_AL_BufferGet(sfx));
+        	// Mark the SFX as used, and grab the raw AL buffer
+        	S_AL_BufferUse(sfx);
+        	qalSourcei(curSource->alSource, AL_BUFFER, S_AL_BufferGet(sfx));
 	}
 
 	qalSourcef(curSource->alSource, AL_PITCH, 1.0f);
@@ -904,7 +901,7 @@
 			}
 		}
 		else if(curSfx->masterLoopSrc != -1 &&
-				rmSource == &srcList[curSfx->masterLoopSrc])
+		        rmSource == &srcList[curSfx->masterLoopSrc])
 		{
 			int firstInactive = -1;
 
@@ -1176,7 +1173,7 @@
 
 	VectorCopy( origin, sanOrigin );
 	S_AL_SanitiseVector( sanOrigin );
-	if ( entityNum < 0 || entityNum >= MAX_LOOP_SOUNDS )
+	if ( entityNum < 0 || entityNum >= MAX_GENTITIES )
 		Com_Error( ERR_DROP, "S_UpdateEntityPosition: bad entitynum %i", entityNum );
 	VectorCopy( sanOrigin, entityList[entityNum].origin );
 }
@@ -1190,7 +1187,7 @@
 */
 static qboolean S_AL_CheckInput(int entityNum, sfxHandle_t sfx)
 {
-	if (entityNum < 0 || entityNum >= MAX_LOOP_SOUNDS)
+	if (entityNum < 0 || entityNum >= MAX_GENTITIES)
 		Com_Error(ERR_DROP, "ERROR: S_AL_CheckInput: bad entitynum %i", entityNum);
 
 	if (sfx < 0 || sfx >= numSfx)
@@ -1238,7 +1235,7 @@
 Play a one-shot sound effect
 =================
 */
-static void S_AL_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
+static void S_AL_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
 {
 	vec3_t sorigin;
 	srcHandle_t src;
@@ -1614,15 +1611,15 @@
 
 		if(!curSource->isStream)
 		{
-			// Check if it's done, and flag it
-			qalGetSourcei(curSource->alSource, AL_SOURCE_STATE, &state);
-			if(state == AL_STOPPED)
-			{
-				curSource->isPlaying = qfalse;
-				S_AL_SrcKill(i);
-				continue;
-			}
-		}
+        		// Check if it's done, and flag it
+	        	qalGetSourcei(curSource->alSource, AL_SOURCE_STATE, &state);
+	        	if(state == AL_STOPPED)
+        		{
+	        		curSource->isPlaying = qfalse;
+		        	S_AL_SrcKill(i);
+		        	continue;
+        		}
+                }
 
 		// Query relativity of source, don't move if it's true
 		qalGetSourcei(curSource->alSource, AL_SOURCE_RELATIVE, &state);
@@ -1730,8 +1727,8 @@
         streamSourceHandles[stream] = cursrc;
        	streamSources[stream] = alsrc;
 
-		streamNumBuffers[stream] = 0;
-		streamBufIndex[stream] = 0;
+	streamNumBuffers[stream] = 0;
+	streamBufIndex[stream] = 0;
 }
 
 /*
@@ -1831,9 +1828,9 @@
 
 	if(entityNum < 0)
 	{
-		// Volume
-		S_AL_Gain (streamSources[stream], volume * s_volume->value * s_alGain->value);
-	}
+        	// Volume
+        	S_AL_Gain (streamSources[stream], volume * s_volume->value * s_alGain->value);
+        }
 
 	// Start stream
 	if(!streamPlaying[stream])
@@ -2125,14 +2122,13 @@
 	{
 		// Open the intro and don't mind whether it succeeds.
 		// The important part is the loop.
-		Com_Printf("^2openal opening intro\n");
 		intro_stream = S_CodecOpenStream(intro);
 	}
 	else
 		intro_stream = NULL;
 
 	mus_stream = S_CodecOpenStream(s_backgroundLoop);
-	if(!mus_stream)  //  &&  !intro_stream)
+	if(!mus_stream)
 	{
 		S_AL_CloseMusicFiles();
 		S_AL_MusicSourceFree();
@@ -2142,7 +2138,7 @@
 	// Generate the musicBuffers
 	if (!S_AL_GenBuffers(NUM_MUSIC_BUFFERS, musicBuffers, "music"))
 		return;
-
+	
 	// Queue the musicBuffers up
 	for(i = 0; i < NUM_MUSIC_BUFFERS; i++)
 	{
@@ -2244,25 +2240,20 @@
 =================
 */
 static
-void S_AL_Respatialize( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater )
+void S_AL_Respatialize( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater )
 {
 	float		orientation[6];
 	vec3_t	sorigin;
-	vec3_t ourAxis[3];  // avoid changing input 'axis'
-
-	VectorCopy(axis[0], ourAxis[0]);
-	VectorCopy(axis[1], ourAxis[1]);
-	VectorCopy(axis[2], ourAxis[2]);
 
 	VectorCopy( origin, sorigin );
 	S_AL_SanitiseVector( sorigin );
 
-	S_AL_SanitiseVector( ourAxis[ 0 ] );
-	S_AL_SanitiseVector( ourAxis[ 1 ] );
-	S_AL_SanitiseVector( ourAxis[ 2 ] );
+	S_AL_SanitiseVector( axis[ 0 ] );
+	S_AL_SanitiseVector( axis[ 1 ] );
+	S_AL_SanitiseVector( axis[ 2 ] );
 
-	orientation[0] = ourAxis[0][0]; orientation[1] = ourAxis[0][1]; orientation[2] = ourAxis[0][2];
-	orientation[3] = ourAxis[2][0]; orientation[4] = ourAxis[2][1]; orientation[5] = ourAxis[2][2];
+	orientation[0] = axis[0][0]; orientation[1] = axis[0][1]; orientation[2] = axis[0][2];
+	orientation[3] = axis[2][0]; orientation[4] = axis[2][1]; orientation[5] = axis[2][2];
 
 	lastListenerNumber = entityNum;
 	VectorCopy( sorigin, lastListenerOrigin );
@@ -2301,10 +2292,7 @@
 	// Update streams
 	for (i = 0; i < MAX_RAW_STREAMS; i++)
 		S_AL_StreamUpdate(i);
-
-	if (!cl_freezeDemo->integer  ||  (cl_freezeDemo->integer  &&  !cl_freezeDemoPauseMusic->integer)) {
-		S_AL_MusicUpdate();
-	}
+	S_AL_MusicUpdate();
 
 	// Doppler
 	if(s_doppler->modified)
@@ -2440,16 +2428,16 @@
 static void S_AL_SoundInfo(void)
 {
 	Com_Printf( "OpenAL info:\n" );
-	Com_Printf( "  Vendor:     %s\n", qalGetString( AL_VENDOR ) );
-	Com_Printf( "  Version:    %s\n", qalGetString( AL_VERSION ) );
-	Com_Printf( "  Renderer:   %s\n", qalGetString( AL_RENDERER ) );
-	Com_Printf( "  AL Extensions: %s\n", qalGetString( AL_EXTENSIONS ) );
+	Com_Printf( "  Vendor:         %s\n", qalGetString( AL_VENDOR ) );
+	Com_Printf( "  Version:        %s\n", qalGetString( AL_VERSION ) );
+	Com_Printf( "  Renderer:       %s\n", qalGetString( AL_RENDERER ) );
+	Com_Printf( "  AL Extensions:  %s\n", qalGetString( AL_EXTENSIONS ) );
 	Com_Printf( "  ALC Extensions: %s\n", qalcGetString( alDevice, ALC_EXTENSIONS ) );
 
 	if(enumeration_all_ext)
 		Com_Printf("  Device:         %s\n", qalcGetString(alDevice, ALC_ALL_DEVICES_SPECIFIER));
 	else if(enumeration_ext)
-		Com_Printf("  Device:     %s\n", qalcGetString(alDevice, ALC_DEVICE_SPECIFIER));
+		Com_Printf("  Device:         %s\n", qalcGetString(alDevice, ALC_DEVICE_SPECIFIER));
 
 	if(enumeration_all_ext || enumeration_ext)
 		Com_Printf("  Available Devices:\n%s", s_alAvailableDevices->string);
@@ -2463,18 +2451,7 @@
 #endif
 }
 
-static void S_AL_PrintSfxFilename (sfxHandle_t sfx)
-{
-	const alSfx_t *s;
-
-	if (sfx >= numSfx  ||  sfx < 0) {
-		Com_Printf("^3S_PrintSfxFilename() invalid handle: %d\n", sfx);
-	}
-
-	s = &knownSfx[sfx];
 
-	Com_Printf("'%s'\n", s->filename);
-}
 
 /*
 =================
@@ -2727,7 +2704,7 @@
 				alCaptureDevice = qalcCaptureOpenDevice(NULL, 48000, AL_FORMAT_MONO16, VOIP_MAX_PACKET_SAMPLES*4);
 			}
 			Com_Printf( "OpenAL capture device %s.\n",
-			            (alCaptureDevice == NULL) ? "failed to open" : "opened");
+				    (alCaptureDevice == NULL) ? "failed to open" : "opened");
 		}
 	}
 #endif
@@ -2752,7 +2729,6 @@
 	si->ClearSoundBuffer = S_AL_ClearSoundBuffer;
 	si->SoundInfo = S_AL_SoundInfo;
 	si->SoundList = S_AL_SoundList;
-	si->PrintSfxFilename = S_AL_PrintSfxFilename;
 
 #ifdef USE_VOIP
 	si->StartCapture = S_AL_StartCapture;

```

### `openarena-engine`  — sha256 `13ea3c1402de...`, 66625 bytes

_Diff stat: +63 / -94 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_openal.c	2026-04-16 20:02:25.179779600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_openal.c	2026-04-16 22:48:25.738377800 +0100
@@ -50,6 +50,7 @@
 #ifdef USE_VOIP
 static qboolean capture_ext = qfalse;
 #endif
+extern int xmpspeed; 		// leilei
 
 /*
 =================
@@ -135,7 +136,7 @@
 	snd_info_t	info;					// information for this sound like rate, sample count..
 
 	qboolean	isDefault;				// Couldn't be loaded - use default FX
-	qboolean 	isDefaultChecked;  		// Sound has been check if it isDefault
+	qboolean	isDefaultChecked;		// Sound has been check if it isDefault
 	qboolean	inMemory;				// Sound is stored in memory
 	qboolean	isLocked;				// Sound is locked (can not be unloaded)
 	int				lastUsedTime;		// Time last used
@@ -481,9 +482,7 @@
 	numSfx = 0;
 
 	// Load the default sound, and lock it
-	//default_sfx = S_AL_BufferFind("sound/feedback/hit.wav");
-	//default_sfx = S_AL_BufferFind("sound/feedback/hit.ogg");
-	default_sfx = S_AL_BufferFind("silence.wav");
+	default_sfx = S_AL_BufferFind("sound/misc/silence.wav");
 	S_AL_BufferUse(default_sfx);
 	knownSfx[default_sfx].isLocked = qtrue;
 
@@ -544,7 +543,7 @@
 =================
 S_AL_BufferGet
 
-Returns an sfx's buffer
+Return's a sfx's buffer
 =================
 */
 static
@@ -584,7 +583,7 @@
 	qboolean	local;			// Is this local (relative to the cam)
 } src_t;
 
-#ifdef __APPLE__
+#ifdef MACOS_X
 	#define MAX_SRC 64
 #else
 	#define MAX_SRC 128
@@ -609,8 +608,7 @@
 	qboolean				startLoopingSound;
 } sentity_t;
 
-// fx scripting uses entities past MAX_GENTITIES
-static sentity_t entityList[MAX_LOOP_SOUNDS];
+static sentity_t entityList[MAX_GENTITIES];
 
 /*
 =================
@@ -620,7 +618,7 @@
 #define S_AL_SanitiseVector(v) _S_AL_SanitiseVector(v,__LINE__)
 static void _S_AL_SanitiseVector( vec3_t v, int line )
 {
-	if( Q_floatIsNan( v[ 0 ] ) || Q_floatIsNan( v[ 1 ] ) || Q_floatIsNan( v[ 2 ] ) )
+	if( Q_isnan( v[ 0 ] ) || Q_isnan( v[ 1 ] ) || Q_isnan( v[ 2 ] ) )
 	{
 		Com_DPrintf( S_COLOR_YELLOW "WARNING: vector with one or more NaN components "
 				"being passed to OpenAL at %s:%d -- zeroing\n", __FILE__, line );
@@ -650,9 +648,9 @@
 =================
 */
 
-static void S_AL_ScaleGain(src_t *chksrc, const vec3_t origin)
+static void S_AL_ScaleGain(src_t *chksrc, vec3_t origin)
 {
-	float distance = 0.0f;
+	float distance;
 	
 	if(!chksrc->local)
 		distance = Distance(origin, lastListenerOrigin);
@@ -818,9 +816,9 @@
 	// Set up OpenAL source
 	if(sfx >= 0)
 	{
-		// Mark the SFX as used, and grab the raw AL buffer
-		S_AL_BufferUse(sfx);
-		qalSourcei(curSource->alSource, AL_BUFFER, S_AL_BufferGet(sfx));
+        	// Mark the SFX as used, and grab the raw AL buffer
+        	S_AL_BufferUse(sfx);
+        	qalSourcei(curSource->alSource, AL_BUFFER, S_AL_BufferGet(sfx));
 	}
 
 	qalSourcef(curSource->alSource, AL_PITCH, 1.0f);
@@ -844,7 +842,7 @@
 
 /*
 =================
-S_AL_SaveLoopPos
+S_AL_NewLoopMaster
 Remove given source as loop master if it is the master and hand off master status to another source in this case.
 =================
 */
@@ -903,8 +901,7 @@
 				S_AL_SaveLoopPos(rmSource, rmSource->alSource);
 			}
 		}
-		else if(curSfx->masterLoopSrc != -1 &&
-				rmSource == &srcList[curSfx->masterLoopSrc])
+		else if(rmSource == &srcList[curSfx->masterLoopSrc])
 		{
 			int firstInactive = -1;
 
@@ -1176,7 +1173,7 @@
 
 	VectorCopy( origin, sanOrigin );
 	S_AL_SanitiseVector( sanOrigin );
-	if ( entityNum < 0 || entityNum >= MAX_LOOP_SOUNDS )
+	if ( entityNum < 0 || entityNum >= MAX_GENTITIES )
 		Com_Error( ERR_DROP, "S_UpdateEntityPosition: bad entitynum %i", entityNum );
 	VectorCopy( sanOrigin, entityList[entityNum].origin );
 }
@@ -1190,7 +1187,7 @@
 */
 static qboolean S_AL_CheckInput(int entityNum, sfxHandle_t sfx)
 {
-	if (entityNum < 0 || entityNum >= MAX_LOOP_SOUNDS)
+	if (entityNum < 0 || entityNum >= MAX_GENTITIES)
 		Com_Error(ERR_DROP, "ERROR: S_AL_CheckInput: bad entitynum %i", entityNum);
 
 	if (sfx < 0 || sfx >= numSfx)
@@ -1238,7 +1235,7 @@
 Play a one-shot sound effect
 =================
 */
-static void S_AL_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
+static void S_AL_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
 {
 	vec3_t sorigin;
 	srcHandle_t src;
@@ -1614,15 +1611,15 @@
 
 		if(!curSource->isStream)
 		{
-			// Check if it's done, and flag it
-			qalGetSourcei(curSource->alSource, AL_SOURCE_STATE, &state);
-			if(state == AL_STOPPED)
-			{
-				curSource->isPlaying = qfalse;
-				S_AL_SrcKill(i);
-				continue;
-			}
-		}
+        		// Check if it's done, and flag it
+	        	qalGetSourcei(curSource->alSource, AL_SOURCE_STATE, &state);
+	        	if(state == AL_STOPPED)
+        		{
+	        		curSource->isPlaying = qfalse;
+		        	S_AL_SrcKill(i);
+		        	continue;
+        		}
+                }
 
 		// Query relativity of source, don't move if it's true
 		qalGetSourcei(curSource->alSource, AL_SOURCE_RELATIVE, &state);
@@ -1730,8 +1727,8 @@
         streamSourceHandles[stream] = cursrc;
        	streamSources[stream] = alsrc;
 
-		streamNumBuffers[stream] = 0;
-		streamBufIndex[stream] = 0;
+	streamNumBuffers[stream] = 0;
+	streamBufIndex[stream] = 0;
 }
 
 /*
@@ -1831,9 +1828,9 @@
 
 	if(entityNum < 0)
 	{
-		// Volume
-		S_AL_Gain (streamSources[stream], volume * s_volume->value * s_alGain->value);
-	}
+        	// Volume
+        	S_AL_Gain (streamSources[stream], volume * s_volume->value * s_alGain->value);
+        }
 
 	// Start stream
 	if(!streamPlaying[stream])
@@ -2119,20 +2116,19 @@
 		issame = qfalse;
 
 	// Copy the loop over
-	Q_strncpyz( s_backgroundLoop, loop, sizeof( s_backgroundLoop ) );
+	strncpy( s_backgroundLoop, loop, sizeof( s_backgroundLoop ) );
 
 	if(!issame)
 	{
 		// Open the intro and don't mind whether it succeeds.
 		// The important part is the loop.
-		Com_Printf("^2openal opening intro\n");
 		intro_stream = S_CodecOpenStream(intro);
 	}
 	else
 		intro_stream = NULL;
 
 	mus_stream = S_CodecOpenStream(s_backgroundLoop);
-	if(!mus_stream)  //  &&  !intro_stream)
+	if(!mus_stream)
 	{
 		S_AL_CloseMusicFiles();
 		S_AL_MusicSourceFree();
@@ -2142,7 +2138,7 @@
 	// Generate the musicBuffers
 	if (!S_AL_GenBuffers(NUM_MUSIC_BUFFERS, musicBuffers, "music"))
 		return;
-
+	
 	// Queue the musicBuffers up
 	for(i = 0; i < NUM_MUSIC_BUFFERS; i++)
 	{
@@ -2211,11 +2207,9 @@
 static cvar_t *s_alCapture;
 #endif
 
-#if defined(_WIN64)
-#define ALDRIVER_DEFAULT "OpenAL64.dll"
-#elif defined(_WIN32)
+#ifdef _WIN32
 #define ALDRIVER_DEFAULT "OpenAL32.dll"
-#elif defined(__APPLE__)
+#elif defined(MACOS_X)
 #define ALDRIVER_DEFAULT "/System/Library/Frameworks/OpenAL.framework/OpenAL"
 #elif defined(__OpenBSD__)
 #define ALDRIVER_DEFAULT "libopenal.so"
@@ -2244,25 +2238,20 @@
 =================
 */
 static
-void S_AL_Respatialize( int entityNum, const vec3_t origin, const vec3_t axis[3], int inwater )
+void S_AL_Respatialize( int entityNum, const vec3_t origin, vec3_t axis[3], int inwater )
 {
 	float		orientation[6];
 	vec3_t	sorigin;
-	vec3_t ourAxis[3];  // avoid changing input 'axis'
-
-	VectorCopy(axis[0], ourAxis[0]);
-	VectorCopy(axis[1], ourAxis[1]);
-	VectorCopy(axis[2], ourAxis[2]);
 
 	VectorCopy( origin, sorigin );
 	S_AL_SanitiseVector( sorigin );
 
-	S_AL_SanitiseVector( ourAxis[ 0 ] );
-	S_AL_SanitiseVector( ourAxis[ 1 ] );
-	S_AL_SanitiseVector( ourAxis[ 2 ] );
+	S_AL_SanitiseVector( axis[ 0 ] );
+	S_AL_SanitiseVector( axis[ 1 ] );
+	S_AL_SanitiseVector( axis[ 2 ] );
 
-	orientation[0] = ourAxis[0][0]; orientation[1] = ourAxis[0][1]; orientation[2] = ourAxis[0][2];
-	orientation[3] = ourAxis[2][0]; orientation[4] = ourAxis[2][1]; orientation[5] = ourAxis[2][2];
+	orientation[0] = axis[0][0]; orientation[1] = axis[0][1]; orientation[2] = axis[0][2];
+	orientation[3] = axis[2][0]; orientation[4] = axis[2][1]; orientation[5] = axis[2][2];
 
 	lastListenerNumber = entityNum;
 	VectorCopy( sorigin, lastListenerOrigin );
@@ -2301,10 +2290,7 @@
 	// Update streams
 	for (i = 0; i < MAX_RAW_STREAMS; i++)
 		S_AL_StreamUpdate(i);
-
-	if (!cl_freezeDemo->integer  ||  (cl_freezeDemo->integer  &&  !cl_freezeDemoPauseMusic->integer)) {
-		S_AL_MusicUpdate();
-	}
+	S_AL_MusicUpdate();
 
 	// Doppler
 	if(s_doppler->modified)
@@ -2324,7 +2310,7 @@
 	}
 	if(s_alDopplerSpeed->modified)
 	{
-		qalSpeedOfSound(s_alDopplerSpeed->value);
+		qalDopplerVelocity(s_alDopplerSpeed->value);
 		s_alDopplerSpeed->modified = qfalse;
 	}
 
@@ -2377,18 +2363,6 @@
 static
 void S_AL_SoundList( void )
 {
-	int		i;
-	alSfx_t	*sfx;
-	int		size, total;
-
-	total = 0;
-	for (sfx=knownSfx, i=0 ; i<numSfx ; i++, sfx++) {
-		size = sfx->info.samples;
-		total += size;
-		Com_Printf("%6i : %s[%s]\n", size,
-				sfx->filename, sfx->inMemory ? "resident " : "paged out");
-	}
-	Com_Printf ("Total resident: %i\n", total);
 }
 
 #ifdef USE_VOIP
@@ -2440,16 +2414,16 @@
 static void S_AL_SoundInfo(void)
 {
 	Com_Printf( "OpenAL info:\n" );
-	Com_Printf( "  Vendor:     %s\n", qalGetString( AL_VENDOR ) );
-	Com_Printf( "  Version:    %s\n", qalGetString( AL_VERSION ) );
-	Com_Printf( "  Renderer:   %s\n", qalGetString( AL_RENDERER ) );
-	Com_Printf( "  AL Extensions: %s\n", qalGetString( AL_EXTENSIONS ) );
+	Com_Printf( "  Vendor:         %s\n", qalGetString( AL_VENDOR ) );
+	Com_Printf( "  Version:        %s\n", qalGetString( AL_VERSION ) );
+	Com_Printf( "  Renderer:       %s\n", qalGetString( AL_RENDERER ) );
+	Com_Printf( "  AL Extensions:  %s\n", qalGetString( AL_EXTENSIONS ) );
 	Com_Printf( "  ALC Extensions: %s\n", qalcGetString( alDevice, ALC_EXTENSIONS ) );
 
 	if(enumeration_all_ext)
 		Com_Printf("  Device:         %s\n", qalcGetString(alDevice, ALC_ALL_DEVICES_SPECIFIER));
 	else if(enumeration_ext)
-		Com_Printf("  Device:     %s\n", qalcGetString(alDevice, ALC_DEVICE_SPECIFIER));
+		Com_Printf("  Device:         %s\n", qalcGetString(alDevice, ALC_DEVICE_SPECIFIER));
 
 	if(enumeration_all_ext || enumeration_ext)
 		Com_Printf("  Available Devices:\n%s", s_alAvailableDevices->string);
@@ -2463,18 +2437,7 @@
 #endif
 }
 
-static void S_AL_PrintSfxFilename (sfxHandle_t sfx)
-{
-	const alSfx_t *s;
 
-	if (sfx >= numSfx  ||  sfx < 0) {
-		Com_Printf("^3S_PrintSfxFilename() invalid handle: %d\n", sfx);
-	}
-
-	s = &knownSfx[sfx];
-
-	Com_Printf("'%s'\n", s->filename);
-}
 
 /*
 =================
@@ -2544,17 +2507,20 @@
 	s_alGain = Cvar_Get( "s_alGain", "1.0", CVAR_ARCHIVE );
 	s_alSources = Cvar_Get( "s_alSources", "96", CVAR_ARCHIVE );
 	s_alDopplerFactor = Cvar_Get( "s_alDopplerFactor", "1.0", CVAR_ARCHIVE );
-	s_alDopplerSpeed = Cvar_Get( "s_alDopplerSpeed", "9000", CVAR_ARCHIVE );
+	s_alDopplerSpeed = Cvar_Get( "s_alDopplerSpeed", "2200", CVAR_ARCHIVE );
 	s_alMinDistance = Cvar_Get( "s_alMinDistance", "120", CVAR_CHEAT );
 	s_alMaxDistance = Cvar_Get("s_alMaxDistance", "1024", CVAR_CHEAT);
 	s_alRolloff = Cvar_Get( "s_alRolloff", "2", CVAR_CHEAT);
 	s_alGraceDistance = Cvar_Get("s_alGraceDistance", "512", CVAR_CHEAT);
 
-	s_alDriver = Cvar_Get( "s_alDriver", ALDRIVER_DEFAULT, CVAR_ARCHIVE | CVAR_LATCH | CVAR_PROTECTED );
+	s_alDriver = Cvar_Get( "s_alDriver", ALDRIVER_DEFAULT, CVAR_ARCHIVE | CVAR_LATCH );
 
 	s_alInputDevice = Cvar_Get( "s_alInputDevice", "", CVAR_ARCHIVE | CVAR_LATCH );
 	s_alDevice = Cvar_Get("s_alDevice", "", CVAR_ARCHIVE | CVAR_LATCH);
 
+
+	xmpspeed = 48000; // leilei - force it to 48000 which is the native mixing rate post-ac'97
+
 	// Load QAL
 	if( !QAL_Init( s_alDriver->string ) )
 	{
@@ -2661,7 +2627,7 @@
 	// Set up OpenAL parameters (doppler, etc)
 	qalDistanceModel(AL_INVERSE_DISTANCE_CLAMPED);
 	qalDopplerFactor( s_alDopplerFactor->value );
-	qalSpeedOfSound( s_alDopplerSpeed->value );
+	qalDopplerVelocity( s_alDopplerSpeed->value );
 
 #ifdef USE_VOIP
 	// !!! FIXME: some of these alcCaptureOpenDevice() values should be cvars.
@@ -2680,7 +2646,7 @@
 #endif
 	else
 	{
-#ifdef __APPLE__
+#ifdef MACOS_X
 		// !!! FIXME: Apple has a 1.1-compliant OpenAL, which includes
 		// !!! FIXME:  capture support, but they don't list it in the
 		// !!! FIXME:  extension string. We need to check the version string,
@@ -2719,15 +2685,19 @@
 
 			s_alAvailableInputDevices = Cvar_Get("s_alAvailableInputDevices", inputdevicenames, CVAR_ROM | CVAR_NORESTART);
 
+			// !!! FIXME: 8000Hz is what Speex narrowband mode needs, but we
+			// !!! FIXME:  should probably open the capture device after
+			// !!! FIXME:  initializing Speex so we can change to wideband
+			// !!! FIXME:  if we like.
 			Com_Printf("OpenAL default capture device is '%s'\n", defaultinputdevice ? defaultinputdevice : "none");
-			alCaptureDevice = qalcCaptureOpenDevice(inputdevice, 48000, AL_FORMAT_MONO16, VOIP_MAX_PACKET_SAMPLES*4);
+			alCaptureDevice = qalcCaptureOpenDevice(inputdevice, 8000, AL_FORMAT_MONO16, 4096);
 			if( !alCaptureDevice && inputdevice )
 			{
 				Com_Printf( "Failed to open OpenAL Input device '%s', trying default.\n", inputdevice );
-				alCaptureDevice = qalcCaptureOpenDevice(NULL, 48000, AL_FORMAT_MONO16, VOIP_MAX_PACKET_SAMPLES*4);
+				alCaptureDevice = qalcCaptureOpenDevice(NULL, 8000, AL_FORMAT_MONO16, 4096);
 			}
 			Com_Printf( "OpenAL capture device %s.\n",
-			            (alCaptureDevice == NULL) ? "failed to open" : "opened");
+				    (alCaptureDevice == NULL) ? "failed to open" : "opened");
 		}
 	}
 #endif
@@ -2752,7 +2722,6 @@
 	si->ClearSoundBuffer = S_AL_ClearSoundBuffer;
 	si->SoundInfo = S_AL_SoundInfo;
 	si->SoundList = S_AL_SoundList;
-	si->PrintSfxFilename = S_AL_PrintSfxFilename;
 
 #ifdef USE_VOIP
 	si->StartCapture = S_AL_StartCapture;

```
