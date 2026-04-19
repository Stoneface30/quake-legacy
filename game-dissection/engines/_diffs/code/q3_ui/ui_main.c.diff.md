# Diff: `code/q3_ui/ui_main.c`
**Canonical:** `wolfcamql-src` (sha256 `d57cb78d4249...`, 7674 bytes)

## Variants

### `quake3-source`  — sha256 `f155558775eb...`, 7216 bytes

_Diff stat: +17 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_main.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_main.c	2026-04-16 20:02:19.948079200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -40,7 +40,7 @@
 This must be the very first function compiled into the .qvm file
 ================
 */
-Q_EXPORT intptr_t vmMain( int command, int arg0, int arg1, int arg2, int arg3, int arg4, int arg5, int arg6, int arg7, int arg8, int arg9, int arg10, int arg11  ) {
+int vmMain( int command, int arg0, int arg1, int arg2, int arg3, int arg4, int arg5, int arg6, int arg7, int arg8, int arg9, int arg10, int arg11  ) {
 	switch ( command ) {
 	case UI_GETAPIVERSION:
 		return UI_API_VERSION;
@@ -58,7 +58,7 @@
 		return 0;
 
 	case UI_MOUSE_EVENT:
-		UI_MouseEvent( arg0, arg1, arg2 );
+		UI_MouseEvent( arg0, arg1 );
 		return 0;
 
 	case UI_REFRESH:
@@ -79,10 +79,7 @@
 		UI_DrawConnectScreen( arg0 );
 		return 0;
 	case UI_HASUNIQUECDKEY:				// mod authors need to observe this
-		return qtrue;  // change this to qfalse for mods!
-	case UI_COLOR_TABLE_CHANGE:
-		Q_SetColorTable(arg0, (float)(arg1) / 255.0, (float)(arg2) / 255.0, (float)(arg3) / 255.0, (float)(arg4) / 255.0);
-		return 0;
+		return qtrue;  // bk010117 - change this to qfalse for mods!
 	}
 
 	return -1;
@@ -158,13 +155,8 @@
 vmCvar_t	ui_server16;
 
 vmCvar_t	ui_cdkeychecked;
-vmCvar_t	ui_ioq3;
-
-vmCvar_t ui_doubleClickTime;
-
-vmCvar_t ui_demoSortDirFirst;
-vmCvar_t ui_demoStayInFolder;
 
+// bk001129 - made static to avoid aliasing.
 static cvarTable_t		cvarTable[] = {
 	{ &ui_ffa_fraglimit, "ui_ffa_fraglimit", "20", CVAR_ARCHIVE },
 	{ &ui_ffa_timelimit, "ui_ffa_timelimit", "0", CVAR_ARCHIVE },
@@ -182,25 +174,25 @@
 
 	{ &ui_arenasFile, "g_arenasFile", "", CVAR_INIT|CVAR_ROM },
 	{ &ui_botsFile, "g_botsFile", "", CVAR_INIT|CVAR_ROM },
-	{ &ui_spScores1, "g_spScores1", "", CVAR_ARCHIVE },
-	{ &ui_spScores2, "g_spScores2", "", CVAR_ARCHIVE },
-	{ &ui_spScores3, "g_spScores3", "", CVAR_ARCHIVE },
-	{ &ui_spScores4, "g_spScores4", "", CVAR_ARCHIVE },
-	{ &ui_spScores5, "g_spScores5", "", CVAR_ARCHIVE },
-	{ &ui_spAwards, "g_spAwards", "", CVAR_ARCHIVE },
-	{ &ui_spVideos, "g_spVideos", "", CVAR_ARCHIVE },
+	{ &ui_spScores1, "g_spScores1", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores2, "g_spScores2", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores3, "g_spScores3", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores4, "g_spScores4", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores5, "g_spScores5", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spAwards, "g_spAwards", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spVideos, "g_spVideos", "", CVAR_ARCHIVE | CVAR_ROM },
 	{ &ui_spSkill, "g_spSkill", "2", CVAR_ARCHIVE | CVAR_LATCH },
 
 	{ &ui_spSelection, "ui_spSelection", "", CVAR_ROM },
 
-	{ &ui_browserMaster, "ui_browserMaster", "1", CVAR_ARCHIVE },
+	{ &ui_browserMaster, "ui_browserMaster", "0", CVAR_ARCHIVE },
 	{ &ui_browserGameType, "ui_browserGameType", "0", CVAR_ARCHIVE },
 	{ &ui_browserSortKey, "ui_browserSortKey", "4", CVAR_ARCHIVE },
 	{ &ui_browserShowFull, "ui_browserShowFull", "1", CVAR_ARCHIVE },
 	{ &ui_browserShowEmpty, "ui_browserShowEmpty", "1", CVAR_ARCHIVE },
 
 	{ &ui_brassTime, "cg_brassTime", "2500", CVAR_ARCHIVE },
-	{ &ui_drawCrosshair, "cg_drawCrosshair", "5", CVAR_ARCHIVE },
+	{ &ui_drawCrosshair, "cg_drawCrosshair", "4", CVAR_ARCHIVE },
 	{ &ui_drawCrosshairNames, "cg_drawCrosshairNames", "1", CVAR_ARCHIVE },
 	{ &ui_marks, "cg_marks", "1", CVAR_ARCHIVE },
 
@@ -221,16 +213,11 @@
 	{ &ui_server15, "server15", "", CVAR_ARCHIVE },
 	{ &ui_server16, "server16", "", CVAR_ARCHIVE },
 
-	{ &ui_cdkeychecked, "ui_cdkeychecked", "0", CVAR_ROM },
-	{ &ui_ioq3, "ui_ioq3", "1", CVAR_ROM },
-	{ NULL, "g_localTeamPref", "", 0 },
-
-	{ &ui_doubleClickTime, "ui_doubleClickTime", "500", CVAR_ARCHIVE },
-	{ &ui_demoSortDirFirst, "ui_demoSortDirFirst", "1", CVAR_ARCHIVE },
-	{ &ui_demoStayInFolder, "ui_demoStayInFolder", "1", CVAR_ARCHIVE },
+	{ &ui_cdkeychecked, "ui_cdkeychecked", "0", CVAR_ROM }
 };
 
-static int cvarTableSize = ARRAY_LEN( cvarTable );
+// bk001129 - made static to avoid aliasing
+static int cvarTableSize = sizeof(cvarTable) / sizeof(cvarTable[0]);
 
 
 /*
@@ -257,10 +244,6 @@
 	cvarTable_t	*cv;
 
 	for ( i = 0, cv = cvarTable ; i < cvarTableSize ; i++, cv++ ) {
-		if ( !cv->vmCvar ) {
-			continue;
-		}
-
 		trap_Cvar_Update( cv->vmCvar );
 	}
 }

```

### `ioquake3`  — sha256 `2aea041225bc...`, 7198 bytes

_Diff stat: +3 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_main.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_main.c	2026-04-16 20:02:21.555592800 +0100
@@ -58,7 +58,7 @@
 		return 0;
 
 	case UI_MOUSE_EVENT:
-		UI_MouseEvent( arg0, arg1, arg2 );
+		UI_MouseEvent( arg0, arg1 );
 		return 0;
 
 	case UI_REFRESH:
@@ -80,9 +80,6 @@
 		return 0;
 	case UI_HASUNIQUECDKEY:				// mod authors need to observe this
 		return qtrue;  // change this to qfalse for mods!
-	case UI_COLOR_TABLE_CHANGE:
-		Q_SetColorTable(arg0, (float)(arg1) / 255.0, (float)(arg2) / 255.0, (float)(arg3) / 255.0, (float)(arg4) / 255.0);
-		return 0;
 	}
 
 	return -1;
@@ -160,11 +157,6 @@
 vmCvar_t	ui_cdkeychecked;
 vmCvar_t	ui_ioq3;
 
-vmCvar_t ui_doubleClickTime;
-
-vmCvar_t ui_demoSortDirFirst;
-vmCvar_t ui_demoStayInFolder;
-
 static cvarTable_t		cvarTable[] = {
 	{ &ui_ffa_fraglimit, "ui_ffa_fraglimit", "20", CVAR_ARCHIVE },
 	{ &ui_ffa_timelimit, "ui_ffa_timelimit", "0", CVAR_ARCHIVE },
@@ -200,7 +192,7 @@
 	{ &ui_browserShowEmpty, "ui_browserShowEmpty", "1", CVAR_ARCHIVE },
 
 	{ &ui_brassTime, "cg_brassTime", "2500", CVAR_ARCHIVE },
-	{ &ui_drawCrosshair, "cg_drawCrosshair", "5", CVAR_ARCHIVE },
+	{ &ui_drawCrosshair, "cg_drawCrosshair", "4", CVAR_ARCHIVE },
 	{ &ui_drawCrosshairNames, "cg_drawCrosshairNames", "1", CVAR_ARCHIVE },
 	{ &ui_marks, "cg_marks", "1", CVAR_ARCHIVE },
 
@@ -223,11 +215,7 @@
 
 	{ &ui_cdkeychecked, "ui_cdkeychecked", "0", CVAR_ROM },
 	{ &ui_ioq3, "ui_ioq3", "1", CVAR_ROM },
-	{ NULL, "g_localTeamPref", "", 0 },
-
-	{ &ui_doubleClickTime, "ui_doubleClickTime", "500", CVAR_ARCHIVE },
-	{ &ui_demoSortDirFirst, "ui_demoSortDirFirst", "1", CVAR_ARCHIVE },
-	{ &ui_demoStayInFolder, "ui_demoStayInFolder", "1", CVAR_ARCHIVE },
+	{ NULL, "g_localTeamPref", "", 0 }
 };
 
 static int cvarTableSize = ARRAY_LEN( cvarTable );

```

### `openarena-engine`  — sha256 `ac75358dfec2...`, 7115 bytes

_Diff stat: +4 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_main.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_main.c	2026-04-16 22:48:25.896194800 +0100
@@ -58,7 +58,7 @@
 		return 0;
 
 	case UI_MOUSE_EVENT:
-		UI_MouseEvent( arg0, arg1, arg2 );
+		UI_MouseEvent( arg0, arg1 );
 		return 0;
 
 	case UI_REFRESH:
@@ -80,9 +80,6 @@
 		return 0;
 	case UI_HASUNIQUECDKEY:				// mod authors need to observe this
 		return qtrue;  // change this to qfalse for mods!
-	case UI_COLOR_TABLE_CHANGE:
-		Q_SetColorTable(arg0, (float)(arg1) / 255.0, (float)(arg2) / 255.0, (float)(arg3) / 255.0, (float)(arg4) / 255.0);
-		return 0;
 	}
 
 	return -1;
@@ -160,11 +157,6 @@
 vmCvar_t	ui_cdkeychecked;
 vmCvar_t	ui_ioq3;
 
-vmCvar_t ui_doubleClickTime;
-
-vmCvar_t ui_demoSortDirFirst;
-vmCvar_t ui_demoStayInFolder;
-
 static cvarTable_t		cvarTable[] = {
 	{ &ui_ffa_fraglimit, "ui_ffa_fraglimit", "20", CVAR_ARCHIVE },
 	{ &ui_ffa_timelimit, "ui_ffa_timelimit", "0", CVAR_ARCHIVE },
@@ -193,14 +185,14 @@
 
 	{ &ui_spSelection, "ui_spSelection", "", CVAR_ROM },
 
-	{ &ui_browserMaster, "ui_browserMaster", "1", CVAR_ARCHIVE },
+	{ &ui_browserMaster, "ui_browserMaster", "0", CVAR_ARCHIVE },
 	{ &ui_browserGameType, "ui_browserGameType", "0", CVAR_ARCHIVE },
 	{ &ui_browserSortKey, "ui_browserSortKey", "4", CVAR_ARCHIVE },
 	{ &ui_browserShowFull, "ui_browserShowFull", "1", CVAR_ARCHIVE },
 	{ &ui_browserShowEmpty, "ui_browserShowEmpty", "1", CVAR_ARCHIVE },
 
 	{ &ui_brassTime, "cg_brassTime", "2500", CVAR_ARCHIVE },
-	{ &ui_drawCrosshair, "cg_drawCrosshair", "5", CVAR_ARCHIVE },
+	{ &ui_drawCrosshair, "cg_drawCrosshair", "4", CVAR_ARCHIVE },
 	{ &ui_drawCrosshairNames, "cg_drawCrosshairNames", "1", CVAR_ARCHIVE },
 	{ &ui_marks, "cg_marks", "1", CVAR_ARCHIVE },
 
@@ -222,12 +214,7 @@
 	{ &ui_server16, "server16", "", CVAR_ARCHIVE },
 
 	{ &ui_cdkeychecked, "ui_cdkeychecked", "0", CVAR_ROM },
-	{ &ui_ioq3, "ui_ioq3", "1", CVAR_ROM },
-	{ NULL, "g_localTeamPref", "", 0 },
-
-	{ &ui_doubleClickTime, "ui_doubleClickTime", "500", CVAR_ARCHIVE },
-	{ &ui_demoSortDirFirst, "ui_demoSortDirFirst", "1", CVAR_ARCHIVE },
-	{ &ui_demoStayInFolder, "ui_demoStayInFolder", "1", CVAR_ARCHIVE },
+	{ &ui_ioq3, "ui_ioq3", "1", CVAR_ROM }
 };
 
 static int cvarTableSize = ARRAY_LEN( cvarTable );
@@ -257,10 +244,6 @@
 	cvarTable_t	*cv;
 
 	for ( i = 0, cv = cvarTable ; i < cvarTableSize ; i++, cv++ ) {
-		if ( !cv->vmCvar ) {
-			continue;
-		}
-
 		trap_Cvar_Update( cv->vmCvar );
 	}
 }

```

### `openarena-gamecode`  — sha256 `0feac69c6a15...`, 10375 bytes

_Diff stat: +140 / -88 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_main.c	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_main.c	2026-04-16 22:48:24.183498100 +0100
@@ -58,7 +58,7 @@
 		return 0;
 
 	case UI_MOUSE_EVENT:
-		UI_MouseEvent( arg0, arg1, arg2 );
+		UI_MouseEvent( arg0, arg1 );
 		return 0;
 
 	case UI_REFRESH:
@@ -79,10 +79,7 @@
 		UI_DrawConnectScreen( arg0 );
 		return 0;
 	case UI_HASUNIQUECDKEY:				// mod authors need to observe this
-		return qtrue;  // change this to qfalse for mods!
-	case UI_COLOR_TABLE_CHANGE:
-		Q_SetColorTable(arg0, (float)(arg1) / 255.0, (float)(arg2) / 255.0, (float)(arg3) / 255.0, (float)(arg4) / 255.0);
-		return 0;
+		return qtrue;  // bk010117 - change this to qfalse for mods!
 	}
 
 	return -1;
@@ -96,76 +93,91 @@
 */
 
 typedef struct {
-	vmCvar_t	*vmCvar;
+	vmCvar_t *vmCvar;
 	char		*cvarName;
 	char		*defaultString;
 	int			cvarFlags;
 } cvarTable_t;
 
-vmCvar_t	ui_ffa_fraglimit;
-vmCvar_t	ui_ffa_timelimit;
-
-vmCvar_t	ui_tourney_fraglimit;
-vmCvar_t	ui_tourney_timelimit;
-
-vmCvar_t	ui_team_fraglimit;
-vmCvar_t	ui_team_timelimit;
-vmCvar_t	ui_team_friendly;
-
-vmCvar_t	ui_ctf_capturelimit;
-vmCvar_t	ui_ctf_timelimit;
-vmCvar_t	ui_ctf_friendly;
-
-vmCvar_t	ui_arenasFile;
-vmCvar_t	ui_botsFile;
-vmCvar_t	ui_spScores1;
-vmCvar_t	ui_spScores2;
-vmCvar_t	ui_spScores3;
-vmCvar_t	ui_spScores4;
-vmCvar_t	ui_spScores5;
-vmCvar_t	ui_spAwards;
-vmCvar_t	ui_spVideos;
-vmCvar_t	ui_spSkill;
-
-vmCvar_t	ui_spSelection;
-
-vmCvar_t	ui_browserMaster;
-vmCvar_t	ui_browserGameType;
-vmCvar_t	ui_browserSortKey;
-vmCvar_t	ui_browserShowFull;
-vmCvar_t	ui_browserShowEmpty;
-
-vmCvar_t	ui_brassTime;
-vmCvar_t	ui_drawCrosshair;
-vmCvar_t	ui_drawCrosshairNames;
-vmCvar_t	ui_marks;
-
-vmCvar_t	ui_server1;
-vmCvar_t	ui_server2;
-vmCvar_t	ui_server3;
-vmCvar_t	ui_server4;
-vmCvar_t	ui_server5;
-vmCvar_t	ui_server6;
-vmCvar_t	ui_server7;
-vmCvar_t	ui_server8;
-vmCvar_t	ui_server9;
-vmCvar_t	ui_server10;
-vmCvar_t	ui_server11;
-vmCvar_t	ui_server12;
-vmCvar_t	ui_server13;
-vmCvar_t	ui_server14;
-vmCvar_t	ui_server15;
-vmCvar_t	ui_server16;
-
-vmCvar_t	ui_cdkeychecked;
-vmCvar_t	ui_ioq3;
+vmCvar_t ui_ffa_fraglimit;
+vmCvar_t ui_ffa_timelimit;
+vmCvar_t ui_tourney_fraglimit;
+vmCvar_t ui_tourney_timelimit;
+vmCvar_t ui_team_fraglimit;
+vmCvar_t ui_team_timelimit;
+vmCvar_t ui_team_friendly;
+vmCvar_t ui_ctf_capturelimit;
+vmCvar_t ui_ctf_timelimit;
+vmCvar_t ui_ctf_friendly;
+vmCvar_t ui_1fctf_capturelimit;
+vmCvar_t ui_1fctf_timelimit;
+vmCvar_t ui_1fctf_friendly;
+vmCvar_t ui_overload_capturelimit;
+vmCvar_t ui_overload_timelimit;
+vmCvar_t ui_overload_friendly;
+vmCvar_t ui_harvester_capturelimit;
+vmCvar_t ui_harvester_timelimit;
+vmCvar_t ui_harvester_friendly;
+vmCvar_t ui_elimination_capturelimit;
+vmCvar_t ui_elimination_timelimit;
+vmCvar_t ui_ctf_elimination_capturelimit;
+vmCvar_t ui_ctf_elimination_timelimit;
+vmCvar_t ui_lms_fraglimit;
+vmCvar_t ui_lms_timelimit;
+vmCvar_t ui_dd_capturelimit;
+vmCvar_t ui_dd_timelimit;
+vmCvar_t ui_dd_friendly;
+vmCvar_t ui_dom_capturelimit;
+vmCvar_t ui_dom_timelimit;
+vmCvar_t ui_dom_friendly;
+vmCvar_t ui_pos_scorelimit;
+vmCvar_t ui_pos_timelimit;
+vmCvar_t ui_arenasFile;
+vmCvar_t ui_botsFile;
+vmCvar_t ui_spScores1;
+vmCvar_t ui_spScores2;
+vmCvar_t ui_spScores3;
+vmCvar_t ui_spScores4;
+vmCvar_t ui_spScores5;
+vmCvar_t ui_spAwards;
+vmCvar_t ui_spVideos;
+vmCvar_t ui_spSkill;
+vmCvar_t ui_spSelection;
+vmCvar_t ui_browserMaster;
+vmCvar_t ui_browserGameType;
+vmCvar_t ui_browserSortKey;
+vmCvar_t ui_browserShowFull;
+vmCvar_t ui_browserShowEmpty;
+vmCvar_t ui_brassTime;
+vmCvar_t ui_drawCrosshair;
+vmCvar_t ui_drawCrosshairNames;
+vmCvar_t ui_marks;
+vmCvar_t ui_server1;
+vmCvar_t ui_server2;
+vmCvar_t ui_server3;
+vmCvar_t ui_server4;
+vmCvar_t ui_server5;
+vmCvar_t ui_server6;
+vmCvar_t ui_server7;
+vmCvar_t ui_server8;
+vmCvar_t ui_server9;
+vmCvar_t ui_server10;
+vmCvar_t ui_server11;
+vmCvar_t ui_server12;
+vmCvar_t ui_server13;
+vmCvar_t ui_server14;
+vmCvar_t ui_server15;
+vmCvar_t ui_server16;
+//vmCvar_t ui_cdkeychecked;
+//new in beta 23:
+vmCvar_t        ui_browserOnlyHumans;
+//new in beta 37:
+vmCvar_t        ui_setupchecked;
 
-vmCvar_t ui_doubleClickTime;
+vmCvar_t ui_browserHidePrivate;
 
-vmCvar_t ui_demoSortDirFirst;
-vmCvar_t ui_demoStayInFolder;
-
-static cvarTable_t		cvarTable[] = {
+// bk001129 - made static to avoid aliasing.
+static cvarTable_t cvarTable[] = {
 	{ &ui_ffa_fraglimit, "ui_ffa_fraglimit", "20", CVAR_ARCHIVE },
 	{ &ui_ffa_timelimit, "ui_ffa_timelimit", "0", CVAR_ARCHIVE },
 
@@ -180,27 +192,59 @@
 	{ &ui_ctf_timelimit, "ui_ctf_timelimit", "30", CVAR_ARCHIVE },
 	{ &ui_ctf_friendly, "ui_ctf_friendly",  "0", CVAR_ARCHIVE },
 
+	{ &ui_1fctf_capturelimit, "ui_1fctf_capturelimit", "8", CVAR_ARCHIVE },
+	{ &ui_1fctf_timelimit, "ui_1fctf_timelimit", "30", CVAR_ARCHIVE },
+	{ &ui_1fctf_friendly, "ui_1fctf_friendly",  "0", CVAR_ARCHIVE },
+
+	{ &ui_overload_capturelimit, "ui_overload_capturelimit", "8", CVAR_ARCHIVE },
+	{ &ui_overload_timelimit, "ui_overload_timelimit", "30", CVAR_ARCHIVE },
+	{ &ui_overload_friendly, "ui_overload_friendly",  "0", CVAR_ARCHIVE },
+
+	{ &ui_harvester_capturelimit, "ui_harvester_capturelimit", "20", CVAR_ARCHIVE },
+	{ &ui_harvester_timelimit, "ui_harvester_timelimit", "30", CVAR_ARCHIVE },
+	{ &ui_harvester_friendly, "ui_harvester_friendly",  "0", CVAR_ARCHIVE },
+
+	{ &ui_elimination_capturelimit, "ui_elimination_capturelimit", "8", CVAR_ARCHIVE },
+	{ &ui_elimination_timelimit, "ui_elimination_timelimit", "20", CVAR_ARCHIVE },
+
+	{ &ui_ctf_elimination_capturelimit, "ui_ctf_elimination_capturelimit", "8", CVAR_ARCHIVE },
+	{ &ui_ctf_elimination_timelimit, "ui_ctf_elimination_timelimit", "30", CVAR_ARCHIVE },
+
+	{ &ui_lms_fraglimit, "ui_lms_fraglimit", "20", CVAR_ARCHIVE },
+	{ &ui_lms_timelimit, "ui_lms_timelimit", "0", CVAR_ARCHIVE },
+
+	{ &ui_dd_capturelimit, "ui_dd_capturelimit", "8", CVAR_ARCHIVE },
+	{ &ui_dd_timelimit, "ui_dd_timelimit", "30", CVAR_ARCHIVE },
+	{ &ui_dd_friendly, "ui_dd_friendly",  "0", CVAR_ARCHIVE },
+
+	{ &ui_dom_capturelimit, "ui_dom_capturelimit", "500", CVAR_ARCHIVE },
+	{ &ui_dom_timelimit, "ui_dom_timelimit", "30", CVAR_ARCHIVE },
+	{ &ui_dom_friendly, "ui_dom_friendly",  "0", CVAR_ARCHIVE },
+
+	{ &ui_pos_scorelimit, "ui_pos_scorelimit", "120", CVAR_ARCHIVE },
+	{ &ui_pos_timelimit, "ui_pos_timelimit", "20", CVAR_ARCHIVE },
+
 	{ &ui_arenasFile, "g_arenasFile", "", CVAR_INIT|CVAR_ROM },
 	{ &ui_botsFile, "g_botsFile", "", CVAR_INIT|CVAR_ROM },
-	{ &ui_spScores1, "g_spScores1", "", CVAR_ARCHIVE },
-	{ &ui_spScores2, "g_spScores2", "", CVAR_ARCHIVE },
-	{ &ui_spScores3, "g_spScores3", "", CVAR_ARCHIVE },
-	{ &ui_spScores4, "g_spScores4", "", CVAR_ARCHIVE },
-	{ &ui_spScores5, "g_spScores5", "", CVAR_ARCHIVE },
-	{ &ui_spAwards, "g_spAwards", "", CVAR_ARCHIVE },
-	{ &ui_spVideos, "g_spVideos", "", CVAR_ARCHIVE },
+	{ &ui_spScores1, "g_spScores1", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores2, "g_spScores2", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores3, "g_spScores3", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores4, "g_spScores4", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spScores5, "g_spScores5", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spAwards, "g_spAwards", "", CVAR_ARCHIVE | CVAR_ROM },
+	{ &ui_spVideos, "g_spVideos", "", CVAR_ARCHIVE | CVAR_ROM },
 	{ &ui_spSkill, "g_spSkill", "2", CVAR_ARCHIVE | CVAR_LATCH },
 
 	{ &ui_spSelection, "ui_spSelection", "", CVAR_ROM },
 
-	{ &ui_browserMaster, "ui_browserMaster", "1", CVAR_ARCHIVE },
+	{ &ui_browserMaster, "ui_browserMaster", "0", CVAR_ARCHIVE },
 	{ &ui_browserGameType, "ui_browserGameType", "0", CVAR_ARCHIVE },
 	{ &ui_browserSortKey, "ui_browserSortKey", "4", CVAR_ARCHIVE },
 	{ &ui_browserShowFull, "ui_browserShowFull", "1", CVAR_ARCHIVE },
 	{ &ui_browserShowEmpty, "ui_browserShowEmpty", "1", CVAR_ARCHIVE },
 
 	{ &ui_brassTime, "cg_brassTime", "2500", CVAR_ARCHIVE },
-	{ &ui_drawCrosshair, "cg_drawCrosshair", "5", CVAR_ARCHIVE },
+	{ &ui_drawCrosshair, "cg_drawCrosshair", "4", CVAR_ARCHIVE },
 	{ &ui_drawCrosshairNames, "cg_drawCrosshairNames", "1", CVAR_ARCHIVE },
 	{ &ui_marks, "cg_marks", "1", CVAR_ARCHIVE },
 
@@ -220,18 +264,14 @@
 	{ &ui_server14, "server14", "", CVAR_ARCHIVE },
 	{ &ui_server15, "server15", "", CVAR_ARCHIVE },
 	{ &ui_server16, "server16", "", CVAR_ARCHIVE },
-
-	{ &ui_cdkeychecked, "ui_cdkeychecked", "0", CVAR_ROM },
-	{ &ui_ioq3, "ui_ioq3", "1", CVAR_ROM },
-	{ NULL, "g_localTeamPref", "", 0 },
-
-	{ &ui_doubleClickTime, "ui_doubleClickTime", "500", CVAR_ARCHIVE },
-	{ &ui_demoSortDirFirst, "ui_demoSortDirFirst", "1", CVAR_ARCHIVE },
-	{ &ui_demoStayInFolder, "ui_demoStayInFolder", "1", CVAR_ARCHIVE },
+	{ &ui_browserOnlyHumans, "ui_browserOnlyHumans", "0", CVAR_ARCHIVE },
+	{ &ui_setupchecked, "ui_setupchecked", "0", CVAR_ARCHIVE },
+	{ &ui_browserHidePrivate, "ui_browserHidePrivate", "1", CVAR_ARCHIVE },
+	{ NULL, "g_localTeamPref", "", 0 }
 };
 
-static int cvarTableSize = ARRAY_LEN( cvarTable );
-
+// bk001129 - made static to avoid aliasing
+static int cvarTableSize = sizeof(cvarTable) / sizeof(cvarTable[0]);
 
 /*
 =================
@@ -260,7 +300,19 @@
 		if ( !cv->vmCvar ) {
 			continue;
 		}
-
 		trap_Cvar_Update( cv->vmCvar );
 	}
 }
+
+/*
+==================
+ * UI_SetDefaultCvar
+ * If the cvar is blank it will be set to value
+ * This is only good for cvars that cannot naturally be blank
+================== 
+ */
+void UI_SetDefaultCvar(const char* cvar, const char* value) {
+	if(strlen(UI_Cvar_VariableString(cvar)) == 0) {
+		trap_Cvar_Set(cvar,value);
+	}
+}

```
