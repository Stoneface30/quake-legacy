# Diff: `code/cgame/cg_public.h`
**Canonical:** `wolfcamql-src` (sha256 `e41247d61c1e...`, 7638 bytes)

## Variants

### `quake3-source`  — sha256 `d8a8a3187918...`, 6405 bytes

_Diff stat: +33 / -106 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_public.h	2026-04-16 20:02:25.149526600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\cgame\cg_public.h	2026-04-16 20:02:19.884537500 +0100
@@ -1,54 +1,35 @@
-#ifndef cg_public_h_included
-#define cg_public_h_included
-
-// Copyright (C) 1999-2000 Id Software, Inc.
-//
-
-
-#define MAX_DEMO_OBITS (1024 * 2)
-#define MAX_ITEM_PICKUPS (1024 * 4)
-#define MAX_TIMEOUTS (256)
-#define MAX_DEMO_ROUND_STARTS 256
-
-typedef struct {
-	int startTime;
-	int endTime;
-	int serverTime;  // time the timeout or timein command is issued, since it takes two config string changes in quake live for the start and end time this is used incase order doesn't matter
-	//int cpmaLevelTime;
-	//int cpmaTd;
-	//int cpmaTimein;
-} timeOut_t;
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
 
-typedef struct {
-	int firstServerTime;
-	int firstMessageNum;
-	int lastServerTime;
-	int lastMessageNum;
-	int number;
-	int killer;
-	int victim;
-	int mod;
-} demoObit_t;
+This file is part of Quake III Arena source code.
 
-typedef struct {
-	int clientNum;
-	int index;
-	vec3_t origin;
-	int pickupTime;
-	int specPickupTime;
-	int number;  // entity number
-	qboolean spec;
-} itemPickup_t;
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
+along with Foobar; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
+//
 
 
-#define	CMD_BACKUP			64
+#define	CMD_BACKUP			64	
 #define	CMD_MASK			(CMD_BACKUP - 1)
 // allow a lot of command backups for very fast systems
 // multiple commands may be combined into a single packet, so this
 // needs to be larger than PACKET_BACKUP
 
 
-#define	MAX_ENTITIES_IN_SNAPSHOT	512  //256
+#define	MAX_ENTITIES_IN_SNAPSHOT	256
 
 // snapshots are a view of the server at a given time
 
@@ -70,15 +51,13 @@
 
 	int				numServerCommands;		// text based server commands to execute when this
 	int				serverCommandSequence;	// snapshot becomes current
-	int messageNum;
 } snapshot_t;
 
 enum {
   CGAME_EVENT_NONE,
   CGAME_EVENT_TEAMMENU,
   CGAME_EVENT_SCOREBOARD,
-  CGAME_EVENT_EDITHUD,
-  CGAME_EVENT_DEMO
+  CGAME_EVENT_EDITHUD
 };
 
 
@@ -90,7 +69,7 @@
 ==================================================================
 */
 
-#define	CGAME_IMPORT_API_VERSION	0x6667
+#define	CGAME_IMPORT_API_VERSION	4
 
 typedef enum {
 	CG_PRINT,
@@ -184,11 +163,13 @@
 	CG_R_ADDPOLYSTOSCENE,
 	CG_R_INPVS,
 	// 1.32
-	CG_FS_SEEK,   // 89
+	CG_FS_SEEK,
 
+/*
 	CG_LOADCAMERA,
 	CG_STARTCAMERA,
 	CG_GETCAMERAINFO,
+*/
 
 	CG_MEMSET = 100,
 	CG_MEMCPY,
@@ -201,57 +182,7 @@
 	CG_CEIL,
 	CG_TESTPRINTINT,
 	CG_TESTPRINTFLOAT,
-	CG_ACOS,
-
-	CG_GET_ADVERTISEMENTS,
-	CG_DRAW_CONSOLE_LINES,
-	CG_KEY_GETBINDING,
-	CG_GETLASTEXECUTEDSERVERCOMMAND,
-	CG_GETNEXTKILLER,
-	CG_GETNEXTVICTIM,
-	CG_REPLACESHADERIMAGE,
-	CG_REGISTERSHADERFROMDATA,
-	CG_GETSHADERIMAGEDIMENSIONS,
-	CG_GETSHADERIMAGEDATA,
-	CG_PEEKSNAPSHOT,
-	CG_CALCSPLINE,
-	CG_SETPATHLINES,
-	CG_GETGAMESTARTTIME,
-	CG_GETGAMEENDTIME,
-	CG_GETFIRSTSERVERTIME,
-	//CG_ADDAT,
-	CG_GETLEGSANIMSTARTTIME,
-	CG_GETTORSOANIMSTARTTIME,
-	CG_R_REGISTERSHADERLIGHTMAP,
-	CG_AUTOWRITECONFIG,
-	CG_SENDCONSOLECOMMANDNOW,
-	CG_POWF,
-	CG_R_CLEAR_REMAPPED_SHADER,
-	CG_GETITEMPICKUPNUMBER,
-	CG_GETITEMPICKUP,
-	CG_R_GETSINGLESHADER,
-	CG_CVAR_EXISTS,
-	CG_GET_DEMO_TIMEOUTS,
-	CG_GET_NUM_PLAYER_INFO,
-	CG_GET_EXTRA_PLAYER_INFO,
-	CG_GET_REAL_MAP_NAME,
-	CG_R_ADDREFENTITYPTRTOSCENE,
-	CG_S_PRINTSFXFILENAME,
-	CG_KEY_GETOVERSTRIKEMODE,
-	CG_KEY_SETOVERSTRIKEMODE,
-	CG_KEY_SETBINDING,
-	CG_KEY_GETBINDINGBUF,
-	CG_KEY_KEYNUMTOSTRINGBUF,
-	CG_R_GETGLYPHINFO,
-	CG_GETLASTSERVERTIME,
-
-	CG_R_GETFONTINFO,
-	CG_GETROUNDSTARTTIMES,
-	CG_GETTEAMSWITCHTIME,
-	CG_R_BEGIN_HUD,
-	CG_R_UPDATE_DOF,
-	CG_R_GETMODELNAME,
-
+	CG_ACOS
 } cgameImport_t;
 
 
