# Diff: `code/botlib/be_aas_file.c`
**Canonical:** `wolfcamql-src` (sha256 `9006bcfef3c1...`, 25107 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `0a1418bc9ef9...`, 25088 bytes

_Diff stat: +10 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_file.c	2026-04-16 20:02:25.115358300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_file.c	2026-04-16 20:02:19.846388500 +0100
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
@@ -37,8 +37,8 @@
 #include "l_libvar.h"
 #include "l_utils.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
 #include "be_aas_def.h"
@@ -61,8 +61,8 @@
 		aasworld.bboxes[i].flags = LittleLong(aasworld.bboxes[i].flags);
 		for (j = 0; j < 3; j++)
 		{
-			aasworld.bboxes[i].mins[j] = LittleFloat(aasworld.bboxes[i].mins[j]);
-			aasworld.bboxes[i].maxs[j] = LittleFloat(aasworld.bboxes[i].maxs[j]);
+			aasworld.bboxes[i].mins[j] = LittleLong(aasworld.bboxes[i].mins[j]);
+			aasworld.bboxes[i].maxs[j] = LittleLong(aasworld.bboxes[i].maxs[j]);
 		} //end for
 	} //end for
 	//vertexes
@@ -277,11 +277,11 @@
 					aasworld.reachabilitysize * sizeof(aas_reachability_t) +
 					aasworld.numportals * sizeof(aas_portal_t) +
 					aasworld.numclusters * sizeof(aas_cluster_t);
-	botimport.Print(PRT_MESSAGE, "optimized size %d KB\n", optimized >> 10);
+	botimport.Print(PRT_MESSAGE, "optimzed size %d KB\n", optimized >> 10);
 } //end of the function AAS_FileInfo
 #endif //AASFILEDEBUG
 //===========================================================================
-// allocate memory and read a lump of an AAS file
+// allocate memory and read a lump of a AAS file
 //
 // Parameter:				-
 // Returns:					-
@@ -300,12 +300,12 @@
 	if (offset != *lastoffset)
 	{
 		botimport.Print(PRT_WARNING, "AAS file not sequentially read\n");
-		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET) < 0)
+		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET))
 		{
 			AAS_Error("can't seek to aas lump\n");
 			AAS_DumpAASData();
 			botimport.FS_FCloseFile(fp);
-			return NULL;
+			return 0;
 		} //end if
 	} //end if
 	//allocate memory

