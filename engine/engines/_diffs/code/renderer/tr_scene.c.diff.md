# Diff: `code/renderer/tr_scene.c`
**Canonical:** `quake3e` (sha256 `4e3d87aa4b8a...`, 13851 bytes)

## Variants

### `quake3-source`  — sha256 `55f96a11bd0b...`, 11115 bytes

_Diff stat: +52 / -162 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_scene.c	2026-04-16 20:02:27.319608900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_scene.c	2026-04-16 20:02:19.973120000 +0100
@@ -15,44 +15,45 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
 #include "tr_local.h"
 
-static int			r_firstSceneDrawSurf;
-#ifdef USE_PMLIGHT
-static int			r_firstSceneLitSurf;
-#endif
+int			r_firstSceneDrawSurf;
 
 int			r_numdlights;
-static int			r_firstSceneDlight;
+int			r_firstSceneDlight;
 
-static int			r_numentities;
-static int			r_firstSceneEntity;
+int			r_numentities;
+int			r_firstSceneEntity;
 
-static int			r_numpolys;
-static int			r_firstScenePoly;
+int			r_numpolys;
+int			r_firstScenePoly;
 
-static int			r_numpolyverts;
+int			r_numpolyverts;
 
 
 /*
 ====================
-R_InitNextFrame
+R_ToggleSmpFrame
 
 ====================
 */