@@ -265,7 +196,7 @@
 
 typedef enum {
 	CG_INIT,
-//	void CG_Init (int serverMessageNum, int serverCommandSequence, int clientNum, qboolean demoPlayback)
+//	void CG_Init( int serverMessageNum, int serverCommandSequence, int clientNum )
 	// called when the level loads or when the renderer is restarted
 	// all media should be registered at this time
 	// cgame will display loading status by calling SCR_Update, which
@@ -275,7 +206,7 @@
 
 	CG_SHUTDOWN,
 //	void (*CG_Shutdown)( void );
-	// opportunity to flush and close any open files
+	// oportunity to flush and close any open files
 
 	CG_CONSOLE_COMMAND,
 //	qboolean (*CG_ConsoleCommand)( void );
@@ -295,17 +226,13 @@
 	CG_LAST_ATTACKER,
 //	int (*CG_LastAttacker)( void );
 
-	CG_KEY_EVENT,
+	CG_KEY_EVENT, 
 //	void	(*CG_KeyEvent)( int key, qboolean down );
 
 	CG_MOUSE_EVENT,
-//	void	(*CG_MouseEvent)( int dx, int dy, qboolean active );
-	CG_EVENT_HANDLING,
+//	void	(*CG_MouseEvent)( int dx, int dy );
+	CG_EVENT_HANDLING
 //	void (*CG_EventHandling)(int type);
-	CG_TIME_CHANGE,
-	CG_COLOR_TABLE_CHANGE,
 } cgameExport_t;
 
 //----------------------------------------------
-
-#endif  // cg_public_h_included

