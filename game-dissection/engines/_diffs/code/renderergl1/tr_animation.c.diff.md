# Diff: `code/renderergl1/tr_animation.c`
**Canonical:** `wolfcamql-src` (sha256 `724f530cb408...`, 15068 bytes)

## Variants

### `ioquake3`  — sha256 `90732c8f826d...`, 14944 bytes

_Diff stat: +27 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_animation.c	2026-04-16 20:02:25.239343200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_animation.c	2026-04-16 20:02:21.578616700 +0100
@@ -50,13 +50,13 @@
 	frameSize = (size_t)( &((mdrFrame_t *)0)->bones[ header->numBones ] );
 	
 	// compute frame pointers
-	newFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->ePtr->frame);
-	oldFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->ePtr->oldframe);
+	newFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->e.frame);
+	oldFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->e.oldframe);
 
 	// cull bounding sphere ONLY if this is not an upscaled entity
-	if ( !ent->ePtr->nonNormalizedAxes )
+	if ( !ent->e.nonNormalizedAxes )
 	{
-		if ( ent->ePtr->frame == ent->ePtr->oldframe )
+		if ( ent->e.frame == ent->e.oldframe )
 		{
 			switch ( R_CullLocalPointAndRadius( newFrame->localOrigin, newFrame->radius ) )
 			{
@@ -149,8 +149,8 @@
 	frameSize = (size_t)( &((mdrFrame_t *)0)->bones[ header->numBones ] );
 
 	// FIXME: non-normalized axis issues
-	mdrFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->ePtr->frame);
-	VectorAdd( ent->ePtr->origin, mdrFrame->localOrigin, localOrigin );
+	mdrFrame = ( mdrFrame_t * ) ( ( byte * ) header + header->ofsFrames + frameSize * ent->e.frame);
+	VectorAdd( ent->e.origin, mdrFrame->localOrigin, localOrigin );
 	for ( i = 1 ; i < tr.world->numfogs ; i++ ) {
 		fog = &tr.world->fogs[i];
 		for ( j = 0 ; j < 3 ; j++ ) {
@@ -192,12 +192,12 @@
 
 	header = (mdrHeader_t *) tr.currentModel->modelData;
 	
-	personalModel = (ent->ePtr->renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
+	personalModel = (ent->e.renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
 	
-	if ( ent->ePtr->renderfx & RF_WRAP_FRAMES )
+	if ( ent->e.renderfx & RF_WRAP_FRAMES )
 	{
-		ent->ePtr->frame %= header->numFrames;
-		ent->ePtr->oldframe %= header->numFrames;
+		ent->e.frame %= header->numFrames;
+		ent->e.oldframe %= header->numFrames;
 	}	
 	
 	//
@@ -206,15 +206,15 @@
 	// when the surfaces are rendered, they don't need to be
 	// range checked again.
 	//
-	if ((ent->ePtr->frame >= header->numFrames) 
-		|| (ent->ePtr->frame < 0)
-		|| (ent->ePtr->oldframe >= header->numFrames)
-		|| (ent->ePtr->oldframe < 0) )
+	if ((ent->e.frame >= header->numFrames) 
+		|| (ent->e.frame < 0)
+		|| (ent->e.oldframe >= header->numFrames)
+		|| (ent->e.oldframe < 0) )
 	{
 		ri.Printf( PRINT_DEVELOPER, "R_MDRAddAnimSurfaces: no such frame %d to %d for '%s'\n",
-			   ent->ePtr->oldframe, ent->ePtr->frame, tr.currentModel->name );
-		ent->ePtr->frame = 0;
-		ent->ePtr->oldframe = 0;
+			   ent->e.oldframe, ent->e.frame, tr.currentModel->name );
+		ent->e.frame = 0;
+		ent->e.oldframe = 0;
 	}
 
 	//
@@ -254,11 +254,11 @@
 	for ( i = 0 ; i < lod->numSurfaces ; i++ )
 	{
 		
-		if(ent->ePtr->customShader)
-			shader = R_GetShaderByHandle(ent->ePtr->customShader);
-		else if(ent->ePtr->customSkin > 0 && ent->ePtr->customSkin < tr.numSkins)
+		if(ent->e.customShader)
+			shader = R_GetShaderByHandle(ent->e.customShader);
+		else if(ent->e.customSkin > 0 && ent->e.customSkin < tr.numSkins)
 		{
-			skin = R_GetSkinByHandle(ent->ePtr->customSkin);
+			skin = R_GetSkinByHandle(ent->e.customSkin);
 			shader = tr.defaultShader;
 			
 			for(j = 0; j < skin->numSurfaces; j++)
@@ -281,7 +281,7 @@
 		if ( !personalModel
 		        && r_shadows->integer == 2
 			&& fogNum == 0
-			&& !(ent->ePtr->renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) )
+			&& !(ent->e.renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) )
 			&& shader->sort == SS_OPAQUE )
 		{
 			R_AddDrawSurf( (void *)surface, tr.shadowShader, 0, qfalse );
@@ -290,7 +290,7 @@
 		// projection shadows work fine with personal models
 		if ( r_shadows->integer == 3
 			&& fogNum == 0
-			&& (ent->ePtr->renderfx & RF_SHADOW_PLANE )
+			&& (ent->e.renderfx & RF_SHADOW_PLANE )
 			&& shader->sort == SS_OPAQUE )
 		{
 			R_AddDrawSurf( (void *)surface, tr.projectionShadowShader, 0, qfalse );
@@ -326,14 +326,14 @@
 
 	// don't lerp if lerping off, or this is the only frame, or the last frame...
 	//
-	if (backEnd.currentEntity->ePtr->oldframe == backEnd.currentEntity->ePtr->frame) 
+	if (backEnd.currentEntity->e.oldframe == backEnd.currentEntity->e.frame) 
 	{
 		backlerp	= 0;	// if backlerp is 0, lerping is off and frontlerp is never used
 		frontlerp	= 1;
 	} 
 	else  
 	{
-		backlerp	= backEnd.currentEntity->ePtr->backlerp;
+		backlerp	= backEnd.currentEntity->e.backlerp;
 		frontlerp	= 1.0f - backlerp;
 	}
 
@@ -342,9 +342,9 @@
 	frameSize = (size_t)( &((mdrFrame_t *)0)->bones[ header->numBones ] );
 
 	frame = (mdrFrame_t *)((byte *)header + header->ofsFrames +
-		backEnd.currentEntity->ePtr->frame * frameSize );
+		backEnd.currentEntity->e.frame * frameSize );
 	oldFrame = (mdrFrame_t *)((byte *)header + header->ofsFrames +
-		backEnd.currentEntity->ePtr->oldframe * frameSize );
+		backEnd.currentEntity->e.oldframe * frameSize );
 
 	RB_CHECKOVERFLOW( surface->numVerts, surface->numTriangles * 3 );
 

```
