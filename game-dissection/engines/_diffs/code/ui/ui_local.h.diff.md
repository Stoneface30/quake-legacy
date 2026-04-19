# Diff: `code/ui/ui_local.h`
**Canonical:** `wolfcamql-src` (sha256 `e7869b5698be...`, 31440 bytes)

## Variants

### `quake3-source`  — sha256 `035b95b6f269...`, 30951 bytes

_Diff stat: +18 / -25 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_local.h	2026-04-16 20:02:25.817962300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_local.h	2026-04-16 20:02:19.986148600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,12 +23,11 @@
 #ifndef __UI_LOCAL_H__
 #define __UI_LOCAL_H__
 
-#include "../qcommon/q_shared.h"
-#include "../renderercommon/tr_types.h"
+#include "../game/q_shared.h"
+#include "../cgame/tr_types.h"
 #include "ui_public.h"
-#include "../client/keycodes.h"
+#include "keycodes.h"
 #include "../game/bg_public.h"
-#include "ui_common.h"
 #include "ui_shared.h"
 
 // global display context
@@ -62,6 +61,7 @@
 
 extern vmCvar_t	ui_browserMaster;
 extern vmCvar_t	ui_browserGameType;
+extern vmCvar_t	ui_browserSortKey;
 extern vmCvar_t	ui_browserShowFull;
 extern vmCvar_t	ui_browserShowEmpty;
 
@@ -144,6 +144,7 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			96
 
 #define MTYPE_NULL				0
 #define MTYPE_SLIDER			1	
@@ -258,7 +259,7 @@
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -351,15 +352,14 @@
 //
 // ui_main.c
 //
-void UI_Report( void );
-void UI_Load( void );
+void UI_Report();
+void UI_Load();
 void UI_LoadMenus(const char *menuFile, qboolean reset);
 void _UI_SetActiveMenu( uiMenuCommand_t menu );
 int UI_AdjustTimeByGame(int time);
 void UI_ShowPostGame(qboolean newHigh);
-void UI_ClearScores( void );
+void UI_ClearScores();
 void UI_LoadArenas(void);
-void UI_LoadArenasIntoMapList(void);
 
 //
 // ui_menu.c
