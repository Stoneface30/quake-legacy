# Diff: `code/q3_ui/ui_setup.c`
**Canonical:** `wolfcamql-src` (sha256 `66baf3654503...`, 10878 bytes)

## Variants

### `quake3-source`  — sha256 `7860e0da8577...`, 10855 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_setup.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_setup.c	2026-04-16 20:02:19.952185700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -293,7 +293,7 @@
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupcontrols );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupsystem );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.game );
-	//Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
+	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.load );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.save );
 	if( !trap_Cvar_VariableValue( "cl_paused" ) ) {

```

### `openarena-engine`  — sha256 `42dfaac36dc0...`, 10876 bytes
Also identical in: ioquake3

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_setup.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_setup.c	2026-04-16 22:48:25.900194200 +0100
@@ -293,7 +293,7 @@
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupcontrols );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupsystem );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.game );
-	//Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
+	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.load );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.save );
 	if( !trap_Cvar_VariableValue( "cl_paused" ) ) {

```

### `openarena-gamecode`  — sha256 `40b210dec72f...`, 10943 bytes

_Diff stat: +12 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_setup.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_setup.c	2026-04-16 22:48:24.187498800 +0100
@@ -34,16 +34,16 @@
 
 #define SETUP_MENU_VERTICAL_SPACING		34
 
-#define ART_BACK0		"menu/art/back_0"
-#define ART_BACK1		"menu/art/back_1"	
-#define ART_FRAMEL		"menu/art/frame2_l"
-#define ART_FRAMER		"menu/art/frame1_r"
+#define ART_BACK0		"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1		"menu/" MENU_ART_DIR "/back_1"
+#define ART_FRAMEL		"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER		"menu/" MENU_ART_DIR "/frame1_r"
 
 #define ID_CUSTOMIZEPLAYER		10
 #define ID_CUSTOMIZECONTROLS	11
 #define ID_SYSTEMCONFIG			12
 #define ID_GAME					13
-#define ID_CDKEY				14
+//#define ID_CDKEY				14
 #define ID_LOAD					15
 #define ID_SAVE					16
 #define ID_DEFAULTS				17
@@ -60,7 +60,7 @@
 	menutext_s		setupcontrols;
 	menutext_s		setupsystem;
 	menutext_s		game;
-	menutext_s		cdkey;
+//	menutext_s		cdkey;
 //	menutext_s		load;
 //	menutext_s		save;
 	menutext_s		defaults;
@@ -123,9 +123,9 @@
 		UI_PreferencesMenu();
 		break;
 
-	case ID_CDKEY:
-		UI_CDKeyMenu();
-		break;
+//	case ID_CDKEY:
+//		UI_CDKeyMenu();
+//		break;
 
 //	case ID_LOAD:
 //		UI_LoadConfigMenu();
@@ -227,7 +227,7 @@
 	setupMenuInfo.game.color						= color_red;
 	setupMenuInfo.game.style						= UI_CENTER;
 
-	y += SETUP_MENU_VERTICAL_SPACING;
+/*	y += SETUP_MENU_VERTICAL_SPACING;
 	setupMenuInfo.cdkey.generic.type				= MTYPE_PTEXT;
 	setupMenuInfo.cdkey.generic.flags				= QMF_CENTER_JUSTIFY|QMF_PULSEIFFOCUS;
 	setupMenuInfo.cdkey.generic.x					= 320;
@@ -236,7 +236,7 @@
 	setupMenuInfo.cdkey.generic.callback			= UI_SetupMenu_Event; 
 	setupMenuInfo.cdkey.string						= "CD Key";
 	setupMenuInfo.cdkey.color						= color_red;
-	setupMenuInfo.cdkey.style						= UI_CENTER;
+	setupMenuInfo.cdkey.style						= UI_CENTER;*/
 
 	if( !trap_Cvar_VariableValue( "cl_paused" ) ) {
 #if 0
@@ -293,7 +293,7 @@
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupcontrols );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.setupsystem );
 	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.game );
-	//Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
+//	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.cdkey );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.load );
 //	Menu_AddItem( &setupMenuInfo.menu, &setupMenuInfo.save );
 	if( !trap_Cvar_VariableValue( "cl_paused" ) ) {

```
