# Diff: `code/q3_ui/ui_connect.c`
**Canonical:** `wolfcamql-src` (sha256 `c7ca855e7ba6...`, 9957 bytes)

## Variants

### `quake3-source`  — sha256 `46cb43736c5c...`, 9954 bytes

_Diff stat: +22 / -22 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_connect.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_connect.c	2026-04-16 20:02:19.944820100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -82,7 +82,16 @@
 	downloadCount = trap_Cvar_VariableValue( "cl_downloadCount" );
 	downloadTime = trap_Cvar_VariableValue( "cl_downloadTime" );
 
-	leftWidth = UI_ProportionalStringWidth( dlText ) * UI_ProportionalSizeScale( style );
+#if 0 // bk010104
+	fprintf( stderr, "\n\n-----------------------------------------------\n");
+	fprintf( stderr, "DB: downloadSize:  %16d\n", downloadSize );
+	fprintf( stderr, "DB: downloadCount: %16d\n", downloadCount );
+	fprintf( stderr, "DB: downloadTime:  %16d\n", downloadTime );  
+  	fprintf( stderr, "DB: UI realtime:   %16d\n", uis.realtime );	// bk
+	fprintf( stderr, "DB: UI frametime:  %16d\n", uis.frametime );	// bk
+#endif
+
+	leftWidth = width = UI_ProportionalStringWidth( dlText ) * UI_ProportionalSizeScale( style );
 	width = UI_ProportionalStringWidth( etaText ) * UI_ProportionalSizeScale( style );
 	if (width > leftWidth) leftWidth = width;
 	width = UI_ProportionalStringWidth( xferText ) * UI_ProportionalSizeScale( style );
@@ -94,7 +103,7 @@
 	UI_DrawProportionalString( 8, 224, xferText, style, color_white );
 
 	if (downloadSize > 0) {
-		s = va( "%s (%d%%)", downloadName, (int)( (float)downloadCount * 100.0f / downloadSize ) );
+		s = va( "%s (%d%%)", downloadName, downloadCount * 100 / downloadSize );
 	} else {
 		s = downloadName;
 	}
