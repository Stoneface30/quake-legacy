# Diff: `code/q3_ui/ui_preferences.c`
**Canonical:** `wolfcamql-src` (sha256 `b6a813835c7f...`, 15695 bytes)

## Variants

### `quake3-source`  — sha256 `57c49848a318...`, 15693 bytes

_Diff stat: +13 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_preferences.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_preferences.c	2026-04-16 20:02:19.949613500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -52,6 +52,9 @@
 #define ID_ALLOWDOWNLOAD			137
 #define ID_BACK					138
 
+#define	NUM_CROSSHAIRS			10
+
+
 typedef struct {
 	menuframework_s		menu;
 
@@ -83,7 +86,7 @@
 	"upper right",
 	"lower right",
 	"lower left",
-	NULL
+	0
 };
 
 static void Preferences_SetMenuItems( void ) {
@@ -108,6 +111,10 @@
 
 	switch( ((menucommon_s*)ptr)->id ) {
 	case ID_CROSSHAIR:
+		s_preferences.crosshair.curvalue++;
+		if( s_preferences.crosshair.curvalue == NUM_CROSSHAIRS ) {
+			s_preferences.crosshair.curvalue = 0;
+		}
 		trap_Cvar_SetValue( "cg_drawCrosshair", s_preferences.crosshair.curvalue );
 		break;
 
@@ -245,7 +252,7 @@
 	s_preferences.framer.height  	   = 334;
 
 	y = 144;
-	s_preferences.crosshair.generic.type		= MTYPE_SPINCONTROL;
+	s_preferences.crosshair.generic.type		= MTYPE_TEXT;
 	s_preferences.crosshair.generic.flags		= QMF_PULSEIFFOCUS|QMF_SMALLFONT|QMF_NODEFAULTINIT|QMF_OWNERDRAW;
 	s_preferences.crosshair.generic.x			= PREFERENCES_X_POS;
 	s_preferences.crosshair.generic.y			= y;
@@ -257,7 +264,6 @@
 	s_preferences.crosshair.generic.bottom		= y + 20;
 	s_preferences.crosshair.generic.left		= PREFERENCES_X_POS - ( ( strlen(s_preferences.crosshair.generic.name) + 1 ) * SMALLCHAR_WIDTH );
 	s_preferences.crosshair.generic.right		= PREFERENCES_X_POS + 48;
-	s_preferences.crosshair.numitems                        = NUM_CROSSHAIRS;
 
 	y += BIGCHAR_HEIGHT+2+4;
 	s_preferences.simpleitems.generic.type        = MTYPE_RADIOBUTTON;
@@ -350,6 +356,7 @@
 	s_preferences.allowdownload.generic.x	       = PREFERENCES_X_POS;
 	s_preferences.allowdownload.generic.y	       = y;
 
+	y += BIGCHAR_HEIGHT+2;
 	s_preferences.back.generic.type	    = MTYPE_BITMAP;
 	s_preferences.back.generic.name     = ART_BACK0;
 	s_preferences.back.generic.flags    = QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS;
@@ -395,9 +402,8 @@
 	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
-	for( n = 1; n < NUM_CROSSHAIRS; n++ ) {
-		//s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
-		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%d",  n ) );
+	for( n = 0; n < NUM_CROSSHAIRS; n++ ) {
+		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
 	}
 }
 

```

### `ioquake3`  — sha256 `d92c913eaa34...`, 15606 bytes

_Diff stat: +6 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_preferences.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_preferences.c	2026-04-16 20:02:21.557593600 +0100
@@ -52,6 +52,9 @@
 #define ID_ALLOWDOWNLOAD			137
 #define ID_BACK					138
 
+#define	NUM_CROSSHAIRS			10
+
+
 typedef struct {
 	menuframework_s		menu;
 
@@ -257,7 +260,7 @@
 	s_preferences.crosshair.generic.bottom		= y + 20;
 	s_preferences.crosshair.generic.left		= PREFERENCES_X_POS - ( ( strlen(s_preferences.crosshair.generic.name) + 1 ) * SMALLCHAR_WIDTH );
 	s_preferences.crosshair.generic.right		= PREFERENCES_X_POS + 48;
-	s_preferences.crosshair.numitems                        = NUM_CROSSHAIRS;
+	s_preferences.crosshair.numitems			= NUM_CROSSHAIRS;
 
 	y += BIGCHAR_HEIGHT+2+4;
 	s_preferences.simpleitems.generic.type        = MTYPE_RADIOBUTTON;
@@ -395,9 +398,8 @@
 	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
-	for( n = 1; n < NUM_CROSSHAIRS; n++ ) {
-		//s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
-		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%d",  n ) );
+	for( n = 0; n < NUM_CROSSHAIRS; n++ ) {
+		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
 	}
 }
 

```

### `openarena-engine`  — sha256 `7b6c70604fa7...`, 15631 bytes

_Diff stat: +7 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_preferences.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_preferences.c	2026-04-16 22:48:25.898194800 +0100
@@ -52,6 +52,9 @@
 #define ID_ALLOWDOWNLOAD			137
 #define ID_BACK					138
 
+#define	NUM_CROSSHAIRS			10
+
+
 typedef struct {
 	menuframework_s		menu;
 
@@ -257,7 +260,7 @@
 	s_preferences.crosshair.generic.bottom		= y + 20;
 	s_preferences.crosshair.generic.left		= PREFERENCES_X_POS - ( ( strlen(s_preferences.crosshair.generic.name) + 1 ) * SMALLCHAR_WIDTH );
 	s_preferences.crosshair.generic.right		= PREFERENCES_X_POS + 48;
-	s_preferences.crosshair.numitems                        = NUM_CROSSHAIRS;
+	s_preferences.crosshair.numitems			= NUM_CROSSHAIRS;
 
 	y += BIGCHAR_HEIGHT+2+4;
 	s_preferences.simpleitems.generic.type        = MTYPE_RADIOBUTTON;
@@ -350,6 +353,7 @@
 	s_preferences.allowdownload.generic.x	       = PREFERENCES_X_POS;
 	s_preferences.allowdownload.generic.y	       = y;
 
+	y += BIGCHAR_HEIGHT+2;
 	s_preferences.back.generic.type	    = MTYPE_BITMAP;
 	s_preferences.back.generic.name     = ART_BACK0;
 	s_preferences.back.generic.flags    = QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS;
@@ -395,9 +399,8 @@
 	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
-	for( n = 1; n < NUM_CROSSHAIRS; n++ ) {
-		//s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
-		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%d",  n ) );
+	for( n = 0; n < NUM_CROSSHAIRS; n++ ) {
+		s_preferences.crosshairShader[n] = trap_R_RegisterShaderNoMip( va("gfx/2d/crosshair%c", 'a' + n ) );
 	}
 }
 

```

### `openarena-gamecode`  — sha256 `64309758abaa...`, 20236 bytes

_Diff stat: +187 / -90 lines_

_(full diff is 20267 bytes — see files directly)_
