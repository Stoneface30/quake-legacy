# Diff: `code/botlib/be_aas_route.c`
**Canonical:** `wolfcamql-src` (sha256 `1a12bb3f4a5a...`, 77373 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `853760cc525d...`, 76930 bytes

_Diff stat: +24 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_route.c	2026-04-16 20:02:25.119908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_route.c	2026-04-16 20:02:19.849387000 +0100
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
 #include "l_utils.h"
 #include "l_memory.h"
 #include "l_log.h"
@@ -39,8 +39,8 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_aas_def.h"
@@ -106,7 +106,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static ID_INLINE int AAS_ClusterAreaNum(int cluster, int areanum)
+__inline int AAS_ClusterAreaNum(int cluster, int areanum)
 {
 	int side, areacluster;
 
@@ -166,13 +166,14 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static ID_INLINE int AAS_TravelFlagForType_inline(int traveltype)
+__inline int AAS_TravelFlagForType_inline(int traveltype)
 {
-	int tfl = 0;
+	int tfl;
 
-	if (traveltype & TRAVELFLAG_NOTTEAM1)
+	tfl = 0;
+	if (tfl & TRAVELFLAG_NOTTEAM1)
 		tfl |= TFL_NOTTEAM1;
-	if (traveltype & TRAVELFLAG_NOTTEAM2)
+	if (tfl & TRAVELFLAG_NOTTEAM2)
 		tfl |= TFL_NOTTEAM2;
 	traveltype &= TRAVELTYPE_MASK;
 	if (traveltype < 0 || traveltype >= MAX_TRAVELTYPES)
@@ -310,7 +311,7 @@
 
 	if (areanum <= 0 || areanum >= aasworld.numareas)
 	{
-		if (botDeveloper)
+		if (bot_developer)
 		{
 			botimport.Print(PRT_ERROR, "AAS_EnableRoutingArea: areanum %d out of range\n", areanum);
 		} //end if
@@ -338,7 +339,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static ID_INLINE float AAS_RoutingTime(void)
+__inline float AAS_RoutingTime(void)
 {
 	return AAS_Time();
 } //end of the function AAS_RoutingTime
@@ -378,7 +379,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static ID_INLINE int AAS_AreaContentsTravelFlags_inline(int areanum)
+__inline int AAS_AreaContentsTravelFlags_inline(int areanum)
 {
 	return aasworld.areacontentstravelflags[areanum];
 } //end of the function AAS_AreaContentsTravelFlags
@@ -505,11 +506,9 @@
 	aas_reversedlink_t *revlink;
 	aas_reachability_t *reach;
 	aas_areasettings_t *settings;
-#ifdef DEBUG
 	int starttime;
 
 	starttime = Sys_MilliSeconds();
-#endif
 	//if there are still area travel times, free the memory
 	if (aasworld.areatraveltimes) FreeMemory(aasworld.areatraveltimes);
 	//get the total size of all the area travel times
@@ -522,8 +521,7 @@
 		//
 		size += settings->numreachableareas * sizeof(unsigned short *);
 		//
-		size += settings->numreachableareas *
-			PAD(revreach->numlinks, sizeof(long)) * sizeof(unsigned short);
+		size += settings->numreachableareas * revreach->numlinks * sizeof(unsigned short);
 	} //end for
 	//allocate memory for the area travel times
 	ptr = (char *) GetClearedMemory(size);
@@ -543,7 +541,7 @@
 		for (l = 0; l < settings->numreachableareas; l++)
 		{
 			aasworld.areatraveltimes[i][l] = (unsigned short *) ptr;
-			ptr += PAD(revreach->numlinks, sizeof(long)) * sizeof(unsigned short);
+			ptr += revreach->numlinks * sizeof(unsigned short);
 			//reachability link
 			reach = &aasworld.reachability[settings->firstreachablearea + l];
 			//
@@ -888,8 +886,7 @@
 //===========================================================================
 void AAS_CreateAllRoutingCache(void)
 {
-	int i, j;
-	//int t;
+	int i, j, t;
 
 	aasworld.initialized = qtrue;
 	botimport.Print(PRT_MESSAGE, "AAS_CreateAllRoutingCache\n");
@@ -900,8 +897,7 @@
 		{
 			if (i == j) continue;
 			if (!AAS_AreaReachability(j)) continue;
-			AAS_AreaTravelTimeToGoalArea(i, aasworld.areas[i].center, j, TFL_DEFAULT);
-			//t = AAS_AreaTravelTimeToGoalArea(i, aasworld.areas[i].center, j, TFL_DEFAULT);
+			t = AAS_AreaTravelTimeToGoalArea(i, aasworld.areas[i].center, j, TFL_DEFAULT);
 			//Log_Write("traveltime from %d to %d is %d", i, j, t);
 		} //end for
 	} //end for
@@ -1068,12 +1064,12 @@
 	botimport.FS_Read(&routecacheheader, sizeof(routecacheheader_t), fp );
 	if (routecacheheader.ident != RCID)
 	{
-		AAS_Error("%s is not a route cache dump\n", filename);
+		AAS_Error("%s is not a route cache dump\n");
 		return qfalse;
 	} //end if
 	if (routecacheheader.version != RCVERSION)
 	{
-		AAS_Error("route cache dump has wrong version %d, should be %d\n", routecacheheader.version, RCVERSION);
+		AAS_Error("route cache dump has wrong version %d, should be %d", routecacheheader.version, RCVERSION);
 		return qfalse;
 	} //end if
 	if (routecacheheader.numareas != aasworld.numareas)
@@ -1603,10 +1599,10 @@
 		*reachnum = 0;
 		return qtrue;
 	}
-	//check !AAS_AreaReachability(areanum) with custom developer-only debug message
+	//
 	if (areanum <= 0 || areanum >= aasworld.numareas)
 	{
-		if (botDeveloper)
+		if (bot_developer)
 		{
 			botimport.Print(PRT_ERROR, "AAS_AreaTravelTimeToGoalArea: areanum %d out of range\n", areanum);
 		} //end if
@@ -1614,16 +1610,12 @@
 	} //end if
 	if (goalareanum <= 0 || goalareanum >= aasworld.numareas)
 	{
-		if (botDeveloper)
+		if (bot_developer)
 		{
 			botimport.Print(PRT_ERROR, "AAS_AreaTravelTimeToGoalArea: goalareanum %d out of range\n", goalareanum);
 		} //end if
 		return qfalse;
 	} //end if
-	if (!aasworld.areasettings[areanum].numreachableareas || !aasworld.areasettings[goalareanum].numreachableareas)
-	{
-		return qfalse;
-	} //end if
 	// make sure the routing cache doesn't grow to large
 	while(AvailableMemory() < 1 * 1024 * 1024) {
 		if (!AAS_FreeOldestCache()) break;
@@ -1774,7 +1766,7 @@
 //===========================================================================
 int AAS_AreaTravelTimeToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
 {
-	int traveltime, reachnum = 0;
+	int traveltime, reachnum;
 
 	if (AAS_AreaRouteToGoalArea(areanum, origin, goalareanum, travelflags, &traveltime, &reachnum))
 	{
@@ -1790,7 +1782,7 @@
 //===========================================================================
 int AAS_AreaReachabilityToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
 {
-	int traveltime, reachnum = 0;
+	int traveltime, reachnum;
 
 	if (AAS_AreaRouteToGoalArea(areanum, origin, goalareanum, travelflags, &traveltime, &reachnum))
 	{

```

### `quake3e`  — sha256 `bd89f64ae41a...`, 77681 bytes

_Diff stat: +55 / -45 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_route.c	2026-04-16 20:02:25.119908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_route.c	2026-04-16 20:02:26.896992000 +0100
@@ -47,7 +47,7 @@
 
 #define ROUTING_DEBUG
 
-//travel time in hundreths of a second = distance * 100 / speed
+//travel time in hundredths of a second = distance * 100 / speed
 #define DISTANCEFACTOR_CROUCH		1.3f		//crouch speed = 100
 #define DISTANCEFACTOR_SWIM			1		//should be 0.66, swim speed = 150
 #define DISTANCEFACTOR_WALK			0.33f	//walk speed = 300
@@ -132,7 +132,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitTravelFlagFromType(void)
+static void AAS_InitTravelFlagFromType(void)
 {
 	int i;
 
@@ -166,16 +166,17 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static ID_INLINE int AAS_TravelFlagForType_inline(int traveltype)
+static ID_INLINE int AAS_TravelFlagForType_inline(unsigned int traveltype)
 {
-	int tfl = 0;
+	int tfl;
 
+	tfl = 0;
 	if (traveltype & TRAVELFLAG_NOTTEAM1)
 		tfl |= TFL_NOTTEAM1;
 	if (traveltype & TRAVELFLAG_NOTTEAM2)
 		tfl |= TFL_NOTTEAM2;
 	traveltype &= TRAVELTYPE_MASK;
-	if (traveltype < 0 || traveltype >= MAX_TRAVELTYPES)
+	if (traveltype >= MAX_TRAVELTYPES)
 		return TFL_INVALID;
 	tfl |= aasworld.travelflagfortype[traveltype];
 	return tfl;
@@ -196,7 +197,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_UnlinkCache(aas_routingcache_t *cache)
+static void AAS_UnlinkCache(aas_routingcache_t *cache)
 {
 	if (cache->time_next) cache->time_next->time_prev = cache->time_prev;
 	else aasworld.newestcache = cache->time_prev;
@@ -211,7 +212,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_LinkCache(aas_routingcache_t *cache)
+static void AAS_LinkCache(aas_routingcache_t *cache)
 {
 	if (aasworld.newestcache)
 	{
@@ -244,7 +245,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_RemoveRoutingCacheInCluster( int clusternum )
+static void AAS_RemoveRoutingCacheInCluster( int clusternum )
 {
 	int i;
 	aas_routingcache_t *cache, *nextcache;
@@ -269,7 +270,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_RemoveRoutingCacheUsingArea( int areanum )
+static void AAS_RemoveRoutingCacheUsingArea( int areanum )
 {
 	int i, clusternum;
 	aas_routingcache_t *cache, *nextcache;
@@ -348,7 +349,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-int AAS_GetAreaContentsTravelFlags(int areanum)
+static int AAS_GetAreaContentsTravelFlags(int areanum)
 {
 	int contents, tfl;
 
@@ -398,7 +399,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitAreaContentsTravelFlags(void)
+static void AAS_InitAreaContentsTravelFlags(void)
 {
 	int i;
 
@@ -415,7 +416,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_CreateReversedReachability(void)
+static void AAS_CreateReversedReachability(void)
 {
 	int i, n;
 	aas_reversedlink_t *revlink;
@@ -442,7 +443,7 @@
 		//settings of the area
 		settings = &aasworld.areasettings[i];
 		//
-		if (settings->numreachableareas >= 128)
+		if (settings->numreachableareas > 128)
 			botimport.Print(PRT_WARNING, "area %d has more than 128 reachabilities\n", i);
 		//create reversed links for the reachabilities
 		for (n = 0; n < settings->numreachableareas && n < 128; n++)
@@ -496,13 +497,14 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_CalculateAreaTravelTimes(void)
+static void AAS_CalculateAreaTravelTimes(void)
 {
-	int i, l, n, size;
+	int i, l, n;
+	size_t size;
 	char *ptr;
 	vec3_t end;
-	aas_reversedreachability_t *revreach;
-	aas_reversedlink_t *revlink;
+	const aas_reversedreachability_t *revreach;
+	const aas_reversedlink_t *revlink;
 	aas_reachability_t *reach;
 	aas_areasettings_t *settings;
 #ifdef DEBUG
@@ -523,7 +525,7 @@
 		size += settings->numreachableareas * sizeof(unsigned short *);
 		//
 		size += settings->numreachableareas *
-			PAD(revreach->numlinks, sizeof(long)) * sizeof(unsigned short);
+			PAD(revreach->numlinks * sizeof(unsigned short), sizeof(uintptr_t));
 	} //end for
 	//allocate memory for the area travel times
 	ptr = (char *) GetClearedMemory(size);
@@ -543,7 +545,7 @@
 		for (l = 0; l < settings->numreachableareas; l++)
 		{
 			aasworld.areatraveltimes[i][l] = (unsigned short *) ptr;
-			ptr += PAD(revreach->numlinks, sizeof(long)) * sizeof(unsigned short);
+			ptr += PAD(revreach->numlinks * sizeof(unsigned short), sizeof(uintptr_t));
 			//reachability link
 			reach = &aasworld.reachability[settings->firstreachablearea + l];
 			//
@@ -565,7 +567,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_PortalMaxTravelTime(int portalnum)
+static int AAS_PortalMaxTravelTime(int portalnum)
 {
 	int l, n, t, maxt;
 	aas_portal_t *portal;
@@ -599,7 +601,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitPortalMaxTravelTimes(void)
+static void AAS_InitPortalMaxTravelTimes(void)
 {
 	int i;
 
@@ -620,7 +622,7 @@
 // Changes Globals:		-
 //===========================================================================
 /*
-int AAS_FreeOldestCache(void)
+static int AAS_FreeOldestCache(void)
 {
 	int i, j, bestcluster, bestarea, freed;
 	float besttime;
@@ -694,7 +696,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_FreeOldestCache(void)
+static int AAS_FreeOldestCache(void)
 {
 	int clusterareanum;
 	aas_routingcache_t *cache;
@@ -733,10 +735,10 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-aas_routingcache_t *AAS_AllocRoutingCache(int numtraveltimes)
+static aas_routingcache_t *AAS_AllocRoutingCache(int numtraveltimes)
 {
 	aas_routingcache_t *cache;
-	int size;
+	size_t size;
 
 	//
 	size = sizeof(aas_routingcache_t)
@@ -757,7 +759,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_FreeAllClusterAreaCache(void)
+static void AAS_FreeAllClusterAreaCache(void)
 {
 	int i, j;
 	aas_routingcache_t *cache, *nextcache;
@@ -789,7 +791,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitClusterAreaCache(void)
+static void AAS_InitClusterAreaCache(void)
 {
 	int i, size;
 	char *ptr;
@@ -818,7 +820,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_FreeAllPortalCache(void)
+static void AAS_FreeAllPortalCache(void)
 {
 	int i;
 	aas_routingcache_t *cache, *nextcache;
@@ -844,7 +846,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitPortalCache(void)
+static void AAS_InitPortalCache(void)
 {
 	//
 	aasworld.portalcache = (aas_routingcache_t **) GetClearedMemory(
@@ -856,7 +858,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_InitRoutingUpdate(void)
+static void AAS_InitRoutingUpdate(void)
 {
 	int i, maxreachabilityareas;
 
@@ -1032,7 +1034,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-aas_routingcache_t *AAS_ReadCache(fileHandle_t fp)
+static aas_routingcache_t *AAS_ReadCache(fileHandle_t fp)
 {
 	int size;
 	aas_routingcache_t *cache;
@@ -1051,7 +1053,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_ReadRouteCache(void)
+static int AAS_ReadRouteCache(void)
 {
 	int i, clusterareanum;//, size;
 	fileHandle_t fp;
@@ -1144,7 +1146,7 @@
 //===========================================================================
 #define MAX_REACHABILITYPASSAREAS		32
 
-void AAS_InitReachabilityAreas(void)
+static void AAS_InitReachabilityAreas(void)
 {
 	int i, j, numareas, areas[MAX_REACHABILITYPASSAREAS];
 	int numreachareas;
@@ -1242,7 +1244,7 @@
 #endif //ROUTING_DEBUG
 	//
 	routingcachesize = 0;
-	max_routingcachesize = 1024 * (int) LibVarValue("max_routingcache", "4096");
+	max_routingcachesize = 1024 * LibVarInteger("max_routingcache", "12288", 0, 65536);
 	// read any routing cache if available
 	AAS_ReadRouteCache();
 } //end of the function AAS_InitRouting
@@ -1289,15 +1291,15 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_UpdateAreaRoutingCache(aas_routingcache_t *areacache)
+static void AAS_UpdateAreaRoutingCache(aas_routingcache_t *areacache)
 {
 	int i, nextareanum, cluster, badtravelflags, clusterareanum, linknum;
 	int numreachabilityareas;
 	unsigned short int t, startareatraveltimes[128]; //NOTE: not more than 128 reachabilities per area allowed
 	aas_routingupdate_t *updateliststart, *updatelistend, *curupdate, *nextupdate;
 	aas_reachability_t *reach;
-	aas_reversedreachability_t *revreach;
-	aas_reversedlink_t *revlink;
+	const aas_reversedreachability_t *revreach;
+	const aas_reversedlink_t *revlink;
 
 #ifdef ROUTING_DEBUG
 	numareacacheupdates++;
@@ -1400,7 +1402,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-aas_routingcache_t *AAS_GetAreaRoutingCache(int clusternum, int areanum, int travelflags)
+static aas_routingcache_t *AAS_GetAreaRoutingCache(int clusternum, int areanum, int travelflags)
 {
 	int clusterareanum;
 	aas_routingcache_t *cache, *clustercache;
@@ -1446,7 +1448,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_UpdatePortalRoutingCache(aas_routingcache_t *portalcache)
+static void AAS_UpdatePortalRoutingCache(aas_routingcache_t *portalcache)
 {
 	int i, portalnum, clusterareanum, clusternum;
 	unsigned short int t;
@@ -1544,7 +1546,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-aas_routingcache_t *AAS_GetPortalRoutingCache(int clusternum, int areanum, int travelflags)
+static aas_routingcache_t *AAS_GetPortalRoutingCache(int clusternum, int areanum, int travelflags)
 {
 	aas_routingcache_t *cache;
 
@@ -1586,7 +1588,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_AreaRouteToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags, int *traveltime, int *reachnum)
+static int AAS_AreaRouteToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags, int *traveltime, int *reachnum)
 {
 	int clusternum, goalclusternum, portalnum, i, clusterareanum, bestreachnum;
 	unsigned short int t, besttime;
@@ -1624,10 +1626,14 @@
 	{
 		return qfalse;
 	} //end if
+
 	// make sure the routing cache doesn't grow to large
-	while(AvailableMemory() < 1 * 1024 * 1024) {
-		if (!AAS_FreeOldestCache()) break;
+	while ( routingcachesize > max_routingcachesize ) {
+		if ( !AAS_FreeOldestCache() ) {
+			break;
+		}
 	}
+
 	//
 	if (AAS_AreaDoNotEnter(areanum) || AAS_AreaDoNotEnter(goalareanum))
 	{
@@ -1788,7 +1794,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_AreaReachabilityToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
+static int AAS_AreaReachabilityToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
 {
 	int traveltime, reachnum = 0;
 
@@ -1908,6 +1914,7 @@
 		return qfalse;
 	return qtrue;
 } //end of the function AAS_PredictRoute
+#if 0
 //===========================================================================
 //
 // Parameter:			-
@@ -1918,6 +1925,7 @@
 {
 	return qfalse;
 } //end of the function AAS_BridgeWalkable
+#endif
 //===========================================================================
 //
 // Parameter:			-
@@ -2061,10 +2069,11 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_AreaVisible(int srcarea, int destarea)
+static int AAS_AreaVisible(int srcarea, int destarea)
 {
 	return qfalse;
 } //end of the function AAS_AreaVisible
+#if 0
 //===========================================================================
 //
 // Parameter:			-
@@ -2079,6 +2088,7 @@
 	VectorSubtract(point, p2, vec);
 	return VectorLength(vec);
 } //end of the function DistancePointToLine
+#endif
 //===========================================================================
 //
 // Parameter:			-

```

### `openarena-engine`  — sha256 `d5653aed8d6b...`, 77207 bytes

_Diff stat: +7 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_route.c	2026-04-16 20:02:25.119908000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_route.c	2026-04-16 22:48:25.711695700 +0100
@@ -1603,7 +1603,7 @@
 		*reachnum = 0;
 		return qtrue;
 	}
-	//check !AAS_AreaReachability(areanum) with custom developer-only debug message
+	//
 	if (areanum <= 0 || areanum >= aasworld.numareas)
 	{
 		if (botDeveloper)
@@ -1620,10 +1620,6 @@
 		} //end if
 		return qfalse;
 	} //end if
-	if (!aasworld.areasettings[areanum].numreachableareas || !aasworld.areasettings[goalareanum].numreachableareas)
-	{
-		return qfalse;
-	} //end if
 	// make sure the routing cache doesn't grow to large
 	while(AvailableMemory() < 1 * 1024 * 1024) {
 		if (!AAS_FreeOldestCache()) break;
@@ -1774,8 +1770,10 @@
 //===========================================================================
 int AAS_AreaTravelTimeToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
 {
-	int traveltime, reachnum = 0;
+	int traveltime, reachnum;
 
+	traveltime = 0;
+	reachnum = 0;
 	if (AAS_AreaRouteToGoalArea(areanum, origin, goalareanum, travelflags, &traveltime, &reachnum))
 	{
 		return traveltime;
@@ -1790,8 +1788,10 @@
 //===========================================================================
 int AAS_AreaReachabilityToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags)
 {
-	int traveltime, reachnum = 0;
+	int traveltime, reachnum;
 
+	traveltime = 0;
+	reachnum = 0;
 	if (AAS_AreaRouteToGoalArea(areanum, origin, goalareanum, travelflags, &traveltime, &reachnum))
 	{
 		return reachnum;

```
