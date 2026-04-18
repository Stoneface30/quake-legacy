# Diff: `code/renderergl1/tr_shadows.c`
**Canonical:** `wolfcamql-src` (sha256 `c0217caa0a7f...`, 8052 bytes)

## Variants

### `ioquake3`  — sha256 `88f09cfbb734...`, 7671 bytes

_Diff stat: +2 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_shadows.c	2026-04-16 20:02:25.247977400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_shadows.c	2026-04-16 20:02:21.602743800 +0100
@@ -44,7 +44,7 @@
 static	edgeDef_t	edgeDefs[SHADER_MAX_VERTEXES][MAX_EDGE_DEFS];
 static	int			numEdgeDefs[SHADER_MAX_VERTEXES];
 static	int			facing[SHADER_MAX_INDEXES/3];
-static	vec3_t	shadowXyz[SHADER_MAX_VERTEXES];
+static	vec3_t		shadowXyz[SHADER_MAX_VERTEXES];
 
 void R_AddEdgeDef( int i1, int i2, int localFacing ) {
 	int		c;
@@ -65,7 +65,6 @@
 #if 0
 	int		numTris;
 
-	//ri.Printf(PRINT_ALL, "old\n");
 	// dumb way -- render every triangle's edges
 	numTris = tess.numIndexes / 3;
 
@@ -157,10 +156,6 @@
 		return;
 	}
 
-	if (tr.usingFinalFrameBufferObject  &&  !tr.usingFboStencil) {
-		return;
-	}
-
 	VectorCopy( backEnd.currentEntity->lightDir, lightDir );
 
 	// project vertexes away from light direction
@@ -249,10 +244,6 @@
 	if ( glConfig.stencilBits < 4 ) {
 		return;
 	}
-	if (tr.usingFinalFrameBufferObject  &&  !tr.usingFboStencil) {
-		return;
-	}
-
 	qglEnable( GL_STENCIL_TEST );
 	qglStencilFunc( GL_NOTEQUAL, 0, 255 );
 
@@ -303,7 +294,7 @@
 	ground[1] = backEnd.or.axis[1][2];
 	ground[2] = backEnd.or.axis[2][2];
 
-	groundDist = backEnd.or.origin[2] - backEnd.currentEntity->ePtr->shadowPlane;
+	groundDist = backEnd.or.origin[2] - backEnd.currentEntity->e.shadowPlane;
 
 	VectorCopy( backEnd.currentEntity->lightDir, lightDir );
 	d = DotProduct( lightDir, ground );
@@ -312,15 +303,6 @@
 		VectorMA( lightDir, (0.5 - d), ground, lightDir );
 		d = DotProduct( lightDir, ground );
 	}
-
-#if 0
-	if ( d < 0.5 ) {
-		VectorMA( lightDir, (0.5 - d), ground, lightDir );
-		d = DotProduct( lightDir, ground );
-		ri.Printf(PRINT_ALL, "wtf.... %f\n", d);
-	}
-#endif
-
 	d = 1.0 / d;
 
 	light[0] = lightDir[0] * d;

```
