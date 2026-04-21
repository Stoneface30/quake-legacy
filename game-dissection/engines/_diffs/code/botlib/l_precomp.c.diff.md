# Diff: `code/botlib/l_precomp.c`
**Canonical:** `wolfcamql-src` (sha256 `01f222e1f61b...`, 91731 bytes)

## Variants

### `quake3-source`  — sha256 `b2a7cc5acc3e...`, 91852 bytes

_Diff stat: +68 / -76 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.c	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_precomp.c	2026-04-16 20:02:19.857903700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -53,8 +53,8 @@
 #endif //SCREWUP
 
 #ifdef BOTLIB
-#include "../qcommon/q_shared.h"
-#include "botlib.h"
+#include "../game/q_shared.h"
+#include "../game/botlib.h"
 #include "be_interface.h"
 #include "l_memory.h"
 #include "l_script.h"
@@ -131,7 +131,7 @@
 	va_list ap;
 
 	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	vsprintf(text, str, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_ERROR, "file %s, line %d: %s\n", source->scriptstack->filename, source->scriptstack->line, text);
@@ -155,7 +155,7 @@
 	va_list ap;
 
 	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	vsprintf(text, str, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_WARNING, "file %s, line %d: %s\n", source->scriptstack->filename, source->scriptstack->line, text);
@@ -269,9 +269,9 @@
 	if (!t)
 	{
 #ifdef BSPC
-		Error("out of token space");
+		Error("out of token space\n");
 #else
-		Com_Error(ERR_FATAL, "out of token space");
+		Com_Error(ERR_FATAL, "out of token space\n");
 #endif
 		return NULL;
 	} //end if
@@ -414,6 +414,7 @@
 				if (indent <= 0)
 				{
 					if (lastcomma) SourceWarning(source, "too many comma's");
+					lastcomma = 1;
 					break;
 				} //end if
 			} //end if
@@ -468,10 +469,9 @@
 	strcat(token->string, "\"");
 	for (t = tokens; t; t = t->next)
 	{
-		snprintf(token->string + strlen(token->string),
-			MAX_TOKEN - strlen(token->string), "%s", t->string);
+		strncat(token->string, t->string, MAX_TOKEN - strlen(token->string));
 	} //end for
-	strncat(token->string, "\"", MAX_TOKEN - strlen(token->string) - 1);
+	strncat(token->string, "\"", MAX_TOKEN - strlen(token->string));
 	return qtrue;
 } //end of the function PC_StringizeTokens
 //============================================================================
@@ -549,7 +549,7 @@
 
 int PC_NameHash(char *name)
 {
-	int hash, i;
+	int register hash, i;
 
 	hash = 0;
 	for (i = 0; name[i] != '\0'; i++)
@@ -653,7 +653,6 @@
 		PC_FreeToken(t);
 	} //end for
 	//free the define
-	FreeMemory(define->name);
 	FreeMemory(define);
 } //end of the function PC_FreeDefine
 //============================================================================
