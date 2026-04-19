# Diff: `code/game/g_weapon.c`
**Canonical:** `wolfcamql-src` (sha256 `35026b0f2c49...`, 30826 bytes)

## Variants

### `quake3-source`  — sha256 `cc12c2c99865...`, 30378 bytes

_Diff stat: +63 / -66 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_weapon.c	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_weapon.c	2026-04-16 20:02:19.912079900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -105,7 +105,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -142,29 +142,24 @@
 
 	for ( i = 0 ; i < 3 ; i++ ) {
 		if ( to[i] <= v[i] ) {
-			v[i] = floor(v[i]);
+			v[i] = (int)v[i];
 		} else {
-			v[i] = ceil(v[i]);
+			v[i] = (int)v[i] + 1;
 		}
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define CHAINGUN_SPREAD		600
-#define CHAINGUN_DAMAGE         7
 #endif
 #define MACHINEGUN_SPREAD	200
 #define	MACHINEGUN_DAMAGE	7
 #define	MACHINEGUN_TEAM_DAMAGE	5		// wimpier MG in teamplay
 
-#define HEAVY_MACHINEGUN_SPREAD 200  //FIXME assuming same as mg
-#define HEAVY_MACHINEGUN_DAMAGE 8
-
-
-void Bullet_Fire (gentity_t *ent, float spread, int damage, int mod) {
+void Bullet_Fire (gentity_t *ent, float spread, int damage ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	float		r;
@@ -209,7 +204,7 @@
 		tent->s.otherEntityNum = ent->s.number;
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -226,8 +221,8 @@
 			else {
 #endif
 				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
-					damage, 0, mod);
-#if 1  //def MPACK
+					damage, 0, MOD_MACHINEGUN);
+#ifdef MISSIONPACK
 			}
 #endif
 		}
@@ -271,11 +266,10 @@
 	trace_t		tr;
 	int			damage, i, passent;
 	gentity_t	*traceEnt;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	vec3_t		tr_start, tr_end;
-	qboolean	hitClient = qfalse;
 
 	passent = ent->s.number;
 	VectorCopy( start, tr_start );
@@ -291,7 +285,7 @@
 
 		if ( traceEnt->takedamage) {
 			damage = DEFAULT_SHOTGUN_DAMAGE * s_quadFactor;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( tr_start, impactpoint, bouncedir, tr_end );
@@ -305,12 +299,19 @@
 				}
 				continue;
 			}
-#endif
-			if( LogAccuracyHit( traceEnt, ent ) ) {
-				hitClient = qtrue;
+			else {
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_SHOTGUN);
+				if( LogAccuracyHit( traceEnt, ent ) ) {
+					return qtrue;
+				}
 			}
-			G_Damage( traceEnt, ent, ent, forward, tr.endpos, damage, 0, MOD_SHOTGUN);
-			return hitClient;
+#else
+			G_Damage( traceEnt, ent, ent, forward, tr.endpos,	damage, 0, MOD_SHOTGUN);
+				if( LogAccuracyHit( traceEnt, ent ) ) {
+					return qtrue;
+				}
+#endif
 		}
 		return qfalse;
 	}
@@ -322,22 +323,25 @@
 	int			i;
 	float		r, u;
 	vec3_t		end;
-	vec3_t		localForward, localRight, localUp;
+	vec3_t		forward, right, up;
+	int			oldScore;
 	qboolean	hitClient = qfalse;
 
 	// derive the right and up vectors from the forward vector, because
 	// the client won't have any other information
