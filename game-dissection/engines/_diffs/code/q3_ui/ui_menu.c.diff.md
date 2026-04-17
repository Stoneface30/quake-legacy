# Diff: `code/q3_ui/ui_menu.c`
**Canonical:** `wolfcamql-src` (sha256 `ace4dcd8fff9...`, 15048 bytes)

## Variants

### `quake3-source`  — sha256 `15ac810ad213...`, 11358 bytes

_Diff stat: +75 / -178 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_menu.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_menu.c	2026-04-16 20:02:19.948079200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -40,13 +40,9 @@
 #define ID_TEAMARENA		15
 #define ID_MODS					16
 #define ID_EXIT					17
-#define ID_QLDEMOS 18
-#define ID_COPYQLPAKS 19
-#define ID_OPEN_QUAKE_LIVE_DIRECTORY 20
-#define ID_OPEN_WOLFCAM_DIRECTORY 21
 
-//#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
-#define MAIN_MENU_VERTICAL_SPACING		24  //34
+#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
+#define MAIN_MENU_VERTICAL_SPACING		34
 
 
 typedef struct {
@@ -56,13 +52,9 @@
 	menutext_s		multiplayer;
 	menutext_s		setup;
 	menutext_s		demos;
-	menutext_s qldemos;
 	menutext_s		cinematics;
 	menutext_s		teamArena;
 	menutext_s		mods;
-	//menutext_s copyQlPaks;
-	menutext_s openQuakeLiveDirectory;
-	menutext_s openWolfcamDirectory;
 	menutext_s		exit;
 
 	qhandle_t		bannerModel;
@@ -72,13 +64,12 @@
 static mainmenu_t s_main;
 
 typedef struct {
-	menuframework_s menu;
+	menuframework_s menu;	
 	char errorMessage[4096];
 } errorMessage_t;
 
 static errorMessage_t s_errorMessage;
 
-#if 0
 /*
 =================
 MainMenu_ExitAction
@@ -90,9 +81,8 @@
 	}
 	UI_PopMenu();
 	UI_CreditMenu();
-	//trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
 }
-#endif
+
 
 
 /*
@@ -119,11 +109,7 @@
 		break;
 
 	case ID_DEMOS:
-		UI_DemosMenu(qfalse, NULL);
-		break;
-
-	case ID_QLDEMOS:
-		UI_DemosMenu(qtrue, NULL);
+		UI_DemosMenu();
 		break;
 
 	case ID_CINEMATICS:
@@ -135,21 +121,12 @@
 		break;
 
 	case ID_TEAMARENA:
-		trap_Cvar_Set( "fs_game", BASETA);
+		trap_Cvar_Set( "fs_game", "missionpack");
 		trap_Cmd_ExecuteText( EXEC_APPEND, "vid_restart;" );
 		break;
 
-	case ID_OPEN_QUAKE_LIVE_DIRECTORY:
-		trap_OpenQuakeLiveDirectory();
-		break;
-
-	case ID_OPEN_WOLFCAM_DIRECTORY:
-		trap_OpenWolfcamDirectory();
-		break;
-
 	case ID_EXIT:
-		//UI_ConfirmMenu( "EXIT GAME?", 0, MainMenu_ExitAction );
-		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
+		UI_ConfirmMenu( "EXIT GAME?", NULL, MainMenu_ExitAction );
 		break;
 	}
 }
@@ -161,7 +138,7 @@
 ===============
 */
 void MainMenu_Cache( void ) {
-	//s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
+	s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
 }
 
 sfxHandle_t ErrorMessage_Key(int key)
@@ -180,13 +157,12 @@
 
 static void Main_MenuDraw( void ) {
 	refdef_t		refdef;
-	//refEntity_t		ent;
-	//vec3_t			origin;
-	//vec3_t			angles;
+	refEntity_t		ent;
+	vec3_t			origin;
+	vec3_t			angles;
 	float			adjust;
 	float			x, y, w, h;
-	vec4_t			color = {1, 1, 1, 1};
-	int sy;
+	vec4_t			color = {0.5, 0, 0, 1};
 
 	// setup the refdef
 
@@ -212,13 +188,12 @@
 
 	refdef.time = uis.realtime;
 
-	//origin[0] = 300;
-	//origin[1] = 0;
-	//origin[2] = -32;
+	origin[0] = 300;
+	origin[1] = 0;
+	origin[2] = -32;
 
 	trap_R_ClearScene();
 
-#if 0
 	// add the model
 
 	memset( &ent, 0, sizeof(ent) );
@@ -232,24 +207,10 @@
 	ent.renderfx = RF_LIGHTING_ORIGIN | RF_NOSHADOW;
 	VectorCopy( ent.origin, ent.oldorigin );
 
-	//trap_R_AddRefEntityToScene( &ent );
-#endif
-	trap_R_RenderScene( &refdef );
-
-	//UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
-	if (uis.showErrorMenu) {
-		//UI_DrawProportionalString(0, 0, "You need to copy quakelive's baseq3 directory into ", UI_SMALLFONT, color);
-		sy = 0;
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  Installation is incomplete.", UI_SMALLFONT, color);
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  You need to copy the files in quakelive's baseq3 directory", UI_SMALLFONT, color);
-		sy += SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  (the files ending with .pk3) into wolfcam's baseq3 directory.", UI_SMALLFONT, color);
-		//return;
-	}
-
+	trap_R_AddRefEntityToScene( &ent );
 
+	trap_R_RenderScene( &refdef );
+	
 	if (strlen(s_errorMessage.errorMessage))
 	{
 		UI_DrawProportionalString_AutoWrapped( 320, 192, 600, 20, s_errorMessage.errorMessage, UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
@@ -257,17 +218,15 @@
 	else
 	{
 		// standard menu drawing
-		Menu_Draw( &s_main.menu );
+		Menu_Draw( &s_main.menu );		
 	}
 
-#if 0
 	if (uis.demoversion) {
 		UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
 		UI_DrawString( 320, 400, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
 	} else {
 		UI_DrawString( 320, 450, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
 	}
-#endif
 }
 
 
@@ -289,7 +248,7 @@
 	for( i = 0; i < numdirs; i++ ) {
 		dirlen = strlen( dirptr ) + 1;
     descptr = dirptr + dirlen;
-		if (Q_stricmp(dirptr, BASETA) == 0) {
+		if (Q_stricmp(dirptr, "missionpack") == 0) {
 			return qtrue;
 		}
     dirptr += dirlen + strlen(descptr) + 1;
@@ -310,14 +269,11 @@
 void UI_MainMenu( void ) {
 	int		y;
 	qboolean teamArena = qfalse;
-	int		style = UI_CENTER | UI_DROPSHADOW | UI_SMALLFONT;
-	int type;
-	char lastDemoDirBuffer[MAX_OSPATH];
+	int		style = UI_CENTER | UI_DROPSHADOW;
 
 	trap_Cvar_Set( "sv_killserver", "1" );
 
-#if 0
-	if (0) {  //( !uis.demoversion && !ui_cdkeychecked.integer ) {
+	if( !uis.demoversion && !ui_cdkeychecked.integer ) {
 		char	key[17];
 
 		trap_GetCDKey( key, sizeof(key) );
@@ -326,197 +282,138 @@
 			return;
 		}
 	}
-#endif
-
+	
 	memset( &s_main, 0 ,sizeof(mainmenu_t) );
 	memset( &s_errorMessage, 0 ,sizeof(errorMessage_t) );
 
 	// com_errorMessage would need that too
 	MainMenu_Cache();
-
+	
 	trap_Cvar_VariableStringBuffer( "com_errorMessage", s_errorMessage.errorMessage, sizeof(s_errorMessage.errorMessage) );
 	if (strlen(s_errorMessage.errorMessage))
-	{
+	{	
 		s_errorMessage.menu.draw = Main_MenuDraw;
 		s_errorMessage.menu.key = ErrorMessage_Key;
 		s_errorMessage.menu.fullscreen = qtrue;
 		s_errorMessage.menu.wrapAround = qtrue;
-		s_errorMessage.menu.showlogo = qtrue;
+		s_errorMessage.menu.showlogo = qtrue;		
 
 		trap_Key_SetCatcher( KEYCATCH_UI );
 		uis.menusp = 0;
 		UI_PushMenu ( &s_errorMessage.menu );
-
+		
 		return;
 	}
 
 	s_main.menu.draw = Main_MenuDraw;
 	s_main.menu.fullscreen = qtrue;
 	s_main.menu.wrapAround = qtrue;
-	s_main.menu.showlogo = qfalse;  //qtrue;
-
-	type = MTYPE_PTEXT;  //MTYPE_TEXT;  // MTYPE_PTEXT
+	s_main.menu.showlogo = qtrue;
 
 	y = 134;
-	s_main.singleplayer.generic.type		= type;
+	s_main.singleplayer.generic.type		= MTYPE_PTEXT;
 	s_main.singleplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.singleplayer.generic.x			= 320;
 	s_main.singleplayer.generic.y			= y;
 	s_main.singleplayer.generic.id			= ID_SINGLEPLAYER;
-	s_main.singleplayer.generic.callback	= Main_MenuEvent;
+	s_main.singleplayer.generic.callback	= Main_MenuEvent; 
 	s_main.singleplayer.string				= "SINGLE PLAYER";
 	s_main.singleplayer.color				= color_red;
 	s_main.singleplayer.style				= style;
 
-	//y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.multiplayer.generic.type			= type;
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.multiplayer.generic.type			= MTYPE_PTEXT;
 	s_main.multiplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.multiplayer.generic.x			= 320;
 	s_main.multiplayer.generic.y			= y;
 	s_main.multiplayer.generic.id			= ID_MULTIPLAYER;
-	s_main.multiplayer.generic.callback		= Main_MenuEvent;
+	s_main.multiplayer.generic.callback		= Main_MenuEvent; 
 	s_main.multiplayer.string				= "MULTIPLAYER";
 	s_main.multiplayer.color				= color_red;
 	s_main.multiplayer.style				= style;
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.demos.generic.type				= type;
+	s_main.setup.generic.type				= MTYPE_PTEXT;
+	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.setup.generic.x					= 320;
+	s_main.setup.generic.y					= y;
+	s_main.setup.generic.id					= ID_SETUP;
+	s_main.setup.generic.callback			= Main_MenuEvent; 
+	s_main.setup.string						= "SETUP";
+	s_main.setup.color						= color_red;
+	s_main.setup.style						= style;
+
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.demos.generic.type				= MTYPE_PTEXT;
 	s_main.demos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.demos.generic.x					= 320;
 	s_main.demos.generic.y					= y;
 	s_main.demos.generic.id					= ID_DEMOS;
-	s_main.demos.generic.callback			= Main_MenuEvent;
-	s_main.demos.string						= "WOLFCAM-DEMOS";
+	s_main.demos.generic.callback			= Main_MenuEvent; 
+	s_main.demos.string						= "DEMOS";
 	s_main.demos.color						= color_red;
 	s_main.demos.style						= style;
 
-#if 1
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.qldemos.generic.type				= type;
-	s_main.qldemos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.qldemos.generic.x					= 320;
-	s_main.qldemos.generic.y					= y;
-	s_main.qldemos.generic.id					= ID_QLDEMOS;
-	s_main.qldemos.generic.callback			= Main_MenuEvent;
-	s_main.qldemos.string						= "QUAKELIVE-DEMOS";
-	s_main.qldemos.color						= color_red;
-	s_main.qldemos.style						= style;
-#endif
-
-#if 0
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.cinematics.generic.type			= type;
+	s_main.cinematics.generic.type			= MTYPE_PTEXT;
 	s_main.cinematics.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.cinematics.generic.x				= 320;
 	s_main.cinematics.generic.y				= y;
 	s_main.cinematics.generic.id			= ID_CINEMATICS;
-	s_main.cinematics.generic.callback		= Main_MenuEvent;
+	s_main.cinematics.generic.callback		= Main_MenuEvent; 
 	s_main.cinematics.string				= "CINEMATICS";
 	s_main.cinematics.color					= color_red;
 	s_main.cinematics.style					= style;
-#endif
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.setup.generic.type				= type;
-	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.setup.generic.x					= 320;
-	s_main.setup.generic.y					= y;
-	s_main.setup.generic.id					= ID_SETUP;
-	s_main.setup.generic.callback			= Main_MenuEvent;
-	s_main.setup.string						= "SETUP";
-	s_main.setup.color						= color_red;
-	s_main.setup.style						= style;
 
-
-	if ( !uis.demoversion && UI_TeamArenaExists() ) {
+	if (UI_TeamArenaExists()) {
 		teamArena = qtrue;
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.teamArena.generic.type			= type;
+		y += MAIN_MENU_VERTICAL_SPACING;
+		s_main.teamArena.generic.type			= MTYPE_PTEXT;
 		s_main.teamArena.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 		s_main.teamArena.generic.x				= 320;
 		s_main.teamArena.generic.y				= y;
 		s_main.teamArena.generic.id				= ID_TEAMARENA;
-		s_main.teamArena.generic.callback		= Main_MenuEvent;
+		s_main.teamArena.generic.callback		= Main_MenuEvent; 
 		s_main.teamArena.string					= "TEAM ARENA";
 		s_main.teamArena.color					= color_red;
 		s_main.teamArena.style					= style;
 	}
 
-	if ( !uis.demoversion ) {
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.mods.generic.type			= type;
-		s_main.mods.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-		s_main.mods.generic.x				= 320;
-		s_main.mods.generic.y				= y;
-		s_main.mods.generic.id				= ID_MODS;
-		s_main.mods.generic.callback		= Main_MenuEvent;
-		s_main.mods.string					= "MODS";
-		s_main.mods.color					= color_red;
-		s_main.mods.style					= style;
-	}
-
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openQuakeLiveDirectory.generic.type				= type;
-	s_main.openQuakeLiveDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openQuakeLiveDirectory.generic.x					= 320;
-	s_main.openQuakeLiveDirectory.generic.y					= y;
-	s_main.openQuakeLiveDirectory.generic.id					= ID_OPEN_QUAKE_LIVE_DIRECTORY;
-	s_main.openQuakeLiveDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openQuakeLiveDirectory.string						= "OPEN QUAKE LIVE DIRECTORY";
-	s_main.openQuakeLiveDirectory.color						= color_red;
-	s_main.openQuakeLiveDirectory.style						= style;
+	s_main.mods.generic.type			= MTYPE_PTEXT;
+	s_main.mods.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.mods.generic.x				= 320;
+	s_main.mods.generic.y				= y;
+	s_main.mods.generic.id				= ID_MODS;
+	s_main.mods.generic.callback		= Main_MenuEvent; 
+	s_main.mods.string					= "MODS";
+	s_main.mods.color					= color_red;
+	s_main.mods.style					= style;
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openWolfcamDirectory.generic.type				= type;
-	s_main.openWolfcamDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openWolfcamDirectory.generic.x					= 320;
-	s_main.openWolfcamDirectory.generic.y					= y;
-	s_main.openWolfcamDirectory.generic.id					= ID_OPEN_WOLFCAM_DIRECTORY;
-	s_main.openWolfcamDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openWolfcamDirectory.string						= "OPEN WOLFCAM DIRECTORY";
-	s_main.openWolfcamDirectory.color						= color_red;
-	s_main.openWolfcamDirectory.style						= style;
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.exit.generic.type				= type;
+	s_main.exit.generic.type				= MTYPE_PTEXT;
 	s_main.exit.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.exit.generic.x					= 320;
 	s_main.exit.generic.y					= y;
 	s_main.exit.generic.id					= ID_EXIT;
-	s_main.exit.generic.callback			= Main_MenuEvent;
+	s_main.exit.generic.callback			= Main_MenuEvent; 
 	s_main.exit.string						= "EXIT";
 	s_main.exit.color						= color_red;
 	s_main.exit.style						= style;
 
-	//Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
-	//Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
-
-	if (!uis.showErrorMenu) {
-		Menu_AddItem( &s_main.menu,	&s_main.demos );
-		Menu_AddItem(&s_main.menu, &s_main.qldemos);
-		//Menu_AddItem( &s_main.menu,	&s_main.cinematics );
-		if (teamArena) {
-			//Menu_AddItem( &s_main.menu,	&s_main.teamArena );
-		}
-		if ( !uis.demoversion ) {
-			//Menu_AddItem( &s_main.menu,	&s_main.mods );
-		}
-		Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.demos );
+	Menu_AddItem( &s_main.menu,	&s_main.cinematics );
+	if (teamArena) {
+		Menu_AddItem( &s_main.menu,	&s_main.teamArena );
 	}
-
-	Menu_AddItem(&s_main.menu, &s_main.openQuakeLiveDirectory);
-	Menu_AddItem(&s_main.menu, &s_main.openWolfcamDirectory);
-	Menu_AddItem( &s_main.menu,	&s_main.exit );
+	Menu_AddItem( &s_main.menu,	&s_main.mods );
+	Menu_AddItem( &s_main.menu,	&s_main.exit );             
 
 	trap_Key_SetCatcher( KEYCATCH_UI );
 	uis.menusp = 0;
 	UI_PushMenu ( &s_main.menu );
-
-	if (ui_demoStayInFolder.integer) {
-		lastDemoDirBuffer[0] = '\0';
-		trap_Cvar_VariableStringBuffer("lastdemodir", lastDemoDirBuffer, sizeof(lastDemoDirBuffer));
-		if (lastDemoDirBuffer[0]) {
-			UI_DemosMenu(qfalse, lastDemoDirBuffer);
-		}
-	}
+		
 }

```

### `openarena-engine`  — sha256 `8e772c52ff00...`, 11459 bytes
Also identical in: ioquake3

_Diff stat: +67 / -166 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_menu.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_menu.c	2026-04-16 22:48:25.896194800 +0100
@@ -40,13 +40,9 @@
 #define ID_TEAMARENA		15
 #define ID_MODS					16
 #define ID_EXIT					17
-#define ID_QLDEMOS 18
-#define ID_COPYQLPAKS 19
-#define ID_OPEN_QUAKE_LIVE_DIRECTORY 20
-#define ID_OPEN_WOLFCAM_DIRECTORY 21
 
-//#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
-#define MAIN_MENU_VERTICAL_SPACING		24  //34
+#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
+#define MAIN_MENU_VERTICAL_SPACING		34
 
 
 typedef struct {
@@ -56,13 +52,9 @@
 	menutext_s		multiplayer;
 	menutext_s		setup;
 	menutext_s		demos;
-	menutext_s qldemos;
 	menutext_s		cinematics;
 	menutext_s		teamArena;
 	menutext_s		mods;
-	//menutext_s copyQlPaks;
-	menutext_s openQuakeLiveDirectory;
-	menutext_s openWolfcamDirectory;
 	menutext_s		exit;
 
 	qhandle_t		bannerModel;
@@ -72,13 +64,12 @@
 static mainmenu_t s_main;
 
 typedef struct {
-	menuframework_s menu;
+	menuframework_s menu;	
 	char errorMessage[4096];
 } errorMessage_t;
 
 static errorMessage_t s_errorMessage;
 
-#if 0
 /*
 =================
 MainMenu_ExitAction
@@ -90,9 +81,8 @@
 	}
 	UI_PopMenu();
 	UI_CreditMenu();
-	//trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
 }
-#endif
+
 
 
 /*
@@ -119,11 +109,7 @@
 		break;
 
 	case ID_DEMOS:
-		UI_DemosMenu(qfalse, NULL);
-		break;
-
-	case ID_QLDEMOS:
-		UI_DemosMenu(qtrue, NULL);
+		UI_DemosMenu();
 		break;
 
 	case ID_CINEMATICS:
@@ -139,17 +125,8 @@
 		trap_Cmd_ExecuteText( EXEC_APPEND, "vid_restart;" );
 		break;
 
-	case ID_OPEN_QUAKE_LIVE_DIRECTORY:
-		trap_OpenQuakeLiveDirectory();
-		break;
-
-	case ID_OPEN_WOLFCAM_DIRECTORY:
-		trap_OpenWolfcamDirectory();
-		break;
-
 	case ID_EXIT:
-		//UI_ConfirmMenu( "EXIT GAME?", 0, MainMenu_ExitAction );
-		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
+		UI_ConfirmMenu( "EXIT GAME?", 0, MainMenu_ExitAction );
 		break;
 	}
 }
@@ -161,7 +138,7 @@
 ===============
 */
 void MainMenu_Cache( void ) {
-	//s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
+	s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
 }
 
 sfxHandle_t ErrorMessage_Key(int key)
@@ -180,13 +157,12 @@
 
 static void Main_MenuDraw( void ) {
 	refdef_t		refdef;
-	//refEntity_t		ent;
-	//vec3_t			origin;
-	//vec3_t			angles;
+	refEntity_t		ent;
+	vec3_t			origin;
+	vec3_t			angles;
 	float			adjust;
 	float			x, y, w, h;
-	vec4_t			color = {1, 1, 1, 1};
-	int sy;
+	vec4_t			color = {0.5, 0, 0, 1};
 
 	// setup the refdef
 
@@ -212,13 +188,12 @@
 
 	refdef.time = uis.realtime;
 
-	//origin[0] = 300;
-	//origin[1] = 0;
-	//origin[2] = -32;
+	origin[0] = 300;
+	origin[1] = 0;
+	origin[2] = -32;
 
 	trap_R_ClearScene();
 
-#if 0
 	// add the model
 
 	memset( &ent, 0, sizeof(ent) );
@@ -232,24 +207,10 @@
 	ent.renderfx = RF_LIGHTING_ORIGIN | RF_NOSHADOW;
 	VectorCopy( ent.origin, ent.oldorigin );
 
-	//trap_R_AddRefEntityToScene( &ent );
-#endif
-	trap_R_RenderScene( &refdef );
-
-	//UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
-	if (uis.showErrorMenu) {
-		//UI_DrawProportionalString(0, 0, "You need to copy quakelive's baseq3 directory into ", UI_SMALLFONT, color);
-		sy = 0;
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  Installation is incomplete.", UI_SMALLFONT, color);
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  You need to copy the files in quakelive's baseq3 directory", UI_SMALLFONT, color);
-		sy += SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  (the files ending with .pk3) into wolfcam's baseq3 directory.", UI_SMALLFONT, color);
-		//return;
-	}
-
+	trap_R_AddRefEntityToScene( &ent );
 
+	trap_R_RenderScene( &refdef );
+	
 	if (strlen(s_errorMessage.errorMessage))
 	{
 		UI_DrawProportionalString_AutoWrapped( 320, 192, 600, 20, s_errorMessage.errorMessage, UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
@@ -257,17 +218,15 @@
 	else
 	{
 		// standard menu drawing
-		Menu_Draw( &s_main.menu );
+		Menu_Draw( &s_main.menu );		
 	}
 
-#if 0
 	if (uis.demoversion) {
 		UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
 		UI_DrawString( 320, 400, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
 	} else {
 		UI_DrawString( 320, 450, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
 	}
-#endif
 }
 
 
@@ -310,14 +269,11 @@
 void UI_MainMenu( void ) {
 	int		y;
 	qboolean teamArena = qfalse;
-	int		style = UI_CENTER | UI_DROPSHADOW | UI_SMALLFONT;
-	int type;
-	char lastDemoDirBuffer[MAX_OSPATH];
+	int		style = UI_CENTER | UI_DROPSHADOW;
 
 	trap_Cvar_Set( "sv_killserver", "1" );
 
-#if 0
-	if (0) {  //( !uis.demoversion && !ui_cdkeychecked.integer ) {
+	if( !uis.demoversion && !ui_cdkeychecked.integer ) {
 		char	key[17];
 
 		trap_GetCDKey( key, sizeof(key) );
@@ -326,197 +282,142 @@
 			return;
 		}
 	}
-#endif
-
+	
 	memset( &s_main, 0 ,sizeof(mainmenu_t) );
 	memset( &s_errorMessage, 0 ,sizeof(errorMessage_t) );
 
 	// com_errorMessage would need that too
 	MainMenu_Cache();
-
+	
 	trap_Cvar_VariableStringBuffer( "com_errorMessage", s_errorMessage.errorMessage, sizeof(s_errorMessage.errorMessage) );
 	if (strlen(s_errorMessage.errorMessage))
-	{
+	{	
 		s_errorMessage.menu.draw = Main_MenuDraw;
 		s_errorMessage.menu.key = ErrorMessage_Key;
 		s_errorMessage.menu.fullscreen = qtrue;
 		s_errorMessage.menu.wrapAround = qtrue;
-		s_errorMessage.menu.showlogo = qtrue;
+		s_errorMessage.menu.showlogo = qtrue;		
 
 		trap_Key_SetCatcher( KEYCATCH_UI );
 		uis.menusp = 0;
 		UI_PushMenu ( &s_errorMessage.menu );
-
+		
 		return;
 	}
 
 	s_main.menu.draw = Main_MenuDraw;
 	s_main.menu.fullscreen = qtrue;
 	s_main.menu.wrapAround = qtrue;
-	s_main.menu.showlogo = qfalse;  //qtrue;
-
-	type = MTYPE_PTEXT;  //MTYPE_TEXT;  // MTYPE_PTEXT
+	s_main.menu.showlogo = qtrue;
 
 	y = 134;
-	s_main.singleplayer.generic.type		= type;
+	s_main.singleplayer.generic.type		= MTYPE_PTEXT;
 	s_main.singleplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.singleplayer.generic.x			= 320;
 	s_main.singleplayer.generic.y			= y;
 	s_main.singleplayer.generic.id			= ID_SINGLEPLAYER;
-	s_main.singleplayer.generic.callback	= Main_MenuEvent;
+	s_main.singleplayer.generic.callback	= Main_MenuEvent; 
 	s_main.singleplayer.string				= "SINGLE PLAYER";
 	s_main.singleplayer.color				= color_red;
 	s_main.singleplayer.style				= style;
 
-	//y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.multiplayer.generic.type			= type;
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.multiplayer.generic.type			= MTYPE_PTEXT;
 	s_main.multiplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.multiplayer.generic.x			= 320;
 	s_main.multiplayer.generic.y			= y;
 	s_main.multiplayer.generic.id			= ID_MULTIPLAYER;
-	s_main.multiplayer.generic.callback		= Main_MenuEvent;
+	s_main.multiplayer.generic.callback		= Main_MenuEvent; 
 	s_main.multiplayer.string				= "MULTIPLAYER";
 	s_main.multiplayer.color				= color_red;
 	s_main.multiplayer.style				= style;
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.demos.generic.type				= type;
+	s_main.setup.generic.type				= MTYPE_PTEXT;
+	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.setup.generic.x					= 320;
+	s_main.setup.generic.y					= y;
+	s_main.setup.generic.id					= ID_SETUP;
+	s_main.setup.generic.callback			= Main_MenuEvent; 
+	s_main.setup.string						= "SETUP";
+	s_main.setup.color						= color_red;
+	s_main.setup.style						= style;
+
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.demos.generic.type				= MTYPE_PTEXT;
 	s_main.demos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.demos.generic.x					= 320;
 	s_main.demos.generic.y					= y;
 	s_main.demos.generic.id					= ID_DEMOS;
-	s_main.demos.generic.callback			= Main_MenuEvent;
-	s_main.demos.string						= "WOLFCAM-DEMOS";
+	s_main.demos.generic.callback			= Main_MenuEvent; 
+	s_main.demos.string						= "DEMOS";
 	s_main.demos.color						= color_red;
 	s_main.demos.style						= style;
 
-#if 1
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.qldemos.generic.type				= type;
-	s_main.qldemos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.qldemos.generic.x					= 320;
-	s_main.qldemos.generic.y					= y;
-	s_main.qldemos.generic.id					= ID_QLDEMOS;
-	s_main.qldemos.generic.callback			= Main_MenuEvent;
-	s_main.qldemos.string						= "QUAKELIVE-DEMOS";
-	s_main.qldemos.color						= color_red;
-	s_main.qldemos.style						= style;
-#endif
-
-#if 0
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.cinematics.generic.type			= type;
+	s_main.cinematics.generic.type			= MTYPE_PTEXT;
 	s_main.cinematics.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.cinematics.generic.x				= 320;
 	s_main.cinematics.generic.y				= y;
 	s_main.cinematics.generic.id			= ID_CINEMATICS;
-	s_main.cinematics.generic.callback		= Main_MenuEvent;
+	s_main.cinematics.generic.callback		= Main_MenuEvent; 
 	s_main.cinematics.string				= "CINEMATICS";
 	s_main.cinematics.color					= color_red;
 	s_main.cinematics.style					= style;
-#endif
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.setup.generic.type				= type;
-	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.setup.generic.x					= 320;
-	s_main.setup.generic.y					= y;
-	s_main.setup.generic.id					= ID_SETUP;
-	s_main.setup.generic.callback			= Main_MenuEvent;
-	s_main.setup.string						= "SETUP";
-	s_main.setup.color						= color_red;
-	s_main.setup.style						= style;
-
 
 	if ( !uis.demoversion && UI_TeamArenaExists() ) {
 		teamArena = qtrue;
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.teamArena.generic.type			= type;
+		y += MAIN_MENU_VERTICAL_SPACING;
+		s_main.teamArena.generic.type			= MTYPE_PTEXT;
 		s_main.teamArena.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 		s_main.teamArena.generic.x				= 320;
 		s_main.teamArena.generic.y				= y;
 		s_main.teamArena.generic.id				= ID_TEAMARENA;
-		s_main.teamArena.generic.callback		= Main_MenuEvent;
+		s_main.teamArena.generic.callback		= Main_MenuEvent; 
 		s_main.teamArena.string					= "TEAM ARENA";
 		s_main.teamArena.color					= color_red;
 		s_main.teamArena.style					= style;
 	}
 
 	if ( !uis.demoversion ) {
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.mods.generic.type			= type;
+		y += MAIN_MENU_VERTICAL_SPACING;
+		s_main.mods.generic.type			= MTYPE_PTEXT;
 		s_main.mods.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 		s_main.mods.generic.x				= 320;
 		s_main.mods.generic.y				= y;
 		s_main.mods.generic.id				= ID_MODS;
-		s_main.mods.generic.callback		= Main_MenuEvent;
+		s_main.mods.generic.callback		= Main_MenuEvent; 
 		s_main.mods.string					= "MODS";
 		s_main.mods.color					= color_red;
 		s_main.mods.style					= style;
 	}
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openQuakeLiveDirectory.generic.type				= type;
-	s_main.openQuakeLiveDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openQuakeLiveDirectory.generic.x					= 320;
-	s_main.openQuakeLiveDirectory.generic.y					= y;
-	s_main.openQuakeLiveDirectory.generic.id					= ID_OPEN_QUAKE_LIVE_DIRECTORY;
-	s_main.openQuakeLiveDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openQuakeLiveDirectory.string						= "OPEN QUAKE LIVE DIRECTORY";
-	s_main.openQuakeLiveDirectory.color						= color_red;
-	s_main.openQuakeLiveDirectory.style						= style;
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openWolfcamDirectory.generic.type				= type;
-	s_main.openWolfcamDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openWolfcamDirectory.generic.x					= 320;
-	s_main.openWolfcamDirectory.generic.y					= y;
-	s_main.openWolfcamDirectory.generic.id					= ID_OPEN_WOLFCAM_DIRECTORY;
-	s_main.openWolfcamDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openWolfcamDirectory.string						= "OPEN WOLFCAM DIRECTORY";
-	s_main.openWolfcamDirectory.color						= color_red;
-	s_main.openWolfcamDirectory.style						= style;
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.exit.generic.type				= type;
+	s_main.exit.generic.type				= MTYPE_PTEXT;
 	s_main.exit.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.exit.generic.x					= 320;
 	s_main.exit.generic.y					= y;
 	s_main.exit.generic.id					= ID_EXIT;
-	s_main.exit.generic.callback			= Main_MenuEvent;
+	s_main.exit.generic.callback			= Main_MenuEvent; 
 	s_main.exit.string						= "EXIT";
 	s_main.exit.color						= color_red;
 	s_main.exit.style						= style;
 
-	//Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
-	//Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
-
-	if (!uis.showErrorMenu) {
-		Menu_AddItem( &s_main.menu,	&s_main.demos );
-		Menu_AddItem(&s_main.menu, &s_main.qldemos);
-		//Menu_AddItem( &s_main.menu,	&s_main.cinematics );
-		if (teamArena) {
-			//Menu_AddItem( &s_main.menu,	&s_main.teamArena );
-		}
-		if ( !uis.demoversion ) {
-			//Menu_AddItem( &s_main.menu,	&s_main.mods );
-		}
-		Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.demos );
+	Menu_AddItem( &s_main.menu,	&s_main.cinematics );
+	if (teamArena) {
+		Menu_AddItem( &s_main.menu,	&s_main.teamArena );
 	}
-
-	Menu_AddItem(&s_main.menu, &s_main.openQuakeLiveDirectory);
-	Menu_AddItem(&s_main.menu, &s_main.openWolfcamDirectory);
-	Menu_AddItem( &s_main.menu,	&s_main.exit );
+	if ( !uis.demoversion ) {
+		Menu_AddItem( &s_main.menu,	&s_main.mods );
+	}
+	Menu_AddItem( &s_main.menu,	&s_main.exit );             
 
 	trap_Key_SetCatcher( KEYCATCH_UI );
 	uis.menusp = 0;
 	UI_PushMenu ( &s_main.menu );
-
-	if (ui_demoStayInFolder.integer) {
-		lastDemoDirBuffer[0] = '\0';
-		trap_Cvar_VariableStringBuffer("lastdemodir", lastDemoDirBuffer, sizeof(lastDemoDirBuffer));
-		if (lastDemoDirBuffer[0]) {
-			UI_DemosMenu(qfalse, lastDemoDirBuffer);
-		}
-	}
+		
 }

```

### `openarena-gamecode`  — sha256 `0b4018af962e...`, 12480 bytes

_Diff stat: +115 / -196 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_menu.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_menu.c	2026-04-16 22:48:24.183498100 +0100
@@ -30,23 +30,21 @@
 
 
 #include "ui_local.h"
+#include "../qcommon/oa_version.h"
 
 
 #define ID_SINGLEPLAYER			10
 #define ID_MULTIPLAYER			11
 #define ID_SETUP				12
 #define ID_DEMOS				13
-#define ID_CINEMATICS			14
+//#define ID_CINEMATICS			14
+#define ID_CHALLENGES                   14
 #define ID_TEAMARENA		15
 #define ID_MODS					16
 #define ID_EXIT					17
-#define ID_QLDEMOS 18
-#define ID_COPYQLPAKS 19
-#define ID_OPEN_QUAKE_LIVE_DIRECTORY 20
-#define ID_OPEN_WOLFCAM_DIRECTORY 21
 
-//#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
-#define MAIN_MENU_VERTICAL_SPACING		24  //34
+#define MAIN_BANNER_MODEL				"models/mapobjects/banner/banner5.md3"
+#define MAIN_MENU_VERTICAL_SPACING		34
 
 
 typedef struct {
@@ -56,13 +54,10 @@
 	menutext_s		multiplayer;
 	menutext_s		setup;
 	menutext_s		demos;
-	menutext_s qldemos;
-	menutext_s		cinematics;
+	//menutext_s		cinematics;
+	menutext_s              challenges;
 	menutext_s		teamArena;
 	menutext_s		mods;
-	//menutext_s copyQlPaks;
-	menutext_s openQuakeLiveDirectory;
-	menutext_s openWolfcamDirectory;
 	menutext_s		exit;
 
 	qhandle_t		bannerModel;
@@ -78,21 +73,20 @@
 
 static errorMessage_t s_errorMessage;
 
-#if 0
 /*
 =================
 MainMenu_ExitAction
 =================
 */
-static void MainMenu_ExitAction( qboolean result ) {
+/*static void MainMenu_ExitAction( qboolean result ) {
 	if( !result ) {
 		return;
 	}
 	UI_PopMenu();
-	UI_CreditMenu();
-	//trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
-}
-#endif
+	//UI_CreditMenu();
+        trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
+}*/
+
 
 
 /*
@@ -100,7 +94,8 @@
 Main_MenuEvent
 =================
 */
-void Main_MenuEvent (void* ptr, int event) {
+void Main_MenuEvent (void* ptr, int event)
+{
 	if( event != QM_ACTIVATED ) {
 		return;
 	}
@@ -111,7 +106,10 @@
 		break;
 
 	case ID_MULTIPLAYER:
-		UI_ArenaServersMenu();
+		if(ui_setupchecked.integer)
+			UI_ArenaServersMenu();
+		else
+			UI_FirstConnectMenu();
 		break;
 
 	case ID_SETUP:
@@ -119,15 +117,15 @@
 		break;
 
 	case ID_DEMOS:
-		UI_DemosMenu(qfalse, NULL);
+		UI_DemosMenu();
 		break;
 
-	case ID_QLDEMOS:
-		UI_DemosMenu(qtrue, NULL);
-		break;
-
-	case ID_CINEMATICS:
+	/*case ID_CINEMATICS:
 		UI_CinematicsMenu();
+		break;*/
+
+	case ID_CHALLENGES:
+		UI_Challenges();
 		break;
 
 	case ID_MODS:
@@ -135,21 +133,13 @@
 		break;
 
 	case ID_TEAMARENA:
-		trap_Cvar_Set( "fs_game", BASETA);
+		trap_Cvar_Set( "fs_game", "missionpack");
 		trap_Cmd_ExecuteText( EXEC_APPEND, "vid_restart;" );
 		break;
 
-	case ID_OPEN_QUAKE_LIVE_DIRECTORY:
-		trap_OpenQuakeLiveDirectory();
-		break;
-
-	case ID_OPEN_WOLFCAM_DIRECTORY:
-		trap_OpenWolfcamDirectory();
-		break;
-
 	case ID_EXIT:
 		//UI_ConfirmMenu( "EXIT GAME?", 0, MainMenu_ExitAction );
-		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
+		UI_CreditMenu();
 		break;
 	}
 }
@@ -160,8 +150,9 @@
 MainMenu_Cache
 ===============
 */
-void MainMenu_Cache( void ) {
-	//s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
+void MainMenu_Cache( void )
+{
+	s_main.bannerModel = trap_R_RegisterModel( MAIN_BANNER_MODEL );
 }
 
 sfxHandle_t ErrorMessage_Key(int key)
@@ -178,15 +169,15 @@
 ===============
 */
 
-static void Main_MenuDraw( void ) {
+static void Main_MenuDraw( void )
+{
 	refdef_t		refdef;
-	//refEntity_t		ent;
-	//vec3_t			origin;
-	//vec3_t			angles;
+	refEntity_t		ent;
+	vec3_t			origin;
+	vec3_t			angles;
 	float			adjust;
 	float			x, y, w, h;
-	vec4_t			color = {1, 1, 1, 1};
-	int sy;
+	vec4_t			color = {0.2, 0.2, 1.0, 1};
 
 	// setup the refdef
 
@@ -212,13 +203,12 @@
 
 	refdef.time = uis.realtime;
 
-	//origin[0] = 300;
-	//origin[1] = 0;
-	//origin[2] = -32;
+	origin[0] = 300;
+	origin[1] = 0;
+	origin[2] = -32;
 
 	trap_R_ClearScene();
 
-#if 0
 	// add the model
 
 	memset( &ent, 0, sizeof(ent) );
@@ -232,42 +222,29 @@
 	ent.renderfx = RF_LIGHTING_ORIGIN | RF_NOSHADOW;
 	VectorCopy( ent.origin, ent.oldorigin );
 
-	//trap_R_AddRefEntityToScene( &ent );
-#endif
-	trap_R_RenderScene( &refdef );
-
-	//UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
-	if (uis.showErrorMenu) {
-		//UI_DrawProportionalString(0, 0, "You need to copy quakelive's baseq3 directory into ", UI_SMALLFONT, color);
-		sy = 0;
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  Installation is incomplete.", UI_SMALLFONT, color);
-		sy += 2 * SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  You need to copy the files in quakelive's baseq3 directory", UI_SMALLFONT, color);
-		sy += SMALLCHAR_HEIGHT;
-		UI_DrawString(0, sy, "  (the files ending with .pk3) into wolfcam's baseq3 directory.", UI_SMALLFONT, color);
-		//return;
-	}
+	trap_R_AddRefEntityToScene( &ent );
 
+	trap_R_RenderScene( &refdef );
 
-	if (strlen(s_errorMessage.errorMessage))
-	{
+	if (strlen(s_errorMessage.errorMessage)) {
 		UI_DrawProportionalString_AutoWrapped( 320, 192, 600, 20, s_errorMessage.errorMessage, UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
 	}
-	else
-	{
+	else {
 		// standard menu drawing
 		Menu_Draw( &s_main.menu );
 	}
 
-#if 0
-	if (uis.demoversion) {
-		UI_DrawProportionalString( 320, 372, "DEMO      FOR MATURE AUDIENCES      DEMO", UI_CENTER|UI_SMALLFONT, color );
-		UI_DrawString( 320, 400, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
-	} else {
-		UI_DrawString( 320, 450, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color );
+	UI_DrawProportionalString( 320, 372, "", UI_CENTER|UI_SMALLFONT, color );
+	UI_DrawString( 320, 400, "OpenArena(c) 2005-2018 OpenArena Team", UI_CENTER|UI_SMALLFONT, color );
+	UI_DrawString( 320, 414, "OpenArena comes with ABSOLUTELY NO WARRANTY; this is free software", UI_CENTER|UI_SMALLFONT, color );
+	UI_DrawString( 320, 428, "and you are welcome to redistribute it under certain conditions;", UI_CENTER|UI_SMALLFONT, color );
+	UI_DrawString( 320, 444, "read COPYING for details.", UI_CENTER|UI_SMALLFONT, color );
+
+	//Draw version.
+	UI_DrawString( 640-40, 480-14, "^7" OA_VERSION, UI_SMALLFONT, color );
+	if ((int)trap_Cvar_VariableValue("protocol")!=OA_STD_PROTOCOL) {
+		UI_DrawString( 0, 480-14, va("^7Protocol: %i",(int)trap_Cvar_VariableValue("protocol")), UI_SMALLFONT, color);
 	}
-#endif
 }
 
 
@@ -276,11 +253,12 @@
 UI_TeamArenaExists
 ===============
 */
-static qboolean UI_TeamArenaExists( void ) {
+static qboolean UI_TeamArenaExists( void )
+{
 	int		numdirs;
 	char	dirlist[2048];
 	char	*dirptr;
-  char  *descptr;
+	char  *descptr;
 	int		i;
 	int		dirlen;
 
@@ -288,11 +266,11 @@
 	dirptr  = dirlist;
 	for( i = 0; i < numdirs; i++ ) {
 		dirlen = strlen( dirptr ) + 1;
-    descptr = dirptr + dirlen;
-		if (Q_stricmp(dirptr, BASETA) == 0) {
+		descptr = dirptr + dirlen;
+		if ( Q_strequal(dirptr, "missionpack") ) {
 			return qtrue;
 		}
-    dirptr += dirlen + strlen(descptr) + 1;
+		dirptr += dirlen + strlen(descptr) + 1;
 	}
 	return qfalse;
 }
@@ -307,26 +285,14 @@
 and that local cinematics are killed
 ===============
 */
-void UI_MainMenu( void ) {
+void UI_MainMenu( void )
+{
 	int		y;
 	qboolean teamArena = qfalse;
-	int		style = UI_CENTER | UI_DROPSHADOW | UI_SMALLFONT;
-	int type;
-	char lastDemoDirBuffer[MAX_OSPATH];
+	int		style = UI_CENTER | UI_DROPSHADOW;
 
 	trap_Cvar_Set( "sv_killserver", "1" );
-
-#if 0
-	if (0) {  //( !uis.demoversion && !ui_cdkeychecked.integer ) {
-		char	key[17];
-
-		trap_GetCDKey( key, sizeof(key) );
-		if( trap_VerifyCDKey( key, NULL ) == qfalse ) {
-			UI_CDKeyMenu();
-			return;
-		}
-	}
-#endif
+	trap_Cvar_SetValue( "handicap", 100 ); //Reset handicap during server change, it must be ser per game
 
 	memset( &s_main, 0 ,sizeof(mainmenu_t) );
 	memset( &s_errorMessage, 0 ,sizeof(errorMessage_t) );
@@ -335,8 +301,7 @@
 	MainMenu_Cache();
 
 	trap_Cvar_VariableStringBuffer( "com_errorMessage", s_errorMessage.errorMessage, sizeof(s_errorMessage.errorMessage) );
-	if (strlen(s_errorMessage.errorMessage))
-	{
+	if (strlen(s_errorMessage.errorMessage)) {
 		s_errorMessage.menu.draw = Main_MenuDraw;
 		s_errorMessage.menu.key = ErrorMessage_Key;
 		s_errorMessage.menu.fullscreen = qtrue;
@@ -353,12 +318,10 @@
 	s_main.menu.draw = Main_MenuDraw;
 	s_main.menu.fullscreen = qtrue;
 	s_main.menu.wrapAround = qtrue;
-	s_main.menu.showlogo = qfalse;  //qtrue;
-
-	type = MTYPE_PTEXT;  //MTYPE_TEXT;  // MTYPE_PTEXT
+	s_main.menu.showlogo = qtrue;
 
 	y = 134;
-	s_main.singleplayer.generic.type		= type;
+	s_main.singleplayer.generic.type		= MTYPE_PTEXT;
 	s_main.singleplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.singleplayer.generic.x			= 320;
 	s_main.singleplayer.generic.y			= y;
@@ -368,8 +331,8 @@
 	s_main.singleplayer.color				= color_red;
 	s_main.singleplayer.style				= style;
 
-	//y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.multiplayer.generic.type			= type;
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.multiplayer.generic.type			= MTYPE_PTEXT;
 	s_main.multiplayer.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.multiplayer.generic.x			= 320;
 	s_main.multiplayer.generic.y			= y;
@@ -380,32 +343,29 @@
 	s_main.multiplayer.style				= style;
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.demos.generic.type				= type;
+	s_main.setup.generic.type				= MTYPE_PTEXT;
+	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.setup.generic.x					= 320;
+	s_main.setup.generic.y					= y;
+	s_main.setup.generic.id					= ID_SETUP;
+	s_main.setup.generic.callback			= Main_MenuEvent;
+	s_main.setup.string						= "SETUP";
+	s_main.setup.color						= color_red;
+	s_main.setup.style						= style;
+
+	y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.demos.generic.type				= MTYPE_PTEXT;
 	s_main.demos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.demos.generic.x					= 320;
 	s_main.demos.generic.y					= y;
 	s_main.demos.generic.id					= ID_DEMOS;
 	s_main.demos.generic.callback			= Main_MenuEvent;
-	s_main.demos.string						= "WOLFCAM-DEMOS";
+	s_main.demos.string						= "DEMOS";
 	s_main.demos.color						= color_red;
 	s_main.demos.style						= style;
 
-#if 1
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.qldemos.generic.type				= type;
-	s_main.qldemos.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.qldemos.generic.x					= 320;
-	s_main.qldemos.generic.y					= y;
-	s_main.qldemos.generic.id					= ID_QLDEMOS;
-	s_main.qldemos.generic.callback			= Main_MenuEvent;
-	s_main.qldemos.string						= "QUAKELIVE-DEMOS";
-	s_main.qldemos.color						= color_red;
-	s_main.qldemos.style						= style;
-#endif
-
-#if 0
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.cinematics.generic.type			= type;
+	/*y += MAIN_MENU_VERTICAL_SPACING;
+	s_main.cinematics.generic.type			= MTYPE_PTEXT;
 	s_main.cinematics.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.cinematics.generic.x				= 320;
 	s_main.cinematics.generic.y				= y;
@@ -413,72 +373,46 @@
 	s_main.cinematics.generic.callback		= Main_MenuEvent;
 	s_main.cinematics.string				= "CINEMATICS";
 	s_main.cinematics.color					= color_red;
-	s_main.cinematics.style					= style;
-#endif
+	s_main.cinematics.style					= style;*/
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.setup.generic.type				= type;
-	s_main.setup.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.setup.generic.x					= 320;
-	s_main.setup.generic.y					= y;
-	s_main.setup.generic.id					= ID_SETUP;
-	s_main.setup.generic.callback			= Main_MenuEvent;
-	s_main.setup.string						= "SETUP";
-	s_main.setup.color						= color_red;
-	s_main.setup.style						= style;
+	s_main.challenges.generic.type			= MTYPE_PTEXT;
+	s_main.challenges.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.challenges.generic.x				= 320;
+	s_main.challenges.generic.y				= y;
+	s_main.challenges.generic.id			= ID_CHALLENGES;
+	s_main.challenges.generic.callback		= Main_MenuEvent;
+	s_main.challenges.string				= "STATISTICS";
+	s_main.challenges.color					= color_red;
+	s_main.challenges.style					= style;
 
-
-	if ( !uis.demoversion && UI_TeamArenaExists() ) {
+	if (UI_TeamArenaExists()) {
 		teamArena = qtrue;
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.teamArena.generic.type			= type;
+		y += MAIN_MENU_VERTICAL_SPACING;
+		s_main.teamArena.generic.type			= MTYPE_PTEXT;
 		s_main.teamArena.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 		s_main.teamArena.generic.x				= 320;
 		s_main.teamArena.generic.y				= y;
 		s_main.teamArena.generic.id				= ID_TEAMARENA;
 		s_main.teamArena.generic.callback		= Main_MenuEvent;
-		s_main.teamArena.string					= "TEAM ARENA";
+		s_main.teamArena.string					= "MISSION PACK";
 		s_main.teamArena.color					= color_red;
 		s_main.teamArena.style					= style;
 	}
 
-	if ( !uis.demoversion ) {
-		//y += MAIN_MENU_VERTICAL_SPACING;
-		s_main.mods.generic.type			= type;
-		s_main.mods.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-		s_main.mods.generic.x				= 320;
-		s_main.mods.generic.y				= y;
-		s_main.mods.generic.id				= ID_MODS;
-		s_main.mods.generic.callback		= Main_MenuEvent;
-		s_main.mods.string					= "MODS";
-		s_main.mods.color					= color_red;
-		s_main.mods.style					= style;
-	}
-
-	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openQuakeLiveDirectory.generic.type				= type;
-	s_main.openQuakeLiveDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openQuakeLiveDirectory.generic.x					= 320;
-	s_main.openQuakeLiveDirectory.generic.y					= y;
-	s_main.openQuakeLiveDirectory.generic.id					= ID_OPEN_QUAKE_LIVE_DIRECTORY;
-	s_main.openQuakeLiveDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openQuakeLiveDirectory.string						= "OPEN QUAKE LIVE DIRECTORY";
-	s_main.openQuakeLiveDirectory.color						= color_red;
-	s_main.openQuakeLiveDirectory.style						= style;
-
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.openWolfcamDirectory.generic.type				= type;
-	s_main.openWolfcamDirectory.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
-	s_main.openWolfcamDirectory.generic.x					= 320;
-	s_main.openWolfcamDirectory.generic.y					= y;
-	s_main.openWolfcamDirectory.generic.id					= ID_OPEN_WOLFCAM_DIRECTORY;
-	s_main.openWolfcamDirectory.generic.callback			= Main_MenuEvent;
-	s_main.openWolfcamDirectory.string						= "OPEN WOLFCAM DIRECTORY";
-	s_main.openWolfcamDirectory.color						= color_red;
-	s_main.openWolfcamDirectory.style						= style;
+	s_main.mods.generic.type			= MTYPE_PTEXT;
+	s_main.mods.generic.flags			= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_main.mods.generic.x				= 320;
+	s_main.mods.generic.y				= y;
+	s_main.mods.generic.id				= ID_MODS;
+	s_main.mods.generic.callback		= Main_MenuEvent;
+	s_main.mods.string					= "MODS";
+	s_main.mods.color					= color_red;
+	s_main.mods.style					= style;
 
 	y += MAIN_MENU_VERTICAL_SPACING;
-	s_main.exit.generic.type				= type;
+	s_main.exit.generic.type				= MTYPE_PTEXT;
 	s_main.exit.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	s_main.exit.generic.x					= 320;
 	s_main.exit.generic.y					= y;
@@ -488,35 +422,20 @@
 	s_main.exit.color						= color_red;
 	s_main.exit.style						= style;
 
-	//Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
-	//Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
-
-	if (!uis.showErrorMenu) {
-		Menu_AddItem( &s_main.menu,	&s_main.demos );
-		Menu_AddItem(&s_main.menu, &s_main.qldemos);
-		//Menu_AddItem( &s_main.menu,	&s_main.cinematics );
-		if (teamArena) {
-			//Menu_AddItem( &s_main.menu,	&s_main.teamArena );
-		}
-		if ( !uis.demoversion ) {
-			//Menu_AddItem( &s_main.menu,	&s_main.mods );
-		}
-		Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.singleplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.multiplayer );
+	Menu_AddItem( &s_main.menu,	&s_main.setup );
+	Menu_AddItem( &s_main.menu,	&s_main.demos );
+	//Menu_AddItem( &s_main.menu,	&s_main.cinematics );
+	Menu_AddItem( &s_main.menu,	&s_main.challenges );
+	if (teamArena) {
+		Menu_AddItem( &s_main.menu,	&s_main.teamArena );
 	}
-
-	Menu_AddItem(&s_main.menu, &s_main.openQuakeLiveDirectory);
-	Menu_AddItem(&s_main.menu, &s_main.openWolfcamDirectory);
+	Menu_AddItem( &s_main.menu,	&s_main.mods );
 	Menu_AddItem( &s_main.menu,	&s_main.exit );
 
 	trap_Key_SetCatcher( KEYCATCH_UI );
 	uis.menusp = 0;
 	UI_PushMenu ( &s_main.menu );
 
-	if (ui_demoStayInFolder.integer) {
-		lastDemoDirBuffer[0] = '\0';
-		trap_Cvar_VariableStringBuffer("lastdemodir", lastDemoDirBuffer, sizeof(lastDemoDirBuffer));
-		if (lastDemoDirBuffer[0]) {
-			UI_DemosMenu(qfalse, lastDemoDirBuffer);
-		}
-	}
 }

```
