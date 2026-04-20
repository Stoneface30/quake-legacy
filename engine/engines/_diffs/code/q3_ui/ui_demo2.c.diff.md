# Diff: `code/q3_ui/ui_demo2.c`
**Canonical:** `wolfcamql-src` (sha256 `38b7e6240ed9...`, 14300 bytes)

## Variants

### `quake3-source`  — sha256 `b2453c10f8fa...`, 8361 bytes

_Diff stat: +43 / -267 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_demo2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_demo2.c	2026-04-16 20:02:19.945826100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -33,7 +33,7 @@
 
 
 #define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
+#define ART_BACK1			"menu/art/back_1"	
 #define ART_GO0				"menu/art/play_0"
 #define ART_GO1				"menu/art/play_1"
 #define ART_FRAMEL			"menu/art/frame2_l"
@@ -42,9 +42,8 @@
 #define ART_ARROWLEFT		"menu/art/arrows_horz_left"
 #define ART_ARROWRIGHT		"menu/art/arrows_horz_right"
 
-#define MAX_DEMOS			4096  //128
-#define NAMEBUFSIZE			( MAX_DEMOS * 64 )
-#define MAX_DIR_STACK 128
+#define MAX_DEMOS			128
+#define NAMEBUFSIZE			( MAX_DEMOS * 16 )
 
 #define ID_BACK				10
 #define ID_GO				11
@@ -66,97 +65,18 @@
 	menulist_s		list;
 
 	menubitmap_s	arrows;
-	//menubitmap_s	left;
-	//menubitmap_s	right;
+	menubitmap_s	left;
+	menubitmap_s	right;
 	menubitmap_s	back;
 	menubitmap_s	go;
 
 	int				numDemos;
 	char			names[NAMEBUFSIZE];
-
 	char			*demolist[MAX_DEMOS];
-	char dirName[MAX_OSPATH];
 } demos_t;
 
 static demos_t	s_demos;
 
-static qboolean UseQuakeLiveDir = qfalse;
-
-static void Demos_MenuInit (const char *dirName);
-
-
-static qboolean Demos_IsDir (const char *fname)
-{
-	int len;
-
-	len = strlen(fname);
-
-	if (fname[len - 1] == '/') {
-		return qtrue;
-	}
-
-	return qfalse;
-}
-
-static void Demos_PlayDemoOrChangeDir (void)
-{
-	const char *fname;
-	int i;
-	int len;
-	int end;
-	char strippedName[MAX_OSPATH];
-	const char *matchString;
-
-	if (UseQuakeLiveDir) {
-		matchString = "ql:demos";
-	} else {
-		matchString = "demos";
-	}
-
-	fname = s_demos.list.itemnames[s_demos.list.curvalue];
-	if (Demos_IsDir(fname)) {
-		//Com_Printf("dir: '%s'  '%s'\n", s_demos.dirName, fname);
-		if (!Q_stricmpn(fname, "../", strlen("../"))) {
-			if (!Q_stricmpn(s_demos.dirName, matchString, sizeof(s_demos.dirName))) {
-				//FIXME hack to avoid problems
-				return;
-			}
-			UI_PopMenu();
-			len = strlen(s_demos.dirName);
-			if (len <= 0) {
-				Com_Printf("^1Demos_PlayDemoOrChangeDir()  FIXME shouldn't happen dirName NULL\n");
-				return;
-			}
-
-			end = len - 1;
-			for (i = end;  i >= 0;  i--) {
-				if (s_demos.dirName[i] == '/') {
-					s_demos.dirName[i] = '\0';
-					break;
-				}
-			}
-
-			Demos_MenuInit(va("%s", s_demos.dirName));
-		} else {  // subdir
-			UI_PopMenu();
-			Q_strncpyz(strippedName, fname, sizeof(strippedName));
-			strippedName[strlen(fname) - 1] = '\0';
-			Demos_MenuInit(va("%s/%s", s_demos.dirName, strippedName));
-		}
-		//UI_PopMenu();
-		UI_PushMenu(&s_demos.menu);
-		return;
-	} else {
-		trap_Cvar_Set("lastdemodir", s_demos.dirName);
-		trap_Cvar_SetValue("lastdemodir_curvalue", s_demos.list.curvalue);
-		trap_Cvar_SetValue("lastdemodir_top", s_demos.list.top);
-
-		//FIXME hack
-		//Com_Printf("^3dirName '%s'  fname '%s'\n", s_demos.dirName, fname);
-		UI_ForceMenuOff();
-		trap_Cmd_ExecuteText(EXEC_APPEND, va("demo \"%s/%s\"\n", s_demos.dirName, fname));
-	}
-}
 
 /*
 ===============
@@ -164,63 +84,27 @@
 ===============
 */
 static void Demos_MenuEvent( void *ptr, int event ) {
-	//Com_Printf("demos menuEvent %p event %d  id %d\n", ptr, event, ((menucommon_s *)ptr)->id);
-
-	if (event == QM_DOUBLECLICKED) {
-		Demos_PlayDemoOrChangeDir();
-		return;
-	}
-
 	if( event != QM_ACTIVATED ) {
 		return;
 	}
 
 	switch( ((menucommon_s*)ptr)->id ) {
-		//case QM_ACTIVATED:
 	case ID_GO:
-		Demos_PlayDemoOrChangeDir();
+		UI_ForceMenuOff ();
+		trap_Cmd_ExecuteText( EXEC_APPEND, va( "demo %s\n",
+								s_demos.list.itemnames[s_demos.list.curvalue]) );
 		break;
 
-	case ID_BACK: {
-		const char *slash;
-
-		slash = strchr(s_demos.dirName, '/');
-		if (!slash) {
-			trap_Cvar_Set("lastdemodir", "");
-			UI_PopMenu();
-		} else {
-			// hack, set '../' as selected demo/dir
-			int i;
-
-			for (i = 0;  i < s_demos.list.numitems;  i++) {
-				const char *fname;
-
-				fname = s_demos.list.itemnames[i];
-				if (!Q_stricmpn(fname, "../", strlen("../"))) {
-					s_demos.list.curvalue = i;
-					break;
-				}
-			}
-
-			if (i < s_demos.list.numitems) {
-				// found '../'
-				Demos_PlayDemoOrChangeDir();
-			} else {
-				trap_Cvar_Set("lastdemodir", "");
-				UI_PopMenu();
-			}
-		}
+	case ID_BACK:
+		UI_PopMenu();
 		break;
-	}
 
 	case ID_LEFT:
-		//ScrollList_Key( &s_demos.list, K_LEFTARROW );
-		//Com_Printf("scroll left\n");
+		ScrollList_Key( &s_demos.list, K_LEFTARROW );
 		break;
 
 	case ID_RIGHT:
-		//ScrollList_Key( &s_demos.list, K_RIGHTARROW );
-		//Com_Printf("scroll right\n");
+		ScrollList_Key( &s_demos.list, K_RIGHTARROW );
 		break;
 	}
 }
@@ -231,101 +115,36 @@
 UI_DemosMenu_Key
 =================
 */