-	VectorNormalize2( origin2, localForward );
-	PerpendicularVector( localRight, localForward );
-	CrossProduct( localForward, localRight, localUp );
+	VectorNormalize2( origin2, forward );
+	PerpendicularVector( right, forward );
+	CrossProduct( forward, right, up );
+
+	oldScore = ent->client->ps.persistant[PERS_SCORE];
 
 	// generate the "random" spread pattern
 	for ( i = 0 ; i < DEFAULT_SHOTGUN_COUNT ; i++ ) {
 		r = Q_crandom( &seed ) * DEFAULT_SHOTGUN_SPREAD * 16;
 		u = Q_crandom( &seed ) * DEFAULT_SHOTGUN_SPREAD * 16;
-		VectorMA( origin, 8192 * 16, localForward, end);
-		VectorMA (end, r, localRight, end);
-		VectorMA (end, u, localUp, end);
+		VectorMA( origin, 8192 * 16, forward, end);
+		VectorMA (end, r, right, end);
+		VectorMA (end, u, up, end);
 		if( ShotgunPellet( origin, end, ent ) && !hitClient ) {
 			hitClient = qtrue;
 			ent->client->accuracy_hits++;
@@ -436,7 +440,7 @@
 #define	MAX_RAIL_HITS	4
 void weapon_railgun_fire (gentity_t *ent) {
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	trace_t		trace;
@@ -464,16 +468,7 @@
 		}
 		traceEnt = &g_entities[ trace.entityNum ];
 		if ( traceEnt->takedamage ) {
-			if (traceEnt->client) {
-				gentity_t *stent;
-
-				stent = G_TempEntity(trace.endpos, EV_MISSILE_HIT);
-				stent->s.otherEntityNum = traceEnt->s.number;
-				stent->s.eventParm = DirToByte(trace.plane.normal);
-				stent->s.weapon = WP_RAILGUN;
-				stent->s.clientNum = ent->s.clientNum;
-			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if ( G_InvulnerabilityEffect( traceEnt, forward, trace.endpos, impactpoint, bouncedir ) ) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -617,7 +612,7 @@
 void Weapon_LightningFire( gentity_t *ent ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	gentity_t	*traceEnt, *tent;
@@ -631,7 +626,7 @@
 
 		trap_Trace( &tr, muzzle, NULL, NULL, end, passent, MASK_SHOT );
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if not the first trace (the lightning bounced of an invulnerability sphere)
 		if (i) {
 			// add bounced off lightning bolt temp entity
@@ -650,7 +645,7 @@
 		traceEnt = &g_entities[ tr.entityNum ];
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -666,11 +661,14 @@
 				}
 				continue;
 			}
-#endif
-			if( LogAccuracyHit( traceEnt, ent ) ) {
-				ent->client->accuracy_hits++;
+			else {
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_LIGHTNING);
 			}
-			G_Damage( traceEnt, ent, ent, forward, tr.endpos, damage, 0, MOD_LIGHTNING);
+#else
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_LIGHTNING);
+#endif
 		}
 
 		if ( traceEnt->takedamage && traceEnt->client ) {
@@ -678,6 +676,9 @@
 			tent->s.otherEntityNum = traceEnt->s.number;
 			tent->s.eventParm = DirToByte( tr.plane.normal );
 			tent->s.weapon = ent->s.weapon;
+			if( LogAccuracyHit( traceEnt, ent ) ) {
+				ent->client->accuracy_hits++;
+			}
 		} else if ( !( tr.surfaceFlags & SURF_NOIMPACT ) ) {
 			tent = G_TempEntity( tr.endpos, EV_MISSILE_MISS );
 			tent->s.eventParm = DirToByte( tr.plane.normal );
@@ -687,7 +688,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ======================================================================
 
@@ -778,10 +779,10 @@
 set muzzle location relative to pivoting eye
 ===============
 */
-void CalcMuzzlePoint ( gentity_t *ent, vec3_t localForward, vec3_t localRight, vec3_t localUp, vec3_t muzzlePoint ) {
+void CalcMuzzlePoint ( gentity_t *ent, vec3_t forward, vec3_t right, vec3_t up, vec3_t muzzlePoint ) {
 	VectorCopy( ent->s.pos.trBase, muzzlePoint );
 	muzzlePoint[2] += ent->client->ps.viewheight;
-	VectorMA( muzzlePoint, 14, localForward, muzzlePoint );
+	VectorMA( muzzlePoint, 14, forward, muzzlePoint );
 	// snap to integer coordinates for more efficient network bandwidth usage
 	SnapVector( muzzlePoint );
 }
@@ -793,10 +794,10 @@
 set muzzle location relative to pivoting eye
 ===============
 */
-void CalcMuzzlePointOrigin ( gentity_t *ent, vec3_t origin, vec3_t localForward, vec3_t localRight, vec3_t localUp, vec3_t muzzlePoint ) {
+void CalcMuzzlePointOrigin ( gentity_t *ent, vec3_t origin, vec3_t forward, vec3_t right, vec3_t up, vec3_t muzzlePoint ) {
 	VectorCopy( ent->s.pos.trBase, muzzlePoint );
 	muzzlePoint[2] += ent->client->ps.viewheight;
-	VectorMA( muzzlePoint, 14, localForward, muzzlePoint );
+	VectorMA( muzzlePoint, 14, forward, muzzlePoint );
 	// snap to integer coordinates for more efficient network bandwidth usage
 	SnapVector( muzzlePoint );
 }
@@ -814,7 +815,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -822,7 +823,7 @@
 
 	// track shots taken for accuracy tracking.  Grapple is not a weapon and gauntet is just not tracked
 	if( ent->s.weapon != WP_GRAPPLING_HOOK && ent->s.weapon != WP_GAUNTLET ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( ent->s.weapon == WP_NAILGUN ) {
 			ent->client->accuracy_shots += NUM_NAILSHOTS;
 		} else {
@@ -851,15 +852,11 @@
 		break;
 	case WP_MACHINEGUN:
 		if ( g_gametype.integer != GT_TEAM ) {
-			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_DAMAGE, MOD_MACHINEGUN );
+			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_DAMAGE );
 		} else {
-			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_TEAM_DAMAGE, MOD_MACHINEGUN );
+			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_TEAM_DAMAGE );
 		}
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		//FIXME != team game like machine gun
-		Bullet_Fire(ent, HEAVY_MACHINEGUN_SPREAD, HEAVY_MACHINEGUN_DAMAGE, MOD_HMG);
-		break;
 	case WP_GRENADE_LAUNCHER:
 		weapon_grenadelauncher_fire( ent );
 		break;
@@ -878,7 +875,7 @@
 	case WP_GRAPPLING_HOOK:
 		Weapon_GrapplingHook_Fire( ent );
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		Weapon_Nailgun_Fire( ent );
 		break;
@@ -886,7 +883,7 @@
 		weapon_proxlauncher_fire( ent );
 		break;
 	case WP_CHAINGUN:
-		Bullet_Fire( ent, CHAINGUN_SPREAD, MACHINEGUN_DAMAGE, MOD_CHAINGUN );
+		Bullet_Fire( ent, CHAINGUN_SPREAD, MACHINEGUN_DAMAGE );
 		break;
 #endif
 	default:
@@ -896,7 +893,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ===============
@@ -931,7 +928,7 @@
 			continue;
 		}
 
-		// don't hit things we have already hit
+		// dont hit things we have already hit
 		if( ent->kamikazeTime > level.time ) {
 			continue;
 		}
@@ -991,7 +988,7 @@
 	for ( e = 0 ; e < numListedEntities ; e++ ) {
 		ent = &g_entities[entityList[ e ]];
 
-		// don't hit things we have already hit
+		// dont hit things we have already hit
 		if( ent->kamikazeShockTime > level.time ) {
 			continue;
 		}

```

### `ioquake3`  — sha256 `53fc2bc1dc7d...`, 30306 bytes

_Diff stat: +24 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_weapon.c	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_weapon.c	2026-04-16 20:02:21.550429200 +0100
@@ -85,6 +85,10 @@
 		return qfalse;
 	}
 
+	if ( ent->client->noclip ) {
+		return qfalse;
+	}
+
 	traceEnt = &g_entities[ tr.entityNum ];
 
 	// send blood impact
@@ -105,7 +109,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -149,22 +153,18 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define CHAINGUN_SPREAD		600
-#define CHAINGUN_DAMAGE         7
+#define CHAINGUN_DAMAGE		7
 #endif
 #define MACHINEGUN_SPREAD	200
 #define	MACHINEGUN_DAMAGE	7
 #define	MACHINEGUN_TEAM_DAMAGE	5		// wimpier MG in teamplay
 
-#define HEAVY_MACHINEGUN_SPREAD 200  //FIXME assuming same as mg
-#define HEAVY_MACHINEGUN_DAMAGE 8
-
-
-void Bullet_Fire (gentity_t *ent, float spread, int damage, int mod) {
+void Bullet_Fire (gentity_t *ent, float spread, int damage, int mod ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	float		r;
@@ -209,7 +209,7 @@
 		tent->s.otherEntityNum = ent->s.number;
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -227,7 +227,7 @@
 #endif
 				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
 					damage, 0, mod);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			}
 #endif
 		}
@@ -271,7 +271,7 @@
 	trace_t		tr;
 	int			damage, i, passent;
 	gentity_t	*traceEnt;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	vec3_t		tr_start, tr_end;
@@ -291,7 +291,7 @@
 
 		if ( traceEnt->takedamage) {
 			damage = DEFAULT_SHOTGUN_DAMAGE * s_quadFactor;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( tr_start, impactpoint, bouncedir, tr_end );
@@ -436,7 +436,7 @@
 #define	MAX_RAIL_HITS	4
 void weapon_railgun_fire (gentity_t *ent) {
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	trace_t		trace;
@@ -464,16 +464,7 @@
 		}
 		traceEnt = &g_entities[ trace.entityNum ];
 		if ( traceEnt->takedamage ) {
-			if (traceEnt->client) {
-				gentity_t *stent;
-
-				stent = G_TempEntity(trace.endpos, EV_MISSILE_HIT);
-				stent->s.otherEntityNum = traceEnt->s.number;
-				stent->s.eventParm = DirToByte(trace.plane.normal);
-				stent->s.weapon = WP_RAILGUN;
-				stent->s.clientNum = ent->s.clientNum;
-			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if ( G_InvulnerabilityEffect( traceEnt, forward, trace.endpos, impactpoint, bouncedir ) ) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -617,7 +608,7 @@
 void Weapon_LightningFire( gentity_t *ent ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	gentity_t	*traceEnt, *tent;
@@ -631,7 +622,7 @@
 
 		trap_Trace( &tr, muzzle, NULL, NULL, end, passent, MASK_SHOT );
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if not the first trace (the lightning bounced of an invulnerability sphere)
 		if (i) {
 			// add bounced off lightning bolt temp entity
@@ -650,7 +641,7 @@
 		traceEnt = &g_entities[ tr.entityNum ];
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -687,7 +678,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ======================================================================
 
@@ -814,7 +805,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -822,7 +813,7 @@
 
 	// track shots taken for accuracy tracking.  Grapple is not a weapon and gauntet is just not tracked
 	if( ent->s.weapon != WP_GRAPPLING_HOOK && ent->s.weapon != WP_GAUNTLET ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( ent->s.weapon == WP_NAILGUN ) {
 			ent->client->accuracy_shots += NUM_NAILSHOTS;
 		} else {
@@ -856,10 +847,6 @@
 			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_TEAM_DAMAGE, MOD_MACHINEGUN );
 		}
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		//FIXME != team game like machine gun
-		Bullet_Fire(ent, HEAVY_MACHINEGUN_SPREAD, HEAVY_MACHINEGUN_DAMAGE, MOD_HMG);
-		break;
 	case WP_GRENADE_LAUNCHER:
 		weapon_grenadelauncher_fire( ent );
 		break;
@@ -878,7 +865,7 @@
 	case WP_GRAPPLING_HOOK:
 		Weapon_GrapplingHook_Fire( ent );
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		Weapon_Nailgun_Fire( ent );
 		break;
@@ -886,7 +873,7 @@
 		weapon_proxlauncher_fire( ent );
 		break;
 	case WP_CHAINGUN:
-		Bullet_Fire( ent, CHAINGUN_SPREAD, MACHINEGUN_DAMAGE, MOD_CHAINGUN );
+		Bullet_Fire( ent, CHAINGUN_SPREAD, CHAINGUN_DAMAGE, MOD_CHAINGUN );
 		break;
 #endif
 	default:
@@ -896,7 +883,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ===============

```

### `openarena-engine`  — sha256 `49d6fec6c976...`, 30450 bytes

_Diff stat: +59 / -60 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_weapon.c	2026-04-16 20:02:25.201155900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_weapon.c	2026-04-16 22:48:25.753047000 +0100
@@ -85,6 +85,10 @@
 		return qfalse;
 	}
 
+	if ( ent->client->noclip ) {
+		return qfalse;
+	}
+
 	traceEnt = &g_entities[ tr.entityNum ];
 
 	// send blood impact
@@ -105,7 +109,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -149,22 +153,18 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define CHAINGUN_SPREAD		600
-#define CHAINGUN_DAMAGE         7
+#define CHAINGUN_DAMAGE		7
 #endif
 #define MACHINEGUN_SPREAD	200
 #define	MACHINEGUN_DAMAGE	7
 #define	MACHINEGUN_TEAM_DAMAGE	5		// wimpier MG in teamplay
 
-#define HEAVY_MACHINEGUN_SPREAD 200  //FIXME assuming same as mg
-#define HEAVY_MACHINEGUN_DAMAGE 8
-
-
-void Bullet_Fire (gentity_t *ent, float spread, int damage, int mod) {
+void Bullet_Fire (gentity_t *ent, float spread, int damage, int mod ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	float		r;
@@ -209,7 +209,7 @@
 		tent->s.otherEntityNum = ent->s.number;
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -227,7 +227,7 @@
 #endif
 				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
 					damage, 0, mod);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			}
 #endif
 		}
@@ -271,11 +271,10 @@
 	trace_t		tr;
 	int			damage, i, passent;
 	gentity_t	*traceEnt;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t		impactpoint, bouncedir;
 #endif
 	vec3_t		tr_start, tr_end;
-	qboolean	hitClient = qfalse;
 
 	passent = ent->s.number;
 	VectorCopy( start, tr_start );
@@ -291,7 +290,7 @@
 
 		if ( traceEnt->takedamage) {
 			damage = DEFAULT_SHOTGUN_DAMAGE * s_quadFactor;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( tr_start, impactpoint, bouncedir, tr_end );
@@ -305,12 +304,19 @@
 				}
 				continue;
 			}
