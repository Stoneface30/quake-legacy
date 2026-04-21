# Diff: `code/q3_ui/ui_splevel.c`
**Canonical:** `wolfcamql-src` (sha256 `d299b93b5433...`, 31823 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `83d64e9f411e...`, 31577 bytes

_Diff stat: +6 / -14 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_splevel.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_splevel.c	2026-04-16 20:02:19.954191600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -130,7 +130,7 @@
 	char	model[MAX_QPATH];
 
 	Q_strncpyz( model, modelAndSkin, sizeof(model));
-	skin = strrchr( model, '/' );
+	skin = Q_strrchr( model, '/' );
 	if ( skin ) {
 		*skin++ = '\0';
 	}
@@ -183,7 +183,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 
@@ -199,11 +199,6 @@
 		}
 
 		botInfo = UI_GetBotInfoByName( bot );
-		if(!botInfo)
-		{
-			botInfo = UI_GetBotInfoByNumber( levelMenuInfo.numBots );
-		}
-	
 		if( botInfo ) {
 			levelMenuInfo.botPics[levelMenuInfo.numBots] = PlayerIconHandle( Info_ValueForKey( botInfo, "model" ) );
 			Q_strncpyz( levelMenuInfo.botNames[levelMenuInfo.numBots], Info_ValueForKey( botInfo, "name" ), 10 );
@@ -236,7 +231,7 @@
 		levelMenuInfo.levelScores[n] = 8;
 	}
 
-	Com_sprintf( levelMenuInfo.levelPicNames[n], sizeof(levelMenuInfo.levelPicNames[n]), "levelshots/%s.tga", map );
+	strcpy( levelMenuInfo.levelPicNames[n], va( "levelshots/%s.tga", map ) );
 	if( !trap_R_RegisterShaderNoMip( levelMenuInfo.levelPicNames[n] ) ) {
 		strcpy( levelMenuInfo.levelPicNames[n], ART_MAP_UNKNOWN );
 	}
@@ -368,11 +363,7 @@
 
 	// clear game variables
 	UI_NewGame();
-	if ( UI_GetSpecialArenaInfo( "training" ) ) {
-		trap_Cvar_SetValue( "ui_spSelection", -4 );
-	} else {
-		trap_Cvar_SetValue( "ui_spSelection", 0 );
-	}
+	trap_Cvar_SetValue( "ui_spSelection", -4 );
 
 	// make the level select menu re-initialize
 	UI_PopMenu();
@@ -729,6 +720,7 @@
 	skill = (int)trap_Cvar_VariableValue( "g_spSkill" );
 	if( skill < 1 || skill > 5 ) {
 		trap_Cvar_Set( "g_spSkill", "2" );
+		skill = 2;
 	}
 
 	memset( &levelMenuInfo, 0, sizeof(levelMenuInfo) );

```

### `openarena-engine`  — sha256 `95468f891bba...`, 31783 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_splevel.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_splevel.c	2026-04-16 22:48:25.902292600 +0100
@@ -183,7 +183,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 
@@ -236,7 +236,7 @@
 		levelMenuInfo.levelScores[n] = 8;
 	}
 
-	Com_sprintf( levelMenuInfo.levelPicNames[n], sizeof(levelMenuInfo.levelPicNames[n]), "levelshots/%s.tga", map );
+	strcpy( levelMenuInfo.levelPicNames[n], va( "levelshots/%s.tga", map ) );
 	if( !trap_R_RegisterShaderNoMip( levelMenuInfo.levelPicNames[n] ) ) {
 		strcpy( levelMenuInfo.levelPicNames[n], ART_MAP_UNKNOWN );
 	}

```

### `openarena-gamecode`  — sha256 `00fbcb3cc6b5...`, 31971 bytes

_Diff stat: +28 / -29 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_splevel.c	2026-04-16 20:02:25.213500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_splevel.c	2026-04-16 22:48:24.188498600 +0100
@@ -31,24 +31,24 @@
 #include "ui_local.h"
 
 
