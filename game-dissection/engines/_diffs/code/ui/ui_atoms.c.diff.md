# Diff: `code/ui/ui_atoms.c`
**Canonical:** `wolfcamql-src` (sha256 `af21833f64e0...`, 14588 bytes)

## Variants

### `quake3-source`  — sha256 `4745f5229db3...`, 14622 bytes

_Diff stat: +27 / -22 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_atoms.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_atoms.c	2026-04-16 20:02:19.985150500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,15 +29,18 @@
 
 qboolean		m_entersound;		// after a frame, so caching won't disrupt the sound
 
+// these are here so the functions in q_shared.c can link
+#ifndef UI_HARD_LINKED
+
 void QDECL Com_Error( int level, const char *error, ... ) {
 	va_list		argptr;
 	char		text[1024];
 
 	va_start (argptr, error);
-	Q_vsnprintf (text, sizeof(text), error, argptr);
+	vsprintf (text, error, argptr);
 	va_end (argptr);
 
-	trap_Error( text );
+	trap_Error( va("%s", text) );
 }
 
 void QDECL Com_Printf( const char *msg, ... ) {
@@ -45,12 +48,14 @@
 	char		text[1024];
 
 	va_start (argptr, msg);
-	Q_vsnprintf (text, sizeof(text), msg, argptr);
+	vsprintf (text, msg, argptr);
 	va_end (argptr);
 
-	trap_Print( text );
+	trap_Print( va("%s", text) );
 }
 
+#endif
+
 qboolean newUI = qfalse;
 
 
@@ -76,7 +81,7 @@
 }
 
 