```

### `ioquake3`  — sha256 `da764f1f1ef9...`, 6427 bytes

_Diff stat: +32 / -105 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_public.h	2026-04-16 20:02:25.149526600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\cgame\cg_public.h	2026-04-16 20:02:21.523053400 +0100
@@ -1,54 +1,35 @@
-#ifndef cg_public_h_included
-#define cg_public_h_included
-
-// Copyright (C) 1999-2000 Id Software, Inc.
-//
-
-
-#define MAX_DEMO_OBITS (1024 * 2)
-#define MAX_ITEM_PICKUPS (1024 * 4)
-#define MAX_TIMEOUTS (256)
-#define MAX_DEMO_ROUND_STARTS 256
-
-typedef struct {
-	int startTime;
-	int endTime;
-	int serverTime;  // time the timeout or timein command is issued, since it takes two config string changes in quake live for the start and end time this is used incase order doesn't matter
-	//int cpmaLevelTime;
-	//int cpmaTd;
-	//int cpmaTimein;
-} timeOut_t;
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
 
-typedef struct {
-	int firstServerTime;
-	int firstMessageNum;
-	int lastServerTime;
-	int lastMessageNum;
-	int number;
-	int killer;
-	int victim;
-	int mod;
-} demoObit_t;
+This file is part of Quake III Arena source code.
 
-typedef struct {
-	int clientNum;
-	int index;
-	vec3_t origin;
-	int pickupTime;
-	int specPickupTime;
-	int number;  // entity number
-	qboolean spec;
-} itemPickup_t;
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
+//
 
 
-#define	CMD_BACKUP			64
+#define	CMD_BACKUP			64	
 #define	CMD_MASK			(CMD_BACKUP - 1)
 // allow a lot of command backups for very fast systems
 // multiple commands may be combined into a single packet, so this
 // needs to be larger than PACKET_BACKUP
 
 
-#define	MAX_ENTITIES_IN_SNAPSHOT	512  //256
+#define	MAX_ENTITIES_IN_SNAPSHOT	256
 
 // snapshots are a view of the server at a given time
 
@@ -70,15 +51,13 @@
 
 	int				numServerCommands;		// text based server commands to execute when this
 	int				serverCommandSequence;	// snapshot becomes current
-	int messageNum;
 } snapshot_t;
 
 enum {
   CGAME_EVENT_NONE,
   CGAME_EVENT_TEAMMENU,
   CGAME_EVENT_SCOREBOARD,
-  CGAME_EVENT_EDITHUD,
-  CGAME_EVENT_DEMO
+  CGAME_EVENT_EDITHUD
 };
 
 
@@ -90,7 +69,7 @@
 ==================================================================
 */
 
-#define	CGAME_IMPORT_API_VERSION	0x6667
+#define	CGAME_IMPORT_API_VERSION	4
 
 typedef enum {
 	CG_PRINT,
@@ -184,11 +163,13 @@
 	CG_R_ADDPOLYSTOSCENE,
 	CG_R_INPVS,
 	// 1.32
-	CG_FS_SEEK,   // 89
+	CG_FS_SEEK,
 
+/*
 	CG_LOADCAMERA,
 	CG_STARTCAMERA,
 	CG_GETCAMERAINFO,
+*/
 
 	CG_MEMSET = 100,
 	CG_MEMCPY,
@@ -201,57 +182,7 @@
 	CG_CEIL,
 	CG_TESTPRINTINT,
 	CG_TESTPRINTFLOAT,
-	CG_ACOS,
-
-	CG_GET_ADVERTISEMENTS,
-	CG_DRAW_CONSOLE_LINES,
-	CG_KEY_GETBINDING,
-	CG_GETLASTEXECUTEDSERVERCOMMAND,
-	CG_GETNEXTKILLER,
-	CG_GETNEXTVICTIM,
-	CG_REPLACESHADERIMAGE,
-	CG_REGISTERSHADERFROMDATA,
-	CG_GETSHADERIMAGEDIMENSIONS,
-	CG_GETSHADERIMAGEDATA,
-	CG_PEEKSNAPSHOT,
-	CG_CALCSPLINE,
-	CG_SETPATHLINES,
-	CG_GETGAMESTARTTIME,
-	CG_GETGAMEENDTIME,
-	CG_GETFIRSTSERVERTIME,
-	//CG_ADDAT,
-	CG_GETLEGSANIMSTARTTIME,
-	CG_GETTORSOANIMSTARTTIME,
-	CG_R_REGISTERSHADERLIGHTMAP,
-	CG_AUTOWRITECONFIG,
-	CG_SENDCONSOLECOMMANDNOW,
-	CG_POWF,
-	CG_R_CLEAR_REMAPPED_SHADER,
-	CG_GETITEMPICKUPNUMBER,
-	CG_GETITEMPICKUP,
-	CG_R_GETSINGLESHADER,
-	CG_CVAR_EXISTS,
-	CG_GET_DEMO_TIMEOUTS,
-	CG_GET_NUM_PLAYER_INFO,
-	CG_GET_EXTRA_PLAYER_INFO,
-	CG_GET_REAL_MAP_NAME,
-	CG_R_ADDREFENTITYPTRTOSCENE,
-	CG_S_PRINTSFXFILENAME,
-	CG_KEY_GETOVERSTRIKEMODE,
-	CG_KEY_SETOVERSTRIKEMODE,
-	CG_KEY_SETBINDING,
-	CG_KEY_GETBINDINGBUF,
-	CG_KEY_KEYNUMTOSTRINGBUF,
-	CG_R_GETGLYPHINFO,
-	CG_GETLASTSERVERTIME,
-
-	CG_R_GETFONTINFO,
-	CG_GETROUNDSTARTTIMES,
-	CG_GETTEAMSWITCHTIME,
-	CG_R_BEGIN_HUD,
-	CG_R_UPDATE_DOF,
-	CG_R_GETMODELNAME,
-
+	CG_ACOS
 } cgameImport_t;
 
 
@@ -265,7 +196,7 @@
 
 typedef enum {
 	CG_INIT,
-//	void CG_Init (int serverMessageNum, int serverCommandSequence, int clientNum, qboolean demoPlayback)
+//	void CG_Init( int serverMessageNum, int serverCommandSequence, int clientNum )
 	// called when the level loads or when the renderer is restarted
 	// all media should be registered at this time
 	// cgame will display loading status by calling SCR_Update, which
@@ -295,17 +226,13 @@
 	CG_LAST_ATTACKER,
 //	int (*CG_LastAttacker)( void );
 
-	CG_KEY_EVENT,
+	CG_KEY_EVENT, 
 //	void	(*CG_KeyEvent)( int key, qboolean down );
 
 	CG_MOUSE_EVENT,
-//	void	(*CG_MouseEvent)( int dx, int dy, qboolean active );
-	CG_EVENT_HANDLING,
+//	void	(*CG_MouseEvent)( int dx, int dy );
+	CG_EVENT_HANDLING
 //	void (*CG_EventHandling)(int type);
-	CG_TIME_CHANGE,
-	CG_COLOR_TABLE_CHANGE,
 } cgameExport_t;
 
 //----------------------------------------------
-
-#endif  // cg_public_h_included

```

