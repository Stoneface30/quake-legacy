# Diff: `code/qcommon/qcommon.h`
**Canonical:** `wolfcamql-src` (sha256 `9b9b1a64937d...`, 41885 bytes)

## Variants

### `quake3-source`  — sha256 `3d46c8ba5fda...`, 33599 bytes

_Diff stat: +181 / -390 lines_

_(full diff is 36247 bytes — see files directly)_

### `ioquake3`  — sha256 `f5fe7cd88981...`, 40069 bytes

_Diff stat: +74 / -118 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qcommon.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\qcommon.h	2026-04-16 20:02:21.571105600 +0100
@@ -120,6 +120,14 @@
 #define NET_DISABLEMCAST        0x08
 
 
+#define	PACKET_BACKUP	32	// number of old messages that must be kept on client and
+							// server for delta comrpession and ping estimation
+#define	PACKET_MASK		(PACKET_BACKUP-1)
+
+#define	MAX_PACKET_USERCMDS		32		// max number of usercmd_t in a packet
+
+#define	MAX_SNAPSHOT_ENTITIES	256
+
 #define	PORT_ANY			-1
 
 #define	MAX_RELIABLE_COMMANDS	64			// max string commands buffered for restransmit
@@ -173,12 +181,12 @@
 void		NET_Sleep(int msec);
 
 
-#define	MAX_MSGLEN				(16384 * 2)		// max length of a message, which may
+#define	MAX_MSGLEN				16384		// max length of a message, which may
 											// be fragmented into multiple packets
 
-#define MAX_DOWNLOAD_WINDOW            48      // ACK window of 48 download chunks. Cannot set this higher, or clients
-                                               // will overflow the reliable commands buffer
-#define MAX_DOWNLOAD_BLKSIZE           1024    // 896 byte block chunks
+#define MAX_DOWNLOAD_WINDOW		48	// ACK window of 48 download chunks. Cannot set this higher, or clients
+						// will overflow the reliable commands buffer
+#define MAX_DOWNLOAD_BLKSIZE		1024	// 896 byte block chunks
 
 #define NETCHAN_GENCHECKSUM(challenge, sequence) ((challenge) ^ ((sequence) * (challenge)))
 
@@ -210,12 +218,12 @@
 	int			unsentLength;
 	byte		unsentBuffer[MAX_MSGLEN];
 
-	int 		challenge;
-	int			lastSentTime;
-	int			lastSentSize;
+	int			challenge;
+	int		lastSentTime;
+	int		lastSentSize;
 
 #ifdef LEGACY_PROTOCOL
-	qboolean 	compat;
+	qboolean	compat;
 #endif
 } netchan_t;
 
@@ -236,18 +244,13 @@
 ==============================================================
 */
 
-extern mapNames_t MapNames[];
-
-//#define	PROTOCOL_VERSION	73
-#define PROTOCOL_VERSION 91
-#define PROTOCOL_LEGACY_VERSION 68
+#define	PROTOCOL_VERSION	71
+#define PROTOCOL_LEGACY_VERSION	68
 // 1.31 - 67
 
 // maintain a list of compatible protocols for demo playing
 // NOTE: that stuff only works with two digits protocols
-// 43, 44, 45, 46, 47, 48, 66, 67, 68, 69, 70, 71, 73, 90, 91
-#define NUM_DEMO_PROTOCOLS 15  //FIXME err....  ARRAY_LEN()
-extern int demo_protocols[NUM_DEMO_PROTOCOLS];
+extern int demo_protocols[];
 
 #if !defined UPDATE_SERVER_NAME && !defined STANDALONE
 #define	UPDATE_SERVER_NAME	"update.quake3arena.com"
@@ -289,10 +292,9 @@
 	svc_snapshot,
 	svc_EOF,
 
-	// svc_extension follows a svc_EOF, followed by another svc_* ...
-	//  this keeps legacy clients compatible.
-	svc_extension,
-	svc_voip,     // not wrapped in USE_VOIP, so this value is reserved.
+// new commands, supported only by ioquake3 protocol but not legacy
+	svc_voipSpeex,     // not wrapped in USE_VOIP, so this value is reserved.
+	svc_voipOpus,      //
 };
 
 
@@ -307,10 +309,9 @@
 	clc_clientCommand,		// [string] message
 	clc_EOF,
 
