# Diff: `code/renderergl2/tr_marks.c`
**Canonical:** `wolfcamql-src` (sha256 `e06bcd07af05...`, 16503 bytes)

## Variants

### `ioquake3`  — sha256 `924ba5ee5c28...`, 14946 bytes

_Diff stat: +10 / -45 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_marks.c	2026-04-16 20:02:25.261257900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_marks.c	2026-04-16 20:02:21.613251700 +0100
@@ -125,8 +125,6 @@
 	}
 }
 
-static msurface_t *mxsurf[128];
-
 /*
 =================
 R_BoxSurfaces_r
@@ -165,15 +163,7 @@
 		// check if the surface has NOIMPACT or NOMARKS set
 		if ( ( surf->shader->surfaceFlags & ( SURF_NOIMPACT | SURF_NOMARKS ) )
 			|| ( surf->shader->contentFlags & CONTENTS_FOG ) ) {
-			if (r_ignoreNoMarks->integer == 0) {
-				*surfViewCount = tr.viewCount;
-			} else if (r_ignoreNoMarks->integer == 1) {
-				if (surf->shader->contentFlags & (CONTENTS_FOG | CONTENTS_WATER | CONTENTS_SLIME | CONTENTS_LAVA)) {
-					*surfViewCount = tr.viewCount;
-				}
-			} else {  // r_ignoreNoMarks->integer >= 2
-				// allow marks liquids, etc...
-			}
+			*surfViewCount = tr.viewCount;
 		}
 		// extra check for surfaces to avoid list overflows
 		else if (*(surf->data) == SF_FACE) {
@@ -193,7 +183,6 @@
 		// already been added if it spans multiple leafs
 		if (*surfViewCount != tr.viewCount) {
 			*surfViewCount = tr.viewCount;
-			mxsurf[*listlength] = surf;
 			list[*listlength] = surf->data;
 			(*listlength)++;
 		}
@@ -207,7 +196,7 @@
 
 =================
 */
-qboolean R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
+void R_AddMarkFragments(int numClipPoints, vec3_t clipPoints[2][MAX_VERTS_ON_POLY],
 				   int numPlanes, vec3_t *normals, float *dists,
 				   int maxPoints, vec3_t pointBuffer,
 				   int maxFragments, markFragment_t *fragmentBuffer,
@@ -231,12 +220,12 @@
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
@@ -258,19 +247,6 @@
 
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
@@ -298,7 +274,6 @@
 	vec3_t			normal;
 	vec3_t			projectionDir;
 	vec3_t			v1, v2;
-	qboolean fragmentAdded;
 
 	if (numPoints <= 0) {
 		return 0;
@@ -397,14 +372,12 @@
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
+
 						if ( returnedFragments == maxFragments ) {
 							return returnedFragments;	// not enough space for more fragments
 						}
@@ -426,14 +399,12 @@
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
@@ -459,14 +430,11 @@
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
@@ -487,13 +455,10 @@
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
