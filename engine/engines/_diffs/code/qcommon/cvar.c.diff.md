# Diff: `code/qcommon/cvar.c`
**Canonical:** `wolfcamql-src` (sha256 `b4fe423a0a7d...`, 36580 bytes)

## Variants

### `quake3-source`  — sha256 `4004a29a16f6...`, 19209 bytes

_Diff stat: +202 / -967 lines_

_(full diff is 37418 bytes — see files directly)_

### `ioquake3`  — sha256 `5383d98cba42...`, 30965 bytes

_Diff stat: +31 / -238 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cvar.c	2026-04-16 20:02:25.221161200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\cvar.c	2026-04-16 20:02:21.567107200 +0100
@@ -28,7 +28,7 @@
 cvar_t		*cvar_cheats;
 int			cvar_modifiedFlags;
 
-#define	MAX_CVARS	1024  * 8  // * 8 // 1024
+#define	MAX_CVARS	2048
 cvar_t		cvar_indexes[MAX_CVARS];
 int			cvar_numIndexes;
 
@@ -82,28 +82,7 @@
 Cvar_FindVar
 ============
 */
-qboolean Cvar_Exists (const char *var_name)
-{
-	cvar_t	*var;
-	long hash;
-
-	hash = generateHashValue(var_name);
-
-	for (var=hashTable[hash] ; var ; var=var->hashNext) {
-		if (!Q_stricmp(var_name, var->name)) {
-			return qtrue;
-		}
-	}
-
-	return qfalse;
-}
-
-/*
-============
-Cvar_FindVar
-============
-*/
-cvar_t *Cvar_FindVar( const char *var_name ) {
+static cvar_t *Cvar_FindVar( const char *var_name ) {
 	cvar_t	*var;
 	long hash;
 
@@ -350,7 +329,7 @@
 #endif
 
 	var = Cvar_FindVar (var_name);
-
+	
 	if(var)
 	{
 		var_value = Cvar_Validate(var, var_value, qfalse);
@@ -382,11 +361,11 @@
 
 				if(var->latchedString)
 					Z_Free(var->latchedString);
-
+				
 				var->latchedString = CopyString(var_value);
 			}
 		}
-
+		
 		// Make sure servers cannot mark engine-added variables as SERVER_CREATED
 		if(var->flags & CVAR_SERVER_CREATED)
 		{
@@ -398,7 +377,7 @@
 			if(flags & CVAR_SERVER_CREATED)
 				flags &= ~CVAR_SERVER_CREATED;
 		}
-
+		
 		var->flags |= flags;
 
 		// only allow one non-empty reset string without a warning
@@ -407,7 +386,7 @@
 			Z_Free( var->resetString );
 			var->resetString = CopyString( var_value );
 		} else if ( var_value[0] && strcmp( var->resetString, var_value ) ) {
-			Com_DPrintf( "Warning: cvar \"%s\" given initial values: \"%s" S_COLOR_WHITE "\" and \"%s" S_COLOR_WHITE "\"\n",
+			Com_DPrintf( "Warning: cvar \"%s\" given initial values: \"%s\" and \"%s\"\n",
 				var_name, var->resetString, var_value );
 		}
 		// if we have a latched string, take that value now
@@ -420,12 +399,9 @@
 			Z_Free( s );
 		}
 
-		// ZOID--needs to be set so that cvars the game sets as
+		// ZOID--needs to be set so that cvars the game sets as 
 		// SERVERINFO get sent to clients
 		cvar_modifiedFlags |= flags;
-		if (!com_writeConfig) {
-			cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-		}
 
 		return var;
 	}
@@ -441,8 +417,6 @@
 			break;
 	}
 
-	//Com_Printf("cvar get index:%d\n", index);
-
 	if(index >= MAX_CVARS)
 	{
 		if(!com_errorEntered)
@@ -450,23 +424,18 @@
 
 		return NULL;
 	}
-
+	
 	var = &cvar_indexes[index];
-
+	
 	if(index >= cvar_numIndexes)
 		cvar_numIndexes = index + 1;
-
+		
 	var->name = CopyString (var_name);
 	var->string = CopyString (var_value);
 	var->modified = qtrue;
 	var->modificationCount = 1;
-	if (var->string[0] == '0'  &&  (var->string[1] == 'x'  ||  var->string[1] == 'X')) {
-		var->integer = Com_HexStrToInt(var->string);
-		var->value = var->integer;
-	} else {
-		var->value = atof (var->string);
-		var->integer = atoi(var->string);
-	}
+	var->value = atof (var->string);
+	var->integer = atoi(var->string);
 	var->resetString = CopyString( var_value );
 	var->validate = qfalse;
 	var->description = NULL;
@@ -482,9 +451,6 @@
 	var->flags = flags;
 	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
 	cvar_modifiedFlags |= var->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
 
 	hash = generateHashValue(var_name);
 	var->hashIndex = hash;
