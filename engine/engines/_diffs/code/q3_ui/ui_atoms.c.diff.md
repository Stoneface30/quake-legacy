# Diff: `code/q3_ui/ui_atoms.c`
**Canonical:** `wolfcamql-src` (sha256 `4b1c12fc107a...`, 27966 bytes)

## Variants

### `quake3-source`  — sha256 `5f749c5ed7fb...`, 26789 bytes

_Diff stat: +56 / -111 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_atoms.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_atoms.c	2026-04-16 20:02:19.944311700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,15 +30,18 @@
 uiStatic_t		uis;
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
@@ -46,12 +49,14 @@
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
 /*
 =================
 UI_ClampCvar
@@ -330,6 +335,8 @@
 #define PROPB_SPACE_WIDTH	12
 #define PROPB_HEIGHT		36
 
+// bk001205 - code below duplicated in cgame/cg_drawtools.c
+// bk001205 - FIXME: does this belong in ui_shared.c?
 /*
 =================
 UI_DrawBannerString
@@ -338,7 +345,7 @@
 static void UI_DrawBannerString2( int x, int y, const char* str, vec4_t color )
 {
 	const char* s;
-	unsigned char	ch;
+	unsigned char	ch; // bk001204 - unsigned
 	float	ax;
 	float	ay;
 	float	aw;
@@ -351,15 +358,15 @@
 	// draw the colored text
 	trap_R_SetColor( color );
 	
-	ax = x * uis.xscale + uis.bias;
-	ay = y * uis.yscale;
+	ax = x * uis.scale + uis.bias;
+	ay = y * uis.scale;
 
 	s = str;
 	while ( *s )
 	{
 		ch = *s & 127;
 		if ( ch == ' ' ) {
-			ax += ((float)PROPB_SPACE_WIDTH + (float)PROPB_GAP_WIDTH)* uis.xscale;
+			ax += ((float)PROPB_SPACE_WIDTH + (float)PROPB_GAP_WIDTH)* uis.scale;
 		}
 		else if ( ch >= 'A' && ch <= 'Z' ) {
 			ch -= 'A';
@@ -367,10 +374,10 @@
 			frow = (float)propMapB[ch][1] / 256.0f;
 			fwidth = (float)propMapB[ch][2] / 256.0f;
 			fheight = (float)PROPB_HEIGHT / 256.0f;
-			aw = (float)propMapB[ch][2] * uis.xscale;
-			ah = (float)PROPB_HEIGHT * uis.yscale;
+			aw = (float)propMapB[ch][2] * uis.scale;
+			ah = (float)PROPB_HEIGHT * uis.scale;
 			trap_R_DrawStretchPic( ax, ay, aw, ah, fcol, frow, fcol+fwidth, frow+fheight, uis.charsetPropB );
-			ax += (aw + (float)PROPB_GAP_WIDTH * uis.xscale);
+			ax += (aw + (float)PROPB_GAP_WIDTH * uis.scale);
 		}
 		s++;
 	}
@@ -448,10 +455,10 @@
 static void UI_DrawProportionalString2( int x, int y, const char* str, vec4_t color, float sizeScale, qhandle_t charset )
 {
 	const char* s;
-	unsigned char	ch;
+	unsigned char	ch; // bk001204 - unsigned
 	float	ax;
 	float	ay;
-	float	aw = 0;
+	float	aw = 0; // bk001204 - init
 	float	ah;
 	float	frow;
 	float	fcol;
@@ -461,27 +468,27 @@
 	// draw the colored text
 	trap_R_SetColor( color );
 	
-	ax = x * uis.xscale + uis.bias;
-	ay = y * uis.yscale;
+	ax = x * uis.scale + uis.bias;
+	ay = y * uis.scale;
 
 	s = str;
 	while ( *s )
 	{
 		ch = *s & 127;
 		if ( ch == ' ' ) {
-			aw = (float)PROP_SPACE_WIDTH * uis.xscale * sizeScale;
+			aw = (float)PROP_SPACE_WIDTH * uis.scale * sizeScale;
 		}
 		else if ( propMap[ch][2] != -1 ) {
 			fcol = (float)propMap[ch][0] / 256.0f;
 			frow = (float)propMap[ch][1] / 256.0f;
 			fwidth = (float)propMap[ch][2] / 256.0f;
 			fheight = (float)PROP_HEIGHT / 256.0f;
-			aw = (float)propMap[ch][2] * uis.xscale * sizeScale;
-			ah = (float)PROP_HEIGHT * uis.yscale * sizeScale;
+			aw = (float)propMap[ch][2] * uis.scale * sizeScale;
+			ah = (float)PROP_HEIGHT * uis.scale * sizeScale;
 			trap_R_DrawStretchPic( ax, ay, aw, ah, fcol, frow, fcol+fwidth, frow+fheight, charset );
 		}
 
-		ax += (aw + (float)PROP_GAP_WIDTH * uis.xscale * sizeScale);
+		ax += (aw + (float)PROP_GAP_WIDTH * uis.scale * sizeScale);
 		s++;
 	}
 
@@ -512,10 +519,6 @@
 	int		width;
 	float	sizeScale;
 
-	if( !str ) {
-		return;
-	}
-
 	sizeScale = UI_ProportionalSizeScale( style );
 
 	switch( style & UI_FORMATMASK ) {
@@ -656,10 +659,10 @@
 	// draw the colored text
 	trap_R_SetColor( color );
 	
-	ax = x * uis.xscale + uis.bias;
-	ay = y * uis.yscale;
-	aw = charw * uis.xscale;
-	ah = charh * uis.yscale;
+	ax = x * uis.scale + uis.bias;
+	ay = y * uis.scale;
+	aw = charw * uis.scale;
+	ah = charh * uis.scale;
 
 	s = str;
 	while ( *s )
@@ -807,7 +810,7 @@
 
 void UI_SetActiveMenu( uiMenuCommand_t menu ) {
 	// this should be the ONLY way the menu system is brought up
-	// ensure minimum menu data is cached
+	// enusure minumum menu data is cached
 	Menu_Cache();
 
 	switch ( menu ) {
@@ -818,10 +821,10 @@
 		UI_MainMenu();
 		return;
 	case UIMENU_NEED_CD:
-		UI_ConfirmMenu( "Insert the CD", 0, NeedCDAction );
+		UI_ConfirmMenu( "Insert the CD", (voidfunc_f)NULL, NeedCDAction );
 		return;
 	case UIMENU_BAD_CD_KEY:
-		UI_ConfirmMenu( "Bad CD Key", 0, NeedCDKeyAction );
+		UI_ConfirmMenu( "Bad CD Key", (voidfunc_f)NULL, NeedCDKeyAction );
 		return;
 	case UIMENU_INGAME:
 		/*
@@ -833,10 +836,11 @@
 		UI_InGameMenu();
 		return;
 		
+	// bk001204
 	case UIMENU_TEAM:
 	case UIMENU_POSTGAME:
 	default:
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 	  Com_Printf("UI_SetActiveMenu: bad enum %d\n", menu );
 #endif
 	  break;
@@ -852,45 +856,6 @@
 	sfxHandle_t		s;
 
 	if (!uis.activemenu) {
-		char buf[MAX_STRING_CHARS];
-
-		if (!down) {
-			return;
-		}
-
-		// menu is NULL but we could be playing cinematic
-		// check for binds to function keys
-
-		switch (key) {
-		case K_F1:
-		case K_F2:
-		case K_F3:
-		case K_F4:
-		case K_F5:
-		case K_F6:
-		case K_F7:
-		case K_F8:
-		case K_F9:
-		case K_F10:
-		case K_F11:
-		case K_F12:
-		case K_F13:
-		case K_F14:
-		case K_F15:
-			// got a function key
-			break;
-		default:
-			// no function key
-			return;
-		}
-
-		buf[0] = '\0';
-		trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-		if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-			return;
-		}
-		trap_Cmd_ExecuteText(EXEC_NOW, buf);
-
 		return;
 	}
 
@@ -912,35 +877,26 @@
 UI_MouseEvent
 =================
 */
