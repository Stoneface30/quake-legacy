# Diff: `code/game/g_missile.c`
**Canonical:** `wolfcamql-src` (sha256 `63793a83889c...`, 23300 bytes)

## Variants

### `quake3-source`  — sha256 `9915e6765633...`, 22428 bytes

_Diff stat: +11 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_missile.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_missile.c	2026-04-16 20:02:19.907572900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -45,11 +45,7 @@
 		VectorScale( ent->s.pos.trDelta, 0.65, ent->s.pos.trDelta );
 		// check for stop
 		if ( trace->plane.normal[2] > 0.2 && VectorLength( ent->s.pos.trDelta ) < 40 ) {
-			//FIXME wolfcam grenade hack to match ql a little and to allow fx
-			// 'moveGravity' without particles being stuck in surface
-			trace->endpos[2] += 2;
 			G_SetOrigin( ent, trace->endpos );
-			ent->s.time = level.time / 4;
 			return;
 		}
 	}
@@ -96,7 +92,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 ProximityMine_Explode
@@ -148,7 +144,7 @@
 		}
 	}
 
-	// ok, now check for ability to damage so we don't get triggered through walls, closed doors, etc...
+	// ok, now check for ability to damage so we don't get triggered thru walls, closed doors, etc...
 	if( !CanDamage( other, trigger->s.pos.trBase ) ) {
 		return;
 	}
