# Diff: `code/q3_ui/ui_playersettings.c`
**Canonical:** `wolfcamql-src` (sha256 `85ba399bc73d...`, 15553 bytes)

## Variants

### `quake3-source`  — sha256 `10cc6118cbd4...`, 15527 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playersettings.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_playersettings.c	2026-04-16 20:02:19.949613500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -95,7 +95,7 @@
 	"15",
 	"10",
 	"5",
-	NULL
+	0
 };
 
 
@@ -467,7 +467,7 @@
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.name );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.handicap );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.effects );
-	//Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
+	Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.back );
 
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.player );

```

### `openarena-engine`  — sha256 `e8a5a60b786e...`, 15551 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playersettings.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_playersettings.c	2026-04-16 22:48:25.898194800 +0100
@@ -467,7 +467,7 @@
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.name );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.handicap );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.effects );
-	//Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
+	Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.back );
 
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.player );

```

### `openarena-gamecode`  — sha256 `05ea5e1bfb15...`, 17614 bytes

_Diff stat: +63 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playersettings.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_playersettings.c	2026-04-16 22:48:24.185499000 +0100
@@ -22,12 +22,12 @@
 //
 #include "ui_local.h"
 
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_MODEL0			"menu/art/model_0"
-#define ART_MODEL1			"menu/art/model_1"
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_MODEL0			"menu/" MENU_ART_DIR "/model_0"
+#define ART_MODEL1			"menu/" MENU_ART_DIR "/model_1"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
 #define ART_FX_BASE			"menu/art/fx_base"
 #define ART_FX_BLUE			"menu/art/fx_blue"
 #define ART_FX_CYAN			"menu/art/fx_cyan"
@@ -40,8 +40,9 @@
 #define ID_NAME			10
 #define ID_HANDICAP		11
 #define ID_EFFECTS		12
-#define ID_BACK			13
-#define ID_MODEL		14
+#define ID_EFFECTS2		13
+#define ID_BACK			14
+#define ID_MODEL		15
 
 #define MAX_NAMELENGTH	20
 
@@ -57,6 +58,9 @@
 	menufield_s			name;
 	menulist_s			handicap;
 	menulist_s			effects;
+        
+        //Added in beta 29
+        menulist_s              effects2;
 
 	menubitmap_s		back;
 	menubitmap_s		model;
@@ -75,7 +79,7 @@
 static int uitogamecode[] = {4,6,2,3,1,5,7};
 
 static const char *handicap_items[] = {
-	"None",
+	"100",
 	"95",
 	"90",
 	"85",
@@ -224,6 +228,20 @@
 	UI_DrawHandlePic( item->generic.x + 64 + item->curvalue * 16 + 8, item->generic.y + PROP_HEIGHT + 6, 16, 12, s_playersettings.fxPic[item->curvalue] );
 }
 
+/*
+=================
+PlayerSettings_DrawEffects
+=================
+*/
+static void PlayerSettings_DrawEffects2( void *self ) {
+	menulist_s		*item;
+
+	item = (menulist_s *)self;
+
+	UI_DrawHandlePic( item->generic.x + 64, item->generic.y + 8, 128, 8, s_playersettings.fxBasePic );
+	UI_DrawHandlePic( item->generic.x + 64 + item->curvalue * 16 + 8, item->generic.y + 6, 16, 12, s_playersettings.fxPic[item->curvalue] );
+}
+
 
 /*
 =================
@@ -236,7 +254,7 @@
 	char			buf[MAX_QPATH];
 
 	trap_Cvar_VariableStringBuffer( "model", buf, sizeof( buf ) );
-	if ( strcmp( buf, s_playersettings.playerModel ) != 0 ) {
+	if ( !strequals( buf, s_playersettings.playerModel ) ) {
 		UI_PlayerInfo_SetModel( &s_playersettings.playerinfo, buf );
 		strcpy( s_playersettings.playerModel, buf );
 
@@ -265,6 +283,9 @@
 
 	// effects color
 	trap_Cvar_SetValue( "color1", uitogamecode[s_playersettings.effects.curvalue] );
+        
+        // effects2 color
+	trap_Cvar_SetValue( "color2", uitogamecode[s_playersettings.effects2.curvalue] );
 }
 
 
@@ -300,6 +321,13 @@
 		c = 6;
 	}
 	s_playersettings.effects.curvalue = gamecodetoui[c];
+        
+        // effects2 color
+	c = trap_Cvar_VariableValue( "color2" ) - 1;
+	if( c < 0 || c > 6 ) {
+		c = 6;
+	}
+	s_playersettings.effects2.curvalue = gamecodetoui[c];
 
 	// model/skin
 	memset( &s_playersettings.playerinfo, 0, sizeof(playerInfo_t) );
@@ -344,6 +372,15 @@
 	}
 }
 
+/*
+=================
+PlayerSettings_StatusBar
+=================
+*/
+static void PlayerSettings_StatusBar( void* ptr ) {
+	UI_DrawString( 320, 400, "Lower handicap makes you weaker", UI_CENTER|UI_SMALLFONT, colorWhite );
+        UI_DrawString( 320, 420, "giving you more challenge", UI_CENTER|UI_SMALLFONT, colorWhite );
+}
 
 /*
 =================
@@ -408,6 +445,7 @@
 	s_playersettings.handicap.generic.top		= y - 8;
 	s_playersettings.handicap.generic.right		= 192 + 200;
 	s_playersettings.handicap.generic.bottom	= y + 2 * PROP_HEIGHT;
+        s_playersettings.handicap.generic.statusbar     = PlayerSettings_StatusBar;
 	s_playersettings.handicap.numitems			= 20;
 
 	y += 3 * PROP_HEIGHT;
@@ -422,6 +460,19 @@
 	s_playersettings.effects.generic.right		= 192 + 200;
 	s_playersettings.effects.generic.bottom		= y + 2* PROP_HEIGHT;
 	s_playersettings.effects.numitems			= 7;
+        
+        y += 2*PROP_HEIGHT;
+	s_playersettings.effects2.generic.type		= MTYPE_SPINCONTROL;
+	s_playersettings.effects2.generic.flags		= QMF_NODEFAULTINIT;
+	s_playersettings.effects2.generic.id			= ID_EFFECTS2;
+	s_playersettings.effects2.generic.ownerdraw	= PlayerSettings_DrawEffects2;
+	s_playersettings.effects2.generic.x			= 192;
+	s_playersettings.effects2.generic.y			= y;
+	s_playersettings.effects2.generic.left		= 192 - 8;
+	s_playersettings.effects2.generic.top		= y - 8;
+	s_playersettings.effects2.generic.right		= 192 + 200;
+	s_playersettings.effects2.generic.bottom		= y + 2* PROP_HEIGHT;
+	s_playersettings.effects2.numitems			= 7;
 
 	s_playersettings.model.generic.type			= MTYPE_BITMAP;
 	s_playersettings.model.generic.name			= ART_MODEL0;
@@ -467,7 +518,8 @@
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.name );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.handicap );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.effects );
-	//Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
+        Menu_AddItem( &s_playersettings.menu, &s_playersettings.effects2 );
+	Menu_AddItem( &s_playersettings.menu, &s_playersettings.model );
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.back );
 
 	Menu_AddItem( &s_playersettings.menu, &s_playersettings.player );

```
