# Diff: `code/client/client.h`
**Canonical:** `wolfcamql-src` (sha256 `55d14d8c3f7a...`, 26356 bytes)

## Variants

### `quake3-source`  — sha256 `b30e007736ae...`, 16524 bytes

_Diff stat: +51 / -376 lines_

_(full diff is 20823 bytes — see files directly)_

### `ioquake3`  — sha256 `42f81243e7c0...`, 20225 bytes

_Diff stat: +45 / -246 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\client.h	2026-04-16 20:02:25.174216300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\client.h	2026-04-16 20:02:21.529570100 +0100
@@ -1,5 +1,3 @@
-#ifndef client_h_included
-#define client_h_included
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -27,25 +25,19 @@
 #include "../qcommon/qcommon.h"
 #include "../renderercommon/tr_public.h"
 #include "../ui/ui_public.h"
-//#include "keys.h"
+#include "keys.h"
 #include "snd_public.h"
 #include "../cgame/cg_public.h"
 #include "../game/bg_public.h"
-#include "cl_avi.h"
-#include "../sys/sys_local.h"
 
 #ifdef USE_HTTP
 #include "cl_http.h"
 #endif /* USE_HTTP */
 
 #ifdef USE_VOIP
-#include "speex/speex.h"
-#include "speex/speex_preprocess.h"
 #include <opus.h>
 #endif
 
-#define MAX_DEMO_FILES 64
-
 // file full of random crap that gets used to create cl_guid
 #define QKEY_FILE "qkey"
 #define QKEY_SIZE 2048
@@ -94,7 +86,7 @@
 // the parseEntities array must be large enough to hold PACKET_BACKUP frames of
 // entities, so that when a delta compressed message arives from the server
 // it can be un-deltad from the original 
-#define  MAX_PARSE_ENTITIES  ( PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES )
+#define	MAX_PARSE_ENTITIES	( PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES )
 
 extern int g_console_field_width;
 
@@ -144,12 +136,11 @@
 	int			serverId;			// included in each client message so the server
 												// can tell if it is for a prior map_restart
 	// big stuff at end of structure so most offsets are 15 bits or less
-	clSnapshot_t	snapshots[PACKET_BACKUP][MAX_DEMO_FILES];
+	clSnapshot_t	snapshots[PACKET_BACKUP];
 
 	entityState_t	entityBaselines[MAX_GENTITIES];	// for delta compression when not in previous frame
 
 	entityState_t	parseEntities[MAX_PARSE_ENTITIES];
-	qboolean draw;
 } clientActive_t;
 
 extern	clientActive_t		cl;
@@ -170,7 +161,7 @@
 
 typedef struct {
 
-	connstate_t	state;						// connection status
+	connstate_t	state;				// connection status
 
 	int			clientNum;
 	int			lastPacketSentTime;			// for retransmits during connection
@@ -226,16 +217,9 @@
 	qboolean	spDemoRecording;
 	qboolean	demorecording;
 	qboolean	demoplaying;
-	int demoPlayBegin;
-	const char *demoWorkshopsString;
-	char currentWorkshop[MAX_STRING_CHARS];
-
-	popenData_t *wfp;
-
 	qboolean	demowaiting;	// don't record until a non-delta message is received
 	qboolean	firstDemoFrameSkipped;
-	fileHandle_t demoReadFile;
-	fileHandle_t	demoWriteFile;
+	fileHandle_t	demofile;
 
 	int			timeDemoFrames;		// counter of rendered frames
 	int			timeDemoStart;		// cls.realtime before first frame
@@ -244,20 +228,16 @@
 	int			timeDemoMinDuration;	// minimum frame duration
 	int			timeDemoMaxDuration;	// maximum frame duration
 	unsigned char	timeDemoDurations[ MAX_TIMEDEMO_DURATIONS ];	// log of frame durations
-	int	cgameTime;
-	int realProtocol;
+
+	float		aviVideoFrameRemainder;
+	float		aviSoundFrameRemainder;
 
 #ifdef USE_VOIP
 	qboolean voipEnabled;
-	qboolean speexInitialized;
-	int speexFrameSize;
-	int speexSampleRate;
 	qboolean voipCodecInitialized;
 
 	// incoming data...
 	// !!! FIXME: convert from parallel arrays to array of a struct.
-	SpeexBits speexDecoderBits[MAX_CLIENTS];
-	void *speexDecoder[MAX_CLIENTS];
 	OpusDecoder *opusDecoder[MAX_CLIENTS];
 	byte voipIncomingGeneration[MAX_CLIENTS];
 	int voipIncomingSequence[MAX_CLIENTS];
@@ -270,9 +250,6 @@
 	// then we are sending to clientnum i.
 	uint8_t voipTargets[(MAX_CLIENTS + 7) / 8];
 	uint8_t voipFlags;
-	SpeexPreprocessState *speexPreprocessor;
-	SpeexBits speexEncoderBits;
-	void *speexEncoder;
 	OpusEncoder *opusEncoder;
 	int voipOutgoingDataSize;
 	int voipOutgoingDataFrames;
@@ -280,9 +257,6 @@
 	byte voipOutgoingGeneration;
 	byte voipOutgoingData[1024];
 	float voipPower;
-
-	float audioPower;
-	float audioDecibels;
 #endif
 
 #ifdef LEGACY_PROTOCOL
@@ -326,8 +300,8 @@
 	int			ping;
 	qboolean	visible;
 	int			punkbuster;
-	int                     g_humanplayers;
-	int                     g_needpass;
+	int			g_humanplayers;
+	int			g_needpass;
 } serverInfo_t;
 
 typedef struct {
@@ -341,15 +315,10 @@
 	qboolean	cgameStarted;
 
 	int			framecount;
-	int			frametime;			// msec since last frame, affected by timescale and artificial video recording frame times, can be 0 if demo is paused
-
-	// note: these are not 'real' since they, like frametime above, will be
-	// affected by timescale and also artificial frame times used for video
-	// recording
-	int			realtime;			// doesn't advance if demo is paused, value can be reset with demo seeking, does advance for ingame pause
-	int			realFrametime;		// ignoring both ingame pause and demo pause, so console always works
+	int			frametime;			// msec since last frame
 
-	int			scaledtime;  		// same as realtime above but doesn't get reset with demo seeking, this always advances or stays the same, used for renderer shaders and cinematics
+	int			realtime;			// ignores pause
+	int			realFrametime;		// ignoring pause, so console always works
 
 	int			numlocalservers;
 	serverInfo_t	localServers[MAX_OTHER_SERVERS];
@@ -379,139 +348,12 @@
 	qhandle_t	charSetShader;
 	qhandle_t	whiteShader;
 	qhandle_t	consoleShader;
-	fontInfo_t consoleFont;
 } clientStatic_t;
 
 extern	clientStatic_t		cls;
 