### `quake3e`  — sha256 `371a42af5f12...`, 6570 bytes

_Diff stat: +41 / -109 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_public.h	2026-04-16 20:02:25.149526600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\cgame\cg_public.h	2026-04-16 20:02:26.908504600 +0100
@@ -1,54 +1,35 @@
-#ifndef cg_public_h_included
-#define cg_public_h_included
-
-// Copyright (C) 1999-2000 Id Software, Inc.
-//
-
-
-#define MAX_DEMO_OBITS (1024 * 2)
-#define MAX_ITEM_PICKUPS (1024 * 4)
-#define MAX_TIMEOUTS (256)
-#define MAX_DEMO_ROUND_STARTS 256
-
-typedef struct {
-	int startTime;
-	int endTime;
-	int serverTime;  // time the timeout or timein command is issued, since it takes two config string changes in quake live for the start and end time this is used incase order doesn't matter
-	//int cpmaLevelTime;
-	//int cpmaTd;
-	//int cpmaTimein;
-} timeOut_t;
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
 
-typedef struct {
-	int firstServerTime;
-	int firstMessageNum;
-	int lastServerTime;
-	int lastMessageNum;
-	int number;
-	int killer;
-	int victim;
-	int mod;
-} demoObit_t;
+This file is part of Quake III Arena source code.
 
-typedef struct {
-	int clientNum;
-	int index;
-	vec3_t origin;
-	int pickupTime;
-	int specPickupTime;
-	int number;  // entity number
-	qboolean spec;
-} itemPickup_t;
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
+//
 
 
-#define	CMD_BACKUP			64
+#define	CMD_BACKUP			64	
 #define	CMD_MASK			(CMD_BACKUP - 1)
 // allow a lot of command backups for very fast systems
 // multiple commands may be combined into a single packet, so this
 // needs to be larger than PACKET_BACKUP
 
 
-#define	MAX_ENTITIES_IN_SNAPSHOT	512  //256
+#define	MAX_ENTITIES_IN_SNAPSHOT	256
 
 // snapshots are a view of the server at a given time
 
@@ -70,15 +51,13 @@
 
 	int				numServerCommands;		// text based server commands to execute when this
 	int				serverCommandSequence;	// snapshot becomes current
-	int messageNum;
 } snapshot_t;
 
 enum {
   CGAME_EVENT_NONE,
   CGAME_EVENT_TEAMMENU,
   CGAME_EVENT_SCOREBOARD,
-  CGAME_EVENT_EDITHUD,
-  CGAME_EVENT_DEMO
+  CGAME_EVENT_EDITHUD
 };
 
 
@@ -90,7 +69,7 @@
 ==================================================================
 */
 
