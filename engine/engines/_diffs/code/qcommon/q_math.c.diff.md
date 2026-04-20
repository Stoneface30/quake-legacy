# Diff: `code/qcommon/q_math.c`
**Canonical:** `wolfcamql-src` (sha256 `95b638eab964...`, 35291 bytes)

## Variants

### `ioquake3`  — sha256 `b026df2cca9c...`, 25707 bytes

_Diff stat: +28 / -434 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_math.c	2026-04-16 20:02:25.225256200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\q_math.c	2026-04-16 20:02:21.570109000 +0100
@@ -39,32 +39,21 @@
 	{0.0f, 0.0f, 1.0f}
 };
 
-vec4_t	g_color_table[8] =
-	{
-	{0.0f, 0.0f, 0.0f, 1.0f},
-	{0.996f, 0.0f, 0.0f, 1.0f},  // fe0000
-	{0.0f, 0.996f, 0.0f, 1.0f},  // 00fe00
-	{0.996f, 0.996f, 0.0f, 1.0f},  // fefe00
-	{0.196f, 0.4f, 0.996f, 1.0f},  // 3266fe
-	{0.0f, 0.996f, 0.996f, 1.0f},  // 00fefe
-	{0.996f, 0.0f, 0.996f, 1.0f},  // fe00fe
-	{0.996f, 0.996f, 0.996f, 1.0f},  // fefefe
-	};
 
-vec4_t	g_color_table_ql[8] =
-	{
-	{0.0f, 0.0f, 0.0f, 1.0f},
-	{0.996f, 0.0f, 0.0f, 1.0f},  // fe0000
-	{0.0f, 0.996f, 0.0f, 1.0f},  // 00fe00
-	{0.996f, 0.996f, 0.0f, 1.0f},  // fefe00
-	{0.196f, 0.4f, 0.996f, 1.0f},  // 3266fe
-	{0.0f, 0.996f, 0.996f, 1.0f},  // 00fefe
-	{0.996f, 0.0f, 0.996f, 1.0f},  // fe00fe
-	{0.996f, 0.996f, 0.996f, 1.0f},  // fefefe
-	};
+vec4_t	colorBlack  = {0.0f,  0.0f,  0.0f,  1.0f};
+vec4_t	colorRed    = {1.0f,  0.0f,  0.0f,  1.0f};
+vec4_t	colorGreen  = {0.0f,  1.0f,  0.0f,  1.0f};
+vec4_t	colorBlue   = {0.0f,  0.0f,  1.0f,  1.0f};
+vec4_t	colorYellow = {1.0f,  1.0f,  0.0f,  1.0f};
+vec4_t	colorMagenta= {1.0f,  0.0f,  1.0f,  1.0f};
+vec4_t	colorCyan   = {0.0f,  1.0f,  1.0f,  1.0f};
+vec4_t	colorWhite  = {1.0f,  1.0f,  1.0f,  1.0f};
+vec4_t	colorLtGrey = {0.75f, 0.75f, 0.75f, 1.0f};
+vec4_t	colorMdGrey = {0.5f,  0.5f,  0.5f,  1.0f};
+vec4_t	colorDkGrey = {0.25f, 0.25f, 0.25f, 1.0f};
 
