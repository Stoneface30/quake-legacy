# Diff: `code/renderer/tr_world.c`
**Canonical:** `quake3e` (sha256 `2bca56258e2d...`, 23054 bytes)

## Variants

### `quake3-source`  — sha256 `2e1aa06f587d...`, 15730 bytes

_Diff stat: +35 / -313 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_world.c	2026-04-16 20:02:27.322645200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_world.c	2026-04-16 20:02:19.975633600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -58,11 +58,12 @@
 		return qtrue;
 	}
 
-	if ( tr.currentEntityNum != REFENTITYNUM_WORLD ) {
+	if ( tr.currentEntityNum != ENTITYNUM_WORLD ) {
 		sphereCull = R_CullLocalPointAndRadius( cv->localOrigin, cv->meshRadius );
 	} else {
 		sphereCull = R_CullPointAndRadius( cv->localOrigin, cv->meshRadius );
 	}
+	boxCull = CULL_OUT;
 	
 	// check for trivial reject
 	if ( sphereCull == CULL_OUT )
@@ -110,7 +111,7 @@
 This will also allow mirrors on both sides of a model without recursion.
 ================
 */
-static qboolean	R_CullSurface( const surfaceType_t *surface, shader_t *shader ) {
+static qboolean	R_CullSurface( surfaceType_t *surface, shader_t *shader ) {
 	srfSurfaceFace_t *sface;
 	float			d;
 
@@ -159,100 +160,17 @@
 }
 
 
-#ifdef USE_PMLIGHT
-qboolean R_LightCullBounds( const dlight_t* dl, const vec3_t mins, const vec3_t maxs )
-{
-	if ( dl->linear ) {
-		if (dl->transformed[0] - dl->radius > maxs[0] && dl->transformed2[0] - dl->radius > maxs[0] )
-			return qtrue;
-		if (dl->transformed[0] + dl->radius < mins[0] && dl->transformed2[0] + dl->radius < mins[0] )
-			return qtrue;
-
-		if (dl->transformed[1] - dl->radius > maxs[1] && dl->transformed2[1] - dl->radius > maxs[1] )
-			return qtrue;
-		if (dl->transformed[1] + dl->radius < mins[1] && dl->transformed2[1] + dl->radius < mins[1] )
-			return qtrue;
-
-		if (dl->transformed[2] - dl->radius > maxs[2] && dl->transformed2[2] - dl->radius > maxs[2] )
-			return qtrue;
-		if (dl->transformed[2] + dl->radius < mins[2] && dl->transformed2[2] + dl->radius < mins[2] )
-			return qtrue;
-
-		return qfalse;
-	}
-
-	if (dl->transformed[0] - dl->radius > maxs[0])
-		return qtrue;
-	if (dl->transformed[0] + dl->radius < mins[0])
-		return qtrue;
-
-	if (dl->transformed[1] - dl->radius > maxs[1])
-		return qtrue;
-	if (dl->transformed[1] + dl->radius < mins[1])
-		return qtrue;
-
-	if (dl->transformed[2] - dl->radius > maxs[2])
-		return qtrue;
-	if (dl->transformed[2] + dl->radius < mins[2])
-		return qtrue;
-
-	return qfalse;
-}
-
-
-static qboolean R_LightCullFace( const srfSurfaceFace_t* face, const dlight_t* dl )
-{
-	float d = DotProduct( dl->transformed, face->plane.normal ) - face->plane.dist;
-	if ( dl->linear )
-	{
-		float d2 = DotProduct( dl->transformed2, face->plane.normal ) - face->plane.dist;
-		if ( (d < -dl->radius) && (d2 < -dl->radius) )
-			return qtrue;
-		if ( (d > dl->radius) && (d2 > dl->radius) ) 
-			return qtrue;
-	} 
-	else 
-	{
-		if ( (d < -dl->radius) || (d > dl->radius) )
-			return qtrue;
-	}
-
-	return qfalse;
-}
-
-
-static qboolean R_LightCullSurface( const surfaceType_t* surface, const dlight_t* dl )
-{
-	switch (*surface) {
-	case SF_FACE:
-		return R_LightCullFace( (const srfSurfaceFace_t*)surface, dl );
-	case SF_GRID: {
-		const srfGridMesh_t* grid = (const srfGridMesh_t*)surface;
-		return R_LightCullBounds( dl, grid->meshBounds[0], grid->meshBounds[1] );
-		}
-	case SF_TRIANGLES: {
-		const srfTriangles_t* tris = (const srfTriangles_t*)surface;
-		return R_LightCullBounds( dl, tris->bounds[0], tris->bounds[1] );
-		}
-	default:
-		return qfalse;
-	};
-}
-#endif // USE_PMLIGHT
-
-
-#ifdef USE_LEGACY_DLIGHTS
 static int R_DlightFace( srfSurfaceFace_t *face, int dlightBits ) {
 	float		d;
 	int			i;
-	const dlight_t	*dl;
+	dlight_t	*dl;
 
-	for ( i = 0; i < tr.refdef.num_dlights; i++ ) {
+	for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
 		if ( ! ( dlightBits & ( 1 << i ) ) ) {
 			continue;
 		}
 		dl = &tr.refdef.dlights[i];
-		d = DotProduct( dl->transformed, face->plane.normal ) - face->plane.dist;
+		d = DotProduct( dl->origin, face->plane.normal ) - face->plane.dist;
 		if ( d < -dl->radius || d > dl->radius ) {
 			// dlight doesn't reach the plane
 			dlightBits &= ~( 1 << i );
@@ -263,14 +181,13 @@
 		tr.pc.c_dlightSurfacesCulled++;
 	}
 
-	face->dlightBits = dlightBits;
+	face->dlightBits[ tr.smpFrame ] = dlightBits;
 	return dlightBits;
 }
 
-
 static int R_DlightGrid( srfGridMesh_t *grid, int dlightBits ) {
 	int			i;
-	const dlight_t	*dl;
+	dlight_t	*dl;
 
 	for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
 		if ( ! ( dlightBits & ( 1 << i ) ) ) {
@@ -292,18 +209,18 @@
 		tr.pc.c_dlightSurfacesCulled++;
 	}
 
-	grid->dlightBits = dlightBits;
+	grid->dlightBits[ tr.smpFrame ] = dlightBits;
 	return dlightBits;
 }
 
 
 static int R_DlightTrisurf( srfTriangles_t *surf, int dlightBits ) {
 	// FIXME: more dlight culling to trisurfs...
-	surf->dlightBits = dlightBits;
+	surf->dlightBits[ tr.smpFrame ] = dlightBits;
 	return dlightBits;
 #if 0
 	int			i;
-	const dlight_t	*dl;
+	dlight_t	*dl;
 
 	for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
 		if ( ! ( dlightBits & ( 1 << i ) ) ) {
@@ -325,12 +242,11 @@
 		tr.pc.c_dlightSurfacesCulled++;
 	}
 
-	grid->dlightBits = dlightBits;
+	grid->dlightBits[ tr.smpFrame ] = dlightBits;
 	return dlightBits;
 #endif
 }
 
-
 /*
 ====================
 R_DlightSurface
@@ -357,7 +273,7 @@
 
 	return dlightBits;
 }
-#endif // USE_LEGACY_DLIGHTS
+
 
 
 /*
@@ -378,18 +294,6 @@
 		return;
 	}
 
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( R_GetDlightMode() ) 
-#endif
-	{
-		surf->vcVisible = tr.viewCount;
-		R_AddDrawSurf( surf->data, surf->shader, surf->fogIndex, 0 );
-		return;
-	}
-#endif // USE_PMLIGHT
-
-#ifdef USE_LEGACY_DLIGHTS
 	// check for dlighting
 	if ( dlightBits ) {
 		dlightBits = R_DlightSurface( surf, dlightBits );
@@ -397,115 +301,8 @@
 	}
 
 	R_AddDrawSurf( surf->data, surf->shader, surf->fogIndex, dlightBits );
-#endif // USE_LEGACY_DLIGHTS
 }
 
-
-/*
-=============================================================
-	PM LIGHTING
-=============================================================
-*/
-#ifdef USE_PMLIGHT
-static void R_AddLitSurface( msurface_t *surf, const dlight_t *light )
-{
-	// since we're not worried about offscreen lights casting into the frustum (ATM !!!)
-	// only add the "lit" version of this surface if it was already added to the view
-	//if ( surf->viewCount != tr.viewCount )
-	//	return;
-
-	// surfaces that were faceculled will still have the current viewCount in vcBSP
-	// because that's set to indicate that it's BEEN vis tested at all, to avoid
-	// repeated vis tests, not whether it actually PASSED the vis test or not
-	// only light surfaces that are GENUINELY visible, as opposed to merely in a visible LEAF
-	if ( surf->vcVisible != tr.viewCount ) {
-		return;
-	}
-
-	if ( surf->shader->lightingStage < 0 ) {
-		return;
-	}
-
-	if ( surf->lightCount == tr.lightCount )
-		return;
-
-	surf->lightCount = tr.lightCount;
-
-	if ( R_LightCullSurface( surf->data, light ) ) {
-		tr.pc.c_lit_culls++;
-		return;
-	}
-
-	R_AddLitSurf( surf->data, surf->shader, surf->fogIndex );
-}
-
-
-static void R_RecursiveLightNode( const mnode_t* node )
-{
-	qboolean children[2];
-	msurface_t** mark;
-	msurface_t* surf;
-	float d;
-	int c;
-	do {
-		// if the node wasn't marked as potentially visible, exit
-		if ( node->visframe != tr.visCount )
-			return;
-
-		if ( node->contents != CONTENTS_NODE )
-			break;
-
-		children[0] = children[1] = qfalse;
-
-		d = DotProduct( tr.light->origin, node->plane->normal ) - node->plane->dist;
-		if ( d > -tr.light->radius ) {
-			children[0] = qtrue;
-		}
-		if ( d < tr.light->radius ) {
-			children[1] = qtrue;
-		}
-
-		if ( tr.light->linear ) {
-			d = DotProduct( tr.light->origin2, node->plane->normal ) - node->plane->dist;
-			if ( d > -tr.light->radius ) {
-				children[0] = qtrue;
-			}
-			if ( d < tr.light->radius ) {
-				children[1] = qtrue;
-			}
-		}
-
-		if ( children[0] && children[1] ) {
-			R_RecursiveLightNode( node->children[0] );
-			node = node->children[1];
-		}
-		else if ( children[0] ) {
-			node = node->children[0];
-		}
-		else if ( children[1] ) {
-			node = node->children[1];
-		}
-		else {
-			return;
-		}
-
-	} while ( 1 );
-
-	tr.pc.c_lit_leafs++;
-
-	// add the individual surfaces
-	c = node->nummarksurfaces;
-	mark = node->firstmarksurface;
-	while ( c-- ) {
-		// the surface may have already been added if it spans multiple leafs
-		surf = *mark;
-		R_AddLitSurface( surf, tr.light );
-		mark++;
-	}
-}
-#endif // USE_PMLIGHT
-
-
 /*
 =============================================================
 
@@ -522,7 +319,7 @@
 void R_AddBrushModelSurfaces ( trRefEntity_t *ent ) {
 	bmodel_t	*bmodel;
 	int			clip;
-	const model_t		*pModel;
+	model_t		*pModel;
 	int			i;
 
 	pModel = R_GetModelByHandle( ent->e.hModel );
@@ -533,45 +330,12 @@
 	if ( clip == CULL_OUT ) {
 		return;
 	}
-
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( R_GetDlightMode() ) 
-#endif
-	{
-		dlight_t *dl;
-		int s;
-
-		for ( s = 0; s < bmodel->numSurfaces; s++ ) {
-			R_AddWorldSurface( bmodel->firstSurface + s, 0 );
-		}
-
-		R_SetupEntityLighting( &tr.refdef, ent );
-		
-		R_TransformDlights( tr.viewParms.num_dlights, tr.viewParms.dlights, &tr.or );
-
-		for ( i = 0; i < tr.viewParms.num_dlights; i++ ) {
-			dl = &tr.viewParms.dlights[i];
-			if ( !R_LightCullBounds( dl, bmodel->bounds[0], bmodel->bounds[1] ) ) {
-				tr.lightCount++;
-				tr.light = dl;
-				for ( s = 0; s < bmodel->numSurfaces; s++ ) {
-					R_AddLitSurface( bmodel->firstSurface + s, dl );
-				}
-			}
-		}
-		return;
-	}
-#endif // USE_PMLIGHT
-
-#ifdef USE_LEGACY_DLIGHTS
-	R_SetupEntityLighting( &tr.refdef, ent );
+	
 	R_DlightBmodel( bmodel );
 
 	for ( i = 0 ; i < bmodel->numSurfaces ; i++ ) {
 		R_AddWorldSurface( bmodel->firstSurface + i, tr.currentEntity->needDlights );
 	}
-#endif
 }
 
 
@@ -589,10 +353,10 @@
 R_RecursiveWorldNode
 ================
 */
-static void R_RecursiveWorldNode( mnode_t *node, unsigned int planeBits, unsigned int dlightBits ) {
+static void R_RecursiveWorldNode( mnode_t *node, int planeBits, int dlightBits ) {
 
 	do {
-		unsigned int newDlights[2];
+		int			newDlights[2];
 
 		// if the node wasn't marked as potentially visible, exit
 		if (node->visframe != tr.visCount) {
@@ -647,7 +411,7 @@
 
 		}
 
-		if ( node->contents != CONTENTS_NODE ) {
+		if ( node->contents != -1 ) {
 			break;
 		}
 
@@ -657,15 +421,11 @@
 		// determine which dlights are needed
 		newDlights[0] = 0;
 		newDlights[1] = 0;
-#ifdef USE_LEGACY_DLIGHTS
-#ifdef USE_PMLIGHT
-		if ( !R_GetDlightMode() )
-#endif
 		if ( dlightBits ) {
 			int	i;
 
 			for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
-				const dlight_t	*dl;
+				dlight_t	*dl;
 				float		dist;
 
 				if ( dlightBits & ( 1 << i ) ) {
@@ -681,16 +441,13 @@
 				}
 			}
 		}
-#endif // USE_LEGACY_DLIGHTS
 
 		// recurse down the children, front side first
-		R_RecursiveWorldNode( node->children[0], planeBits, newDlights[0] );
+		R_RecursiveWorldNode (node->children[0], planeBits, newDlights[0] );
 
 		// tail recurse
 		node = node->children[1];
-#ifdef USE_LEGACY_DLIGHTS
 		dlightBits = newDlights[1];
-#endif
 	} while ( 1 );
 
 	{
@@ -732,6 +489,7 @@
 			mark++;
 		}
 	}
+
 }
 
 
@@ -743,7 +501,7 @@
 static mnode_t *R_PointInLeaf( const vec3_t p ) {
 	mnode_t		*node;
 	float		d;
-	const cplane_t	*plane;
+	cplane_t	*plane;
 	
 	if ( !tr.world ) {
 		ri.Error (ERR_DROP, "R_PointInLeaf: bad model");
@@ -751,7 +509,7 @@
 
 	node = tr.world->nodes;
 	while( 1 ) {
-		if (node->contents != CONTENTS_NODE ) {
+		if (node->contents != -1) {
 			break;
 		}
 		plane = node->plane;
@@ -772,7 +530,7 @@
 ==============
 */
 static const byte *R_ClusterPVS (int cluster) {
-	if ( !tr.world->vis || cluster < 0 || cluster >= tr.world->numClusters ) {
+	if (!tr.world || !tr.world->vis || cluster < 0 || cluster >= tr.world->numClusters ) {
 		return tr.world->novis;
 	}
 
@@ -785,16 +543,12 @@
 =================
 */
 qboolean R_inPVS( const vec3_t p1, const vec3_t p2 ) {
-	const mnode_t *leaf;
-	const byte	*vis;
+	mnode_t *leaf;
+	byte	*vis;
 
 	leaf = R_PointInLeaf( p1 );
-	if ( leaf->cluster < 0 )
-		return qfalse;
-	vis = ri.CM_ClusterPVS( leaf->cluster );
+	vis = CM_ClusterPVS( leaf->cluster );
 	leaf = R_PointInLeaf( p2 );
-	if ( leaf->cluster < 0 )
-		return qfalse;
 
 	if ( !(vis[leaf->cluster>>3] & (1<<(leaf->cluster&7))) ) {
 		return qfalse;
@@ -868,7 +622,7 @@
 		}
 
 		// check for door connection
-		if ( leaf->area >= 0 && (tr.refdef.areamask[leaf->area>>3] & (1<<(leaf->area&7))) ) {
+		if ( (tr.refdef.areamask[leaf->area>>3] & (1<<(leaf->area&7)) ) ) {
 			continue;		// not visible
 		}
 
@@ -888,12 +642,7 @@
 R_AddWorldSurfaces
 =============
 */
-void R_AddWorldSurfaces( void ) {
-#ifdef USE_PMLIGHT
-	dlight_t* dl;
-	int i;
-#endif
-
+void R_AddWorldSurfaces (void) {
 	if ( !r_drawworld->integer ) {
 		return;
 	}
@@ -902,8 +651,8 @@
 		return;
 	}
 
-	tr.currentEntityNum = REFENTITYNUM_WORLD;
-	tr.shiftedEntityNum = tr.currentEntityNum << QSORT_REFENTITYNUM_SHIFT;
+	tr.currentEntityNum = ENTITYNUM_WORLD;
+	tr.shiftedEntityNum = tr.currentEntityNum << QSORT_ENTITYNUM_SHIFT;
 
 	// determine which leaves are in the PVS / areamask
 	R_MarkLeaves ();
@@ -912,35 +661,8 @@
 	ClearBounds( tr.viewParms.visBounds[0], tr.viewParms.visBounds[1] );
 
 	// perform frustum culling and add all the potentially visible surfaces
-	if ( tr.refdef.num_dlights > MAX_DLIGHTS ) {
-		tr.refdef.num_dlights = MAX_DLIGHTS;
-	}
-
-	R_RecursiveWorldNode( tr.world->nodes, 15, ( 1ULL << tr.refdef.num_dlights ) - 1 );
-
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( !R_GetDlightMode() )
-		return;
-#endif // USE_LEGACY_DLIGHTS
-
-	// "transform" all the dlights so that dl->transformed is actually populated
-	// (even though HERE it's == dl->origin) so we can always use R_LightCullBounds
-	// instead of having copypasted versions for both world and local cases
-
-	R_TransformDlights( tr.viewParms.num_dlights, tr.viewParms.dlights, &tr.viewParms.world );
-	for ( i = 0; i < tr.viewParms.num_dlights; i++ ) 
-	{
-		dl = &tr.viewParms.dlights[i];	
-		dl->head = dl->tail = NULL;
-		if ( R_CullDlight( dl ) == CULL_OUT ) {
-			tr.pc.c_light_cull_out++;
-			continue;
-		}
-		tr.pc.c_light_cull_in++;
-		tr.lightCount++;
-		tr.light = dl;
-		R_RecursiveLightNode( tr.world->nodes );
+	if ( tr.refdef.num_dlights > 32 ) {
+		tr.refdef.num_dlights = 32 ;
 	}
-#endif // USE_PMLIGHT
+	R_RecursiveWorldNode( tr.world->nodes, 15, ( 1 << tr.refdef.num_dlights ) - 1 );
 }

```
