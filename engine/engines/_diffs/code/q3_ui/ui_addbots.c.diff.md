# Diff: `code/q3_ui/ui_addbots.c`
**Canonical:** `wolfcamql-src` (sha256 `ded899c791bf...`, 12417 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `ba7041d319ec...`, 11908 bytes

_Diff stat: +21 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_addbots.c	2026-04-16 20:02:25.203156700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_addbots.c	2026-04-16 20:02:19.943312300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -59,16 +59,10 @@
 
 typedef struct {
 	menuframework_s	menu;
-
-	menutext_s		banner;
-	menubitmap_s	background;
-
 	menubitmap_s	arrows;
 	menubitmap_s	up;
 	menubitmap_s	down;
-
 	menutext_s		bots[7];
-
 	menulist_s		skill;
 	menulist_s		team;
 	menubitmap_s	go;
@@ -221,6 +215,21 @@
 	qsort( addBotsMenuInfo.sortedBotNums, addBotsMenuInfo.numBots, sizeof(addBotsMenuInfo.sortedBotNums[0]), UI_AddBotsMenu_SortCompare );
 }
 
+
+/*
+=================
+UI_AddBotsMenu_Draw
+=================
+*/
+static void UI_AddBotsMenu_Draw( void ) {
+	UI_DrawBannerString( 320, 16, "ADD BOTS", UI_CENTER, color_white );
+	UI_DrawNamedPic( 320-233, 240-166, 466, 332, ART_BACKGROUND );
+
+	// standard menu drawing
+	Menu_Draw( &addBotsMenuInfo.menu );
+}
+
+	
 /*
 =================
 UI_AddBotsMenu_Init
@@ -232,18 +241,18 @@
 	"Hurt Me Plenty",
 	"Hardcore",
 	"Nightmare!",
-	NULL
+	0
 };
 
 static const char *teamNames1[] = {
 	"Free",
-	NULL
+	0
 };
 
 static const char *teamNames2[] = {
 	"Red",
 	"Blue",
-	NULL
+	0
 };
 
 static void UI_AddBotsMenu_Init( void ) {
@@ -257,6 +266,7 @@
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 
 	memset( &addBotsMenuInfo, 0 ,sizeof(addBotsMenuInfo) );
+	addBotsMenuInfo.menu.draw = UI_AddBotsMenu_Draw;
 	addBotsMenuInfo.menu.fullscreen = qfalse;
 	addBotsMenuInfo.menu.wrapAround = qtrue;
 	addBotsMenuInfo.delay = 1000;
@@ -266,21 +276,6 @@
 	addBotsMenuInfo.numBots = UI_GetNumBots();
 	count = addBotsMenuInfo.numBots < 7 ? addBotsMenuInfo.numBots : 7;
 
-	addBotsMenuInfo.banner.generic.type			= MTYPE_BTEXT;
-	addBotsMenuInfo.banner.generic.x			= 320;
-	addBotsMenuInfo.banner.generic.y			= 16;
-	addBotsMenuInfo.banner.string				= "ADD BOTS";
-	addBotsMenuInfo.banner.color				= color_white;
-	addBotsMenuInfo.banner.style				= UI_CENTER;
-
-	addBotsMenuInfo.background.generic.type		= MTYPE_BITMAP;
-	addBotsMenuInfo.background.generic.name		= ART_BACKGROUND;
-	addBotsMenuInfo.background.generic.flags	= QMF_INACTIVE;
-	addBotsMenuInfo.background.generic.x		= 320-233;
-	addBotsMenuInfo.background.generic.y		= 240-166;
-	addBotsMenuInfo.background.width			= 466;
-	addBotsMenuInfo.background.height			= 332;
-
 	addBotsMenuInfo.arrows.generic.type  = MTYPE_BITMAP;
 	addBotsMenuInfo.arrows.generic.name  = ART_ARROWS;
 	addBotsMenuInfo.arrows.generic.flags = QMF_INACTIVE;
@@ -375,9 +370,8 @@
 	UI_AddBotsMenu_GetSortedBotNums();
 	UI_AddBotsMenu_SetBotNames();
 
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.background );
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.banner );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.arrows );
+
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.up );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.down );
 	for( n = 0; n < count; n++ ) {

```

### `openarena-engine`  — sha256 `f2360606ce4f...`, 11938 bytes

_Diff stat: +17 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_addbots.c	2026-04-16 20:02:25.203156700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_addbots.c	2026-04-16 22:48:25.892200500 +0100
@@ -59,16 +59,10 @@
 
 typedef struct {
 	menuframework_s	menu;
-
-	menutext_s		banner;
-	menubitmap_s	background;
-
 	menubitmap_s	arrows;
 	menubitmap_s	up;
 	menubitmap_s	down;
-
 	menutext_s		bots[7];
-
 	menulist_s		skill;
 	menulist_s		team;
 	menubitmap_s	go;
@@ -221,6 +215,21 @@
 	qsort( addBotsMenuInfo.sortedBotNums, addBotsMenuInfo.numBots, sizeof(addBotsMenuInfo.sortedBotNums[0]), UI_AddBotsMenu_SortCompare );
 }
 
+
+/*
+=================
+UI_AddBotsMenu_Draw
+=================
+*/
+static void UI_AddBotsMenu_Draw( void ) {
+	UI_DrawBannerString( 320, 16, "ADD BOTS", UI_CENTER, color_white );
+	UI_DrawNamedPic( 320-233, 240-166, 466, 332, ART_BACKGROUND );
+
+	// standard menu drawing
+	Menu_Draw( &addBotsMenuInfo.menu );
+}
+
+	
 /*
 =================
 UI_AddBotsMenu_Init
@@ -257,6 +266,7 @@
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 
 	memset( &addBotsMenuInfo, 0 ,sizeof(addBotsMenuInfo) );
+	addBotsMenuInfo.menu.draw = UI_AddBotsMenu_Draw;
 	addBotsMenuInfo.menu.fullscreen = qfalse;
 	addBotsMenuInfo.menu.wrapAround = qtrue;
 	addBotsMenuInfo.delay = 1000;
@@ -266,21 +276,6 @@
 	addBotsMenuInfo.numBots = UI_GetNumBots();
 	count = addBotsMenuInfo.numBots < 7 ? addBotsMenuInfo.numBots : 7;
 
-	addBotsMenuInfo.banner.generic.type			= MTYPE_BTEXT;
-	addBotsMenuInfo.banner.generic.x			= 320;
-	addBotsMenuInfo.banner.generic.y			= 16;
-	addBotsMenuInfo.banner.string				= "ADD BOTS";
-	addBotsMenuInfo.banner.color				= color_white;
-	addBotsMenuInfo.banner.style				= UI_CENTER;
-
-	addBotsMenuInfo.background.generic.type		= MTYPE_BITMAP;
-	addBotsMenuInfo.background.generic.name		= ART_BACKGROUND;
-	addBotsMenuInfo.background.generic.flags	= QMF_INACTIVE;
-	addBotsMenuInfo.background.generic.x		= 320-233;
-	addBotsMenuInfo.background.generic.y		= 240-166;
-	addBotsMenuInfo.background.width			= 466;
-	addBotsMenuInfo.background.height			= 332;
-
 	addBotsMenuInfo.arrows.generic.type  = MTYPE_BITMAP;
 	addBotsMenuInfo.arrows.generic.name  = ART_ARROWS;
 	addBotsMenuInfo.arrows.generic.flags = QMF_INACTIVE;
@@ -375,9 +370,8 @@
 	UI_AddBotsMenu_GetSortedBotNums();
 	UI_AddBotsMenu_SetBotNames();
 
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.background );
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.banner );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.arrows );
+
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.up );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.down );
 	for( n = 0; n < count; n++ ) {

```

### `openarena-gamecode`  — sha256 `839aa2d428d3...`, 12088 bytes

_Diff stat: +26 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_addbots.c	2026-04-16 20:02:25.203156700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_addbots.c	2026-04-16 22:48:24.178986800 +0100
@@ -32,14 +32,14 @@
 #include "ui_local.h"
 
 
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"	
-#define ART_FIGHT0			"menu/art/accept_0"
-#define ART_FIGHT1			"menu/art/accept_1"
-#define ART_BACKGROUND		"menu/art/addbotframe"
-#define ART_ARROWS			"menu/art/arrows_vert_0"
-#define ART_ARROWUP			"menu/art/arrows_vert_top"
-#define ART_ARROWDOWN		"menu/art/arrows_vert_bot"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_FIGHT0			"menu/" MENU_ART_DIR "/accept_0"
+#define ART_FIGHT1			"menu/" MENU_ART_DIR "/accept_1"
+#define ART_BACKGROUND		"menu/" MENU_ART_DIR "/addbotframe"
+#define ART_ARROWS			"menu/" MENU_ART_DIR "/arrows_vert_0"
+#define ART_ARROWUP			"menu/" MENU_ART_DIR "/arrows_vert_top"
+#define ART_ARROWDOWN		"menu/" MENU_ART_DIR "/arrows_vert_bot"
 
 #define ID_BACK				10
 #define ID_GO				11
@@ -59,16 +59,10 @@
 
 typedef struct {
 	menuframework_s	menu;
-
-	menutext_s		banner;
-	menubitmap_s	background;
-
 	menubitmap_s	arrows;
 	menubitmap_s	up;
 	menubitmap_s	down;
-
 	menutext_s		bots[7];
-
 	menulist_s		skill;
 	menulist_s		team;
 	menubitmap_s	go;
@@ -221,6 +215,21 @@
 	qsort( addBotsMenuInfo.sortedBotNums, addBotsMenuInfo.numBots, sizeof(addBotsMenuInfo.sortedBotNums[0]), UI_AddBotsMenu_SortCompare );
 }
 
+
+/*
+=================
+UI_AddBotsMenu_Draw
+=================
+*/
+static void UI_AddBotsMenu_Draw( void ) {
+	UI_DrawBannerString( 320, 16, "ADD BOTS", UI_CENTER, color_white );
+	UI_DrawNamedPic( 320-233, 240-166, 466, 332, ART_BACKGROUND );
+
+	// standard menu drawing
+	Menu_Draw( &addBotsMenuInfo.menu );
+}
+
+	
 /*
 =================
 UI_AddBotsMenu_Init
@@ -257,6 +266,7 @@
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 
 	memset( &addBotsMenuInfo, 0 ,sizeof(addBotsMenuInfo) );
+	addBotsMenuInfo.menu.draw = UI_AddBotsMenu_Draw;
 	addBotsMenuInfo.menu.fullscreen = qfalse;
 	addBotsMenuInfo.menu.wrapAround = qtrue;
 	addBotsMenuInfo.delay = 1000;
@@ -266,21 +276,6 @@
 	addBotsMenuInfo.numBots = UI_GetNumBots();
 	count = addBotsMenuInfo.numBots < 7 ? addBotsMenuInfo.numBots : 7;
 
-	addBotsMenuInfo.banner.generic.type			= MTYPE_BTEXT;
-	addBotsMenuInfo.banner.generic.x			= 320;
-	addBotsMenuInfo.banner.generic.y			= 16;
-	addBotsMenuInfo.banner.string				= "ADD BOTS";
-	addBotsMenuInfo.banner.color				= color_white;
-	addBotsMenuInfo.banner.style				= UI_CENTER;
-
-	addBotsMenuInfo.background.generic.type		= MTYPE_BITMAP;
-	addBotsMenuInfo.background.generic.name		= ART_BACKGROUND;
-	addBotsMenuInfo.background.generic.flags	= QMF_INACTIVE;
-	addBotsMenuInfo.background.generic.x		= 320-233;
-	addBotsMenuInfo.background.generic.y		= 240-166;
-	addBotsMenuInfo.background.width			= 466;
-	addBotsMenuInfo.background.height			= 332;
-
 	addBotsMenuInfo.arrows.generic.type  = MTYPE_BITMAP;
 	addBotsMenuInfo.arrows.generic.name  = ART_ARROWS;
 	addBotsMenuInfo.arrows.generic.flags = QMF_INACTIVE;
@@ -338,7 +333,7 @@
 	addBotsMenuInfo.team.generic.y			= y;
 	addBotsMenuInfo.team.generic.name		= "Team: ";
 	addBotsMenuInfo.team.generic.id			= ID_TEAM;
-	if( gametype >= GT_TEAM ) {
+	if( gametype >= GT_TEAM && gametype!=GT_LMS  && gametype!=GT_POSSESSION) {
 		addBotsMenuInfo.team.itemnames		= teamNames2;
 	}
 	else {
@@ -375,9 +370,8 @@
 	UI_AddBotsMenu_GetSortedBotNums();
 	UI_AddBotsMenu_SetBotNames();
 
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.background );
-	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.banner );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.arrows );
+
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.up );
 	Menu_AddItem( &addBotsMenuInfo.menu, &addBotsMenuInfo.down );
 	for( n = 0; n < count; n++ ) {

```
