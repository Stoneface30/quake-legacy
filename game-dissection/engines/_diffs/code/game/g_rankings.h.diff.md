# Diff: `code/game/g_rankings.h`
**Canonical:** `wolfcamql-src` (sha256 `1e4eff579a3f...`, 14245 bytes)

## Variants

### `quake3-source`  — sha256 `752dbd0ecb56...`, 14223 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.h	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_rankings.h	2026-04-16 20:02:19.908574000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -229,7 +229,7 @@
 #define QGR_KEY_PICKUP_UNKNOWN			1111021109
 #define QGR_KEY_TIME_UNKNOWN			1111021110
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_FRAG_NAILGIN			1211021200
 #define QGR_KEY_SUICIDE_NAILGIN			1111021201
@@ -296,7 +296,7 @@
 #define QGR_KEY_BOXES_BFG_AMMO			1111030800
 #define QGR_KEY_ROUNDS_BFG_AMMO			1111030801
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_BOXES_NAILGUN_AMMO		1111030900
 #define QGR_KEY_ROUNDS_NAILGUN_AMMO	 	1111030901
@@ -334,13 +334,13 @@
 #define QGR_KEY_REGEN					1111060500
 #define QGR_KEY_FLIGHT					1111060600
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // persistant powerup keys
 // new to team arena
 #define QGR_KEY_SCOUT					1111160800
 #define QGR_KEY_GUARD					1111160801
 #define QGR_KEY_DOUBLER					1111160802
-#define QGR_KEY_ARMORREGEN				1111160803
+#define QGR_KEY_AMMOREGEN				1111160803
 
 #endif //MISSIONPACK
 
@@ -351,7 +351,7 @@
 #define QGR_KEY_TELEPORTER				1111070100
 #define QGR_KEY_TELEPORTER_USE			1111070101
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_KAMIKAZE				1111070200
 #define QGR_KEY_KAMIKAZE_USE			1111070201

```

### `openarena-engine`  — sha256 `ff4f76d46d2a...`, 14244 bytes
Also identical in: ioquake3

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.h	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_rankings.h	2026-04-16 22:48:25.750042300 +0100
@@ -229,7 +229,7 @@
 #define QGR_KEY_PICKUP_UNKNOWN			1111021109
 #define QGR_KEY_TIME_UNKNOWN			1111021110
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_FRAG_NAILGIN			1211021200
 #define QGR_KEY_SUICIDE_NAILGIN			1111021201
@@ -296,7 +296,7 @@
 #define QGR_KEY_BOXES_BFG_AMMO			1111030800
 #define QGR_KEY_ROUNDS_BFG_AMMO			1111030801
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_BOXES_NAILGUN_AMMO		1111030900
 #define QGR_KEY_ROUNDS_NAILGUN_AMMO	 	1111030901
@@ -334,13 +334,13 @@
 #define QGR_KEY_REGEN					1111060500
 #define QGR_KEY_FLIGHT					1111060600
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // persistant powerup keys
 // new to team arena
 #define QGR_KEY_SCOUT					1111160800
 #define QGR_KEY_GUARD					1111160801
 #define QGR_KEY_DOUBLER					1111160802
-#define QGR_KEY_ARMORREGEN				1111160803
+#define QGR_KEY_AMMOREGEN				1111160803
 
 #endif //MISSIONPACK
 
@@ -351,7 +351,7 @@
 #define QGR_KEY_TELEPORTER				1111070100
 #define QGR_KEY_TELEPORTER_USE			1111070101
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 // new to team arena
 #define QGR_KEY_KAMIKAZE				1111070200
 #define QGR_KEY_KAMIKAZE_USE			1111070201

```

### `openarena-gamecode`  — sha256 `4a5f668a71ce...`, 14064 bytes

_Diff stat: +1 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_rankings.h	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_rankings.h	2026-04-16 22:48:24.173988500 +0100
@@ -229,7 +229,6 @@
 #define QGR_KEY_PICKUP_UNKNOWN			1111021109
 #define QGR_KEY_TIME_UNKNOWN			1111021110
 
-#if 1  //def MPACK
 // new to team arena
 #define QGR_KEY_FRAG_NAILGIN			1211021200
 #define QGR_KEY_SUICIDE_NAILGIN			1111021201
@@ -266,7 +265,6 @@
 #define QGR_KEY_SPLASH_TAKEN_CHAINGUN	1111021408
 #define QGR_KEY_PICKUP_CHAINGUN			1111021409
 #define QGR_KEY_TIME_CHAINGUN			1111021410
-#endif /* MISSIONPACK */
 
 // ammo keys
 #define QGR_KEY_BOXES					1111030000
@@ -296,7 +294,6 @@
 #define QGR_KEY_BOXES_BFG_AMMO			1111030800
 #define QGR_KEY_ROUNDS_BFG_AMMO			1111030801
 
-#if 1  //def MPACK
 // new to team arena
 #define QGR_KEY_BOXES_NAILGUN_AMMO		1111030900
 #define QGR_KEY_ROUNDS_NAILGUN_AMMO	 	1111030901
@@ -306,7 +303,6 @@
 // new to team arena
 #define QGR_KEY_BOXES_CHAINGUN_AMMO 	1111031100
 #define QGR_KEY_ROUNDS_CHAINGUN_AMMO 	1111031101
-#endif /* MISSIONPACK */
 
 // health keys
 #define QGR_KEY_HEALTH					1111040000
@@ -334,15 +330,13 @@
 #define QGR_KEY_REGEN					1111060500
 #define QGR_KEY_FLIGHT					1111060600
 
-#if 1  //def MPACK
 // persistant powerup keys
 // new to team arena
 #define QGR_KEY_SCOUT					1111160800
 #define QGR_KEY_GUARD					1111160801
 #define QGR_KEY_DOUBLER					1111160802
-#define QGR_KEY_ARMORREGEN				1111160803
+#define QGR_KEY_AMMOREGEN				1111160803
 
-#endif //MISSIONPACK
 
 // holdable item keys
 #define QGR_KEY_MEDKIT					1111070000
@@ -351,7 +345,6 @@
 #define QGR_KEY_TELEPORTER				1111070100
 #define QGR_KEY_TELEPORTER_USE			1111070101
 
-#if 1  //def MPACK
 // new to team arena
 #define QGR_KEY_KAMIKAZE				1111070200
 #define QGR_KEY_KAMIKAZE_USE			1111070201
@@ -361,7 +354,6 @@
 // new to team arena
 #define QGR_KEY_INVULNERABILITY			1111070400
 #define QGR_KEY_INVULNERABILITY_USE		1111070401
-#endif /* MISSIONPACK */
 
 // hazard keys
 #define QGR_KEY_HAZARD_DEATH			1111080000

```