@@ -512,9 +478,9 @@
 
 	if ( !( v->flags & CVAR_ROM ) ) {
 		if ( !Q_stricmp( v->string, v->resetString ) ) {
-			Com_Printf (S_COLOR_WHITE ", the default" );
+			Com_Printf (", the default" );
 		} else {
-			Com_Printf (S_COLOR_WHITE " default:\"%s" S_COLOR_WHITE "\"",
+			Com_Printf (" default:\"%s" S_COLOR_WHITE "\"",
 					v->resetString );
 		}
 	}
@@ -522,7 +488,7 @@
 	Com_Printf ("\n");
 
 	if ( v->latchedString ) {
-		Com_Printf(S_COLOR_WHITE "latched: \"%s" S_COLOR_WHITE "\"\n", v->latchedString );
+		Com_Printf( "latched: \"%s\"\n", v->latchedString );
 	}
 
 	if ( v->description ) {
@@ -588,9 +554,6 @@
 
 	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
 	cvar_modifiedFlags |= var->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
 
 	if (!force)
 	{
@@ -611,7 +574,7 @@
 			Com_Printf ("%s is cheat protected.\n", var_name);
 			return var;
 		}
-
+		
 		if (var->flags & CVAR_LATCH)
 		{
 			if (var->latchedString)
@@ -651,13 +614,8 @@
 	Z_Free (var->string);	// free the old value string
 	
 	var->string = CopyString(value);
-	if (var->string[0] == '0'  &&  (var->string[1] == 'x'  ||  var->string[1] == 'X')) {
-		var->integer = Com_HexStrToInt(var->string);
-		var->value = var->integer;
-	} else {
-		var->value = atof (var->string);
-		var->integer = atoi (var->string);
-	}
+	var->value = atof (var->string);
+	var->integer = atoi (var->string);
 
 	return var;
 }
@@ -684,10 +642,10 @@
 	{
 		if( value )
 			Com_Error( ERR_DROP, "Restricted source tried to set "
-					   "\"%s\" to \"%s\"", var_name, value );
+				"\"%s\" to \"%s\"", var_name, value );
 		else
 			Com_Error( ERR_DROP, "Restricted source tried to "
-					   "modify \"%s\"", var_name );
+				"modify \"%s\"", var_name );
 		return;
 	}
 	Cvar_Set( var_name, value );
@@ -883,56 +841,6 @@
 	Cvar_Set2(Cmd_Argv(1), Cmd_Argv(2), qfalse);
 }
 
