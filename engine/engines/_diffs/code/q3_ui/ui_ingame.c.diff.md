# Diff: `code/q3_ui/ui_ingame.c`
**Canonical:** `wolfcamql-src` (sha256 `bf95ee19e7e9...`, 10479 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `5b1e5902b781...`, 10488 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_ingame.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_ingame.c	2026-04-16 20:02:19.946829300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -120,11 +120,11 @@
 		break;
 
 	case ID_RESTART:
-		UI_ConfirmMenu( "RESTART ARENA?", 0, InGame_RestartAction );
+		UI_ConfirmMenu( "RESTART ARENA?", (voidfunc_f)NULL, InGame_RestartAction );
 		break;
 
 	case ID_QUIT:
-		UI_ConfirmMenu( "EXIT GAME?",  0, InGame_QuitAction );
+		UI_ConfirmMenu( "EXIT GAME?",  (voidfunc_f)NULL, InGame_QuitAction );
 		break;
 
 	case ID_SERVERINFO:

```

### `openarena-gamecode`  — sha256 `aaaad6fda366...`, 11494 bytes

_Diff stat: +33 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_ingame.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_ingame.c	2026-04-16 22:48:24.182499300 +0100
@@ -7,7 +7,7 @@
 Quake III Arena source code is free software; you can redistribute it
 and/or modify it under the terms of the GNU General Public License as
 published by the Free Software Foundation; either version 2 of the License,
-or (at your option) any later version.
+or (at your option) any later version.SERVER
 
 Quake III Arena source code is distributed in the hope that it will be
 useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
@@ -32,8 +32,8 @@
 #include "ui_local.h"
 
 
-#define INGAME_FRAME					"menu/art/addbotframe"
-//#define INGAME_FRAME					"menu/art/cut_frame"
+#define INGAME_FRAME					"menu/" MENU_ART_DIR "/addbotframe"
+//#define INGAME_FRAME					"menu/" MENU_ART_DIR "/cut_frame"
 #define INGAME_MENU_VERTICAL_SPACING	28
 
 #define ID_TEAM					10
@@ -46,6 +46,7 @@
 #define ID_QUIT					17
 #define ID_RESUME				18
 #define ID_TEAMORDERS			19
+#define ID_VOTE                         20
 
 
 typedef struct {
@@ -62,6 +63,7 @@
 	menutext_s		teamorders;
 	menutext_s		quit;
 	menutext_s		resume;
+        menutext_s              vote;
 } ingamemenu_t;
 
 static ingamemenu_t	s_ingame;
@@ -92,7 +94,8 @@
 		return;
 	}
 	UI_PopMenu();
-	UI_CreditMenu();
+	//UI_CreditMenu();
+        trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
 }
 
 
@@ -146,6 +149,10 @@
 	case ID_RESUME:
 		UI_PopMenu();
 		break;
+                
+        case ID_VOTE:
+                UI_VoteMenuMenu();
+                break;
 	}
 }
 
@@ -160,10 +167,13 @@
 	uiClientState_t	cs;
 	char	info[MAX_INFO_STRING];
 	int		team;
+	int		gametype;
 
 	memset( &s_ingame, 0 ,sizeof(ingamemenu_t) );
 
 	InGame_Cache();
+	
+	gametype = trap_Cvar_VariableValue("g_gametype");
 
 	s_ingame.menu.wrapAround = qtrue;
 	s_ingame.menu.fullscreen = qfalse;
@@ -198,7 +208,7 @@
 	s_ingame.addbots.string				= "ADD BOTS";
 	s_ingame.addbots.color				= color_red;
 	s_ingame.addbots.style				= UI_CENTER|UI_SMALLFONT;
-	if( !trap_Cvar_VariableValue( "sv_running" ) || !trap_Cvar_VariableValue( "bot_enable" ) || (trap_Cvar_VariableValue( "g_gametype" ) == GT_SINGLE_PLAYER)) {
+	if( !trap_Cvar_VariableValue( "sv_running" ) || !trap_Cvar_VariableValue( "bot_enable" ) || gametype == GT_SINGLE_PLAYER) {
 		s_ingame.addbots.generic.flags |= QMF_GRAYED;
 	}
 
@@ -212,7 +222,7 @@
 	s_ingame.removebots.string				= "REMOVE BOTS";
 	s_ingame.removebots.color				= color_red;
 	s_ingame.removebots.style				= UI_CENTER|UI_SMALLFONT;
-	if( !trap_Cvar_VariableValue( "sv_running" ) || !trap_Cvar_VariableValue( "bot_enable" ) || (trap_Cvar_VariableValue( "g_gametype" ) == GT_SINGLE_PLAYER)) {
+	if( !trap_Cvar_VariableValue( "sv_running" ) || !trap_Cvar_VariableValue( "bot_enable" ) || gametype == GT_SINGLE_PLAYER) {
 		s_ingame.removebots.generic.flags |= QMF_GRAYED;
 	}
 
@@ -226,7 +236,7 @@
 	s_ingame.teamorders.string				= "TEAM ORDERS";
 	s_ingame.teamorders.color				= color_red;
 	s_ingame.teamorders.style				= UI_CENTER|UI_SMALLFONT;
-	if( !(trap_Cvar_VariableValue( "g_gametype" ) >= GT_TEAM) ) {
+	if( !(gametype >= GT_TEAM) || gametype == GT_LMS || gametype == GT_POSSESSION  ) {
 		s_ingame.teamorders.generic.flags |= QMF_GRAYED;
 	}
 	else {
@@ -238,6 +248,21 @@
 		}
 	}
 
+        y += INGAME_MENU_VERTICAL_SPACING;
+	s_ingame.vote.generic.type		= MTYPE_PTEXT;
+	s_ingame.vote.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
+	s_ingame.vote.generic.x			= 320;
+	s_ingame.vote.generic.y			= y;
+	s_ingame.vote.generic.id			= ID_VOTE;
+	s_ingame.vote.generic.callback	= InGame_Event;
+	s_ingame.vote.string				= "CALL VOTE";
+	s_ingame.vote.color				= color_red;
+	s_ingame.vote.style				= UI_CENTER|UI_SMALLFONT;
+        trap_GetConfigString( CS_SERVERINFO, info, MAX_INFO_STRING );
+        if( atoi( Info_ValueForKey(info,"g_allowVote") )==0 || gametype==GT_SINGLE_PLAYER ) {
+		s_ingame.vote.generic.flags |= QMF_GRAYED;
+	}
+
 	y += INGAME_MENU_VERTICAL_SPACING;
 	s_ingame.setup.generic.type			= MTYPE_PTEXT;
 	s_ingame.setup.generic.flags		= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
@@ -312,6 +337,7 @@
 	Menu_AddItem( &s_ingame.menu, &s_ingame.addbots );
 	Menu_AddItem( &s_ingame.menu, &s_ingame.removebots );
 	Menu_AddItem( &s_ingame.menu, &s_ingame.teamorders );
+	Menu_AddItem( &s_ingame.menu, &s_ingame.vote );
 	Menu_AddItem( &s_ingame.menu, &s_ingame.setup );
 	Menu_AddItem( &s_ingame.menu, &s_ingame.server );
 	Menu_AddItem( &s_ingame.menu, &s_ingame.restart );

```
