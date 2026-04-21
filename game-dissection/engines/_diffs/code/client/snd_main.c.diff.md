# Diff: `code/client/snd_main.c`
**Canonical:** `wolfcamql-src` (sha256 `f3145c969d83...`, 14251 bytes)

## Variants

### `ioquake3`  — sha256 `d6298f2f5443...`, 11079 bytes

_Diff stat: +12 / -113 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_main.c	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_main.c	2026-04-16 20:02:21.533570500 +0100
@@ -33,15 +33,6 @@
 cvar_t *s_backend;
 cvar_t *s_muteWhenMinimized;
 cvar_t *s_muteWhenUnfocused;
-cvar_t *s_announcerVolume;
-cvar_t *s_killBeepVolume;
-cvar_t *s_useTimescale;
-cvar_t *s_forceScale;
-cvar_t *s_showMiss;
-cvar_t *s_maxSoundRepeatTime;
-cvar_t *s_maxSoundInstances;
-cvar_t *s_qlAttenuate;
-cvar_t *s_debugMissingSounds;
 
 static soundInterface_t si;
 
@@ -89,7 +80,7 @@
 S_StartSound
 =================
 */
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
 {
 	if( si.StartSound ) {
 		si.StartSound( origin, entnum, entchannel, sfx );
@@ -115,34 +106,8 @@
 */
 void S_StartBackgroundTrack( const char *intro, const char *loop )
 {
-	// quakelive hack, all files default to ogg
-	char introx[MAX_STRING_CHARS];
-	char loopx[MAX_STRING_CHARS];
-
-	//Com_Printf("S_StartBackgroundTrack intro:'%s'  loop:'%s'\n", intro, loop);
-
-	COM_StripExtension(intro, introx, sizeof(introx));
-	COM_StripExtension(loop, loopx, sizeof(loopx));
-
-	Q_strcat(introx, sizeof(introx), ".ogg");
-	Q_strcat(loopx, sizeof(loopx), ".ogg");
-	//Com_Printf("intro:%s  loop:%s\n", introx, loopx);
-
-	if (!*intro  &&  !*loop) {
-		// request to stop background track
-		introx[0] = '\0';
-		loopx[0] = '\0';
-	}
-
 	if( si.StartBackgroundTrack ) {
-		//si.StartBackgroundTrack( intro, loop );
-		if (!*loop) {
-			//Com_Printf("^2using intro as loop\n");
-			si.StartBackgroundTrack(introx, introx);
-		} else {
-			//Com_Printf("^2loop and intro\n");
-			si.StartBackgroundTrack( introx, loopx );
-		}
+		si.StartBackgroundTrack( intro, loop );
 	}
 }
 
@@ -164,7 +129,7 @@
 =================
 */
 void S_RawSamples (int stream, int samples, int rate, int width, int channels,
-				   const byte *data, float volume, int entityNum)
+		   const byte *data, float volume, int entityNum)
 {
 	if(si.RawSamples)
 		si.RawSamples(stream, samples, rate, width, channels, data, volume, entityNum);
@@ -202,7 +167,6 @@
 void S_AddLoopingSound( int entityNum, const vec3_t origin,
 		const vec3_t velocity, sfxHandle_t sfx )
 {
-	//Com_Printf("adding looping sound: %d\n", sfx);
 	if( si.AddLoopingSound ) {
 		si.AddLoopingSound( entityNum, origin, velocity, sfx );
 	}
@@ -239,7 +203,7 @@
 =================
 */
 void S_Respatialize( int entityNum, const vec3_t origin,
-		const vec3_t axis[3], int inwater )
+		vec3_t axis[3], int inwater )
 {
 	if( si.Respatialize ) {
 		si.Respatialize( entityNum, origin, axis, inwater );
@@ -283,11 +247,7 @@
 			s_muted->modified = qtrue;
 		}
 	}
-
-	if (CL_VideoRecording(&afdMain)  &&  (cl_freezeDemoPauseVideoRecording->integer  &&  cl_freezeDemo->integer)) {
-		return;
-	}
-
+	
 	if( si.Update ) {
 		si.Update( );
 	}
@@ -324,57 +284,13 @@
 */
 sfxHandle_t	S_RegisterSound( const char *sample, qboolean compressed )
 {
-	sfxHandle_t s;
-	char newName[MAX_QPATH];
-	int slen;
-
-	if (sample == NULL) {
-		Com_Printf("^1%s() sample == NULL (shouldn't happen)\n", __FUNCTION__);
-		return 0;
-	}
-	//Com_Printf("S_RegisterSound %s\n", sample);
-
 	if( si.RegisterSound ) {
-		slen = strlen(sample);
-		if (slen >= 5) {
-			// first try ogg
-			//strncpy(newName, sample, MAX_QPATH);
-			COM_StripExtension(sample, newName, sizeof(newName));
-			slen = strlen(newName);
-			s = 0;
-			if (slen + 5 >= sizeof(newName)) {
-				Com_Printf("^3%s() couldn't add ogg extension to '%s', name is too long\n", __FUNCTION__, sample);
-				s = 0;
-			} else {
-				newName[slen + 0] = '.';
-				newName[slen + 1] = 'o';
-				newName[slen + 2] = 'g';
-				newName[slen + 3] = 'g';
-				newName[slen + 4] = '\0';
-				s = si.RegisterSound(newName, compressed);
-			}
-			if (!s) {
-				s = si.RegisterSound(sample, compressed);
-			}
-			if (!s) {
-				//Com_Printf("^1S_RegisterSound() couldn't open '%s' or '%s'\n", newName, sample);
-				Com_Printf("^1S_RegisterSound() couldn't open '%s'\n", sample);
-			}
-			return s;
-		} else {
-			Com_Printf("^3FIXME S_RegisterSound() '%s' name is too short\n", sample);
-			return si.RegisterSound( sample, compressed );
-		}
+		return si.RegisterSound( sample, compressed );
 	} else {
 		return 0;
 	}
 }
 
-void S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	si.PrintSfxFilename(sfx);
-}
-
 /*
 =================
 S_ClearSoundBuffer
@@ -484,7 +400,7 @@
 */
 void S_Play_f( void ) {
 	int 		i;
-	int                     c;
+	int			c;
 	sfxHandle_t	h;
 
 	if( !si.RegisterSound || !si.StartLocalSound ) {
@@ -499,7 +415,7 @@
 	}
 
 	for( i = 1; i < c; i++ ) {
-		h = S_RegisterSound(Cmd_Argv(i), qfalse);
+		h = si.RegisterSound( Cmd_Argv(i), qfalse );
 
 		if( h ) {
 			si.StartLocalSound( h, CHAN_LOCAL_SOUND );
@@ -561,21 +477,12 @@
 	Com_Printf( "------ Initializing Sound ------\n" );
 
 	s_volume = Cvar_Get( "s_volume", "0.8", CVAR_ARCHIVE );
-	s_musicVolume = Cvar_Get( "s_musicvolume", "0", CVAR_ARCHIVE );
+	s_musicVolume = Cvar_Get( "s_musicvolume", "0.25", CVAR_ARCHIVE );
 	s_muted = Cvar_Get("s_muted", "0", CVAR_ROM);
 	s_doppler = Cvar_Get( "s_doppler", "1", CVAR_ARCHIVE );
-	s_backend = Cvar_Get( "s_backend", "base", CVAR_ROM );
+	s_backend = Cvar_Get( "s_backend", "", CVAR_ROM );
 	s_muteWhenMinimized = Cvar_Get( "s_muteWhenMinimized", "0", CVAR_ARCHIVE );
 	s_muteWhenUnfocused = Cvar_Get( "s_muteWhenUnfocused", "0", CVAR_ARCHIVE );
-	s_announcerVolume = Cvar_Get("s_announcerVolume", "1.0", CVAR_ARCHIVE);
-	s_killBeepVolume = Cvar_Get("s_killBeepVolume", "1.0", CVAR_ARCHIVE);
-	s_useTimescale = Cvar_Get("s_useTimescale", "0", CVAR_ARCHIVE);
-	s_forceScale = Cvar_Get("s_forceScale", "0.0", CVAR_ARCHIVE);
-	s_showMiss = Cvar_Get("s_showMiss", "0", CVAR_ARCHIVE);
-	s_maxSoundRepeatTime = Cvar_Get("s_maxSoundRepeatTime", "0", CVAR_ARCHIVE);
-	s_maxSoundInstances = Cvar_Get("s_maxSoundInstances", "96", CVAR_ARCHIVE);
-	s_qlAttenuate = Cvar_Get("s_qlAttenuate", "1", CVAR_ARCHIVE);
-	s_debugMissingSounds = Cvar_Get("s_debugMissingSounds", "0", CVAR_ARCHIVE);
 
 	cv = Cvar_Get( "s_initsound", "1", 0 );
 	if( !cv->integer ) {
@@ -591,7 +498,7 @@
 		Cmd_AddCommand( "s_stop", S_StopAllSounds );
 		Cmd_AddCommand( "s_info", S_SoundInfo );
 
-		cv = Cvar_Get( "s_useOpenAL", "0", CVAR_ARCHIVE | CVAR_LATCH );
+		cv = Cvar_Get( "s_useOpenAL", "1", CVAR_ARCHIVE | CVAR_LATCH );
 		if( cv->integer ) {
 			//OpenAL
 			started = S_AL_Init( &si );
@@ -605,7 +512,7 @@
 
 		if( started ) {
 			if( !S_ValidSoundInterface( &si ) ) {
-				Com_Error( ERR_FATAL, "Sound interface invalid." );
+				Com_Error( ERR_FATAL, "Sound interface invalid" );
 			}
 
 			S_SoundInfo( );
@@ -641,11 +548,3 @@
 	S_CodecShutdown( );
 }
 
-int S_Milliseconds (void)
-{
-	int t;
-
-	t = Com_Milliseconds();
-
-	return t;
-}

```

### `quake3e`  — sha256 `03f4e64f2c36...`, 10151 bytes

_Diff stat: +101 / -261 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_main.c	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_main.c	2026-04-16 20:02:26.916520900 +0100
@@ -27,21 +27,10 @@
 #include "snd_public.h"
 
 cvar_t *s_volume;
-cvar_t *s_muted;
 cvar_t *s_musicVolume;
 cvar_t *s_doppler;
-cvar_t *s_backend;
 cvar_t *s_muteWhenMinimized;
 cvar_t *s_muteWhenUnfocused;
-cvar_t *s_announcerVolume;
-cvar_t *s_killBeepVolume;
-cvar_t *s_useTimescale;
-cvar_t *s_forceScale;
-cvar_t *s_showMiss;
-cvar_t *s_maxSoundRepeatTime;
-cvar_t *s_maxSoundInstances;
-cvar_t *s_qlAttenuate;
-cvar_t *s_debugMissingSounds;
 
 static soundInterface_t si;
 
@@ -50,52 +39,46 @@
 S_ValidateInterface
 =================
 */
-static qboolean S_ValidSoundInterface( soundInterface_t *pSi )
+static qboolean S_ValidSoundInterface( const soundInterface_t *s )
 {
-	if( !pSi->Shutdown ) return qfalse;
-	if( !pSi->StartSound ) return qfalse;
-	if( !pSi->StartLocalSound ) return qfalse;
-	if( !pSi->StartBackgroundTrack ) return qfalse;
-	if( !pSi->StopBackgroundTrack ) return qfalse;
-	if( !pSi->RawSamples ) return qfalse;
-	if( !pSi->StopAllSounds ) return qfalse;
-	if( !pSi->ClearLoopingSounds ) return qfalse;
-	if( !pSi->AddLoopingSound ) return qfalse;
-	if( !pSi->AddRealLoopingSound ) return qfalse;
-	if( !pSi->StopLoopingSound ) return qfalse;
-	if( !pSi->Respatialize ) return qfalse;
-	if( !pSi->UpdateEntityPosition ) return qfalse;
-	if( !pSi->Update ) return qfalse;
-	if( !pSi->DisableSounds ) return qfalse;
-	if( !pSi->BeginRegistration ) return qfalse;
-	if( !pSi->RegisterSound ) return qfalse;
-	if( !pSi->ClearSoundBuffer ) return qfalse;
-	if( !pSi->SoundInfo ) return qfalse;
-	if( !pSi->SoundList ) return qfalse;
-
-#ifdef USE_VOIP
-	if( !pSi->StartCapture ) return qfalse;
-	if( !pSi->AvailableCaptureSamples ) return qfalse;
-	if( !pSi->Capture ) return qfalse;
-	if( !pSi->StopCapture ) return qfalse;
-	if( !pSi->MasterGain ) return qfalse;
-#endif
+	if( !s->Shutdown ) return qfalse;
+	if( !s->StartSound ) return qfalse;
+	if( !s->StartLocalSound ) return qfalse;
+	if( !s->StartBackgroundTrack ) return qfalse;
+	if( !s->StopBackgroundTrack ) return qfalse;
+	if( !s->RawSamples ) return qfalse;
+	if( !s->StopAllSounds ) return qfalse;
+	if( !s->ClearLoopingSounds ) return qfalse;
+	if( !s->AddLoopingSound ) return qfalse;
+	if( !s->AddRealLoopingSound ) return qfalse;
+	if( !s->StopLoopingSound ) return qfalse;
+	if( !s->Respatialize ) return qfalse;
+	if( !s->UpdateEntityPosition ) return qfalse;
+	if( !s->Update ) return qfalse;
+	if( !s->DisableSounds ) return qfalse;
+	if( !s->BeginRegistration ) return qfalse;
+	if( !s->RegisterSound ) return qfalse;
+	if( !s->ClearSoundBuffer ) return qfalse;
+	if( !s->SoundInfo ) return qfalse;
+	if( !s->SoundList ) return qfalse;
 
 	return qtrue;
 }
 
+
 /*
 =================
 S_StartSound
 =================
 */
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
 {
 	if( si.StartSound ) {
 		si.StartSound( origin, entnum, entchannel, sfx );
 	}
 }
 
+
 /*
 =================
 S_StartLocalSound
@@ -108,6 +91,7 @@
 	}
 }
 
+
 /*
 =================
 S_StartBackgroundTrack
@@ -115,37 +99,12 @@
 */
 void S_StartBackgroundTrack( const char *intro, const char *loop )
 {
-	// quakelive hack, all files default to ogg
-	char introx[MAX_STRING_CHARS];
-	char loopx[MAX_STRING_CHARS];
-
-	//Com_Printf("S_StartBackgroundTrack intro:'%s'  loop:'%s'\n", intro, loop);
-
-	COM_StripExtension(intro, introx, sizeof(introx));
-	COM_StripExtension(loop, loopx, sizeof(loopx));
-
-	Q_strcat(introx, sizeof(introx), ".ogg");
-	Q_strcat(loopx, sizeof(loopx), ".ogg");
-	//Com_Printf("intro:%s  loop:%s\n", introx, loopx);
-
-	if (!*intro  &&  !*loop) {
-		// request to stop background track
-		introx[0] = '\0';
-		loopx[0] = '\0';
-	}
-
 	if( si.StartBackgroundTrack ) {
-		//si.StartBackgroundTrack( intro, loop );
-		if (!*loop) {
-			//Com_Printf("^2using intro as loop\n");
-			si.StartBackgroundTrack(introx, introx);
-		} else {
-			//Com_Printf("^2loop and intro\n");
-			si.StartBackgroundTrack( introx, loopx );
-		}
+		si.StartBackgroundTrack( intro, loop );
 	}
 }
 
+
 /*
 =================
 S_StopBackgroundTrack
@@ -158,18 +117,21 @@
 	}
 }
 
+
 /*
 =================
 S_RawSamples
 =================
 */
-void S_RawSamples (int stream, int samples, int rate, int width, int channels,
-				   const byte *data, float volume, int entityNum)
+void S_RawSamples (int samples, int rate, int width, int channels,
+		   const byte *data, float volume)
 {
-	if(si.RawSamples)
-		si.RawSamples(stream, samples, rate, width, channels, data, volume, entityNum);
+	if( si.RawSamples ) {
+		si.RawSamples( samples, rate, width, channels, data, volume );
+	}
 }
 
+
 /*
 =================
 S_StopAllSounds
@@ -178,10 +140,11 @@
 void S_StopAllSounds( void )
 {
 	if( si.StopAllSounds ) {
-		si.StopAllSounds( );
+		si.StopAllSounds();
 	}
 }
 
+
 /*
 =================
 S_ClearLoopingSounds
@@ -194,6 +157,7 @@
 	}
 }
 
+
 /*
 =================
 S_AddLoopingSound
@@ -202,12 +166,12 @@
 void S_AddLoopingSound( int entityNum, const vec3_t origin,
 		const vec3_t velocity, sfxHandle_t sfx )
 {
-	//Com_Printf("adding looping sound: %d\n", sfx);
 	if( si.AddLoopingSound ) {
 		si.AddLoopingSound( entityNum, origin, velocity, sfx );
 	}
 }
 
+
 /*
 =================
 S_AddRealLoopingSound
@@ -221,6 +185,7 @@
 	}
 }
 
+
 /*
 =================
 S_StopLoopingSound
@@ -233,19 +198,21 @@
 	}
 }
 
+
 /*
 =================
 S_Respatialize
 =================
 */
 void S_Respatialize( int entityNum, const vec3_t origin,
-		const vec3_t axis[3], int inwater )
+		vec3_t axis[3], int inwater )
 {
 	if( si.Respatialize ) {
 		si.Respatialize( entityNum, origin, axis, inwater );
 	}
 }
 
+
 /*
 =================
 S_UpdateEntityPosition
@@ -258,41 +225,20 @@
 	}
 }
 
+
 /*
 =================
 S_Update
 =================
 */
-void S_Update( void )
+void S_Update( int msec )
 {
-	if(s_muted->integer)
-	{
-		if(!(s_muteWhenMinimized->integer && com_minimized->integer) &&
-		   !(s_muteWhenUnfocused->integer && com_unfocused->integer))
-		{
-			s_muted->integer = qfalse;
-			s_muted->modified = qtrue;
-		}
-	}
-	else
-	{
-		if((s_muteWhenMinimized->integer && com_minimized->integer) ||
-		   (s_muteWhenUnfocused->integer && com_unfocused->integer))
-		{
-			s_muted->integer = qtrue;
-			s_muted->modified = qtrue;
-		}
-	}
-
-	if (CL_VideoRecording(&afdMain)  &&  (cl_freezeDemoPauseVideoRecording->integer  &&  cl_freezeDemo->integer)) {
-		return;
-	}
-
-	if( si.Update ) {
-		si.Update( );
+	if ( si.Update ) {
+		si.Update( msec );
 	}
 }
 
+
 /*
 =================
 S_DisableSounds
@@ -301,10 +247,11 @@
 void S_DisableSounds( void )
 {
 	if( si.DisableSounds ) {
-		si.DisableSounds( );
+		si.DisableSounds();
 	}
 }
 
+
 /*
 =================
 S_BeginRegistration
@@ -312,11 +259,12 @@
 */
 void S_BeginRegistration( void )
 {
-	if( si.BeginRegistration ) {
-		si.BeginRegistration( );
+	if ( si.BeginRegistration ) {
+		si.BeginRegistration();
 	}
 }
 
+
 /*
 =================
 S_RegisterSound
@@ -324,56 +272,18 @@
 */
 sfxHandle_t	S_RegisterSound( const char *sample, qboolean compressed )
 {
-	sfxHandle_t s;
-	char newName[MAX_QPATH];
-	int slen;
-
-	if (sample == NULL) {
-		Com_Printf("^1%s() sample == NULL (shouldn't happen)\n", __FUNCTION__);
+	if ( !sample || !*sample ) {
+		Com_Printf( "NULL sound\n" );
 		return 0;
 	}
-	//Com_Printf("S_RegisterSound %s\n", sample);
 
 	if( si.RegisterSound ) {
-		slen = strlen(sample);
-		if (slen >= 5) {
-			// first try ogg
-			//strncpy(newName, sample, MAX_QPATH);
-			COM_StripExtension(sample, newName, sizeof(newName));
-			slen = strlen(newName);
-			s = 0;
-			if (slen + 5 >= sizeof(newName)) {
-				Com_Printf("^3%s() couldn't add ogg extension to '%s', name is too long\n", __FUNCTION__, sample);
-				s = 0;
-			} else {
-				newName[slen + 0] = '.';
-				newName[slen + 1] = 'o';
-				newName[slen + 2] = 'g';
-				newName[slen + 3] = 'g';
-				newName[slen + 4] = '\0';
-				s = si.RegisterSound(newName, compressed);
-			}
-			if (!s) {
-				s = si.RegisterSound(sample, compressed);
-			}
-			if (!s) {
-				//Com_Printf("^1S_RegisterSound() couldn't open '%s' or '%s'\n", newName, sample);
-				Com_Printf("^1S_RegisterSound() couldn't open '%s'\n", sample);
-			}
-			return s;
-		} else {
-			Com_Printf("^3FIXME S_RegisterSound() '%s' name is too short\n", sample);
-			return si.RegisterSound( sample, compressed );
-		}
+		return si.RegisterSound( sample, compressed );
 	} else {
 		return 0;
 	}
 }
 
-void S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	si.PrintSfxFilename(sfx);
-}
 
 /*
 =================
@@ -383,97 +293,35 @@
 void S_ClearSoundBuffer( void )
 {
 	if( si.ClearSoundBuffer ) {
-		si.ClearSoundBuffer( );
+		si.ClearSoundBuffer();
 	}
 }
 
+
 /*
 =================
 S_SoundInfo
 =================
 */
-void S_SoundInfo( void )
+static void S_SoundInfo( void )
 {
 	if( si.SoundInfo ) {
-		si.SoundInfo( );
+		si.SoundInfo();
 	}
 }
 
+
 /*
 =================
 S_SoundList
 =================
 */
-void S_SoundList( void )
+static void S_SoundList( void )
 {
 	if( si.SoundList ) {
-		si.SoundList( );
-	}
-}
-
-
-#ifdef USE_VOIP
-/*
-=================
-S_StartCapture
-=================
-*/
-void S_StartCapture( void )
-{
-	if( si.StartCapture ) {
-		si.StartCapture( );
-	}
-}
-
-/*
-=================
-S_AvailableCaptureSamples
-=================
-*/
-int S_AvailableCaptureSamples( void )
-{
-	if( si.AvailableCaptureSamples ) {
-		return si.AvailableCaptureSamples( );
-	}
-	return 0;
-}
-
-/*
-=================
-S_Capture
-=================
-*/
-void S_Capture( int samples, byte *data )
-{
-	if( si.Capture ) {
-		si.Capture( samples, data );
-	}
-}
-
-/*
-=================
-S_StopCapture
-=================
-*/
-void S_StopCapture( void )
-{
-	if( si.StopCapture ) {
-		si.StopCapture( );
-	}
-}
-
-/*
-=================
-S_MasterGain
-=================
-*/
-void S_MasterGain( float gain )
-{
-	if( si.MasterGain ) {
-		si.MasterGain( gain );
+		si.SoundList();
 	}
 }
-#endif
 
 //=============================================================================
 
@@ -482,9 +330,9 @@
 S_Play_f
 =================
 */
-void S_Play_f( void ) {
+static void S_Play_f( void ) {
 	int 		i;
-	int                     c;
+	int			c;
 	sfxHandle_t	h;
 
 	if( !si.RegisterSound || !si.StartLocalSound ) {
@@ -499,7 +347,7 @@
 	}
 
 	for( i = 1; i < c; i++ ) {
-		h = S_RegisterSound(Cmd_Argv(i), qfalse);
+		h = si.RegisterSound( Cmd_Argv(i), qfalse );
 
 		if( h ) {
 			si.StartLocalSound( h, CHAN_LOCAL_SOUND );
@@ -507,12 +355,13 @@
 	}
 }
 
+
 /*
 =================
 S_Music_f
 =================
 */
-void S_Music_f( void ) {
+static void S_Music_f( void ) {
 	int		c;
 
 	if( !si.StartBackgroundTrack ) {
@@ -532,14 +381,15 @@
 
 }
 
+
 /*
 =================
-S_Music_f
+S_StopMusic_f
 =================
 */
-void S_StopMusic_f( void )
+static void S_StopMusic_f( void )
 {
-	if(!si.StopBackgroundTrack)
+	if ( !si.StopBackgroundTrack )
 		return;
 
 	si.StopBackgroundTrack();
@@ -561,28 +411,28 @@
 	Com_Printf( "------ Initializing Sound ------\n" );
 
 	s_volume = Cvar_Get( "s_volume", "0.8", CVAR_ARCHIVE );
-	s_musicVolume = Cvar_Get( "s_musicvolume", "0", CVAR_ARCHIVE );
-	s_muted = Cvar_Get("s_muted", "0", CVAR_ROM);
-	s_doppler = Cvar_Get( "s_doppler", "1", CVAR_ARCHIVE );
-	s_backend = Cvar_Get( "s_backend", "base", CVAR_ROM );
-	s_muteWhenMinimized = Cvar_Get( "s_muteWhenMinimized", "0", CVAR_ARCHIVE );
-	s_muteWhenUnfocused = Cvar_Get( "s_muteWhenUnfocused", "0", CVAR_ARCHIVE );
-	s_announcerVolume = Cvar_Get("s_announcerVolume", "1.0", CVAR_ARCHIVE);
-	s_killBeepVolume = Cvar_Get("s_killBeepVolume", "1.0", CVAR_ARCHIVE);
-	s_useTimescale = Cvar_Get("s_useTimescale", "0", CVAR_ARCHIVE);
-	s_forceScale = Cvar_Get("s_forceScale", "0.0", CVAR_ARCHIVE);
-	s_showMiss = Cvar_Get("s_showMiss", "0", CVAR_ARCHIVE);
-	s_maxSoundRepeatTime = Cvar_Get("s_maxSoundRepeatTime", "0", CVAR_ARCHIVE);
-	s_maxSoundInstances = Cvar_Get("s_maxSoundInstances", "96", CVAR_ARCHIVE);
-	s_qlAttenuate = Cvar_Get("s_qlAttenuate", "1", CVAR_ARCHIVE);
-	s_debugMissingSounds = Cvar_Get("s_debugMissingSounds", "0", CVAR_ARCHIVE);
+	Cvar_CheckRange( s_volume, "0", "1", CV_FLOAT );
+	Cvar_SetDescription( s_volume, "Sets master volume for all game audio." );
+	s_musicVolume = Cvar_Get( "s_musicVolume", "0.25", CVAR_ARCHIVE );
+	Cvar_CheckRange( s_musicVolume, "0", "1", CV_FLOAT );
+	Cvar_SetDescription( s_musicVolume, "Sets volume for in-game music only." );
+	s_doppler = Cvar_Get( "s_doppler", "1", CVAR_ARCHIVE_ND );
+	Cvar_CheckRange( s_doppler, "0", "1", CV_INTEGER );
+	Cvar_SetDescription( s_doppler, "Enables doppler effect on moving projectiles." );
+	s_muteWhenUnfocused = Cvar_Get( "s_muteWhenUnfocused", "1", CVAR_ARCHIVE );
+	Cvar_CheckRange( s_muteWhenUnfocused, "0", "1", CV_INTEGER );
+	Cvar_SetDescription( s_muteWhenUnfocused, "Mutes all audio while game window is unfocused." );
+	s_muteWhenMinimized = Cvar_Get( "s_muteWhenMinimized", "1", CVAR_ARCHIVE );
+	Cvar_CheckRange( s_muteWhenMinimized, "0", "1", CV_INTEGER );
+	Cvar_SetDescription( s_muteWhenMinimized, "Mutes all audio while game is minimized." );
 
 	cv = Cvar_Get( "s_initsound", "1", 0 );
-	if( !cv->integer ) {
+	Cvar_SetDescription( cv, "Whether or not to startup the sound system." );
+	if ( !cv->integer ) {
 		Com_Printf( "Sound disabled.\n" );
 	} else {
 
-		S_CodecInit( );
+		S_CodecInit();
 
 		Cmd_AddCommand( "play", S_Play_f );
 		Cmd_AddCommand( "music", S_Music_f );
@@ -591,24 +441,16 @@
 		Cmd_AddCommand( "s_stop", S_StopAllSounds );
 		Cmd_AddCommand( "s_info", S_SoundInfo );
 
-		cv = Cvar_Get( "s_useOpenAL", "0", CVAR_ARCHIVE | CVAR_LATCH );
-		if( cv->integer ) {
-			//OpenAL
-			started = S_AL_Init( &si );
-			Cvar_Set( "s_backend", "OpenAL" );
-		}
-
-		if( !started ) {
+		if ( !started ) {
 			started = S_Base_Init( &si );
-			Cvar_Set( "s_backend", "base" );
 		}
 
-		if( started ) {
+		if ( started ) {
 			if( !S_ValidSoundInterface( &si ) ) {
-				Com_Error( ERR_FATAL, "Sound interface invalid." );
+				Com_Error( ERR_FATAL, "Sound interface invalid" );
 			}
 
-			S_SoundInfo( );
+			S_SoundInfo();
 			Com_Printf( "Sound initialization successful.\n" );
 		} else {
 			Com_Printf( "Sound initialization failed.\n" );
@@ -618,6 +460,7 @@
 	Com_Printf( "--------------------------------\n");
 }
 
+
 /*
 =================
 S_Shutdown
@@ -625,8 +468,12 @@
 */
 void S_Shutdown( void )
 {
-	if( si.Shutdown ) {
-		si.Shutdown( );
+	if ( si.StopAllSounds ) {
+		si.StopAllSounds();
+	}
+
+	if ( si.Shutdown ) {
+		si.Shutdown();
 	}
 
 	Com_Memset( &si, 0, sizeof( soundInterface_t ) );
@@ -638,14 +485,7 @@
 	Cmd_RemoveCommand( "s_stop" );
 	Cmd_RemoveCommand( "s_info" );
 
-	S_CodecShutdown( );
-}
-
-int S_Milliseconds (void)
-{
-	int t;
-
-	t = Com_Milliseconds();
+	S_CodecShutdown();
 
-	return t;
+	cls.soundStarted = qfalse;
 }

```

### `openarena-engine`  — sha256 `2deb33400f07...`, 11483 bytes

_Diff stat: +46 / -139 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_main.c	2026-04-16 20:02:25.178566900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_main.c	2026-04-16 22:48:25.737379400 +0100
@@ -33,15 +33,9 @@
 cvar_t *s_backend;
 cvar_t *s_muteWhenMinimized;
 cvar_t *s_muteWhenUnfocused;
-cvar_t *s_announcerVolume;
-cvar_t *s_killBeepVolume;
-cvar_t *s_useTimescale;
-cvar_t *s_forceScale;
-cvar_t *s_showMiss;
-cvar_t *s_maxSoundRepeatTime;
-cvar_t *s_maxSoundInstances;
-cvar_t *s_qlAttenuate;
-cvar_t *s_debugMissingSounds;
+
+cvar_t *s_interrupts;
+cvar_t *s_xmp_startPattern;
 
 static soundInterface_t si;
 
@@ -50,35 +44,35 @@
 S_ValidateInterface
 =================
 */
-static qboolean S_ValidSoundInterface( soundInterface_t *pSi )
+static qboolean S_ValidSoundInterface( soundInterface_t *si )
 {
-	if( !pSi->Shutdown ) return qfalse;
-	if( !pSi->StartSound ) return qfalse;
-	if( !pSi->StartLocalSound ) return qfalse;
-	if( !pSi->StartBackgroundTrack ) return qfalse;
-	if( !pSi->StopBackgroundTrack ) return qfalse;
-	if( !pSi->RawSamples ) return qfalse;
-	if( !pSi->StopAllSounds ) return qfalse;
-	if( !pSi->ClearLoopingSounds ) return qfalse;
-	if( !pSi->AddLoopingSound ) return qfalse;
-	if( !pSi->AddRealLoopingSound ) return qfalse;
-	if( !pSi->StopLoopingSound ) return qfalse;
-	if( !pSi->Respatialize ) return qfalse;
-	if( !pSi->UpdateEntityPosition ) return qfalse;
-	if( !pSi->Update ) return qfalse;
-	if( !pSi->DisableSounds ) return qfalse;
-	if( !pSi->BeginRegistration ) return qfalse;
-	if( !pSi->RegisterSound ) return qfalse;
-	if( !pSi->ClearSoundBuffer ) return qfalse;
-	if( !pSi->SoundInfo ) return qfalse;
-	if( !pSi->SoundList ) return qfalse;
+	if( !si->Shutdown ) return qfalse;
+	if( !si->StartSound ) return qfalse;
+	if( !si->StartLocalSound ) return qfalse;
+	if( !si->StartBackgroundTrack ) return qfalse;
+	if( !si->StopBackgroundTrack ) return qfalse;
+	if( !si->RawSamples ) return qfalse;
+	if( !si->StopAllSounds ) return qfalse;
+	if( !si->ClearLoopingSounds ) return qfalse;
+	if( !si->AddLoopingSound ) return qfalse;
+	if( !si->AddRealLoopingSound ) return qfalse;
+	if( !si->StopLoopingSound ) return qfalse;
+	if( !si->Respatialize ) return qfalse;
+	if( !si->UpdateEntityPosition ) return qfalse;
+	if( !si->Update ) return qfalse;
+	if( !si->DisableSounds ) return qfalse;
+	if( !si->BeginRegistration ) return qfalse;
+	if( !si->RegisterSound ) return qfalse;
+	if( !si->ClearSoundBuffer ) return qfalse;
+	if( !si->SoundInfo ) return qfalse;
+	if( !si->SoundList ) return qfalse;
 
 #ifdef USE_VOIP
-	if( !pSi->StartCapture ) return qfalse;
-	if( !pSi->AvailableCaptureSamples ) return qfalse;
-	if( !pSi->Capture ) return qfalse;
-	if( !pSi->StopCapture ) return qfalse;
-	if( !pSi->MasterGain ) return qfalse;
+	if( !si->StartCapture ) return qfalse;
+	if( !si->AvailableCaptureSamples ) return qfalse;
+	if( !si->Capture ) return qfalse;
+	if( !si->StopCapture ) return qfalse;
+	if( !si->MasterGain ) return qfalse;
 #endif
 
 	return qtrue;
@@ -89,7 +83,7 @@
 S_StartSound
 =================
 */
-void S_StartSound( const vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
+void S_StartSound( vec3_t origin, int entnum, int entchannel, sfxHandle_t sfx )
 {
 	if( si.StartSound ) {
 		si.StartSound( origin, entnum, entchannel, sfx );
@@ -115,34 +109,10 @@
 */
 void S_StartBackgroundTrack( const char *intro, const char *loop )
 {
-	// quakelive hack, all files default to ogg
-	char introx[MAX_STRING_CHARS];
-	char loopx[MAX_STRING_CHARS];
-
-	//Com_Printf("S_StartBackgroundTrack intro:'%s'  loop:'%s'\n", intro, loop);
-
-	COM_StripExtension(intro, introx, sizeof(introx));
-	COM_StripExtension(loop, loopx, sizeof(loopx));
-
-	Q_strcat(introx, sizeof(introx), ".ogg");
-	Q_strcat(loopx, sizeof(loopx), ".ogg");
-	//Com_Printf("intro:%s  loop:%s\n", introx, loopx);
-
-	if (!*intro  &&  !*loop) {
-		// request to stop background track
-		introx[0] = '\0';
-		loopx[0] = '\0';
-	}
+	// leilei - i used to have extension stripping here, but it crashed on looped tracks
 
 	if( si.StartBackgroundTrack ) {
-		//si.StartBackgroundTrack( intro, loop );
-		if (!*loop) {
-			//Com_Printf("^2using intro as loop\n");
-			si.StartBackgroundTrack(introx, introx);
-		} else {
-			//Com_Printf("^2loop and intro\n");
-			si.StartBackgroundTrack( introx, loopx );
-		}
+		si.StartBackgroundTrack( intro, loop );
 	}
 }
 
@@ -164,7 +134,7 @@
 =================
 */
 void S_RawSamples (int stream, int samples, int rate, int width, int channels,
-				   const byte *data, float volume, int entityNum)
+		   const byte *data, float volume, int entityNum)
 {
 	if(si.RawSamples)
 		si.RawSamples(stream, samples, rate, width, channels, data, volume, entityNum);
@@ -202,7 +172,6 @@
 void S_AddLoopingSound( int entityNum, const vec3_t origin,
 		const vec3_t velocity, sfxHandle_t sfx )
 {
-	//Com_Printf("adding looping sound: %d\n", sfx);
 	if( si.AddLoopingSound ) {
 		si.AddLoopingSound( entityNum, origin, velocity, sfx );
 	}
@@ -239,7 +208,7 @@
 =================
 */
 void S_Respatialize( int entityNum, const vec3_t origin,
-		const vec3_t axis[3], int inwater )
+		vec3_t axis[3], int inwater )
 {
 	if( si.Respatialize ) {
 		si.Respatialize( entityNum, origin, axis, inwater );
@@ -283,11 +252,7 @@
 			s_muted->modified = qtrue;
 		}
 	}
-
-	if (CL_VideoRecording(&afdMain)  &&  (cl_freezeDemoPauseVideoRecording->integer  &&  cl_freezeDemo->integer)) {
-		return;
-	}
-
+	
 	if( si.Update ) {
 		si.Update( );
 	}
@@ -324,57 +289,13 @@
 */
 sfxHandle_t	S_RegisterSound( const char *sample, qboolean compressed )
 {
-	sfxHandle_t s;
-	char newName[MAX_QPATH];
-	int slen;
-
-	if (sample == NULL) {
-		Com_Printf("^1%s() sample == NULL (shouldn't happen)\n", __FUNCTION__);
-		return 0;
-	}
-	//Com_Printf("S_RegisterSound %s\n", sample);
-
 	if( si.RegisterSound ) {
-		slen = strlen(sample);
-		if (slen >= 5) {
-			// first try ogg
-			//strncpy(newName, sample, MAX_QPATH);
-			COM_StripExtension(sample, newName, sizeof(newName));
-			slen = strlen(newName);
-			s = 0;
-			if (slen + 5 >= sizeof(newName)) {
-				Com_Printf("^3%s() couldn't add ogg extension to '%s', name is too long\n", __FUNCTION__, sample);
-				s = 0;
-			} else {
-				newName[slen + 0] = '.';
-				newName[slen + 1] = 'o';
-				newName[slen + 2] = 'g';
-				newName[slen + 3] = 'g';
-				newName[slen + 4] = '\0';
-				s = si.RegisterSound(newName, compressed);
-			}
-			if (!s) {
-				s = si.RegisterSound(sample, compressed);
-			}
-			if (!s) {
-				//Com_Printf("^1S_RegisterSound() couldn't open '%s' or '%s'\n", newName, sample);
-				Com_Printf("^1S_RegisterSound() couldn't open '%s'\n", sample);
-			}
-			return s;
-		} else {
-			Com_Printf("^3FIXME S_RegisterSound() '%s' name is too short\n", sample);
-			return si.RegisterSound( sample, compressed );
-		}
+		return si.RegisterSound( sample, compressed );
 	} else {
 		return 0;
 	}
 }
 
-void S_PrintSfxFilename (sfxHandle_t sfx)
-{
-	si.PrintSfxFilename(sfx);
-}
-
 /*
 =================
 S_ClearSoundBuffer
@@ -484,7 +405,7 @@
 */
 void S_Play_f( void ) {
 	int 		i;
-	int                     c;
+	int			c;
 	sfxHandle_t	h;
 
 	if( !si.RegisterSound || !si.StartLocalSound ) {
@@ -499,7 +420,7 @@
 	}
 
 	for( i = 1; i < c; i++ ) {
-		h = S_RegisterSound(Cmd_Argv(i), qfalse);
+		h = si.RegisterSound( Cmd_Argv(i), qfalse );
 
 		if( h ) {
 			si.StartLocalSound( h, CHAN_LOCAL_SOUND );
@@ -521,6 +442,8 @@
 
 	c = Cmd_Argc();
 
+	// leilei - strip the extension so we can play other formats if our song's not there.
+
 	if ( c == 2 ) {
 		si.StartBackgroundTrack( Cmd_Argv(1), NULL );
 	} else if ( c == 3 ) {
@@ -561,22 +484,14 @@
 	Com_Printf( "------ Initializing Sound ------\n" );
 
 	s_volume = Cvar_Get( "s_volume", "0.8", CVAR_ARCHIVE );
-	s_musicVolume = Cvar_Get( "s_musicvolume", "0", CVAR_ARCHIVE );
+	s_musicVolume = Cvar_Get( "s_musicvolume", "0.25", CVAR_ARCHIVE );
 	s_muted = Cvar_Get("s_muted", "0", CVAR_ROM);
 	s_doppler = Cvar_Get( "s_doppler", "1", CVAR_ARCHIVE );
-	s_backend = Cvar_Get( "s_backend", "base", CVAR_ROM );
+	s_backend = Cvar_Get( "s_backend", "", CVAR_ROM );
+	s_interrupts = Cvar_Get( "s_interrupts", "0", CVAR_ARCHIVE ); // leilei - pre-1.25 sound behavior
 	s_muteWhenMinimized = Cvar_Get( "s_muteWhenMinimized", "0", CVAR_ARCHIVE );
 	s_muteWhenUnfocused = Cvar_Get( "s_muteWhenUnfocused", "0", CVAR_ARCHIVE );
-	s_announcerVolume = Cvar_Get("s_announcerVolume", "1.0", CVAR_ARCHIVE);
-	s_killBeepVolume = Cvar_Get("s_killBeepVolume", "1.0", CVAR_ARCHIVE);
-	s_useTimescale = Cvar_Get("s_useTimescale", "0", CVAR_ARCHIVE);
-	s_forceScale = Cvar_Get("s_forceScale", "0.0", CVAR_ARCHIVE);
-	s_showMiss = Cvar_Get("s_showMiss", "0", CVAR_ARCHIVE);
-	s_maxSoundRepeatTime = Cvar_Get("s_maxSoundRepeatTime", "0", CVAR_ARCHIVE);
-	s_maxSoundInstances = Cvar_Get("s_maxSoundInstances", "96", CVAR_ARCHIVE);
-	s_qlAttenuate = Cvar_Get("s_qlAttenuate", "1", CVAR_ARCHIVE);
-	s_debugMissingSounds = Cvar_Get("s_debugMissingSounds", "0", CVAR_ARCHIVE);
-
+	s_xmp_startPattern = Cvar_Get( "s_xmp_startPattern", "0", CVAR_CHEAT ); // leilei - starting pattern for song
 	cv = Cvar_Get( "s_initsound", "1", 0 );
 	if( !cv->integer ) {
 		Com_Printf( "Sound disabled.\n" );
@@ -591,7 +506,7 @@
 		Cmd_AddCommand( "s_stop", S_StopAllSounds );
 		Cmd_AddCommand( "s_info", S_SoundInfo );
 
-		cv = Cvar_Get( "s_useOpenAL", "0", CVAR_ARCHIVE | CVAR_LATCH );
+		cv = Cvar_Get( "s_useOpenAL", "1", CVAR_ARCHIVE );
 		if( cv->integer ) {
 			//OpenAL
 			started = S_AL_Init( &si );
@@ -605,7 +520,7 @@
 
 		if( started ) {
 			if( !S_ValidSoundInterface( &si ) ) {
-				Com_Error( ERR_FATAL, "Sound interface invalid." );
+				Com_Error( ERR_FATAL, "Sound interface invalid" );
 			}
 
 			S_SoundInfo( );
@@ -641,11 +556,3 @@
 	S_CodecShutdown( );
 }
 
-int S_Milliseconds (void)
-{
-	int t;
-
-	t = Com_Milliseconds();
-
-	return t;
-}

```
