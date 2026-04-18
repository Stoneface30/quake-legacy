# Diff: `code/renderergl1/tr_mesh.c`
**Canonical:** `wolfcamql-src` (sha256 `86d44037e438...`, 11168 bytes)

## Variants

### `ioquake3`  — sha256 `870aa1c26803...`, 11049 bytes

_Diff stat: +28 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_mesh.c	2026-04-16 20:02:25.245359600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_mesh.c	2026-04-16 20:02:21.599744000 +0100
@@ -81,13 +81,13 @@
 	int			i;
 
 	// compute frame pointers
-	newFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->ePtr->frame;
-	oldFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->ePtr->oldframe;
+	newFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->e.frame;
+	oldFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->e.oldframe;
 
 	// cull bounding sphere ONLY if this is not an upscaled entity
-	if ( !ent->ePtr->nonNormalizedAxes )
+	if ( !ent->e.nonNormalizedAxes )
 	{
-		if ( ent->ePtr->frame == ent->ePtr->oldframe )
+		if ( ent->e.frame == ent->e.oldframe )
 		{
 			switch ( R_CullLocalPointAndRadius( newFrame->localOrigin, newFrame->radius ) )
 			{
@@ -188,7 +188,7 @@
 			mdr = (mdrHeader_t *) tr.currentModel->modelData;
 			frameSize = (size_t) (&((mdrFrame_t *)0)->bones[mdr->numBones]);
 			
-			mdrframe = (mdrFrame_t *) ((byte *) mdr + mdr->ofsFrames + frameSize * ent->ePtr->frame);
+			mdrframe = (mdrFrame_t *) ((byte *) mdr + mdr->ofsFrames + frameSize * ent->e.frame);
 			
 			radius = RadiusFromBounds(mdrframe->bounds[0], mdrframe->bounds[1]);
 		}
@@ -196,12 +196,12 @@
 		{
 			frame = ( md3Frame_t * ) ( ( ( unsigned char * ) tr.currentModel->md3[0] ) + tr.currentModel->md3[0]->ofsFrames );
 
-			frame += ent->ePtr->frame;
+			frame += ent->e.frame;
 
 			radius = RadiusFromBounds( frame->bounds[0], frame->bounds[1] );
 		}
 
-		if ( ( projectedRadius = ProjectRadius( radius, ent->ePtr->origin ) ) != 0 )
+		if ( ( projectedRadius = ProjectRadius( radius, ent->e.origin ) ) != 0 )
 		{
 			lodscale = r_lodscale->value;
 			if (lodscale > 20) lodscale = 20;
@@ -227,7 +227,7 @@
 	}
 
 	lod += r_lodbias->integer;
-
+	
 	if ( lod >= tr.currentModel->numLods )
 		lod = tr.currentModel->numLods - 1;
 	if ( lod < 0 )
@@ -253,8 +253,8 @@
 	}
 
 	// FIXME: non-normalized axis issues
-	md3Frame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->ePtr->frame;
-	VectorAdd( ent->ePtr->origin, md3Frame->localOrigin, localOrigin );
+	md3Frame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->e.frame;
+	VectorAdd( ent->e.origin, md3Frame->localOrigin, localOrigin );
 	for ( i = 1 ; i < tr.world->numfogs ; i++ ) {
 		fog = &tr.world->fogs[i];
 		for ( j = 0 ; j < 3 ; j++ ) {
@@ -291,11 +291,11 @@
 	qboolean		personalModel;
 
 	// don't add third_person objects if not in a portal
-	personalModel = (ent->ePtr->renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
+	personalModel = (ent->e.renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
 
-	if ( ent->ePtr->renderfx & RF_WRAP_FRAMES ) {
-		ent->ePtr->frame %= tr.currentModel->md3[0]->numFrames;
-		ent->ePtr->oldframe %= tr.currentModel->md3[0]->numFrames;
+	if ( ent->e.renderfx & RF_WRAP_FRAMES ) {
+		ent->e.frame %= tr.currentModel->md3[0]->numFrames;
+		ent->e.oldframe %= tr.currentModel->md3[0]->numFrames;
 	}
 
 	//
@@ -304,15 +304,15 @@
 	// when the surfaces are rendered, they don't need to be
 	// range checked again.
 	//
-	if ( (ent->ePtr->frame >= tr.currentModel->md3[0]->numFrames) 
-		|| (ent->ePtr->frame < 0)
-		|| (ent->ePtr->oldframe >= tr.currentModel->md3[0]->numFrames)
-		|| (ent->ePtr->oldframe < 0) ) {
+	if ( (ent->e.frame >= tr.currentModel->md3[0]->numFrames) 
+		|| (ent->e.frame < 0)
+		|| (ent->e.oldframe >= tr.currentModel->md3[0]->numFrames)
+		|| (ent->e.oldframe < 0) ) {
 			ri.Printf( PRINT_DEVELOPER, "R_AddMD3Surfaces: no such frame %d to %d for '%s'\n",
-				ent->ePtr->oldframe, ent->ePtr->frame,
+				ent->e.oldframe, ent->e.frame,
 				tr.currentModel->name );
-			ent->ePtr->frame = 0;
-			ent->ePtr->oldframe = 0;
+			ent->e.frame = 0;
+			ent->e.oldframe = 0;
 	}
 
 	//
@@ -349,13 +349,13 @@
 	surface = (md3Surface_t *)( (byte *)header + header->ofsSurfaces );
 	for ( i = 0 ; i < header->numSurfaces ; i++ ) {
 
-		if ( ent->ePtr->customShader ) {
-			shader = R_GetShaderByHandle( ent->ePtr->customShader );
-		} else if ( ent->ePtr->customSkin > 0 && ent->ePtr->customSkin < tr.numSkins ) {
+		if ( ent->e.customShader ) {
+			shader = R_GetShaderByHandle( ent->e.customShader );
+		} else if ( ent->e.customSkin > 0 && ent->e.customSkin < tr.numSkins ) {
 			skin_t *skin;
 			int		j;
 
-			skin = R_GetSkinByHandle( ent->ePtr->customSkin );
+			skin = R_GetSkinByHandle( ent->e.customSkin );
 
 			// match the surface name to something in the skin file
 			shader = tr.defaultShader;
@@ -376,7 +376,7 @@
 			shader = tr.defaultShader;
 		} else {
 			md3Shader = (md3Shader_t *) ( (byte *)surface + surface->ofsShaders );
-			md3Shader += ent->ePtr->skinNum % surface->numShaders;
+			md3Shader += ent->e.skinNum % surface->numShaders;
 			shader = tr.shaders[ md3Shader->shaderIndex ];
 		}
 
@@ -387,7 +387,7 @@
 		if ( !personalModel
 			&& r_shadows->integer == 2 
 			&& fogNum == 0
-			&& !(ent->ePtr->renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) ) 
+			&& !(ent->e.renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) ) 
 			&& shader->sort == SS_OPAQUE ) {
 			R_AddDrawSurf( (void *)surface, tr.shadowShader, 0, qfalse );
 		}
@@ -395,7 +395,7 @@
 		// projection shadows work fine with personal models
 		if ( r_shadows->integer == 3
 			&& fogNum == 0
-			&& (ent->ePtr->renderfx & RF_SHADOW_PLANE )
+			&& (ent->e.renderfx & RF_SHADOW_PLANE )
 			&& shader->sort == SS_OPAQUE ) {
 			R_AddDrawSurf( (void *)surface, tr.projectionShadowShader, 0, qfalse );
 		}

```
