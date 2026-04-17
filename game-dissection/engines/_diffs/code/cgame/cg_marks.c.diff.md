# Diff: `code/cgame/cg_marks.c`
**Canonical:** `wolfcamql-src` (sha256 `4a1138961a52...`, 10481 bytes)

## Variants

### `quake3-source`  — sha256 `71b50729deea...`, 49724 bytes

_Diff stat: +2003 / -147 lines_

_(full diff is 50071 bytes — see files directly)_

### `ioquake3`  — sha256 `7512db48c4ce...`, 8138 bytes

_Diff stat: +40 / -165 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_marks.c	2026-04-16 20:02:25.144503500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\cgame\cg_marks.c	2026-04-16 20:02:21.521055100 +0100
@@ -1,15 +1,29 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
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
 //
 // cg_marks.c -- wall marks
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_marks.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
 /*
 ===================================================================
 
@@ -19,9 +33,9 @@
 */
 
 
-static markPoly_t	cg_activeMarkPolys;			// double linked list
-static markPoly_t	*cg_freeMarkPolys;			// single linked list
-static markPoly_t	cg_markPolys[MAX_MARK_POLYS];
+markPoly_t	cg_activeMarkPolys;			// double linked list
+markPoly_t	*cg_freeMarkPolys;			// single linked list
+markPoly_t	cg_markPolys[MAX_MARK_POLYS];
 static		int	markTotal;
 
 /*
@@ -36,8 +50,6 @@
 
 	memset( cg_markPolys, 0, sizeof(cg_markPolys) );
 
-	//Com_Printf("^6mark polys: %f MB\n", (float)sizeof(cg_markPolys) / 1024.0 / 1024.0);
-
 	cg_activeMarkPolys.nextMark = &cg_activeMarkPolys;
 	cg_activeMarkPolys.prevMark = &cg_activeMarkPolys;
 	cg_freeMarkPolys = cg_markPolys;
@@ -52,9 +64,9 @@
 CG_FreeMarkPoly
 ==================
 */
