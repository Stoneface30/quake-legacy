# Diff: `code/botlib/be_aas_move.c`
**Canonical:** `wolfcamql-src` (sha256 `aff4bca58859...`, 38307 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `d6137fce7b4c...`, 38680 bytes

_Diff stat: +22 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_move.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_move.c	2026-04-16 20:02:19.847388800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,15 +29,15 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "l_libvar.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_aas_def.h"
 
@@ -168,7 +168,7 @@
 		//get the plane the face is in
 		plane = &aasworld.planes[face->planenum ^ side];
 		//if the origin is pretty close to the plane
-		if (fabsf(DotProduct(plane->normal, origin) - plane->dist) < 3)
+		if (abs(DotProduct(plane->normal, origin) - plane->dist) < 3)
 		{
 			if (AAS_PointInsideFace(abs(facenum), origin, 0.1f)) return qtrue;
 		} //end if
@@ -382,6 +382,18 @@
 	}
 } //end of the function AAS_Accelerate
 //===========================================================================
+//
+// Parameter:			-
+// Returns:				-
+// Changes Globals:		-
+//===========================================================================
+void AAS_AirControl(vec3_t start, vec3_t end, vec3_t velocity, vec3_t cmdmove)
+{
+	vec3_t dir;
+
+	VectorSubtract(end, start, dir);
+} //end of the function AAS_AirControl
+//===========================================================================
 // applies ground friction to the given velocity
 //
 // Parameter:			-
@@ -506,8 +518,7 @@
 	float phys_maxstep, phys_maxsteepness, phys_jumpvel, friction;
 	float gravity, delta, maxvel, wishspeed, accelerate;
 	//float velchange, newvel;
-	//int ax;
-	int n, i, j, pc, step, swimming, crouch, event, jump_frame, areanum;
+	int n, i, j, pc, step, swimming, ax, crouch, event, jump_frame, areanum;
 	int areas[20], numareas;
 	vec3_t points[20];
 	vec3_t org, end, feet, start, stepend, lastorg, wishdir;
