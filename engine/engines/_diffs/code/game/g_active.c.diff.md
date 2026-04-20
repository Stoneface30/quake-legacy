# Diff: `code/game/g_active.c`
**Canonical:** `wolfcamql-src` (sha256 `6f5b16dc2ba9...`, 33872 bytes)

## Variants

### `quake3-source`  — sha256 `f56d9e3c3fb6...`, 32679 bytes

_Diff stat: +36 / -76 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_active.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_active.c	2026-04-16 20:02:19.904124600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -69,21 +69,10 @@
 		client->ps.damageYaw = angles[YAW]/360.0 * 256;
 	}
 
-	// play an appropriate pain sound
+	// play an apropriate pain sound
 	if ( (level.time > player->pain_debounce_time) && !(player->flags & FL_GODMODE) ) {
 		player->pain_debounce_time = level.time + 700;
-
-		// since protocol 90 ql doesn't send real health value
-		if (player->health >= 80) {
-			G_AddEvent( player, EV_PAIN, 80 );
-		} else if (player->health >= 60) {
-			G_AddEvent( player, EV_PAIN, 60 );
-		} else if (player->health >= 40) {
-			G_AddEvent( player, EV_PAIN, 40 );
-		} else {
-			G_AddEvent( player, EV_PAIN, 20 );
-		}
-
+		G_AddEvent( player, EV_PAIN, player->health );
 		client->ps.damageEvent++;
 	}
 
@@ -193,7 +182,7 @@
 ===============
 */
 void G_SetClientSound( gentity_t *ent ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.eFlags & EF_TICKING ) {
 		ent->client->ps.loopSound = G_SoundIndex( "sound/weapons/proxmine/wstbtick.wav");
 	}
@@ -299,7 +288,7 @@
 			}
 		}
 
