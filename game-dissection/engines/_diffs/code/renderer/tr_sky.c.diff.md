# Diff: `code/renderer/tr_sky.c`
**Canonical:** `quake3e` (sha256 `bba9a0e84a8e...`, 21265 bytes)

## Variants

### `quake3-source`  — sha256 `eab02d833aca...`, 21380 bytes

_Diff stat: +221 / -246 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderer\tr_sky.c	2026-04-16 20:02:27.321609800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\renderer\tr_sky.c	2026-04-16 20:02:19.974627900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -26,6 +26,7 @@
 #define HALF_SKY_SUBDIVISIONS	(SKY_SUBDIVISIONS/2)
 
 static float s_cloudTexCoords[6][SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1][2];
+static float s_cloudTexP[6][SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1];
 
 /*
 ===================================================================================
@@ -35,19 +36,18 @@
 ===================================================================================
 */
 
-static const vec3_t sky_clip[6] =
+static vec3_t sky_clip[6] = 
 {
-	{ 1, 1, 0},
-	{ 1,-1, 0},
-	{ 0,-1, 1},
-	{ 0, 1, 1},
-	{ 1, 0, 1},
-	{-1, 0, 1}
+	{1,1,0},
+	{1,-1,0},
+	{0,-1,1},
+	{0,1,1},
+	{1,0,1},
+	{-1,0,1} 
 };
 
 static float	sky_mins[2][6], sky_maxs[2][6];
 static float	sky_min, sky_max;
-static float	sky_min_depth;
 
 /*
 ================
@@ -62,7 +62,7 @@
 	int		axis;
 	float	*vp;
 	// s = [0]/[2], t = [1]/[2]
-	static const int vec_to_st[6][3] =
+	static int	vec_to_st[6][3] =
 	{
 		{-2,3,1},
 		{2,3,-1},
@@ -149,7 +149,7 @@
 */
 static void ClipSkyPolygon (int nump, vec3_t vecs, int stage) 
 {
-	const float *norm;
+	float	*norm;
 	float	*v;
 	qboolean	front, back;
 	float	d, e;
@@ -257,7 +257,7 @@
 RB_ClipSkyPolygons
 ================
 */
-static void RB_ClipSkyPolygons( const shaderCommands_t *input )
+void RB_ClipSkyPolygons( shaderCommands_t *input )
 {
 	vec3_t		p[5];	// need one extra point for clipping
 	int			i, j;
@@ -289,10 +289,10 @@
 **
 ** Parms: s, t range from -1 to 1
 */
-static void MakeSkyVec( float s, float t, int axis, vec3_t outXYZ )
+static void MakeSkyVec( float s, float t, int axis, float outSt[2], vec3_t outXYZ )
 {
 	// 1 = s, 2 = t, 3 = 2048
-	static const int st_to_vec[6][3] =
+	static int	st_to_vec[6][3] =
 	{
 		{3,-1,2},
 		{-3,1,2},
@@ -313,10 +313,10 @@
 	b[1] = t*boxSize;
 	b[2] = boxSize;
 
-	for ( j = 0; j < 3; j++ )
+	for (j=0 ; j<3 ; j++)
 	{
 		k = st_to_vec[axis][j];
-		if ( k < 0 )
+		if (k < 0)
 		{
 			outXYZ[j] = -b[-k - 1];
 		}
@@ -325,156 +325,75 @@
 			outXYZ[j] = b[k - 1];
 		}
 	}
-}
-
-
-static const int sky_texorder[6] = {0, 2, 1, 3, 4, 5};
-static vec3_t	s_skyPoints[SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1];
-static float	s_skyTexCoords[SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1][2];
 
-
-/*
-=================
-CullPoints
-=================
-*/
-static qboolean CullPoints( vec4_t v[], const int count )
-{
-	const cplane_t *frust;
-	int i, j;
-	float dist;
-
-	for ( i = 0; i < 5; i++ ) {
-		frust = &backEnd.viewParms.frustum[i];
-		for ( j = 0; j < count; j++ ) {
-			dist = DotProduct( v[j], frust->normal ) - frust->dist;
-			if ( dist >= 0 ) {
-				break;
-			}
-		}
-		// all points are completely behind at least of one frustum plane
-		if ( j == count ) {
-			return qtrue;
-		}
+	// avoid bilerp seam
+	s = (s+1)*0.5;
+	t = (t+1)*0.5;
+	if (s < sky_min)
+	{
+		s = sky_min;
+	}
+	else if (s > sky_max)
+	{
+		s = sky_max;
 	}
 
-	return qfalse;
-}
-
-
-static qboolean CullSkySide( const int mins[2], const int maxs[2] )
-{
-	int s, t;
-	vec4_t v[4];
-
-	if ( r_nocull->integer )
-		return qfalse;
-
-	s = mins[0] + HALF_SKY_SUBDIVISIONS;
-	t = mins[1] + HALF_SKY_SUBDIVISIONS;
-	VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, v[0] );
-
-	s = mins[0] + HALF_SKY_SUBDIVISIONS;
-	t = maxs[1] + HALF_SKY_SUBDIVISIONS;
-	VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, v[1] );
-
-	s = maxs[0] + HALF_SKY_SUBDIVISIONS;
-	t = mins[1] + HALF_SKY_SUBDIVISIONS;
-	VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, v[2] );
+	if (t < sky_min)
+	{
+		t = sky_min;
+	}
+	else if (t > sky_max)
+	{
+		t = sky_max;
+	}
 
-	s = maxs[0] + HALF_SKY_SUBDIVISIONS;
-	t = maxs[1] + HALF_SKY_SUBDIVISIONS;
-	VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, v[3] );
+	t = 1.0 - t;
 