-void UI_MouseEvent( int dx, int dy, qboolean active )
+void UI_MouseEvent( int dx, int dy )
 {
 	int				i;
-	int				bias;
 	menucommon_s*	m;
 
 	if (!uis.activemenu)
 		return;
 
-	// convert X bias to 640 coords
-	bias = uis.bias / uis.xscale;
-
 	// update mouse screen position
-	if (active) {
-		uis.cursorx += dx;
-		if (uis.cursorx < -bias)
-			uis.cursorx = -bias;
-		else if (uis.cursorx > SCREEN_WIDTH+bias)
-			uis.cursorx = SCREEN_WIDTH+bias;
-
-		uis.cursory += dy;
-		if (uis.cursory < 0)
-			uis.cursory = 0;
-		else if (uis.cursory > SCREEN_HEIGHT)
-			uis.cursory = SCREEN_HEIGHT;
-	} else {
-		uis.cursorx = -bias + (dx * (float)((float)(SCREEN_WIDTH + 2 * bias) / (float)uis.glconfig.vidWidth));
-		uis.cursory = dy * (float)((float)SCREEN_HEIGHT / (float)uis.glconfig.vidHeight);
-	}
+	uis.cursorx += dx;
+	if (uis.cursorx < 0)
+		uis.cursorx = 0;
+	else if (uis.cursorx > SCREEN_WIDTH)
+		uis.cursorx = SCREEN_WIDTH;
+
+	uis.cursory += dy;
+	if (uis.cursory < 0)
+		uis.cursory = 0;
+	else if (uis.cursory > SCREEN_HEIGHT)
+		uis.cursory = SCREEN_HEIGHT;
 
 	// region test the active menu items
 	for (i=0; i<uis.activemenu->nitems; i++)
@@ -1047,9 +1003,6 @@
 qboolean UI_ConsoleCommand( int realTime ) {
 	char	*cmd;
 
-	uis.frametime = realTime - uis.realtime;
-	uis.realtime = realTime;
-
 	cmd = UI_Argv( 0 );
 
 	// ensure minimum menu data is available
@@ -1112,8 +1065,6 @@
 =================
 */
 void UI_Init( void ) {
-	Com_Printf("UI_Init() version: %s\n", WOLFCAM_VERSION);
-
 	UI_RegisterCvars();
 
 	UI_InitGameinfo();
@@ -1122,12 +1073,10 @@
 	trap_GetGlconfig( &uis.glconfig );
 
 	// for 640x480 virtualized screen
-	uis.xscale = uis.glconfig.vidWidth * (1.0/640.0);
-	uis.yscale = uis.glconfig.vidHeight * (1.0/480.0);
+	uis.scale = uis.glconfig.vidHeight * (1.0/480.0);
 	if ( uis.glconfig.vidWidth * 480 > uis.glconfig.vidHeight * 640 ) {
 		// wide screen
 		uis.bias = 0.5 * ( uis.glconfig.vidWidth - ( uis.glconfig.vidHeight * (640.0/480.0) ) );
-		uis.xscale = uis.yscale;
 	}
 	else {
 		// no wide screen
@@ -1150,10 +1099,10 @@
 */
 void UI_AdjustFrom640( float *x, float *y, float *w, float *h ) {
 	// expect valid pointers
-	*x = *x * uis.xscale + uis.bias;
-	*y *= uis.yscale;
-	*w *= uis.xscale;
-	*h *= uis.yscale;
+	*x = *x * uis.scale + uis.bias;
+	*y *= uis.scale;
+	*w *= uis.scale;
+	*h *= uis.scale;
 }
 
 void UI_DrawNamedPic( float x, float y, float width, float height, const char *picname ) {
@@ -1254,8 +1203,6 @@
 
 	UI_UpdateCvars();
 
-	trap_R_BeginHud();
-
 	if ( uis.activemenu )
 	{
 		if (uis.activemenu->fullscreen)
@@ -1275,18 +1222,16 @@
 			Menu_Draw( uis.activemenu );
 
 		if( uis.firstdraw ) {
-			UI_MouseEvent( 0, 0, qtrue );
+			UI_MouseEvent( 0, 0 );
 			uis.firstdraw = qfalse;
 		}
 	}
 
 	// draw cursor
 	UI_SetColor( NULL );
-	if (uis.glconfig.isFullscreen  ||  (int)trap_Cvar_VariableValue("in_nograb") == 0) {
-		UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
-	}
+	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
 
-#ifndef NQDEBUG
+#ifndef NDEBUG
 	if (uis.debug)
 	{
 		// cursor coordinates

```

### `ioquake3`  — sha256 `6b08e79da7af...`, 26809 bytes

_Diff stat: +16 / -66 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_atoms.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_atoms.c	2026-04-16 20:02:21.552427700 +0100
@@ -836,7 +836,7 @@
 	case UIMENU_TEAM:
 	case UIMENU_POSTGAME:
 	default:
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 	  Com_Printf("UI_SetActiveMenu: bad enum %d\n", menu );
 #endif
 	  break;
@@ -852,45 +852,6 @@
 	sfxHandle_t		s;
 
 	if (!uis.activemenu) {
-		char buf[MAX_STRING_CHARS];
-
-		if (!down) {
-			return;
-		}
-
-		// menu is NULL but we could be playing cinematic
-		// check for binds to function keys
-
-		switch (key) {
-		case K_F1:
-		case K_F2:
-		case K_F3:
-		case K_F4:
-		case K_F5:
-		case K_F6:
-		case K_F7:
-		case K_F8:
-		case K_F9:
-		case K_F10:
-		case K_F11:
-		case K_F12:
-		case K_F13:
-		case K_F14:
-		case K_F15:
-			// got a function key
-			break;
-		default:
-			// no function key
-			return;
-		}
-
-		buf[0] = '\0';
-		trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-		if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-			return;
-		}
-		trap_Cmd_ExecuteText(EXEC_NOW, buf);
-
 		return;
 	}
 
@@ -912,7 +873,7 @@
 UI_MouseEvent
 =================
 */
-void UI_MouseEvent( int dx, int dy, qboolean active )
+void UI_MouseEvent( int dx, int dy )
 {
 	int				i;
 	int				bias;
@@ -925,22 +886,17 @@
 	bias = uis.bias / uis.xscale;
 
 	// update mouse screen position
-	if (active) {
-		uis.cursorx += dx;
-		if (uis.cursorx < -bias)
-			uis.cursorx = -bias;
-		else if (uis.cursorx > SCREEN_WIDTH+bias)
-			uis.cursorx = SCREEN_WIDTH+bias;
-
-		uis.cursory += dy;
-		if (uis.cursory < 0)
-			uis.cursory = 0;
-		else if (uis.cursory > SCREEN_HEIGHT)
-			uis.cursory = SCREEN_HEIGHT;
-	} else {
-		uis.cursorx = -bias + (dx * (float)((float)(SCREEN_WIDTH + 2 * bias) / (float)uis.glconfig.vidWidth));
-		uis.cursory = dy * (float)((float)SCREEN_HEIGHT / (float)uis.glconfig.vidHeight);
-	}
+	uis.cursorx += dx;
+	if (uis.cursorx < -bias)
+		uis.cursorx = -bias;
+	else if (uis.cursorx > SCREEN_WIDTH+bias)
+		uis.cursorx = SCREEN_WIDTH+bias;
+
+	uis.cursory += dy;
+	if (uis.cursory < 0)
+		uis.cursory = 0;
+	else if (uis.cursory > SCREEN_HEIGHT)
+		uis.cursory = SCREEN_HEIGHT;
 
 	// region test the active menu items
 	for (i=0; i<uis.activemenu->nitems; i++)
@@ -1112,8 +1068,6 @@
 =================
 */
 void UI_Init( void ) {
-	Com_Printf("UI_Init() version: %s\n", WOLFCAM_VERSION);
-
 	UI_RegisterCvars();
 
 	UI_InitGameinfo();
@@ -1254,8 +1208,6 @@
 
 	UI_UpdateCvars();
 
-	trap_R_BeginHud();
-
 	if ( uis.activemenu )
 	{
 		if (uis.activemenu->fullscreen)
@@ -1275,18 +1227,16 @@
 			Menu_Draw( uis.activemenu );
 
 		if( uis.firstdraw ) {
-			UI_MouseEvent( 0, 0, qtrue );
+			UI_MouseEvent( 0, 0 );
 			uis.firstdraw = qfalse;
 		}
 	}
 
 	// draw cursor
 	UI_SetColor( NULL );
-	if (uis.glconfig.isFullscreen  ||  (int)trap_Cvar_VariableValue("in_nograb") == 0) {
-		UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
-	}
+	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
 
-#ifndef NQDEBUG
+#ifndef NDEBUG
 	if (uis.debug)
 	{
 		// cursor coordinates

```

### `openarena-engine`  — sha256 `624c35cf7801...`, 26711 bytes

_Diff stat: +17 / -75 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_atoms.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_atoms.c	2026-04-16 22:48:25.892200500 +0100
@@ -512,10 +512,6 @@
 	int		width;
 	float	sizeScale;
 
-	if( !str ) {
-		return;
-	}
-
 	sizeScale = UI_ProportionalSizeScale( style );
 
 	switch( style & UI_FORMATMASK ) {
@@ -807,7 +803,7 @@
 
 void UI_SetActiveMenu( uiMenuCommand_t menu ) {
 	// this should be the ONLY way the menu system is brought up
-	// ensure minimum menu data is cached
+	// enusure minumum menu data is cached
 	Menu_Cache();
 
 	switch ( menu ) {
@@ -836,7 +832,7 @@
 	case UIMENU_TEAM:
 	case UIMENU_POSTGAME:
 	default:
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 	  Com_Printf("UI_SetActiveMenu: bad enum %d\n", menu );
 #endif
 	  break;
@@ -852,45 +848,6 @@
 	sfxHandle_t		s;
 
 	if (!uis.activemenu) {
-		char buf[MAX_STRING_CHARS];
-
-		if (!down) {
-			return;
-		}
-
-		// menu is NULL but we could be playing cinematic
-		// check for binds to function keys
-
-		switch (key) {
-		case K_F1:
-		case K_F2:
-		case K_F3:
-		case K_F4:
-		case K_F5:
-		case K_F6:
-		case K_F7:
-		case K_F8:
-		case K_F9:
-		case K_F10:
-		case K_F11:
-		case K_F12:
-		case K_F13:
-		case K_F14:
-		case K_F15:
-			// got a function key
-			break;
-		default:
-			// no function key
-			return;
-		}
-
-		buf[0] = '\0';
-		trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-		if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-			return;
-		}
-		trap_Cmd_ExecuteText(EXEC_NOW, buf);
-
 		return;
 	}
 
@@ -912,35 +869,26 @@
 UI_MouseEvent
 =================
 */
-void UI_MouseEvent( int dx, int dy, qboolean active )
+void UI_MouseEvent( int dx, int dy )
 {
 	int				i;
-	int				bias;
 	menucommon_s*	m;
 
 	if (!uis.activemenu)
 		return;
 
-	// convert X bias to 640 coords
-	bias = uis.bias / uis.xscale;
-
 	// update mouse screen position
-	if (active) {
-		uis.cursorx += dx;
-		if (uis.cursorx < -bias)
-			uis.cursorx = -bias;
-		else if (uis.cursorx > SCREEN_WIDTH+bias)
-			uis.cursorx = SCREEN_WIDTH+bias;
-
-		uis.cursory += dy;
-		if (uis.cursory < 0)
-			uis.cursory = 0;
-		else if (uis.cursory > SCREEN_HEIGHT)
-			uis.cursory = SCREEN_HEIGHT;
-	} else {
-		uis.cursorx = -bias + (dx * (float)((float)(SCREEN_WIDTH + 2 * bias) / (float)uis.glconfig.vidWidth));
-		uis.cursory = dy * (float)((float)SCREEN_HEIGHT / (float)uis.glconfig.vidHeight);
-	}
+	uis.cursorx += dx;
+	if (uis.cursorx < -uis.bias)
+		uis.cursorx = -uis.bias;
+	else if (uis.cursorx > SCREEN_WIDTH+uis.bias)
+		uis.cursorx = SCREEN_WIDTH+uis.bias;
+
+	uis.cursory += dy;
+	if (uis.cursory < 0)
+		uis.cursory = 0;
+	else if (uis.cursory > SCREEN_HEIGHT)
+		uis.cursory = SCREEN_HEIGHT;
 
 	// region test the active menu items
 	for (i=0; i<uis.activemenu->nitems; i++)
@@ -1112,8 +1060,6 @@
 =================
 */
 void UI_Init( void ) {
-	Com_Printf("UI_Init() version: %s\n", WOLFCAM_VERSION);
-
 	UI_RegisterCvars();
 
 	UI_InitGameinfo();
@@ -1254,8 +1200,6 @@
 
 	UI_UpdateCvars();
 
-	trap_R_BeginHud();
-
 	if ( uis.activemenu )
 	{
 		if (uis.activemenu->fullscreen)
@@ -1275,18 +1219,16 @@
 			Menu_Draw( uis.activemenu );
 
 		if( uis.firstdraw ) {
-			UI_MouseEvent( 0, 0, qtrue );
+			UI_MouseEvent( 0, 0 );
 			uis.firstdraw = qfalse;
 		}
 	}
 
 	// draw cursor
 	UI_SetColor( NULL );
-	if (uis.glconfig.isFullscreen  ||  (int)trap_Cvar_VariableValue("in_nograb") == 0) {
-		UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
-	}
+	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
 
-#ifndef NQDEBUG
+#ifndef NDEBUG
 	if (uis.debug)
 	{
 		// cursor coordinates

```

### `openarena-gamecode`  — sha256 `57723b52a49a...`, 27907 bytes

_Diff stat: +61 / -90 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_atoms.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_atoms.c	2026-04-16 22:48:24.178986800 +0100
@@ -38,7 +38,7 @@
 	Q_vsnprintf (text, sizeof(text), error, argptr);
 	va_end (argptr);
 
-	trap_Error( text );
+	trap_Error( va("%s", text) );
 }
 
 void QDECL Com_Printf( const char *msg, ... ) {
@@ -49,7 +49,7 @@
 	Q_vsnprintf (text, sizeof(text), msg, argptr);
 	va_end (argptr);
 
-	trap_Print( text );
+	trap_Print( va("%s", text) );
 }
 
 /*
@@ -330,6 +330,8 @@
 #define PROPB_SPACE_WIDTH	12
 #define PROPB_HEIGHT		36
 
+// bk001205 - code below duplicated in cgame/cg_drawtools.c
+// bk001205 - FIXME: does this belong in ui_shared.c?
 /*
 =================
 UI_DrawBannerString
@@ -338,7 +340,7 @@
 static void UI_DrawBannerString2( int x, int y, const char* str, vec4_t color )
 {
 	const char* s;
-	unsigned char	ch;
+	unsigned char	ch; // bk001204 - unsigned
 	float	ax;
 	float	ay;
 	float	aw;
@@ -448,10 +450,10 @@
 static void UI_DrawProportionalString2( int x, int y, const char* str, vec4_t color, float sizeScale, qhandle_t charset )
 {
 	const char* s;
-	unsigned char	ch;
+	unsigned char	ch; // bk001204 - unsigned
 	float	ax;
 	float	ay;
-	float	aw = 0;
+	float	aw = 0; // bk001204 - init
 	float	ah;
 	float	frow;
 	float	fcol;
@@ -512,10 +514,6 @@
 	int		width;
 	float	sizeScale;
 
-	if( !str ) {
-		return;
-	}
-
 	sizeScale = UI_ProportionalSizeScale( style );
 
 	switch( style & UI_FORMATMASK ) {
@@ -807,7 +805,7 @@
 
 void UI_SetActiveMenu( uiMenuCommand_t menu ) {
 	// this should be the ONLY way the menu system is brought up
-	// ensure minimum menu data is cached
+	// enusure minumum menu data is cached
 	Menu_Cache();
 
 	switch ( menu ) {
@@ -833,10 +831,11 @@
 		UI_InGameMenu();
 		return;
 		
+	// bk001204
 	case UIMENU_TEAM:
 	case UIMENU_POSTGAME:
 	default:
-#if 1  //ndef NQDEBUG
+#ifndef NDEBUG
 	  Com_Printf("UI_SetActiveMenu: bad enum %d\n", menu );
 #endif
 	  break;
@@ -852,45 +851,6 @@
 	sfxHandle_t		s;
 
 	if (!uis.activemenu) {
-		char buf[MAX_STRING_CHARS];
-
-		if (!down) {
-			return;
-		}
-
-		// menu is NULL but we could be playing cinematic
-		// check for binds to function keys
-
-		switch (key) {
-		case K_F1:
-		case K_F2:
-		case K_F3:
-		case K_F4:
-		case K_F5:
-		case K_F6:
-		case K_F7:
-		case K_F8:
-		case K_F9:
-		case K_F10:
-		case K_F11:
-		case K_F12:
-		case K_F13:
-		case K_F14:
-		case K_F15:
-			// got a function key
-			break;
-		default:
-			// no function key
-			return;
-		}
-
-		buf[0] = '\0';
-		trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-		if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-			return;
-		}
-		trap_Cmd_ExecuteText(EXEC_NOW, buf);
-
 		return;
 	}
 
@@ -912,35 +872,26 @@
 UI_MouseEvent
 =================
 */
-void UI_MouseEvent( int dx, int dy, qboolean active )
+void UI_MouseEvent( int dx, int dy )
 {
 	int				i;
-	int				bias;
 	menucommon_s*	m;
 
 	if (!uis.activemenu)
 		return;
 
-	// convert X bias to 640 coords
-	bias = uis.bias / uis.xscale;
-
 	// update mouse screen position
-	if (active) {
-		uis.cursorx += dx;
-		if (uis.cursorx < -bias)
-			uis.cursorx = -bias;
-		else if (uis.cursorx > SCREEN_WIDTH+bias)
-			uis.cursorx = SCREEN_WIDTH+bias;
-
-		uis.cursory += dy;
-		if (uis.cursory < 0)
-			uis.cursory = 0;
-		else if (uis.cursory > SCREEN_HEIGHT)
-			uis.cursory = SCREEN_HEIGHT;
-	} else {
-		uis.cursorx = -bias + (dx * (float)((float)(SCREEN_WIDTH + 2 * bias) / (float)uis.glconfig.vidWidth));
-		uis.cursory = dy * (float)((float)SCREEN_HEIGHT / (float)uis.glconfig.vidHeight);
-	}
+	uis.cursorx += dx;
+	if (uis.cursorx < -uis.bias)
+		uis.cursorx = -uis.bias;
+	else if (uis.cursorx > SCREEN_WIDTH+uis.bias)
+		uis.cursorx = SCREEN_WIDTH+uis.bias;
+
+	uis.cursory += dy;
+	if (uis.cursory < 0)
+		uis.cursory = 0;
+	else if (uis.cursory > SCREEN_HEIGHT)
+		uis.cursory = SCREEN_HEIGHT;
 
 	// region test the active menu items
 	for (i=0; i<uis.activemenu->nitems; i++)
@@ -1055,46 +1006,68 @@
 	// ensure minimum menu data is available
 	Menu_Cache();
 
-	if ( Q_stricmp (cmd, "levelselect") == 0 ) {
+	if ( Q_strequal(cmd, "levelselect") ) {
 		UI_SPLevelMenu_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "postgame") == 0 ) {
+	if ( Q_strequal(cmd, "postgame") ) {
 		UI_SPPostgameMenu_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_cache") == 0 ) {
+	if ( Q_strequal(cmd, "ui_cache") ) {
 		UI_Cache_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_cinematics") == 0 ) {
+	if ( Q_strequal(cmd, "ui_cinematics") ) {
 		UI_CinematicsMenu_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_teamOrders") == 0 ) {
+	if ( Q_strequal(cmd, "ui_teamOrders") ) {
 		UI_TeamOrdersMenu_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "iamacheater") == 0 ) {
+	if ( Q_strequal(cmd, "iamacheater") ) {
 		UI_SPUnlock_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "iamamonkey") == 0 ) {
+	if ( Q_strequal(cmd, "iamamonkey") ) {
 		UI_SPUnlockMedals_f();
 		return qtrue;
 	}
 
-	if ( Q_stricmp (cmd, "ui_cdkey") == 0 ) {
+	if ( Q_strequal(cmd, "ui_cdkey") ) {
 		UI_CDKeyMenu_f();
 		return qtrue;
 	}
 
+        if ( Q_strequal(cmd, "ui_mappage") ) {
+		mappage.pagenumber = atoi(UI_Argv( 1 ));
+                Q_strncpyz(mappage.mapname[0],UI_Argv(2),32);
+                Q_strncpyz(mappage.mapname[1],UI_Argv(3),32);
+                Q_strncpyz(mappage.mapname[2],UI_Argv(4),32);
+                Q_strncpyz(mappage.mapname[3],UI_Argv(5),32);
+                Q_strncpyz(mappage.mapname[4],UI_Argv(6),32);
+                Q_strncpyz(mappage.mapname[5],UI_Argv(7),32);
+                Q_strncpyz(mappage.mapname[6],UI_Argv(8),32);
+                Q_strncpyz(mappage.mapname[7],UI_Argv(9),32);
+                Q_strncpyz(mappage.mapname[8],UI_Argv(10),32);
+                Q_strncpyz(mappage.mapname[9],UI_Argv(11),32);
+
+                UI_VoteMapMenuInternal();
+		return qtrue;
+	}
+        
+        if ( Q_strequal(cmd, "ui_writemappools") ) {
+            WriteMapList();
+            return qtrue;
+        }
+
 	return qfalse;
 }
 
@@ -1112,8 +1085,6 @@
 =================
 */
 void UI_Init( void ) {
-	Com_Printf("UI_Init() version: %s\n", WOLFCAM_VERSION);
-
 	UI_RegisterCvars();
 
 	UI_InitGameinfo();
@@ -1194,6 +1165,10 @@
 	trap_R_DrawStretchPic( x, y, w, h, s0, t0, s1, t1, hShader );
 }
 
+void UI_DrawBackgroundPic( qhandle_t hShader ) {
+	trap_R_DrawStretchPic( 0.0, 0.0, uis.glconfig.vidWidth, uis.glconfig.vidHeight, 0, 0, 1, 1, hShader );
+}
+
 /*
 ================
 UI_FillRect
@@ -1254,18 +1229,16 @@
 
 	UI_UpdateCvars();
 
-	trap_R_BeginHud();
-
 	if ( uis.activemenu )
 	{
 		if (uis.activemenu->fullscreen)
 		{
 			// draw the background
 			if( uis.activemenu->showlogo ) {
-				UI_DrawHandlePic( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, uis.menuBackShader );
+				UI_DrawBackgroundPic( uis.menuBackShader );
 			}
 			else {
-				UI_DrawHandlePic( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, uis.menuBackNoLogoShader );
+				UI_DrawBackgroundPic( uis.menuBackNoLogoShader );
 			}
 		}
 
@@ -1275,18 +1248,16 @@
 			Menu_Draw( uis.activemenu );
 
 		if( uis.firstdraw ) {
-			UI_MouseEvent( 0, 0, qtrue );
+			UI_MouseEvent( 0, 0 );
 			uis.firstdraw = qfalse;
 		}
 	}
 
 	// draw cursor
 	UI_SetColor( NULL );
-	if (uis.glconfig.isFullscreen  ||  (int)trap_Cvar_VariableValue("in_nograb") == 0) {
-		UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
-	}
+	UI_DrawHandlePic( uis.cursorx-16, uis.cursory-16, 32, 32, uis.cursor);
 
-#ifndef NQDEBUG
+#ifndef NDEBUG
 	if (uis.debug)
 	{
 		// cursor coordinates

```