-extern char            cl_oldGame[MAX_QPATH];
-extern qboolean        cl_oldGameSet;
-
-typedef struct {
-	qboolean valid;
-	int num;
-	qhandle_t f;
-	int serverTime;
-	clSnapshot_t snap;
-	int serverMessageSequence;
-} demoFile_t;
-
-#define MAX_PLAYER_INFO 256
-
-typedef struct {
-	char modelName[MAX_QPATH];
-} playerInfo_t;
-
-#define MAX_TEAM_SWITCHES 512
-
-typedef struct {
-	int clientNum;
-	int oldTeam;
-	int newTeam;
-	int serverTime;
-} teamSwitch_t;
-
-typedef struct {
-	int numSnaps;
-	int lastServerTime;
-	int firstServerTime;
-	int gameStartTime;
-	int gameEndTime;
-	int serverFrameTime;
-
-	double wantedTime;
-	int snapCount;
-
-	int demoPos;
-	int snapsInDemo;
-	qboolean gotFirstSnap;
-	qboolean skipSnap;
-
-	qboolean endOfDemo;
-	qboolean testParse;
-
-	// is it protocol 43 - 48
-	qboolean checkedForOlderUncompressedDemo;
-	qboolean olderUncompressedDemo;
-	int olderUncompressedDemoProtocol;
-
-	demoObit_t obit[MAX_DEMO_OBITS];
-	int obitNum;
-	//qboolean clientAlive[MAX_CLIENTS];
-	qboolean offlineDemo;
-	qboolean hasWarmup;
-
-	int oldLegsAnim[MAX_GENTITIES];
-	int oldTorsoAnim[MAX_GENTITIES];
-	int oldLegsAnimTime[MAX_GENTITIES];
-	int oldTorsoAnimTime[MAX_GENTITIES];
-
-	int oldPsLegsAnim;
-	int oldPsTorsoAnim;
-	int oldPsLegsAnimTime;
-	int oldPsTorsoAnimTime;
-	qboolean seeking;
-
-	int firstNonDeltaMessageNumWritten;
-
-	itemPickup_t itemPickups[MAX_ITEM_PICKUPS];
-	int numItemPickups;
-
-	int entityPreviousEvent[MAX_GENTITIES];
-	//qboolean entityInSnap[MAX_GENTITIES];
-	qboolean entityInOldSnap[MAX_GENTITIES];
-	entityState_t *oldEs[MAX_GENTITIES];
-	int entitySnapShotTime[MAX_GENTITIES];
-	int protocol;
-	qboolean cpma;
-	int cpmaLastTs;
-	int cpmaLastTd;
-	int cpmaLastTe;
-
-	timeOut_t timeOuts[MAX_TIMEOUTS];
-	int numTimeouts;
-
-	demoFile_t demoFiles[MAX_DEMO_FILES];
-	int numDemoFiles;
-
-	int roundStarts[MAX_DEMO_ROUND_STARTS];
-	int numRoundStarts;
-
-	int pov;
-
-	playerInfo_t playerInfo[MAX_PLAYER_INFO];
-	int numPlayerInfo;
-
-	// keeps track of current team
-	int clientTeam[MAX_CLIENTS];
-
-	teamSwitch_t teamSwitches[MAX_TEAM_SWITCHES];
-	int numTeamSwitches;
-
-	int gametype;
-
-	qboolean streaming;
-	qboolean waitingForStream;
-	int streamWaitTime;
-} demoInfo_t;
-
-extern demoInfo_t di;
-
-typedef struct {
-    qboolean valid;
-    int seekPoint;
-	int demoSeekPoints[MAX_DEMO_FILES];
-    clientActive_t cl;
-    clientConnection_t clc;
-    clientStatic_t cls;
-    int numSnaps;
-} rewindBackups_t;
-
-//FIXME can make dynamic to improve seek performance
-#define MAX_REWIND_BACKUPS 12   // 1000 ~ 175 megabytes, sizeof(rewindBackups_t) is 1.753348 mb
-
-extern rewindBackups_t *rewindBackups;
-extern int maxRewindBackups;
+extern	char		cl_oldGame[MAX_QPATH];
+extern	qboolean	cl_oldGameSet;
 
 //=============================================================================
 
