# Diff: `code/cgame/cg_predict.c`
**Canonical:** `wolfcamql-src` (sha256 `d457e0923ebc...`, 20820 bytes)

## Variants

### `quake3-source`  — sha256 `722364556e9e...`, 17672 bytes

_Diff stat: +56 / -140 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_predict.c	2026-04-16 20:02:25.148527000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\cgame\cg_predict.c	2026-04-16 20:02:19.884537500 +0100
@@ -1,4 +1,24 @@
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
+along with Foobar; if not, write to the Free Software
+Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
+===========================================================================
+*/
 //
 // cg_predict.c -- this file generates cg.predictedPlayerState by either
 // interpolating between snapshots from the server or locally predicting
@@ -7,21 +27,12 @@
 
 #include "cg_local.h"
 
-#include "cg_ents.h"
-#include "cg_main.h"
-#include "cg_players.h"
-#include "cg_playerstate.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-int cg_numSolidEntities;
-centity_t *cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
-
 static	pmove_t		cg_pmove;
 
+static	int			cg_numSolidEntities;
+static	centity_t	*cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
 static	int			cg_numTriggerEntities;
-static centity_t *cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
+static	centity_t	*cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
 
 /*
 ====================
@@ -35,9 +46,8 @@
 void CG_BuildSolidList( void ) {
 	int			i;
 	centity_t	*cent;
-	const snapshot_t	*snap;
-	const entityState_t	*ent;
-	clipHandle_t 	cmodel;
+	snapshot_t	*snap;
+	entityState_t	*ent;
 
 	cg_numSolidEntities = 0;
 	cg_numTriggerEntities = 0;
@@ -48,16 +58,6 @@
 		snap = cg.snap;
 	}
 
-#if 0
-	if (snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR) {
-		cg_solidEntities[cg_numSolidEntities] = &cg_entities[snap->ps.clientNum];
-		cg_numSolidEntities++;
-		cg_entities[snap->ps.clientNum].nextState.solid = 4200463;
-		Com_Printf("adding %s to solid list\n", cgs.clientinfo[snap->ps.clientNum].name);
-
-	}
-#endif
-
 	for ( i = 0 ; i < snap->numEntities ; i++ ) {
 		cent = &cg_entities[ snap->entities[ i ].number ];
 		ent = &cent->currentState;
@@ -69,15 +69,6 @@
 		}
 
 		if ( cent->nextState.solid ) {
-			//Com_Printf("solid: %d\n", cent->nextState.solid);
-			//FIXME hack for broken demo playback
-			if (cent->nextState.solid == SOLID_BMODEL ) {
-				// special value for bmodel
-				cmodel = trap_CM_InlineModel( ent->modelindex );
-				if (cmodel < 0) {
-					continue;
-				}
-			}
 			cg_solidEntities[cg_numSolidEntities] = cent;
 			cg_numSolidEntities++;
 			continue;
@@ -95,12 +86,11 @@
 							int skipNumber, int mask, trace_t *tr ) {
 	int			i, x, zd, zu;
 	trace_t		trace;
-	const entityState_t	*ent;
+	entityState_t	*ent;
 	clipHandle_t 	cmodel;
 	vec3_t		bmins, bmaxs;
 	vec3_t		origin, angles;
-	const centity_t	*cent;
-	vec3_t tmpOrigin;
+	centity_t	*cent;
 
 	for ( i = 0 ; i < cg_numSolidEntities ; i++ ) {
 		cent = cg_solidEntities[ i ];
@@ -112,17 +102,7 @@
 
 		if ( ent->solid == SOLID_BMODEL ) {
 			// special value for bmodel
-			if (SC_Cvar_Get_Int("debug_bmodel")) {
-				CG_FloatNumber(ent->number, ent->origin, RF_DEPTHHACK, NULL, 1.0);
-				VectorCopy(ent->origin, tmpOrigin);
-				tmpOrigin[2] += 20;
-				CG_FloatNumber(ent->modelindex, tmpOrigin, RF_DEPTHHACK, NULL, 1.0);
-				Com_Printf("^4%d  modelindex %d\n", ent->number, ent->modelindex);
-			}
 			cmodel = trap_CM_InlineModel( ent->modelindex );
-			if (cmodel < 0) {
-				continue;
-			}
 			VectorCopy( cent->lerpAngles, angles );
 			BG_EvaluateTrajectory( &cent->currentState.pos, cg.physicsTime, origin );
 		} else {
@@ -181,8 +161,8 @@
 */
 int		CG_PointContents( const vec3_t point, int passEntityNum ) {
 	int			i;
-	const entityState_t	*ent;
-	const centity_t	*cent;
+	entityState_t	*ent;
+	centity_t	*cent;
 	clipHandle_t cmodel;
 	int			contents;
 
@@ -206,7 +186,7 @@
 			continue;
 		}
 
-		contents |= trap_CM_TransformedPointContents( point, cmodel, cent->lerpOrigin, cent->lerpAngles );
+		contents |= trap_CM_TransformedPointContents( point, cmodel, ent->origin, ent->angles );
 	}
 
 	return contents;