-static sfxHandle_t UI_DemosMenu_Key (int key)
-{
-	//menucommon_s	*item;
-
-	//Com_Printf("ui demo menu key: %d  (curvalue %d, oldvalue %d)  m->nitems %d\n", key, s_demos.list.curvalue, s_demos.list.oldvalue, s_demos.menu.nitems);
-	if (key == K_ENTER  ||  key == K_KP_ENTER) {
-		// if 'back' button has focus don't play demo or change dir
-		//Com_Printf("focus: %d\n", Menu_ItemAtCursor(&s_demos.menu) == &s_demos.back);
-		if (Menu_ItemAtCursor(&s_demos.menu) != &s_demos.back) {
-			Demos_PlayDemoOrChangeDir();
-		}
-	}
-	//item = Menu_ItemAtCursor( &s_demos.menu );
+static sfxHandle_t UI_DemosMenu_Key( int key ) {
+	menucommon_s	*item;
 
-	// hack
-	if (key == K_ESCAPE) {
-		trap_Cvar_Set("lastdemodir", "");
-	}
+	item = Menu_ItemAtCursor( &s_demos.menu );
 
 	return Menu_DefaultKey( &s_demos.menu, key );
 }
 
 
-static int CmpDemoNameStrings (const void *p1, const void *p2)
-{
-	int lens1, lens2;
-	char lastp1, lastp2;
-	const char *s1, *s2;
-
-	s1 = *(const char **)p1;
-	s2 = *(const char **)p2;
-
-	// special case for '../' to make it always appear as the first entry
-	if (!Q_stricmp(s1, "../")) {
-		return -1;
-	} else if (!Q_stricmp(s2, "../")) {
-		return 1;
-	}
-
-	if (!ui_demoSortDirFirst.integer) {
-		return Q_stricmp(s1, s2);
-	}
-
-	// sort directories first
-
-	lens1 = strlen(s1);
-	lens2 = strlen(s2);
-
-	if (lens1 < 1) {
-		lastp1 = '\0';
-	} else {
-		lastp1 = s1[strlen(s1) - 1];
-	}
-
-	if (lens2 < 1) {
-		lastp2 = '\0';
-	} else {
-		lastp2 = s2[strlen(s2) - 1];
-	}
-
-	if (lastp1 == '/'  &&  lastp2 != '/') {
-		return -1;
-	} else if (lastp1 != '/'  &&  lastp2 == '/') {
-		return 1;
-	}
-
-	return Q_stricmp(s1, s2);
-}
-
 /*
 ===============
 Demos_MenuInit
 ===============
 */
-static void Demos_MenuInit (const char *dirName)
-{
+static void Demos_MenuInit( void ) {
 	int		i;
 	int		len;
 	char	*demoname, extension[32];
 
 	memset( &s_demos, 0 ,sizeof(demos_t) );
 	s_demos.menu.key = UI_DemosMenu_Key;
-	Q_strncpyz(s_demos.dirName, dirName, sizeof(s_demos.dirName));
-	//Com_sprintf(s_demos.dirName, sizeof(s_demos.dirName), "%s%s", UseQuakeLiveDir ? "ql:" : "", dirName);
-	//Com_Printf("dirname '%s'\n", s_demos.dirName);
+
 	Demos_Cache();
 
 	s_demos.menu.fullscreen = qtrue;
 	s_demos.menu.wrapAround = qtrue;
 
-	s_demos.banner.generic.type		= MTYPE_BTEXT;  //MTYPE_PTEXT;  //MTYPE_BTEXT;
+	s_demos.banner.generic.type		= MTYPE_BTEXT;
 	s_demos.banner.generic.x		= 320;
 	s_demos.banner.generic.y		= 16;
-	//s_demos.banner.width 	= 10;
-	//s_demos.banner.height   = 10;
 	s_demos.banner.string			= "DEMOS";
 	s_demos.banner.color			= color_white;
 	s_demos.banner.style			= UI_CENTER;
@@ -333,7 +152,7 @@
 	s_demos.framel.generic.type		= MTYPE_BITMAP;
 	s_demos.framel.generic.name		= ART_FRAMEL;
 	s_demos.framel.generic.flags	= QMF_INACTIVE;
-	s_demos.framel.generic.x		= 0;
+	s_demos.framel.generic.x		= 0;  
 	s_demos.framel.generic.y		= 78;
 	s_demos.framel.width			= 256;
 	s_demos.framel.height			= 329;
@@ -346,7 +165,6 @@
 	s_demos.framer.width			= 256;
 	s_demos.framer.height			= 334;
 
-#if 1
 	s_demos.arrows.generic.type		= MTYPE_BITMAP;
 	s_demos.arrows.generic.name		= ART_ARROWS;
 	s_demos.arrows.generic.flags	= QMF_INACTIVE;
@@ -354,9 +172,7 @@
 	s_demos.arrows.generic.y		= 400;
 	s_demos.arrows.width			= ARROWS_WIDTH;
 	s_demos.arrows.height			= ARROWS_HEIGHT;
-#endif
 
-#if 0
 	s_demos.left.generic.type		= MTYPE_BITMAP;
 	s_demos.left.generic.flags		= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_MOUSEONLY;
 	s_demos.left.generic.x			= 320-ARROWS_WIDTH/2;
@@ -376,7 +192,6 @@
 	s_demos.right.width				= ARROWS_WIDTH/2;
 	s_demos.right.height			= ARROWS_HEIGHT;
 	s_demos.right.focuspic			= ART_ARROWRIGHT;
-#endif
 
 	s_demos.back.generic.type		= MTYPE_BITMAP;
 	s_demos.back.generic.name		= ART_BACK0;
@@ -404,63 +219,46 @@
 	s_demos.list.generic.flags		= QMF_PULSEIFFOCUS;
 	s_demos.list.generic.callback	= Demos_MenuEvent;
 	s_demos.list.generic.id			= ID_LIST;
-	s_demos.list.generic.x			= 20;  //118;
-	s_demos.list.generic.y			= 90;  //130;
-	s_demos.list.width				= 40;  //16;
-	s_demos.list.height				= 20;  //14;
-	Com_sprintf(extension, sizeof(extension), ".%s%d", DEMOEXT, (int) trap_Cvar_VariableValue("protocol"));
-	//s_demos.list.numitems			= trap_FS_GetFileList( "demos", extension, s_demos.names, NAMEBUFSIZE );
-	//s_demos.list.numitems			= trap_FS_GetFileList("demos", "*wantDirs", s_demos.names, NAMEBUFSIZE);
-	s_demos.list.numitems			= trap_FS_GetFileList(dirName, "*wantDirs", s_demos.names, NAMEBUFSIZE);
+	s_demos.list.generic.x			= 118;
+	s_demos.list.generic.y			= 130;
+	s_demos.list.width				= 16;
+	s_demos.list.height				= 14;
+	Com_sprintf(extension, sizeof(extension), "dm_%d", (int)trap_Cvar_VariableValue( "protocol" ) );
+	s_demos.list.numitems			= trap_FS_GetFileList( "demos", extension, s_demos.names, NAMEBUFSIZE );
 	s_demos.list.itemnames			= (const char **)s_demos.demolist;
-	s_demos.list.columns			= 1;
-
-	//Com_Printf("numitems: %d\n", s_demos.list.numitems);
+	s_demos.list.columns			= 3;
 
 	if (!s_demos.list.numitems) {
-		//strcpy( s_demos.names, "No Demos Found." );
-		Q_strncpyz(s_demos.names, "../", sizeof(s_demos.names));
+		strcpy( s_demos.names, "No Demos Found." );
 		s_demos.list.numitems = 1;
 
 		//degenerate case, not selectable
 		s_demos.go.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
 	}
-	else if (s_demos.list.numitems > MAX_DEMOS) {
-		Com_Printf("^1maximum number of demos (%d) for a directory, skipping some demos\n", MAX_DEMOS);
+	else if (s_demos.list.numitems > MAX_DEMOS)
 		s_demos.list.numitems = MAX_DEMOS;
-	}
 
 	demoname = s_demos.names;
-
 	for ( i = 0; i < s_demos.list.numitems; i++ ) {
 		s_demos.list.itemnames[i] = demoname;
-
-		len = strlen( demoname );
-#if 0
+		
 		// strip extension
+		len = strlen( demoname );
 		if (!Q_stricmp(demoname +  len - 4,".dm3"))
 			demoname[len-4] = '\0';
-#endif
-//		Q_strupr(demoname);
-
-		demoname += len + 1;
-	}
 
-	qsort(s_demos.list.itemnames, s_demos.list.numitems, sizeof(char *), CmpDemoNameStrings);
+		Q_strupr(demoname);
 
-#if 0
-	for (i = 0;  i < s_demos.list.numitems;  i++) {
-		Com_Printf("%d: %s\n", i, s_demos.list.itemnames[i]);
+		demoname += len + 1;
 	}
-#endif
 
 	Menu_AddItem( &s_demos.menu, &s_demos.banner );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framel );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framer );
+	Menu_AddItem( &s_demos.menu, &s_demos.framel );
+	Menu_AddItem( &s_demos.menu, &s_demos.framer );
 	Menu_AddItem( &s_demos.menu, &s_demos.list );
-	//Menu_AddItem( &s_demos.menu, &s_demos.arrows );
-	//Menu_AddItem( &s_demos.menu, &s_demos.left );
-	//Menu_AddItem( &s_demos.menu, &s_demos.right );
+	Menu_AddItem( &s_demos.menu, &s_demos.arrows );
+	Menu_AddItem( &s_demos.menu, &s_demos.left );
+	Menu_AddItem( &s_demos.menu, &s_demos.right );
 	Menu_AddItem( &s_demos.menu, &s_demos.back );
 	Menu_AddItem( &s_demos.menu, &s_demos.go );
 }