@@ -519,6 +361,7 @@
 extern	vm_t			*uivm;	// interface to ui dll or vm
 extern	refexport_t		re;		// interface to refresh .dll
 
+
 //
 // cvars
 //
@@ -553,31 +396,20 @@
 extern	cvar_t	*m_side;
 extern	cvar_t	*m_filter;
 
-extern  cvar_t  *j_pitch;
-extern  cvar_t  *j_yaw;
-extern  cvar_t  *j_forward;
-extern  cvar_t  *j_side;
-extern  cvar_t  *j_up;
-extern  cvar_t  *j_pitch_axis;
-extern  cvar_t  *j_yaw_axis;
-extern  cvar_t  *j_forward_axis;
-extern  cvar_t  *j_side_axis;
-extern  cvar_t  *j_up_axis;
+extern	cvar_t	*j_pitch;
+extern	cvar_t	*j_yaw;
+extern	cvar_t	*j_forward;
+extern	cvar_t	*j_side;
+extern	cvar_t	*j_up;
+extern	cvar_t	*j_pitch_axis;
+extern	cvar_t	*j_yaw_axis;
+extern	cvar_t	*j_forward_axis;
+extern	cvar_t	*j_side_axis;
+extern	cvar_t	*j_up_axis;
 
 extern	cvar_t	*cl_timedemo;
 extern	cvar_t	*cl_aviFrameRate;
-extern cvar_t *cl_aviFrameRateDivider;
-extern	cvar_t	*cl_aviCodec;
-extern cvar_t *cl_aviAllowLargeFiles;
-extern cvar_t *cl_aviFetchMode;
-extern cvar_t *cl_aviExtension;
-extern cvar_t *cl_aviPipeCommand;
-extern cvar_t *cl_aviPipeExtension;
-extern cvar_t *cl_aviAudioWaitForVideoFrame;
-extern cvar_t *cl_aviAudioMatchVideoLength;
-
-extern cvar_t *cl_freezeDemoPauseVideoRecording;
-extern cvar_t *cl_freezeDemoPauseMusic;
+extern	cvar_t	*cl_aviMotionJpeg;
 
 extern	cvar_t	*cl_activeAction;
 
@@ -585,7 +417,6 @@
 extern  cvar_t  *cl_downloadMethod;
 extern	cvar_t	*cl_conXOffset;
 extern	cvar_t	*cl_inGameVideo;
-extern cvar_t *cl_cinematicIgnoreSeek;
 
 extern	cvar_t	*cl_lanForcePackets;
 extern	cvar_t	*cl_autoRecordDemo;
@@ -609,32 +440,15 @@
 extern	cvar_t	*cl_voipCaptureMult;
 extern	cvar_t	*cl_voipShowMeter;
 extern	cvar_t	*cl_voip;
-extern	cvar_t	*cl_voipOverallGain;
-extern	cvar_t	*cl_voipGainOtherPlayback;
 
 // 20ms at 48k
-#define VOIP_MAX_FRAME_SAMPLES         ( 20 * 48 )
+#define VOIP_MAX_FRAME_SAMPLES		( 20 * 48 )
 
 // 3 frame is 60ms of audio, the max opus will encode at once
-#define VOIP_MAX_PACKET_FRAMES         3
-#define VOIP_MAX_PACKET_SAMPLES                ( VOIP_MAX_FRAME_SAMPLES * VOIP_MAX_PACKET_FRAMES )
-
+#define VOIP_MAX_PACKET_FRAMES		3
+#define VOIP_MAX_PACKET_SAMPLES		( VOIP_MAX_FRAME_SAMPLES * VOIP_MAX_PACKET_FRAMES )
 #endif
 
-extern cvar_t	*cl_useq3gibs;
-extern cvar_t	*cl_consoleAsChat;
-extern cvar_t *cl_numberPadInput;
-extern cvar_t *cl_maxRewindBackups;
-extern cvar_t *cl_keepDemoFileInMemory;
-extern cvar_t *cl_demoFileCheckSystem;
-extern cvar_t *cl_demoFile;
-extern cvar_t *cl_demoFileBaseName;
-extern cvar_t *cl_downloadWorkshops;
-
-extern cvar_t *cl_volumeShowMeter;
-
-extern double Overf;
-
 //=================================================
 
 //
@@ -652,7 +466,7 @@
 void CL_Snd_Restart_f (void);
 void CL_StartDemoLoop( void );
 void CL_NextDemo( void );
-void CL_ReadDemoMessage (qboolean seeking);
+void CL_ReadDemoMessage( void );
 void CL_StopRecord_f(void);
 
 void CL_InitDownloads(void);
@@ -693,6 +507,8 @@
 void CL_VerifyCode( void );
 
 float CL_KeyState (kbutton_t *key);