-	if ( CullPoints( v, 4 ) )
-		return qtrue;
 
-	return qfalse;
+	if ( outSt )
+	{
+		outSt[0] = s;
+		outSt[1] = t;
+	}
 }
 
+static int	sky_texorder[6] = {0,2,1,3,4,5};
+static vec3_t	s_skyPoints[SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1];
+static float	s_skyTexCoords[SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1][2];
 
-static void FillSkySide( const int mins[2], const int maxs[2], float skyTexCoords[SKY_SUBDIVISIONS+1][SKY_SUBDIVISIONS+1][2] )
+static void DrawSkySide( struct image_s *image, const int mins[2], const int maxs[2] )
 {
-	const int vertexStart = tess.numVertexes;
-	const int tHeight = maxs[1] - mins[1] + 1;
-	const int sWidth = maxs[0] - mins[0] + 1;
 	int s, t;
 
-	if ( CullSkySide( mins, maxs ) )
-		return;
-
-#if ( (SKY_SUBDIVISIONS+1) * (SKY_SUBDIVISIONS+1) * 6 > SHADER_MAX_VERTEXES )
-	if ( tess.numVertexes + tHeight * sWidth > SHADER_MAX_VERTEXES )
-		ri.Error( ERR_DROP, "SHADER_MAX_VERTEXES hit in %s()", __func__ );
-#endif
-
-#if ( SKY_SUBDIVISIONS * SKY_SUBDIVISIONS * 6 * 6 > SHADER_MAX_INDEXES )
-	if ( tess.numIndexes + (tHeight - 1) * (sWidth - 1) * 6 > SHADER_MAX_INDEXES )
-		ri.Error( ERR_DROP, "SHADER_MAX_INDEXES hit in %s()", __func__ );
-#endif
+	GL_Bind( image );
 
-	for ( t = mins[1]+HALF_SKY_SUBDIVISIONS; t <= maxs[1]+HALF_SKY_SUBDIVISIONS; t++ )
+	for ( t = mins[1]+HALF_SKY_SUBDIVISIONS; t < maxs[1]+HALF_SKY_SUBDIVISIONS; t++ )
 	{
-		for ( s = mins[0]+HALF_SKY_SUBDIVISIONS; s <= maxs[0]+HALF_SKY_SUBDIVISIONS; s++ )
-		{
-			VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, tess.xyz[ tess.numVertexes ] );
-			tess.texCoords[0][tess.numVertexes][0] = skyTexCoords[t][s][0];
-			tess.texCoords[0][tess.numVertexes][1] = skyTexCoords[t][s][1];
-			tess.numVertexes++;
-		}
-	}
+		qglBegin( GL_TRIANGLE_STRIP );
 
