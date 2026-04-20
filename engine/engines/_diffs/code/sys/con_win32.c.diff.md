# Diff: `code/sys/con_win32.c`
**Canonical:** `wolfcamql-src` (sha256 `65c1eb0a572f...`, 13089 bytes)

## Variants

### `ioquake3`  — sha256 `10c3510c4046...`, 12780 bytes

_Diff stat: +64 / -68 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\con_win32.c	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sys\con_win32.c	2026-04-16 20:02:21.622757900 +0100
@@ -60,23 +60,23 @@
 	WORD attrib;
 
 	if ( color == COLOR_WHITE )
-		{
-			// use console's foreground and background colors
-			attrib = qconsole_attrib;
-		}
+	{
+		// use console's foreground and background colors
+		attrib = qconsole_attrib;
+	}
 	else
-		{
-			float *rgba = g_color_table[ ColorIndex( color ) ];
+	{
+		float *rgba = g_color_table[ ColorIndex( color ) ];
 
-			// set foreground color
-			attrib = ( rgba[0] >= 0.5 ? FOREGROUND_RED : 0 ) |
-				( rgba[1] >= 0.5 ? FOREGROUND_GREEN : 0 ) |
-				( rgba[2] >= 0.5 ? FOREGROUND_BLUE : 0 ) |
-				( rgba[3] >= 0.5 ? FOREGROUND_INTENSITY : 0 );
+		// set foreground color
+		attrib = ( rgba[0] >= 0.5 ? FOREGROUND_RED		: 0 ) |
+				( rgba[1] >= 0.5 ? FOREGROUND_GREEN		: 0 ) |
+				( rgba[2] >= 0.5 ? FOREGROUND_BLUE		: 0 ) |
+				( rgba[3] >= 0.5 ? FOREGROUND_INTENSITY	: 0 );
 
-			// use console's background color
-			attrib |= qconsole_backgroundAttrib;
-		}
+		// use console's background color
+		attrib |= qconsole_backgroundAttrib;
+	}
 
 	return attrib;
 }
@@ -238,10 +238,10 @@
 	// set curor position
 	cursorPos.Y = binfo.dwCursorPosition.Y;
 	cursorPos.X = qconsole_cursor < qconsole_linelen
-		? qconsole_cursor
-		: qconsole_linelen > binfo.srWindow.Right
-		        ? binfo.srWindow.Right
-		        : qconsole_linelen;
+					? qconsole_cursor
+					: qconsole_linelen > binfo.srWindow.Right
+						? binfo.srWindow.Right
+						: qconsole_linelen;
 
 	SetConsoleCursorPosition( qconsole_hout, cursorPos );
 }
@@ -328,7 +328,6 @@
 CON_Input
 ==================
 */
-//FIXME UTF-8 input
 char *CON_Input( void )
 {
 	INPUT_RECORD buff[ MAX_EDIT_LINE ];
@@ -411,15 +410,12 @@
 		else if( key == VK_TAB )
 		{
 			field_t f;
-			const char *fieldString;
 
-			//Q_strncpyz( f.buffer, qconsole_line, sizeof( f.buffer ) );
-			Field_SetBuffer(&f, qconsole_line, sizeof(qconsole_line), 0);
+			Q_strncpyz( f.buffer, qconsole_line,
+				sizeof( f.buffer ) );
 			Field_AutoComplete( &f );
-			//Q_strncpyz( qconsole_line, f.buffer, sizeof( qconsole_line ) );
-			fieldString = Field_AsStr(&f, 0, 0);
-			Q_strncpyz(qconsole_line, fieldString, sizeof(qconsole_line));
-
+			Q_strncpyz( qconsole_line, f.buffer,
+				sizeof( qconsole_line ) );
 			qconsole_linelen = strlen( qconsole_line );
 			qconsole_cursor = qconsole_linelen;
 			break;
@@ -437,8 +433,8 @@
 					if ( qconsole_cursor < qconsole_linelen )
 					{
 						memmove( qconsole_line + qconsole_cursor - 1,
-								 qconsole_line + qconsole_cursor,
-								 qconsole_linelen - qconsole_cursor );
+									qconsole_line + qconsole_cursor,
+									qconsole_linelen - qconsole_cursor );
 					}
 
 					qconsole_line[ newlen ] = '\0';
@@ -451,8 +447,8 @@
 				if ( qconsole_linelen > qconsole_cursor )
 				{
 					memmove( qconsole_line + qconsole_cursor + 1,
-							 qconsole_line + qconsole_cursor,
-							 qconsole_linelen - qconsole_cursor );
+								qconsole_line + qconsole_cursor,
+								qconsole_linelen - qconsole_cursor );
 				}
 
 				qconsole_line[ qconsole_cursor++ ] = c;