-void Cvar_Copy_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: ccopy <variable> [new variable name]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(2), va("%f", Cvar_VariableValue(Cmd_Argv(1))), qfalse);
-}
-
-void Cvar_Add_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cadd <variable> [value to add]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) + atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Subtract_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: csub <variable> [value to subtract]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) - atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Multiply_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cmul <variable> [value to multiply]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) * atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Divide_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cdiv <variable> [value to divide by]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) / atof(Cmd_Argv(2))), qfalse);
-}
-
 /*
 ============
 Cvar_Set_f
@@ -964,13 +872,9 @@
 	}
 	switch( cmd[3] ) {
 		case 'a':
-			if (!Q_stricmpn("cg_forcebmodel", Cmd_Argv(1), strlen("cg_forcebmodel"))) {
-				Com_Printf("^3ignoring archive flag for '%s'\n", Cmd_Argv(1));
-			} else if( !( v->flags & CVAR_ARCHIVE ) ) {
+			if( !( v->flags & CVAR_ARCHIVE ) ) {
 				v->flags |= CVAR_ARCHIVE;
-				if (com_writeConfig) {
-					cvar_modifiedFlags |= CVAR_ARCHIVE;
-				}
+				cvar_modifiedFlags |= CVAR_ARCHIVE;
 			}
 			break;
 		case 'u':
@@ -1109,7 +1013,7 @@
 			Com_Printf(" ");
 		}
 
-		Com_Printf (" %s \"%s" S_COLOR_WHITE "\"\n", var->name, var->string);
+		Com_Printf (" %s \"%s\"\n", var->name, var->string);
 	}
 
 	Com_Printf ("\n%i total cvars\n", i);
@@ -1214,9 +1118,6 @@
 
 	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
 	cvar_modifiedFlags |= cv->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
 
 	if(cv->name)
 		Z_Free(cv->name);
@@ -1259,39 +1160,18 @@
 void Cvar_Unset_f(void)
 {
 	cvar_t *cv;
-	const char *varName;
-
+	
 	if(Cmd_Argc() != 2)
 	{
-		Com_Printf("Usage: %s <varname | varname*>\n", Cmd_Argv(0));
+		Com_Printf("Usage: %s <varname>\n", Cmd_Argv(0));
 		return;
 	}
-
-	varName = Cmd_Argv(1);
-
-	if (varName  &&  *varName  &&  strlen(varName) >= 1) {
-		if (varName[strlen(varName) - 1] == '*') {
-			//Com_Printf("unset all: '%s'\n", varName);
-
-			cv = cvar_vars;
-			while (cv) {
-				if (cv->flags & CVAR_USER_CREATED  &&  (varName[0] == '*'  ||  !Q_stricmpn(cv->name, varName, strlen(varName) - 2))) {
-					cv = Cvar_Unset(cv);
-					continue;
-				}
-
-				cv = cv->next;
-			}
-
-			return;
-		}
-	}
-
+	
 	cv = Cvar_FindVar(Cmd_Argv(1));
 
 	if(!cv)
 		return;
-
+	
 	if(cv->flags & CVAR_USER_CREATED)
 		Cvar_Unset(cv);
 	else
@@ -1452,7 +1332,7 @@
 	// baseq3) sets both flags. We unset CVAR_ROM for such cvars.
 	if ((flags & (CVAR_ARCHIVE | CVAR_ROM)) == (CVAR_ARCHIVE | CVAR_ROM)) {
 		Com_DPrintf( S_COLOR_YELLOW "WARNING: Unsetting CVAR_ROM from cvar '%s', "
-					 "since it is also CVAR_ARCHIVE\n", varName );
+			"since it is also CVAR_ARCHIVE\n", varName );
 		flags &= ~CVAR_ROM;
 	}
 
@@ -1483,7 +1363,7 @@
 	// Don't modify cvar if it's protected.
 	if ( cv && ( cv->flags & CVAR_PROTECTED ) ) {
 		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to register protected cvar '%s' with value '%s'%s\n",
-					 varName, defaultValue, ( flags & ~cv->flags ) != 0 ? " and new flags" : "" );
+			varName, defaultValue, ( flags & ~cv->flags ) != 0 ? " and new flags" : "" );
 	} else {
 		cv = Cvar_Get(varName, defaultValue, flags | CVAR_VM_CREATED);
 	}
@@ -1524,7 +1404,7 @@
 	if ( strlen(cv->string)+1 > MAX_CVAR_VALUE_STRING ) 
 	  Com_Error( ERR_DROP, "Cvar_Update: src %s length %u exceeds MAX_CVAR_VALUE_STRING",
 		     cv->string, 
-				 (unsigned int)strlen(cv->string));
+		     (unsigned int) strlen(cv->string));
 	Q_strncpyz( vmCvar->string, cv->string,  MAX_CVAR_VALUE_STRING ); 
 
 	vmCvar->value = cv->value;
@@ -1548,77 +1428,6 @@
 	}
 }
 
-void Cvar_ListChanges_f (void)
-{
-	cvar_t	*var;
-	//char	buffer[1024];
-
-	for (var = cvar_vars; var; var = var->next)
-	{
-		if (var->flags & CVAR_ROM) {
-			//continue;
-		}
-
-		if (!Q_stricmp(var->string, var->resetString)) {
-			continue;
-		}
-
-		Com_Printf("%s \"%s" S_COLOR_WHITE "\"  default: \"%s" S_COLOR_WHITE "\"%s\n", var->name, var->string, var->resetString, var->flags & CVAR_ROM ? S_COLOR_CYAN " (read only)" : "");
-	}
-
-	for (var = cvar_cheats; var; var = var->next)
-	{
-		if (!Q_stricmp(var->string, var->resetString)) {
-			continue;
-		}
-
-		Com_Printf("%s \"%s" S_COLOR_WHITE "\"  default: \"%s" S_COLOR_WHITE "\"  (cheat cvar)\n", var->name, var->string, var->resetString);
-	}
-}
-
-void Cvar_CvarResetAllMatching_f (void)
-{
-	cvar_t *var;
-	char s[1024];
-
-	if ( Cmd_Argc() != 2 ) {
-		Com_Printf("usage: reseta <variable matching string>\n");
-		return;
-	}
-	Q_strncpyz(s, Cmd_Argv(1), sizeof(s));
-
-	for (var = cvar_vars;  var;  var = var->next) {
-		if (Q_stricmpn(s, var->name, strlen(s)) == 0) {
-			Com_Printf("resetting %s\n", var->name);
-			Cvar_Reset(var->name);
-		}
-	}
-}
-
-void Cvar_Search_f (void)
-{
-	cvar_t *var;
-
-	if (Cmd_Argc() != 2) {
-		Com_Printf("usage: cvarsearch <string1>\n");
-		return;
-	}
-	for (var = cvar_vars;  var;  var = var->next) {
-		char *s;
-		s = var->name;
-		while (*s) {
-			if (Q_stricmpn(Cmd_Argv(1), s, strlen(Cmd_Argv(1))) == 0) {
-				if (Q_stricmp(var->string, var->resetString)) {
-					Com_Printf(S_COLOR_YELLOW "%s  '%s" S_COLOR_YELLOW  "'  default: " S_COLOR_CYAN "'%s" S_COLOR_CYAN "'\n", var->name, var->string, var->resetString);
-				} else {
-					Com_Printf("%s set to default '%s" S_COLOR_WHITE "'\n", var->name, var->string);
-				}
-			}
-			s++;
-		}
-	}
-}
-
 /*
 ============
 Cvar_Init
@@ -1636,16 +1445,6 @@
 	Cmd_AddCommand ("print", Cvar_Print_f);
 	Cmd_AddCommand ("toggle", Cvar_Toggle_f);
 	Cmd_SetCommandCompletionFunc( "toggle", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("ccopy", Cvar_Copy_f);
-	Cmd_SetCommandCompletionFunc( "ccopy", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cadd", Cvar_Add_f);
-	Cmd_SetCommandCompletionFunc( "cadd", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("csub", Cvar_Subtract_f);
-	Cmd_SetCommandCompletionFunc( "csub", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cmul", Cvar_Multiply_f);
-	Cmd_SetCommandCompletionFunc( "cmul", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cdiv", Cvar_Divide_f);
-	Cmd_SetCommandCompletionFunc( "cdiv", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("set", Cvar_Set_f);
 	Cmd_SetCommandCompletionFunc( "set", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("sets", Cvar_Set_f);
@@ -1658,12 +1457,6 @@
 	Cmd_SetCommandCompletionFunc( "reset", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("unset", Cvar_Unset_f);
 	Cmd_SetCommandCompletionFunc("unset", Cvar_CompleteCvarName);
-	Cmd_AddCommand("listcvarchanges", Cvar_ListChanges_f);
-	Cmd_SetCommandCompletionFunc("listcvarchanges", Cvar_CompleteCvarName);
-	Cmd_AddCommand("reseta", Cvar_CvarResetAllMatching_f);
-	Cmd_SetCommandCompletionFunc("reseta", Cvar_CompleteCvarName);
-	Cmd_AddCommand("cvarsearch", Cvar_Search_f);
-	Cmd_SetCommandCompletionFunc("cvarsearch", Cvar_CompleteCvarName);
 
 	Cmd_AddCommand ("cvarlist", Cvar_List_f);
 	Cmd_AddCommand ("cvar_modified", Cvar_ListModified_f);

```

### `quake3e`  — sha256 `e426a90ab72c...`, 45151 bytes

_Diff stat: +1024 / -556 lines_

_(full diff is 53147 bytes — see files directly)_

### `openarena-engine`  — sha256 `251373b40f8c...`, 27428 bytes

_Diff stat: +39 / -387 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cvar.c	2026-04-16 20:02:25.221161200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cvar.c	2026-04-16 22:48:25.907297500 +0100
@@ -28,7 +28,7 @@
 cvar_t		*cvar_cheats;
 int			cvar_modifiedFlags;
 
-#define	MAX_CVARS	1024  * 8  // * 8 // 1024
+#define	MAX_CVARS	2048
 cvar_t		cvar_indexes[MAX_CVARS];
 int			cvar_numIndexes;
 
@@ -82,28 +82,7 @@
 Cvar_FindVar
 ============
 */
