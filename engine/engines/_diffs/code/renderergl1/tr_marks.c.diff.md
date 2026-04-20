# Diff: `code/renderergl1/tr_marks.c`
**Canonical:** `wolfcamql-src` (sha256 `070a614c1e1d...`, 16463 bytes)

## Variants

### `ioquake3`  — sha256 `cce488f138e8...`, 14606 bytes

_Diff stat: +14 / -58 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_marks.c	2026-04-16 20:02:25.244835800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_marks.c	2026-04-16 20:02:21.599744000 +0100
@@ -41,8 +41,8 @@
 static void R_ChopPolyBehindPlane( int numInPoints, vec3_t inPoints[MAX_VERTS_ON_POLY],
 								   int *numOutPoints, vec3_t outPoints[MAX_VERTS_ON_POLY], 
 							vec3_t normal, vec_t dist, vec_t epsilon) {
-	float    dists[MAX_VERTS_ON_POLY+4] = { 0 };
-	int      sides[MAX_VERTS_ON_POLY+4] = { 0 };
+	float		dists[MAX_VERTS_ON_POLY+4] = { 0 };
+	int			sides[MAX_VERTS_ON_POLY+4] = { 0 };
 	int			counts[3];
 	float		dot;
 	int			i, j;
@@ -125,8 +125,6 @@
 	}
 }
 
-static msurface_t *mxsurf[128];
-
 /*
 =================
 R_BoxSurfaces_r
@@ -159,19 +157,10 @@
 		if (*listlength >= listsize) break;
 		//
 		surf = *mark;
-		//ri.Printf(PRINT_ALL, "^3surf: %s\n", surf->shader->name);
 		// check if the surface has NOIMPACT or NOMARKS set
 		if ( ( surf->shader->surfaceFlags & ( SURF_NOIMPACT | SURF_NOMARKS ) )
-			 ||  ( surf->shader->contentFlags & CONTENTS_FOG ) ) {
-			if (r_ignoreNoMarks->integer == 0) {
-				surf->viewCount = tr.viewCount;
-			} else if (r_ignoreNoMarks->integer == 1) {
-				if (surf->shader->contentFlags & (CONTENTS_FOG | CONTENTS_WATER | CONTENTS_SLIME | CONTENTS_LAVA)) {
-					surf->viewCount = tr.viewCount;
-				}
-			} else {  // r_ignoreNoMarks->integer >= 2
-				// allow marks liquids, etc..
-			}
+			|| ( surf->shader->contentFlags & CONTENTS_FOG ) ) {
+			surf->viewCount = tr.viewCount;
 		}
 		// extra check for surfaces to avoid list overflows
 		else if (*(surf->data) == SF_FACE) {
@@ -180,26 +169,19 @@
 			if (s == 1 || s == 2) {
 				surf->viewCount = tr.viewCount;
 			} else if (DotProduct((( srfSurfaceFace_t * ) surf->data)->plane.normal, dir) > -0.5) {
-				// don't add faces that make sharp angles with the projection direction
-				//ri.Printf(PRINT_ALL, "^3sharp angle '%s'\n", surf->shader->name);
+			// don't add faces that make sharp angles with the projection direction
 				surf->viewCount = tr.viewCount;
-			} else {
-				//ri.Printf(PRINT_ALL, "^3surf: %s\n", surf->shader->name);
 			}
 		}
 		else if (*(surfaceType_t *) (surf->data) != SF_GRID &&
-				 *(surfaceType_t *) (surf->data) != SF_TRIANGLES) {
+			 *(surfaceType_t *) (surf->data) != SF_TRIANGLES)
 			surf->viewCount = tr.viewCount;
-		}
-
 		// check the viewCount because the surface may have
 		// already been added if it spans multiple leafs
 		if (surf->viewCount != tr.viewCount) {
 			surf->viewCount = tr.viewCount;
-			mxsurf[*listlength] = surf;
 			list[*listlength] = (surfaceType_t *) surf->data;
 			(*listlength)++;
-			//ri.Printf(PRINT_ALL, "^3surf: %s\n", surf->shader->name);
 		}
 		mark++;
 	}
@@ -211,7 +193,7 @@
 
 =================
 */
-qboolean R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
+void R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
 				   int numPlanes, vec3_t *normals, float *dists,
 				   int maxPoints, vec3_t pointBuffer,
 				   int maxFragments, markFragment_t *fragmentBuffer,
