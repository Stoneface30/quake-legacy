# Diff: `code/client/cl_scrn.c`
**Canonical:** `wolfcamql-src` (sha256 `da860c488c71...`, 16501 bytes)

## Variants

### `quake3-source`  — sha256 `01cf0a288921...`, 12263 bytes

_Diff stat: +77 / -201 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_scrn.c	2026-04-16 20:02:25.173221100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\cl_scrn.c	2026-04-16 20:02:19.892591600 +0100
@@ -15,16 +15,15 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // cl_scrn.c -- master for refresh, status bar, console, chat, notify, etc
 
 #include "client.h"
-#include <time.h>
 
-static qboolean	scr_initialized;		// ready to draw
+qboolean	scr_initialized;		// ready to draw
 
 cvar_t		*cl_timegraph;
 cvar_t		*cl_debuggraph;
@@ -120,8 +119,7 @@
 ** SCR_DrawChar
 ** chars are drawn at 640*480 virtual screen size
 */
-static void SCR_DrawChar (int x, int y, float size, int ch)
-{
+static void SCR_DrawChar( int x, int y, float size, int ch ) {
 	int row, col;
 	float frow, fcol;
 	float	ax, ay, aw, ah;
@@ -155,48 +153,36 @@
 					   cls.charSetShader );
 }
 
-//FIXME ioquake3 uses g_smallchar_* with this function, the only places this
-// is used (almost everything else uses SCR_DrawSmallCharExt() which scales) is
-// drawing the version number in console and quake live workshop downloads.
-// For workshop downloads not sure what to use so keeping this as is for now.
-
 /*
 ** SCR_DrawSmallChar
 ** small chars are drawn at native screen resolution
 */
 void SCR_DrawSmallChar( int x, int y, int ch ) {
-	glyphInfo_t glyph;
+	int row, col;
+	float frow, fcol;
+	float size;
 
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
+	ch &= 255;
 
-	if ( y < -SMALLCHAR_HEIGHT ) {
+	if ( ch == ' ' ) {
 		return;
 	}
 
-	re.DrawStretchPic(x, y - glyph.top, SMALLCHAR_WIDTH, /* SMALLCHAR_HEIGHT */ glyph.height < SMALLCHAR_HEIGHT ? glyph.height : SMALLCHAR_HEIGHT,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
-}
-
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch ) {
-	glyphInfo_t glyph;
-	float scale;
-
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
-
-	if ( y < -height ) {
+	if ( y < -SMALLCHAR_HEIGHT ) {
 		return;
 	}
 
-	scale = height / SMALLCHAR_HEIGHT;
+	row = ch>>4;
+	col = ch&15;
 
-	// 2018-11-12 checking fo glyph.height since super and subscripts will be smaller (ex:  trademark symbol)
+	frow = row*0.0625;
+	fcol = col*0.0625;
+	size = 0.0625;
 
-	re.DrawStretchPic(x, y - glyph.top, width,  /* height */  (glyph.height * scale) < height ? (glyph.height * scale) : height ,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
+	re.DrawStretchPic( x, y, SMALLCHAR_WIDTH, SMALLCHAR_HEIGHT,
+					   fcol, frow, 
+					   fcol + size, frow + size, 
+					   cls.charSetShader );
 }
 
 
@@ -210,14 +196,11 @@
 Coordinates are at 640 by 480 virtual resolution
 ==================
 */
-void SCR_DrawStringExt( int x, int y, float size, const char *string, float *setColor, qboolean forceColor,
-		qboolean noColorEscape ) {
+void SCR_DrawStringExt( int x, int y, float size, const char *string, float *setColor, qboolean forceColor ) {
 	vec4_t		color;
 	const char	*s;
 	int			xx;
 
-	//printf("SCR_DrawStringExt: '%s'\n", string);
-
 	// draw the drop shadow
 	color[0] = color[1] = color[2] = 0;
 	color[3] = setColor[3];
@@ -225,7 +208,7 @@
 	s = string;
 	xx = x;
 	while ( *s ) {
-		if ( !noColorEscape && Q_IsColorString( s ) ) {
+		if ( Q_IsColorString( s ) ) {
 			s += 2;
 			continue;
 		}
@@ -246,10 +229,8 @@
 				color[3] = setColor[3];
 				re.SetColor( color );
 			}
-			if ( !noColorEscape ) {
-				s += 2;
-				continue;
-			}
+			s += 2;
+			continue;
 		}
 		SCR_DrawChar( xx, y, size, *s );
 		xx += size;
@@ -259,16 +240,16 @@
 }
 
 
-void SCR_DrawBigString( int x, int y, const char *s, float alpha, qboolean noColorEscape ) {
+void SCR_DrawBigString( int x, int y, const char *s, float alpha ) {
 	float	color[4];
 
 	color[0] = color[1] = color[2] = 1.0;
 	color[3] = alpha;
-	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qfalse, noColorEscape );
+	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qfalse );
 }
 
-void SCR_DrawBigStringColor( int x, int y, const char *s, vec4_t color, qboolean noColorEscape ) {
-	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qtrue, noColorEscape );
+void SCR_DrawBigStringColor( int x, int y, const char *s, vec4_t color ) {
+	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qtrue );
 }
 
 
@@ -278,40 +259,31 @@
 
 Draws a multi-colored string with a drop shadow, optionally forcing
 to a fixed color.
+
+Coordinates are at 640 by 480 virtual resolution
 ==================
 */
-void SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor,
-		qboolean noColorEscape ) {
+void SCR_DrawSmallStringExt( int x, int y, const char *string, float *setColor, qboolean forceColor ) {
 	vec4_t		color;
 	const char	*s;
-	float			xx;
-	//glyphInfo_t glyph;
+	int			xx;
 
 	// draw the colored text
 	s = string;
 	xx = x;
 	re.SetColor( setColor );
 	while ( *s ) {
-		int codePoint;
-		int numUtf8Bytes;
-		qboolean error;
-
 		if ( Q_IsColorString( s ) ) {
 			if ( !forceColor ) {
 				Com_Memcpy( color, g_color_table[ColorIndex(*(s+1))], sizeof( color ) );
 				color[3] = setColor[3];
 				re.SetColor( color );
 			}
-			if ( !noColorEscape ) {
-				s += 2;
-				continue;
-			}
+			s += 2;
+			continue;
 		}
-		codePoint = Q_GetCpFromUtf8(s, &numUtf8Bytes, &error);
-		s += (numUtf8Bytes - 1);
-		//SCR_DrawSmallCharExt( xx, y, cwidth, cheight, *s );
-		SCR_DrawSmallCharExt(xx, y, cwidth, cheight, codePoint);
-		xx += cwidth;  //SMALLCHAR_WIDTH;
+		SCR_DrawSmallChar( xx, y, *s );
+		xx += SMALLCHAR_WIDTH;
 		s++;
 	}
 	re.SetColor( NULL );
@@ -319,7 +291,6 @@
 
 
 
-
 /*
 ** SCR_Strlen -- skips color escape codes
 */
@@ -343,7 +314,7 @@
 ** SCR_GetBigStringWidth
 */ 
 int	SCR_GetBigStringWidth( const char *str ) {
-	return SCR_Strlen( str ) * BIGCHAR_WIDTH;
+	return SCR_Strlen( str ) * 16;
 }
 
 
@@ -365,98 +336,13 @@
 		return;
 	}
 
-	pos = FS_FTell( clc.demoWriteFile );
+	pos = FS_FTell( clc.demofile );
 	sprintf( string, "RECORDING %s: %ik", clc.demoName, pos / 1024 );
 
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 20, 8, string, g_color_table[7], qtrue, qfalse );
+	SCR_DrawStringExt( 320 - strlen( string ) * 4, 20, 8, string, g_color_table[7], qtrue );
 }
 
 
