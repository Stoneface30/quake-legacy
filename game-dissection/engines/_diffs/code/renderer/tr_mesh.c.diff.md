# Diff: `code/renderer/tr_mesh.c`
**Canonical:** `quake3e` (sha256 `97c1d980dd46...`, 11879 bytes)

## Variants

### `quake3-source`  — sha256 `e80111f52a10...`, 10589 bytes

_Diff stat: +51 / -93 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_mesh.c	2026-04-16 20:02:27.318608500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_mesh.c	2026-04-16 20:02:19.972123600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -41,26 +41,26 @@
 	p[1] = fabs( r );
 	p[2] = -dist;
 
-#if 0
-	projected[0] = p[0] * tr.viewParms.projectionMatrix[0] +
-					p[1] * tr.viewParms.projectionMatrix[4] +
-					p[2] * tr.viewParms.projectionMatrix[8] +
-					tr.viewParms.projectionMatrix[12];
-#endif
-	projected[1] = p[0] * tr.viewParms.projectionMatrix[1] +
-					p[1] * tr.viewParms.projectionMatrix[5] +
-					p[2] * tr.viewParms.projectionMatrix[9] +
-					tr.viewParms.projectionMatrix[13];
-#if 0
-	projected[2] = p[0] * tr.viewParms.projectionMatrix[2] +
-					p[1] * tr.viewParms.projectionMatrix[6] +
-					p[2] * tr.viewParms.projectionMatrix[10] +
-					tr.viewParms.projectionMatrix[14];
-#endif
-	projected[3] = p[0] * tr.viewParms.projectionMatrix[3] +
-					p[1] * tr.viewParms.projectionMatrix[7] +
-					p[2] * tr.viewParms.projectionMatrix[11] +
-					tr.viewParms.projectionMatrix[15];
+	projected[0] = p[0] * tr.viewParms.projectionMatrix[0] + 
+		           p[1] * tr.viewParms.projectionMatrix[4] +
+				   p[2] * tr.viewParms.projectionMatrix[8] +
+				   tr.viewParms.projectionMatrix[12];
+
+	projected[1] = p[0] * tr.viewParms.projectionMatrix[1] + 
+		           p[1] * tr.viewParms.projectionMatrix[5] +
+				   p[2] * tr.viewParms.projectionMatrix[9] +
+				   tr.viewParms.projectionMatrix[13];
+
+	projected[2] = p[0] * tr.viewParms.projectionMatrix[2] + 
+		           p[1] * tr.viewParms.projectionMatrix[6] +
+				   p[2] * tr.viewParms.projectionMatrix[10] +
+				   tr.viewParms.projectionMatrix[14];
+
+	projected[3] = p[0] * tr.viewParms.projectionMatrix[3] + 
+		           p[1] * tr.viewParms.projectionMatrix[7] +
+				   p[2] * tr.viewParms.projectionMatrix[11] +
+				   tr.viewParms.projectionMatrix[15];
+
 
 	pr = projected[1] / projected[3];
 
@@ -70,14 +70,13 @@
 	return pr;
 }
 
-
 /*
 =============
 R_CullModel
 =============
 */
-static int R_CullModel( md3Header_t *header, const trRefEntity_t *ent, vec3_t bounds[] ) {
-	//vec3_t bounds[2];
+static int R_CullModel( md3Header_t *header, trRefEntity_t *ent ) {
+	vec3_t		bounds[2];
 	md3Frame_t	*oldFrame, *newFrame;
 	int			i;
 
@@ -85,12 +84,6 @@
 	newFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->e.frame;
 	oldFrame = ( md3Frame_t * ) ( ( byte * ) header + header->ofsFrames ) + ent->e.oldframe;
 
-	// calculate a bounding box in the current coordinate system
-	for (i = 0 ; i < 3 ; i++) {
-		bounds[0][i] = oldFrame->bounds[0][i] < newFrame->bounds[0][i] ? oldFrame->bounds[0][i] : newFrame->bounds[0][i];
-		bounds[1][i] = oldFrame->bounds[1][i] > newFrame->bounds[1][i] ? oldFrame->bounds[1][i] : newFrame->bounds[1][i];
-	}
-
 	// cull bounding sphere ONLY if this is not an upscaled entity
 	if ( !ent->e.nonNormalizedAxes )
 	{
@@ -141,6 +134,12 @@
 			}
 		}
 	}