-		// use separate code for determining if an item is picked up
+		// use seperate code for determining if an item is picked up
 		// so you don't have to actually contact its bounding box
 		if ( hit->s.eType == ET_ITEM ) {
 			if ( !BG_PlayerTouchesItem( &ent->client->ps, &hit->s, level.time ) ) {
@@ -340,17 +329,8 @@
 
 	client = ent->client;
 
-	if ( client->sess.spectatorState != SPECTATOR_FOLLOW || !( client->ps.pm_flags & PMF_FOLLOW ) ) {
-		if ( client->sess.spectatorState == SPECTATOR_FREE ) {
-			if ( client->noclip ) {
-				client->ps.pm_type = PM_NOCLIP;
-			} else {
-				client->ps.pm_type = PM_SPECTATOR;
-			}
-		} else {
-			client->ps.pm_type = PM_FREEZE;
-		}
-
+	if ( client->sess.spectatorState != SPECTATOR_FOLLOW ) {
+		client->ps.pm_type = PM_SPECTATOR;
 		client->ps.speed = 400;	// faster than normal
 
 		// set up for pmove
@@ -486,10 +466,10 @@
 		}
 	}
 #ifdef MISSIONPACK
-	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		int w, max, inc, t, i;
     int weapList[]={WP_MACHINEGUN,WP_SHOTGUN,WP_GRENADE_LAUNCHER,WP_ROCKET_LAUNCHER,WP_LIGHTNING,WP_RAILGUN,WP_PLASMAGUN,WP_BFG,WP_NAILGUN,WP_PROX_LAUNCHER,WP_CHAINGUN};
-    int weapCount = ARRAY_LEN( weapList );
+    int weapCount = sizeof(weapList) / sizeof(int);
 		//
     for (i = 0; i < weapCount; i++) {
 		  w = weapList[i];
@@ -559,6 +539,7 @@
 	int		event;
 	gclient_t *client;
 	int		damage;
+	vec3_t	dir;
 	vec3_t	origin, angles;
 //	qboolean	fired;
 	gitem_t *item;
@@ -578,7 +559,7 @@
 			if ( ent->s.eType != ET_PLAYER ) {
 				break;		// not in the player model
 			}
-			if ( g_dmflags.integer & DF_NO_FALLING_DAMAGE ) {
+			if ( g_dmflags.integer & DF_NO_FALLING ) {
 				break;
 			}
 			if ( event == EV_FALL_FAR ) {
@@ -586,6 +567,7 @@
 			} else {
 				damage = 5;
 			}
+			VectorSet (dir, 0, 0, 1);
 			ent->pain_debounce_time = level.time + 200;	// no normal pain sound
 			G_Damage (ent, NULL, NULL, NULL, NULL, damage, 0, MOD_FALLING);
 			break;
@@ -643,7 +625,7 @@
 				}
 			}
 #endif
-			SelectSpawnPoint( ent->client->ps.origin, origin, angles, qfalse );
+			SelectSpawnPoint( ent->client->ps.origin, origin, angles );
 			TeleportPlayer( ent, origin, angles );
 			break;
 
@@ -652,7 +634,7 @@
 
 			break;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case EV_USE_ITEM3:		// kamikaze
 			// make sure the invulnerability is off
 			ent->client->invulnerabilityTime = 0;
@@ -680,7 +662,7 @@
 
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==============
 StuckInOtherClient
@@ -809,11 +791,9 @@
 
 	if ( pmove_msec.integer < 8 ) {
 		trap_Cvar_Set("pmove_msec", "8");
-		trap_Cvar_Update(&pmove_msec);
 	}
 	else if (pmove_msec.integer > 33) {
 		trap_Cvar_Set("pmove_msec", "33");
-		trap_Cvar_Update(&pmove_msec);
 	}
 
 	if ( pmove_fixed.integer || client->pers.pmoveFixed ) {
@@ -862,7 +842,7 @@
 	// set speed
 	client->ps.speed = g_speed.value;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		client->ps.speed *= 1.5;
 	}
@@ -895,12 +875,12 @@
 		ent->client->pers.cmd.buttons |= BUTTON_GESTURE;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// check for invulnerability expansion before doing the Pmove
 	if (client->ps.powerups[PW_INVULNERABILITY] ) {
 		if ( !(client->ps.pm_flags & PMF_INVULEXPAND) ) {
-			vec3_t mins = { -INVUL_RADIUS, -INVUL_RADIUS, -INVUL_RADIUS };
-			vec3_t maxs = { INVUL_RADIUS, INVUL_RADIUS, INVUL_RADIUS };
+			vec3_t mins = { -42, -42, -42 };
+			vec3_t maxs = { 42, 42, 42 };
 			vec3_t oldmins, oldmaxs;
 
 			VectorCopy (ent->r.mins, oldmins);
@@ -936,8 +916,7 @@
 	pm.trace = trap_Trace;
 	pm.pointcontents = trap_PointContents;
 	pm.debugLevel = g_debugMove.integer;
-	//pm.noFootsteps = 0;  //FIXME  ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
-	pm.noFootsteps = (g_dmflags.integer & DF_NO_FOOTSTEPS);
+	pm.noFootsteps = ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
 
 	pm.pmove_fixed = pmove_fixed.integer | client->pers.pmoveFixed;
 	pm.pmove_msec = pmove_msec.integer;
@@ -1022,13 +1001,13 @@
 			// forcerespawn is to prevent users from waiting out powerups
 			if ( g_forcerespawn.integer > 0 && 
 				( level.time - client->respawnTime ) > g_forcerespawn.integer * 1000 ) {
-				ClientRespawn( ent );
+				respawn( ent );
 				return;
 			}
 		
 			// pressing attack or use is the normal respawn method
 			if ( ucmd->buttons & ( BUTTON_ATTACK | BUTTON_USE_HOLDABLE ) ) {
-				ClientRespawn( ent );
+				respawn( ent );
 			}
 		}
 		return;
@@ -1078,9 +1057,6 @@
 */
 void SpectatorClientEndFrame( gentity_t *ent ) {
 	gclient_t	*cl;
-	//int ourClientNum;
-
-	//ourClientNum = ent->client - level.clients;
 
 	// if we are doing a chase cam or a remote view, grab the latest info
 	if ( ent->client->sess.spectatorState == SPECTATOR_FOLLOW ) {
@@ -1094,14 +1070,6 @@
 		} else if ( clientNum == -2 ) {
 			clientNum = level.follow2;
 		}
-
-#if 0
-		if (clientNum < 0) {
-			Com_Printf("follow %d\n", clientNum);
-			clientNum = ourClientNum;
-		}
-#endif
-
 		if ( clientNum >= 0 ) {
 			cl = &level.clients[ clientNum ];
 			if ( cl->pers.connected == CON_CONNECTED && cl->sess.sessionTeam != TEAM_SPECTATOR ) {
@@ -1110,19 +1078,13 @@
 				ent->client->ps.pm_flags |= PMF_FOLLOW;
 				ent->client->ps.eFlags = flags;
 				return;
+			} else {
+				// drop them to free spectators unless they are dedicated camera followers
+				if ( ent->client->sess.spectatorClient >= 0 ) {
+					ent->client->sess.spectatorState = SPECTATOR_FREE;
+					ClientBegin( ent->client - level.clients );
+				}
 			}
-		} else {
-			ent->client->sess.spectatorState = SPECTATOR_FREE;
-			ClientBegin( ent->client - level.clients );
-		}
-
-		if ( ent->client->ps.pm_flags & PMF_FOLLOW ) {
-			// drop them to free spectators unless they are dedicated camera followers
-			if ( ent->client->sess.spectatorClient >= 0 ) {
-				ent->client->sess.spectatorState = SPECTATOR_FREE;
-			}
-
-			ClientBegin( ent->client - level.clients );
 		}
 	}
 
@@ -1131,11 +1093,6 @@
 	} else {
 		ent->client->ps.pm_flags &= ~PMF_SCOREBOARD;
 	}
-
-	// hack to match quake live
-	if ( ent->client->sess.spectatorState == SPECTATOR_FREE ) {
-		ent->client->ps.stats[STAT_HEALTH] = ent->health = 0;
-	}
 }
 
 /*
@@ -1149,12 +1106,15 @@
 */
 void ClientEndFrame( gentity_t *ent ) {
 	int			i;
+	clientPersistant_t	*pers;
 
 	if ( ent->client->sess.sessionTeam == TEAM_SPECTATOR ) {
 		SpectatorClientEndFrame( ent );
 		return;
 	}
 
+	pers = &ent->client->pers;
+
 	// turn off any expired powerups
 	for ( i = 0 ; i < MAX_POWERUPS ; i++ ) {
 		if ( ent->client->ps.powerups[ i ] < level.time ) {
@@ -1162,7 +1122,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// set powerup for player animation
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		ent->client->ps.powerups[PW_GUARD] = level.time;
@@ -1173,8 +1133,8 @@
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_DOUBLER ) {
 		ent->client->ps.powerups[PW_DOUBLER] = level.time;
 	}
-	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
-		ent->client->ps.powerups[PW_ARMORREGEN] = level.time;
+	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
+		ent->client->ps.powerups[PW_AMMOREGEN] = level.time;
 	}
 	if ( ent->client->invulnerabilityTime > level.time ) {
 		ent->client->ps.powerups[PW_INVULNERABILITY] = level.time;
@@ -1205,9 +1165,9 @@
 
 	// add the EF_CONNECTION flag if we haven't gotten commands recently
 	if ( level.time - ent->client->lastCmdTime > 1000 ) {
-		ent->client->ps.eFlags |= EF_CONNECTION;
+		ent->s.eFlags |= EF_CONNECTION;
 	} else {
-		ent->client->ps.eFlags &= ~EF_CONNECTION;
+		ent->s.eFlags &= ~EF_CONNECTION;
 	}
 
 	ent->client->ps.stats[STAT_HEALTH] = ent->health;	// FIXME: get rid of ent->health...

```

### `ioquake3`  — sha256 `0ec484b25ac2...`, 32684 bytes

_Diff stat: +12 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_active.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_active.c	2026-04-16 20:02:21.541889300 +0100
@@ -72,18 +72,7 @@
 	// play an appropriate pain sound
 	if ( (level.time > player->pain_debounce_time) && !(player->flags & FL_GODMODE) ) {
 		player->pain_debounce_time = level.time + 700;
-
-		// since protocol 90 ql doesn't send real health value
-		if (player->health >= 80) {
-			G_AddEvent( player, EV_PAIN, 80 );
-		} else if (player->health >= 60) {
-			G_AddEvent( player, EV_PAIN, 60 );
-		} else if (player->health >= 40) {
-			G_AddEvent( player, EV_PAIN, 40 );
-		} else {
-			G_AddEvent( player, EV_PAIN, 20 );
-		}
-
+		G_AddEvent( player, EV_PAIN, player->health );
 		client->ps.damageEvent++;
 	}
 
@@ -139,15 +128,6 @@
 				if (ent->damage > 15)
 					ent->damage = 15;
 
-				// play a gurp sound instead of a normal pain sound
-				if (ent->health <= ent->damage) {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("*drown.wav"));
-				} else if (rand()&1) {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("sound/player/gurp1.wav"));
-				} else {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("sound/player/gurp2.wav"));
-				}
-
 				// don't play a normal pain sound
 				ent->pain_debounce_time = level.time + 200;
 
@@ -193,7 +173,7 @@
 ===============
 */
 void G_SetClientSound( gentity_t *ent ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.eFlags & EF_TICKING ) {
 		ent->client->ps.loopSound = G_SoundIndex( "sound/weapons/proxmine/wstbtick.wav");
 	}
@@ -486,7 +466,7 @@
 		}
 	}
 #ifdef MISSIONPACK
-	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		int w, max, inc, t, i;
     int weapList[]={WP_MACHINEGUN,WP_SHOTGUN,WP_GRENADE_LAUNCHER,WP_ROCKET_LAUNCHER,WP_LIGHTNING,WP_RAILGUN,WP_PLASMAGUN,WP_BFG,WP_NAILGUN,WP_PROX_LAUNCHER,WP_CHAINGUN};
     int weapCount = ARRAY_LEN( weapList );
@@ -578,7 +558,7 @@
 			if ( ent->s.eType != ET_PLAYER ) {
 				break;		// not in the player model
 			}
-			if ( g_dmflags.integer & DF_NO_FALLING_DAMAGE ) {
+			if ( g_dmflags.integer & DF_NO_FALLING ) {
 				break;
 			}
 			if ( event == EV_FALL_FAR ) {
@@ -652,7 +632,7 @@
 
 			break;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case EV_USE_ITEM3:		// kamikaze
 			// make sure the invulnerability is off
 			ent->client->invulnerabilityTime = 0;
@@ -680,7 +660,7 @@
 
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==============
 StuckInOtherClient
@@ -862,7 +842,7 @@
 	// set speed
 	client->ps.speed = g_speed.value;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		client->ps.speed *= 1.5;
 	}
@@ -895,7 +875,7 @@
 		ent->client->pers.cmd.buttons |= BUTTON_GESTURE;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// check for invulnerability expansion before doing the Pmove
 	if (client->ps.powerups[PW_INVULNERABILITY] ) {
 		if ( !(client->ps.pm_flags & PMF_INVULEXPAND) ) {
@@ -936,8 +916,7 @@
 	pm.trace = trap_Trace;
 	pm.pointcontents = trap_PointContents;
 	pm.debugLevel = g_debugMove.integer;
-	//pm.noFootsteps = 0;  //FIXME  ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
-	pm.noFootsteps = (g_dmflags.integer & DF_NO_FOOTSTEPS);
+	pm.noFootsteps = ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
 
 	pm.pmove_fixed = pmove_fixed.integer | client->pers.pmoveFixed;
 	pm.pmove_msec = pmove_msec.integer;
@@ -1078,9 +1057,6 @@
 */
 void SpectatorClientEndFrame( gentity_t *ent ) {
 	gclient_t	*cl;
-	//int ourClientNum;
-
-	//ourClientNum = ent->client - level.clients;
 
 	// if we are doing a chase cam or a remote view, grab the latest info
 	if ( ent->client->sess.spectatorState == SPECTATOR_FOLLOW ) {
@@ -1094,14 +1070,6 @@
 		} else if ( clientNum == -2 ) {
 			clientNum = level.follow2;
 		}
-
-#if 0
-		if (clientNum < 0) {
-			Com_Printf("follow %d\n", clientNum);
-			clientNum = ourClientNum;
-		}
-#endif
-
 		if ( clientNum >= 0 ) {
 			cl = &level.clients[ clientNum ];
 			if ( cl->pers.connected == CON_CONNECTED && cl->sess.sessionTeam != TEAM_SPECTATOR ) {
@@ -1111,9 +1079,6 @@
 				ent->client->ps.eFlags = flags;
 				return;
 			}
-		} else {
-			ent->client->sess.spectatorState = SPECTATOR_FREE;
-			ClientBegin( ent->client - level.clients );
 		}
 
 		if ( ent->client->ps.pm_flags & PMF_FOLLOW ) {
@@ -1131,11 +1096,6 @@
 	} else {
 		ent->client->ps.pm_flags &= ~PMF_SCOREBOARD;
 	}
-
-	// hack to match quake live
-	if ( ent->client->sess.spectatorState == SPECTATOR_FREE ) {
-		ent->client->ps.stats[STAT_HEALTH] = ent->health = 0;
-	}
 }
 
 /*
@@ -1162,7 +1122,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// set powerup for player animation
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		ent->client->ps.powerups[PW_GUARD] = level.time;
@@ -1173,8 +1133,8 @@
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_DOUBLER ) {
 		ent->client->ps.powerups[PW_DOUBLER] = level.time;
 	}
-	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
-		ent->client->ps.powerups[PW_ARMORREGEN] = level.time;
+	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
+		ent->client->ps.powerups[PW_AMMOREGEN] = level.time;
 	}
 	if ( ent->client->invulnerabilityTime > level.time ) {
 		ent->client->ps.powerups[PW_INVULNERABILITY] = level.time;

```

### `openarena-engine`  — sha256 `49beefa46e69...`, 32275 bytes

_Diff stat: +24 / -78 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_active.c	2026-04-16 20:02:25.192640800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_active.c	2026-04-16 22:48:25.745536200 +0100
@@ -69,21 +69,10 @@
 		client->ps.damageYaw = angles[YAW]/360.0 * 256;
 	}
 
-	// play an appropriate pain sound
+	// play an apropriate pain sound
 	if ( (level.time > player->pain_debounce_time) && !(player->flags & FL_GODMODE) ) {
 		player->pain_debounce_time = level.time + 700;
-
-		// since protocol 90 ql doesn't send real health value
-		if (player->health >= 80) {
-			G_AddEvent( player, EV_PAIN, 80 );
-		} else if (player->health >= 60) {
-			G_AddEvent( player, EV_PAIN, 60 );
-		} else if (player->health >= 40) {
-			G_AddEvent( player, EV_PAIN, 40 );
-		} else {
-			G_AddEvent( player, EV_PAIN, 20 );
-		}
-
+		G_AddEvent( player, EV_PAIN, player->health );
 		client->ps.damageEvent++;
 	}
 
@@ -139,15 +128,6 @@
 				if (ent->damage > 15)
 					ent->damage = 15;
 
-				// play a gurp sound instead of a normal pain sound
-				if (ent->health <= ent->damage) {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("*drown.wav"));
-				} else if (rand()&1) {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("sound/player/gurp1.wav"));
-				} else {
-					G_Sound(ent, CHAN_VOICE, G_SoundIndex("sound/player/gurp2.wav"));
-				}
-
 				// don't play a normal pain sound
 				ent->pain_debounce_time = level.time + 200;
 