-	for ( t = 0; t < tHeight-1; t++ )
-	{	
-		for ( s = 0; s < sWidth-1; s++ )
+		for ( s = mins[0]+HALF_SKY_SUBDIVISIONS; s <= maxs[0]+HALF_SKY_SUBDIVISIONS; s++ )
 		{
-			tess.indexes[tess.numIndexes] = vertexStart + s + t * ( sWidth );
-			tess.numIndexes++;
-			tess.indexes[tess.numIndexes] = vertexStart + s + ( t + 1 ) * ( sWidth );
-			tess.numIndexes++;
-			tess.indexes[tess.numIndexes] = vertexStart + s + 1 + t * ( sWidth );
-			tess.numIndexes++;
+			qglTexCoord2fv( s_skyTexCoords[t][s] );
+			qglVertex3fv( s_skyPoints[t][s] );
 
-			tess.indexes[tess.numIndexes] = vertexStart + s + ( t + 1 ) * ( sWidth );
-			tess.numIndexes++;
-			tess.indexes[tess.numIndexes] = vertexStart + s + 1 + ( t + 1 ) * ( sWidth );
-			tess.numIndexes++;
-			tess.indexes[tess.numIndexes] = vertexStart + s + 1 + t * ( sWidth );
-			tess.numIndexes++;
+			qglTexCoord2fv( s_skyTexCoords[t+1][s] );
+			qglVertex3fv( s_skyPoints[t+1][s] );
 		}
-	}
-}
-
-
-static void DrawSkySide( image_t *image, const int mins[2], const int maxs[2] )
-{
-	tess.numVertexes = 0;
-	tess.numIndexes = 0;
-
-	FillSkySide( mins, maxs, s_skyTexCoords );
-
-	if ( tess.numIndexes )
-	{
-		GL_Bind( image );
 
-		qglVertexPointer( 3, GL_FLOAT, 16, tess.xyz );
-		qglTexCoordPointer( 2, GL_FLOAT, 0, tess.texCoords[0] );
-
-		R_DrawElements( tess.numIndexes, tess.indexes );
-
-		tess.numVertexes = 0;
-		tess.numIndexes = 0;
+		qglEnd();
 	}
 }
 
-
-static void DrawSkyBox( const shader_t *shader )
+static void DrawSkyBox( shader_t *shader )
 {
 	int		i;
+
 	sky_min = 0;
 	sky_max = 1;
 
-	for ( i = 0; i < 6; i++ )
+	Com_Memset( s_skyTexCoords, 0, sizeof( s_skyTexCoords ) );
+
+	for (i=0 ; i<6 ; i++)
 	{
 		int sky_mins_subd[2], sky_maxs_subd[2];
 		int s, t;
@@ -484,7 +403,8 @@
 		sky_maxs[0][i] = ceil( sky_maxs[0][i] * HALF_SKY_SUBDIVISIONS ) / HALF_SKY_SUBDIVISIONS;
 		sky_maxs[1][i] = ceil( sky_maxs[1][i] * HALF_SKY_SUBDIVISIONS ) / HALF_SKY_SUBDIVISIONS;
 
-		if ( ( sky_mins[0][i] >= sky_maxs[0][i] ) || ( sky_mins[1][i] >= sky_maxs[1][i] ) )
+		if ( ( sky_mins[0][i] >= sky_maxs[0][i] ) ||
+			 ( sky_mins[1][i] >= sky_maxs[1][i] ) )
 		{
 			continue;
 		}
@@ -521,17 +441,70 @@
 			{
 				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
 							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
-							i,
+							i, 
+							s_skyTexCoords[t][s], 
 							s_skyPoints[t][s] );
 			}
 		}
 