-#ifndef MISSIONPACK
+#ifndef MISSIONPACK // bk001206
 static void NeedCDAction( qboolean result ) {
 	if ( !result ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
@@ -84,7 +89,7 @@
 }
 #endif // MISSIONPACK
 
-#ifndef MISSIONPACK
+#ifndef MISSIONPACK // bk001206
 static void NeedCDKeyAction( qboolean result ) {
 	if ( !result ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
@@ -146,8 +151,7 @@
 	}
 }
 
-void UI_LoadBestScores(const char *map, int game)
-{
+void UI_LoadBestScores(const char *map, int game) {
 	char		fileName[MAX_QPATH];
 	fileHandle_t f;
 	postGameInfo_t newInfo;
@@ -163,7 +167,7 @@
 	}
 	UI_SetBestScores(&newInfo, qfalse);
 
-	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, (int)trap_Cvar_VariableValue("protocol"));
+	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.dm_%d", map, game, (int)trap_Cvar_VariableValue("protocol"));
 	uiInfo.demoAvailable = qfalse;
 	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
 		uiInfo.demoAvailable = qtrue;
@@ -176,7 +180,7 @@
 UI_ClearScores
 ===============
 */
-void UI_ClearScores(void) {
+void UI_ClearScores() {
 	char	gameList[4096];
 	char *gameFile;
 	int		i, len, count, size;
@@ -207,7 +211,7 @@
 
 
 
-static void	UI_Cache_f( void ) {
+static void	UI_Cache_f() {
 	Display_CacheAll();
 }
 
@@ -216,7 +220,7 @@
 UI_CalcPostGameStats
 =======================
 */
-static void UI_CalcPostGameStats( void ) {
+static void UI_CalcPostGameStats() {
 	char		map[MAX_QPATH];
 	char		fileName[MAX_QPATH];
 	char		info[MAX_INFO_STRING];
@@ -330,14 +334,13 @@
 
 	if ( Q_stricmp (cmd, "ui_test") == 0 ) {
 		UI_ShowPostGame(qtrue);
-		return qtrue;
 	}
 
 	if ( Q_stricmp (cmd, "ui_report") == 0 ) {
 		UI_Report();
 		return qtrue;
 	}
-
+	
 	if ( Q_stricmp (cmd, "ui_load") == 0 ) {
 		UI_Load();
 		return qtrue;
@@ -347,14 +350,9 @@
 		if (trap_Argc() == 4) {
 			char shader1[MAX_QPATH];
 			char shader2[MAX_QPATH];
-			//char shader3[MAX_QPATH];  // what????
-			char timeOffset[128];
-
 			Q_strncpyz(shader1, UI_Argv(1), sizeof(shader1));
 			Q_strncpyz(shader2, UI_Argv(2), sizeof(shader2));
-			Q_strncpyz(timeOffset, UI_Argv(3), sizeof(timeOffset));
-
-			trap_R_RemapShader(shader1, shader2, timeOffset);
+			trap_R_RemapShader(shader1, shader2, UI_Argv(3));
 			return qtrue;
 		}
 	}
@@ -400,7 +398,14 @@
 */
 void UI_AdjustFrom640( float *x, float *y, float *w, float *h ) {
 	// expect valid pointers
-	*x = *x * uiInfo.uiDC.xscale + uiInfo.uiDC.bias;
+#if 0
+	*x = *x * uiInfo.uiDC.scale + uiInfo.uiDC.bias;
+	*y *= uiInfo.uiDC.scale;
+	*w *= uiInfo.uiDC.scale;
+	*h *= uiInfo.uiDC.scale;
+#endif
+
+	*x *= uiInfo.uiDC.xscale;
 	*y *= uiInfo.uiDC.yscale;
 	*w *= uiInfo.uiDC.xscale;
 	*h *= uiInfo.uiDC.yscale;

```

### `ioquake3`  — sha256 `1368efdc141e...`, 15052 bytes

_Diff stat: +29 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_atoms.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\ui\ui_atoms.c	2026-04-16 20:02:21.811557000 +0100
@@ -151,6 +151,8 @@
 	char		fileName[MAX_QPATH];
 	fileHandle_t f;
 	postGameInfo_t newInfo;
+	int protocol, protocolLegacy;
+	
 	memset(&newInfo, 0, sizeof(postGameInfo_t));
 	Com_sprintf(fileName, MAX_QPATH, "games/%s_%i.game", map, game);
 	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
@@ -163,11 +165,30 @@
 	}
 	UI_SetBestScores(&newInfo, qfalse);
 
-	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, (int)trap_Cvar_VariableValue("protocol"));
 	uiInfo.demoAvailable = qfalse;
-	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
+
+	protocolLegacy = trap_Cvar_VariableValue("com_legacyprotocol");
+	protocol = trap_Cvar_VariableValue("com_protocol");
+
+	if(!protocol)
+		protocol = trap_Cvar_VariableValue("protocol");
+	if(protocolLegacy == protocol)
+		protocolLegacy = 0;
+
+	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, protocol);
+	if(trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0)
+	{
 		uiInfo.demoAvailable = qtrue;
 		trap_FS_FCloseFile(f);
+	}
+	else if(protocolLegacy > 0)
+	{
+		Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, protocolLegacy);
+		if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0)
+		{
+			uiInfo.demoAvailable = qtrue;
+			trap_FS_FCloseFile(f);
+		}
 	} 
 }
 
@@ -337,7 +358,7 @@
 		UI_Report();
 		return qtrue;
 	}
-
+	
 	if ( Q_stricmp (cmd, "ui_load") == 0 ) {
 		UI_Load();
 		return qtrue;
@@ -347,14 +368,13 @@
 		if (trap_Argc() == 4) {
 			char shader1[MAX_QPATH];
 			char shader2[MAX_QPATH];
-			//char shader3[MAX_QPATH];  // what????
-			char timeOffset[128];
-
+			char shader3[MAX_QPATH];
+			
 			Q_strncpyz(shader1, UI_Argv(1), sizeof(shader1));
 			Q_strncpyz(shader2, UI_Argv(2), sizeof(shader2));
-			Q_strncpyz(timeOffset, UI_Argv(3), sizeof(timeOffset));
-
-			trap_R_RemapShader(shader1, shader2, timeOffset);
+			Q_strncpyz(shader3, UI_Argv(3), sizeof(shader3));
+			
+			trap_R_RemapShader(shader1, shader2, shader3);
 			return qtrue;
 		}
 	}
@@ -404,7 +424,6 @@
 	*y *= uiInfo.uiDC.yscale;
 	*w *= uiInfo.uiDC.xscale;
 	*h *= uiInfo.uiDC.yscale;
-
 }
 
 void UI_DrawNamedPic( float x, float y, float width, float height, const char *picname ) {

```

### `openarena-engine`  — sha256 `2caa22d26c5f...`, 15179 bytes

_Diff stat: +37 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_atoms.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_atoms.c	2026-04-16 22:48:25.958099000 +0100
@@ -151,6 +151,8 @@
 	char		fileName[MAX_QPATH];
 	fileHandle_t f;
 	postGameInfo_t newInfo;
+	int protocol, protocolLegacy;
+	
 	memset(&newInfo, 0, sizeof(postGameInfo_t));
 	Com_sprintf(fileName, MAX_QPATH, "games/%s_%i.game", map, game);
 	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
@@ -163,11 +165,30 @@
 	}
 	UI_SetBestScores(&newInfo, qfalse);
 
-	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, (int)trap_Cvar_VariableValue("protocol"));
 	uiInfo.demoAvailable = qfalse;
-	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
+
+	protocolLegacy = trap_Cvar_VariableValue("com_legacyprotocol");
+	protocol = trap_Cvar_VariableValue("com_protocol");
+
+	if(!protocol)
+		protocol = trap_Cvar_VariableValue("protocol");
+	if(protocolLegacy == protocol)
+		protocolLegacy = 0;
+
+	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, protocol);
+	if(trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0)
+	{
 		uiInfo.demoAvailable = qtrue;
 		trap_FS_FCloseFile(f);
+	}
+	else if(protocolLegacy > 0)
+	{
+		Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, protocolLegacy);
+		if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0)
+		{
+			uiInfo.demoAvailable = qtrue;
+			trap_FS_FCloseFile(f);
+		}
 	} 
 }
 
@@ -337,7 +358,7 @@
 		UI_Report();
 		return qtrue;
 	}
