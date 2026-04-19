# Diff: `code/game/g_misc.c`
**Canonical:** `wolfcamql-src` (sha256 `9e600576c40e...`, 13900 bytes)

## Variants

### `quake3-source`  — sha256 `bf29bf68e000...`, 13689 bytes

_Diff stat: +8 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_misc.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_misc.c	2026-04-16 20:02:19.907572900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -78,9 +78,7 @@
 
 void TeleportPlayer( gentity_t *player, vec3_t origin, vec3_t angles ) {
 	gentity_t	*tent;
-	qboolean noAngles;
 
-	noAngles = (angles[0] > 999999.0);
 	// use temp events at source and destination to prevent the effect
 	// from getting dropped by a second player event
 	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR ) {
@@ -96,17 +94,19 @@
 
 	VectorCopy ( origin, player->client->ps.origin );
 	player->client->ps.origin[2] += 1;
-	if (!noAngles) {
+
 	// spit the player out
 	AngleVectors( angles, player->client->ps.velocity, NULL, NULL );
 	VectorScale( player->client->ps.velocity, 400, player->client->ps.velocity );
 	player->client->ps.pm_time = 160;		// hold time
 	player->client->ps.pm_flags |= PMF_TIME_KNOCKBACK;
-	// set angles
-	SetClientViewAngle(player, angles);
-	}
+
 	// toggle the teleport bit so the client knows to not lerp
 	player->client->ps.eFlags ^= EF_TELEPORT_BIT;
+
+	// set angles
+	SetClientViewAngle( player, angles );
+
 	// kill anything at the destination
 	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR ) {
 		G_KillBox (player);
@@ -160,8 +160,6 @@
 	gentity_t	*target;
 	gentity_t	*owner;
 
-	//Com_Printf("^1locateCamera %s\n", ent->target);
-
 	owner = G_PickTarget( ent->target );
 	if ( !owner ) {
 		G_Printf( "Couldn't find target for misc_partal_surface\n" );
@@ -201,7 +199,6 @@
 	}
 
 	ent->s.eventParm = DirToByte( dir );
-	//Com_Printf("%d  dir %d\n", ent->s.number, ent->s.eventParm);
 }
 
 /*QUAKED misc_portal_surface (0 0 1) (-8 -8 -8) (8 8 8)
@@ -340,7 +337,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 static void PortalDie (gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int mod) {
 	G_FreeEntity( self );
 	//FIXME do something more interesting

```

### `openarena-engine`  — sha256 `bef4dc868b70...`, 13781 bytes
Also identical in: ioquake3

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_misc.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_misc.c	2026-04-16 22:48:25.748537400 +0100
@@ -160,8 +160,6 @@
 	gentity_t	*target;
 	gentity_t	*owner;
 
-	//Com_Printf("^1locateCamera %s\n", ent->target);
-
 	owner = G_PickTarget( ent->target );
 	if ( !owner ) {
 		G_Printf( "Couldn't find target for misc_partal_surface\n" );
@@ -201,7 +199,6 @@
 	}
 
 	ent->s.eventParm = DirToByte( dir );
-	//Com_Printf("%d  dir %d\n", ent->s.number, ent->s.eventParm);
 }
 
 /*QUAKED misc_portal_surface (0 0 1) (-8 -8 -8) (8 8 8)
@@ -340,7 +337,7 @@
 }
 
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 static void PortalDie (gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int mod) {
 	G_FreeEntity( self );
 	//FIXME do something more interesting

```

### `openarena-gamecode`  — sha256 `09693b68f2ac...`, 16126 bytes

_Diff stat: +110 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_misc.c	2026-04-16 20:02:25.196158500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_misc.c	2026-04-16 22:48:24.171988900 +0100
@@ -83,7 +83,7 @@
 	noAngles = (angles[0] > 999999.0);
 	// use temp events at source and destination to prevent the effect
 	// from getting dropped by a second player event
-	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR ) {
+	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR && player->client->ps.pm_type != PM_SPECTATOR) {
 		tent = G_TempEntity( player->client->ps.origin, EV_PLAYER_TELEPORT_OUT );
 		tent->s.clientNum = player->s.clientNum;
 
@@ -96,19 +96,28 @@
 
 	VectorCopy ( origin, player->client->ps.origin );
 	player->client->ps.origin[2] += 1;
+
 	if (!noAngles) {
-	// spit the player out
-	AngleVectors( angles, player->client->ps.velocity, NULL, NULL );
-	VectorScale( player->client->ps.velocity, 400, player->client->ps.velocity );
-	player->client->ps.pm_time = 160;		// hold time
-	player->client->ps.pm_flags |= PMF_TIME_KNOCKBACK;
-	// set angles
-	SetClientViewAngle(player, angles);
+		// spit the player out
+		AngleVectors( angles, player->client->ps.velocity, NULL, NULL );
+		VectorScale( player->client->ps.velocity, 400, player->client->ps.velocity );
+		player->client->ps.pm_time = 160;		// hold time
+		player->client->ps.pm_flags |= PMF_TIME_KNOCKBACK;
+
+		// set angles
+		SetClientViewAngle(player, angles);
 	}
+
 	// toggle the teleport bit so the client knows to not lerp
 	player->client->ps.eFlags ^= EF_TELEPORT_BIT;
+
+//unlagged - backward reconciliation #3
+	// we don't want players being backward-reconciled back through teleporters
+	G_ResetHistory( player );
+//unlagged - backward reconciliation #3
+
 	// kill anything at the destination
-	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR ) {
+	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR && player->client->ps.pm_type != PM_SPECTATOR ) {
 		G_KillBox (player);
 	}
 
@@ -118,7 +127,7 @@
 	// use the precise origin for linking
 	VectorCopy( player->client->ps.origin, player->r.currentOrigin );
 
-	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR ) {
+	if ( player->client->sess.sessionTeam != TEAM_SPECTATOR && player->client->ps.pm_type != PM_SPECTATOR ) {
 		trap_LinkEntity (player);
 	}
 }
@@ -160,8 +169,6 @@
 	gentity_t	*target;
 	gentity_t	*owner;
 
-	//Com_Printf("^1locateCamera %s\n", ent->target);
-
 	owner = G_PickTarget( ent->target );
 	if ( !owner ) {
 		G_Printf( "Couldn't find target for misc_partal_surface\n" );
@@ -201,7 +208,6 @@
 	}
 
 	ent->s.eventParm = DirToByte( dir );
-	//Com_Printf("%d  dir %d\n", ent->s.number, ent->s.eventParm);
 }
 
 /*QUAKED misc_portal_surface (0 0 1) (-8 -8 -8) (8 8 8)
@@ -339,8 +345,6 @@
 	InitShooter( ent, WP_GRENADE_LAUNCHER);
 }
 
-
-#if 1  //def MPACK
 static void PortalDie (gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int mod) {
 	G_FreeEntity( self );
 	//FIXME do something more interesting
@@ -482,4 +486,94 @@
 	}
 
 }
-#endif
+
+static int countItems(const char* itemname, qboolean exclude_no_bots) {
+	gentity_t	*spot;
+	int			count;
+
+	count = 0;
+	spot = NULL;
+
+	while ((spot = G_Find (spot, FOFS(classname), itemname)) != NULL) {
+			if(exclude_no_bots && spot->flags & (FL_NO_BOTS|FL_NO_HUMANS) )
+		continue; //Do not count no_humans or no_bots items
+			count++;
+	}
+	G_Printf("Number of %s: %i\n",itemname,count);
+	return count;
+}
+
+static int countFfaSpawnpoints(void) {
+    return countItems("info_player_deathmatch",qtrue);
+}
+
+static int countDdSpawnpoints(void) {
+	int mincount,tmp;
+	mincount = 100;
+
+	tmp = countItems("info_player_dd_red",qtrue);
+	if(!tmp){
+	tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount)
+		mincount=tmp;
+
+	tmp = countItems("info_player_dd_blue",qtrue);
+	if(!tmp){
+	tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount)
+		mincount=tmp;
+
+	return mincount;
+
+}
+
+static int countCtfSpawnpoints(void) {
+	int mincount,tmp;
+
+	mincount=100;
+
+	tmp = countItems("team_CTF_redplayer",qtrue);
+	if(!tmp){
+		tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount) {
+		mincount=tmp;
+	}
+
+	tmp = countItems("team_CTF_blueplayer",qtrue);
+	if(!tmp){
+		tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount) {
+		mincount=tmp;
+	}
+
+	tmp = countItems("team_CTF_redspawn",qtrue);
+	if(!tmp){
+		tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount)
+		mincount=tmp;
+
+	tmp = countItems("team_CTF_bluespawn",qtrue);
+	if(!tmp){
+		tmp = countFfaSpawnpoints(); //tmp==0 -> Fallback to FFA spawnpoints!
+	}
+	if(tmp<mincount) {
+		mincount=tmp;
+	}
+
+	return mincount;
+}
+
+int MinSpawnpointCount(void) {
+	if(g_gametype.integer < GT_CTF || g_ffa_gt > 0) {
+		return countFfaSpawnpoints();
+	}
+	if(g_gametype.integer == GT_DOUBLE_D ) {
+		return countDdSpawnpoints();
+	}
+	return countCtfSpawnpoints();
+}

```
