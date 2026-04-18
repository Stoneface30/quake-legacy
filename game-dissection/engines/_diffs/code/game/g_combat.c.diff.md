# Diff: `code/game/g_combat.c`
**Canonical:** `wolfcamql-src` (sha256 `c4a69ecda245...`, 32159 bytes)

## Variants

### `quake3-source`  — sha256 `a19a66ecaf1d...`, 30930 bytes

_Diff stat: +81 / -140 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_combat.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_combat.c	2026-04-16 20:02:19.905577500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -126,7 +126,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 =================
@@ -157,10 +157,6 @@
 		item = BG_FindItem( "Blue Cube" );
 	}
 
-	if (!item) {
-		return;
-	}
-
 	angles[YAW] = (float)(level.time % 360);
 	angles[PITCH] = 0;	// always forward
 	angles[ROLL] = 0;
@@ -182,7 +178,7 @@
 	drop->think = G_FreeEntity;
 	drop->spawnflags = self->client->sess.sessionTeam;
 }
-#endif
+
 
 /*
 =================
@@ -210,19 +206,17 @@
 	ent->client->ps.stats[STAT_PERSISTANT_POWERUP] = 0;
 	ent->client->persistantPowerup = NULL;
 }
+#endif
 
 
-
-// not in quakelive
-
 /*
 ==================
 LookAtKiller
 ==================
 */
 void LookAtKiller( gentity_t *self, gentity_t *inflictor, gentity_t *attacker ) {
-#if 0  // not in quakelive
 	vec3_t		dir;
+	vec3_t		angles;
 
 	if ( attacker && attacker != self ) {
 		VectorSubtract (attacker->s.pos.trBase, self->s.pos.trBase, dir);
@@ -234,7 +228,10 @@
 	}
 
 	self->client->ps.stats[STAT_DEAD_YAW] = vectoyaw ( dir );
-#endif
+
+	angles[YAW] = vectoyaw ( dir );
+	angles[PITCH] = 0; 
+	angles[ROLL] = 0;
 }
 
 /*
@@ -249,7 +246,7 @@
 	//if this entity still has kamikaze
 	if (self->s.eFlags & EF_KAMIKAZE) {
 		// check if there is a kamikaze timer around for this owner
-		for (i = 0; i < level.num_entities; i++) {
+		for (i = 0; i < MAX_GENTITIES; i++) {
 			ent = &g_entities[i];
 			if (!ent->inuse)
 				continue;
@@ -286,51 +283,41 @@
 
 
 // these are just for logging, the client prints its own messages
-static char *modNames[] = {
+char	*modNames[] = {
 	"MOD_UNKNOWN",
 	"MOD_SHOTGUN",
 	"MOD_GAUNTLET",
 	"MOD_MACHINEGUN",
 	"MOD_GRENADE",
-
-	"MOD_GRENADE_SPLASH",  // 5
+	"MOD_GRENADE_SPLASH",
 	"MOD_ROCKET",
 	"MOD_ROCKET_SPLASH",
 	"MOD_PLASMA",
 	"MOD_PLASMA_SPLASH",
-
-	"MOD_RAILGUN",  // 10
+	"MOD_RAILGUN",
 	"MOD_LIGHTNING",
 	"MOD_BFG",
 	"MOD_BFG_SPLASH",
 	"MOD_WATER",
-
-	"MOD_SLIME",  // 15
+	"MOD_SLIME",
 	"MOD_LAVA",
 	"MOD_CRUSH",
 	"MOD_TELEFRAG",
 	"MOD_FALLING",
-
-	"MOD_SUICIDE",  // 20
+	"MOD_SUICIDE",
 	"MOD_TARGET_LASER",
 	"MOD_TRIGGER_HURT",
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	"MOD_NAIL",
 	"MOD_CHAINGUN",
-
-	"MOD_PROXIMITY_MINE",  // 25
+	"MOD_PROXIMITY_MINE",
 	"MOD_KAMIKAZE",
 	"MOD_JUICED",
 #endif
-	"MOD_GRAPPLE",
-	"MOD_SWITCH_TEAMS",  // 29
-
-	"MOD_THAW",  // 30
-	"MOD_UNKNOWN31",
-	"MOD_HMG",  // 32
+	"MOD_GRAPPLE"
 };
 
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 Kamikaze_DeathActivate
@@ -473,7 +460,7 @@
 	if (self->client && self->client->hook) {
 		Weapon_HookFree(self->client->hook);
 	}
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if ((self->client->ps.eFlags & EF_TICKING) && self->activator) {
 		self->client->ps.eFlags &= ~EF_TICKING;
 		self->activator->think = G_FreeEntity;
@@ -499,10 +486,10 @@
 		killerName = "<world>";
 	}
 
-	if ( meansOfDeath < 0 || meansOfDeath >= ARRAY_LEN( modNames ) ) {
+	if ( meansOfDeath < 0 || meansOfDeath >= sizeof( modNames ) / sizeof( modNames[0] ) ) {
 		obit = "<bad obituary>";
 	} else {
-		obit = modNames[meansOfDeath];
+		obit = modNames[ meansOfDeath ];
 	}
 
 	G_LogPrintf("Kill: %i %i %i: %s killed %s by %s\n", 
@@ -579,9 +566,23 @@
 		}
 	}
 
-	TossClientItems( self );
-
-#if 1  //def MPACK
+	// if client is in a nodrop area, don't drop anything (but return CTF flags!)
+	contents = trap_PointContents( self->r.currentOrigin, -1 );
+	if ( !( contents & CONTENTS_NODROP )) {
+		TossClientItems( self );
+	}
+	else {
+		if ( self->client->ps.powerups[PW_NEUTRALFLAG] ) {		// only happens in One Flag CTF
+			Team_ReturnFlag( TEAM_FREE );
+		}
+		else if ( self->client->ps.powerups[PW_REDFLAG] ) {		// only happens in standard CTF
+			Team_ReturnFlag( TEAM_RED );
+		}
+		else if ( self->client->ps.powerups[PW_BLUEFLAG] ) {	// only happens in standard CTF
+			Team_ReturnFlag( TEAM_BLUE );
+		}
+	}
+#ifdef MISSIONPACK
 	TossClientPersistantPowerups( self );
 	if( g_gametype.integer == GT_HARVESTER ) {
 		TossClientCubes( self );
@@ -614,13 +615,13 @@
 
 	self->s.angles[0] = 0;
 	self->s.angles[2] = 0;
-	//LookAtKiller (self, inflictor, attacker);  // not in quake live
+	LookAtKiller (self, inflictor, attacker);
 
 	VectorCopy( self->s.angles, self->client->ps.viewangles );
 
 	self->s.loopSound = 0;
 
-	self->r.maxs[2] = DEAD_HEIGHT;
+	self->r.maxs[2] = -8;
 
 	// don't allow respawn until the death anim is done
 	// g_forcerespawn may force spawning at some later time
@@ -630,16 +631,14 @@
 	memset( self->client->ps.powerups, 0, sizeof(self->client->ps.powerups) );
 
 	// never gib in a nodrop
-	contents = trap_PointContents( self->r.currentOrigin, -1 );
-
 	if ( (self->health <= GIB_HEALTH && !(contents & CONTENTS_NODROP) && g_blood.integer) || meansOfDeath == MOD_SUICIDE) {
 		// gib death
 		GibEntity( self, killer );
 	} else {
 		// normal death
-		static int lastDeath;
+		static int i;
 
-		switch ( lastDeath ) {
+		switch ( i ) {
 		case 0:
 			anim = BOTH_DEATH1;
 			break;
@@ -663,15 +662,15 @@
 		self->client->ps.torsoAnim = 
 			( ( self->client->ps.torsoAnim & ANIM_TOGGLEBIT ) ^ ANIM_TOGGLEBIT ) | anim;
 
-		G_AddEvent( self, EV_DEATH1 + lastDeath, killer );
+		G_AddEvent( self, EV_DEATH1 + i, killer );
 
 		// the body can still be gibbed
 		self->die = body_die;
 
 		// globally cycle through the different death animations
-		lastDeath = ( lastDeath + 1 ) % 3;
+		i = ( i + 1 ) % 3;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (self->s.eFlags & EF_KAMIKAZE) {
 			Kamikaze_DeathTimer( self );
 		}
@@ -756,7 +755,7 @@
 	return 0;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 G_InvulnerabilityEffect
@@ -772,7 +771,8 @@
 	}
 	VectorCopy(dir, vec);
 	VectorInverse(vec);
-	n = RaySphereIntersections( targ->client->ps.origin, INVUL_RADIUS, point, vec, intersections);
+	// sphere model radius = 42 units
+	n = RaySphereIntersections( targ->client->ps.origin, 42, point, vec, intersections);
 	if (n > 0) {
 		impact = G_TempEntity( targ->client->ps.origin, EV_INVUL_IMPACT );
 		VectorSubtract(intersections[0], targ->client->ps.origin, vec);
@@ -796,7 +796,7 @@
 #endif
 /*
 ============
-G_Damage
+T_Damage
 
 targ		entity that is being damaged
 inflictor	entity that is causing the damage
@@ -822,10 +822,11 @@
 			   vec3_t dir, vec3_t point, int damage, int dflags, int mod ) {
 	gclient_t	*client;
 	int			take;
+	int			save;
 	int			asave;
 	int			knockback;
 	int			max;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		bouncedir, impactpoint;
 #endif
 
@@ -833,12 +834,12 @@
 		return;
 	}
 
-	// the intermission has already been qualified for, so don't
+	// the intermission has allready been qualified for, so don't
 	// allow any extra scoring
 	if ( level.intermissionQueued ) {
 		return;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( targ->client && mod != MOD_JUICED) {
 		if ( targ->client->invulnerabilityTime > level.time) {
 			if ( dir && point ) {
@@ -871,7 +872,7 @@
 	// unless they are rocket jumping
 	if ( attacker->client && attacker != targ ) {
 		max = attacker->client->ps.stats[STAT_MAX_HEALTH];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( bg_itemlist[attacker->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 			max /= 2;
 		}
@@ -936,16 +937,16 @@
 
 		// if TF_NO_FRIENDLY_FIRE is set, don't do damage to the target
 		// if the attacker was on the same team
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( mod != MOD_JUICED && targ != attacker && !(dflags & DAMAGE_NO_TEAM_PROTECTION) && OnSameTeam (targ, attacker)  ) {
-#else
+#else	
 		if ( targ != attacker && OnSameTeam (targ, attacker)  ) {
 #endif
 			if ( !g_friendlyFire.integer ) {
 				return;
 			}
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (mod == MOD_PROXIMITY_MINE) {
 			if (inflictor && inflictor->parent && OnSameTeam(targ, inflictor->parent)) {
 				return;
@@ -973,8 +974,7 @@
 	}
 
 	// add to the attacker's hit counter (if the target isn't a general entity like a prox mine)
-	if ( attacker->client && client
-			&& targ != attacker && targ->health > 0
+	if ( attacker->client && targ != attacker && targ->health > 0
 			&& targ->s.eType != ET_MISSILE
 			&& targ->s.eType != ET_GENERAL) {
 		if ( OnSameTeam( targ, attacker ) ) {
@@ -995,6 +995,7 @@
 		damage = 1;
 	}
 	take = damage;
+	save = 0;
 
 	// save some from armor
 	asave = CheckArmor (targ, take, dflags);
@@ -1029,7 +1030,7 @@
 	// See if it's the player hurting the emeny flag carrier
 #ifdef MISSIONPACK
 	if( g_gametype.integer == GT_CTF || g_gametype.integer == GT_1FCTF ) {
-#else
+#else	
 	if( g_gametype.integer == GT_CTF) {
 #endif
 		Team_CheckHurtCarrier(targ, attacker);
@@ -1041,27 +1042,13 @@
 		targ->client->lasthurt_mod = mod;
 	}
 
-	if (take) {
-		gentity_t *tent;
-
-		// EV_DAMAGEPLUM
-		if (targ->client  &&  attacker->client) {
-			tent = G_TempEntity(targ->r.currentOrigin, EV_DAMAGEPLUM);
-			tent->s.clientNum = attacker->s.number;
-			tent->s.generic1 = BG_ModToWeapon(mod);
-			tent->s.time = take;
-
-			//G_Printf("^2 damage plum %d\n", tent->s.clientNum);
-		}
-	}
-
 	// do the damage
 	if (take) {
 		targ->health = targ->health - take;
 		if ( targ->client ) {
 			targ->client->ps.stats[STAT_HEALTH] = targ->health;
 		}
-
+			
 		if ( targ->health <= 0 ) {
 			if ( client )
 				targ->flags |= FL_NO_KNOCKBACK;
@@ -1092,93 +1079,47 @@
 	vec3_t	dest;
 	trace_t	tr;
 	vec3_t	midpoint;
-	vec3_t	offsetmins = {-15, -15, -15};
-	vec3_t	offsetmaxs = {15, 15, 15};
 
 	// use the midpoint of the bounds instead of the origin, because
 	// bmodels may have their origin is 0,0,0
 	VectorAdd (targ->r.absmin, targ->r.absmax, midpoint);
 	VectorScale (midpoint, 0.5, midpoint);
 
-	VectorCopy(midpoint, dest);
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
+	VectorCopy (midpoint, dest);
+	trap_Trace ( &tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 	if (tr.fraction == 1.0 || tr.entityNum == targ->s.number)
 		return qtrue;
 
 	// this should probably check in the plane of projection, 
-	// rather than in world coordinate
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmaxs[0];
-	dest[1] += offsetmaxs[1];
-	dest[2] += offsetmaxs[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
+	// rather than in world coordinate, and also include Z
+	VectorCopy (midpoint, dest);
+	dest[0] += 15.0;
+	dest[1] += 15.0;
+	trap_Trace ( &tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 	if (tr.fraction == 1.0)
 		return qtrue;
 
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmaxs[0];
-	dest[1] += offsetmins[1];
-	dest[2] += offsetmaxs[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
-	if (tr.fraction == 1.0)
-		return qtrue;
-
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmins[0];
-	dest[1] += offsetmaxs[1];
-	dest[2] += offsetmaxs[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
-	if (tr.fraction == 1.0)
-		return qtrue;
-
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmins[0];
-	dest[1] += offsetmins[1];
-	dest[2] += offsetmaxs[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
+	VectorCopy (midpoint, dest);
+	dest[0] += 15.0;
+	dest[1] -= 15.0;
+	trap_Trace ( &tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 	if (tr.fraction == 1.0)
 		return qtrue;
 
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmaxs[0];
-	dest[1] += offsetmaxs[1];
-	dest[2] += offsetmins[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
+	VectorCopy (midpoint, dest);
+	dest[0] -= 15.0;
+	dest[1] += 15.0;
+	trap_Trace ( &tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 	if (tr.fraction == 1.0)
 		return qtrue;
 
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmaxs[0];
-	dest[1] += offsetmins[1];
-	dest[2] += offsetmins[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
+	VectorCopy (midpoint, dest);
+	dest[0] -= 15.0;
+	dest[1] -= 15.0;
+	trap_Trace ( &tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 	if (tr.fraction == 1.0)
 		return qtrue;
 
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmins[0];
-	dest[1] += offsetmaxs[1];
-	dest[2] += offsetmins[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
-	if (tr.fraction == 1.0)
-		return qtrue;
-
-	VectorCopy(midpoint, dest);
-	dest[0] += offsetmins[0];
-	dest[1] += offsetmins[1];
-	dest[2] += offsetmins[2];
-	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
-
-	if (tr.fraction == 1.0)
-		return qtrue;
 
 	return qfalse;
 }

```

### `ioquake3`  — sha256 `cc1fe46e1662...`, 31554 bytes

_Diff stat: +25 / -58 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_combat.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_combat.c	2026-04-16 20:02:21.543355100 +0100
@@ -126,7 +126,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 =================
@@ -157,10 +157,6 @@
 		item = BG_FindItem( "Blue Cube" );
 	}
 
-	if (!item) {
-		return;
-	}
-
 	angles[YAW] = (float)(level.time % 360);
 	angles[PITCH] = 0;	// always forward
 	angles[ROLL] = 0;
@@ -182,7 +178,7 @@
 	drop->think = G_FreeEntity;
 	drop->spawnflags = self->client->sess.sessionTeam;
 }
-#endif
+
 
 /*
 =================
@@ -210,18 +206,15 @@
 	ent->client->ps.stats[STAT_PERSISTANT_POWERUP] = 0;
 	ent->client->persistantPowerup = NULL;
 }
+#endif
 
 
-
-// not in quakelive
-
 /*
 ==================
 LookAtKiller
 ==================
 */
 void LookAtKiller( gentity_t *self, gentity_t *inflictor, gentity_t *attacker ) {
-#if 0  // not in quakelive
 	vec3_t		dir;
 
 	if ( attacker && attacker != self ) {
@@ -234,7 +227,6 @@
 	}
 
 	self->client->ps.stats[STAT_DEAD_YAW] = vectoyaw ( dir );
-#endif
 }
 
 /*
@@ -286,51 +278,41 @@
 
 
 // these are just for logging, the client prints its own messages
-static char *modNames[] = {
+char	*modNames[] = {
 	"MOD_UNKNOWN",
 	"MOD_SHOTGUN",
 	"MOD_GAUNTLET",
 	"MOD_MACHINEGUN",
 	"MOD_GRENADE",
-
-	"MOD_GRENADE_SPLASH",  // 5
+	"MOD_GRENADE_SPLASH",
 	"MOD_ROCKET",
 	"MOD_ROCKET_SPLASH",
 	"MOD_PLASMA",
 	"MOD_PLASMA_SPLASH",
-
-	"MOD_RAILGUN",  // 10
+	"MOD_RAILGUN",
 	"MOD_LIGHTNING",
 	"MOD_BFG",
 	"MOD_BFG_SPLASH",
 	"MOD_WATER",
-
-	"MOD_SLIME",  // 15
+	"MOD_SLIME",
 	"MOD_LAVA",
 	"MOD_CRUSH",
 	"MOD_TELEFRAG",
 	"MOD_FALLING",
-
-	"MOD_SUICIDE",  // 20
+	"MOD_SUICIDE",
 	"MOD_TARGET_LASER",
 	"MOD_TRIGGER_HURT",
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	"MOD_NAIL",
 	"MOD_CHAINGUN",
-
-	"MOD_PROXIMITY_MINE",  // 25
+	"MOD_PROXIMITY_MINE",
 	"MOD_KAMIKAZE",
 	"MOD_JUICED",
 #endif
-	"MOD_GRAPPLE",
-	"MOD_SWITCH_TEAMS",  // 29
-
-	"MOD_THAW",  // 30
-	"MOD_UNKNOWN31",
-	"MOD_HMG",  // 32
+	"MOD_GRAPPLE"
 };
 
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 Kamikaze_DeathActivate
@@ -473,7 +455,7 @@
 	if (self->client && self->client->hook) {
 		Weapon_HookFree(self->client->hook);
 	}
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if ((self->client->ps.eFlags & EF_TICKING) && self->activator) {
 		self->client->ps.eFlags &= ~EF_TICKING;
 		self->activator->think = G_FreeEntity;
@@ -580,8 +562,7 @@
 	}
 
 	TossClientItems( self );
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	TossClientPersistantPowerups( self );
 	if( g_gametype.integer == GT_HARVESTER ) {
 		TossClientCubes( self );
@@ -614,7 +595,7 @@
 
 	self->s.angles[0] = 0;
 	self->s.angles[2] = 0;
-	//LookAtKiller (self, inflictor, attacker);  // not in quake live
+	LookAtKiller (self, inflictor, attacker);
 
 	VectorCopy( self->s.angles, self->client->ps.viewangles );
 
@@ -671,7 +652,7 @@
 		// globally cycle through the different death animations
 		lastDeath = ( lastDeath + 1 ) % 3;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (self->s.eFlags & EF_KAMIKAZE) {
 			Kamikaze_DeathTimer( self );
 		}
@@ -756,7 +737,7 @@
 	return 0;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 G_InvulnerabilityEffect
@@ -825,7 +806,7 @@
 	int			asave;
 	int			knockback;
 	int			max;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		bouncedir, impactpoint;
 #endif
 
@@ -838,7 +819,7 @@
 	if ( level.intermissionQueued ) {
 		return;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( targ->client && mod != MOD_JUICED) {
 		if ( targ->client->invulnerabilityTime > level.time) {
 			if ( dir && point ) {
@@ -871,7 +852,7 @@
 	// unless they are rocket jumping
 	if ( attacker->client && attacker != targ ) {
 		max = attacker->client->ps.stats[STAT_MAX_HEALTH];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( bg_itemlist[attacker->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 			max /= 2;
 		}
@@ -936,16 +917,16 @@
 
 		// if TF_NO_FRIENDLY_FIRE is set, don't do damage to the target
 		// if the attacker was on the same team
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( mod != MOD_JUICED && targ != attacker && !(dflags & DAMAGE_NO_TEAM_PROTECTION) && OnSameTeam (targ, attacker)  ) {
-#else
+#else	
 		if ( targ != attacker && OnSameTeam (targ, attacker)  ) {
 #endif
 			if ( !g_friendlyFire.integer ) {
 				return;
 			}
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (mod == MOD_PROXIMITY_MINE) {
 			if (inflictor && inflictor->parent && OnSameTeam(targ, inflictor->parent)) {
 				return;
@@ -1029,7 +1010,7 @@
 	// See if it's the player hurting the emeny flag carrier
 #ifdef MISSIONPACK
 	if( g_gametype.integer == GT_CTF || g_gametype.integer == GT_1FCTF ) {
-#else
+#else	
 	if( g_gametype.integer == GT_CTF) {
 #endif
 		Team_CheckHurtCarrier(targ, attacker);
@@ -1041,27 +1022,13 @@
 		targ->client->lasthurt_mod = mod;
 	}
 
-	if (take) {
-		gentity_t *tent;
-
-		// EV_DAMAGEPLUM
-		if (targ->client  &&  attacker->client) {
-			tent = G_TempEntity(targ->r.currentOrigin, EV_DAMAGEPLUM);
-			tent->s.clientNum = attacker->s.number;
-			tent->s.generic1 = BG_ModToWeapon(mod);
-			tent->s.time = take;
-
-			//G_Printf("^2 damage plum %d\n", tent->s.clientNum);
-		}
-	}
-
 	// do the damage
 	if (take) {
 		targ->health = targ->health - take;
 		if ( targ->client ) {
 			targ->client->ps.stats[STAT_HEALTH] = targ->health;
 		}
-
+			
 		if ( targ->health <= 0 ) {
 			if ( client )
 				targ->flags |= FL_NO_KNOCKBACK;

```

### `openarena-engine`  — sha256 `8a8963ad5f80...`, 31532 bytes

_Diff stat: +35 / -67 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_combat.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_combat.c	2026-04-16 22:48:25.746535800 +0100
@@ -126,7 +126,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 =================
@@ -157,10 +157,6 @@
 		item = BG_FindItem( "Blue Cube" );
 	}
 
-	if (!item) {
-		return;
-	}
-
 	angles[YAW] = (float)(level.time % 360);
 	angles[PITCH] = 0;	// always forward
 	angles[ROLL] = 0;
@@ -182,7 +178,7 @@
 	drop->think = G_FreeEntity;
 	drop->spawnflags = self->client->sess.sessionTeam;
 }
-#endif
+
 
 /*
 =================
@@ -210,18 +206,15 @@
 	ent->client->ps.stats[STAT_PERSISTANT_POWERUP] = 0;
 	ent->client->persistantPowerup = NULL;
 }
+#endif
 
 
-
-// not in quakelive
-
 /*
 ==================
 LookAtKiller
 ==================
 */
 void LookAtKiller( gentity_t *self, gentity_t *inflictor, gentity_t *attacker ) {
-#if 0  // not in quakelive
 	vec3_t		dir;
 
 	if ( attacker && attacker != self ) {
@@ -234,7 +227,6 @@
 	}
 
 	self->client->ps.stats[STAT_DEAD_YAW] = vectoyaw ( dir );
-#endif
 }
 
 /*
@@ -286,51 +278,41 @@
 
 
 // these are just for logging, the client prints its own messages
-static char *modNames[] = {
+char	*modNames[] = {
 	"MOD_UNKNOWN",
 	"MOD_SHOTGUN",
 	"MOD_GAUNTLET",
 	"MOD_MACHINEGUN",
 	"MOD_GRENADE",
-
-	"MOD_GRENADE_SPLASH",  // 5
+	"MOD_GRENADE_SPLASH",
 	"MOD_ROCKET",
 	"MOD_ROCKET_SPLASH",
 	"MOD_PLASMA",
 	"MOD_PLASMA_SPLASH",
-
-	"MOD_RAILGUN",  // 10
+	"MOD_RAILGUN",
 	"MOD_LIGHTNING",
 	"MOD_BFG",
 	"MOD_BFG_SPLASH",
 	"MOD_WATER",
-
-	"MOD_SLIME",  // 15
+	"MOD_SLIME",
 	"MOD_LAVA",
 	"MOD_CRUSH",
 	"MOD_TELEFRAG",
 	"MOD_FALLING",
-
-	"MOD_SUICIDE",  // 20
+	"MOD_SUICIDE",
 	"MOD_TARGET_LASER",
 	"MOD_TRIGGER_HURT",
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	"MOD_NAIL",
 	"MOD_CHAINGUN",
-
-	"MOD_PROXIMITY_MINE",  // 25
+	"MOD_PROXIMITY_MINE",
 	"MOD_KAMIKAZE",
 	"MOD_JUICED",
 #endif
-	"MOD_GRAPPLE",
-	"MOD_SWITCH_TEAMS",  // 29
-
-	"MOD_THAW",  // 30
-	"MOD_UNKNOWN31",
-	"MOD_HMG",  // 32
+	"MOD_GRAPPLE"
 };
 
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==================
 Kamikaze_DeathActivate
@@ -473,7 +455,7 @@
 	if (self->client && self->client->hook) {
 		Weapon_HookFree(self->client->hook);
 	}
-#if  1  //def MPACK
+#ifdef MISSIONPACK
 	if ((self->client->ps.eFlags & EF_TICKING) && self->activator) {
 		self->client->ps.eFlags &= ~EF_TICKING;
 		self->activator->think = G_FreeEntity;
@@ -580,8 +562,7 @@
 	}
 
 	TossClientItems( self );
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	TossClientPersistantPowerups( self );
 	if( g_gametype.integer == GT_HARVESTER ) {
 		TossClientCubes( self );
@@ -614,13 +595,13 @@
 
 	self->s.angles[0] = 0;
 	self->s.angles[2] = 0;
-	//LookAtKiller (self, inflictor, attacker);  // not in quake live
+	LookAtKiller (self, inflictor, attacker);
 
 	VectorCopy( self->s.angles, self->client->ps.viewangles );
 
 	self->s.loopSound = 0;
 
-	self->r.maxs[2] = DEAD_HEIGHT;
+	self->r.maxs[2] = -8;
 
 	// don't allow respawn until the death anim is done
 	// g_forcerespawn may force spawning at some later time
@@ -637,9 +618,9 @@
 		GibEntity( self, killer );
 	} else {
 		// normal death
-		static int lastDeath;
+		static int i;
 
-		switch ( lastDeath ) {
+		switch ( i ) {
 		case 0:
 			anim = BOTH_DEATH1;
 			break;
@@ -663,15 +644,15 @@
 		self->client->ps.torsoAnim = 
 			( ( self->client->ps.torsoAnim & ANIM_TOGGLEBIT ) ^ ANIM_TOGGLEBIT ) | anim;
 
-		G_AddEvent( self, EV_DEATH1 + lastDeath, killer );
+		G_AddEvent( self, EV_DEATH1 + i, killer );
 
 		// the body can still be gibbed
 		self->die = body_die;
 
 		// globally cycle through the different death animations
-		lastDeath = ( lastDeath + 1 ) % 3;
+		i = ( i + 1 ) % 3;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (self->s.eFlags & EF_KAMIKAZE) {
 			Kamikaze_DeathTimer( self );
 		}
@@ -756,7 +737,7 @@
 	return 0;
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ================
 G_InvulnerabilityEffect
@@ -772,7 +753,8 @@
 	}
 	VectorCopy(dir, vec);
 	VectorInverse(vec);
-	n = RaySphereIntersections( targ->client->ps.origin, INVUL_RADIUS, point, vec, intersections);
+	// sphere model radius = 42 units
+	n = RaySphereIntersections( targ->client->ps.origin, 42, point, vec, intersections);
 	if (n > 0) {
 		impact = G_TempEntity( targ->client->ps.origin, EV_INVUL_IMPACT );
 		VectorSubtract(intersections[0], targ->client->ps.origin, vec);
@@ -796,7 +778,7 @@
 #endif
 /*
 ============
-G_Damage
+T_Damage
 
 targ		entity that is being damaged
 inflictor	entity that is causing the damage
@@ -825,7 +807,7 @@
 	int			asave;
 	int			knockback;
 	int			max;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		bouncedir, impactpoint;
 #endif
 
@@ -833,12 +815,12 @@
 		return;
 	}
 
-	// the intermission has already been qualified for, so don't
+	// the intermission has allready been qualified for, so don't
 	// allow any extra scoring
 	if ( level.intermissionQueued ) {
 		return;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( targ->client && mod != MOD_JUICED) {
 		if ( targ->client->invulnerabilityTime > level.time) {
 			if ( dir && point ) {
@@ -871,7 +853,7 @@
 	// unless they are rocket jumping
 	if ( attacker->client && attacker != targ ) {
 		max = attacker->client->ps.stats[STAT_MAX_HEALTH];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( bg_itemlist[attacker->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 			max /= 2;
 		}
@@ -936,16 +918,16 @@
 
 		// if TF_NO_FRIENDLY_FIRE is set, don't do damage to the target
 		// if the attacker was on the same team
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if ( mod != MOD_JUICED && targ != attacker && !(dflags & DAMAGE_NO_TEAM_PROTECTION) && OnSameTeam (targ, attacker)  ) {
-#else
+#else	
 		if ( targ != attacker && OnSameTeam (targ, attacker)  ) {
 #endif
 			if ( !g_friendlyFire.integer ) {
 				return;
 			}
 		}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if (mod == MOD_PROXIMITY_MINE) {
 			if (inflictor && inflictor->parent && OnSameTeam(targ, inflictor->parent)) {
 				return;
@@ -1029,7 +1011,7 @@
 	// See if it's the player hurting the emeny flag carrier
 #ifdef MISSIONPACK
 	if( g_gametype.integer == GT_CTF || g_gametype.integer == GT_1FCTF ) {
-#else
+#else	
 	if( g_gametype.integer == GT_CTF) {
 #endif
 		Team_CheckHurtCarrier(targ, attacker);
@@ -1041,27 +1023,13 @@
 		targ->client->lasthurt_mod = mod;
 	}
 
-	if (take) {
-		gentity_t *tent;
-
-		// EV_DAMAGEPLUM
-		if (targ->client  &&  attacker->client) {
-			tent = G_TempEntity(targ->r.currentOrigin, EV_DAMAGEPLUM);
-			tent->s.clientNum = attacker->s.number;
-			tent->s.generic1 = BG_ModToWeapon(mod);
-			tent->s.time = take;
-
-			//G_Printf("^2 damage plum %d\n", tent->s.clientNum);
-		}
-	}
-
 	// do the damage
 	if (take) {
 		targ->health = targ->health - take;
 		if ( targ->client ) {
 			targ->client->ps.stats[STAT_HEALTH] = targ->health;
 		}
-
+			
 		if ( targ->health <= 0 ) {
 			if ( client )
 				targ->flags |= FL_NO_KNOCKBACK;
@@ -1173,7 +1141,7 @@
 
 	VectorCopy(midpoint, dest);
 	dest[0] += offsetmins[0];
-	dest[1] += offsetmins[1];
+	dest[1] += offsetmins[2];
 	dest[2] += offsetmins[2];
 	trap_Trace(&tr, origin, vec3_origin, vec3_origin, dest, ENTITYNUM_NONE, MASK_SOLID);
 

```

### `openarena-gamecode`  — sha256 `bd12b704e43c...`, 43447 bytes

_Diff stat: +567 / -240 lines_

_(full diff is 39853 bytes — see files directly)_
