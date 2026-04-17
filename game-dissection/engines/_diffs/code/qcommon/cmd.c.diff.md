# Diff: `code/qcommon/cmd.c`
**Canonical:** `wolfcamql-src` (sha256 `1c09fc257a5f...`, 28278 bytes)

## Variants

### `quake3-source`  — sha256 `43e3b1ba3e17...`, 14447 bytes

_Diff stat: +47 / -672 lines_

_(full diff is 21267 bytes — see files directly)_

### `ioquake3`  — sha256 `df9d409a8be9...`, 18372 bytes

_Diff stat: +49 / -518 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cmd.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\cmd.c	2026-04-16 20:02:21.566111000 +0100
@@ -24,8 +24,8 @@
 #include "q_shared.h"
 #include "qcommon.h"
 
-#define	MAX_CMD_BUFFER	(16384 * 10)
-#define	MAX_CMD_LINE	(1024 * 10)
+#define	MAX_CMD_BUFFER  128*1024
+#define	MAX_CMD_LINE	1024
 
 typedef struct {
 	byte	*data;
@@ -38,11 +38,6 @@
 byte		cmd_text_buf[MAX_CMD_BUFFER];
 
 
-#define MAX_ALIASES 256
-static alias_t cmd_aliases[MAX_ALIASES];
-static int numAliases = 0;
-
-
 //=============================================================================
 
 /*
@@ -152,7 +147,6 @@
 	case EXEC_NOW:
 		if (text && strlen(text) > 0) {
 			Com_DPrintf(S_COLOR_YELLOW "EXEC_NOW %s\n", text);
-			//Com_Printf("^1execing now '%s'\n", text);
 			Cmd_ExecuteString (text);
 		} else {
 			Cbuf_Execute();
@@ -181,9 +175,12 @@
 	char	*text;
 	char	line[MAX_CMD_LINE];
 	int		quotes;
-	qboolean cComment;
-	qboolean slashComment;
 
+	// This will keep // style comments all on one line by not breaking on
+	// a semicolon.  It will keep /* ... */ style comments all on one line by not
+	// breaking it for semicolon or newline.
+	qboolean in_star_comment = qfalse;
+	qboolean in_slash_comment = qfalse;
 	while (cmd_text.cursize)
 	{
 		if ( cmd_wait > 0 ) {
@@ -193,49 +190,37 @@
 			break;
 		}
 
-		// find a \n or ; line break
+		// find a \n or ; line break or comment: // or /* */
 		text = (char *)cmd_text.data;
 
-		cComment = qfalse;
-		slashComment = qfalse;
 		quotes = 0;
 		for (i=0 ; i< cmd_text.cursize ; i++)
 		{
-			if (cComment) {
-				if (text[i - 1] == '*'  &&  text[i] == '/') {
-					break;
-				} else {
-					continue;
-				}
-			}
-
-			if (slashComment) {
-				if (text[i] == '\0'  ||  text[i] == '\n'  ||  text[i] == '\r') {
-					break;
-				} else {
-					continue;
-				}
-			}
-
-			if (i > 0) {
-				if (text[i - 1] == '/'  &&  text[i] == '*') {
-					cComment = qtrue;
-					continue;
-				}
-				if (text[i - 1] == '/'  &&  text[i] == '/') {
-					slashComment = qtrue;
-					continue;
-				}
-			}
-
 			if (text[i] == '"')
 				quotes++;
-			if ( !(quotes&1) &&  text[i] == ';') {
-				//Com_Printf("breaking...\n");
-				break;	// don't break if inside a quoted string
+
+			if ( !(quotes&1)) {
+				if (i < cmd_text.cursize - 1) {
+					if (! in_star_comment && text[i] == '/' && text[i+1] == '/')
+						in_slash_comment = qtrue;
+					else if (! in_slash_comment && text[i] == '/' && text[i+1] == '*')
+						in_star_comment = qtrue;
+					else if (in_star_comment && text[i] == '*' && text[i+1] == '/') {
+						in_star_comment = qfalse;
+						// If we are in a star comment, then the part after it is valid
+						// Note: This will cause it to NUL out the terminating '/'
+						// but ExecuteString doesn't require it anyway.
+						i++;
+						break;
+					}
+				}
+				if (! in_slash_comment && ! in_star_comment && text[i] == ';')
+					break;
 			}
-			if (text[i] == '\n' || text[i] == '\r' )
+			if (! in_star_comment && (text[i] == '\n' || text[i] == '\r')) {
+				in_slash_comment = qfalse;
 				break;
+			}
 		}
 
 		if( i >= (MAX_CMD_LINE - 1)) {
@@ -260,7 +245,7 @@
 
 // execute the command line
 
-		Cmd_ExecuteString (line);
+		Cmd_ExecuteString (line);		
 	}
 }
 
@@ -279,8 +264,6 @@
 Cmd_Exec_f
 ===============
 */
-//static qboolean ExecNowDamnIt = qfalse;
-
 void Cmd_Exec_f( void ) {
 	qboolean quiet;
 	union {
@@ -292,7 +275,8 @@
 	quiet = !Q_stricmp(Cmd_Argv(0), "execq");
 
 	if (Cmd_Argc () != 2) {
-		Com_Printf ("exec%s <filename> : execute a script file%s\n", quiet ? "q" : "", quiet ? " without notification" : "");
+		Com_Printf ("exec%s <filename> : execute a script file%s\n",
+		            quiet ? "q" : "", quiet ? " without notification" : "");
 		return;
 	}
 
@@ -300,38 +284,17 @@
 	COM_DefaultExtension( filename, sizeof( filename ), ".cfg" );
 	FS_ReadFile( filename, &f.v);
 	if (!f.c) {
-		if ((!com_cl_running  ||  !com_sv_running)  ||  (com_execVerbose  &&  com_execVerbose->integer)) {
-			if (!quiet) {
-				Com_Printf("couldn't exec %s\n", filename);
-			}
-		}
+		Com_Printf ("couldn't exec %s\n", filename);
 		return;
 	}
-
-	if ((!com_cl_running  ||  !com_sv_running)  ||  (com_execVerbose  &&  com_execVerbose->integer)) {
-		if (!quiet) {
-			Com_Printf ("execing %s\n", filename);
-		}
-	}
-
-	if (0) {  //(ExecNowDamnIt) {
-		Cbuf_ExecuteText(EXEC_NOW, f.c);
-	} else {
-		Cbuf_InsertText (f.c);
-	}
+	if (!quiet)
+		Com_Printf ("execing %s\n", filename);
+	
+	Cbuf_InsertText (f.c);
 
 	FS_FreeFile (f.v);
 }
 
-#if 0
-void Cmd_ExecNow_f (void)
-{
-	ExecNowDamnIt = qtrue;
-	Cmd_Exec_f();
-	ExecNowDamnIt = qfalse;
-}
-#endif
-
 
 /*
 ===============
@@ -352,408 +315,6 @@
 	Cbuf_InsertText( va("%s\n", v ) );
 }
 
-void Cmd_Ifeq_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifeq <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval == v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifneq_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifneq <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval != v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgt_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgt <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval > v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgte_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgte <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval >= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Iflt_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: iflt <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval < v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Iflte_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: iflte <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval <= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifeqf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifeqf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval == v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifneqf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifneqf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval != v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgtf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgtf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval > v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgtef_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgtef <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval >= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifltf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifltf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval < v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifltef_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifltef <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval <= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-static void Cmd_AliasExec_f (void)
-{
-	int i;
-	const char *arg;
-
-	arg = Cmd_Argv(0);
-
-	for (i = 0;  i < numAliases;  i++) {
-		if (!Q_stricmp(arg, cmd_aliases[i].name)) {
-			Cbuf_InsertText(va("%s\n", cmd_aliases[i].command));
-			break;
-		}
-	}
-}
-
-static void Cmd_Alias_f (void)
-{
-	int i;
-
-	if (Cmd_Argc() == 1) {
-		Com_Printf("Usage: alias \"command\"\n");
-		Com_Printf("Alias List:\n");
-
-		for (i = 0;  i < numAliases;  i++) {
-			Com_Printf("  %s \"%s\"\n", cmd_aliases[i].name, cmd_aliases[i].command);
-		}
-
-		return;
-	}
-
-	if (Cmd_Argc() == 2) {
-		return;
-	}
-
-	//FIXME hash and CopyString()
-
-	for (i = 0;  i < numAliases;  i++) {
-		if (!Q_stricmp(Cmd_Argv(1), cmd_aliases[i].name)) {
-			Q_strncpyz(cmd_aliases[i].command, Cmd_Argv(2), sizeof(cmd_aliases[i].command));
-			return;
-		}
-	}
-
-	if (numAliases >= MAX_ALIASES) {
-		Com_Printf("^1maximum number of aliases %d\n", MAX_ALIASES);
-		return;
-	}
-
-	Q_strncpyz(cmd_aliases[numAliases].name, Cmd_Argv(1), sizeof(cmd_aliases[numAliases].name));
-	Q_strncpyz(cmd_aliases[numAliases].command, Cmd_Argv(2), sizeof(cmd_aliases[numAliases].command));
-	numAliases++;
-
-	Cmd_AddCommand(Cmd_Argv(1), Cmd_AliasExec_f);
-}
-
-static void Cmd_Unalias_f (void)
-{
-	int i, j;
-	alias_t *a;
-
-	if (Cmd_Argc() == 1) {
-		Com_Printf("usage: unalias \"command\"\n");
-		Com_Printf("alias list:\n");
-
-		for (i = 0;  i < numAliases;  i++) {
-			Com_Printf("  %s \"%s\"\n", cmd_aliases[i].name, cmd_aliases[i].command);
-		}
-
-		return;
-	}
-
-	for (i = 0;  i < numAliases;  i++) {
-		a = &cmd_aliases[i];
-
-		if (!Q_stricmp(Cmd_Argv(1), a->name)) {
-			Cmd_RemoveCommand(a->name);
-			for (j = i + 1;  j < numAliases;  j++) {
-				memcpy(&cmd_aliases[j - 1], &cmd_aliases[j], sizeof(cmd_aliases[j - 1]));
-			}
-
-			numAliases--;
-			return;
-		}
-	}
-}
-
-static void Cmd_Unaliasall_f (void)
-{
-	int i;
-
-	for (i = 0;  i < numAliases;  i++) {
-		Cmd_RemoveCommand(cmd_aliases[i].name);
-	}
-
-	numAliases = 0;
-}
-
-static void Cmd_CompleteAliasName (char *args, int argNum)
-{
-	const char *name;
-	int i;
-
-	name = args + 7;
-
-	//FIXME only one match doesn't print in quake live
-	if (argNum == 2) {
-		for (i = 0;  i < numAliases;  i++) {
-			if (!Q_stricmpn(name, cmd_aliases[i].name, strlen(name))) {
-				Com_Printf("     %s\n", cmd_aliases[i].name);
-			}
-		}
-	}
-}
-
 
 /*
 ===============
@@ -810,7 +371,7 @@
 	if ( (unsigned)arg >= cmd_argc ) {
 		return "";
 	}
-	return cmd_argv[arg];
+	return cmd_argv[arg];	
 }
 
 /*
@@ -912,10 +473,10 @@
 	for(i = 1; i < cmd_argc; i++)
 	{
 		char *c = cmd_argv[i];
-
+		
 		if(strlen(c) > MAX_CVAR_VALUE_STRING - 1)
 			c[MAX_CVAR_VALUE_STRING - 1] = '\0';
-
+		
 		while ((c = strpbrk(c, "\n\r;"))) {
 			*c = ' ';
 			++c;
@@ -936,16 +497,14 @@
 // NOTE TTimo define that to track tokenization issues
 //#define TKN_DBG
 static void Cmd_TokenizeString2( const char *text_in, qboolean ignoreQuotes ) {
-	const unsigned char *text;
-	unsigned char *textOut;
+	const char	*text;
+	char	*textOut;
 
 #ifdef TKN_DBG
   // FIXME TTimo blunt hook to try to find the tokenization of userinfo
   Com_DPrintf("Cmd_TokenizeString: %s\n", text_in);
 #endif
 
-  //Com_Printf("string:  '%s'\n", text_in);
-
 	// clear previous args
 	cmd_argc = 0;
 
@@ -955,8 +514,8 @@
 	
 	Q_strncpyz( cmd_cmd, text_in, sizeof(cmd_cmd) );
 
-	text = (unsigned char *)text_in;
-	textOut = (unsigned char *)cmd_tokenized;
+	text = text_in;
+	textOut = cmd_tokenized;
 
 	while ( 1 ) {
 		if ( cmd_argc == MAX_STRING_TOKENS ) {
@@ -974,15 +533,6 @@
 
 			// skip // comments
 			if ( text[0] == '/' && text[1] == '/' ) {
-				while (*text) {
-					if (text[0] == '\n'  ||  text[0] == '\r') {
-						break;
-					}
-					text++;
-				}
-				if (!*text) {
-					return;
-				}
 				return;			// all tokens parsed
 			}
 
@@ -1003,7 +553,7 @@
 		// handle quoted strings
     // NOTE TTimo this doesn't handle \" escaping
 		if ( !ignoreQuotes && *text == '"' ) {
-			cmd_argv[cmd_argc] = (char *)textOut;
+			cmd_argv[cmd_argc] = textOut;
 			cmd_argc++;
 			text++;
 			while ( *text && *text != '"' ) {
@@ -1018,7 +568,7 @@
 		}
 
 		// regular token
-		cmd_argv[cmd_argc] = (char *)textOut;
+		cmd_argv[cmd_argc] = textOut;
 		cmd_argc++;
 
 		// skip until whitespace, quote, or command
@@ -1163,7 +713,7 @@
 	if( cmd->function )
 	{
 		Com_Error( ERR_DROP, "Restricted source tried to remove "
-				   "system command \"%s\"", cmd_name );
+			"system command \"%s\"", cmd_name );
 		return;
 	}
 
@@ -1235,7 +785,6 @@
 			} else {
 				cmd->function ();
 			}
-			//Com_Printf("^1did function '%s'\n", cmd->name);
 			return;
 		}
 	}
@@ -1245,7 +794,6 @@
 		return;
 	}
 
-	//Com_Printf("^1yes\n");
 	// check client game commands
 	if ( com_cl_running && com_cl_running->integer && CL_GameCommand() ) {
 		return;
@@ -1300,7 +848,7 @@
 */
 void Cmd_CompleteCfgName( char *args, int argNum ) {
 	if( argNum == 2 ) {
-		Field_CompleteFilename( "", "cfg", NULL, qfalse, qtrue, NULL );
+		Field_CompleteFilename( "", "cfg", NULL, qfalse, qtrue );
 	}
 }
 
@@ -1312,29 +860,12 @@
 void Cmd_Init (void) {
 	Cmd_AddCommand ("cmdlist",Cmd_List_f);
 	Cmd_AddCommand ("exec",Cmd_Exec_f);
-	Cmd_SetCommandCompletionFunc( "exec", Cmd_CompleteCfgName );
 	Cmd_AddCommand ("execq",Cmd_Exec_f);
+	Cmd_SetCommandCompletionFunc( "exec", Cmd_CompleteCfgName );
 	Cmd_SetCommandCompletionFunc( "execq", Cmd_CompleteCfgName );
 	Cmd_AddCommand ("vstr",Cmd_Vstr_f);
 	Cmd_SetCommandCompletionFunc( "vstr", Cvar_CompleteCvarName );
-	Cmd_AddCommand("alias", Cmd_Alias_f);
-	Cmd_SetCommandCompletionFunc("alias", Cmd_CompleteAliasName);
-	Cmd_AddCommand("unalias", Cmd_Unalias_f);
-	Cmd_AddCommand("unaliasall", Cmd_Unaliasall_f);
 	Cmd_AddCommand ("echo",Cmd_Echo_f);
 	Cmd_AddCommand ("wait", Cmd_Wait_f);
-	Cmd_AddCommand("ifeq", Cmd_Ifeq_f);
-	Cmd_AddCommand("ifneq", Cmd_Ifneq_f);
-	Cmd_AddCommand("ifgt", Cmd_Ifgt_f);
-	Cmd_AddCommand("ifgte", Cmd_Ifgte_f);
-	Cmd_AddCommand("iflt", Cmd_Iflt_f);
-	Cmd_AddCommand("iflte", Cmd_Iflte_f);
-
-	Cmd_AddCommand("ifeqf", Cmd_Ifeqf_f);
-	Cmd_AddCommand("ifneqf", Cmd_Ifneqf_f);
-	Cmd_AddCommand("ifgtf", Cmd_Ifgtf_f);
-	Cmd_AddCommand("ifgtef", Cmd_Ifgtef_f);
-	Cmd_AddCommand("ifltf", Cmd_Ifltf_f);
-	Cmd_AddCommand("ifltef", Cmd_Ifltef_f);
 }
 

```

### `quake3e`  — sha256 `b13187e82848...`, 22236 bytes

_Diff stat: +370 / -663 lines_

_(full diff is 34458 bytes — see files directly)_

### `openarena-engine`  — sha256 `ad6570891e14...`, 18351 bytes

_Diff stat: +56 / -527 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cmd.c	2026-04-16 20:02:25.219162800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cmd.c	2026-04-16 22:48:25.906297600 +0100
@@ -24,8 +24,8 @@
 #include "q_shared.h"
 #include "qcommon.h"
 
-#define	MAX_CMD_BUFFER	(16384 * 10)
-#define	MAX_CMD_LINE	(1024 * 10)
+#define	MAX_CMD_BUFFER  128*1024
+#define	MAX_CMD_LINE	1024
 
 typedef struct {
 	byte	*data;
@@ -38,11 +38,6 @@
 byte		cmd_text_buf[MAX_CMD_BUFFER];
 
 
-#define MAX_ALIASES 256
-static alias_t cmd_aliases[MAX_ALIASES];
-static int numAliases = 0;
-
-
 //=============================================================================
 
 /*
@@ -152,7 +147,6 @@
 	case EXEC_NOW:
 		if (text && strlen(text) > 0) {
 			Com_DPrintf(S_COLOR_YELLOW "EXEC_NOW %s\n", text);
-			//Com_Printf("^1execing now '%s'\n", text);
 			Cmd_ExecuteString (text);
 		} else {
 			Cbuf_Execute();
@@ -181,9 +175,12 @@
 	char	*text;
 	char	line[MAX_CMD_LINE];
 	int		quotes;
-	qboolean cComment;
-	qboolean slashComment;
 
+	// This will keep // style comments all on one line by not breaking on
+	// a semicolon.  It will keep /* ... */ style comments all on one line by not
+	// breaking it for semicolon or newline.
+	qboolean in_star_comment = qfalse;
+	qboolean in_slash_comment = qfalse;
 	while (cmd_text.cursize)
 	{
 		if ( cmd_wait > 0 ) {
@@ -193,49 +190,37 @@
 			break;
 		}
 
-		// find a \n or ; line break
+		// find a \n or ; line break or comment: // or /* */
 		text = (char *)cmd_text.data;
 
-		cComment = qfalse;
-		slashComment = qfalse;
 		quotes = 0;
 		for (i=0 ; i< cmd_text.cursize ; i++)
 		{
-			if (cComment) {
-				if (text[i - 1] == '*'  &&  text[i] == '/') {
-					break;
-				} else {
-					continue;
-				}
-			}
-
-			if (slashComment) {
-				if (text[i] == '\0'  ||  text[i] == '\n'  ||  text[i] == '\r') {
-					break;
-				} else {
-					continue;
-				}
-			}
-
-			if (i > 0) {
-				if (text[i - 1] == '/'  &&  text[i] == '*') {
-					cComment = qtrue;
-					continue;
-				}
-				if (text[i - 1] == '/'  &&  text[i] == '/') {
-					slashComment = qtrue;
-					continue;
-				}
-			}
-
 			if (text[i] == '"')
 				quotes++;
-			if ( !(quotes&1) &&  text[i] == ';') {
-				//Com_Printf("breaking...\n");
-				break;	// don't break if inside a quoted string
+
+			if ( !(quotes&1)) {
+				if (i < cmd_text.cursize - 1) {
+					if (! in_star_comment && text[i] == '/' && text[i+1] == '/')
+						in_slash_comment = qtrue;
+					else if (! in_slash_comment && text[i] == '/' && text[i+1] == '*')
+						in_star_comment = qtrue;
+					else if (in_star_comment && text[i] == '*' && text[i+1] == '/') {
+						in_star_comment = qfalse;
+						// If we are in a star comment, then the part after it is valid
+						// Note: This will cause it to NUL out the terminating '/'
+						// but ExecuteString doesn't require it anyway.
+						i++;
+						break;
+					}
+				}
+				if (! in_slash_comment && ! in_star_comment && text[i] == ';')
+					break;
 			}
-			if (text[i] == '\n' || text[i] == '\r' )
+			if (! in_star_comment && (text[i] == '\n' || text[i] == '\r')) {
+				in_slash_comment = qfalse;
 				break;
+			}
 		}
 
 		if( i >= (MAX_CMD_LINE - 1)) {
@@ -260,7 +245,7 @@
 
 // execute the command line
 
-		Cmd_ExecuteString (line);
+		Cmd_ExecuteString (line);		
 	}
 }
 
@@ -279,8 +264,6 @@
 Cmd_Exec_f
 ===============
 */
-//static qboolean ExecNowDamnIt = qfalse;
-
 void Cmd_Exec_f( void ) {
 	qboolean quiet;
 	union {
@@ -292,7 +275,8 @@
 	quiet = !Q_stricmp(Cmd_Argv(0), "execq");
 
 	if (Cmd_Argc () != 2) {
-		Com_Printf ("exec%s <filename> : execute a script file%s\n", quiet ? "q" : "", quiet ? " without notification" : "");
+		Com_Printf ("exec%s <filename> : execute a script file%s\n",
+		            quiet ? "q" : "", quiet ? " without notification" : "");
 		return;
 	}
 
@@ -300,38 +284,17 @@
 	COM_DefaultExtension( filename, sizeof( filename ), ".cfg" );
 	FS_ReadFile( filename, &f.v);
 	if (!f.c) {
-		if ((!com_cl_running  ||  !com_sv_running)  ||  (com_execVerbose  &&  com_execVerbose->integer)) {
-			if (!quiet) {
-				Com_Printf("couldn't exec %s\n", filename);
-			}
-		}
+		Com_Printf ("couldn't exec %s\n", filename);
 		return;
 	}
-
-	if ((!com_cl_running  ||  !com_sv_running)  ||  (com_execVerbose  &&  com_execVerbose->integer)) {
-		if (!quiet) {
-			Com_Printf ("execing %s\n", filename);
-		}
-	}
-
-	if (0) {  //(ExecNowDamnIt) {
-		Cbuf_ExecuteText(EXEC_NOW, f.c);
-	} else {
-		Cbuf_InsertText (f.c);
-	}
+	if (!quiet)
+		Com_Printf ("execing %s\n", filename);
+	
+	Cbuf_InsertText (f.c);
 
 	FS_FreeFile (f.v);
 }
 
-#if 0
-void Cmd_ExecNow_f (void)
-{
-	ExecNowDamnIt = qtrue;
-	Cmd_Exec_f();
-	ExecNowDamnIt = qfalse;
-}
-#endif
-
 
 /*
 ===============
@@ -352,408 +315,6 @@
 	Cbuf_InsertText( va("%s\n", v ) );
 }
 
-void Cmd_Ifeq_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifeq <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval == v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifneq_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifneq <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval != v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgt_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgt <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval > v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgte_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgte <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval >= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Iflt_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: iflt <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval < v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Iflte_f (void)
-{
-	int cval;
-	int v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: iflte <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableIntegerValue(Cmd_Argv(1));
-	v = atoi(Cmd_Argv(2));
-	if (cval <= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifeqf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifeqf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval == v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifneqf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifneqf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval != v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgtf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgtf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval > v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifgtef_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifgtef <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval >= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifltf_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifltf <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval < v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-void Cmd_Ifltef_f (void)
-{
-	float cval;
-	float v;
-	const char *s;
-
-	if (Cmd_Argc() < 4) {
-		Com_Printf("usage: ifltef <cvar> <value> <vstr to execute if true> [optional vstr to execute if false]\n");
-		return;
-	}
-
-	cval = Cvar_VariableValue(Cmd_Argv(1));
-	v = atof(Cmd_Argv(2));
-	if (cval <= v) {
-		s = Cvar_VariableString(Cmd_Argv(3));
-		Cbuf_InsertText(va("%s\n", s));
-	} else {
-		if (Cmd_Argc() >= 5) {
-			s = Cvar_VariableString(Cmd_Argv(4));
-			Cbuf_InsertText(va("%s\n", s));
-		}
-	}
-}
-
-static void Cmd_AliasExec_f (void)
-{
-	int i;
-	const char *arg;
-
-	arg = Cmd_Argv(0);
-
-	for (i = 0;  i < numAliases;  i++) {
-		if (!Q_stricmp(arg, cmd_aliases[i].name)) {
-			Cbuf_InsertText(va("%s\n", cmd_aliases[i].command));
-			break;
-		}
-	}
-}
-
-static void Cmd_Alias_f (void)
-{
-	int i;
-
-	if (Cmd_Argc() == 1) {
-		Com_Printf("Usage: alias \"command\"\n");
-		Com_Printf("Alias List:\n");
-
-		for (i = 0;  i < numAliases;  i++) {
-			Com_Printf("  %s \"%s\"\n", cmd_aliases[i].name, cmd_aliases[i].command);
-		}
-
-		return;
-	}
-
-	if (Cmd_Argc() == 2) {
-		return;
-	}
-
-	//FIXME hash and CopyString()
-
-	for (i = 0;  i < numAliases;  i++) {
-		if (!Q_stricmp(Cmd_Argv(1), cmd_aliases[i].name)) {
-			Q_strncpyz(cmd_aliases[i].command, Cmd_Argv(2), sizeof(cmd_aliases[i].command));
-			return;
-		}
-	}
-
-	if (numAliases >= MAX_ALIASES) {
-		Com_Printf("^1maximum number of aliases %d\n", MAX_ALIASES);
-		return;
-	}
-
-	Q_strncpyz(cmd_aliases[numAliases].name, Cmd_Argv(1), sizeof(cmd_aliases[numAliases].name));
-	Q_strncpyz(cmd_aliases[numAliases].command, Cmd_Argv(2), sizeof(cmd_aliases[numAliases].command));
-	numAliases++;
-
-	Cmd_AddCommand(Cmd_Argv(1), Cmd_AliasExec_f);
-}
-
-static void Cmd_Unalias_f (void)
-{
-	int i, j;
-	alias_t *a;
-
-	if (Cmd_Argc() == 1) {
-		Com_Printf("usage: unalias \"command\"\n");
-		Com_Printf("alias list:\n");
-
-		for (i = 0;  i < numAliases;  i++) {
-			Com_Printf("  %s \"%s\"\n", cmd_aliases[i].name, cmd_aliases[i].command);
-		}
-
-		return;
-	}
-
-	for (i = 0;  i < numAliases;  i++) {
-		a = &cmd_aliases[i];
-
-		if (!Q_stricmp(Cmd_Argv(1), a->name)) {
-			Cmd_RemoveCommand(a->name);
-			for (j = i + 1;  j < numAliases;  j++) {
-				memcpy(&cmd_aliases[j - 1], &cmd_aliases[j], sizeof(cmd_aliases[j - 1]));
-			}
-
-			numAliases--;
-			return;
-		}
-	}
-}
-
-static void Cmd_Unaliasall_f (void)
-{
-	int i;
-
-	for (i = 0;  i < numAliases;  i++) {
-		Cmd_RemoveCommand(cmd_aliases[i].name);
-	}
-
-	numAliases = 0;
-}
-
-static void Cmd_CompleteAliasName (char *args, int argNum)
-{
-	const char *name;
-	int i;
-
-	name = args + 7;
-
-	//FIXME only one match doesn't print in quake live
-	if (argNum == 2) {
-		for (i = 0;  i < numAliases;  i++) {
-			if (!Q_stricmpn(name, cmd_aliases[i].name, strlen(name))) {
-				Com_Printf("     %s\n", cmd_aliases[i].name);
-			}
-		}
-	}
-}
-
 
 /*
 ===============
@@ -810,7 +371,7 @@
 	if ( (unsigned)arg >= cmd_argc ) {
 		return "";
 	}
-	return cmd_argv[arg];
+	return cmd_argv[arg];	
 }
 
 /*
@@ -912,10 +473,10 @@
 	for(i = 1; i < cmd_argc; i++)
 	{
 		char *c = cmd_argv[i];
-
+		
 		if(strlen(c) > MAX_CVAR_VALUE_STRING - 1)
 			c[MAX_CVAR_VALUE_STRING - 1] = '\0';
-
+		
 		while ((c = strpbrk(c, "\n\r;"))) {
 			*c = ' ';
 			++c;
@@ -928,24 +489,22 @@
 Cmd_TokenizeString
 
 Parses the given string into command line tokens.
-The text is copied to a separate buffer and 0 characters
-are inserted in the appropriate place, The argv array
+The text is copied to a seperate buffer and 0 characters
+are inserted in the apropriate place, The argv array
 will point into this temporary buffer.
 ============
 */
 // NOTE TTimo define that to track tokenization issues
 //#define TKN_DBG
 static void Cmd_TokenizeString2( const char *text_in, qboolean ignoreQuotes ) {
-	const unsigned char *text;
-	unsigned char *textOut;
+	const char	*text;
+	char	*textOut;
 
 #ifdef TKN_DBG
   // FIXME TTimo blunt hook to try to find the tokenization of userinfo
   Com_DPrintf("Cmd_TokenizeString: %s\n", text_in);
 #endif
 
-  //Com_Printf("string:  '%s'\n", text_in);
-
 	// clear previous args
 	cmd_argc = 0;
 
@@ -955,8 +514,8 @@
 	
 	Q_strncpyz( cmd_cmd, text_in, sizeof(cmd_cmd) );
 
-	text = (unsigned char *)text_in;
-	textOut = (unsigned char *)cmd_tokenized;
+	text = text_in;
+	textOut = cmd_tokenized;
 
 	while ( 1 ) {
 		if ( cmd_argc == MAX_STRING_TOKENS ) {
@@ -974,15 +533,6 @@
 
 			// skip // comments
 			if ( text[0] == '/' && text[1] == '/' ) {
-				while (*text) {
-					if (text[0] == '\n'  ||  text[0] == '\r') {
-						break;
-					}
-					text++;
-				}
-				if (!*text) {
-					return;
-				}
 				return;			// all tokens parsed
 			}
 
@@ -1003,7 +553,7 @@
 		// handle quoted strings
     // NOTE TTimo this doesn't handle \" escaping
 		if ( !ignoreQuotes && *text == '"' ) {
-			cmd_argv[cmd_argc] = (char *)textOut;
+			cmd_argv[cmd_argc] = textOut;
 			cmd_argc++;
 			text++;
 			while ( *text && *text != '"' ) {
@@ -1018,7 +568,7 @@
 		}
 
 		// regular token
-		cmd_argv[cmd_argc] = (char *)textOut;
+		cmd_argv[cmd_argc] = textOut;
 		cmd_argc++;
 
 		// skip until whitespace, quote, or command
@@ -1117,7 +667,6 @@
 	for( cmd = cmd_functions; cmd; cmd = cmd->next ) {
 		if( !Q_stricmp( command, cmd->name ) ) {
 			cmd->complete = complete;
-			return;
 		}
 	}
 }
@@ -1139,7 +688,9 @@
 		}
 		if ( !strcmp( cmd_name, cmd->name ) ) {
 			*back = cmd->next;
-			Z_Free (cmd->name);
+			if (cmd->name) {
+				Z_Free(cmd->name);
+			}
 			Z_Free (cmd);
 			return;
 		}
@@ -1163,7 +714,7 @@
 	if( cmd->function )
 	{
 		Com_Error( ERR_DROP, "Restricted source tried to remove "
-				   "system command \"%s\"", cmd_name );
+			"system command \"%s\"", cmd_name );
 		return;
 	}
 
@@ -1192,11 +743,8 @@
 	cmd_function_t	*cmd;
 
 	for( cmd = cmd_functions; cmd; cmd = cmd->next ) {
-		if( !Q_stricmp( command, cmd->name ) ) {
-			if ( cmd->complete ) {
-				cmd->complete( args, argNum );
-			}
-			return;
+		if( !Q_stricmp( command, cmd->name ) && cmd->complete ) {
+			cmd->complete( args, argNum );
 		}
 	}
 }
@@ -1235,7 +783,6 @@
 			} else {
 				cmd->function ();
 			}
-			//Com_Printf("^1did function '%s'\n", cmd->name);
 			return;
 		}
 	}
@@ -1245,7 +792,6 @@
 		return;
 	}
 
-	//Com_Printf("^1yes\n");
 	// check client game commands
 	if ( com_cl_running && com_cl_running->integer && CL_GameCommand() ) {
 		return;
@@ -1300,7 +846,7 @@
 */
 void Cmd_CompleteCfgName( char *args, int argNum ) {
 	if( argNum == 2 ) {
-		Field_CompleteFilename( "", "cfg", NULL, qfalse, qtrue, NULL );
+		Field_CompleteFilename( "", "cfg", qfalse, qtrue );
 	}
 }
 
@@ -1312,29 +858,12 @@
 void Cmd_Init (void) {
 	Cmd_AddCommand ("cmdlist",Cmd_List_f);
 	Cmd_AddCommand ("exec",Cmd_Exec_f);
-	Cmd_SetCommandCompletionFunc( "exec", Cmd_CompleteCfgName );
 	Cmd_AddCommand ("execq",Cmd_Exec_f);
+	Cmd_SetCommandCompletionFunc( "exec", Cmd_CompleteCfgName );
 	Cmd_SetCommandCompletionFunc( "execq", Cmd_CompleteCfgName );
 	Cmd_AddCommand ("vstr",Cmd_Vstr_f);
 	Cmd_SetCommandCompletionFunc( "vstr", Cvar_CompleteCvarName );
-	Cmd_AddCommand("alias", Cmd_Alias_f);
-	Cmd_SetCommandCompletionFunc("alias", Cmd_CompleteAliasName);
-	Cmd_AddCommand("unalias", Cmd_Unalias_f);
-	Cmd_AddCommand("unaliasall", Cmd_Unaliasall_f);
 	Cmd_AddCommand ("echo",Cmd_Echo_f);
 	Cmd_AddCommand ("wait", Cmd_Wait_f);
-	Cmd_AddCommand("ifeq", Cmd_Ifeq_f);
-	Cmd_AddCommand("ifneq", Cmd_Ifneq_f);
-	Cmd_AddCommand("ifgt", Cmd_Ifgt_f);
-	Cmd_AddCommand("ifgte", Cmd_Ifgte_f);
-	Cmd_AddCommand("iflt", Cmd_Iflt_f);
-	Cmd_AddCommand("iflte", Cmd_Iflte_f);
-
-	Cmd_AddCommand("ifeqf", Cmd_Ifeqf_f);
-	Cmd_AddCommand("ifneqf", Cmd_Ifneqf_f);
-	Cmd_AddCommand("ifgtf", Cmd_Ifgtf_f);
-	Cmd_AddCommand("ifgtef", Cmd_Ifgtef_f);
-	Cmd_AddCommand("ifltf", Cmd_Ifltf_f);
-	Cmd_AddCommand("ifltef", Cmd_Ifltef_f);
 }
 

```
