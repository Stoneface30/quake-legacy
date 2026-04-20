# Diff: `code/botlib/aasfile.h`
**Canonical:** `wolfcamql-src` (sha256 `727e1723604b...`, 9199 bytes)
Also identical in: ioquake3, quake3e

## Variants

### `quake3-source`  — sha256 `5ff45e7c4458...`, 9178 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\aasfile.h	2026-04-16 20:02:25.111324200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\aasfile.h	2026-04-16 20:02:19.842867400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -65,8 +65,8 @@
 #define FACE_LADDER					2		//ladder
 #define FACE_GROUND					4		//standing on ground when in this face
 #define FACE_GAP					8		//gap in the ground
-#define FACE_LIQUID					16		//face separating two areas with liquid
-#define FACE_LIQUIDSURFACE			32		//face separating liquid and air
+#define FACE_LIQUID					16		//face seperating two areas with liquid
+#define FACE_LIQUIDSURFACE			32		//face seperating liquid and air
 #define FACE_BRIDGE					64		//can walk over this face if bridge is closed
 
 //area contents
@@ -191,7 +191,7 @@
 //edge index, negative if vertexes are reversed
 typedef int aas_edgeindex_t;
 
-//a face bounds an area, often it will also separate two areas
+//a face bounds an area, often it will also seperate two areas
 typedef struct aas_face_s
 {
 	int planenum;						//number of the plane this face is in

```

### `openarena-engine`  — sha256 `8a7efaad5177...`, 9199 bytes
Also identical in: openarena-gamecode

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\aasfile.h	2026-04-16 20:02:25.111324200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\aasfile.h	2026-04-16 22:48:25.705436300 +0100
@@ -65,8 +65,8 @@
 #define FACE_LADDER					2		//ladder
 #define FACE_GROUND					4		//standing on ground when in this face
 #define FACE_GAP					8		//gap in the ground
-#define FACE_LIQUID					16		//face separating two areas with liquid
-#define FACE_LIQUIDSURFACE			32		//face separating liquid and air
+#define FACE_LIQUID					16		//face seperating two areas with liquid
+#define FACE_LIQUIDSURFACE			32		//face seperating liquid and air
 #define FACE_BRIDGE					64		//can walk over this face if bridge is closed
 
 //area contents
@@ -191,7 +191,7 @@
 //edge index, negative if vertexes are reversed
 typedef int aas_edgeindex_t;
 
-//a face bounds an area, often it will also separate two areas
+//a face bounds an area, often it will also seperate two areas
 typedef struct aas_face_s
 {
 	int planenum;						//number of the plane this face is in

```
