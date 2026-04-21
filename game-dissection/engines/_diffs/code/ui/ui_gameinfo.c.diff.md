# Diff: `code/ui/ui_gameinfo.c`
**Canonical:** `wolfcamql-src` (sha256 `81f26df0b69f...`, 8181 bytes)

## Variants

### `quake3-source`  — sha256 `19ee1eb133b8...`, 8010 bytes

_Diff stat: +11 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_gameinfo.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_gameinfo.c	2026-04-16 20:02:19.985150500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -38,7 +38,7 @@
 static int		ui_numArenas;
 static char		*ui_arenaInfos[MAX_ARENAS];
 
-#ifndef MISSIONPACK
+#ifndef MISSIONPACK // bk001206
 static int		ui_numSinglePlayerArenas;
 static int		ui_numSpecialSinglePlayerArenas;
 #endif
@@ -115,7 +115,7 @@
 		return;
 	}
 	if ( len >= MAX_ARENAS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_ARENAS_TEXT ) );
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_ARENAS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -136,12 +136,14 @@
 	int			numdirs;
 	vmCvar_t	arenasFile;
 	char		filename[128];
-	char		dirlist[4096];
+	char		dirlist[1024];
 	char*		dirptr;
-	int			i;
+	int			i, n;
 	int			dirlen;
+	char		*type;
 
 	ui_numArenas = 0;
+	uiInfo.mapCount = 0;
 
 	trap_Cvar_Register( &arenasFile, "g_arenasFile", "", CVAR_INIT|CVAR_ROM );
 	if( *arenasFile.string ) {
@@ -152,7 +154,7 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 1024 );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
@@ -162,20 +164,8 @@
 	}
 	trap_Print( va( "%i arenas parsed\n", ui_numArenas ) );
 	if (UI_OutOfMemory()) {
-		trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all arenas\n");
+		trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all arenas\n");
 	}
-}
-
-/*
-===============
-UI_LoadArenasIntoMapList
-===============
-*/
-void UI_LoadArenasIntoMapList( void ) {
-	int                     n;
-	char            *type;
-
-	uiInfo.mapCount = 0;
 
 	for( n = 0; n < ui_numArenas; n++ ) {
 		// determine type
@@ -236,7 +226,7 @@
 		return;
 	}
 	if ( len >= MAX_BOTS_TEXT ) {
-		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i\n", filename, len, MAX_BOTS_TEXT ) );
+		trap_Print( va( S_COLOR_RED "file too large: %s is %i, max allowed is %i", filename, len, MAX_BOTS_TEXT ) );
 		trap_FS_FCloseFile( f );
 		return;
 	}
@@ -320,7 +310,7 @@
 	return NULL;
 }
 
