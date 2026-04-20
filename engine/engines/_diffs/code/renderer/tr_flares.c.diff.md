# Diff: `code/renderer/tr_flares.c`
**Canonical:** `quake3e` (sha256 `6c205cbed916...`, 13624 bytes)

## Variants

### `quake3-source`  — sha256 `f81a5743f302...`, 12858 bytes

_Diff stat: +105 / -143 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_flares.c	2026-04-16 20:02:27.315570800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_flares.c	2026-04-16 20:02:19.969123300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,12 +29,12 @@
 LIGHT FLARES
 
 A light flare is an effect that takes place inside the eye when bright light
-sources are visible.  The size of the flare relative to the screen is nearly
+sources are visible.  The size of the flare reletive to the screen is nearly
 constant, irrespective of distance, but the intensity should be proportional to the
 projected area of the light source.
 
 A surface that has been flagged as having a light flare will calculate the depth
-buffer value that its midpoint should have when the surface is added.
+buffer value that it's midpoint should have when the surface is added.
 
 After all opaque surfaces have been rendered, the depth buffer is read back for
 each flare in view.  If the point has not been obscured by a closer surface, the
@@ -62,7 +62,7 @@
 
 	int			addedFrame;
 
-	portalView_t portalView;
+	qboolean	inPortal;				// true if in a portal view of the scene
 	int			frameSceneNum;
 	void		*surface;
 	int			fogNum;
@@ -74,13 +74,11 @@
 
 	int			windowX, windowY;
 	float		eyeZ;
-	float		drawZ;
 
-	vec3_t		origin;
 	vec3_t		color;
 } flare_t;
 
-#define		MAX_FLARES		256
+#define		MAX_FLARES		128
 
 flare_t		r_flareStructs[MAX_FLARES];
 flare_t		*r_activeFlares, *r_inactiveFlares;
