# Diff: `code/botlib/l_libvar.h`
**Canonical:** `wolfcamql-src` (sha256 `d9bfb004d275...`, 2548 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `1c4bb2d957ef...`, 2449 bytes

_Diff stat: +10 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_libvar.h	2026-04-16 20:02:19.855902700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -43,21 +43,21 @@
 //removes all library variables
 void LibVarDeAllocAll(void);
 //gets the library variable with the given name
-libvar_t *LibVarGet(const char *var_name);
+libvar_t *LibVarGet(char *var_name);
 //gets the string of the library variable with the given name
-char *LibVarGetString(const char *var_name);
+char *LibVarGetString(char *var_name);
 //gets the value of the library variable with the given name
-float LibVarGetValue(const char *var_name);
+float LibVarGetValue(char *var_name);
 //creates the library variable if not existing already and returns it
-libvar_t *LibVar(const char *var_name, const char *value);
+libvar_t *LibVar(char *var_name, char *value);
 //creates the library variable if not existing already and returns the value
-float LibVarValue(const char *var_name, const char *value);
+float LibVarValue(char *var_name, char *value);
 //creates the library variable if not existing already and returns the value string
-char *LibVarString(const char *var_name, const char *value);
+char *LibVarString(char *var_name, char *value);
 //sets the library variable
-void LibVarSet(const char *var_name, const char *value);
+void LibVarSet(char *var_name, char *value);
 //returns true if the library variable has been modified
-qboolean LibVarChanged(const char *var_name);
+qboolean LibVarChanged(char *var_name);
 //sets the library variable to unmodified
-void LibVarSetNotModified(const char *var_name);
+void LibVarSetNotModified(char *var_name);
 

```

### `quake3e`  — sha256 `3d3e531faf33...`, 2762 bytes

_Diff stat: +13 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_libvar.h	2026-04-16 20:02:26.904499600 +0100
@@ -43,21 +43,24 @@
 //removes all library variables
 void LibVarDeAllocAll(void);
 //gets the library variable with the given name
-libvar_t *LibVarGet(const char *var_name);
+libvar_t *LibVarGet( const char *var_name );
 //gets the string of the library variable with the given name
-char *LibVarGetString(const char *var_name);
+const char *LibVarGetString( const char *var_name );
 //gets the value of the library variable with the given name
-float LibVarGetValue(const char *var_name);
+float LibVarGetValue( const char *var_name );
 //creates the library variable if not existing already and returns it
-libvar_t *LibVar(const char *var_name, const char *value);
+libvar_t *LibVar( const char *var_name, const char *value );
 //creates the library variable if not existing already and returns the value
-float LibVarValue(const char *var_name, const char *value);
+float LibVarValue( const char *var_name, const char *value );
+//creates the library variable if not existing already and returns the integer value
+int LibVarInteger( const char *var_name, const char *value, int min_v, int max_v );
 //creates the library variable if not existing already and returns the value string
-char *LibVarString(const char *var_name, const char *value);
+const char *LibVarString( const char *var_name, const char *value );
 //sets the library variable
-void LibVarSet(const char *var_name, const char *value);
+void LibVarSet( const char *var_name, const char *value );
+#if 0
 //returns true if the library variable has been modified
-qboolean LibVarChanged(const char *var_name);
+qboolean LibVarChanged( const char *var_name );
 //sets the library variable to unmodified
-void LibVarSetNotModified(const char *var_name);
-
+void LibVarSetNotModified( const char *var_name );
+#endif

```

### `openarena-engine`  — sha256 `98c186d9ea12...`, 2470 bytes
Also identical in: openarena-gamecode

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.h	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_libvar.h	2026-04-16 22:48:25.717693900 +0100
@@ -43,21 +43,21 @@
 //removes all library variables
 void LibVarDeAllocAll(void);
 //gets the library variable with the given name
-libvar_t *LibVarGet(const char *var_name);
+libvar_t *LibVarGet(char *var_name);
 //gets the string of the library variable with the given name
-char *LibVarGetString(const char *var_name);
+char *LibVarGetString(char *var_name);
 //gets the value of the library variable with the given name
-float LibVarGetValue(const char *var_name);
+float LibVarGetValue(char *var_name);
 //creates the library variable if not existing already and returns it
-libvar_t *LibVar(const char *var_name, const char *value);
+libvar_t *LibVar(char *var_name, char *value);
 //creates the library variable if not existing already and returns the value
-float LibVarValue(const char *var_name, const char *value);
+float LibVarValue(char *var_name, char *value);
 //creates the library variable if not existing already and returns the value string
-char *LibVarString(const char *var_name, const char *value);
+char *LibVarString(char *var_name, char *value);
 //sets the library variable
-void LibVarSet(const char *var_name, const char *value);
+void LibVarSet(char *var_name, char *value);
 //returns true if the library variable has been modified
-qboolean LibVarChanged(const char *var_name);
+qboolean LibVarChanged(char *var_name);
 //sets the library variable to unmodified
-void LibVarSetNotModified(const char *var_name);
+void LibVarSetNotModified(char *var_name);
 

```
