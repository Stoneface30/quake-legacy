# Diff: `code/botlib/l_precomp.h`
**Canonical:** `wolfcamql-src` (sha256 `758f82ec8011...`, 6360 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `3a9fb7b12d9d...`, 6356 bytes

_Diff stat: +8 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.h	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_precomp.h	2026-04-16 20:02:19.857903700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,6 +29,10 @@
  *
  *****************************************************************************/
 
+#ifndef MAX_PATH
+	#define MAX_PATH			MAX_QPATH
+#endif
+
 #ifndef PATH_SEPERATORSTR
 	#if defined(WIN32)|defined(_WIN32)|defined(__NT__)|defined(__WINDOWS__)|defined(__WINDOWS_386__)
 		#define PATHSEPERATOR_STR		"\\"
@@ -113,7 +117,7 @@
 int PC_ExpectAnyToken(source_t *source, token_t *token);
 //returns true when the token is available
 int PC_CheckTokenString(source_t *source, char *string);
-//returns true and reads the token when a token with the given type is available
+//returns true an reads the token when a token with the given type is available
 int PC_CheckTokenType(source_t *source, int type, int subtype, token_t *token);
 //skip tokens until the given token string is read
 int PC_SkipUntilString(source_t *source, char *string);
@@ -148,9 +152,9 @@
 //free the given source
 void FreeSource(source_t *source);
 //print a source error
-void QDECL SourceError(source_t *source, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SourceError(source_t *source, char *str, ...);
 //print a source warning
-void QDECL SourceWarning(source_t *source, char *str, ...)  Q_PRINTF_FUNC(2, 3);
+void QDECL SourceWarning(source_t *source, char *str, ...);
 
 #ifdef BSPC
 // some of BSPC source does include game/q_shared.h and some does not

```

### `quake3e`  — sha256 `510cf1b49926...`, 6262 bytes

_Diff stat: +21 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.h	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_precomp.h	2026-04-16 20:02:26.906503400 +0100
@@ -29,6 +29,10 @@
  *
  *****************************************************************************/
 
+#ifndef MAX_PATH
+	#define MAX_PATH			MAX_QPATH
+#endif
+
 #ifndef PATH_SEPERATORSTR
 	#if defined(WIN32)|defined(_WIN32)|defined(__NT__)|defined(__WINDOWS__)|defined(__WINDOWS_386__)
 		#define PATHSEPERATOR_STR		"\\"
@@ -113,44 +117,42 @@
 int PC_ExpectAnyToken(source_t *source, token_t *token);
 //returns true when the token is available
 int PC_CheckTokenString(source_t *source, char *string);
-//returns true and reads the token when a token with the given type is available
-int PC_CheckTokenType(source_t *source, int type, int subtype, token_t *token);
-//skip tokens until the given token string is read
-int PC_SkipUntilString(source_t *source, char *string);
 //unread the last token read from the script
 void PC_UnreadLastToken(source_t *source);
 //unread the given token
 void PC_UnreadToken(source_t *source, token_t *token);
-//read a token only if on the same line, lines are concatenated with a slash
-int PC_ReadLine(source_t *source, token_t *token);
-//returns true if there was a white space in front of the token
-int PC_WhiteSpaceBeforeToken(token_t *token);
-//add a define to the source
-int PC_AddDefine(source_t *source, char *string);
 //add a globals define that will be added to all opened sources
-int PC_AddGlobalDefine(char *string);
-//remove the given global define
-int PC_RemoveGlobalDefine(char *name);
+int PC_AddGlobalDefine(const char *string);
 //remove all globals defines
 void PC_RemoveAllGlobalDefines(void);
+#if 0
+//skip tokens until the given token string is read
+int PC_SkipUntilString(source_t *source, char *string);
+//returns true and reads the token when a token with the given type is available
+int PC_CheckTokenType(source_t *source, int type, int subtype, token_t *token);
+//remove the given global define
+int PC_RemoveGlobalDefine(char *name);
+//add a define to the source
+int PC_AddDefine(source_t *source, char *string);
 //add builtin defines
 void PC_AddBuiltinDefines(source_t *source);
 //set the source include path
-void PC_SetIncludePath(source_t *source, char *path);
+void PC_SetIncludePath(source_t *source, const char *path);
 //set the punction set
 void PC_SetPunctuations(source_t *source, punctuation_t *p);
+//load a source from memory
+source_t *LoadSourceMemory(char *ptr, int length, char *name);
+#endif
 //set the base folder to load files from
-void PC_SetBaseFolder(char *path);
+void PC_SetBaseFolder(const char *path);
 //load a source file
 source_t *LoadSourceFile(const char *filename);
-//load a source from memory
-source_t *LoadSourceMemory(char *ptr, int length, char *name);
 //free the given source
 void FreeSource(source_t *source);
 //print a source error
-void QDECL SourceError(source_t *source, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SourceError(source_t *source, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 //print a source warning
-void QDECL SourceWarning(source_t *source, char *str, ...)  Q_PRINTF_FUNC(2, 3);
+void QDECL SourceWarning(source_t *source, const char *fmt, ...)  __attribute__ ((format (printf, 2, 3)));
 
 #ifdef BSPC
 // some of BSPC source does include game/q_shared.h and some does not

```

### `openarena-engine`  — sha256 `cbeb9ad20901...`, 6459 bytes

_Diff stat: +6 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.h	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_precomp.h	2026-04-16 22:48:25.720197700 +0100
@@ -29,6 +29,10 @@
  *
  *****************************************************************************/
 
+#ifndef MAX_PATH
+	#define MAX_PATH			MAX_QPATH
+#endif
+
 #ifndef PATH_SEPERATORSTR
 	#if defined(WIN32)|defined(_WIN32)|defined(__NT__)|defined(__WINDOWS__)|defined(__WINDOWS_386__)
 		#define PATHSEPERATOR_STR		"\\"
@@ -148,9 +152,9 @@
 //free the given source
 void FreeSource(source_t *source);
 //print a source error
-void QDECL SourceError(source_t *source, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SourceError(source_t *source, char *str, ...) __attribute__ ((format (printf, 2, 3)));
 //print a source warning
-void QDECL SourceWarning(source_t *source, char *str, ...)  Q_PRINTF_FUNC(2, 3);
+void QDECL SourceWarning(source_t *source, char *str, ...)  __attribute__ ((format (printf, 2, 3)));
 
 #ifdef BSPC
 // some of BSPC source does include game/q_shared.h and some does not

```

### `openarena-gamecode`  — sha256 `6c110de9f6f0...`, 6377 bytes

_Diff stat: +7 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_precomp.h	2026-04-16 20:02:25.130483900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\l_precomp.h	2026-04-16 22:48:24.144820900 +0100
@@ -29,6 +29,10 @@
  *
  *****************************************************************************/
 
+#ifndef MAX_PATH
+	#define MAX_PATH			MAX_QPATH
+#endif
+
 #ifndef PATH_SEPERATORSTR
 	#if defined(WIN32)|defined(_WIN32)|defined(__NT__)|defined(__WINDOWS__)|defined(__WINDOWS_386__)
 		#define PATHSEPERATOR_STR		"\\"
@@ -113,7 +117,7 @@
 int PC_ExpectAnyToken(source_t *source, token_t *token);
 //returns true when the token is available
 int PC_CheckTokenString(source_t *source, char *string);
-//returns true and reads the token when a token with the given type is available
+//returns true an reads the token when a token with the given type is available
 int PC_CheckTokenType(source_t *source, int type, int subtype, token_t *token);
 //skip tokens until the given token string is read
 int PC_SkipUntilString(source_t *source, char *string);
@@ -148,9 +152,9 @@
 //free the given source
 void FreeSource(source_t *source);
 //print a source error
-void QDECL SourceError(source_t *source, char *str, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SourceError(source_t *source, char *str, ...);
 //print a source warning
-void QDECL SourceWarning(source_t *source, char *str, ...)  Q_PRINTF_FUNC(2, 3);
+void QDECL SourceWarning(source_t *source, char *str, ...);
 
 #ifdef BSPC
 // some of BSPC source does include game/q_shared.h and some does not

```
