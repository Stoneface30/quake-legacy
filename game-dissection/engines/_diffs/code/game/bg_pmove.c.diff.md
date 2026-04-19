# Diff: `code/game/bg_pmove.c`
**Canonical:** `wolfcamql-src` (sha256 `3cdcddd7b5c8...`, 48691 bytes)

## Variants

### `quake3-source`  — sha256 `3ced04aed868...`, 47509 bytes

_Diff stat: +38 / -69 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_pmove.c	2026-04-16 20:02:25.190640500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\bg_pmove.c	2026-04-16 20:02:19.903124100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,7 +23,7 @@
 // bg_pmove.c -- both games player movement code
 // takes a playerstate and a usercmd as input and returns a modifed playerstate
 
-#include "../qcommon/q_shared.h"
+#include "q_shared.h"
 #include "bg_public.h"
 #include "bg_local.h"
 
@@ -34,6 +34,7 @@
 float	pm_stopspeed = 100.0f;
 float	pm_duckScale = 0.25f;
 float	pm_swimScale = 0.50f;
+float	pm_wadeScale = 0.70f;
 
 float	pm_accelerate = 10.0f;
 float	pm_airaccelerate = 1.0f;
@@ -141,7 +142,7 @@
 Slide off of the impacting surface
 ==================
 */
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce ) {
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce ) {
 	float	backoff;
 	float	change;
 	int		i;
@@ -173,9 +174,7 @@
 	float	*vel;
 	float	speed, newspeed, control;
 	float	drop;
-
-	//Com_Printf("PM_Friction\n");
-
+	
 	vel = pm->ps->velocity;
 	
 	VectorCopy( vel, vec );
@@ -238,7 +237,7 @@
 Handles user intended acceleration
 ==============
 */
-static void PM_Accelerate( const vec3_t wishdir, float wishspeed, float accel ) {
+static void PM_Accelerate( vec3_t wishdir, float wishspeed, float accel ) {
 #if 1
 	// q2 style
 	int			i;
@@ -288,16 +287,11 @@
 without getting a sqrt(2) distortion in speed.
 ============
 */
-static float PM_CmdScale( const usercmd_t *cmd ) {
+static float PM_CmdScale( usercmd_t *cmd ) {
 	int		max;
 	float	total;
 	float	scale;
 
-	//Com_Printf("cmdscale f:%d s:%d u:%d\n", cmd->forwardmove, cmd->rightmove, cmd->upmove);
-	if (cmd->forwardmove != 127) {
-		//Com_Printf("wtf pmove fmove \n");
-	}
-
 	max = abs( cmd->forwardmove );
 	if ( abs( cmd->rightmove ) > max ) {
 		max = abs( cmd->rightmove );
@@ -321,7 +315,7 @@
 ================
 PM_SetMovementDir
 
-Determine the rotation of the legs relative
+Determine the rotation of the legs reletive
 to the facing dir
 ================
 */
@@ -431,7 +425,7 @@
 
 	spot[2] += 16;
 	cont = pm->pointcontents (spot, pm->ps->clientNum );
-	if ( cont & (CONTENTS_SOLID|CONTENTS_PLAYERCLIP|CONTENTS_BODY) ) {
+	if ( cont ) {
 		return qfalse;
 	}
 
@@ -486,15 +480,13 @@
 		PM_WaterJumpMove();
 		return;
 	}
-
-//FIXME 2015-08-06 test now that there have been fixes (ioq3)
 #if 0
 	// jump = head for surface
 	if ( pm->cmd.upmove >= 10 ) {
 		if (pm->ps->velocity[2] > -300) {
-			if ( pm->watertype & CONTENTS_WATER ) {
+			if ( pm->watertype == CONTENTS_WATER ) {
 				pm->ps->velocity[2] = 100;
-			} else if ( pm->watertype & CONTENTS_SLIME ) {
+			} else if (pm->watertype == CONTENTS_SLIME) {
 				pm->ps->velocity[2] = 80;
 			} else {
 				pm->ps->velocity[2] = 50;
@@ -542,7 +534,7 @@
 	PM_SlideMove( qfalse );
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ===================
 PM_InvulnerabilityMove
@@ -908,23 +900,16 @@
 ================
 PM_FootstepForSurface
 
-Returns an event number appropriate for the groundsurface
+Returns an event number apropriate for the groundsurface
 ================
 */
 static int PM_FootstepForSurface( void ) {
-	//Com_Printf("footsteps surfaceflags 0x%x\n", pml.groundTrace.surfaceFlags);
 	if ( pml.groundTrace.surfaceFlags & SURF_NOSTEPS ) {
 		return 0;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_WOOD ) {
-		return EV_FOOTSTEP_WOOD;
-	}
 	if ( pml.groundTrace.surfaceFlags & SURF_METALSTEPS ) {
 		return EV_FOOTSTEP_METAL;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_SNOW ) {
-		return EV_FOOTSTEP_SNOW;
-	}
 	return EV_FOOTSTEP;
 }
 
@@ -1268,12 +1253,12 @@
 	if ( pm->ps->powerups[PW_INVULNERABILITY] ) {
 		if ( pm->ps->pm_flags & PMF_INVULEXPAND ) {
 			// invulnerability sphere has a 42 units radius
-			VectorSet( pm->mins, -INVUL_RADIUS, -INVUL_RADIUS, -INVUL_RADIUS );
-			VectorSet( pm->maxs, INVUL_RADIUS, INVUL_RADIUS, INVUL_RADIUS );
+			VectorSet( pm->mins, -42, -42, -42 );
+			VectorSet( pm->maxs, 42, 42, 42 );
 		}
 		else {
-			VectorSet( pm->mins, -PLAYER_WIDTH, -PLAYER_WIDTH, MINS_Z );
-			VectorSet( pm->maxs, PLAYER_WIDTH, PLAYER_WIDTH, 16 );
+			VectorSet( pm->mins, -15, -15, MINS_Z );
+			VectorSet( pm->maxs, 15, 15, 16 );
 		}
 		pm->ps->pm_flags |= PMF_DUCKED;
 		pm->ps->viewheight = CROUCH_VIEWHEIGHT;
@@ -1281,17 +1266,17 @@
 	}
 	pm->ps->pm_flags &= ~PMF_INVULEXPAND;
 
-	pm->mins[0] = -PLAYER_WIDTH;
-	pm->mins[1] = -PLAYER_WIDTH;
+	pm->mins[0] = -15;
+	pm->mins[1] = -15;
 
-	pm->maxs[0] = PLAYER_WIDTH;
-	pm->maxs[1] = PLAYER_WIDTH;
+	pm->maxs[0] = 15;
+	pm->maxs[1] = 15;
 
 	pm->mins[2] = MINS_Z;
 
 	if (pm->ps->pm_type == PM_DEAD)
 	{
-		pm->maxs[2] = DEAD_HEIGHT;
+		pm->maxs[2] = -8;
 		pm->ps->viewheight = DEAD_VIEWHEIGHT;
 		return;
 	}
@@ -1305,7 +1290,7 @@
 		if (pm->ps->pm_flags & PMF_DUCKED)
 		{
 			// try to stand up
-			pm->maxs[2] = DEFAULT_HEIGHT;
+			pm->maxs[2] = 32;
 			pm->trace (&trace, pm->ps->origin, pm->mins, pm->maxs, pm->ps->origin, pm->ps->clientNum, pm->tracemask );
 			if (!trace.allsolid)
 				pm->ps->pm_flags &= ~PMF_DUCKED;
@@ -1314,12 +1299,12 @@
 
 	if (pm->ps->pm_flags & PMF_DUCKED)
 	{
-		pm->maxs[2] = CROUCH_HEIGHT;
+		pm->maxs[2] = 16;
 		pm->ps->viewheight = CROUCH_VIEWHEIGHT;
 	}
 	else
 	{
-		pm->maxs[2] = DEFAULT_HEIGHT;
+		pm->maxs[2] = 32;
 		pm->ps->viewheight = DEFAULT_VIEWHEIGHT;
 	}
 }
@@ -1418,7 +1403,7 @@
 	old = pm->ps->bobCycle;
 	pm->ps->bobCycle = (int)( old + bobmove * pml.msec ) & 255;
 
-	// if we just crossed a cycle boundary, play an appropriate footstep event
+	// if we just crossed a cycle boundary, play an apropriate footstep event
 	if ( ( ( old + 64 ) ^ ( pm->ps->bobCycle + 64 ) ) & 128 ) {
 		if ( pm->waterlevel == 0 ) {
 			// on ground will only play sounds if running
@@ -1630,7 +1615,7 @@
 
 	// start the animation even if out of ammo
 	if ( pm->ps->weapon == WP_GAUNTLET ) {
-		// the gauntlet only "fires" when it actually hits something
+		// the guantlet only "fires" when it actually hits something
 		if ( !pm->gauntletHit ) {
 			pm->ps->weaponTime = 0;
 			pm->ps->weaponstate = WEAPON_READY;
@@ -1672,9 +1657,6 @@
 	case WP_MACHINEGUN:
 		addTime = 100;
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		addTime = 75;
-		break;
 	case WP_GRENADE_LAUNCHER:
 		addTime = 800;
 		break;
@@ -1683,7 +1665,6 @@
 		break;
 	case WP_PLASMAGUN:
 		addTime = 100;
-		//addTime = g_weapon_plasma_rate.integer;
 		break;
 	case WP_RAILGUN:
 		addTime = 1500;
@@ -1694,7 +1675,7 @@
 	case WP_GRAPPLING_HOOK:
 		addTime = 400;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		addTime = 1000;
 		break;
@@ -1707,15 +1688,15 @@
 #endif
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		addTime /= 1.5;
 	}
 	else
-	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		addTime /= 1.3;
-	}
-	else
+  }
+  else
 #endif
 	if ( pm->ps->powerups[PW_HASTE] ) {
 		addTime /= 1.3;
@@ -1737,7 +1718,7 @@
 			pm->ps->torsoTimer = TIMER_GESTURE;
 			PM_AddEvent( EV_TAUNT );
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	} else if ( pm->cmd.buttons & BUTTON_GETFLAG ) {
 		if ( pm->ps->torsoTimer == 0 ) {
 			PM_StartTorsoAnim( TORSO_GETFLAG );
@@ -1810,10 +1791,10 @@
 PM_UpdateViewAngles
 
 This can be used as another entry point when only the viewangles
-are being updated instead of a full move
+are being updated isntead of a full move
 ================
 */
-void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd, qboolean unlockPitch ) {
+void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd ) {
 	short		temp;
 	int		i;
 
@@ -1821,7 +1802,6 @@
 		return;		// no view changes at all
 	}
 
-	//FIXME PM_NOCLIP needs health > 0
 	if ( ps->pm_type != PM_SPECTATOR && ps->stats[STAT_HEALTH] <= 0 ) {
 		return;		// no view changes at all
 	}
@@ -1829,7 +1809,7 @@
 	// circularly clamp the angles with deltas
 	for (i=0 ; i<3 ; i++) {
 		temp = cmd->angles[i] + ps->delta_angles[i];
-		if ( !unlockPitch  &&  i == PITCH ) {
+		if ( i == PITCH ) {
 			// don't let the player look up or down more than 90 degrees
 			if ( temp > 16000 ) {
 				ps->delta_angles[i] = 16000 - cmd->angles[i];
@@ -1854,10 +1834,6 @@
 void trap_SnapVector( float *v );
 
 void PmoveSingle (pmove_t *pmove) {
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("psingle\n");
-	}
-
 	pm = pmove;
 
 	// this counter lets us debug movement problems with a journal
@@ -1933,7 +1909,7 @@
 	pml.frametime = pml.msec * 0.001;
 
 	// update the viewangles
-	PM_UpdateViewAngles( pm->ps, &pm->cmd, pm->unlockPitch );
+	PM_UpdateViewAngles( pm->ps, &pm->cmd );
 
 	AngleVectors (pm->ps->viewangles, pml.forward, pml.right, pml.up);
 
@@ -1965,7 +1941,6 @@
 	if ( pm->ps->pm_type == PM_NOCLIP ) {
 		PM_NoclipMove ();
 		PM_DropTimers ();
-		PM_Weapon();
 		return;
 	}
 
@@ -1993,7 +1968,7 @@
 
 	PM_DropTimers();
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( pm->ps->powerups[PW_INVULNERABILITY] ) {
 		PM_InvulnerabilityMove();
 	} else
@@ -2051,11 +2026,6 @@
 void Pmove (pmove_t *pmove) {
 	int			finalTime;
 
-
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("pmove fmove start wtf\n");
-	}
-
 	finalTime = pmove->cmd.serverTime;
 
 	if ( finalTime < pmove->ps->commandTime ) {
@@ -2087,7 +2057,6 @@
 		}
 		pmove->cmd.serverTime = pmove->ps->commandTime + msec;
 		PmoveSingle( pmove );
-		//Com_Printf("..\n");
 
 		if ( pmove->ps->pm_flags & PMF_JUMP_HELD ) {
 			pmove->cmd.upmove = 20;

```

### `ioquake3`  — sha256 `65758cf0258e...`, 47781 bytes

_Diff stat: +15 / -47 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_pmove.c	2026-04-16 20:02:25.190640500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\bg_pmove.c	2026-04-16 20:02:21.540890600 +0100
@@ -141,7 +141,7 @@
 Slide off of the impacting surface
 ==================
 */
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce ) {
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce ) {
 	float	backoff;
 	float	change;
 	int		i;
@@ -173,9 +173,7 @@
 	float	*vel;
 	float	speed, newspeed, control;
 	float	drop;
-
-	//Com_Printf("PM_Friction\n");
-
+	
 	vel = pm->ps->velocity;
 	
 	VectorCopy( vel, vec );
@@ -238,7 +236,7 @@
 Handles user intended acceleration
 ==============
 */
-static void PM_Accelerate( const vec3_t wishdir, float wishspeed, float accel ) {
+static void PM_Accelerate( vec3_t wishdir, float wishspeed, float accel ) {
 #if 1
 	// q2 style
 	int			i;
@@ -288,16 +286,11 @@
 without getting a sqrt(2) distortion in speed.
 ============
 */
-static float PM_CmdScale( const usercmd_t *cmd ) {
+static float PM_CmdScale( usercmd_t *cmd ) {
 	int		max;
 	float	total;
 	float	scale;
 
-	//Com_Printf("cmdscale f:%d s:%d u:%d\n", cmd->forwardmove, cmd->rightmove, cmd->upmove);
-	if (cmd->forwardmove != 127) {
-		//Com_Printf("wtf pmove fmove \n");
-	}
-
 	max = abs( cmd->forwardmove );
 	if ( abs( cmd->rightmove ) > max ) {
 		max = abs( cmd->rightmove );
@@ -486,8 +479,6 @@
 		PM_WaterJumpMove();
 		return;
 	}
-
-//FIXME 2015-08-06 test now that there have been fixes (ioq3)
 #if 0
 	// jump = head for surface
 	if ( pm->cmd.upmove >= 10 ) {
@@ -542,7 +533,7 @@
 	PM_SlideMove( qfalse );
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ===================
 PM_InvulnerabilityMove
@@ -912,19 +903,12 @@
 ================
 */
 static int PM_FootstepForSurface( void ) {
-	//Com_Printf("footsteps surfaceflags 0x%x\n", pml.groundTrace.surfaceFlags);
 	if ( pml.groundTrace.surfaceFlags & SURF_NOSTEPS ) {
 		return 0;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_WOOD ) {
-		return EV_FOOTSTEP_WOOD;
-	}
 	if ( pml.groundTrace.surfaceFlags & SURF_METALSTEPS ) {
 		return EV_FOOTSTEP_METAL;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_SNOW ) {
-		return EV_FOOTSTEP_SNOW;
-	}
 	return EV_FOOTSTEP;
 }
 
@@ -1630,7 +1614,7 @@
 
 	// start the animation even if out of ammo
 	if ( pm->ps->weapon == WP_GAUNTLET ) {
-		// the gauntlet only "fires" when it actually hits something
+		// the guantlet only "fires" when it actually hits something
 		if ( !pm->gauntletHit ) {
 			pm->ps->weaponTime = 0;
 			pm->ps->weaponstate = WEAPON_READY;
@@ -1672,9 +1656,6 @@
 	case WP_MACHINEGUN:
 		addTime = 100;
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		addTime = 75;
-		break;
 	case WP_GRENADE_LAUNCHER:
 		addTime = 800;
 		break;
@@ -1683,7 +1664,6 @@
 		break;
 	case WP_PLASMAGUN:
 		addTime = 100;
-		//addTime = g_weapon_plasma_rate.integer;
 		break;
 	case WP_RAILGUN:
 		addTime = 1500;
@@ -1694,7 +1674,7 @@
 	case WP_GRAPPLING_HOOK:
 		addTime = 400;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		addTime = 1000;
 		break;
@@ -1707,12 +1687,12 @@
 #endif
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		addTime /= 1.5;
 	}
 	else
-	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		addTime /= 1.3;
 	}
 	else
@@ -1737,7 +1717,7 @@
 			pm->ps->torsoTimer = TIMER_GESTURE;
 			PM_AddEvent( EV_TAUNT );
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	} else if ( pm->cmd.buttons & BUTTON_GETFLAG ) {
 		if ( pm->ps->torsoTimer == 0 ) {
 			PM_StartTorsoAnim( TORSO_GETFLAG );
@@ -1813,7 +1793,7 @@
 are being updated instead of a full move
 ================
 */
-void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd, qboolean unlockPitch ) {
+void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd ) {
 	short		temp;
 	int		i;
 
@@ -1821,7 +1801,6 @@
 		return;		// no view changes at all
 	}
 
-	//FIXME PM_NOCLIP needs health > 0
 	if ( ps->pm_type != PM_SPECTATOR && ps->stats[STAT_HEALTH] <= 0 ) {
 		return;		// no view changes at all
 	}
@@ -1829,7 +1808,7 @@
 	// circularly clamp the angles with deltas
 	for (i=0 ; i<3 ; i++) {
 		temp = cmd->angles[i] + ps->delta_angles[i];
-		if ( !unlockPitch  &&  i == PITCH ) {
+		if ( i == PITCH ) {
 			// don't let the player look up or down more than 90 degrees
 			if ( temp > 16000 ) {
 				ps->delta_angles[i] = 16000 - cmd->angles[i];
@@ -1854,10 +1833,6 @@
 void trap_SnapVector( float *v );
 
 void PmoveSingle (pmove_t *pmove) {
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("psingle\n");
-	}
-
 	pm = pmove;
 
 	// this counter lets us debug movement problems with a journal
@@ -1887,7 +1862,7 @@
 	}
 
 	// set the firing flag for continuous beam weapons
-	if ( !(pm->ps->pm_flags & PMF_RESPAWNED) && pm->ps->pm_type != PM_INTERMISSION
+	if ( !(pm->ps->pm_flags & PMF_RESPAWNED) && pm->ps->pm_type != PM_INTERMISSION && pm->ps->pm_type != PM_NOCLIP
 		&& ( pm->cmd.buttons & BUTTON_ATTACK ) && pm->ps->ammo[ pm->ps->weapon ] ) {
 		pm->ps->eFlags |= EF_FIRING;
 	} else {
@@ -1933,7 +1908,7 @@
 	pml.frametime = pml.msec * 0.001;
 
 	// update the viewangles
-	PM_UpdateViewAngles( pm->ps, &pm->cmd, pm->unlockPitch );
+	PM_UpdateViewAngles( pm->ps, &pm->cmd );
 
 	AngleVectors (pm->ps->viewangles, pml.forward, pml.right, pml.up);
 
@@ -1965,7 +1940,6 @@
 	if ( pm->ps->pm_type == PM_NOCLIP ) {
 		PM_NoclipMove ();
 		PM_DropTimers ();
-		PM_Weapon();
 		return;
 	}
 
@@ -1993,7 +1967,7 @@
 
 	PM_DropTimers();
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( pm->ps->powerups[PW_INVULNERABILITY] ) {
 		PM_InvulnerabilityMove();
 	} else
@@ -2051,11 +2025,6 @@
 void Pmove (pmove_t *pmove) {
 	int			finalTime;
 
-
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("pmove fmove start wtf\n");
-	}
-
 	finalTime = pmove->cmd.serverTime;
 
 	if ( finalTime < pmove->ps->commandTime ) {
@@ -2087,7 +2056,6 @@
 		}
 		pmove->cmd.serverTime = pmove->ps->commandTime + msec;
 		PmoveSingle( pmove );
-		//Com_Printf("..\n");
 
 		if ( pmove->ps->pm_flags & PMF_JUMP_HELD ) {
 			pmove->cmd.upmove = 20;

```

### `openarena-engine`  — sha256 `0e9a1a763c8a...`, 47597 bytes

_Diff stat: +34 / -66 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_pmove.c	2026-04-16 20:02:25.190640500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\bg_pmove.c	2026-04-16 22:48:25.744536600 +0100
@@ -141,7 +141,7 @@
 Slide off of the impacting surface
 ==================
 */
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce ) {
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce ) {
 	float	backoff;
 	float	change;
 	int		i;
@@ -173,9 +173,7 @@
 	float	*vel;
 	float	speed, newspeed, control;
 	float	drop;
-
-	//Com_Printf("PM_Friction\n");
-
+	
 	vel = pm->ps->velocity;
 	
 	VectorCopy( vel, vec );
@@ -238,7 +236,7 @@
 Handles user intended acceleration
 ==============
 */
-static void PM_Accelerate( const vec3_t wishdir, float wishspeed, float accel ) {
+static void PM_Accelerate( vec3_t wishdir, float wishspeed, float accel ) {
 #if 1
 	// q2 style
 	int			i;
@@ -288,16 +286,11 @@
 without getting a sqrt(2) distortion in speed.
 ============
 */
-static float PM_CmdScale( const usercmd_t *cmd ) {
+static float PM_CmdScale( usercmd_t *cmd ) {
 	int		max;
 	float	total;
 	float	scale;
 
-	//Com_Printf("cmdscale f:%d s:%d u:%d\n", cmd->forwardmove, cmd->rightmove, cmd->upmove);
-	if (cmd->forwardmove != 127) {
-		//Com_Printf("wtf pmove fmove \n");
-	}
-
 	max = abs( cmd->forwardmove );
 	if ( abs( cmd->rightmove ) > max ) {
 		max = abs( cmd->rightmove );
@@ -486,15 +479,13 @@
 		PM_WaterJumpMove();
 		return;
 	}
-
-//FIXME 2015-08-06 test now that there have been fixes (ioq3)
 #if 0
 	// jump = head for surface
 	if ( pm->cmd.upmove >= 10 ) {
 		if (pm->ps->velocity[2] > -300) {
-			if ( pm->watertype & CONTENTS_WATER ) {
+			if ( pm->watertype == CONTENTS_WATER ) {
 				pm->ps->velocity[2] = 100;
-			} else if ( pm->watertype & CONTENTS_SLIME ) {
+			} else if (pm->watertype == CONTENTS_SLIME) {
 				pm->ps->velocity[2] = 80;
 			} else {
 				pm->ps->velocity[2] = 50;
@@ -542,7 +533,7 @@
 	PM_SlideMove( qfalse );
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ===================
 PM_InvulnerabilityMove
@@ -908,23 +899,16 @@
 ================
 PM_FootstepForSurface
 
-Returns an event number appropriate for the groundsurface
+Returns an event number apropriate for the groundsurface
 ================
 */
 static int PM_FootstepForSurface( void ) {
-	//Com_Printf("footsteps surfaceflags 0x%x\n", pml.groundTrace.surfaceFlags);
 	if ( pml.groundTrace.surfaceFlags & SURF_NOSTEPS ) {
 		return 0;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_WOOD ) {
-		return EV_FOOTSTEP_WOOD;
-	}
 	if ( pml.groundTrace.surfaceFlags & SURF_METALSTEPS ) {
 		return EV_FOOTSTEP_METAL;
 	}
-	if ( pml.groundTrace.surfaceFlags & SURF_SNOW ) {
-		return EV_FOOTSTEP_SNOW;
-	}
 	return EV_FOOTSTEP;
 }
 
@@ -1268,12 +1252,12 @@
 	if ( pm->ps->powerups[PW_INVULNERABILITY] ) {
 		if ( pm->ps->pm_flags & PMF_INVULEXPAND ) {
 			// invulnerability sphere has a 42 units radius
-			VectorSet( pm->mins, -INVUL_RADIUS, -INVUL_RADIUS, -INVUL_RADIUS );
-			VectorSet( pm->maxs, INVUL_RADIUS, INVUL_RADIUS, INVUL_RADIUS );
+			VectorSet( pm->mins, -42, -42, -42 );
+			VectorSet( pm->maxs, 42, 42, 42 );
 		}
 		else {
-			VectorSet( pm->mins, -PLAYER_WIDTH, -PLAYER_WIDTH, MINS_Z );
-			VectorSet( pm->maxs, PLAYER_WIDTH, PLAYER_WIDTH, 16 );
+			VectorSet( pm->mins, -15, -15, MINS_Z );
+			VectorSet( pm->maxs, 15, 15, 16 );
 		}
 		pm->ps->pm_flags |= PMF_DUCKED;
 		pm->ps->viewheight = CROUCH_VIEWHEIGHT;
@@ -1281,17 +1265,17 @@
 	}
 	pm->ps->pm_flags &= ~PMF_INVULEXPAND;
 
-	pm->mins[0] = -PLAYER_WIDTH;
-	pm->mins[1] = -PLAYER_WIDTH;
+	pm->mins[0] = -15;
+	pm->mins[1] = -15;
 
-	pm->maxs[0] = PLAYER_WIDTH;
-	pm->maxs[1] = PLAYER_WIDTH;
+	pm->maxs[0] = 15;
+	pm->maxs[1] = 15;
 
 	pm->mins[2] = MINS_Z;
 
 	if (pm->ps->pm_type == PM_DEAD)
 	{
-		pm->maxs[2] = DEAD_HEIGHT;
+		pm->maxs[2] = -8;
 		pm->ps->viewheight = DEAD_VIEWHEIGHT;
 		return;
 	}
@@ -1305,7 +1289,7 @@
 		if (pm->ps->pm_flags & PMF_DUCKED)
 		{
 			// try to stand up
-			pm->maxs[2] = DEFAULT_HEIGHT;
+			pm->maxs[2] = 32;
 			pm->trace (&trace, pm->ps->origin, pm->mins, pm->maxs, pm->ps->origin, pm->ps->clientNum, pm->tracemask );
 			if (!trace.allsolid)
 				pm->ps->pm_flags &= ~PMF_DUCKED;
@@ -1314,12 +1298,12 @@
 
 	if (pm->ps->pm_flags & PMF_DUCKED)
 	{
-		pm->maxs[2] = CROUCH_HEIGHT;
+		pm->maxs[2] = 16;
 		pm->ps->viewheight = CROUCH_VIEWHEIGHT;
 	}
 	else
 	{
-		pm->maxs[2] = DEFAULT_HEIGHT;
+		pm->maxs[2] = 32;
 		pm->ps->viewheight = DEFAULT_VIEWHEIGHT;
 	}
 }
@@ -1418,7 +1402,7 @@
 	old = pm->ps->bobCycle;
 	pm->ps->bobCycle = (int)( old + bobmove * pml.msec ) & 255;
 
-	// if we just crossed a cycle boundary, play an appropriate footstep event
+	// if we just crossed a cycle boundary, play an apropriate footstep event
 	if ( ( ( old + 64 ) ^ ( pm->ps->bobCycle + 64 ) ) & 128 ) {
 		if ( pm->waterlevel == 0 ) {
 			// on ground will only play sounds if running
@@ -1630,7 +1614,7 @@
 
 	// start the animation even if out of ammo
 	if ( pm->ps->weapon == WP_GAUNTLET ) {
-		// the gauntlet only "fires" when it actually hits something
+		// the guantlet only "fires" when it actually hits something
 		if ( !pm->gauntletHit ) {
 			pm->ps->weaponTime = 0;
 			pm->ps->weaponstate = WEAPON_READY;
@@ -1672,9 +1656,6 @@
 	case WP_MACHINEGUN:
 		addTime = 100;
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		addTime = 75;
-		break;
 	case WP_GRENADE_LAUNCHER:
 		addTime = 800;
 		break;
@@ -1683,7 +1664,6 @@
 		break;
 	case WP_PLASMAGUN:
 		addTime = 100;
-		//addTime = g_weapon_plasma_rate.integer;
 		break;
 	case WP_RAILGUN:
 		addTime = 1500;
@@ -1694,7 +1674,7 @@
 	case WP_GRAPPLING_HOOK:
 		addTime = 400;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		addTime = 1000;
 		break;
@@ -1707,15 +1687,15 @@
 #endif
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		addTime /= 1.5;
 	}
 	else
-	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[pm->ps->stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		addTime /= 1.3;
-	}
-	else
+  }
+  else
 #endif
 	if ( pm->ps->powerups[PW_HASTE] ) {
 		addTime /= 1.3;
@@ -1737,7 +1717,7 @@
 			pm->ps->torsoTimer = TIMER_GESTURE;
 			PM_AddEvent( EV_TAUNT );
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	} else if ( pm->cmd.buttons & BUTTON_GETFLAG ) {
 		if ( pm->ps->torsoTimer == 0 ) {
 			PM_StartTorsoAnim( TORSO_GETFLAG );
@@ -1810,10 +1790,10 @@
 PM_UpdateViewAngles
 
 This can be used as another entry point when only the viewangles
-are being updated instead of a full move
+are being updated isntead of a full move
 ================
 */
-void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd, qboolean unlockPitch ) {
+void PM_UpdateViewAngles( playerState_t *ps, const usercmd_t *cmd ) {
 	short		temp;
 	int		i;
 
@@ -1821,7 +1801,6 @@
 		return;		// no view changes at all
 	}
 
-	//FIXME PM_NOCLIP needs health > 0
 	if ( ps->pm_type != PM_SPECTATOR && ps->stats[STAT_HEALTH] <= 0 ) {
 		return;		// no view changes at all
 	}
@@ -1829,7 +1808,7 @@
 	// circularly clamp the angles with deltas
 	for (i=0 ; i<3 ; i++) {
 		temp = cmd->angles[i] + ps->delta_angles[i];
-		if ( !unlockPitch  &&  i == PITCH ) {
+		if ( i == PITCH ) {
 			// don't let the player look up or down more than 90 degrees
 			if ( temp > 16000 ) {
 				ps->delta_angles[i] = 16000 - cmd->angles[i];
@@ -1854,10 +1833,6 @@
 void trap_SnapVector( float *v );
 
 void PmoveSingle (pmove_t *pmove) {
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("psingle\n");
-	}
-
 	pm = pmove;
 
 	// this counter lets us debug movement problems with a journal
@@ -1887,7 +1862,7 @@
 	}
 
 	// set the firing flag for continuous beam weapons
-	if ( !(pm->ps->pm_flags & PMF_RESPAWNED) && pm->ps->pm_type != PM_INTERMISSION
+	if ( !(pm->ps->pm_flags & PMF_RESPAWNED) && pm->ps->pm_type != PM_INTERMISSION && pm->ps->pm_type != PM_NOCLIP
 		&& ( pm->cmd.buttons & BUTTON_ATTACK ) && pm->ps->ammo[ pm->ps->weapon ] ) {
 		pm->ps->eFlags |= EF_FIRING;
 	} else {
@@ -1933,7 +1908,7 @@
 	pml.frametime = pml.msec * 0.001;
 
 	// update the viewangles
-	PM_UpdateViewAngles( pm->ps, &pm->cmd, pm->unlockPitch );
+	PM_UpdateViewAngles( pm->ps, &pm->cmd );
 
 	AngleVectors (pm->ps->viewangles, pml.forward, pml.right, pml.up);
 
@@ -1965,7 +1940,6 @@
 	if ( pm->ps->pm_type == PM_NOCLIP ) {
 		PM_NoclipMove ();
 		PM_DropTimers ();
-		PM_Weapon();
 		return;
 	}
 
@@ -1993,7 +1967,7 @@
 
 	PM_DropTimers();
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( pm->ps->powerups[PW_INVULNERABILITY] ) {
 		PM_InvulnerabilityMove();
 	} else
@@ -2051,11 +2025,6 @@
 void Pmove (pmove_t *pmove) {
 	int			finalTime;
 
-
-	if (pmove->cmd.forwardmove != 127) {
-		//Com_Printf("pmove fmove start wtf\n");
-	}
-
 	finalTime = pmove->cmd.serverTime;
 
 	if ( finalTime < pmove->ps->commandTime ) {
@@ -2087,7 +2056,6 @@
 		}
 		pmove->cmd.serverTime = pmove->ps->commandTime + msec;
 		PmoveSingle( pmove );
-		//Com_Printf("..\n");
 
 		if ( pmove->ps->pm_flags & PMF_JUMP_HELD ) {
 			pmove->cmd.upmove = 20;

```

### `openarena-gamecode`  — sha256 `2e2bf36606f7...`, 50760 bytes

_Diff stat: +439 / -303 lines_

_(full diff is 41448 bytes — see files directly)_
