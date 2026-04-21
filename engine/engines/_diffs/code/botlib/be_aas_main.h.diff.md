# Diff: `code/botlib/be_aas_main.h`
**Canonical:** `wolfcamql-src` (sha256 `e734177819cd...`, 1983 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `3a77aa4fffde...`, 2116 bytes

_Diff stat: +6 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_main.h	2026-04-16 20:02:19.846388500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -34,7 +34,7 @@
 extern aas_t aasworld;
 
 //AAS error message
-void QDECL AAS_Error(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL AAS_Error(char *fmt, ...);
 //set AAS initialized
 void AAS_SetInitialized(void);
 //setup AAS with the given number of entities and clients
@@ -51,6 +51,10 @@
 int AAS_Initialized(void);
 //returns true if the AAS file is loaded
 int AAS_Loaded(void);
+//returns the model name from the given index
+char *AAS_ModelFromIndex(int index);
+//returns the index from the given model name
+int AAS_IndexFromModel(char *modelname);
 //returns the current time
 float AAS_Time(void);
 //

```

### `quake3e`  — sha256 `d86137809fbd...`, 1948 bytes

_Diff stat: +1 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_main.h	2026-04-16 20:02:26.894280200 +0100
@@ -34,9 +34,7 @@
 extern aas_t aasworld;
 
 //AAS error message
-void QDECL AAS_Error(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
-//set AAS initialized
-void AAS_SetInitialized(void);
+void QDECL AAS_Error(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
 //setup AAS with the given number of entities and clients
 int AAS_Setup(void);
 //shutdown AAS

```

### `openarena-engine`  — sha256 `6d919eba333f...`, 2003 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_main.h	2026-04-16 22:48:25.709437000 +0100
@@ -34,7 +34,7 @@
 extern aas_t aasworld;
 
 //AAS error message
-void QDECL AAS_Error(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL AAS_Error(char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
 //set AAS initialized
 void AAS_SetInitialized(void);
 //setup AAS with the given number of entities and clients

```

### `openarena-gamecode`  — sha256 `e8166024d645...`, 2137 bytes

_Diff stat: +5 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_main.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\be_aas_main.h	2026-04-16 22:48:24.141312400 +0100
@@ -34,7 +34,7 @@
 extern aas_t aasworld;
 
 //AAS error message
-void QDECL AAS_Error(char *fmt, ...) Q_PRINTF_FUNC(1, 2);
+void QDECL AAS_Error(char *fmt, ...);
 //set AAS initialized
 void AAS_SetInitialized(void);
 //setup AAS with the given number of entities and clients
@@ -51,6 +51,10 @@
 int AAS_Initialized(void);
 //returns true if the AAS file is loaded
 int AAS_Loaded(void);
+//returns the model name from the given index
+char *AAS_ModelFromIndex(int index);
+//returns the index from the given model name
+int AAS_IndexFromModel(char *modelname);
 //returns the current time
 float AAS_Time(void);
 //

```
