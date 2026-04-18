# Diff: `code/botlib/l_struct.h`
**Canonical:** `wolfcamql-src` (sha256 `eaa0de3eca40...`, 2590 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `0ba59377f8e0...`, 2569 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_struct.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\l_struct.h	2026-04-16 20:02:19.858903200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `0fe01e7eb5f4...`, 2621 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\l_struct.h	2026-04-16 20:02:25.130988400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\l_struct.h	2026-04-16 20:02:26.907505100 +0100
@@ -47,7 +47,7 @@
 //structure field definition
 typedef struct fielddef_s
 {
-	char *name;										//name of the field
+	const char *name;										//name of the field
 	int offset;										//offset in the structure
 	int type;										//type of the field
 	//type specific fields
@@ -60,16 +60,16 @@
 typedef struct structdef_s
 {
 	int size;
-	fielddef_t *fields;
+	const fielddef_t *fields;
 } structdef_t;
 
 //read a structure from a script
-int ReadStructure(source_t *source, structdef_t *def, char *structure);
+int ReadStructure(source_t *source, const structdef_t *def, char *structure);
 //write a structure to a file
-int WriteStructure(FILE *fp, structdef_t *def, char *structure);
+int WriteStructure(FILE *fp, const structdef_t *def, const char *structure);
 //writes indents
 int WriteIndent(FILE *fp, int indent);
-//writes a float without traling zeros
+//writes a float without trailing zeros
 int WriteFloat(FILE *fp, float value);
 
 

```