-#define	CGAME_IMPORT_API_VERSION	0x6667
+#define	CGAME_IMPORT_API_VERSION	4
 
 typedef enum {
 	CG_PRINT,
@@ -184,73 +163,27 @@
 	CG_R_ADDPOLYSTOSCENE,
 	CG_R_INPVS,
 	// 1.32
-	CG_FS_SEEK,   // 89
+	CG_FS_SEEK,
 
+/*
 	CG_LOADCAMERA,
 	CG_STARTCAMERA,
 	CG_GETCAMERAINFO,
+*/
 
-	CG_MEMSET = 100,
-	CG_MEMCPY,
-	CG_STRNCPY,
-	CG_SIN,
-	CG_COS,
-	CG_ATAN2,
-	CG_SQRT,
-	CG_FLOOR,
+	CG_FLOOR = 107,
 	CG_CEIL,
 	CG_TESTPRINTINT,
 	CG_TESTPRINTFLOAT,
 	CG_ACOS,
 
-	CG_GET_ADVERTISEMENTS,
-	CG_DRAW_CONSOLE_LINES,
-	CG_KEY_GETBINDING,
-	CG_GETLASTEXECUTEDSERVERCOMMAND,
-	CG_GETNEXTKILLER,
-	CG_GETNEXTVICTIM,
-	CG_REPLACESHADERIMAGE,
-	CG_REGISTERSHADERFROMDATA,
-	CG_GETSHADERIMAGEDIMENSIONS,
-	CG_GETSHADERIMAGEDATA,
-	CG_PEEKSNAPSHOT,
-	CG_CALCSPLINE,
-	CG_SETPATHLINES,
-	CG_GETGAMESTARTTIME,
-	CG_GETGAMEENDTIME,
-	CG_GETFIRSTSERVERTIME,
-	//CG_ADDAT,
-	CG_GETLEGSANIMSTARTTIME,
-	CG_GETTORSOANIMSTARTTIME,
-	CG_R_REGISTERSHADERLIGHTMAP,
-	CG_AUTOWRITECONFIG,
-	CG_SENDCONSOLECOMMANDNOW,
-	CG_POWF,
-	CG_R_CLEAR_REMAPPED_SHADER,
-	CG_GETITEMPICKUPNUMBER,
-	CG_GETITEMPICKUP,
-	CG_R_GETSINGLESHADER,
-	CG_CVAR_EXISTS,
-	CG_GET_DEMO_TIMEOUTS,
-	CG_GET_NUM_PLAYER_INFO,
-	CG_GET_EXTRA_PLAYER_INFO,
-	CG_GET_REAL_MAP_NAME,
-	CG_R_ADDREFENTITYPTRTOSCENE,
-	CG_S_PRINTSFXFILENAME,
-	CG_KEY_GETOVERSTRIKEMODE,
-	CG_KEY_SETOVERSTRIKEMODE,
-	CG_KEY_SETBINDING,
-	CG_KEY_GETBINDINGBUF,
-	CG_KEY_KEYNUMTOSTRINGBUF,
-	CG_R_GETGLYPHINFO,
-	CG_GETLASTSERVERTIME,
-
-	CG_R_GETFONTINFO,
-	CG_GETROUNDSTARTTIMES,
-	CG_GETTEAMSWITCHTIME,
-	CG_R_BEGIN_HUD,
-	CG_R_UPDATE_DOF,
-	CG_R_GETMODELNAME,
+	// engine extensions
+	CG_R_ADDREFENTITYTOSCENE2,
+	CG_R_FORCEFIXEDDLIGHTS,
+	CG_R_ADDLINEARLIGHTTOSCENE,
+	CG_IS_RECORDING_DEMO,
+	CG_CVAR_SETDESCRIPTION,
+	CG_TRAP_GETVALUE = COM_TRAP_GETVALUE,
 
 } cgameImport_t;
 
@@ -265,7 +198,7 @@
 
 typedef enum {
 	CG_INIT,
-//	void CG_Init (int serverMessageNum, int serverCommandSequence, int clientNum, qboolean demoPlayback)
+//	void CG_Init( int serverMessageNum, int serverCommandSequence, int clientNum )
 	// called when the level loads or when the renderer is restarted
 	// all media should be registered at this time
 	// cgame will display loading status by calling SCR_Update, which
@@ -295,17 +228,16 @@
 	CG_LAST_ATTACKER,
 //	int (*CG_LastAttacker)( void );
 
-	CG_KEY_EVENT,
+	CG_KEY_EVENT, 
 //	void	(*CG_KeyEvent)( int key, qboolean down );
 
 	CG_MOUSE_EVENT,
-//	void	(*CG_MouseEvent)( int dx, int dy, qboolean active );
+//	void	(*CG_MouseEvent)( int dx, int dy );
+
 	CG_EVENT_HANDLING,
 //	void (*CG_EventHandling)(int type);
-	CG_TIME_CHANGE,
-	CG_COLOR_TABLE_CHANGE,
+
+	CG_EXPORT_LAST,
 } cgameExport_t;
 
 //----------------------------------------------
-
-#endif  // cg_public_h_included

