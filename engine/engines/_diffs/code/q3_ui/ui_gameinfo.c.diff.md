# Diff: `code/q3_ui/ui_gameinfo.c`
**Canonical:** `wolfcamql-src` (sha256 `dc33b2d3dd9e...`, 17503 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `7cf2863bd199...`, 17648 bytes

_Diff stat: +15 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_gameinfo.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_gameinfo.c	2026-04-16 20:02:19.946829300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -148,7 +148,7 @@
 		return;
 	}
 	if ( len >= MAX_ARENAS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_ARENAS_TEXT ) );
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_ARENAS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -169,7 +169,7 @@
 	int			numdirs;
 	vmCvar_t	arenasFile;
 	char		filename[128];
-	char		dirlist[4096];
+	char		dirlist[1024];
 	char*		dirptr;
 	int			i, n;
 	int			dirlen;
@@ -188,7 +188,7 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 1024 );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
@@ -197,7 +197,7 @@
 		UI_LoadArenasFromFile(filename);
 	}
 	trap_Print( va( "%i arenas parsed\n", ui_numArenas ) );
-	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all arenas\n");
+	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all arenas\n");
 
 	// set initial numbers
 	for( n = 0; n < ui_numArenas; n++ ) {
@@ -337,7 +337,7 @@
 		return;
 	}
 	if ( len >= MAX_BOTS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_BOTS_TEXT ) );
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_BOTS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -347,7 +347,7 @@
 	trap_FS_FCloseFile( f );
 
 	ui_numBots += UI_ParseInfos( buf, MAX_BOTS - ui_numBots, &ui_botInfos[ui_numBots] );
-	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all bots\n");
+	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all bots\n");
 }
 
 /*
@@ -659,7 +659,7 @@
 */
 int UI_GetCurrentGame( void ) {
 	int		level;
-	int		rank = 0;
+	int		rank;
 	int		skill;
 	const char *info;
 
@@ -796,7 +796,7 @@
 
 	trap_Cvar_Set( "g_spAwards", awardData );
 
-	trap_Print( "All awards unlocked at 100\n" );
+	trap_Print( "All levels unlocked at 100\n" );
 }
 
 
@@ -811,5 +811,10 @@
 	UI_LoadArenas();
 	UI_LoadBots();
 
-	uis.demoversion = qfalse;
+	if( (trap_Cvar_VariableValue( "fs_restrict" )) || (ui_numSpecialSinglePlayerArenas == 0 && ui_numSinglePlayerArenas == 4) ) {
+		uis.demoversion = qtrue;
+	}
+	else {
+		uis.demoversion = qfalse;
+	}
 }

```

### `openarena-engine`  — sha256 `d8067ad81f3d...`, 17499 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_gameinfo.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_gameinfo.c	2026-04-16 22:48:25.895195900 +0100
@@ -169,7 +169,7 @@
 	int			numdirs;
 	vmCvar_t	arenasFile;
 	char		filename[128];
-	char		dirlist[4096];
+	char		dirlist[2048];
 	char*		dirptr;
 	int			i, n;
 	int			dirlen;
@@ -188,7 +188,7 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 2048 );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
@@ -659,7 +659,7 @@
 */
 int UI_GetCurrentGame( void ) {
 	int		level;
-	int		rank = 0;
+	int		rank;
 	int		skill;
 	const char *info;
 
@@ -796,7 +796,7 @@
 
 	trap_Cvar_Set( "g_spAwards", awardData );
 
-	trap_Print( "All awards unlocked at 100\n" );
+	trap_Print( "All levels unlocked at 100\n" );
 }
 
 

```

### `openarena-gamecode`  — sha256 `df6e53c79702...`, 17572 bytes

_Diff stat: +17 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_gameinfo.c	2026-04-16 20:02:25.206500400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_gameinfo.c	2026-04-16 22:48:24.182499300 +0100
@@ -94,7 +94,7 @@
 		if ( !token[0] ) {
 			break;
 		}
-		if ( strcmp( token, "{" ) ) {
+		if ( !strequals( token, "{" ) ) {
 			Com_Printf( "Missing { in info file\n" );
 			break;
 		}
@@ -111,7 +111,7 @@
 				Com_Printf( "Unexpected end of info file\n" );
 				break;
 			}
