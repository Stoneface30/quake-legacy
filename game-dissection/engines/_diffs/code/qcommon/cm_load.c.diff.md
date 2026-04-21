# Diff: `code/qcommon/cm_load.c`
**Canonical:** `wolfcamql-src` (sha256 `ff0ee65c72df...`, 23048 bytes)

## Variants

### `quake3-source`  — sha256 `feef0ac1c2b9...`, 21255 bytes

_Diff stat: +52 / -107 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_load.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\cm_load.c	2026-04-16 20:02:19.956607700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -87,7 +87,7 @@
 CMod_LoadShaders
 =================
 */
-static void CMod_LoadShaders( const lump_t *l ) {
+void CMod_LoadShaders( lump_t *l ) {
 	dshader_t	*in, *out;
 	int			i, count;
 
@@ -109,8 +109,6 @@
 	for ( i=0 ; i<count ; i++, in++, out++ ) {
 		out->contentFlags = LittleLong( out->contentFlags );
 		out->surfaceFlags = LittleLong( out->surfaceFlags );
-
-		//Com_Printf("cm: %03d '%s' content:0x%x  surface:0x%x\n", i, out->shader, out->contentFlags, out->surfaceFlags);
 	}
 }
 
@@ -120,7 +118,7 @@
 CMod_LoadSubmodels
 =================
 */
-static void CMod_LoadSubmodels( const lump_t *l ) {
+void CMod_LoadSubmodels( lump_t *l ) {
 	dmodel_t	*in;
 	cmodel_t	*out;
 	int			i, j, count;
@@ -140,7 +138,7 @@
 		Com_Error( ERR_DROP, "MAX_SUBMODELS exceeded" );
 	}
 
-	for ( i=0 ; i<count ; i++, in++)
+	for ( i=0 ; i<count ; i++, in++, out++)
 	{
 		out = &cm.cmodels[i];
 
@@ -178,15 +176,15 @@
 
 =================
 */
-static void CMod_LoadNodes( const lump_t *l ) {
+void CMod_LoadNodes( lump_t *l ) {
 	dnode_t		*in;
 	int			child;
 	cNode_t		*out;
 	int			i, j, count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadNodes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -214,7 +212,7 @@
 
 =================
 */
-static void CM_BoundBrush( cbrush_t *b ) {
+void CM_BoundBrush( cbrush_t *b ) {
 	b->bounds[0][0] = -b->sides[0].plane->dist;
 	b->bounds[1][0] = b->sides[1].plane->dist;
 
@@ -232,14 +230,14 @@
 
 =================
 */
-static void CMod_LoadBrushes( const lump_t *l ) {
+void CMod_LoadBrushes( lump_t *l ) {
 	dbrush_t	*in;
 	cbrush_t	*out;
 	int			i, count;
 
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in)) {
-		Com_Error (ERR_DROP, "CMod_LoadBrushes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	}
 	count = l->filelen / sizeof(*in);
 
@@ -258,7 +256,6 @@
 		}
 		out->contents = cm.shaders[out->shaderNum].contentFlags;
 
-		//Com_Printf("brush: %03d %s\n", i, cm.shaders[out->shaderNum].shader);
 		CM_BoundBrush( out );
 	}
 
@@ -269,16 +266,16 @@
 CMod_LoadLeafs
 =================
 */
-static void CMod_LoadLeafs (const lump_t *l)
+void CMod_LoadLeafs (lump_t *l)
 {
 	int			i;
 	cLeaf_t		*out;
 	dleaf_t 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafs: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -287,7 +284,7 @@
 	cm.leafs = Hunk_Alloc( ( BOX_LEAFS + count ) * sizeof( *cm.leafs ), h_high );
 	cm.numLeafs = count;
 
-	out = cm.leafs;
+	out = cm.leafs;	
 	for ( i=0 ; i<count ; i++, in++, out++)
 	{
 		out->cluster = LittleLong (in->cluster);
@@ -312,17 +309,17 @@
 CMod_LoadPlanes
 =================
 */
-static void CMod_LoadPlanes (const lump_t *l)
+void CMod_LoadPlanes (lump_t *l)
 {
 	int			i, j;
 	cplane_t	*out;
 	dplane_t 	*in;
 	int			count;
 	int			bits;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadPlanes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -330,7 +327,7 @@
 	cm.planes = Hunk_Alloc( ( BOX_PLANES + count ) * sizeof( *cm.planes ), h_high );
 	cm.numPlanes = count;
 
-	out = cm.planes;
+	out = cm.planes;	
 
 	for ( i=0 ; i<count ; i++, in++, out++)
 	{
@@ -353,16 +350,16 @@
 CMod_LoadLeafBrushes
 =================
 */
-static void CMod_LoadLeafBrushes (const lump_t *l)
+void CMod_LoadLeafBrushes (lump_t *l)
 {
 	int			i;
 	int			*out;
 	int		 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafBrushes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	cm.leafbrushes = Hunk_Alloc( (count + BOX_BRUSHES) * sizeof( *cm.leafbrushes ), h_high );
@@ -380,16 +377,16 @@
 CMod_LoadLeafSurfaces
 =================
 */
-static void CMod_LoadLeafSurfaces( const lump_t *l )
+void CMod_LoadLeafSurfaces( lump_t *l )
 {
 	int			i;
 	int			*out;
 	int		 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafSurfaces: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	cm.leafsurfaces = Hunk_Alloc( count * sizeof( *cm.leafsurfaces ), h_high );
@@ -407,7 +404,7 @@
 CMod_LoadBrushSides
 =================
 */
-static void CMod_LoadBrushSides (const lump_t *l)
+void CMod_LoadBrushSides (lump_t *l)
 {
 	int				i;
 	cbrushside_t	*out;
@@ -417,14 +414,14 @@
 
 	in = (void *)(cmod_base + l->fileofs);
 	if ( l->filelen % sizeof(*in) ) {
-		Com_Error (ERR_DROP, "CMod_LoadBrushSides: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	}
 	count = l->filelen / sizeof(*in);
 
 	cm.brushsides = Hunk_Alloc( ( BOX_SIDES + count ) * sizeof( *cm.brushsides ), h_high );
 	cm.numBrushSides = count;
 
-	out = cm.brushsides;
+	out = cm.brushsides;	
 
 	for ( i=0 ; i<count ; i++, in++, out++) {
 		num = LittleLong( in->planeNum );
@@ -443,7 +440,7 @@
 CMod_LoadEntityString
 =================
 */
-static void CMod_LoadEntityString( const lump_t *l ) {
+void CMod_LoadEntityString( lump_t *l ) {
 	cm.entityString = Hunk_Alloc( l->filelen, h_high );
 	cm.numEntityChars = l->filelen;
 	Com_Memcpy (cm.entityString, cmod_base + l->fileofs, l->filelen);
@@ -455,7 +452,7 @@
 =================
 */
 #define	VIS_HEADER	8
-static void CMod_LoadVisibility( const lump_t *l ) {
+void CMod_LoadVisibility( lump_t *l ) {
 	int		len;
 	byte	*buf;
 
@@ -484,7 +481,7 @@
 =================
 */
 #define	MAX_PATCH_VERTS		1024
-static void CMod_LoadPatches( const lump_t *surfs, const lump_t *verts ) {
+void CMod_LoadPatches( lump_t *surfs, lump_t *verts ) {
 	drawVert_t	*dv, *dv_p;
 	dsurface_t	*in;
 	int			count;
@@ -495,16 +492,15 @@
 	int			width, height;
 	int			shaderNum;
 
-	//Com_Printf("...................  ^3CMod_LoadPatches\n");
 	in = (void *)(cmod_base + surfs->fileofs);
 	if (surfs->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadPatches: (a) funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	cm.numSurfaces = count = surfs->filelen / sizeof(*in);
 	cm.surfaces = Hunk_Alloc( cm.numSurfaces * sizeof( cm.surfaces[0] ), h_high );
 
 	dv = (void *)(cmod_base + verts->fileofs);
 	if (verts->filelen % sizeof(*dv))
-		Com_Error (ERR_DROP, "CMod_LoadPatches: (b) funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 
 	// scan through all the surfaces, but only load patches,
 	// not planar faces
@@ -534,7 +530,6 @@
 		shaderNum = LittleLong( in->shaderNum );
 		patch->contents = cm.shaders[shaderNum].contentFlags;
 		patch->surfaceFlags = cm.shaders[shaderNum].surfaceFlags;
-		//patch->shaderNum = shaderNum;
 
 		// create the internal facet structure
 		patch->pc = CM_GeneratePatchCollide( width, height, points );
@@ -543,13 +538,11 @@
 
 //==================================================================
 
-#if 0  // unused
-
-static unsigned CM_LumpChecksum(const lump_t *lump) {
+unsigned CM_LumpChecksum(lump_t *lump) {
 	return LittleLong (Com_BlockChecksum (cmod_base + lump->fileofs, lump->filelen));
 }
 
-static unsigned CM_Checksum(const dheader_t *header) {
+unsigned CM_Checksum(dheader_t *header) {
 	unsigned checksums[16];
 	checksums[0] = CM_LumpChecksum(&header->lumps[LUMP_SHADERS]);
 	checksums[1] = CM_LumpChecksum(&header->lumps[LUMP_LEAFS]);
@@ -566,8 +559,6 @@
 	return LittleLong(Com_BlockChecksum(checksums, 11 * 4));
 }
 
-#endif
-
 /*
 ==================
 CM_LoadMap
@@ -576,10 +567,7 @@
 ==================
 */
 void CM_LoadMap( const char *name, qboolean clientload, int *checksum ) {
-	union {
-		int				*i;
-		void			*v;
-	} buf;
+	int				*buf;
 	int				i;
 	dheader_t		header;
 	int				length;
@@ -589,8 +577,6 @@
 		Com_Error( ERR_DROP, "CM_LoadMap: NULL name" );
 	}
 
-	Com_Printf("CM_LoadMap(%s)\n", name);
-
 #ifndef BSPC
 	cm_noAreas = Cvar_Get ("cm_noAreas", "0", CVAR_CHEAT);
 	cm_noCurves = Cvar_Get ("cm_noCurves", "0", CVAR_CHEAT);
@@ -620,59 +606,29 @@
 	// load the file
 	//
 #ifndef BSPC
-	length = FS_ReadFile( name, &buf.v );
+	length = FS_ReadFile( name, (void **)&buf );
 #else
-	length = LoadQuakeFile((quakefile_t *) name, &buf.v);
+	length = LoadQuakeFile((quakefile_t *) name, (void **)&buf);
 #endif
 
-	if ( !buf.i ) {
-		//Com_Error (ERR_DROP, "Couldn't load %s", name);
-
-		i = 0;
-		while (1) {
-			if (MapNames[i].oldName == NULL) {
-				break;
-			}
-			if (!Q_stricmp(name, MapNames[i].oldName)) {
-				length = FS_ReadFile(MapNames[i].newName, &buf.v);
-				if (!buf.i) {
-					Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-					break;
-				}
-				break;
-			}
-
-			if (!Q_stricmp(name, MapNames[i].newName)) {
-				length = FS_ReadFile(MapNames[i].oldName, &buf.v);
-				if (!buf.i) {
-					Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-					break;
-				}
-				break;
-			}
-
-			i++;
-		}
-
-		if (!buf.i) {
-			Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-		}
+	if ( !buf ) {
+		Com_Error (ERR_DROP, "Couldn't load %s", name);
 	}
 
-	last_checksum = LittleLong (Com_BlockChecksum (buf.i, length));
+	last_checksum = LittleLong (Com_BlockChecksum (buf, length));
 	*checksum = last_checksum;
 
-	header = *(dheader_t *)buf.i;
+	header = *(dheader_t *)buf;
 	for (i=0 ; i<sizeof(dheader_t)/4 ; i++) {
 		((int *)&header)[i] = LittleLong ( ((int *)&header)[i]);
 	}
 
-	if ( header.version > BSP_VERSION ) {  //FIXME only check supported ones
+	if ( header.version != BSP_VERSION ) {
 		Com_Error (ERR_DROP, "CM_LoadMap: %s has wrong version number (%i should be %i)"
 		, name, header.version, BSP_VERSION );
 	}
 
-	cmod_base = (byte *)buf.i;
+	cmod_base = (byte *)buf;
 
 	// load into heap
 	CMod_LoadShaders( &header.lumps[LUMP_SHADERS] );
@@ -689,7 +645,7 @@
 	CMod_LoadPatches( &header.lumps[LUMP_SURFACES], &header.lumps[LUMP_DRAWVERTS] );
 
 	// we are NOT freeing the file, because it is cached for the ref
-	FS_FreeFile (buf.v);
+	FS_FreeFile (buf);
 
 	CM_InitBoxHull ();
 
@@ -716,15 +672,9 @@
 CM_ClipHandleToModel
 ==================
 */
-
-static cmodel_t emptyCmodel;
-
 cmodel_t	*CM_ClipHandleToModel( clipHandle_t handle ) {
 	if ( handle < 0 ) {
-		//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle );
-		//return NULL;
-		//Com_Printf("CM_ClipHandleToModel() bad handle %i\n", handle);
-		return &emptyCmodel;
+		Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle );
 	}
 	if ( handle < cm.numSubModels ) {
 		return &cm.cmodels[handle];
@@ -733,15 +683,12 @@
 		return &box_model;
 	}
 	if ( handle < MAX_SUBMODELS ) {
-		//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i < %i < %i", cm.numSubModels, handle, MAX_SUBMODELS );
-		Com_Printf("CM_ClipHandleToModel: bad handle %i < %i < %i\n", cm.numSubModels, handle, MAX_SUBMODELS);
-		return &emptyCmodel;
-	}
-	//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle + MAX_SUBMODELS );
-	Com_Printf("CM_ClipHandleToModel: last bad handle %i  (%i)\n", handle, handle + MAX_SUBMODELS);
-	return &emptyCmodel;
+		Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i < %i < %i", 
+			cm.numSubModels, handle, MAX_SUBMODELS );
+	}
+	Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle + MAX_SUBMODELS );
 
-	//return NULL;
+	return NULL;
 
 }
 
@@ -752,9 +699,7 @@
 */
 clipHandle_t	CM_InlineModel( int index ) {
 	if ( index < 0 || index >= cm.numSubModels ) {
-		//Com_Error (ERR_DROP, "CM_InlineModel: bad number %d", index);
-		//Com_Printf("CM_InlineModel: bad number %d\n", index);
-		return -1;
+		Com_Error (ERR_DROP, "CM_InlineModel: bad number");
 	}
 	return index;
 }
@@ -838,7 +783,7 @@
 		p->normal[i>>1] = -1;
 
 		SetPlaneSignbits( p );
-	}
+	}	
 }
 
 /*

```

### `openarena-engine`  — sha256 `fcdea95f2155...`, 21297 bytes
Also identical in: ioquake3

_Diff stat: +42 / -94 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\cm_load.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\cm_load.c	2026-04-16 22:48:25.904298500 +0100
@@ -87,7 +87,7 @@
 CMod_LoadShaders
 =================
 */
-static void CMod_LoadShaders( const lump_t *l ) {
+void CMod_LoadShaders( lump_t *l ) {
 	dshader_t	*in, *out;
 	int			i, count;
 
@@ -109,8 +109,6 @@
 	for ( i=0 ; i<count ; i++, in++, out++ ) {
 		out->contentFlags = LittleLong( out->contentFlags );
 		out->surfaceFlags = LittleLong( out->surfaceFlags );
-
-		//Com_Printf("cm: %03d '%s' content:0x%x  surface:0x%x\n", i, out->shader, out->contentFlags, out->surfaceFlags);
 	}
 }
 
@@ -120,7 +118,7 @@
 CMod_LoadSubmodels
 =================
 */
-static void CMod_LoadSubmodels( const lump_t *l ) {
+void CMod_LoadSubmodels( lump_t *l ) {
 	dmodel_t	*in;
 	cmodel_t	*out;
 	int			i, j, count;
@@ -178,15 +176,15 @@
 
 =================
 */
-static void CMod_LoadNodes( const lump_t *l ) {
+void CMod_LoadNodes( lump_t *l ) {
 	dnode_t		*in;
 	int			child;
 	cNode_t		*out;
 	int			i, j, count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadNodes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -214,7 +212,7 @@
 
 =================
 */
-static void CM_BoundBrush( cbrush_t *b ) {
+void CM_BoundBrush( cbrush_t *b ) {
 	b->bounds[0][0] = -b->sides[0].plane->dist;
 	b->bounds[1][0] = b->sides[1].plane->dist;
 
@@ -232,14 +230,14 @@
 
 =================
 */
-static void CMod_LoadBrushes( const lump_t *l ) {
+void CMod_LoadBrushes( lump_t *l ) {
 	dbrush_t	*in;
 	cbrush_t	*out;
 	int			i, count;
 
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in)) {
-		Com_Error (ERR_DROP, "CMod_LoadBrushes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	}
 	count = l->filelen / sizeof(*in);
 
@@ -258,7 +256,6 @@
 		}
 		out->contents = cm.shaders[out->shaderNum].contentFlags;
 
-		//Com_Printf("brush: %03d %s\n", i, cm.shaders[out->shaderNum].shader);
 		CM_BoundBrush( out );
 	}
 
@@ -269,16 +266,16 @@
 CMod_LoadLeafs
 =================
 */
-static void CMod_LoadLeafs (const lump_t *l)
+void CMod_LoadLeafs (lump_t *l)
 {
 	int			i;
 	cLeaf_t		*out;
 	dleaf_t 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafs: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -287,7 +284,7 @@
 	cm.leafs = Hunk_Alloc( ( BOX_LEAFS + count ) * sizeof( *cm.leafs ), h_high );
 	cm.numLeafs = count;
 
-	out = cm.leafs;
+	out = cm.leafs;	
 	for ( i=0 ; i<count ; i++, in++, out++)
 	{
 		out->cluster = LittleLong (in->cluster);
@@ -312,17 +309,17 @@
 CMod_LoadPlanes
 =================
 */
-static void CMod_LoadPlanes (const lump_t *l)
+void CMod_LoadPlanes (lump_t *l)
 {
 	int			i, j;
 	cplane_t	*out;
 	dplane_t 	*in;
 	int			count;
 	int			bits;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadPlanes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	if (count < 1)
@@ -330,7 +327,7 @@
 	cm.planes = Hunk_Alloc( ( BOX_PLANES + count ) * sizeof( *cm.planes ), h_high );
 	cm.numPlanes = count;
 
-	out = cm.planes;
+	out = cm.planes;	
 
 	for ( i=0 ; i<count ; i++, in++, out++)
 	{
@@ -353,16 +350,16 @@
 CMod_LoadLeafBrushes
 =================
 */
-static void CMod_LoadLeafBrushes (const lump_t *l)
+void CMod_LoadLeafBrushes (lump_t *l)
 {
 	int			i;
 	int			*out;
 	int		 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafBrushes: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	cm.leafbrushes = Hunk_Alloc( (count + BOX_BRUSHES) * sizeof( *cm.leafbrushes ), h_high );
@@ -380,16 +377,16 @@
 CMod_LoadLeafSurfaces
 =================
 */
-static void CMod_LoadLeafSurfaces( const lump_t *l )
+void CMod_LoadLeafSurfaces( lump_t *l )
 {
 	int			i;
 	int			*out;
 	int		 	*in;
 	int			count;
-
+	
 	in = (void *)(cmod_base + l->fileofs);
 	if (l->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadLeafSurfaces: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	count = l->filelen / sizeof(*in);
 
 	cm.leafsurfaces = Hunk_Alloc( count * sizeof( *cm.leafsurfaces ), h_high );
@@ -407,7 +404,7 @@
 CMod_LoadBrushSides
 =================
 */
-static void CMod_LoadBrushSides (const lump_t *l)
+void CMod_LoadBrushSides (lump_t *l)
 {
 	int				i;
 	cbrushside_t	*out;
@@ -417,14 +414,14 @@
 
 	in = (void *)(cmod_base + l->fileofs);
 	if ( l->filelen % sizeof(*in) ) {
-		Com_Error (ERR_DROP, "CMod_LoadBrushSides: funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	}
 	count = l->filelen / sizeof(*in);
 
 	cm.brushsides = Hunk_Alloc( ( BOX_SIDES + count ) * sizeof( *cm.brushsides ), h_high );
 	cm.numBrushSides = count;
 
-	out = cm.brushsides;
+	out = cm.brushsides;	
 
 	for ( i=0 ; i<count ; i++, in++, out++) {
 		num = LittleLong( in->planeNum );
@@ -443,7 +440,7 @@
 CMod_LoadEntityString
 =================
 */
-static void CMod_LoadEntityString( const lump_t *l ) {
+void CMod_LoadEntityString( lump_t *l ) {
 	cm.entityString = Hunk_Alloc( l->filelen, h_high );
 	cm.numEntityChars = l->filelen;
 	Com_Memcpy (cm.entityString, cmod_base + l->fileofs, l->filelen);
@@ -455,7 +452,7 @@
 =================
 */
 #define	VIS_HEADER	8
-static void CMod_LoadVisibility( const lump_t *l ) {
+void CMod_LoadVisibility( lump_t *l ) {
 	int		len;
 	byte	*buf;
 
@@ -484,7 +481,7 @@
 =================
 */
 #define	MAX_PATCH_VERTS		1024
-static void CMod_LoadPatches( const lump_t *surfs, const lump_t *verts ) {
+void CMod_LoadPatches( lump_t *surfs, lump_t *verts ) {
 	drawVert_t	*dv, *dv_p;
 	dsurface_t	*in;
 	int			count;
@@ -495,16 +492,15 @@
 	int			width, height;
 	int			shaderNum;
 
-	//Com_Printf("...................  ^3CMod_LoadPatches\n");
 	in = (void *)(cmod_base + surfs->fileofs);
 	if (surfs->filelen % sizeof(*in))
-		Com_Error (ERR_DROP, "CMod_LoadPatches: (a) funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 	cm.numSurfaces = count = surfs->filelen / sizeof(*in);
 	cm.surfaces = Hunk_Alloc( cm.numSurfaces * sizeof( cm.surfaces[0] ), h_high );
 
 	dv = (void *)(cmod_base + verts->fileofs);
 	if (verts->filelen % sizeof(*dv))
-		Com_Error (ERR_DROP, "CMod_LoadPatches: (b) funny lump size");
+		Com_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size");
 
 	// scan through all the surfaces, but only load patches,
 	// not planar faces
@@ -534,7 +530,6 @@
 		shaderNum = LittleLong( in->shaderNum );
 		patch->contents = cm.shaders[shaderNum].contentFlags;
 		patch->surfaceFlags = cm.shaders[shaderNum].surfaceFlags;
-		//patch->shaderNum = shaderNum;
 
 		// create the internal facet structure
 		patch->pc = CM_GeneratePatchCollide( width, height, points );
@@ -543,13 +538,11 @@
 
 //==================================================================
 
-#if 0  // unused
-
-static unsigned CM_LumpChecksum(const lump_t *lump) {
+unsigned CM_LumpChecksum(lump_t *lump) {
 	return LittleLong (Com_BlockChecksum (cmod_base + lump->fileofs, lump->filelen));
 }
 
-static unsigned CM_Checksum(const dheader_t *header) {
+unsigned CM_Checksum(dheader_t *header) {
 	unsigned checksums[16];
 	checksums[0] = CM_LumpChecksum(&header->lumps[LUMP_SHADERS]);
 	checksums[1] = CM_LumpChecksum(&header->lumps[LUMP_LEAFS]);
@@ -566,8 +559,6 @@
 	return LittleLong(Com_BlockChecksum(checksums, 11 * 4));
 }
 
-#endif
-
 /*
 ==================
 CM_LoadMap
@@ -589,8 +580,6 @@
 		Com_Error( ERR_DROP, "CM_LoadMap: NULL name" );
 	}
 
-	Com_Printf("CM_LoadMap(%s)\n", name);
-
 #ifndef BSPC
 	cm_noAreas = Cvar_Get ("cm_noAreas", "0", CVAR_CHEAT);
 	cm_noCurves = Cvar_Get ("cm_noCurves", "0", CVAR_CHEAT);
@@ -626,37 +615,7 @@
 #endif
 
 	if ( !buf.i ) {
-		//Com_Error (ERR_DROP, "Couldn't load %s", name);
-
-		i = 0;
-		while (1) {
-			if (MapNames[i].oldName == NULL) {
-				break;
-			}
-			if (!Q_stricmp(name, MapNames[i].oldName)) {
-				length = FS_ReadFile(MapNames[i].newName, &buf.v);
-				if (!buf.i) {
-					Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-					break;
-				}
-				break;
-			}
-
-			if (!Q_stricmp(name, MapNames[i].newName)) {
-				length = FS_ReadFile(MapNames[i].oldName, &buf.v);
-				if (!buf.i) {
-					Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-					break;
-				}
-				break;
-			}
-
-			i++;
-		}
-
-		if (!buf.i) {
-			Com_Error (ERR_DROP, "CM_LoadMap(): Couldn't load %s", name);
-		}
+		Com_Error (ERR_DROP, "Couldn't load %s", name);
 	}
 
 	last_checksum = LittleLong (Com_BlockChecksum (buf.i, length));
@@ -667,7 +626,7 @@
 		((int *)&header)[i] = LittleLong ( ((int *)&header)[i]);
 	}
 
-	if ( header.version > BSP_VERSION ) {  //FIXME only check supported ones
+	if ( header.version != BSP_VERSION ) {
 		Com_Error (ERR_DROP, "CM_LoadMap: %s has wrong version number (%i should be %i)"
 		, name, header.version, BSP_VERSION );
 	}
@@ -716,15 +675,9 @@
 CM_ClipHandleToModel
 ==================
 */
-
-static cmodel_t emptyCmodel;
-
 cmodel_t	*CM_ClipHandleToModel( clipHandle_t handle ) {
 	if ( handle < 0 ) {
-		//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle );
-		//return NULL;
-		//Com_Printf("CM_ClipHandleToModel() bad handle %i\n", handle);
-		return &emptyCmodel;
+		Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle );
 	}
 	if ( handle < cm.numSubModels ) {
 		return &cm.cmodels[handle];
@@ -733,15 +686,12 @@
 		return &box_model;
 	}
 	if ( handle < MAX_SUBMODELS ) {
-		//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i < %i < %i", cm.numSubModels, handle, MAX_SUBMODELS );
-		Com_Printf("CM_ClipHandleToModel: bad handle %i < %i < %i\n", cm.numSubModels, handle, MAX_SUBMODELS);
-		return &emptyCmodel;
-	}
-	//Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle + MAX_SUBMODELS );
-	Com_Printf("CM_ClipHandleToModel: last bad handle %i  (%i)\n", handle, handle + MAX_SUBMODELS);
-	return &emptyCmodel;
+		Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i < %i < %i", 
+			cm.numSubModels, handle, MAX_SUBMODELS );
+	}
+	Com_Error( ERR_DROP, "CM_ClipHandleToModel: bad handle %i", handle + MAX_SUBMODELS );
 
-	//return NULL;
+	return NULL;
 
 }
 
@@ -752,9 +702,7 @@
 */
 clipHandle_t	CM_InlineModel( int index ) {
 	if ( index < 0 || index >= cm.numSubModels ) {
-		//Com_Error (ERR_DROP, "CM_InlineModel: bad number %d", index);
-		//Com_Printf("CM_InlineModel: bad number %d\n", index);
-		return -1;
+		Com_Error (ERR_DROP, "CM_InlineModel: bad number");
 	}
 	return index;
 }
@@ -838,7 +786,7 @@
 		p->normal[i>>1] = -1;
 
 		SetPlaneSignbits( p );
-	}
+	}	
 }
 
 /*

```

### `quake3e`  — sha256 `18878ce243a0...`, 25920 bytes

_Diff stat: +339 / -248 lines_

_(full diff is 31018 bytes — see files directly)_