-		DrawSkySide( shader->sky.outerbox[sky_texorder[i]], sky_mins_subd, sky_maxs_subd );
+		DrawSkySide( shader->sky.outerbox[sky_texorder[i]],
+			         sky_mins_subd,
+					 sky_maxs_subd );
 	}
+
 }
 
+static void FillCloudySkySide( const int mins[2], const int maxs[2], qboolean addIndexes )
+{
+	int s, t;
+	int vertexStart = tess.numVertexes;
+	int tHeight, sWidth;
+
+	tHeight = maxs[1] - mins[1] + 1;
+	sWidth = maxs[0] - mins[0] + 1;
+
+	for ( t = mins[1]+HALF_SKY_SUBDIVISIONS; t <= maxs[1]+HALF_SKY_SUBDIVISIONS; t++ )
+	{
+		for ( s = mins[0]+HALF_SKY_SUBDIVISIONS; s <= maxs[0]+HALF_SKY_SUBDIVISIONS; s++ )
+		{
+			VectorAdd( s_skyPoints[t][s], backEnd.viewParms.or.origin, tess.xyz[tess.numVertexes] );
+			tess.texCoords[tess.numVertexes][0][0] = s_skyTexCoords[t][s][0];
+			tess.texCoords[tess.numVertexes][0][1] = s_skyTexCoords[t][s][1];
+
+			tess.numVertexes++;
+
+			if ( tess.numVertexes >= SHADER_MAX_VERTEXES )
+			{
+				ri.Error( ERR_DROP, "SHADER_MAX_VERTEXES hit in FillCloudySkySide()\n" );
+			}
+		}
+	}
 
-static void FillCloudBox( void )
+	// only add indexes for one pass, otherwise it would draw multiple times for each pass
+	if ( addIndexes ) {
+		for ( t = 0; t < tHeight-1; t++ )
+		{	
+			for ( s = 0; s < sWidth-1; s++ )
+			{
+				tess.indexes[tess.numIndexes] = vertexStart + s + t * ( sWidth );
+				tess.numIndexes++;
+				tess.indexes[tess.numIndexes] = vertexStart + s + ( t + 1 ) * ( sWidth );
+				tess.numIndexes++;
+				tess.indexes[tess.numIndexes] = vertexStart + s + 1 + t * ( sWidth );
+				tess.numIndexes++;
+
+				tess.indexes[tess.numIndexes] = vertexStart + s + ( t + 1 ) * ( sWidth );
+				tess.numIndexes++;
+				tess.indexes[tess.numIndexes] = vertexStart + s + 1 + ( t + 1 ) * ( sWidth );
+				tess.numIndexes++;
+				tess.indexes[tess.numIndexes] = vertexStart + s + 1 + t * ( sWidth );
+				tess.numIndexes++;
+			}
+		}
+	}
+}
+
+static void FillCloudBox( const shader_t *shader, int stage )
 {
 	int i;
 
@@ -613,24 +586,31 @@
 				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
 							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
 							i, 
+							NULL,
 							s_skyPoints[t][s] );
+
+				s_skyTexCoords[t][s][0] = s_cloudTexCoords[i][t][s][0];
+				s_skyTexCoords[t][s][1] = s_cloudTexCoords[i][t][s][1];
 			}
 		}
 
-		FillSkySide( sky_mins_subd, sky_maxs_subd, s_cloudTexCoords[i] );
+		// only add indexes for first stage
+		FillCloudySkySide( sky_mins_subd, sky_maxs_subd, ( stage == 0 ) );
 	}
 }
 
-
 /*
 ** R_BuildCloudData
 */
