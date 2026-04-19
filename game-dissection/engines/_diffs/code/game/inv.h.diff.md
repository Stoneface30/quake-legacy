# Diff: `code/game/inv.h`
**Canonical:** `wolfcamql-src` (sha256 `157e0b7aa4d7...`, 5144 bytes)

## Variants

### `quake3-source`  — sha256 `2f04387a7ad9...`, 5122 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\inv.h	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\inv.h	2026-04-16 20:02:19.913080300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -65,7 +65,7 @@
 #define INVENTORY_SCOUT				41
 #define INVENTORY_GUARD				42
 #define INVENTORY_DOUBLER			43
-#define INVENTORY_ARMORREGEN		44
+#define INVENTORY_AMMOREGEN			44
 
 #define INVENTORY_REDFLAG			45
 #define INVENTORY_BLUEFLAG			46
@@ -139,7 +139,7 @@
 #define MODELINDEX_SCOUT			42
 #define MODELINDEX_GUARD			43
 #define MODELINDEX_DOUBLER			44
-#define MODELINDEX_ARMORREGEN		45
+#define MODELINDEX_AMMOREGEN		45
 
 #define MODELINDEX_NEUTRALFLAG		46
 #define MODELINDEX_REDCUBE			47

```

### `openarena-engine`  — sha256 `485a9cf5e2b9...`, 5143 bytes
Also identical in: ioquake3

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\inv.h	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\inv.h	2026-04-16 22:48:25.753047000 +0100
@@ -65,7 +65,7 @@
 #define INVENTORY_SCOUT				41
 #define INVENTORY_GUARD				42
 #define INVENTORY_DOUBLER			43
-#define INVENTORY_ARMORREGEN		44
+#define INVENTORY_AMMOREGEN			44
 
 #define INVENTORY_REDFLAG			45
 #define INVENTORY_BLUEFLAG			46
@@ -139,7 +139,7 @@
 #define MODELINDEX_SCOUT			42
 #define MODELINDEX_GUARD			43
 #define MODELINDEX_DOUBLER			44
-#define MODELINDEX_ARMORREGEN		45
+#define MODELINDEX_AMMOREGEN		45
 
 #define MODELINDEX_NEUTRALFLAG		46
 #define MODELINDEX_REDCUBE			47

```

### `openarena-gamecode`  — sha256 `246f09b599f2...`, 5578 bytes

_Diff stat: +20 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\inv.h	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\inv.h	2026-04-16 22:48:24.177987400 +0100
@@ -65,26 +65,24 @@
 #define INVENTORY_SCOUT				41
 #define INVENTORY_GUARD				42
 #define INVENTORY_DOUBLER			43
-#define INVENTORY_ARMORREGEN		44
+#define INVENTORY_AMMOREGEN			44
 
 #define INVENTORY_REDFLAG			45
 #define INVENTORY_BLUEFLAG			46
 #define INVENTORY_NEUTRALFLAG		47
 #define INVENTORY_REDCUBE			48
 #define INVENTORY_BLUECUBE			49
+//Elimination mod: Domination inventory
+#define INVENTORY_POINTWHITE			50
+#define INVENTORY_POINTRED			51
+#define INVENTORY_POINTBLUE			52
+
 //enemy stuff
 #define ENEMY_HORIZONTAL_DIST		200
 #define ENEMY_HEIGHT				201
 #define NUM_VISIBLE_ENEMIES			202
 #define NUM_VISIBLE_TEAMMATES		203
 
-// if running the mission pack
-#ifdef MISSIONPACK
-
-//#error "running mission pack"
-
-#endif
-
 //item numbers (make sure they are in sync with bg_itemlist in bg_misc.c)
 #define MODELINDEX_ARMORSHARD		1
 #define MODELINDEX_ARMORCOMBAT		2
@@ -139,7 +137,7 @@
 #define MODELINDEX_SCOUT			42
 #define MODELINDEX_GUARD			43
 #define MODELINDEX_DOUBLER			44
-#define MODELINDEX_ARMORREGEN		45
+#define MODELINDEX_AMMOREGEN		45
 
 #define MODELINDEX_NEUTRALFLAG		46
 #define MODELINDEX_REDCUBE			47
@@ -149,6 +147,19 @@
 #define MODELINDEX_PROXLAUNCHER		50
 #define MODELINDEX_CHAINGUN			51
 
+//Elimination mod: Double Domination and Standard Domination
+
+#define MODELINDEX_POINTABLUE			52
+#define MODELINDEX_POINTBBLUE			53
+#define MODELINDEX_POINTARED			54
+#define MODELINDEX_POINTBRED			55
+#define MODELINDEX_POINTAWHITE			56
+#define MODELINDEX_POINTBWHITE			57
+#define MODELINDEX_POINTWHITE			58
+#define MODELINDEX_POINTRED			59
+#define MODELINDEX_POINTBLUE			60
+
+
 
 //
 #define WEAPONINDEX_GAUNTLET			1

```
