# Diff: `code/game/bg_slidemove.c`
**Canonical:** `wolfcamql-src` (sha256 `5192dc5be547...`, 10017 bytes)

## Variants

### `quake3-source`  — sha256 `327fa83a0c52...`, 9140 bytes

_Diff stat: +18 / -50 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_slidemove.c	2026-04-16 20:02:25.191639300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\bg_slidemove.c	2026-04-16 20:02:19.903124100 +0100
@@ -15,14 +15,14 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 //
 // bg_slidemove.c -- part of bg_pmove functionality
 
-#include "../qcommon/q_shared.h"
+#include "q_shared.h"
 #include "bg_public.h"
 #include "bg_local.h"
 
@@ -158,10 +158,8 @@
 			// slide along the plane
 			PM_ClipVelocity (pm->ps->velocity, planes[i], clipVelocity, OVERCLIP );
 
-			if ( gravity ) {
-				// slide along the plane
-				PM_ClipVelocity (endVelocity, planes[i], endClipVelocity, OVERCLIP );
-			}
+			// slide along the plane
+			PM_ClipVelocity (endVelocity, planes[i], endClipVelocity, OVERCLIP );
 
 			// see if there is a second plane that the new move enters
 			for ( j = 0 ; j < numplanes ; j++ ) {
@@ -174,10 +172,7 @@
 
 				// try clipping the move to the plane
 				PM_ClipVelocity( clipVelocity, planes[j], clipVelocity, OVERCLIP );
-
-				if ( gravity ) {
-					PM_ClipVelocity( endClipVelocity, planes[j], endClipVelocity, OVERCLIP );
-				}
+				PM_ClipVelocity( endClipVelocity, planes[j], endClipVelocity, OVERCLIP );
 
 				// see if it goes back into the first clip plane
 				if ( DotProduct( clipVelocity, planes[i] ) >= 0 ) {
@@ -190,12 +185,10 @@
 				d = DotProduct( dir, pm->ps->velocity );
 				VectorScale( dir, d, clipVelocity );
 
-				if ( gravity ) {
-					CrossProduct (planes[i], planes[j], dir);
-					VectorNormalize( dir );
-					d = DotProduct( dir, endVelocity );
-					VectorScale( dir, d, endClipVelocity );
-				}
+				CrossProduct (planes[i], planes[j], dir);
+				VectorNormalize( dir );
+				d = DotProduct( dir, endVelocity );
+				VectorScale( dir, d, endClipVelocity );
 
 				// see if there is a third plane the the new move enters
 				for ( k = 0 ; k < numplanes ; k++ ) {
@@ -214,11 +207,7 @@
 
 			// if we have fixed all interactions, try another move
 			VectorCopy( clipVelocity, pm->ps->velocity );
-
-			if ( gravity ) {
-				VectorCopy( endClipVelocity, endVelocity );
-			}
-
+			VectorCopy( endClipVelocity, endVelocity );
 			break;
 		}
 	}
@@ -235,13 +224,6 @@
 	return ( bumpcount != 0 );
 }
 
-#ifdef CGAME
-extern void CG_AddClientSidePredictableEvent (int event, int eventParam);
-
-// cg. debugging
-//#include "../cgame/cg_local.h"
-#endif
-
 /*
 ==================
 PM_StepSlideMove
@@ -250,7 +232,7 @@
 */
 void PM_StepSlideMove( qboolean gravity ) {
 	vec3_t		start_o, start_v;
-//	vec3_t		down_o, down_v;
+	vec3_t		down_o, down_v;
 	trace_t		trace;
 //	float		down_dist, up_dist;
 //	vec3_t		delta, delta2;
@@ -274,8 +256,8 @@
 		return;
 	}
 
-	//VectorCopy (pm->ps->origin, down_o);
-	//VectorCopy (pm->ps->velocity, down_v);
+	VectorCopy (pm->ps->origin, down_o);
+	VectorCopy (pm->ps->velocity, down_v);
 
 	VectorCopy (start_o, up);
 	up[2] += STEPSIZE;