-	// clc_extension follows a clc_EOF, followed by another clc_* ...
-	//  this keeps legacy servers compatible.
-	clc_extension,
-	clc_voip,   // not wrapped in USE_VOIP, so this value is reserved.
+// new commands, supported only by ioquake3 protocol but not legacy
+	clc_voipSpeex,   // not wrapped in USE_VOIP, so this value is reserved.
+	clc_voipOpus,    //
 };
 
 /*
@@ -435,7 +436,7 @@
 typedef void (*completionFunc_t)( char *args, int argNum );
 
 // don't allow VMs to remove system commands
-void    Cmd_RemoveCommandSafe( const char *cmd_name );
+void	Cmd_RemoveCommandSafe( const char *cmd_name );
 
 void	Cmd_CommandCompletion( void(*callback)(const char *s) );
 // callback with each valid string
@@ -511,14 +512,14 @@
 cvar_t	*Cvar_Set2(const char *var_name, const char *value, qboolean force);
 // same as Cvar_Set, but allows more control over setting of cvar
 
-void    Cvar_SetSafe( const char *var_name, const char *value );
+void	Cvar_SetSafe( const char *var_name, const char *value );
 // sometimes we set variables from an untrusted source: fail if flags & CVAR_PROTECTED
 
 void Cvar_SetLatched( const char *var_name, const char *value);
 // don't set the cvar immediately
 
 void	Cvar_SetValue( const char *var_name, float value );
-void    Cvar_SetValueSafe( const char *var_name, float value );
+void	Cvar_SetValueSafe( const char *var_name, float value );
 // expands value to a string and calls Cvar_Set/Cvar_SetSafe
 
 float	Cvar_VariableValue( const char *var_name );
@@ -564,8 +565,6 @@
 void	Cvar_Restart_f( void );
 
 void Cvar_CompleteCvarName( char *args, int argNum );
-qboolean Cvar_Exists (const char *var_name);
-cvar_t *Cvar_FindVar( const char *var_name );
 
 extern	int			cvar_modifiedFlags;
 // whenever a cvar is modifed, its flags will be OR'd into this, so
@@ -596,9 +595,9 @@
 #define	MAX_FILE_HANDLES	64
 
 #ifdef DEDICATED
-#      define Q3CONFIG_CFG CONFIG_PREFIX "_server.cfg"
+#	define Q3CONFIG_CFG CONFIG_PREFIX "_server.cfg"
 #else
-#      define Q3CONFIG_CFG CONFIG_PREFIX ".cfg"
+#	define Q3CONFIG_CFG CONFIG_PREFIX ".cfg"
 #endif
 
 qboolean FS_Initialized( void );
@@ -618,15 +617,13 @@
 void	FS_FreeFileList( char **list );
 
 qboolean FS_FileExists_HomeData( const char *file );
-const char *FS_FindSystemFile (const char *file);
-qboolean FS_VirtualFileExists (const char *file);
 
 qboolean FS_CreatePath (const char *OSPath);
 
 int FS_FindVM(void **startSearch, char *found, int foundlen, const char *name, int enableDll);
 
-char   *FS_BaseDir_BuildOSPath( const char *base, const char *qpath );
-char   *FS_BuildOSPath( const char *base, const char *game, const char *qpath );
+char	*FS_BaseDir_BuildOSPath( const char *base, const char *qpath );
+char	*FS_BuildOSPath( const char *base, const char *game, const char *qpath );
 qboolean FS_CompareZipChecksum(const char *zipfile);
 
 int		FS_LoadStack( void );
@@ -634,12 +631,12 @@
 int		FS_GetFileList(  const char *path, const char *extension, char *listbuf, int bufsize );
 int		FS_GetModList(  char *listbuf, int bufsize );
 
-void   FS_GetModDescription( const char *modDir, char *description, int descriptionLen );
+void	FS_GetModDescription( const char *modDir, char *description, int descriptionLen );
 
-fileHandle_t   FS_FOpenFileWrite_HomeConfig( const char *filename );
-fileHandle_t   FS_FOpenFileWrite_HomeData( const char *filename );
-fileHandle_t   FS_FOpenFileWrite_HomeState( const char *filename );
-fileHandle_t   FS_FOpenFileAppend_HomeData( const char *filename );
+fileHandle_t	FS_FOpenFileWrite_HomeConfig( const char *filename );
+fileHandle_t	FS_FOpenFileWrite_HomeData( const char *filename );
+fileHandle_t	FS_FOpenFileWrite_HomeState( const char *filename );
+fileHandle_t	FS_FOpenFileAppend_HomeData( const char *filename );
 fileHandle_t	FS_FCreateOpenPipeFile( const char *filename );
 // will properly create any needed paths and deal with seperater character issues
 
@@ -648,7 +645,6 @@
 fileHandle_t FS_BaseDir_FOpenFileWrite_HomeState( const char *filename );
 long		FS_BaseDir_FOpenFileRead( const char *filename, fileHandle_t *fp );
 void	FS_BaseDir_Rename_HomeData( const char *from, const char *to, qboolean safe );
-void FS_FOpenSysFileRead (const char *filename, fileHandle_t *file);
 long		FS_FOpenFileRead( const char *qpath, fileHandle_t *file, qboolean uniqueFILE );
 // if uniqueFILE is true, then a new FILE will be fopened even if the file
 // is found in an already open pak file.  If uniqueFILE is false, you must call
@@ -656,8 +652,6 @@
 // It is generally safe to always set uniqueFILE to true, because the majority of
 // file IO goes through FS_ReadFile, which Does The Right Thing already.
 
-qboolean FS_FileLoadInMemory (qhandle_t f);
-
 int		FS_FileIsInPAK(const char *filename, int *pChecksum );
 // returns 1 if a file is in the PAK file, otherwise -1
 
@@ -669,8 +663,8 @@
 void	FS_FCloseFile( fileHandle_t f );
 // note: you can't just fclose from another DLL, due to MS libc issues
 
-long   FS_ReadFileDir(const char *qpath, void *searchPath, qboolean unpure, void **buffer);
-long   FS_ReadFile(const char *qpath, void **buffer);
+long	FS_ReadFileDir(const char *qpath, void *searchPath, qboolean unpure, void **buffer);
+long	FS_ReadFile(const char *qpath, void **buffer);
 // returns the length of the file
 // a null buffer will just return the file length without loading
 // as a quick check for existence. -1 length == not present
@@ -704,8 +698,6 @@
 int		FS_Seek( fileHandle_t f, long offset, int origin );
 // seek on a file
 
-FILE *FS_FileForHandle( fileHandle_t f );
-
 qboolean FS_FilenameCompare( const char *s1, const char *s2 );
 
 const char *FS_LoadedPakNames( void );
@@ -745,13 +737,6 @@
 const char *FS_GetCurrentGameDir(void);
 qboolean FS_Which(const char *filename, void *searchPath);
 
-void FS_SortFileList(char **filelist, int numfiles);
-void FS_ReplaceSeparators (char *path);
-char *FS_BaseName (const char *path);
-
-fileHandle_t FS_PipeOpen (const char *cmd);
-int FS_PipeClose (fileHandle_t f);
-
 /*
 ==============================================================
 
@@ -760,40 +745,23 @@
 ==============================================================
 */
 
