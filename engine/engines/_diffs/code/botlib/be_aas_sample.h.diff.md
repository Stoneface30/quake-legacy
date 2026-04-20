# Diff: `code/botlib/be_aas_sample.h`
**Canonical:** `wolfcamql-src` (sha256 `7396a70d19d6...`, 3202 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3-source`  — sha256 `e3c89a934927...`, 3181 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_sample.h	2026-04-16 20:02:25.120907700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_sample.h	2026-04-16 20:02:19.850388800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */

```

### `quake3e`  — sha256 `a67979869dfb...`, 3145 bytes

_Diff stat: +5 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_sample.h	2026-04-16 20:02:25.120907700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_sample.h	2026-04-16 20:02:26.897995100 +0100
@@ -34,13 +34,14 @@
 void AAS_InitAASLinkedEntities(void);
 void AAS_FreeAASLinkHeap(void);
 void AAS_FreeAASLinkedEntities(void);
+#if 0
 aas_face_t *AAS_AreaGroundFace(int areanum, vec3_t point);
+#endif
 aas_face_t *AAS_TraceEndFace(aas_trace_t *trace);
 aas_plane_t *AAS_PlaneFromNum(int planenum);
 aas_link_t *AAS_AASLinkEntity(vec3_t absmins, vec3_t absmaxs, int entnum);
 aas_link_t *AAS_LinkEntityClientBBox(vec3_t absmins, vec3_t absmaxs, int entnum, int presencetype);
 qboolean AAS_PointInsideFace(int facenum, vec3_t point, float epsilon);
-qboolean AAS_InsideFace(aas_face_t *face, vec3_t pnormal, vec3_t point, float epsilon);
 void AAS_UnlinkFromAreas(aas_link_t *areas);
 #endif //AASINTERN
 
@@ -64,6 +65,9 @@
 int AAS_PointAreaNum(vec3_t point);
 //
 int AAS_PointReachabilityAreaIndex( vec3_t point );
+#if 0
 //returns the plane the given face is in
 void AAS_FacePlane(int facenum, vec3_t normal, float *dist);
+#endif
+
 

```
