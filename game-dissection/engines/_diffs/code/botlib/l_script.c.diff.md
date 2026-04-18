# Diff: `code/botlib/l_script.c`
**Canonical:** `wolfcamql-src` (sha256 `4f513ce79c3f...`, 41908 bytes)

## Variants

### `quake3-source`  — sha256 `d412466949e9...`, 41814 bytes

_Diff stat: +52 / -64 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.c	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_script.c	2026-04-16 20:02:19.857903700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -49,8 +49,8 @@
 
 #ifdef BOTLIB
 //include files for usage in the bot library
-#include "../qcommon/q_shared.h"
-#include "botlib.h"
+#include "../game/q_shared.h"
+#include "../game/botlib.h"
 #include "be_interface.h"
 #include "l_script.h"
 #include "l_memory.h"
@@ -160,7 +160,9 @@
 	{NULL, 0}
 };
 
-#ifdef BOTLIB
+#ifdef BSPC
+char basefolder[MAX_PATH];
+#else
 char basefolder[MAX_QPATH];
 #endif
 
@@ -218,7 +220,7 @@
 	{
 		if (script->punctuations[i].n == num) return script->punctuations[i].p;
 	} //end for
-	return "unknown punctuation";
+	return "unkown punctuation";
 } //end of the function PunctuationFromNum
 //===========================================================================
 //
@@ -234,7 +236,7 @@
 	if (script->flags & SCFL_NOERRORS) return;
 
 	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	vsprintf(text, str, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_ERROR, "file %s, line %d: %s\n", script->filename, script->line, text);
@@ -260,7 +262,7 @@
 	if (script->flags & SCFL_NOWARNINGS) return;
 
 	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	vsprintf(text, str, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_WARNING, "file %s, line %d: %s\n", script->filename, script->line, text);
