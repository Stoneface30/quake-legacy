# Diff: `code/game/g_trigger.c`
**Canonical:** `wolfcamql-src` (sha256 `2568681d7f57...`, 12329 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `09f073e27b76...`, 12328 bytes

_Diff stat: +9 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_trigger.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_trigger.c	2026-04-16 20:02:19.911076800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -84,7 +84,7 @@
 	multi_trigger( self, other );
 }
 
-/*QUAKED trigger_multiple (.5 .5 .5) ? RED_ONLY BLUE_ONLY
+/*QUAKED trigger_multiple (.5 .5 .5) ?
 "wait" : Seconds between triggerings, 0.5 default, -1 = one time only.
 "random"	wait variance, default is 0
 Variable sized repeatable trigger.  Must be targeted at one or more entities.
@@ -336,7 +336,7 @@
 It does dmg points of damage each server frame
 Targeting the trigger will toggle its on / off state.
 
-SILENT			suppresses playing the sound
+SILENT			supresses playing the sound
 SLOW			changes the damage rate to once per second
 NO_PROTECTION	*nothing* stops the damage
 
@@ -390,13 +390,14 @@
 		self->damage = 5;
 	}
 
-	self->use = hurt_use;
+	self->r.contents = CONTENTS_TRIGGER;
 
-	// link in to the world if starting active
-	if ( self->spawnflags & 1 ) {
-		trap_UnlinkEntity (self);
+	if ( self->spawnflags & 2 ) {
+		self->use = hurt_use;
 	}
-	else {
+
+	// link in to the world if starting active
+	if ( ! (self->spawnflags & 1) ) {
 		trap_LinkEntity (self);
 	}
 }

```

### `openarena-engine`  — sha256 `56418e51246f...`, 12309 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_trigger.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_trigger.c	2026-04-16 22:48:25.752047200 +0100
@@ -84,7 +84,7 @@
 	multi_trigger( self, other );
 }
 
-/*QUAKED trigger_multiple (.5 .5 .5) ? RED_ONLY BLUE_ONLY
+/*QUAKED trigger_multiple (.5 .5 .5) ?
 "wait" : Seconds between triggerings, 0.5 default, -1 = one time only.
 "random"	wait variance, default is 0
 Variable sized repeatable trigger.  Must be targeted at one or more entities.
@@ -336,7 +336,7 @@
 It does dmg points of damage each server frame
 Targeting the trigger will toggle its on / off state.
 
-SILENT			suppresses playing the sound
+SILENT			supresses playing the sound
 SLOW			changes the damage rate to once per second
 NO_PROTECTION	*nothing* stops the damage
 

```

### `openarena-gamecode`  — sha256 `9007f9040abb...`, 12475 bytes

_Diff stat: +59 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_trigger.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_trigger.c	2026-04-16 22:48:24.176987600 +0100
@@ -23,7 +23,8 @@
 #include "g_local.h"
 
 
-void InitTrigger( gentity_t *self ) {
+void InitTrigger( gentity_t *self )
+{
 	if (!VectorCompare (self->s.angles, vec3_origin))
 		G_SetMovedir (self->s.angles, self->movedir);
 
@@ -34,7 +35,8 @@
 
 
 // the wait time has passed, so set back up for another activation
-void multi_wait( gentity_t *ent ) {
+void multi_wait( gentity_t *ent )
+{
 	ent->nextthink = 0;
 }
 
@@ -42,7 +44,8 @@
 // the trigger was just activated
 // ent->activator should be set to the activator so it can be held through a delay
 // so wait for the delay time before firing
-void multi_trigger( gentity_t *ent, gentity_t *activator ) {
+void multi_trigger( gentity_t *ent, gentity_t *activator )
+{
 	ent->activator = activator;
 	if ( ent->nextthink ) {
 		return;		// can't retrigger until the wait is over
@@ -64,7 +67,8 @@
 	if ( ent->wait > 0 ) {
 		ent->think = multi_wait;
 		ent->nextthink = level.time + ( ent->wait + ent->random * crandom() ) * 1000;
-	} else {
+	}
+	else {
 		// we can't just remove (self) here, because this is a touch function
 		// called while looping through area links...
 		ent->touch = 0;
@@ -73,11 +77,13 @@
 	}
 }
 
-void Use_Multi( gentity_t *ent, gentity_t *other, gentity_t *activator ) {
+void Use_Multi( gentity_t *ent, gentity_t *other, gentity_t *activator )
+{
 	multi_trigger( ent, activator );
 }
 
-void Touch_Multi( gentity_t *self, gentity_t *other, trace_t *trace ) {
+void Touch_Multi( gentity_t *self, gentity_t *other, trace_t *trace )
+{
 	if( !other->client ) {
 		return;
 	}
@@ -91,7 +97,8 @@
 so, the basic time between firing is a random time between
 (wait - random) and (wait + random)
 */