@@ -670,7 +669,7 @@
 	{
 		char *string;
 		int builtin;
-	} builtin[] = {
+	} builtin[] = { // bk001204 - brackets
 		{ "__LINE__",	BUILTIN_LINE },
 		{ "__FILE__",	BUILTIN_FILE },
 		{ "__DATE__",	BUILTIN_DATE },
@@ -681,9 +680,9 @@
 
 	for (i = 0; builtin[i].string; i++)
 	{
-		define = (define_t *) GetMemory(sizeof(define_t));
+		define = (define_t *) GetMemory(sizeof(define_t) + strlen(builtin[i].string) + 1);
 		Com_Memset(define, 0, sizeof(define_t));
-		define->name = (char *) GetMemory(strlen(builtin[i].string) + 1);
+		define->name = (char *) define + sizeof(define_t);
 		strcpy(define->name, builtin[i].string);
 		define->flags |= DEFINE_FIXED;
 		define->builtin = builtin[i].builtin;
@@ -706,8 +705,7 @@
 										token_t **firsttoken, token_t **lasttoken)
 {
 	token_t *token;
-	time_t t;
-	
+	unsigned long t;	//	time_t t; //to prevent LCC warning
 	char *curtime;
 
 	token = PC_CopyToken(deftoken);
@@ -783,7 +781,7 @@
 int PC_ExpandDefine(source_t *source, token_t *deftoken, define_t *define,
 										token_t **firsttoken, token_t **lasttoken)
 {
-	token_t *parms[MAX_DEFINEPARMS] = { NULL }, *dt, *pt, *t; 
+	token_t *parms[MAX_DEFINEPARMS], *dt, *pt, *t;
 	token_t *t1, *t2, *first, *last, *nextpt, token;
 	int parmnum, i;
 
@@ -948,7 +946,7 @@
 		if ((*ptr == '\\' || *ptr == '/') &&
 				(*(ptr+1) == '\\' || *(ptr+1) == '/'))
 		{
-			memmove(ptr, ptr+1, strlen(ptr));
+			strcpy(ptr, ptr+1);
 		} //end if
 		else
 		{
@@ -972,7 +970,7 @@
 {
 	script_t *script;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 #ifdef QUAKE
 	foundfile_t file;
 #endif //QUAKE
@@ -996,14 +994,14 @@
 		script = LoadScriptFile(token.string);
 		if (!script)
 		{
-			Q_strncpyz(path, source->includepath, sizeof(path));
-			Q_strcat(path, sizeof(path), token.string);
+			strcpy(path, source->includepath);
+			strcat(path, token.string);
 			script = LoadScriptFile(path);
 		} //end if
 	} //end if
 	else if (token.type == TT_PUNCTUATION && *token.string == '<')
 	{
-		Q_strncpyz(path, source->includepath, sizeof(path));
+		strcpy(path, source->includepath);
 		while(PC_ReadSourceToken(source, &token))
 		{
 			if (token.linescrossed > 0)
@@ -1012,7 +1010,7 @@
 				break;
 			} //end if
 			if (token.type == TT_PUNCTUATION && *token.string == '>') break;
-			Q_strcat(path, sizeof(path), token.string);
+			strncat(path, token.string, MAX_PATH);
 		} //end while
 		if (*token.string != '>')
 		{
@@ -1036,7 +1034,7 @@
 	{
 		Com_Memset(&file, 0, sizeof(foundfile_t));
 		script = LoadScriptFile(path);
-		if (script) Q_strncpyz(script->filename, path, sizeof(script->filename));
+		if (script) strncpy(script->filename, path, MAX_PATH);
 	} //end if
 #endif //QUAKE
 	if (!script)
@@ -1209,11 +1207,17 @@
 		//unread the define name before executing the #undef directive
 		PC_UnreadSourceToken(source, &token);
 		if (!PC_Directive_undef(source)) return qfalse;
+		//if the define was not removed (define->flags & DEFINE_FIXED)
+#if DEFINEHASHING
+		define = PC_FindHashedDefine(source->definehash, token.string);
+#else
+		define = PC_FindDefine(source->defines, token.string);
+#endif //DEFINEHASHING
 	} //end if
 	//allocate define
-	define = (define_t *) GetMemory(sizeof(define_t));
+	define = (define_t *) GetMemory(sizeof(define_t) + strlen(token.string) + 1);
 	Com_Memset(define, 0, sizeof(define_t));
-	define->name = (char *) GetMemory(strlen(token.string) + 1);
+	define->name = (char *) define + sizeof(define_t);
 	strcpy(define->name, token.string);
 	//add the define to the source
 #if DEFINEHASHING
@@ -1324,7 +1328,7 @@
 	script = LoadScriptMemory(string, strlen(string), "*extern");
 	//create a new source
 	Com_Memset(&src, 0, sizeof(source_t));
-	Q_strncpyz(src.filename, "*extern", sizeof(src.filename));
+	strncpy(src.filename, "*extern", MAX_PATH);
 	src.scriptstack = script;
 #if DEFINEHASHING
 	src.definehash = GetClearedMemory(DEFINEHASHSIZE * sizeof(define_t *));
@@ -1356,7 +1360,7 @@
 #endif //DEFINEHASHING
 	//
 	FreeScript(script);
-	//if the define was created successfully
+	//if the define was created succesfully
 	if (res > 0) return def;
 	//free the define is created
 	if (src.defines) PC_FreeDefine(def);
@@ -1447,9 +1451,9 @@
 	define_t *newdefine;
 	token_t *token, *newtoken, *lasttoken;
 
-	newdefine = (define_t *) GetMemory(sizeof(define_t));
+	newdefine = (define_t *) GetMemory(sizeof(define_t) + strlen(define->name) + 1);
 	//copy the define name
-	newdefine->name = (char *) GetMemory(strlen(define->name) + 1);
+	newdefine->name = (char *) newdefine + sizeof(define_t);
 	strcpy(newdefine->name, define->name);
 	newdefine->flags = define->flags;
 	newdefine->builtin = define->builtin;
@@ -1611,7 +1615,7 @@
 typedef struct value_s
 {
 	signed long int intvalue;
-	float floatvalue;
+	double floatvalue;
 	int parentheses;
 	struct value_s *prev, *next;
 } value_t;
@@ -1660,7 +1664,7 @@
 #define MAX_OPERATORS	64
 #define AllocValue(val)									\
 	if (numvalues >= MAX_VALUES) {						\
-		SourceError(source, "out of value space");		\
+		SourceError(source, "out of value space\n");		\
 		error = 1;										\
 		break;											\
 	}													\
@@ -1670,7 +1674,7 @@
 //
 #define AllocOperator(op)								\
 	if (numoperators >= MAX_OPERATORS) {				\
-		SourceError(source, "out of operator space");	\
+		SourceError(source, "out of operator space\n");	\
 		error = 1;										\
 		break;											\
 	}													\
@@ -1679,7 +1683,7 @@
 #define FreeOperator(op)
 
 int PC_EvaluateTokens(source_t *source, token_t *tokens, signed long int *intvalue,
-																	float *floatvalue, int integer)
+																	double *floatvalue, int integer)
 {
 	operator_t *o, *firstoperator, *lastoperator;
 	value_t *v, *firstvalue, *lastvalue, *v1, *v2;
@@ -1690,8 +1694,9 @@
 	int lastwasvalue = 0;
 	int negativevalue = 0;
 	int questmarkintvalue = 0;
-	float questmarkfloatvalue = 0;
+	double questmarkfloatvalue = 0;
 	int gotquestmarkvalue = qfalse;
+	int lastoperatortype = 0;
 	//
 	operator_t operator_heap[MAX_OPERATORS];
 	int numoperators = 0;
@@ -1832,7 +1837,7 @@
 						t->subtype == P_BIN_AND || t->subtype == P_BIN_OR ||
 						t->subtype == P_BIN_XOR)
 					{
-						SourceError(source, "illigal operator %s on floating point operands", t->string);
+						SourceError(source, "illigal operator %s on floating point operands\n", t->string);
 						error = 1;
 						break;
 					} //end if
@@ -1999,7 +2004,7 @@
 									v1->floatvalue *= v2->floatvalue; break;
 			case P_DIV:				if (!v2->intvalue || !v2->floatvalue)
 									{
-										SourceError(source, "divide by zero in #if/#elif");
+										SourceError(source, "divide by zero in #if/#elif\n");
 										error = 1;
 										break;
 									}
@@ -2007,7 +2012,7 @@
 									v1->floatvalue /= v2->floatvalue; break;
 			case P_MOD:				if (!v2->intvalue)
 									{
-										SourceError(source, "divide by zero in #if/#elif");
+										SourceError(source, "divide by zero in #if/#elif\n");
 										error = 1;
 										break;
 									}
@@ -2080,6 +2085,7 @@
 		else Log_Write("result value = %f", v1->floatvalue);
 #endif //DEBUG_EVAL
 		if (error) break;
+		lastoperatortype = o->operator;
 		//if not an operator with arity 1
 		if (o->operator != P_LOGIC_NOT
 				&& o->operator != P_BIN_NOT)
@@ -2087,12 +2093,10 @@
 			//remove the second value if not question mark operator
 			if (o->operator != P_QUESTIONMARK) v = v->next;
 			//
-			if (v)
-			{
-				if (v->prev) v->prev->next = v->next;
-				else firstvalue = v->next;
-				if (v->next) v->next->prev = v->prev;
-			}
+			if (v->prev) v->prev->next = v->next;
+			else firstvalue = v->next;
+			if (v->next) v->next->prev = v->prev;
+			else lastvalue = v->prev;
 			//FreeMemory(v);
 			FreeValue(v);
 		} //end if
@@ -2100,6 +2104,7 @@
 		if (o->prev) o->prev->next = o->next;
 		else firstoperator = o->next;
 		if (o->next) o->next->prev = o->prev;
+		else lastoperator = o->prev;
 		//FreeMemory(o);
 		FreeOperator(o);
 	} //end while
@@ -2132,7 +2137,7 @@
 // Changes Globals:		-
 //============================================================================
 int PC_Evaluate(source_t *source, signed long int *intvalue,
-												float *floatvalue, int integer)
+												double *floatvalue, int integer)
 {
 	token_t token, *firsttoken, *lasttoken;
 	token_t *t, *nexttoken;
@@ -2231,7 +2236,7 @@
 // Changes Globals:		-
 //============================================================================
 int PC_DollarEvaluate(source_t *source, signed long int *intvalue,
-												float *floatvalue, int integer)
+												double *floatvalue, int integer)
 {
 	int indent, defined = qfalse;
 	token_t token, *firsttoken, *lasttoken;
@@ -2446,7 +2451,7 @@
 	token.whitespace_p = source->scriptstack->script_p;
 	token.endwhitespace_p = source->scriptstack->script_p;
 	token.linescrossed = 0;
-	sprintf(token.string, "%ld", labs(value));
+	sprintf(token.string, "%d", abs(value));
 	token.type = TT_NUMBER;
 	token.subtype = TT_INTEGER|TT_LONG|TT_DECIMAL;
 	PC_UnreadSourceToken(source, &token);
@@ -2461,7 +2466,7 @@
 //============================================================================
 int PC_Directive_evalfloat(source_t *source)
 {
-	float value;
+	double value;
 	token_t token;
 
 	if (!PC_Evaluate(source, NULL, &value, qfalse)) return qfalse;
@@ -2551,19 +2556,15 @@
 	token.whitespace_p = source->scriptstack->script_p;
 	token.endwhitespace_p = source->scriptstack->script_p;
 	token.linescrossed = 0;
-	sprintf(token.string, "%ld", labs(value));
+	sprintf(token.string, "%d", abs(value));
 	token.type = TT_NUMBER;
 	token.subtype = TT_INTEGER|TT_LONG|TT_DECIMAL;
-
 #ifdef NUMBERVALUE
-	token.intvalue = labs(value);
-	token.floatvalue = token.intvalue;
+	token.intvalue = value;
+	token.floatvalue = value;
 #endif //NUMBERVALUE
-
 	PC_UnreadSourceToken(source, &token);
-	if (value < 0)
-		UnreadSignToken(source);
-
+	if (value < 0) UnreadSignToken(source);
 	return qtrue;
 } //end of the function PC_DollarDirective_evalint
 //============================================================================
@@ -2574,7 +2575,7 @@
 //============================================================================
 int PC_DollarDirective_evalfloat(source_t *source)
 {
-	float value;
+	double value;
 	token_t token;
 
 	if (!PC_DollarEvaluate(source, NULL, &value, qfalse)) return qfalse;
@@ -2585,16 +2586,12 @@
 	sprintf(token.string, "%1.2f", fabs(value));
 	token.type = TT_NUMBER;
 	token.subtype = TT_FLOAT|TT_LONG|TT_DECIMAL;
-
 #ifdef NUMBERVALUE
-	token.floatvalue = fabs(value);
-	token.intvalue = (unsigned long) token.floatvalue;
+	token.intvalue = (unsigned long) value;
+	token.floatvalue = value;
 #endif //NUMBERVALUE
-
 	PC_UnreadSourceToken(source, &token);
-	if (value < 0)
-		UnreadSignToken(source);
-
+	if (value < 0) UnreadSignToken(source);
 	return qtrue;
 } //end of the function PC_DollarDirective_evalfloat
 //============================================================================
@@ -2745,7 +2742,7 @@
 					token->string[strlen(token->string)-1] = '\0';
 					if (strlen(token->string) + strlen(newtoken.string+1) + 1 >= MAX_TOKEN)
 					{
-						SourceError(source, "string longer than MAX_TOKEN %d", MAX_TOKEN);
+						SourceError(source, "string longer than MAX_TOKEN %d\n", MAX_TOKEN);
 						return qfalse;
 					}
 					strcat(token->string, newtoken.string+1);
@@ -2835,7 +2832,6 @@
 	{
 		if ((token->subtype & subtype) != subtype)
 		{
-			strcpy(str, "");
 			if (subtype & TT_DECIMAL) strcpy(str, "decimal");
 			if (subtype & TT_HEX) strcpy(str, "hex");
 			if (subtype & TT_OCTAL) strcpy(str, "octal");
@@ -2959,14 +2955,10 @@
 //============================================================================
 void PC_SetIncludePath(source_t *source, char *path)
 {
-	size_t len;
-
-	Q_strncpyz(source->includepath, path, sizeof(source->includepath)-1);
-
-	len = strlen(source->includepath);
+	strncpy(source->includepath, path, MAX_PATH);
 	//add trailing path seperator
-	if (len > 0 && source->includepath[len-1] != '\\' &&
-		source->includepath[len-1] != '/')
+	if (source->includepath[strlen(source->includepath)-1] != '\\' &&
+		source->includepath[strlen(source->includepath)-1] != '/')
 	{
 		strcat(source->includepath, PATHSEPERATOR_STR);
 	} //end if
@@ -3002,7 +2994,7 @@
 	source = (source_t *) GetMemory(sizeof(source_t));
 	Com_Memset(source, 0, sizeof(source_t));
 
-	Q_strncpyz(source->filename, filename, sizeof(source->filename));
+	strncpy(source->filename, filename, MAX_PATH);
 	source->scriptstack = script;
 	source->tokens = NULL;
 	source->defines = NULL;
@@ -3035,7 +3027,7 @@
 	source = (source_t *) GetMemory(sizeof(source_t));
 	Com_Memset(source, 0, sizeof(source_t));
 
-	Q_strncpyz(source->filename, name, sizeof(source->filename));
+	strncpy(source->filename, name, MAX_PATH);
 	source->scriptstack = script;
 	source->tokens = NULL;
 	source->defines = NULL;

```

### `ioquake3`  — sha256 `82fa9c648698...`, 91730 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.c	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\botlib\l_precomp.c	2026-04-16 20:02:21.515489600 +0100
@@ -783,7 +783,7 @@
 int PC_ExpandDefine(source_t *source, token_t *deftoken, define_t *define,
 										token_t **firsttoken, token_t **lasttoken)
 {
-	token_t *parms[MAX_DEFINEPARMS] = { NULL }, *dt, *pt, *t; 
+	token_t *parms[MAX_DEFINEPARMS] = { NULL }, *dt, *pt, *t;
 	token_t *t1, *t2, *first, *last, *nextpt, token;
 	int parmnum, i;
 

```

### `quake3e`  — sha256 `a04b7d9bdd8d...`, 92510 bytes

_Diff stat: +133 / -111 lines_

_(full diff is 29773 bytes — see files directly)_

### `openarena-engine`  — sha256 `183b7cbfd102...`, 91488 bytes

_Diff stat: +21 / -30 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.c	2026-04-16 20:02:25.129417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_precomp.c	2026-04-16 22:48:25.720197700 +0100
@@ -468,8 +468,7 @@
 	strcat(token->string, "\"");
 	for (t = tokens; t; t = t->next)
 	{
-		snprintf(token->string + strlen(token->string),
-			MAX_TOKEN - strlen(token->string), "%s", t->string);
+		strncat(token->string, t->string, MAX_TOKEN - strlen(token->string) - 1);
 	} //end for
 	strncat(token->string, "\"", MAX_TOKEN - strlen(token->string) - 1);
 	return qtrue;
@@ -549,7 +548,7 @@
 
 int PC_NameHash(char *name)
 {
-	int hash, i;
+	int register hash, i;
 
 	hash = 0;
 	for (i = 0; name[i] != '\0'; i++)
@@ -783,7 +782,7 @@
 int PC_ExpandDefine(source_t *source, token_t *deftoken, define_t *define,
 										token_t **firsttoken, token_t **lasttoken)
 {
-	token_t *parms[MAX_DEFINEPARMS] = { NULL }, *dt, *pt, *t; 
+	token_t *parms[MAX_DEFINEPARMS] = { NULL }, *dt, *pt, *t;
 	token_t *t1, *t2, *first, *last, *nextpt, token;
 	int parmnum, i;
 
@@ -972,7 +971,7 @@
 {
 	script_t *script;
 	token_t token;
-	char path[MAX_QPATH];
+	char path[MAX_PATH];
 #ifdef QUAKE
 	foundfile_t file;
 #endif //QUAKE
@@ -996,14 +995,14 @@
 		script = LoadScriptFile(token.string);
 		if (!script)
 		{
-			Q_strncpyz(path, source->includepath, sizeof(path));
-			Q_strcat(path, sizeof(path), token.string);
+			strcpy(path, source->includepath);
+			strcat(path, token.string);
 			script = LoadScriptFile(path);
 		} //end if
 	} //end if
 	else if (token.type == TT_PUNCTUATION && *token.string == '<')
 	{
-		Q_strncpyz(path, source->includepath, sizeof(path));
+		strcpy(path, source->includepath);
 		while(PC_ReadSourceToken(source, &token))
 		{
 			if (token.linescrossed > 0)
@@ -1012,7 +1011,7 @@
 				break;
 			} //end if
 			if (token.type == TT_PUNCTUATION && *token.string == '>') break;
-			Q_strcat(path, sizeof(path), token.string);
+			strncat(path, token.string, MAX_PATH - 1);
 		} //end while
 		if (*token.string != '>')
 		{
@@ -1036,7 +1035,7 @@
 	{
 		Com_Memset(&file, 0, sizeof(foundfile_t));
 		script = LoadScriptFile(path);
-		if (script) Q_strncpyz(script->filename, path, sizeof(script->filename));
+		if (script) strncpy(script->filename, path, MAX_PATH);
 	} //end if
 #endif //QUAKE
 	if (!script)
@@ -1324,7 +1323,7 @@
 	script = LoadScriptMemory(string, strlen(string), "*extern");
 	//create a new source
 	Com_Memset(&src, 0, sizeof(source_t));
-	Q_strncpyz(src.filename, "*extern", sizeof(src.filename));
+	strncpy(src.filename, "*extern", MAX_PATH);
 	src.scriptstack = script;
 #if DEFINEHASHING
 	src.definehash = GetClearedMemory(DEFINEHASHSIZE * sizeof(define_t *));
@@ -2087,12 +2086,9 @@
 			//remove the second value if not question mark operator
 			if (o->operator != P_QUESTIONMARK) v = v->next;
 			//
-			if (v)
-			{
-				if (v->prev) v->prev->next = v->next;
-				else firstvalue = v->next;
-				if (v->next) v->next->prev = v->prev;
-			}
+			if (v->prev) v->prev->next = v->next;
+			else firstvalue = v->next;
+			if (v->next) v->next->prev = v->prev;
 			//FreeMemory(v);
 			FreeValue(v);
 		} //end if
@@ -2446,7 +2442,7 @@
 	token.whitespace_p = source->scriptstack->script_p;
 	token.endwhitespace_p = source->scriptstack->script_p;
 	token.linescrossed = 0;
-	sprintf(token.string, "%ld", labs(value));
+	sprintf(token.string, "%d", abs(value));
 	token.type = TT_NUMBER;
 	token.subtype = TT_INTEGER|TT_LONG|TT_DECIMAL;
 	PC_UnreadSourceToken(source, &token);
@@ -2551,12 +2547,12 @@
 	token.whitespace_p = source->scriptstack->script_p;
 	token.endwhitespace_p = source->scriptstack->script_p;
 	token.linescrossed = 0;
-	sprintf(token.string, "%ld", labs(value));
+	sprintf(token.string, "%d", abs(value));
 	token.type = TT_NUMBER;
 	token.subtype = TT_INTEGER|TT_LONG|TT_DECIMAL;
 
 #ifdef NUMBERVALUE
-	token.intvalue = labs(value);
+	token.intvalue = abs(value);
 	token.floatvalue = token.intvalue;
 #endif //NUMBERVALUE
 
@@ -2835,7 +2831,6 @@
 	{
 		if ((token->subtype & subtype) != subtype)
 		{
-			strcpy(str, "");
 			if (subtype & TT_DECIMAL) strcpy(str, "decimal");
 			if (subtype & TT_HEX) strcpy(str, "hex");
 			if (subtype & TT_OCTAL) strcpy(str, "octal");
@@ -2959,14 +2954,10 @@
 //============================================================================
 void PC_SetIncludePath(source_t *source, char *path)
 {
-	size_t len;
-
-	Q_strncpyz(source->includepath, path, sizeof(source->includepath)-1);
-
-	len = strlen(source->includepath);
+	strncpy(source->includepath, path, MAX_PATH);
 	//add trailing path seperator
-	if (len > 0 && source->includepath[len-1] != '\\' &&
-		source->includepath[len-1] != '/')
+	if (source->includepath[strlen(source->includepath)-1] != '\\' &&
+		source->includepath[strlen(source->includepath)-1] != '/')
 	{
 		strcat(source->includepath, PATHSEPERATOR_STR);
 	} //end if
@@ -3002,7 +2993,7 @@
 	source = (source_t *) GetMemory(sizeof(source_t));
 	Com_Memset(source, 0, sizeof(source_t));
 
-	Q_strncpyz(source->filename, filename, sizeof(source->filename));
+	strncpy(source->filename, filename, MAX_PATH);
 	source->scriptstack = script;
 	source->tokens = NULL;
 	source->defines = NULL;
@@ -3035,7 +3026,7 @@
 	source = (source_t *) GetMemory(sizeof(source_t));
 	Com_Memset(source, 0, sizeof(source_t));
 
-	Q_strncpyz(source->filename, name, sizeof(source->filename));
+	strncpy(source->filename, name, MAX_PATH);
 	source->scriptstack = script;
 	source->tokens = NULL;
 	source->defines = NULL;

```
