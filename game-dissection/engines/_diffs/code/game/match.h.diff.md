# Diff: `code/game/match.h`
**Canonical:** `wolfcamql-src` (sha256 `a3d80207b00c...`, 4859 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `860f73b118c0...`, 4838 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\match.h	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\match.h	2026-04-16 20:02:19.914082700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `openarena-gamecode`  — sha256 `c4ef3601b791...`, 4986 bytes

_Diff stat: +11 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\match.h	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\match.h	2026-04-16 22:48:24.177987400 +0100
@@ -32,6 +32,7 @@
 #define MTCONTEXT_PATROLKEYAREA			64
 #define MTCONTEXT_REPLYCHAT				128
 #define MTCONTEXT_CTF					256
+#define MTCONTEXT_DD				512
 
 //message types
 #define MSG_NEWLEADER					1		//new leader
@@ -68,6 +69,11 @@
 #define MSG_HARVEST						32		//go harvest
 #define MSG_SUICIDE						33		//order to suicide
 //
+
+//Double Domination messages
+#define MSG_TAKEA					90
+#define MSG_TAKEB					91
+//
 #define MSG_ME							100
 #define MSG_EVERYONE					101
 #define MSG_MULTIPLENAMES				102
@@ -85,6 +91,8 @@
 //
 #define MSG_CTF							300		//ctf message
 
+
+
 //command sub types
 #define ST_SOMEWHERE					0
 #define ST_NEARITEM						1
@@ -104,6 +112,8 @@
 #define ST_RETURNEDFLAG					16384
 #define ST_TEAM							32768
 #define ST_1FCTFGOTFLAG					65535
+
+
 //ctf task preferences
 #define ST_DEFENDER						1
 #define ST_ATTACKER						2
@@ -132,3 +142,4 @@
 #define MORE							6
 
 
+

```