@@ -475,8 +273,8 @@
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
 	trap_R_RegisterShaderNoMip( ART_GO0 );
 	trap_R_RegisterShaderNoMip( ART_GO1 );
-	//trap_R_RegisterShaderNoMip( ART_FRAMEL );
-	//trap_R_RegisterShaderNoMip( ART_FRAMER );
+	trap_R_RegisterShaderNoMip( ART_FRAMEL );
+	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_ARROWS );
 	trap_R_RegisterShaderNoMip( ART_ARROWLEFT );
 	trap_R_RegisterShaderNoMip( ART_ARROWRIGHT );
@@ -487,29 +285,7 @@
 UI_DemosMenu
 ===============
 */
-//void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir, int top, int curvalue)
-void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir)
-{
-	UseQuakeLiveDir = useQuakeLiveDir;
-
-	if (lastdemodir) {
-		int curvalue, top;
-
-		Demos_MenuInit(lastdemodir);
-		curvalue = trap_Cvar_VariableValue("lastdemodir_curvalue");
-		top = trap_Cvar_VariableValue("lastdemodir_top");
-
-		//Com_Printf("numitems %d  curvalue %d  top %d\n", s_demos.list.numitems, curvalue, top);
-		if (curvalue <= s_demos.list.numitems  &&  top <= s_demos.list.numitems) {
-			s_demos.list.curvalue = curvalue;
-			s_demos.list.top = top;
-		}
-	} else {
-		if (UseQuakeLiveDir) {
-			Demos_MenuInit("ql:demos");
-		} else {
-			Demos_MenuInit("demos");
-		}
-	}
-	UI_PushMenu(&s_demos.menu);
+void UI_DemosMenu( void ) {
+	Demos_MenuInit();
+	UI_PushMenu( &s_demos.menu );
 }

```

### `openarena-engine`  — sha256 `80e176b12042...`, 8652 bytes
Also identical in: ioquake3

_Diff stat: +74 / -285 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_demo2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_demo2.c	2026-04-16 22:48:25.894194800 +0100
@@ -33,7 +33,7 @@
 
 
 #define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
+#define ART_BACK1			"menu/art/back_1"	
 #define ART_GO0				"menu/art/play_0"
 #define ART_GO1				"menu/art/play_1"
 #define ART_FRAMEL			"menu/art/frame2_l"
@@ -42,9 +42,8 @@
 #define ART_ARROWLEFT		"menu/art/arrows_horz_left"
 #define ART_ARROWRIGHT		"menu/art/arrows_horz_right"
 
-#define MAX_DEMOS			4096  //128
-#define NAMEBUFSIZE			( MAX_DEMOS * 64 )
-#define MAX_DIR_STACK 128
+#define MAX_DEMOS			1024
+#define NAMEBUFSIZE			(MAX_DEMOS * 32)
 
 #define ID_BACK				10
 #define ID_GO				11
@@ -66,97 +65,19 @@
 	menulist_s		list;
 
 	menubitmap_s	arrows;
-	//menubitmap_s	left;
-	//menubitmap_s	right;
+	menubitmap_s	left;
+	menubitmap_s	right;
 	menubitmap_s	back;
 	menubitmap_s	go;
 
 	int				numDemos;
 	char			names[NAMEBUFSIZE];
-
+	
 	char			*demolist[MAX_DEMOS];
-	char dirName[MAX_OSPATH];
 } demos_t;
 
 static demos_t	s_demos;
 
-static qboolean UseQuakeLiveDir = qfalse;
-
-static void Demos_MenuInit (const char *dirName);
-
-
-static qboolean Demos_IsDir (const char *fname)
-{
-	int len;
-
-	len = strlen(fname);
-
-	if (fname[len - 1] == '/') {
-		return qtrue;
-	}
-
-	return qfalse;
-}
-
-static void Demos_PlayDemoOrChangeDir (void)
-{
-	const char *fname;
-	int i;
-	int len;
-	int end;
-	char strippedName[MAX_OSPATH];
-	const char *matchString;
-
-	if (UseQuakeLiveDir) {
-		matchString = "ql:demos";
-	} else {
-		matchString = "demos";
-	}
-
-	fname = s_demos.list.itemnames[s_demos.list.curvalue];
-	if (Demos_IsDir(fname)) {
-		//Com_Printf("dir: '%s'  '%s'\n", s_demos.dirName, fname);
-		if (!Q_stricmpn(fname, "../", strlen("../"))) {
-			if (!Q_stricmpn(s_demos.dirName, matchString, sizeof(s_demos.dirName))) {
-				//FIXME hack to avoid problems
-				return;
-			}
-			UI_PopMenu();
-			len = strlen(s_demos.dirName);
-			if (len <= 0) {
-				Com_Printf("^1Demos_PlayDemoOrChangeDir()  FIXME shouldn't happen dirName NULL\n");
-				return;
-			}
-
-			end = len - 1;
-			for (i = end;  i >= 0;  i--) {
-				if (s_demos.dirName[i] == '/') {
-					s_demos.dirName[i] = '\0';
-					break;
-				}
-			}
-
-			Demos_MenuInit(va("%s", s_demos.dirName));
-		} else {  // subdir
-			UI_PopMenu();
-			Q_strncpyz(strippedName, fname, sizeof(strippedName));
-			strippedName[strlen(fname) - 1] = '\0';
-			Demos_MenuInit(va("%s/%s", s_demos.dirName, strippedName));
-		}
-		//UI_PopMenu();
-		UI_PushMenu(&s_demos.menu);
-		return;
-	} else {
-		trap_Cvar_Set("lastdemodir", s_demos.dirName);
-		trap_Cvar_SetValue("lastdemodir_curvalue", s_demos.list.curvalue);
-		trap_Cvar_SetValue("lastdemodir_top", s_demos.list.top);
-
-		//FIXME hack
-		//Com_Printf("^3dirName '%s'  fname '%s'\n", s_demos.dirName, fname);
-		UI_ForceMenuOff();
-		trap_Cmd_ExecuteText(EXEC_APPEND, va("demo \"%s/%s\"\n", s_demos.dirName, fname));
-	}
-}
 
 /*
 ===============
@@ -164,168 +85,53 @@
 ===============
 */
 static void Demos_MenuEvent( void *ptr, int event ) {
-	//Com_Printf("demos menuEvent %p event %d  id %d\n", ptr, event, ((menucommon_s *)ptr)->id);
-
-	if (event == QM_DOUBLECLICKED) {
-		Demos_PlayDemoOrChangeDir();
-		return;
-	}
-
 	if( event != QM_ACTIVATED ) {
 		return;
 	}
 
 	switch( ((menucommon_s*)ptr)->id ) {
-		//case QM_ACTIVATED:
 	case ID_GO:
-		Demos_PlayDemoOrChangeDir();
+		UI_ForceMenuOff ();
+		trap_Cmd_ExecuteText( EXEC_APPEND, va( "demo %s\n",
+								s_demos.list.itemnames[s_demos.list.curvalue]) );
 		break;
 
-	case ID_BACK: {
-		const char *slash;
-
-		slash = strchr(s_demos.dirName, '/');
-		if (!slash) {
-			trap_Cvar_Set("lastdemodir", "");
-			UI_PopMenu();
-		} else {
-			// hack, set '../' as selected demo/dir
-			int i;
-
-			for (i = 0;  i < s_demos.list.numitems;  i++) {
-				const char *fname;
-
-				fname = s_demos.list.itemnames[i];
-				if (!Q_stricmpn(fname, "../", strlen("../"))) {
-					s_demos.list.curvalue = i;
-					break;
-				}
-			}
-
-			if (i < s_demos.list.numitems) {
-				// found '../'
-				Demos_PlayDemoOrChangeDir();
-			} else {
-				trap_Cvar_Set("lastdemodir", "");
-				UI_PopMenu();
-			}
-		}
+	case ID_BACK:
+		UI_PopMenu();
 		break;
-	}
 
 	case ID_LEFT:
-		//ScrollList_Key( &s_demos.list, K_LEFTARROW );
-		//Com_Printf("scroll left\n");
+		ScrollList_Key( &s_demos.list, K_LEFTARROW );
 		break;
 
 	case ID_RIGHT:
-		//ScrollList_Key( &s_demos.list, K_RIGHTARROW );
-		//Com_Printf("scroll right\n");
+		ScrollList_Key( &s_demos.list, K_RIGHTARROW );
 		break;
 	}
 }
 
 
 /*
-=================
-UI_DemosMenu_Key
-=================
-*/
-static sfxHandle_t UI_DemosMenu_Key (int key)
-{
-	//menucommon_s	*item;
-
-	//Com_Printf("ui demo menu key: %d  (curvalue %d, oldvalue %d)  m->nitems %d\n", key, s_demos.list.curvalue, s_demos.list.oldvalue, s_demos.menu.nitems);
-	if (key == K_ENTER  ||  key == K_KP_ENTER) {
-		// if 'back' button has focus don't play demo or change dir
-		//Com_Printf("focus: %d\n", Menu_ItemAtCursor(&s_demos.menu) == &s_demos.back);
-		if (Menu_ItemAtCursor(&s_demos.menu) != &s_demos.back) {
-			Demos_PlayDemoOrChangeDir();
-		}
-	}
-	//item = Menu_ItemAtCursor( &s_demos.menu );
-
-	// hack
-	if (key == K_ESCAPE) {
-		trap_Cvar_Set("lastdemodir", "");
-	}
-
-	return Menu_DefaultKey( &s_demos.menu, key );
-}
-
-
-static int CmpDemoNameStrings (const void *p1, const void *p2)
-{
-	int lens1, lens2;
-	char lastp1, lastp2;
-	const char *s1, *s2;
-
-	s1 = *(const char **)p1;
-	s2 = *(const char **)p2;
-
-	// special case for '../' to make it always appear as the first entry
-	if (!Q_stricmp(s1, "../")) {
-		return -1;
-	} else if (!Q_stricmp(s2, "../")) {
-		return 1;
-	}
-
-	if (!ui_demoSortDirFirst.integer) {
-		return Q_stricmp(s1, s2);
-	}
-
-	// sort directories first
-
-	lens1 = strlen(s1);
-	lens2 = strlen(s2);
-
-	if (lens1 < 1) {
-		lastp1 = '\0';
-	} else {
-		lastp1 = s1[strlen(s1) - 1];
-	}
-
-	if (lens2 < 1) {
-		lastp2 = '\0';
-	} else {
-		lastp2 = s2[strlen(s2) - 1];
-	}
-
-	if (lastp1 == '/'  &&  lastp2 != '/') {
-		return -1;
-	} else if (lastp1 != '/'  &&  lastp2 == '/') {
-		return 1;
-	}
-
-	return Q_stricmp(s1, s2);
-}
-
-/*
 ===============
 Demos_MenuInit
 ===============
 */
-static void Demos_MenuInit (const char *dirName)
-{
-	int		i;
+static void Demos_MenuInit( void ) {
+	int		i, j;
 	int		len;
 	char	*demoname, extension[32];
+	int	protocol, protocolLegacy;
 
 	memset( &s_demos, 0 ,sizeof(demos_t) );
-	s_demos.menu.key = UI_DemosMenu_Key;
-	Q_strncpyz(s_demos.dirName, dirName, sizeof(s_demos.dirName));
-	//Com_sprintf(s_demos.dirName, sizeof(s_demos.dirName), "%s%s", UseQuakeLiveDir ? "ql:" : "", dirName);
-	//Com_Printf("dirname '%s'\n", s_demos.dirName);
+
 	Demos_Cache();
 
 	s_demos.menu.fullscreen = qtrue;
 	s_demos.menu.wrapAround = qtrue;
 
-	s_demos.banner.generic.type		= MTYPE_BTEXT;  //MTYPE_PTEXT;  //MTYPE_BTEXT;
+	s_demos.banner.generic.type		= MTYPE_BTEXT;
 	s_demos.banner.generic.x		= 320;
 	s_demos.banner.generic.y		= 16;
-	//s_demos.banner.width 	= 10;
-	//s_demos.banner.height   = 10;
 	s_demos.banner.string			= "DEMOS";
 	s_demos.banner.color			= color_white;
 	s_demos.banner.style			= UI_CENTER;
@@ -333,7 +139,7 @@
 	s_demos.framel.generic.type		= MTYPE_BITMAP;
 	s_demos.framel.generic.name		= ART_FRAMEL;
 	s_demos.framel.generic.flags	= QMF_INACTIVE;
-	s_demos.framel.generic.x		= 0;
+	s_demos.framel.generic.x		= 0;  
 	s_demos.framel.generic.y		= 78;
 	s_demos.framel.width			= 256;
 	s_demos.framel.height			= 329;
@@ -346,7 +152,6 @@
 	s_demos.framer.width			= 256;
 	s_demos.framer.height			= 334;
 
-#if 1
 	s_demos.arrows.generic.type		= MTYPE_BITMAP;
 	s_demos.arrows.generic.name		= ART_ARROWS;
 	s_demos.arrows.generic.flags	= QMF_INACTIVE;
@@ -354,9 +159,7 @@
 	s_demos.arrows.generic.y		= 400;
 	s_demos.arrows.width			= ARROWS_WIDTH;
 	s_demos.arrows.height			= ARROWS_HEIGHT;
-#endif
 
-#if 0
 	s_demos.left.generic.type		= MTYPE_BITMAP;
 	s_demos.left.generic.flags		= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_MOUSEONLY;
 	s_demos.left.generic.x			= 320-ARROWS_WIDTH/2;
@@ -376,7 +179,6 @@
 	s_demos.right.width				= ARROWS_WIDTH/2;
 	s_demos.right.height			= ARROWS_HEIGHT;
 	s_demos.right.focuspic			= ART_ARROWRIGHT;
-#endif
 
 	s_demos.back.generic.type		= MTYPE_BITMAP;
 	s_demos.back.generic.name		= ART_BACK0;
@@ -404,63 +206,72 @@
 	s_demos.list.generic.flags		= QMF_PULSEIFFOCUS;
 	s_demos.list.generic.callback	= Demos_MenuEvent;
 	s_demos.list.generic.id			= ID_LIST;
-	s_demos.list.generic.x			= 20;  //118;
-	s_demos.list.generic.y			= 90;  //130;
-	s_demos.list.width				= 40;  //16;
-	s_demos.list.height				= 20;  //14;
-	Com_sprintf(extension, sizeof(extension), ".%s%d", DEMOEXT, (int) trap_Cvar_VariableValue("protocol"));
-	//s_demos.list.numitems			= trap_FS_GetFileList( "demos", extension, s_demos.names, NAMEBUFSIZE );
-	//s_demos.list.numitems			= trap_FS_GetFileList("demos", "*wantDirs", s_demos.names, NAMEBUFSIZE);
-	s_demos.list.numitems			= trap_FS_GetFileList(dirName, "*wantDirs", s_demos.names, NAMEBUFSIZE);
+	s_demos.list.generic.x			= 118;
+	s_demos.list.generic.y			= 130;
+	s_demos.list.width				= 16;
+	s_demos.list.height				= 14;
 	s_demos.list.itemnames			= (const char **)s_demos.demolist;
-	s_demos.list.columns			= 1;
+	s_demos.list.columns			= 3;
 
-	//Com_Printf("numitems: %d\n", s_demos.list.numitems);
+	protocolLegacy = trap_Cvar_VariableValue("com_legacyprotocol");
+	protocol = trap_Cvar_VariableValue("com_protocol");
 
-	if (!s_demos.list.numitems) {
-		//strcpy( s_demos.names, "No Demos Found." );
-		Q_strncpyz(s_demos.names, "../", sizeof(s_demos.names));
-		s_demos.list.numitems = 1;
+	if(!protocol)
+		protocol = trap_Cvar_VariableValue("protocol");
+	if(protocolLegacy == protocol)
+		protocolLegacy = 0;
 
-		//degenerate case, not selectable
-		s_demos.go.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
-	}
-	else if (s_demos.list.numitems > MAX_DEMOS) {
-		Com_Printf("^1maximum number of demos (%d) for a directory, skipping some demos\n", MAX_DEMOS);
-		s_demos.list.numitems = MAX_DEMOS;
-	}
+	Com_sprintf(extension, sizeof(extension), ".%s%d", DEMOEXT, protocol);
+	s_demos.numDemos = trap_FS_GetFileList("demos", extension, s_demos.names, ARRAY_LEN(s_demos.names));
 
 	demoname = s_demos.names;
+	i = 0;
 
-	for ( i = 0; i < s_demos.list.numitems; i++ ) {
-		s_demos.list.itemnames[i] = demoname;
+	for(j = 0; j < 2; j++)
+	{
+		if(s_demos.numDemos > MAX_DEMOS)
+			s_demos.numDemos = MAX_DEMOS;
+
+		for(; i < s_demos.numDemos; i++)
+		{
+			s_demos.list.itemnames[i] = demoname;
+		
+			len = strlen(demoname);
 
-		len = strlen( demoname );
-#if 0
-		// strip extension
-		if (!Q_stricmp(demoname +  len - 4,".dm3"))
-			demoname[len-4] = '\0';
-#endif
-//		Q_strupr(demoname);
+			demoname += len + 1;
+		}
 
-		demoname += len + 1;
+		if(!j)
+		{
+			if(protocolLegacy > 0 && s_demos.numDemos < MAX_DEMOS)
+			{
+				Com_sprintf(extension, sizeof(extension), ".%s%d", DEMOEXT, protocolLegacy);
+				s_demos.numDemos += trap_FS_GetFileList("demos", extension, demoname,
+									ARRAY_LEN(s_demos.names) - (demoname - s_demos.names));
+			}
+			else
+				break;
+		}
 	}
 
-	qsort(s_demos.list.itemnames, s_demos.list.numitems, sizeof(char *), CmpDemoNameStrings);
+	s_demos.list.numitems = s_demos.numDemos;
 
-#if 0
-	for (i = 0;  i < s_demos.list.numitems;  i++) {
-		Com_Printf("%d: %s\n", i, s_demos.list.itemnames[i]);
+	if(!s_demos.numDemos)
+	{
+		s_demos.list.itemnames[0] = "No Demos Found.";
+		s_demos.list.numitems = 1;
+
+		//degenerate case, not selectable
+		s_demos.go.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
 	}
-#endif
 
 	Menu_AddItem( &s_demos.menu, &s_demos.banner );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framel );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framer );
+	Menu_AddItem( &s_demos.menu, &s_demos.framel );
+	Menu_AddItem( &s_demos.menu, &s_demos.framer );
 	Menu_AddItem( &s_demos.menu, &s_demos.list );
-	//Menu_AddItem( &s_demos.menu, &s_demos.arrows );
-	//Menu_AddItem( &s_demos.menu, &s_demos.left );
-	//Menu_AddItem( &s_demos.menu, &s_demos.right );
+	Menu_AddItem( &s_demos.menu, &s_demos.arrows );
+	Menu_AddItem( &s_demos.menu, &s_demos.left );
+	Menu_AddItem( &s_demos.menu, &s_demos.right );
 	Menu_AddItem( &s_demos.menu, &s_demos.back );
 	Menu_AddItem( &s_demos.menu, &s_demos.go );
 }
@@ -475,8 +286,8 @@
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
 	trap_R_RegisterShaderNoMip( ART_GO0 );
 	trap_R_RegisterShaderNoMip( ART_GO1 );
-	//trap_R_RegisterShaderNoMip( ART_FRAMEL );
-	//trap_R_RegisterShaderNoMip( ART_FRAMER );
+	trap_R_RegisterShaderNoMip( ART_FRAMEL );
+	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_ARROWS );
 	trap_R_RegisterShaderNoMip( ART_ARROWLEFT );
 	trap_R_RegisterShaderNoMip( ART_ARROWRIGHT );
@@ -487,29 +298,7 @@
 UI_DemosMenu
 ===============
 */
-//void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir, int top, int curvalue)
-void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir)
-{
-	UseQuakeLiveDir = useQuakeLiveDir;
-
-	if (lastdemodir) {
-		int curvalue, top;
-
-		Demos_MenuInit(lastdemodir);
-		curvalue = trap_Cvar_VariableValue("lastdemodir_curvalue");
-		top = trap_Cvar_VariableValue("lastdemodir_top");
-
-		//Com_Printf("numitems %d  curvalue %d  top %d\n", s_demos.list.numitems, curvalue, top);
-		if (curvalue <= s_demos.list.numitems  &&  top <= s_demos.list.numitems) {
-			s_demos.list.curvalue = curvalue;
-			s_demos.list.top = top;
-		}
-	} else {
-		if (UseQuakeLiveDir) {
-			Demos_MenuInit("ql:demos");
-		} else {
-			Demos_MenuInit("demos");
-		}
-	}
-	UI_PushMenu(&s_demos.menu);
+void UI_DemosMenu( void ) {
+	Demos_MenuInit();
+	UI_PushMenu( &s_demos.menu );
 }

```

### `openarena-gamecode`  — sha256 `62ba25a035c0...`, 8680 bytes

_Diff stat: +80 / -297 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_demo2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_demo2.c	2026-04-16 22:48:24.181495000 +0100
@@ -32,25 +32,24 @@
 #include "ui_local.h"
 
 
-#define ART_BACK0			"menu/art/back_0"
-#define ART_BACK1			"menu/art/back_1"
-#define ART_GO0				"menu/art/play_0"
-#define ART_GO1				"menu/art/play_1"
-#define ART_FRAMEL			"menu/art/frame2_l"
-#define ART_FRAMER			"menu/art/frame1_r"
-#define ART_ARROWS			"menu/art/arrows_horz_0"
-#define ART_ARROWLEFT		"menu/art/arrows_horz_left"
-#define ART_ARROWRIGHT		"menu/art/arrows_horz_right"
-
-#define MAX_DEMOS			4096  //128
-#define NAMEBUFSIZE			( MAX_DEMOS * 64 )
-#define MAX_DIR_STACK 128
+#define ART_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1			"menu/" MENU_ART_DIR "/back_1"
+#define ART_GO0				"menu/" MENU_ART_DIR "/play_0"
+#define ART_GO1				"menu/" MENU_ART_DIR "/play_1"
+#define ART_FRAMEL			"menu/" MENU_ART_DIR "/frame2_l"
+#define ART_FRAMER			"menu/" MENU_ART_DIR "/frame1_r"
+#define ART_ARROWS			"menu/" MENU_ART_DIR "/arrows_vert_0"
+#define ART_ARROWUP		"menu/" MENU_ART_DIR "/arrows_vert_top"
+#define ART_ARROWDN		"menu/" MENU_ART_DIR "/arrows_vert_bot"
+
+#define MAX_DEMOS			128
+#define NAMEBUFSIZE			( MAX_DEMOS * 16 )
 
 #define ID_BACK				10
 #define ID_GO				11
 #define ID_LIST				12
-#define ID_RIGHT			13
-#define ID_LEFT				14
+#define ID_SCROLLDN			13
+#define ID_SCROLLUP				14
 
 #define ARROWS_WIDTH		128
 #define ARROWS_HEIGHT		48
@@ -66,97 +65,18 @@
 	menulist_s		list;
 
 	menubitmap_s	arrows;
-	//menubitmap_s	left;
-	//menubitmap_s	right;
+	menubitmap_s	left;
+	menubitmap_s	right;
 	menubitmap_s	back;
 	menubitmap_s	go;
 
 	int				numDemos;
 	char			names[NAMEBUFSIZE];
-
 	char			*demolist[MAX_DEMOS];
-	char dirName[MAX_OSPATH];
 } demos_t;
 
 static demos_t	s_demos;
 