-#ifdef USE_VOIP
-/*
-=================
-SCR_DrawVoipMeter
-=================
-*/
-static void SCR_DrawVoipMeter( void ) {
-	char	buffer[16];
-	char	string[256];
-	int limit, i;
-
-	if (!cl_voipShowMeter->integer)
-		return;  // player doesn't want to show meter at all.
-	else if (!cl_voipSend->integer)
-		return;  // not recording at the moment.
-	else if (clc.state != CA_ACTIVE)
-		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
-		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
-		return;  // playing back a demo.
-	else if (!cl_voip->integer)
-		return;  // client has VoIP support disabled.
-
-	limit = (int) (clc.voipPower * 10.0f);
-	if (limit > 10)
-		limit = 10;
-
-	for (i = 0; i < limit; i++)
-		buffer[i] = '*';
-	while (i < 10)
-		buffer[i++] = ' ';
-	buffer[i] = '\0';
-
-	sprintf( string, "VoIP: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 10, 8, string, g_color_table[7], qtrue, qfalse );
-}
-#endif
-
-/*
-=================
-SCR_DrawVolumeMeter
-=================
-*/
-static void SCR_DrawVolumeMeter( void ) {
-	char	buffer[16];
-	char	string[256];
-	int limit, i;
-
-	if (!cl_volumeShowMeter->integer)
-		return;  // player doesn't want to show meter at all.
-
-#if 0
-	else if (!cl_voipSend->integer)
-		return;  // not recording at the moment.
-	else if (clc.state != CA_ACTIVE)
-		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
-		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
-		return;  // playing back a demo.
-	else if (!cl_voip->integer)
-		return;  // client has VoIP support disabled.
-#endif
-
-	limit = (int) (clc.audioPower * 10.0f);
-	if (limit > 10)
-		limit = 10;
-
-	for (i = 0; i < limit; i++)
-		buffer[i] = '*';
-	while (i < 10)
-		buffer[i++] = ' ';
-	buffer[i] = '\0';
-
-	sprintf( string, "Volume: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 200, 8, string, g_color_table[7], qtrue, qfalse );
-
-	sprintf(string, "%f dB", clc.audioDecibels);
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 220, 8, string, g_color_table[7], qtrue, qfalse );
-}
-
-
-
-
 /*
 ===============================================================================
 
@@ -465,18 +351,25 @@
 ===============================================================================
 */
 
+typedef struct
+{
+	float	value;
+	int		color;
+} graphsamp_t;
+
 static	int			current;
-static	float		values[1024];
+static	graphsamp_t	values[1024];
 
 /*
 ==============
 SCR_DebugGraph
 ==============
 */
-void SCR_DebugGraph (float value)
+void SCR_DebugGraph (float value, int color)
 {
-	values[current] = value;
-	current = (current + 1) % ARRAY_LEN(values);
+	values[current&1023].value = value;
+	values[current&1023].color = color;
+	current++;
 }
 
 /*
@@ -488,6 +381,7 @@
 {
 	int		a, x, y, w, i, h;
 	float	v;
+	int		color;
 
 	//
 	// draw the graph
@@ -496,16 +390,17 @@
 	x = 0;
 	y = cls.glconfig.vidHeight;
 	re.SetColor( g_color_table[0] );
-	re.DrawStretchPic(x, y - cl_graphheight->integer,
+	re.DrawStretchPic(x, y - cl_graphheight->integer, 
 		w, cl_graphheight->integer, 0, 0, 0, 0, cls.whiteShader );
 	re.SetColor( NULL );
 
 	for (a=0 ; a<w ; a++)
 	{
-		i = (ARRAY_LEN(values)+current-1-(a % ARRAY_LEN(values))) % ARRAY_LEN(values);
-		v = values[i];
+		i = (current-1-a+1024) & 1023;
+		v = values[i].value;
+		color = values[i].color;
 		v = v * cl_graphscale->integer + cl_graphshift->integer;
-
+		
 		if (v < 0)
 			v += cl_graphheight->integer * (1+(int)(-v / cl_graphheight->integer));
 		h = (int)v % cl_graphheight->integer;
@@ -520,7 +415,6 @@
 SCR_Init
 ==================
 */
-
 void SCR_Init( void ) {
 	cl_timegraph = Cvar_Get ("timegraph", "0", CVAR_CHEAT);
 	cl_debuggraph = Cvar_Get ("debuggraph", "0", CVAR_CHEAT);
@@ -542,15 +436,11 @@
 ==================
 */
 void SCR_DrawScreenField( stereoFrame_t stereoFrame ) {
-	qboolean uiFullscreen;
-
-	re.BeginFrame(stereoFrame, CL_VideoRecording(&afdMain));
-
-	uiFullscreen = (uivm && VM_Call( uivm, UI_IS_FULLSCREEN ));
+	re.BeginFrame( stereoFrame );
 
 	// wide aspect ratio screens need to have the sides cleared
 	// unless they are displaying game renderings
-	if ( uiFullscreen || clc.state < CA_LOADING ) {
+	if ( cls.state != CA_ACTIVE ) {
 		if ( cls.glconfig.vidWidth * 480 > cls.glconfig.vidHeight * 640 ) {
 			re.SetColor( g_color_table[0] );
 			re.DrawStretchPic( 0, 0, cls.glconfig.vidWidth, cls.glconfig.vidHeight, 0, 0, 0, 0, cls.whiteShader );
@@ -558,12 +448,17 @@
 		}
 	}
 
+	if ( !uivm ) {
+		Com_DPrintf("draw screen without UI loaded\n");
+		return;
+	}
+
 	// if the menu is going to cover the entire screen, we
 	// don't need to render anything under it
-	if ( uivm && !uiFullscreen ) {
-		switch( clc.state ) {
+	if ( !VM_Call( uivm, UI_IS_FULLSCREEN )) {
+		switch( cls.state ) {
 		default:
-			Com_Error( ERR_FATAL, "SCR_DrawScreenField: bad clc.state" );
+			Com_Error( ERR_FATAL, "SCR_DrawScreenField: bad cls.state" );
 			break;
 		case CA_CINEMATIC:
 			SCR_DrawCinematic();
@@ -573,7 +468,6 @@
 			S_StopAllSounds();
 			VM_Call( uivm, UI_SET_ACTIVE_MENU, UIMENU_MAIN );
 			break;
-		case CA_DOWNLOADINGWORKSHOPS:
 		case CA_CONNECTING:
 		case CA_CHALLENGING:
 		case CA_CONNECTED:
@@ -585,7 +479,7 @@
 		case CA_LOADING:
 		case CA_PRIMED:
 			// draw the game information screen and loading progress
-			CL_CGameRendering(stereoFrame);
+			CL_CGameRendering( stereoFrame );
 
 			// also draw the connection information, so it doesn't
 			// flash away too briefly on local or lan games
@@ -594,19 +488,14 @@
 			VM_Call( uivm, UI_DRAW_CONNECT_SCREEN, qtrue );
 			break;
 		case CA_ACTIVE:
-			// always supply STEREO_CENTER as vieworg offset is now done by the engine.
-			CL_CGameRendering(stereoFrame);
+			CL_CGameRendering( stereoFrame );
 			SCR_DrawDemoRecording();
-#ifdef USE_VOIP
-			SCR_DrawVoipMeter();
-#endif
-			SCR_DrawVolumeMeter();
 			break;
 		}
 	}
 
 	// the menu draws next
-	if ( Key_GetCatcher( ) & KEYCATCH_UI && uivm ) {
+	if ( cls.keyCatchers & KEYCATCH_UI && uivm ) {
 		VM_Call( uivm, UI_REFRESH, cls.realtime );
 	}
 
@@ -639,31 +528,18 @@
 	}
 	recursive = 1;
 
-	// If there is no VM, there are also no rendering commands issued. Stop the renderer in
-	// that case.
-	if( uivm || com_dedicated->integer )
-	{
-		int in_anaglyphMode = Cvar_VariableIntegerValue("r_anaglyphMode");
-
-		// if running in stereo, we need to draw the frame twice
-		if ( cls.glconfig.stereoEnabled || in_anaglyphMode) {
-			SCR_DrawScreenField( STEREO_LEFT );
-			SCR_DrawScreenField( STEREO_RIGHT );
-		} else {
-			//Com_Printf("1:  %d\n", (int)time(NULL));
-			//Com_Printf("1:  %d\n", Sys_Milliseconds());
-			SCR_DrawScreenField( STEREO_CENTER );
-		}
+	// if running in stereo, we need to draw the frame twice
+	if ( cls.glconfig.stereoEnabled ) {
+		SCR_DrawScreenField( STEREO_LEFT );
+		SCR_DrawScreenField( STEREO_RIGHT );
+	} else {
+		SCR_DrawScreenField( STEREO_CENTER );
+	}
 
-		if ( com_speeds->integer ) {
-			re.EndFrame( &time_frontend, &time_backend );
-		} else {
-			re.EndFrame( NULL, NULL );
-		}
-		//Com_Printf("2:  %d\n", (int)time(NULL));
-		//Com_Printf("2:  %d\n", Sys_Milliseconds());
+	if ( com_speeds->integer ) {
+		re.EndFrame( &time_frontend, &time_backend );
 	} else {
-		//
+		re.EndFrame( NULL, NULL );
 	}
 
 	recursive = 0;

```

### `ioquake3`  — sha256 `5eef13ec5094...`, 13771 bytes

_Diff stat: +30 / -107 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_scrn.c	2026-04-16 20:02:25.173221100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\cl_scrn.c	2026-04-16 20:02:21.529570100 +0100
@@ -22,9 +22,8 @@
 // cl_scrn.c -- master for refresh, status bar, console, chat, notify, etc
 
 #include "client.h"
-#include <time.h>
 
-static qboolean	scr_initialized;		// ready to draw
+qboolean	scr_initialized;		// ready to draw
 
 cvar_t		*cl_timegraph;
 cvar_t		*cl_debuggraph;
@@ -120,8 +119,7 @@
 ** SCR_DrawChar
 ** chars are drawn at 640*480 virtual screen size
 */
-static void SCR_DrawChar (int x, int y, float size, int ch)
-{
+static void SCR_DrawChar( int x, int y, float size, int ch ) {
 	int row, col;
 	float frow, fcol;
 	float	ax, ay, aw, ah;
@@ -155,48 +153,36 @@
 					   cls.charSetShader );
 }
 
-//FIXME ioquake3 uses g_smallchar_* with this function, the only places this
-// is used (almost everything else uses SCR_DrawSmallCharExt() which scales) is
-// drawing the version number in console and quake live workshop downloads.
-// For workshop downloads not sure what to use so keeping this as is for now.
-
 /*
 ** SCR_DrawSmallChar
 ** small chars are drawn at native screen resolution
 */
 void SCR_DrawSmallChar( int x, int y, int ch ) {
-	glyphInfo_t glyph;
+	int row, col;
+	float frow, fcol;
+	float size;
 
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
+	ch &= 255;
 
-	if ( y < -SMALLCHAR_HEIGHT ) {
+	if ( ch == ' ' ) {
 		return;
 	}
 
-	re.DrawStretchPic(x, y - glyph.top, SMALLCHAR_WIDTH, /* SMALLCHAR_HEIGHT */ glyph.height < SMALLCHAR_HEIGHT ? glyph.height : SMALLCHAR_HEIGHT,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
-}
-
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch ) {
-	glyphInfo_t glyph;
-	float scale;
-
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
-
-	if ( y < -height ) {
+	if ( y < -g_smallchar_height ) {
 		return;
 	}
 
-	scale = height / SMALLCHAR_HEIGHT;
+	row = ch>>4;
+	col = ch&15;
 
-	// 2018-11-12 checking fo glyph.height since super and subscripts will be smaller (ex:  trademark symbol)
+	frow = row*0.0625;
+	fcol = col*0.0625;
+	size = 0.0625;
 
-	re.DrawStretchPic(x, y - glyph.top, width,  /* height */  (glyph.height * scale) < height ? (glyph.height * scale) : height ,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
+	re.DrawStretchPic( x, y, g_smallchar_width, g_smallchar_height,
+					   fcol, frow, 
+					   fcol + size, frow + size, 
+					   cls.charSetShader );
 }
 
 
@@ -216,8 +202,6 @@
 	const char	*s;
 	int			xx;
 
-	//printf("SCR_DrawStringExt: '%s'\n", string);
-
 	// draw the drop shadow
 	color[0] = color[1] = color[2] = 0;
 	color[3] = setColor[3];
@@ -280,22 +264,17 @@
 to a fixed color.
 ==================
 */
-void SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor,
+void SCR_DrawSmallStringExt( int x, int y, const char *string, float *setColor, qboolean forceColor,
 		qboolean noColorEscape ) {
 	vec4_t		color;
 	const char	*s;
-	float			xx;
-	//glyphInfo_t glyph;
+	int			xx;
 
 	// draw the colored text
 	s = string;
 	xx = x;
 	re.SetColor( setColor );
 	while ( *s ) {
-		int codePoint;
-		int numUtf8Bytes;
-		qboolean error;
-
 		if ( Q_IsColorString( s ) ) {
 			if ( !forceColor ) {
 				Com_Memcpy( color, g_color_table[ColorIndex(*(s+1))], sizeof( color ) );
@@ -307,11 +286,8 @@
 				continue;
 			}
 		}
-		codePoint = Q_GetCpFromUtf8(s, &numUtf8Bytes, &error);
-		s += (numUtf8Bytes - 1);
-		//SCR_DrawSmallCharExt( xx, y, cwidth, cheight, *s );
-		SCR_DrawSmallCharExt(xx, y, cwidth, cheight, codePoint);
-		xx += cwidth;  //SMALLCHAR_WIDTH;
+		SCR_DrawSmallChar( xx, y, *s );
+		xx += g_smallchar_width;
 		s++;
 	}
 	re.SetColor( NULL );
@@ -319,7 +295,6 @@
 
 
 
-
 /*
 ** SCR_Strlen -- skips color escape codes
 */
@@ -365,7 +340,7 @@
 		return;
 	}
 
-	pos = FS_FTell( clc.demoWriteFile );
+	pos = FS_FTell( clc.demofile );
 	sprintf( string, "RECORDING %s: %ik", clc.demoName, pos / 1024 );
 
 	SCR_DrawStringExt( 320 - strlen( string ) * 4, 20, 8, string, g_color_table[7], qtrue, qfalse );
@@ -378,7 +353,7 @@
 SCR_DrawVoipMeter
 =================
 */
-static void SCR_DrawVoipMeter( void ) {
+void SCR_DrawVoipMeter( void ) {
 	char	buffer[16];
 	char	string[256];
 	int limit, i;
@@ -389,9 +364,9 @@
 		return;  // not recording at the moment.
 	else if (clc.state != CA_ACTIVE)
 		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
+	else if (!clc.voipEnabled)
 		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
+	else if (clc.demoplaying)
 		return;  // playing back a demo.
 	else if (!cl_voip->integer)
 		return;  // client has VoIP support disabled.
@@ -411,49 +386,6 @@
 }
 #endif
 
-/*
-=================
-SCR_DrawVolumeMeter
-=================
-*/
-static void SCR_DrawVolumeMeter( void ) {
-	char	buffer[16];
-	char	string[256];
-	int limit, i;
-
-	if (!cl_volumeShowMeter->integer)
-		return;  // player doesn't want to show meter at all.
-
-#if 0
-	else if (!cl_voipSend->integer)
-		return;  // not recording at the moment.
-	else if (clc.state != CA_ACTIVE)
-		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
-		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
-		return;  // playing back a demo.
-	else if (!cl_voip->integer)
-		return;  // client has VoIP support disabled.
-#endif
-
-	limit = (int) (clc.audioPower * 10.0f);
-	if (limit > 10)
-		limit = 10;
-
-	for (i = 0; i < limit; i++)
-		buffer[i] = '*';
-	while (i < 10)
-		buffer[i++] = ' ';
-	buffer[i] = '\0';
-
-	sprintf( string, "Volume: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 200, 8, string, g_color_table[7], qtrue, qfalse );
-
-	sprintf(string, "%f dB", clc.audioDecibels);
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 220, 8, string, g_color_table[7], qtrue, qfalse );
-}
-
 
 
 
@@ -496,7 +428,7 @@
 	x = 0;
 	y = cls.glconfig.vidHeight;
 	re.SetColor( g_color_table[0] );
-	re.DrawStretchPic(x, y - cl_graphheight->integer,
+	re.DrawStretchPic(x, y - cl_graphheight->integer, 
 		w, cl_graphheight->integer, 0, 0, 0, 0, cls.whiteShader );
 	re.SetColor( NULL );
 
@@ -505,7 +437,7 @@
 		i = (ARRAY_LEN(values)+current-1-(a % ARRAY_LEN(values))) % ARRAY_LEN(values);
 		v = values[i];
 		v = v * cl_graphscale->integer + cl_graphshift->integer;
-
+		
 		if (v < 0)
 			v += cl_graphheight->integer * (1+(int)(-v / cl_graphheight->integer));
 		h = (int)v % cl_graphheight->integer;
@@ -520,7 +452,6 @@
 SCR_Init
 ==================
 */
-
 void SCR_Init( void ) {
 	cl_timegraph = Cvar_Get ("timegraph", "0", CVAR_CHEAT);
 	cl_debuggraph = Cvar_Get ("debuggraph", "0", CVAR_CHEAT);
@@ -544,7 +475,7 @@
 void SCR_DrawScreenField( stereoFrame_t stereoFrame ) {
 	qboolean uiFullscreen;
 
-	re.BeginFrame(stereoFrame, CL_VideoRecording(&afdMain));
+	re.BeginFrame( stereoFrame );
 
 	uiFullscreen = (uivm && VM_Call( uivm, UI_IS_FULLSCREEN ));
 
@@ -573,7 +504,6 @@
 			S_StopAllSounds();
 			VM_Call( uivm, UI_SET_ACTIVE_MENU, UIMENU_MAIN );
 			break;
-		case CA_DOWNLOADINGWORKSHOPS:
 		case CA_CONNECTING:
 		case CA_CHALLENGING:
 		case CA_CONNECTED:
@@ -600,7 +530,6 @@
 #ifdef USE_VOIP
 			SCR_DrawVoipMeter();
 #endif
-			SCR_DrawVolumeMeter();
 			break;
 		}
 	}
@@ -643,15 +572,13 @@
 	// that case.
 	if( uivm || com_dedicated->integer )
 	{
+		// XXX
 		int in_anaglyphMode = Cvar_VariableIntegerValue("r_anaglyphMode");
-
 		// if running in stereo, we need to draw the frame twice
 		if ( cls.glconfig.stereoEnabled || in_anaglyphMode) {
 			SCR_DrawScreenField( STEREO_LEFT );
 			SCR_DrawScreenField( STEREO_RIGHT );
 		} else {
-			//Com_Printf("1:  %d\n", (int)time(NULL));
-			//Com_Printf("1:  %d\n", Sys_Milliseconds());
 			SCR_DrawScreenField( STEREO_CENTER );
 		}
 
@@ -660,12 +587,8 @@
 		} else {
 			re.EndFrame( NULL, NULL );
 		}
-		//Com_Printf("2:  %d\n", (int)time(NULL));
-		//Com_Printf("2:  %d\n", Sys_Milliseconds());
-	} else {
-		//
 	}
-
+	
 	recursive = 0;
 }
 

```

### `quake3e`  — sha256 `84cf81f65456...`, 15440 bytes

_Diff stat: +133 / -146 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_scrn.c	2026-04-16 20:02:25.173221100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\cl_scrn.c	2026-04-16 20:02:26.914504200 +0100
@@ -22,15 +22,14 @@
 // cl_scrn.c -- master for refresh, status bar, console, chat, notify, etc
 
 #include "client.h"
-#include <time.h>
 
 static qboolean	scr_initialized;		// ready to draw
 
 cvar_t		*cl_timegraph;
-cvar_t		*cl_debuggraph;
-cvar_t		*cl_graphheight;
-cvar_t		*cl_graphscale;
-cvar_t		*cl_graphshift;
+static cvar_t		*cl_debuggraph;
+static cvar_t		*cl_graphheight;
+static cvar_t		*cl_graphscale;
+static cvar_t		*cl_graphshift;
 
 /*
 ================
@@ -115,13 +114,11 @@
 }
 
 
-
 /*
 ** SCR_DrawChar
 ** chars are drawn at 640*480 virtual screen size
 */
-static void SCR_DrawChar (int x, int y, float size, int ch)
-{
+static void SCR_DrawChar( int x, int y, float size, int ch ) {
 	int row, col;
 	float frow, fcol;
 	float	ax, ay, aw, ah;
@@ -155,48 +152,69 @@
 					   cls.charSetShader );
 }
 
-//FIXME ioquake3 uses g_smallchar_* with this function, the only places this
-// is used (almost everything else uses SCR_DrawSmallCharExt() which scales) is
-// drawing the version number in console and quake live workshop downloads.
-// For workshop downloads not sure what to use so keeping this as is for now.
 
 /*
 ** SCR_DrawSmallChar
 ** small chars are drawn at native screen resolution
 */
 void SCR_DrawSmallChar( int x, int y, int ch ) {
-	glyphInfo_t glyph;
+	int row, col;
+	float frow, fcol;
+	float size;
+
+	ch &= 255;
 
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
+	if ( ch == ' ' ) {
+		return;
+	}
 
-	if ( y < -SMALLCHAR_HEIGHT ) {
+	if ( y < -smallchar_height ) {
 		return;
 	}
 
-	re.DrawStretchPic(x, y - glyph.top, SMALLCHAR_WIDTH, /* SMALLCHAR_HEIGHT */ glyph.height < SMALLCHAR_HEIGHT ? glyph.height : SMALLCHAR_HEIGHT,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
+	row = ch>>4;
+	col = ch&15;
+
+	frow = row*0.0625;
+	fcol = col*0.0625;
+	size = 0.0625;
+
+	re.DrawStretchPic( x, y, smallchar_width, smallchar_height,
+					   fcol, frow, 
+					   fcol + size, frow + size, 
+					   cls.charSetShader );
 }
 
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch ) {
-	glyphInfo_t glyph;
-	float scale;
 
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
+/*
+** SCR_DrawSmallString
+** small string are drawn at native screen resolution
+*/
+void SCR_DrawSmallString( int x, int y, const char *s, int len ) {
+	int row, col, ch, i;
+	float frow, fcol;
+	float size;
 
-	if ( y < -height ) {
+	if ( y < -smallchar_height ) {
 		return;
 	}
 
-	scale = height / SMALLCHAR_HEIGHT;
+	size = 0.0625;
 
-	// 2018-11-12 checking fo glyph.height since super and subscripts will be smaller (ex:  trademark symbol)
+	for ( i = 0; i < len; i++ ) {
+		ch = *s++ & 255;
+		row = ch>>4;
+		col = ch&15;
+
+		frow = row*0.0625;
+		fcol = col*0.0625;
+
+		re.DrawStretchPic( x, y, smallchar_width, smallchar_height,
+						   fcol, frow, fcol + size, frow + size, 
+						   cls.charSetShader );
 
-	re.DrawStretchPic(x, y - glyph.top, width,  /* height */  (glyph.height * scale) < height ? (glyph.height * scale) : height ,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
+		x += smallchar_width;
+	}
 }
 
 
@@ -210,16 +228,14 @@
 Coordinates are at 640 by 480 virtual resolution
 ==================
 */
-void SCR_DrawStringExt( int x, int y, float size, const char *string, float *setColor, qboolean forceColor,
+void SCR_DrawStringExt( int x, int y, float size, const char *string, const float *setColor, qboolean forceColor,
 		qboolean noColorEscape ) {
 	vec4_t		color;
 	const char	*s;
 	int			xx;
 
-	//printf("SCR_DrawStringExt: '%s'\n", string);
-
 	// draw the drop shadow
-	color[0] = color[1] = color[2] = 0;
+	color[0] = color[1] = color[2] = 0.0;
 	color[3] = setColor[3];
 	re.SetColor( color );
 	s = string;
@@ -242,7 +258,7 @@
 	while ( *s ) {
 		if ( Q_IsColorString( s ) ) {
 			if ( !forceColor ) {
-				Com_Memcpy( color, g_color_table[ColorIndex(*(s+1))], sizeof( color ) );
+				Com_Memcpy( color, g_color_table[ ColorIndexFromChar( *(s+1) ) ], sizeof( color ) );
 				color[3] = setColor[3];
 				re.SetColor( color );
 			}
@@ -259,6 +275,11 @@
 }
 
 
+/*
+==================
+SCR_DrawBigString
+==================
+*/
 void SCR_DrawBigString( int x, int y, const char *s, float alpha, qboolean noColorEscape ) {
 	float	color[4];
 
@@ -267,10 +288,6 @@
 	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qfalse, noColorEscape );
 }
 
-void SCR_DrawBigStringColor( int x, int y, const char *s, vec4_t color, qboolean noColorEscape ) {
-	SCR_DrawStringExt( x, y, BIGCHAR_WIDTH, s, color, qtrue, noColorEscape );
-}
-
 
 /*
 ==================
@@ -280,25 +297,20 @@
 to a fixed color.
 ==================
 */
-void SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor,
+void SCR_DrawSmallStringExt( int x, int y, const char *string, const float *setColor, qboolean forceColor,
 		qboolean noColorEscape ) {
 	vec4_t		color;
 	const char	*s;
-	float			xx;
-	//glyphInfo_t glyph;
+	int			xx;
 
 	// draw the colored text
 	s = string;
 	xx = x;
 	re.SetColor( setColor );
 	while ( *s ) {
-		int codePoint;
-		int numUtf8Bytes;
-		qboolean error;
-
 		if ( Q_IsColorString( s ) ) {
 			if ( !forceColor ) {
-				Com_Memcpy( color, g_color_table[ColorIndex(*(s+1))], sizeof( color ) );
+				Com_Memcpy( color, g_color_table[ ColorIndexFromChar( *(s+1) ) ], sizeof( color ) );
 				color[3] = setColor[3];
 				re.SetColor( color );
 			}
@@ -307,19 +319,14 @@
 				continue;
 			}
 		}
-		codePoint = Q_GetCpFromUtf8(s, &numUtf8Bytes, &error);
-		s += (numUtf8Bytes - 1);
-		//SCR_DrawSmallCharExt( xx, y, cwidth, cheight, *s );
-		SCR_DrawSmallCharExt(xx, y, cwidth, cheight, codePoint);
-		xx += cwidth;  //SMALLCHAR_WIDTH;
+		SCR_DrawSmallChar( xx, y, *s );
+		xx += smallchar_width;
 		s++;
 	}
 	re.SetColor( NULL );
 }
 
 
-
-
 /*
 ** SCR_Strlen -- skips color escape codes
 */
@@ -339,10 +346,11 @@
 	return count;
 }
 
+
 /*
 ** SCR_GetBigStringWidth
 */ 
-int	SCR_GetBigStringWidth( const char *str ) {
+int SCR_GetBigStringWidth( const char *str ) {
 	return SCR_Strlen( str ) * BIGCHAR_WIDTH;
 }
 
@@ -354,8 +362,8 @@
 SCR_DrawDemoRecording
 =================
 */
-void SCR_DrawDemoRecording( void ) {
-	char	string[1024];
+static void SCR_DrawDemoRecording( void ) {
+	char	string[sizeof(clc.recordNameShort)+32];
 	int		pos;
 
 	if ( !clc.demorecording ) {
@@ -365,10 +373,15 @@
 		return;
 	}
 
-	pos = FS_FTell( clc.demoWriteFile );
-	sprintf( string, "RECORDING %s: %ik", clc.demoName, pos / 1024 );
+	pos = FS_FTell( clc.recordfile );
 
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 20, 8, string, g_color_table[7], qtrue, qfalse );
+	if (cl_drawRecording->integer == 1) {
+		sprintf(string, "RECORDING %s: %ik", clc.recordNameShort, pos / 1024);
+		SCR_DrawStringExt(320 - strlen(string) * 4, 20, 8, string, g_color_table[ColorIndex(COLOR_WHITE)], qtrue, qfalse);
+	} else if (cl_drawRecording->integer == 2) {
+		sprintf(string, "RECORDING: %ik", pos / 1024);
+		SCR_DrawStringExt(320 - strlen(string) * 4, 20, 8, string, g_color_table[ColorIndex(COLOR_WHITE)], qtrue, qfalse);
+	}
 }
 
 
@@ -389,9 +402,9 @@
 		return;  // not recording at the moment.
 	else if (clc.state != CA_ACTIVE)
 		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
+	else if (!clc.voipEnabled)
 		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
+	else if (clc.demoplaying)
 		return;  // playing back a demo.
 	else if (!cl_voip->integer)
 		return;  // client has VoIP support disabled.
@@ -407,55 +420,10 @@
 	buffer[i] = '\0';
 
 	sprintf( string, "VoIP: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 10, 8, string, g_color_table[7], qtrue, qfalse );
+	SCR_DrawStringExt( 320 - strlen( string ) * 4, 10, 8, string, g_color_table[ ColorIndex( COLOR_WHITE ) ], qtrue, qfalse );
 }
 #endif
 
-/*
-=================
-SCR_DrawVolumeMeter
-=================
-*/
-static void SCR_DrawVolumeMeter( void ) {
-	char	buffer[16];
-	char	string[256];
-	int limit, i;
-
-	if (!cl_volumeShowMeter->integer)
-		return;  // player doesn't want to show meter at all.
-
-#if 0
-	else if (!cl_voipSend->integer)
-		return;  // not recording at the moment.
-	else if (clc.state != CA_ACTIVE)
-		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
-		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
-		return;  // playing back a demo.
-	else if (!cl_voip->integer)
-		return;  // client has VoIP support disabled.
-#endif
-
-	limit = (int) (clc.audioPower * 10.0f);
-	if (limit > 10)
-		limit = 10;
-
-	for (i = 0; i < limit; i++)
-		buffer[i] = '*';
-	while (i < 10)
-		buffer[i++] = ' ';
-	buffer[i] = '\0';
-
-	sprintf( string, "Volume: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 200, 8, string, g_color_table[7], qtrue, qfalse );
-
-	sprintf(string, "%f dB", clc.audioDecibels);
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 220, 8, string, g_color_table[7], qtrue, qfalse );
-}
-
-
-
 
 /*
 ===============================================================================
@@ -473,18 +441,19 @@
 SCR_DebugGraph
 ==============
 */
-void SCR_DebugGraph (float value)
+void SCR_DebugGraph( float value )
 {
 	values[current] = value;
 	current = (current + 1) % ARRAY_LEN(values);
 }
 
+
 /*
 ==============
 SCR_DrawDebugGraph
 ==============
 */
-void SCR_DrawDebugGraph (void)
+static void SCR_DrawDebugGraph( void )
 {
 	int		a, x, y, w, i, h;
 	float	v;
@@ -495,8 +464,8 @@
 	w = cls.glconfig.vidWidth;
 	x = 0;
 	y = cls.glconfig.vidHeight;
-	re.SetColor( g_color_table[0] );
-	re.DrawStretchPic(x, y - cl_graphheight->integer,
+	re.SetColor( g_color_table[ ColorIndex( COLOR_BLACK ) ] );
+	re.DrawStretchPic(x, y - cl_graphheight->integer, 
 		w, cl_graphheight->integer, 0, 0, 0, 0, cls.whiteShader );
 	re.SetColor( NULL );
 
@@ -505,7 +474,7 @@
 		i = (ARRAY_LEN(values)+current-1-(a % ARRAY_LEN(values))) % ARRAY_LEN(values);
 		v = values[i];
 		v = v * cl_graphscale->integer + cl_graphshift->integer;
-
+		
 		if (v < 0)
 			v += cl_graphheight->integer * (1+(int)(-v / cl_graphheight->integer));
 		h = (int)v % cl_graphheight->integer;
@@ -520,7 +489,6 @@
 SCR_Init
 ==================
 */
-
 void SCR_Init( void ) {
 	cl_timegraph = Cvar_Get ("timegraph", "0", CVAR_CHEAT);
 	cl_debuggraph = Cvar_Get ("debuggraph", "0", CVAR_CHEAT);
@@ -532,6 +500,16 @@
 }
 
 
+/*
+==================
+SCR_Done
+==================
+*/
+void SCR_Done( void ) {
+	scr_initialized = qfalse;
+}
+
+
 //=======================================================
 
 /*
@@ -541,19 +519,22 @@
 This will be called twice if rendering in stereo mode
 ==================
 */
-void SCR_DrawScreenField( stereoFrame_t stereoFrame ) {
+static void SCR_DrawScreenField( stereoFrame_t stereoFrame ) {
 	qboolean uiFullscreen;
 
-	re.BeginFrame(stereoFrame, CL_VideoRecording(&afdMain));
+	re.BeginFrame( stereoFrame );
 
-	uiFullscreen = (uivm && VM_Call( uivm, UI_IS_FULLSCREEN ));
+	uiFullscreen = (uivm && VM_Call( uivm, 0, UI_IS_FULLSCREEN ));
 
 	// wide aspect ratio screens need to have the sides cleared
 	// unless they are displaying game renderings
-	if ( uiFullscreen || clc.state < CA_LOADING ) {
+	if ( uiFullscreen || cls.state < CA_LOADING ) {
 		if ( cls.glconfig.vidWidth * 480 > cls.glconfig.vidHeight * 640 ) {
-			re.SetColor( g_color_table[0] );
-			re.DrawStretchPic( 0, 0, cls.glconfig.vidWidth, cls.glconfig.vidHeight, 0, 0, 0, 0, cls.whiteShader );
+			// draw vertical bars on sides for legacy mods
+			const int w = (cls.glconfig.vidWidth - ((cls.glconfig.vidHeight * 640) / 480)) /2;
+			re.SetColor( g_color_table[ ColorIndex( COLOR_BLACK ) ] );
+			re.DrawStretchPic( 0, 0, w, cls.glconfig.vidHeight, 0, 0, 0, 0, cls.whiteShader );
+			re.DrawStretchPic( cls.glconfig.vidWidth - w, 0, w, cls.glconfig.vidHeight, 0, 0, 0, 0, cls.whiteShader );
 			re.SetColor( NULL );
 		}
 	}
@@ -561,9 +542,9 @@
 	// if the menu is going to cover the entire screen, we
 	// don't need to render anything under it
 	if ( uivm && !uiFullscreen ) {
-		switch( clc.state ) {
+		switch( cls.state ) {
 		default:
-			Com_Error( ERR_FATAL, "SCR_DrawScreenField: bad clc.state" );
+			Com_Error( ERR_FATAL, "SCR_DrawScreenField: bad cls.state" );
 			break;
 		case CA_CINEMATIC:
 			SCR_DrawCinematic();
@@ -571,43 +552,42 @@
 		case CA_DISCONNECTED:
 			// force menu up
 			S_StopAllSounds();
-			VM_Call( uivm, UI_SET_ACTIVE_MENU, UIMENU_MAIN );
+			VM_Call( uivm, 1, UI_SET_ACTIVE_MENU, UIMENU_MAIN );
 			break;
-		case CA_DOWNLOADINGWORKSHOPS:
 		case CA_CONNECTING:
 		case CA_CHALLENGING:
 		case CA_CONNECTED:
 			// connecting clients will only show the connection dialog
 			// refresh to update the time
-			VM_Call( uivm, UI_REFRESH, cls.realtime );
-			VM_Call( uivm, UI_DRAW_CONNECT_SCREEN, qfalse );
+			VM_Call( uivm, 1, UI_REFRESH, cls.realtime );
+			VM_Call( uivm, 1, UI_DRAW_CONNECT_SCREEN, qfalse );
 			break;
 		case CA_LOADING:
 		case CA_PRIMED:
 			// draw the game information screen and loading progress
-			CL_CGameRendering(stereoFrame);
-
+			if ( cgvm ) {
+				CL_CGameRendering( stereoFrame );
+			}
 			// also draw the connection information, so it doesn't
 			// flash away too briefly on local or lan games
 			// refresh to update the time
-			VM_Call( uivm, UI_REFRESH, cls.realtime );
-			VM_Call( uivm, UI_DRAW_CONNECT_SCREEN, qtrue );
+			VM_Call( uivm, 1, UI_REFRESH, cls.realtime );
+			VM_Call( uivm, 1, UI_DRAW_CONNECT_SCREEN, qtrue );
 			break;
 		case CA_ACTIVE:
 			// always supply STEREO_CENTER as vieworg offset is now done by the engine.
-			CL_CGameRendering(stereoFrame);
+			CL_CGameRendering( stereoFrame );
 			SCR_DrawDemoRecording();
 #ifdef USE_VOIP
 			SCR_DrawVoipMeter();
 #endif
-			SCR_DrawVolumeMeter();
 			break;
 		}
 	}
 
 	// the menu draws next
 	if ( Key_GetCatcher( ) & KEYCATCH_UI && uivm ) {
-		VM_Call( uivm, UI_REFRESH, cls.realtime );
+		VM_Call( uivm, 1, UI_REFRESH, cls.realtime );
 	}
 
 	// console draws next
@@ -619,6 +599,7 @@
 	}
 }
 
+
 /*
 ==================
 SCR_UpdateScreen
@@ -628,10 +609,23 @@
 ==================
 */
 void SCR_UpdateScreen( void ) {
-	static int	recursive;
-
-	if ( !scr_initialized ) {
-		return;				// not initialized yet
+	static int recursive;
+	static int framecount;
+	static int next_frametime;
+
+	if ( !scr_initialized )
+		return; // not initialized yet
+
+	if ( framecount == cls.framecount ) {
+		int ms = Sys_Milliseconds();
+		if ( next_frametime && ms - next_frametime < 0 ) {
+			re.ThrottleBackend();
+		} else {
+			next_frametime = ms + 16; // limit to 60 FPS
+		}
+	} else {
+		next_frametime = 0;
+		framecount = cls.framecount;
 	}
 
 	if ( ++recursive > 2 ) {
@@ -641,17 +635,15 @@
 
 	// If there is no VM, there are also no rendering commands issued. Stop the renderer in
 	// that case.
-	if( uivm || com_dedicated->integer )
+	if ( uivm )
 	{
+		// XXX
 		int in_anaglyphMode = Cvar_VariableIntegerValue("r_anaglyphMode");
-
 		// if running in stereo, we need to draw the frame twice
 		if ( cls.glconfig.stereoEnabled || in_anaglyphMode) {
 			SCR_DrawScreenField( STEREO_LEFT );
 			SCR_DrawScreenField( STEREO_RIGHT );
 		} else {
-			//Com_Printf("1:  %d\n", (int)time(NULL));
-			//Com_Printf("1:  %d\n", Sys_Milliseconds());
 			SCR_DrawScreenField( STEREO_CENTER );
 		}
 
@@ -660,12 +652,7 @@
 		} else {
 			re.EndFrame( NULL, NULL );
 		}
-		//Com_Printf("2:  %d\n", (int)time(NULL));
-		//Com_Printf("2:  %d\n", Sys_Milliseconds());
-	} else {
-		//
 	}
 
 	recursive = 0;
 }
-

```

### `openarena-engine`  — sha256 `3e10c491acf1...`, 15397 bytes

_Diff stat: +113 / -115 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_scrn.c	2026-04-16 20:02:25.173221100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_scrn.c	2026-04-16 22:48:25.733378900 +0100
@@ -22,9 +22,8 @@
 // cl_scrn.c -- master for refresh, status bar, console, chat, notify, etc
 
 #include "client.h"
-#include <time.h>
 
-static qboolean	scr_initialized;		// ready to draw
+qboolean	scr_initialized;		// ready to draw
 
 cvar_t		*cl_timegraph;
 cvar_t		*cl_debuggraph;
@@ -85,6 +84,35 @@
 	}
 }
 
+
+/*
+================
+SCR_AdjustFrom480
+
+leilei - Adjusted for resolution and screen aspect ratio.... but from vertical only so the aspect is ok
+================
+*/
+void SCR_AdjustFrom480( float *x, float *y, float *w, float *h ) {
+	float	yscale;
+
+	// scale for screen sizes
+	yscale = cls.glconfig.vidHeight / 480.0;
+
+	if ( x ) {
+		*x *= yscale;
+	}
+	if ( y ) {
+		*y *= yscale;
+	}
+	if ( w ) {
+		*w *= yscale;
+	}
+	if ( h ) {
+		*h *= yscale;
+	}
+}
+
+
 /*
 ================
 SCR_FillRect
@@ -120,8 +148,7 @@
 ** SCR_DrawChar
 ** chars are drawn at 640*480 virtual screen size
 */
-static void SCR_DrawChar (int x, int y, float size, int ch)
-{
+static void SCR_DrawChar( int x, int y, float size, int ch ) {
 	int row, col;
 	float frow, fcol;
 	float	ax, ay, aw, ah;
@@ -155,48 +182,82 @@
 					   cls.charSetShader );
 }
 
-//FIXME ioquake3 uses g_smallchar_* with this function, the only places this
-// is used (almost everything else uses SCR_DrawSmallCharExt() which scales) is
-// drawing the version number in console and quake live workshop downloads.
-// For workshop downloads not sure what to use so keeping this as is for now.
-
 /*
 ** SCR_DrawSmallChar
 ** small chars are drawn at native screen resolution
 */
-void SCR_DrawSmallChar( int x, int y, int ch ) {
-	glyphInfo_t glyph;
-
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
+void SCR_DrawSmallChar( int x, int y, int ch, int scalemode ) {
+	int row, col;
+	float frow, fcol;
+	float size;
 
-	if ( y < -SMALLCHAR_HEIGHT ) {
-		return;
+	if ((scalemode) && (cl_consoleScale->integer) && (cls.glconfig.vidWidth > SCREEN_WIDTH))
+	{
+		// leilei - ideally, I want to have the same amount of lines as 640x480 on any higher resolution to keep it readable,
+		// while horizontally it's also like 640x480 but keeping up a gap to the right so the characters are still 1:2 aspect.
+		// like idTech 4.
+		// in 640x480 on a normal pulled down console, there are 12 lines, 6.5 lines on a half pull, and 29 for a full console
+		int row, col;
+		float frow, fcol;
+		float	ax, ay, aw, ah;
+		float size;
+		ch &= 255;
+	
+		if ( ch == ' ' ) {
+			return;
+		}
+	
+		if ( y < -SMALLCHAR_HEIGHT ) {
+			return;
+		}
+	
+		ax = x;
+		ay = y;
+		aw = SMALLCHAR_WIDTH ;
+		ah = SMALLCHAR_HEIGHT;
+		if (scalemode == 2)
+		SCR_AdjustFrom480( &ax, &ay, &aw, &ah );
+		else
+		SCR_AdjustFrom640( &ax, &ay, &aw, &ah );
+
+		row = ch>>4;
+		col = ch&15;
+	
+		frow = row*0.0625;
+		fcol = col*0.0625;
+		size = 0.0625;
+	
+		re.DrawStretchPic( ax, ay, aw, ah,
+						   fcol, frow, 
+						   fcol + size, frow + size, 
+						   cls.charSetShader );
+	
+	
 	}
-
-	re.DrawStretchPic(x, y - glyph.top, SMALLCHAR_WIDTH, /* SMALLCHAR_HEIGHT */ glyph.height < SMALLCHAR_HEIGHT ? glyph.height : SMALLCHAR_HEIGHT,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
-}
-
-void SCR_DrawSmallCharExt( float x, float y, float width, float height, int ch ) {
-	glyphInfo_t glyph;
-	float scale;
-
-	re.GetGlyphInfo(&cls.consoleFont, ch, &glyph);
-
-	if ( y < -height ) {
-		return;
+	else
+	{
+		ch &= 255;
+	
+		if ( ch == ' ' ) {
+			return;
+		}
+	
+		if ( y < -SMALLCHAR_HEIGHT ) {
+			return;
+		}
+	
+		row = ch>>4;
+		col = ch&15;
+	
+		frow = row*0.0625;
+		fcol = col*0.0625;
+		size = 0.0625;
+	
+		re.DrawStretchPic( x, y, SMALLCHAR_WIDTH, SMALLCHAR_HEIGHT,
+						   fcol, frow, 
+						   fcol + size, frow + size, 
+						   cls.charSetShader );
 	}
-
-	scale = height / SMALLCHAR_HEIGHT;
-
-	// 2018-11-12 checking fo glyph.height since super and subscripts will be smaller (ex:  trademark symbol)
-
-	re.DrawStretchPic(x, y - glyph.top, width,  /* height */  (glyph.height * scale) < height ? (glyph.height * scale) : height ,
-					  glyph.s, glyph.t,
-					  glyph.s2, glyph.t2,
-					  glyph.glyph);
 }
 
 
@@ -216,8 +277,6 @@
 	const char	*s;
 	int			xx;
 
-	//printf("SCR_DrawStringExt: '%s'\n", string);
-
 	// draw the drop shadow
 	color[0] = color[1] = color[2] = 0;
 	color[3] = setColor[3];
@@ -280,22 +339,17 @@
 to a fixed color.
 ==================
 */
-void SCR_DrawSmallStringExt( float x, float y, float cwidth, float cheight, const char *string, float *setColor, qboolean forceColor,
+void SCR_DrawSmallStringExt( int x, int y, const char *string, float *setColor, qboolean forceColor,
 		qboolean noColorEscape ) {
 	vec4_t		color;
 	const char	*s;
-	float			xx;
-	//glyphInfo_t glyph;
+	int			xx;
 
 	// draw the colored text
 	s = string;
 	xx = x;
 	re.SetColor( setColor );
 	while ( *s ) {
-		int codePoint;
-		int numUtf8Bytes;
-		qboolean error;
-
 		if ( Q_IsColorString( s ) ) {
 			if ( !forceColor ) {
 				Com_Memcpy( color, g_color_table[ColorIndex(*(s+1))], sizeof( color ) );
@@ -307,11 +361,8 @@
 				continue;
 			}
 		}
-		codePoint = Q_GetCpFromUtf8(s, &numUtf8Bytes, &error);
-		s += (numUtf8Bytes - 1);
-		//SCR_DrawSmallCharExt( xx, y, cwidth, cheight, *s );
-		SCR_DrawSmallCharExt(xx, y, cwidth, cheight, codePoint);
-		xx += cwidth;  //SMALLCHAR_WIDTH;
+		SCR_DrawSmallChar( xx, y, *s, 2 );
+		xx += SMALLCHAR_WIDTH;
 		s++;
 	}
 	re.SetColor( NULL );
@@ -319,7 +370,6 @@
 
 
 
-
 /*
 ** SCR_Strlen -- skips color escape codes
 */
@@ -365,7 +415,7 @@
 		return;
 	}
 
-	pos = FS_FTell( clc.demoWriteFile );
+	pos = FS_FTell( clc.demofile );
 	sprintf( string, "RECORDING %s: %ik", clc.demoName, pos / 1024 );
 
 	SCR_DrawStringExt( 320 - strlen( string ) * 4, 20, 8, string, g_color_table[7], qtrue, qfalse );
@@ -378,7 +428,7 @@
 SCR_DrawVoipMeter
 =================
 */
-static void SCR_DrawVoipMeter( void ) {
+void SCR_DrawVoipMeter( void ) {
 	char	buffer[16];
 	char	string[256];
 	int limit, i;
@@ -389,9 +439,9 @@
 		return;  // not recording at the moment.
 	else if (clc.state != CA_ACTIVE)
 		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
+	else if (!clc.voipEnabled)
 		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
+	else if (clc.demoplaying)
 		return;  // playing back a demo.
 	else if (!cl_voip->integer)
 		return;  // client has VoIP support disabled.
@@ -411,49 +461,6 @@
 }
 #endif
 
-/*
-=================
-SCR_DrawVolumeMeter
-=================
-*/
-static void SCR_DrawVolumeMeter( void ) {
-	char	buffer[16];
-	char	string[256];
-	int limit, i;
-
-	if (!cl_volumeShowMeter->integer)
-		return;  // player doesn't want to show meter at all.
-
-#if 0
-	else if (!cl_voipSend->integer)
-		return;  // not recording at the moment.
-	else if (clc.state != CA_ACTIVE)
-		return;  // not connected to a server.
-	else if (!clc.voipEnabled  &&  !clc.demoplaying)
-		return;  // server doesn't support VoIP.
-	else if (clc.demoplaying  &&  !clc.demorecording)
-		return;  // playing back a demo.
-	else if (!cl_voip->integer)
-		return;  // client has VoIP support disabled.
-#endif
-
-	limit = (int) (clc.audioPower * 10.0f);
-	if (limit > 10)
-		limit = 10;
-
-	for (i = 0; i < limit; i++)
-		buffer[i] = '*';
-	while (i < 10)
-		buffer[i++] = ' ';
-	buffer[i] = '\0';
-
-	sprintf( string, "Volume: [%s]", buffer );
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 200, 8, string, g_color_table[7], qtrue, qfalse );
-
-	sprintf(string, "%f dB", clc.audioDecibels);
-	SCR_DrawStringExt( 320 - strlen( string ) * 4, 220, 8, string, g_color_table[7], qtrue, qfalse );
-}
-
 
 
 
@@ -496,7 +503,7 @@
 	x = 0;
 	y = cls.glconfig.vidHeight;
 	re.SetColor( g_color_table[0] );
-	re.DrawStretchPic(x, y - cl_graphheight->integer,
+	re.DrawStretchPic(x, y - cl_graphheight->integer, 
 		w, cl_graphheight->integer, 0, 0, 0, 0, cls.whiteShader );
 	re.SetColor( NULL );
 
@@ -505,7 +512,7 @@
 		i = (ARRAY_LEN(values)+current-1-(a % ARRAY_LEN(values))) % ARRAY_LEN(values);
 		v = values[i];
 		v = v * cl_graphscale->integer + cl_graphshift->integer;
-
+		
 		if (v < 0)
 			v += cl_graphheight->integer * (1+(int)(-v / cl_graphheight->integer));
 		h = (int)v % cl_graphheight->integer;
@@ -520,7 +527,6 @@
 SCR_Init
 ==================
 */
-
 void SCR_Init( void ) {
 	cl_timegraph = Cvar_Get ("timegraph", "0", CVAR_CHEAT);
 	cl_debuggraph = Cvar_Get ("debuggraph", "0", CVAR_CHEAT);
@@ -544,7 +550,7 @@
 void SCR_DrawScreenField( stereoFrame_t stereoFrame ) {
 	qboolean uiFullscreen;
 
-	re.BeginFrame(stereoFrame, CL_VideoRecording(&afdMain));
+	re.BeginFrame( stereoFrame );
 
 	uiFullscreen = (uivm && VM_Call( uivm, UI_IS_FULLSCREEN ));
 
@@ -573,7 +579,6 @@
 			S_StopAllSounds();
 			VM_Call( uivm, UI_SET_ACTIVE_MENU, UIMENU_MAIN );
 			break;
-		case CA_DOWNLOADINGWORKSHOPS:
 		case CA_CONNECTING:
 		case CA_CHALLENGING:
 		case CA_CONNECTED:
@@ -600,7 +605,6 @@
 #ifdef USE_VOIP
 			SCR_DrawVoipMeter();
 #endif
-			SCR_DrawVolumeMeter();
 			break;
 		}
 	}
@@ -643,15 +647,13 @@
 	// that case.
 	if( uivm || com_dedicated->integer )
 	{
+		// XXX
 		int in_anaglyphMode = Cvar_VariableIntegerValue("r_anaglyphMode");
-
 		// if running in stereo, we need to draw the frame twice
 		if ( cls.glconfig.stereoEnabled || in_anaglyphMode) {
 			SCR_DrawScreenField( STEREO_LEFT );
 			SCR_DrawScreenField( STEREO_RIGHT );
 		} else {
-			//Com_Printf("1:  %d\n", (int)time(NULL));
-			//Com_Printf("1:  %d\n", Sys_Milliseconds());
 			SCR_DrawScreenField( STEREO_CENTER );
 		}
 
@@ -660,12 +662,8 @@
 		} else {
 			re.EndFrame( NULL, NULL );
 		}
-		//Com_Printf("2:  %d\n", (int)time(NULL));
-		//Com_Printf("2:  %d\n", Sys_Milliseconds());
-	} else {
-		//
 	}
-
+	
 	recursive = 0;
 }
 

```