-#define ART_LEVELFRAME_FOCUS		"menu/art/maps_select"
-#define ART_LEVELFRAME_SELECTED		"menu/art/maps_selected"
-#define ART_ARROW					"menu/art/narrow_0"
-#define ART_ARROW_FOCUS				"menu/art/narrow_1"
-#define ART_MAP_UNKNOWN				"menu/art/unknownmap"
-#define ART_MAP_COMPLETE1			"menu/art/level_complete1"
-#define ART_MAP_COMPLETE2			"menu/art/level_complete2"
-#define ART_MAP_COMPLETE3			"menu/art/level_complete3"
-#define ART_MAP_COMPLETE4			"menu/art/level_complete4"
-#define ART_MAP_COMPLETE5			"menu/art/level_complete5"
-#define ART_BACK0					"menu/art/back_0"
-#define ART_BACK1					"menu/art/back_1"	
-#define ART_FIGHT0					"menu/art/fight_0"
-#define ART_FIGHT1					"menu/art/fight_1"
-#define ART_RESET0					"menu/art/reset_0"
-#define ART_RESET1					"menu/art/reset_1"	
-#define ART_CUSTOM0					"menu/art/skirmish_0"
-#define ART_CUSTOM1					"menu/art/skirmish_1"
+#define ART_LEVELFRAME_FOCUS		"menu/" MENU_ART_DIR "/maps_select"
+#define ART_LEVELFRAME_SELECTED		"menu/" MENU_ART_DIR "/maps_selected"
+#define ART_ARROW			"menu/" MENU_ART_DIR "/narrow_0"
+#define ART_ARROW_FOCUS			"menu/" MENU_ART_DIR "/narrow_1"
+#define ART_MAP_UNKNOWN			"menu/art/unknownmap"
+#define ART_MAP_COMPLETE1		"menu/art/level_complete1"
+#define ART_MAP_COMPLETE2		"menu/art/level_complete2"
+#define ART_MAP_COMPLETE3		"menu/art/level_complete3"
+#define ART_MAP_COMPLETE4		"menu/art/level_complete4"
+#define ART_MAP_COMPLETE5		"menu/art/level_complete5"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_FIGHT0			"menu/" MENU_ART_DIR "/fight_0"
+#define ART_FIGHT1			"menu/" MENU_ART_DIR "/fight_1"
+#define ART_RESET0			"menu/" MENU_ART_DIR "/reset_0"
+#define ART_RESET1			"menu/" MENU_ART_DIR "/reset_1"
+#define ART_CUSTOM0			"menu/" MENU_ART_DIR "/skirmish_0"
+#define ART_CUSTOM1			"menu/" MENU_ART_DIR "/skirmish_1"
 
 #define ID_LEFTARROW		10
 #define ID_PICTURE0			11
@@ -140,7 +140,7 @@
 
 	Com_sprintf(iconName, iconNameMaxSize, "models/players/%s/icon_%s.tga", model, skin );
 
-	if( !trap_R_RegisterShaderNoMip( iconName ) && Q_stricmp( skin, "default" ) != 0 ) {
+	if( !trap_R_RegisterShaderNoMip( iconName ) && !Q_strequal( skin, "default" ) ) {
 		Com_sprintf(iconName, iconNameMaxSize, "models/players/%s/icon_default.tga", model );
 	}
 }
@@ -180,7 +180,7 @@
 	p = &bots[0];
 	while( *p && levelMenuInfo.numBots < 7 ) {
 		//skip spaces
-		while( *p && *p == ' ' ) {
+		while( *p == ' ' ) {
 			p++;
 		}
 		if( !*p ) {
@@ -190,7 +190,7 @@
 		// mark start of bot name
 		bot = p;
 
-		// skip until space of null
+		// skip until space or null
 		while( *p && *p != ' ' ) {
 			p++;
 		}
@@ -199,11 +199,9 @@
 		}
 
 		botInfo = UI_GetBotInfoByName( bot );
-		if(!botInfo)
-		{
-			botInfo = UI_GetBotInfoByNumber( levelMenuInfo.numBots );
-		}
-	
+                if( !botInfo )	{
+                     botInfo = UI_GetBotInfoByNumber( levelMenuInfo.numBots );
+                }
 		if( botInfo ) {
 			levelMenuInfo.botPics[levelMenuInfo.numBots] = PlayerIconHandle( Info_ValueForKey( botInfo, "model" ) );
 			Q_strncpyz( levelMenuInfo.botNames[levelMenuInfo.numBots], Info_ValueForKey( botInfo, "name" ), 10 );
@@ -236,7 +234,7 @@
 		levelMenuInfo.levelScores[n] = 8;
 	}
 
-	Com_sprintf( levelMenuInfo.levelPicNames[n], sizeof(levelMenuInfo.levelPicNames[n]), "levelshots/%s.tga", map );
+	strcpy( levelMenuInfo.levelPicNames[n], va( "levelshots/%s.tga", map ) );
 	if( !trap_R_RegisterShaderNoMip( levelMenuInfo.levelPicNames[n] ) ) {
 		strcpy( levelMenuInfo.levelPicNames[n], ART_MAP_UNKNOWN );
 	}
@@ -564,7 +562,7 @@
 
 	// check for model changes
 	trap_Cvar_VariableStringBuffer( "model", buf, sizeof(buf) );
-	if( Q_stricmp( buf, levelMenuInfo.playerModel ) != 0 ) {
+	if( !Q_strequal( buf, levelMenuInfo.playerModel ) ) {
 		Q_strncpyz( levelMenuInfo.playerModel, buf, sizeof(levelMenuInfo.playerModel) );
 		PlayerIcon( levelMenuInfo.playerModel, levelMenuInfo.playerPicName, sizeof(levelMenuInfo.playerPicName) );
 		levelMenuInfo.item_player.shader = 0;
@@ -728,7 +726,8 @@
 
 	skill = (int)trap_Cvar_VariableValue( "g_spSkill" );
 	if( skill < 1 || skill > 5 ) {
-		trap_Cvar_Set( "g_spSkill", "2" );
+		skill = 2;
+		trap_Cvar_SetValue( "g_spSkill", (float)skill );
 	}
 
 	memset( &levelMenuInfo, 0, sizeof(levelMenuInfo) );

```