@@ -317,41 +299,27 @@
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:bend\n", c_pmove);
 		}
-	} else
+	} else 
 #endif
 	{
-		// 2019-04-09 ql seems to only do client side step prediction
-#ifdef CGAME
 		// use the step move
 		float	delta;
 
 		delta = pm->ps->origin[2] - start_o[2];
 		if ( delta > 2 ) {
-			int newEvent = EV_STEP_16;
-
 			if ( delta < 7 ) {
-				//PM_AddEvent( EV_STEP_4 );
-				newEvent = EV_STEP_4;
+				PM_AddEvent( EV_STEP_4 );
 			} else if ( delta < 11 ) {
-				//PM_AddEvent( EV_STEP_8 );
-				newEvent = EV_STEP_8;
+				PM_AddEvent( EV_STEP_8 );
 			} else if ( delta < 15 ) {
-				//PM_AddEvent( EV_STEP_12 );
-				newEvent = EV_STEP_12;
+				PM_AddEvent( EV_STEP_12 );
 			} else {
- 				//PM_AddEvent( EV_STEP_16 );
-				newEvent = EV_STEP_16;
+				PM_AddEvent( EV_STEP_16 );
 			}
-
-			// don't use BG_Add...() since it's only client side
-			//BG_AddPredictableEventToPlayerstate(newEvent, delta, pm->ps);
-			CG_AddClientSidePredictableEvent(newEvent, delta);
-			//Com_Printf("^5game step  pm->ps.eventSequence %d  serverTime %d  cg.time %d\n", pm->ps->eventSequence, cg.snap->serverTime, cg.time);
 		}
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:stepped\n", c_pmove);
 		}
-#endif
 	}
 }
 

```

### `ioquake3`  — sha256 `918d3d2255a3...`, 9304 bytes

_Diff stat: +5 / -26 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_slidemove.c	2026-04-16 20:02:25.191639300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\bg_slidemove.c	2026-04-16 20:02:21.540890600 +0100
@@ -235,13 +235,6 @@
 	return ( bumpcount != 0 );
 }
 
-#ifdef CGAME
-extern void CG_AddClientSidePredictableEvent (int event, int eventParam);
-
-// cg. debugging
-//#include "../cgame/cg_local.h"
-#endif
-
 /*
 ==================
 PM_StepSlideMove
@@ -317,41 +310,27 @@
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:bend\n", c_pmove);
 		}
-	} else
+	} else 
 #endif
 	{
-		// 2019-04-09 ql seems to only do client side step prediction
-#ifdef CGAME
 		// use the step move
 		float	delta;
 
 		delta = pm->ps->origin[2] - start_o[2];
 		if ( delta > 2 ) {
-			int newEvent = EV_STEP_16;
-
 			if ( delta < 7 ) {
-				//PM_AddEvent( EV_STEP_4 );
-				newEvent = EV_STEP_4;
+				PM_AddEvent( EV_STEP_4 );
 			} else if ( delta < 11 ) {
-				//PM_AddEvent( EV_STEP_8 );
-				newEvent = EV_STEP_8;
+				PM_AddEvent( EV_STEP_8 );
 			} else if ( delta < 15 ) {
-				//PM_AddEvent( EV_STEP_12 );
-				newEvent = EV_STEP_12;
+				PM_AddEvent( EV_STEP_12 );
 			} else {
- 				//PM_AddEvent( EV_STEP_16 );
-				newEvent = EV_STEP_16;
+				PM_AddEvent( EV_STEP_16 );
 			}
-
-			// don't use BG_Add...() since it's only client side
-			//BG_AddPredictableEventToPlayerstate(newEvent, delta, pm->ps);
-			CG_AddClientSidePredictableEvent(newEvent, delta);
-			//Com_Printf("^5game step  pm->ps.eventSequence %d  serverTime %d  cg.time %d\n", pm->ps->eventSequence, cg.snap->serverTime, cg.time);
 		}
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:stepped\n", c_pmove);
 		}
-#endif
 	}
 }
 

```