-typedef struct {
-	int codePoint;
-	char utf8Bytes[4];
-	int numUtf8Bytes;
-} fieldChar_t;
-
 #define	MAX_EDIT_LINE	256
 typedef struct {
 	int		cursor;
 	int		scroll;
 	int		widthInChars;
-	//char	buffer[MAX_EDIT_LINE];
-	fieldChar_t	xbuffer[MAX_EDIT_LINE];
+	char	buffer[MAX_EDIT_LINE];
 } field_t;
 
 void Field_Clear( field_t *edit );
 void Field_AutoComplete( field_t *edit );
 void Field_CompleteKeyname( void );
-void Field_CompleteFilename (const char *dir, const char *ext,
+void Field_CompleteFilename( const char *dir, const char *ext,
 		char *filter, qboolean stripExt,
-		qboolean allowNonPureFilesOnDisk, qboolean *foundMatch);
-void Field_CompleteCommand( char *cmd, qboolean doCommands, qboolean doCvars );
+		qboolean allowNonPureFilesOnDisk );
+void Field_CompleteCommand( char *cmd,
+		qboolean doCommands, qboolean doCvars );
 void Field_CompletePlayerName( const char **names, int count );
-size_t Field_Strlen (const field_t *field);
-
-// char *p must be able to hold at least MAX_EDIT_LINE * 4 (UTF-8 bytes) chars
-// len == 0 is full string
-void Field_ToStr (char *p, const field_t *field, int skip, int len);
-
-// len == 0 is full string
-char *Field_AsStr (const field_t *field, int skip, int len);
-void Field_Insert (field_t *field, int pos, int codePoint);
-
-void Field_SetBuffer (field_t *field, const char *p, int len, int pos);
 
 /*
 ==============================================================
@@ -821,18 +789,17 @@
 } cpuFeatures_t;
 
 // centralized and cleaned, that's the max string you can send to a Com_Printf / Com_DPrintf (above gets truncated)
-//#define	MAXPRINTMSG	(4096 * 2)
+#define	MAXPRINTMSG	4096
 
 
 typedef enum {
 	// SE_NONE must be zero
 	SE_NONE = 0,		// evTime is still valid
-	SE_KEY,				// evValue is a key code, evValue2 is the down flag
-	SE_CHAR,			// evValue is an ascii char
-	SE_MOUSE,			// evValue and evValue2 are relative signed x / y moves
-	SE_MOUSE_INACTIVE,	// evValue and evValue2 are window x and y coordinates
+	SE_KEY,			// evValue is a key code, evValue2 is the down flag
+	SE_CHAR,		// evValue is an ascii char
+	SE_MOUSE,		// evValue and evValue2 are relative signed x / y moves
 	SE_JOYSTICK_AXIS,	// evValue is an axis number and evValue2 is the current state (-127 to 127)
-	SE_CONSOLE			// evPtr is a char*
+	SE_CONSOLE		// evPtr is a char*
 } sysEventType_t;
 
 typedef struct {
@@ -863,7 +830,7 @@
 char		*Com_MD5File(const char *filename, int length, const char *prefix, int prefix_len);
 int			Com_Filter(char *filter, char *name, int casesensitive);
 int			Com_FilterPath(char *filter, char *name, int casesensitive);
-int			Com_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int			Com_RealTime(qtime_t *qtime);
 qboolean	Com_SafeMode( void );
 void		Com_RunAndTimeServerPacket(netadr_t *evFrom, msg_t *buf);
 
@@ -874,16 +841,15 @@
 // if match is NULL, all set commands will be executed, otherwise
 // only a set with the exact name.  Only used during startup.
 
-qboolean               Com_PlayerNameToFieldString( char *str, int length, const char *name );
-qboolean               Com_FieldStringToPlayerName( char *name, int length, const char *rawname );
-int QDECL      Com_strCompare( const void *a, const void *b );
+qboolean		Com_PlayerNameToFieldString( char *str, int length, const char *name );
+qboolean		Com_FieldStringToPlayerName( char *name, int length, const char *rawname );
+int QDECL	Com_strCompare( const void *a, const void *b );
 
 
 extern	cvar_t	*com_developer;
 extern	cvar_t	*com_dedicated;
 extern	cvar_t	*com_speeds;
 extern	cvar_t	*com_timescale;
-extern cvar_t *com_timescaleSafe;
 extern	cvar_t	*com_sv_running;
 extern	cvar_t	*com_cl_running;
 extern	cvar_t	*com_version;
@@ -897,9 +863,9 @@
 extern	cvar_t	*com_minimized;
 extern	cvar_t	*com_maxfpsMinimized;
 extern	cvar_t	*com_altivec;
-extern 	cvar_t 	*com_standalone;
+extern	cvar_t	*com_standalone;
 extern	cvar_t	*com_basegame;
-extern	cvar_t 	*com_homepath;
+extern	cvar_t	*com_homepath;
 
 // both client and server must agree to pause
 extern	cvar_t	*cl_paused;
@@ -909,16 +875,13 @@
 extern	cvar_t	*sv_packetdelay;
 
 extern	cvar_t	*com_gamename;
-extern  cvar_t  *com_protocol;
+extern	cvar_t	*com_protocol;
 #ifdef LEGACY_PROTOCOL
-extern cvar_t	*com_legacyprotocol;
+extern	cvar_t	*com_legacyprotocol;
+#endif
+#ifndef DEDICATED
+extern  cvar_t  *con_autochat;
 #endif
-extern cvar_t *com_autoWriteConfig;
-extern qboolean com_writeConfig;
-
-extern cvar_t *com_execVerbose;
-extern cvar_t *com_qlColors;
-extern cvar_t *com_brokenDemo;
 
 // com_speeds times
 extern	int		time_game;
@@ -933,8 +896,6 @@
 extern	fileHandle_t	com_journalFile;
 extern	fileHandle_t	com_journalDataFile;
 
-extern qboolean com_sse2_supported;
-
 typedef enum {
 	TAG_FREE,
 	TAG_GENERAL,
@@ -963,11 +924,9 @@
 
 */
 