-static qboolean UseQuakeLiveDir = qfalse;
-
-static void Demos_MenuInit (const char *dirName);
-
-
-static qboolean Demos_IsDir (const char *fname)
-{
-	int len;
-
-	len = strlen(fname);
-
-	if (fname[len - 1] == '/') {
-		return qtrue;
-	}
-
-	return qfalse;
-}
-
-static void Demos_PlayDemoOrChangeDir (void)
-{
-	const char *fname;
-	int i;
-	int len;
-	int end;
-	char strippedName[MAX_OSPATH];
-	const char *matchString;
-
-	if (UseQuakeLiveDir) {
-		matchString = "ql:demos";
-	} else {
-		matchString = "demos";
-	}
-
-	fname = s_demos.list.itemnames[s_demos.list.curvalue];
-	if (Demos_IsDir(fname)) {
-		//Com_Printf("dir: '%s'  '%s'\n", s_demos.dirName, fname);
-		if (!Q_stricmpn(fname, "../", strlen("../"))) {
-			if (!Q_stricmpn(s_demos.dirName, matchString, sizeof(s_demos.dirName))) {
-				//FIXME hack to avoid problems
-				return;
-			}
-			UI_PopMenu();
-			len = strlen(s_demos.dirName);
-			if (len <= 0) {
-				Com_Printf("^1Demos_PlayDemoOrChangeDir()  FIXME shouldn't happen dirName NULL\n");
-				return;
-			}
-
-			end = len - 1;
-			for (i = end;  i >= 0;  i--) {
-				if (s_demos.dirName[i] == '/') {
-					s_demos.dirName[i] = '\0';
-					break;
-				}
-			}
-
-			Demos_MenuInit(va("%s", s_demos.dirName));
-		} else {  // subdir
-			UI_PopMenu();
-			Q_strncpyz(strippedName, fname, sizeof(strippedName));
-			strippedName[strlen(fname) - 1] = '\0';
-			Demos_MenuInit(va("%s/%s", s_demos.dirName, strippedName));
-		}
-		//UI_PopMenu();
-		UI_PushMenu(&s_demos.menu);
-		return;
-	} else {
-		trap_Cvar_Set("lastdemodir", s_demos.dirName);
-		trap_Cvar_SetValue("lastdemodir_curvalue", s_demos.list.curvalue);
-		trap_Cvar_SetValue("lastdemodir_top", s_demos.list.top);
-
-		//FIXME hack
-		//Com_Printf("^3dirName '%s'  fname '%s'\n", s_demos.dirName, fname);
-		UI_ForceMenuOff();
-		trap_Cmd_ExecuteText(EXEC_APPEND, va("demo \"%s/%s\"\n", s_demos.dirName, fname));
-	}
-}
 
 /*
 ===============
@@ -164,64 +84,28 @@
 ===============
 */
 static void Demos_MenuEvent( void *ptr, int event ) {
-	//Com_Printf("demos menuEvent %p event %d  id %d\n", ptr, event, ((menucommon_s *)ptr)->id);
-
-	if (event == QM_DOUBLECLICKED) {
-		Demos_PlayDemoOrChangeDir();
-		return;
-	}
-
 	if( event != QM_ACTIVATED ) {
 		return;
 	}
 
 	switch( ((menucommon_s*)ptr)->id ) {
-		//case QM_ACTIVATED:
 	case ID_GO:
-		Demos_PlayDemoOrChangeDir();
+		UI_ForceMenuOff ();
+		trap_Cmd_ExecuteText( EXEC_APPEND, va( "demo %s\n",
+								s_demos.list.itemnames[s_demos.list.curvalue]) );
 		break;
-
-	case ID_BACK: {
-		const char *slash;
-
-		slash = strchr(s_demos.dirName, '/');
-		if (!slash) {
-			trap_Cvar_Set("lastdemodir", "");
-			UI_PopMenu();
-		} else {
-			// hack, set '../' as selected demo/dir
-			int i;
-
-			for (i = 0;  i < s_demos.list.numitems;  i++) {
-				const char *fname;
-
-				fname = s_demos.list.itemnames[i];
-				if (!Q_stricmpn(fname, "../", strlen("../"))) {
-					s_demos.list.curvalue = i;
-					break;
-				}
-			}
-
-			if (i < s_demos.list.numitems) {
-				// found '../'
-				Demos_PlayDemoOrChangeDir();
-			} else {
-				trap_Cvar_Set("lastdemodir", "");
-				UI_PopMenu();
-			}
-		}
+	case ID_BACK:
+		UI_PopMenu();
 		break;
-	}
 
-	case ID_LEFT:
-		//ScrollList_Key( &s_demos.list, K_LEFTARROW );
-		//Com_Printf("scroll left\n");
+	case ID_SCROLLUP:
+		ScrollList_Key( &s_demos.list, K_UPARROW );
 		break;
 
-	case ID_RIGHT:
-		//ScrollList_Key( &s_demos.list, K_RIGHTARROW );
-		//Com_Printf("scroll right\n");
-		break;
+	case ID_SCROLLDN:
+		ScrollList_Key( &s_demos.list, K_DOWNARROW );
+                break;
+
 	}
 }
 
