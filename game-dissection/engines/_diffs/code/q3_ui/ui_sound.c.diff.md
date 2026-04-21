# Diff: `code/q3_ui/ui_sound.c`
**Canonical:** `wolfcamql-src` (sha256 `2eac3bb66754...`, 16202 bytes)

## Variants

### `quake3-source`  — sha256 `97f0db7c0974...`, 11273 bytes

_Diff stat: +37 / -171 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sound.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_sound.c	2026-04-16 20:02:19.952185700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -35,8 +35,6 @@
 #define ART_FRAMER			"menu/art/frame1_r"
 #define ART_BACK0			"menu/art/back_0"
 #define ART_BACK1			"menu/art/back_1"
-#define ART_ACCEPT0			"menu/art/accept_0"
-#define ART_ACCEPT1			"menu/art/accept_1"
 
 #define ID_GRAPHICS			10
 #define ID_DISPLAY			11
@@ -45,22 +43,12 @@
 #define ID_EFFECTSVOLUME	14
 #define ID_MUSICVOLUME		15
 #define ID_QUALITY			16
-#define ID_SOUNDSYSTEM		17
-//#define ID_A3D			18
-#define ID_BACK				19
-#define ID_APPLY			20
+//#define ID_A3D				17
+#define ID_BACK				18
 
-#define DEFAULT_SDL_SND_SPEED 22050
 
 static const char *quality_items[] = {
-	"Low", "Medium", "High", NULL
-};
-
-#define UISND_SDL 0
-#define UISND_OPENAL 1
-
-static const char *soundSystem_items[] = {
-	"SDL", "OpenAL", NULL
+	"Low", "High", 0
 };
 
 typedef struct {
@@ -77,17 +65,10 @@
 
 	menuslider_s		sfxvolume;
 	menuslider_s		musicvolume;
-	menulist_s			soundSystem;
 	menulist_s			quality;
 //	menuradiobutton_s	a3d;
 
 	menubitmap_s		back;
-	menubitmap_s		apply;
-
-	float				sfxvolume_original;
-	float				musicvolume_original;
-	int					soundSystem_original;
-	int					quality_original;
 } soundOptionsInfo_t;
 
 static soundOptionsInfo_t	soundOptionsInfo;
@@ -121,6 +102,27 @@
 		UI_PopMenu();
 		UI_NetworkOptionsMenu();
 		break;