@@ -193,7 +173,7 @@
 ===============
 */
 void G_SetClientSound( gentity_t *ent ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( ent->s.eFlags & EF_TICKING ) {
 		ent->client->ps.loopSound = G_SoundIndex( "sound/weapons/proxmine/wstbtick.wav");
 	}
@@ -299,7 +279,7 @@
 			}
 		}
 
-		// use separate code for determining if an item is picked up
+		// use seperate code for determining if an item is picked up
 		// so you don't have to actually contact its bounding box
 		if ( hit->s.eType == ET_ITEM ) {
 			if ( !BG_PlayerTouchesItem( &ent->client->ps, &hit->s, level.time ) ) {
@@ -340,17 +320,8 @@
 
 	client = ent->client;
 
-	if ( client->sess.spectatorState != SPECTATOR_FOLLOW || !( client->ps.pm_flags & PMF_FOLLOW ) ) {
-		if ( client->sess.spectatorState == SPECTATOR_FREE ) {
-			if ( client->noclip ) {
-				client->ps.pm_type = PM_NOCLIP;
-			} else {
-				client->ps.pm_type = PM_SPECTATOR;
-			}
-		} else {
-			client->ps.pm_type = PM_FREEZE;
-		}
-
+	if ( client->sess.spectatorState != SPECTATOR_FOLLOW ) {
+		client->ps.pm_type = PM_SPECTATOR;
 		client->ps.speed = 400;	// faster than normal
 
 		// set up for pmove
@@ -486,7 +457,7 @@
 		}
 	}
 #ifdef MISSIONPACK
-	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
+	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
 		int w, max, inc, t, i;
     int weapList[]={WP_MACHINEGUN,WP_SHOTGUN,WP_GRENADE_LAUNCHER,WP_ROCKET_LAUNCHER,WP_LIGHTNING,WP_RAILGUN,WP_PLASMAGUN,WP_BFG,WP_NAILGUN,WP_PROX_LAUNCHER,WP_CHAINGUN};
     int weapCount = ARRAY_LEN( weapList );
@@ -578,7 +549,7 @@
 			if ( ent->s.eType != ET_PLAYER ) {
 				break;		// not in the player model
 			}
-			if ( g_dmflags.integer & DF_NO_FALLING_DAMAGE ) {
+			if ( g_dmflags.integer & DF_NO_FALLING ) {
 				break;
 			}
 			if ( event == EV_FALL_FAR ) {
@@ -652,7 +623,7 @@
 
 			break;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 		case EV_USE_ITEM3:		// kamikaze
 			// make sure the invulnerability is off
 			ent->client->invulnerabilityTime = 0;
@@ -680,7 +651,7 @@
 
 }
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 /*
 ==============
 StuckInOtherClient
@@ -809,11 +780,9 @@
 
 	if ( pmove_msec.integer < 8 ) {
 		trap_Cvar_Set("pmove_msec", "8");
-		trap_Cvar_Update(&pmove_msec);
 	}
 	else if (pmove_msec.integer > 33) {
 		trap_Cvar_Set("pmove_msec", "33");
-		trap_Cvar_Update(&pmove_msec);
 	}
 
 	if ( pmove_fixed.integer || client->pers.pmoveFixed ) {
@@ -862,7 +831,7 @@
 	// set speed
 	client->ps.speed = g_speed.value;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_SCOUT ) {
 		client->ps.speed *= 1.5;
 	}
@@ -895,12 +864,12 @@
 		ent->client->pers.cmd.buttons |= BUTTON_GESTURE;
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// check for invulnerability expansion before doing the Pmove
 	if (client->ps.powerups[PW_INVULNERABILITY] ) {
 		if ( !(client->ps.pm_flags & PMF_INVULEXPAND) ) {
-			vec3_t mins = { -INVUL_RADIUS, -INVUL_RADIUS, -INVUL_RADIUS };
-			vec3_t maxs = { INVUL_RADIUS, INVUL_RADIUS, INVUL_RADIUS };
+			vec3_t mins = { -42, -42, -42 };
+			vec3_t maxs = { 42, 42, 42 };
 			vec3_t oldmins, oldmaxs;
 
 			VectorCopy (ent->r.mins, oldmins);
@@ -936,8 +905,7 @@
 	pm.trace = trap_Trace;
 	pm.pointcontents = trap_PointContents;
 	pm.debugLevel = g_debugMove.integer;
-	//pm.noFootsteps = 0;  //FIXME  ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
-	pm.noFootsteps = (g_dmflags.integer & DF_NO_FOOTSTEPS);
+	pm.noFootsteps = ( g_dmflags.integer & DF_NO_FOOTSTEPS ) > 0;
 
 	pm.pmove_fixed = pmove_fixed.integer | client->pers.pmoveFixed;
 	pm.pmove_msec = pmove_msec.integer;
@@ -1078,9 +1046,6 @@
 */
 void SpectatorClientEndFrame( gentity_t *ent ) {
 	gclient_t	*cl;
-	//int ourClientNum;
-
-	//ourClientNum = ent->client - level.clients;
 
 	// if we are doing a chase cam or a remote view, grab the latest info
 	if ( ent->client->sess.spectatorState == SPECTATOR_FOLLOW ) {
@@ -1094,14 +1059,6 @@
 		} else if ( clientNum == -2 ) {
 			clientNum = level.follow2;
 		}
-
-#if 0
-		if (clientNum < 0) {
-			Com_Printf("follow %d\n", clientNum);
-			clientNum = ourClientNum;
-		}
-#endif
-
 		if ( clientNum >= 0 ) {
 			cl = &level.clients[ clientNum ];
 			if ( cl->pers.connected == CON_CONNECTED && cl->sess.sessionTeam != TEAM_SPECTATOR ) {
@@ -1110,19 +1067,13 @@
 				ent->client->ps.pm_flags |= PMF_FOLLOW;
 				ent->client->ps.eFlags = flags;
 				return;
+			} else {
+				// drop them to free spectators unless they are dedicated camera followers
+				if ( ent->client->sess.spectatorClient >= 0 ) {
+					ent->client->sess.spectatorState = SPECTATOR_FREE;
+					ClientBegin( ent->client - level.clients );
+				}
 			}
-		} else {
-			ent->client->sess.spectatorState = SPECTATOR_FREE;
-			ClientBegin( ent->client - level.clients );
-		}
-
-		if ( ent->client->ps.pm_flags & PMF_FOLLOW ) {
-			// drop them to free spectators unless they are dedicated camera followers
-			if ( ent->client->sess.spectatorClient >= 0 ) {
-				ent->client->sess.spectatorState = SPECTATOR_FREE;
-			}
-
-			ClientBegin( ent->client - level.clients );
 		}
 	}
 
@@ -1131,11 +1082,6 @@
 	} else {
 		ent->client->ps.pm_flags &= ~PMF_SCOREBOARD;
 	}
-
-	// hack to match quake live
-	if ( ent->client->sess.spectatorState == SPECTATOR_FREE ) {
-		ent->client->ps.stats[STAT_HEALTH] = ent->health = 0;
-	}
 }
 
 /*
@@ -1162,7 +1108,7 @@
 		}
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	// set powerup for player animation
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		ent->client->ps.powerups[PW_GUARD] = level.time;
@@ -1173,8 +1119,8 @@
 	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_DOUBLER ) {
 		ent->client->ps.powerups[PW_DOUBLER] = level.time;
 	}
-	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_ARMORREGEN ) {
-		ent->client->ps.powerups[PW_ARMORREGEN] = level.time;
+	if( bg_itemlist[ent->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_AMMOREGEN ) {
+		ent->client->ps.powerups[PW_AMMOREGEN] = level.time;
 	}
 	if ( ent->client->invulnerabilityTime > level.time ) {
 		ent->client->ps.powerups[PW_INVULNERABILITY] = level.time;

```

### `openarena-gamecode`  — sha256 `fc659e317317...`, 40309 bytes

_Diff stat: +315 / -169 lines_

_(full diff is 27500 bytes — see files directly)_
