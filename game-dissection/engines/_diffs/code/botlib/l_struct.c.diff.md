# Diff: `code/botlib/l_struct.c`
**Canonical:** `wolfcamql-src` (sha256 `1811d6d71b9d...`, 12781 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `23cf2f1e3653...`, 12829 bytes

_Diff stat: +9 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_struct.c	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_struct.c	2026-04-16 20:02:19.858903200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -30,8 +30,8 @@
  *****************************************************************************/
 
 #ifdef BOTLIB
-#include "../qcommon/q_shared.h"
-#include "botlib.h"				//for the include of be_interface.h
+#include "../game/q_shared.h"
+#include "../game/botlib.h"				//for the include of be_interface.h
 #include "l_script.h"
 #include "l_precomp.h"
 #include "l_struct.h"
@@ -150,7 +150,7 @@
 		} //end if
 		if (intval < intmin || intval > intmax)
 		{
-			SourceError(source, "value %ld out of range [%ld, %ld]", intval, intmin, intmax);
+			SourceError(source, "value %d out of range [%d, %d]", intval, intmin, intmax);
 			return 0;
 		} //end if
 	} //end if
@@ -160,7 +160,7 @@
 		{
 			if (intval < fd->floatmin || intval > fd->floatmax)
 			{
-				SourceError(source, "value %ld out of range [%f, %f]", intval, fd->floatmin, fd->floatmax);
+				SourceError(source, "value %d out of range [%f, %f]", intval, fd->floatmin, fd->floatmax);
 				return 0;
 			} //end if
 		} //end if
@@ -221,7 +221,9 @@
 	//remove the double quotes
 	StripDoubleQuotes(token.string);
 	//copy the string
-	Q_strncpyz((char *) p, token.string, MAX_STRINGFIELD);
+	strncpy((char *) p, token.string, MAX_STRINGFIELD);
+	//make sure the string is closed with a zero
+	((char *)p)[MAX_STRINGFIELD-1] = '\0';
 	//
 	return 1;
 } //end of the function ReadString
@@ -344,7 +346,7 @@
 	char buf[128];
 	int l;
 
-	Com_sprintf(buf, sizeof(buf), "%f", value);
+	sprintf(buf, "%f", value);
 	l = strlen(buf);
 	//strip any trailing zeros
 	while(l-- > 1)

```

### `quake3e`  — sha256 `5b155124f12d...`, 12929 bytes

_Diff stat: +11 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_struct.c	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_struct.c	2026-04-16 20:02:26.907505100 +0100
@@ -57,7 +57,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-fielddef_t *FindField(fielddef_t *defs, char *name)
+static const fielddef_t *FindField(const fielddef_t *defs, const char *name)
 {
 	int i;
 
@@ -73,7 +73,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean ReadNumber(source_t *source, fielddef_t *fd, void *p)
+static qboolean ReadNumber(source_t *source, const fielddef_t *fd, void *p)
 {
 	token_t token;
 	int negative = qfalse;
@@ -188,7 +188,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean ReadChar(source_t *source, fielddef_t *fd, void *p)
+static qboolean ReadChar(source_t *source, const fielddef_t *fd, void *p)
 {
 	token_t token;
 
@@ -213,16 +213,15 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int ReadString(source_t *source, fielddef_t *fd, void *p)
+static int ReadString(source_t *source, const fielddef_t *fd, void *p)
 {
 	token_t token;
 
 	if (!PC_ExpectTokenType(source, TT_STRING, 0, &token)) return 0;
 	//remove the double quotes
 	StripDoubleQuotes(token.string);
-	//copy the string
-	Q_strncpyz((char *) p, token.string, MAX_STRINGFIELD);
-	//
+	//copy the string and make sure it is closed with a zero
+	Q_strncpyz( (char *)p, token.string, MAX_STRINGFIELD );
 	return 1;
 } //end of the function ReadString
 //===========================================================================
@@ -231,10 +230,10 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int ReadStructure(source_t *source, structdef_t *def, char *structure)
+int ReadStructure(source_t *source, const structdef_t *def, char *structure)
 {
 	token_t token;
-	fielddef_t *fd;
+	const fielddef_t *fd;
 	void *p;
 	int num;
 
@@ -367,11 +366,11 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int WriteStructWithIndent(FILE *fp, structdef_t *def, char *structure, int indent)
+static int WriteStructWithIndent(FILE *fp, const structdef_t *def, const char *structure, int indent)
 {
 	int i, num;
 	void *p;
-	fielddef_t *fd;
+	const fielddef_t *fd;
 
 	if (!WriteIndent(fp, indent)) return qfalse;
 	if (fprintf(fp, "{\r\n") < 0) return qfalse;
@@ -453,7 +452,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int WriteStructure(FILE *fp, structdef_t *def, char *structure)
+int WriteStructure(FILE *fp, const structdef_t *def, const char *structure)
 {
 	return WriteStructWithIndent(fp, def, structure, 0);
 } //end of the function WriteStructure

```

### `openarena-engine`  — sha256 `598e92548853...`, 12866 bytes

_Diff stat: +3 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_struct.c	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\l_struct.c	2026-04-16 22:48:25.720197700 +0100
@@ -221,7 +221,9 @@
 	//remove the double quotes
 	StripDoubleQuotes(token.string);
 	//copy the string
-	Q_strncpyz((char *) p, token.string, MAX_STRINGFIELD);
+	strncpy((char *) p, token.string, MAX_STRINGFIELD);
+	//make sure the string is closed with a zero
+	((char *)p)[MAX_STRINGFIELD-1] = '\0';
 	//
 	return 1;
 } //end of the function ReadString

```
