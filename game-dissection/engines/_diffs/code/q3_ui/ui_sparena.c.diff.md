# Diff: `code/q3_ui/ui_sparena.c`
**Canonical:** `wolfcamql-src` (sha256 `60f0fa8f13ef...`, 1708 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `727d0967979f...`, 1687 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sparena.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_sparena.c	2026-04-16 20:02:19.953195000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `67ccb850c97b...`, 1700 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_sparena.c	2026-04-16 20:02:25.212501000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_sparena.c	2026-04-16 22:48:24.188498600 +0100
@@ -36,10 +36,10 @@
 	level = atoi( Info_ValueForKey( arenaInfo, "num" ) );
 	txt = Info_ValueForKey( arenaInfo, "special" );
 	if( txt[0] ) {
-		if( Q_stricmp( txt, "training" ) == 0 ) {
+		if( Q_strequal( txt, "training" ) ) {
 			level = -4;
 		}
-		else if( Q_stricmp( txt, "final" ) == 0 ) {
+		else if( Q_strequal( txt, "final" ) ) {
 			level = UI_GetNumSPTiers() * ARENAS_PER_TIER;
 		}
 	}

```
