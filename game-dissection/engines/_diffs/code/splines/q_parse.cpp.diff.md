# Diff: `code/splines/q_parse.cpp`
**Canonical:** `wolfcamql-src` (sha256 `7edbdca5aa05...`, 11457 bytes)

## Variants

### `quake3-source`  — sha256 `894ade70264c...`, 11120 bytes

_Diff stat: +6 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\q_parse.cpp	2026-04-16 20:02:25.272780200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\q_parse.cpp	2026-04-16 20:02:19.981635900 +0100
@@ -57,9 +57,7 @@
 */
 void Com_BeginParseSession( const char *filename ) {
 	if ( parseInfoNum == MAX_PARSE_INFO - 1 ) {
-          //Com_Error( ERR_FATAL, "Com_BeginParseSession: session overflow" );
-          Com_Printf("^1ERROR Com_BeginParseSession: session overflow\n");
-          return;
+		Com_Error( ERR_FATAL, "Com_BeginParseSession: session overflow" );
 	}
 	parseInfoNum++;
 	pi = &parseInfo[parseInfoNum];
@@ -75,9 +73,7 @@
 */
 void Com_EndParseSession( void ) {
 	if ( parseInfoNum == 0 ) {
-          //Com_Error( ERR_FATAL, "Com_EndParseSession: session underflow" );
-          Com_Printf("^1ERROR Com_EndParseSession: session underflow\n");
-          return;
+		Com_Error( ERR_FATAL, "Com_EndParseSession: session underflow" );
 	}
 	parseInfoNum--;
 	pi = &parseInfo[parseInfoNum];
@@ -107,8 +103,7 @@
 	vsprintf( string, msg,argptr );
 	va_end( argptr );
 
-	//Com_Error( ERR_DROP, "File %s, line %i: %s", pi->parseFile, pi->lines, string );
-        Com_Printf("^1ERROR File %s, line %i: %s\n", pi->parseFile, pi->lines, string);
+	Com_Error( ERR_DROP, "File %s, line %i: %s", pi->parseFile, pi->lines, string );
 }
 
 void Com_ScriptWarning( const char *msg, ... ) {
@@ -119,7 +114,7 @@
 	vsprintf( string, msg,argptr );
 	va_end( argptr );
 
-	Com_Printf( "File %s, line %i: %s\n", pi->parseFile, pi->lines, string );
+	Com_Printf( "File %s, line %i: %s", pi->parseFile, pi->lines, string );
 }
 
 
@@ -133,8 +128,7 @@
 */
 void Com_UngetToken( void ) {
 	if ( pi->ungetToken ) {
-          Com_ScriptError( "UngetToken called twice" );
-          return;
+		Com_ScriptError( "UngetToken called twice" );
 	}
 	pi->ungetToken = qtrue;
 }
@@ -177,7 +171,7 @@
 	const char **punc;
 
 	if ( !data_p ) {
-          Com_Error( ERR_FATAL, "Com_ParseExt: NULL data_p" );
+		Com_Error( ERR_FATAL, "Com_ParseExt: NULL data_p" );
 	}
 
 	data = *data_p;

```