-qboolean Cvar_Exists (const char *var_name)
-{
-	cvar_t	*var;
-	long hash;
-
-	hash = generateHashValue(var_name);
-
-	for (var=hashTable[hash] ; var ; var=var->hashNext) {
-		if (!Q_stricmp(var_name, var->name)) {
-			return qtrue;
-		}
-	}
-
-	return qfalse;
-}
-
-/*
-============
-Cvar_FindVar
-============
-*/
-cvar_t *Cvar_FindVar( const char *var_name ) {
+static cvar_t *Cvar_FindVar( const char *var_name ) {
 	cvar_t	*var;
 	long hash;
 
@@ -350,7 +329,7 @@
 #endif
 
 	var = Cvar_FindVar (var_name);
-
+	
 	if(var)
 	{
 		var_value = Cvar_Validate(var, var_value, qfalse);
@@ -375,18 +354,18 @@
 			Z_Free( var->resetString );
 			var->resetString = CopyString( var_value );
 
-			if(flags & CVAR_ROM)
+			if( (flags & CVAR_ROM) && !(flags & CVAR_ARCHIVE) )
 			{
 				// this variable was set by the user,
 				// so force it to value given by the engine.
 
 				if(var->latchedString)
 					Z_Free(var->latchedString);
-
+				
 				var->latchedString = CopyString(var_value);
 			}
 		}
-
+		
 		// Make sure servers cannot mark engine-added variables as SERVER_CREATED
 		if(var->flags & CVAR_SERVER_CREATED)
 		{
@@ -398,7 +377,7 @@
 			if(flags & CVAR_SERVER_CREATED)
 				flags &= ~CVAR_SERVER_CREATED;
 		}
-
+		
 		var->flags |= flags;
 
 		// only allow one non-empty reset string without a warning
@@ -407,7 +386,7 @@
 			Z_Free( var->resetString );
 			var->resetString = CopyString( var_value );
 		} else if ( var_value[0] && strcmp( var->resetString, var_value ) ) {
-			Com_DPrintf( "Warning: cvar \"%s\" given initial values: \"%s" S_COLOR_WHITE "\" and \"%s" S_COLOR_WHITE "\"\n",
+			Com_DPrintf( "Warning: cvar \"%s\" given initial values: \"%s\" and \"%s\"\n",
 				var_name, var->resetString, var_value );
 		}
 		// if we have a latched string, take that value now
@@ -420,12 +399,9 @@
 			Z_Free( s );
 		}
 
-		// ZOID--needs to be set so that cvars the game sets as
+		// ZOID--needs to be set so that cvars the game sets as 
 		// SERVERINFO get sent to clients
 		cvar_modifiedFlags |= flags;
-		if (!com_writeConfig) {
-			cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-		}
 
 		return var;
 	}