-#endif
-			if( LogAccuracyHit( traceEnt, ent ) ) {
-				hitClient = qtrue;
+			else {
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_SHOTGUN);
+				if( LogAccuracyHit( traceEnt, ent ) ) {
+					return qtrue;
+				}
 			}
-			G_Damage( traceEnt, ent, ent, forward, tr.endpos, damage, 0, MOD_SHOTGUN);
-			return hitClient;
+#else
+			G_Damage( traceEnt, ent, ent, forward, tr.endpos,	damage, 0, MOD_SHOTGUN);
+				if( LogAccuracyHit( traceEnt, ent ) ) {
+					return qtrue;
+				}
+#endif
 		}
 		return qfalse;
 	}
@@ -322,22 +328,22 @@
 	int			i;
 	float		r, u;
 	vec3_t		end;
-	vec3_t		localForward, localRight, localUp;
+	vec3_t		forward, right, up;
 	qboolean	hitClient = qfalse;
 
 	// derive the right and up vectors from the forward vector, because
 	// the client won't have any other information
-	VectorNormalize2( origin2, localForward );
-	PerpendicularVector( localRight, localForward );
-	CrossProduct( localForward, localRight, localUp );
+	VectorNormalize2( origin2, forward );
+	PerpendicularVector( right, forward );
+	CrossProduct( forward, right, up );
 
 	// generate the "random" spread pattern
 	for ( i = 0 ; i < DEFAULT_SHOTGUN_COUNT ; i++ ) {
 		r = Q_crandom( &seed ) * DEFAULT_SHOTGUN_SPREAD * 16;
 		u = Q_crandom( &seed ) * DEFAULT_SHOTGUN_SPREAD * 16;
-		VectorMA( origin, 8192 * 16, localForward, end);
-		VectorMA (end, r, localRight, end);
-		VectorMA (end, u, localUp, end);
+		VectorMA( origin, 8192 * 16, forward, end);
+		VectorMA (end, r, right, end);
+		VectorMA (end, u, up, end);
 		if( ShotgunPellet( origin, end, ent ) && !hitClient ) {
 			hitClient = qtrue;
 			ent->client->accuracy_hits++;
@@ -436,7 +442,7 @@
 #define	MAX_RAIL_HITS	4
 void weapon_railgun_fire (gentity_t *ent) {
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	trace_t		trace;
@@ -464,16 +470,7 @@
 		}
 		traceEnt = &g_entities[ trace.entityNum ];
 		if ( traceEnt->takedamage ) {
-			if (traceEnt->client) {
-				gentity_t *stent;
-
-				stent = G_TempEntity(trace.endpos, EV_MISSILE_HIT);
-				stent->s.otherEntityNum = traceEnt->s.number;
-				stent->s.eventParm = DirToByte(trace.plane.normal);
-				stent->s.weapon = WP_RAILGUN;
-				stent->s.clientNum = ent->s.clientNum;
-			}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if ( G_InvulnerabilityEffect( traceEnt, forward, trace.endpos, impactpoint, bouncedir ) ) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -617,7 +614,7 @@
 void Weapon_LightningFire( gentity_t *ent ) {
 	trace_t		tr;
 	vec3_t		end;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	vec3_t impactpoint, bouncedir;
 #endif
 	gentity_t	*traceEnt, *tent;
@@ -631,7 +628,7 @@
 
 		trap_Trace( &tr, muzzle, NULL, NULL, end, passent, MASK_SHOT );
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		// if not the first trace (the lightning bounced of an invulnerability sphere)
 		if (i) {
 			// add bounced off lightning bolt temp entity
@@ -650,7 +647,7 @@
 		traceEnt = &g_entities[ tr.entityNum ];
 
 		if ( traceEnt->takedamage) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 			if ( traceEnt->client && traceEnt->client->invulnerabilityTime > level.time ) {
 				if (G_InvulnerabilityEffect( traceEnt, forward, tr.endpos, impactpoint, bouncedir )) {
 					G_BounceProjectile( muzzle, impactpoint, bouncedir, end );
@@ -666,11 +663,14 @@
 				}
 				continue;
 			}
-#endif
-			if( LogAccuracyHit( traceEnt, ent ) ) {
-				ent->client->accuracy_hits++;
+			else {
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_LIGHTNING);
 			}
-			G_Damage( traceEnt, ent, ent, forward, tr.endpos, damage, 0, MOD_LIGHTNING);
+#else
+				G_Damage( traceEnt, ent, ent, forward, tr.endpos,
+					damage, 0, MOD_LIGHTNING);
+#endif
 		}
 
 		if ( traceEnt->takedamage && traceEnt->client ) {
@@ -678,6 +678,9 @@
 			tent->s.otherEntityNum = traceEnt->s.number;
 			tent->s.eventParm = DirToByte( tr.plane.normal );
 			tent->s.weapon = ent->s.weapon;
+			if( LogAccuracyHit( traceEnt, ent ) ) {
+				ent->client->accuracy_hits++;
+			}
 		} else if ( !( tr.surfaceFlags & SURF_NOIMPACT ) ) {
 			tent = G_TempEntity( tr.endpos, EV_MISSILE_MISS );
 			tent->s.eventParm = DirToByte( tr.plane.normal );
@@ -687,7 +690,7 @@
 	}
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ======================================================================
 
@@ -778,10 +781,10 @@
 set muzzle location relative to pivoting eye
 ===============
 */
-void CalcMuzzlePoint ( gentity_t *ent, vec3_t localForward, vec3_t localRight, vec3_t localUp, vec3_t muzzlePoint ) {
+void CalcMuzzlePoint ( gentity_t *ent, vec3_t forward, vec3_t right, vec3_t up, vec3_t muzzlePoint ) {
 	VectorCopy( ent->s.pos.trBase, muzzlePoint );
 	muzzlePoint[2] += ent->client->ps.viewheight;
-	VectorMA( muzzlePoint, 14, localForward, muzzlePoint );
+	VectorMA( muzzlePoint, 14, forward, muzzlePoint );
 	// snap to integer coordinates for more efficient network bandwidth usage
 	SnapVector( muzzlePoint );
 }
@@ -793,10 +796,10 @@
 set muzzle location relative to pivoting eye
 ===============
 */
-void CalcMuzzlePointOrigin ( gentity_t *ent, vec3_t origin, vec3_t localForward, vec3_t localRight, vec3_t localUp, vec3_t muzzlePoint ) {
+void CalcMuzzlePointOrigin ( gentity_t *ent, vec3_t origin, vec3_t forward, vec3_t right, vec3_t up, vec3_t muzzlePoint ) {
 	VectorCopy( ent->s.pos.trBase, muzzlePoint );
 	muzzlePoint[2] += ent->client->ps.viewheight;
-	VectorMA( muzzlePoint, 14, localForward, muzzlePoint );
+	VectorMA( muzzlePoint, 14, forward, muzzlePoint );
 	// snap to integer coordinates for more efficient network bandwidth usage
 	SnapVector( muzzlePoint );
 }
@@ -814,7 +817,7 @@
 	} else {
 		s_quadFactor = 1;
 	}
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->client->persistantPowerup && ent->client->persistantPowerup->item && ent->client->persistantPowerup->item->giTag == PW_DOUBLER ) {
 		s_quadFactor *= 2;
 	}
@@ -822,7 +825,7 @@
 
 	// track shots taken for accuracy tracking.  Grapple is not a weapon and gauntet is just not tracked
 	if( ent->s.weapon != WP_GRAPPLING_HOOK && ent->s.weapon != WP_GAUNTLET ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		if( ent->s.weapon == WP_NAILGUN ) {
 			ent->client->accuracy_shots += NUM_NAILSHOTS;
 		} else {
@@ -856,10 +859,6 @@
 			Bullet_Fire( ent, MACHINEGUN_SPREAD, MACHINEGUN_TEAM_DAMAGE, MOD_MACHINEGUN );
 		}
 		break;
-	case WP_HEAVY_MACHINEGUN:
-		//FIXME != team game like machine gun
-		Bullet_Fire(ent, HEAVY_MACHINEGUN_SPREAD, HEAVY_MACHINEGUN_DAMAGE, MOD_HMG);
-		break;
 	case WP_GRENADE_LAUNCHER:
 		weapon_grenadelauncher_fire( ent );
 		break;
@@ -878,7 +877,7 @@
 	case WP_GRAPPLING_HOOK:
 		Weapon_GrapplingHook_Fire( ent );
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case WP_NAILGUN:
 		Weapon_Nailgun_Fire( ent );
 		break;
@@ -886,7 +885,7 @@
 		weapon_proxlauncher_fire( ent );
 		break;
 	case WP_CHAINGUN:
-		Bullet_Fire( ent, CHAINGUN_SPREAD, MACHINEGUN_DAMAGE, MOD_CHAINGUN );
+		Bullet_Fire( ent, CHAINGUN_SPREAD, CHAINGUN_DAMAGE, MOD_CHAINGUN );
 		break;
 #endif
 	default:
@@ -896,7 +895,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 
 /*
 ===============
@@ -931,7 +930,7 @@
 			continue;
 		}
 
-		// don't hit things we have already hit
+		// dont hit things we have already hit
 		if( ent->kamikazeTime > level.time ) {
 			continue;
 		}
@@ -991,7 +990,7 @@
 	for ( e = 0 ; e < numListedEntities ; e++ ) {
 		ent = &g_entities[entityList[ e ]];
 
-		// don't hit things we have already hit
+		// dont hit things we have already hit
 		if( ent->kamikazeShockTime > level.time ) {
 			continue;
 		}

```

### `openarena-gamecode`  — sha256 `29aa3c8f67f0...`, 33837 bytes

_Diff stat: +260 / -142 lines_

_(full diff is 26323 bytes — see files directly)_