-static void R_BuildCloudData( const shaderCommands_t *input )
+void R_BuildCloudData( shaderCommands_t *input )
 {
-	const shader_t *shader;
+	int			i;
+	shader_t	*shader;
 
 	shader = input->shader;
 
+	assert( shader->isSky );
+
 	sky_min = 1.0 / 256.0f;		// FIXME: not correct?
 	sky_max = 255.0 / 256.0f;
 
@@ -638,61 +618,23 @@
 	tess.numIndexes = 0;
 	tess.numVertexes = 0;
 
-	if ( shader->sky.cloudHeight )
+	if ( input->shader->sky.cloudHeight )
 	{
-		if ( tess.xstages[0] )
+		for ( i = 0; i < MAX_SHADER_STAGES; i++ )
 		{
-			FillCloudBox();
-		}
-	}
-}
-
-
-static void BuildSkyTexCoords( void )
-{
-	float s, t;
-	int i, j;
-
-	for ( i = 0; i <= SKY_SUBDIVISIONS; i++ ) {
-		for ( j = 0; j <= SKY_SUBDIVISIONS; j++ ) {
-			s = ( j - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS;
-			t = ( i - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS;
-
-			// avoid bilerp seam
-			s = (s+1)*0.5;
-			t = (t+1)*0.5;
-
-			if ( s < 0.0f )
-			{
-				s = 0.0f;
-			}
-			else if ( s > 1.0f )
-			{
-				s = 1.0f;
-			}
-
-			if ( t < 0.0f )
-			{
-				t = 0.0f;
-			}
-			else if ( t > 1.0f )
-			{
-				t = 1.0f;
+			if ( !tess.xstages[i] ) {
+				break;
 			}
-
-			t = 1.0f - t;
-
-			s_skyTexCoords[i][j][0] = s;
-			s_skyTexCoords[i][j][1] = t;
+			FillCloudBox( input->shader, i );
 		}
 	}
 }
 
-
 /*
 ** R_InitSkyTexCoords
 ** Called when a sky shader is parsed
 */
+#define SQR( a ) ((a)*(a))
 void R_InitSkyTexCoords( float heightCloud )
 {
 	int i, s, t;
@@ -702,13 +644,6 @@
 	vec3_t skyVec;
 	vec3_t v;
 
-	if ( !Q_stricmp( glConfig.renderer_string, "GDI Generic" ) && !Q_stricmp( glConfig.version_string, "1.1.0" ) ) {
-		// fix skybox rendering on MS software GL implementation
-		sky_min_depth = 0.999f;
-	} else {
-		sky_min_depth = 1.0;
-	}
-
 	// init zfar so MakeSkyVec works even though
 	// a world hasn't been bounded
 	backEnd.viewParms.zFar = 1024;
@@ -722,19 +657,22 @@
 				// compute vector from view origin to sky side integral point
 				MakeSkyVec( ( s - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
 							( t - HALF_SKY_SUBDIVISIONS ) / ( float ) HALF_SKY_SUBDIVISIONS, 
-							i,
+							i, 
+							NULL,
 							skyVec );
 
 				// compute parametric value 'p' that intersects with cloud layer
 				p = ( 1.0f / ( 2 * DotProduct( skyVec, skyVec ) ) ) *
 					( -2 * skyVec[2] * radiusWorld + 
-						2 * sqrt( Square( skyVec[2] ) * Square( radiusWorld ) + 
-							2 * Square( skyVec[0] ) * radiusWorld * heightCloud +
-							Square( skyVec[0] ) * Square( heightCloud ) + 
-							2 * Square( skyVec[1] ) * radiusWorld * heightCloud +
-							Square( skyVec[1] ) * Square( heightCloud ) + 
-							2 * Square( skyVec[2] ) * radiusWorld * heightCloud +
-							Square( skyVec[2] ) * Square( heightCloud ) ) );
+					   2 * sqrt( SQR( skyVec[2] ) * SQR( radiusWorld ) + 
+					             2 * SQR( skyVec[0] ) * radiusWorld * heightCloud +
+								 SQR( skyVec[0] ) * SQR( heightCloud ) + 
+								 2 * SQR( skyVec[1] ) * radiusWorld * heightCloud +
+								 SQR( skyVec[1] ) * SQR( heightCloud ) + 
+								 2 * SQR( skyVec[2] ) * radiusWorld * heightCloud +
+								 SQR( skyVec[2] ) * SQR( heightCloud ) ) );
+
+				s_cloudTexP[i][t][s] = p;
 
 				// compute intersection point based on p
 				VectorScale( skyVec, p, v );
@@ -751,8 +689,6 @@
 			}
 		}
 	}
-
-	BuildSkyTexCoords();
 }
 
 //======================================================================================
