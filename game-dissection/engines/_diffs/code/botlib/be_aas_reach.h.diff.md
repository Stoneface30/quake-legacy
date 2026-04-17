# Diff: `code/botlib/be_aas_reach.h`
**Canonical:** `wolfcamql-src` (sha256 `92b937a9715c...`, 2917 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `eee2835cdc59...`, 2896 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_reach.h	2026-04-16 20:02:25.118908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_reach.h	2026-04-16 20:02:19.848387200 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `a9c342cdb8f8...`, 2837 bytes

_Diff stat: +2 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_reach.h	2026-04-16 20:02:25.118908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_reach.h	2026-04-16 20:02:26.896992000 +0100
@@ -34,8 +34,9 @@
 void AAS_InitReachability(void);
 //continue calculating the reachabilities
 int AAS_ContinueInitReachability(float time);
-//
+#if 0
 int AAS_BestReachableLinkArea(aas_link_t *areas);
+#endif
 #endif //AASINTERN
 
 //returns true if the are has reachabilities to other areas
@@ -60,8 +61,6 @@
 int AAS_AreaSlime(int areanum);
 //returns true if the area has one or more ground faces
 int AAS_AreaGrounded(int areanum);
-//returns true if the area has one or more ladder faces
-int AAS_AreaLadder(int areanum);
 //returns true if the area is a jump pad
 int AAS_AreaJumpPad(int areanum);
 //returns true if the area is donotenter

```