@@ -441,8 +417,6 @@
 			break;
 	}
 
-	//Com_Printf("cvar get index:%d\n", index);
-
 	if(index >= MAX_CVARS)
 	{
 		if(!com_errorEntered)
@@ -450,26 +424,20 @@
 
 		return NULL;
 	}
-
+	
 	var = &cvar_indexes[index];
-
+	
 	if(index >= cvar_numIndexes)
 		cvar_numIndexes = index + 1;
-
+		
 	var->name = CopyString (var_name);
 	var->string = CopyString (var_value);
 	var->modified = qtrue;
 	var->modificationCount = 1;
-	if (var->string[0] == '0'  &&  (var->string[1] == 'x'  ||  var->string[1] == 'X')) {
-		var->integer = Com_HexStrToInt(var->string);
-		var->value = var->integer;
-	} else {
-		var->value = atof (var->string);
-		var->integer = atoi(var->string);
-	}
+	var->value = atof (var->string);
+	var->integer = atoi(var->string);
 	var->resetString = CopyString( var_value );
 	var->validate = qfalse;
-	var->description = NULL;
 
 	// link the variable in
 	var->next = cvar_vars;
@@ -482,9 +450,6 @@
 	var->flags = flags;
 	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
 	cvar_modifiedFlags |= var->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
 
 	hash = generateHashValue(var_name);
 	var->hashIndex = hash;
@@ -512,9 +477,9 @@
 
 	if ( !( v->flags & CVAR_ROM ) ) {
 		if ( !Q_stricmp( v->string, v->resetString ) ) {
-			Com_Printf (S_COLOR_WHITE ", the default" );
+			Com_Printf (", the default" );
 		} else {
-			Com_Printf (S_COLOR_WHITE " default:\"%s" S_COLOR_WHITE "\"",
+			Com_Printf (" default:\"%s" S_COLOR_WHITE "\"",
 					v->resetString );
 		}
 	}
@@ -522,11 +487,7 @@
 	Com_Printf ("\n");
 
 	if ( v->latchedString ) {
-		Com_Printf(S_COLOR_WHITE "latched: \"%s" S_COLOR_WHITE "\"\n", v->latchedString );
-	}
-
-	if ( v->description ) {
-		Com_Printf( "%s\n", v->description );
+		Com_Printf( "latched: \"%s\"\n", v->latchedString );
 	}
 }
 
@@ -588,9 +549,6 @@
 
 	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
 	cvar_modifiedFlags |= var->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
 
 	if (!force)
 	{
@@ -606,12 +564,6 @@
 			return var;
 		}
 
-		if ((var->flags & CVAR_CHEAT) && !cvar_cheats->integer)
-		{
-			Com_Printf ("%s is cheat protected.\n", var_name);
-			return var;
-		}
-
 		if (var->flags & CVAR_LATCH)
 		{
 			if (var->latchedString)
@@ -632,6 +584,13 @@
 			var->modificationCount++;
 			return var;
 		}
+
+		if ( (var->flags & CVAR_CHEAT) && !cvar_cheats->integer )
+		{
+			Com_Printf ("%s is cheat protected.\n", var_name);
+			return var;
+		}
+
 	}
 	else
 	{
@@ -651,13 +610,8 @@
 	Z_Free (var->string);	// free the old value string
 	
 	var->string = CopyString(value);
-	if (var->string[0] == '0'  &&  (var->string[1] == 'x'  ||  var->string[1] == 'X')) {
-		var->integer = Com_HexStrToInt(var->string);
-		var->value = var->integer;
-	} else {
-		var->value = atof (var->string);
-		var->integer = atoi (var->string);
-	}
+	var->value = atof (var->string);
+	var->integer = atoi (var->string);
 
 	return var;
 }
