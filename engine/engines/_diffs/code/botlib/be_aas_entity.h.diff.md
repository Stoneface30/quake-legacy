# Diff: `code/botlib/be_aas_entity.h`
**Canonical:** `wolfcamql-src` (sha256 `bd18fb7c5a81...`, 2581 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `a4497e8b20df...`, 2560 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_entity.h	2026-04-16 20:02:25.115358300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_entity.h	2026-04-16 20:02:19.845388400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `58e4e2781845...`, 2639 bytes

_Diff stat: +8 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_entity.h	2026-04-16 20:02:25.115358300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_entity.h	2026-04-16 20:02:26.893283500 +0100
@@ -39,23 +39,30 @@
 //updates an entity
 int AAS_UpdateEntity(int ent, bot_entitystate_t *state);
 //gives the entity data used for collision detection
+#if 0
 void AAS_EntityBSPData(int entnum, bsp_entdata_t *entdata);
+#endif
 #endif //AASINTERN
-
+#if 0
 //returns the size of the entity bounding box in mins and maxs
 void AAS_EntitySize(int entnum, vec3_t mins, vec3_t maxs);
+#endif
 //returns the BSP model number of the entity
 int AAS_EntityModelNum(int entnum);
 //returns the origin of an entity with the given model number
 int AAS_OriginOfMoverWithModelNum(int modelnum, vec3_t origin);
+#if 0
 //returns the best reachable area the entity is situated in
 int AAS_BestReachableEntityArea(int entnum);
+#endif
 //returns the info of the given entity
 void AAS_EntityInfo(int entnum, aas_entityinfo_t *info);
 //returns the next entity
 int AAS_NextEntity(int entnum);
+#if 0
 //returns the origin of the entity
 void AAS_EntityOrigin(int entnum, vec3_t origin);
+#endif
 //returns the entity type
 int AAS_EntityType(int entnum);
 //returns the model index of the entity

```