@@ -493,54 +489,54 @@
 */
 void CON_WindowsColorPrint( const char *msg )
 {
-	static char buffer[ MAX_PRINT_MSG ];
-	int length = 0;
+	static char buffer[ MAXPRINTMSG ];
+	int         length = 0;
 
 	while( *msg )
+	{
+		qconsole_drawinput = ( *msg == '\n' );
+
+		if( Q_IsColorString( msg ) || *msg == '\n' )
 		{
-			qconsole_drawinput = ( *msg == '\n' );
+			// First empty the buffer
+			if( length > 0 )
+			{
+				buffer[ length ] = '\0';
+				fputs( buffer, stderr );
+				length = 0;
+			}
 
-			if( Q_IsColorString( msg ) || *msg == '\n' )
-				{
-					// First empty the buffer
-					if( length > 0 )
-						{
-							buffer[ length ] = '\0';
-							fputs( buffer, stderr );
-							length = 0;
-						}
-
-					if( *msg == '\n' )
-						{
-							// Reset color and then add the newline
-							SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( COLOR_WHITE ) );
-							fputs( "\n", stderr );
-							msg++;
-						}
-					else
-						{
-							// Set the color
-							SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( *( msg + 1 ) ) );
-							msg += 2;
-						}
-				}
+			if( *msg == '\n' )
+			{
+				// Reset color and then add the newline
+				SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( COLOR_WHITE ) );
+				fputs( "\n", stderr );
+				msg++;
+			}
 			else
-				{
-					if( length >= MAX_PRINT_MSG - 1 )
-						break;
+			{
+				// Set the color
+				SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( *( msg + 1 ) ) );
+				msg += 2;
+			}
+		}
+		else
+		{
+			if( length >= MAXPRINTMSG - 1 )
+				break;
 
-					buffer[ length ] = *msg;
-					length++;
-					msg++;
-				}
+			buffer[ length ] = *msg;
+			length++;
+			msg++;
 		}
+	}
 
 	// Empty anything still left in the buffer
 	if( length > 0 )