```

### `quake3e`  — sha256 `c9f45a62f85a...`, 30335 bytes

_Diff stat: +162 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_file.c	2026-04-16 20:02:25.115358300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_file.c	2026-04-16 20:02:26.893283500 +0100
@@ -51,7 +51,7 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void AAS_SwapAASData(void)
+static void AAS_SwapAASData(void)
 {
 	int i, j;
 	//bounding boxes
@@ -173,6 +173,130 @@
 		aasworld.clusters[i].firstportal = LittleLong(aasworld.clusters[i].firstportal);
 	} //end for
 } //end of the function AAS_SwapAASData
+
+#define CHECK_RANGE(first, count, limit) \
+	((uint64_t)(unsigned)(first) + (unsigned)(count) > (limit))
+
+#define UABS(c)	(((c) & 0x80000000) ? -(unsigned)c : (unsigned)c)
+
+static const char *AAS_ValidateAASData(void)
+{
+	unsigned c, numareas, numreachabilityareas;
+	int i, j;
+
+	c = aasworld.numvertexes ? aasworld.numvertexes : 1;
+
+	for (i = 0; i < aasworld.numedges; i++) {
+		if ((unsigned)aasworld.edges[i].v[0] >= c || (unsigned)aasworld.edges[i].v[1] >= c)
+			return "edges: bad vertexes";
+	}
+
+	for (i = 0; i < aasworld.edgeindexsize; i++) {
+		if (UABS(aasworld.edgeindex[i]) >= aasworld.numedges)
+			return "edgeindex: bad edge";
+	}
+
+	for (i = 0; i < aasworld.numfaces; i++) {
+		if ((unsigned)aasworld.faces[i].planenum >= aasworld.numplanes)
+			return "faces: bad planenum";
+		if (CHECK_RANGE(aasworld.faces[i].firstedge, aasworld.faces[i].numedges, aasworld.edgeindexsize))
+			return "faces: bad edges";
+		if ((unsigned)aasworld.faces[i].frontarea >= aasworld.numareas)
+			return "faces: bad frontarea";
+		if ((unsigned)aasworld.faces[i].backarea >= aasworld.numareas)
+			return "faces: bad backarea";
+	}
+
+	for (i = 0; i < aasworld.faceindexsize; i++) {
+		if (UABS(aasworld.faceindex[i]) >= aasworld.numfaces)
+			return "faceindex: bad face";
+	}
+
+	for (i = 0; i < aasworld.numareas; i++) {
+		if (CHECK_RANGE(aasworld.areas[i].firstface, aasworld.areas[i].numfaces, aasworld.faceindexsize))
+			return "areas: bad faces";
+	}
+
+	for (i = 0; i < aasworld.numareasettings; i++) {
+		if (CHECK_RANGE(aasworld.areasettings[i].firstreachablearea,
+						aasworld.areasettings[i].numreachableareas,
+						aasworld.reachabilitysize))
+			return "areasettings: bad reachable areas";
+		c = aasworld.areasettings[i].cluster;
+		if (c & 0x80000000) {
+			if (-c >= aasworld.numportals)
+				return "areasettings: bad portal";
+		} else {
+			if (c >= aasworld.numclusters)
+				return "areasettings: bad cluster";
+			if ((unsigned)aasworld.areasettings[i].clusterareanum >= (c ? aasworld.clusters[c].numareas : 1))
+				return "areasettings: bad clusterareanum";
+		}
+	}
+
+	for (i = 0; i < aasworld.reachabilitysize; i++) {
+		if ((unsigned)aasworld.reachability[i].areanum >= aasworld.numareasettings)
+			return "reachability: bad areanum";
+		switch (aasworld.reachability[i].traveltype & TRAVELTYPE_MASK)
+			case TRAVEL_ELEVATOR: case TRAVEL_JUMPPAD: case TRAVEL_FUNCBOB: continue;
+		if (UABS(aasworld.reachability[i].facenum) >= aasworld.numfaces)
+			return "reachability: bad facenum";
+		if (UABS(aasworld.reachability[i].edgenum) >= aasworld.numedges)
+			return "reachability: bad edgenum";
+	}
+
+	for (i = 0; i < aasworld.numnodes; i++) {
+		if ((unsigned)aasworld.nodes[i].planenum >= aasworld.numplanes)
+			return "nodes: bad planenum";
+		for (j = 0; j < 2; j++) {
+			c = aasworld.nodes[i].children[j];
+			if (c & 0x80000000) {
+				if (-c >= aasworld.numareasettings)
+					return "nodes: bad areasetting";
+			} else {
+				if (c >= aasworld.numnodes)
+					return "nodes: bad node";
+			}
+		}
+	}
+
+	for (i = 0; i < aasworld.numportals; i++) {
+		if ((unsigned)aasworld.portals[i].areanum >= aasworld.numareas)
+			return "portals: bad areanum";
+
+		c = aasworld.portals[i].frontcluster;
+		if (c >= aasworld.numclusters)
+			return "portals: bad frontcluster";
+		if ((unsigned)aasworld.portals[i].clusterareanum[0] >= (c ? aasworld.clusters[c].numareas : 1))
+			return "portals: bad clusterareanum[0]";
+
+		c = aasworld.portals[i].backcluster;
+		if (c >= aasworld.numclusters)
+			return "portals: bad backcluster";
+		if ((unsigned)aasworld.portals[i].clusterareanum[1] >= (c ? aasworld.clusters[c].numareas : 1))
+			return "portals: bad clusterareanum[1]";
+	}
+
+	for (i = 0; i < aasworld.portalindexsize; i++) {
+		if ((unsigned)aasworld.portalindex[i] >= aasworld.numportals)
+			return "portalindex: bad portal";
+	}
+
+	numareas = numreachabilityareas = 0;
+	for (i = 0; i < aasworld.numclusters; i++) {
+		if ((unsigned)aasworld.clusters[i].numareas > 0xffff - numareas)
+			return "clusters: bad numareas";
+		if ((unsigned)aasworld.clusters[i].numreachabilityareas > 0xffff - numreachabilityareas)
+			return "clusters: bad numreachabilityareas";
+		if (CHECK_RANGE(aasworld.clusters[i].firstportal, aasworld.clusters[i].numportals, aasworld.portalindexsize))
+			return "clusters: bad portals";
+		numareas += aasworld.clusters[i].numareas;
+		numreachabilityareas += aasworld.clusters[i].numreachabilityareas;
+	}
+
+	return NULL;
+}
+
 //===========================================================================
 // dump the current loaded aas file
 //
@@ -237,7 +361,7 @@
 // Changes Globals:		-
 //===========================================================================
 #ifdef AASFILEDEBUG
-void AAS_FileInfo(void)
+static void AAS_FileInfo(void)
 {
 	int i, n, optimized;
 
@@ -287,20 +411,27 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-char *AAS_LoadAASLump(fileHandle_t fp, int offset, int length, int *lastoffset, int size)
+static char *AAS_LoadAASLump(fileHandle_t fp, long offset, unsigned length, long *lastoffset, unsigned size)
 {
 	char *buf;
 	//
 	if (!length)
 	{
 		//just alloc a dummy
-		return (char *) GetClearedHunkMemory(size+1);
+		return (char *) GetClearedHunkMemory(size);
 	} //end if
+	if (length > INT_MAX || length % size || offset < 0 || length > LONG_MAX - offset)
+	{
+		AAS_Error("bad AAS lump offset/length\n");
+		AAS_DumpAASData();
+		botimport.FS_FCloseFile(fp);
+		return NULL;
+	}
 	//seek to the data
 	if (offset != *lastoffset)
 	{
 		botimport.Print(PRT_WARNING, "AAS file not sequentially read\n");
-		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET) < 0)
+		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET))
 		{
 			AAS_Error("can't seek to aas lump\n");
 			AAS_DumpAASData();
@@ -309,13 +440,15 @@
 		} //end if
 	} //end if
 	//allocate memory
-	buf = (char *) GetClearedHunkMemory(length+1);
+	buf = (char *) GetClearedHunkMemory(length);
 	//read the data
-	if (length)
-	{
-		botimport.FS_Read(buf, length, fp );
-		*lastoffset += length;
-	} //end if
+	if (botimport.FS_Read(buf, length, fp) != length) {
+		AAS_Error("can't read AAS file\n");
+		AAS_DumpAASData();
+		botimport.FS_FCloseFile(fp);
+		return NULL;
+	}
+	*lastoffset = offset + length;
 	return buf;
 } //end of the function AAS_LoadAASLump
 //===========================================================================
@@ -324,7 +457,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_DData(unsigned char *data, int size)
+static void AAS_DData(unsigned char *data, int size)
 {
 	int i;
 
@@ -344,7 +477,9 @@
 {
 	fileHandle_t fp;
 	aas_header_t header;
-	int offset, length, lastoffset;
+	long offset, lastoffset;
+	unsigned length;
+	const char *err;
 
 	botimport.Print(PRT_MESSAGE, "trying to load %s\n", filename);
 	//dump current loaded aas file
@@ -357,8 +492,13 @@
 		return BLERR_CANNOTOPENAASFILE;
 	} //end if
 	//read the header
-	botimport.FS_Read(&header, sizeof(aas_header_t), fp );
-	lastoffset = sizeof(aas_header_t);
+	lastoffset = botimport.FS_Read(&header, sizeof(aas_header_t), fp);
+	if (lastoffset != sizeof(aas_header_t))
+	{
+		AAS_Error("AAS file %s is too short\n", filename);
+		botimport.FS_FCloseFile(fp);
+		return BLERR_CANNOTOPENAASFILE;
+	}
 	//check header identification
 	header.ident = LittleLong(header.ident);
 	if (header.ident != AASID)
@@ -476,6 +616,12 @@
 	if (aasworld.numclusters && !aasworld.clusters) return BLERR_CANNOTREADAASLUMP;
 	//swap everything
 	AAS_SwapAASData();
+	err = AAS_ValidateAASData();
+	if (err) {
+		AAS_Error("AAS file %s is corrupted: %s\n", filename, err);
+		botimport.FS_FCloseFile(fp);
+		return BLERR_CANNOTREADAASLUMP;
+	}
 	//aas file is loaded
 	aasworld.loaded = qtrue;
 	//close the file
@@ -495,7 +641,7 @@
 //===========================================================================
 static int AAS_WriteAASLump_offset;
 
-int AAS_WriteAASLump(fileHandle_t fp, aas_header_t *h, int lumpnum, void *data, int length)
+static int AAS_WriteAASLump(fileHandle_t fp, aas_header_t *h, int lumpnum, void *data, int length)
 {
 	aas_lump_t *lump;
 

```