+
+	case ID_EFFECTSVOLUME:
+		trap_Cvar_SetValue( "s_volume", soundOptionsInfo.sfxvolume.curvalue / 10 );
+		break;
+
+	case ID_MUSICVOLUME:
+		trap_Cvar_SetValue( "s_musicvolume", soundOptionsInfo.musicvolume.curvalue / 10 );
+		break;
+
+	case ID_QUALITY:
+		if( soundOptionsInfo.quality.curvalue ) {
+			trap_Cvar_SetValue( "s_khz", 22 );
+			trap_Cvar_SetValue( "s_compression", 0 );
+		}
+		else {
+			trap_Cvar_SetValue( "s_khz", 11 );
+			trap_Cvar_SetValue( "s_compression", 1 );
+		}
+		UI_ForceMenuOff();
+		trap_Cmd_ExecuteText( EXEC_APPEND, "snd_restart\n" );
+		break;
 /*
 	case ID_A3D:
 		if( soundOptionsInfo.a3d.curvalue ) {
@@ -135,98 +137,9 @@
 	case ID_BACK:
 		UI_PopMenu();
 		break;
-
-	case ID_APPLY:
-		trap_Cvar_SetValue( "s_volume", soundOptionsInfo.sfxvolume.curvalue / 10 );
-		soundOptionsInfo.sfxvolume_original = soundOptionsInfo.sfxvolume.curvalue;
-
-		trap_Cvar_SetValue( "s_musicvolume", soundOptionsInfo.musicvolume.curvalue / 10 );
-		soundOptionsInfo.musicvolume_original = soundOptionsInfo.musicvolume.curvalue;
-
-		// Check if something changed that requires the sound system to be restarted.
-		if (soundOptionsInfo.quality_original != soundOptionsInfo.quality.curvalue
-			|| soundOptionsInfo.soundSystem_original != soundOptionsInfo.soundSystem.curvalue)
-		{
-			int speed;
-
-			switch ( soundOptionsInfo.quality.curvalue )
-			{
-			default:
-			case 0:
-				speed = 11025;
-				break;
-			case 1:
-				speed = 22050;
-				break;
-			case 2:
-				speed = 44100;
-				break;
-			}
-
-			if (speed == DEFAULT_SDL_SND_SPEED)
-				speed = 0;
-
-			trap_Cvar_SetValue( "s_sdlSpeed", speed );
-			soundOptionsInfo.quality_original = soundOptionsInfo.quality.curvalue;
-
-			trap_Cvar_SetValue( "s_useOpenAL", (soundOptionsInfo.soundSystem.curvalue == UISND_OPENAL) );
-			soundOptionsInfo.soundSystem_original = soundOptionsInfo.soundSystem.curvalue;
-
-			UI_ForceMenuOff();
-			trap_Cmd_ExecuteText( EXEC_APPEND, "snd_restart\n" );
-		}
-		break;
 	}
 }
 
-/*
-=================
-SoundOptions_UpdateMenuItems
-=================
-*/
-static void SoundOptions_UpdateMenuItems( void )
-{
-	if ( soundOptionsInfo.soundSystem.curvalue == UISND_SDL )
-	{
-		soundOptionsInfo.quality.generic.flags &= ~QMF_GRAYED;
-	}
-	else
-	{
-		soundOptionsInfo.quality.generic.flags |= QMF_GRAYED;
-	}
-
-	soundOptionsInfo.apply.generic.flags |= QMF_HIDDEN|QMF_INACTIVE;
-
-	if ( soundOptionsInfo.sfxvolume_original != soundOptionsInfo.sfxvolume.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.musicvolume_original != soundOptionsInfo.musicvolume.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.soundSystem_original != soundOptionsInfo.soundSystem.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.quality_original != soundOptionsInfo.quality.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-}
-
-/*
-================
-SoundOptions_MenuDraw
-================
-*/
-void SoundOptions_MenuDraw (void)
-{
-//APSFIX - rework this
-	SoundOptions_UpdateMenuItems();
-
-	Menu_Draw( &soundOptionsInfo.menu );
-}
 
 /*
 ===============
@@ -235,14 +148,12 @@
 */
 static void UI_SoundOptionsMenu_Init( void ) {
 	int				y;
-	int				speed;
 
 	memset( &soundOptionsInfo, 0, sizeof(soundOptionsInfo) );
 
 	UI_SoundOptionsMenu_Cache();
 	soundOptionsInfo.menu.wrapAround = qtrue;
 	soundOptionsInfo.menu.fullscreen = qtrue;
-	soundOptionsInfo.menu.draw					= SoundOptions_MenuDraw;
 
 	soundOptionsInfo.banner.generic.type		= MTYPE_BTEXT;
 	soundOptionsInfo.banner.generic.flags		= QMF_CENTER_JUSTIFY;
@@ -308,7 +219,7 @@
 	soundOptionsInfo.network.style				= UI_RIGHT;
 	soundOptionsInfo.network.color				= color_red;
 
-	y = 240 - 2 * (BIGCHAR_HEIGHT + 2);
+	y = 240 - 1.5 * (BIGCHAR_HEIGHT + 2);
 	soundOptionsInfo.sfxvolume.generic.type		= MTYPE_SLIDER;
 	soundOptionsInfo.sfxvolume.generic.name		= "Effects Volume:";
 	soundOptionsInfo.sfxvolume.generic.flags	= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
@@ -331,25 +242,14 @@
 	soundOptionsInfo.musicvolume.maxvalue			= 10;
 
 	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.soundSystem.generic.type               = MTYPE_SPINCONTROL;
-	soundOptionsInfo.soundSystem.generic.name               = "Sound System:";
-	soundOptionsInfo.soundSystem.generic.flags              = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.soundSystem.generic.callback   = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.soundSystem.generic.id                 = ID_SOUNDSYSTEM;
-	soundOptionsInfo.soundSystem.generic.x                  = 400;
-	soundOptionsInfo.soundSystem.generic.y                  = y;
-	soundOptionsInfo.soundSystem.itemnames                  = soundSystem_items;
-
-	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.quality.generic.type           = MTYPE_SPINCONTROL;
-	soundOptionsInfo.quality.generic.name           = "SDL Sound Quality:";
-	soundOptionsInfo.quality.generic.flags          = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.quality.generic.callback       = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.quality.generic.id                     = ID_QUALITY;
-	soundOptionsInfo.quality.generic.x                      = 400;
-	soundOptionsInfo.quality.generic.y                      = y;
-	soundOptionsInfo.quality.itemnames                      = quality_items;
-
+	soundOptionsInfo.quality.generic.type		= MTYPE_SPINCONTROL;
+	soundOptionsInfo.quality.generic.name		= "Sound Quality:";
+	soundOptionsInfo.quality.generic.flags		= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	soundOptionsInfo.quality.generic.callback	= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.quality.generic.id			= ID_QUALITY;
+	soundOptionsInfo.quality.generic.x			= 400;
+	soundOptionsInfo.quality.generic.y			= y;
+	soundOptionsInfo.quality.itemnames			= quality_items;
 /*
 	y += BIGCHAR_HEIGHT+2;
 	soundOptionsInfo.a3d.generic.type			= MTYPE_RADIOBUTTON;
@@ -371,17 +271,6 @@
 	soundOptionsInfo.back.height				= 64;
 	soundOptionsInfo.back.focuspic				= ART_BACK1;
 
-	soundOptionsInfo.apply.generic.type                     = MTYPE_BITMAP;
-	soundOptionsInfo.apply.generic.name                     = ART_ACCEPT0;
-	soundOptionsInfo.apply.generic.flags            = QMF_RIGHT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_HIDDEN|QMF_INACTIVE;
-	soundOptionsInfo.apply.generic.callback         = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.apply.generic.id                       = ID_APPLY;
-	soundOptionsInfo.apply.generic.x                        = 640;
-	soundOptionsInfo.apply.generic.y                        = 480-64;
-	soundOptionsInfo.apply.width                            = 128;
-	soundOptionsInfo.apply.height                           = 64;
-	soundOptionsInfo.apply.focuspic                         = ART_ACCEPT1;
-
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.banner );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.framel );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.framer );
@@ -391,34 +280,13 @@
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.network );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.sfxvolume );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.musicvolume );
-	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.soundSystem );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.quality );
 //	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.a3d );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.back );
-	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.apply );
-
-	soundOptionsInfo.sfxvolume.curvalue = soundOptionsInfo.sfxvolume_original = trap_Cvar_VariableValue( "s_volume" ) * 10;
-	soundOptionsInfo.musicvolume.curvalue = soundOptionsInfo.musicvolume_original = trap_Cvar_VariableValue( "s_musicvolume" ) * 10;
-
-	if (trap_Cvar_VariableValue( "s_useOpenAL" ))
-		soundOptionsInfo.soundSystem_original = UISND_OPENAL;
-	else
-		soundOptionsInfo.soundSystem_original = UISND_SDL;
-
-	soundOptionsInfo.soundSystem.curvalue = soundOptionsInfo.soundSystem_original;
-
-	speed = trap_Cvar_VariableValue( "s_sdlSpeed" );
-	if (!speed) // Check for default
-		speed = DEFAULT_SDL_SND_SPEED;
-
-	if (speed <= 11025)
-		soundOptionsInfo.quality_original = 0;
-	else if (speed <= 22050)
-		soundOptionsInfo.quality_original = 1;
-	else // 44100
-		soundOptionsInfo.quality_original = 2;
-	soundOptionsInfo.quality.curvalue = soundOptionsInfo.quality_original;
 
+	soundOptionsInfo.sfxvolume.curvalue = trap_Cvar_VariableValue( "s_volume" ) * 10;
+	soundOptionsInfo.musicvolume.curvalue = trap_Cvar_VariableValue( "s_musicvolume" ) * 10;
+	soundOptionsInfo.quality.curvalue = !trap_Cvar_VariableValue( "s_compression" );
 //	soundOptionsInfo.a3d.curvalue = (int)trap_Cvar_VariableValue( "s_usingA3D" );
 }
 
@@ -433,8 +301,6 @@
 	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
-	trap_R_RegisterShaderNoMip( ART_ACCEPT0 );
-	trap_R_RegisterShaderNoMip( ART_ACCEPT1 );
 }
 
 

```

### `openarena-engine`  — sha256 `97874f88bace...`, 15822 bytes
Also identical in: ioquake3

_Diff stat: +39 / -39 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sound.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_sound.c	2026-04-16 22:48:25.900751300 +0100
@@ -46,7 +46,7 @@
 #define ID_MUSICVOLUME		15
 #define ID_QUALITY			16
 #define ID_SOUNDSYSTEM		17
-//#define ID_A3D			18
+//#define ID_A3D				18
 #define ID_BACK				19
 #define ID_APPLY			20
 
@@ -77,7 +77,7 @@
 
 	menuslider_s		sfxvolume;
 	menuslider_s		musicvolume;
-	menulist_s			soundSystem;
+	menulist_s  		soundSystem;
 	menulist_s			quality;
 //	menuradiobutton_s	a3d;
 
@@ -151,16 +151,16 @@
 
 			switch ( soundOptionsInfo.quality.curvalue )
 			{
-			default:
-			case 0:
-				speed = 11025;
-				break;
-			case 1:
-				speed = 22050;
-				break;
-			case 2:
-				speed = 44100;
-				break;
+				default:
+				case 0:
+					speed = 11025;
+					break;
+				case 1:
+					speed = 22050;
+					break;
+				case 2:
+					speed = 44100;
+					break;
 			}
 
 			if (speed == DEFAULT_SDL_SND_SPEED)
@@ -242,7 +242,7 @@
 	UI_SoundOptionsMenu_Cache();
 	soundOptionsInfo.menu.wrapAround = qtrue;
 	soundOptionsInfo.menu.fullscreen = qtrue;
-	soundOptionsInfo.menu.draw					= SoundOptions_MenuDraw;
+	soundOptionsInfo.menu.draw		= SoundOptions_MenuDraw;
 
 	soundOptionsInfo.banner.generic.type		= MTYPE_BTEXT;
 	soundOptionsInfo.banner.generic.flags		= QMF_CENTER_JUSTIFY;
@@ -331,24 +331,24 @@
 	soundOptionsInfo.musicvolume.maxvalue			= 10;
 
 	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.soundSystem.generic.type               = MTYPE_SPINCONTROL;
-	soundOptionsInfo.soundSystem.generic.name               = "Sound System:";
-	soundOptionsInfo.soundSystem.generic.flags              = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.soundSystem.generic.callback   = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.soundSystem.generic.id                 = ID_SOUNDSYSTEM;
-	soundOptionsInfo.soundSystem.generic.x                  = 400;
-	soundOptionsInfo.soundSystem.generic.y                  = y;
-	soundOptionsInfo.soundSystem.itemnames                  = soundSystem_items;
+	soundOptionsInfo.soundSystem.generic.type		= MTYPE_SPINCONTROL;
+	soundOptionsInfo.soundSystem.generic.name		= "Sound System:";
+	soundOptionsInfo.soundSystem.generic.flags		= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	soundOptionsInfo.soundSystem.generic.callback	= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.soundSystem.generic.id			= ID_SOUNDSYSTEM;
+	soundOptionsInfo.soundSystem.generic.x			= 400;
+	soundOptionsInfo.soundSystem.generic.y			= y;
+	soundOptionsInfo.soundSystem.itemnames			= soundSystem_items;
 
 	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.quality.generic.type           = MTYPE_SPINCONTROL;
-	soundOptionsInfo.quality.generic.name           = "SDL Sound Quality:";
-	soundOptionsInfo.quality.generic.flags          = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.quality.generic.callback       = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.quality.generic.id                     = ID_QUALITY;
-	soundOptionsInfo.quality.generic.x                      = 400;
-	soundOptionsInfo.quality.generic.y                      = y;
-	soundOptionsInfo.quality.itemnames                      = quality_items;
+	soundOptionsInfo.quality.generic.type		= MTYPE_SPINCONTROL;
+	soundOptionsInfo.quality.generic.name		= "SDL Sound Quality:";
+	soundOptionsInfo.quality.generic.flags		= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	soundOptionsInfo.quality.generic.callback	= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.quality.generic.id			= ID_QUALITY;
+	soundOptionsInfo.quality.generic.x			= 400;
+	soundOptionsInfo.quality.generic.y			= y;
+	soundOptionsInfo.quality.itemnames			= quality_items;
 
 /*
 	y += BIGCHAR_HEIGHT+2;
@@ -371,16 +371,16 @@
 	soundOptionsInfo.back.height				= 64;
 	soundOptionsInfo.back.focuspic				= ART_BACK1;
 
-	soundOptionsInfo.apply.generic.type                     = MTYPE_BITMAP;
-	soundOptionsInfo.apply.generic.name                     = ART_ACCEPT0;
-	soundOptionsInfo.apply.generic.flags            = QMF_RIGHT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_HIDDEN|QMF_INACTIVE;
-	soundOptionsInfo.apply.generic.callback         = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.apply.generic.id                       = ID_APPLY;
-	soundOptionsInfo.apply.generic.x                        = 640;
-	soundOptionsInfo.apply.generic.y                        = 480-64;
-	soundOptionsInfo.apply.width                            = 128;
-	soundOptionsInfo.apply.height                           = 64;
-	soundOptionsInfo.apply.focuspic                         = ART_ACCEPT1;
+	soundOptionsInfo.apply.generic.type			= MTYPE_BITMAP;
+	soundOptionsInfo.apply.generic.name			= ART_ACCEPT0;
+	soundOptionsInfo.apply.generic.flags		= QMF_RIGHT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_HIDDEN|QMF_INACTIVE;
+	soundOptionsInfo.apply.generic.callback		= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.apply.generic.id			= ID_APPLY;
+	soundOptionsInfo.apply.generic.x			= 640;
+	soundOptionsInfo.apply.generic.y			= 480-64;
+	soundOptionsInfo.apply.width				= 128;
+	soundOptionsInfo.apply.height				= 64;
+	soundOptionsInfo.apply.focuspic				= ART_ACCEPT1;
 
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.banner );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.framel );

```

### `openarena-gamecode`  — sha256 `125830292fc3...`, 12325 bytes

_Diff stat: +63 / -172 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sound.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_sound.c	2026-04-16 22:48:24.188498600 +0100
@@ -31,12 +31,10 @@
 #include "ui_local.h"
 
 
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
-#define ART_ACCEPT0			"menu/art/accept_0"
-#define ART_ACCEPT1			"menu/art/accept_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
 
 #define ID_GRAPHICS			10
 #define ID_DISPLAY			11
@@ -45,22 +43,14 @@
 #define ID_EFFECTSVOLUME	14
 #define ID_MUSICVOLUME		15
 #define ID_QUALITY			16
-#define ID_SOUNDSYSTEM		17
-//#define ID_A3D			18
+//#define ID_A3D				17
+//Sago: Here I do some stuff!
+#define ID_OPENAL			18
 #define ID_BACK				19
-#define ID_APPLY			20
 
-#define DEFAULT_SDL_SND_SPEED 22050
 
 static const char *quality_items[] = {
-	"Low", "Medium", "High", NULL
-};
-
-#define UISND_SDL 0
-#define UISND_OPENAL 1
-
-static const char *soundSystem_items[] = {
-	"SDL", "OpenAL", NULL
+	"Low", "High", NULL
 };
 
 typedef struct {
@@ -77,17 +67,11 @@
 
 	menuslider_s		sfxvolume;
 	menuslider_s		musicvolume;
-	menulist_s			soundSystem;
 	menulist_s			quality;
 //	menuradiobutton_s	a3d;
+	menuradiobutton_s	openal;
 
 	menubitmap_s		back;
-	menubitmap_s		apply;
-
-	float				sfxvolume_original;
-	float				musicvolume_original;
-	int					soundSystem_original;
-	int					quality_original;
 } soundOptionsInfo_t;
 
 static soundOptionsInfo_t	soundOptionsInfo;
@@ -121,6 +105,27 @@
 		UI_PopMenu();
 		UI_NetworkOptionsMenu();
 		break;
+
+	case ID_EFFECTSVOLUME:
+		trap_Cvar_SetValue( "s_volume", soundOptionsInfo.sfxvolume.curvalue / 10 );
+		break;
+
+	case ID_MUSICVOLUME:
+		trap_Cvar_SetValue( "s_musicvolume", soundOptionsInfo.musicvolume.curvalue / 10 );
+		break;
+
+	case ID_QUALITY:
+		if( soundOptionsInfo.quality.curvalue ) {
+			trap_Cvar_SetValue( "s_khz", 22 );
+			trap_Cvar_SetValue( "s_compression", 0 );
+		}
+		else {
+			trap_Cvar_SetValue( "s_khz", 11 );
+			trap_Cvar_SetValue( "s_compression", 1 );
+		}
+		UI_ForceMenuOff();
+		trap_Cmd_ExecuteText( EXEC_APPEND, "snd_restart\n" );
+		break;
 /*
 	case ID_A3D:
 		if( soundOptionsInfo.a3d.curvalue ) {
@@ -132,101 +137,23 @@
 		soundOptionsInfo.a3d.curvalue = (int)trap_Cvar_VariableValue( "s_usingA3D" );
 		break;
 */
-	case ID_BACK:
-		UI_PopMenu();
-		break;
-
-	case ID_APPLY:
-		trap_Cvar_SetValue( "s_volume", soundOptionsInfo.sfxvolume.curvalue / 10 );
-		soundOptionsInfo.sfxvolume_original = soundOptionsInfo.sfxvolume.curvalue;
-
-		trap_Cvar_SetValue( "s_musicvolume", soundOptionsInfo.musicvolume.curvalue / 10 );
-		soundOptionsInfo.musicvolume_original = soundOptionsInfo.musicvolume.curvalue;
-
-		// Check if something changed that requires the sound system to be restarted.
-		if (soundOptionsInfo.quality_original != soundOptionsInfo.quality.curvalue
-			|| soundOptionsInfo.soundSystem_original != soundOptionsInfo.soundSystem.curvalue)
-		{
-			int speed;
-
-			switch ( soundOptionsInfo.quality.curvalue )
-			{
-			default:
-			case 0:
-				speed = 11025;
-				break;
-			case 1:
-				speed = 22050;
-				break;
-			case 2:
-				speed = 44100;
-				break;
-			}
-
-			if (speed == DEFAULT_SDL_SND_SPEED)
-				speed = 0;
-
-			trap_Cvar_SetValue( "s_sdlSpeed", speed );
-			soundOptionsInfo.quality_original = soundOptionsInfo.quality.curvalue;
-
-			trap_Cvar_SetValue( "s_useOpenAL", (soundOptionsInfo.soundSystem.curvalue == UISND_OPENAL) );
-			soundOptionsInfo.soundSystem_original = soundOptionsInfo.soundSystem.curvalue;
 
-			UI_ForceMenuOff();
-			trap_Cmd_ExecuteText( EXEC_APPEND, "snd_restart\n" );
+	case ID_OPENAL:
+		if( soundOptionsInfo.openal.curvalue ) {
+			trap_Cmd_ExecuteText( EXEC_NOW, "s_useopenal 1\n" );
 		}
+		else {
+			trap_Cmd_ExecuteText( EXEC_NOW, "s_useopenal 0\n" );
+		}
+		soundOptionsInfo.openal.curvalue = (int)trap_Cvar_VariableValue( "s_useopenal" );
 		break;
-	}
-}
-
-/*
-=================
-SoundOptions_UpdateMenuItems
-=================
-*/
-static void SoundOptions_UpdateMenuItems( void )
-{
-	if ( soundOptionsInfo.soundSystem.curvalue == UISND_SDL )
-	{
-		soundOptionsInfo.quality.generic.flags &= ~QMF_GRAYED;
-	}
-	else
-	{
-		soundOptionsInfo.quality.generic.flags |= QMF_GRAYED;
-	}
-
-	soundOptionsInfo.apply.generic.flags |= QMF_HIDDEN|QMF_INACTIVE;
 
-	if ( soundOptionsInfo.sfxvolume_original != soundOptionsInfo.sfxvolume.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.musicvolume_original != soundOptionsInfo.musicvolume.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.soundSystem_original != soundOptionsInfo.soundSystem.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
-	if ( soundOptionsInfo.quality_original != soundOptionsInfo.quality.curvalue )
-	{
-		soundOptionsInfo.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
+	case ID_BACK:
+		UI_PopMenu();
+		break;
 	}
 }
 
-/*
-================
-SoundOptions_MenuDraw
-================
-*/
-void SoundOptions_MenuDraw (void)
-{
-//APSFIX - rework this
-	SoundOptions_UpdateMenuItems();
-
-	Menu_Draw( &soundOptionsInfo.menu );
-}
 
 /*
 ===============
@@ -235,14 +162,12 @@
 */
 static void UI_SoundOptionsMenu_Init( void ) {
 	int				y;
-	int				speed;
 
 	memset( &soundOptionsInfo, 0, sizeof(soundOptionsInfo) );
 
 	UI_SoundOptionsMenu_Cache();
 	soundOptionsInfo.menu.wrapAround = qtrue;
 	soundOptionsInfo.menu.fullscreen = qtrue;
-	soundOptionsInfo.menu.draw					= SoundOptions_MenuDraw;
 
 	soundOptionsInfo.banner.generic.type		= MTYPE_BTEXT;
 	soundOptionsInfo.banner.generic.flags		= QMF_CENTER_JUSTIFY;
@@ -308,7 +233,7 @@
 	soundOptionsInfo.network.style				= UI_RIGHT;
 	soundOptionsInfo.network.color				= color_red;
 
-	y = 240 - 2 * (BIGCHAR_HEIGHT + 2);
+	y = 240 - 1.5 * (BIGCHAR_HEIGHT + 2);
 	soundOptionsInfo.sfxvolume.generic.type		= MTYPE_SLIDER;
 	soundOptionsInfo.sfxvolume.generic.name		= "Effects Volume:";
 	soundOptionsInfo.sfxvolume.generic.flags	= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
@@ -331,25 +256,14 @@
 	soundOptionsInfo.musicvolume.maxvalue			= 10;
 
 	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.soundSystem.generic.type               = MTYPE_SPINCONTROL;
-	soundOptionsInfo.soundSystem.generic.name               = "Sound System:";
-	soundOptionsInfo.soundSystem.generic.flags              = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.soundSystem.generic.callback   = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.soundSystem.generic.id                 = ID_SOUNDSYSTEM;
-	soundOptionsInfo.soundSystem.generic.x                  = 400;
-	soundOptionsInfo.soundSystem.generic.y                  = y;
-	soundOptionsInfo.soundSystem.itemnames                  = soundSystem_items;
-
-	y += BIGCHAR_HEIGHT+2;
-	soundOptionsInfo.quality.generic.type           = MTYPE_SPINCONTROL;
-	soundOptionsInfo.quality.generic.name           = "SDL Sound Quality:";
-	soundOptionsInfo.quality.generic.flags          = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	soundOptionsInfo.quality.generic.callback       = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.quality.generic.id                     = ID_QUALITY;
-	soundOptionsInfo.quality.generic.x                      = 400;
-	soundOptionsInfo.quality.generic.y                      = y;
-	soundOptionsInfo.quality.itemnames                      = quality_items;
-
+	soundOptionsInfo.quality.generic.type		= MTYPE_SPINCONTROL;
+	soundOptionsInfo.quality.generic.name		= "Sound Quality:";
+	soundOptionsInfo.quality.generic.flags		= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	soundOptionsInfo.quality.generic.callback	= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.quality.generic.id			= ID_QUALITY;
+	soundOptionsInfo.quality.generic.x			= 400;
+	soundOptionsInfo.quality.generic.y			= y;
+	soundOptionsInfo.quality.itemnames			= quality_items;
 /*
 	y += BIGCHAR_HEIGHT+2;
 	soundOptionsInfo.a3d.generic.type			= MTYPE_RADIOBUTTON;
@@ -360,6 +274,15 @@
 	soundOptionsInfo.a3d.generic.x				= 400;
 	soundOptionsInfo.a3d.generic.y				= y;
 */
+	y += BIGCHAR_HEIGHT+2;
+	soundOptionsInfo.openal.generic.type			= MTYPE_RADIOBUTTON;
+	soundOptionsInfo.openal.generic.name			= "OpenAL:";
+	soundOptionsInfo.openal.generic.flags			= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
+	soundOptionsInfo.openal.generic.callback		= UI_SoundOptionsMenu_Event;
+	soundOptionsInfo.openal.generic.id				= ID_OPENAL;
+	soundOptionsInfo.openal.generic.x				= 400;
+	soundOptionsInfo.openal.generic.y				= y;
+
 	soundOptionsInfo.back.generic.type			= MTYPE_BITMAP;
 	soundOptionsInfo.back.generic.name			= ART_BACK0;
 	soundOptionsInfo.back.generic.flags			= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS;
@@ -371,17 +294,6 @@
 	soundOptionsInfo.back.height				= 64;
 	soundOptionsInfo.back.focuspic				= ART_BACK1;
 
-	soundOptionsInfo.apply.generic.type                     = MTYPE_BITMAP;
-	soundOptionsInfo.apply.generic.name                     = ART_ACCEPT0;
-	soundOptionsInfo.apply.generic.flags            = QMF_RIGHT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_HIDDEN|QMF_INACTIVE;
-	soundOptionsInfo.apply.generic.callback         = UI_SoundOptionsMenu_Event;
-	soundOptionsInfo.apply.generic.id                       = ID_APPLY;
-	soundOptionsInfo.apply.generic.x                        = 640;
-	soundOptionsInfo.apply.generic.y                        = 480-64;
-	soundOptionsInfo.apply.width                            = 128;
-	soundOptionsInfo.apply.height                           = 64;
-	soundOptionsInfo.apply.focuspic                         = ART_ACCEPT1;
-
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.banner );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.framel );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.framer );
@@ -391,35 +303,16 @@
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.network );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.sfxvolume );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.musicvolume );
-	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.soundSystem );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.quality );
 //	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.a3d );
