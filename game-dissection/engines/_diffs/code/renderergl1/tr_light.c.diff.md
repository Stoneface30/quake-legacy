# Diff: `code/renderergl1/tr_light.c`
**Canonical:** `wolfcamql-src` (sha256 `12cf49ce4b56...`, 11307 bytes)

## Variants

### `ioquake3`  — sha256 `f090586cc8ed...`, 11204 bytes

_Diff stat: +16 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_light.c	2026-04-16 20:02:25.243274600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_light.c	2026-04-16 20:02:21.598740100 +0100
@@ -26,7 +26,7 @@
 #define	DLIGHT_AT_RADIUS		16
 // at the edge of a dlight's influence, this amount of light will be added
 
-#define	DLIGHT_MINIMUM_RADIUS	16
+#define	DLIGHT_MINIMUM_RADIUS	16		
 // never calculate a range less than this to prevent huge light numbers
 
 
@@ -133,13 +133,13 @@
 	vec3_t	direction;
 	float	totalFactor;
 
-	if ( ent->ePtr->renderfx & RF_LIGHTING_ORIGIN ) {
+	if ( ent->e.renderfx & RF_LIGHTING_ORIGIN ) {
 		// separate lightOrigins are needed so an object that is
 		// sinking into the ground can still be lit, and so
 		// multi-part models can be lit identically
-		VectorCopy( ent->ePtr->lightingOrigin, lightOrigin );
+		VectorCopy( ent->e.lightingOrigin, lightOrigin );
 	} else {
-		VectorCopy( ent->ePtr->origin, lightOrigin );
+		VectorCopy( ent->e.origin, lightOrigin );
 	}
 
 	VectorSubtract( lightOrigin, tr.world->lightGridOrigin, lightOrigin );
@@ -183,7 +183,7 @@
 		for ( j = 0 ; j < 3 ; j++ ) {
 			if ( i & (1<<j) ) {
 				if ( pos[j] + 1 > tr.world->lightGridBounds[j] - 1 ) {
-					break;  // ignore values outside lightgrid
+					break; // ignore values outside lightgrid
 				}
 				factor *= frac[j];
 				data += gridStep[j];
@@ -195,7 +195,6 @@
 		if ( j != 3 ) {
 			continue;
 		}
-
 		if ( !(data[0]+data[1]+data[2]) ) {
 			continue;	// ignore samples in walls
 		}
@@ -257,7 +256,7 @@
 static void LogLight( trRefEntity_t *ent ) {
 	int	max1, max2;
 
-	if ( !(ent->ePtr->renderfx & RF_FIRST_PERSON ) ) {
+	if ( !(ent->e.renderfx & RF_FIRST_PERSON ) ) {
 		return;
 	}
 
@@ -295,7 +294,7 @@
 	vec3_t			lightDir;
 	vec3_t			lightOrigin;
 
-	// lighting calculations
+	// lighting calculations 
 	if ( ent->lightingCalculated ) {
 		return;
 	}
@@ -304,13 +303,13 @@
 	//
 	// trace a sample point down to find ambient light
 	//
-	if ( ent->ePtr->renderfx & RF_LIGHTING_ORIGIN ) {
+	if ( ent->e.renderfx & RF_LIGHTING_ORIGIN ) {
 		// separate lightOrigins are needed so an object that is
 		// sinking into the ground can still be lit, and so
 		// multi-part models can be lit identically
-		VectorCopy( ent->ePtr->lightingOrigin, lightOrigin );
+		VectorCopy( ent->e.lightingOrigin, lightOrigin );
 	} else {
-		VectorCopy( ent->ePtr->origin, lightOrigin );
+		VectorCopy( ent->e.origin, lightOrigin );
 	}
 
 	// if NOWORLDMODEL, only use dynamic lights (menu system, etc)
@@ -327,8 +326,6 @@
 
 	// bonus items and view weapons have a fixed minimum add
 	if ( 1 /* ent->e.renderfx & RF_MINLIGHT */ ) {
-	//if (ent->e.renderfx & RF_MINLIGHT) {
-	//if (0) {
 		// give everything a minimum light add
 		ent->ambientLight[0] += tr.identityLight * 32;
 		ent->ambientLight[1] += tr.identityLight * 32;
@@ -372,12 +369,12 @@
 	((byte *)&ent->ambientLightInt)[1] = ri.ftol(ent->ambientLight[1]);
 	((byte *)&ent->ambientLightInt)[2] = ri.ftol(ent->ambientLight[2]);
 	((byte *)&ent->ambientLightInt)[3] = 0xff;
-
+	
 	// transform the direction to local space
 	VectorNormalize( lightDir );
-	ent->lightDir[0] = DotProduct( lightDir, ent->ePtr->axis[0] );
-	ent->lightDir[1] = DotProduct( lightDir, ent->ePtr->axis[1] );
-	ent->lightDir[2] = DotProduct( lightDir, ent->ePtr->axis[2] );
+	ent->lightDir[0] = DotProduct( lightDir, ent->e.axis[0] );
+	ent->lightDir[1] = DotProduct( lightDir, ent->e.axis[1] );
+	ent->lightDir[2] = DotProduct( lightDir, ent->e.axis[2] );
 }
 
 /*
@@ -385,7 +382,7 @@
 R_LightForPoint
 =================
 */
-int R_LightForPoint( const vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir )
+int R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir )
 {
 	trRefEntity_t ent;
 	
@@ -393,7 +390,7 @@
 	  return qfalse;
 
 	Com_Memset(&ent, 0, sizeof(ent));
-	VectorCopy( point, ent.ePtr->origin );
+	VectorCopy( point, ent.e.origin );
 	R_SetupEntityLightingGrid( &ent );
 	VectorCopy(ent.ambientLight, ambientLight);
 	VectorCopy(ent.directedLight, directedLight);

```