-vec4_t	g_color_table_q3[8] =
-	{
+vec4_t	g_color_table[8] =
+{
 	{0.0f, 0.0f, 0.0f, 1.0f},
 	{1.0f, 0.0f, 0.0f, 1.0f},
 	{0.0f, 1.0f, 0.0f, 1.0f},
@@ -73,115 +62,8 @@
 	{0.0f, 1.0f, 1.0f, 1.0f},
 	{1.0f, 0.0f, 1.0f, 1.0f},
 	{1.0f, 1.0f, 1.0f, 1.0f},
-	};
-
-vec4_t		colorBlack	= {0.0f, 0.0f, 0.0f, 1.0f};
-vec4_t		colorRed	= { 0.96f, 0.0f, 0.0f, 1.0f };  //{1, 0, 0, 1};
-vec4_t		colorGreen	= { 0.0f, 0.96f, 0.0f, 1.0f };  //{0, 1, 0, 1};
-vec4_t		colorBlue	= { 0.196f, 0.4f, 0.96f, 1.0f };  //{0, 0, 1, 1};
-vec4_t		colorYellow	= { 0.96f, 0.96f, 0.0f, 1.0f };  //{1, 1, 0, 1};
-vec4_t		colorMagenta= { 0.96f, 0.0f, 0.96f, 1.0f };  //{1, 0, 1, 1};
-vec4_t		colorCyan	= { 0.0f, 0.96f, 0.96f, 1.0f };  //{0, 1, 1, 1};
-vec4_t		colorWhite	= { 0.96f, 0.96f, 0.96f, 1.0f };  //{1, 1, 1, 1};
-
-vec4_t		colorLtGrey	= {0.75f, 0.75f, 0.75f, 1.0f};
-vec4_t		colorMdGrey	= {0.5f, 0.5f, 0.5f, 1.0f};
-vec4_t		colorDkGrey	= {0.25f, 0.25f, 0.25f, 1.0f};
-
-
-vec4_t		qlcolorRed	= { 0.96f, 0.0f, 0.0f, 1.0f };  //{1, 0, 0, 1};
-vec4_t		qlcolorGreen	= { 0.0f, 0.96f, 0.0f, 1.0f };  //{0, 1, 0, 1};
-vec4_t		qlcolorBlue	= { 0.196f, 0.4f, 0.96f, 1.0f };  //{0, 0, 1, 1};
-vec4_t		qlcolorYellow	= { 0.96f, 0.96f, 0.0f, 1.0f };  //{1, 1, 0, 1};
-vec4_t		qlcolorMagenta= { 0.96f, 0.0f, 0.96f, 1.0f };  //{1, 0, 1, 1};
-vec4_t		qlcolorCyan	= { 0.0f, 0.96f, 0.96f, 1.0f };  //{0, 1, 1, 1};
-vec4_t		qlcolorWhite	= { 0.96f, 0.96f, 0.96f, 1.0f };  //{1, 1, 1, 1};
-
-vec4_t		q3colorRed	= {1.0f, 0.0f, 0.0f, 1.0f};
-vec4_t		q3colorGreen	= {0.0f, 1.0f, 0.0f, 1.0f};
-vec4_t		q3colorBlue	= {0.0f, 0.0f, 1.0f, 1.0f};
-vec4_t		q3colorYellow	= {1.0f, 1.0f, 0.0f, 1.0f};
-vec4_t		q3colorMagenta= {1.0f, 0.0f, 1.0f, 1.0f};
-vec4_t		q3colorCyan	= {0.0f, 1.0f, 1.0f, 1.0f};
-vec4_t		q3colorWhite	=  {1.0f, 1.0f, 1.0f, 1.0f};
-
-void Q_SetColors (qboolean ql)
-{
-	int i;
-
-	if (ql) {
-		Vector4Copy(qlcolorRed, colorRed);
-		Vector4Copy(qlcolorGreen, colorGreen);
-		Vector4Copy(qlcolorBlue, colorBlue);
-		Vector4Copy(qlcolorYellow, colorYellow);
-		Vector4Copy(qlcolorMagenta, colorMagenta);
-		Vector4Copy(qlcolorCyan, colorCyan);
-		Vector4Copy(qlcolorWhite, colorWhite);
-		for (i = 0;  i < 8;  i++) {
-			Vector4Copy(g_color_table_ql[i], g_color_table[i]);
-		}
-	} else {
-		Vector4Copy(q3colorRed, colorRed);
-		Vector4Copy(q3colorGreen, colorGreen);
-		Vector4Copy(q3colorBlue, colorBlue);
-		Vector4Copy(q3colorYellow, colorYellow);
-		Vector4Copy(q3colorMagenta, colorMagenta);
-		Vector4Copy(q3colorCyan, colorCyan);
-		Vector4Copy(q3colorWhite, colorWhite);
-		for (i = 0;  i < 8;  i++) {
-			Vector4Copy(g_color_table_q3[i], g_color_table[i]);
-		}
-	}
-
-	Vector4Set(colorLtGrey, 0.75f, 0.75f, 0.75f, 1.0f);
-	Vector4Set(colorMdGrey, 0.5f, 0.5f, 0.5f, 1.0f);
-	Vector4Set(colorDkGrey, 0.25f, 0.25f, 0.25f, 1.0f);
-}
-
-void Q_SetColorTable (int n, float r, float g, float b, float a)
-{
-	if (n > 10) {
-		Com_Printf("Q_SetColorTable() invalid index '%d'\n", n);
-	}
+};
 
-	if (n == 8) {
-		Vector4Set(colorLtGrey, r, g, b, a);
-	} else if (n == 9) {
-		Vector4Set(colorMdGrey, r, g, b, a);
-	} else if (n == 10) {
-		Vector4Set(colorDkGrey, r, g, b, a);
-	} else {
-		Vector4Set(g_color_table[n], r, g, b, a);
-		switch (n) {
-		case 0:
-			Vector4Set(colorBlack, r, g, b, a);
-			break;
-		case 1:
-			Vector4Set(colorRed, r, g, b, a);
-			break;
-		case 2:
-			Vector4Set(colorGreen, r, g, b, a);
-			break;
-		case 3:
-			Vector4Set(colorYellow, r, g, b, a);
-			break;
-		case 4:
-			Vector4Set(colorBlue, r, g, b, a);
-			break;
-		case 5:
-			Vector4Set(colorCyan, r, g, b, a);
-			break;
-		case 6:
-			Vector4Set(colorMagenta, r, g, b, a);
-			break;
-		case 7:
-			Vector4Set(colorWhite, r, g, b, a);
-			break;
-		default:
-			break;
-		}
-	}
-}
 
 vec3_t	bytedirs[NUMVERTEXNORMALS] =
 {
@@ -340,7 +222,7 @@
 
 
 unsigned ColorBytes3 (float r, float g, float b) {
-	unsigned	i = 0;
+	unsigned	i;
 
 	( (byte *)&i )[0] = r * 255;
 	( (byte *)&i )[1] = g * 255;
@@ -350,7 +232,7 @@
 }
 
 unsigned ColorBytes4 (float r, float g, float b, float a) {
-	unsigned	i = 0;
+	unsigned	i;
 
 	( (byte *)&i )[0] = r * 255;
 	( (byte *)&i )[1] = g * 255;
@@ -362,7 +244,7 @@
 
 float NormalizeColor( const vec3_t in, vec3_t out ) {
 	float	max;
-
+	
 	max = in[0];
 	if ( in[1] > max ) {
 		max = in[1];
@@ -474,7 +356,7 @@
 */
 void RotateAroundDirection( vec3_t axis[3], float yaw ) {
 
-	// create an arbitrary axis[1]
+	// create an arbitrary axis[1] 
 	PerpendicularVector( axis[1], axis[0] );
 
 	// rotate it around axis[0] by yaw
@@ -494,7 +376,7 @@
 void vectoangles( const vec3_t value1, vec3_t angles ) {
 	float	forward;
 	float	yaw, pitch;
-
+	
 	if ( value1[1] == 0 && value1[0] == 0 ) {
 		yaw = 0;
 		if ( value1[2] > 0 ) {
@@ -503,7 +385,6 @@
 		else {
 			pitch = 270;
 		}
-		//Com_Printf("pitch %f\n", pitch);
 	}
 	else {
 		if ( value1[0] ) {
@@ -563,15 +444,6 @@
 	VectorCopy( in[2], out[2] );
 }
 
-void ProjectPointOntoVector (vec3_t point, vec3_t vStart, vec3_t vDir, vec3_t vProj)
-{
-	vec3_t pVec;
-
-	VectorSubtract( point, vStart, pVec );
-	// project onto the directional vector for this segment
-	VectorMA( vStart, DotProduct( pVec, vDir ), vDir, vProj );
-}
-
 void ProjectPointOnPlane( vec3_t dst, const vec3_t p, const vec3_t normal )
 {
 	float d;
@@ -580,15 +452,7 @@
 
 	inv_denom =  DotProduct( normal, normal );
 #ifndef Q3_VM
-	//FIXME some quakelive demos trigger this assert, don't just bail out
-	if (Q_fabs(inv_denom) == 0.0f) {
-		Com_Printf("ProjectPointOnPlane:  inv_denom == 0.0  (%f %f %f)\n", normal[0], normal[1], normal[2]);
-		//* ( int * ) 0 = 0x12345678;
-		//inv_denom = 0.001f;
-		return;
-	}
-	//assert( Q_fabs(inv_denom) != 0.0f ); // zero vectors get here
-
+	assert( Q_fabs(inv_denom) != 0.0f ); // zero vectors get here
 #endif
 	inv_denom = 1.0f / inv_denom;
 
@@ -603,22 +467,6 @@
 	dst[2] = p[2] - d * n[2];
 }
 
-void PointToPlane (vec3_t dst, const vec3_t point, const vec3_t planePoint, const vec3_t normal)
-{
-	vec3_t pv;
-	float d, nm, denom;
-
-	VectorSubtract(point, planePoint, pv);
-	nm = -DotProduct(normal, pv);
-	denom = DotProduct(normal, normal);
-	if (Q_fabs(denom) == 0.0) {
-		Com_Printf("PointToPlane() divide by zero\n");
-		return;
-	}
-	d = nm / denom;
-	VectorMA(point, d, normal, dst);
-}
-
 /*
 ================
 MakeNormalVectors
@@ -650,30 +498,6 @@
 	out[2] = DotProduct( in, matrix[2] );
 }
 
-float VectorGetScale (vec3_t v, vec3_t norm)
-{
-	float s = 0;
-
-	if (norm[0]) {
-		s = v[0] / norm[0];
-		//Com_Printf("0 %f  %f\n", s, v[0]);
-	}
-	if (norm[1]) {
-		s = v[1] / norm[1];
-		//Com_Printf("1 %f  %f\n", s, v[1]);
-	}
-	if (norm[2]) {
-		s = v[2] / norm[2];
-		//Com_Printf("2 %f  %f\n", s, v[2]);
-	}
-
-	if (s == 0.0) {
-		//Com_Printf("^3VectorGetScale %f\n", s);
-	}
-
-	return s;
-}
-
 //============================================================================
 
 #if !idppc
@@ -713,7 +537,7 @@
 ===============
 */
 float LerpAngle (float from, float to, float frac) {
-	float a;
+	float	a;
 
 	if ( to - from > 180 ) {
 		to -= 360;
@@ -726,110 +550,6 @@
 	return a;
 }
 
-// can be used with playerState angles
-float LerpAngleNear (float from, float to, float frac)
-{
-	float a;
-	float dist;
-#if 0
-	static float fromOrig = 0;
-	static float toOrig = 0;
-	static int count = 0;
-#endif
-
-
-#if 0
-	count++;
-
-	if (from != fromOrig) {
-		Com_Printf("^5%d from %f  frac %f\n", count, from, frac);
-	}
-	if (to != toOrig) {
-		Com_Printf("^5%d to %f  frac %f\n", count, to, frac);
-	}
-
-
-	fromOrig = from;
-	toOrig = to;
-
-#endif
-
-	if (Q_floatIsNan(from)  ||  Q_floatIsNan(to)) {
-		Com_Printf("^3LerpAngleNear invalid angle: %f %f\n", from, to);
-		return from;
-	}
-
-	while (from > 180) {
-		from -= 360;
-	}
-	while (from < -180) {
-		from += 360;
-	}
-
-	while (to > 180) {
-		to -= 360;
-	}
-	while (to < -180) {
-		to += 360;
-	}
-
-	if (to < -180  ||  to > 180) {
-		Com_Printf("^3to wtf %f\n", to);
-	}
-	if (from < -180  ||  from > 180) {
-		Com_Printf("^3from wtf %f\n", from);
-	}
-
-	// angles are between -180 and 180
-
-	//           -90
-	// -180/180          0
-	//            90
-
-	if ((from <= 0  &&  to <= 0)  ||  (from >= 0  &&  to >= 0)) {
-		dist = to - from;
-	} else {  // different signs
-		float clockWiseDist = 0;
-		float counterDist = 0;
-
-		// try clockwise distance first
-		if (from >= 0) {
-			clockWiseDist = (180 - from);
-			clockWiseDist += (to + 180);
-
-			counterDist = from;
-			counterDist += -to;
-		} else {  // from < 0
-			clockWiseDist = -from;
-			clockWiseDist += to;
-
-			counterDist = -(-180 - from);
-			counterDist += (180 - to);
-		}
-
-		if (clockWiseDist > counterDist) {
-			dist = -counterDist;
-		} else {
-			dist = clockWiseDist;
-		}
-	}
-
-	//a = from + frac * (to - from);
-	a = from + frac * dist;
-
-	//Com_Printf("%f (orig %f)  -> %f (orig %f) frac %f  %f\n", from, fromOrig, to, toOrig, frac, a);
-
-	//a = 0;
-
-	return a;
-}
-
-// q3mme camera
-void LerpAngles( const vec3_t from, const vec3_t to, vec3_t out, float lerp ) {
-	out[0] = LerpAngle( from[0], to[0], lerp );
-	out[1] = LerpAngle( from[1], to[1], lerp );
-	out[2] = LerpAngle( from[2], to[2], lerp );
-}
 
 /*
 =================
@@ -839,7 +559,7 @@
 =================
 */
 float	AngleSubtract( float a1, float a2 ) {
-	float a;
+	float	a;
 
 	a = a1 - a2;
 	while ( a > 180 ) {
@@ -852,25 +572,12 @@
 }
 
 
-void AnglesSubtract( const vec3_t v1, const vec3_t v2, vec3_t v3 ) {
+void AnglesSubtract( vec3_t v1, vec3_t v2, vec3_t v3 ) {
 	v3[0] = AngleSubtract( v1[0], v2[0] );
 	v3[1] = AngleSubtract( v1[1], v2[1] );
 	v3[2] = AngleSubtract( v1[2], v2[2] );
 }
 
-float AngleAdd (float a1, float a2)
-{
-	float a;
-
-	a = a1 + a2;
-	while ( a > 180 ) {
-		a -= 360;
-	}
-	while ( a < -180 ) {
-		a += 360;
-	}
-	return a;
-}
 
 float	AngleMod(float a) {
 	a = (360.0/65536) * ((int)(a*(65536/360.0)) & 65535);
@@ -1080,8 +787,6 @@
 	return qtrue;
 }
 
-#if 1  //def Q3_VM
-
 vec_t VectorNormalize( vec3_t v ) {
 	// NOTE: TTimo - Apple G4 altivec source uses double?
 	float	length, ilength;
@@ -1097,40 +802,10 @@
 		v[1] *= ilength;
 		v[2] *= ilength;
 	}
-
+		
 	return length;
 }
 
-#else
-
-vec_t VectorNormalize( vec3_t v ) {
-	// NOTE: TTimo - Apple G4 altivec source uses double?
-	float	length, ilength;
-	int c;
-
-	length = v[0]*v[0] + v[1]*v[1] + v[2]*v[2];
-
-	c = fpclassify(length);
-
-	//if (c == FP_NORMAL) {
-	if (c != FP_NAN) {
-		/* writing it this way allows gcc to recognize that rsqrt can be used */
-		ilength = 1/(float)sqrt (length);
-		/* sqrt(length) = length * (1 / sqrt(length)) */
-		length *= ilength;
-		v[0] *= ilength;
-		v[1] *= ilength;
-		v[2] *= ilength;
-	} else {
-		Com_Printf("%s invalid length fp type %d  (%f %f %f)\n", __FUNCTION__, c, v[0], v[1], v[2]);
-		assert(0);
-	}
-
-	return length;
-}
-
-#endif
-
 vec_t VectorNormalize2( const vec3_t v, vec3_t out) {
 	float	length, ilength;
 
@@ -1148,7 +823,7 @@
 	} else {
 		VectorClear( out );
 	}
-
+		
 	return length;
 
 }
@@ -1195,17 +870,6 @@
 	out[3] = in[3]*scale;
 }
 
-float AngleBetweenVectors (const vec3_t v1, const vec3_t v2)
-{
-	vec3_t n1, n2;
-
-	VectorCopy(v1, n1);
-	VectorCopy(v2, n2);
-	VectorNormalize(n1);
-	VectorNormalize(n2);
-
-	return acos(DotProduct(n1, n2));
-}
 
 int Q_log2( int val ) {
 	int answer;
@@ -1232,7 +896,7 @@
 		return PLANE_Y;
 	if ( normal[2] == 1.0 )
 		return PLANE_Z;
-
+	
 	return PLANE_NON_AXIAL;
 }
 */
@@ -1315,9 +979,6 @@
 	*/
 	for ( pos = 0, i = 0; i < 3; i++ )
 	{
-		if (src[i] > 1.0) {
-			Com_Printf(S_COLOR_YELLOW "PerpendicularVector() src[%d] %f\n", i, src[i]);
-		}
 		if ( fabs( src[i] ) < minelem )
 		{
 			pos = i;
@@ -1327,7 +988,6 @@
 	tempvec[0] = tempvec[1] = tempvec[2] = 0.0F;
 	tempvec[pos] = 1.0F;
 
-	//Com_Printf("pos %d (%f %f %f)\n", pos, tempvec[0], tempvec[1], tempvec[2]);
 	/*
 	** project the point onto the plane defined by src
 	*/
@@ -1339,73 +999,14 @@
 	VectorNormalize( dst );
 }
 
-void VectorStartEndDir (const vec3_t start, const vec3_t end, vec3_t dir)
-{
-	VectorSubtract(end, start, dir);
-}
-
-qboolean VectorCheck (const vec3_t v)
-{
-	qboolean valid = qtrue;
-
-#ifdef Q3_VM
-
-	if (IS_NAN(v[0])) {
-		valid = qfalse;
-	} else if (IS_NAN(v[1])) {
-		valid = qfalse;
-	} else if (IS_NAN(v[2])) {
-		valid = qfalse;
-	}
-
-#else
-
-	if (isnan(v[0])) {
-		valid = qfalse;
-	} else if (isnan(v[1])) {
-		valid = qfalse;
-	} else if (isnan(v[2])) {
-		valid = qfalse;
-	}
-
-#endif
-
-	if (!valid) {
-		Crash();
-	}
-
-	return valid;
-}
-
-void VectorReflect (const vec3_t src, const vec3_t reflectNorm, vec3_t reflected)
-{
-	//vec3_t srcNorm;
-	vec3_t planeNorm;
-	float dot;
-
-	//VectorCheck(src);
-	//VectorCheck(reflectNorm);
-
-	//VectorCopy(src, srcNorm);
-	//VectorNormalize(srcNorm);
-
-	VectorCopy(reflectNorm, planeNorm);
-	VectorNormalize(planeNorm);
-
-	//dot = DotProduct(srcNorm, planeNorm);
-	dot = DotProduct(src, planeNorm);
-	//VectorMA(srcNorm, -2.0 * dot, planeNorm, reflected);
-	VectorMA(src, -2.0 * dot, planeNorm, reflected);
-}
-
 /*
 ================
-Q_floatIsNan
+Q_isnan
 
 Don't pass doubles to this
 ================
 */
-int Q_floatIsNan (float x)
+int Q_isnan( float x )
 {
 	floatint_t fi;
 
@@ -1444,10 +1045,3 @@
 	return angle;
 }
 #endif
-
-#ifdef Q3_VM
-float Q_fmodf (float x, float y)
-{
-	return (x - y * floor(x / y));
-}
-#endif

```

### `quake3e`  — sha256 `a6933c8fbfa3...`, 28893 bytes

_Diff stat: +207 / -490 lines_

_(full diff is 22576 bytes — see files directly)_

### `openarena-engine`  — sha256 `1899ac5c0628...`, 29533 bytes

_Diff stat: +175 / -452 lines_

_(full diff is 20160 bytes — see files directly)_

### `openarena-gamecode`  — sha256 `e2d3477d3685...`, 31188 bytes

_Diff stat: +374 / -511 lines_

_(full diff is 24704 bytes — see files directly)_