-static void CG_FreeMarkPoly( markPoly_t *le ) {
-	if ( !le->prevMark  ||  !le->nextMark ) {
-		CG_Error( "CG_FreeMarkPoly: not active" );
+void CG_FreeMarkPoly( markPoly_t *le ) {
+	if ( !le->prevMark || !le->nextMark ) {
+		CG_Error( "CG_FreeLocalEntity: not active" );
 	}
 
 	// remove from the doubly linked active list
@@ -73,7 +85,7 @@
 Will allways succeed, even if it requires freeing an old active mark
 ===================
 */
-static markPoly_t *CG_AllocMark( void ) {
+markPoly_t	*CG_AllocMark( void ) {
 	markPoly_t	*le;
 	int time;
 
@@ -117,7 +129,7 @@
 
 void CG_ImpactMark( qhandle_t markShader, const vec3_t origin, const vec3_t dir, 
 				   float orientation, float red, float green, float blue, float alpha,
-					qboolean alphaFade, float radius, qboolean temporary, qboolean energy, qboolean debug ) {
+				   qboolean alphaFade, float radius, qboolean temporary ) {
 	vec3_t			axis[3];
 	float			texCoordScale;
 	vec3_t			originalPoints[4];
@@ -128,15 +140,7 @@
 	vec3_t			markPoints[MAX_MARK_POINTS];
 	vec3_t			projection;
 
-	if (debug) {
-		VectorCopy(origin, cg.lastImpactOrigin);
-	}
-
-	if (cg_debugImpactOrigin.integer  &&  debug) {
-		Com_Printf("mark origin: %f %f %f\n", origin[0], origin[1], origin[2]);
-	}
-
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
@@ -198,7 +202,7 @@
 
 		// if it is a temporary (shadow) mark, add it immediately and forget about it
 		if ( temporary ) {
-			trap_R_AddPolyToScene( markShader, mf->numPoints, verts, qfalse );
+			trap_R_AddPolyToScene( markShader, mf->numPoints, verts );
 			continue;
 		}
 
@@ -207,7 +211,6 @@
 		mark->time = cg.time;
 		mark->alphaFade = alphaFade;
 		mark->markShader = markShader;
-		mark->energy = energy;
 		mark->poly.numVerts = mf->numPoints;
 		mark->color[0] = red;
 		mark->color[1] = green;
@@ -224,24 +227,19 @@
 CG_AddMarks
 ===============
 */
-//#define	MARK_TOTAL_TIME		10000
-//#define	MARK_FADE_TIME		1000
+#define	MARK_TOTAL_TIME		10000
+#define	MARK_FADE_TIME		1000
 
 void CG_AddMarks( void ) {
 	int			j;
 	markPoly_t	*mp, *next;
 	int			t;
 	int			fade;
-	int MARK_TOTAL_TIME;
-	int MARK_FADE_TIME;
 
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
-	MARK_TOTAL_TIME = cg_markTime.integer;
-	MARK_FADE_TIME = cg_markFadeTime.integer;
-
 	mp = cg_activeMarkPolys.nextMark;
 	for ( ; mp != &cg_activeMarkPolys ; mp = next ) {
 		// grab next now, so if the local entity is freed we
@@ -255,11 +253,9 @@
 		}
 
 		// fade out the energy bursts
-		//if ( mp->markShader == cgs.media.energyMarkShader ) {
-		if (mp->energy) {
+		if ( mp->markShader == cgs.media.energyMarkShader ) {
 
 			fade = 450 - 450 * ( (cg.time - mp->time ) / 3000.0 );
-			//Com_Printf("energy fade: %d\n", fade);
 			if ( fade < 255 ) {
 				if ( fade < 0 ) {
 					fade = 0;
@@ -278,141 +274,20 @@
 		t = mp->time + MARK_TOTAL_TIME - cg.time;
 		if ( t < MARK_FADE_TIME ) {
 			fade = 255 * t / MARK_FADE_TIME;
-			//Com_Printf("mark fade: %d  alphafade:%d\n", fade, mp->alphaFade);
 			if ( mp->alphaFade ) {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
 					mp->verts[j].modulate[3] = fade;
 				}
 			} else {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
-					if (mp->energy) {
-						mp->verts[j].modulate[0] *= fade;
-						mp->verts[j].modulate[1] *= fade;
-						mp->verts[j].modulate[2] *= fade;
-					} else {
-						mp->verts[j].modulate[0] = mp->color[0] * fade;
-						mp->verts[j].modulate[1] = mp->color[1] * fade;
-						mp->verts[j].modulate[2] = mp->color[2] * fade;
-					}
+					mp->verts[j].modulate[0] = mp->color[0] * fade;
+					mp->verts[j].modulate[1] = mp->color[1] * fade;
+					mp->verts[j].modulate[2] = mp->color[2] * fade;
 				}
 			}
 		}
 
-		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts, qfalse );
-	}
-}
-
-#if 0   // testing
-static float   frand(void)
-{
-	return (rand()&32767)* (1.0/32767);
-}
-
-static float   crand(void)
-{
-	return (rand()&32767)* (2.0/32767) - 1;
-}
 
-
-void CG_Q2RailTrail (const vec3_t start, const vec3_t end)
-{
-	vec3_t          move;
-	vec3_t          vec;
-	float           len;
-	int                     j;
-	cparticle_t     *p;
-	float           dec;
-	vec3_t          right, up;
-	int                     i;
-	float           d, c, s;
-	vec3_t          dir;
-	byte            clr = 0x74;
-
-	VectorCopy (start, move);
-	VectorSubtract (end, start, vec);
-	len = VectorNormalize (vec);
-
-	MakeNormalVectors (vec, right, up);
-
-	//goto core;
-
-	for (i=0 ; i<len ; i++)
-        {
-			if (!free_particles)
-				return;
-
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			d = i * 0.1;
-			c = cos(d);
-			s = sin(d);
-
-			VectorScale (right, c, dir);
-			VectorMA (dir, s, up, dir);
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (1+frand()*0.2);
-			p->color = clr + (rand()&7);
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + dir[j]*3;
-					p->vel[j] = dir[j]*6;
-                }
-
-			VectorAdd (move, vec, move);
-        }
-
-//core:
-
-	dec = 0.75;
-	VectorScale (vec, dec, vec);
-	VectorCopy (start, move);
-
-	while (len > 0)
-        {
-			len -= dec;
-
-			if (!free_particles)
-				return;
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			//p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->pshader = cgs.media.railRingsShader;
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (0.6+frand()*0.2);
-			p->color = 0x0 + (rand()&15);
-
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + crand()*3;
-					p->vel[j] = crand()*3;
-					p->accel[j] = 0;
-                }
-
-			VectorAdd (move, vec, move);
-        }
+		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts );
+	}
 }
-#endif

```

### `openarena-engine`  — sha256 `2ab955520f48...`, 8121 bytes

_Diff stat: +40 / -165 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_marks.c	2026-04-16 20:02:25.144503500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_marks.c	2026-04-16 22:48:25.725201800 +0100
@@ -1,15 +1,29 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
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
 //
 // cg_marks.c -- wall marks
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_marks.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
 /*
 ===================================================================
 
@@ -19,9 +33,9 @@
 */
 
 
-static markPoly_t	cg_activeMarkPolys;			// double linked list
-static markPoly_t	*cg_freeMarkPolys;			// single linked list
-static markPoly_t	cg_markPolys[MAX_MARK_POLYS];
+markPoly_t	cg_activeMarkPolys;			// double linked list
+markPoly_t	*cg_freeMarkPolys;			// single linked list
+markPoly_t	cg_markPolys[MAX_MARK_POLYS];
 static		int	markTotal;
 
 /*
@@ -36,8 +50,6 @@
 
 	memset( cg_markPolys, 0, sizeof(cg_markPolys) );
 
-	//Com_Printf("^6mark polys: %f MB\n", (float)sizeof(cg_markPolys) / 1024.0 / 1024.0);
-
 	cg_activeMarkPolys.nextMark = &cg_activeMarkPolys;
 	cg_activeMarkPolys.prevMark = &cg_activeMarkPolys;
 	cg_freeMarkPolys = cg_markPolys;
@@ -52,9 +64,9 @@
 CG_FreeMarkPoly
 ==================
 */
-static void CG_FreeMarkPoly( markPoly_t *le ) {
-	if ( !le->prevMark  ||  !le->nextMark ) {
-		CG_Error( "CG_FreeMarkPoly: not active" );
+void CG_FreeMarkPoly( markPoly_t *le ) {
+	if ( !le->prevMark ) {
+		CG_Error( "CG_FreeLocalEntity: not active" );
 	}
 
 	// remove from the doubly linked active list
@@ -73,7 +85,7 @@
 Will allways succeed, even if it requires freeing an old active mark
 ===================
 */
-static markPoly_t *CG_AllocMark( void ) {
+markPoly_t	*CG_AllocMark( void ) {
 	markPoly_t	*le;
 	int time;
 
@@ -117,7 +129,7 @@
 
 void CG_ImpactMark( qhandle_t markShader, const vec3_t origin, const vec3_t dir, 
 				   float orientation, float red, float green, float blue, float alpha,
-					qboolean alphaFade, float radius, qboolean temporary, qboolean energy, qboolean debug ) {
+				   qboolean alphaFade, float radius, qboolean temporary ) {
 	vec3_t			axis[3];
 	float			texCoordScale;
 	vec3_t			originalPoints[4];
@@ -128,15 +140,7 @@
 	vec3_t			markPoints[MAX_MARK_POINTS];
 	vec3_t			projection;
 
-	if (debug) {
-		VectorCopy(origin, cg.lastImpactOrigin);
-	}
-
-	if (cg_debugImpactOrigin.integer  &&  debug) {
-		Com_Printf("mark origin: %f %f %f\n", origin[0], origin[1], origin[2]);
-	}
-
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
@@ -198,7 +202,7 @@
 
 		// if it is a temporary (shadow) mark, add it immediately and forget about it
 		if ( temporary ) {
-			trap_R_AddPolyToScene( markShader, mf->numPoints, verts, qfalse );
+			trap_R_AddPolyToScene( markShader, mf->numPoints, verts );
 			continue;
 		}
 
@@ -207,7 +211,6 @@
 		mark->time = cg.time;
 		mark->alphaFade = alphaFade;
 		mark->markShader = markShader;
-		mark->energy = energy;
 		mark->poly.numVerts = mf->numPoints;
 		mark->color[0] = red;
 		mark->color[1] = green;
@@ -224,24 +227,19 @@
 CG_AddMarks
 ===============
 */
-//#define	MARK_TOTAL_TIME		10000
-//#define	MARK_FADE_TIME		1000
+#define	MARK_TOTAL_TIME		10000
+#define	MARK_FADE_TIME		1000
 
 void CG_AddMarks( void ) {
 	int			j;
 	markPoly_t	*mp, *next;
 	int			t;
 	int			fade;
-	int MARK_TOTAL_TIME;
-	int MARK_FADE_TIME;
 
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
-	MARK_TOTAL_TIME = cg_markTime.integer;
-	MARK_FADE_TIME = cg_markFadeTime.integer;
-
 	mp = cg_activeMarkPolys.nextMark;
 	for ( ; mp != &cg_activeMarkPolys ; mp = next ) {
 		// grab next now, so if the local entity is freed we
@@ -255,11 +253,9 @@
 		}
 
 		// fade out the energy bursts
-		//if ( mp->markShader == cgs.media.energyMarkShader ) {
-		if (mp->energy) {
+		if ( mp->markShader == cgs.media.energyMarkShader ) {
 
 			fade = 450 - 450 * ( (cg.time - mp->time ) / 3000.0 );
-			//Com_Printf("energy fade: %d\n", fade);
 			if ( fade < 255 ) {
 				if ( fade < 0 ) {
 					fade = 0;
@@ -278,141 +274,20 @@
 		t = mp->time + MARK_TOTAL_TIME - cg.time;
 		if ( t < MARK_FADE_TIME ) {
 			fade = 255 * t / MARK_FADE_TIME;
-			//Com_Printf("mark fade: %d  alphafade:%d\n", fade, mp->alphaFade);
 			if ( mp->alphaFade ) {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
 					mp->verts[j].modulate[3] = fade;
 				}
 			} else {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
-					if (mp->energy) {
-						mp->verts[j].modulate[0] *= fade;
-						mp->verts[j].modulate[1] *= fade;
-						mp->verts[j].modulate[2] *= fade;
-					} else {
-						mp->verts[j].modulate[0] = mp->color[0] * fade;
-						mp->verts[j].modulate[1] = mp->color[1] * fade;
-						mp->verts[j].modulate[2] = mp->color[2] * fade;
-					}
+					mp->verts[j].modulate[0] = mp->color[0] * fade;
+					mp->verts[j].modulate[1] = mp->color[1] * fade;
+					mp->verts[j].modulate[2] = mp->color[2] * fade;
 				}
 			}
 		}
 
-		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts, qfalse );
-	}
-}
-
-#if 0   // testing
-static float   frand(void)
-{
-	return (rand()&32767)* (1.0/32767);
-}
-
-static float   crand(void)
-{
-	return (rand()&32767)* (2.0/32767) - 1;
-}
 
-
-void CG_Q2RailTrail (const vec3_t start, const vec3_t end)
-{
-	vec3_t          move;
-	vec3_t          vec;
-	float           len;
-	int                     j;
-	cparticle_t     *p;
-	float           dec;
-	vec3_t          right, up;
-	int                     i;
-	float           d, c, s;
-	vec3_t          dir;
-	byte            clr = 0x74;
-
-	VectorCopy (start, move);
-	VectorSubtract (end, start, vec);
-	len = VectorNormalize (vec);
-
-	MakeNormalVectors (vec, right, up);
-
-	//goto core;
-
-	for (i=0 ; i<len ; i++)
-        {
-			if (!free_particles)
-				return;
-
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			d = i * 0.1;
-			c = cos(d);
-			s = sin(d);
-
-			VectorScale (right, c, dir);
-			VectorMA (dir, s, up, dir);
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (1+frand()*0.2);
-			p->color = clr + (rand()&7);
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + dir[j]*3;
-					p->vel[j] = dir[j]*6;
-                }
-
-			VectorAdd (move, vec, move);
-        }
-
-//core:
-
-	dec = 0.75;
-	VectorScale (vec, dec, vec);
-	VectorCopy (start, move);
-
-	while (len > 0)
-        {
-			len -= dec;
-
-			if (!free_particles)
-				return;
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			//p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->pshader = cgs.media.railRingsShader;
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (0.6+frand()*0.2);
-			p->color = 0x0 + (rand()&15);
-
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + crand()*3;
-					p->vel[j] = crand()*3;
-					p->accel[j] = 0;
-                }
-
-			VectorAdd (move, vec, move);
-        }
+		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts );
+	}
 }
-#endif

```

### `openarena-gamecode`  — sha256 `e5f9b82274f7...`, 8151 bytes

_Diff stat: +42 / -163 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_marks.c	2026-04-16 20:02:25.144503500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\cgame\cg_marks.c	2026-04-16 22:48:24.151331100 +0100
@@ -1,15 +1,29 @@
-// Copyright (C) 1999-2000 Id Software, Inc.
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
 //
 // cg_marks.c -- wall marks
 
 #include "cg_local.h"
 
-#include "cg_localents.h"
-#include "cg_main.h"
-#include "cg_marks.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-
 /*
 ===================================================================
 
@@ -19,9 +33,9 @@
 */
 
 
-static markPoly_t	cg_activeMarkPolys;			// double linked list
-static markPoly_t	*cg_freeMarkPolys;			// single linked list
-static markPoly_t	cg_markPolys[MAX_MARK_POLYS];
+markPoly_t	cg_activeMarkPolys;			// double linked list
+markPoly_t	*cg_freeMarkPolys;			// single linked list
+markPoly_t	cg_markPolys[MAX_MARK_POLYS];
 static		int	markTotal;
 
 /*
@@ -36,8 +50,6 @@
 
 	memset( cg_markPolys, 0, sizeof(cg_markPolys) );
 
-	//Com_Printf("^6mark polys: %f MB\n", (float)sizeof(cg_markPolys) / 1024.0 / 1024.0);
-
 	cg_activeMarkPolys.nextMark = &cg_activeMarkPolys;
 	cg_activeMarkPolys.prevMark = &cg_activeMarkPolys;
 	cg_freeMarkPolys = cg_markPolys;
@@ -52,9 +64,9 @@
 CG_FreeMarkPoly
 ==================
 */
-static void CG_FreeMarkPoly( markPoly_t *le ) {
-	if ( !le->prevMark  ||  !le->nextMark ) {
-		CG_Error( "CG_FreeMarkPoly: not active" );
+void CG_FreeMarkPoly( markPoly_t *le ) {
+	if ( !le->prevMark ) {
+		CG_Error( "CG_FreeLocalEntity: not active" );
 	}
 
 	// remove from the doubly linked active list
@@ -73,7 +85,7 @@
 Will allways succeed, even if it requires freeing an old active mark
 ===================
 */
-static markPoly_t *CG_AllocMark( void ) {
+markPoly_t	*CG_AllocMark( void ) {
 	markPoly_t	*le;
 	int time;
 
@@ -117,7 +129,7 @@
 
 void CG_ImpactMark( qhandle_t markShader, const vec3_t origin, const vec3_t dir, 
 				   float orientation, float red, float green, float blue, float alpha,
-					qboolean alphaFade, float radius, qboolean temporary, qboolean energy, qboolean debug ) {
+				   qboolean alphaFade, float radius, qboolean temporary ) {
 	vec3_t			axis[3];
 	float			texCoordScale;
 	vec3_t			originalPoints[4];
@@ -128,15 +140,7 @@
 	vec3_t			markPoints[MAX_MARK_POINTS];
 	vec3_t			projection;
 
-	if (debug) {
-		VectorCopy(origin, cg.lastImpactOrigin);
-	}
-
-	if (cg_debugImpactOrigin.integer  &&  debug) {
-		Com_Printf("mark origin: %f %f %f\n", origin[0], origin[1], origin[2]);
-	}
-
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
@@ -151,6 +155,7 @@
 	// create the texture axis
 	VectorNormalize2( dir, axis[0] );
 	PerpendicularVector( axis[1], axis[0] );
+	
 	RotatePointAroundVector( axis[2], axis[0], axis[1], orientation );
 	CrossProduct( axis[0], axis[2], axis[1] );
 
@@ -198,7 +203,7 @@
 
 		// if it is a temporary (shadow) mark, add it immediately and forget about it
 		if ( temporary ) {
-			trap_R_AddPolyToScene( markShader, mf->numPoints, verts, qfalse );
+			trap_R_AddPolyToScene( markShader, mf->numPoints, verts );
 			continue;
 		}
 
@@ -207,7 +212,6 @@
 		mark->time = cg.time;
 		mark->alphaFade = alphaFade;
 		mark->markShader = markShader;
-		mark->energy = energy;
 		mark->poly.numVerts = mf->numPoints;
 		mark->color[0] = red;
 		mark->color[1] = green;
@@ -224,24 +228,19 @@
 CG_AddMarks
 ===============
 */
-//#define	MARK_TOTAL_TIME		10000
-//#define	MARK_FADE_TIME		1000
+#define	MARK_TOTAL_TIME		10000
+#define	MARK_FADE_TIME		1000
 
 void CG_AddMarks( void ) {
 	int			j;
 	markPoly_t	*mp, *next;
 	int			t;
 	int			fade;
-	int MARK_TOTAL_TIME;
-	int MARK_FADE_TIME;
 
-	if ( !cg_marks.integer ) {
+	if ( !cg_addMarks.integer ) {
 		return;
 	}
 
-	MARK_TOTAL_TIME = cg_markTime.integer;
-	MARK_FADE_TIME = cg_markFadeTime.integer;
-
 	mp = cg_activeMarkPolys.nextMark;
 	for ( ; mp != &cg_activeMarkPolys ; mp = next ) {
 		// grab next now, so if the local entity is freed we
@@ -255,11 +254,9 @@
 		}
 
 		// fade out the energy bursts
-		//if ( mp->markShader == cgs.media.energyMarkShader ) {
-		if (mp->energy) {
+		if ( mp->markShader == cgs.media.energyMarkShader ) {
 
 			fade = 450 - 450 * ( (cg.time - mp->time ) / 3000.0 );
-			//Com_Printf("energy fade: %d\n", fade);
 			if ( fade < 255 ) {
 				if ( fade < 0 ) {
 					fade = 0;
@@ -278,141 +275,23 @@
 		t = mp->time + MARK_TOTAL_TIME - cg.time;
 		if ( t < MARK_FADE_TIME ) {
 			fade = 255 * t / MARK_FADE_TIME;
-			//Com_Printf("mark fade: %d  alphafade:%d\n", fade, mp->alphaFade);
 			if ( mp->alphaFade ) {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
 					mp->verts[j].modulate[3] = fade;
 				}
 			} else {
 				for ( j = 0 ; j < mp->poly.numVerts ; j++ ) {
-					if (mp->energy) {
-						mp->verts[j].modulate[0] *= fade;
-						mp->verts[j].modulate[1] *= fade;
-						mp->verts[j].modulate[2] *= fade;
-					} else {
-						mp->verts[j].modulate[0] = mp->color[0] * fade;
-						mp->verts[j].modulate[1] = mp->color[1] * fade;
-						mp->verts[j].modulate[2] = mp->color[2] * fade;
-					}
+					mp->verts[j].modulate[0] = mp->color[0] * fade;
+					mp->verts[j].modulate[1] = mp->color[1] * fade;
+					mp->verts[j].modulate[2] = mp->color[2] * fade;
 				}
 			}
 		}
 
-		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts, qfalse );
-	}
-}
 
-#if 0   // testing
-static float   frand(void)
-{
-	return (rand()&32767)* (1.0/32767);
-}
-
-static float   crand(void)
-{
-	return (rand()&32767)* (2.0/32767) - 1;
+		trap_R_AddPolyToScene( mp->markShader, mp->poly.numVerts, mp->verts );
+	}
 }
 
 
-void CG_Q2RailTrail (const vec3_t start, const vec3_t end)
-{
-	vec3_t          move;
-	vec3_t          vec;
-	float           len;
-	int                     j;
-	cparticle_t     *p;
-	float           dec;
-	vec3_t          right, up;
-	int                     i;
-	float           d, c, s;
-	vec3_t          dir;
-	byte            clr = 0x74;
-
-	VectorCopy (start, move);
-	VectorSubtract (end, start, vec);
-	len = VectorNormalize (vec);
-
-	MakeNormalVectors (vec, right, up);
-
-	//goto core;
-
-	for (i=0 ; i<len ; i++)
-        {
-			if (!free_particles)
-				return;
-
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			d = i * 0.1;
-			c = cos(d);
-			s = sin(d);
-
-			VectorScale (right, c, dir);
-			VectorMA (dir, s, up, dir);
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (1+frand()*0.2);
-			p->color = clr + (rand()&7);
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + dir[j]*3;
-					p->vel[j] = dir[j]*6;
-                }
-
-			VectorAdd (move, vec, move);
-        }
-
-//core:
-
-	dec = 0.75;
-	VectorScale (vec, dec, vec);
-	VectorCopy (start, move);
-
-	while (len > 0)
-        {
-			len -= dec;
-
-			if (!free_particles)
-				return;
-			p = free_particles;
-			free_particles = p->next;
-			p->next = active_particles;
-			active_particles = p;
-
-			p->time = cg.time;
-			VectorClear (p->accel);
-			//p->pshader = trap_R_RegisterShader("gfx/misc/tracer");
-			p->pshader = cgs.media.railRingsShader;
-			p->type = P_SPRITE;
-			p->width = 1;
-			p->height = 1;
-			p->endwidth = 1;
-			p->endheight = 1;
-
-			p->alpha = 1.0;
-			p->alphavel = -1.0 / (0.6+frand()*0.2);
-			p->color = 0x0 + (rand()&15);
-
-			for (j=0 ; j<3 ; j++)
-                {
-					p->org[j] = move[j] + crand()*3;
-					p->vel[j] = crand()*3;
-					p->accel[j] = 0;
-                }
-
-			VectorAdd (move, vec, move);
-        }
-}
-#endif
+// gutted to renderer

```