-#if 0
-#if defined(NDEBUG) && !defined(BSPC)
+#if !defined(NDEBUG) && !defined(BSPC)
 	#define ZONE_DEBUG
 #endif
-#endif
 
 #ifdef ZONE_DEBUG
 #define Z_TagMalloc(size, tag)			Z_TagMallocDebug(size, tag, #size, __FILE__, __LINE__)
@@ -1022,20 +981,20 @@
 void CL_Init( void );
 void CL_Disconnect( qboolean showMainMenu );
 void CL_Shutdown(char *finalmsg, qboolean disconnect, qboolean quit);
-void CL_Frame( int msec, double fmsec );
+void CL_Frame( int msec );
 qboolean CL_GameCommand( void );
 void CL_KeyEvent (int key, qboolean down, unsigned time);
 
 void CL_CharEvent( int key );
 // char events are for field typing, not game control
 
-void CL_MouseEvent( int dx, int dy, int time, qboolean active );
+void CL_MouseEvent( int dx, int dy, int time );
 
 void CL_JoystickEvent( int axis, int value, int time );
 
 void CL_PacketEvent( netadr_t from, msg_t *msg );
 
-//void CL_ConsolePrint( char *text );
+void CL_ConsolePrint( char *text );
 
 void CL_MapLoading( void );
 // do a screen update before starting to load a map
