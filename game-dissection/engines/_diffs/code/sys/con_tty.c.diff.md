# Diff: `code/sys/con_tty.c`
**Canonical:** `wolfcamql-src` (sha256 `27bc7d4f4c27...`, 15526 bytes)

## Variants

### `ioquake3`  — sha256 `7e6ff99b8459...`, 12366 bytes

_Diff stat: +18 / -125 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\con_tty.c	2026-04-16 20:02:25.276294700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sys\con_tty.c	2026-04-16 20:02:21.622757900 +0100
@@ -44,8 +44,6 @@
 =============================================================
 */
 
-extern qboolean ConsoleIsPassive;
-
 extern qboolean stdinIsATTY;
 static qboolean stdin_active;
 // general flag to tell about tty console mode
@@ -156,11 +154,7 @@
 			{
 				for (i=0; i<TTY_con.cursor; i++)
 				{
-					int n;
-					//size = write(STDOUT_FILENO, TTY_con.buffer+i, 1);
-					for (n = 0;  n < TTY_con.xbuffer[i].numUtf8Bytes;  n++) {
-						size = write(STDOUT_FILENO, &TTY_con.xbuffer[i].utf8Bytes[n], 1);
-					}
+					size = write(STDOUT_FILENO, TTY_con.buffer+i, 1);
 				}
 			}
 		}
