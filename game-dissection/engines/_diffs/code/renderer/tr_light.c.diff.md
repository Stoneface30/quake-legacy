# Diff: `code/renderer/tr_light.c`
**Canonical:** `quake3e` (sha256 `06cdd6692430...`, 12771 bytes)

## Variants

### `quake3-source`  — sha256 `e05df1b0a95f...`, 11140 bytes

_Diff stat: +40 / -102 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_light.c	2026-04-16 20:02:27.316570300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_light.c	2026-04-16 20:02:19.971118900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -26,7 +26,7 @@
 #define	DLIGHT_AT_RADIUS		16
 // at the edge of a dlight's influence, this amount of light will be added
 
-#define	DLIGHT_MINIMUM_RADIUS	16
+#define	DLIGHT_MINIMUM_RADIUS	16		
 // never calculate a range less than this to prevent huge light numbers
 
 
@@ -41,24 +41,16 @@
 */
 void R_TransformDlights( int count, dlight_t *dl, orientationr_t *or) {
 	int		i;
-	vec3_t	temp, temp2;
+	vec3_t	temp;
 
 	for ( i = 0 ; i < count ; i++, dl++ ) {
 		VectorSubtract( dl->origin, or->origin, temp );
 		dl->transformed[0] = DotProduct( temp, or->axis[0] );
 		dl->transformed[1] = DotProduct( temp, or->axis[1] );
 		dl->transformed[2] = DotProduct( temp, or->axis[2] );
-		if ( dl->linear ) {
-			VectorSubtract( dl->origin2, or->origin, temp2 );
-			dl->transformed2[0] = DotProduct( temp2, or->axis[0] );
-			dl->transformed2[1] = DotProduct( temp2, or->axis[1] );
-			dl->transformed2[2] = DotProduct( temp2, or->axis[2] );
-		}
 	}
 }
 