-		{
-			buffer[ length ] = '\0';
-			fputs( buffer, stderr );
-		}
+	{
+		buffer[ length ] = '\0';
+		fputs( buffer, stderr );
+	}
 }
 
 /*

```

### `openarena-engine`  — sha256 `53a0862c7114...`, 11469 bytes

_Diff stat: +65 / -125 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\con_win32.c	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\con_win32.c	2026-04-16 22:48:25.939962600 +0100
@@ -44,7 +44,6 @@
 static char qconsole_line[ MAX_EDIT_LINE ];
 static int qconsole_linelen = 0;
 static qboolean qconsole_drawinput = qtrue;
-static int qconsole_cursor;
 
 static HANDLE qconsole_hout;
 static HANDLE qconsole_hin;
@@ -60,23 +59,23 @@
 	WORD attrib;
 
 	if ( color == COLOR_WHITE )
-		{
-			// use console's foreground and background colors
-			attrib = qconsole_attrib;
-		}
+	{
+		// use console's foreground and background colors
+		attrib = qconsole_attrib;
+	}
 	else
-		{
-			float *rgba = g_color_table[ ColorIndex( color ) ];
+	{
+		float *rgba = g_color_table[ ColorIndex( color ) ];
 
-			// set foreground color
-			attrib = ( rgba[0] >= 0.5 ? FOREGROUND_RED : 0 ) |
-				( rgba[1] >= 0.5 ? FOREGROUND_GREEN : 0 ) |
-				( rgba[2] >= 0.5 ? FOREGROUND_BLUE : 0 ) |
-				( rgba[3] >= 0.5 ? FOREGROUND_INTENSITY : 0 );
+		// set foreground color
+		attrib = ( rgba[0] >= 0.5 ? FOREGROUND_RED		: 0 ) |
+				( rgba[1] >= 0.5 ? FOREGROUND_GREEN		: 0 ) |
+				( rgba[2] >= 0.5 ? FOREGROUND_BLUE		: 0 ) |
+				( rgba[3] >= 0.5 ? FOREGROUND_INTENSITY	: 0 );
 
-			// use console's background color
-			attrib |= qconsole_backgroundAttrib;
-		}
+		// use console's background color
+		attrib |= qconsole_backgroundAttrib;
+	}
 
 	return attrib;
 }
@@ -140,7 +139,6 @@
 	Q_strncpyz( qconsole_line, qconsole_history[ qconsole_history_pos ], 
 		sizeof( qconsole_line ) );
 	qconsole_linelen = strlen( qconsole_line );
-	qconsole_cursor = qconsole_linelen;
 }
 
 /*
@@ -165,7 +163,6 @@
 		qconsole_history_pos = pos;
 		qconsole_line[ 0 ] = '\0';
 		qconsole_linelen = 0;
-		qconsole_cursor = qconsole_linelen;
 		return;
 	}
 
@@ -173,7 +170,6 @@
 	Q_strncpyz( qconsole_line, qconsole_history[ qconsole_history_pos ],
 		sizeof( qconsole_line ) );
 	qconsole_linelen = strlen( qconsole_line );
-	qconsole_cursor = qconsole_linelen;
 }
 
 
@@ -212,7 +208,7 @@
 	{
 		if( i < qconsole_linelen )
 		{
-			if( i + 1 < qconsole_linelen && Q_IsColorString( qconsole_line + i ) )
+			if( Q_IsColorString( qconsole_line + i ) )
 				attrib = CON_ColorCharToAttrib( *( qconsole_line + i + 1 ) );
 
 			line[ i ].Char.AsciiChar = qconsole_line[ i ];
@@ -237,11 +233,7 @@
 
 	// set curor position
 	cursorPos.Y = binfo.dwCursorPosition.Y;
-	cursorPos.X = qconsole_cursor < qconsole_linelen
-		? qconsole_cursor
-		: qconsole_linelen > binfo.srWindow.Right
-		        ? binfo.srWindow.Right
-		        : qconsole_linelen;
+	cursorPos.X = qconsole_linelen > binfo.srWindow.Right ? binfo.srWindow.Right : qconsole_linelen;
 
 	SetConsoleCursorPosition( qconsole_hout, cursorPos );
 }
@@ -328,7 +320,6 @@
 CON_Input
 ==================
 */
-//FIXME UTF-8 input
 char *CON_Input( void )
 {
 	INPUT_RECORD buff[ MAX_EDIT_LINE ];
@@ -367,7 +358,6 @@
 		if( key == VK_RETURN )
 		{
 			newlinepos = i;
-			qconsole_cursor = 0;
 			break;
 		}
 		else if( key == VK_UP )
@@ -380,48 +370,16 @@
 			CON_HistNext();
 			break;
 		}
-		else if( key == VK_LEFT )
-		{
-			qconsole_cursor--;
-			if ( qconsole_cursor < 0 )
-			{
-				qconsole_cursor = 0;
-			}
-			break;
-		}
-		else if( key == VK_RIGHT )
-		{
-			qconsole_cursor++;
-			if ( qconsole_cursor > qconsole_linelen )
-			{
-				qconsole_cursor = qconsole_linelen;
-			}
-			break;
-		}
-		else if( key == VK_HOME )
-		{
-			qconsole_cursor = 0;
-			break;
-		}
-		else if( key == VK_END )
-		{
-			qconsole_cursor = qconsole_linelen;
-			break;
-		}
 		else if( key == VK_TAB )
 		{
 			field_t f;
-			const char *fieldString;
 
-			//Q_strncpyz( f.buffer, qconsole_line, sizeof( f.buffer ) );
-			Field_SetBuffer(&f, qconsole_line, sizeof(qconsole_line), 0);
+			Q_strncpyz( f.buffer, qconsole_line,
+				sizeof( f.buffer ) );
 			Field_AutoComplete( &f );
-			//Q_strncpyz( qconsole_line, f.buffer, sizeof( qconsole_line ) );
-			fieldString = Field_AsStr(&f, 0, 0);
-			Q_strncpyz(qconsole_line, fieldString, sizeof(qconsole_line));
-
+			Q_strncpyz( qconsole_line, f.buffer,
+				sizeof( qconsole_line ) );
 			qconsole_linelen = strlen( qconsole_line );
-			qconsole_cursor = qconsole_linelen;
 			break;
 		}
 