-
+	
 	if ( Q_stricmp (cmd, "ui_load") == 0 ) {
 		UI_Load();
 		return qtrue;
@@ -347,14 +368,13 @@
 		if (trap_Argc() == 4) {
 			char shader1[MAX_QPATH];
 			char shader2[MAX_QPATH];
-			//char shader3[MAX_QPATH];  // what????
-			char timeOffset[128];
-
+			char shader3[MAX_QPATH];
+			
 			Q_strncpyz(shader1, UI_Argv(1), sizeof(shader1));
 			Q_strncpyz(shader2, UI_Argv(2), sizeof(shader2));
-			Q_strncpyz(timeOffset, UI_Argv(3), sizeof(timeOffset));
-
-			trap_R_RemapShader(shader1, shader2, timeOffset);
+			Q_strncpyz(shader3, UI_Argv(3), sizeof(shader3));
+			
+			trap_R_RemapShader(shader1, shader2, shader3);
 			return qtrue;
 		}
 	}
@@ -400,7 +420,14 @@
 */
 void UI_AdjustFrom640( float *x, float *y, float *w, float *h ) {
 	// expect valid pointers
-	*x = *x * uiInfo.uiDC.xscale + uiInfo.uiDC.bias;
+#if 0
+	*x = *x * uiInfo.uiDC.scale + uiInfo.uiDC.bias;
+	*y *= uiInfo.uiDC.scale;
+	*w *= uiInfo.uiDC.scale;
+	*h *= uiInfo.uiDC.scale;
+#endif
+
+	*x *= uiInfo.uiDC.xscale;
 	*y *= uiInfo.uiDC.yscale;
 	*w *= uiInfo.uiDC.xscale;
 	*h *= uiInfo.uiDC.yscale;

```

### `openarena-gamecode`  — sha256 `9441f11c74f0...`, 17074 bytes

_Diff stat: +105 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_atoms.c	2026-04-16 20:02:25.816935500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\ui\ui_atoms.c	2026-04-16 22:48:24.211592100 +0100
@@ -37,7 +37,7 @@
 	Q_vsnprintf (text, sizeof(text), error, argptr);
 	va_end (argptr);
 
-	trap_Error( text );
+	trap_Error( va("%s", text) );
 }
 
 void QDECL Com_Printf( const char *msg, ... ) {
@@ -48,7 +48,7 @@
 	Q_vsnprintf (text, sizeof(text), msg, argptr);
 	va_end (argptr);
 
-	trap_Print( text );
+	trap_Print( va("%s", text) );
 }
 
 qboolean newUI = qfalse;
@@ -76,7 +76,7 @@
 }
 
 
-#ifndef MISSIONPACK
+#ifndef MISSIONPACK // bk001206
 static void NeedCDAction( qboolean result ) {
 	if ( !result ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
@@ -84,7 +84,7 @@
 }
 #endif // MISSIONPACK
 
-#ifndef MISSIONPACK
+#ifndef MISSIONPACK // bk001206
 static void NeedCDKeyAction( qboolean result ) {
 	if ( !result ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
@@ -127,7 +127,7 @@
 	trap_Cvar_Set("ui_scoreShutoutBonus",	va("%i", newInfo->shutoutBonus));
 	trap_Cvar_Set("ui_scoreTime",					va("%02i:%02i", newInfo->time / 60, newInfo->time % 60));
 	trap_Cvar_Set("ui_scoreCaptures",		va("%i", newInfo->captures));
-  if (postGame) {
+	if (postGame) {
 		trap_Cvar_Set("ui_scoreAccuracy2",     va("%i%%", newInfo->accuracy));
 		trap_Cvar_Set("ui_scoreImpressives2",	va("%i", newInfo->impressives));
 		trap_Cvar_Set("ui_scoreExcellents2", 	va("%i", newInfo->excellents));
@@ -146,8 +146,7 @@
 	}
 }
 
-void UI_LoadBestScores(const char *map, int game)
-{
+void UI_LoadBestScores(const char *map, int game) {
 	char		fileName[MAX_QPATH];
 	fileHandle_t f;
 	postGameInfo_t newInfo;
@@ -163,7 +162,7 @@
 	}
 	UI_SetBestScores(&newInfo, qfalse);
 
-	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.%s%d", map, game, DEMOEXT, (int)trap_Cvar_VariableValue("protocol"));
+	Com_sprintf(fileName, MAX_QPATH, "demos/%s_%d.dm_%d", map, game, (int)trap_Cvar_VariableValue("protocol"));
 	uiInfo.demoAvailable = qfalse;
 	if (trap_FS_FOpenFile(fileName, &f, FS_READ) >= 0) {
 		uiInfo.demoAvailable = qtrue;
@@ -311,6 +310,74 @@
 
 }
 
+/*
+=======================
+ui_randomIntToCvar CVAR minInt maxInt
+Sets the CVAR to a random integer between minInt and maxInt (both included)
+=======================
+*/
+static void ui_randomIntToCvar( void ) {
+	if (trap_Argc() == 4) {
+		char cvarName[MAX_QPATH];
+		char minIntString[MAX_QPATH];
+		char maxIntString[MAX_QPATH];
+		int minInt = 0;
+		int maxInt = 0;
+		Q_strncpyz(cvarName, UI_Argv(1), sizeof(cvarName));
+		Q_strncpyz(minIntString, UI_Argv(2), sizeof(minIntString));
+		Q_strncpyz(maxIntString, UI_Argv(3), sizeof(maxIntString));
+		minInt = atoi(minIntString);
+		maxInt = atoi(maxIntString)+1;
+		if (minInt >= maxInt) {
+			Com_Printf("maxInt (%d) must be greater than minInt (%d)\n", maxInt-1, minInt);
+			return;
+		}
+		if (maxInt-minInt > RAND_MAX) {
+			Com_Printf("The difference between min and max (%d) is larger than %d\n", maxInt-minInt, RAND_MAX);
+			return;
+		}
+		trap_Cvar_SetValue(cvarName, minInt+rand()%(maxInt-minInt));
+	}
+	else {
+		Com_Printf("Must be called like: ui_randomIntToCvar CVAR min max\n");
+	}
+}
+
+static void ui_randomFloatToCvar( void ) {
+	if (trap_Argc() == 4) {
+		char cvarName[MAX_QPATH];
+		char minFloatString[MAX_QPATH];
+		char maxFloatString[MAX_QPATH];
+		float minFloat = 0;
+		float maxFloat = 0;
+		Q_strncpyz(cvarName, UI_Argv(1), sizeof(cvarName));
+		Q_strncpyz(minFloatString, UI_Argv(2), sizeof(minFloatString));
+		Q_strncpyz(maxFloatString, UI_Argv(3), sizeof(maxFloatString));
+		minFloat = atof(minFloatString);
+		maxFloat = atof(maxFloatString);
+		if (minFloat >= maxFloat) {
+			Com_Printf("max (%f) must be greater than min (%f)\n", maxFloat, minFloat);
+			return;
+		}
+		trap_Cvar_SetValue(cvarName, minFloat+((maxFloat+minFloat)*(float)rand()/(float)RAND_MAX));
+	}
+	else {
+		Com_Printf("Must be called like: ui_randomIntToCvar CVAR min max\n");
+	}
+	return;
+}
+
+static void ui_randomStringToCvar( void ) {
+	char cvarName[MAX_QPATH];
+	int choice = rand();
+	if (trap_Argc() < 2) {
+		Com_Printf("Must be called like: ui_randomStringToCvar CVAR string1 stringN...\n");
+		return;
+	}
+	Q_strncpyz(cvarName, UI_Argv(1), sizeof(cvarName));
+	trap_Cvar_Set(cvarName, UI_Argv(2+choice%(trap_Argc()-2)));
+	return;
+}
 
 /*
 =================
@@ -330,52 +397,64 @@
 
 	if ( Q_stricmp (cmd, "ui_test") == 0 ) {
 		UI_ShowPostGame(qtrue);
-		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_report") == 0 ) {
+	if ( Q_strequal(cmd, "ui_report") ) {
 		UI_Report();
 		return qtrue;
 	}
-
-	if ( Q_stricmp (cmd, "ui_load") == 0 ) {
+	
+	if ( Q_strequal(cmd, "ui_load") ) {
 		UI_Load();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "remapShader") == 0 ) {
+	if ( Q_strequal(cmd, "remapShader") ) {
 		if (trap_Argc() == 4) {
 			char shader1[MAX_QPATH];
 			char shader2[MAX_QPATH];
-			//char shader3[MAX_QPATH];  // what????
-			char timeOffset[128];
-
+			char shader3[MAX_QPATH];
+			
 			Q_strncpyz(shader1, UI_Argv(1), sizeof(shader1));
 			Q_strncpyz(shader2, UI_Argv(2), sizeof(shader2));
-			Q_strncpyz(timeOffset, UI_Argv(3), sizeof(timeOffset));
-
-			trap_R_RemapShader(shader1, shader2, timeOffset);
+			Q_strncpyz(shader3, UI_Argv(3), sizeof(shader3));
+			
+			trap_R_RemapShader(shader1, shader2, shader3);
 			return qtrue;
 		}
 	}
 
-	if ( Q_stricmp (cmd, "postgame") == 0 ) {
+	if ( Q_strequal(cmd, "postgame") ) {
 		UI_CalcPostGameStats();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_cache") == 0 ) {
+	if ( Q_strequal(cmd, "ui_cache") ) {
 		UI_Cache_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_teamOrders") == 0 ) {
+	if ( Q_strequal(cmd, "ui_teamOrders") ) {
 		//UI_TeamOrdersMenu_f();
 		return qtrue;
 	}
 
+	if ( Q_strequal(cmd, "ui_randomIntToCvar") ) {
+		ui_randomIntToCvar();
+		return qtrue;
+	}
+
+	if ( Q_strequal(cmd, "ui_randomFloatToCvar") ) {
+		ui_randomFloatToCvar();
+		return qtrue;
+	}
 
-	if ( Q_stricmp (cmd, "ui_cdkey") == 0 ) {
+	if ( Q_strequal(cmd, "ui_randomStringToCvar") ) {
+		ui_randomStringToCvar();
+		return qtrue;
+	}
+
+	if ( Q_strequal(cmd, "ui_cdkey") ) {
 		//UI_CDKeyMenu_f();
 		return qtrue;
 	}
@@ -400,11 +479,10 @@
 */
 void UI_AdjustFrom640( float *x, float *y, float *w, float *h ) {
 	// expect valid pointers
-	*x = *x * uiInfo.uiDC.xscale + uiInfo.uiDC.bias;
+	*x = *x * uiInfo.uiDC.xscale + uiInfo.uiDC.bias;		// leilei - widescreen adjust
 	*y *= uiInfo.uiDC.yscale;
 	*w *= uiInfo.uiDC.xscale;
 	*h *= uiInfo.uiDC.yscale;
-
 }
 
 void UI_DrawNamedPic( float x, float y, float width, float height, const char *picname ) {
@@ -482,8 +560,8 @@
 void UI_DrawRect( float x, float y, float width, float height, const float *color ) {
 	trap_R_SetColor( color );
 
-  UI_DrawTopBottom(x, y, width, height);
-  UI_DrawSides(x, y, width, height);
+	UI_DrawTopBottom(x, y, width, height);
+	UI_DrawSides(x, y, width, height);
 
 	trap_R_SetColor( NULL );
 }

```