@@ -176,10 +170,6 @@
 */
 void CON_Shutdown( void )
 {
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	if (ttycon_on)
 	{
 		CON_Hide();
@@ -287,10 +277,6 @@
 {
 	struct termios tc;
 
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	// If the process is backgrounded (running non interactively)
 	// then SIGTTIN or SIGTOU is emitted, if not caught, turns into a SIGSTP
 	signal(SIGTTIN, SIG_IGN);
@@ -350,50 +336,14 @@
 	static char text[MAX_EDIT_LINE];
 	int avail;
 	char key;
-	unsigned char ukey;
 	field_t *history;
 	size_t Q_UNUSED_VAR size;
-	int i;
-	static int needUtf8Bytes = 0;
-
-	if (ConsoleIsPassive) {
-		return NULL;
-	}
 
 	if(ttycon_on)
 	{
 		avail = read(STDIN_FILENO, &key, 1);
 		if (avail != -1)
 		{
-			//printf("key... %d  '%d'\n", (unsigned char)key & 0xff, key);
-
-			if (needUtf8Bytes > 0) {
-				for (i = 1;  i < 4;  i++) {
-					if (TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[i] == '\0') {
-						TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[i] = key;
-						needUtf8Bytes--;
-						break;
-					}
-				}
-
-				if (needUtf8Bytes <= 0) {
-					// got it
-
-					{
-						int nbytes;
-						qboolean uerror;
-
-						TTY_con.xbuffer[TTY_con.cursor].codePoint = Q_GetCpFromUtf8(TTY_con.xbuffer[TTY_con.cursor].utf8Bytes, &nbytes, &uerror);
-					}
-
-					// print the current line (this is differential)
-					size = write(STDOUT_FILENO, TTY_con.xbuffer[TTY_con.cursor].utf8Bytes, TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes);
-					TTY_con.cursor++; // next char will always be '\0';
-				}
-
-				return NULL;
-			}
-
 			// we have something
 			// backspace?
 			// NOTE TTimo testing a lot of values .. seems it's the only way to get it to work everywhere
@@ -402,46 +352,33 @@
 				if (TTY_con.cursor > 0)
 				{
 					TTY_con.cursor--;
-					//TTY_con.buffer[TTY_con.cursor] = '\0';
-					TTY_con.xbuffer[TTY_con.cursor].codePoint = '\0';
-					TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 1;
-					TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[0] = '\0';
+					TTY_con.buffer[TTY_con.cursor] = '\0';
 					CON_Back();
 				}
 				return NULL;
 			}
 			// check if this is a control char
-			if ((key) && (key) < ' ' &&  key > '\0')
+			if ((key) && (key) < ' ')
 			{
-				//printf("control char xxxxx\n");
-
 				if (key == '\n')
 				{
-					const char *fieldString;
-
 #ifndef DEDICATED
 					// if not in the game explicitly prepend a slash if needed
-					if (clc.state != CA_ACTIVE && TTY_con.cursor &&
-						TTY_con.xbuffer[0].codePoint != '/' && TTY_con.xbuffer[0].codePoint != '\\')
+					if (clc.state != CA_ACTIVE && con_autochat->integer && TTY_con.cursor &&
+						TTY_con.buffer[0] != '/' && TTY_con.buffer[0] != '\\')
 					{
-						memmove(TTY_con.xbuffer + 1, TTY_con.xbuffer, sizeof(TTY_con.xbuffer) - (1 * sizeof(fieldChar_t)));
-						TTY_con.xbuffer[0].codePoint = '\\';
-						TTY_con.xbuffer[0].numUtf8Bytes = 1;
-						TTY_con.xbuffer[0].utf8Bytes[0] = '\\';
+						memmove(TTY_con.buffer + 1, TTY_con.buffer, sizeof(TTY_con.buffer) - 1);
+						TTY_con.buffer[0] = '\\';
 						TTY_con.cursor++;
 					}
 
-					if (TTY_con.xbuffer[0].codePoint == '/' ||  TTY_con.xbuffer[0].codePoint == '\\') {
-						//Q_strncpyz(text, TTY_con.buffer + 1, sizeof(text));
-						fieldString = Field_AsStr(&TTY_con, 1, 0);
-						Q_strncpyz(text, fieldString, sizeof(text));
+					if (TTY_con.buffer[0] == '/' || TTY_con.buffer[0] == '\\') {
+						Q_strncpyz(text, TTY_con.buffer + 1, sizeof(text));
 					} else if (TTY_con.cursor) {
-						if (cl_consoleAsChat->integer) {
-							//Com_sprintf(text, sizeof(text), "cmd say %s", TTY_con.buffer);
-							Com_sprintf(text, sizeof(text), "cmd say %s", Field_AsStr(&TTY_con, 0, 0));
+						if (con_autochat->integer) {
+							Com_sprintf(text, sizeof(text), "cmd say %s", TTY_con.buffer);
 						} else {
-							fieldString = Field_AsStr(&TTY_con, 1, 0);
-							Q_strncpyz(text, fieldString, sizeof(text));
+							Q_strncpyz(text, TTY_con.buffer, sizeof(text));
 						}
 					} else {
 						text[0] = '\0';
@@ -450,16 +387,13 @@
 					// push it in history
 					Hist_Add(&TTY_con);
 					CON_Hide();
-					//Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, TTY_con.buffer);
-					Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, Field_AsStr(&TTY_con, 0, 0));
+					Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, TTY_con.buffer);
 					Field_Clear(&TTY_con);
 					CON_Show();
 #else
 					// push it in history
 					Hist_Add(&TTY_con);
-					//Q_strncpyz(text, TTY_con.buffer, sizeof(text));
-					fieldString = Field_AsStr(&TTY_con, 0, 0);
-					Q_strncpyz(text, fieldString, sizeof(text));
+					Q_strncpyz(text, TTY_con.buffer, sizeof(text));
 					Field_Clear(&TTY_con);
 					key = '\n';
 					size = write(STDOUT_FILENO, &key, 1);
@@ -524,44 +458,9 @@
 			}
 			if (TTY_con.cursor >= sizeof(text) - 1)
 				return NULL;
-
-
-			// push regular character and/or check of UTF-8
-
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[1] = '\0';
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[2] = '\0';
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[3] = '\0';
-
-			TTY_con.xbuffer[TTY_con.cursor].codePoint = key;
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[0] = key;
-			TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 1;
-
-			ukey = key;
-
-			// UTF-8 check
-			if (ukey <= 0x7f) {
-				// 1 byte UTF-8, all set
-			} else if ((ukey & 0xe0) == 0xc0) {  // 2 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 2;
-				needUtf8Bytes = 1;
-				return NULL;
-			} else if ((ukey & 0xf0) == 0xe0) {  // 3 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 3;
-				needUtf8Bytes = 2;
-				return NULL;
-			} else if ((ukey & 0xf8) == 0xf0) {  // 4 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 4;
-				needUtf8Bytes = 3;
-				return NULL;
-			} else {
-				Com_Printf(S_COLOR_YELLOW "CON_Input() invalid byte: %x\n", (unsigned int)ukey);
-				return NULL;
-			}
-
-			// UTF-8 1 byte
-			needUtf8Bytes = 0;
-
-			TTY_con.cursor++; // next char will always be '\0';
+			// push regular character
+			TTY_con.buffer[TTY_con.cursor] = key;
+			TTY_con.cursor++; // next char will always be '\0'
 			// print the current line (this is differential)
 			size = write(STDOUT_FILENO, &key, 1);
 		}
@@ -607,19 +506,13 @@
 	if (!msg[0])
 		return;
 
-	if (!ConsoleIsPassive) {
-		CON_Hide( );
-	}
+	CON_Hide( );
 
 	if( com_ansiColor && com_ansiColor->integer )
 		Sys_AnsiColorPrint( msg );
 	else
 		fputs( msg, stderr );
 
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	if (!ttycon_on) {
 		// CON_Hide didn't do anything.
 		return;

```

### `openarena-engine`  — sha256 `d4d14af9cb26...`, 12404 bytes

_Diff stat: +35 / -132 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\con_tty.c	2026-04-16 20:02:25.276294700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\con_tty.c	2026-04-16 22:48:25.938962600 +0100
@@ -44,8 +44,6 @@
 =============================================================
 */
 
-extern qboolean ConsoleIsPassive;
-
 extern qboolean stdinIsATTY;
 static qboolean stdin_active;
 // general flag to tell about tty console mode
@@ -77,6 +75,20 @@
 
 /*
 ==================
+CON_FlushIn
+
+Flush stdin, I suspect some terminals are sending a LOT of shit
+FIXME relevant?
+==================
+*/
+static void CON_FlushIn( void )
+{
+	char key;
+	while (read(STDIN_FILENO, &key, 1)!=-1);
+}
+
+/*
+==================
 CON_Back
 
 Output a backspace
@@ -89,7 +101,7 @@
 static void CON_Back( void )
 {
 	char key;
-	size_t Q_UNUSED_VAR size;
+	size_t UNUSED_VAR size;
 
 	key = '\b';
 	size = write(STDOUT_FILENO, &key, 1);
@@ -150,17 +162,13 @@
 		ttycon_hide--;
 		if (ttycon_hide == 0)
 		{
-			size_t Q_UNUSED_VAR size;
+			size_t UNUSED_VAR size;
 			size = write(STDOUT_FILENO, TTY_CONSOLE_PROMPT, strlen(TTY_CONSOLE_PROMPT));
 			if (TTY_con.cursor)
 			{
 				for (i=0; i<TTY_con.cursor; i++)
 				{
-					int n;
-					//size = write(STDOUT_FILENO, TTY_con.buffer+i, 1);
-					for (n = 0;  n < TTY_con.xbuffer[i].numUtf8Bytes;  n++) {
-						size = write(STDOUT_FILENO, &TTY_con.xbuffer[i].utf8Bytes[n], 1);
-					}
+					size = write(STDOUT_FILENO, TTY_con.buffer+i, 1);
 				}
 			}
 		}
@@ -176,10 +184,6 @@
 */
 void CON_Shutdown( void )
 {
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	if (ttycon_on)
 	{
 		CON_Hide();
@@ -287,10 +291,6 @@
 {
 	struct termios tc;
 
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	// If the process is backgrounded (running non interactively)
 	// then SIGTTIN or SIGTOU is emitted, if not caught, turns into a SIGSTP
 	signal(SIGTTIN, SIG_IGN);
@@ -350,50 +350,14 @@
 	static char text[MAX_EDIT_LINE];
 	int avail;
 	char key;
-	unsigned char ukey;
 	field_t *history;
-	size_t Q_UNUSED_VAR size;
-	int i;
-	static int needUtf8Bytes = 0;
-
-	if (ConsoleIsPassive) {
-		return NULL;
-	}
+	size_t UNUSED_VAR size;
 
 	if(ttycon_on)
 	{
 		avail = read(STDIN_FILENO, &key, 1);
 		if (avail != -1)
 		{
-			//printf("key... %d  '%d'\n", (unsigned char)key & 0xff, key);
-
-			if (needUtf8Bytes > 0) {
-				for (i = 1;  i < 4;  i++) {
-					if (TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[i] == '\0') {
-						TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[i] = key;
-						needUtf8Bytes--;
-						break;
-					}
-				}
-
-				if (needUtf8Bytes <= 0) {
-					// got it
-
-					{
-						int nbytes;
-						qboolean uerror;
-
-						TTY_con.xbuffer[TTY_con.cursor].codePoint = Q_GetCpFromUtf8(TTY_con.xbuffer[TTY_con.cursor].utf8Bytes, &nbytes, &uerror);
-					}
-
-					// print the current line (this is differential)
-					size = write(STDOUT_FILENO, TTY_con.xbuffer[TTY_con.cursor].utf8Bytes, TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes);
-					TTY_con.cursor++; // next char will always be '\0';
-				}
-
-				return NULL;
-			}
-
 			// we have something
 			// backspace?
 			// NOTE TTimo testing a lot of values .. seems it's the only way to get it to work everywhere
@@ -402,47 +366,30 @@
 				if (TTY_con.cursor > 0)
 				{
 					TTY_con.cursor--;
-					//TTY_con.buffer[TTY_con.cursor] = '\0';
-					TTY_con.xbuffer[TTY_con.cursor].codePoint = '\0';
-					TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 1;
-					TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[0] = '\0';
+					TTY_con.buffer[TTY_con.cursor] = '\0';
 					CON_Back();
 				}
 				return NULL;
 			}
 			// check if this is a control char
-			if ((key) && (key) < ' ' &&  key > '\0')
+			if ((key) && (key) < ' ')
 			{
-				//printf("control char xxxxx\n");
-
 				if (key == '\n')
 				{
-					const char *fieldString;
-
 #ifndef DEDICATED
 					// if not in the game explicitly prepend a slash if needed
 					if (clc.state != CA_ACTIVE && TTY_con.cursor &&
-						TTY_con.xbuffer[0].codePoint != '/' && TTY_con.xbuffer[0].codePoint != '\\')
+						TTY_con.buffer[0] != '/' && TTY_con.buffer[0] != '\\')
 					{
-						memmove(TTY_con.xbuffer + 1, TTY_con.xbuffer, sizeof(TTY_con.xbuffer) - (1 * sizeof(fieldChar_t)));
-						TTY_con.xbuffer[0].codePoint = '\\';
-						TTY_con.xbuffer[0].numUtf8Bytes = 1;
-						TTY_con.xbuffer[0].utf8Bytes[0] = '\\';
+						memmove(TTY_con.buffer + 1, TTY_con.buffer, sizeof(TTY_con.buffer) - 1);
+						TTY_con.buffer[0] = '\\';
 						TTY_con.cursor++;
 					}
 
-					if (TTY_con.xbuffer[0].codePoint == '/' ||  TTY_con.xbuffer[0].codePoint == '\\') {
-						//Q_strncpyz(text, TTY_con.buffer + 1, sizeof(text));
-						fieldString = Field_AsStr(&TTY_con, 1, 0);
-						Q_strncpyz(text, fieldString, sizeof(text));
+					if (TTY_con.buffer[0] == '/' || TTY_con.buffer[0] == '\\') {
+						Q_strncpyz(text, TTY_con.buffer + 1, sizeof(text));
 					} else if (TTY_con.cursor) {
-						if (cl_consoleAsChat->integer) {
-							//Com_sprintf(text, sizeof(text), "cmd say %s", TTY_con.buffer);
-							Com_sprintf(text, sizeof(text), "cmd say %s", Field_AsStr(&TTY_con, 0, 0));
-						} else {
-							fieldString = Field_AsStr(&TTY_con, 1, 0);
-							Q_strncpyz(text, fieldString, sizeof(text));
-						}
+						Com_sprintf(text, sizeof(text), "cmd say %s", TTY_con.buffer);
 					} else {
 						text[0] = '\0';
 					}
@@ -450,16 +397,13 @@
 					// push it in history
 					Hist_Add(&TTY_con);
 					CON_Hide();
-					//Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, TTY_con.buffer);
-					Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, Field_AsStr(&TTY_con, 0, 0));
+					Com_Printf("%s%s\n", TTY_CONSOLE_PROMPT, TTY_con.buffer);
 					Field_Clear(&TTY_con);
 					CON_Show();
 #else
 					// push it in history
 					Hist_Add(&TTY_con);
-					//Q_strncpyz(text, TTY_con.buffer, sizeof(text));
-					fieldString = Field_AsStr(&TTY_con, 0, 0);
-					Q_strncpyz(text, fieldString, sizeof(text));
+					Q_strncpyz(text, TTY_con.buffer, sizeof(text));
 					Field_Clear(&TTY_con);
 					key = '\n';
 					size = write(STDOUT_FILENO, &key, 1);
@@ -493,7 +437,7 @@
 										TTY_con = *history;
 										CON_Show();
 									}
-									tcflush(STDIN_FILENO, TCIFLUSH);
+									CON_FlushIn();
 									return NULL;
 									break;
 								case 'B':
@@ -507,7 +451,7 @@
 										Field_Clear(&TTY_con);
 									}
 									CON_Show();
-									tcflush(STDIN_FILENO, TCIFLUSH);
+									CON_FlushIn();
 									return NULL;
 									break;
 								case 'C':
@@ -519,49 +463,14 @@
 					}
 				}
 				Com_DPrintf("droping ISCTL sequence: %d, TTY_erase: %d\n", key, TTY_erase);
-				tcflush(STDIN_FILENO, TCIFLUSH);
+				CON_FlushIn();
 				return NULL;
 			}
 			if (TTY_con.cursor >= sizeof(text) - 1)
 				return NULL;
-
-
-			// push regular character and/or check of UTF-8
-
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[1] = '\0';
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[2] = '\0';
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[3] = '\0';
-
-			TTY_con.xbuffer[TTY_con.cursor].codePoint = key;
-			TTY_con.xbuffer[TTY_con.cursor].utf8Bytes[0] = key;
-			TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 1;
-
-			ukey = key;
-
-			// UTF-8 check
-			if (ukey <= 0x7f) {
-				// 1 byte UTF-8, all set
-			} else if ((ukey & 0xe0) == 0xc0) {  // 2 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 2;
-				needUtf8Bytes = 1;
-				return NULL;
-			} else if ((ukey & 0xf0) == 0xe0) {  // 3 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 3;
-				needUtf8Bytes = 2;
-				return NULL;
-			} else if ((ukey & 0xf8) == 0xf0) {  // 4 bytes
-				TTY_con.xbuffer[TTY_con.cursor].numUtf8Bytes = 4;
-				needUtf8Bytes = 3;
-				return NULL;
-			} else {
-				Com_Printf(S_COLOR_YELLOW "CON_Input() invalid byte: %x\n", (unsigned int)ukey);
-				return NULL;
-			}
-
-			// UTF-8 1 byte
-			needUtf8Bytes = 0;
-
-			TTY_con.cursor++; // next char will always be '\0';
+			// push regular character
+			TTY_con.buffer[TTY_con.cursor] = key;
+			TTY_con.cursor++; // next char will always be '\0'
 			// print the current line (this is differential)
 			size = write(STDOUT_FILENO, &key, 1);
 		}
@@ -607,19 +516,13 @@
 	if (!msg[0])
 		return;
 
-	if (!ConsoleIsPassive) {
-		CON_Hide( );
-	}
+	CON_Hide( );
 
 	if( com_ansiColor && com_ansiColor->integer )
 		Sys_AnsiColorPrint( msg );
 	else
 		fputs( msg, stderr );
 
-	if (ConsoleIsPassive) {
-		return;
-	}
-
 	if (!ttycon_on) {
 		// CON_Hide didn't do anything.
 		return;

```