@@ -113,24 +111,13 @@
 */
 void RB_AddFlare( void *surface, int fogNum, vec3_t point, vec3_t color, vec3_t normal ) {
 	int				i;
-	flare_t			*f;
+	flare_t			*f, *oldest;
 	vec3_t			local;
-	float			d = 1;
+	float			d;
 	vec4_t			eye, clip, normalized, window;
 
 	backEnd.pc.c_flareAdds++;
 
-	if ( normal && (normal[0] || normal[1] || normal[2]) )
-	{
-		VectorSubtract( backEnd.viewParms.or.origin, point, local );
-		VectorNormalizeFast( local );
-		d = DotProduct( local, normal );
-
-		// If the viewer is behind the flare don't add it.
-		if ( d < 0 )
-			return;
-	}
-
 	// if the point is off the screen, don't bother adding it
 	// calculate screen coordinates and depth
 	R_TransformModelToClip( point, backEnd.or.modelMatrix, 
@@ -151,15 +138,16 @@
 	}
 
 	// see if a flare with a matching surface, scene, and view exists
+	oldest = r_flareStructs;
 	for ( f = r_activeFlares ; f ; f = f->next ) {
 		if ( f->surface == surface && f->frameSceneNum == backEnd.viewParms.frameSceneNum
-			&& f->portalView == backEnd.viewParms.portalView ) {
+			&& f->inPortal == backEnd.viewParms.isPortal ) {
 			break;
 		}
 	}
 
 	// allocate a new one
-	if ( !f ) {
+	if (!f ) {
 		if ( !r_inactiveFlares ) {
 			// the list is completely full
 			return;
@@ -171,7 +159,7 @@
 
 		f->surface = surface;
 		f->frameSceneNum = backEnd.viewParms.frameSceneNum;
-		f->portalView = backEnd.viewParms.portalView;
+		f->inPortal = backEnd.viewParms.isPortal;
 		f->addedFrame = -1;
 	}
 
@@ -183,26 +171,24 @@
 	f->addedFrame = backEnd.viewParms.frameCount;
 	f->fogNum = fogNum;
 
-	VectorCopy( point, f->origin );
 	VectorCopy( color, f->color );
 
 	// fade the intensity of the flare down as the
 	// light surface turns away from the viewer
-	VectorScale( f->color, d, f->color ); 
+	if ( normal ) {
+		VectorSubtract( backEnd.viewParms.or.origin, point, local );
+		VectorNormalizeFast( local );
+		d = DotProduct( local, normal );
+		VectorScale( f->color, d, f->color ); 
+	}
 
 	// save info needed to test
 	f->windowX = backEnd.viewParms.viewportX + window[0];
 	f->windowY = backEnd.viewParms.viewportY + window[1];
 
 	f->eyeZ = eye[2];
-
-	if ( backEnd.viewParms.portalView )
-		f->drawZ = (clip[2] + clip[3] - 1.5 ) / ( 2 * clip[3] );
-	else
-		f->drawZ = (clip[2] + clip[3] - 0.5 ) / ( 2 * clip[3] );
 }
 
-
 /*
 ==================
 RB_AddDlightFlares
@@ -211,39 +197,31 @@
 void RB_AddDlightFlares( void ) {
 	dlight_t		*l;
 	int				i, j, k;
-	fog_t			*fog = NULL;
+	fog_t			*fog;
 
 	if ( !r_flares->integer ) {
 		return;
 	}
 
 	l = backEnd.refdef.dlights;
-
-	if(tr.world)
-		fog = tr.world->fogs;
-
+	fog = tr.world->fogs;
 	for (i=0 ; i<backEnd.refdef.num_dlights ; i++, l++) {
 
-		if(fog)
-		{
-			// find which fog volume the light is in 
-			for ( j = 1 ; j < tr.world->numfogs ; j++ ) {
-				fog = &tr.world->fogs[j];
-				for ( k = 0 ; k < 3 ; k++ ) {
-					if ( l->origin[k] < fog->bounds[0][k] || l->origin[k] > fog->bounds[1][k] ) {
-						break;
-					}
-				}
-				if ( k == 3 ) {
+		// find which fog volume the light is in 
+		for ( j = 1 ; j < tr.world->numfogs ; j++ ) {
+			fog = &tr.world->fogs[j];
+			for ( k = 0 ; k < 3 ; k++ ) {
+				if ( l->origin[k] < fog->bounds[0][k] || l->origin[k] > fog->bounds[1][k] ) {
 					break;
 				}
 			}
-			if ( j == tr.world->numfogs ) {
-				j = 0;
+			if ( k == 3 ) {
+				break;
 			}
 		}
-		else
+		if ( j == tr.world->numfogs ) {
 			j = 0;
+		}
 
 		RB_AddFlare( (void *)l, j, l->origin, l->color, NULL );
 	}
@@ -262,10 +240,11 @@
 RB_TestFlare
 ==================
 */
-static void RB_TestFlare( flare_t *f ) {
+void RB_TestFlare( flare_t *f ) {
 	float			depth;
 	qboolean		visible;
 	float			fade;
+	float			screenZ;
 
 	backEnd.pc.c_flareTests++;
 
@@ -275,7 +254,12 @@
 
 	// read back the z buffer contents
 	qglReadPixels( f->windowX, f->windowY, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, &depth );
-	visible = (depth > f->drawZ);
+
+	screenZ = backEnd.viewParms.projectionMatrix[14] / 
+		( ( 2*depth - 1 ) * backEnd.viewParms.projectionMatrix[11] - backEnd.viewParms.projectionMatrix[10] );
+
+	visible = ( -f->eyeZ - -screenZ ) < 24;
+
 	if ( visible ) {
 		if ( !f->visible ) {
 			f->visible = qtrue;
@@ -306,78 +290,73 @@
 RB_RenderFlare
 ==================
 */
-static void RB_RenderFlare( flare_t *f ) {
+void RB_RenderFlare( flare_t *f ) {
 	float			size;
 	vec3_t			color;
-	float distance, intensity, factor;
-	byte fogFactors[3] = {255, 255, 255};
-	color4ub_t		c;
+	int				iColor[3];
 
 	backEnd.pc.c_flareRenders++;
 
-	// We don't want too big values anyways when dividing by distance.
-	if ( f->eyeZ > -1.0f )
-		distance = 1.0f;
-	else
-		distance = -f->eyeZ;
+	VectorScale( f->color, f->drawIntensity*tr.identityLight, color );
+	iColor[0] = color[0] * 255;
+	iColor[1] = color[1] * 255;
+	iColor[2] = color[2] * 255;
 
-	// calculate the flare size..
-	size = backEnd.viewParms.viewportWidth * ( r_flareSize->value/640.0f + 8 / distance );
-
-/*
- * This is an alternative to intensity scaling. It changes the size of the flare on screen instead
- * with growing distance. See in the description at the top why this is not the way to go.
-	// size will change ~ 1/r.
-	size = backEnd.viewParms.viewportWidth * (r_flareSize->value / (distance * -2.0f));
-*/
-
-/*
- * As flare sizes stay nearly constant with increasing distance we must decrease the intensity
- * to achieve a reasonable visual result. The intensity is ~ (size^2 / distance^2) which can be
- * got by considering the ratio of
- * (flaresurface on screen) : (Surface of sphere defined by flare origin and distance from flare)
- * An important requirement is:
- * intensity <= 1 for all distances.
- *
- * The formula used here to compute the intensity is as follows:
- * intensity = flareCoeff * size^2 / (distance + size*sqrt(flareCoeff))^2
- * As you can see, the intensity will have a max. of 1 when the distance is 0.
- * The coefficient flareCoeff will determine the falloff speed with increasing distance.
- */
-
-	factor = distance + size * sqrt( r_flareCoeff->value );
-	
-	intensity = r_flareCoeff->value * size * size / (factor * factor);
-
-	VectorScale(f->color, f->drawIntensity * intensity, color);
-
-	// Calculations for fogging
-	if ( tr.world && f->fogNum > 0 && f->fogNum < tr.world->numfogs )
-	{
-		tess.numVertexes = 1;
-		VectorCopy(f->origin, tess.xyz[0]);
-		tess.fogNum = f->fogNum;
-	
-		RB_CalcModulateColorsByFog(fogFactors);
-		
-		// We don't need to render the flare if colors are 0 anyways.
-		if (!(fogFactors[0] || fogFactors[1] || fogFactors[2]))
-			return;
-	}
+	size = backEnd.viewParms.viewportWidth * ( r_flareSize->value/640.0f + 8 / -f->eyeZ );
 
 	RB_BeginSurface( tr.flareShader, f->fogNum );
 
-	c.rgba[0] = color[0] * fogFactors[0];
-	c.rgba[1] = color[1] * fogFactors[1];
-	c.rgba[2] = color[2] * fogFactors[2];
-	c.rgba[3] = 255;
-
-	RB_AddQuadStamp2( f->windowX - size, f->windowY - size, size * 2, size * 2, 0, 0, 1, 1, c );
+	// FIXME: use quadstamp?
+	tess.xyz[tess.numVertexes][0] = f->windowX - size;
+	tess.xyz[tess.numVertexes][1] = f->windowY - size;
+	tess.texCoords[tess.numVertexes][0][0] = 0;
+	tess.texCoords[tess.numVertexes][0][1] = 0;
+	tess.vertexColors[tess.numVertexes][0] = iColor[0];
+	tess.vertexColors[tess.numVertexes][1] = iColor[1];
+	tess.vertexColors[tess.numVertexes][2] = iColor[2];
+	tess.vertexColors[tess.numVertexes][3] = 255;
+	tess.numVertexes++;
+
+	tess.xyz[tess.numVertexes][0] = f->windowX - size;
+	tess.xyz[tess.numVertexes][1] = f->windowY + size;
+	tess.texCoords[tess.numVertexes][0][0] = 0;
+	tess.texCoords[tess.numVertexes][0][1] = 1;
+	tess.vertexColors[tess.numVertexes][0] = iColor[0];
+	tess.vertexColors[tess.numVertexes][1] = iColor[1];
+	tess.vertexColors[tess.numVertexes][2] = iColor[2];
+	tess.vertexColors[tess.numVertexes][3] = 255;
+	tess.numVertexes++;
+
+	tess.xyz[tess.numVertexes][0] = f->windowX + size;
+	tess.xyz[tess.numVertexes][1] = f->windowY + size;
+	tess.texCoords[tess.numVertexes][0][0] = 1;
+	tess.texCoords[tess.numVertexes][0][1] = 1;
+	tess.vertexColors[tess.numVertexes][0] = iColor[0];
+	tess.vertexColors[tess.numVertexes][1] = iColor[1];
+	tess.vertexColors[tess.numVertexes][2] = iColor[2];
+	tess.vertexColors[tess.numVertexes][3] = 255;
+	tess.numVertexes++;
+
+	tess.xyz[tess.numVertexes][0] = f->windowX + size;
+	tess.xyz[tess.numVertexes][1] = f->windowY - size;
+	tess.texCoords[tess.numVertexes][0][0] = 1;
+	tess.texCoords[tess.numVertexes][0][1] = 0;
+	tess.vertexColors[tess.numVertexes][0] = iColor[0];
+	tess.vertexColors[tess.numVertexes][1] = iColor[1];
+	tess.vertexColors[tess.numVertexes][2] = iColor[2];
+	tess.vertexColors[tess.numVertexes][3] = 255;
+	tess.numVertexes++;
+
+	tess.indexes[tess.numIndexes++] = 0;
+	tess.indexes[tess.numIndexes++] = 1;
+	tess.indexes[tess.numIndexes++] = 2;
+	tess.indexes[tess.numIndexes++] = 0;
+	tess.indexes[tess.numIndexes++] = 2;
+	tess.indexes[tess.numIndexes++] = 3;
 
 	RB_EndSurface();
 }
 
-
 /*
 ==================
 RB_RenderFlares
@@ -403,30 +382,14 @@
 		return;
 	}
 
-	if ( backEnd.isHyperspace ) {
-		return;
-	}
-
-	// Reset currentEntity to world so that any previously referenced entities
-	// don't have influence on the rendering of these flares (i.e. RF_ renderer flags).
-	backEnd.currentEntity = &tr.worldEntity;
-	backEnd.or = backEnd.viewParms.world;
-
-#ifdef USE_FBO
-	// we can't read from multisampled renderbuffer storage
-	if ( blitMSfbo ) {
-		FBO_BlitMS( qtrue );
-	}
-#endif
-
-	// RB_AddDlightFlares();
+//	RB_AddDlightFlares();
 
 	// perform z buffer readback on each flare in this view
 	draw = qfalse;
 	prev = &r_activeFlares;
 	while ( ( f = *prev ) != NULL ) {
 		// throw out any flares that weren't added last frame
-		if ( backEnd.viewParms.frameCount - f->addedFrame > 0 && f->portalView == backEnd.viewParms.portalView ) {
+		if ( f->addedFrame < backEnd.viewParms.frameCount - 1 ) {
 			*prev = f->next;
 			f->next = r_inactiveFlares;
 			r_inactiveFlares = f;
@@ -435,7 +398,8 @@
 
 		// don't draw any here that aren't from this scene / portal
 		f->drawIntensity = 0;
-		if ( f->frameSceneNum == backEnd.viewParms.frameSceneNum && f->portalView == backEnd.viewParms.portalView ) {
+		if ( f->frameSceneNum == backEnd.viewParms.frameSceneNum
+			&& f->inPortal == backEnd.viewParms.isPortal ) {
 			RB_TestFlare( f );
 			if ( f->drawIntensity ) {
 				draw = qtrue;
@@ -451,30 +415,27 @@
 		prev = &f->next;
 	}
 
-#ifdef USE_FBO
-	// bind primary framebuffer again
-	if ( blitMSfbo ) {
-		FBO_BindMain();
-	}
-#endif
-
 	if ( !draw ) {
 		return;		// none visible
 	}
 
-	if ( backEnd.viewParms.portalView != PV_NONE ) {
-		qglDisable( GL_CLIP_PLANE0 );
+	if ( backEnd.viewParms.isPortal ) {
+		qglDisable (GL_CLIP_PLANE0);
 	}
 
 	qglPushMatrix();
-	qglLoadIdentity();
+    qglLoadIdentity();
 	qglMatrixMode( GL_PROJECTION );
 	qglPushMatrix();
-	qglLoadMatrixf( GL_Ortho( backEnd.viewParms.viewportX, backEnd.viewParms.viewportX + backEnd.viewParms.viewportWidth,
-		backEnd.viewParms.viewportY, backEnd.viewParms.viewportY + backEnd.viewParms.viewportHeight, -99999, 99999 ) );
+    qglLoadIdentity();
+	qglOrtho( backEnd.viewParms.viewportX, backEnd.viewParms.viewportX + backEnd.viewParms.viewportWidth,
+			  backEnd.viewParms.viewportY, backEnd.viewParms.viewportY + backEnd.viewParms.viewportHeight,
+			  -99999, 99999 );
 
 	for ( f = r_activeFlares ; f ; f = f->next ) {
-		if ( f->frameSceneNum == backEnd.viewParms.frameSceneNum && f->portalView == backEnd.viewParms.portalView && f->drawIntensity ) {
+		if ( f->frameSceneNum == backEnd.viewParms.frameSceneNum
+			&& f->inPortal == backEnd.viewParms.isPortal
+			&& f->drawIntensity ) {
 			RB_RenderFlare( f );
 		}
 	}
@@ -483,3 +444,4 @@
 	qglMatrixMode( GL_MODELVIEW );
 	qglPopMatrix();
 }
+

```