@@ -1077,13 +1036,17 @@
 
 void SCR_DebugGraph (float value);	// FIXME: move logging to common?
 
+// AVI files have the start of pixel lines 4 byte-aligned
+#define AVI_LINE_PADDING 4
+
 //
 // server interface
 //
 void SV_Init( void );
 void SV_Shutdown( char *finalmsg );
-void SV_Frame( int msec, double fmsec );
+void SV_Frame( int msec );
 void SV_PacketEvent( netadr_t from, msg_t *msg );
+int SV_FrameMsec(void);
 qboolean SV_GameCommand( void );
 int SV_SendQueuedPackets(void);
 
@@ -1114,7 +1077,7 @@
 void	Sys_Init (void);
 
 // general development dll loading for virtual machine testing
-void   * QDECL Sys_LoadGameDll( const char *name, vmMainProc *entryPoint,
+void	* QDECL Sys_LoadGameDll( const char *name, vmMainProc *entryPoint,
 				  intptr_t (QDECL *systemcalls)(intptr_t, ...) );
 void	Sys_UnloadDll( void *dllHandle );
 
@@ -1149,13 +1112,12 @@
 qboolean	Sys_IsLANAddress (netadr_t adr);
 void		Sys_ShowIP(void);
 
-FILE  *Sys_FOpen( const char *ospath, const char *mode );
+FILE	*Sys_FOpen( const char *ospath, const char *mode );
 qboolean Sys_Mkdir( const char *path );
 FILE	*Sys_Mkfifo( const char *ospath );
 char	*Sys_Cwd( void );
 void	Sys_SetDefaultInstallPath(const char *path);
 char	*Sys_DefaultInstallPath(void);
-char *Sys_QuakeLiveDir (void);
 char	*Sys_SteamPath(void);
 char	*Sys_GogPath(void);
 char	*Sys_MicrosoftStorePath(void);
@@ -1164,9 +1126,9 @@
 char    *Sys_DefaultAppPath(void);
 #endif
 
-char   *Sys_DefaultHomeConfigPath(void);
-char   *Sys_DefaultHomeDataPath(void);
-char   *Sys_DefaultHomeStatePath(void);
+char	*Sys_DefaultHomeConfigPath(void);
+char	*Sys_DefaultHomeDataPath(void);
+char	*Sys_DefaultHomeStatePath(void);
 const char *Sys_Dirname( char *path );
 const char *Sys_Basename( char *path );
 char *Sys_ConsoleInput(void);
@@ -1178,9 +1140,6 @@
 qboolean Sys_LowPhysicalMemory( void );
 
 void Sys_SetEnv(const char *name, const char *value);
-void Sys_OpenQuakeLiveDirectory (void);
-void Sys_OpenWolfcamDirectory (void);
-int Sys_DirnameCmp (const char *pathName1, const char *pathName2);
 
 typedef enum
 {
@@ -1205,9 +1164,6 @@
 void Sys_RemovePIDFile( const char *gamedir );
 void Sys_InitPIDFile( const char *gamedir );
 
-FILE *Sys_Popen (const char *command);
-int Sys_Pclose (FILE *stream);
-
 /* This is based on the Adaptive Huffman algorithm described in Sayood's Data
  * Compression book.  The ranks are not actually stored, but implicitly defined
  * by the location of a node within a doubly-linked list */

```

### `quake3e`  — sha256 `92d55680d655...`, 44189 bytes

_Diff stat: +566 / -474 lines_

_(full diff is 56155 bytes — see files directly)_

### `openarena-engine`  — sha256 `ee68d726c8fb...`, 39167 bytes

_Diff stat: +102 / -161 lines_

_(full diff is 23740 bytes — see files directly)_

### `openarena-gamecode`  — sha256 `a70a38949644...`, 35931 bytes

_Diff stat: +124 / -264 lines_

_(full diff is 30045 bytes — see files directly)_