@@ -553,7 +564,7 @@
 		//if on the ground or swimming
 		if (onground || swimming)
 		{
-			friction = swimming ? phys_waterfriction : phys_friction;
+			friction = swimming ? phys_friction : phys_waterfriction;
 			//apply friction
 			VectorScale(frame_test_vel, 1/frametime, frame_test_vel);
 			AAS_ApplyFriction(frame_test_vel, friction, phys_stopspeed, frametime);
@@ -563,7 +574,7 @@
 		//apply command movement
 		if (n < cmdframes)
 		{
-			//ax = 0;
+			ax = 0;
 			maxvel = phys_maxwalkvelocity;
 			accelerate = phys_airaccelerate;
 			VectorCopy(cmdmove, wishdir);
@@ -587,13 +598,13 @@
 				{
 					accelerate = phys_walkaccelerate;
 				} //end else
-				//ax = 2;
+				ax = 2;
 			} //end if
 			if (swimming)
 			{
 				maxvel = phys_maxswimvelocity;
 				accelerate = phys_swimaccelerate;
-				//ax = 3;
+				ax = 3;
 			} //end if
 			else
 			{

```

### `quake3e`  — sha256 `a5761e5aadaf...`, 38558 bytes

_Diff stat: +28 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_move.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_move.c	2026-04-16 20:02:26.894280200 +0100
@@ -168,7 +168,7 @@
 		//get the plane the face is in
 		plane = &aasworld.planes[face->planenum ^ side];
 		//if the origin is pretty close to the plane
-		if (fabsf(DotProduct(plane->normal, origin) - plane->dist) < 3)
+		if (fabs(DotProduct(plane->normal, origin) - plane->dist) < 3)
 		{
 			if (AAS_PointInsideFace(abs(facenum), origin, 0.1f)) return qtrue;
 		} //end if
@@ -227,10 +227,10 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-static vec3_t VEC_UP			= {0, -1,  0};
-static vec3_t MOVEDIR_UP		= {0,  0,  1};
-static vec3_t VEC_DOWN		= {0, -2,  0};
-static vec3_t MOVEDIR_DOWN	= {0,  0, -1};
+static const vec3_t VEC_UP			= {0, -1,  0};
+static const vec3_t MOVEDIR_UP		= {0,  0,  1};
+static const vec3_t VEC_DOWN		= {0, -2,  0};
+static const vec3_t MOVEDIR_DOWN	= {0,  0, -1};
 
 void AAS_SetMovedir(vec3_t angles, vec3_t movedir)
 {
@@ -287,7 +287,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-float AAS_WeaponJumpZVelocity(vec3_t origin, float radiusdamage)
+static float AAS_WeaponJumpZVelocity(vec3_t origin, float radiusdamage)
 {
 	vec3_t kvel, v, start, end, forward, right, viewangles, dir;
 	float	mass, knockback, points;
@@ -340,7 +340,7 @@
 //===========================================================================
 float AAS_RocketJumpZVelocity(vec3_t origin)
 {
-	//rocket radius damage is 120 (p_weapon.c: Weapon_RocketLauncher_Fire)
+	//rocket radius damage is 120
 	return AAS_WeaponJumpZVelocity(origin, 120);
 } //end of the function AAS_RocketJumpZVelocity
 //===========================================================================
@@ -351,7 +351,7 @@
 //===========================================================================
 float AAS_BFGJumpZVelocity(vec3_t origin)
 {
-	//bfg radius damage is 1000 (p_weapon.c: weapon_bfg_fire)
+	//bfg radius damage is 120
 	return AAS_WeaponJumpZVelocity(origin, 120);
 } //end of the function AAS_BFGJumpZVelocity
 //===========================================================================
@@ -361,7 +361,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_Accelerate(vec3_t velocity, float frametime, vec3_t wishdir, float wishspeed, float accel)
+static void AAS_Accelerate(vec3_t velocity, float frametime, vec3_t wishdir, float wishspeed, float accel)
 {
 	// q2 style
 	int			i;
@@ -388,7 +388,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void AAS_ApplyFriction(vec3_t vel, float friction, float stopspeed,
+static void AAS_ApplyFriction(vec3_t vel, float friction, float stopspeed,
 													float frametime)
 {
 	float speed, control, newspeed;
@@ -411,7 +411,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int AAS_ClipToBBox(aas_trace_t *trace, vec3_t start, vec3_t end, int presencetype, vec3_t mins, vec3_t maxs)
+static qboolean AAS_ClipToBBox( aas_trace_t *trace, const vec3_t start, const vec3_t end, int presencetype, const vec3_t mins, const vec3_t maxs )
 {
 	int i, j, side;
 	float front, back, frac, planedist;
@@ -433,6 +433,8 @@
 	frac = 1;
 	for (i = 0; i < 3; i++)
 	{
+		if ( fabsf( dir[i] ) < 0.001f ) // this may cause denormalization or division by zero
+			continue;
 		//get plane to test collision with for the current axis direction
 		if (dir[i] > 0) planedist = absmins[i];
 		else planedist = absmaxs[i];
@@ -490,14 +492,14 @@
 // Returns:				aas_clientmove_t
 // Changes Globals:		-
 //===========================================================================
-int AAS_ClientMovementPrediction(struct aas_clientmove_s *move,
-								int entnum, vec3_t origin,
+static int AAS_ClientMovementPrediction( aas_clientmove_t *move,
+								int entnum, const vec3_t origin,
 								int presencetype, int onground,
-								vec3_t velocity, vec3_t cmdmove,
+								const vec3_t velocity, const vec3_t cmdmove,
 								int cmdframes,
 								int maxframes, float frametime,
 								int stopevent, int stopareanum,
-								vec3_t mins, vec3_t maxs, int visualize)
+								const vec3_t mins, const vec3_t maxs, int visualize )
 {
 	float phys_friction, phys_stopspeed, phys_gravity, phys_waterfriction;
 	float phys_watergravity;
@@ -533,8 +535,8 @@
 	phys_maxsteepness = aassettings.phys_maxsteepness;
 	phys_jumpvel = aassettings.phys_jumpvel * frametime;
 	//
-	Com_Memset(move, 0, sizeof(aas_clientmove_t));
-	Com_Memset(&trace, 0, sizeof(aas_trace_t));
+	Com_Memset( move, 0, sizeof( *move ) );
+	Com_Memset( &trace, 0, sizeof( trace ) );
 	//start at the current origin
 	VectorCopy(origin, org);
 	org[2] += 0.25;
@@ -981,14 +983,15 @@
 // Changes Globals:		-
 //===========================================================================
 int AAS_PredictClientMovement(struct aas_clientmove_s *move,
-								int entnum, vec3_t origin,
+								int entnum, const vec3_t origin,
 								int presencetype, int onground,
-								vec3_t velocity, vec3_t cmdmove,
+								const vec3_t velocity, const vec3_t cmdmove,
 								int cmdframes,
 								int maxframes, float frametime,
 								int stopevent, int stopareanum, int visualize)
 {
-	vec3_t mins, maxs;
+	const vec3_t mins = { -4, -4, -4 };
+	const vec3_t maxs = { 4, 4, 4 };
 	return AAS_ClientMovementPrediction(move, entnum, origin, presencetype, onground,
 										velocity, cmdmove, cmdframes, maxframes,
 										frametime, stopevent, stopareanum,
@@ -1001,18 +1004,19 @@
 // Changes Globals:		-
 //===========================================================================
 int AAS_ClientMovementHitBBox(struct aas_clientmove_s *move,
-								int entnum, vec3_t origin,
+								int entnum, const vec3_t origin,
 								int presencetype, int onground,
-								vec3_t velocity, vec3_t cmdmove,
+								const vec3_t velocity, const vec3_t cmdmove,
 								int cmdframes,
 								int maxframes, float frametime,
-								vec3_t mins, vec3_t maxs, int visualize)
+								const vec3_t mins, const vec3_t maxs, int visualize)
 {
 	return AAS_ClientMovementPrediction(move, entnum, origin, presencetype, onground,
 										velocity, cmdmove, cmdframes, maxframes,
 										frametime, SE_HITBOUNDINGBOX, 0,
 										mins, maxs, visualize);
 } //end of the function AAS_ClientMovementHitBBox
+#if 0
 //===========================================================================
 //
 // Parameter:			-
@@ -1037,6 +1041,7 @@
 		botimport.Print(PRT_MESSAGE, "leave ground\n");
 	} //end if
 } //end of the function TestMovementPrediction
+#endif
 //===========================================================================
 // calculates the horizontal velocity needed to perform a jump from start
 // to end

```

### `openarena-engine`  — sha256 `f53f7daca2ea...`, 38305 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_move.c	2026-04-16 20:02:25.116863500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_aas_move.c	2026-04-16 22:48:25.709437000 +0100
@@ -168,7 +168,7 @@
 		//get the plane the face is in
 		plane = &aasworld.planes[face->planenum ^ side];
 		//if the origin is pretty close to the plane
-		if (fabsf(DotProduct(plane->normal, origin) - plane->dist) < 3)
+		if (abs(DotProduct(plane->normal, origin) - plane->dist) < 3)
 		{
 			if (AAS_PointInsideFace(abs(facenum), origin, 0.1f)) return qtrue;
 		} //end if
@@ -553,7 +553,7 @@
 		//if on the ground or swimming
 		if (onground || swimming)
 		{
-			friction = swimming ? phys_waterfriction : phys_friction;
+			friction = swimming ? phys_friction : phys_waterfriction;
 			//apply friction
 			VectorScale(frame_test_vel, 1/frametime, frame_test_vel);
 			AAS_ApplyFriction(frame_test_vel, friction, phys_stopspeed, frametime);

```
