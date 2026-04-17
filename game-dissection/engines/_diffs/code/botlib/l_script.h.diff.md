# Diff: `code/botlib/l_script.h`
**Canonical:** `wolfcamql-src` (sha256 `8a0665995309...`, 8521 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `08d0cc98e218...`, 8471 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_script.h	2026-04-16 20:02:19.857903700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -161,7 +161,7 @@
 	int subtype;					//last read token sub type
 #ifdef NUMBERVALUE
 	unsigned long int intvalue;	//integer value
-	float floatvalue;			//floating point value
+	long double floatvalue;			//floating point value
 #endif //NUMBERVALUE
 	char *whitespace_p;				//start of white space before token
 	char *endwhitespace_p;			//start of white space before token
@@ -201,7 +201,7 @@
 int PS_ExpectAnyToken(script_t *script, token_t *token);
 //returns true when the token is available
 int PS_CheckTokenString(script_t *script, char *string);
-//returns true and reads the token when a token with the given type is available
+//returns true an reads the token when a token with the given type is available
 int PS_CheckTokenType(script_t *script, int type, int subtype, token_t *token);
 //skip tokens until the given token string is read
 int PS_SkipUntilString(script_t *script, char *string);
@@ -218,7 +218,7 @@
 //read a possible signed integer
 signed long int ReadSignedInt(script_t *script);
 //read a possible signed floating point number
-float ReadSignedFloat(script_t *script);
+long double ReadSignedFloat(script_t *script);
 //set an array with punctuations, NULL restores default C/C++ set
 void SetScriptPunctuations(script_t *script, punctuation_t *p);
 //set script flags
@@ -240,8 +240,8 @@
 //set the base folder to load files from
 void PS_SetBaseFolder(char *path);
 //print a script error with filename and line number
-void QDECL ScriptError(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptError(script_t *script, char *str, ...);
 //print a script warning with filename and line number
-void QDECL ScriptWarning(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptWarning(script_t *script, char *str, ...);
 
 

```

### `quake3e`  — sha256 `7b1e3b775ac5...`, 8341 bytes

_Diff stat: +19 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_script.h	2026-04-16 20:02:26.907505100 +0100
@@ -148,7 +148,7 @@
 //punctuation
 typedef struct punctuation_s
 {
-	char *p;						//punctuation character(s)
+	const char *p;						//punctuation character(s)
 	int n;							//punctuation indication
 	struct punctuation_s *next;		//next punctuation
 } punctuation_t;
@@ -193,55 +193,53 @@
 
 //read a token from the script
 int PS_ReadToken(script_t *script, token_t *token);
-//expect a certain token
-int PS_ExpectTokenString(script_t *script, char *string);
 //expect a certain token type
 int PS_ExpectTokenType(script_t *script, int type, int subtype, token_t *token);
 //expect a token
 int PS_ExpectAnyToken(script_t *script, token_t *token);
+#if 0
+//expect a certain token
+int PS_ExpectTokenString(script_t *script, const char *string);
 //returns true when the token is available
-int PS_CheckTokenString(script_t *script, char *string);
+int PS_CheckTokenString(script_t *script, const char *string);
 //returns true and reads the token when a token with the given type is available
 int PS_CheckTokenType(script_t *script, int type, int subtype, token_t *token);
 //skip tokens until the given token string is read
-int PS_SkipUntilString(script_t *script, char *string);
-//unread the last token read from the script
-void PS_UnreadLastToken(script_t *script);
+int PS_SkipUntilString(script_t *script, const char *string);
 //unread the given token
 void PS_UnreadToken(script_t *script, token_t *token);
 //returns the next character of the read white space, returns NULL if none
 char PS_NextWhiteSpaceChar(script_t *script);
-//remove any leading and trailing double quotes from the token
-void StripDoubleQuotes(char *string);
-//remove any leading and trailing single quotes from the token
-void StripSingleQuotes(char *string);
 //read a possible signed integer
 signed long int ReadSignedInt(script_t *script);
 //read a possible signed floating point number
 float ReadSignedFloat(script_t *script);
-//set an array with punctuations, NULL restores default C/C++ set
-void SetScriptPunctuations(script_t *script, punctuation_t *p);
-//set script flags
-void SetScriptFlags(script_t *script, int flags);
 //get script flags
 int GetScriptFlags(script_t *script);
 //reset a script
 void ResetScript(script_t *script);
+#endif
+//unread the last token read from the script
+void PS_UnreadLastToken(script_t *script);
+//remove any leading and trailing double quotes from the token
+void StripDoubleQuotes(char *string);
+//remove any leading and trailing single quotes from the token
+void StripSingleQuotes(char *string);
+//set script flags
+void SetScriptFlags(script_t *script, int flags);
 //returns true if at the end of the script
 int EndOfScript(script_t *script);
 //returns a pointer to the punctuation with the given number
-char *PunctuationFromNum(script_t *script, int num);
+const char *PunctuationFromNum(script_t *script, int num);
 //load a script from the given file at the given offset with the given length
 script_t *LoadScriptFile(const char *filename);
 //load a script from the given memory with the given length
-script_t *LoadScriptMemory(char *ptr, int length, char *name);
+script_t *LoadScriptMemory(const char *ptr, int length, const char *name);
 //free a script
 void FreeScript(script_t *script);
 //set the base folder to load files from
-void PS_SetBaseFolder(char *path);
+void PS_SetBaseFolder(const char *path);
 //print a script error with filename and line number
-void QDECL ScriptError(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
-//print a script warning with filename and line number
-void QDECL ScriptWarning(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptError(script_t *script, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 
 

```

### `openarena-engine`  — sha256 `1eb47ce2cec0...`, 8561 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_script.h	2026-04-16 22:48:25.720197700 +0100
@@ -240,8 +240,8 @@
 //set the base folder to load files from
 void PS_SetBaseFolder(char *path);
 //print a script error with filename and line number
-void QDECL ScriptError(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptError(script_t *script, char *str, ...) __attribute__ ((format (printf, 2, 3)));
 //print a script warning with filename and line number
-void QDECL ScriptWarning(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptWarning(script_t *script, char *str, ...) __attribute__ ((format (printf, 2, 3)));
 
 

```

### `openarena-gamecode`  — sha256 `7bf3640ccde4...`, 8480 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_script.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\l_script.h	2026-04-16 22:48:24.144820900 +0100
@@ -201,7 +201,7 @@
 int PS_ExpectAnyToken(script_t *script, token_t *token);
 //returns true when the token is available
 int PS_CheckTokenString(script_t *script, char *string);
-//returns true and reads the token when a token with the given type is available
+//returns true an reads the token when a token with the given type is available
 int PS_CheckTokenType(script_t *script, int type, int subtype, token_t *token);
 //skip tokens until the given token string is read
 int PS_SkipUntilString(script_t *script, char *string);
@@ -240,8 +240,8 @@
 //set the base folder to load files from
 void PS_SetBaseFolder(char *path);
 //print a script error with filename and line number
-void QDECL ScriptError(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptError(script_t *script, char *str, ...);
 //print a script warning with filename and line number
-void QDECL ScriptWarning(script_t *script, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL ScriptWarning(script_t *script, char *str, ...);
 
 

```