+int Key_StringToKeynum( char *str );
+char *Key_KeynumToString (int keynum);
 
 //
 // cl_parse.c
@@ -706,7 +522,6 @@
 
 void CL_SystemInfoChanged( void );
 void CL_ParseServerMessage( msg_t *msg );
-void CL_ParseExtraServerMessage (demoFile_t *df, msg_t *msg, qboolean justPeek);
 
 //====================================================================
 
@@ -721,19 +536,18 @@
 //
 // console
 //
-extern int g_smallchar_scaled_width;
-extern int g_smallchar_scaled_height;
+extern int g_smallchar_width;
+extern int g_smallchar_height;
 
-// not used outside of cl_console.c
-//void Con_CheckResize (void);
+void Con_DrawCharacter (int cx, int line, int num);
 
+void Con_CheckResize (void);
 void Con_Init(void);
 void Con_Shutdown(void);
 void Con_Clear_f (void);
 void Con_ToggleConsole_f (void);
 void Con_DrawNotify (void);
 void Con_ClearNotify (void);
-void Con_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 void Con_RunConsole (void);
 void Con_DrawConsole (void);
 void Con_PageUp( void );
@@ -763,19 +577,15 @@
 
 void	SCR_DrawBigString( int x, int y, const char *s, float alpha, qboolean noColorEscape );			// draws a string with embedded color control characters with fade
 void	SCR_DrawBigStringColor( int x, int y, const char *s, vec4_t color, qboolean noColorEscape );	// ignores embedded color control characters
-void	SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor, qboolean noColorEscape );
+void	SCR_DrawSmallStringExt( int x, int y, const char *string, float *setColor, qboolean forceColor, qboolean noColorEscape );
 void	SCR_DrawSmallChar( int x, int y, int ch );
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch );
-//void SCR_DrawChar (int x, int y, float size, int ch);
-void SCR_Text_Paint (float x, float y, float scale, vec4_t color, const char *text, float adjust, int limit, int style, fontInfo_t *fontOrig);
+
 
 //
 // cl_cin.c
 //
 
 void CL_PlayCinematic_f( void );
-void CL_RestartCinematic_f (void);
-void CL_ListCinematic_f (void);
 void SCR_DrawCinematic (void);
 void SCR_RunCinematic (void);
 void SCR_StopCinematic (void);
@@ -787,7 +597,6 @@
 void CIN_SetLooping (int handle, qboolean loop);
 void CIN_UploadCinematic(int handle);
 void CIN_CloseAllVideos(void);
-void CIN_SeekCinematic (double offset);
 
 //
 // cl_cgame.c
@@ -820,25 +629,15 @@
 //
 // cl_avi.c
 //
-qboolean CL_OpenAVIForWriting (aviFileData_t *afd, const char *filename, qboolean us, qboolean avi, qboolean noSoundAvi, qboolean wav, qboolean tga, qboolean jpg, qboolean png, qboolean pipe, qboolean depth, qboolean split, qboolean left);
-void CL_TakeVideoFrame (aviFileData_t *afd);
-void CL_WriteAVIVideoFrame (aviFileData_t *afd, const byte *imageBuffer, int size);
-void CL_WriteAVIAudioFrame (aviFileData_t *afd, const byte *pcmBuffer, int size);
-qboolean CL_CloseAVI (aviFileData_t *afd, qboolean us);
-//qboolean CL_VideoRecording (aviFileData_t *afd);
+qboolean CL_OpenAVIForWriting( const char *filename );
+void CL_TakeVideoFrame( void );
+void CL_WriteAVIVideoFrame( const byte *imageBuffer, int size );
+void CL_WriteAVIAudioFrame( const byte *pcmBuffer, int size );
+qboolean CL_CloseAVI( void );
+qboolean CL_VideoRecording( void );
 
 //
 // cl_main.c
 //
 void CL_WriteDemoMessage ( msg_t *msg, int headerBytes );
 
-void CL_ParseSnapshot( msg_t *msg, clSnapshot_t *sn, int serverMessageSequence, qboolean justPeek );
-void CL_ParseVoipSpeex (msg_t *msg, qboolean checkForFlags, qboolean justPeek);
-void CL_ParseVoip (msg_t *msg, qboolean ignoreData);
-qboolean CL_PeekSnapshot (int snapshotNumber, snapshot_t *snapshot);
-void CL_Pause_f (void);
-void CL_AddAt (int serverTime, const char *clockTime, const char *command);
-
-qboolean CL_GetServerCommand (int serverCommandNumber);
-
-#endif  // client_h_included