### `openarena-engine`  — sha256 `3409117de8fd...`, 9178 bytes

_Diff stat: +13 / -45 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_slidemove.c	2026-04-16 20:02:25.191639300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\bg_slidemove.c	2026-04-16 22:48:25.744536600 +0100
@@ -158,10 +158,8 @@
 			// slide along the plane
 			PM_ClipVelocity (pm->ps->velocity, planes[i], clipVelocity, OVERCLIP );
 
-			if ( gravity ) {
-				// slide along the plane
-				PM_ClipVelocity (endVelocity, planes[i], endClipVelocity, OVERCLIP );
-			}
+			// slide along the plane
+			PM_ClipVelocity (endVelocity, planes[i], endClipVelocity, OVERCLIP );
 
 			// see if there is a second plane that the new move enters
 			for ( j = 0 ; j < numplanes ; j++ ) {
@@ -174,10 +172,7 @@
 
 				// try clipping the move to the plane
 				PM_ClipVelocity( clipVelocity, planes[j], clipVelocity, OVERCLIP );
-
-				if ( gravity ) {
-					PM_ClipVelocity( endClipVelocity, planes[j], endClipVelocity, OVERCLIP );
-				}
+				PM_ClipVelocity( endClipVelocity, planes[j], endClipVelocity, OVERCLIP );
 
 				// see if it goes back into the first clip plane
 				if ( DotProduct( clipVelocity, planes[i] ) >= 0 ) {
@@ -190,12 +185,10 @@
 				d = DotProduct( dir, pm->ps->velocity );
 				VectorScale( dir, d, clipVelocity );
 
-				if ( gravity ) {
-					CrossProduct (planes[i], planes[j], dir);
-					VectorNormalize( dir );
-					d = DotProduct( dir, endVelocity );
-					VectorScale( dir, d, endClipVelocity );
-				}
+				CrossProduct (planes[i], planes[j], dir);
+				VectorNormalize( dir );
+				d = DotProduct( dir, endVelocity );
+				VectorScale( dir, d, endClipVelocity );
 
 				// see if there is a third plane the the new move enters
 				for ( k = 0 ; k < numplanes ; k++ ) {
@@ -214,11 +207,7 @@
 
 			// if we have fixed all interactions, try another move
 			VectorCopy( clipVelocity, pm->ps->velocity );
-
-			if ( gravity ) {
-				VectorCopy( endClipVelocity, endVelocity );
-			}
-
+			VectorCopy( endClipVelocity, endVelocity );
 			break;
 		}
 	}
@@ -235,13 +224,6 @@
 	return ( bumpcount != 0 );
 }
 