@@ -534,9 +534,6 @@
 
 	animation_t		animations[MAX_TOTALANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
-
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
 	qhandle_t		flashModel;
@@ -579,7 +576,7 @@
 //
 // ui_atoms.c
 //
-// this is only used in the old ui, the new ui has its own version
+// this is only used in the old ui, the new ui has it's own version
 typedef struct {
 	int					frametime;
 	int					realtime;
@@ -589,6 +586,7 @@
 	qboolean		debug;
 	qhandle_t		whiteShader;
 	qhandle_t		menuBackShader;
+	qhandle_t		menuBackShader2;
 	qhandle_t		menuBackNoLogoShader;
 	qhandle_t		charset;
 	qhandle_t		charsetProp;
@@ -611,7 +609,7 @@
 #define MAX_HEADNAME  32
 #define MAX_TEAMS 64
 #define MAX_GAMETYPES 16
-#define MAX_MAPS MAX_ARENAS
+#define MAX_MAPS 128
 #define MAX_SPMAPS 16
 #define PLAYERS_PER_TEAM 5
 #define MAX_PINGREQUESTS		32
@@ -634,7 +632,7 @@
 #define MAPS_PER_TIER 3
 #define MAX_TIERS 16
 #define MAX_MODS 64
-#define MAX_DEMOS 4096  //256
+#define MAX_DEMOS 256
 #define MAX_MOVIES 256
 #define MAX_PLAYERMODELS 256
 
@@ -918,7 +916,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error(const char *string) Q_NO_RETURN;
+void			trap_Error( const char *string );
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -929,8 +927,6 @@
 void			trap_Cvar_Reset( const char *name );
 void			trap_Cvar_Create( const char *var_name, const char *var_value, int flags );
 void			trap_Cvar_InfoStringBuffer( int bit, char *buffer, int bufsize );
-qboolean trap_Cvar_Exists (const char *var_name);
-
 int				trap_Argc( void );
 void			trap_Argv( int n, char *buffer, int bufferLength );
 void			trap_Cmd_ExecuteText( int exec_when, const char *text );	// don't use EXEC_NOW!
@@ -976,8 +972,8 @@
 void			trap_LAN_ClearPing( int n );
 void			trap_LAN_GetPing( int n, char *buf, int buflen, int *pingtime );
 void			trap_LAN_GetPingInfo( int n, char *buf, int buflen );
-void			trap_LAN_LoadCachedServers( void );
-void			trap_LAN_SaveCachedServers( void );
+void			trap_LAN_LoadCachedServers();
+void			trap_LAN_SaveCachedServers();
 void			trap_LAN_MarkServerVisible(int source, int n, qboolean visible);
 int				trap_LAN_ServerIsVisible( int source, int n);
 qboolean		trap_LAN_UpdateVisiblePings( int source );
@@ -997,14 +993,11 @@
 e_status		trap_CIN_RunCinematic (int handle);
 void			trap_CIN_DrawCinematic (int handle);
 void			trap_CIN_SetExtents (int handle, int x, int y, int w, int h);
-int				trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int				trap_RealTime(qtime_t *qtime);
 void			trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset );
 qboolean		trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 
 //
 // ui_addbots.c

```

### `ioquake3`  — sha256 `ac24c0379a93...`, 31150 bytes

_Diff stat: +5 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_local.h	2026-04-16 20:02:25.817962300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\ui\ui_local.h	2026-04-16 20:02:21.812554400 +0100
@@ -28,7 +28,6 @@
 #include "ui_public.h"
 #include "../client/keycodes.h"
 #include "../game/bg_public.h"
-#include "ui_common.h"
 #include "ui_shared.h"
 
 // global display context
@@ -144,6 +143,7 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			96
 
 #define MTYPE_NULL				0
 #define MTYPE_SLIDER			1	
@@ -534,8 +534,8 @@
 
 	animation_t		animations[MAX_TOTALANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
+	qboolean		fixedlegs;		// true if legs yaw is always the same as torso yaw
+	qboolean		fixedtorso;		// true if torso never changes yaw
 
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
@@ -634,7 +634,7 @@
 #define MAPS_PER_TIER 3
 #define MAX_TIERS 16
 #define MAX_MODS 64
-#define MAX_DEMOS 4096  //256
+#define MAX_DEMOS 512
 #define MAX_MOVIES 256
 #define MAX_PLAYERMODELS 256
 
@@ -929,8 +929,6 @@
 void			trap_Cvar_Reset( const char *name );
 void			trap_Cvar_Create( const char *var_name, const char *var_value, int flags );
 void			trap_Cvar_InfoStringBuffer( int bit, char *buffer, int bufsize );
-qboolean trap_Cvar_Exists (const char *var_name);
-
 int				trap_Argc( void );
 void			trap_Argv( int n, char *buffer, int bufferLength );
 void			trap_Cmd_ExecuteText( int exec_when, const char *text );	// don't use EXEC_NOW!
@@ -997,14 +995,11 @@
 e_status		trap_CIN_RunCinematic (int handle);
 void			trap_CIN_DrawCinematic (int handle);
 void			trap_CIN_SetExtents (int handle, int x, int y, int w, int h);
-int				trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int				trap_RealTime(qtime_t *qtime);
 void			trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset );
 qboolean		trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 
 //
 // ui_addbots.c

```

### `openarena-engine`  — sha256 `e8d1d9945531...`, 30981 bytes

_Diff stat: +6 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_local.h	2026-04-16 20:02:25.817962300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_local.h	2026-04-16 22:48:25.959096900 +0100
@@ -28,7 +28,6 @@
 #include "ui_public.h"
 #include "../client/keycodes.h"
 #include "../game/bg_public.h"
-#include "ui_common.h"
 #include "ui_shared.h"
 
 // global display context
@@ -144,6 +143,7 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			96
 
 #define MTYPE_NULL				0
 #define MTYPE_SLIDER			1	
@@ -258,7 +258,7 @@
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -359,7 +359,6 @@
 void UI_ShowPostGame(qboolean newHigh);
 void UI_ClearScores( void );
 void UI_LoadArenas(void);
-void UI_LoadArenasIntoMapList(void);
 
 //
 // ui_menu.c
@@ -534,9 +533,6 @@
 
 	animation_t		animations[MAX_TOTALANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
-
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
 	qhandle_t		flashModel;
@@ -611,7 +607,7 @@
 #define MAX_HEADNAME  32
 #define MAX_TEAMS 64
 #define MAX_GAMETYPES 16
-#define MAX_MAPS MAX_ARENAS
+#define MAX_MAPS 128
 #define MAX_SPMAPS 16
 #define PLAYERS_PER_TEAM 5
 #define MAX_PINGREQUESTS		32
@@ -634,7 +630,7 @@
 #define MAPS_PER_TIER 3
 #define MAX_TIERS 16
 #define MAX_MODS 64
-#define MAX_DEMOS 4096  //256
+#define MAX_DEMOS 512
 #define MAX_MOVIES 256
 #define MAX_PLAYERMODELS 256
 
@@ -918,7 +914,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error(const char *string) Q_NO_RETURN;
+void			trap_Error(const char *string) __attribute__((noreturn));
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -929,8 +925,6 @@
 void			trap_Cvar_Reset( const char *name );
 void			trap_Cvar_Create( const char *var_name, const char *var_value, int flags );
 void			trap_Cvar_InfoStringBuffer( int bit, char *buffer, int bufsize );
-qboolean trap_Cvar_Exists (const char *var_name);
-
 int				trap_Argc( void );
 void			trap_Argv( int n, char *buffer, int bufferLength );
 void			trap_Cmd_ExecuteText( int exec_when, const char *text );	// don't use EXEC_NOW!
@@ -997,14 +991,11 @@
 e_status		trap_CIN_RunCinematic (int handle);
 void			trap_CIN_DrawCinematic (int handle);
 void			trap_CIN_SetExtents (int handle, int x, int y, int w, int h);
-int				trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int				trap_RealTime(qtime_t *qtime);
 void			trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset );
 qboolean		trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 
 //
 // ui_addbots.c

```

### `openarena-gamecode`  — sha256 `190b38a066ba...`, 36533 bytes

_Diff stat: +290 / -120 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_local.h	2026-04-16 20:02:25.817962300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\ui\ui_local.h	2026-04-16 22:48:24.212592000 +0100
@@ -24,114 +24,176 @@
 #define __UI_LOCAL_H__
 
 #include "../qcommon/q_shared.h"
-#include "../renderercommon/tr_types.h"
+#include "../renderer/tr_types.h"
 #include "ui_public.h"
 #include "../client/keycodes.h"
 #include "../game/bg_public.h"
-#include "ui_common.h"
 #include "ui_shared.h"
 
 // global display context
 
-extern vmCvar_t	ui_ffa_fraglimit;
-extern vmCvar_t	ui_ffa_timelimit;
-
-extern vmCvar_t	ui_tourney_fraglimit;
-extern vmCvar_t	ui_tourney_timelimit;
-
-extern vmCvar_t	ui_team_fraglimit;
-extern vmCvar_t	ui_team_timelimit;
-extern vmCvar_t	ui_team_friendly;
-
-extern vmCvar_t	ui_ctf_capturelimit;
-extern vmCvar_t	ui_ctf_timelimit;
-extern vmCvar_t	ui_ctf_friendly;
-
-extern vmCvar_t	ui_arenasFile;
-extern vmCvar_t	ui_botsFile;
-extern vmCvar_t	ui_spScores1;
-extern vmCvar_t	ui_spScores2;
-extern vmCvar_t	ui_spScores3;
-extern vmCvar_t	ui_spScores4;
-extern vmCvar_t	ui_spScores5;
-extern vmCvar_t	ui_spAwards;
-extern vmCvar_t	ui_spVideos;
-extern vmCvar_t	ui_spSkill;
-
-extern vmCvar_t	ui_spSelection;
-
-extern vmCvar_t	ui_browserMaster;
-extern vmCvar_t	ui_browserGameType;
-extern vmCvar_t	ui_browserShowFull;
-extern vmCvar_t	ui_browserShowEmpty;
-
-extern vmCvar_t	ui_brassTime;
-extern vmCvar_t	ui_drawCrosshair;
-extern vmCvar_t	ui_drawCrosshairNames;
-extern vmCvar_t	ui_marks;
-
-extern vmCvar_t	ui_server1;
-extern vmCvar_t	ui_server2;
-extern vmCvar_t	ui_server3;
-extern vmCvar_t	ui_server4;
-extern vmCvar_t	ui_server5;
-extern vmCvar_t	ui_server6;
-extern vmCvar_t	ui_server7;
-extern vmCvar_t	ui_server8;
-extern vmCvar_t	ui_server9;
-extern vmCvar_t	ui_server10;
-extern vmCvar_t	ui_server11;
-extern vmCvar_t	ui_server12;
-extern vmCvar_t	ui_server13;
-extern vmCvar_t	ui_server14;
-extern vmCvar_t	ui_server15;
-extern vmCvar_t	ui_server16;
-
-extern vmCvar_t	ui_cdkey;
-extern vmCvar_t	ui_cdkeychecked;
-
-extern vmCvar_t	ui_captureLimit;
-extern vmCvar_t	ui_fragLimit;
-extern vmCvar_t	ui_gameType;
-extern vmCvar_t	ui_netGameType;
-extern vmCvar_t	ui_actualNetGameType;
-extern vmCvar_t	ui_joinGameType;
-extern vmCvar_t	ui_netSource;
-extern vmCvar_t	ui_serverFilterType;
-extern vmCvar_t	ui_dedicated;
-extern vmCvar_t	ui_opponentName;
-extern vmCvar_t	ui_menuFiles;
-extern vmCvar_t	ui_currentTier;
-extern vmCvar_t	ui_currentMap;
-extern vmCvar_t	ui_currentNetMap;
-extern vmCvar_t	ui_mapIndex;
-extern vmCvar_t	ui_currentOpponent;
-extern vmCvar_t	ui_selectedPlayer;
-extern vmCvar_t	ui_selectedPlayerName;
-extern vmCvar_t	ui_lastServerRefresh_0;
-extern vmCvar_t	ui_lastServerRefresh_1;
-extern vmCvar_t	ui_lastServerRefresh_2;
-extern vmCvar_t	ui_lastServerRefresh_3;
-extern vmCvar_t	ui_singlePlayerActive;
-extern vmCvar_t	ui_scoreAccuracy;
-extern vmCvar_t	ui_scoreImpressives;
-extern vmCvar_t	ui_scoreExcellents;
-extern vmCvar_t	ui_scoreDefends;
-extern vmCvar_t	ui_scoreAssists;
-extern vmCvar_t	ui_scoreGauntlets;
-extern vmCvar_t	ui_scoreScore;
-extern vmCvar_t	ui_scorePerfect;
-extern vmCvar_t	ui_scoreTeam;
-extern vmCvar_t	ui_scoreBase;
-extern vmCvar_t	ui_scoreTimeBonus;
-extern vmCvar_t	ui_scoreSkillBonus;
-extern vmCvar_t	ui_scoreShutoutBonus;
-extern vmCvar_t	ui_scoreTime;
-extern vmCvar_t	ui_smallFont;
-extern vmCvar_t	ui_bigFont;
+extern vmCvar_t ui_ffa_fraglimit;
+extern vmCvar_t ui_ffa_timelimit;
+extern vmCvar_t ui_tourney_fraglimit;
+extern vmCvar_t ui_tourney_timelimit;
+extern vmCvar_t ui_team_fraglimit;
+extern vmCvar_t ui_team_timelimit;
+extern vmCvar_t ui_team_friendly;
+extern vmCvar_t ui_ctf_capturelimit;
+extern vmCvar_t ui_ctf_timelimit;
+extern vmCvar_t ui_ctf_friendly;
+extern vmCvar_t ui_1fctf_capturelimit;
+extern vmCvar_t ui_1fctf_timelimit;
+extern vmCvar_t ui_1fctf_friendly;
+extern vmCvar_t ui_overload_capturelimit;
+extern vmCvar_t ui_overload_timelimit;
+extern vmCvar_t ui_overload_friendly;
+extern vmCvar_t ui_harvester_capturelimit;
+extern vmCvar_t ui_harvester_timelimit;
+extern vmCvar_t ui_harvester_friendly;
+extern vmCvar_t ui_elimination_capturelimit;
+extern vmCvar_t ui_elimination_timelimit;
+extern vmCvar_t ui_ctf_elimination_capturelimit;
+extern vmCvar_t ui_ctf_elimination_timelimit;
+extern vmCvar_t ui_lms_fraglimit;
+extern vmCvar_t ui_lms_timelimit;
+extern vmCvar_t ui_dd_capturelimit;
+extern vmCvar_t ui_dd_timelimit;
+extern vmCvar_t ui_dd_friendly;
+extern vmCvar_t ui_dom_capturelimit;
+extern vmCvar_t ui_dom_timelimit;
+extern vmCvar_t ui_dom_friendly;
+extern vmCvar_t ui_pos_scorelimit;
+extern vmCvar_t ui_pos_timelimit;
+extern vmCvar_t ui_arenasFile;
+extern vmCvar_t ui_botsFile;
+extern vmCvar_t ui_spScores1;
+extern vmCvar_t ui_spScores2;
+extern vmCvar_t ui_spScores3;
+extern vmCvar_t ui_spScores4;
+extern vmCvar_t ui_spScores5;
+extern vmCvar_t ui_spAwards;
+extern vmCvar_t ui_spVideos;
+extern vmCvar_t ui_spSkill;
+extern vmCvar_t ui_spSelection;
+extern vmCvar_t ui_browserMaster;
+extern vmCvar_t ui_browserGameType;
+extern vmCvar_t ui_browserSortKey;
+extern vmCvar_t ui_browserShowFull;
+extern vmCvar_t ui_browserShowEmpty;
+extern vmCvar_t ui_brassTime;
+extern vmCvar_t ui_drawCrosshair;
+extern vmCvar_t ui_drawCrosshairNames;
+extern vmCvar_t ui_marks;
+extern vmCvar_t ui_server1;
+extern vmCvar_t ui_server2;
+extern vmCvar_t ui_server3;
+extern vmCvar_t ui_server4;
+extern vmCvar_t ui_server5;
+extern vmCvar_t ui_server6;
+extern vmCvar_t ui_server7;
+extern vmCvar_t ui_server8;
+extern vmCvar_t ui_server9;
+extern vmCvar_t ui_server10;
+extern vmCvar_t ui_server11;
+extern vmCvar_t ui_server12;
+extern vmCvar_t ui_server13;
+extern vmCvar_t ui_server14;
+extern vmCvar_t ui_server15;
+extern vmCvar_t ui_server16;
+extern vmCvar_t ui_cdkey;
+extern vmCvar_t ui_cdkeychecked;
+extern vmCvar_t ui_captureLimit;
+extern vmCvar_t ui_fragLimit;
+extern vmCvar_t ui_gameType;
+extern vmCvar_t ui_netGameType;
+extern vmCvar_t ui_actualNetGameType;
+extern vmCvar_t ui_joinGameType;
+extern vmCvar_t ui_netSource;
+extern vmCvar_t ui_serverFilterType;
+extern vmCvar_t ui_dedicated;
+extern vmCvar_t ui_opponentName;
+extern vmCvar_t ui_menuFiles;
+extern vmCvar_t ui_introFiles;
+extern vmCvar_t ui_currentTier;
+extern vmCvar_t ui_currentMap;
+extern vmCvar_t ui_currentNetMap;
+extern vmCvar_t ui_mapIndex;
+extern vmCvar_t ui_currentOpponent;
+extern vmCvar_t ui_selectedPlayer;
+extern vmCvar_t ui_selectedPlayerName;
+extern vmCvar_t ui_lastServerRefresh_0;
+extern vmCvar_t ui_lastServerRefresh_1;
+extern vmCvar_t ui_lastServerRefresh_2;
+extern vmCvar_t ui_lastServerRefresh_3;
+extern vmCvar_t ui_singlePlayerActive;
+extern vmCvar_t ui_scoreAccuracy;
+extern vmCvar_t ui_scoreImpressives;
+extern vmCvar_t ui_scoreExcellents;
+extern vmCvar_t ui_scoreDefends;
+extern vmCvar_t ui_scoreAssists;
+extern vmCvar_t ui_scoreGauntlets;
+extern vmCvar_t ui_scoreScore;
+extern vmCvar_t ui_scorePerfect;
+extern vmCvar_t ui_scoreTeam;
+extern vmCvar_t ui_scoreBase;
+extern vmCvar_t ui_scoreTimeBonus;
+extern vmCvar_t ui_scoreSkillBonus;
+extern vmCvar_t ui_scoreShutoutBonus;
+extern vmCvar_t ui_scoreTime;
+extern vmCvar_t ui_smallFont;
+extern vmCvar_t ui_bigFont;
 extern vmCvar_t ui_serverStatusTimeOut;
-
-
+extern vmCvar_t ui_humansonly;
+extern vmCvar_t ui_introPlayed;
+extern vmCvar_t ui_colors;
+extern vmCvar_t ui_findPlayer;
+extern vmCvar_t ui_Q3Model;
+extern vmCvar_t ui_hudFiles;
+extern vmCvar_t ui_recordSPDemo;
+extern vmCvar_t ui_realCaptureLimit;
+extern vmCvar_t ui_realWarmUp;
+// Changed RD
+extern vmCvar_t ui_LowerAnim;
+extern vmCvar_t ui_UpperAnim;
+extern vmCvar_t ui_Weapon;
+extern vmCvar_t ui_PlayerViewAngleYaw;
+extern vmCvar_t ui_PlayerViewAnglePitch;
+extern vmCvar_t ui_PlayerMoveAngleYaw;
+extern vmCvar_t ui_PlayerMoveAnglePitch;
+extern vmCvar_t ui_SaveGame;
+extern vmCvar_t ui_LoadGame;
+extern vmCvar_t ui_CustomServer;
+extern vmCvar_t ui_HostName;
+extern vmCvar_t ui_SpecialGame;
+extern vmCvar_t ui_TeamMembers;
+extern vmCvar_t ui_loading;
+extern vmCvar_t ui_transitionkey;
+extern vmCvar_t ui_applychanges;
+extern vmCvar_t Save_Loading;
+extern vmCvar_t persid;
+extern vmCvar_t gameover; // ai script
+// end changed RD
+// leilei
+extern vmCvar_t ui_new;
+extern vmCvar_t ui_leidebug;
+extern vmCvar_t ui_debug;
+extern vmCvar_t ui_initialized;
+extern vmCvar_t ui_teamArenaFirstRun;
+extern vmCvar_t ui_redteam;
+extern vmCvar_t ui_redteam1;
+extern vmCvar_t ui_redteam2;
+extern vmCvar_t ui_redteam3;
+extern vmCvar_t ui_redteam4;
+extern vmCvar_t ui_redteam5;
+extern vmCvar_t ui_blueteam;
+extern vmCvar_t ui_blueteam1;
+extern vmCvar_t ui_blueteam2;
+extern vmCvar_t ui_blueteam3;
+extern vmCvar_t ui_blueteam4;
+extern vmCvar_t ui_blueteam5;
+extern vmCvar_t ui_teamName;
+extern vmCvar_t ui_developer;
 
 //
 // ui_qmenu.c
@@ -144,6 +206,7 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			256	// was 96 - rfactory change
 
 #define MTYPE_NULL				0
 #define MTYPE_SLIDER			1	
@@ -258,7 +321,7 @@
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -359,7 +422,10 @@
 void UI_ShowPostGame(qboolean newHigh);
 void UI_ClearScores( void );
 void UI_LoadArenas(void);
-void UI_LoadArenasIntoMapList(void);
+// rfactory change
+// Changed RD
+qboolean SP_LoadGame(char *load_game, char *loadmap);
+// end changed RD
 
 //
 // ui_menu.c
@@ -519,6 +585,17 @@
 	int			animationTime;		// time when the first frame of the animation will be exact
 } lerpFrame_t;
 
+
+// leilei - OC parts!
+typedef struct {
+
+	qhandle_t		m;			// model to use
+	char 			modelname[MAX_QPATH];	// path to model to use
+
+	vec3_t			col;			// color to use
+
+} ocpart_t;
+
 typedef struct {
 	// model info
 	qhandle_t		legsModel;
@@ -533,9 +610,8 @@
 	qhandle_t		headSkin;
 
 	animation_t		animations[MAX_TOTALANIMATIONS];
-
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
+	qboolean		fixedlegs;		// true if legs yaw is always the same as torso yaw
+	qboolean		fixedtorso;		// true if torso never changes yaw
 
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
@@ -569,9 +645,71 @@
 	int				barrelTime;
 
 	int				realWeapon;
+
+
+	// leilei - oc experiment
+		// Head
+	ocpart_t		oc_hairBack;	// Hair etc
+	ocpart_t		oc_hairFront;	// Locks etc
+	ocpart_t		oc_Hat;		// Hats etc
+	ocpart_t		oc_Ears;		// Ears etc
+	ocpart_t		oc_Face;		// Different shapes of faces
+	ocpart_t		oc_Glasses;	// Glasses, eypatches, etc
+		// Torso
+	ocpart_t		oc_Back;		// could be for cape, wings etc
+	ocpart_t		oc_Clothes;	// might be too synonymous with torso
+	ocpart_t		oc_Shoulder;	// pads
+	ocpart_t		oc_Arm;		// Blades and stuff like that
+
+		// Legs
+	ocpart_t		oc_Shoe;
+	ocpart_t		oc_Pants;
+	ocpart_t		oc_Skirt;
+	ocpart_t		oc_Tail;
+
+	// Colors
+
+	int 	shirtcolor1;
+	int 	shirtcolor2;
+
+	int 	pantscolor1;
+	int 	pantscolor2;
+
+	int 	haircolor1;
+	int 	haircolor2;
+
+	int 	skincolor;
+
+	qhandle_t		skinSkin;	// for race skin
+	qhandle_t		eyeSkin;	// for head's eye skin
+	qhandle_t		underSkin;	// for undergarment/swimsuit alpha shell skin
+	// leilei - oc experiment
+
+	vec3_t			eyepos;		// where our eyes at
+	vec3_t			eyelookat;	// what we seein'
+	lerpFrame_t		head;
+
+	// status bar head
+	float		headYaw;
+	float		headEndPitch;
+	float		headEndRoll;
+	float		headEndYaw;
+	int			headEndTime;
+	float		headStartPitch;
+	float		torsoStartPitch;
+	float		torsoStartYaw;
+	float		torsoEndPitch;
+	float		torsoEndYaw;
+	float		headStartRoll;
+	float		headStartYaw;
+	int			headStartTime;
+
 } playerInfo_t;
 
 void UI_DrawPlayer( float x, float y, float w, float h, playerInfo_t *pi, int time );
+void UI_DrawPlayerII( float x, float y, float w, float h, playerInfo_t *pi, int time );
+void UI_DrawPlayerOC( float x, float y, float w, float h, playerInfo_t *pi, int time );
+void UI_DrawPlayersBust( float x, float y, float w, float h, playerInfo_t *pi, int time );
 void UI_PlayerInfo_SetModel( playerInfo_t *pi, const char *model, const char *headmodel, char *teamName );
 void UI_PlayerInfo_SetInfo( playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNum, qboolean chat );
 qboolean UI_RegisterClientModelname( playerInfo_t *pi, const char *modelSkinName , const char *headName, const char *teamName);
@@ -579,7 +717,7 @@
 //
 // ui_atoms.c
 //
-// this is only used in the old ui, the new ui has its own version
+// this is only used in the old ui, the new ui has it's own version
 typedef struct {
 	int					frametime;
 	int					realtime;
@@ -589,6 +727,7 @@
 	qboolean		debug;
 	qhandle_t		whiteShader;
 	qhandle_t		menuBackShader;
+	qhandle_t		menuBackShader2;
 	qhandle_t		menuBackNoLogoShader;
 	qhandle_t		charset;
 	qhandle_t		charsetProp;
@@ -611,8 +750,8 @@
 #define MAX_HEADNAME  32
 #define MAX_TEAMS 64
 #define MAX_GAMETYPES 16
-#define MAX_MAPS MAX_ARENAS
-#define MAX_SPMAPS 16
+#define MAX_MAPS 4096	// leilei - was 128
+#define MAX_SPMAPS 45
 #define PLAYERS_PER_TEAM 5
 #define MAX_PINGREQUESTS		32
 #define MAX_ADDRESSLENGTH		64
@@ -633,10 +772,17 @@
 #define GAMES_CTF			4
 #define MAPS_PER_TIER 3
 #define MAX_TIERS 16
-#define MAX_MODS 64
-#define MAX_DEMOS 4096  //256
+#define MAX_MODS 128
+#define MAX_DEMOS 512
 #define MAX_MOVIES 256
-#define MAX_PLAYERMODELS 256
+//#define MAX_PLAYERMODELS 256
+#define MAX_PLAYERMODELS 1024
+
+// rfactory change
+// Changed RD
+#define MAX_SAVEGAMES 16
+// end changed RD
+
 
 
 typedef struct {
@@ -674,6 +820,12 @@
   const char *mapLoadName;
 	const char *imageName;
 	const char *opponentName;
+// rfactory 
+// Changed RD
+	const char *botName;
+	const char *special;
+	int fraglimit;
+// end changed RD
 	int teamMembers;
   int typeBits;
 	int cinematic;
@@ -782,6 +934,12 @@
 	int numJoinGameTypes;
 	gameTypeInfo joinGameTypes[MAX_GAMETYPES];
 
+	// rfactory change
+	// Changed RD
+	int maskGameTypes[MAX_GAMETYPES];
+	qboolean dorefresh;
+	// end changed RD
+
 	int redBlue;
 	int playerCount;
 	int myTeamCount;
@@ -811,6 +969,13 @@
 	int demoCount;
 	int demoIndex;
 
+// rfactory 
+// Changed RD
+	const char *saveList[MAX_SAVEGAMES];
+	int saveCount;
+	int saveIndex;
+// end changed RD
+
 	const char *movieList[MAX_MOVIES];
 	int movieCount;
 	int movieIndex;
@@ -839,12 +1004,20 @@
 	int				q3HeadCount;
 	char			q3HeadNames[MAX_PLAYERMODELS][64];
 	qhandle_t	q3HeadIcons[MAX_PLAYERMODELS];
+	qhandle_t	q3HeadIcons2[MAX_PLAYERMODELS];
+	qhandle_t	q3Portraits[MAX_PLAYERMODELS];	// leilei - displaying portraits with deferred loading for some screens
 	int				q3SelectedHead;
 
 	int effectsColor;
 
 	qboolean inGameLoad;
 
+// rfactory change
+// Changed RD
+	playerInfo_t info;
+// end changed RD
+	int				q3HeadCount2;		// leilei - a complete list for the text list. for saving vram
+	char			q3HeadNames2[MAX_PLAYERMODELS][64];
 }	uiInfo_t;
 
 extern uiInfo_t uiInfo;
@@ -918,7 +1091,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error(const char *string) Q_NO_RETURN;
+void			trap_Error( const char *string ) __attribute__((noreturn));
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -929,8 +1102,6 @@
 void			trap_Cvar_Reset( const char *name );
 void			trap_Cvar_Create( const char *var_name, const char *var_value, int flags );
 void			trap_Cvar_InfoStringBuffer( int bit, char *buffer, int bufsize );
-qboolean trap_Cvar_Exists (const char *var_name);
-
 int				trap_Argc( void );
 void			trap_Argv( int n, char *buffer, int bufferLength );
 void			trap_Cmd_ExecuteText( int exec_when, const char *text );	// don't use EXEC_NOW!
@@ -997,14 +1168,11 @@
 e_status		trap_CIN_RunCinematic (int handle);
 void			trap_CIN_DrawCinematic (int handle);
 void			trap_CIN_SetExtents (int handle, int x, int y, int w, int h);
-int				trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int				trap_RealTime(qtime_t *qtime);
 void			trap_R_RemapShader( const char *oldShader, const char *newShader, const char *timeOffset );
 qboolean		trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
 
 //
 // ui_addbots.c
@@ -1112,12 +1280,13 @@
 //
 void RankStatus_Cache( void );
 void UI_RankStatusMenu( void );
-
+// leilei - wide hack
+extern int wideAdjustX;
 
 // new ui 
 
 #define ASSET_BACKGROUND "uiBackground"
-
+void RefreshHexColors( void );
 // for tracking sp game info in Team Arena
 typedef struct postGameInfo_s {
 	int score;
@@ -1141,3 +1310,4 @@
 
 
 #endif
+

```
