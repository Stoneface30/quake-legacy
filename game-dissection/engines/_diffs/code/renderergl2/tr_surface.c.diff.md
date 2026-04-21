# Diff: `code/renderergl2/tr_surface.c`
**Canonical:** `wolfcamql-src` (sha256 `9747faa0a942...`, 43693 bytes)

## Variants

### `ioquake3`  — sha256 `3dc0d275243e...`, 35924 bytes

_Diff stat: +7 / -302 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_surface.c	2026-04-16 20:02:25.264766300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_surface.c	2026-04-16 20:02:21.616761100 +0100
@@ -167,18 +167,6 @@
 	RB_AddQuadStampExt( origin, left, up, color, 0, 0, 1, 1 );
 }
 
-static void RB_AddQuadStampByteColor ( vec3_t origin, vec3_t left, vec3_t up, byte bcolor[4] ) {
-	vec4_t color;
-
-	color[0] = (float)bcolor[0] / 255.0f;
-	color[1] = (float)bcolor[1] / 255.0f;
-	color[2] = (float)bcolor[2] / 255.0f;
-	color[3] = (float)bcolor[3] / 255.0f;
-
-	RB_AddQuadStampExt( origin, left, up, color, 0, 0, 1, 1 );
-}
-
-
 
 /*
 ==============
@@ -245,97 +233,6 @@
 	RB_InstantQuad2(quadVerts, texCoords);
 }
 
-// q3mme quad  sprite:  origin, dir, shader, color, size, angle
-static void RB_SurfaceSpriteFixed (void)
-{
-	vec3_t forward, up, left;
-	float radius;
-	refEntity_t *re;
-	vec3_t angles;
-	vec3_t dir;
-	vec3_t axis[3];
-
-	//re = backEnd.currentEntity->ePtr;
-	re = &backEnd.currentEntity->e;
-	radius = re->radius;
-
-	VectorCopy(re->oldorigin, dir);
-	//VectorNormalize(dir);
-	vectoangles(dir, angles);
-	AngleVectors(angles, forward, left, up);
-	VectorSubtract(vec3_origin, left, left);
-
-	VectorCopy(forward, axis[0]);
-	VectorCopy(left, axis[1]);
-	VectorCopy(up, axis[2]);
-	RotateAroundDirection(axis, re->rotation);
-	VectorCopy(axis[0], forward);
-	VectorCopy(axis[1], left);
-	VectorCopy(axis[2], up);
-
-	//FIXME rectangular sprite even possible in q3mme ?
-
-	VectorScale(left, radius, left);
-	VectorScale(up, radius, up);
-
-	if (backEnd.viewParms.isMirror) {
-		VectorSubtract(vec3_origin, left, left);
-	}
-
-	// swap up and left to match q3mme
-	RB_AddQuadStampByteColor(re->origin, up, left, re->shaderRGBA);
-}
-
-// q3mme spark view aligned uses:  origin, velocity, shader, color, size, width
-//   aligns to view origin and not view angles
-
-static void RB_SurfaceSpark (void)
-{
-	vec3_t left, up, forward;
-	float radius;
-	float width;
-	refEntity_t *re;
-	vec3_t v;
-	vec3_t newForward;
-
-	//re = backEnd.currentEntity->ePtr;
-	re = &backEnd.currentEntity->e;
-
-	// size
-	radius = re->radius;
-	radius *= 0.5;
-
-	width = re->width;
-	width *= 0.5;
-
-	// dir (velocity)
-	VectorCopy(re->oldorigin, up);
-	VectorNormalize(up);
-	MakeNormalVectors(up, forward, left);
-
-	// origin view align
-	PointToPlane(v, backEnd.viewParms.or.origin, re->origin, up);
-	VectorSubtract(v, re->origin, newForward);
-	VectorNormalize(newForward);
-	CrossProduct(up, newForward, left);
-
-	VectorNormalize(left);
-	VectorNormalize(up);
-
-	VectorScale(left, width, left);
-	VectorScale(up, radius, up);
-
-	if (backEnd.viewParms.isMirror) {
-		VectorSubtract(vec3_origin, left, left);
-	}
-
-	// match q3mme
-	VectorSubtract(vec3_origin, up, up);
-	VectorSubtract(vec3_origin, left, left);
-
-	// swap up and left to match q3mme
-	RB_AddQuadStampByteColor(re->origin, up, left, re->shaderRGBA);
-}
 
 /*
 ==============
@@ -345,30 +242,18 @@
 static void RB_SurfaceSprite( void ) {
 	vec3_t		left, up;
 	float		radius;
-	int width, height;
-	float ratio;
 	float			colors[4];
 	trRefEntity_t	*ent = backEnd.currentEntity;
 
 	// calculate the xyz locations for the four corners
 	radius = ent->e.radius;
-
-	// wc hack:  only used with name sprites to allow rectangular scaled image
-	if (ent->e.useScale) {
-		RE_GetShaderImageDimensions(ent->e.customShader, &width, &height);
-		ratio = (float)width / (float)height;
-		VectorScale(backEnd.viewParms.or.axis[1], radius * ratio, left);
-		VectorScale(backEnd.viewParms.or.axis[2], radius, up);
-	} else if (ent->e.stretch) {
-		VectorScale(backEnd.viewParms.or.axis[1], ent->e.width, left);
-		VectorScale(backEnd.viewParms.or.axis[2], ent->e.height, up);
-	} else if ( ent->e.rotation == 0 ) {
+	if ( ent->e.rotation == 0 ) {
 		VectorScale( backEnd.viewParms.or.axis[1], radius, left );
 		VectorScale( backEnd.viewParms.or.axis[2], radius, up );
 	} else {
 		float	s, c;
 		float	ang;
-
+		
 		ang = M_PI * ent->e.rotation / 180;
 		s = sin( ang );
 		c = cos( ang );
@@ -379,18 +264,13 @@
 		VectorScale( backEnd.viewParms.or.axis[2], c * radius, up );
 		VectorMA( up, s * radius, backEnd.viewParms.or.axis[1], up );
 	}
-
 	if ( backEnd.viewParms.isMirror ) {
 		VectorSubtract( vec3_origin, left, left );
 	}
 
 	VectorScale4(ent->e.shaderRGBA, 1.0f / 255.0f, colors);
 
-	if (ent->e.stretch) {
-		RB_AddQuadStampExt(ent->e.origin, left, up, colors, ent->e.s1, ent->e.t1, ent->e.s2, ent->e.t2);
-	} else {
-		RB_AddQuadStamp( ent->e.origin, left, up, colors );
-	}
+	RB_AddQuadStamp( ent->e.origin, left, up, colors );
 }
 
 
@@ -675,86 +555,9 @@
 	tess.firstIndex = 0;
 }
 
-static void RB_SurfaceBeamQ3mme (void)
-{
-	vec3_t left, up, forward;
-	float radius;
-	float width;
-	vec3_t angles;
-	refEntity_t *re;
-	int repetitions;
-	int i;
-	vec3_t origin;
-	vec3_t v;
-	vec3_t newForward;
-
-	//re = backEnd.currentEntity->ePtr;
-	re = &backEnd.currentEntity->e;
-
-	if (re->rotation) {
-		repetitions = 180 / re->rotation;
-	} else {
-		repetitions = 1;
-	}
-
-	// size
-	radius = re->radius;
-	radius *= 0.5;
-
-	width = VectorLength(re->oldorigin);
-	width *= 0.5;
-
-	vectoangles(re->oldorigin, angles);
-	AngleVectors(angles, forward, left, up);
-
-	// origin align
-	PointToPlane(v, backEnd.viewParms.or.origin, re->origin, forward);
-	VectorSubtract(v, re->origin, newForward);
-	VectorNormalize(newForward);
-	CrossProduct(forward, newForward, left);
-	//VectorSubtract(vec3_origin, left, left);
-	VectorCopy(left, up);
-	VectorSubtract(vec3_origin, up, up);  // to match q3mme
-
-	VectorCopy(forward, left);
-	VectorSubtract(vec3_origin, left, left);  // to match q3mme
-	VectorScale(left, width, left);
-	VectorScale(up, radius, up);
-	VectorMA(re->origin, width, forward, origin);
-
-	for (i = 0;  i < repetitions;  i++) {
-
-		if (backEnd.viewParms.isMirror) {
-			VectorSubtract(vec3_origin, up, up);  // to match q3mme
-		}
-
-		RB_AddQuadStampByteColor(origin, left, up, re->shaderRGBA);
-
-		vectoangles(re->oldorigin, angles);
-		angles[ROLL] += re->rotation * (i + 1);
-
-		AngleVectors(angles, forward, left, up);
-
-		PointToPlane(v, backEnd.viewParms.or.origin, re->origin, forward);
-		VectorSubtract(v, re->origin, newForward);
-		VectorNormalize(newForward);
-		CrossProduct(forward, newForward, left);
-		//VectorSubtract(vec3_origin, left, left);
-
-		VectorCopy(left, up);
-		VectorSubtract(vec3_origin, up, up);  // to match q3mme
-
-		VectorCopy(forward, left);
-		VectorSubtract(vec3_origin, left, left);  // to match q3mme
-		VectorScale(left, width, left);
-		VectorScale(up, radius, up);
-		VectorMA(re->origin, width, forward, origin);
-	}
-}
-
 //================================================================================
 
-void DoRailCore( const vec3_t start, const vec3_t end, const vec3_t up, float len, float spanWidth )
+static void DoRailCore( const vec3_t start, const vec3_t end, const vec3_t up, float len, float spanWidth )
 {
 	float		spanWidth2;
 	int			vbase;
@@ -811,12 +614,12 @@
 	tess.indexes[tess.numIndexes++] = vbase + 3;
 }
 
-static void DoRailDiscs( int numSegs, const vec3_t start, const vec3_t dir, const vec3_t right, const vec3_t up, float spanWidth )
+static void DoRailDiscs( int numSegs, const vec3_t start, const vec3_t dir, const vec3_t right, const vec3_t up )
 {
 	int i;
 	vec3_t	pos[4];
 	vec3_t	v;
-	//int		spanWidth = r_railWidth->integer;
+	int		spanWidth = r_railWidth->integer;
 	float c, s;
 	float		scale;
 
@@ -900,52 +703,7 @@
 
 	VectorScale( vec, r_railSegmentLength->value, vec );
 
-	DoRailDiscs( numSegs, start, vec, right, up, r_railWidth->integer );
-}
-
-static void RB_SurfaceRailRingsQ3mme (void)
-{
-	refEntity_t *e;
-	int numSegs;
-	float len;
-	vec3_t vec;
-	vec3_t right, up;
-	vec3_t start, end;
-
-	//e = backEnd.currentEntity->ePtr;
-	e = &backEnd.currentEntity->e;
-
-	//ri.Printf(PRINT_ALL, "rend q3mme rail rings rotation %f  radius %f \n", e->rotation, e->radius);
-
-	//VectorCopy(e->oldorigin, start);
-
-	//VectorMA(e->origin, 1, e->oldorigin, start);
-	//VectorCopy(e->origin, end);
-
-	// arggggg
-	//VectorCopy(e->origin, start);
-	//VectorMA(e->oldorigin, -1, start, end);
-	//VectorCopy(e->oldorigin, end);
-	//ri.Printf(PRINT_ALL, "e->oldorigin %f %f %f\n", e->oldorigin[0], e->oldorigin[1], e->oldorigin[2]);
-
-	//VectorCopy( e->oldorigin, start );
-
-	VectorCopy( e->origin, end );
-	VectorMA(e->origin, 1, e->oldorigin, start);
-
-	// compute variables
-	VectorSubtract(end, start, vec);
-	len = VectorNormalize(vec);
-	MakeNormalVectors(vec, right, up);
-	numSegs = (len) / e->rotation;  //r_railSegmentLength->value;
-	if (numSegs <= 0) {
-		numSegs = 1;
-	}
-
-	//VectorScale( vec, r_railSegmentLength->value, vec );  // width in q3mme script
-	VectorScale(vec, e->rotation, vec);  // width in q3mme script
-
-	DoRailDiscs(numSegs, start, vec, right, up,  e->radius);  // size in q3mme script
+	DoRailDiscs( numSegs, start, vec, right, up );
 }
 
 /*
@@ -1016,44 +774,6 @@
 	}
 }
 
-static void RB_SurfaceGrapple( void ) {
-	refEntity_t *e;
-	int			len;
-	vec3_t		right;
-	vec3_t		vec;
-	vec3_t		start, end;
-	vec3_t		v1, v2;
-	int			i;
-
-	//e = backEnd.currentEntity->ePtr;
-	e = &backEnd.currentEntity->e;
-
-	VectorCopy( e->oldorigin, end );
-	VectorCopy( e->origin, start );
-
-	// compute variables
-	VectorSubtract( end, start, vec );
-	len = VectorNormalize( vec );
-
-	len *= e->width;  //0.5;
-
-	// compute side vector
-	VectorSubtract( start, backEnd.viewParms.or.origin, v1 );
-	VectorNormalize( v1 );
-	VectorSubtract( end, backEnd.viewParms.or.origin, v2 );
-	VectorNormalize( v2 );
-	CrossProduct( v1, v2, right );
-	VectorNormalize( right );
-
-	for ( i = 0 ; i < 1 ; i++ ) {
-		vec3_t	temp;
-
-		//DoRailCore( start, end, right, len, 8 );
-		DoRailCore( start, end, right, len, e->radius );
-		RotatePointAroundVector( temp, vec, right, 45 );
-		VectorCopy( temp, right );
-	}
-}
 
 static void LerpMeshVertexes(mdvSurface_t *surf, float backlerp)
 {
@@ -1461,12 +1181,6 @@
 	case RT_SPRITE:
 		RB_SurfaceSprite();
 		break;
-	case RT_SPRITE_FIXED:
-		RB_SurfaceSpriteFixed();
-		break;
-	case RT_SPARK:
-		RB_SurfaceSpark();
-		break;
 	case RT_BEAM:
 		RB_SurfaceBeam();
 		break;
@@ -1476,18 +1190,9 @@
 	case RT_RAIL_RINGS:
 		RB_SurfaceRailRings();
 		break;
-	case RT_BEAM_Q3MME:
-		RB_SurfaceBeamQ3mme();
-		break;
-	case RT_RAIL_RINGS_Q3MME:
-		RB_SurfaceRailRingsQ3mme();
-		break;
 	case RT_LIGHTNING:
 		RB_SurfaceLightningBolt();
 		break;
-	case RT_GRAPPLE:
-		RB_SurfaceGrapple();
-		break;
 	default:
 		RB_SurfaceAxis();
 		break;

```
