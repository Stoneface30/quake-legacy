# Diff: `q3asm/opstrings.h`
**Canonical:** `quake3-source` (sha256 `4072dd65a4aa...`, 3810 bytes)

## Variants

### `q3vm`  — sha256 `9304f935f036...`, 3861 bytes

_Diff stat: +5 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\q3asm\opstrings.h	2026-04-16 20:02:20.124514000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\q3asm\opstrings.h	2026-04-16 22:48:28.103253600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -38,7 +38,7 @@
 //{ "ARGP", OP_ARG },
 //{ "ARGU", OP_ARG },
 
-{ "ASGNB", 	OP_BLOCK_COPY },
+{ "ASGNB",  OP_BLOCK_COPY },
 { "ASGNF4", OP_STORE4 },
 { "ASGNI4", OP_STORE4 },
 { "ASGNP4", OP_STORE4 },
@@ -50,7 +50,7 @@
 { "ASGNI1", OP_STORE1 },
 { "ASGNU1", OP_STORE1 },
 
-{ "INDIRB", OP_IGNORE },	// block copy deals with this
+{ "INDIRB", OP_IGNORE },    // block copy deals with this
 { "INDIRF4", OP_LOAD4 },
 { "INDIRI4", OP_LOAD4 },
 { "INDIRP4", OP_LOAD4 },
@@ -66,7 +66,7 @@
 { "CVFI4", OP_CVFI },
 
 { "CVIF4", OP_CVIF },
-{ "CVII4", OP_SEX8 },	// will be either SEX8 or SEX16
+{ "CVII4", OP_SEX8 },   // will be either SEX8 or SEX16
 { "CVII1", OP_IGNORE },
 { "CVII2", OP_IGNORE },
 { "CVIU4", OP_IGNORE },
@@ -78,6 +78,7 @@
 { "CVUU4", OP_IGNORE },
 
 { "CVUU1", OP_IGNORE },
+{ "CVUU2", OP_IGNORE },
 
 { "NEGF4", OP_NEGF },
 { "NEGI4", OP_NEGI },

```