```

### `quake3e`  — sha256 `69aa1c2032f5...`, 19843 bytes

_Diff stat: +204 / -423 lines_

_(full diff is 28118 bytes — see files directly)_

### `openarena-engine`  — sha256 `807e3ef807ad...`, 20365 bytes

_Diff stat: +62 / -256 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\client.h	2026-04-16 20:02:25.174216300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\client.h	2026-04-16 22:48:25.733378900 +0100
@@ -1,5 +1,3 @@
-#ifndef client_h_included
-#define client_h_included
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -27,25 +25,20 @@
 #include "../qcommon/qcommon.h"
 #include "../renderercommon/tr_public.h"
 #include "../ui/ui_public.h"
-//#include "keys.h"
+#include "keys.h"
 #include "snd_public.h"
 #include "../cgame/cg_public.h"
 #include "../game/bg_public.h"
-#include "cl_avi.h"
-#include "../sys/sys_local.h"
 
-#ifdef USE_HTTP
-#include "cl_http.h"
-#endif /* USE_HTTP */
+#ifdef USE_CURL
+#include "cl_curl.h"
+#endif /* USE_CURL */
 
 #ifdef USE_VOIP
 #include "speex/speex.h"
 #include "speex/speex_preprocess.h"
-#include <opus.h>
 #endif
 
-#define MAX_DEMO_FILES 64
-
 // file full of random crap that gets used to create cl_guid
 #define QKEY_FILE "qkey"
 #define QKEY_SIZE 2048
@@ -94,7 +87,7 @@
 // the parseEntities array must be large enough to hold PACKET_BACKUP frames of
 // entities, so that when a delta compressed message arives from the server
 // it can be un-deltad from the original 
-#define  MAX_PARSE_ENTITIES  ( PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES )
+#define	MAX_PARSE_ENTITIES	( PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES )
 
 extern int g_console_field_width;
 
@@ -144,12 +137,11 @@
 	int			serverId;			// included in each client message so the server
 												// can tell if it is for a prior map_restart
 	// big stuff at end of structure so most offsets are 15 bits or less
-	clSnapshot_t	snapshots[PACKET_BACKUP][MAX_DEMO_FILES];
+	clSnapshot_t	snapshots[PACKET_BACKUP];
 
 	entityState_t	entityBaselines[MAX_GENTITIES];	// for delta compression when not in previous frame
 
 	entityState_t	parseEntities[MAX_PARSE_ENTITIES];
-	qboolean draw;
 } clientActive_t;
 
 extern	clientActive_t		cl;
@@ -170,7 +162,7 @@
 
 typedef struct {
 
-	connstate_t	state;						// connection status
+	connstate_t	state;				// connection status
 
 	int			clientNum;
 	int			lastPacketSentTime;			// for retransmits during connection
@@ -207,11 +199,14 @@
 	fileHandle_t download;
 	char		downloadTempName[MAX_OSPATH];
 	char		downloadName[MAX_OSPATH];
-#ifdef USE_HTTP
-	qboolean	httpUsed;
-	qboolean	disconnectedForHttpDownload;
+#ifdef USE_CURL
+	qboolean	cURLEnabled;
+	qboolean	cURLUsed;
+	qboolean	cURLDisconnected;
 	char		downloadURL[MAX_OSPATH];
-#endif /* USE_HTTP */
+	CURL		*downloadCURL;
+	CURLM		*downloadCURLM;
+#endif /* USE_CURL */
 	int		sv_allowDownload;
 	char		sv_dlURL[MAX_CVAR_VALUE_STRING];
 	int			downloadNumber;
@@ -226,16 +221,9 @@
 	qboolean	spDemoRecording;
 	qboolean	demorecording;
 	qboolean	demoplaying;
-	int demoPlayBegin;
-	const char *demoWorkshopsString;
-	char currentWorkshop[MAX_STRING_CHARS];
-
-	popenData_t *wfp;
-
 	qboolean	demowaiting;	// don't record until a non-delta message is received
 	qboolean	firstDemoFrameSkipped;
-	fileHandle_t demoReadFile;
-	fileHandle_t	demoWriteFile;
+	fileHandle_t	demofile;
 
 	int			timeDemoFrames;		// counter of rendered frames
 	int			timeDemoStart;		// cls.realtime before first frame
@@ -244,21 +232,20 @@
 	int			timeDemoMinDuration;	// minimum frame duration
 	int			timeDemoMaxDuration;	// maximum frame duration
 	unsigned char	timeDemoDurations[ MAX_TIMEDEMO_DURATIONS ];	// log of frame durations
-	int	cgameTime;
-	int realProtocol;
+
+	float		aviVideoFrameRemainder;
+	float		aviSoundFrameRemainder;
 
 #ifdef USE_VOIP
 	qboolean voipEnabled;
 	qboolean speexInitialized;
 	int speexFrameSize;
 	int speexSampleRate;
-	qboolean voipCodecInitialized;
 
 	// incoming data...
 	// !!! FIXME: convert from parallel arrays to array of a struct.
 	SpeexBits speexDecoderBits[MAX_CLIENTS];
 	void *speexDecoder[MAX_CLIENTS];
-	OpusDecoder *opusDecoder[MAX_CLIENTS];
 	byte voipIncomingGeneration[MAX_CLIENTS];
 	int voipIncomingSequence[MAX_CLIENTS];
 	float voipGain[MAX_CLIENTS];
@@ -273,16 +260,12 @@
 	SpeexPreprocessState *speexPreprocessor;
 	SpeexBits speexEncoderBits;
 	void *speexEncoder;
-	OpusEncoder *opusEncoder;
 	int voipOutgoingDataSize;
 	int voipOutgoingDataFrames;
 	int voipOutgoingSequence;
 	byte voipOutgoingGeneration;
 	byte voipOutgoingData[1024];
 	float voipPower;
-
-	float audioPower;
-	float audioDecibels;
 #endif
 
 #ifdef LEGACY_PROTOCOL
@@ -314,7 +297,7 @@
 
 typedef struct {
 	netadr_t	adr;
-	char	  	hostName[MAX_HOSTNAME_LENGTH];
+	char	  	hostName[MAX_NAME_LENGTH];
 	char	  	mapName[MAX_NAME_LENGTH];
 	char	  	game[MAX_NAME_LENGTH];
 	int			netType;
@@ -326,8 +309,8 @@
 	int			ping;
 	qboolean	visible;
 	int			punkbuster;
-	int                     g_humanplayers;
-	int                     g_needpass;
+	int			g_humanplayers;
+	int			g_needpass;
 } serverInfo_t;
 
 typedef struct {
@@ -341,15 +324,10 @@
 	qboolean	cgameStarted;
 
 	int			framecount;
-	int			frametime;			// msec since last frame, affected by timescale and artificial video recording frame times, can be 0 if demo is paused
+	int			frametime;			// msec since last frame
 
-	// note: these are not 'real' since they, like frametime above, will be
-	// affected by timescale and also artificial frame times used for video
-	// recording
-	int			realtime;			// doesn't advance if demo is paused, value can be reset with demo seeking, does advance for ingame pause
-	int			realFrametime;		// ignoring both ingame pause and demo pause, so console always works
-
-	int			scaledtime;  		// same as realtime above but doesn't get reset with demo seeking, this always advances or stays the same, used for renderer shaders and cinematics
+	int			realtime;			// ignores pause
+	int			realFrametime;		// ignoring pause, so console always works
 
 	int			numlocalservers;
 	serverInfo_t	localServers[MAX_OTHER_SERVERS];
@@ -372,146 +350,17 @@
 
 	netadr_t	authorizeServer;
 
-	netadr_t	rconAddress;
-
 	// rendering info
 	glconfig_t	glconfig;
 	qhandle_t	charSetShader;
 	qhandle_t	whiteShader;
 	qhandle_t	consoleShader;
-	fontInfo_t consoleFont;
 } clientStatic_t;
 
 extern	clientStatic_t		cls;
 
-extern char            cl_oldGame[MAX_QPATH];
-extern qboolean        cl_oldGameSet;
-
-typedef struct {
-	qboolean valid;
-	int num;
-	qhandle_t f;
-	int serverTime;
-	clSnapshot_t snap;
-	int serverMessageSequence;
-} demoFile_t;
-
-#define MAX_PLAYER_INFO 256
-
-typedef struct {
-	char modelName[MAX_QPATH];
-} playerInfo_t;
-
-#define MAX_TEAM_SWITCHES 512
-
-typedef struct {
-	int clientNum;
-	int oldTeam;
-	int newTeam;
-	int serverTime;
-} teamSwitch_t;
-
-typedef struct {
-	int numSnaps;
-	int lastServerTime;
-	int firstServerTime;
-	int gameStartTime;
-	int gameEndTime;
-	int serverFrameTime;
-
-	double wantedTime;
-	int snapCount;
-
-	int demoPos;
-	int snapsInDemo;
-	qboolean gotFirstSnap;
-	qboolean skipSnap;
-
-	qboolean endOfDemo;
-	qboolean testParse;
-
-	// is it protocol 43 - 48
-	qboolean checkedForOlderUncompressedDemo;
-	qboolean olderUncompressedDemo;
-	int olderUncompressedDemoProtocol;
-
-	demoObit_t obit[MAX_DEMO_OBITS];
-	int obitNum;
-	//qboolean clientAlive[MAX_CLIENTS];
-	qboolean offlineDemo;
-	qboolean hasWarmup;
-
-	int oldLegsAnim[MAX_GENTITIES];
-	int oldTorsoAnim[MAX_GENTITIES];
-	int oldLegsAnimTime[MAX_GENTITIES];
-	int oldTorsoAnimTime[MAX_GENTITIES];
-
-	int oldPsLegsAnim;
-	int oldPsTorsoAnim;
-	int oldPsLegsAnimTime;
-	int oldPsTorsoAnimTime;
-	qboolean seeking;
-
-	int firstNonDeltaMessageNumWritten;
-
-	itemPickup_t itemPickups[MAX_ITEM_PICKUPS];
-	int numItemPickups;
-
-	int entityPreviousEvent[MAX_GENTITIES];
-	//qboolean entityInSnap[MAX_GENTITIES];
-	qboolean entityInOldSnap[MAX_GENTITIES];
-	entityState_t *oldEs[MAX_GENTITIES];
-	int entitySnapShotTime[MAX_GENTITIES];
-	int protocol;
-	qboolean cpma;
-	int cpmaLastTs;
-	int cpmaLastTd;
-	int cpmaLastTe;
-
-	timeOut_t timeOuts[MAX_TIMEOUTS];
-	int numTimeouts;
-
-	demoFile_t demoFiles[MAX_DEMO_FILES];
-	int numDemoFiles;
-
-	int roundStarts[MAX_DEMO_ROUND_STARTS];
-	int numRoundStarts;
-
-	int pov;
-
-	playerInfo_t playerInfo[MAX_PLAYER_INFO];
-	int numPlayerInfo;
-
-	// keeps track of current team
-	int clientTeam[MAX_CLIENTS];
-
-	teamSwitch_t teamSwitches[MAX_TEAM_SWITCHES];
-	int numTeamSwitches;
-
-	int gametype;
-
-	qboolean streaming;
-	qboolean waitingForStream;
-	int streamWaitTime;
-} demoInfo_t;
-
-extern demoInfo_t di;
-
-typedef struct {
-    qboolean valid;
-    int seekPoint;
-	int demoSeekPoints[MAX_DEMO_FILES];
-    clientActive_t cl;
-    clientConnection_t clc;
-    clientStatic_t cls;
-    int numSnaps;
-} rewindBackups_t;
-
-//FIXME can make dynamic to improve seek performance
-#define MAX_REWIND_BACKUPS 12   // 1000 ~ 175 megabytes, sizeof(rewindBackups_t) is 1.753348 mb
-
-extern rewindBackups_t *rewindBackups;
-extern int maxRewindBackups;
+extern	char		cl_oldGame[MAX_QPATH];
+extern	qboolean	cl_oldGameSet;
 
 //=============================================================================
 
@@ -519,6 +368,7 @@
 extern	vm_t			*uivm;	// interface to ui dll or vm
 extern	refexport_t		re;		// interface to refresh .dll
 
+
 //
 // cvars
 //
@@ -553,31 +403,20 @@
 extern	cvar_t	*m_side;
 extern	cvar_t	*m_filter;
 
-extern  cvar_t  *j_pitch;
-extern  cvar_t  *j_yaw;
-extern  cvar_t  *j_forward;
-extern  cvar_t  *j_side;
-extern  cvar_t  *j_up;
-extern  cvar_t  *j_pitch_axis;
-extern  cvar_t  *j_yaw_axis;
-extern  cvar_t  *j_forward_axis;
-extern  cvar_t  *j_side_axis;
-extern  cvar_t  *j_up_axis;
+extern	cvar_t	*j_pitch;
+extern	cvar_t	*j_yaw;
+extern	cvar_t	*j_forward;
+extern	cvar_t	*j_side;
+extern	cvar_t	*j_up;
+extern	cvar_t	*j_pitch_axis;
+extern	cvar_t	*j_yaw_axis;
+extern	cvar_t	*j_forward_axis;
+extern	cvar_t	*j_side_axis;
+extern	cvar_t	*j_up_axis;
 
 extern	cvar_t	*cl_timedemo;
 extern	cvar_t	*cl_aviFrameRate;
-extern cvar_t *cl_aviFrameRateDivider;
-extern	cvar_t	*cl_aviCodec;
-extern cvar_t *cl_aviAllowLargeFiles;
-extern cvar_t *cl_aviFetchMode;
-extern cvar_t *cl_aviExtension;
-extern cvar_t *cl_aviPipeCommand;
-extern cvar_t *cl_aviPipeExtension;
-extern cvar_t *cl_aviAudioWaitForVideoFrame;
-extern cvar_t *cl_aviAudioMatchVideoLength;
-
-extern cvar_t *cl_freezeDemoPauseVideoRecording;
-extern cvar_t *cl_freezeDemoPauseMusic;
+extern	cvar_t	*cl_aviMotionJpeg;
 
 extern	cvar_t	*cl_activeAction;
 
@@ -585,13 +424,20 @@
 extern  cvar_t  *cl_downloadMethod;
 extern	cvar_t	*cl_conXOffset;
 extern	cvar_t	*cl_inGameVideo;
-extern cvar_t *cl_cinematicIgnoreSeek;
 
 extern	cvar_t	*cl_lanForcePackets;
 extern	cvar_t	*cl_autoRecordDemo;
 
 extern	cvar_t	*cl_consoleKeys;
 
+extern cvar_t *cl_consoleType;
+extern cvar_t *cl_consoleColor[4];
+
+extern cvar_t *cl_consoleScale;
+extern cvar_t *cl_consoleAccent;
+
+extern cvar_t *cl_consoleHeight;
+
 #ifdef USE_MUMBLE
 extern	cvar_t	*cl_useMumble;
 extern	cvar_t	*cl_mumbleScale;
@@ -609,32 +455,8 @@
 extern	cvar_t	*cl_voipCaptureMult;
 extern	cvar_t	*cl_voipShowMeter;
 extern	cvar_t	*cl_voip;
-extern	cvar_t	*cl_voipOverallGain;
-extern	cvar_t	*cl_voipGainOtherPlayback;
-
-// 20ms at 48k
-#define VOIP_MAX_FRAME_SAMPLES         ( 20 * 48 )
-
-// 3 frame is 60ms of audio, the max opus will encode at once
-#define VOIP_MAX_PACKET_FRAMES         3
-#define VOIP_MAX_PACKET_SAMPLES                ( VOIP_MAX_FRAME_SAMPLES * VOIP_MAX_PACKET_FRAMES )
-
 #endif
 
-extern cvar_t	*cl_useq3gibs;
-extern cvar_t	*cl_consoleAsChat;
-extern cvar_t *cl_numberPadInput;
-extern cvar_t *cl_maxRewindBackups;
-extern cvar_t *cl_keepDemoFileInMemory;
-extern cvar_t *cl_demoFileCheckSystem;
-extern cvar_t *cl_demoFile;
-extern cvar_t *cl_demoFileBaseName;
-extern cvar_t *cl_downloadWorkshops;
-
-extern cvar_t *cl_volumeShowMeter;
-
-extern double Overf;
-
 //=================================================
 
 //
@@ -652,7 +474,7 @@
 void CL_Snd_Restart_f (void);
 void CL_StartDemoLoop( void );
 void CL_NextDemo( void );
-void CL_ReadDemoMessage (qboolean seeking);
+void CL_ReadDemoMessage( void );
 void CL_StopRecord_f(void);
 
 void CL_InitDownloads(void);
@@ -693,6 +515,8 @@
 void CL_VerifyCode( void );
 
 float CL_KeyState (kbutton_t *key);
+int Key_StringToKeynum( char *str );
+char *Key_KeynumToString (int keynum);
 
 //
 // cl_parse.c
@@ -706,7 +530,6 @@
 
 void CL_SystemInfoChanged( void );
 void CL_ParseServerMessage( msg_t *msg );
-void CL_ParseExtraServerMessage (demoFile_t *df, msg_t *msg, qboolean justPeek);
 
 //====================================================================
 
@@ -721,19 +544,15 @@
 //
 // console
 //
-extern int g_smallchar_scaled_width;
-extern int g_smallchar_scaled_height;
-
-// not used outside of cl_console.c
-//void Con_CheckResize (void);
+void Con_DrawCharacter (int cx, int line, int num);
 
+void Con_CheckResize (void);
 void Con_Init(void);
 void Con_Shutdown(void);
 void Con_Clear_f (void);
 void Con_ToggleConsole_f (void);
 void Con_DrawNotify (void);
 void Con_ClearNotify (void);
-void Con_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 void Con_RunConsole (void);
 void Con_DrawConsole (void);
 void Con_PageUp( void );
@@ -742,6 +561,8 @@
 void Con_Bottom( void );
 void Con_Close( void );
 
+void Con_SetFrac( const float conFrac );
+
 void CL_LoadConsoleHistory( void );
 void CL_SaveConsoleHistory( void );
 
@@ -763,19 +584,15 @@
 
 void	SCR_DrawBigString( int x, int y, const char *s, float alpha, qboolean noColorEscape );			// draws a string with embedded color control characters with fade
 void	SCR_DrawBigStringColor( int x, int y, const char *s, vec4_t color, qboolean noColorEscape );	// ignores embedded color control characters
-void	SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor, qboolean noColorEscape );
-void	SCR_DrawSmallChar( int x, int y, int ch );
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch );
-//void SCR_DrawChar (int x, int y, float size, int ch);
-void SCR_Text_Paint (float x, float y, float scale, vec4_t color, const char *text, float adjust, int limit, int style, fontInfo_t *fontOrig);
+void	SCR_DrawSmallStringExt( int x, int y, const char *string, float *setColor, qboolean forceColor, qboolean noColorEscape );
+void	SCR_DrawSmallChar( int x, int y, int ch, int scalemode );
+
 
 //
 // cl_cin.c
 //
 
 void CL_PlayCinematic_f( void );
-void CL_RestartCinematic_f (void);
-void CL_ListCinematic_f (void);
 void SCR_DrawCinematic (void);
 void SCR_RunCinematic (void);
 void SCR_StopCinematic (void);
@@ -787,7 +604,6 @@
 void CIN_SetLooping (int handle, qboolean loop);
 void CIN_UploadCinematic(int handle);
 void CIN_CloseAllVideos(void);
-void CIN_SeekCinematic (double offset);
 
 //
 // cl_cgame.c
@@ -820,25 +636,15 @@
 //
 // cl_avi.c
 //
-qboolean CL_OpenAVIForWriting (aviFileData_t *afd, const char *filename, qboolean us, qboolean avi, qboolean noSoundAvi, qboolean wav, qboolean tga, qboolean jpg, qboolean png, qboolean pipe, qboolean depth, qboolean split, qboolean left);
-void CL_TakeVideoFrame (aviFileData_t *afd);
-void CL_WriteAVIVideoFrame (aviFileData_t *afd, const byte *imageBuffer, int size);
-void CL_WriteAVIAudioFrame (aviFileData_t *afd, const byte *pcmBuffer, int size);
-qboolean CL_CloseAVI (aviFileData_t *afd, qboolean us);
-//qboolean CL_VideoRecording (aviFileData_t *afd);
+qboolean CL_OpenAVIForWriting( const char *filename );
+void CL_TakeVideoFrame( void );
+void CL_WriteAVIVideoFrame( const byte *imageBuffer, int size );
+void CL_WriteAVIAudioFrame( const byte *pcmBuffer, int size );
+qboolean CL_CloseAVI( void );
+qboolean CL_VideoRecording( void );
 
 //
 // cl_main.c
 //
 void CL_WriteDemoMessage ( msg_t *msg, int headerBytes );
 
-void CL_ParseSnapshot( msg_t *msg, clSnapshot_t *sn, int serverMessageSequence, qboolean justPeek );
-void CL_ParseVoipSpeex (msg_t *msg, qboolean checkForFlags, qboolean justPeek);
-void CL_ParseVoip (msg_t *msg, qboolean ignoreData);
-qboolean CL_PeekSnapshot (int snapshotNumber, snapshot_t *snapshot);
-void CL_Pause_f (void);
-void CL_AddAt (int serverTime, const char *clockTime, const char *command);
-
-qboolean CL_GetServerCommand (int serverCommandNumber);
-
-#endif  // client_h_included

```
