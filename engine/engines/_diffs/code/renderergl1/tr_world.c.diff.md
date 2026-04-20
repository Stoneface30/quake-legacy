# Diff: `code/renderergl1/tr_world.c`
**Canonical:** `wolfcamql-src` (sha256 `d0a40edd0fd0...`, 16382 bytes)

## Variants

### `ioquake3`  — sha256 `9ab3c7636b4f...`, 15785 bytes

_Diff stat: +15 / -41 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_world.c	2026-04-16 20:02:25.249044400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_world.c	2026-04-16 20:02:21.602743800 +0100
@@ -63,7 +63,7 @@
 	} else {
 		sphereCull = R_CullPointAndRadius( cv->localOrigin, cv->meshRadius );
 	}
-
+	
 	// check for trivial reject
 	if ( sphereCull == CULL_OUT )
 	{
@@ -77,7 +77,7 @@
 
 		boxCull = R_CullLocalBox( cv->meshBounds );
 
-		if ( boxCull == CULL_OUT )
+		if ( boxCull == CULL_OUT ) 
 		{
 			tr.pc.c_box_cull_patch_out++;
 			return qtrue;
@@ -144,7 +144,7 @@
 
 	// don't cull exactly on the plane, because there are levels of rounding
 	// through the BSP, ICD, and hardware that may cause pixel gaps if an
-	// epsilon isn't allowed here
+	// epsilon isn't allowed here 
 	if ( shader->cullType == CT_FRONT_SIDED ) {
 		if ( d < sface->plane.dist - 8 ) {
 			return qtrue;
@@ -164,11 +164,6 @@
 	int			i;
 	dlight_t	*dl;
 
-	if (r_dynamiclight->integer > 2) {
-		face->dlightBits = dlightBits;
-		return dlightBits;
-	}
-
 	for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
 		if ( ! ( dlightBits & ( 1 << i ) ) ) {
 			continue;
@@ -193,11 +188,6 @@
 	int			i;
 	dlight_t	*dl;
 
-	if (r_dynamiclight->integer > 2) {
-		grid->dlightBits = dlightBits;
-		return dlightBits;
-	}
-
 	for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
 		if ( ! ( dlightBits & ( 1 << i ) ) ) {
 			continue;
@@ -225,10 +215,6 @@
 
 static int R_DlightTrisurf( srfTriangles_t *surf, int dlightBits ) {
 	// FIXME: more dlight culling to trisurfs...
-	if (r_dynamiclight->integer > 2) {
-		surf->dlightBits = dlightBits;
-		return dlightBits;
-	}
 	surf->dlightBits = dlightBits;
 	return dlightBits;
 #if 0
@@ -295,20 +281,15 @@
 ======================
 */
 static void R_AddWorldSurface( msurface_t *surf, int dlightBits ) {
-	shader_t *shader;
-
 	if ( surf->viewCount == tr.viewCount ) {
 		return;		// already in this view
 	}
 
 	surf->viewCount = tr.viewCount;
-	shader = surf->shader;
-
 	// FIXME: bmodel fog?
 
 	// try to cull before dlighting or adding
-
-	if ( R_CullSurface( surf->data, shader ) ) {
+	if ( R_CullSurface( surf->data, surf->shader ) ) {
 		return;
 	}
 
@@ -318,7 +299,7 @@
 		dlightBits = ( dlightBits != 0 );
 	}
 
-	R_AddDrawSurf( surf->data, shader, surf->fogIndex, dlightBits );
+	R_AddDrawSurf( surf->data, surf->shader, surf->fogIndex, dlightBits );
 }
 
 /*
@@ -340,7 +321,7 @@
 	model_t		*pModel;
 	int			i;
 
-	pModel = R_GetModelByHandle( ent->ePtr->hModel );
+	pModel = R_GetModelByHandle( ent->e.hModel );
 
 	bmodel = pModel->bmodel;
 
@@ -348,7 +329,7 @@
 	if ( clip == CULL_OUT ) {
 		return;
 	}
-
+	
 	R_SetupEntityLighting( &tr.refdef, ent );
 	R_DlightBmodel( bmodel );
 
@@ -440,7 +421,7 @@
 		// determine which dlights are needed
 		newDlights[0] = 0;
 		newDlights[1] = 0;
-		if (r_dynamiclight->integer == 2  &&  dlightBits) {
+		if ( dlightBits ) {
 			int	i;
 
 			for ( i = 0 ; i < tr.refdef.num_dlights ; i++ ) {
@@ -450,8 +431,7 @@
 				if ( dlightBits & ( 1 << i ) ) {
 					dl = &tr.refdef.dlights[i];
 					dist = DotProduct( dl->origin, node->plane->normal ) - node->plane->dist;
-
-					//if ( dist < 0.0  &&  dist > -dl->radius ) {  ???
+					
 					if ( dist > -dl->radius ) {
 						newDlights[0] |= ( 1 << i );
 					}
@@ -460,9 +440,6 @@
 					}
 				}
 			}
-		} else if (r_dynamiclight->integer == 1  ||  r_dynamiclight->integer > 2) {
-			newDlights[0] = (1 << tr.refdef.num_dlights) - 1;
-			newDlights[1] = (1 << tr.refdef.num_dlights) - 1;
 		}
 
 		// recurse down the children, front side first
@@ -473,7 +450,6 @@
 		dlightBits = newDlights[1];
 	} while ( 1 );
 
-
 	{
 		// leaf node, so add mark surfaces
 		int			c;
@@ -505,7 +481,6 @@
 		// add the individual surfaces
 		mark = node->firstmarksurface;
 		c = node->nummarksurfaces;
-
 		while (c--) {
 			// the surface may have already been added if it
 			// spans multiple leafs
@@ -523,12 +498,11 @@
 R_PointInLeaf
 ===============
 */
-mnode_t *R_PointInLeaf (const vec3_t p)
-{
+static mnode_t *R_PointInLeaf( const vec3_t p ) {
 	mnode_t		*node;
 	float		d;
 	cplane_t	*plane;
-
+	
 	if ( !tr.world ) {
 		ri.Error (ERR_DROP, "R_PointInLeaf: bad model");
 	}
@@ -546,7 +520,7 @@
 			node = node->children[1];
 		}
 	}
-
+	
 	return node;
 }
 
@@ -609,8 +583,8 @@
 	// if the cluster is the same and the area visibility matrix
 	// hasn't changed, we don't need to mark everything again
 
-	// if r_showcluster was just turned on, remark everything
-	if ( tr.viewCluster == cluster && !tr.refdef.areamaskModified
+	// if r_showcluster was just turned on, remark everything 
+	if ( tr.viewCluster == cluster && !tr.refdef.areamaskModified 
 		&& !r_showcluster->modified ) {
 		return;
 	}
@@ -635,7 +609,7 @@
 	}
 
 	vis = R_ClusterPVS (tr.viewCluster);
-
+	
 	for (i=0,leaf=tr.world->nodes ; i<tr.world->numnodes ; i++, leaf++) {
 		cluster = leaf->cluster;
 		if ( cluster < 0 || cluster >= tr.world->numClusters ) {

```
