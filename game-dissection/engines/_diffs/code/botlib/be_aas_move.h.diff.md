# Diff: `code/botlib/be_aas_move.h`
**Canonical:** `wolfcamql-src` (sha256 `69c28e050760...`, 2978 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `b55e34d4142f...`, 2957 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_move.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_move.h	2026-04-16 20:02:19.847388800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `0361e7022794...`, 3026 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_move.h	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_move.h	2026-04-16 20:02:26.894280200 +0100
@@ -35,20 +35,20 @@
 
 //movement prediction
 int AAS_PredictClientMovement(struct aas_clientmove_s *move,
-							int entnum, vec3_t origin,
+							int entnum, const vec3_t origin,
 							int presencetype, int onground,
-							vec3_t velocity, vec3_t cmdmove,
+							const vec3_t velocity, const vec3_t cmdmove,
 							int cmdframes,
 							int maxframes, float frametime,
 							int stopevent, int stopareanum, int visualize);
 //predict movement until bounding box is hit
 int AAS_ClientMovementHitBBox(struct aas_clientmove_s *move,
-								int entnum, vec3_t origin,
+								int entnum, const vec3_t origin,
 								int presencetype, int onground,
-								vec3_t velocity, vec3_t cmdmove,
+								const vec3_t velocity, const vec3_t cmdmove,
 								int cmdframes,
 								int maxframes, float frametime,
-								vec3_t mins, vec3_t maxs, int visualize);
+								const vec3_t mins, const vec3_t maxs, int visualize);
 //returns true if on the ground at the given origin
 int AAS_OnGround(vec3_t origin, int presencetype, int passent);
 //returns true if swimming at the given origin

```