@@ -109,6 +118,10 @@
 		UI_DrawProportionalString( leftWidth, 192, 
 			va("(%s of %s copied)", dlSizeBuf, totalSizeBuf), style, color_white );
 	} else {
+	  // bk010108
+	  //float elapsedTime = (float)(uis.realtime - downloadTime); // current - start (msecs)
+	  //elapsedTime = elapsedTime * 0.001f; // in seconds
+	  //if ( elapsedTime <= 0.0f ) elapsedTime == 0.0f;
 	  if ( (uis.realtime - downloadTime) / 1000) {
 			xferRate = downloadCount / ((uis.realtime - downloadTime) / 1000);
 		  //xferRate = (int)( ((float)downloadCount) / elapsedTime);
@@ -116,6 +129,9 @@
 			xferRate = 0;
 		}
 
+	  //fprintf( stderr, "DB: elapsedTime:  %16.8f\n", elapsedTime );	// bk
+	  //fprintf( stderr, "DB: xferRate:   %16d\n", xferRate );	// bk
+
 		UI_ReadableSize( xferRateBuf, sizeof xferRateBuf, xferRate );
 
 		// Extrapolate estimated completion time
@@ -125,7 +141,7 @@
 			// We do it in K (/1024) because we'd overflow around 4MB
 			n = (n - (((downloadCount/1024) * n) / (downloadSize/1024))) * 1000;
 			
-			UI_PrintTime ( dlTimeBuf, sizeof dlTimeBuf, n );
+			UI_PrintTime ( dlTimeBuf, sizeof dlTimeBuf, n ); // bk010104
 				//(n - (((downloadCount/1024) * n) / (downloadSize/1024))) * 1000);
 
 			UI_DrawProportionalString( leftWidth, 160, 
@@ -180,21 +196,8 @@
 		UI_DrawProportionalString( 320, 16, va( "Loading %s", Info_ValueForKey( info, "mapname" ) ), UI_BIGFONT|UI_CENTER|UI_DROPSHADOW, color_white );
 	}
 
-	if (!cstate.demoplaying) {
-		UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-		//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-	} else {
-		//FIXME would need wrapping
-		//UI_DrawProportionalString( 320, 64, va("Playing %s", UI_Cvar_VariableString("cl_demoFileBaseName")), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-
-		if (cstate.connState == CA_DOWNLOADINGWORKSHOPS) {
-			//FIXME maybe show current workshop number
-			UI_DrawProportionalString(320, 64, "Downloading Workshops", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-			trap_DrawConsoleLinesOver(10, 160, 10);
-		} else {
-			UI_DrawProportionalString(320, 64, "Playing demo", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-		}
-	}
+	UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
+	//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
 
 	// display global MOTD at bottom
 	UI_DrawProportionalString( SCREEN_WIDTH/2, SCREEN_HEIGHT-32, 
@@ -245,7 +248,6 @@
 		char downloadName[MAX_INFO_VALUE];
 
 			trap_Cvar_VariableStringBuffer( "cl_downloadName", downloadName, sizeof(downloadName) );
-			//Q_strncpyz(downloadName, "test download", sizeof(downloadName));
 			if (*downloadName) {
 				UI_DisplayDownloadInfo( downloadName );
 				return;
@@ -254,7 +256,6 @@
 		s = "Awaiting gamestate...";
 		break;
 	case CA_LOADING:
-		//Com_Printf("loading ...\n");
 		return;
 	case CA_PRIMED:
 		return;
@@ -274,7 +275,6 @@
 ===================
 */
 void UI_KeyConnect( int key ) {
-	//Com_Printf("^5ui key connect: %d\n", key);
 	if ( key == K_ESCAPE ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "disconnect\n" );
 		return;

```

### `openarena-engine`  — sha256 `4e1eb3bc029d...`, 9170 bytes
Also identical in: ioquake3

_Diff stat: +2 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_connect.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_connect.c	2026-04-16 22:48:25.893195200 +0100
@@ -180,21 +180,8 @@
 		UI_DrawProportionalString( 320, 16, va( "Loading %s", Info_ValueForKey( info, "mapname" ) ), UI_BIGFONT|UI_CENTER|UI_DROPSHADOW, color_white );
 	}
 
-	if (!cstate.demoplaying) {
-		UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-		//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-	} else {
-		//FIXME would need wrapping
-		//UI_DrawProportionalString( 320, 64, va("Playing %s", UI_Cvar_VariableString("cl_demoFileBaseName")), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-
-		if (cstate.connState == CA_DOWNLOADINGWORKSHOPS) {
-			//FIXME maybe show current workshop number
-			UI_DrawProportionalString(320, 64, "Downloading Workshops", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-			trap_DrawConsoleLinesOver(10, 160, 10);
-		} else {
-			UI_DrawProportionalString(320, 64, "Playing demo", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-		}
-	}
+	UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
+	//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
 
 	// display global MOTD at bottom
 	UI_DrawProportionalString( SCREEN_WIDTH/2, SCREEN_HEIGHT-32, 
@@ -245,7 +232,6 @@
 		char downloadName[MAX_INFO_VALUE];
 
 			trap_Cvar_VariableStringBuffer( "cl_downloadName", downloadName, sizeof(downloadName) );
-			//Q_strncpyz(downloadName, "test download", sizeof(downloadName));
 			if (*downloadName) {
 				UI_DisplayDownloadInfo( downloadName );
 				return;
@@ -254,7 +240,6 @@
 		s = "Awaiting gamestate...";
 		break;
 	case CA_LOADING:
-		//Com_Printf("loading ...\n");
 		return;
 	case CA_PRIMED:
 		return;
@@ -274,7 +259,6 @@
 ===================
 */
 void UI_KeyConnect( int key ) {
-	//Com_Printf("^5ui key connect: %d\n", key);
 	if ( key == K_ESCAPE ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "disconnect\n" );
 		return;

```

### `openarena-gamecode`  — sha256 `9d3955e574d8...`, 9994 bytes

_Diff stat: +20 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_connect.c	2026-04-16 20:02:25.204155300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_connect.c	2026-04-16 22:48:24.180490100 +0100
@@ -82,7 +82,16 @@
 	downloadCount = trap_Cvar_VariableValue( "cl_downloadCount" );
 	downloadTime = trap_Cvar_VariableValue( "cl_downloadTime" );
 
-	leftWidth = UI_ProportionalStringWidth( dlText ) * UI_ProportionalSizeScale( style );
+#if 0 // bk010104
+	fprintf( stderr, "\n\n-----------------------------------------------\n");
+	fprintf( stderr, "DB: downloadSize:  %16d\n", downloadSize );
+	fprintf( stderr, "DB: downloadCount: %16d\n", downloadCount );
+	fprintf( stderr, "DB: downloadTime:  %16d\n", downloadTime );  
+  	fprintf( stderr, "DB: UI realtime:   %16d\n", uis.realtime );	// bk
+	fprintf( stderr, "DB: UI frametime:  %16d\n", uis.frametime );	// bk
+#endif
+
+	leftWidth = width = UI_ProportionalStringWidth( dlText ) * UI_ProportionalSizeScale( style );
 	width = UI_ProportionalStringWidth( etaText ) * UI_ProportionalSizeScale( style );
 	if (width > leftWidth) leftWidth = width;
 	width = UI_ProportionalStringWidth( xferText ) * UI_ProportionalSizeScale( style );
@@ -109,6 +118,10 @@
 		UI_DrawProportionalString( leftWidth, 192, 
 			va("(%s of %s copied)", dlSizeBuf, totalSizeBuf), style, color_white );
 	} else {
+	  // bk010108
+	  //float elapsedTime = (float)(uis.realtime - downloadTime); // current - start (msecs)
+	  //elapsedTime = elapsedTime * 0.001f; // in seconds
+	  //if ( elapsedTime <= 0.0f ) elapsedTime == 0.0f;
 	  if ( (uis.realtime - downloadTime) / 1000) {
 			xferRate = downloadCount / ((uis.realtime - downloadTime) / 1000);
 		  //xferRate = (int)( ((float)downloadCount) / elapsedTime);
@@ -116,6 +129,9 @@
 			xferRate = 0;
 		}
 
+	  //fprintf( stderr, "DB: elapsedTime:  %16.8f\n", elapsedTime );	// bk
+	  //fprintf( stderr, "DB: xferRate:   %16d\n", xferRate );	// bk
+
 		UI_ReadableSize( xferRateBuf, sizeof xferRateBuf, xferRate );
 
 		// Extrapolate estimated completion time
@@ -125,7 +141,7 @@
 			// We do it in K (/1024) because we'd overflow around 4MB
 			n = (n - (((downloadCount/1024) * n) / (downloadSize/1024))) * 1000;
 			
-			UI_PrintTime ( dlTimeBuf, sizeof dlTimeBuf, n );
+			UI_PrintTime ( dlTimeBuf, sizeof dlTimeBuf, n ); // bk010104
 				//(n - (((downloadCount/1024) * n) / (downloadSize/1024))) * 1000);
 
 			UI_DrawProportionalString( leftWidth, 160, 
@@ -180,21 +196,8 @@
 		UI_DrawProportionalString( 320, 16, va( "Loading %s", Info_ValueForKey( info, "mapname" ) ), UI_BIGFONT|UI_CENTER|UI_DROPSHADOW, color_white );
 	}
 
-	if (!cstate.demoplaying) {
-		UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-		//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-	} else {
-		//FIXME would need wrapping
-		//UI_DrawProportionalString( 320, 64, va("Playing %s", UI_Cvar_VariableString("cl_demoFileBaseName")), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
-
-		if (cstate.connState == CA_DOWNLOADINGWORKSHOPS) {
-			//FIXME maybe show current workshop number
-			UI_DrawProportionalString(320, 64, "Downloading Workshops", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-			trap_DrawConsoleLinesOver(10, 160, 10);
-		} else {
-			UI_DrawProportionalString(320, 64, "Playing demo", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color);
-		}
-	}
+	UI_DrawProportionalString( 320, 64, va("Connecting to %s", cstate.servername), UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
+	//UI_DrawProportionalString( 320, 96, "Press Esc to abort", UI_CENTER|UI_SMALLFONT|UI_DROPSHADOW, menu_text_color );
 
 	// display global MOTD at bottom
 	UI_DrawProportionalString( SCREEN_WIDTH/2, SCREEN_HEIGHT-32, 
@@ -245,7 +248,6 @@
 		char downloadName[MAX_INFO_VALUE];
 
 			trap_Cvar_VariableStringBuffer( "cl_downloadName", downloadName, sizeof(downloadName) );
-			//Q_strncpyz(downloadName, "test download", sizeof(downloadName));
 			if (*downloadName) {
 				UI_DisplayDownloadInfo( downloadName );
 				return;
@@ -254,7 +256,6 @@
 		s = "Awaiting gamestate...";
 		break;
 	case CA_LOADING:
-		//Com_Printf("loading ...\n");
 		return;
 	case CA_PRIMED:
 		return;
@@ -274,7 +275,6 @@
 ===================
 */
 void UI_KeyConnect( int key ) {
-	//Com_Printf("^5ui key connect: %d\n", key);
 	if ( key == K_ESCAPE ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "disconnect\n" );
 		return;

```
