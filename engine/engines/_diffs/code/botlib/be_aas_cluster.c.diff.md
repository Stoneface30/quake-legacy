# Diff: `code/botlib/be_aas_cluster.c`
**Canonical:** `wolfcamql-src` (sha256 `d808087247b1...`, 52536 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `04e7a92ee946...`, 52500 bytes

_Diff stat: +16 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_cluster.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_cluster.c	2026-04-16 20:02:19.844383000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,7 +29,7 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
@@ -38,11 +38,10 @@
 #include "l_memory.h"
 #include "l_libvar.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
-#include "be_aas_cluster.h"
 
 extern botlib_import_t botimport;
 
@@ -130,7 +129,7 @@
 	//
 	if (portalnum == aasworld.numportals)
 	{
-		AAS_Error("no portal of area %d\n", areanum);
+		AAS_Error("no portal of area %d", areanum);
 		return qtrue;
 	} //end if
 	//
@@ -152,12 +151,12 @@
 	{
 		//remove the cluster portal flag contents
 		aasworld.areasettings[areanum].contents &= ~AREACONTENTS_CLUSTERPORTAL;
-		Log_Write("portal area %d is separating more than two clusters\r\n", areanum);
+		Log_Write("portal area %d is seperating more than two clusters\r\n", areanum);
 		return qfalse;
 	} //end else
 	if (aasworld.portalindexsize >= AAS_MAX_PORTALINDEXSIZE)
 	{
-		AAS_Error("AAS_MAX_PORTALINDEXSIZE\n");
+		AAS_Error("AAS_MAX_PORTALINDEXSIZE");
 		return qtrue;
 	} //end if
 	//set the area cluster number to the negative portal number
@@ -184,7 +183,7 @@
 	//
 	if (areanum <= 0 || areanum >= aasworld.numareas)
 	{
-		AAS_Error("AAS_FloodClusterAreas_r: areanum out of range\n");
+		AAS_Error("AAS_FloodClusterAreas_r: areanum out of range");
 		return qfalse;
 	} //end if
 	//if the area is already part of a cluster
@@ -194,7 +193,7 @@
 		//
 		//there's a reachability going from one cluster to another only in one direction
 		//
-		AAS_Error("cluster %d touched cluster %d at area %d\n",
+		AAS_Error("cluster %d touched cluster %d at area %d\r\n",
 				clusternum, aasworld.areasettings[areanum].cluster, areanum);
 		return qfalse;
 	} //end if
@@ -410,7 +409,7 @@
 			continue;
 		if (aasworld.numclusters >= AAS_MAX_CLUSTERS)
 		{
-			AAS_Error("AAS_MAX_CLUSTERS\n");
+			AAS_Error("AAS_MAX_CLUSTERS");
 			return qfalse;
 		} //end if
 		cluster = &aasworld.clusters[aasworld.numclusters];
@@ -449,7 +448,7 @@
 		{
 			if (aasworld.numportals >= AAS_MAX_PORTALS)
 			{
-				AAS_Error("AAS_MAX_PORTALS\n");
+				AAS_Error("AAS_MAX_PORTALS");
 				return;
 			} //end if
 			portal = &aasworld.portals[aasworld.numportals];
@@ -776,7 +775,7 @@
 			{
 				if (numareas >= MAX_PORTALAREAS)
 				{
-					AAS_Error("MAX_PORTALAREAS\n");
+					AAS_Error("MAX_PORTALAREAS");
 					return numareas;
 				} //end if
 				numareas = AAS_GetAdjacentAreasWithLessPresenceTypes_r(areanums, numareas, otherareanum);
@@ -811,7 +810,7 @@
 	//
 	Com_Memset(numareafrontfaces, 0, sizeof(numareafrontfaces));
 	Com_Memset(numareabackfaces, 0, sizeof(numareabackfaces));
-	numfrontfaces = numbackfaces = 0;
+	numareas = numfrontfaces = numbackfaces = 0;
 	numfrontareas = numbackareas = 0;
 	frontplanenum = backplanenum = -1;
 	//add any adjacent areas with less presence types
@@ -1168,7 +1167,7 @@
 			if (aasworld.areasettings[otherareanum].contents & AREACONTENTS_CLUSTERPORTAL) continue;
 			//if the area already has a cluster set
 			if (aasworld.areasettings[otherareanum].cluster) continue;
-			//another cluster is separated by this portal
+			//another cluster is seperated by this portal
 			numseperatedclusters++;
 			//flood the cluster
 			AAS_FloodCluster_r(otherareanum, numseperatedclusters);
@@ -1185,13 +1184,13 @@
 			if (aasworld.areasettings[otherareanum].contents & AREACONTENTS_CLUSTERPORTAL) continue;
 			//if the area already has a cluster set
 			if (aasworld.areasettings[otherareanum].cluster) continue;
-			//another cluster is separated by this portal
+			//another cluster is seperated by this portal
 			numseperatedclusters++;
 			//flood the cluster
 			AAS_FloodCluster_r(otherareanum, numseperatedclusters);
 			AAS_FloodClusterReachabilities(numseperatedclusters);
 		} //end for
-		//a portal must separate no more and no less than 2 clusters
+		//a portal must seperate no more and no less than 2 clusters
 		if (numseperatedclusters != 2)
 		{
 			aasworld.areasettings[i].contents &= ~AREACONTENTS_CLUSTERPORTAL;

```

### `quake3e`  — sha256 `88dc28392ecc...`, 52664 bytes

_Diff stat: +23 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_cluster.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_cluster.c	2026-04-16 20:02:26.891282500 +0100
@@ -53,7 +53,7 @@
 #define MAX_PORTALAREAS			1024
 
 // do not flood through area faces, only use reachabilities
-int nofaceflood = qtrue;
+static int nofaceflood = qtrue;
 
 //===========================================================================
 //
@@ -61,7 +61,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_RemoveClusterAreas(void)
+static void AAS_RemoveClusterAreas(void)
 {
 	int i;
 
@@ -76,6 +76,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
+#if 0
 void AAS_ClearCluster(int clusternum)
 {
 	int i;
@@ -110,13 +111,14 @@
 		} //end if
 	} //end for
 } //end of the function AAS_RemovePortalsClusterReference
+#endif
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_UpdatePortal(int areanum, int clusternum)
+static int AAS_UpdatePortal(int areanum, int clusternum)
 {
 	int portalnum;
 	aas_portal_t *portal;
@@ -175,7 +177,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_FloodClusterAreas_r(int areanum, int clusternum)
+static int AAS_FloodClusterAreas_r(int areanum, int clusternum)
 {
 	aas_area_t *area;
 	aas_face_t *face;
@@ -248,7 +250,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_FloodClusterAreasUsingReachabilities(int clusternum)
+static int AAS_FloodClusterAreasUsingReachabilities(int clusternum)
 {
 	int i, j, areanum;
 
@@ -280,13 +282,14 @@
 	} //end for
 	return qtrue;
 } //end of the function AAS_FloodClusterAreasUsingReachabilities
+#if 0
 //===========================================================================
 //
 // Parameter:			-
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_NumberClusterPortals(int clusternum)
+static void AAS_NumberClusterPortals(int clusternum)
 {
 	int i, portalnum;
 	aas_cluster_t *cluster;
@@ -307,13 +310,14 @@
 		} //end else
 	} //end for
 } //end of the function AAS_NumberClusterPortals
+#endif
 //===========================================================================
 //
 // Parameter:			-
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_NumberClusterAreas(int clusternum)
+static void AAS_NumberClusterAreas(int clusternum)
 {
 	int i, portalnum;
 	aas_cluster_t *cluster;
@@ -387,7 +391,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_FindClusters(void)
+static int AAS_FindClusters(void)
 {
 	int i;
 	aas_cluster_t *cluster;
@@ -437,7 +441,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_CreatePortals(void)
+static void AAS_CreatePortals(void)
 {
 	int i;
 	aas_portal_t *portal;
@@ -685,7 +689,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_ConnectedAreas_r(int *areanums, int numareas, int *connectedareas, int curarea)
+static void AAS_ConnectedAreas_r(int *areanums, int numareas, int *connectedareas, int curarea)
 {
 	int i, j, otherareanum, facenum;
 	aas_area_t *area;
@@ -721,7 +725,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-qboolean AAS_ConnectedAreas(int *areanums, int numareas)
+static qboolean AAS_ConnectedAreas(int *areanums, int numareas)
 {
 	int connectedareas[MAX_PORTALAREAS], i;
 
@@ -742,7 +746,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_GetAdjacentAreasWithLessPresenceTypes_r(int *areanums, int numareas, int curareanum)
+static int AAS_GetAdjacentAreasWithLessPresenceTypes_r(int *areanums, int numareas, int curareanum)
 {
 	int i, j, presencetype, otherpresencetype, otherareanum, facenum;
 	aas_area_t *area;
@@ -791,7 +795,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_CheckAreaForPossiblePortals(int areanum)
+static int AAS_CheckAreaForPossiblePortals(int areanum)
 {
 	int i, j, k, fen, ben, frontedgenum, backedgenum, facenum;
 	int areanums[MAX_PORTALAREAS], numareas, otherareanum;
@@ -918,7 +922,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_FindPossiblePortals(void)
+static void AAS_FindPossiblePortals(void)
 {
 	int i, numpossibleportals;
 
@@ -929,6 +933,7 @@
 	} //end for
 	botimport.Print(PRT_MESSAGE, "\r%6d possible portal areas\n", numpossibleportals);
 } //end of the function AAS_FindPossiblePortals
+#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -944,8 +949,6 @@
 		aasworld.areasettings[i].contents &= ~AREACONTENTS_CLUSTERPORTAL;
 	} //end for
 } //end of the function AAS_RemoveAllPortals
-
-#if 0
 //===========================================================================
 //
 // Parameter:				-
@@ -1055,7 +1058,6 @@
 		} //end for
 	} //end for
 } //end of the function AAS_FloodClusterReachabilities
-
 //===========================================================================
 //
 // Parameter:				-
@@ -1128,14 +1130,12 @@
 	} //end for
 	botimport.Print(PRT_MESSAGE, "\r%6d non closing portals removed\n", nonclosingportals);
 } //end of the function AAS_RemoveNotClusterClosingPortals
-
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-
 void AAS_RemoveNotClusterClosingPortals(void)
 {
 	int i, j, facenum, otherareanum, nonclosingportals, numseperatedclusters;
@@ -1202,14 +1202,12 @@
 	} //end for
 	botimport.Print(PRT_MESSAGE, "\r%6d non closing portals removed\n", nonclosingportals);
 } //end of the function AAS_RemoveNotClusterClosingPortals
-
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-
 void AAS_AddTeleporterPortals(void)
 {
 	int j, area2num, facenum, otherareanum;
@@ -1340,7 +1338,6 @@
 	} //end for
 	AAS_FreeBSPEntities(entities);
 } //end of the function AAS_AddTeleporterPortals
-
 //===========================================================================
 //
 // Parameter:				-
@@ -1361,16 +1358,14 @@
 		} //end for
 	} //end for
 } //end of the function AAS_AddTeleporterPortals
-
 #endif
-
 //===========================================================================
 //
 // Parameter:				-
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_TestPortals(void)
+static int AAS_TestPortals(void)
 {
 	int i;
 	aas_portal_t *portal;
@@ -1399,7 +1394,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_CountForcedClusterPortals(void)
+static void AAS_CountForcedClusterPortals(void)
 {
 	int num, i;
 
@@ -1420,7 +1415,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_CreateViewPortals(void)
+static void AAS_CreateViewPortals(void)
 {
 	int i;
 
@@ -1479,7 +1474,7 @@
 	AAS_RemoveClusterAreas();
 	//find possible cluster portals
 	AAS_FindPossiblePortals();
-	//craete portals to for the bot view
+	//create portals for the bot view
 	AAS_CreateViewPortals();
 	//remove all portals that are not closing a cluster
 	//AAS_RemoveNotClusterClosingPortals();

```

### `openarena-engine`  — sha256 `c5650835b587...`, 52536 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_cluster.c	2026-04-16 20:02:25.113325500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_cluster.c	2026-04-16 22:48:25.707438500 +0100
@@ -152,7 +152,7 @@
 	{
 		//remove the cluster portal flag contents
 		aasworld.areasettings[areanum].contents &= ~AREACONTENTS_CLUSTERPORTAL;
-		Log_Write("portal area %d is separating more than two clusters\r\n", areanum);
+		Log_Write("portal area %d is seperating more than two clusters\r\n", areanum);
 		return qfalse;
 	} //end else
 	if (aasworld.portalindexsize >= AAS_MAX_PORTALINDEXSIZE)
@@ -1168,7 +1168,7 @@
 			if (aasworld.areasettings[otherareanum].contents & AREACONTENTS_CLUSTERPORTAL) continue;
 			//if the area already has a cluster set
 			if (aasworld.areasettings[otherareanum].cluster) continue;
-			//another cluster is separated by this portal
+			//another cluster is seperated by this portal
 			numseperatedclusters++;
 			//flood the cluster
 			AAS_FloodCluster_r(otherareanum, numseperatedclusters);
@@ -1185,13 +1185,13 @@
 			if (aasworld.areasettings[otherareanum].contents & AREACONTENTS_CLUSTERPORTAL) continue;
 			//if the area already has a cluster set
 			if (aasworld.areasettings[otherareanum].cluster) continue;
-			//another cluster is separated by this portal
+			//another cluster is seperated by this portal
 			numseperatedclusters++;
 			//flood the cluster
 			AAS_FloodCluster_r(otherareanum, numseperatedclusters);
 			AAS_FloodClusterReachabilities(numseperatedclusters);
 		} //end for
-		//a portal must separate no more and no less than 2 clusters
+		//a portal must seperate no more and no less than 2 clusters
 		if (numseperatedclusters != 2)
 		{
 			aasworld.areasettings[i].contents &= ~AREACONTENTS_CLUSTERPORTAL;

```