@@ -760,23 +696,25 @@
 /*
 ** RB_DrawSun
 */
-void RB_DrawSun( float scale, shader_t *shader ) {
+void RB_DrawSun( void ) {
 	float		size;
 	float		dist;
 	vec3_t		origin, vec1, vec2;
-	color4ub_t	sunColor;
+	vec3_t		temp;
 
-	if ( !backEnd.skyRenderedThisView )
+	if ( !backEnd.skyRenderedThisView ) {
 		return;
-
-	sunColor.u32 = ~0U;
-
+	}
+	if ( !r_drawSun->integer ) {
+		return;
+	}
 	qglLoadMatrixf( backEnd.viewParms.world.modelMatrix );
+	qglTranslatef (backEnd.viewParms.or.origin[0], backEnd.viewParms.or.origin[1], backEnd.viewParms.or.origin[2]);
 
-	dist = backEnd.viewParms.zFar / 1.75;		// div sqrt(3)
-	size = dist * scale;
+	dist = 	backEnd.viewParms.zFar / 1.75;		// div sqrt(3)
+	size = dist * 0.4;
 
-	VectorMA( backEnd.viewParms.or.origin, dist, tr.sunDirection, origin );
+	VectorScale( tr.sunDirection, dist, origin );
 	PerpendicularVector( vec1, tr.sunDirection );
 	CrossProduct( tr.sunDirection, vec1, vec2 );
 
@@ -784,11 +722,60 @@
 	VectorScale( vec2, size, vec2 );
 
 	// farthest depth range
-	qglDepthRange( sky_min_depth, 1.0 );
+	qglDepthRange( 1.0, 1.0 );
 
-	RB_BeginSurface( shader, 0 );
-
-	RB_AddQuadStamp( origin, vec1, vec2, sunColor );
+	// FIXME: use quad stamp
+	RB_BeginSurface( tr.sunShader, tess.fogNum );
+		VectorCopy( origin, temp );
+		VectorSubtract( temp, vec1, temp );
+		VectorSubtract( temp, vec2, temp );
+		VectorCopy( temp, tess.xyz[tess.numVertexes] );
+		tess.texCoords[tess.numVertexes][0][0] = 0;
+		tess.texCoords[tess.numVertexes][0][1] = 0;
+		tess.vertexColors[tess.numVertexes][0] = 255;
+		tess.vertexColors[tess.numVertexes][1] = 255;
+		tess.vertexColors[tess.numVertexes][2] = 255;
+		tess.numVertexes++;
+
+		VectorCopy( origin, temp );
+		VectorAdd( temp, vec1, temp );
+		VectorSubtract( temp, vec2, temp );
+		VectorCopy( temp, tess.xyz[tess.numVertexes] );
+		tess.texCoords[tess.numVertexes][0][0] = 0;
+		tess.texCoords[tess.numVertexes][0][1] = 1;
+		tess.vertexColors[tess.numVertexes][0] = 255;
+		tess.vertexColors[tess.numVertexes][1] = 255;
+		tess.vertexColors[tess.numVertexes][2] = 255;
+		tess.numVertexes++;
+
+		VectorCopy( origin, temp );
+		VectorAdd( temp, vec1, temp );
+		VectorAdd( temp, vec2, temp );
+		VectorCopy( temp, tess.xyz[tess.numVertexes] );
+		tess.texCoords[tess.numVertexes][0][0] = 1;
+		tess.texCoords[tess.numVertexes][0][1] = 1;
+		tess.vertexColors[tess.numVertexes][0] = 255;
+		tess.vertexColors[tess.numVertexes][1] = 255;
+		tess.vertexColors[tess.numVertexes][2] = 255;
+		tess.numVertexes++;
+
+		VectorCopy( origin, temp );
+		VectorSubtract( temp, vec1, temp );
+		VectorAdd( temp, vec2, temp );
+		VectorCopy( temp, tess.xyz[tess.numVertexes] );
+		tess.texCoords[tess.numVertexes][0][0] = 1;
+		tess.texCoords[tess.numVertexes][0][1] = 0;
+		tess.vertexColors[tess.numVertexes][0] = 255;
+		tess.vertexColors[tess.numVertexes][1] = 255;
+		tess.vertexColors[tess.numVertexes][2] = 255;
+		tess.numVertexes++;
+
+		tess.indexes[tess.numIndexes++] = 0;
+		tess.indexes[tess.numIndexes++] = 1;
+		tess.indexes[tess.numIndexes++] = 2;
+		tess.indexes[tess.numIndexes++] = 0;
+		tess.indexes[tess.numIndexes++] = 2;
+		tess.indexes[tess.numIndexes++] = 3;
 
 	RB_EndSurface();
 
@@ -797,6 +784,8 @@
 }
 
 
+
+
 /*
 ================
 RB_StageIteratorSky
@@ -807,24 +796,10 @@
 ================
 */
 void RB_StageIteratorSky( void ) {
-
-#ifdef USE_PMLIGHT
-#ifdef USE_LEGACY_DLIGHTS
-	if ( R_GetDlightMode() )
-#endif 
-	{
-		GL_ProgramDisable();
-	}
-#endif // USE_PMLIGHT
-
 	if ( r_fastsky->integer ) {
 		return;
 	}
 
-#ifdef USE_VBO
-	VBO_UnBind();
-#endif
-
 	// go through all the polygons and project them onto
 	// the sky box to see which blocks on each side need
 	// to be drawn
@@ -836,31 +811,30 @@
 	if ( r_showsky->integer ) {
 		qglDepthRange( 0.0, 0.0 );
 	} else {
-		qglDepthRange( sky_min_depth, 1.0 );
+		qglDepthRange( 1.0, 1.0 );
 	}
 
 	// draw the outer skybox
 	if ( tess.shader->sky.outerbox[0] && tess.shader->sky.outerbox[0] != tr.defaultImage ) {
-
-		GL_ClientState( 1, CLS_NONE );
-		GL_ClientState( 0, CLS_TEXCOORD_ARRAY );
-
-		qglColor4f( tr.identityLight, tr.identityLight, tr.identityLight, 1.0 );
-
+		qglColor3f( tr.identityLight, tr.identityLight, tr.identityLight );
+		
+		qglPushMatrix ();
 		GL_State( 0 );
-		GL_Cull( CT_FRONT_SIDED );
+		qglTranslatef (backEnd.viewParms.or.origin[0], backEnd.viewParms.or.origin[1], backEnd.viewParms.or.origin[2]);
 
 		DrawSkyBox( tess.shader );
+
+		qglPopMatrix();
 	}
 
 	// generate the vertexes for all the clouds, which will be drawn
 	// by the generic shader routine
 	R_BuildCloudData( &tess );
 
+	RB_StageIteratorGeneric();
+
 	// draw the inner skybox
-	if ( tess.numVertexes ) {
-		RB_StageIteratorGeneric();
-	}
+
 
 	// back to normal depth range
 	qglDepthRange( 0.0, 1.0 );
@@ -868,3 +842,4 @@
 	// note that sky was drawn so we will draw a sun later
 	backEnd.skyRenderedThisView = qtrue;
 }
+

```