@@ -231,73 +115,19 @@
 UI_DemosMenu_Key
 =================
 */
-static sfxHandle_t UI_DemosMenu_Key (int key)
-{
-	//menucommon_s	*item;
-
-	//Com_Printf("ui demo menu key: %d  (curvalue %d, oldvalue %d)  m->nitems %d\n", key, s_demos.list.curvalue, s_demos.list.oldvalue, s_demos.menu.nitems);
-	if (key == K_ENTER  ||  key == K_KP_ENTER) {
-		// if 'back' button has focus don't play demo or change dir
-		//Com_Printf("focus: %d\n", Menu_ItemAtCursor(&s_demos.menu) == &s_demos.back);
-		if (Menu_ItemAtCursor(&s_demos.menu) != &s_demos.back) {
-			Demos_PlayDemoOrChangeDir();
-		}
+static sfxHandle_t UI_DemosMenu_Key( int key ) {
+	if( key == K_MWHEELUP ) {
+		ScrollList_Key( &s_demos.list, K_UPARROW );
 	}
-	//item = Menu_ItemAtCursor( &s_demos.menu );
-
-	// hack
-	if (key == K_ESCAPE) {
-		trap_Cvar_Set("lastdemodir", "");
+	if( key == K_MWHEELDOWN ) {
+		ScrollList_Key( &s_demos.list, K_DOWNARROW );
 	}
-
 	return Menu_DefaultKey( &s_demos.menu, key );
 }
 
 
-static int CmpDemoNameStrings (const void *p1, const void *p2)
-{
-	int lens1, lens2;
-	char lastp1, lastp2;
-	const char *s1, *s2;
-
-	s1 = *(const char **)p1;
-	s2 = *(const char **)p2;
-
-	// special case for '../' to make it always appear as the first entry
-	if (!Q_stricmp(s1, "../")) {
-		return -1;
-	} else if (!Q_stricmp(s2, "../")) {
-		return 1;
-	}
-
-	if (!ui_demoSortDirFirst.integer) {
-		return Q_stricmp(s1, s2);
-	}
-
-	// sort directories first
-
-	lens1 = strlen(s1);
-	lens2 = strlen(s2);
-
-	if (lens1 < 1) {
-		lastp1 = '\0';
-	} else {
-		lastp1 = s1[strlen(s1) - 1];
-	}
-
-	if (lens2 < 1) {
-		lastp2 = '\0';
-	} else {
-		lastp2 = s2[strlen(s2) - 1];
-	}
-
-	if (lastp1 == '/'  &&  lastp2 != '/') {
-		return -1;
-	} else if (lastp1 != '/'  &&  lastp2 == '/') {
-		return 1;
-	}
-
-	return Q_stricmp(s1, s2);
+static void meowdrawdemo( void ) {
+    Menu_Draw(&s_demos.menu);
 }
 
 /*
@@ -305,27 +135,23 @@
 Demos_MenuInit
 ===============
 */
-static void Demos_MenuInit (const char *dirName)
-{
+static void Demos_MenuInit( void ) {
 	int		i;
 	int		len;
 	char	*demoname, extension[32];
 
 	memset( &s_demos, 0 ,sizeof(demos_t) );
 	s_demos.menu.key = UI_DemosMenu_Key;
-	Q_strncpyz(s_demos.dirName, dirName, sizeof(s_demos.dirName));
-	//Com_sprintf(s_demos.dirName, sizeof(s_demos.dirName), "%s%s", UseQuakeLiveDir ? "ql:" : "", dirName);
-	//Com_Printf("dirname '%s'\n", s_demos.dirName);
+
 	Demos_Cache();
 
 	s_demos.menu.fullscreen = qtrue;
-	s_demos.menu.wrapAround = qtrue;
+        s_demos.menu.wrapAround = qtrue;
+        s_demos.menu.draw = meowdrawdemo;
 
-	s_demos.banner.generic.type		= MTYPE_BTEXT;  //MTYPE_PTEXT;  //MTYPE_BTEXT;
+	s_demos.banner.generic.type		= MTYPE_BTEXT;
 	s_demos.banner.generic.x		= 320;
 	s_demos.banner.generic.y		= 16;
-	//s_demos.banner.width 	= 10;
-	//s_demos.banner.height   = 10;
 	s_demos.banner.string			= "DEMOS";
 	s_demos.banner.color			= color_white;
 	s_demos.banner.style			= UI_CENTER;
@@ -346,37 +172,33 @@
 	s_demos.framer.width			= 256;
 	s_demos.framer.height			= 334;
 
-#if 1
 	s_demos.arrows.generic.type		= MTYPE_BITMAP;
 	s_demos.arrows.generic.name		= ART_ARROWS;
 	s_demos.arrows.generic.flags	= QMF_INACTIVE;
-	s_demos.arrows.generic.x		= 320-ARROWS_WIDTH/2;
-	s_demos.arrows.generic.y		= 400;
-	s_demos.arrows.width			= ARROWS_WIDTH;
-	s_demos.arrows.height			= ARROWS_HEIGHT;
-#endif
+	s_demos.arrows.generic.x		= 512+48+12;
+	s_demos.arrows.generic.y		= 240-64+48;
+	s_demos.arrows.width			= 64;
+	s_demos.arrows.height			= 128;
 
-#if 0
 	s_demos.left.generic.type		= MTYPE_BITMAP;
 	s_demos.left.generic.flags		= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_MOUSEONLY;
-	s_demos.left.generic.x			= 320-ARROWS_WIDTH/2;
-	s_demos.left.generic.y			= 400;
-	s_demos.left.generic.id			= ID_LEFT;
+	s_demos.left.generic.x			= 512+48+12;
+	s_demos.left.generic.y			= 240-64+48;
+	s_demos.left.generic.id			= ID_SCROLLUP;
 	s_demos.left.generic.callback	= Demos_MenuEvent;
-	s_demos.left.width				= ARROWS_WIDTH/2;
-	s_demos.left.height				= ARROWS_HEIGHT;
-	s_demos.left.focuspic			= ART_ARROWLEFT;
+	s_demos.left.width				= 64;
+	s_demos.left.height				= 64;
+	s_demos.left.focuspic			= ART_ARROWUP;
 
 	s_demos.right.generic.type		= MTYPE_BITMAP;
 	s_demos.right.generic.flags		= QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_MOUSEONLY;
-	s_demos.right.generic.x			= 320;
-	s_demos.right.generic.y			= 400;
-	s_demos.right.generic.id		= ID_RIGHT;
+	s_demos.right.generic.x			= 512+48+12;
+	s_demos.right.generic.y			= 240+48;
+	s_demos.right.generic.id		= ID_SCROLLDN;
 	s_demos.right.generic.callback	= Demos_MenuEvent;
-	s_demos.right.width				= ARROWS_WIDTH/2;
-	s_demos.right.height			= ARROWS_HEIGHT;
-	s_demos.right.focuspic			= ART_ARROWRIGHT;
-#endif
+	s_demos.right.width				= 64;
+	s_demos.right.height			= 64;
+	s_demos.right.focuspic			= ART_ARROWDN;
 
 	s_demos.back.generic.type		= MTYPE_BITMAP;
 	s_demos.back.generic.name		= ART_BACK0;
@@ -401,66 +223,49 @@
 	s_demos.go.focuspic				= ART_GO1;
 
 	s_demos.list.generic.type		= MTYPE_SCROLLLIST;
-	s_demos.list.generic.flags		= QMF_PULSEIFFOCUS;
+	s_demos.list.generic.flags		= QMF_HIGHLIGHT_IF_FOCUS|QMF_SMALLFONT;
 	s_demos.list.generic.callback	= Demos_MenuEvent;
 	s_demos.list.generic.id			= ID_LIST;
-	s_demos.list.generic.x			= 20;  //118;
-	s_demos.list.generic.y			= 90;  //130;
-	s_demos.list.width				= 40;  //16;
-	s_demos.list.height				= 20;  //14;
-	Com_sprintf(extension, sizeof(extension), ".%s%d", DEMOEXT, (int) trap_Cvar_VariableValue("protocol"));
-	//s_demos.list.numitems			= trap_FS_GetFileList( "demos", extension, s_demos.names, NAMEBUFSIZE );
-	//s_demos.list.numitems			= trap_FS_GetFileList("demos", "*wantDirs", s_demos.names, NAMEBUFSIZE);
-	s_demos.list.numitems			= trap_FS_GetFileList(dirName, "*wantDirs", s_demos.names, NAMEBUFSIZE);
+	s_demos.list.generic.x			= 22;
+	s_demos.list.generic.y			= 50;
+	s_demos.list.width				= 70;
+	s_demos.list.height				= 23;
+	Com_sprintf(extension, sizeof(extension), "dm_%d", (int)trap_Cvar_VariableValue( "protocol" ) );
+	s_demos.list.numitems			= trap_FS_GetFileList( "demos", extension, s_demos.names, NAMEBUFSIZE );
 	s_demos.list.itemnames			= (const char **)s_demos.demolist;
-	s_demos.list.columns			= 1;
-
-	//Com_Printf("numitems: %d\n", s_demos.list.numitems);
+	//s_demos.list.columns			= 1;
 
 	if (!s_demos.list.numitems) {
-		//strcpy( s_demos.names, "No Demos Found." );
-		Q_strncpyz(s_demos.names, "../", sizeof(s_demos.names));
+		strcpy( s_demos.names, "No Demos Found." );
 		s_demos.list.numitems = 1;
 
 		//degenerate case, not selectable
 		s_demos.go.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
 	}
-	else if (s_demos.list.numitems > MAX_DEMOS) {
-		Com_Printf("^1maximum number of demos (%d) for a directory, skipping some demos\n", MAX_DEMOS);
+	else if (s_demos.list.numitems > MAX_DEMOS)
 		s_demos.list.numitems = MAX_DEMOS;
-	}
 
 	demoname = s_demos.names;
-
 	for ( i = 0; i < s_demos.list.numitems; i++ ) {
 		s_demos.list.itemnames[i] = demoname;
 
-		len = strlen( demoname );
-#if 0
 		// strip extension
-		if (!Q_stricmp(demoname +  len - 4,".dm3"))
+		len = strlen( demoname );
+		if (Q_strequal(demoname +  len - 4,".dm3"))
 			demoname[len-4] = '\0';
-#endif
+
 //		Q_strupr(demoname);
 
 		demoname += len + 1;
 	}
 
-	qsort(s_demos.list.itemnames, s_demos.list.numitems, sizeof(char *), CmpDemoNameStrings);
-
-#if 0
-	for (i = 0;  i < s_demos.list.numitems;  i++) {
-		Com_Printf("%d: %s\n", i, s_demos.list.itemnames[i]);
-	}
-#endif
-
 	Menu_AddItem( &s_demos.menu, &s_demos.banner );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framel );
-	//Menu_AddItem( &s_demos.menu, &s_demos.framer );
+	Menu_AddItem( &s_demos.menu, &s_demos.framel );
+	Menu_AddItem( &s_demos.menu, &s_demos.framer );
 	Menu_AddItem( &s_demos.menu, &s_demos.list );
-	//Menu_AddItem( &s_demos.menu, &s_demos.arrows );
-	//Menu_AddItem( &s_demos.menu, &s_demos.left );
-	//Menu_AddItem( &s_demos.menu, &s_demos.right );
+	Menu_AddItem( &s_demos.menu, &s_demos.arrows );
+	Menu_AddItem( &s_demos.menu, &s_demos.left );
+	Menu_AddItem( &s_demos.menu, &s_demos.right );
 	Menu_AddItem( &s_demos.menu, &s_demos.back );
 	Menu_AddItem( &s_demos.menu, &s_demos.go );
 }
@@ -475,11 +280,11 @@
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
 	trap_R_RegisterShaderNoMip( ART_GO0 );
 	trap_R_RegisterShaderNoMip( ART_GO1 );
-	//trap_R_RegisterShaderNoMip( ART_FRAMEL );
-	//trap_R_RegisterShaderNoMip( ART_FRAMER );
+	trap_R_RegisterShaderNoMip( ART_FRAMEL );
+	trap_R_RegisterShaderNoMip( ART_FRAMER );
 	trap_R_RegisterShaderNoMip( ART_ARROWS );
-	trap_R_RegisterShaderNoMip( ART_ARROWLEFT );
-	trap_R_RegisterShaderNoMip( ART_ARROWRIGHT );
+	trap_R_RegisterShaderNoMip( ART_ARROWUP );
+	trap_R_RegisterShaderNoMip( ART_ARROWDN );
 }
 
 /*
@@ -487,29 +292,7 @@
 UI_DemosMenu
 ===============
 */
-//void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir, int top, int curvalue)
-void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir)
-{
-	UseQuakeLiveDir = useQuakeLiveDir;
-
-	if (lastdemodir) {
-		int curvalue, top;
-
-		Demos_MenuInit(lastdemodir);
-		curvalue = trap_Cvar_VariableValue("lastdemodir_curvalue");
-		top = trap_Cvar_VariableValue("lastdemodir_top");
-
-		//Com_Printf("numitems %d  curvalue %d  top %d\n", s_demos.list.numitems, curvalue, top);
-		if (curvalue <= s_demos.list.numitems  &&  top <= s_demos.list.numitems) {
-			s_demos.list.curvalue = curvalue;
-			s_demos.list.top = top;
-		}
-	} else {
-		if (UseQuakeLiveDir) {
-			Demos_MenuInit("ql:demos");
-		} else {
-			Demos_MenuInit("demos");
-		}
-	}
-	UI_PushMenu(&s_demos.menu);
+void UI_DemosMenu( void ) {
+	Demos_MenuInit();
+	UI_PushMenu( &s_demos.menu );
 }

```