@@ -235,12 +217,12 @@
 	}
 	// completely clipped away?
 	if ( numClipPoints == 0 ) {
-		return qfalse;
+		return;
 	}
 
 	// add this fragment to the returned list
 	if ( numClipPoints + (*returnedPoints) > maxPoints ) {
-		return qfalse;	// not enough space for this polygon
+		return;	// not enough space for this polygon
 	}
 	/*
 	// all the clip points should be within the bounding box
@@ -262,19 +244,6 @@
 
 	(*returnedPoints) += numClipPoints;
 	(*returnedFragments)++;
-	return qtrue;
-}
-
-static void R_GotMarkSurfaceName (const char *type, const char *name)
-{
-	if (Q_stricmp(name, tr.markSurfaceNames[1])) {
-		Q_strncpyz(tr.markSurfaceNames[0], tr.markSurfaceNames[1], sizeof(tr.markSurfaceNames[0]));
-		Q_strncpyz(tr.markSurfaceNames[1], name, sizeof(tr.markSurfaceNames[1]));
-		ri.Printf(PRINT_ALL, "0: %s\n1: %s\n", tr.markSurfaceNames[0], tr.markSurfaceNames[1]);
-	}
-
-	ri.Printf(PRINT_ALL, "^3%s mark %s\n", type, name);
-	ri.Cmd_ExecuteText(EXEC_NOW, va("addchatline ^3%s\n", name));
 }
 
 /*
@@ -302,7 +271,6 @@
 	vec3_t			projectionDir;
 	vec3_t			v1, v2;
 	int				*indexes;
-	qboolean fragmentAdded;
 
 	if (numPoints <= 0) {
 		return 0;
@@ -327,7 +295,6 @@
 	}
 
 	if (numPoints > MAX_VERTS_ON_POLY) numPoints = MAX_VERTS_ON_POLY;
-
 	// create the bounding planes for the to be projected polygon
 	for ( i = 0 ; i < numPoints ; i++ ) {
 		VectorSubtract(points[(i+1)%numPoints], points[i], v1);
@@ -398,14 +365,11 @@
 					VectorNormalizeFast(normal);
 					if (DotProduct(normal, projectionDir) < -0.1) {
 						// add the fragments of this triangle
-						fragmentAdded = R_AddMarkFragments(numClipPoints, clipPoints,
+						R_AddMarkFragments(numClipPoints, clipPoints,
 										   numPlanes, normals, dists,
 										   maxPoints, pointBuffer,
 										   maxFragments, fragmentBuffer,
 										   &returnedPoints, &returnedFragments, mins, maxs);
-						if (r_debugMarkSurface->integer  &&  fragmentAdded) {
-							R_GotMarkSurfaceName("grid1", mxsurf[i]->shader->name);
-						}
 
 						if ( returnedFragments == maxFragments ) {
 							return returnedFragments;	// not enough space for more fragments
@@ -425,14 +389,12 @@
 					VectorNormalizeFast(normal);
 					if (DotProduct(normal, projectionDir) < -0.05) {
 						// add the fragments of this triangle
-						fragmentAdded = R_AddMarkFragments(numClipPoints, clipPoints,
+						R_AddMarkFragments(numClipPoints, clipPoints,
 										   numPlanes, normals, dists,
 										   maxPoints, pointBuffer,
 										   maxFragments, fragmentBuffer,
 										   &returnedPoints, &returnedFragments, mins, maxs);
-						if (r_debugMarkSurface->integer  &&  fragmentAdded) {
-							R_GotMarkSurfaceName("grid2", mxsurf[i]->shader->name);
-						}
+
 						if ( returnedFragments == maxFragments ) {
 							return returnedFragments;	// not enough space for more fragments
 						}
@@ -457,14 +419,11 @@
 				}
 
 				// add the fragments of this face
-				fragmentAdded = R_AddMarkFragments( 3 , clipPoints,
+				R_AddMarkFragments( 3 , clipPoints,
 								   numPlanes, normals, dists,
 								   maxPoints, pointBuffer,
 								   maxFragments, fragmentBuffer,
 								   &returnedPoints, &returnedFragments, mins, maxs);
-				if (r_debugMarkSurface->integer  &&  fragmentAdded) {
-					R_GotMarkSurfaceName("face", mxsurf[i]->shader->name);
-				}
 				if ( returnedFragments == maxFragments ) {
 					return returnedFragments;	// not enough space for more fragments
 				}
@@ -483,13 +442,10 @@
 				}
 
 				// add the fragments of this face
-				fragmentAdded = R_AddMarkFragments(3, clipPoints,
+				R_AddMarkFragments(3, clipPoints,
 								   numPlanes, normals, dists,
 								   maxPoints, pointBuffer,
 								   maxFragments, fragmentBuffer, &returnedPoints, &returnedFragments, mins, maxs);
-				if (r_debugMarkSurface->integer  &&  fragmentAdded) {
-					R_GotMarkSurfaceName("triangle", mxsurf[i]->shader->name);
-				}
 				if(returnedFragments == maxFragments)
 				{
 					return returnedFragments;	// not enough space for more fragments

```