@@ -222,11 +202,10 @@
 ========================
 */
 static void CG_InterpolatePlayerState( qboolean grabAngles ) {
-	double			f;
+	float			f;
 	int				i;
 	playerState_t	*out;
-	const snapshot_t		*prev, *next;
-	//static int lastCgtime = 0;  // testing
+	snapshot_t		*prev, *next;
 
 	out = &cg.predictedPlayerState;
 	prev = cg.snap;
@@ -234,17 +213,6 @@
 
 	*out = cg.snap->ps;
 
-	//FIXME here better
-#if 0
-	if (cg_demoSmoothing.integer  &&  cg.noMove) {
-		//Com_Printf("CG_InterpolatePlayerState  cg.snap->serverTime %d\n", cg.snap->serverTime);
-		if (cg.nextNextSnapValid) {
-			next = &cg.nextNextSnap;
-			Com_Printf("^2yes\n");
-		}
-	}
-#endif
-
 	// if we are still allowing local input, short circuit the view angles
 	if ( grabAngles ) {
 		usercmd_t	cmd;
@@ -253,34 +221,19 @@
 		cmdNum = trap_GetCurrentCmdNumber();
 		trap_GetUserCmd( cmdNum, &cmd );
 
-		PM_UpdateViewAngles( out, &cmd, qfalse );
+		PM_UpdateViewAngles( out, &cmd );
 	}
 
 	// if the next frame is a teleport, we can't lerp to it
 	if ( cg.nextFrameTeleport ) {
-		//Com_Printf("nextframeteleport %d\n", cg.nextSnap->serverTime);
 		return;
 	}
 
-	if (!next) {
-		if (!SC_Cvar_Get_Int("cl_freezeDemo")  &&  SC_Cvar_Get_Float("timescale") == 1.0) {
-			//Com_Printf("!next\n");
-		}
+	if ( !next || next->serverTime <= prev->serverTime ) {
 		return;
 	}
 
-	if (next->serverTime <= prev->serverTime) {
-		Com_Printf("next->serverTime <= prev->serverTime  %d  %d\n", next->serverTime, prev->serverTime);
-		return;
-	}
-
-	//f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
-	//Com_Printf("interp(1)  %f  %s\n", f, (cg.time - lastCgtime) ? "*" : "");
-	//lastCgtime = cg.time;
-
-	//f = (float)( (float)cg.time + (float)cg.ioverf / SUBTIME_RESOLUTION  - (float)prev->serverTime ) / (float)( next->serverTime - prev->serverTime );
-	f = (cg.ftime - (double)prev->serverTime ) / (double)(next->serverTime - prev->serverTime);
-	//Com_Printf("interp(2)  %f\n", f);
+	f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
 
 	i = next->ps.bobCycle;
 	if ( i < prev->ps.bobCycle ) {
@@ -291,10 +244,10 @@
 	for ( i = 0 ; i < 3 ; i++ ) {
 		out->origin[i] = prev->ps.origin[i] + f * (next->ps.origin[i] - prev->ps.origin[i] );
 		if ( !grabAngles ) {
-			out->viewangles[i] = LerpAngle(
+			out->viewangles[i] = LerpAngle( 
 				prev->ps.viewangles[i], next->ps.viewangles[i], f );
 		}
-		out->velocity[i] = prev->ps.velocity[i] +
+		out->velocity[i] = prev->ps.velocity[i] + 
 			f * (next->ps.velocity[i] - prev->ps.velocity[i] );
 	}
 
@@ -306,17 +259,11 @@
 ===================
 */
 static void CG_TouchItem( centity_t *cent ) {
-	const gitem_t		*item;
+	gitem_t		*item;
 
 	if ( !cg_predictItems.integer ) {
 		return;
 	}
-
-	// hack for ql timer pies which still send items with EF_NODRAW
-	if (cent->nextState.eFlags & EF_NODRAW) {
-		return;
-	}
-
 	if ( !BG_PlayerTouchesItem( &cg.predictedPlayerState, &cent->currentState, cg.time ) ) {
 		return;
 	}
@@ -332,22 +279,23 @@
 
 	item = &bg_itemlist[ cent->currentState.modelindex ];
 
-	// Special case for flags.
+	// Special case for flags.  
 	// We don't predict touching our own flag
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( cgs.gametype == GT_1FCTF ) {
-		if( item->giType == IT_TEAM && item->giTag != PW_NEUTRALFLAG ) {
+		if( item->giTag != PW_NEUTRALFLAG ) {
 			return;
 		}
 	}
-
-	if(cgs.gametype == GT_CTF  ||  cgs.gametype == GT_CTFS  ||  cgs.gametype == GT_NTF) {
+	if( cgs.gametype == GT_CTF || cgs.gametype == GT_HARVESTER ) {
+#else
+	if( cgs.gametype == GT_CTF ) {
 #endif
 		if (cg.predictedPlayerState.persistant[PERS_TEAM] == TEAM_RED &&
-			item->giType == IT_TEAM && item->giTag == PW_REDFLAG)
+			item->giTag == PW_REDFLAG)
 			return;
 		if (cg.predictedPlayerState.persistant[PERS_TEAM] == TEAM_BLUE &&
-			item->giType == IT_TEAM && item->giTag == PW_BLUEFLAG)
+			item->giTag == PW_BLUEFLAG)
 			return;
 	}
 
@@ -360,7 +308,7 @@
 	// don't touch it again this prediction
 	cent->miscTime = cg.time;
 
-	// if it's a weapon, give them some predicted ammo so the autoswitch will work
+	// if its a weapon, give them some predicted ammo so the autoswitch will work
 	if ( item->giType == IT_WEAPON ) {
 		cg.predictedPlayerState.stats[ STAT_WEAPONS ] |= 1 << item->giTag;
 		if ( !cg.predictedPlayerState.ammo[ item->giTag ] ) {
@@ -414,7 +362,7 @@
 			continue;
 		}
 
-		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin,
+		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin, 
 			cg_pmove.mins, cg_pmove.maxs, cmodel, -1 );
 
 		if ( !trace.startsolid ) {
@@ -422,13 +370,8 @@
 		}
 
 		if ( ent->eType == ET_TELEPORT_TRIGGER ) {
-			if (SC_Cvar_Get_Int("r_teleporterFlash") == 2) {
-				cg.hyperspace = qfalse;
-			} else {
-				cg.hyperspace = qtrue;
-			}
+			cg.hyperspace = qtrue;
 		} else if ( ent->eType == ET_PUSH_TRIGGER ) {
-			//Com_Printf("bg touch jump pad\n");
 			BG_TouchJumpPad( &cg.predictedPlayerState, ent );
 		}
 	}
@@ -475,11 +418,6 @@
 	usercmd_t	oldestCmd;
 	usercmd_t	latestCmd;
 
-	if (cg.freezeEntity[cg.snap->ps.clientNum]) {
-		cg.predictedPlayerState = cg.freezePs;
-		return;
-	}
-
 	cg.hyperspace = qfalse;	// will be set if touching a trigger_teleport
 
 	// if this is the first frame we must guarantee
@@ -516,16 +454,11 @@
 	if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR ) {
 		cg_pmove.tracemask &= ~CONTENTS_BODY;	// spectators can fly through bodies
 	}
-	//cg_pmove.noFootsteps = 0;  //FIXME  ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
-	cg_pmove.noFootsteps = (cgs.dmflags & DF_NO_FOOTSTEPS);
+	cg_pmove.noFootsteps = ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
 
 	// save the state before the pmove so we can detect transitions
 	oldPlayerState = cg.predictedPlayerState;
 
-	memcpy(cg.clientSidePredictableEventsOld, cg.clientSidePredictableEvents, sizeof(cg.clientSidePredictableEventsOld));
-	memcpy(cg.clientSidePredictableEventParamsOld, cg.clientSidePredictableEventParams, sizeof(cg.clientSidePredictableEventParamsOld));
-	cg.clientSideEventSequenceOld = cg.clientSideEventSequence;
-
 	current = trap_GetCurrentCmdNumber();
 
 	// if we don't have the commands right after the snapshot, we
@@ -533,7 +466,7 @@
 	// the last good position we had
 	cmdNum = current - CMD_BACKUP + 1;
 	trap_GetUserCmd( cmdNum, &oldestCmd );
-	if ( oldestCmd.serverTime > cg.snap->ps.commandTime
+	if ( oldestCmd.serverTime > cg.snap->ps.commandTime 
 		&& oldestCmd.serverTime < cg.time ) {	// special check for map_restart
 		if ( cg_showmiss.integer ) {
 			CG_Printf ("exceeded PACKET_BACKUP on commands\n");
@@ -555,17 +488,12 @@
 		cg.predictedPlayerState = cg.snap->ps;
 		cg.physicsTime = cg.snap->serverTime;
 	}
-	memset(cg.clientSidePredictableEvents, 0, sizeof(cg.clientSidePredictableEvents));
-	memset(cg.clientSidePredictableEventParams, 0, sizeof(cg.clientSidePredictableEventParams));
-	cg.clientSideEventSequence = 0;
 
 	if ( pmove_msec.integer < 8 ) {
 		trap_Cvar_Set("pmove_msec", "8");
-		trap_Cvar_Update(&pmove_msec);
 	}
 	else if (pmove_msec.integer > 33) {
 		trap_Cvar_Set("pmove_msec", "33");
-		trap_Cvar_Update(&pmove_msec);
 	}
 
 	cg_pmove.pmove_fixed = pmove_fixed.integer;// | cg_pmove_fixed.integer;
@@ -578,7 +506,7 @@
 		trap_GetUserCmd( cmdNum, &cg_pmove.cmd );
 
 		if ( cg_pmove.pmove_fixed ) {
-			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd, qfalse );
+			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd );
 		}
 
 		// don't do anything if the time is before the snapshot player time
@@ -608,9 +536,9 @@
 				}
 				cg.thisFrameTeleport = qfalse;
 			} else {
-				vec3_t	adjusted, new_angles;
+				vec3_t	adjusted;
 				CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
-										   cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted, cg.foverf, cg.predictedPlayerState.viewangles, new_angles );
+					cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted );
 
 				if ( cg_showmiss.integer ) {
 					if (!VectorCompare( oldPlayerState.origin, adjusted )) {
@@ -653,18 +581,6 @@
 			cg_pmove.cmd.serverTime = ((cg_pmove.cmd.serverTime + pmove_msec.integer-1) / pmove_msec.integer) * pmove_msec.integer;
 		}
 
-		// camera script
-		if (cgs.scrFadeAlphaCurrent) {
-			cg_pmove.cmd.buttons = 0;
-			cg_pmove.cmd.forwardmove = 0;
-			cg_pmove.cmd.rightmove = 0;
-			cg_pmove.cmd.upmove = 0;
-			if (cg_pmove.cmd.serverTime - cg.predictedPlayerState.commandTime > 1)
-				cg_pmove.cmd.serverTime = cg.predictedPlayerState.commandTime + 1;
-		}
-		// end camera script
-
-		//Com_Printf("cgame pmove cg.time %d  serverTime %d  eventSequence %d\n", cg.time, cg.snap->serverTime, cg.predictedPlayerState.eventSequence);
 		Pmove (&cg_pmove);
 
 		moved = qtrue;
@@ -690,7 +606,7 @@
 	// adjust for the movement of the groundentity
 	CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
 		cg.predictedPlayerState.groundEntityNum, 
-							   cg.physicsTime, cg.time, cg.predictedPlayerState.origin, cg.foverf, cg.predictedPlayerState.viewangles, cg.predictedPlayerState.viewangles );
+		cg.physicsTime, cg.time, cg.predictedPlayerState.origin );
 
 	if ( cg_showmiss.integer ) {
 		if (cg.predictedPlayerState.eventSequence > oldPlayerState.eventSequence + MAX_PS_EVENTS) {

```

### `ioquake3`  — sha256 `ca3d5bfb5568...`, 17910 bytes

_Diff stat: +49 / -133 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_predict.c	2026-04-16 20:02:25.148527000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\cgame\cg_predict.c	2026-04-16 20:02:21.523053400 +0100
@@ -1,4 +1,24 @@
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
 // cg_predict.c -- this file generates cg.predictedPlayerState by either
 // interpolating between snapshots from the server or locally predicting
@@ -7,21 +27,12 @@
 
 #include "cg_local.h"
 
-#include "cg_ents.h"
-#include "cg_main.h"
-#include "cg_players.h"
-#include "cg_playerstate.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-int cg_numSolidEntities;
-centity_t *cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
-
 static	pmove_t		cg_pmove;
 
+static	int			cg_numSolidEntities;
+static	centity_t	*cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
 static	int			cg_numTriggerEntities;
-static centity_t *cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
+static	centity_t	*cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
 
 /*
 ====================
@@ -35,9 +46,8 @@
 void CG_BuildSolidList( void ) {
 	int			i;
 	centity_t	*cent;
-	const snapshot_t	*snap;
-	const entityState_t	*ent;
-	clipHandle_t 	cmodel;
+	snapshot_t	*snap;
+	entityState_t	*ent;
 
 	cg_numSolidEntities = 0;
 	cg_numTriggerEntities = 0;
@@ -48,16 +58,6 @@
 		snap = cg.snap;
 	}
 
-#if 0
-	if (snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR) {
-		cg_solidEntities[cg_numSolidEntities] = &cg_entities[snap->ps.clientNum];
-		cg_numSolidEntities++;
-		cg_entities[snap->ps.clientNum].nextState.solid = 4200463;
-		Com_Printf("adding %s to solid list\n", cgs.clientinfo[snap->ps.clientNum].name);
-
-	}
-#endif
-
 	for ( i = 0 ; i < snap->numEntities ; i++ ) {
 		cent = &cg_entities[ snap->entities[ i ].number ];
 		ent = &cent->currentState;
@@ -69,15 +69,6 @@
 		}
 
 		if ( cent->nextState.solid ) {
-			//Com_Printf("solid: %d\n", cent->nextState.solid);
-			//FIXME hack for broken demo playback
-			if (cent->nextState.solid == SOLID_BMODEL ) {
-				// special value for bmodel
-				cmodel = trap_CM_InlineModel( ent->modelindex );
-				if (cmodel < 0) {
-					continue;
-				}
-			}
 			cg_solidEntities[cg_numSolidEntities] = cent;
 			cg_numSolidEntities++;
 			continue;
@@ -95,12 +86,11 @@
 							int skipNumber, int mask, trace_t *tr ) {
 	int			i, x, zd, zu;
 	trace_t		trace;
-	const entityState_t	*ent;
+	entityState_t	*ent;
 	clipHandle_t 	cmodel;
 	vec3_t		bmins, bmaxs;
 	vec3_t		origin, angles;
-	const centity_t	*cent;
-	vec3_t tmpOrigin;
+	centity_t	*cent;
 
 	for ( i = 0 ; i < cg_numSolidEntities ; i++ ) {
 		cent = cg_solidEntities[ i ];
@@ -112,17 +102,7 @@
 
 		if ( ent->solid == SOLID_BMODEL ) {
 			// special value for bmodel
-			if (SC_Cvar_Get_Int("debug_bmodel")) {
-				CG_FloatNumber(ent->number, ent->origin, RF_DEPTHHACK, NULL, 1.0);
-				VectorCopy(ent->origin, tmpOrigin);
-				tmpOrigin[2] += 20;
-				CG_FloatNumber(ent->modelindex, tmpOrigin, RF_DEPTHHACK, NULL, 1.0);
-				Com_Printf("^4%d  modelindex %d\n", ent->number, ent->modelindex);
-			}
 			cmodel = trap_CM_InlineModel( ent->modelindex );
-			if (cmodel < 0) {
-				continue;
-			}
 			VectorCopy( cent->lerpAngles, angles );
 			BG_EvaluateTrajectory( &cent->currentState.pos, cg.physicsTime, origin );
 		} else {
@@ -181,8 +161,8 @@
 */
 int		CG_PointContents( const vec3_t point, int passEntityNum ) {
 	int			i;
-	const entityState_t	*ent;
-	const centity_t	*cent;
+	entityState_t	*ent;
+	centity_t	*cent;
 	clipHandle_t cmodel;
 	int			contents;
 
@@ -222,11 +202,10 @@
 ========================
 */
 static void CG_InterpolatePlayerState( qboolean grabAngles ) {
-	double			f;
+	float			f;
 	int				i;
 	playerState_t	*out;
-	const snapshot_t		*prev, *next;
-	//static int lastCgtime = 0;  // testing
+	snapshot_t		*prev, *next;
 
 	out = &cg.predictedPlayerState;
 	prev = cg.snap;
@@ -234,17 +213,6 @@
 
 	*out = cg.snap->ps;
 
-	//FIXME here better
-#if 0
-	if (cg_demoSmoothing.integer  &&  cg.noMove) {
-		//Com_Printf("CG_InterpolatePlayerState  cg.snap->serverTime %d\n", cg.snap->serverTime);
-		if (cg.nextNextSnapValid) {
-			next = &cg.nextNextSnap;
-			Com_Printf("^2yes\n");
-		}
-	}
-#endif
-
 	// if we are still allowing local input, short circuit the view angles
 	if ( grabAngles ) {
 		usercmd_t	cmd;
@@ -253,34 +221,19 @@
 		cmdNum = trap_GetCurrentCmdNumber();
 		trap_GetUserCmd( cmdNum, &cmd );
 
-		PM_UpdateViewAngles( out, &cmd, qfalse );
+		PM_UpdateViewAngles( out, &cmd );
 	}
 
 	// if the next frame is a teleport, we can't lerp to it
 	if ( cg.nextFrameTeleport ) {
-		//Com_Printf("nextframeteleport %d\n", cg.nextSnap->serverTime);
 		return;
 	}
 
-	if (!next) {
-		if (!SC_Cvar_Get_Int("cl_freezeDemo")  &&  SC_Cvar_Get_Float("timescale") == 1.0) {
-			//Com_Printf("!next\n");
-		}
+	if ( !next || next->serverTime <= prev->serverTime ) {
 		return;
 	}
 
-	if (next->serverTime <= prev->serverTime) {
-		Com_Printf("next->serverTime <= prev->serverTime  %d  %d\n", next->serverTime, prev->serverTime);
-		return;
-	}
-
-	//f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
-	//Com_Printf("interp(1)  %f  %s\n", f, (cg.time - lastCgtime) ? "*" : "");
-	//lastCgtime = cg.time;
-
-	//f = (float)( (float)cg.time + (float)cg.ioverf / SUBTIME_RESOLUTION  - (float)prev->serverTime ) / (float)( next->serverTime - prev->serverTime );
-	f = (cg.ftime - (double)prev->serverTime ) / (double)(next->serverTime - prev->serverTime);
-	//Com_Printf("interp(2)  %f\n", f);
+	f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
 
 	i = next->ps.bobCycle;
 	if ( i < prev->ps.bobCycle ) {
@@ -291,10 +244,10 @@
 	for ( i = 0 ; i < 3 ; i++ ) {
 		out->origin[i] = prev->ps.origin[i] + f * (next->ps.origin[i] - prev->ps.origin[i] );
 		if ( !grabAngles ) {
-			out->viewangles[i] = LerpAngle(
+			out->viewangles[i] = LerpAngle( 
 				prev->ps.viewangles[i], next->ps.viewangles[i], f );
 		}
-		out->velocity[i] = prev->ps.velocity[i] +
+		out->velocity[i] = prev->ps.velocity[i] + 
 			f * (next->ps.velocity[i] - prev->ps.velocity[i] );
 	}
 
@@ -306,17 +259,11 @@
 ===================
 */
 static void CG_TouchItem( centity_t *cent ) {
-	const gitem_t		*item;
+	gitem_t		*item;
 
 	if ( !cg_predictItems.integer ) {
 		return;
 	}
-
-	// hack for ql timer pies which still send items with EF_NODRAW
-	if (cent->nextState.eFlags & EF_NODRAW) {
-		return;
-	}
-
 	if ( !BG_PlayerTouchesItem( &cg.predictedPlayerState, &cent->currentState, cg.time ) ) {
 		return;
 	}
@@ -332,17 +279,16 @@
 
 	item = &bg_itemlist[ cent->currentState.modelindex ];
 
-	// Special case for flags.
+	// Special case for flags.  
 	// We don't predict touching our own flag
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( cgs.gametype == GT_1FCTF ) {
 		if( item->giType == IT_TEAM && item->giTag != PW_NEUTRALFLAG ) {
 			return;
 		}
 	}
-
-	if(cgs.gametype == GT_CTF  ||  cgs.gametype == GT_CTFS  ||  cgs.gametype == GT_NTF) {
 #endif
+	if( cgs.gametype == GT_CTF ) {
 		if (cg.predictedPlayerState.persistant[PERS_TEAM] == TEAM_RED &&
 			item->giType == IT_TEAM && item->giTag == PW_REDFLAG)
 			return;
@@ -414,7 +360,7 @@
 			continue;
 		}
 
-		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin,
+		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin, 
 			cg_pmove.mins, cg_pmove.maxs, cmodel, -1 );
 
 		if ( !trace.startsolid ) {
@@ -422,13 +368,8 @@
 		}
 
 		if ( ent->eType == ET_TELEPORT_TRIGGER ) {
-			if (SC_Cvar_Get_Int("r_teleporterFlash") == 2) {
-				cg.hyperspace = qfalse;
-			} else {
-				cg.hyperspace = qtrue;
-			}
+			cg.hyperspace = qtrue;
 		} else if ( ent->eType == ET_PUSH_TRIGGER ) {
-			//Com_Printf("bg touch jump pad\n");
 			BG_TouchJumpPad( &cg.predictedPlayerState, ent );
 		}
 	}
@@ -475,11 +416,6 @@
 	usercmd_t	oldestCmd;
 	usercmd_t	latestCmd;
 
-	if (cg.freezeEntity[cg.snap->ps.clientNum]) {
-		cg.predictedPlayerState = cg.freezePs;
-		return;
-	}
-
 	cg.hyperspace = qfalse;	// will be set if touching a trigger_teleport
 
 	// if this is the first frame we must guarantee
@@ -516,16 +452,11 @@
 	if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR ) {
 		cg_pmove.tracemask &= ~CONTENTS_BODY;	// spectators can fly through bodies
 	}
-	//cg_pmove.noFootsteps = 0;  //FIXME  ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
-	cg_pmove.noFootsteps = (cgs.dmflags & DF_NO_FOOTSTEPS);
+	cg_pmove.noFootsteps = ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
 
 	// save the state before the pmove so we can detect transitions
 	oldPlayerState = cg.predictedPlayerState;
 
-	memcpy(cg.clientSidePredictableEventsOld, cg.clientSidePredictableEvents, sizeof(cg.clientSidePredictableEventsOld));
-	memcpy(cg.clientSidePredictableEventParamsOld, cg.clientSidePredictableEventParams, sizeof(cg.clientSidePredictableEventParamsOld));
-	cg.clientSideEventSequenceOld = cg.clientSideEventSequence;
-
 	current = trap_GetCurrentCmdNumber();
 
 	// if we don't have the commands right after the snapshot, we
@@ -533,7 +464,7 @@
 	// the last good position we had
 	cmdNum = current - CMD_BACKUP + 1;
 	trap_GetUserCmd( cmdNum, &oldestCmd );
-	if ( oldestCmd.serverTime > cg.snap->ps.commandTime
+	if ( oldestCmd.serverTime > cg.snap->ps.commandTime 
 		&& oldestCmd.serverTime < cg.time ) {	// special check for map_restart
 		if ( cg_showmiss.integer ) {
 			CG_Printf ("exceeded PACKET_BACKUP on commands\n");
@@ -555,9 +486,6 @@
 		cg.predictedPlayerState = cg.snap->ps;
 		cg.physicsTime = cg.snap->serverTime;
 	}
-	memset(cg.clientSidePredictableEvents, 0, sizeof(cg.clientSidePredictableEvents));
-	memset(cg.clientSidePredictableEventParams, 0, sizeof(cg.clientSidePredictableEventParams));
-	cg.clientSideEventSequence = 0;
 
 	if ( pmove_msec.integer < 8 ) {
 		trap_Cvar_Set("pmove_msec", "8");
@@ -578,7 +506,7 @@
 		trap_GetUserCmd( cmdNum, &cg_pmove.cmd );
 
 		if ( cg_pmove.pmove_fixed ) {
-			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd, qfalse );
+			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd );
 		}
 
 		// don't do anything if the time is before the snapshot player time
@@ -608,9 +536,9 @@
 				}
 				cg.thisFrameTeleport = qfalse;
 			} else {
-				vec3_t	adjusted, new_angles;
+				vec3_t adjusted, new_angles;
 				CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
-										   cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted, cg.foverf, cg.predictedPlayerState.viewangles, new_angles );
+				cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted, cg.predictedPlayerState.viewangles, new_angles);
 
 				if ( cg_showmiss.integer ) {
 					if (!VectorCompare( oldPlayerState.origin, adjusted )) {
@@ -653,18 +581,6 @@
 			cg_pmove.cmd.serverTime = ((cg_pmove.cmd.serverTime + pmove_msec.integer-1) / pmove_msec.integer) * pmove_msec.integer;
 		}
 
-		// camera script
-		if (cgs.scrFadeAlphaCurrent) {
-			cg_pmove.cmd.buttons = 0;
-			cg_pmove.cmd.forwardmove = 0;
-			cg_pmove.cmd.rightmove = 0;
-			cg_pmove.cmd.upmove = 0;
-			if (cg_pmove.cmd.serverTime - cg.predictedPlayerState.commandTime > 1)
-				cg_pmove.cmd.serverTime = cg.predictedPlayerState.commandTime + 1;
-		}
-		// end camera script
-
-		//Com_Printf("cgame pmove cg.time %d  serverTime %d  eventSequence %d\n", cg.time, cg.snap->serverTime, cg.predictedPlayerState.eventSequence);
 		Pmove (&cg_pmove);
 
 		moved = qtrue;
@@ -690,7 +606,7 @@
 	// adjust for the movement of the groundentity
 	CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
 		cg.predictedPlayerState.groundEntityNum, 
-							   cg.physicsTime, cg.time, cg.predictedPlayerState.origin, cg.foverf, cg.predictedPlayerState.viewangles, cg.predictedPlayerState.viewangles );
+		cg.physicsTime, cg.time, cg.predictedPlayerState.origin, cg.predictedPlayerState.viewangles, cg.predictedPlayerState.viewangles);
 
 	if ( cg_showmiss.integer ) {
 		if (cg.predictedPlayerState.eventSequence > oldPlayerState.eventSequence + MAX_PS_EVENTS) {

```

### `openarena-engine`  — sha256 `627db99b81c8...`, 17842 bytes

_Diff stat: +49 / -135 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\cg_predict.c	2026-04-16 20:02:25.148527000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\cgame\cg_predict.c	2026-04-16 22:48:25.726201700 +0100
@@ -1,4 +1,24 @@
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
 // cg_predict.c -- this file generates cg.predictedPlayerState by either
 // interpolating between snapshots from the server or locally predicting
@@ -7,21 +27,12 @@
 
 #include "cg_local.h"
 
-#include "cg_ents.h"
-#include "cg_main.h"
-#include "cg_players.h"
-#include "cg_playerstate.h"
-#include "cg_predict.h"
-#include "cg_syscalls.h"
-#include "sc.h"
-
-int cg_numSolidEntities;
-centity_t *cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
-
 static	pmove_t		cg_pmove;
 
+static	int			cg_numSolidEntities;
+static	centity_t	*cg_solidEntities[MAX_ENTITIES_IN_SNAPSHOT];
 static	int			cg_numTriggerEntities;
-static centity_t *cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
+static	centity_t	*cg_triggerEntities[MAX_ENTITIES_IN_SNAPSHOT];
 
 /*
 ====================
@@ -35,9 +46,8 @@
 void CG_BuildSolidList( void ) {
 	int			i;
 	centity_t	*cent;
-	const snapshot_t	*snap;
-	const entityState_t	*ent;
-	clipHandle_t 	cmodel;
+	snapshot_t	*snap;
+	entityState_t	*ent;
 
 	cg_numSolidEntities = 0;
 	cg_numTriggerEntities = 0;
@@ -48,16 +58,6 @@
 		snap = cg.snap;
 	}
 
-#if 0
-	if (snap->ps.persistant[PERS_TEAM] != TEAM_SPECTATOR) {
-		cg_solidEntities[cg_numSolidEntities] = &cg_entities[snap->ps.clientNum];
-		cg_numSolidEntities++;
-		cg_entities[snap->ps.clientNum].nextState.solid = 4200463;
-		Com_Printf("adding %s to solid list\n", cgs.clientinfo[snap->ps.clientNum].name);
-
-	}
-#endif
-
 	for ( i = 0 ; i < snap->numEntities ; i++ ) {
 		cent = &cg_entities[ snap->entities[ i ].number ];
 		ent = &cent->currentState;
@@ -69,15 +69,6 @@
 		}
 
 		if ( cent->nextState.solid ) {
-			//Com_Printf("solid: %d\n", cent->nextState.solid);
-			//FIXME hack for broken demo playback
-			if (cent->nextState.solid == SOLID_BMODEL ) {
-				// special value for bmodel
-				cmodel = trap_CM_InlineModel( ent->modelindex );
-				if (cmodel < 0) {
-					continue;
-				}
-			}
 			cg_solidEntities[cg_numSolidEntities] = cent;
 			cg_numSolidEntities++;
 			continue;
@@ -95,12 +86,11 @@
 							int skipNumber, int mask, trace_t *tr ) {
 	int			i, x, zd, zu;
 	trace_t		trace;
-	const entityState_t	*ent;
+	entityState_t	*ent;
 	clipHandle_t 	cmodel;
 	vec3_t		bmins, bmaxs;
 	vec3_t		origin, angles;
-	const centity_t	*cent;
-	vec3_t tmpOrigin;
+	centity_t	*cent;
 
 	for ( i = 0 ; i < cg_numSolidEntities ; i++ ) {
 		cent = cg_solidEntities[ i ];
@@ -112,17 +102,7 @@
 
 		if ( ent->solid == SOLID_BMODEL ) {
 			// special value for bmodel
-			if (SC_Cvar_Get_Int("debug_bmodel")) {
-				CG_FloatNumber(ent->number, ent->origin, RF_DEPTHHACK, NULL, 1.0);
-				VectorCopy(ent->origin, tmpOrigin);
-				tmpOrigin[2] += 20;
-				CG_FloatNumber(ent->modelindex, tmpOrigin, RF_DEPTHHACK, NULL, 1.0);
-				Com_Printf("^4%d  modelindex %d\n", ent->number, ent->modelindex);
-			}
 			cmodel = trap_CM_InlineModel( ent->modelindex );
-			if (cmodel < 0) {
-				continue;
-			}
 			VectorCopy( cent->lerpAngles, angles );
 			BG_EvaluateTrajectory( &cent->currentState.pos, cg.physicsTime, origin );
 		} else {
@@ -181,8 +161,8 @@
 */
 int		CG_PointContents( const vec3_t point, int passEntityNum ) {
 	int			i;
-	const entityState_t	*ent;
-	const centity_t	*cent;
+	entityState_t	*ent;
+	centity_t	*cent;
 	clipHandle_t cmodel;
 	int			contents;
 
@@ -222,11 +202,10 @@
 ========================
 */
 static void CG_InterpolatePlayerState( qboolean grabAngles ) {
-	double			f;
+	float			f;
 	int				i;
 	playerState_t	*out;
-	const snapshot_t		*prev, *next;
-	//static int lastCgtime = 0;  // testing
+	snapshot_t		*prev, *next;
 
 	out = &cg.predictedPlayerState;
 	prev = cg.snap;
@@ -234,17 +213,6 @@
 
 	*out = cg.snap->ps;
 
-	//FIXME here better
-#if 0
-	if (cg_demoSmoothing.integer  &&  cg.noMove) {
-		//Com_Printf("CG_InterpolatePlayerState  cg.snap->serverTime %d\n", cg.snap->serverTime);
-		if (cg.nextNextSnapValid) {
-			next = &cg.nextNextSnap;
-			Com_Printf("^2yes\n");
-		}
-	}
-#endif
-
 	// if we are still allowing local input, short circuit the view angles
 	if ( grabAngles ) {
 		usercmd_t	cmd;
@@ -253,34 +221,19 @@
 		cmdNum = trap_GetCurrentCmdNumber();
 		trap_GetUserCmd( cmdNum, &cmd );
 
-		PM_UpdateViewAngles( out, &cmd, qfalse );
+		PM_UpdateViewAngles( out, &cmd );
 	}
 
 	// if the next frame is a teleport, we can't lerp to it
 	if ( cg.nextFrameTeleport ) {
-		//Com_Printf("nextframeteleport %d\n", cg.nextSnap->serverTime);
 		return;
 	}
 
-	if (!next) {
-		if (!SC_Cvar_Get_Int("cl_freezeDemo")  &&  SC_Cvar_Get_Float("timescale") == 1.0) {
-			//Com_Printf("!next\n");
-		}
+	if ( !next || next->serverTime <= prev->serverTime ) {
 		return;
 	}
 
-	if (next->serverTime <= prev->serverTime) {
-		Com_Printf("next->serverTime <= prev->serverTime  %d  %d\n", next->serverTime, prev->serverTime);
-		return;
-	}
-
-	//f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
-	//Com_Printf("interp(1)  %f  %s\n", f, (cg.time - lastCgtime) ? "*" : "");
-	//lastCgtime = cg.time;
-
-	//f = (float)( (float)cg.time + (float)cg.ioverf / SUBTIME_RESOLUTION  - (float)prev->serverTime ) / (float)( next->serverTime - prev->serverTime );
-	f = (cg.ftime - (double)prev->serverTime ) / (double)(next->serverTime - prev->serverTime);
-	//Com_Printf("interp(2)  %f\n", f);
+	f = (float)( cg.time - prev->serverTime ) / ( next->serverTime - prev->serverTime );
 
 	i = next->ps.bobCycle;
 	if ( i < prev->ps.bobCycle ) {
@@ -291,10 +244,10 @@
 	for ( i = 0 ; i < 3 ; i++ ) {
 		out->origin[i] = prev->ps.origin[i] + f * (next->ps.origin[i] - prev->ps.origin[i] );
 		if ( !grabAngles ) {
-			out->viewangles[i] = LerpAngle(
+			out->viewangles[i] = LerpAngle( 
 				prev->ps.viewangles[i], next->ps.viewangles[i], f );
 		}
-		out->velocity[i] = prev->ps.velocity[i] +
+		out->velocity[i] = prev->ps.velocity[i] + 
 			f * (next->ps.velocity[i] - prev->ps.velocity[i] );
 	}
 
@@ -306,17 +259,11 @@
 ===================
 */
 static void CG_TouchItem( centity_t *cent ) {
-	const gitem_t		*item;
+	gitem_t		*item;
 
 	if ( !cg_predictItems.integer ) {
 		return;
 	}
-
-	// hack for ql timer pies which still send items with EF_NODRAW
-	if (cent->nextState.eFlags & EF_NODRAW) {
-		return;
-	}
-
 	if ( !BG_PlayerTouchesItem( &cg.predictedPlayerState, &cent->currentState, cg.time ) ) {
 		return;
 	}
@@ -332,17 +279,16 @@
 
 	item = &bg_itemlist[ cent->currentState.modelindex ];
 
-	// Special case for flags.
+	// Special case for flags.  
 	// We don't predict touching our own flag
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( cgs.gametype == GT_1FCTF ) {
 		if( item->giType == IT_TEAM && item->giTag != PW_NEUTRALFLAG ) {
 			return;
 		}
 	}
-
-	if(cgs.gametype == GT_CTF  ||  cgs.gametype == GT_CTFS  ||  cgs.gametype == GT_NTF) {
 #endif
+	if( cgs.gametype == GT_CTF ) {
 		if (cg.predictedPlayerState.persistant[PERS_TEAM] == TEAM_RED &&
 			item->giType == IT_TEAM && item->giTag == PW_REDFLAG)
 			return;
@@ -414,7 +360,7 @@
 			continue;
 		}
 
-		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin,
+		trap_CM_BoxTrace( &trace, cg.predictedPlayerState.origin, cg.predictedPlayerState.origin, 
 			cg_pmove.mins, cg_pmove.maxs, cmodel, -1 );
 
 		if ( !trace.startsolid ) {
@@ -422,13 +368,8 @@
 		}
 
 		if ( ent->eType == ET_TELEPORT_TRIGGER ) {
-			if (SC_Cvar_Get_Int("r_teleporterFlash") == 2) {
-				cg.hyperspace = qfalse;
-			} else {
-				cg.hyperspace = qtrue;
-			}
+			cg.hyperspace = qtrue;
 		} else if ( ent->eType == ET_PUSH_TRIGGER ) {
-			//Com_Printf("bg touch jump pad\n");
 			BG_TouchJumpPad( &cg.predictedPlayerState, ent );
 		}
 	}
@@ -475,11 +416,6 @@
 	usercmd_t	oldestCmd;
 	usercmd_t	latestCmd;
 
-	if (cg.freezeEntity[cg.snap->ps.clientNum]) {
-		cg.predictedPlayerState = cg.freezePs;
-		return;
-	}
-
 	cg.hyperspace = qfalse;	// will be set if touching a trigger_teleport
 
 	// if this is the first frame we must guarantee
@@ -516,16 +452,11 @@
 	if ( cg.snap->ps.persistant[PERS_TEAM] == TEAM_SPECTATOR ) {
 		cg_pmove.tracemask &= ~CONTENTS_BODY;	// spectators can fly through bodies
 	}
-	//cg_pmove.noFootsteps = 0;  //FIXME  ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
-	cg_pmove.noFootsteps = (cgs.dmflags & DF_NO_FOOTSTEPS);
+	cg_pmove.noFootsteps = ( cgs.dmflags & DF_NO_FOOTSTEPS ) > 0;
 
 	// save the state before the pmove so we can detect transitions
 	oldPlayerState = cg.predictedPlayerState;
 
-	memcpy(cg.clientSidePredictableEventsOld, cg.clientSidePredictableEvents, sizeof(cg.clientSidePredictableEventsOld));
-	memcpy(cg.clientSidePredictableEventParamsOld, cg.clientSidePredictableEventParams, sizeof(cg.clientSidePredictableEventParamsOld));
-	cg.clientSideEventSequenceOld = cg.clientSideEventSequence;
-
 	current = trap_GetCurrentCmdNumber();
 
 	// if we don't have the commands right after the snapshot, we
@@ -533,7 +464,7 @@
 	// the last good position we had
 	cmdNum = current - CMD_BACKUP + 1;
 	trap_GetUserCmd( cmdNum, &oldestCmd );
-	if ( oldestCmd.serverTime > cg.snap->ps.commandTime
+	if ( oldestCmd.serverTime > cg.snap->ps.commandTime 
 		&& oldestCmd.serverTime < cg.time ) {	// special check for map_restart
 		if ( cg_showmiss.integer ) {
 			CG_Printf ("exceeded PACKET_BACKUP on commands\n");
@@ -555,17 +486,12 @@
 		cg.predictedPlayerState = cg.snap->ps;
 		cg.physicsTime = cg.snap->serverTime;
 	}
-	memset(cg.clientSidePredictableEvents, 0, sizeof(cg.clientSidePredictableEvents));
-	memset(cg.clientSidePredictableEventParams, 0, sizeof(cg.clientSidePredictableEventParams));
-	cg.clientSideEventSequence = 0;
 
 	if ( pmove_msec.integer < 8 ) {
 		trap_Cvar_Set("pmove_msec", "8");
-		trap_Cvar_Update(&pmove_msec);
 	}
 	else if (pmove_msec.integer > 33) {
 		trap_Cvar_Set("pmove_msec", "33");
-		trap_Cvar_Update(&pmove_msec);
 	}
 
 	cg_pmove.pmove_fixed = pmove_fixed.integer;// | cg_pmove_fixed.integer;
@@ -578,7 +504,7 @@
 		trap_GetUserCmd( cmdNum, &cg_pmove.cmd );
 
 		if ( cg_pmove.pmove_fixed ) {
-			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd, qfalse );
+			PM_UpdateViewAngles( cg_pmove.ps, &cg_pmove.cmd );
 		}
 
 		// don't do anything if the time is before the snapshot player time
@@ -608,9 +534,9 @@
 				}
 				cg.thisFrameTeleport = qfalse;
 			} else {
-				vec3_t	adjusted, new_angles;
+				vec3_t adjusted, new_angles;
 				CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
-										   cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted, cg.foverf, cg.predictedPlayerState.viewangles, new_angles );
+				cg.predictedPlayerState.groundEntityNum, cg.physicsTime, cg.oldTime, adjusted, cg.predictedPlayerState.viewangles, new_angles);
 
 				if ( cg_showmiss.integer ) {
 					if (!VectorCompare( oldPlayerState.origin, adjusted )) {
@@ -653,18 +579,6 @@
 			cg_pmove.cmd.serverTime = ((cg_pmove.cmd.serverTime + pmove_msec.integer-1) / pmove_msec.integer) * pmove_msec.integer;
 		}
 
-		// camera script
-		if (cgs.scrFadeAlphaCurrent) {
-			cg_pmove.cmd.buttons = 0;
-			cg_pmove.cmd.forwardmove = 0;
-			cg_pmove.cmd.rightmove = 0;
-			cg_pmove.cmd.upmove = 0;
-			if (cg_pmove.cmd.serverTime - cg.predictedPlayerState.commandTime > 1)
-				cg_pmove.cmd.serverTime = cg.predictedPlayerState.commandTime + 1;
-		}
-		// end camera script
-
-		//Com_Printf("cgame pmove cg.time %d  serverTime %d  eventSequence %d\n", cg.time, cg.snap->serverTime, cg.predictedPlayerState.eventSequence);
 		Pmove (&cg_pmove);
 
 		moved = qtrue;
@@ -690,7 +604,7 @@
 	// adjust for the movement of the groundentity
 	CG_AdjustPositionForMover( cg.predictedPlayerState.origin, 
 		cg.predictedPlayerState.groundEntityNum, 
-							   cg.physicsTime, cg.time, cg.predictedPlayerState.origin, cg.foverf, cg.predictedPlayerState.viewangles, cg.predictedPlayerState.viewangles );
+		cg.physicsTime, cg.time, cg.predictedPlayerState.origin, cg.predictedPlayerState.viewangles, cg.predictedPlayerState.viewangles);
 
 	if ( cg_showmiss.integer ) {
 		if (cg.predictedPlayerState.eventSequence > oldPlayerState.eventSequence + MAX_PS_EVENTS) {

```

### `openarena-gamecode`  — sha256 `b7bdf5847051...`, 28395 bytes

_Diff stat: +376 / -146 lines_

_(full diff is 25304 bytes — see files directly)_