-#ifdef CGAME
-extern void CG_AddClientSidePredictableEvent (int event, int eventParam);
-
-// cg. debugging
-//#include "../cgame/cg_local.h"
-#endif
-
 /*
 ==================
 PM_StepSlideMove
@@ -317,41 +299,27 @@
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:bend\n", c_pmove);
 		}
-	} else
+	} else 
 #endif
 	{
-		// 2019-04-09 ql seems to only do client side step prediction
-#ifdef CGAME
 		// use the step move
 		float	delta;
 
 		delta = pm->ps->origin[2] - start_o[2];
 		if ( delta > 2 ) {
-			int newEvent = EV_STEP_16;
-
 			if ( delta < 7 ) {
-				//PM_AddEvent( EV_STEP_4 );
-				newEvent = EV_STEP_4;
+				PM_AddEvent( EV_STEP_4 );
 			} else if ( delta < 11 ) {
-				//PM_AddEvent( EV_STEP_8 );
-				newEvent = EV_STEP_8;
+				PM_AddEvent( EV_STEP_8 );
 			} else if ( delta < 15 ) {
-				//PM_AddEvent( EV_STEP_12 );
-				newEvent = EV_STEP_12;
+				PM_AddEvent( EV_STEP_12 );
 			} else {
- 				//PM_AddEvent( EV_STEP_16 );
-				newEvent = EV_STEP_16;
+				PM_AddEvent( EV_STEP_16 );
 			}
-
-			// don't use BG_Add...() since it's only client side
-			//BG_AddPredictableEventToPlayerstate(newEvent, delta, pm->ps);
-			CG_AddClientSidePredictableEvent(newEvent, delta);
-			//Com_Printf("^5game step  pm->ps.eventSequence %d  serverTime %d  cg.time %d\n", pm->ps->eventSequence, cg.snap->serverTime, cg.time);
 		}
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:stepped\n", c_pmove);
 		}
-#endif
 	}
 }
 

```

### `openarena-gamecode`  — sha256 `754ff2b3b836...`, 9328 bytes

_Diff stat: +12 / -29 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_slidemove.c	2026-04-16 20:02:25.191639300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\bg_slidemove.c	2026-04-16 22:48:24.165478600 +0100
@@ -235,13 +235,6 @@
 	return ( bumpcount != 0 );
 }
 
-#ifdef CGAME
-extern void CG_AddClientSidePredictableEvent (int event, int eventParam);
-
-// cg. debugging
-//#include "../cgame/cg_local.h"
-#endif
-
 /*
 ==================
 PM_StepSlideMove
@@ -250,7 +243,9 @@
 */
 void PM_StepSlideMove( qboolean gravity ) {
 	vec3_t		start_o, start_v;
-//	vec3_t		down_o, down_v;
+#if 0
+	vec3_t		down_o, down_v;
+#endif
 	trace_t		trace;
 //	float		down_dist, up_dist;
 //	vec3_t		delta, delta2;
@@ -274,8 +269,10 @@
 		return;
 	}
 
-	//VectorCopy (pm->ps->origin, down_o);
-	//VectorCopy (pm->ps->velocity, down_v);
+#if 0
+	VectorCopy (pm->ps->origin, down_o);
+	VectorCopy (pm->ps->velocity, down_v);
+#endif
 
 	VectorCopy (start_o, up);
 	up[2] += STEPSIZE;
@@ -317,41 +314,27 @@
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:bend\n", c_pmove);
 		}
-	} else
+	} else 
 #endif
 	{
-		// 2019-04-09 ql seems to only do client side step prediction
-#ifdef CGAME
 		// use the step move
 		float	delta;
 
 		delta = pm->ps->origin[2] - start_o[2];
 		if ( delta > 2 ) {
-			int newEvent = EV_STEP_16;
-
 			if ( delta < 7 ) {
-				//PM_AddEvent( EV_STEP_4 );
-				newEvent = EV_STEP_4;
+				PM_AddEvent( EV_STEP_4 );
 			} else if ( delta < 11 ) {
-				//PM_AddEvent( EV_STEP_8 );
-				newEvent = EV_STEP_8;
+				PM_AddEvent( EV_STEP_8 );
 			} else if ( delta < 15 ) {
-				//PM_AddEvent( EV_STEP_12 );
-				newEvent = EV_STEP_12;
+				PM_AddEvent( EV_STEP_12 );
 			} else {
- 				//PM_AddEvent( EV_STEP_16 );
-				newEvent = EV_STEP_16;
+				PM_AddEvent( EV_STEP_16 );
 			}
-
-			// don't use BG_Add...() since it's only client side
-			//BG_AddPredictableEventToPlayerstate(newEvent, delta, pm->ps);
-			CG_AddClientSidePredictableEvent(newEvent, delta);
-			//Com_Printf("^5game step  pm->ps.eventSequence %d  serverTime %d  cg.time %d\n", pm->ps->eventSequence, cg.snap->serverTime, cg.time);
 		}
 		if ( pm->debugLevel ) {
 			Com_Printf("%i:stepped\n", c_pmove);
 		}
-#endif
 	}
 }
 

```
