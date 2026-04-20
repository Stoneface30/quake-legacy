# Diff: `code/renderergl1/tr_model_iqm.c`
**Canonical:** `wolfcamql-src` (sha256 `12ad7a1e9651...`, 49285 bytes)

## Variants

### `ioquake3`  — sha256 `6e2703fc9ca2...`, 49181 bytes

_Diff stat: +24 / -24 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_model_iqm.c	2026-04-16 20:02:25.246415300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_model_iqm.c	2026-04-16 20:02:21.600740300 +0100
@@ -976,8 +976,8 @@
 	}
 
 	// compute bounds pointers
-	oldBounds = data->bounds + 6*ent->ePtr->oldframe;
-	newBounds = data->bounds + 6*ent->ePtr->frame;
+	oldBounds = data->bounds + 6*ent->e.oldframe;
+	newBounds = data->bounds + 6*ent->e.frame;
 
 	// calculate a bounding box in the current coordinate system
 	for (i = 0 ; i < 3 ; i++) {
@@ -1021,13 +1021,13 @@
 
 	// FIXME: non-normalized axis issues
 	if (data->bounds) {
-		bounds = data->bounds + 6*ent->ePtr->frame;
+		bounds = data->bounds + 6*ent->e.frame;
 	} else {
 		bounds = defaultBounds;
 	}
 	VectorSubtract( bounds+3, bounds, diag );
 	VectorMA( bounds, 0.5f, diag, center );
-	VectorAdd( ent->ePtr->origin, center, localOrigin );
+	VectorAdd( ent->e.origin, center, localOrigin );
 	radius = 0.5f * VectorLength( diag );
 
 	for ( i = 1 ; i < tr.world->numfogs ; i++ ) {
@@ -1069,11 +1069,11 @@
 	surface = data->surfaces;
 
 	// don't add third_person objects if not in a portal
-	personalModel = (ent->ePtr->renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
+	personalModel = (ent->e.renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
 
-	if ( ent->ePtr->renderfx & RF_WRAP_FRAMES ) {
-		ent->ePtr->frame %= data->num_frames;
-		ent->ePtr->oldframe %= data->num_frames;
+	if ( ent->e.renderfx & RF_WRAP_FRAMES ) {
+		ent->e.frame %= data->num_frames;
+		ent->e.oldframe %= data->num_frames;
 	}
 
 	//
@@ -1082,15 +1082,15 @@
 	// when the surfaces are rendered, they don't need to be
 	// range checked again.
 	//
-	if ( (ent->ePtr->frame >= data->num_frames) 
-	     || (ent->ePtr->frame < 0)
-	     || (ent->ePtr->oldframe >= data->num_frames)
-	     || (ent->ePtr->oldframe < 0) ) {
+	if ( (ent->e.frame >= data->num_frames) 
+	     || (ent->e.frame < 0)
+	     || (ent->e.oldframe >= data->num_frames)
+	     || (ent->e.oldframe < 0) ) {
 		ri.Printf( PRINT_DEVELOPER, "R_AddIQMSurfaces: no such frame %d to %d for '%s'\n",
-			   ent->ePtr->oldframe, ent->ePtr->frame,
+			   ent->e.oldframe, ent->e.frame,
 			   tr.currentModel->name );
-		ent->ePtr->frame = 0;
-		ent->ePtr->oldframe = 0;
+		ent->e.frame = 0;
+		ent->e.oldframe = 0;
 	}
 
 	//
@@ -1115,11 +1115,11 @@
 	fogNum = R_ComputeIQMFogNum( data, ent );
 
 	for ( i = 0 ; i < data->num_surfaces ; i++ ) {
-		if(ent->ePtr->customShader)
-			shader = R_GetShaderByHandle( ent->ePtr->customShader );
-		else if(ent->ePtr->customSkin > 0 && ent->ePtr->customSkin < tr.numSkins)
+		if(ent->e.customShader)
+			shader = R_GetShaderByHandle( ent->e.customShader );
+		else if(ent->e.customSkin > 0 && ent->e.customSkin < tr.numSkins)
 		{
-			skin = R_GetSkinByHandle(ent->ePtr->customSkin);
+			skin = R_GetSkinByHandle(ent->e.customSkin);
 			shader = tr.defaultShader;
 
 			for(j = 0; j < skin->numSurfaces; j++)
@@ -1140,7 +1140,7 @@
 		if ( !personalModel
 			&& r_shadows->integer == 2 
 			&& fogNum == 0
-			&& !(ent->ePtr->renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) ) 
+			&& !(ent->e.renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) ) 
 			&& shader->sort == SS_OPAQUE ) {
 			R_AddDrawSurf( (void *)surface, tr.shadowShader, 0, 0 );
 		}
@@ -1148,7 +1148,7 @@
 		// projection shadows work fine with personal models
 		if ( r_shadows->integer == 3
 			&& fogNum == 0
-			&& (ent->ePtr->renderfx & RF_SHADOW_PLANE )
+			&& (ent->e.renderfx & RF_SHADOW_PLANE )
 			&& shader->sort == SS_OPAQUE ) {
 			R_AddDrawSurf( (void *)surface, tr.projectionShadowShader, 0, 0 );
 		}
@@ -1267,9 +1267,9 @@
 	vec2_t		(*outTexCoord)[2];
 	color4ub_t	*outColor;
 
-	int	frame = data->num_frames ? backEnd.currentEntity->ePtr->frame % data->num_frames : 0;
-	int	oldframe = data->num_frames ? backEnd.currentEntity->ePtr->oldframe % data->num_frames : 0;
-	float	backlerp = backEnd.currentEntity->ePtr->backlerp;
+	int	frame = data->num_frames ? backEnd.currentEntity->e.frame % data->num_frames : 0;
+	int	oldframe = data->num_frames ? backEnd.currentEntity->e.oldframe % data->num_frames : 0;
+	float	backlerp = backEnd.currentEntity->e.backlerp;
 
 	int		*tri;
 	glIndex_t	*ptr;

```
