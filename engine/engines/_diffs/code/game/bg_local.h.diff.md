# Diff: `code/game/bg_local.h`
**Canonical:** `wolfcamql-src` (sha256 `c3be835a9983...`, 2537 bytes)

## Variants

### `quake3-source`  — sha256 `1f8953894410...`, 2362 bytes

_Diff stat: +5 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_local.h	2026-04-16 20:02:25.189641600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\bg_local.h	2026-04-16 20:02:19.902126400 +0100
@@ -1,6 +1,3 @@
-#ifndef bg_local_h_included
-#define bg_local_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -18,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -27,7 +24,7 @@
 
 #define	MIN_WALK_NORMAL	0.7f		// can't walk on very steep slopes
 
-#define	STEPSIZE		22.0  //18.0  //22.0
+#define	STEPSIZE		18
 
 #define	JUMP_VELOCITY	270
 
@@ -63,6 +60,7 @@
 extern	float	pm_stopspeed;
 extern	float	pm_duckScale;
 extern	float	pm_swimScale;
+extern	float	pm_wadeScale;
 
 extern	float	pm_accelerate;
 extern	float	pm_airaccelerate;
@@ -75,14 +73,11 @@
 
 extern	int		c_pmove;
 
-extern vec3_t bg_playerMins;
-extern vec3_t bg_playerMaxs;
-
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce );
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce );
 void PM_AddTouchEnt( int entityNum );
 void PM_AddEvent( int newEvent );
 
 qboolean	PM_SlideMove( qboolean gravity );
 void		PM_StepSlideMove( qboolean gravity );
 
-#endif  // bg_local_h_included
+

```

### `openarena-engine`  — sha256 `f6c8c63bffa2...`, 2355 bytes
Also identical in: ioquake3

_Diff stat: +3 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_local.h	2026-04-16 20:02:25.189641600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\bg_local.h	2026-04-16 22:48:25.743535300 +0100
@@ -1,6 +1,3 @@
-#ifndef bg_local_h_included
-#define bg_local_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -27,7 +24,7 @@
 
 #define	MIN_WALK_NORMAL	0.7f		// can't walk on very steep slopes
 
-#define	STEPSIZE		22.0  //18.0  //22.0
+#define	STEPSIZE		18
 
 #define	JUMP_VELOCITY	270
 
@@ -75,14 +72,11 @@
 
 extern	int		c_pmove;
 
-extern vec3_t bg_playerMins;
-extern vec3_t bg_playerMaxs;
-
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce );
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce );
 void PM_AddTouchEnt( int entityNum );
 void PM_AddEvent( int newEvent );
 
 qboolean	PM_SlideMove( qboolean gravity );
 void		PM_StepSlideMove( qboolean gravity );
 
-#endif  // bg_local_h_included
+

```

### `openarena-gamecode`  — sha256 `b6b76b0f1d48...`, 2355 bytes

_Diff stat: +4 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_local.h	2026-04-16 20:02:25.189641600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\bg_local.h	2026-04-16 22:48:24.164479300 +0100
@@ -1,6 +1,3 @@
-#ifndef bg_local_h_included
-#define bg_local_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -27,7 +24,7 @@
 
 #define	MIN_WALK_NORMAL	0.7f		// can't walk on very steep slopes
 
-#define	STEPSIZE		22.0  //18.0  //22.0
+#define	STEPSIZE		18
 
 #define	JUMP_VELOCITY	270
 
@@ -62,7 +59,7 @@
 // movement parameters
 extern	float	pm_stopspeed;
 extern	float	pm_duckScale;
-extern	float	pm_swimScale;
+extern	float	pm_wadeScale;
 
 extern	float	pm_accelerate;
 extern	float	pm_airaccelerate;
@@ -75,14 +72,11 @@
 
 extern	int		c_pmove;
 
-extern vec3_t bg_playerMins;
-extern vec3_t bg_playerMaxs;
-
-void PM_ClipVelocity( const vec3_t in, const vec3_t normal, vec3_t out, float overbounce );
+void PM_ClipVelocity( vec3_t in, vec3_t normal, vec3_t out, float overbounce );
 void PM_AddTouchEnt( int entityNum );
 void PM_AddEvent( int newEvent );
 
 qboolean	PM_SlideMove( qboolean gravity );
 void		PM_StepSlideMove( qboolean gravity );
 
-#endif  // bg_local_h_included
+

```