```

### `openarena-engine`  — sha256 `662b68f6be65...`, 6531 bytes

_Diff stat: +34 / -105 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_public.h	2026-04-16 20:02:25.149526600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_public.h	2026-04-16 22:48:25.726201700 +0100
@@ -1,54 +1,35 @@
-#ifndef cg_public_h_included
-#define cg_public_h_included
-
-// Copyright (C) 1999-2000 Id Software, Inc.
-//
-
-
-#define MAX_DEMO_OBITS (1024 * 2)
-#define MAX_ITEM_PICKUPS (1024 * 4)
-#define MAX_TIMEOUTS (256)
-#define MAX_DEMO_ROUND_STARTS 256
-
-typedef struct {
-	int startTime;
-	int endTime;
-	int serverTime;  // time the timeout or timein command is issued, since it takes two config string changes in quake live for the start and end time this is used incase order doesn't matter
-	//int cpmaLevelTime;
-	//int cpmaTd;
-	//int cpmaTimein;
-} timeOut_t;
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
 
-typedef struct {
-	int firstServerTime;
-	int firstMessageNum;
-	int lastServerTime;
-	int lastMessageNum;
-	int number;
-	int killer;
-	int victim;
-	int mod;
-} demoObit_t;
+This file is part of Quake III Arena source code.
 
-typedef struct {
-	int clientNum;
-	int index;
-	vec3_t origin;
-	int pickupTime;
-	int specPickupTime;
-	int number;  // entity number
-	qboolean spec;
-} itemPickup_t;
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
+//
 
 
-#define	CMD_BACKUP			64
+#define	CMD_BACKUP			64	
 #define	CMD_MASK			(CMD_BACKUP - 1)
 // allow a lot of command backups for very fast systems
 // multiple commands may be combined into a single packet, so this
 // needs to be larger than PACKET_BACKUP
 
 
-#define	MAX_ENTITIES_IN_SNAPSHOT	512  //256
+#define	MAX_ENTITIES_IN_SNAPSHOT	256
 
 // snapshots are a view of the server at a given time
 
@@ -70,15 +51,13 @@
 
 	int				numServerCommands;		// text based server commands to execute when this
 	int				serverCommandSequence;	// snapshot becomes current
-	int messageNum;
 } snapshot_t;
 
 enum {
   CGAME_EVENT_NONE,
   CGAME_EVENT_TEAMMENU,
   CGAME_EVENT_SCOREBOARD,
-  CGAME_EVENT_EDITHUD,
-  CGAME_EVENT_DEMO
+  CGAME_EVENT_EDITHUD
 };
 
 
@@ -90,7 +69,7 @@
 ==================================================================
 */
 
-#define	CGAME_IMPORT_API_VERSION	0x6667
+#define	CGAME_IMPORT_API_VERSION	4
 
 typedef enum {
 	CG_PRINT,
@@ -184,11 +163,13 @@
 	CG_R_ADDPOLYSTOSCENE,
 	CG_R_INPVS,
 	// 1.32
-	CG_FS_SEEK,   // 89
+	CG_FS_SEEK,
 
+/*
 	CG_LOADCAMERA,
 	CG_STARTCAMERA,
 	CG_GETCAMERAINFO,
+*/
 
 	CG_MEMSET = 100,
 	CG_MEMCPY,
@@ -202,56 +183,8 @@
 	CG_TESTPRINTINT,
 	CG_TESTPRINTFLOAT,
 	CG_ACOS,
-
-	CG_GET_ADVERTISEMENTS,
-	CG_DRAW_CONSOLE_LINES,
-	CG_KEY_GETBINDING,
-	CG_GETLASTEXECUTEDSERVERCOMMAND,
-	CG_GETNEXTKILLER,
-	CG_GETNEXTVICTIM,
-	CG_REPLACESHADERIMAGE,
-	CG_REGISTERSHADERFROMDATA,
-	CG_GETSHADERIMAGEDIMENSIONS,
-	CG_GETSHADERIMAGEDATA,
-	CG_PEEKSNAPSHOT,
-	CG_CALCSPLINE,
-	CG_SETPATHLINES,
-	CG_GETGAMESTARTTIME,
-	CG_GETGAMEENDTIME,
-	CG_GETFIRSTSERVERTIME,
-	//CG_ADDAT,
-	CG_GETLEGSANIMSTARTTIME,
-	CG_GETTORSOANIMSTARTTIME,
-	CG_R_REGISTERSHADERLIGHTMAP,
-	CG_AUTOWRITECONFIG,
-	CG_SENDCONSOLECOMMANDNOW,
-	CG_POWF,
-	CG_R_CLEAR_REMAPPED_SHADER,
-	CG_GETITEMPICKUPNUMBER,
-	CG_GETITEMPICKUP,
-	CG_R_GETSINGLESHADER,
-	CG_CVAR_EXISTS,
-	CG_GET_DEMO_TIMEOUTS,
-	CG_GET_NUM_PLAYER_INFO,
-	CG_GET_EXTRA_PLAYER_INFO,
-	CG_GET_REAL_MAP_NAME,
-	CG_R_ADDREFENTITYPTRTOSCENE,
-	CG_S_PRINTSFXFILENAME,
-	CG_KEY_GETOVERSTRIKEMODE,
-	CG_KEY_SETOVERSTRIKEMODE,
-	CG_KEY_SETBINDING,
-	CG_KEY_GETBINDINGBUF,
-	CG_KEY_KEYNUMTOSTRINGBUF,
-	CG_R_GETGLYPHINFO,
-	CG_GETLASTSERVERTIME,
-
-	CG_R_GETFONTINFO,
-	CG_GETROUNDSTARTTIMES,
-	CG_GETTEAMSWITCHTIME,
-	CG_R_BEGIN_HUD,
-	CG_R_UPDATE_DOF,
-	CG_R_GETMODELNAME,
-
+	CG_R_LFX_PARTICLEEFFECT,	// leilei - particle effects
+	CG_R_VIEWPOSITION		// leilei - view position 
 } cgameImport_t;
 
 
@@ -265,7 +198,7 @@
 
 typedef enum {
 	CG_INIT,
-//	void CG_Init (int serverMessageNum, int serverCommandSequence, int clientNum, qboolean demoPlayback)
+//	void CG_Init( int serverMessageNum, int serverCommandSequence, int clientNum )
 	// called when the level loads or when the renderer is restarted
 	// all media should be registered at this time
 	// cgame will display loading status by calling SCR_Update, which
@@ -275,7 +208,7 @@
 
 	CG_SHUTDOWN,
 //	void (*CG_Shutdown)( void );
-	// opportunity to flush and close any open files
+	// oportunity to flush and close any open files
 
 	CG_CONSOLE_COMMAND,
 //	qboolean (*CG_ConsoleCommand)( void );
@@ -295,17 +228,13 @@
 	CG_LAST_ATTACKER,
 //	int (*CG_LastAttacker)( void );
 
-	CG_KEY_EVENT,
+	CG_KEY_EVENT, 
 //	void	(*CG_KeyEvent)( int key, qboolean down );
 
 	CG_MOUSE_EVENT,
-//	void	(*CG_MouseEvent)( int dx, int dy, qboolean active );
-	CG_EVENT_HANDLING,
+//	void	(*CG_MouseEvent)( int dx, int dy );
+	CG_EVENT_HANDLING
 //	void (*CG_EventHandling)(int type);
-	CG_TIME_CHANGE,
-	CG_COLOR_TABLE_CHANGE,
 } cgameExport_t;
 
 //----------------------------------------------
-
-#endif  // cg_public_h_included

```

