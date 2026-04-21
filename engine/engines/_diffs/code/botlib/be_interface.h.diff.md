# Diff: `code/botlib/be_interface.h`
**Canonical:** `wolfcamql-src` (sha256 `b47eb2acb19c...`, 1961 bytes)
Also identical in: ioquake3, openarena-engine, quake3e

## Variants

### `quake3-source`  — sha256 `c38377657d8e...`, 1941 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_interface.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_interface.h	2026-04-16 20:02:19.854388000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -50,7 +50,7 @@
 
 extern botlib_globals_t botlibglobals;
 extern botlib_import_t botimport;
-extern int botDeveloper;					//true if developer is on
+extern int bot_developer;					//true if developer is on
 
 //
 int Sys_MilliSeconds(void);

```

### `openarena-gamecode`  — sha256 `ac6eb41e3d9f...`, 1962 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_interface.h	2026-04-16 20:02:25.127417300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\be_interface.h	2026-04-16 22:48:24.143820800 +0100
@@ -50,7 +50,7 @@
 
 extern botlib_globals_t botlibglobals;
 extern botlib_import_t botimport;
-extern int botDeveloper;					//true if developer is on
+extern int bot_developer;					//true if developer is on
 
 //
 int Sys_MilliSeconds(void);

```