@@ -356,7 +358,7 @@
 //============================================================================
 int PS_ReadEscapeCharacter(script_t *script, char *ch)
 {
-	int c, val;
+	int c, val, i;
 
 	//step over the leading '\\'
 	script->script_p++;
@@ -377,7 +379,7 @@
 		case 'x':
 		{
 			script->script_p++;
-			for (val = 0; ; script->script_p++)
+			for (i = 0, val = 0; ; i++, script->script_p++)
 			{
 				c = *script->script_p;
 				if (c >= '0' && c <= '9') c = c - '0';
@@ -398,7 +400,7 @@
 		default: //NOTE: decimal ASCII code, NOT octal
 		{
 			if (*script->script_p < '0' || *script->script_p > '9') ScriptError(script, "unknown escape char");
-			for (val = 0; ; script->script_p++)
+			for (i = 0, val = 0; ; i++, script->script_p++)
 			{
 				c = *script->script_p;
 				if (c >= '0' && c <= '9') c = c - '0';
@@ -419,7 +421,7 @@
 	script->script_p++;
 	//store the escape character
 	*ch = c;
-	//successfully read escape character
+	//succesfully read escape character
 	return 1;
 } //end of the function PS_ReadEscapeCharacter
 //============================================================================
@@ -429,7 +431,7 @@
 //
 // Parameter:				script		: script to read from
 //								token			: buffer to store the string
-// Returns:					qtrue when a string was read successfully
+// Returns:					qtrue when a string was read succesfully
 // Changes Globals:		-
 //============================================================================
 int PS_ReadString(script_t *script, token_t *token, int quote)
@@ -552,7 +554,7 @@
 // Changes Globals:		-
 //============================================================================
 void NumberValue(char *string, int subtype, unsigned long int *intvalue,
-															float *floatvalue)
+															long double *floatvalue)
 {
 	unsigned long int dotfound = 0;
 
@@ -571,13 +573,13 @@
 			} //end if
 			if (dotfound)
 			{
-				*floatvalue = *floatvalue + (float) (*string - '0') /
-																	(float) dotfound;
+				*floatvalue = *floatvalue + (long double) (*string - '0') /
+																	(long double) dotfound;
 				dotfound *= 10;
 			} //end if
 			else
 			{
-				*floatvalue = *floatvalue * 10.0 + (float) (*string - '0');
+				*floatvalue = *floatvalue * 10.0 + (long double) (*string - '0');
 			} //end else
 			string++;
 		} //end while
@@ -629,7 +631,7 @@
 	int octal, dot;
 	char c;
 //	unsigned long int intvalue = 0;
-//	double floatvalue = 0;
+//	long double floatvalue = 0;
 
 	token->type = TT_NUMBER;
 	//check for a hexadecimal number
@@ -643,7 +645,7 @@
 		//hexadecimal
 		while((c >= '0' && c <= '9') ||
 					(c >= 'a' && c <= 'f') ||
-					(c >= 'A' && c <= 'F'))
+					(c >= 'A' && c <= 'A'))
 		{
 			token->string[len++] = *script->script_p++;
 			if (len >= MAX_TOKEN)
@@ -704,14 +706,14 @@
 	{
 		c = *script->script_p;
 		//check for a LONG number
-		if ( (c == 'l' || c == 'L')
+		if ( (c == 'l' || c == 'L') // bk001204 - brackets 
 		     && !(token->subtype & TT_LONG))
 		{
 			script->script_p++;
 			token->subtype |= TT_LONG;
 		} //end if
 		//check for an UNSIGNED number
-		else if ( (c == 'u' || c == 'U')
+		else if ( (c == 'u' || c == 'U') // bk001204 - brackets 
 			  && !(token->subtype & (TT_UNSIGNED | TT_FLOAT)))
 		{
 			script->script_p++;
@@ -802,7 +804,7 @@
 			//if the script contains the punctuation
 			if (!strncmp(script->script_p, p, len))
 			{
-				Q_strncpyz(token->string, p, MAX_TOKEN);
+				strncpy(token->string, p, MAX_TOKEN);
 				script->script_p += len;
 				token->type = TT_PUNCTUATION;
 				//sub type is the number of the punctuation
@@ -826,7 +828,7 @@
 	len = 0;
 	while(*script->script_p > ' ' && *script->script_p != ';')
 	{
-		if (len >= MAX_TOKEN - 1)
+		if (len >= MAX_TOKEN)
 		{
 			ScriptError(script, "primitive token longer than MAX_TOKEN = %d", MAX_TOKEN);
 			return 0;
@@ -836,7 +838,7 @@
 	token->string[len] = 0;
 	//copy the token into the script structure
 	Com_Memcpy(&script->token, token, sizeof(token_t));
-	//primitive reading successful
+	//primitive reading successfull
 	return 1;
 } //end of the function PS_ReadPrimitive
 //============================================================================
@@ -877,7 +879,7 @@
 	{
 		if (!PS_ReadString(script, token, '\"')) return 0;
 	} //end if
-	//if a literal
+	//if an literal
 	else if (*script->script_p == '\'')
 	{
 		//if (!PS_ReadLiteral(script, token)) return 0;
@@ -898,7 +900,7 @@
 	//if there is a name
 	else if ((*script->script_p >= 'a' && *script->script_p <= 'z') ||
 		(*script->script_p >= 'A' && *script->script_p <= 'Z') ||
-		*script->script_p == '_'  ||  *script->script_p == '@')
+		*script->script_p == '_')
 	{
 		if (!PS_ReadName(script, token)) return 0;
 	} //end if
@@ -910,7 +912,7 @@
 	} //end if
 	//copy the token into the script structure
 	Com_Memcpy(&script->token, token, sizeof(token_t));
-	//successfully read a token
+	//succesfully read a token
 	return 1;
 } //end of the function PS_ReadToken
 //============================================================================
@@ -954,7 +956,6 @@
 
 	if (token->type != type)
 	{
-		strcpy(str, "");
 		if (type == TT_STRING) strcpy(str, "string");
 		if (type == TT_LITERAL) strcpy(str, "literal");
 		if (type == TT_NUMBER) strcpy(str, "number");
@@ -967,7 +968,6 @@
 	{
 		if ((token->subtype & subtype) != subtype)
 		{
-			strcpy(str, "");
 			if (subtype & TT_DECIMAL) strcpy(str, "decimal");
 			if (subtype & TT_HEX) strcpy(str, "hex");
 			if (subtype & TT_OCTAL) strcpy(str, "octal");
@@ -990,7 +990,7 @@
 		if (token->subtype != subtype)
 		{
 			ScriptError(script, "expected %s, found %s",
-							script->punctuations[subtype].p, token->string);
+							script->punctuations[subtype], token->string);
 			return 0;
 		} //end if
 	} //end else if
@@ -1118,7 +1118,7 @@
 {
 	if (*string == '\"')
 	{
-		memmove(string, string+1, strlen(string));
+		strcpy(string, string+1);
 	} //end if
 	if (string[strlen(string)-1] == '\"')
 	{
@@ -1135,7 +1135,7 @@
 {
 	if (*string == '\'')
 	{
-		memmove(string, string+1, strlen(string));
+		strcpy(string, string+1);
 	} //end if
 	if (string[strlen(string)-1] == '\'')
 	{
@@ -1148,29 +1148,21 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-float ReadSignedFloat(script_t *script)
+long double ReadSignedFloat(script_t *script)
 {
 	token_t token;
-	float sign = 1.0;
+	long double sign = 1;
 
 	PS_ExpectAnyToken(script, &token);
 	if (!strcmp(token.string, "-"))
 	{
-		if(!PS_ExpectAnyToken(script, &token))
-		{
-			ScriptError(script, "Missing float value");
-			return 0;
-		}
-
-		sign = -1.0;
-	}
-	
-	if (token.type != TT_NUMBER)
+		sign = -1;
+		PS_ExpectTokenType(script, TT_NUMBER, 0, &token);
+	} //end if
+	else if (token.type != TT_NUMBER)
 	{
-		ScriptError(script, "expected float value, found %s", token.string);
-		return 0;
-	}
-
+		ScriptError(script, "expected float value, found %s\n", token.string);
+	} //end else if
 	return sign * token.floatvalue;
 } //end of the function ReadSignedFloat
 //============================================================================
@@ -1187,21 +1179,13 @@
 	PS_ExpectAnyToken(script, &token);
 	if (!strcmp(token.string, "-"))
 	{
-		if(!PS_ExpectAnyToken(script, &token))
-		{
-			ScriptError(script, "Missing integer value");
-			return 0;
-		}
-
 		sign = -1;
-	}
-
-	if (token.type != TT_NUMBER || token.subtype == TT_FLOAT)
+		PS_ExpectTokenType(script, TT_NUMBER, TT_INTEGER, &token);
+	} //end if
+	else if (token.type != TT_NUMBER || token.subtype == TT_FLOAT)
 	{
-		ScriptError(script, "expected integer value, found %s", token.string);
-		return 0;
-	}
-	
+		ScriptError(script, "expected integer value, found %s\n", token.string);
+	} //end else if
 	return sign * token.intvalue;
 } //end of the function ReadSignedInt
 //============================================================================
@@ -1350,7 +1334,7 @@
 	buffer = GetClearedMemory(sizeof(script_t) + length + 1);
 	script = (script_t *) buffer;
 	Com_Memset(script, 0, sizeof(script_t));
-	Q_strncpyz(script->filename, filename, sizeof(script->filename));
+	strcpy(script->filename, filename);
 	script->buffer = (char *) buffer + sizeof(script_t);
 	script->buffer[length] = 0;
 	script->length = length;
@@ -1379,6 +1363,8 @@
 	} //end if
 	fclose(fp);
 #endif
+	//
+	script->length = COM_Compress(script->buffer);
 
 	return script;
 } //end of the function LoadScriptFile
@@ -1396,7 +1382,7 @@
 	buffer = GetClearedMemory(sizeof(script_t) + length + 1);
 	script = (script_t *) buffer;
 	Com_Memset(script, 0, sizeof(script_t));
-	Q_strncpyz(script->filename, name, sizeof(script->filename));
+	strcpy(script->filename, name);
 	script->buffer = (char *) buffer + sizeof(script_t);
 	script->buffer[length] = 0;
 	script->length = length;
@@ -1439,7 +1425,9 @@
 //============================================================================
 void PS_SetBaseFolder(char *path)
 {
-#ifdef BOTLIB
-	Com_sprintf(basefolder, sizeof(basefolder), "%s", path);
+#ifdef BSPC
+	sprintf(basefolder, path);
+#else
+	Com_sprintf(basefolder, sizeof(basefolder), path);
 #endif
 } //end of the function PS_SetBaseFolder

```

### `ioquake3`  — sha256 `8c3c0ab7838d...`, 41878 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.c	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\botlib\l_script.c	2026-04-16 20:02:21.516486500 +0100
@@ -898,7 +898,7 @@
 	//if there is a name
 	else if ((*script->script_p >= 'a' && *script->script_p <= 'z') ||
 		(*script->script_p >= 'A' && *script->script_p <= 'Z') ||
-		*script->script_p == '_'  ||  *script->script_p == '@')
+		*script->script_p == '_')
 	{
 		if (!PS_ReadName(script, token)) return 0;
 	} //end if

```

### `quake3e`  — sha256 `cc64a366055a...`, 42303 bytes

_Diff stat: +83 / -56 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.c	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_script.c	2026-04-16 20:02:26.907505100 +0100
@@ -83,7 +83,7 @@
 #define PUNCTABLE
 
 //longer punctuations first
-punctuation_t default_punctuations[] =
+static punctuation_t default_punctuations[] =
 {
 	//binary operators
 	{">>=",P_RSHIFT_ASSIGN, NULL},
@@ -99,7 +99,7 @@
 	{"<=",P_LOGIC_LEQ, NULL},
 	{"==",P_LOGIC_EQ, NULL},
 	{"!=",P_LOGIC_UNEQ, NULL},
-	//arithmatic operators
+	//arithmetic operators
 	{"*=",P_MUL_ASSIGN, NULL},
 	{"/=",P_DIV_ASSIGN, NULL},
 	{"%=",P_MOD_ASSIGN, NULL},
@@ -118,7 +118,7 @@
 	//C++
 	{"::",P_CPP1, NULL},
 	{".*",P_CPP2, NULL},
-	//arithmatic operators
+	//arithmetic operators
 	{"*",P_MUL, NULL},
 	{"/",P_DIV, NULL},
 	{"%",P_MOD, NULL},
@@ -136,7 +136,7 @@
 	{"<",P_LOGIC_LESS, NULL},
 	//reference operator
 	{".",P_REF, NULL},
-	//seperators
+	//separators
 	{",",P_COMMA, NULL},
 	{";",P_SEMICOLON, NULL},
 	//label indication
@@ -160,8 +160,10 @@
 	{NULL, 0}
 };
 
-#ifdef BOTLIB
-char basefolder[MAX_QPATH];
+#ifdef BSPC
+static char basefolder[MAX_PATH];
+#else
+static char basefolder[MAX_QPATH];
 #endif
 
 //===========================================================================
@@ -170,7 +172,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void PS_CreatePunctuationTable(script_t *script, punctuation_t *punctuations)
+static void PS_CreatePunctuationTable(script_t *script, punctuation_t *punctuations)
 {
 	int i;
 	punctuation_t *p, *lastp, *newp;
@@ -210,7 +212,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *PunctuationFromNum(script_t *script, int num)
+const char *PunctuationFromNum(script_t *script, int num)
 {
 	int i;
 
@@ -226,15 +228,15 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void QDECL ScriptError(script_t *script, char *str, ...)
+void QDECL ScriptError(script_t *script, const char *fmt, ...)
 {
 	char text[1024];
 	va_list ap;
 
 	if (script->flags & SCFL_NOERRORS) return;
 
-	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	va_start(ap, fmt);
+	Q_vsnprintf(text, sizeof(text), fmt, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_ERROR, "file %s, line %d: %s\n", script->filename, script->line, text);
@@ -252,15 +254,15 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void QDECL ScriptWarning(script_t *script, char *str, ...)
+static void QDECL ScriptWarning(script_t *script, const char *fmt, ...)
 {
 	char text[1024];
 	va_list ap;
 
 	if (script->flags & SCFL_NOWARNINGS) return;
 
-	va_start(ap, str);
-	Q_vsnprintf(text, sizeof(text), str, ap);
+	va_start(ap, fmt);
+	Q_vsnprintf(text, sizeof(text), fmt, ap);
 	va_end(ap);
 #ifdef BOTLIB
 	botimport.Print(PRT_WARNING, "file %s, line %d: %s\n", script->filename, script->line, text);
@@ -278,7 +280,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void SetScriptPunctuations(script_t *script, punctuation_t *p)
+static void SetScriptPunctuations(script_t *script, punctuation_t *p)
 {
 #ifdef PUNCTABLE
 	if (p) PS_CreatePunctuationTable(script, p);
@@ -295,7 +297,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadWhiteSpace(script_t *script)
+static int PS_ReadWhiteSpace(script_t *script)
 {
 	while(1)
 	{
@@ -354,7 +356,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadEscapeCharacter(script_t *script, char *ch)
+static int PS_ReadEscapeCharacter(script_t *script, char *ch)
 {
 	int c, val;
 
@@ -377,40 +379,46 @@
 		case 'x':
 		{
 			script->script_p++;
-			for (val = 0; ; script->script_p++)
+			for (val = 0; ;script->script_p++)
 			{
 				c = *script->script_p;
-				if (c >= '0' && c <= '9') c = c - '0';
-				else if (c >= 'A' && c <= 'Z') c = c - 'A' + 10;
-				else if (c >= 'a' && c <= 'z') c = c - 'a' + 10;
-				else break;
+				if (c >= '0' && c <= '9')
+					c = c - '0';
+				else if (c >= 'A' && c <= 'Z')
+					c = c - 'A' + 10;
+				else if (c >= 'a' && c <= 'z')
+					c = c - 'a' + 10;
+				else
+					break;
 				val = (val << 4) + c;
-			} //end for
+			}
 			script->script_p--;
 			if (val > 0xFF)
 			{
 				ScriptWarning(script, "too large value in escape character");
 				val = 0xFF;
-			} //end if
+			}
 			c = val;
 			break;
 		} //end case
 		default: //NOTE: decimal ASCII code, NOT octal
 		{
 			if (*script->script_p < '0' || *script->script_p > '9') ScriptError(script, "unknown escape char");
-			for (val = 0; ; script->script_p++)
+			for (val = 0; ;script->script_p++)
 			{
 				c = *script->script_p;
-				if (c >= '0' && c <= '9') c = c - '0';
-				else break;
+				if (c >= '0' && c <= '9')
+					c = c - '0';
+				else
+					break;
 				val = val * 10 + c;
-			} //end for
+			}
 			script->script_p--;
 			if (val > 0xFF)
 			{
 				ScriptWarning(script, "too large value in escape character");
 				val = 0xFF;
-			} //end if
+			}
 			c = val;
 			break;
 		} //end default
@@ -432,7 +440,7 @@
 // Returns:					qtrue when a string was read successfully
 // Changes Globals:		-
 //============================================================================
-int PS_ReadString(script_t *script, token_t *token, int quote)
+static int PS_ReadString(script_t *script, token_t *token, int quote)
 {
 	int len, tmpline;
 	char *tmpscript_p;
@@ -473,7 +481,7 @@
 			//
 			tmpscript_p = script->script_p;
 			tmpline = script->line;
-			//read unusefull stuff between possible two following strings
+			//read unuseful stuff between possible two following strings
 			if (!PS_ReadWhiteSpace(script))
 			{
 				script->script_p = tmpscript_p;
@@ -521,7 +529,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadName(script_t *script, token_t *token)
+static int PS_ReadName(script_t *script, token_t *token)
 {
 	int len = 0;
 	char c;
@@ -551,7 +559,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-void NumberValue(char *string, int subtype, unsigned long int *intvalue,
+static void NumberValue(char *string, int subtype, unsigned long int *intvalue,
 															float *floatvalue)
 {
 	unsigned long int dotfound = 0;
@@ -623,7 +631,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadNumber(script_t *script, token_t *token)
+static int PS_ReadNumber(script_t *script, token_t *token)
 {
 	int len = 0, i;
 	int octal, dot;
@@ -725,13 +733,14 @@
 	if (!(token->subtype & TT_FLOAT)) token->subtype |= TT_INTEGER;
 	return 1;
 } //end of the function PS_ReadNumber
+#if 0
 //============================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadLiteral(script_t *script, token_t *token)
+static int PS_ReadLiteral(script_t *script, token_t *token)
 {
 	token->type = TT_LITERAL;
 	//first quote
@@ -772,16 +781,17 @@
 	//
 	return 1;
 } //end of the function PS_ReadLiteral
+#endif
 //============================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadPunctuation(script_t *script, token_t *token)
+static int PS_ReadPunctuation(script_t *script, token_t *token)
 {
 	int len;
-	char *p;
+	const char *p;
 	punctuation_t *punc;
 
 #ifdef PUNCTABLE
@@ -802,7 +812,7 @@
 			//if the script contains the punctuation
 			if (!strncmp(script->script_p, p, len))
 			{
-				Q_strncpyz(token->string, p, MAX_TOKEN);
+				Q_strncpyz( token->string, p, sizeof( token->string ) );
 				script->script_p += len;
 				token->type = TT_PUNCTUATION;
 				//sub type is the number of the punctuation
@@ -819,7 +829,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ReadPrimitive(script_t *script, token_t *token)
+static int PS_ReadPrimitive(script_t *script, token_t *token)
 {
 	int len;
 
@@ -863,7 +873,7 @@
 	//start of the white space
 	script->whitespace_p = script->script_p;
 	token->whitespace_p = script->script_p;
-	//read unusefull stuff
+	//read unuseful stuff
 	if (!PS_ReadWhiteSpace(script)) return 0;
 	//end of the white space
 	script->endwhitespace_p = script->script_p;
@@ -898,7 +908,7 @@
 	//if there is a name
 	else if ((*script->script_p >= 'a' && *script->script_p <= 'z') ||
 		(*script->script_p >= 'A' && *script->script_p <= 'Z') ||
-		*script->script_p == '_'  ||  *script->script_p == '@')
+		*script->script_p == '_')
 	{
 		if (!PS_ReadName(script, token)) return 0;
 	} //end if
@@ -913,13 +923,14 @@
 	//successfully read a token
 	return 1;
 } //end of the function PS_ReadToken
+#if 0
 //============================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_ExpectTokenString(script_t *script, char *string)
+int PS_ExpectTokenString(script_t *script, const char *string)
 {
 	token_t token;
 
@@ -936,6 +947,7 @@
 	} //end if
 	return 1;
 } //end of the function PS_ExpectToken
+#endif
 //============================================================================
 //
 // Parameter:				-
@@ -1014,13 +1026,14 @@
 		return 1;
 	} //end else
 } //end of the function PS_ExpectAnyToken
+#if 0
 //============================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_CheckTokenString(script_t *script, char *string)
+int PS_CheckTokenString(script_t *script, const char *string)
 {
 	token_t tok;
 
@@ -1059,7 +1072,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int PS_SkipUntilString(script_t *script, char *string)
+int PS_SkipUntilString(script_t *script, const char *string)
 {
 	token_t token;
 
@@ -1069,6 +1082,7 @@
 	} //end while
 	return 0;
 } //end of the function PS_SkipUntilString
+#endif
 //============================================================================
 //
 // Parameter:				-
@@ -1079,6 +1093,7 @@
 {
 	script->tokenavailable = 1;
 } //end of the function UnreadLastToken
+#if 0
 //============================================================================
 //
 // Parameter:				-
@@ -1108,6 +1123,7 @@
 		return 0;
 	} //end else
 } //end of the function PS_NextWhiteSpaceChar
+#endif
 //============================================================================
 //
 // Parameter:				-
@@ -1142,6 +1158,7 @@
 		string[strlen(string)-1] = '\0';
 	} //end if
 } //end of the function StripSingleQuotes
+#if 0
 //============================================================================
 //
 // Parameter:				-
@@ -1204,6 +1221,7 @@
 	
 	return sign * token.intvalue;
 } //end of the function ReadSignedInt
+#endif
 //============================================================================
 //
 // Parameter:				-
@@ -1214,6 +1232,7 @@
 {
 	script->flags = flags;
 } //end of the function SetScriptFlags
+#if 0
 //============================================================================
 //
 // Parameter:				-
@@ -1248,6 +1267,7 @@
 	//clear the saved token
 	Com_Memset(&script->token, 0, sizeof(token_t));
 } //end of the function ResetScript
+#endif
 //============================================================================
 // returns true if at the end of the script
 //
@@ -1259,6 +1279,7 @@
 {
 	return script->script_p >= script->end_p;
 } //end of the function EndOfScript
+#if 0
 //============================================================================
 //
 // Parameter:				-
@@ -1295,6 +1316,7 @@
 		script->script_p++;
 	} while(1);
 } //end of the function ScriptSkipTo
+#endif
 #ifndef BOTLIB
 //============================================================================
 //
@@ -1302,7 +1324,7 @@
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-int FileLength(FILE *fp)
+static int FileLength(FILE *fp)
 {
 	int pos;
 	int end;
@@ -1325,7 +1347,7 @@
 {
 #ifdef BOTLIB
 	fileHandle_t fp;
-	char pathname[MAX_QPATH];
+	char pathname[MAX_QPATH*2];
 #else
 	FILE *fp;
 #endif
@@ -1334,14 +1356,15 @@
 	script_t *script;
 
 #ifdef BOTLIB
-	if (strlen(basefolder))
-		Com_sprintf(pathname, sizeof(pathname), "%s/%s", basefolder, filename);
+	if ( basefolder[0] != '\0' )
+		Com_sprintf( pathname, sizeof( pathname ), "%s/%s", basefolder, filename );
 	else
-		Com_sprintf(pathname, sizeof(pathname), "%s", filename);
+		Com_sprintf( pathname, sizeof( pathname ), "%s", filename );
+
 	length = botimport.FS_FOpenFile( pathname, &fp, FS_READ );
 	if (!fp) return NULL;
 #else
-	fp = fopen(filename, "rb");
+	fp = Sys_FOpen(filename, "rb");
 	if (!fp) return NULL;
 
 	length = FileLength(fp);
@@ -1369,7 +1392,11 @@
 	SetScriptPunctuations(script, NULL);
 	//
 #ifdef BOTLIB
-	botimport.FS_Read(script->buffer, length, fp);
+	if (botimport.FS_Read(script->buffer, length, fp) != length)
+	{
+		FreeMemory(buffer);
+		script = NULL;
+	}
 	botimport.FS_FCloseFile(fp);
 #else
 	if (fread(script->buffer, length, 1, fp) != 1)
@@ -1388,7 +1415,7 @@
 // Returns:				-
 // Changes Globals:		-
 //============================================================================
-script_t *LoadScriptMemory(char *ptr, int length, char *name)
+script_t *LoadScriptMemory(const char *ptr, int length, const char *name)
 {
 	void *buffer;
 	script_t *script;
@@ -1432,14 +1459,14 @@
 	FreeMemory(script);
 } //end of the function FreeScript
 //============================================================================
+// set the base folder to load files from
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //============================================================================
-void PS_SetBaseFolder(char *path)
+void PS_SetBaseFolder( const char *path )
 {
-#ifdef BOTLIB
-	Com_sprintf(basefolder, sizeof(basefolder), "%s", path);
-#endif
+	Q_strncpyz( basefolder, path, sizeof( basefolder ) );
 } //end of the function PS_SetBaseFolder
+

```

### `openarena-engine`  — sha256 `fafb0050b7c4...`, 41864 bytes

_Diff stat: +17 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.c	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_script.c	2026-04-16 22:48:25.720197700 +0100
@@ -160,7 +160,9 @@
 	{NULL, 0}
 };
 
-#ifdef BOTLIB
+#ifdef BSPC
+char basefolder[MAX_PATH];
+#else
 char basefolder[MAX_QPATH];
 #endif
 
@@ -218,7 +220,7 @@
 	{
 		if (script->punctuations[i].n == num) return script->punctuations[i].p;
 	} //end for
-	return "unknown punctuation";
+	return "unkown punctuation";
 } //end of the function PunctuationFromNum
 //===========================================================================
 //
@@ -356,7 +358,7 @@
 //============================================================================
 int PS_ReadEscapeCharacter(script_t *script, char *ch)
 {
-	int c, val;
+	int c, val, i;
 
 	//step over the leading '\\'
 	script->script_p++;
@@ -377,7 +379,7 @@
 		case 'x':
 		{
 			script->script_p++;
-			for (val = 0; ; script->script_p++)
+			for (i = 0, val = 0; ; i++, script->script_p++)
 			{
 				c = *script->script_p;
 				if (c >= '0' && c <= '9') c = c - '0';
@@ -398,7 +400,7 @@
 		default: //NOTE: decimal ASCII code, NOT octal
 		{
 			if (*script->script_p < '0' || *script->script_p > '9') ScriptError(script, "unknown escape char");
-			for (val = 0; ; script->script_p++)
+			for (i = 0, val = 0; ; i++, script->script_p++)
 			{
 				c = *script->script_p;
 				if (c >= '0' && c <= '9') c = c - '0';
@@ -643,7 +645,7 @@
 		//hexadecimal
 		while((c >= '0' && c <= '9') ||
 					(c >= 'a' && c <= 'f') ||
-					(c >= 'A' && c <= 'F'))
+					(c >= 'A' && c <= 'A'))
 		{
 			token->string[len++] = *script->script_p++;
 			if (len >= MAX_TOKEN)
@@ -802,7 +804,7 @@
 			//if the script contains the punctuation
 			if (!strncmp(script->script_p, p, len))
 			{
-				Q_strncpyz(token->string, p, MAX_TOKEN);
+				strncpy(token->string, p, MAX_TOKEN);
 				script->script_p += len;
 				token->type = TT_PUNCTUATION;
 				//sub type is the number of the punctuation
@@ -826,7 +828,7 @@
 	len = 0;
 	while(*script->script_p > ' ' && *script->script_p != ';')
 	{
-		if (len >= MAX_TOKEN - 1)
+		if (len >= MAX_TOKEN)
 		{
 			ScriptError(script, "primitive token longer than MAX_TOKEN = %d", MAX_TOKEN);
 			return 0;
@@ -836,7 +838,7 @@
 	token->string[len] = 0;
 	//copy the token into the script structure
 	Com_Memcpy(&script->token, token, sizeof(token_t));
-	//primitive reading successful
+	//primitive reading successfull
 	return 1;
 } //end of the function PS_ReadPrimitive
 //============================================================================
@@ -898,7 +900,7 @@
 	//if there is a name
 	else if ((*script->script_p >= 'a' && *script->script_p <= 'z') ||
 		(*script->script_p >= 'A' && *script->script_p <= 'Z') ||
-		*script->script_p == '_'  ||  *script->script_p == '@')
+		*script->script_p == '_')
 	{
 		if (!PS_ReadName(script, token)) return 0;
 	} //end if
@@ -954,7 +956,6 @@
 
 	if (token->type != type)
 	{
-		strcpy(str, "");
 		if (type == TT_STRING) strcpy(str, "string");
 		if (type == TT_LITERAL) strcpy(str, "literal");
 		if (type == TT_NUMBER) strcpy(str, "number");
@@ -967,7 +968,6 @@
 	{
 		if ((token->subtype & subtype) != subtype)
 		{
-			strcpy(str, "");
 			if (subtype & TT_DECIMAL) strcpy(str, "decimal");
 			if (subtype & TT_HEX) strcpy(str, "hex");
 			if (subtype & TT_OCTAL) strcpy(str, "octal");
@@ -1350,7 +1350,7 @@
 	buffer = GetClearedMemory(sizeof(script_t) + length + 1);
 	script = (script_t *) buffer;
 	Com_Memset(script, 0, sizeof(script_t));
-	Q_strncpyz(script->filename, filename, sizeof(script->filename));
+	strcpy(script->filename, filename);
 	script->buffer = (char *) buffer + sizeof(script_t);
 	script->buffer[length] = 0;
 	script->length = length;
@@ -1396,7 +1396,7 @@
 	buffer = GetClearedMemory(sizeof(script_t) + length + 1);
 	script = (script_t *) buffer;
 	Com_Memset(script, 0, sizeof(script_t));
-	Q_strncpyz(script->filename, name, sizeof(script->filename));
+	strcpy(script->filename, name);
 	script->buffer = (char *) buffer + sizeof(script_t);
 	script->buffer[length] = 0;
 	script->length = length;
@@ -1439,7 +1439,9 @@
 //============================================================================
 void PS_SetBaseFolder(char *path)
 {
-#ifdef BOTLIB
+#ifdef BSPC
+	sprintf(basefolder, path);
+#else
 	Com_sprintf(basefolder, sizeof(basefolder), "%s", path);
 #endif
 } //end of the function PS_SetBaseFolder

```