@@ -273,7 +269,7 @@
 void G_MissileImpact( gentity_t *ent, trace_t *trace ) {
 	gentity_t		*other;
 	qboolean		hitClient = qfalse;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t			forward, impactpoint, bouncedir;
 	int				eFlags;
 #endif
@@ -287,7 +283,7 @@
 		return;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( other->takedamage ) {
 		if ( ent->s.weapon != WP_PROX_LAUNCHER ) {
 			if ( other->client && other->client->invulnerabilityTime > level.time ) {
@@ -327,7 +323,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.weapon == WP_PROX_LAUNCHER ) {
 		if( ent->s.pos.trType != TR_GRAVITY ) {
 			return;
@@ -460,7 +456,7 @@
 	if ( ent->target_ent ) {
 		passent = ent->target_ent->s.number;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// prox mines that left the owner bbox will attach to anything, even the owner
 	else if (ent->s.weapon == WP_PROX_LAUNCHER && ent->count) {
 		passent = ENTITYNUM_NONE;
@@ -499,7 +495,7 @@
 			return;		// exploded
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// if the prox mine wasn't yet outside the player body
 	if (ent->s.weapon == WP_PROX_LAUNCHER && !ent->count) {
 		// check if the prox mine is outside the owner bbox
@@ -535,7 +531,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_PLASMAGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->splashDamage = 15;
@@ -548,8 +543,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	//VectorScale( dir, 2000, bolt->s.pos.trDelta );
-	VectorScale(dir, g_weapon_plasma_speed.integer, bolt->s.pos.trDelta);
+	VectorScale( dir, 2000, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 
 	VectorCopy (start, bolt->r.currentOrigin);
@@ -579,8 +573,6 @@
 	bolt->s.weapon = WP_GRENADE_LAUNCHER;
 	bolt->s.eFlags = EF_BOUNCE_HALF;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
-	bolt->s.clientNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -622,7 +614,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_BFG;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -663,7 +654,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_ROCKET_LAUNCHER;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -676,7 +666,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	VectorScale( dir, g_weapon_rocket_speed.integer, bolt->s.pos.trDelta );
+	VectorScale( dir, 900, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 	VectorCopy (start, bolt->r.currentOrigin);
 
@@ -720,7 +710,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 =================
 fire_nail
@@ -742,7 +732,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_NAILGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->methodOfDeath = MOD_NAIL;
@@ -791,7 +780,6 @@
 	bolt->s.weapon = WP_PROX_LAUNCHER;
 	bolt->s.eFlags = 0;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 0;
 	bolt->splashDamage = 100;

```

### `ioquake3`  — sha256 `3385e06db7dc...`, 22486 bytes

_Diff stat: +9 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_missile.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_missile.c	2026-04-16 20:02:21.545479700 +0100
@@ -45,9 +45,6 @@
 		VectorScale( ent->s.pos.trDelta, 0.65, ent->s.pos.trDelta );
 		// check for stop
 		if ( trace->plane.normal[2] > 0.2 && VectorLength( ent->s.pos.trDelta ) < 40 ) {
-			//FIXME wolfcam grenade hack to match ql a little and to allow fx
-			// 'moveGravity' without particles being stuck in surface
-			trace->endpos[2] += 2;
 			G_SetOrigin( ent, trace->endpos );
 			ent->s.time = level.time / 4;
 			return;
@@ -96,7 +93,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 ProximityMine_Explode
@@ -273,7 +270,7 @@
 void G_MissileImpact( gentity_t *ent, trace_t *trace ) {
 	gentity_t		*other;
 	qboolean		hitClient = qfalse;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t			forward, impactpoint, bouncedir;
 	int				eFlags;
 #endif
@@ -287,7 +284,7 @@
 		return;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( other->takedamage ) {
 		if ( ent->s.weapon != WP_PROX_LAUNCHER ) {
 			if ( other->client && other->client->invulnerabilityTime > level.time ) {
@@ -327,7 +324,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.weapon == WP_PROX_LAUNCHER ) {
 		if( ent->s.pos.trType != TR_GRAVITY ) {
 			return;
@@ -460,7 +457,7 @@
 	if ( ent->target_ent ) {
 		passent = ent->target_ent->s.number;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// prox mines that left the owner bbox will attach to anything, even the owner
 	else if (ent->s.weapon == WP_PROX_LAUNCHER && ent->count) {
 		passent = ENTITYNUM_NONE;
@@ -499,7 +496,7 @@
 			return;		// exploded
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// if the prox mine wasn't yet outside the player body
 	if (ent->s.weapon == WP_PROX_LAUNCHER && !ent->count) {
 		// check if the prox mine is outside the owner bbox
@@ -535,7 +532,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_PLASMAGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->splashDamage = 15;
@@ -548,8 +544,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	//VectorScale( dir, 2000, bolt->s.pos.trDelta );
-	VectorScale(dir, g_weapon_plasma_speed.integer, bolt->s.pos.trDelta);
+	VectorScale( dir, 2000, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 
 	VectorCopy (start, bolt->r.currentOrigin);
@@ -579,8 +574,6 @@
 	bolt->s.weapon = WP_GRENADE_LAUNCHER;
 	bolt->s.eFlags = EF_BOUNCE_HALF;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
-	bolt->s.clientNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -622,7 +615,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_BFG;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -663,7 +655,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_ROCKET_LAUNCHER;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -676,7 +667,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	VectorScale( dir, g_weapon_rocket_speed.integer, bolt->s.pos.trDelta );
+	VectorScale( dir, 900, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 	VectorCopy (start, bolt->r.currentOrigin);
 
@@ -720,7 +711,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 =================
 fire_nail
@@ -742,7 +733,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_NAILGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->methodOfDeath = MOD_NAIL;
@@ -791,7 +781,6 @@
 	bolt->s.weapon = WP_PROX_LAUNCHER;
 	bolt->s.eFlags = 0;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 0;
 	bolt->splashDamage = 100;

```

### `openarena-engine`  — sha256 `bf105201bc68...`, 22483 bytes

_Diff stat: +10 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_missile.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_missile.c	2026-04-16 22:48:25.748537400 +0100
@@ -45,9 +45,6 @@
 		VectorScale( ent->s.pos.trDelta, 0.65, ent->s.pos.trDelta );
 		// check for stop
 		if ( trace->plane.normal[2] > 0.2 && VectorLength( ent->s.pos.trDelta ) < 40 ) {
-			//FIXME wolfcam grenade hack to match ql a little and to allow fx
-			// 'moveGravity' without particles being stuck in surface
-			trace->endpos[2] += 2;
 			G_SetOrigin( ent, trace->endpos );
 			ent->s.time = level.time / 4;
 			return;
@@ -96,7 +93,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 ProximityMine_Explode
@@ -148,7 +145,7 @@
 		}
 	}
 
-	// ok, now check for ability to damage so we don't get triggered through walls, closed doors, etc...
+	// ok, now check for ability to damage so we don't get triggered thru walls, closed doors, etc...
 	if( !CanDamage( other, trigger->s.pos.trBase ) ) {
 		return;
 	}
@@ -273,7 +270,7 @@
 void G_MissileImpact( gentity_t *ent, trace_t *trace ) {
 	gentity_t		*other;
 	qboolean		hitClient = qfalse;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t			forward, impactpoint, bouncedir;
 	int				eFlags;
 #endif
@@ -287,7 +284,7 @@
 		return;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( other->takedamage ) {
 		if ( ent->s.weapon != WP_PROX_LAUNCHER ) {
 			if ( other->client && other->client->invulnerabilityTime > level.time ) {
@@ -327,7 +324,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.weapon == WP_PROX_LAUNCHER ) {
 		if( ent->s.pos.trType != TR_GRAVITY ) {
 			return;
@@ -460,7 +457,7 @@
 	if ( ent->target_ent ) {
 		passent = ent->target_ent->s.number;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// prox mines that left the owner bbox will attach to anything, even the owner
 	else if (ent->s.weapon == WP_PROX_LAUNCHER && ent->count) {
 		passent = ENTITYNUM_NONE;
@@ -499,7 +496,7 @@
 			return;		// exploded
 		}
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// if the prox mine wasn't yet outside the player body
 	if (ent->s.weapon == WP_PROX_LAUNCHER && !ent->count) {
 		// check if the prox mine is outside the owner bbox
@@ -535,7 +532,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_PLASMAGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->splashDamage = 15;
@@ -548,8 +544,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	//VectorScale( dir, 2000, bolt->s.pos.trDelta );
-	VectorScale(dir, g_weapon_plasma_speed.integer, bolt->s.pos.trDelta);
+	VectorScale( dir, 2000, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 
 	VectorCopy (start, bolt->r.currentOrigin);
@@ -579,8 +574,6 @@
 	bolt->s.weapon = WP_GRENADE_LAUNCHER;
 	bolt->s.eFlags = EF_BOUNCE_HALF;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
-	bolt->s.clientNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -622,7 +615,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_BFG;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -663,7 +655,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_ROCKET_LAUNCHER;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -676,7 +667,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	VectorScale( dir, g_weapon_rocket_speed.integer, bolt->s.pos.trDelta );
+	VectorScale( dir, 900, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 	VectorCopy (start, bolt->r.currentOrigin);
 
@@ -720,7 +711,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 =================
 fire_nail
@@ -742,7 +733,6 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_NAILGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->methodOfDeath = MOD_NAIL;
@@ -791,7 +781,6 @@
 	bolt->s.weapon = WP_PROX_LAUNCHER;
 	bolt->s.eFlags = 0;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
 	bolt->parent = self;
 	bolt->damage = 0;
 	bolt->splashDamage = 100;

```

### `openarena-gamecode`  — sha256 `921c5d1ae4c0...`, 25479 bytes

_Diff stat: +175 / -63 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_missile.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_missile.c	2026-04-16 22:48:24.172990200 +0100
@@ -30,7 +30,8 @@
 
 ================
 */
-void G_BounceMissile( gentity_t *ent, trace_t *trace ) {
+void G_BounceMissile( gentity_t *ent, trace_t *trace )
+{
 	vec3_t	velocity;
 	float	dot;
 	int		hitTime;
@@ -45,9 +46,6 @@
 		VectorScale( ent->s.pos.trDelta, 0.65, ent->s.pos.trDelta );
 		// check for stop
 		if ( trace->plane.normal[2] > 0.2 && VectorLength( ent->s.pos.trDelta ) < 40 ) {
-			//FIXME wolfcam grenade hack to match ql a little and to allow fx
-			// 'moveGravity' without particles being stuck in surface
-			trace->endpos[2] += 2;
 			G_SetOrigin( ent, trace->endpos );
 			ent->s.time = level.time / 4;
 			return;
@@ -67,7 +65,8 @@
 Explode a missile without an impact
 ================
 */
-void G_ExplodeMissile( gentity_t *ent ) {
+void G_ExplodeMissile( gentity_t *ent )
+{
 	vec3_t		dir;
 	vec3_t		origin;
 
@@ -87,22 +86,22 @@
 	// splash damage
 	if ( ent->splashDamage ) {
 		if( G_RadiusDamage( ent->r.currentOrigin, ent->parent, ent->splashDamage, ent->splashRadius, ent
-			, ent->splashMethodOfDeath ) ) {
+		                    , ent->splashMethodOfDeath ) ) {
 			g_entities[ent->r.ownerNum].client->accuracy_hits++;
+			g_entities[ent->r.ownerNum].client->accuracy[ent->s.weapon][1]++;
 		}
 	}
 
 	trap_LinkEntity( ent );
 }
 
-
-#if 1  //def MPACK
 /*
 ================
 ProximityMine_Explode
 ================
 */
-static void ProximityMine_Explode( gentity_t *mine ) {
+static void ProximityMine_Explode( gentity_t *mine )
+{
 	G_ExplodeMissile( mine );
 	// if the prox mine has a trigger free it
 	if (mine->activator) {
@@ -116,7 +115,8 @@
 ProximityMine_Die
 ================
 */
-static void ProximityMine_Die( gentity_t *ent, gentity_t *inflictor, gentity_t *attacker, int damage, int mod ) {
+static void ProximityMine_Die( gentity_t *ent, gentity_t *inflictor, gentity_t *attacker, int damage, int mod )
+{
 	ent->think = ProximityMine_Explode;
 	ent->nextthink = level.time + 1;
 }
@@ -126,7 +126,8 @@
 ProximityMine_Trigger
 ================
 */
-void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace ) {
+void ProximityMine_Trigger( gentity_t *trigger, gentity_t *other, trace_t *trace )
+{
 	vec3_t		v;
 	gentity_t	*mine;
 
@@ -141,14 +142,14 @@
 	}
 
 
-	if ( g_gametype.integer >= GT_TEAM ) {
+	if ( g_gametype.integer >= GT_TEAM && g_ffa_gt!=1) {
 		// don't trigger same team mines
 		if (trigger->parent->s.generic1 == other->client->sess.sessionTeam) {
 			return;
 		}
 	}
 
-	// ok, now check for ability to damage so we don't get triggered through walls, closed doors, etc...
+	// ok, now check for ability to damage so we don't get triggered thru walls, closed doors, etc...
 	if( !CanDamage( other, trigger->s.pos.trBase ) ) {
 		return;
 	}
@@ -167,12 +168,63 @@
 ProximityMine_Activate
 ================
 */
-static void ProximityMine_Activate( gentity_t *ent ) {
+static void ProximityMine_Activate( gentity_t *ent )
+{
 	gentity_t	*trigger;
 	float		r;
+	vec3_t          v1;
+	gentity_t       *flag;
+	char            *c = NULL;
+	qboolean        nearFlag = qfalse;
+
+	// find the flag
+	switch (ent->s.generic1) {
+	case TEAM_RED:
+		c = "team_CTF_redflag";
+		break;
+	case TEAM_BLUE:
+		c = "team_CTF_blueflag";
+		break;
+	default:
+		c = NULL;
+	}
+	
+	if (g_gametype.integer == GT_TEAM || g_gametype.integer == GT_DOMINATION || g_gametype.integer == GT_ELIMINATION || g_gametype.integer == GT_DOUBLE_D) {
+		c = NULL;
+	}
+	
+	if (g_gametype.integer == GT_OBELISK || g_gametype.integer == GT_HARVESTER) {
+		switch (ent->s.generic1) {
+		case TEAM_RED:
+			c = "team_redobelisk";
+			break;
+		case TEAM_BLUE:
+			c = "team_blueobelisk";
+			break;
+		default:
+			c = NULL;
+		}
+	}
+
+	if(c) {
+		flag = NULL;
+		while ((flag = G_Find (flag, FOFS(classname), c)) != NULL) {
+			if (!(flag->flags & FL_DROPPED_ITEM))
+				break;
+		}
+
+		if(flag) {
+			VectorSubtract(ent->r.currentOrigin,flag->r.currentOrigin , v1);
+			if(VectorLength(v1) < 500)
+				nearFlag = qtrue;
+		}
+	}
 
 	ent->think = ProximityMine_Explode;
-	ent->nextthink = level.time + g_proxMineTimeout.integer;
+	if( nearFlag)
+		ent->nextthink = level.time + g_proxMineTimeout.integer/15;
+	else
+		ent->nextthink = level.time + g_proxMineTimeout.integer;
 
 	ent->takedamage = qtrue;
 	ent->health = 1;
@@ -206,7 +258,8 @@
 ProximityMine_ExplodeOnPlayer
 ================
 */
-static void ProximityMine_ExplodeOnPlayer( gentity_t *mine ) {
+static void ProximityMine_ExplodeOnPlayer( gentity_t *mine )
+{
 	gentity_t	*player;
 
 	player = mine->enemy;
@@ -231,7 +284,8 @@
 ProximityMine_Player
 ================
 */
-static void ProximityMine_Player( gentity_t *mine, gentity_t *player ) {
+static void ProximityMine_Player( gentity_t *mine, gentity_t *player )
+{
 	if( mine->s.eFlags & EF_NODRAW ) {
 		return;
 	}
@@ -263,34 +317,50 @@
 		mine->nextthink = level.time + 10 * 1000;
 	}
 }
-#endif
+
+/*
+ *=================
+ *ProximityMine_RemoveAll
+ *=================
+ */
+
+void ProximityMine_RemoveAll()
+{
+	gentity_t	*mine;
+
+	mine = NULL;
+
+	while ((mine = G_Find (mine, FOFS(classname), "prox mine")) != NULL) {
+		mine->think = ProximityMine_Explode;
+		mine->nextthink = level.time + 1;
+	}
+}
 
 /*
 ================
 G_MissileImpact
 ================
 */
-void G_MissileImpact( gentity_t *ent, trace_t *trace ) {
+void G_MissileImpact( gentity_t *ent, trace_t *trace )
+{
 	gentity_t		*other;
 	qboolean		hitClient = qfalse;
-#if 1  //def MPACK
 	vec3_t			forward, impactpoint, bouncedir;
 	int				eFlags;
-#endif
 	other = &g_entities[trace->entityNum];
 
 	// check for bounce
 	if ( !other->takedamage &&
-		( ent->s.eFlags & ( EF_BOUNCE | EF_BOUNCE_HALF ) ) ) {
+	        ( ent->s.eFlags & ( EF_BOUNCE | EF_BOUNCE_HALF ) ) ) {
 		G_BounceMissile( ent, trace );
 		G_AddEvent( ent, EV_GRENADE_BOUNCE, 0 );
 		return;
 	}
 
-#if 1  //def MPACK
 	if ( other->takedamage ) {
 		if ( ent->s.weapon != WP_PROX_LAUNCHER ) {
 			if ( other->client && other->client->invulnerabilityTime > level.time ) {
+
 				//
 				VectorCopy( ent->s.pos.trDelta, forward );
 				VectorNormalize( forward );
@@ -306,7 +376,6 @@
 			}
 		}
 	}
-#endif
 	// impact damage
 	if (other->takedamage) {
 		// FIXME: wrong damage direction?
@@ -316,18 +385,18 @@
 			if( LogAccuracyHit( other, &g_entities[ent->r.ownerNum] ) ) {
 				g_entities[ent->r.ownerNum].client->accuracy_hits++;
 				hitClient = qtrue;
+				g_entities[ent->r.ownerNum].client->accuracy[ent->s.weapon][1]++;
 			}
 			BG_EvaluateTrajectoryDelta( &ent->s.pos, level.time, velocity );
 			if ( VectorLength( velocity ) == 0 ) {
 				velocity[2] = 1;	// stepped on a grenade
 			}
 			G_Damage (other, ent, &g_entities[ent->r.ownerNum], velocity,
-				ent->s.origin, ent->damage, 
-				0, ent->methodOfDeath);
+			          ent->s.origin, ent->damage,
+			          0, ent->methodOfDeath);
 		}
 	}
 
-#if 1  //def MPACK
 	if( ent->s.weapon == WP_PROX_LAUNCHER ) {
 		if( ent->s.pos.trType != TR_GRAVITY ) {
 			return;
@@ -362,9 +431,8 @@
 
 		return;
 	}
-#endif
 
-	if (!strcmp(ent->classname, "hook")) {
+	if (strequals(ent->classname, "hook")) {
 		gentity_t *nent;
 		vec3_t v;
 
@@ -381,7 +449,8 @@
 			v[2] = other->r.currentOrigin[2] + (other->r.mins[2] + other->r.maxs[2]) * 0.5;
 
 			SnapVectorTowards( v, ent->s.pos.trBase );	// save net bandwidth
-		} else {
+		}
+		else {
 			VectorCopy(trace->endpos, v);
 			G_AddEvent( nent, EV_MISSILE_MISS, DirToByte( trace->plane.normal ) );
 			ent->enemy = NULL;
@@ -415,9 +484,11 @@
 	if ( other->takedamage && other->client ) {
 		G_AddEvent( ent, EV_MISSILE_HIT, DirToByte( trace->plane.normal ) );
 		ent->s.otherEntityNum = other->s.number;
-	} else if( trace->surfaceFlags & SURF_METALSTEPS ) {
+	}
+	else if( trace->surfaceFlags & SURF_METALSTEPS ) {
 		G_AddEvent( ent, EV_MISSILE_MISS_METAL, DirToByte( trace->plane.normal ) );
-	} else {
+	}
+	else {
 		G_AddEvent( ent, EV_MISSILE_MISS, DirToByte( trace->plane.normal ) );
 	}
 
@@ -432,10 +503,11 @@
 
 	// splash damage (doesn't apply to person directly hit)
 	if ( ent->splashDamage ) {
-		if( G_RadiusDamage( trace->endpos, ent->parent, ent->splashDamage, ent->splashRadius, 
-			other, ent->splashMethodOfDeath ) ) {
+		if( G_RadiusDamage( trace->endpos, ent->parent, ent->splashDamage, ent->splashRadius,
+		                    other, ent->splashMethodOfDeath ) ) {
 			if( !hitClient ) {
 				g_entities[ent->r.ownerNum].client->accuracy_hits++;
+				g_entities[ent->r.ownerNum].client->accuracy[ent->s.weapon][1]++;
 			}
 		}
 	}
@@ -448,7 +520,8 @@
 G_RunMissile
 ================
 */
-void G_RunMissile( gentity_t *ent ) {
+void G_RunMissile( gentity_t *ent )
+{
 	vec3_t		origin;
 	trace_t		tr;
 	int			passent;
@@ -460,12 +533,10 @@
 	if ( ent->target_ent ) {
 		passent = ent->target_ent->s.number;
 	}
-#if 1  //def MPACK
 	// prox mines that left the owner bbox will attach to anything, even the owner
 	else if (ent->s.weapon == WP_PROX_LAUNCHER && ent->count) {
 		passent = ENTITYNUM_NONE;
 	}
-#endif
 	else {
 		// ignore interactions with the missile owner
 		passent = ent->r.ownerNum;
@@ -499,7 +570,6 @@
 			return;		// exploded
 		}
 	}
-#if 1  //def MPACK
 	// if the prox mine wasn't yet outside the player body
 	if (ent->s.weapon == WP_PROX_LAUNCHER && !ent->count) {
 		// check if the prox mine is outside the owner bbox
@@ -508,7 +578,6 @@
 			ent->count = 1;
 		}
 	}
-#endif
 	// check think function after bouncing
 	G_RunThink( ent );
 }
@@ -522,7 +591,8 @@
 
 =================
 */
-gentity_t *fire_plasma (gentity_t *self, vec3_t start, vec3_t dir) {
+gentity_t *fire_plasma (gentity_t *self, vec3_t start, vec3_t dir)
+{
 	gentity_t	*bolt;
 
 	VectorNormalize (dir);
@@ -535,7 +605,10 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_PLASMAGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->splashDamage = 15;
@@ -548,14 +621,13 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	//VectorScale( dir, 2000, bolt->s.pos.trDelta );
-	VectorScale(dir, g_weapon_plasma_speed.integer, bolt->s.pos.trDelta);
+	VectorScale( dir, 2000, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 
 	VectorCopy (start, bolt->r.currentOrigin);
 
 	return bolt;
-}	
+}
 
 //=============================================================================
 
@@ -565,7 +637,8 @@
 fire_grenade
 =================
 */
-gentity_t *fire_grenade (gentity_t *self, vec3_t start, vec3_t dir) {
+gentity_t *fire_grenade (gentity_t *self, vec3_t start, vec3_t dir)
+{
 	gentity_t	*bolt;
 
 	VectorNormalize (dir);
@@ -579,8 +652,10 @@
 	bolt->s.weapon = WP_GRENADE_LAUNCHER;
 	bolt->s.eFlags = EF_BOUNCE_HALF;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
-	bolt->s.clientNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -609,7 +684,8 @@
 fire_bfg
 =================
 */
-gentity_t *fire_bfg (gentity_t *self, vec3_t start, vec3_t dir) {
+gentity_t *fire_bfg (gentity_t *self, vec3_t start, vec3_t dir)
+{
 	gentity_t	*bolt;
 
 	VectorNormalize (dir);
@@ -622,7 +698,10 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_BFG;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -650,7 +729,8 @@
 fire_rocket
 =================
 */
-gentity_t *fire_rocket (gentity_t *self, vec3_t start, vec3_t dir) {
+gentity_t *fire_rocket (gentity_t *self, vec3_t start, vec3_t dir)
+{
 	gentity_t	*bolt;
 
 	VectorNormalize (dir);
@@ -663,7 +743,10 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_ROCKET_LAUNCHER;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 100;
 	bolt->splashDamage = 100;
@@ -676,7 +759,7 @@
 	bolt->s.pos.trType = TR_LINEAR;
 	bolt->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
 	VectorCopy( start, bolt->s.pos.trBase );
-	VectorScale( dir, g_weapon_rocket_speed.integer, bolt->s.pos.trDelta );
+	VectorScale( dir, 900, bolt->s.pos.trDelta );
 	SnapVector( bolt->s.pos.trDelta );			// save net bandwidth
 	VectorCopy (start, bolt->r.currentOrigin);
 
@@ -688,8 +771,12 @@
 fire_grapple
 =================
 */
-gentity_t *fire_grapple (gentity_t *self, vec3_t start, vec3_t dir) {
+gentity_t *fire_grapple (gentity_t *self, vec3_t start, vec3_t dir)
+{
 	gentity_t	*hook;
+//unlagged - grapple
+	int hooktime;
+//unlagged - grapple
 
 	VectorNormalize (dir);
 
@@ -706,21 +793,39 @@
 	hook->parent = self;
 	hook->target_ent = NULL;
 
+//unlagged - grapple
+	// we might want this later
+	hook->s.otherEntityNum = self->s.number;
+
+	// setting the projectile base time back makes the hook's first
+	// step larger
+
+	if ( self->client ) {
+		hooktime = self->client->pers.cmd.serverTime + 50;
+	}
+	else {
+		hooktime = level.time - MISSILE_PRESTEP_TIME;
+	}
+
+	hook->s.pos.trTime = hooktime;
+//unlagged - grapple
+
 	hook->s.pos.trType = TR_LINEAR;
-	hook->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
+//unlagged - grapple
+	//hook->s.pos.trTime = level.time - MISSILE_PRESTEP_TIME;		// move a bit on the very first frame
+//unlagged - grapple
 	hook->s.otherEntityNum = self->s.number; // use to match beam in client
 	VectorCopy( start, hook->s.pos.trBase );
 	VectorScale( dir, 800, hook->s.pos.trDelta );
 	SnapVector( hook->s.pos.trDelta );			// save net bandwidth
 	VectorCopy (start, hook->r.currentOrigin);
 
-	self->client->hook = hook;
+	if(self->client)
+		self->client->hook = hook;
 
 	return hook;
 }
 
-
-#if 1  //def MPACK
 /*
 =================
 fire_nail
@@ -728,7 +833,8 @@
 */
 #define NAILGUN_SPREAD	500
 
-gentity_t *fire_nail( gentity_t *self, vec3_t start, vec3_t forward, vec3_t right, vec3_t up ) {
+gentity_t *fire_nail( gentity_t *self, vec3_t start, vec3_t forward, vec3_t right, vec3_t up )
+{
 	gentity_t	*bolt;
 	vec3_t		dir;
 	vec3_t		end;
@@ -742,7 +848,10 @@
 	bolt->r.svFlags = SVF_USE_CURRENT_ORIGIN;
 	bolt->s.weapon = WP_NAILGUN;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 20;
 	bolt->methodOfDeath = MOD_NAIL;
@@ -769,7 +878,7 @@
 	VectorCopy( start, bolt->r.currentOrigin );
 
 	return bolt;
-}	
+}
 
 
 /*
@@ -777,7 +886,8 @@
 fire_prox
 =================
 */
-gentity_t *fire_prox( gentity_t *self, vec3_t start, vec3_t dir ) {
+gentity_t *fire_prox( gentity_t *self, vec3_t start, vec3_t dir )
+{
 	gentity_t	*bolt;
 
 	VectorNormalize (dir);
@@ -791,7 +901,10 @@
 	bolt->s.weapon = WP_PROX_LAUNCHER;
 	bolt->s.eFlags = 0;
 	bolt->r.ownerNum = self->s.number;
-	bolt->s.otherEntityNum = self->s.number;  // 2019-03-07 quake live adds owner
+//unlagged - projectile nudge
+	// we'll need this for nudging projectiles later
+	bolt->s.otherEntityNum = self->s.number;
+//unlagged - projectile nudge
 	bolt->parent = self;
 	bolt->damage = 0;
 	bolt->splashDamage = 100;
@@ -817,4 +930,3 @@
 
 	return bolt;
 }
-#endif

```