### `openarena-gamecode`  — sha256 `3a08fb4d45b4...`, 6503 bytes

_Diff stat: +34 / -105 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_public.h	2026-04-16 20:02:25.149526600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\cgame\cg_public.h	2026-04-16 22:48:24.153329500 +0100
@@ -1,54 +1,35 @@
-#ifndef cg_public_h_included
-#define cg_public_h_included
-
-// Copyright (C) 1999-2000 Id Software, Inc.
-//
-
-
-#define MAX_DEMO_OBITS (1024 * 2)
-#define MAX_ITEM_PICKUPS (1024 * 4)
-#define MAX_TIMEOUTS (256)
-#define MAX_DEMO_ROUND_STARTS 256
-
-typedef struct {
-	int startTime;
-	int endTime;
-	int serverTime;  // time the timeout or timein command is issued, since it takes two config string changes in quake live for the start and end time this is used incase order doesn't matter
-	//int cpmaLevelTime;
-	//int cpmaTd;
-	//int cpmaTimein;
-} timeOut_t;
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
 
-typedef struct {
-	int firstServerTime;
-	int firstMessageNum;
-	int lastServerTime;
-	int lastMessageNum;
-	int number;
-	int killer;
-	int victim;
-	int mod;
-} demoObit_t;
+This file is part of Quake III Arena source code.
 
-typedef struct {
-	int clientNum;
-	int index;
-	vec3_t origin;
-	int pickupTime;
-	int specPickupTime;
-	int number;  // entity number
-	qboolean spec;
-} itemPickup_t;
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
+//
 
 
-#define	CMD_BACKUP			64
+#define	CMD_BACKUP			64	
 #define	CMD_MASK			(CMD_BACKUP - 1)
 // allow a lot of command backups for very fast systems
 // multiple commands may be combined into a single packet, so this
 // needs to be larger than PACKET_BACKUP
 
 
-#define	MAX_ENTITIES_IN_SNAPSHOT	512  //256
+#define	MAX_ENTITIES_IN_SNAPSHOT	256
 
 // snapshots are a view of the server at a given time
 
@@ -70,15 +51,13 @@
 
 	int				numServerCommands;		// text based server commands to execute when this
 	int				serverCommandSequence;	// snapshot becomes current
-	int messageNum;
 } snapshot_t;
 
 enum {
   CGAME_EVENT_NONE,
   CGAME_EVENT_TEAMMENU,
   CGAME_EVENT_SCOREBOARD,
-  CGAME_EVENT_EDITHUD,
-  CGAME_EVENT_DEMO
+  CGAME_EVENT_EDITHUD
 };
 
 
@@ -90,7 +69,7 @@
 ==================================================================
 */
 