-void R_InitNextFrame( void ) {
+void R_ToggleSmpFrame( void ) {
+	if ( r_smp->integer ) {
+		// use the other buffers next frame, because another CPU
+		// may still be rendering into the current ones
+		tr.smpFrame ^= 1;
+	} else {
+		tr.smpFrame = 0;
+	}
 
-	backEndData->commands.used = 0;
+	backEndData[tr.smpFrame]->commands.used = 0;
 
 	r_firstSceneDrawSurf = 0;
-#ifdef USE_PMLIGHT
-	r_firstSceneLitSurf = 0;
-#endif
 
 	r_numdlights = 0;
 	r_firstSceneDlight = 0;
@@ -97,14 +98,14 @@
 void R_AddPolygonSurfaces( void ) {
 	int			i;
 	shader_t	*sh;
-	const srfPoly_t	*poly;
+	srfPoly_t	*poly;
 
-	tr.currentEntityNum = REFENTITYNUM_WORLD;
-	tr.shiftedEntityNum = tr.currentEntityNum << QSORT_REFENTITYNUM_SHIFT;
+	tr.currentEntityNum = ENTITYNUM_WORLD;
+	tr.shiftedEntityNum = tr.currentEntityNum << QSORT_ENTITYNUM_SHIFT;
 
 	for ( i = 0, poly = tr.refdef.polys; i < tr.refdef.numPolys ; i++, poly++ ) {
 		sh = R_GetShaderByHandle( poly->hShader );
-		R_AddDrawSurf( ( void * )poly, sh, poly->fogIndex, 0 );
+		R_AddDrawSurf( ( void * )poly, sh, poly->fogIndex, qfalse );
 	}
 }
 
@@ -118,18 +119,18 @@
 	srfPoly_t	*poly;
 	int			i, j;
 	int			fogIndex;
-	const fog_t		*fog;
+	fog_t		*fog;
 	vec3_t		bounds[2];
 
 	if ( !tr.registered ) {
 		return;
 	}
-#if 0
+
 	if ( !hShader ) {
 		ri.Printf( PRINT_WARNING, "WARNING: RE_AddPolyToScene: NULL poly shader\n");
 		return;
 	}
-#endif
+
 	for ( j = 0; j < numPolys; j++ ) {
 		if ( r_numpolyverts + numVerts > max_polyverts || r_numpolys >= max_polys ) {
       /*
@@ -142,21 +143,20 @@
 			return;
 		}
 
-		poly = &backEndData->polys[r_numpolys];
+		poly = &backEndData[tr.smpFrame]->polys[r_numpolys];
 		poly->surfaceType = SF_POLY;
 		poly->hShader = hShader;
 		poly->numVerts = numVerts;
-		poly->verts = &backEndData->polyVerts[r_numpolyverts];
+		poly->verts = &backEndData[tr.smpFrame]->polyVerts[r_numpolyverts];
 		
 		Com_Memcpy( poly->verts, &verts[numVerts*j], numVerts * sizeof( *verts ) );
-#if 0
+
 		if ( glConfig.hardwareType == GLHW_RAGEPRO ) {
 			poly->verts->modulate[0] = 255;
 			poly->verts->modulate[1] = 255;
 			poly->verts->modulate[2] = 255;
 			poly->verts->modulate[3] = 255;
 		}
-#endif
 		// done.
 		r_numpolys++;
 		r_numpolyverts += numVerts;
@@ -197,42 +197,27 @@
 
 //=================================================================================
 
-static int isnan_fp( const float *f )
-{
-	uint32_t u = *( (uint32_t*) f );
-	u = 0x7F800000 - ( u & 0x7FFFFFFF );
-	return (int)( u >> 31 );
-}
-
 
 /*
 =====================
 RE_AddRefEntityToScene
+
 =====================
 */
-void RE_AddRefEntityToScene( const refEntity_t *ent, qboolean intShaderTime ) {
+void RE_AddRefEntityToScene( const refEntity_t *ent ) {
 	if ( !tr.registered ) {
 		return;
 	}
-	if ( r_numentities >= MAX_REFENTITIES ) {
-		ri.Printf( PRINT_DEVELOPER, "RE_AddRefEntityToScene: Dropping refEntity, reached MAX_REFENTITIES\n" );
-		return;
-	}
-	if ( isnan_fp( &ent->origin[0] ) || isnan_fp( &ent->origin[1] ) || isnan_fp( &ent->origin[2] ) ) {
-		static qboolean first_time = qtrue;
-		if ( first_time ) {
-			first_time = qfalse;
-			ri.Printf( PRINT_WARNING, "RE_AddRefEntityToScene passed a refEntity which has an origin with a NaN component\n" );
-		}
+  // https://zerowing.idsoftware.com/bugzilla/show_bug.cgi?id=402
+	if ( r_numentities >= ENTITYNUM_WORLD ) {
 		return;
 	}
-	if ( (unsigned)ent->reType >= RT_MAX_REF_ENTITY_TYPE ) {
+	if ( ent->reType < 0 || ent->reType >= RT_MAX_REF_ENTITY_TYPE ) {
 		ri.Error( ERR_DROP, "RE_AddRefEntityToScene: bad reType %i", ent->reType );
 	}
 
-	backEndData->entities[r_numentities].e = *ent;
-	backEndData->entities[r_numentities].lightingCalculated = qfalse;
-	backEndData->entities[r_numentities].intShaderTime = intShaderTime;
+	backEndData[tr.smpFrame]->entities[r_numentities].e = *ent;
+	backEndData[tr.smpFrame]->entities[r_numentities].lightingCalculated = qfalse;
 
 	r_numentities++;
 }
@@ -241,15 +226,16 @@
 /*
 =====================
 RE_AddDynamicLightToScene
+
 =====================
 */
-static void RE_AddDynamicLightToScene( const vec3_t org, float intensity, float r, float g, float b, int additive ) {
+void RE_AddDynamicLightToScene( const vec3_t org, float intensity, float r, float g, float b, int additive ) {
 	dlight_t	*dl;
 
 	if ( !tr.registered ) {
 		return;
 	}
-	if ( r_numdlights >= ARRAY_LEN( backEndData->dlights ) ) {
+	if ( r_numdlights >= MAX_DLIGHTS ) {
 		return;
 	}
 	if ( intensity <= 0 ) {
@@ -259,90 +245,15 @@
 	if ( glConfig.hardwareType == GLHW_RIVA128 || glConfig.hardwareType == GLHW_PERMEDIA2 ) {
 		return;
 	}
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( R_GetDlightMode() )
-#endif
-	{
-		r *= r_dlightIntensity->value;
-		g *= r_dlightIntensity->value;
-		b *= r_dlightIntensity->value;
-		intensity *= r_dlightScale->value;
-	}
-#endif
-
-	if ( r_dlightSaturation->value != 1.0 )
-	{
-		float luminance = LUMA( r, g, b );
-		r = LERP( luminance, r, r_dlightSaturation->value );
-		g = LERP( luminance, g, r_dlightSaturation->value );
-		b = LERP( luminance, b, r_dlightSaturation->value );
-	}
-
-	dl = &backEndData->dlights[r_numdlights++];
-	VectorCopy( org, dl->origin );
+	dl = &backEndData[tr.smpFrame]->dlights[r_numdlights++];
+	VectorCopy (org, dl->origin);
 	dl->radius = intensity;
 	dl->color[0] = r;
 	dl->color[1] = g;
 	dl->color[2] = b;
 	dl->additive = additive;
-	dl->linear = qfalse;
 }
 
-
-/*
-=====================
-RE_AddLinearLightToScene
-=====================
-*/
-void RE_AddLinearLightToScene( const vec3_t start, const vec3_t end, float intensity, float r, float g, float b  ) {
-	dlight_t	*dl;
-	if ( VectorCompare( start, end ) ) {
-		RE_AddDynamicLightToScene( start, intensity, r, g, b, 0 );
-		return;
-	}
-	if ( !tr.registered ) {
-		return;
-	}
-	if ( r_numdlights >= ARRAY_LEN( backEndData->dlights ) ) {
-		return;
-	}
-	if ( intensity <= 0 ) {
-		return;
-	}
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( R_GetDlightMode() )
-#endif
-	{
-		r *= r_dlightIntensity->value;
-		g *= r_dlightIntensity->value;
-		b *= r_dlightIntensity->value;
-		intensity *= r_dlightScale->value;
-	}
-#endif
-
-	if ( r_dlightSaturation->value != 1.0 )
-	{
-		float luminance = LUMA( r, g, b );
-		r = LERP( luminance, r, r_dlightSaturation->value );
-		g = LERP( luminance, g, r_dlightSaturation->value );
-		b = LERP( luminance, b, r_dlightSaturation->value );
-	}
-
-	dl = &backEndData->dlights[ r_numdlights++ ];
-	VectorCopy( start, dl->origin );
-	VectorCopy( end, dl->origin2 );
-	dl->radius = intensity;
-	dl->color[0] = r;
-	dl->color[1] = g;
-	dl->color[2] = b;
-	dl->additive = 0;
-	dl->linear = qtrue;
-}
-
-
-
 /*
 =====================
 RE_AddLightToScene
@@ -353,7 +264,6 @@
 	RE_AddDynamicLightToScene( org, intensity, r, g, b, qfalse );
 }
 
-
 /*
 =====================
 RE_AddAdditiveLightToScene
@@ -364,7 +274,6 @@
 	RE_AddDynamicLightToScene( org, intensity, r, g, b, qtrue );
 }
 
-
 /*
 @@@@@@@@@@@@@@@@@@@@@
 RE_RenderScene
@@ -383,6 +292,7 @@
 	if ( !tr.registered ) {
 		return;
 	}
+	GLimp_LogComment( "====== RE_RenderScene =====\n" );
 
 	if ( r_norefresh->integer ) {
 		return;
@@ -420,7 +330,7 @@
 
 		// compare the area bits
 		areaDiff = 0;
-		for ( i = 0; i < MAX_MAP_AREA_BYTES/sizeof(int); i++ ) {
+		for (i = 0 ; i < MAX_MAP_AREA_BYTES/4 ; i++) {
 			areaDiff |= ((int *)tr.refdef.areamask)[i] ^ ((int *)fd->areamask)[i];
 			((int *)tr.refdef.areamask)[i] = ((int *)fd->areamask)[i];
 		}
@@ -434,28 +344,25 @@
 
 	// derived info
 
-	tr.refdef.floatTime = (double)tr.refdef.time * 0.001; // -EC-: cast to double
+	tr.refdef.floatTime = tr.refdef.time * 0.001f;
 
 	tr.refdef.numDrawSurfs = r_firstSceneDrawSurf;
-	tr.refdef.drawSurfs = backEndData->drawSurfs;
-
-#ifdef USE_PMLIGHT
-	tr.refdef.numLitSurfs = r_firstSceneLitSurf;
-	tr.refdef.litSurfs = backEndData->litSurfs;
-#endif
+	tr.refdef.drawSurfs = backEndData[tr.smpFrame]->drawSurfs;
 
 	tr.refdef.num_entities = r_numentities - r_firstSceneEntity;
-	tr.refdef.entities = &backEndData->entities[r_firstSceneEntity];
+	tr.refdef.entities = &backEndData[tr.smpFrame]->entities[r_firstSceneEntity];
 
 	tr.refdef.num_dlights = r_numdlights - r_firstSceneDlight;
-	tr.refdef.dlights = &backEndData->dlights[r_firstSceneDlight];
+	tr.refdef.dlights = &backEndData[tr.smpFrame]->dlights[r_firstSceneDlight];
 
 	tr.refdef.numPolys = r_numpolys - r_firstScenePoly;
-	tr.refdef.polys = &backEndData->polys[r_firstScenePoly];
+	tr.refdef.polys = &backEndData[tr.smpFrame]->polys[r_firstScenePoly];
 
 	// turn off dynamic lighting globally by clearing all the
-	// dlights if it needs to be disabled
-	if ( r_dynamiclight->integer == 0 || glConfig.hardwareType == GLHW_PERMEDIA2 ) {
+	// dlights if it needs to be disabled or if vertex lighting is enabled
+	if ( r_dynamiclight->integer == 0 ||
+		 r_vertexLight->integer == 1 ||
+		 glConfig.hardwareType == GLHW_PERMEDIA2 ) {
 		tr.refdef.num_dlights = 0;
 	}
 
@@ -478,23 +385,10 @@
 	parms.viewportY = glConfig.vidHeight - ( tr.refdef.y + tr.refdef.height );
 	parms.viewportWidth = tr.refdef.width;
 	parms.viewportHeight = tr.refdef.height;
-
-	parms.scissorX = parms.viewportX;
-	parms.scissorY = parms.viewportY;
-	parms.scissorWidth = parms.viewportWidth;
-	parms.scissorHeight = parms.viewportHeight;
-
-	parms.portalView = PV_NONE;
-
-#ifdef USE_PMLIGHT
-	parms.dlights = tr.refdef.dlights;
-	parms.num_dlights = tr.refdef.num_dlights;
-#endif
+	parms.isPortal = qfalse;
 
 	parms.fovX = tr.refdef.fov_x;
 	parms.fovY = tr.refdef.fov_y;
-	
-	parms.stereoFrame = tr.refdef.stereoFrame;
 
 	VectorCopy( fd->vieworg, parms.or.origin );
 	VectorCopy( fd->viewaxis[0], parms.or.axis[0] );
@@ -507,10 +401,6 @@
 
 	// the next scene rendered in this frame will tack on after this one
 	r_firstSceneDrawSurf = tr.refdef.numDrawSurfs;
-#ifdef USE_PMLIGHT
-	r_firstSceneLitSurf = tr.refdef.numLitSurfs;
-#endif
-
 	r_firstSceneEntity = r_numentities;
 	r_firstSceneDlight = r_numdlights;
 	r_firstScenePoly = r_numpolys;

```
