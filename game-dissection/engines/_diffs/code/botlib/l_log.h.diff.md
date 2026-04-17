# Diff: `code/botlib/l_log.h`
**Canonical:** `wolfcamql-src` (sha256 `a9e4b217616b...`, 1751 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `3489eeec377f...`, 1690 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_log.h	2026-04-16 20:02:19.855902700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -36,9 +36,9 @@
 //close log file if present
 void Log_Shutdown(void);
 //write to the current opened log file
-void QDECL Log_Write(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_Write(char *fmt, ...);
 //write to the current opened log file with a time stamp
-void QDECL Log_WriteTimeStamped(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_WriteTimeStamped(char *fmt, ...);
 //returns a pointer to the log file
 FILE *Log_FilePointer(void);
 //flush log file

```

### `quake3e`  — sha256 `421683c5dd89...`, 1761 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_log.h	2026-04-16 20:02:26.905505600 +0100
@@ -30,15 +30,15 @@
  *****************************************************************************/
 
 //open a log file
-void Log_Open(char *filename);
-//close the current log file
-void Log_Close(void);
+void Log_Open( const char *filename );
 //close log file if present
 void Log_Shutdown(void);
 //write to the current opened log file
-void QDECL Log_Write(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_Write(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
+#if 0
 //write to the current opened log file with a time stamp
-void QDECL Log_WriteTimeStamped(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_WriteTimeStamped(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
+#endif
 //returns a pointer to the log file
 FILE *Log_FilePointer(void);
 //flush log file

```

### `openarena-engine`  — sha256 `ad323ca48e09...`, 1791 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_log.h	2026-04-16 22:48:25.718693900 +0100
@@ -36,9 +36,9 @@
 //close log file if present
 void Log_Shutdown(void);
 //write to the current opened log file
-void QDECL Log_Write(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_Write(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
 //write to the current opened log file with a time stamp
-void QDECL Log_WriteTimeStamped(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_WriteTimeStamped(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
 //returns a pointer to the log file
 FILE *Log_FilePointer(void);
 //flush log file

```

### `openarena-gamecode`  — sha256 `5de20e03d03d...`, 1711 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_log.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\l_log.h	2026-04-16 22:48:24.144820900 +0100
@@ -36,9 +36,9 @@
 //close log file if present
 void Log_Shutdown(void);
 //write to the current opened log file
-void QDECL Log_Write(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_Write(char *fmt, ...);
 //write to the current opened log file with a time stamp
-void QDECL Log_WriteTimeStamped(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL Log_WriteTimeStamped(char *fmt, ...);
 //returns a pointer to the log file
 FILE *Log_FilePointer(void);
 //flush log file

```
