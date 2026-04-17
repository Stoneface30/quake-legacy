# Diff: `code/botlib/l_libvar.c`
**Canonical:** `wolfcamql-src` (sha256 `f03756d8f06e...`, 7997 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `dcf0db188491...`, 7867 bytes

_Diff stat: +16 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_libvar.c	2026-04-16 20:02:19.854895300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,12 +29,12 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_libvar.h"
 
 //list with library variables
-libvar_t *libvarlist = NULL;
+libvar_t *libvarlist;
 
 //===========================================================================
 //
@@ -42,7 +42,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarStringValue(const char *string)
+float LibVarStringValue(char *string)
 {
 	int dotfound = 0;
 	float value = 0;
@@ -80,13 +80,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarAlloc(const char *var_name)
+libvar_t *LibVarAlloc(char *var_name)
 {
 	libvar_t *v;
 
-	v = (libvar_t *) GetMemory(sizeof(libvar_t));
+	v = (libvar_t *) GetMemory(sizeof(libvar_t) + strlen(var_name) + 1);
 	Com_Memset(v, 0, sizeof(libvar_t));
-	v->name = (char *) GetMemory(strlen(var_name)+1);
+	v->name = (char *) v + sizeof(libvar_t);
 	strcpy(v->name, var_name);
 	//add the variable in the list
 	v->next = libvarlist;
@@ -102,7 +102,6 @@
 void LibVarDeAlloc(libvar_t *v)
 {
 	if (v->string) FreeMemory(v->string);
-	FreeMemory(v->name);
 	FreeMemory(v);
 } //end of the function LibVarDeAlloc
 //===========================================================================
@@ -128,7 +127,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarGet(const char *var_name)
+libvar_t *LibVarGet(char *var_name)
 {
 	libvar_t *v;
 
@@ -147,7 +146,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarGetString(const char *var_name)
+char *LibVarGetString(char *var_name)
 {
 	libvar_t *v;
 
@@ -167,7 +166,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarGetValue(const char *var_name)
+float LibVarGetValue(char *var_name)
 {
 	libvar_t *v;
 
@@ -187,7 +186,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVar(const char *var_name, const char *value)
+libvar_t *LibVar(char *var_name, char *value)
 {
 	libvar_t *v;
 	v = LibVarGet(var_name);
@@ -210,7 +209,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarString(const char *var_name, const char *value)
+char *LibVarString(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -223,7 +222,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarValue(const char *var_name, const char *value)
+float LibVarValue(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -236,7 +235,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSet(const char *var_name, const char *value)
+void LibVarSet(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -263,7 +262,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean LibVarChanged(const char *var_name)
+qboolean LibVarChanged(char *var_name)
 {
 	libvar_t *v;
 
@@ -283,7 +282,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSetNotModified(const char *var_name)
+void LibVarSetNotModified(char *var_name)
 {
 	libvar_t *v;
 

```

### `quake3e`  — sha256 `3f43f1571b32...`, 8680 bytes

_Diff stat: +73 / -45 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_libvar.c	2026-04-16 20:02:26.904499600 +0100
@@ -30,8 +30,10 @@
  *****************************************************************************/
 
 #include "../qcommon/q_shared.h"
+#include "botlib.h"
 #include "l_memory.h"
 #include "l_libvar.h"
+#include "be_interface.h"
 
 //list with library variables
 libvar_t *libvarlist = NULL;
@@ -42,7 +44,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarStringValue(const char *string)
+static float LibVarStringValue( const char *string )
 {
 	int dotfound = 0;
 	float value = 0;
@@ -80,14 +82,14 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarAlloc(const char *var_name)
+libvar_t *LibVarAlloc( const char *var_name )
 {
 	libvar_t *v;
 
-	v = (libvar_t *) GetMemory(sizeof(libvar_t));
-	Com_Memset(v, 0, sizeof(libvar_t));
-	v->name = (char *) GetMemory(strlen(var_name)+1);
-	strcpy(v->name, var_name);
+	v = (libvar_t *) GetMemory( sizeof( libvar_t ) );
+	Com_Memset( v, 0, sizeof( libvar_t ) );
+	v->name = (char *) GetMemory( strlen( var_name )+1 );
+	strcpy( v->name, var_name );
 	//add the variable in the list
 	v->next = libvarlist;
 	libvarlist = v;
@@ -99,11 +101,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarDeAlloc(libvar_t *v)
+void LibVarDeAlloc( libvar_t *v )
 {
-	if (v->string) FreeMemory(v->string);
-	FreeMemory(v->name);
-	FreeMemory(v);
+	if ( v->string )
+		FreeMemory( v->string );
+	FreeMemory( v->name );
+	FreeMemory( v );
 } //end of the function LibVarDeAlloc
 //===========================================================================
 //
@@ -115,10 +118,10 @@
 {
 	libvar_t *v;
 
-	for (v = libvarlist; v; v = libvarlist)
+	for ( v = libvarlist; v; v = libvarlist )
 	{
 		libvarlist = libvarlist->next;
-		LibVarDeAlloc(v);
+		LibVarDeAlloc( v );
 	} //end for
 	libvarlist = NULL;
 } //end of the function LibVarDeAllocAll
@@ -128,13 +131,13 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarGet(const char *var_name)
+libvar_t *LibVarGet( const char *var_name )
 {
 	libvar_t *v;
 
-	for (v = libvarlist; v; v = v->next)
+	for ( v = libvarlist; v; v = v->next )
 	{
-		if (!Q_stricmp(v->name, var_name))
+		if ( !Q_stricmp( v->name, var_name ) )
 		{
 			return v;
 		} //end if
@@ -147,12 +150,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarGetString(const char *var_name)
+const char *LibVarGetString( const char *var_name )
 {
 	libvar_t *v;
 
-	v = LibVarGet(var_name);
-	if (v)
+	v = LibVarGet( var_name );
+	if ( v )
 	{
 		return v->string;
 	} //end if
@@ -167,12 +170,12 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarGetValue(const char *var_name)
+float LibVarGetValue( const char *var_name )
 {
 	libvar_t *v;
 
-	v = LibVarGet(var_name);
-	if (v)
+	v = LibVarGet( var_name );
+	if ( v )
 	{
 		return v->value;
 	} //end if
@@ -187,18 +190,19 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVar(const char *var_name, const char *value)
+libvar_t *LibVar( const char *var_name, const char *value )
 {
 	libvar_t *v;
-	v = LibVarGet(var_name);
-	if (v) return v;
+	v = LibVarGet( var_name );
+	if ( v ) 
+		return v;
 	//create new variable
-	v = LibVarAlloc(var_name);
+	v = LibVarAlloc( var_name );
 	//variable string
-	v->string = (char *) GetMemory(strlen(value) + 1);
-	strcpy(v->string, value);
+	v->string = (char *) GetMemory( strlen( value ) + 1 );
+	strcpy( v->string, value );
 	//the value
-	v->value = LibVarStringValue(v->string);
+	v->value = LibVarStringValue( v->string );
 	//variable is modified
 	v->modified = qtrue;
 	//
@@ -210,11 +214,11 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarString(const char *var_name, const char *value)
+const char *LibVarString( const char *var_name, const char *value )
 {
 	libvar_t *v;
 
-	v = LibVar(var_name, value);
+	v = LibVar( var_name, value );
 	return v->string;
 } //end of the function LibVarString
 //===========================================================================
@@ -223,52 +227,75 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarValue(const char *var_name, const char *value)
+float LibVarValue( const char *var_name, const char *value )
 {
 	libvar_t *v;
 
-	v = LibVar(var_name, value);
+	v = LibVar( var_name, value );
 	return v->value;
 } //end of the function LibVarValue
+
+int LibVarInteger( const char *var_name, const char *value, int min_v, int max_v )
+{
+	int v = (int) LibVarValue(var_name, value);
+
+	// if less than minimum, reset to default value
+	// if more than maximum, set to maximum
+	if (v < min_v || v > max_v)
+	{
+		botimport.Print(PRT_ERROR, "%s = %d\n", var_name, v);
+		if (v < min_v) {
+			v = atoi(value);
+			LibVarSet(var_name, value);
+		} else {
+			v = max_v;
+			LibVarSet(var_name, va("%d", max_v));
+		}
+	}
+
+	return v;
+}
+
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSet(const char *var_name, const char *value)
+void LibVarSet( const char *var_name, const char *value )
 {
 	libvar_t *v;
 
 	v = LibVarGet(var_name);
-	if (v)
+	if ( v )
 	{
-		FreeMemory(v->string);
+		FreeMemory( v->string );
 	} //end if
 	else
 	{
-		v = LibVarAlloc(var_name);
+		v = LibVarAlloc( var_name );
 	} //end else
 	//variable string
-	v->string = (char *) GetMemory(strlen(value) + 1);
-	strcpy(v->string, value);
+	v->string = (char *) GetMemory( strlen( value ) + 1 );
+	strcpy( v->string, value );
 	//the value
-	v->value = LibVarStringValue(v->string);
+	v->value = LibVarStringValue( v->string );
 	//variable is modified
 	v->modified = qtrue;
 } //end of the function LibVarSet
+#if 0
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean LibVarChanged(const char *var_name)
+qboolean LibVarChanged( const char *var_name )
 {
 	libvar_t *v;
 
-	v = LibVarGet(var_name);
-	if (v)
+	v = LibVarGet( var_name );
+	if ( v )
 	{
 		return v->modified;
 	} //end if
@@ -283,13 +310,14 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSetNotModified(const char *var_name)
+void LibVarSetNotModified( const char *var_name )
 {
 	libvar_t *v;
 
-	v = LibVarGet(var_name);
-	if (v)
+	v = LibVarGet( var_name );
+	if ( v )
 	{
 		v->modified = qfalse;
 	} //end if
 } //end of the function LibVarSetNotModified
+#endif

```

### `openarena-engine`  — sha256 `d2287255d965...`, 7907 bytes

_Diff stat: +11 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_libvar.c	2026-04-16 20:02:25.128417400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_libvar.c	2026-04-16 22:48:25.717693900 +0100
@@ -42,7 +42,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarStringValue(const char *string)
+float LibVarStringValue(char *string)
 {
 	int dotfound = 0;
 	float value = 0;
@@ -80,7 +80,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarAlloc(const char *var_name)
+libvar_t *LibVarAlloc(char *var_name)
 {
 	libvar_t *v;
 
@@ -128,7 +128,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVarGet(const char *var_name)
+libvar_t *LibVarGet(char *var_name)
 {
 	libvar_t *v;
 
@@ -147,7 +147,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarGetString(const char *var_name)
+char *LibVarGetString(char *var_name)
 {
 	libvar_t *v;
 
@@ -167,7 +167,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarGetValue(const char *var_name)
+float LibVarGetValue(char *var_name)
 {
 	libvar_t *v;
 
@@ -187,7 +187,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-libvar_t *LibVar(const char *var_name, const char *value)
+libvar_t *LibVar(char *var_name, char *value)
 {
 	libvar_t *v;
 	v = LibVarGet(var_name);
@@ -210,7 +210,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *LibVarString(const char *var_name, const char *value)
+char *LibVarString(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -223,7 +223,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-float LibVarValue(const char *var_name, const char *value)
+float LibVarValue(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -236,7 +236,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSet(const char *var_name, const char *value)
+void LibVarSet(char *var_name, char *value)
 {
 	libvar_t *v;
 
@@ -263,7 +263,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean LibVarChanged(const char *var_name)
+qboolean LibVarChanged(char *var_name)
 {
 	libvar_t *v;
 
@@ -283,7 +283,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void LibVarSetNotModified(const char *var_name)
+void LibVarSetNotModified(char *var_name)
 {
 	libvar_t *v;
 

```
