# Diff: `code/renderergl1/tr_shade_calc.c`
**Canonical:** `wolfcamql-src` (sha256 `29959968828f...`, 27952 bytes)

## Variants

### `ioquake3`  — sha256 `b365d177397c...`, 27612 bytes

_Diff stat: +16 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_shade_calc.c	2026-04-16 20:02:25.246936200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_shade_calc.c	2026-04-16 20:02:21.601742100 +0100
@@ -24,7 +24,7 @@
 #include "tr_local.h"
 
 
-#define        WAVEVALUE( table, base, amplitude, phase, freq )  ((base) + table[ ( (int64_t) ( ( (phase) + tess.shaderTime * (freq) ) * FUNCTABLE_SIZE ) ) & FUNCTABLE_MASK ] * (amplitude))
+#define	WAVEVALUE( table, base, amplitude, phase, freq )  ((base) + table[ ( (int64_t) ( ( (phase) + tess.shaderTime * (freq) ) * FUNCTABLE_SIZE ) ) & FUNCTABLE_MASK ] * (amplitude))
 
 static float *TableForFunc( genFunc_t func ) 
 {
@@ -208,7 +208,7 @@
 	now = backEnd.refdef.time * 0.001 * ds->bulgeSpeed;
 
 	for ( i = 0; i < tess.numVertexes; i++, xyz += 4, st += 4, normal += 4 ) {
-		int64_t	off;
+		int64_t off;
 		float scale;
 
 		off = (float)( FUNCTABLE_SIZE / (M_PI*2) ) * ( st[0] * ds->bulgeWidth + now );
@@ -355,15 +355,11 @@
 	vec3_t	left, up;
 	vec3_t	leftDir, upDir;
 
-	//ri.Printf(PRINT_ALL, "^5autosprite '%s'  %d  %d  %f %f %f\n", tess.shader->name, tess.numVertexes, tess.numIndexes, tess.xyz[0][0], tess.xyz[0][1], tess.xyz[0][2]);
-	//ri.Printf(PRINT_ALL, "^5autosprite '%s'\n", tess.shader->name);
-
 	if ( tess.numVertexes & 3 ) {
-		ri.Printf( PRINT_WARNING, "Autosprite shader %s had odd vertex count %d\n", tess.shader->name, tess.numVertexes );
-		//return;
+		ri.Printf( PRINT_WARNING, "Autosprite shader %s had odd vertex count\n", tess.shader->name );
 	}
 	if ( tess.numIndexes != ( tess.numVertexes >> 2 ) * 6 ) {
-		ri.Printf( PRINT_WARNING, "Autosprite shader %s had odd index count %d\n", tess.shader->name, tess.numIndexes );
+		ri.Printf( PRINT_WARNING, "Autosprite shader %s had odd index count\n", tess.shader->name );
 	}
 
 	oldVerts = tess.numVertexes;
@@ -397,9 +393,9 @@
 		}
 
 	  // compensate for scale in the axes if necessary
-  	if ( backEnd.currentEntity->ePtr->nonNormalizedAxes ) {
+  	if ( backEnd.currentEntity->e.nonNormalizedAxes ) {
       float axisLength;
-		  axisLength = VectorLength( backEnd.currentEntity->ePtr->axis[0] );
+		  axisLength = VectorLength( backEnd.currentEntity->e.axis[0] );
   		if ( !axisLength ) {
 	  		axisLength = 0;
   		} else {
@@ -437,10 +433,10 @@
 	vec3_t	forward;
 
 	if ( tess.numVertexes & 3 ) {
-		ri.Printf( PRINT_WARNING, "Autosprite2 shader %s had odd vertex count\n", tess.shader->name );
+		ri.Printf( PRINT_WARNING, "Autosprite2 shader %s had odd vertex count", tess.shader->name );
 	}
 	if ( tess.numIndexes != ( tess.numVertexes >> 2 ) * 6 ) {
-		ri.Printf( PRINT_WARNING, "Autosprite2 shader %s had odd index count\n", tess.shader->name );
+		ri.Printf( PRINT_WARNING, "Autosprite2 shader %s had odd index count", tess.shader->name );
 	}
 
 	if ( backEnd.currentEntity != &tr.worldEntity ) {
@@ -605,7 +601,7 @@
 	if ( !backEnd.currentEntity )
 		return;
 
-	c = * ( int * ) backEnd.currentEntity->ePtr->shaderRGBA;
+	c = * ( int * ) backEnd.currentEntity->e.shaderRGBA;
 
 	for ( i = 0; i < tess.numVertexes; i++, pColors++ )
 	{
@@ -626,10 +622,10 @@
 	if ( !backEnd.currentEntity )
 		return;
 
-	invModulate[0] = 255 - backEnd.currentEntity->ePtr->shaderRGBA[0];
-	invModulate[1] = 255 - backEnd.currentEntity->ePtr->shaderRGBA[1];
-	invModulate[2] = 255 - backEnd.currentEntity->ePtr->shaderRGBA[2];
-	invModulate[3] = 255 - backEnd.currentEntity->ePtr->shaderRGBA[3];	// this trashes alpha, but the AGEN block fixes it
+	invModulate[0] = 255 - backEnd.currentEntity->e.shaderRGBA[0];
+	invModulate[1] = 255 - backEnd.currentEntity->e.shaderRGBA[1];
+	invModulate[2] = 255 - backEnd.currentEntity->e.shaderRGBA[2];
+	invModulate[3] = 255 - backEnd.currentEntity->e.shaderRGBA[3];	// this trashes alpha, but the AGEN block fixes it
 
 	c = * ( int * ) invModulate;
 
@@ -653,7 +649,7 @@
 
 	for ( i = 0; i < tess.numVertexes; i++, dstColors += 4 )
 	{
-		*dstColors = backEnd.currentEntity->ePtr->shaderRGBA[3];
+		*dstColors = backEnd.currentEntity->e.shaderRGBA[3];
 	}
 }
 
@@ -671,7 +667,7 @@
 
 	for ( i = 0; i < tess.numVertexes; i++, dstColors += 4 )
 	{
-		*dstColors = 0xff - backEnd.currentEntity->ePtr->shaderRGBA[3];
+		*dstColors = 0xff - backEnd.currentEntity->e.shaderRGBA[3];
 	}
 }
 
@@ -1018,6 +1014,7 @@
 	RB_CalcTransformTexCoords( &tmi, st );
 }
 
+
 /*
 ** RB_CalcSpecularAlpha
 **
@@ -1082,7 +1079,6 @@
 **
 ** The basic vertex lighting calc
 */
-
 static void RB_CalcDiffuseColor_scalar( unsigned char *colors )
 {
 	int				i, j;

```