+	
+	// calculate a bounding box in the current coordinate system
+	for (i = 0 ; i < 3 ; i++) {
+		bounds[0][i] = oldFrame->bounds[0][i] < newFrame->bounds[0][i] ? oldFrame->bounds[0][i] : newFrame->bounds[0][i];
+		bounds[1][i] = oldFrame->bounds[1][i] > newFrame->bounds[1][i] ? oldFrame->bounds[1][i] : newFrame->bounds[1][i];
+	}
 
 	switch ( R_CullLocalBox( bounds ) )
 	{
@@ -161,6 +160,7 @@
 /*
 =================
 R_ComputeLOD
+
 =================
 */
 int R_ComputeLOD( trRefEntity_t *ent ) {
@@ -168,8 +168,6 @@
 	float flod, lodscale;
 	float projectedRadius;
 	md3Frame_t *frame;
-	mdrHeader_t *mdr;
-	mdrFrame_t *mdrframe;
 	int lod;
 
 	if ( tr.currentModel->numLods < 2 )
@@ -182,24 +180,11 @@
 		// multiple LODs exist, so compute projected bounding sphere
 		// and use that as a criteria for selecting LOD
 
-		if(tr.currentModel->type == MOD_MDR)
-		{
-			int frameSize;
-			mdr = (mdrHeader_t *) tr.currentModel->modelData;
-			frameSize = (size_t) (&((mdrFrame_t *)0)->bones[mdr->numBones]);
-			
-			mdrframe = (mdrFrame_t *) ((byte *) mdr + mdr->ofsFrames + frameSize * ent->e.frame);
-			
-			radius = RadiusFromBounds(mdrframe->bounds[0], mdrframe->bounds[1]);
-		}
-		else
-		{
-			frame = ( md3Frame_t * ) ( ( ( unsigned char * ) tr.currentModel->md3[0] ) + tr.currentModel->md3[0]->ofsFrames );
+		frame = ( md3Frame_t * ) ( ( ( unsigned char * ) tr.currentModel->md3[0] ) + tr.currentModel->md3[0]->ofsFrames );
 
-			frame += ent->e.frame;
+		frame += ent->e.frame;
 
-			radius = RadiusFromBounds( frame->bounds[0], frame->bounds[1] );
-		}
+		radius = RadiusFromBounds( frame->bounds[0], frame->bounds[1] );
 
 		if ( ( projectedRadius = ProjectRadius( radius, ent->e.origin ) ) != 0 )
 		{
@@ -236,15 +221,15 @@
 	return lod;
 }
 
-
 /*
 =================
 R_ComputeFogNum
+
 =================
 */
-static int R_ComputeFogNum( md3Header_t *header, const trRefEntity_t *ent ) {
+int R_ComputeFogNum( md3Header_t *header, trRefEntity_t *ent ) {
 	int				i, j;
-	const fog_t			*fog;
+	fog_t			*fog;
 	md3Frame_t		*md3Frame;
 	vec3_t			localOrigin;
 
@@ -273,32 +258,25 @@
 	return 0;
 }
 
-
 /*
 =================
 R_AddMD3Surfaces
+
 =================
 */
 void R_AddMD3Surfaces( trRefEntity_t *ent ) {
-	vec3_t			bounds[2];
 	int				i;
-	md3Header_t		*header = NULL;
-	md3Surface_t	*surface = NULL;
-	md3Shader_t		*md3Shader = NULL;
-	shader_t		*shader = NULL;
+	md3Header_t		*header = 0;
+	md3Surface_t	*surface = 0;
+	md3Shader_t		*md3Shader = 0;
+	shader_t		*shader = 0;
 	int				cull;
 	int				lod;
 	int				fogNum;
 	qboolean		personalModel;
-#ifdef USE_PMLIGHT
-	dlight_t		*dl;
-	int				n;
-	dlight_t		*dlights[ ARRAY_LEN( backEndData->dlights ) ];
-	int				numDlights;
-#endif
 
 	// don't add third_person objects if not in a portal
-	personalModel = (ent->e.renderfx & RF_THIRD_PERSON) && (tr.viewParms.portalView == PV_NONE);
+	personalModel = (ent->e.renderfx & RF_THIRD_PERSON) && !tr.viewParms.isPortal;
 
 	if ( ent->e.renderfx & RF_WRAP_FRAMES ) {
 		ent->e.frame %= tr.currentModel->md3[0]->numFrames;
@@ -333,7 +311,7 @@
 	// cull the entire model if merged bounding box of both frames
 	// is outside the view frustum.
 	//
-	cull = R_CullModel( header, ent, bounds );
+	cull = R_CullModel ( header, ent );
 	if ( cull == CULL_OUT ) {
 		return;
 	}
@@ -345,18 +323,6 @@
 		R_SetupEntityLighting( &tr.refdef, ent );
 	}
 
-#ifdef USE_PMLIGHT
-	numDlights = 0;
-	if ( R_GetDlightMode() >= 2 && ( !personalModel || tr.viewParms.portalView != PV_NONE ) ) {
-		R_TransformDlights( tr.viewParms.num_dlights, tr.viewParms.dlights, &tr.or );
-		for ( n = 0; n < tr.viewParms.num_dlights; n++ ) {
-			dl = &tr.viewParms.dlights[ n ];
-			if ( !R_LightCullBounds( dl, bounds[0], bounds[1] ) ) 
-				dlights[ numDlights++ ] = dl;
-		}
-	}
-#endif
-
 	//
 	// see if we are in a fog volume
 	//
@@ -371,7 +337,7 @@
 		if ( ent->e.customShader ) {
 			shader = R_GetShaderByHandle( ent->e.customShader );
 		} else if ( ent->e.customSkin > 0 && ent->e.customSkin < tr.numSkins ) {
-			const skin_t *skin;
+			skin_t *skin;
 			int		j;
 
 			skin = R_GetSkinByHandle( ent->e.customSkin );
@@ -380,8 +346,8 @@
 			shader = tr.defaultShader;
 			for ( j = 0 ; j < skin->numSurfaces ; j++ ) {
 				// the names have both been lowercased
-				if ( !strcmp( skin->surfaces[j].name, surface->name ) ) {
-					shader = skin->surfaces[j].shader;
+				if ( !strcmp( skin->surfaces[j]->name, surface->name ) ) {
+					shader = skin->surfaces[j]->shader;
 					break;
 				}
 			}
@@ -408,7 +374,7 @@
 			&& fogNum == 0
 			&& !(ent->e.renderfx & ( RF_NOSHADOW | RF_DEPTHHACK ) ) 
 			&& shader->sort == SS_OPAQUE ) {
-			R_AddDrawSurf( (void *)surface, tr.shadowShader, 0, 0 );
+			R_AddDrawSurf( (void *)surface, tr.shadowShader, 0, qfalse );
 		}
 
 		// projection shadows work fine with personal models
@@ -416,24 +382,16 @@
 			&& fogNum == 0
 			&& (ent->e.renderfx & RF_SHADOW_PLANE )
 			&& shader->sort == SS_OPAQUE ) {
-			R_AddDrawSurf( (void *)surface, tr.projectionShadowShader, 0, 0 );
+			R_AddDrawSurf( (void *)surface, tr.projectionShadowShader, 0, qfalse );
 		}
 
 		// don't add third_person objects if not viewing through a portal
 		if ( !personalModel ) {
-			R_AddDrawSurf( (void *)surface, shader, fogNum, 0 );
-		}
-
-#ifdef USE_PMLIGHT
-		if ( numDlights && shader->lightingStage >= 0 ) {
-			for ( n = 0; n < numDlights; n++ ) {
-				dl = dlights[ n ];
-				tr.light = dl;
-				R_AddLitSurf( (void *)surface, shader, fogNum );
-			}
+			R_AddDrawSurf( (void *)surface, shader, fogNum, qfalse );
 		}
-#endif
 
 		surface = (md3Surface_t *)( (byte *)surface + surface->ofsEnd );
 	}
+
 }
+

```
