# Diff: `code/q3_ui/ui_mods.c`
**Canonical:** `wolfcamql-src` (sha256 `e66279658fa1...`, 6820 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `41a036f9d569...`, 7582 bytes

_Diff stat: +37 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mods.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_mods.c	2026-04-16 20:02:19.948586100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -106,6 +106,42 @@
 }
 
 
+#if 0 // bk001204 - unused
+/*
+===============
+UI_Mods_LoadModsFromFile
+===============
+*/
+static void UI_Mods_LoadModsFromFile( char *filename ) {
+	int				len;
+	fileHandle_t	f;
+	char			buf[1024];
+
+	len = trap_FS_FOpenFile( filename, &f, FS_READ );
+	if ( !f ) {
+		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		return;
+	}
+	if ( len >= sizeof(buf) ) {
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, sizeof(buf) ) );
+		trap_FS_FCloseFile( f );
+		return;
+	}
+
+	trap_FS_Read( buf, len, f );
+	buf[len] = 0;
+	trap_FS_FCloseFile( f );
+
+	len = strlen( filename );
+	if( !Q_stricmp(filename +  len - 4,".mod") ) {
+		filename[len-4] = '\0';
+	}
+
+	UI_Mods_ParseInfos( filename, buf );
+}
+#endif
+
+
 /*
 ===============
 UI_Mods_LoadMods

```

### `openarena-gamecode`  — sha256 `9d4e076f1413...`, 8046 bytes

_Diff stat: +62 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mods.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_mods.c	2026-04-16 22:48:24.184499000 +0100
@@ -22,12 +22,12 @@
 //
 #include "ui_local.h"
 
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"	
-#define ART_FIGHT0			"menu/art/load_0"
-#define ART_FIGHT1			"menu/art/load_1"
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_FIGHT0			"menu/" MENU_ART_DIR "/load_0"
+#define ART_FIGHT1			"menu/" MENU_ART_DIR "/load_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
 
 #define MAX_MODS			64
 #define NAMEBUFSIZE			( MAX_MODS * 48 )
@@ -106,6 +106,42 @@
 }
 
 
+#if 0 // bk001204 - unused
+/*
+===============
+UI_Mods_LoadModsFromFile
+===============
+*/
+static void UI_Mods_LoadModsFromFile( char *filename ) {
+	int				len;
+	fileHandle_t	f;
+	char			buf[1024];
+
+	len = trap_FS_FOpenFile( filename, &f, FS_READ );
+	if ( !f ) {
+		trap_Print( va( S_COLOR_RED "file not found: %s\n", filename ) );
+		return;
+	}
+	if ( len >= sizeof(buf) ) {
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, sizeof(buf) ) );
+		trap_FS_FCloseFile( f );
+		return;
+	}
+
+	trap_FS_Read( buf, len, f );
+	buf[len] = 0;
+	trap_FS_FCloseFile( f );
+
+	len = strlen( filename );
+	if( Q_strequal(filename +  len - 4,".mod") ) {
+		filename[len-4] = '\0';
+	}
+
+	UI_Mods_ParseInfos( filename, buf );
+}
+#endif
+
+
 /*
 ===============
 UI_Mods_LoadMods
@@ -123,9 +159,9 @@
 	s_mods.descriptionPtr = s_mods.description;
 	s_mods.fs_gamePtr = s_mods.fs_game;
 
-	// always start off with baseq3
+	// always start off with baseoa
 	s_mods.list.numitems = 1;
-	s_mods.list.itemnames[0] = s_mods.descriptionList[0] = "Quake III Arena";
+	s_mods.list.itemnames[0] = s_mods.descriptionList[0] = "OpenArena";
 	s_mods.fs_gameList[0] = "";
 
 	numdirs = trap_FS_GetFileList( "$modlist", "", dirlist, sizeof(dirlist) );
@@ -143,6 +179,21 @@
 	}
 }
 
+/*
+=================
+UI_ModsMenu_Key
+=================
+*/
+static sfxHandle_t UI_ModsMenu_Key( int key ) {
+	if( key == K_MWHEELUP ) {
+		ScrollList_Key( &s_mods.list, K_UPARROW );
+	}
+
+	if( key == K_MWHEELDOWN ) {
+		ScrollList_Key( &s_mods.list, K_DOWNARROW );
+	}
+	return Menu_DefaultKey( &s_mods.menu, key );
+}
 
 /*
 ===============
@@ -153,6 +204,9 @@
 	UI_ModsMenu_Cache();
 
 	memset( &s_mods, 0 ,sizeof(mods_t) );
+
+        s_mods.menu.key = UI_ModsMenu_Key;
+
 	s_mods.menu.wrapAround = qtrue;
 	s_mods.menu.fullscreen = qtrue;
 

```
