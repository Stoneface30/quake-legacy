# Diff: `code/botlib/l_log.c`
**Canonical:** `wolfcamql-src` (sha256 `9e2a6adbfe75...`, 5441 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `968cf8579d13...`, 5245 bytes

_Diff stat: +5 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_log.c	2026-04-16 20:02:19.855902700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -33,12 +33,10 @@
 #include <stdio.h>
 #include <string.h>
 
-#include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
-#include "botlib.h"
+#include "../game/q_shared.h"
+#include "../game/botlib.h"
 #include "be_interface.h"			//for botimport.Print
 #include "l_libvar.h"
-#include "l_log.h"
 
 #define MAX_LOGFILENAMESIZE		1024
 
@@ -59,7 +57,6 @@
 //===========================================================================
 void Log_Open(char *filename)
 {
-	char *ospath;
 	if (!LibVarValue("log", "0")) return;
 	if (!filename || !strlen(filename))
 	{
@@ -71,14 +68,13 @@
 		botimport.Print(PRT_ERROR, "log file %s is already opened\n", logfile.filename);
 		return;
 	} //end if
-	ospath = FS_BuildOSPath(Cvar_VariableString("fs_homestatepath"), Cvar_VariableString("fs_game"), filename);
-	logfile.fp = fopen(ospath, "wb");
+	logfile.fp = fopen(filename, "wb");
 	if (!logfile.fp)
 	{
 		botimport.Print(PRT_ERROR, "can't open the log file %s\n", filename);
 		return;
 	} //end if
-	Q_strncpyz(logfile.filename, filename, MAX_LOGFILENAMESIZE);
+	strncpy(logfile.filename, filename, MAX_LOGFILENAMESIZE);
 	botimport.Print(PRT_MESSAGE, "Opened log %s\n", logfile.filename);
 } //end of the function Log_Create
 //===========================================================================

```

### `quake3e`  — sha256 `e5c85366d4d5...`, 5495 bytes

_Diff stat: +23 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_log.c	2026-04-16 20:02:26.905505600 +0100
@@ -57,37 +57,43 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void Log_Open(char *filename)
+void Log_Open( const char *filename )
 {
-	char *ospath;
-	if (!LibVarValue("log", "0")) return;
-	if (!filename || !strlen(filename))
+	const char *ospath;
+
+	if ( !LibVarValue( "log", "0" ) ) 
+		return;
+
+	if ( !filename || !*filename )
 	{
-		botimport.Print(PRT_MESSAGE, "openlog <filename>\n");
+		botimport.Print( PRT_MESSAGE, "openlog <filename>\n" );
 		return;
 	} //end if
-	if (logfile.fp)
+
+	if ( logfile.fp )
 	{
 		botimport.Print(PRT_ERROR, "log file %s is already opened\n", logfile.filename);
 		return;
 	} //end if
-	ospath = FS_BuildOSPath(Cvar_VariableString("fs_homestatepath"), Cvar_VariableString("fs_game"), filename);
-	logfile.fp = fopen(ospath, "wb");
-	if (!logfile.fp)
+
+	ospath = FS_BuildOSPath( Cvar_VariableString( "fs_homepath" ), "", filename );
+	logfile.fp = Sys_FOpen( ospath, "wb" );
+	if ( !logfile.fp )
 	{
-		botimport.Print(PRT_ERROR, "can't open the log file %s\n", filename);
+		botimport.Print( PRT_ERROR, "can't open the log file %s\n", filename );
 		return;
 	} //end if
-	Q_strncpyz(logfile.filename, filename, MAX_LOGFILENAMESIZE);
-	botimport.Print(PRT_MESSAGE, "Opened log %s\n", logfile.filename);
-} //end of the function Log_Create
+
+	Q_strncpyz( logfile.filename, filename, sizeof( logfile.filename ) );
+	botimport.Print( PRT_MESSAGE, "Opened log %s\n", logfile.filename );
+} //end of the function Log_Open
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void Log_Close(void)
+static void Log_Close(void)
 {
 	if (!logfile.fp) return;
 	if (fclose(logfile.fp))
@@ -125,6 +131,7 @@
 	//fprintf(logfile.fp, "\r\n");
 	fflush(logfile.fp);
 } //end of the function Log_Write
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -149,7 +156,8 @@
 	fprintf(logfile.fp, "\r\n");
 	logfile.numwrites++;
 	fflush(logfile.fp);
-} //end of the function Log_Write
+} //end of the function Log_WriteTimeStamped
+#endif
 //===========================================================================
 //
 // Parameter:				-

```

### `openarena-engine`  — sha256 `fb3172a41697...`, 5281 bytes

_Diff stat: +2 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_log.c	2026-04-16 22:48:25.718693900 +0100
@@ -34,7 +34,6 @@
 #include <string.h>
 
 #include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
 #include "botlib.h"
 #include "be_interface.h"			//for botimport.Print
 #include "l_libvar.h"
@@ -59,7 +58,6 @@
 //===========================================================================
 void Log_Open(char *filename)
 {
-	char *ospath;
 	if (!LibVarValue("log", "0")) return;
 	if (!filename || !strlen(filename))
 	{
@@ -71,14 +69,13 @@
 		botimport.Print(PRT_ERROR, "log file %s is already opened\n", logfile.filename);
 		return;
 	} //end if
-	ospath = FS_BuildOSPath(Cvar_VariableString("fs_homestatepath"), Cvar_VariableString("fs_game"), filename);
-	logfile.fp = fopen(ospath, "wb");
+	logfile.fp = fopen(filename, "wb");
 	if (!logfile.fp)
 	{
 		botimport.Print(PRT_ERROR, "can't open the log file %s\n", filename);
 		return;
 	} //end if
-	Q_strncpyz(logfile.filename, filename, MAX_LOGFILENAMESIZE);
+	strncpy(logfile.filename, filename, MAX_LOGFILENAMESIZE);
 	botimport.Print(PRT_MESSAGE, "Opened log %s\n", logfile.filename);
 } //end of the function Log_Create
 //===========================================================================

```