@@ -684,10 +638,10 @@
 	{
 		if( value )
 			Com_Error( ERR_DROP, "Restricted source tried to set "
-					   "\"%s\" to \"%s\"", var_name, value );
+				"\"%s\" to \"%s\"", var_name, value );
 		else
 			Com_Error( ERR_DROP, "Restricted source tried to "
-					   "modify \"%s\"", var_name );
+				"modify \"%s\"", var_name );
 		return;
 	}
 	Cvar_Set( var_name, value );
@@ -883,56 +837,6 @@
 	Cvar_Set2(Cmd_Argv(1), Cmd_Argv(2), qfalse);
 }
 
-void Cvar_Copy_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: ccopy <variable> [new variable name]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(2), va("%f", Cvar_VariableValue(Cmd_Argv(1))), qfalse);
-}
-
-void Cvar_Add_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cadd <variable> [value to add]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) + atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Subtract_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: csub <variable> [value to subtract]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) - atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Multiply_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cmul <variable> [value to multiply]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) * atof(Cmd_Argv(2))), qfalse);
-}
-
-void Cvar_Divide_f (void)
-{
-	if(Cmd_Argc() < 3) {
-		Com_Printf("usage: cdiv <variable> [value to divide by]\n");
-		return;
-	}
-
-	Cvar_Set2(Cmd_Argv(1), va("%f", Cvar_VariableValue(Cmd_Argv(1)) / atof(Cmd_Argv(2))), qfalse);
-}
-
 /*
 ============
 Cvar_Set_f
@@ -964,13 +868,9 @@
 	}
 	switch( cmd[3] ) {
 		case 'a':
-			if (!Q_stricmpn("cg_forcebmodel", Cmd_Argv(1), strlen("cg_forcebmodel"))) {
-				Com_Printf("^3ignoring archive flag for '%s'\n", Cmd_Argv(1));
-			} else if( !( v->flags & CVAR_ARCHIVE ) ) {
+			if( !( v->flags & CVAR_ARCHIVE ) ) {
 				v->flags |= CVAR_ARCHIVE;
-				if (com_writeConfig) {
-					cvar_modifiedFlags |= CVAR_ARCHIVE;
-				}
+				cvar_modifiedFlags |= CVAR_ARCHIVE;
 			}
 			break;
 		case 'u':
@@ -1109,7 +1009,7 @@
 			Com_Printf(" ");
 		}
 
-		Com_Printf (" %s \"%s" S_COLOR_WHITE "\"\n", var->name, var->string);
+		Com_Printf (" %s \"%s\"\n", var->name, var->string);
 	}
 
 	Com_Printf ("\n%i total cvars\n", i);
@@ -1118,90 +1018,6 @@
 
 /*
 ============
-Cvar_ListModified_f
-============
-*/
-void Cvar_ListModified_f( void ) {
-	cvar_t	*var;
-	int		totalModified;
-	char	*value;
-	char	*match;
-
-	if ( Cmd_Argc() > 1 ) {
-		match = Cmd_Argv( 1 );
-	} else {
-		match = NULL;
-	}
-
-	totalModified = 0;
-	for (var = cvar_vars ; var ; var = var->next)
-	{
-		if ( !var->name || !var->modificationCount )
-			continue;
-
-		value = var->latchedString ? var->latchedString : var->string;
-		if ( !strcmp( value, var->resetString ) )
-			continue;
-
-		totalModified++;
-
-		if (match && !Com_Filter(match, var->name, qfalse))
-			continue;
-
-		if (var->flags & CVAR_SERVERINFO) {
-			Com_Printf("S");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_SYSTEMINFO) {
-			Com_Printf("s");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_USERINFO) {
-			Com_Printf("U");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_ROM) {
-			Com_Printf("R");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_INIT) {
-			Com_Printf("I");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_ARCHIVE) {
-			Com_Printf("A");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_LATCH) {
-			Com_Printf("L");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_CHEAT) {
-			Com_Printf("C");
-		} else {
-			Com_Printf(" ");
-		}
-		if (var->flags & CVAR_USER_CREATED) {
-			Com_Printf("?");
-		} else {
-			Com_Printf(" ");
-		}
-
-		Com_Printf (" %s \"%s\", default \"%s\"\n", var->name, value, var->resetString);
-	}
-
-	Com_Printf ("\n%i total modified cvars\n", totalModified);
-}
-
-/*
-============
 Cvar_Unset
 
 Unsets a cvar
@@ -1212,12 +1028,6 @@
 {
 	cvar_t *next = cv->next;
 
-	// note what types of cvars have been modified (userinfo, archive, serverinfo, systeminfo)
-	cvar_modifiedFlags |= cv->flags;
-	if (!com_writeConfig) {
-		cvar_modifiedFlags &= ~CVAR_ARCHIVE;
-	}
-
 	if(cv->name)
 		Z_Free(cv->name);
 	if(cv->string)
@@ -1226,8 +1036,6 @@
 		Z_Free(cv->latchedString);
 	if(cv->resetString)
 		Z_Free(cv->resetString);
-	if(cv->description)
-		Z_Free(cv->description);
 
 	if(cv->prev)
 		cv->prev->next = cv->next;
@@ -1259,39 +1067,18 @@
 void Cvar_Unset_f(void)
 {
 	cvar_t *cv;
-	const char *varName;
-
+	
 	if(Cmd_Argc() != 2)
 	{
-		Com_Printf("Usage: %s <varname | varname*>\n", Cmd_Argv(0));
+		Com_Printf("Usage: %s <varname>\n", Cmd_Argv(0));
 		return;
 	}
-
-	varName = Cmd_Argv(1);
-
-	if (varName  &&  *varName  &&  strlen(varName) >= 1) {
-		if (varName[strlen(varName) - 1] == '*') {
-			//Com_Printf("unset all: '%s'\n", varName);
-
-			cv = cvar_vars;
-			while (cv) {
-				if (cv->flags & CVAR_USER_CREATED  &&  (varName[0] == '*'  ||  !Q_stricmpn(cv->name, varName, strlen(varName) - 2))) {
-					cv = Cvar_Unset(cv);
-					continue;
-				}
-
-				cv = cv->next;
-			}
-
-			return;
-		}
-	}
-
+	
 	cv = Cvar_FindVar(Cmd_Argv(1));
 
 	if(!cv)
 		return;
-
+	
 	if(cv->flags & CVAR_USER_CREATED)
 		Cvar_Unset(cv);
 	else
@@ -1420,23 +1207,6 @@
 
 /*
 =====================
-Cvar_SetDescription
-=====================
-*/
-void Cvar_SetDescription( cvar_t *var, const char *var_description )
-{
-	if( var_description && var_description[0] != '\0' )
-	{
-		if( var->description != NULL )
-		{
-			Z_Free( var->description );
-		}
-		var->description = CopyString( var_description );
-	}
-}
-
-/*
-=====================
 Cvar_Register
 
 basically a slightly modified Cvar_Get for the interpreted modules
@@ -1451,42 +1221,12 @@
 	// flags. Unfortunately some historical game code (including single player
 	// baseq3) sets both flags. We unset CVAR_ROM for such cvars.
 	if ((flags & (CVAR_ARCHIVE | CVAR_ROM)) == (CVAR_ARCHIVE | CVAR_ROM)) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: Unsetting CVAR_ROM from cvar '%s', "
-					 "since it is also CVAR_ARCHIVE\n", varName );
+		Com_DPrintf( S_COLOR_YELLOW "WARNING: Unsetting CVAR_ROM cvar '%s', "
+			"since it is also CVAR_ARCHIVE\n", varName );
 		flags &= ~CVAR_ROM;
 	}
 
-	// Don't allow VM to specific a different creator or other internal flags.
-	if ( flags & CVAR_USER_CREATED ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to set CVAR_USER_CREATED on cvar '%s'\n", varName );
-		flags &= ~CVAR_USER_CREATED;
-	}
-	if ( flags & CVAR_SERVER_CREATED ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to set CVAR_SERVER_CREATED on cvar '%s'\n", varName );
-		flags &= ~CVAR_SERVER_CREATED;
-	}
-	if ( flags & CVAR_PROTECTED ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to set CVAR_PROTECTED on cvar '%s'\n", varName );
-		flags &= ~CVAR_PROTECTED;
-	}
-	if ( flags & CVAR_MODIFIED ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to set CVAR_MODIFIED on cvar '%s'\n", varName );
-		flags &= ~CVAR_MODIFIED;
-	}
-	if ( flags & CVAR_NONEXISTENT ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to set CVAR_NONEXISTENT on cvar '%s'\n", varName );
-		flags &= ~CVAR_NONEXISTENT;
-	}
-
-	cv = Cvar_FindVar(varName);
-
-	// Don't modify cvar if it's protected.
-	if ( cv && ( cv->flags & CVAR_PROTECTED ) ) {
-		Com_DPrintf( S_COLOR_YELLOW "WARNING: VM tried to register protected cvar '%s' with value '%s'%s\n",
-					 varName, defaultValue, ( flags & ~cv->flags ) != 0 ? " and new flags" : "" );
-	} else {
-		cv = Cvar_Get(varName, defaultValue, flags | CVAR_VM_CREATED);
-	}
+	cv = Cvar_Get(varName, defaultValue, flags | CVAR_VM_CREATED);
 
 	if (!vmCvar)
 		return;
@@ -1524,7 +1264,7 @@
 	if ( strlen(cv->string)+1 > MAX_CVAR_VALUE_STRING ) 
 	  Com_Error( ERR_DROP, "Cvar_Update: src %s length %u exceeds MAX_CVAR_VALUE_STRING",
 		     cv->string, 
-				 (unsigned int)strlen(cv->string));
+		     (unsigned int) strlen(cv->string));
 	Q_strncpyz( vmCvar->string, cv->string,  MAX_CVAR_VALUE_STRING ); 
 
 	vmCvar->value = cv->value;
@@ -1548,77 +1288,6 @@
 	}
 }
 
-void Cvar_ListChanges_f (void)
-{
-	cvar_t	*var;
-	//char	buffer[1024];
-
-	for (var = cvar_vars; var; var = var->next)
-	{
-		if (var->flags & CVAR_ROM) {
-			//continue;
-		}
-
-		if (!Q_stricmp(var->string, var->resetString)) {
-			continue;
-		}
-
-		Com_Printf("%s \"%s" S_COLOR_WHITE "\"  default: \"%s" S_COLOR_WHITE "\"%s\n", var->name, var->string, var->resetString, var->flags & CVAR_ROM ? S_COLOR_CYAN " (read only)" : "");
-	}
-
-	for (var = cvar_cheats; var; var = var->next)
-	{
-		if (!Q_stricmp(var->string, var->resetString)) {
-			continue;
-		}
-
-		Com_Printf("%s \"%s" S_COLOR_WHITE "\"  default: \"%s" S_COLOR_WHITE "\"  (cheat cvar)\n", var->name, var->string, var->resetString);
-	}
-}
-
-void Cvar_CvarResetAllMatching_f (void)
-{
-	cvar_t *var;
-	char s[1024];
-
-	if ( Cmd_Argc() != 2 ) {
-		Com_Printf("usage: reseta <variable matching string>\n");
-		return;
-	}
-	Q_strncpyz(s, Cmd_Argv(1), sizeof(s));
-
-	for (var = cvar_vars;  var;  var = var->next) {
-		if (Q_stricmpn(s, var->name, strlen(s)) == 0) {
-			Com_Printf("resetting %s\n", var->name);
-			Cvar_Reset(var->name);
-		}
-	}
-}
-
-void Cvar_Search_f (void)
-{
-	cvar_t *var;
-
-	if (Cmd_Argc() != 2) {
-		Com_Printf("usage: cvarsearch <string1>\n");
-		return;
-	}
-	for (var = cvar_vars;  var;  var = var->next) {
-		char *s;
-		s = var->name;
-		while (*s) {
-			if (Q_stricmpn(Cmd_Argv(1), s, strlen(Cmd_Argv(1))) == 0) {
-				if (Q_stricmp(var->string, var->resetString)) {
-					Com_Printf(S_COLOR_YELLOW "%s  '%s" S_COLOR_YELLOW  "'  default: " S_COLOR_CYAN "'%s" S_COLOR_CYAN "'\n", var->name, var->string, var->resetString);
-				} else {
-					Com_Printf("%s set to default '%s" S_COLOR_WHITE "'\n", var->name, var->string);
-				}
-			}
-			s++;
-		}
-	}
-}
-
 /*
 ============
 Cvar_Init
@@ -1636,16 +1305,6 @@
 	Cmd_AddCommand ("print", Cvar_Print_f);
 	Cmd_AddCommand ("toggle", Cvar_Toggle_f);
 	Cmd_SetCommandCompletionFunc( "toggle", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("ccopy", Cvar_Copy_f);
-	Cmd_SetCommandCompletionFunc( "ccopy", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cadd", Cvar_Add_f);
-	Cmd_SetCommandCompletionFunc( "cadd", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("csub", Cvar_Subtract_f);
-	Cmd_SetCommandCompletionFunc( "csub", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cmul", Cvar_Multiply_f);
-	Cmd_SetCommandCompletionFunc( "cmul", Cvar_CompleteCvarName );
-	Cmd_AddCommand ("cdiv", Cvar_Divide_f);
-	Cmd_SetCommandCompletionFunc( "cdiv", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("set", Cvar_Set_f);
 	Cmd_SetCommandCompletionFunc( "set", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("sets", Cvar_Set_f);
@@ -1658,14 +1317,7 @@
 	Cmd_SetCommandCompletionFunc( "reset", Cvar_CompleteCvarName );
 	Cmd_AddCommand ("unset", Cvar_Unset_f);
 	Cmd_SetCommandCompletionFunc("unset", Cvar_CompleteCvarName);
-	Cmd_AddCommand("listcvarchanges", Cvar_ListChanges_f);
-	Cmd_SetCommandCompletionFunc("listcvarchanges", Cvar_CompleteCvarName);
-	Cmd_AddCommand("reseta", Cvar_CvarResetAllMatching_f);
-	Cmd_SetCommandCompletionFunc("reseta", Cvar_CompleteCvarName);
-	Cmd_AddCommand("cvarsearch", Cvar_Search_f);
-	Cmd_SetCommandCompletionFunc("cvarsearch", Cvar_CompleteCvarName);
 
 	Cmd_AddCommand ("cvarlist", Cvar_List_f);
-	Cmd_AddCommand ("cvar_modified", Cvar_ListModified_f);
 	Cmd_AddCommand ("cvar_restart", Cvar_Restart_f);
 }

```