-
-#ifdef USE_LEGACY_DLIGHTS
 /*
 =============
 R_DlightBmodel
@@ -68,7 +60,7 @@
 */
 void R_DlightBmodel( bmodel_t *bmodel ) {
 	int			i, j;
-	const dlight_t	*dl;
+	dlight_t	*dl;
 	int			mask;
 	msurface_t	*surf;
 
@@ -76,7 +68,7 @@
 	R_TransformDlights( tr.refdef.num_dlights, tr.refdef.dlights, &tr.or );
 
 	mask = 0;
-	for ( i = 0; i < tr.refdef.num_dlights; i++ ) {
+	for ( i=0 ; i<tr.refdef.num_dlights ; i++ ) {
 		dl = &tr.refdef.dlights[i];
 
 		// see if the point is close enough to the bounds to matter
@@ -96,22 +88,21 @@
 		mask |= 1 << i;
 	}
 
-	tr.currentEntity->needDlights = (mask != 0) ? 1 : 0;
+	tr.currentEntity->needDlights = (mask != 0);
 
 	// set the dlight bits in all the surfaces
 	for ( i = 0 ; i < bmodel->numSurfaces ; i++ ) {
 		surf = bmodel->firstSurface + i;
 
 		if ( *surf->data == SF_FACE ) {
-			((srfSurfaceFace_t *)surf->data)->dlightBits = mask;
+			((srfSurfaceFace_t *)surf->data)->dlightBits[ tr.smpFrame ] = mask;
 		} else if ( *surf->data == SF_GRID ) {
-			((srfGridMesh_t *)surf->data)->dlightBits = mask;
+			((srfGridMesh_t *)surf->data)->dlightBits[ tr.smpFrame ] = mask;
 		} else if ( *surf->data == SF_TRIANGLES ) {
-			((srfTriangles_t *)surf->data)->dlightBits = mask;
+			((srfTriangles_t *)surf->data)->dlightBits[ tr.smpFrame ] = mask;
 		}
 	}
 }
-#endif // USE_LEGACY_DLIGHTS
 
 
 /*
@@ -143,7 +134,7 @@
 	float	totalFactor;
 
 	if ( ent->e.renderfx & RF_LIGHTING_ORIGIN ) {
-		// separate lightOrigins are needed so an object that is
+		// seperate lightOrigins are needed so an object that is
 		// sinking into the ground can still be lit, and so
 		// multi-part models can be lit identically
 		VectorCopy( ent->e.lightingOrigin, lightOrigin );
@@ -160,7 +151,7 @@
 		frac[i] = v - pos[i];
 		if ( pos[i] < 0 ) {
 			pos[i] = 0;
-		} else if ( pos[i] > tr.world->lightGridBounds[i] - 1 ) {
+		} else if ( pos[i] >= tr.world->lightGridBounds[i] - 1 ) {
 			pos[i] = tr.world->lightGridBounds[i] - 1;
 		}
 	}
@@ -169,7 +160,7 @@
 	VectorClear( ent->directedLight );
 	VectorClear( direction );
 
-	assert( tr.world->lightGridData ); // NULL with -nolight maps
+	assert( tr.world->lightGridData ); // bk010103 - NULL with -nolight maps
 
 	// trilerp the light value
 	gridStep[0] = 8;
@@ -184,13 +175,13 @@
 		byte	*data;
 		int		lat, lng;
 		vec3_t	normal;
+		#if idppc
+		float d0, d1, d2, d3, d4, d5;
+		#endif
 		factor = 1.0;
 		data = gridData;
 		for ( j = 0 ; j < 3 ; j++ ) {
 			if ( i & (1<<j) ) {
-				if ( pos[j] + 1 > tr.world->lightGridBounds[j] - 1 ) {
-					break; // ignore values outside lightgrid
-				}
 				factor *= frac[j];
 				data += gridStep[j];
 			} else {
@@ -198,15 +189,22 @@
 			}
 		}
 
-		if ( j != 3 ) {
-			continue;
-		}
-
 		if ( !(data[0]+data[1]+data[2]) ) {
 			continue;	// ignore samples in walls
 		}
 		totalFactor += factor;
-
+		#if idppc
+		d0 = data[0]; d1 = data[1]; d2 = data[2];
+		d3 = data[3]; d4 = data[4]; d5 = data[5];
+
+		ent->ambientLight[0] += factor * d0;
+		ent->ambientLight[1] += factor * d1;
+		ent->ambientLight[2] += factor * d2;
+
+		ent->directedLight[0] += factor * d3;
+		ent->directedLight[1] += factor * d4;
+		ent->directedLight[2] += factor * d5;
+		#else
 		ent->ambientLight[0] += factor * data[0];
 		ent->ambientLight[1] += factor * data[1];
 		ent->ambientLight[2] += factor * data[2];
@@ -214,7 +212,7 @@
 		ent->directedLight[0] += factor * data[3];
 		ent->directedLight[1] += factor * data[4];
 		ent->directedLight[2] += factor * data[5];
-
+		#endif
 		lat = data[7];
 		lng = data[6];
 		lat *= (FUNCTABLE_SIZE/256);
@@ -249,7 +247,7 @@
 LogLight
 ===============
 */
-static void LogLight( const trRefEntity_t *ent ) {
+static void LogLight( trRefEntity_t *ent ) {
 	int	max1, max2;
 
 	if ( !(ent->e.renderfx & RF_FIRST_PERSON ) ) {
@@ -273,7 +271,6 @@
 	ri.Printf( PRINT_ALL, "amb:%i  dir:%i\n", max1, max2 );
 }
 
-
 /*
 =================
 R_SetupEntityLighting
@@ -284,17 +281,14 @@
 */
 void R_SetupEntityLighting( const trRefdef_t *refdef, trRefEntity_t *ent ) {
 	int				i;
-	const dlight_t		*dl;
+	dlight_t		*dl;
 	float			power;
 	vec3_t			dir;
 	float			d;
 	vec3_t			lightDir;
 	vec3_t			lightOrigin;
-#ifdef USE_PMLIGHT
-	vec3_t			shadowLightDir;
-#endif
 
-	// lighting calculations
+	// lighting calculations 
 	if ( ent->lightingCalculated ) {
 		return;
 	}
@@ -304,7 +298,7 @@
 	// trace a sample point down to find ambient light
 	//
 	if ( ent->e.renderfx & RF_LIGHTING_ORIGIN ) {
-		// separate lightOrigins are needed so an object that is
+		// seperate lightOrigins are needed so an object that is
 		// sinking into the ground can still be lit, and so
 		// multi-part models can be lit identically
 		VectorCopy( ent->e.lightingOrigin, lightOrigin );
@@ -313,13 +307,13 @@
 	}
 
 	// if NOWORLDMODEL, only use dynamic lights (menu system, etc)
-	if ( !(refdef->rdflags & RDF_NOWORLDMODEL )
+	if ( !(refdef->rdflags & RDF_NOWORLDMODEL ) 
 		&& tr.world->lightGridData ) {
 		R_SetupEntityLightingGrid( ent );
 	} else {
-		ent->ambientLight[0] = ent->ambientLight[1] =
+		ent->ambientLight[0] = ent->ambientLight[1] = 
 			ent->ambientLight[2] = tr.identityLight * 150;
-		ent->directedLight[0] = ent->directedLight[1] =
+		ent->directedLight[0] = ent->directedLight[1] = 
 			ent->directedLight[2] = tr.identityLight * 150;
 		VectorCopy( tr.sunDirection, ent->lightDir );
 	}
@@ -337,29 +331,7 @@
 	//
 	d = VectorLength( ent->directedLight );
 	VectorScale( ent->lightDir, d, lightDir );
-#ifdef USE_PMLIGHT
-	if ( R_GetDlightMode() == 2 ) {
-		// only direct lights
-		// but we need to deal with shadow light direction
-		VectorCopy( lightDir, shadowLightDir );
-		if ( r_shadows->integer == 2 ) {
-			for ( i = 0 ; i < refdef->num_dlights ; i++ ) {
-				dl = &refdef->dlights[i];
-				if ( dl->linear ) // no support for linear lights atm
-					continue;
-				VectorSubtract( dl->origin, lightOrigin, dir );
-				d = VectorNormalize( dir );
-				power = DLIGHT_AT_RADIUS * ( dl->radius * dl->radius );
-				if ( d < DLIGHT_MINIMUM_RADIUS ) {
-					d = DLIGHT_MINIMUM_RADIUS;
-				}
-				d = power / ( d * d );
-				VectorMA( shadowLightDir, d, dir, shadowLightDir );
-			}
-		} // if ( r_shadows->integer == 2 )
-	}  // if ( dlightMode == 2 )
-	else
-#endif
+
 	for ( i = 0 ; i < refdef->num_dlights ; i++ ) {
 		dl = &refdef->dlights[i];
 		VectorSubtract( dl->origin, lightOrigin, dir );
@@ -387,28 +359,18 @@
 	}
 
 	// save out the byte packet version
-	((byte *)&ent->ambientLightInt)[0] = myftol( ent->ambientLight[0] ); // -EC-: don't use ri.ftol to avoid precision losses
+	((byte *)&ent->ambientLightInt)[0] = myftol( ent->ambientLight[0] );
 	((byte *)&ent->ambientLightInt)[1] = myftol( ent->ambientLight[1] );
 	((byte *)&ent->ambientLightInt)[2] = myftol( ent->ambientLight[2] );
 	((byte *)&ent->ambientLightInt)[3] = 0xff;
-
+	
 	// transform the direction to local space
 	VectorNormalize( lightDir );
 	ent->lightDir[0] = DotProduct( lightDir, ent->e.axis[0] );
 	ent->lightDir[1] = DotProduct( lightDir, ent->e.axis[1] );
 	ent->lightDir[2] = DotProduct( lightDir, ent->e.axis[2] );
-
-#ifdef USE_PMLIGHT
-	if ( r_shadows->integer == 2 && R_GetDlightMode() == 2 ) {
-		VectorNormalize( shadowLightDir );
-		ent->shadowLightDir[0] = DotProduct( shadowLightDir, ent->e.axis[0] );
-		ent->shadowLightDir[1] = DotProduct( shadowLightDir, ent->e.axis[1] );
-		ent->shadowLightDir[2] = DotProduct( shadowLightDir, ent->e.axis[2] );
-	}
-#endif
 }
 
-
 /*
 =================
 R_LightForPoint
@@ -417,7 +379,8 @@
 int R_LightForPoint( vec3_t point, vec3_t ambientLight, vec3_t directedLight, vec3_t lightDir )
 {
 	trRefEntity_t ent;
-
+	
+	// bk010103 - this segfaults with -nolight maps
 	if ( tr.world->lightGridData == NULL )
 	  return qfalse;
 
@@ -430,28 +393,3 @@
 
 	return qtrue;
 }
-
-/*
-=============
-R_GetDlightMode
-
-Get the dynamic lighing method used
-
-Return 0 for legacy vertex lighting
-       1 for per pixel lighting
-	   2 for per pixel lighting also affecting MD3 models
-=============
-*/
-
-int R_GetDlightMode( void )
-{
-#ifdef USE_PMLIGHT
-	if (!qglGenProgramsARB) {
-		return 0;
-	} else {
-		return r_dlightMode->integer;
-	}
-#else
-	return 0;
-#endif
-}

```