@@ -431,33 +389,15 @@
 
 			if( key == VK_BACK )
 			{
-				if ( qconsole_cursor > 0 )
-				{
-					int newlen = ( qconsole_linelen > 0 ) ? qconsole_linelen - 1 : 0;
-					if ( qconsole_cursor < qconsole_linelen )
-					{
-						memmove( qconsole_line + qconsole_cursor - 1,
-								 qconsole_line + qconsole_cursor,
-								 qconsole_linelen - qconsole_cursor );
-					}
-
-					qconsole_line[ newlen ] = '\0';
-					qconsole_linelen = newlen;
-					qconsole_cursor--;
-				}
+				int pos = ( qconsole_linelen > 0 ) ?
+					qconsole_linelen - 1 : 0; 
+
+				qconsole_line[ pos ] = '\0';
+				qconsole_linelen = pos;
 			}
 			else if( c )
 			{
-				if ( qconsole_linelen > qconsole_cursor )
-				{
-					memmove( qconsole_line + qconsole_cursor + 1,
-							 qconsole_line + qconsole_cursor,
-							 qconsole_linelen - qconsole_cursor );
-				}
-
-				qconsole_line[ qconsole_cursor++ ] = c;
-
-				qconsole_linelen++;
+				qconsole_line[ qconsole_linelen++ ] = c;
 				qconsole_line[ qconsole_linelen ] = '\0'; 
 			}
 		}
@@ -493,54 +433,54 @@
 */
 void CON_WindowsColorPrint( const char *msg )
 {
-	static char buffer[ MAX_PRINT_MSG ];
-	int length = 0;
+	static char buffer[ MAXPRINTMSG ];
+	int         length = 0;
 
 	while( *msg )
+	{
+		qconsole_drawinput = ( *msg == '\n' );
+
+		if( Q_IsColorString( msg ) || *msg == '\n' )
 		{
-			qconsole_drawinput = ( *msg == '\n' );
+			// First empty the buffer
+			if( length > 0 )
+			{
+				buffer[ length ] = '\0';
+				fputs( buffer, stderr );
+				length = 0;
+			}
 
-			if( Q_IsColorString( msg ) || *msg == '\n' )
-				{
-					// First empty the buffer
-					if( length > 0 )
-						{
-							buffer[ length ] = '\0';
-							fputs( buffer, stderr );
-							length = 0;
-						}
-
-					if( *msg == '\n' )
-						{
-							// Reset color and then add the newline
-							SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( COLOR_WHITE ) );
-							fputs( "\n", stderr );
-							msg++;
-						}
-					else
-						{
-							// Set the color
-							SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( *( msg + 1 ) ) );
-							msg += 2;
-						}
-				}
+			if( *msg == '\n' )
+			{
+				// Reset color and then add the newline
+				SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( COLOR_WHITE ) );
+				fputs( "\n", stderr );
+				msg++;
+			}
 			else
-				{
-					if( length >= MAX_PRINT_MSG - 1 )
-						break;
-
-					buffer[ length ] = *msg;
-					length++;
-					msg++;
-				}
+			{
+				// Set the color
+				SetConsoleTextAttribute( qconsole_hout, CON_ColorCharToAttrib( *( msg + 1 ) ) );
+				msg += 2;
+			}
 		}
+		else
+		{
+			if( length >= MAXPRINTMSG - 1 )
+				break;
+
+			buffer[ length ] = *msg;
+			length++;
+			msg++;
+		}
+	}
 
 	// Empty anything still left in the buffer
 	if( length > 0 )
-		{
-			buffer[ length ] = '\0';
-			fputs( buffer, stderr );
-		}
+	{
+		buffer[ length ] = '\0';
+		fputs( buffer, stderr );
+	}
 }
 
 /*

```
