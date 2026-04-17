# Diff: `code/renderergl1/tr_sky.c`
**Canonical:** `wolfcamql-src` (sha256 `0e0b862ddf21...`, 23637 bytes)

## Variants

### `ioquake3`  — sha256 `852a58cf85b1...`, 20366 bytes

_Diff stat: +25 / -118 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_sky.c	2026-04-16 20:02:25.248499000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_sky.c	2026-04-16 20:02:21.602743800 +0100
@@ -399,8 +399,8 @@
 static void DrawSkyBox( shader_t *shader )
 {
 	int		i;
-	float   w_offset, w_scale;
-	float   h_offset, h_scale;
+	float	w_offset, w_scale;
+	float	h_offset, h_scale;
 
 	sky_min = 0;
 	sky_max = 1;
@@ -431,31 +431,31 @@
 		sky_maxs_subd[0] = sky_maxs[0][i] * HALF_SKY_SUBDIVISIONS;
 		sky_maxs_subd[1] = sky_maxs[1][i] * HALF_SKY_SUBDIVISIONS;
 
-		if ( sky_mins_subd[0] < -HALF_SKY_SUBDIVISIONS )
+		if ( sky_mins_subd[0] < -HALF_SKY_SUBDIVISIONS ) 
 			sky_mins_subd[0] = -HALF_SKY_SUBDIVISIONS;
-		else if ( sky_mins_subd[0] > HALF_SKY_SUBDIVISIONS )
+		else if ( sky_mins_subd[0] > HALF_SKY_SUBDIVISIONS ) 
 			sky_mins_subd[0] = HALF_SKY_SUBDIVISIONS;
 		if ( sky_mins_subd[1] < -HALF_SKY_SUBDIVISIONS )
 			sky_mins_subd[1] = -HALF_SKY_SUBDIVISIONS;
-		else if ( sky_mins_subd[1] > HALF_SKY_SUBDIVISIONS )
+		else if ( sky_mins_subd[1] > HALF_SKY_SUBDIVISIONS ) 
 			sky_mins_subd[1] = HALF_SKY_SUBDIVISIONS;
 
-		if ( sky_maxs_subd[0] < -HALF_SKY_SUBDIVISIONS )
+		if ( sky_maxs_subd[0] < -HALF_SKY_SUBDIVISIONS ) 
 			sky_maxs_subd[0] = -HALF_SKY_SUBDIVISIONS;
-		else if ( sky_maxs_subd[0] > HALF_SKY_SUBDIVISIONS )
+		else if ( sky_maxs_subd[0] > HALF_SKY_SUBDIVISIONS ) 
 			sky_maxs_subd[0] = HALF_SKY_SUBDIVISIONS;
-		if ( sky_maxs_subd[1] < -HALF_SKY_SUBDIVISIONS )
+		if ( sky_maxs_subd[1] < -HALF_SKY_SUBDIVISIONS ) 
 			sky_maxs_subd[1] = -HALF_SKY_SUBDIVISIONS;
-		else if ( sky_maxs_subd[1] > HALF_SKY_SUBDIVISIONS )
+		else if ( sky_maxs_subd[1] > HALF_SKY_SUBDIVISIONS ) 
 			sky_maxs_subd[1] = HALF_SKY_SUBDIVISIONS;
 
 		if ( !haveClampToEdge )
 		{
-				w_offset = 0.5f / shader->sky.outerbox[sky_texorder[i]]->width;
-				h_offset = 0.5f / shader->sky.outerbox[sky_texorder[i]]->height;
+			w_offset = 0.5f / shader->sky.outerbox[sky_texorder[i]]->width;
+			h_offset = 0.5f / shader->sky.outerbox[sky_texorder[i]]->height;
 
-				w_scale = 1.0f - w_offset * 2;
-				h_scale = 1.0f - h_offset * 2;
+			w_scale = 1.0f - w_offset * 2;
+			h_scale = 1.0f - h_offset * 2;
 		}
 
 		//
@@ -465,10 +465,10 @@
 		{
 			for ( s = sky_mins_subd[0]+HALF_SKY_SUBDIVISIONS; s <= sky_maxs_subd[0]+HALF_SKY_SUBDIVISIONS; s++ )
 			{
-				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS,
-							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS,
-							i,
-							s_skyTexCoords[t][s],
+				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
+							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
+							i, 
+							s_skyTexCoords[t][s], 
 							s_skyPoints[t][s] );
 
 				s_skyTexCoords[t][s][0] *= w_scale;
@@ -495,8 +495,6 @@
 	tHeight = maxs[1] - mins[1] + 1;
 	sWidth = maxs[0] - mins[0] + 1;
 
-	//ri.Printf(PRINT_ALL, "^3%d -> %d   %d -> %d\n", mins[1], maxs[1], mins[0], maxs[0]);
-
 	for ( t = mins[1]+HALF_SKY_SUBDIVISIONS; t <= maxs[1]+HALF_SKY_SUBDIVISIONS; t++ )
 	{
 		for ( s = mins[0]+HALF_SKY_SUBDIVISIONS; s <= maxs[0]+HALF_SKY_SUBDIVISIONS; s++ )
@@ -553,9 +551,8 @@
 			MIN_T = -HALF_SKY_SUBDIVISIONS;
 
 			// still don't want to draw the bottom, even if fullClouds
-			if ( i == 5   &&  !r_drawSkyFloor->integer) {
+			if ( i == 5 )
 				continue;
-			}
 		}
 		else
 		{
@@ -585,7 +582,6 @@
 		if ( ( sky_mins[0][i] >= sky_maxs[0][i] ) ||
 			 ( sky_mins[1][i] >= sky_maxs[1][i] ) )
 		{
-			//ri.Printf(PRINT_ALL, "nope %d\n", i);
 			continue;
 		}
 
@@ -609,10 +605,9 @@
 			sky_maxs_subd[0] = HALF_SKY_SUBDIVISIONS;
 		if ( sky_maxs_subd[1] < MIN_T )
 			sky_maxs_subd[1] = MIN_T;
-		else if ( sky_maxs_subd[1] > HALF_SKY_SUBDIVISIONS )
+		else if ( sky_maxs_subd[1] > HALF_SKY_SUBDIVISIONS ) 
 			sky_maxs_subd[1] = HALF_SKY_SUBDIVISIONS;
 
-		//ri.Printf(PRINT_ALL, "%d -> %d   %d -> %d\n", sky_mins_subd[1], sky_maxs_subd[1], sky_mins_subd[0], sky_maxs_subd[0]);
 		//
 		// iterate through the subdivisions
 		//
@@ -620,9 +615,9 @@
 		{
 			for ( s = sky_mins_subd[0]+HALF_SKY_SUBDIVISIONS; s <= sky_maxs_subd[0]+HALF_SKY_SUBDIVISIONS; s++ )
 			{
-				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS,
-							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS,
-							i,
+				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
+							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
+							i, 
 							NULL,
 							s_skyPoints[t][s] );
 
@@ -655,8 +650,6 @@
 	tess.numIndexes = 0;
 	tess.numVertexes = 0;
 
-	//ri.Printf(PRINT_ALL, "^1cloudHeight %f\n", input->shader->sky.cloudHeight);
-
 	if ( shader->sky.cloudHeight )
 	{
 		for ( i = 0; i < MAX_SHADER_STAGES; i++ )
@@ -664,7 +657,6 @@
 			if ( !tess.xstages[i] ) {
 				break;
 			}
-			//ri.Printf(PRINT_ALL, "fill cloud box %d\n", i);
 			FillCloudBox( shader, i );
 		}
 	}
@@ -684,10 +676,6 @@
 	vec3_t skyVec;
 	vec3_t v;
 
-	if (*r_cloudHeight->string) {
-		heightCloud = r_cloudHeight->value;
-	}
-
 	// init zfar so MakeSkyVec works even though
 	// a world hasn't been bounded
 	backEnd.viewParms.zFar = 1024;
@@ -744,8 +732,7 @@
 	float		size;
 	float		dist;
 	vec3_t		origin, vec1, vec2;
-	//vec3_t		temp;
-	byte sunColor[4] = { 255, 255, 255, 255 };
+	byte		sunColor[4] = { 255, 255, 255, 255 };
 
 	if ( !backEnd.skyRenderedThisView ) {
 		return;
@@ -755,7 +742,6 @@
 	qglTranslatef (backEnd.viewParms.or.origin[0], backEnd.viewParms.or.origin[1], backEnd.viewParms.or.origin[2]);
 
 	dist = 	backEnd.viewParms.zFar / 1.75;		// div sqrt(3)
-	//size = dist * 0.4;
 	size = dist * scale;
 
 	VectorScale( tr.sunDirection, dist, origin );
@@ -768,61 +754,6 @@
 	// farthest depth range
 	qglDepthRange( 1.0, 1.0 );
 
-#if 0  // ioquake3 takes out
-	// FIXME: use quad stamp
-	RB_BeginSurface( tr.sunShader, tess.fogNum );
-		VectorCopy( origin, temp );
-		VectorSubtract( temp, vec1, temp );
-		VectorSubtract( temp, vec2, temp );
-		VectorCopy( temp, tess.xyz[tess.numVertexes] );
-		tess.texCoords[tess.numVertexes][0][0] = 0;
-		tess.texCoords[tess.numVertexes][0][1] = 0;
-		tess.vertexColors[tess.numVertexes][0] = 255;
-		tess.vertexColors[tess.numVertexes][1] = 255;
-		tess.vertexColors[tess.numVertexes][2] = 255;
-		tess.numVertexes++;
-
-		VectorCopy( origin, temp );
-		VectorAdd( temp, vec1, temp );
-		VectorSubtract( temp, vec2, temp );
-		VectorCopy( temp, tess.xyz[tess.numVertexes] );
-		tess.texCoords[tess.numVertexes][0][0] = 0;
-		tess.texCoords[tess.numVertexes][0][1] = 1;
-		tess.vertexColors[tess.numVertexes][0] = 255;
-		tess.vertexColors[tess.numVertexes][1] = 255;
-		tess.vertexColors[tess.numVertexes][2] = 255;
-		tess.numVertexes++;
-
-		VectorCopy( origin, temp );
-		VectorAdd( temp, vec1, temp );
-		VectorAdd( temp, vec2, temp );
-		VectorCopy( temp, tess.xyz[tess.numVertexes] );
-		tess.texCoords[tess.numVertexes][0][0] = 1;
-		tess.texCoords[tess.numVertexes][0][1] = 1;
-		tess.vertexColors[tess.numVertexes][0] = 255;
-		tess.vertexColors[tess.numVertexes][1] = 255;
-		tess.vertexColors[tess.numVertexes][2] = 255;
-		tess.numVertexes++;
-
-		VectorCopy( origin, temp );
-		VectorSubtract( temp, vec1, temp );
-		VectorAdd( temp, vec2, temp );
-		VectorCopy( temp, tess.xyz[tess.numVertexes] );
-		tess.texCoords[tess.numVertexes][0][0] = 1;
-		tess.texCoords[tess.numVertexes][0][1] = 0;
-		tess.vertexColors[tess.numVertexes][0] = 255;
-		tess.vertexColors[tess.numVertexes][1] = 255;
-		tess.vertexColors[tess.numVertexes][2] = 255;
-		tess.numVertexes++;
-
-		tess.indexes[tess.numIndexes++] = 0;
-		tess.indexes[tess.numIndexes++] = 1;
-		tess.indexes[tess.numIndexes++] = 2;
-		tess.indexes[tess.numIndexes++] = 0;
-		tess.indexes[tess.numIndexes++] = 2;
-		tess.indexes[tess.numIndexes++] = 3;
-#endif
-
 	RB_BeginSurface( shader, 0 );
 
 	RB_AddQuadStamp(origin, vec1, vec2, sunColor);
@@ -846,27 +777,7 @@
 ================
 */
 void RB_StageIteratorSky( void ) {
-	int clearBits = 0;
-
 	if ( r_fastsky->integer ) {
-		if (r_fastsky->integer == 2  &&  !(backEnd.refdef.rdflags & RDF_NOWORLDMODEL)) {
-			clearBits |= GL_COLOR_BUFFER_BIT;	// FIXME: only if sky shaders have been used
-			if (*r_fastSkyColor->string) {
-				int v, sr, sg, sb;
-
-				v = r_fastSkyColor->integer;
-				sr = (v & 0xff0000) / 0x010000;
-				sg = (v & 0x00ff00) / 0x000100;
-				sb = (v & 0x0000ff) / 0x000001;
-
-				qglClearColor((float)sr / 255.0, (float)sg / 255.0, (float)sb / 255.0, 1.0);
-			} else {
-				qglClearColor(0.0f, 0.0f, 0.0f, 1.0f);	// FIXME: get color of sky
-			}
-
-			qglClear(clearBits);
-		}
-
 		return;
 	}
 
@@ -887,7 +798,7 @@
 	// draw the outer skybox
 	if ( tess.shader->sky.outerbox[0] && tess.shader->sky.outerbox[0] != tr.defaultImage ) {
 		qglColor3f( tr.identityLight, tr.identityLight, tr.identityLight );
-
+		
 		qglPushMatrix ();
 		GL_State( 0 );
 		GL_Cull( CT_FRONT_SIDED );
@@ -902,14 +813,10 @@
 	// by the generic shader routine
 	R_BuildCloudData( &tess );
 
-	if (tess.numVertexes) {
-		// yes, sky has cloud stages
-		RB_StageIteratorGeneric();
-	}
+	RB_StageIteratorGeneric();
 
 	// draw the inner skybox
 
-	//FIXME not even done
 
 	// back to normal depth range
 	qglDepthRange( 0.0, 1.0 );

```