### `openarena-engine`  — sha256 `0384098030cb...`, 25100 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_file.c	2026-04-16 20:02:25.115358300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_file.c	2026-04-16 22:48:25.708437600 +0100
@@ -61,8 +61,8 @@
 		aasworld.bboxes[i].flags = LittleLong(aasworld.bboxes[i].flags);
 		for (j = 0; j < 3; j++)
 		{
-			aasworld.bboxes[i].mins[j] = LittleFloat(aasworld.bboxes[i].mins[j]);
-			aasworld.bboxes[i].maxs[j] = LittleFloat(aasworld.bboxes[i].maxs[j]);
+			aasworld.bboxes[i].mins[j] = LittleLong(aasworld.bboxes[i].mins[j]);
+			aasworld.bboxes[i].maxs[j] = LittleLong(aasworld.bboxes[i].maxs[j]);
 		} //end for
 	} //end for
 	//vertexes
@@ -277,7 +277,7 @@
 					aasworld.reachabilitysize * sizeof(aas_reachability_t) +
 					aasworld.numportals * sizeof(aas_portal_t) +
 					aasworld.numclusters * sizeof(aas_cluster_t);
-	botimport.Print(PRT_MESSAGE, "optimized size %d KB\n", optimized >> 10);
+	botimport.Print(PRT_MESSAGE, "optimzed size %d KB\n", optimized >> 10);
 } //end of the function AAS_FileInfo
 #endif //AASFILEDEBUG
 //===========================================================================
@@ -300,7 +300,7 @@
 	if (offset != *lastoffset)
 	{
 		botimport.Print(PRT_WARNING, "AAS file not sequentially read\n");
-		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET) < 0)
+		if (botimport.FS_Seek(fp, offset, FS_SEEK_SET))
 		{
 			AAS_Error("can't seek to aas lump\n");
 			AAS_DumpAASData();

```
