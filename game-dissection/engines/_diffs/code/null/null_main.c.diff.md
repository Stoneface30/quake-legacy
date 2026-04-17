# Diff: `code/null/null_main.c`
**Canonical:** `quake3-source` (sha256 `3a80e3af88c0...`, 2533 bytes)

## Variants

### `openarena-engine`  — sha256 `0c57a737e693...`, 2648 bytes

_Diff stat: +5 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\null\null_main.c	2026-04-16 20:02:19.940311700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\null\null_main.c	2026-04-16 22:48:25.834145700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Foobar; if not, write to the Free Software
+along with Quake III Arena source code; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -82,6 +82,10 @@
 	return 0;
 }
 
+FILE	*Sys_FOpen(const char *ospath, const char *mode) {
+	return fopen( ospath, mode );
+}
+
 void	Sys_Mkdir (char *path) {
 }
 

```