+	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.openal );
 	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.back );
-	Menu_AddItem( &soundOptionsInfo.menu, ( void * ) &soundOptionsInfo.apply );
-
-	soundOptionsInfo.sfxvolume.curvalue = soundOptionsInfo.sfxvolume_original = trap_Cvar_VariableValue( "s_volume" ) * 10;
-	soundOptionsInfo.musicvolume.curvalue = soundOptionsInfo.musicvolume_original = trap_Cvar_VariableValue( "s_musicvolume" ) * 10;
-
-	if (trap_Cvar_VariableValue( "s_useOpenAL" ))
-		soundOptionsInfo.soundSystem_original = UISND_OPENAL;
-	else
-		soundOptionsInfo.soundSystem_original = UISND_SDL;
-
-	soundOptionsInfo.soundSystem.curvalue = soundOptionsInfo.soundSystem_original;
-
-	speed = trap_Cvar_VariableValue( "s_sdlSpeed" );
-	if (!speed) // Check for default
-		speed = DEFAULT_SDL_SND_SPEED;
-
-	if (speed <= 11025)
-		soundOptionsInfo.quality_original = 0;
-	else if (speed <= 22050)
-		soundOptionsInfo.quality_original = 1;
-	else // 44100
-		soundOptionsInfo.quality_original = 2;
-	soundOptionsInfo.quality.curvalue = soundOptionsInfo.quality_original;
 
+	soundOptionsInfo.sfxvolume.curvalue = trap_Cvar_VariableValue( "s_volume" ) * 10;
+	soundOptionsInfo.musicvolume.curvalue = trap_Cvar_VariableValue( "s_musicvolume" ) * 10;
+	soundOptionsInfo.quality.curvalue = !trap_Cvar_VariableValue( "s_compression" );
 //	soundOptionsInfo.a3d.curvalue = (int)trap_Cvar_VariableValue( "s_usingA3D" );
+	soundOptionsInfo.openal.curvalue = (int)trap_Cvar_VariableValue( "s_useopenal" );
 }
 
 
@@ -433,8 +326,6 @@
 	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
-	trap_R_RegisterShaderNoMip( ART_ACCEPT0 );
-	trap_R_RegisterShaderNoMip( ART_ACCEPT1 );
 }
 
 

```
