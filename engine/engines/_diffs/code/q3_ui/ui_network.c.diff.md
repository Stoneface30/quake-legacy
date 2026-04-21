# Diff: `code/q3_ui/ui_network.c`
**Canonical:** `wolfcamql-src` (sha256 `9288496060f7...`, 9306 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `1d1e3a45ba96...`, 9282 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_network.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_network.c	2026-04-16 20:02:19.949102200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -50,7 +50,7 @@
 	"56K",
 	"ISDN",
 	"LAN/Cable/xDSL",
-	NULL
+	0
 };
 
 typedef struct {

```

### `openarena-gamecode`  — sha256 `bdbd0a5d7bae...`, 11187 bytes

_Diff stat: +42 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_network.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_network.c	2026-04-16 22:48:24.184499000 +0100
@@ -31,20 +31,22 @@
 #include "ui_local.h"
 
 
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
 
 #define ID_GRAPHICS			10
 #define ID_DISPLAY			11
 #define ID_SOUND			12
 #define ID_NETWORK			13
 #define ID_RATE				14
-#define ID_BACK				15
+#define ID_ALLOWDOWNLOAD	15
+#define ID_LAGOMETER		16
+#define ID_BACK				17
 
 
-static const char *rate_items[] = {
+const char *rate_items[] = {
 	"<= 28.8K",
 	"33.6K",
 	"56K",
@@ -66,6 +68,8 @@
 	menutext_s		network;
 
 	menulist_s		rate;
+	menuradiobutton_s	allowdownload;
+	menuradiobutton_s	lagometer;
 
 	menubitmap_s	back;
 } networkOptionsInfo_t;
@@ -120,6 +124,15 @@
 		}
 		break;
 
+	case ID_ALLOWDOWNLOAD:
+		trap_Cvar_SetValue( "cl_allowDownload", networkOptionsInfo.allowdownload.curvalue );
+		trap_Cvar_SetValue( "sv_allowDownload", networkOptionsInfo.allowdownload.curvalue );
+		break;
+
+	case ID_LAGOMETER:
+		trap_Cvar_SetValue( "cg_lagometer", networkOptionsInfo.lagometer.curvalue );
+		break;
+
 	case ID_BACK:
 		UI_PopMenu();
 		break;
@@ -216,6 +229,24 @@
 	networkOptionsInfo.rate.generic.y			= y;
 	networkOptionsInfo.rate.itemnames			= rate_items;
 
+	y += BIGCHAR_HEIGHT+2;
+	networkOptionsInfo.allowdownload.generic.type     = MTYPE_RADIOBUTTON;
+	networkOptionsInfo.allowdownload.generic.name	   = "Auto Downloading:";
+	networkOptionsInfo.allowdownload.generic.flags	   = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	networkOptionsInfo.allowdownload.generic.callback = UI_NetworkOptionsMenu_Event;
+	networkOptionsInfo.allowdownload.generic.id       = ID_ALLOWDOWNLOAD;
+	networkOptionsInfo.allowdownload.generic.x	       = 400;
+	networkOptionsInfo.allowdownload.generic.y	       = y;
+
+	y += BIGCHAR_HEIGHT+2;
+	networkOptionsInfo.lagometer.generic.type     = MTYPE_RADIOBUTTON;
+	networkOptionsInfo.lagometer.generic.name	   = "Lagometer:";
+	networkOptionsInfo.lagometer.generic.flags	   = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	networkOptionsInfo.lagometer.generic.callback = UI_NetworkOptionsMenu_Event;
+	networkOptionsInfo.lagometer.generic.id       = ID_LAGOMETER;
+	networkOptionsInfo.lagometer.generic.x	       = 400;
+	networkOptionsInfo.lagometer.generic.y	       = y;
+
 	networkOptionsInfo.back.generic.type		= MTYPE_BITMAP;
 	networkOptionsInfo.back.generic.name		= ART_BACK0;
 	networkOptionsInfo.back.generic.flags		= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS;
@@ -235,6 +266,8 @@
 	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.sound );
 	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.network );
 	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.rate );
+	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.allowdownload );
+	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.lagometer );
 	Menu_AddItem( &networkOptionsInfo.menu, ( void * ) &networkOptionsInfo.back );
 
 	rate = trap_Cvar_VariableValue( "rate" );
@@ -253,6 +286,9 @@
 	else {
 		networkOptionsInfo.rate.curvalue = 4;
 	}
+
+	networkOptionsInfo.allowdownload.curvalue = trap_Cvar_VariableValue( "cl_allowDownload" ) != 0;
+	networkOptionsInfo.lagometer.curvalue = trap_Cvar_VariableValue( "cg_lagometer" ) != 0;
 }
 
 

```
