# Diff: `code/game/g_mover.c`
**Canonical:** `wolfcamql-src` (sha256 `18259fc2414f...`, 43851 bytes)

## Variants

### `quake3-source`  — sha256 `4c9934ebd38e...`, 42562 bytes

_Diff stat: +36 / -71 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_mover.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_mover.c	2026-04-16 20:02:19.908574000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -33,6 +33,8 @@
 ===============================================================================
 */
 
+void MatchTeam( gentity_t *teamLeader, int moverState, int time );
+
 typedef struct {
 	gentity_t	*ent;
 	vec3_t	origin;
@@ -164,7 +166,7 @@
 
 	// may have pushed them off an edge
 	if ( check->s.groundEntityNum != pusher->s.number ) {
-		check->s.groundEntityNum = ENTITYNUM_NONE;
+		check->s.groundEntityNum = -1;
 	}
 
 	block = G_TestEntityPosition( check );
@@ -180,7 +182,7 @@
 	}
 
 	// if it is ok to leave in the old position, do it
-	// this is only relevant for riding entities, not pushed
+	// this is only relevent for riding entities, not pushed
 	// Sliding trapdoors can cause this.
 	VectorCopy( (pushed_p-1)->origin, check->s.pos.trBase);
 	if ( check->client ) {
@@ -189,7 +191,7 @@
 	VectorCopy( (pushed_p-1)->angles, check->s.apos.trBase );
 	block = G_TestEntityPosition (check);
 	if ( !block ) {
-		check->s.groundEntityNum = ENTITYNUM_NONE;
+		check->s.groundEntityNum = -1;
 		pushed_p--;
 		return qtrue;
 	}
@@ -308,7 +310,7 @@
 
 	listedEntities = trap_EntitiesInBox( totalMins, totalMaxs, entityList, MAX_GENTITIES );
 
-	// move the pusher to its final position
+	// move the pusher to it's final position
 	VectorAdd( pusher->r.currentOrigin, move, pusher->r.currentOrigin );
 	VectorAdd( pusher->r.currentAngles, amove, pusher->r.currentAngles );
 	trap_LinkEntity( pusher );
@@ -317,7 +319,7 @@
 	for ( e = 0 ; e < listedEntities ; e++ ) {
 		check = &g_entities[ entityList[ e ] ];
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( check->s.eType == ET_MISSILE ) {
 			// if it is a prox mine
 			if ( !strcmp(check->classname, "prox mine") ) {
@@ -424,7 +426,7 @@
 
 	obstacle = NULL;
 
-	// make sure all team members can move before committing
+	// make sure all team slaves can move before commiting
 	// any moves or calling any think functions
 	// if the move is blocked, all moved objects will be backed out
 	pushed_p = pushed;
@@ -478,7 +480,7 @@
 void G_RunMover( gentity_t *ent ) {
 	// if not a team captain, don't do anything, because
 	// the captain will handle everything
-	if ( ent->flags & FL_TEAMMEMBER ) {
+	if ( ent->flags & FL_TEAMSLAVE ) {
 		return;
 	}
 
@@ -550,10 +552,10 @@
 ================
 */
 void MatchTeam( gentity_t *teamLeader, int moverState, int time ) {
-	gentity_t		*member;
+	gentity_t		*slave;
 
-	for ( member = teamLeader ; member ; member = member->teamchain ) {
-		SetMoverState( member, moverState, time );
+	for ( slave = teamLeader ; slave ; slave = slave->teamchain ) {
+		SetMoverState( slave, moverState, time );
 	}
 }
 
@@ -634,7 +636,7 @@
 	int		partial;
 
 	// only the master should be used
-	if ( ent->flags & FL_TEAMMEMBER ) {
+	if ( ent->flags & FL_TEAMSLAVE ) {
 		Use_BinaryMover( ent->teammaster, other, activator );
 		return;
 	}
@@ -718,7 +720,7 @@
 	qboolean	lightSet, colorSet;
 	char		*sound;
 
-	// if the "model2" key is set, use a separate model
+	// if the "model2" key is set, use a seperate model
 	// for drawing, but clip against the brushes
 	if ( ent->model2 ) {
 		ent->s.modelindex2 = G_ModelIndex( ent->model2 );
@@ -752,19 +754,6 @@
 			i = 255;
 		}
 		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-		//Com_Printf("^5mover light ... %d\n", ent->s.number);
-	} else {
-#if 0
-		int r, g, b, i;
-
-		Com_Printf("^1fake light\n");
-
-		i = 100 / 4;
-		r = 0;
-		g = 255;
-		b = 0;
-		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-#endif
 	}
 
 
@@ -840,26 +829,26 @@
 ================
 */
 static void Touch_DoorTriggerSpectator( gentity_t *ent, gentity_t *other, trace_t *trace ) {
-	int axis;
-	float doorMin, doorMax;
-	vec3_t origin;
+	int i, axis;
+	vec3_t origin, dir, angles;
 
 	axis = ent->count;
-	// the constants below relate to constants in Think_SpawnNewDoorTrigger()
-	doorMin = ent->r.absmin[axis] + 100;
-	doorMax = ent->r.absmax[axis] - 100;
-
-	VectorCopy(other->client->ps.origin, origin);
-
-	if (origin[axis] < doorMin || origin[axis] > doorMax) return;
-
-	if (fabs(origin[axis] - doorMax) < fabs(origin[axis] - doorMin)) {
-		origin[axis] = doorMin - 10;
-	} else {
-		origin[axis] = doorMax + 10;
+	VectorClear(dir);
+	if (fabs(other->s.origin[axis] - ent->r.absmax[axis]) <
+		fabs(other->s.origin[axis] - ent->r.absmin[axis])) {
+		origin[axis] = ent->r.absmin[axis] - 10;
+		dir[axis] = -1;
 	}
-
-	TeleportPlayer(other, origin, tv(10000000.0, 0, 0));
+	else {
+		origin[axis] = ent->r.absmax[axis] + 10;
+		dir[axis] = 1;
+	}
+	for (i = 0; i < 3; i++) {
+		if (i == axis) continue;
+		origin[i] = (ent->r.absmin[i] + ent->r.absmax[i]) * 0.5;
+	}
+	vectoangles(dir, angles);
+	TeleportPlayer(other, origin, angles );
 }
 
 /*
@@ -894,12 +883,7 @@
 	vec3_t		mins, maxs;
 	int			i, best;
 
-	if (!ent) {
-		Com_Printf("^1ERROR:  Think_SpawnNewDoorTrigger ent == null\n");
-		return;
-	}
-
-	// set all of the members as shootable
+	// set all of the slaves as shootable
 	for ( other = ent ; other ; other = other->teamchain ) {
 		other->takedamage = qtrue;
 	}
@@ -1011,7 +995,7 @@
 
 	ent->nextthink = level.time + FRAMETIME;
 
-	if ( ! (ent->flags & FL_TEAMMEMBER ) ) {
+	if ( ! (ent->flags & FL_TEAMSLAVE ) ) {
 		int health;
 
 		G_SpawnInt( "health", "0", &health );
@@ -1199,7 +1183,7 @@
 
 
 /*QUAKED func_button (0 .5 .8) ?
-When a button is touched, it moves some distance in the direction of its angle, triggers all of its targets, waits some time, then returns to its original position where it can be triggered again.
+When a button is touched, it moves some distance in the direction of it's angle, triggers all of it's targets, waits some time, then returns to it's original position where it can be triggered again.
 
 "model2"	.md3 model to also draw
 "angle"		determines the opening direction
@@ -1293,7 +1277,7 @@
 	vec3_t			move;
 	float			length;
 
-	// copy the appropriate values
+	// copy the apropriate values
 	next = ent->nextTrain;
 	if ( !next || !next->nextTrain ) {
 		return;		// just stop
@@ -1324,25 +1308,6 @@
 
 	ent->s.pos.trDuration = length * 1000 / speed;
 
-	// Tequila comment: Be sure to send to clients after any fast move case
-	ent->r.svFlags &= ~SVF_NOCLIENT;
-
-	// Tequila comment: Fast move case
-	if(ent->s.pos.trDuration<1) {
-		// Tequila comment: As trDuration is used later in a division, we need to avoid that case now
-		// With null trDuration,
-		// the calculated rocks bounding box becomes infinite and the engine think for a short time
-		// any entity is riding that mover but not the world entity... In rare case, I found it
-		// can also stuck every map entities after func_door are used.
-		// The desired effect with very very big speed is to have instant move, so any not null duration
-		// lower than a frame duration should be sufficient.
-		// Afaik, the negative case don't have to be supported.
-		ent->s.pos.trDuration=1;
-
-		// Tequila comment: Don't send entity to clients so it becomes really invisible 
-		ent->r.svFlags |= SVF_NOCLIENT;
-	}
-
 	// looping sound
 	ent->s.loopSound = next->soundLoop;
 

```

### `ioquake3`  — sha256 `dd69c6830577...`, 43525 bytes

_Diff stat: +1 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_mover.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_mover.c	2026-04-16 20:02:21.546476900 +0100
@@ -317,7 +317,7 @@
 	for ( e = 0 ; e < listedEntities ; e++ ) {
 		check = &g_entities[ entityList[ e ] ];
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( check->s.eType == ET_MISSILE ) {
 			// if it is a prox mine
 			if ( !strcmp(check->classname, "prox mine") ) {
@@ -752,19 +752,6 @@
 			i = 255;
 		}
 		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-		//Com_Printf("^5mover light ... %d\n", ent->s.number);
-	} else {
-#if 0
-		int r, g, b, i;
-
-		Com_Printf("^1fake light\n");
-
-		i = 100 / 4;
-		r = 0;
-		g = 255;
-		b = 0;
-		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-#endif
 	}
 
 
@@ -895,7 +882,6 @@
 	int			i, best;
 
 	if (!ent) {
-		Com_Printf("^1ERROR:  Think_SpawnNewDoorTrigger ent == null\n");
 		return;
 	}
 

```

### `openarena-engine`  — sha256 `f88e09b7651e...`, 43481 bytes

_Diff stat: +12 / -30 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_mover.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_mover.c	2026-04-16 22:48:25.748537400 +0100
@@ -180,7 +180,7 @@
 	}
 
 	// if it is ok to leave in the old position, do it
-	// this is only relevant for riding entities, not pushed
+	// this is only relevent for riding entities, not pushed
 	// Sliding trapdoors can cause this.
 	VectorCopy( (pushed_p-1)->origin, check->s.pos.trBase);
 	if ( check->client ) {
@@ -317,7 +317,7 @@
 	for ( e = 0 ; e < listedEntities ; e++ ) {
 		check = &g_entities[ entityList[ e ] ];
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( check->s.eType == ET_MISSILE ) {
 			// if it is a prox mine
 			if ( !strcmp(check->classname, "prox mine") ) {
@@ -424,7 +424,7 @@
 
 	obstacle = NULL;
 
-	// make sure all team members can move before committing
+	// make sure all team slaves can move before commiting
 	// any moves or calling any think functions
 	// if the move is blocked, all moved objects will be backed out
 	pushed_p = pushed;
@@ -478,7 +478,7 @@
 void G_RunMover( gentity_t *ent ) {
 	// if not a team captain, don't do anything, because
 	// the captain will handle everything
-	if ( ent->flags & FL_TEAMMEMBER ) {
+	if ( ent->flags & FL_TEAMSLAVE ) {
 		return;
 	}
 
@@ -550,10 +550,10 @@
 ================
 */
 void MatchTeam( gentity_t *teamLeader, int moverState, int time ) {
-	gentity_t		*member;
+	gentity_t		*slave;
 
-	for ( member = teamLeader ; member ; member = member->teamchain ) {
-		SetMoverState( member, moverState, time );
+	for ( slave = teamLeader ; slave ; slave = slave->teamchain ) {
+		SetMoverState( slave, moverState, time );
 	}
 }
 
@@ -634,7 +634,7 @@
 	int		partial;
 
 	// only the master should be used
-	if ( ent->flags & FL_TEAMMEMBER ) {
+	if ( ent->flags & FL_TEAMSLAVE ) {
 		Use_BinaryMover( ent->teammaster, other, activator );
 		return;
 	}
@@ -718,7 +718,7 @@
 	qboolean	lightSet, colorSet;
 	char		*sound;
 
-	// if the "model2" key is set, use a separate model
+	// if the "model2" key is set, use a seperate model
 	// for drawing, but clip against the brushes
 	if ( ent->model2 ) {
 		ent->s.modelindex2 = G_ModelIndex( ent->model2 );
@@ -752,19 +752,6 @@
 			i = 255;
 		}
 		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-		//Com_Printf("^5mover light ... %d\n", ent->s.number);
-	} else {
-#if 0
-		int r, g, b, i;
-
-		Com_Printf("^1fake light\n");
-
-		i = 100 / 4;
-		r = 0;
-		g = 255;
-		b = 0;
-		ent->s.constantLight = r | ( g << 8 ) | ( b << 16 ) | ( i << 24 );
-#endif
 	}
 
 
@@ -894,12 +881,7 @@
 	vec3_t		mins, maxs;
 	int			i, best;
 
-	if (!ent) {
-		Com_Printf("^1ERROR:  Think_SpawnNewDoorTrigger ent == null\n");
-		return;
-	}
-
-	// set all of the members as shootable
+	// set all of the slaves as shootable
 	for ( other = ent ; other ; other = other->teamchain ) {
 		other->takedamage = qtrue;
 	}
@@ -1011,7 +993,7 @@
 
 	ent->nextthink = level.time + FRAMETIME;
 
-	if ( ! (ent->flags & FL_TEAMMEMBER ) ) {
+	if ( ! (ent->flags & FL_TEAMSLAVE ) ) {
 		int health;
 
 		G_SpawnInt( "health", "0", &health );
@@ -1293,7 +1275,7 @@
 	vec3_t			move;
 	float			length;
 
-	// copy the appropriate values
+	// copy the apropriate values
 	next = ent->nextTrain;
 	if ( !next || !next->nextTrain ) {
 		return;		// just stop

```

### `openarena-gamecode`  — sha256 `92bded4e936c...`, 44628 bytes

_Diff stat: +193 / -133 lines_

_(full diff is 25002 bytes — see files directly)_