-int UI_GetNumBots( void ) {
+int UI_GetNumBots() {
 	return ui_numBots;
 }
 

```

### `ioquake3`  — sha256 `673eb889979f...`, 8153 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_gameinfo.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\ui\ui_gameinfo.c	2026-04-16 20:02:21.811557000 +0100
@@ -172,8 +172,8 @@
 ===============
 */
 void UI_LoadArenasIntoMapList( void ) {
-	int                     n;
-	char            *type;
+	int			n;
+	char		*type;
 
 	uiInfo.mapCount = 0;
 

```

### `openarena-engine`  — sha256 `6287625380cc...`, 8029 bytes

_Diff stat: +5 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_gameinfo.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_gameinfo.c	2026-04-16 22:48:25.958099000 +0100
@@ -136,12 +136,14 @@
 	int			numdirs;
 	vmCvar_t	arenasFile;
 	char		filename[128];
-	char		dirlist[4096];
+	char		dirlist[1024];
 	char*		dirptr;
-	int			i;
+	int			i, n;
 	int			dirlen;
+	char		*type;
 
 	ui_numArenas = 0;
+	uiInfo.mapCount = 0;
 
 	trap_Cvar_Register( &arenasFile, "g_arenasFile", "", CVAR_INIT|CVAR_ROM );
 	if( *arenasFile.string ) {
@@ -152,7 +154,7 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 1024 );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
@@ -164,18 +166,6 @@
 	if (UI_OutOfMemory()) {
 		trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all arenas\n");
 	}
-}
-
-/*
-===============
-UI_LoadArenasIntoMapList
-===============
-*/
-void UI_LoadArenasIntoMapList( void ) {
-	int                     n;
-	char            *type;
-
-	uiInfo.mapCount = 0;
 
 	for( n = 0; n < ui_numArenas; n++ ) {
 		// determine type

```

### `openarena-gamecode`  — sha256 `0d6f301a1cdf...`, 9585 bytes

_Diff stat: +80 / -54 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_gameinfo.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\ui\ui_gameinfo.c	2026-04-16 22:48:24.212592000 +0100
@@ -32,15 +32,15 @@
 //
 
 
-int				ui_numBots;
-static char		*ui_botInfos[MAX_BOTS];
+int             ui_numBots;
+static char     *ui_botInfos[MAX_BOTS];
 
-static int		ui_numArenas;
-static char		*ui_arenaInfos[MAX_ARENAS];
+static int      ui_numArenas;
+static char     *ui_arenaInfos[MAX_ARENAS];
 
-#ifndef MISSIONPACK
-static int		ui_numSinglePlayerArenas;
-static int		ui_numSpecialSinglePlayerArenas;
+#ifndef MISSIONPACK // bk001206
+static int      ui_numSinglePlayerArenas;
+static int      ui_numSpecialSinglePlayerArenas;
 #endif
 
 /*
@@ -49,10 +49,10 @@
 ===============
 */
 int UI_ParseInfos( char *buf, int max, char *infos[] ) {
-	char	*token;
-	int		count;
-	char	key[MAX_TOKEN_CHARS];
-	char	info[MAX_INFO_STRING];
+	char    *token;
+	int     count;
+	char    key[MAX_TOKEN_CHARS];
+	char    info[MAX_INFO_STRING];
 
 	count = 0;
 
@@ -105,9 +105,9 @@
 ===============
 */
 static void UI_LoadArenasFromFile( char *filename ) {
-	int				len;
-	fileHandle_t	f;
-	char			buf[MAX_ARENAS_TEXT];
+	int             len;
+	fileHandle_t    f;
+	char            buf[MAX_ARENAS_TEXT];
 
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( !f ) {
@@ -133,15 +133,22 @@
 ===============
 */
 void UI_LoadArenas( void ) {
-	int			numdirs;
-	vmCvar_t	arenasFile;
-	char		filename[128];
-	char		dirlist[4096];
-	char*		dirptr;
-	int			i;
-	int			dirlen;
+	int         numdirs;
+	vmCvar_t    arenasFile;
+	char        filename[128];
+	char        dirlist[1024];
+	char*       dirptr;
+	int         i;
+	int         n;
+	int         dirlen;
+	char        *type;
+	// rfactory changes
+	// Changed RD
+	char specialgame[100];
+	// end changed RD
 
 	ui_numArenas = 0;
+	uiInfo.mapCount = 0;
 
 	trap_Cvar_Register( &arenasFile, "g_arenasFile", "", CVAR_INIT|CVAR_ROM );
 	if( *arenasFile.string ) {
@@ -152,7 +159,7 @@
 	}
 
 	// get all arenas from .arena files
-	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 4096 );
+	numdirs = trap_FS_GetFileList("scripts", ".arena", dirlist, 1024 );
 	dirptr  = dirlist;
 	for (i = 0; i < numdirs; i++, dirptr += dirlen+1) {
 		dirlen = strlen(dirptr);
@@ -162,20 +169,8 @@
 	}
 	trap_Print( va( "%i arenas parsed\n", ui_numArenas ) );
 	if (UI_OutOfMemory()) {
-		trap_Print(S_COLOR_YELLOW"WARNING: not enough memory in pool to load all arenas\n");
+		trap_Print(S_COLOR_YELLOW"WARNING: not anough memory in pool to load all arenas\n");
 	}
-}
-
-/*
-===============
-UI_LoadArenasIntoMapList
-===============
-*/
-void UI_LoadArenasIntoMapList( void ) {
-	int                     n;
-	char            *type;
-
-	uiInfo.mapCount = 0;
 
 	for( n = 0; n < ui_numArenas; n++ ) {
 		// determine type
@@ -183,6 +178,12 @@
 		uiInfo.mapList[uiInfo.mapCount].cinematic = -1;
 		uiInfo.mapList[uiInfo.mapCount].mapLoadName = String_Alloc(Info_ValueForKey(ui_arenaInfos[n], "map"));
 		uiInfo.mapList[uiInfo.mapCount].mapName = String_Alloc(Info_ValueForKey(ui_arenaInfos[n], "longname"));
+		// rfactory changes
+		// Changed RD
+		uiInfo.mapList[uiInfo.mapCount].botName = String_Alloc(Info_ValueForKey(ui_arenaInfos[n], "bots"));
+		uiInfo.mapList[uiInfo.mapCount].special = String_Alloc(Info_ValueForKey(ui_arenaInfos[n], "special"));
+		uiInfo.mapList[uiInfo.mapCount].fraglimit = atoi(Info_ValueForKey( ui_arenaInfos[n], "fraglimit" ));
+		// end changed RD
 		uiInfo.mapList[uiInfo.mapCount].levelShot = -1;
 		uiInfo.mapList[uiInfo.mapCount].imageName = String_Alloc(va("levelshots/%s", uiInfo.mapList[uiInfo.mapCount].mapLoadName));
 		uiInfo.mapList[uiInfo.mapCount].typeBits = 0;
@@ -190,24 +191,49 @@
 		type = Info_ValueForKey( ui_arenaInfos[n], "type" );
 		// if no type specified, it will be treated as "ffa"
 		if( *type ) {
-			if( strstr( type, "ffa" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_FFA);
-			}
-			if( strstr( type, "tourney" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_TOURNAMENT);
-			}
-			if( strstr( type, "ctf" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_CTF);
-			}
-			if( strstr( type, "oneflag" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_1FCTF);
-			}
-			if( strstr( type, "overload" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_OBELISK);
-			}
-			if( strstr( type, "harvester" ) ) {
-				uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_HARVESTER);
-			}
+			// Changed RD
+			trap_Cvar_VariableStringBuffer( "ui_SpecialGame", specialgame, sizeof(specialgame) );
+//			if (!specialgame[0])
+//			{
+				if( strstr( type, "ffa" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_FFA);
+				}
+				if( strstr( type, "tourney" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_TOURNAMENT);
+				}
+				if( strstr( type, "team" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_TEAM);
+				}
+				if( strstr( type, "ctf" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_CTF);
+				}
+				if( strstr( type, "oneflag" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_1FCTF);
+				}
+				if( strstr( type, "overload" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_OBELISK);
+				}
+				if( strstr( type, "harvester" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_HARVESTER);
+				}
+				if( strstr( type, "elimination" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_ELIMINATION);
+				}
+				if( strstr( type, "ctfelimination" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_CTF_ELIMINATION);
+				}
+				if( strstr( type, "lms" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_LMS);
+				}
+				if( strstr( type, "dd" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_DOUBLE_D);
+				}
+				if( strstr( type, "dom" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_DOMINATION);
+				}
+				if( strstr( type, "pos" ) ) {
+					uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_POSSESSION);
+				}
 		} else {
 			uiInfo.mapList[uiInfo.mapCount].typeBits |= (1 << GT_FFA);
 		}
@@ -312,7 +338,7 @@
 
 	for ( n = 0; n < ui_numBots ; n++ ) {
 		value = Info_ValueForKey( ui_botInfos[n], "name" );
-		if ( !Q_stricmp( value, name ) ) {
+		if ( Q_strequal( value, name ) ) {
 			return ui_botInfos[n];
 		}
 	}

```
