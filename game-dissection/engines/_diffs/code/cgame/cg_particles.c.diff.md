# Diff: `code/cgame/cg_particles.c`
**Canonical:** `wolfcamql-src` (sha256 `7a2199b96cfd...`, 42612 bytes)

## Variants

### `quake3-source`  — sha256 `a6814b4b43b9...`, 42781 bytes

_Diff stat: +48 / -61 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_particles.c	2026-04-16 20:02:25.146528900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\cgame\cg_particles.c	2026-04-16 20:02:19.883535600 +0100
@@ -1,15 +1,29 @@
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Foobar; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 // Rafael particles
 // cg_particles.c  
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
-//#define WOLF_PARTICLES
-
 #define BLOODRED	2
 #define EMISIVEFADE	3
 #define GREY75		4
@@ -77,21 +91,6 @@
 #define	MAX_SHADER_ANIMS		32
 #define	MAX_SHADER_ANIM_FRAMES	64
 
-#ifndef WOLF_PARTICLES
-static char *shaderAnimNames[MAX_SHADER_ANIMS] = {
-	"explode1",
-	NULL
-};
-static qhandle_t shaderAnims[MAX_SHADER_ANIMS][MAX_SHADER_ANIM_FRAMES];
-static int     shaderAnimCounts[MAX_SHADER_ANIMS] = {
-	23
-};
-static float   shaderAnimSTRatio[MAX_SHADER_ANIMS] = {
-	1.0f
-};
-static int     numShaderAnims;
-// done.
-#else
 static char *shaderAnimNames[MAX_SHADER_ANIMS] = {
 	"explode1",
 	"blacksmokeanim",
@@ -118,14 +117,11 @@
 	1.0f,
 	1.0f,
 };
-#endif
+static int	numShaderAnims;
+// done.
 
 #define		PARTICLE_GRAVITY	40
-#ifdef WOLF_PARTICLES
 #define		MAX_PARTICLES	1024 * 8
-#else
-#define		MAX_PARTICLES 1024
-#endif
 
 cparticle_t	*active_particles, *free_particles;
 cparticle_t	particles[MAX_PARTICLES];
@@ -194,16 +190,6 @@
 	polyVert_t	TRIverts[3];
 	vec3_t		rright2, rup2;
 
