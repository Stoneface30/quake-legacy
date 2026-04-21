# Diff: `code/botlib/be_ai_move.c`
**Canonical:** `wolfcamql-src` (sha256 `8157ae21bf07...`, 116117 bytes)

## Variants

### `quake3-source`  — sha256 `3d9018b8a206...`, 116680 bytes

_Diff stat: +130 / -93 lines_

_(full diff is 24736 bytes — see files directly)_

### `ioquake3`  — sha256 `c6054caa9198...`, 115346 bytes

_Diff stat: +1 / -14 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_move.c	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\botlib\be_ai_move.c	2026-04-16 20:02:21.509907100 +0100
@@ -1488,8 +1488,6 @@
 		hordir[0] = reach->end[0] - ms->origin[0];
 		hordir[1] = reach->end[1] - ms->origin[1];
 		hordir[2] = 0;
-		// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-		VectorNormalize(hordir);
 		//
 		BotCheckBlocked(ms, hordir, qtrue, &result);
 		//
@@ -1581,9 +1579,6 @@
 	dir[0] += crandom() * 10;
 	dir[1] += crandom() * 10;
 	dir[2] += 70 + crandom() * 10;
-
-	// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(dir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-	VectorNormalize(dir);
 	//elemantary actions
 	EA_Move(ms->client, dir, 400);
 	//set the ideal view angles
@@ -1721,10 +1716,6 @@
 		VectorCopy(dir, hordir);
 		hordir[2] = 0;
 		//
-
-		// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-
-		VectorNormalize(hordir);
 		speed = 400;
 	} //end if
 	//
@@ -1791,7 +1782,7 @@
 bot_moveresult_t BotTravel_Jump(bot_movestate_t *ms, aas_reachability_t *reach)
 {
 	vec3_t hordir, dir1, dir2, mins, maxs, start, end;
-    int gapdist;
+	int gapdist;
 	float dist1, dist2, speed;
 	bot_moveresult_t_cleared( result );
 	bsp_trace_t trace;
@@ -2879,10 +2870,6 @@
 	hordir[0] = reach->start[0] - ms->origin[0];
 	hordir[1] = reach->start[1] - ms->origin[1];
 	hordir[2] = 0;
-
-	// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-
-	VectorNormalize(hordir);
 	//
 	BotCheckBlocked(ms, hordir, qtrue, &result);
 	//elemantary action move in direction

```

### `quake3e`  — sha256 `412f8505c184...`, 115866 bytes

_Diff stat: +94 / -103 lines_

_(full diff is 28643 bytes — see files directly)_

### `openarena-engine`  — sha256 `b474d1bdea53...`, 115341 bytes

_Diff stat: +5 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_move.c	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_move.c	2026-04-16 22:48:25.714694200 +0100
@@ -1488,8 +1488,6 @@
 		hordir[0] = reach->end[0] - ms->origin[0];
 		hordir[1] = reach->end[1] - ms->origin[1];
 		hordir[2] = 0;
-		// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-		VectorNormalize(hordir);
 		//
 		BotCheckBlocked(ms, hordir, qtrue, &result);
 		//
@@ -1581,9 +1579,6 @@
 	dir[0] += crandom() * 10;
 	dir[1] += crandom() * 10;
 	dir[2] += 70 + crandom() * 10;
-
-	// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(dir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-	VectorNormalize(dir);
 	//elemantary actions
 	EA_Move(ms->client, dir, 400);
 	//set the ideal view angles
@@ -1610,7 +1605,7 @@
 	VectorSubtract(reach->start, ms->origin, dir);
 	VectorNormalize(dir);
 	BotCheckBlocked(ms, dir, qtrue, &result);
-	//if the reachability start and end are practically above each other
+	//if the reachability start and end are practially above each other
 	VectorSubtract(reach->end, reach->start, dir);
 	dir[2] = 0;
 	reachhordist = VectorLength(dir);
@@ -1721,10 +1716,6 @@
 		VectorCopy(dir, hordir);
 		hordir[2] = 0;
 		//
-
-		// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-
-		VectorNormalize(hordir);
 		speed = 400;
 	} //end if
 	//
@@ -1791,7 +1782,7 @@
 bot_moveresult_t BotTravel_Jump(bot_movestate_t *ms, aas_reachability_t *reach)
 {
 	vec3_t hordir, dir1, dir2, mins, maxs, start, end;
-    int gapdist;
+	int gapdist;
 	float dist1, dist2, speed;
 	bot_moveresult_t_cleared( result );
 	bsp_trace_t trace;
@@ -2063,7 +2054,7 @@
 		botimport.Print(PRT_MESSAGE, "bot on elevator\n");
 #endif //DEBUG_ELEVATOR
 		//if vertically not too far from the end point
-		if (fabsf(ms->origin[2] - reach->end[2]) < sv_maxbarrier->value)
+		if (abs(ms->origin[2] - reach->end[2]) < sv_maxbarrier->value)
 		{
 #ifdef DEBUG_ELEVATOR
 			botimport.Print(PRT_MESSAGE, "bot moving to end\n");
@@ -2753,7 +2744,7 @@
 	result.ideal_viewangles[PITCH] = 90;
 	//set the view angles directly
 	EA_View(ms->client, result.ideal_viewangles);
-	//view is important for the movement
+	//view is important for the movment
 	result.flags |= MOVERESULT_MOVEMENTVIEWSET;
 	//select the rocket launcher
 	EA_SelectWeapon(ms->client, (int) weapindex_rocketlauncher->value);
@@ -2813,7 +2804,7 @@
 	result.ideal_viewangles[PITCH] = 90;
 	//set the view angles directly
 	EA_View(ms->client, result.ideal_viewangles);
-	//view is important for the movement
+	//view is important for the movment
 	result.flags |= MOVERESULT_MOVEMENTVIEWSET;
 	//select the rocket launcher
 	EA_SelectWeapon(ms->client, (int) weapindex_bfg10k->value);
@@ -2879,10 +2870,6 @@
 	hordir[0] = reach->start[0] - ms->origin[0];
 	hordir[1] = reach->start[1] - ms->origin[1];
 	hordir[2] = 0;
-
-	// 2017-07-09 ioquake3 patch 2104 removed 'dist = VectorNormalize(hordir)' apparently because dist isn't used, but not sure if VectorNormalize() is still needed
-
-	VectorNormalize(hordir);
 	//
 	BotCheckBlocked(ms, hordir, qtrue, &result);
 	//elemantary action move in direction

```