-#define	CGAME_IMPORT_API_VERSION	0x6667
+#define	CGAME_IMPORT_API_VERSION	4
 
 typedef enum {
 	CG_PRINT,
@@ -184,11 +163,13 @@
 	CG_R_ADDPOLYSTOSCENE,
 	CG_R_INPVS,
 	// 1.32
-	CG_FS_SEEK,   // 89
+	CG_FS_SEEK,
 
+/*
 	CG_LOADCAMERA,
 	CG_STARTCAMERA,
 	CG_GETCAMERAINFO,
+*/
 
 	CG_MEMSET = 100,
 	CG_MEMCPY,
@@ -202,56 +183,8 @@
 	CG_TESTPRINTINT,
 	CG_TESTPRINTFLOAT,
 	CG_ACOS,
-
-	CG_GET_ADVERTISEMENTS,
-	CG_DRAW_CONSOLE_LINES,
-	CG_KEY_GETBINDING,
-	CG_GETLASTEXECUTEDSERVERCOMMAND,
-	CG_GETNEXTKILLER,
-	CG_GETNEXTVICTIM,
-	CG_REPLACESHADERIMAGE,
-	CG_REGISTERSHADERFROMDATA,
-	CG_GETSHADERIMAGEDIMENSIONS,
-	CG_GETSHADERIMAGEDATA,
-	CG_PEEKSNAPSHOT,
-	CG_CALCSPLINE,
-	CG_SETPATHLINES,
-	CG_GETGAMESTARTTIME,
-	CG_GETGAMEENDTIME,
-	CG_GETFIRSTSERVERTIME,
-	//CG_ADDAT,
-	CG_GETLEGSANIMSTARTTIME,
-	CG_GETTORSOANIMSTARTTIME,
-	CG_R_REGISTERSHADERLIGHTMAP,
-	CG_AUTOWRITECONFIG,
-	CG_SENDCONSOLECOMMANDNOW,
-	CG_POWF,
-	CG_R_CLEAR_REMAPPED_SHADER,
-	CG_GETITEMPICKUPNUMBER,
-	CG_GETITEMPICKUP,
-	CG_R_GETSINGLESHADER,
-	CG_CVAR_EXISTS,
-	CG_GET_DEMO_TIMEOUTS,
-	CG_GET_NUM_PLAYER_INFO,
-	CG_GET_EXTRA_PLAYER_INFO,
-	CG_GET_REAL_MAP_NAME,
-	CG_R_ADDREFENTITYPTRTOSCENE,
-	CG_S_PRINTSFXFILENAME,
-	CG_KEY_GETOVERSTRIKEMODE,
-	CG_KEY_SETOVERSTRIKEMODE,
-	CG_KEY_SETBINDING,
-	CG_KEY_GETBINDINGBUF,
-	CG_KEY_KEYNUMTOSTRINGBUF,
-	CG_R_GETGLYPHINFO,
-	CG_GETLASTSERVERTIME,
-
-	CG_R_GETFONTINFO,
-	CG_GETROUNDSTARTTIMES,
-	CG_GETTEAMSWITCHTIME,
-	CG_R_BEGIN_HUD,
-	CG_R_UPDATE_DOF,
-	CG_R_GETMODELNAME,
-
+	CG_R_LFX_PARTICLEEFFECT,	// leilei - particle effects
+	CG_R_VIEWPOSITION
 } cgameImport_t;
 
 
@@ -265,7 +198,7 @@
 
 typedef enum {
 	CG_INIT,
-//	void CG_Init (int serverMessageNum, int serverCommandSequence, int clientNum, qboolean demoPlayback)
+//	void CG_Init( int serverMessageNum, int serverCommandSequence, int clientNum )
 	// called when the level loads or when the renderer is restarted
 	// all media should be registered at this time
 	// cgame will display loading status by calling SCR_Update, which
@@ -275,7 +208,7 @@
 
 	CG_SHUTDOWN,
 //	void (*CG_Shutdown)( void );
-	// opportunity to flush and close any open files
+	// oportunity to flush and close any open files
 
 	CG_CONSOLE_COMMAND,
 //	qboolean (*CG_ConsoleCommand)( void );
@@ -295,17 +228,13 @@
 	CG_LAST_ATTACKER,
 //	int (*CG_LastAttacker)( void );
 
-	CG_KEY_EVENT,
+	CG_KEY_EVENT, 
 //	void	(*CG_KeyEvent)( int key, qboolean down );
 
 	CG_MOUSE_EVENT,
-//	void	(*CG_MouseEvent)( int dx, int dy, qboolean active );
-	CG_EVENT_HANDLING,
+//	void	(*CG_MouseEvent)( int dx, int dy );
+	CG_EVENT_HANDLING
 //	void (*CG_EventHandling)(int type);
-	CG_TIME_CHANGE,
-	CG_COLOR_TABLE_CHANGE,
 } cgameExport_t;
 
 //----------------------------------------------
-
-#endif  // cg_public_h_included

```