-			if ( !strcmp( token, "}" ) ) {
+			if ( strequals( token, "}" ) ) {
 				break;
 			}
 			Q_strncpyz( key, token, sizeof( key ) );
@@ -137,7 +137,7 @@
 UI_LoadArenasFromFile
 ===============
 */
-static void UI_LoadArenasFromFile( char *filename ) {
+static void UI_LoadArenasFromFile( const char *filename ) {
 	int				len;
 	fileHandle_t	f;
 	char			buf[MAX_ARENAS_TEXT];
@@ -169,13 +169,13 @@
 	int			numdirs;
 	vmCvar_t	arenasFile;
 	char		filename[128];
-	char		dirlist[4096];
+	char		dirlist[20*1024];
 	char*		dirptr;
 	int			i, n;
 	int			dirlen;
 	char		*type;
 	char		*tag;
-	int			singlePlayerNum, specialNum, otherNum;
+	int		singlePlayerNum, specialNum, otherNum;
 
 	ui_numArenas = 0;
 
@@ -188,16 +188,16 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, sizeof(dirlist) );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
-		strcpy(filename, "scripts/");
-		strcat(filename, dirptr);
+		Q_snprintf(filename, sizeof(filename), "scripts/%s", dirptr);
 		UI_LoadArenasFromFile(filename);
+		trap_Print( va( "Read %s\n", filename ) );
 	}
 	trap_Print( va( "%i arenas parsed\n", ui_numArenas ) );
-	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all arenas\n");
+	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all arenas\n");
 
 	// set initial numbers
 	for( n = 0; n < ui_numArenas; n++ ) {
@@ -237,7 +237,7 @@
 	// go through once more and assign number to the levels
 	singlePlayerNum = 0;
 	specialNum = singlePlayerNum + ui_numSinglePlayerArenas;
-	otherNum = specialNum + ui_numSpecialSinglePlayerArenas;
+	otherNum = specialNum + ui_numSpecialSinglePlayerArenas + n;
 	for( n = 0; n < ui_numArenas; n++ ) {
 		// determine type
 		type = Info_ValueForKey( ui_arenaInfos[n], "type" );
@@ -295,7 +295,7 @@
 	int			n;
 
 	for( n = 0; n < ui_numArenas; n++ ) {
-		if( Q_stricmp( Info_ValueForKey( ui_arenaInfos[n], "map" ), map ) == 0 ) {
+		if( Q_strequal( Info_ValueForKey( ui_arenaInfos[n], "map" ), map ) ) {
 			return ui_arenaInfos[n];
 		}
 	}
@@ -313,7 +313,7 @@
 	int			n;
 
 	for( n = 0; n < ui_numArenas; n++ ) {
-		if( Q_stricmp( Info_ValueForKey( ui_arenaInfos[n], "special" ), tag ) == 0 ) {
+		if( Q_strequal( Info_ValueForKey( ui_arenaInfos[n], "special" ), tag ) ) {
 			return ui_arenaInfos[n];
 		}
 	}
@@ -347,7 +347,7 @@
 	trap_FS_FCloseFile( f );
 
 	ui_numBots += UI_ParseInfos( buf, MAX_BOTS - ui_numBots, &ui_botInfos[ui_numBots] );
-	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all bots\n");
+	if (outOfMemory) trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all bots\n");
 }
 
 /*
@@ -379,8 +379,7 @@
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
-		strcpy(filename, "scripts/");
-		strcat(filename, dirptr);
+		Q_snprintf(filename, sizeof(filename), "scripts/%s", dirptr);
 		UI_LoadBotsFromFile(filename);
 	}
 	trap_Print( va( "%i bots parsed\n", ui_numBots ) );
@@ -412,7 +411,7 @@
 
 	for ( n = 0; n < ui_numBots ; n++ ) {
 		value = Info_ValueForKey( ui_botInfos[n], "name" );
-		if ( !Q_stricmp( value, name ) ) {
+		if ( Q_strequal( value, name ) ) {
 			return ui_botInfos[n];
 		}
 	}
@@ -659,7 +658,7 @@
 */
 int UI_GetCurrentGame( void ) {
 	int		level;
-	int		rank = 0;
+	int		rank;
 	int		skill;
 	const char *info;
 
@@ -796,7 +795,7 @@
 
 	trap_Cvar_Set( "g_spAwards", awardData );
 
-	trap_Print( "All awards unlocked at 100\n" );
+	trap_Print( "All levels unlocked at 100\n" );
 }
 
 

```