-#if 0
-	if (!r_weather.integer  &&  (p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		return;
-	}
-#endif
-
-	if ((p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		//Com_Printf("weather\n");
-	}
-
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY
 		|| p->type == P_BUBBLE || p->type == P_BUBBLE_TURBULENT)
 	{// create a front facing polygon
@@ -345,11 +331,7 @@
 		vec3_t	rr, ru;
 		vec3_t	rotate_ang;
 
-#ifdef WOLF_PARTICLES
 		VectorSet (color, 1.0, 1.0, 1.0);
-#else
-		VectorSet (color, 1.0, 1.0, 0.5);
-#endif
 		time = cg.time - p->time;
 		time2 = p->endtime - p->time;
 		ratio = time / time2;
@@ -567,12 +549,12 @@
 	{
 		vec3_t	rr, ru;
 		vec3_t	rotate_ang;
-		float	pAlpha;
+		float	alpha;
 
-		pAlpha = p->alpha;
+		alpha = p->alpha;
 		
 		if ( cgs.glconfig.hardwareType == GLHW_RAGEPRO )
-			pAlpha = 1;
+			alpha = 1;
 
 		if (p->roll) 
 		{
@@ -594,7 +576,7 @@
 		verts[0].modulate[0] = 111;	
 		verts[0].modulate[1] = 19;	
 		verts[0].modulate[2] = 9;	
-		verts[0].modulate[3] = 255 * pAlpha;	
+		verts[0].modulate[3] = 255 * alpha;	
 
 		VectorMA (org, -p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -604,7 +586,7 @@
 		verts[1].modulate[0] = 111;	
 		verts[1].modulate[1] = 19;	
 		verts[1].modulate[2] = 9;	
-		verts[1].modulate[3] = 255 * pAlpha;	
+		verts[1].modulate[3] = 255 * alpha;	
 
 		VectorMA (org, p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -624,11 +606,12 @@
 		verts[3].modulate[0] = 111;	
 		verts[3].modulate[1] = 19;	
 		verts[3].modulate[2] = 9;	
-		verts[3].modulate[3] = 255 * pAlpha;	
+		verts[3].modulate[3] = 255 * alpha;	
 
 	}
 	else if (p->type == P_FLAT_SCALEUP)
 	{
+		float width, height;
 		float sinR, cosR;
 
 		if (p->color == BLOODRED)
@@ -830,9 +813,9 @@
 	}
 
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY)
-		trap_R_AddPolyToScene( p->pshader, 3, TRIverts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 3, TRIverts );
 	else
-		trap_R_AddPolyToScene( p->pshader, 4, verts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 4, verts );
 
 }
 
@@ -850,7 +833,9 @@
 	float			alpha;
 	float			time, time2;
 	vec3_t			org;
+	int				color;
 	cparticle_t		*active, *tail;
+	int				type;
 	vec3_t			rotate_ang;
 
 	if (!initparticles)
@@ -955,12 +940,16 @@
 		if (alpha > 1.0)
 			alpha = 1;
 
+		color = p->color;
+
 		time2 = time*time;
 
 		org[0] = p->org[0] + p->vel[0]*time + p->accel[0]*time2;
 		org[1] = p->org[1] + p->vel[1]*time + p->accel[1]*time2;
 		org[2] = p->org[2] + p->vel[2]*time + p->accel[2]*time2;
 
+		type = p->type;
+
 		CG_AddParticleToScene (p, org, alpha);
 	}
 
@@ -977,8 +966,6 @@
 	cparticle_t	*p;
 	qboolean turb = qtrue;
 
-	//Com_Printf("snow\n");
-
 	if (!pshader)
 		CG_Printf ("CG_ParticleSnowFlurry pshader == ZERO!\n");
 
@@ -1022,6 +1009,10 @@
 	
 	VectorCopy(cent->currentState.origin, p->org);
 
+	p->org[0] = p->org[0];
+	p->org[1] = p->org[1];
+	p->org[2] = p->org[2];
+
 	p->vel[0] = p->vel[1] = 0;
 	
 	p->accel[0] = p->accel[1] = p->accel[2] = 0;
@@ -1261,11 +1252,11 @@
 
 	// find the animation string
 	for (anim=0; shaderAnimNames[anim]; anim++) {
-		if (!Q_stricmp( animStr, shaderAnimNames[anim] ))
+		if (!stricmp( animStr, shaderAnimNames[anim] ))
 			break;
 	}
 	if (!shaderAnimNames[anim]) {
-		CG_Error("CG_ParticleExplosion: unknown animation string: %s", animStr);
+		CG_Error("CG_ParticleExplosion: unknown animation string: %s\n", animStr);
 		return;
 	}
 
@@ -1276,11 +1267,7 @@
 	p->next = active_particles;
 	active_particles = p;
 	p->time = cg.time;
-#ifdef WOLF_PARTICLES
 	p->alpha = 1.0;
-#else
-	p->alpha = 0.5;
-#endif
 	p->alphavel = 0;
 
 	if (duration < 0) {
@@ -1311,6 +1298,7 @@
 // Rafael Shrapnel
 void CG_AddParticleShrapnel (localEntity_t *le)
 {
+	return;
 }
 // done.
 
@@ -1665,8 +1653,8 @@
 	vec3_t	angles;
 	vec3_t	right, up;
 	vec3_t	this_pos, x_pos, center_pos, end_pos;
-	int	x, y;
-	int	fwidth, fheight;
+	float	x, y;
+	float	fwidth, fheight;
 	trace_t	trace;
 	vec3_t	normal;
 
@@ -1692,7 +1680,7 @@
 			CG_Trace (&trace, this_pos, NULL, NULL, end_pos, -1, CONTENTS_SOLID);
 
 			
-			if (trace.entityNum < ENTITYNUM_WORLD) // may only land on world
+			if (trace.entityNum < (MAX_ENTITIES - 1)) // may only land on world
 				return qfalse;
 
 			if (!(!trace.startsolid && trace.fraction < 1))
@@ -2028,4 +2016,3 @@
 
 	p->rotate = qfalse;
 }
-

```

### `ioquake3`  — sha256 `84d1f297c13c...`, 43156 bytes

_Diff stat: +33 / -29 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_particles.c	2026-04-16 20:02:25.146528900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\cgame\cg_particles.c	2026-04-16 20:02:21.522051500 +0100
@@ -1,13 +1,29 @@
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 // Rafael particles
 // cg_particles.c  
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
 //#define WOLF_PARTICLES
 
 #define BLOODRED	2
@@ -83,13 +99,13 @@
 	NULL
 };
 static qhandle_t shaderAnims[MAX_SHADER_ANIMS][MAX_SHADER_ANIM_FRAMES];
-static int     shaderAnimCounts[MAX_SHADER_ANIMS] = {
+static int	shaderAnimCounts[MAX_SHADER_ANIMS] = {
 	23
 };
-static float   shaderAnimSTRatio[MAX_SHADER_ANIMS] = {
+static float	shaderAnimSTRatio[MAX_SHADER_ANIMS] = {
 	1.0f
 };
-static int     numShaderAnims;
+static int	numShaderAnims;
 // done.
 #else
 static char *shaderAnimNames[MAX_SHADER_ANIMS] = {
@@ -121,6 +137,7 @@
 #endif
 
 #define		PARTICLE_GRAVITY	40
+
 #ifdef WOLF_PARTICLES
 #define		MAX_PARTICLES	1024 * 8
 #else
@@ -194,16 +211,6 @@
 	polyVert_t	TRIverts[3];
 	vec3_t		rright2, rup2;
 
-#if 0
-	if (!r_weather.integer  &&  (p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		return;
-	}
-#endif
-
-	if ((p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		//Com_Printf("weather\n");
-	}
-
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY
 		|| p->type == P_BUBBLE || p->type == P_BUBBLE_TURBULENT)
 	{// create a front facing polygon
@@ -594,7 +601,7 @@
 		verts[0].modulate[0] = 111;	
 		verts[0].modulate[1] = 19;	
 		verts[0].modulate[2] = 9;	
-		verts[0].modulate[3] = 255 * pAlpha;	
+		verts[0].modulate[3] = 255 * pAlpha;
 
 		VectorMA (org, -p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -604,7 +611,7 @@
 		verts[1].modulate[0] = 111;	
 		verts[1].modulate[1] = 19;	
 		verts[1].modulate[2] = 9;	
-		verts[1].modulate[3] = 255 * pAlpha;	
+		verts[1].modulate[3] = 255 * pAlpha;
 
 		VectorMA (org, p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -614,7 +621,7 @@
 		verts[2].modulate[0] = 111;	
 		verts[2].modulate[1] = 19;	
 		verts[2].modulate[2] = 9;	
-		verts[2].modulate[3] = 255 * alpha;	
+		verts[2].modulate[3] = 255 * pAlpha;
 
 		VectorMA (org, p->height, ru, point);	
 		VectorMA (point, -p->width, rr, point);	
@@ -624,7 +631,7 @@
 		verts[3].modulate[0] = 111;	
 		verts[3].modulate[1] = 19;	
 		verts[3].modulate[2] = 9;	
-		verts[3].modulate[3] = 255 * pAlpha;	
+		verts[3].modulate[3] = 255 * pAlpha;
 
 	}
 	else if (p->type == P_FLAT_SCALEUP)
@@ -830,9 +837,9 @@
 	}
 
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY)
-		trap_R_AddPolyToScene( p->pshader, 3, TRIverts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 3, TRIverts );
 	else
-		trap_R_AddPolyToScene( p->pshader, 4, verts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 4, verts );
 
 }
 
@@ -977,8 +984,6 @@
 	cparticle_t	*p;
 	qboolean turb = qtrue;
 
-	//Com_Printf("snow\n");
-
 	if (!pshader)
 		CG_Printf ("CG_ParticleSnowFlurry pshader == ZERO!\n");
 
@@ -1665,8 +1670,8 @@
 	vec3_t	angles;
 	vec3_t	right, up;
 	vec3_t	this_pos, x_pos, center_pos, end_pos;
-	int	x, y;
-	int	fwidth, fheight;
+	int		x, y;
+	int		fwidth, fheight;
 	trace_t	trace;
 	vec3_t	normal;
 
@@ -2028,4 +2033,3 @@
 
 	p->rotate = qfalse;
 }
-

```

### `openarena-engine`  — sha256 `458438768308...`, 43230 bytes

_Diff stat: +39 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_particles.c	2026-04-16 20:02:25.146528900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_particles.c	2026-04-16 22:48:25.725201800 +0100
@@ -1,13 +1,29 @@
+/*
+===========================================================================
+Copyright (C) 1999-2005 Id Software, Inc.
+
+This file is part of Quake III Arena source code.
+
+Quake III Arena source code is free software; you can redistribute it
+and/or modify it under the terms of the GNU General Public License as
+published by the Free Software Foundation; either version 2 of the License,
+or (at your option) any later version.
+
+Quake III Arena source code is distributed in the hope that it will be
+useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
+MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
+GNU General Public License for more details.
+
+You should have received a copy of the GNU General Public License
+along with Quake III Arena source code; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 // Rafael particles
 // cg_particles.c  
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
 //#define WOLF_PARTICLES
 
 #define BLOODRED	2
@@ -83,13 +99,13 @@
 	NULL
 };
 static qhandle_t shaderAnims[MAX_SHADER_ANIMS][MAX_SHADER_ANIM_FRAMES];
-static int     shaderAnimCounts[MAX_SHADER_ANIMS] = {
+static int	shaderAnimCounts[MAX_SHADER_ANIMS] = {
 	23
 };
-static float   shaderAnimSTRatio[MAX_SHADER_ANIMS] = {
+static float	shaderAnimSTRatio[MAX_SHADER_ANIMS] = {
 	1.0f
 };
-static int     numShaderAnims;
+static int	numShaderAnims;
 // done.
 #else
 static char *shaderAnimNames[MAX_SHADER_ANIMS] = {
@@ -121,6 +137,7 @@
 #endif
 
 #define		PARTICLE_GRAVITY	40
+
 #ifdef WOLF_PARTICLES
 #define		MAX_PARTICLES	1024 * 8
 #else
@@ -194,16 +211,6 @@
 	polyVert_t	TRIverts[3];
 	vec3_t		rright2, rup2;
 
-#if 0
-	if (!r_weather.integer  &&  (p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		return;
-	}
-#endif
-
-	if ((p->type == P_WEATHER  ||  p->type == P_WEATHER_TURBULENT  ||  p->type == P_WEATHER_FLURRY)) {
-		//Com_Printf("weather\n");
-	}
-
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY
 		|| p->type == P_BUBBLE || p->type == P_BUBBLE_TURBULENT)
 	{// create a front facing polygon
@@ -567,12 +574,12 @@
 	{
 		vec3_t	rr, ru;
 		vec3_t	rotate_ang;
-		float	pAlpha;
+		float	alpha;
 
-		pAlpha = p->alpha;
+		alpha = p->alpha;
 		
 		if ( cgs.glconfig.hardwareType == GLHW_RAGEPRO )
-			pAlpha = 1;
+			alpha = 1;
 
 		if (p->roll) 
 		{
@@ -594,7 +601,7 @@
 		verts[0].modulate[0] = 111;	
 		verts[0].modulate[1] = 19;	
 		verts[0].modulate[2] = 9;	
-		verts[0].modulate[3] = 255 * pAlpha;	
+		verts[0].modulate[3] = 255 * alpha;	
 
 		VectorMA (org, -p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -604,7 +611,7 @@
 		verts[1].modulate[0] = 111;	
 		verts[1].modulate[1] = 19;	
 		verts[1].modulate[2] = 9;	
-		verts[1].modulate[3] = 255 * pAlpha;	
+		verts[1].modulate[3] = 255 * alpha;	
 
 		VectorMA (org, p->height, ru, point);	
 		VectorMA (point, p->width, rr, point);	
@@ -624,7 +631,7 @@
 		verts[3].modulate[0] = 111;	
 		verts[3].modulate[1] = 19;	
 		verts[3].modulate[2] = 9;	
-		verts[3].modulate[3] = 255 * pAlpha;	
+		verts[3].modulate[3] = 255 * alpha;	
 
 	}
 	else if (p->type == P_FLAT_SCALEUP)
@@ -830,9 +837,9 @@
 	}
 
 	if (p->type == P_WEATHER || p->type == P_WEATHER_TURBULENT || p->type == P_WEATHER_FLURRY)
-		trap_R_AddPolyToScene( p->pshader, 3, TRIverts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 3, TRIverts );
 	else
-		trap_R_AddPolyToScene( p->pshader, 4, verts, qfalse );
+		trap_R_AddPolyToScene( p->pshader, 4, verts );
 
 }
 
@@ -977,8 +984,6 @@
 	cparticle_t	*p;
 	qboolean turb = qtrue;
 
-	//Com_Printf("snow\n");
-
 	if (!pshader)
 		CG_Printf ("CG_ParticleSnowFlurry pshader == ZERO!\n");
 
@@ -1022,6 +1027,10 @@
 	
 	VectorCopy(cent->currentState.origin, p->org);
 
+	p->org[0] = p->org[0];
+	p->org[1] = p->org[1];
+	p->org[2] = p->org[2];
+
 	p->vel[0] = p->vel[1] = 0;
 	
 	p->accel[0] = p->accel[1] = p->accel[2] = 0;
@@ -1665,8 +1674,8 @@
 	vec3_t	angles;
 	vec3_t	right, up;
 	vec3_t	this_pos, x_pos, center_pos, end_pos;
-	int	x, y;
-	int	fwidth, fheight;
+	int		x, y;
+	int		fwidth, fheight;
 	trace_t	trace;
 	vec3_t	normal;
 
@@ -2028,4 +2037,3 @@
 
 	p->rotate = qfalse;
 }
-

```
