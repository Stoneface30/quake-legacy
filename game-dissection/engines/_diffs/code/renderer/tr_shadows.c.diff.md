# Diff: `code/renderer/tr_shadows.c`
**Canonical:** `quake3e` (sha256 `4c79a7144612...`, 8455 bytes)

## Variants

### `quake3-source`  — sha256 `ac1bd5e41e63...`, 8241 bytes

_Diff stat: +100 / -103 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_shadows.c	2026-04-16 20:02:27.320608600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_shadows.c	2026-04-16 20:02:19.974627900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -45,7 +45,7 @@
 static	int			numEdgeDefs[SHADER_MAX_VERTEXES];
 static	int			facing[SHADER_MAX_INDEXES/3];
 
-static void R_AddEdgeDef( int i1, int i2, int f ) {
+void R_AddEdgeDef( int i1, int i2, int facing ) {
 	int		c;
 
 	c = numEdgeDefs[ i1 ];
@@ -53,62 +53,92 @@
 		return;		// overflow
 	}
 	edgeDefs[ i1 ][ c ].i2 = i2;
-	edgeDefs[ i1 ][ c ].facing = f;
+	edgeDefs[ i1 ][ c ].facing = facing;
 
 	numEdgeDefs[ i1 ]++;
 }
 
-
-static void R_CalcShadowEdges( void ) {
-	qboolean sil_edge;
+void R_RenderShadowEdges( void ) {
 	int		i;
+
+#if 0
+	int		numTris;
+
+	// dumb way -- render every triangle's edges
+	numTris = tess.numIndexes / 3;
+
+	for ( i = 0 ; i < numTris ; i++ ) {
+		int		i1, i2, i3;
+
+		if ( !facing[i] ) {
+			continue;
+		}
+
+		i1 = tess.indexes[ i*3 + 0 ];
+		i2 = tess.indexes[ i*3 + 1 ];
+		i3 = tess.indexes[ i*3 + 2 ];
+
+		qglBegin( GL_TRIANGLE_STRIP );
+		qglVertex3fv( tess.xyz[ i1 ] );
+		qglVertex3fv( tess.xyz[ i1 + tess.numVertexes ] );
+		qglVertex3fv( tess.xyz[ i2 ] );
+		qglVertex3fv( tess.xyz[ i2 + tess.numVertexes ] );
+		qglVertex3fv( tess.xyz[ i3 ] );
+		qglVertex3fv( tess.xyz[ i3 + tess.numVertexes ] );
+		qglVertex3fv( tess.xyz[ i1 ] );
+		qglVertex3fv( tess.xyz[ i1 + tess.numVertexes ] );
+		qglEnd();
+	}
+#else
 	int		c, c2;
 	int		j, k;
 	int		i2;
-
-	tess.numIndexes = 0;
+	int		c_edges, c_rejected;
+	int		hit[2];
 
 	// an edge is NOT a silhouette edge if its face doesn't face the light,
 	// or if it has a reverse paired edge that also faces the light.
 	// A well behaved polyhedron would have exactly two faces for each edge,
 	// but lots of models have dangling edges or overfanned edges
-	for ( i = 0; i < tess.numVertexes; i++ ) {
+	c_edges = 0;
+	c_rejected = 0;
+
+	for ( i = 0 ; i < tess.numVertexes ; i++ ) {
 		c = numEdgeDefs[ i ];
 		for ( j = 0 ; j < c ; j++ ) {
 			if ( !edgeDefs[ i ][ j ].facing ) {
 				continue;
 			}
 
-			sil_edge = qtrue;
+			hit[0] = 0;
+			hit[1] = 0;
+
 			i2 = edgeDefs[ i ][ j ].i2;
 			c2 = numEdgeDefs[ i2 ];
 			for ( k = 0 ; k < c2 ; k++ ) {
-				if ( edgeDefs[ i2 ][ k ].i2 == i && edgeDefs[ i2 ][ k ].facing ) {
-					sil_edge = qfalse;
-					break;
+				if ( edgeDefs[ i2 ][ k ].i2 == i ) {
+					hit[ edgeDefs[ i2 ][ k ].facing ]++;
 				}
 			}
 
 			// if it doesn't share the edge with another front facing
 			// triangle, it is a sil edge
-			if ( sil_edge ) {
-				if ( tess.numIndexes > ARRAY_LEN( tess.indexes ) - 6 ) {
-					i = tess.numVertexes;
-					break;
-				}
-				tess.indexes[ tess.numIndexes + 0 ] = i;
-				tess.indexes[ tess.numIndexes + 1 ] = i + tess.numVertexes;
-				tess.indexes[ tess.numIndexes + 2 ] = i2;
-				tess.indexes[ tess.numIndexes + 3 ] = i2;
-				tess.indexes[ tess.numIndexes + 4 ] = i + tess.numVertexes;
-				tess.indexes[ tess.numIndexes + 5 ] = i2 + tess.numVertexes;
-				tess.numIndexes += 6;
+			if ( hit[ 1 ] == 0 ) {
+				qglBegin( GL_TRIANGLE_STRIP );
+				qglVertex3fv( tess.xyz[ i ] );
+				qglVertex3fv( tess.xyz[ i + tess.numVertexes ] );
+				qglVertex3fv( tess.xyz[ i2 ] );
+				qglVertex3fv( tess.xyz[ i2 + tess.numVertexes ] );
+				qglEnd();
+				c_edges++;
+			} else {
+				c_rejected++;
 			}
 		}
 	}
+#endif
 }
 
-
 /*
 =================
 RB_ShadowTessEnd
@@ -125,32 +155,25 @@
 	int		i;
 	int		numTris;
 	vec3_t	lightDir;
-	GLboolean rgba[4];
 
-	if ( glConfig.stencilBits < 4 ) {
+	// we can only do this if we have enough space in the vertex buffers
+	if ( tess.numVertexes >= SHADER_MAX_VERTEXES / 2 ) {
 		return;
 	}
 
-#ifdef USE_PMLIGHT
-	if ( R_GetDlightMode() == 2 && r_shadows->integer == 2 )
-		VectorCopy( backEnd.currentEntity->shadowLightDir, lightDir );
-	else
-#endif
-		VectorCopy( backEnd.currentEntity->lightDir, lightDir );
-
-	// clamp projection by height
-	if ( lightDir[2] > 0.1 ) {
-		float s = 0.1 / lightDir[2];
-		VectorScale( lightDir, s, lightDir );
+	if ( glConfig.stencilBits < 4 ) {
+		return;
 	}
 
+	VectorCopy( backEnd.currentEntity->lightDir, lightDir );
+
 	// project vertexes away from light direction
-	for ( i = 0; i < tess.numVertexes; i++ ) {
+	for ( i = 0 ; i < tess.numVertexes ; i++ ) {
 		VectorMA( tess.xyz[i], -512, lightDir, tess.xyz[i+tess.numVertexes] );
 	}
 
 	// decide which triangles face the light
-	Com_Memset( numEdgeDefs, 0, tess.numVertexes * sizeof( numEdgeDefs[0] ) );
+	Com_Memset( numEdgeDefs, 0, 4 * tess.numVertexes );
 
 	numTris = tess.numIndexes / 3;
 	for ( i = 0 ; i < numTris ; i++ ) {
@@ -184,51 +207,45 @@
 		R_AddEdgeDef( i3, i1, facing[ i ] );
 	}
 
-	R_CalcShadowEdges();
-
-	GL_ClientState( 1, CLS_NONE );
-	GL_ClientState( 0, CLS_NONE );
-
-	qglVertexPointer( 3, GL_FLOAT, sizeof( tess.xyz[0] ), tess.xyz );
-
-	if ( qglLockArraysEXT )
-		qglLockArraysEXT( 0, tess.numVertexes*2 );
-
 	// draw the silhouette edges
 
-	qglDisable( GL_TEXTURE_2D );
-	//GL_Bind( tr.whiteImage );
+	GL_Bind( tr.whiteImage );
+	qglEnable( GL_CULL_FACE );
 	GL_State( GLS_SRCBLEND_ONE | GLS_DSTBLEND_ZERO );
-	qglColor4f( 0.2f, 0.2f, 0.2f, 1.0f );
+	qglColor3f( 0.2f, 0.2f, 0.2f );
 
 	// don't write to the color buffer
-	qglGetBooleanv( GL_COLOR_WRITEMASK, rgba );
 	qglColorMask( GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE );
 
 	qglEnable( GL_STENCIL_TEST );
 	qglStencilFunc( GL_ALWAYS, 1, 255 );
 
-	GL_Cull( CT_BACK_SIDED );
-	qglStencilOp( GL_KEEP, GL_KEEP, GL_INCR );
+	// mirrors have the culling order reversed
+	if ( backEnd.viewParms.isMirror ) {
+		qglCullFace( GL_FRONT );
+		qglStencilOp( GL_KEEP, GL_KEEP, GL_INCR );
 
-	R_DrawElements( tess.numIndexes, tess.indexes );
+		R_RenderShadowEdges();
 
-	GL_Cull( CT_FRONT_SIDED );
-	qglStencilOp( GL_KEEP, GL_KEEP, GL_DECR );
+		qglCullFace( GL_BACK );
+		qglStencilOp( GL_KEEP, GL_KEEP, GL_DECR );
 
-	R_DrawElements( tess.numIndexes, tess.indexes );
+		R_RenderShadowEdges();
+	} else {
+		qglCullFace( GL_BACK );
+		qglStencilOp( GL_KEEP, GL_KEEP, GL_INCR );
 
-	if ( qglUnlockArraysEXT )
-		qglUnlockArraysEXT();
+		R_RenderShadowEdges();
 
-	// re-enable writing to the color buffer
-	qglColorMask(rgba[0], rgba[1], rgba[2], rgba[3]);
+		qglCullFace( GL_FRONT );
+		qglStencilOp( GL_KEEP, GL_KEEP, GL_DECR );
 
-	qglEnable( GL_TEXTURE_2D );
+		R_RenderShadowEdges();
+	}
 
-	backEnd.doneShadows = qtrue;
 
-	tess.numIndexes = 0;
+	// reenable writing to the color buffer
+	qglColorMask( GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE );
 }
 
 
@@ -243,51 +260,37 @@
 =================
 */
 void RB_ShadowFinish( void ) {
-
-	static const vec3_t verts[4] = {
-		{ -100, 100, -10 },
-		{  100, 100, -10 },
-		{ -100,-100, -10 },
-		{  100,-100, -10 }
-	};
-
-	if ( !backEnd.doneShadows ) {
-		return;
-	}
-
-	backEnd.doneShadows = qfalse;
-
 	if ( r_shadows->integer != 2 ) {
 		return;
 	}
 	if ( glConfig.stencilBits < 4 ) {
 		return;
 	}
-
 	qglEnable( GL_STENCIL_TEST );
 	qglStencilFunc( GL_NOTEQUAL, 0, 255 );
 
-	qglDisable( GL_CLIP_PLANE0 );
-	GL_Cull( CT_TWO_SIDED );
+	qglDisable (GL_CLIP_PLANE0);
+	qglDisable (GL_CULL_FACE);
 
-	qglDisable( GL_TEXTURE_2D );
+	GL_Bind( tr.whiteImage );
 
-	qglLoadIdentity();
+    qglLoadIdentity ();
 
-	qglColor4f( 0.6f, 0.6f, 0.6f, 1 );
+	qglColor3f( 0.6f, 0.6f, 0.6f );
 	GL_State( GLS_DEPTHMASK_TRUE | GLS_SRCBLEND_DST_COLOR | GLS_DSTBLEND_ZERO );
 
-	//qglColor4f( 1, 0, 0, 1 );
-	//GL_State( GLS_DEPTHMASK_TRUE | GLS_SRCBLEND_ONE | GLS_DSTBLEND_ZERO );
+//	qglColor3f( 1, 0, 0 );
+//	GL_State( GLS_DEPTHMASK_TRUE | GLS_SRCBLEND_ONE | GLS_DSTBLEND_ZERO );
 
-	GL_ClientState( 0, CLS_NONE );
-	qglVertexPointer( 3, GL_FLOAT, 0, verts );
-	qglDrawArrays( GL_TRIANGLE_STRIP, 0, 4 );
+	qglBegin( GL_QUADS );
+	qglVertex3f( -100, 100, -10 );
+	qglVertex3f( 100, 100, -10 );
+	qglVertex3f( 100, -100, -10 );
+	qglVertex3f( -100, -100, -10 );
+	qglEnd ();
 
-	qglColor4f( 1, 1, 1, 1 );
+	qglColor4f(1,1,1,1);
 	qglDisable( GL_STENCIL_TEST );
-
-	qglEnable( GL_TEXTURE_2D );
 }
 
 
@@ -315,13 +318,7 @@
 
 	groundDist = backEnd.or.origin[2] - backEnd.currentEntity->e.shadowPlane;
 
-#ifdef USE_PMLIGHT
-	if ( R_GetDlightMode() == 2 && r_shadows->integer == 2 )
-		VectorCopy( backEnd.currentEntity->shadowLightDir, lightDir );
-	else
-#endif
-		VectorCopy( backEnd.currentEntity->lightDir, lightDir );
-
+	VectorCopy( backEnd.currentEntity->lightDir, lightDir );
 	d = DotProduct( lightDir, ground );
 	// don't let the shadows get too long or go negative
 	if ( d < 0.5 ) {

```
