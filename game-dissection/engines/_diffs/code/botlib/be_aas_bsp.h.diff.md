# Diff: `code/botlib/be_aas_bsp.h`
**Canonical:** `wolfcamql-src` (sha256 `147f2afafb86...`, 3364 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `389ada6e1c94...`, 3343 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_bsp.h	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_bsp.h	2026-04-16 20:02:19.842867400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `53bbac8e6faa...`, 3403 bytes

_Diff stat: +6 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_bsp.h	2026-04-16 20:02:25.112324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_bsp.h	2026-04-16 20:02:26.890278900 +0100
@@ -66,6 +66,7 @@
 								int contentmask);
 //returns the contents at the given point
 int AAS_PointContents(vec3_t point);
+#if 0
 //returns true when p2 is in the PVS of p1
 qboolean AAS_inPVS(vec3_t p1, vec3_t p2);
 //returns true when p2 is in the PHS of p1
@@ -74,16 +75,17 @@
 qboolean AAS_AreasConnected(int area1, int area2);
 //creates a list with entities totally or partly within the given box
 int AAS_BoxEntities(vec3_t absmins, vec3_t absmaxs, int *list, int maxcount);
+#endif
 //gets the mins, maxs and origin of a BSP model
 void AAS_BSPModelMinsMaxsOrigin(int modelnum, vec3_t angles, vec3_t mins, vec3_t maxs, vec3_t origin);
 //handle to the next bsp entity
 int AAS_NextBSPEntity(int ent);
 //return the value of the BSP epair key
-int AAS_ValueForBSPEpairKey(int ent, char *key, char *value, int size);
+int AAS_ValueForBSPEpairKey(int ent, const char *key, char *value, int size);
 //get a vector for the BSP epair key
-int AAS_VectorForBSPEpairKey(int ent, char *key, vec3_t v);
+int AAS_VectorForBSPEpairKey(int ent, const char *key, vec3_t v);
 //get a float for the BSP epair key
-int AAS_FloatForBSPEpairKey(int ent, char *key, float *value);
+int AAS_FloatForBSPEpairKey(int ent, const char *key, float *value);
 //get an integer for the BSP epair key
-int AAS_IntForBSPEpairKey(int ent, char *key, int *value);
+int AAS_IntForBSPEpairKey(int ent, const char *key, int *value);
 

```