-void SP_trigger_multiple( gentity_t *ent ) {
+void SP_trigger_multiple( gentity_t *ent )
+{
 	G_SpawnFloat( "wait", "0.5", &ent->wait );
 	G_SpawnFloat( "random", "0", &ent->random );
 
@@ -117,7 +124,8 @@
 ==============================================================================
 */
 
-void trigger_always_think( gentity_t *ent ) {
+void trigger_always_think( gentity_t *ent )
+{
 	G_UseTargets(ent, ent);
 	G_FreeEntity( ent );
 }
@@ -125,7 +133,8 @@
 /*QUAKED trigger_always (.5 .5 .5) (-8 -8 -8) (8 8 8)
 This trigger will always fire.  It is activated by the world.
 */
-void SP_trigger_always (gentity_t *ent) {
+void SP_trigger_always (gentity_t *ent)
+{
 	// we must have some delay to make sure our use targets are present
 	ent->nextthink = level.time + 300;
 	ent->think = trigger_always_think;
@@ -140,7 +149,8 @@
 ==============================================================================
 */
 
-void trigger_push_touch (gentity_t *self, gentity_t *other, trace_t *trace ) {
+void trigger_push_touch (gentity_t *self, gentity_t *other, trace_t *trace )
+{
 
 	if ( !other->client ) {
 		return;
@@ -157,7 +167,8 @@
 Calculate origin2 so the target apogee will be hit
 =================
 */
-void AimAtTarget( gentity_t *self ) {
+void AimAtTarget( gentity_t *self )
+{
 	gentity_t	*ent;
 	vec3_t		origin;
 	float		height, gravity, time, forward;
@@ -173,7 +184,7 @@
 	}
 
 	height = ent->s.origin[2] - origin[2];
-	gravity = g_gravity.value;
+	gravity = g_gravity.value*g_gravityModifier.value;
 	time = sqrt( height / ( .5 * gravity ) );
 	if ( !time ) {
 		G_FreeEntity( self );
@@ -196,7 +207,8 @@
 Must point at a target_position, which will be the apex of the leap.
 This will be client side predicted, unlike target_push
 */
-void SP_trigger_push( gentity_t *self ) {
+void SP_trigger_push( gentity_t *self )
+{
 	InitTrigger (self);
 
 	// unlike other triggers, we need to send this one to the client
@@ -213,7 +225,8 @@
 }
 
 
-void Use_target_push( gentity_t *self, gentity_t *other, gentity_t *activator ) {
+void Use_target_push( gentity_t *self, gentity_t *other, gentity_t *activator )
+{
 	if ( !activator->client ) {
 		return;
 	}
@@ -239,7 +252,8 @@
 "speed"		defaults to 1000
 if "bouncepad", play bounce noise instead of windfly
 */
-void SP_target_push( gentity_t *self ) {
+void SP_target_push( gentity_t *self )
+{
 	if (!self->speed) {
 		self->speed = 1000;
 	}
@@ -248,7 +262,8 @@
 
 	if ( self->spawnflags & 1 ) {
 		self->noise_index = G_SoundIndex("sound/world/jumppad.wav");
-	} else {
+	}
+	else {
 		self->noise_index = G_SoundIndex("sound/misc/windfly.wav");
 	}
 	if ( self->target ) {
@@ -268,18 +283,20 @@
 ==============================================================================
 */
 
-void trigger_teleporter_touch (gentity_t *self, gentity_t *other, trace_t *trace ) {
+void trigger_teleporter_touch (gentity_t *self, gentity_t *other, trace_t *trace )
+{
 	gentity_t	*dest;
 
 	if ( !other->client ) {
 		return;
 	}
+
 	if ( other->client->ps.pm_type == PM_DEAD ) {
 		return;
 	}
 	// Spectators only?
-	if ( ( self->spawnflags & 1 ) && 
-		other->client->sess.sessionTeam != TEAM_SPECTATOR ) {
+	if ( ( self->spawnflags & 1 ) &&
+	        (other->client->sess.sessionTeam != TEAM_SPECTATOR && other->client->ps.pm_type != PM_SPECTATOR) ) {
 		return;
 	}
 
@@ -302,14 +319,16 @@
 Spectator teleporters are not normally placed in the editor, but are created
 automatically near doors to allow spectators to move through them
 */
-void SP_trigger_teleport( gentity_t *self ) {
+void SP_trigger_teleport( gentity_t *self )
+{
 	InitTrigger (self);
 
 	// unlike other triggers, we need to send this one to the client
 	// unless is a spectator trigger
 	if ( self->spawnflags & 1 ) {
 		self->r.svFlags |= SVF_NOCLIENT;
-	} else {
+	}
+	else {
 		self->r.svFlags &= ~SVF_NOCLIENT;
 	}
 
@@ -336,22 +355,25 @@
 It does dmg points of damage each server frame
 Targeting the trigger will toggle its on / off state.
 
-SILENT			suppresses playing the sound
+SILENT			supresses playing the sound
 SLOW			changes the damage rate to once per second
 NO_PROTECTION	*nothing* stops the damage
 
 "dmg"			default 5 (whole numbers only)
 
 */
-void hurt_use( gentity_t *self, gentity_t *other, gentity_t *activator ) {
+void hurt_use( gentity_t *self, gentity_t *other, gentity_t *activator )
+{
 	if ( self->r.linked ) {
 		trap_UnlinkEntity( self );
-	} else {
+	}
+	else {
 		trap_LinkEntity( self );
 	}
 }
 
-void hurt_touch( gentity_t *self, gentity_t *other, trace_t *trace ) {
+void hurt_touch( gentity_t *self, gentity_t *other, trace_t *trace )
+{
 	int		dflags;
 
 	if ( !other->takedamage ) {
@@ -364,7 +386,8 @@
 
 	if ( self->spawnflags & 16 ) {
 		self->timestamp = level.time + 1000;
-	} else {
+	}
+	else {
 		self->timestamp = level.time + FRAMETIME;
 	}
 
@@ -380,7 +403,8 @@
 	G_Damage (other, self, self, NULL, NULL, self->damage, dflags, MOD_TRIGGER_HURT);
 }
 
-void SP_trigger_hurt( gentity_t *self ) {
+void SP_trigger_hurt( gentity_t *self )
+{
 	InitTrigger (self);
 
 	self->noise_index = G_SoundIndex( "sound/world/electro.wav" );
@@ -390,6 +414,8 @@
 		self->damage = 5;
 	}
 
+	self->r.contents = CONTENTS_TRIGGER;
+
 	self->use = hurt_use;
 
 	// link in to the world if starting active
@@ -422,13 +448,15 @@
 (wait - random) and (wait + random)
 
 */
-void func_timer_think( gentity_t *self ) {
+void func_timer_think( gentity_t *self )
+{
 	G_UseTargets (self, self->activator);
 	// set time before next firing
 	self->nextthink = level.time + 1000 * ( self->wait + crandom() * self->random );
 }
 
-void func_timer_use( gentity_t *self, gentity_t *other, gentity_t *activator ) {
+void func_timer_use( gentity_t *self, gentity_t *other, gentity_t *activator )
+{
 	self->activator = activator;
 
 	// if on, turn it off
@@ -441,7 +469,8 @@
 	func_timer_think (self);
 }
 
-void SP_func_timer( gentity_t *self ) {
+void SP_func_timer( gentity_t *self )
+{
 	G_SpawnFloat( "random", "1", &self->random);
 	G_SpawnFloat( "wait", "1", &self->wait );
 
@@ -460,5 +489,3 @@
 
 	self->r.svFlags = SVF_NOCLIENT;
 }
-
-

```
