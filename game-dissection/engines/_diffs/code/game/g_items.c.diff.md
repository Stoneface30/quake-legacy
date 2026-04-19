# Diff: `code/game/g_items.c`
**Canonical:** `wolfcamql-src` (sha256 `85a03d1e6686...`, 27404 bytes)

## Variants

### `quake3-source`  — sha256 `168044c842d1...`, 26403 bytes

_Diff stat: +41 / -76 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_items.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_items.c	2026-04-16 20:02:19.906577000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -32,7 +32,7 @@
 
   Respawnable items don't actually go away when picked up, they are
   just made invisible and untouchable.  This allows them to ride
-  movers and respawn appropriately.
+  movers and respawn apropriately.
 */
 
 
@@ -117,7 +117,7 @@
 
 //======================================================================
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Pickup_PersistantPowerup( gentity_t *ent, gentity_t *other ) {
 	int		clientNum;
 	char	userinfo[MAX_INFO_STRING];
@@ -127,7 +127,8 @@
 	other->client->ps.stats[STAT_PERSISTANT_POWERUP] = ent->item - bg_itemlist;
 	other->client->persistantPowerup = ent;
 
-	if (ent->item->giTag == PW_GUARD) {
+	switch( ent->item->giTag ) {
+	case PW_GUARD:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -141,7 +142,10 @@
 		other->client->ps.stats[STAT_MAX_HEALTH] = max;
 		other->client->ps.stats[STAT_ARMOR] = max;
 		other->client->pers.maxHealth = max;
-	} else if (ent->item->giTag == PW_SCOUT) {
+
+		break;
+
+	case PW_SCOUT:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -150,7 +154,9 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		other->client->ps.stats[STAT_ARMOR] = 0;
-	} else if (ent->item->giTag == PW_DOUBLER) {
+		break;
+
+	case PW_DOUBLER:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -158,7 +164,8 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
-	} else if (ent->item->giTag == PW_ARMORREGEN) {
+		break;
+	case PW_AMMOREGEN:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -167,7 +174,8 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		memset(other->client->ammoTimes, 0, sizeof(other->client->ammoTimes));
-	} else {
+		break;
+	default:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -175,6 +183,7 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
+		break;
 	}
 
 	return -1;
@@ -215,27 +224,7 @@
 		quantity = ent->item->quantity;
 	}
 
-	if (!Q_stricmp(ent->item->classname, "ammo_pack")) {
-		int i;
-
-		for (i = 0;  i < bg_numItems;  i++) {
-			const gitem_t *item;
-
-			item = &bg_itemlist[i];
-			if (item->giType != IT_AMMO) {
-				// skip
-				continue;
-			}
-			if (!Q_stricmp(item->classname, "ammo_pack")) {
-				// skip
-				continue;
-			}
-
-			Add_Ammo(other, item->giTag, item->quantity);
-		}
-	} else {
-		Add_Ammo (other, ent->item->giTag, quantity);
-	}
+	Add_Ammo (other, ent->item->giTag, quantity);
 
 	return RESPAWN_AMMO;
 }
@@ -291,8 +280,8 @@
 	int			quantity;
 
 	// small and mega healths will go over the max
-#if 1  //def MPACK
-	if( bg_itemlist[other->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
+#ifdef MISSIONPACK
+	if( other->client && bg_itemlist[other->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		max = other->client->ps.stats[STAT_MAX_HEALTH];
 	}
 	else
@@ -326,7 +315,7 @@
 //======================================================================
 
 int Pickup_Armor( gentity_t *ent, gentity_t *other ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int		upperBound;
 
 	other->client->ps.stats[STAT_ARMOR] += ent->item->quantity;
@@ -359,11 +348,6 @@
 ===============
 */
 void RespawnItem( gentity_t *ent ) {
-	if (!ent) {
-		Com_Printf("^1ERROR RespawnItem ent == null\n");
-		return;
-	}
-
 	// randomly select from teamed entities
 	if (ent->team) {
 		gentity_t	*master;
@@ -378,20 +362,12 @@
 		for (count = 0, ent = master; ent; ent = ent->teamchain, count++)
 			;
 
-		if (count) {
-			choice = rand() % count;
-		} else {
-			choice = 0;
-		}
+		choice = rand() % count;
 
-		for (count = 0, ent = master; ent && count < choice; ent = ent->teamchain, count++)
+		for (count = 0, ent = master; count < choice; ent = ent->teamchain, count++)
 			;
 	}
 
-	if (!ent) {
-		return;
-	}
-
 	ent->r.contents = CONTENTS_TRIGGER;
 	ent->s.eFlags &= ~EF_NODRAW;
 	ent->r.svFlags &= ~SVF_NOCLIENT;
@@ -477,7 +453,7 @@
 		respawn = Pickup_Powerup(ent, other);
 		predict = qfalse;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case IT_PERSISTANT_POWERUP:
 		respawn = Pickup_PersistantPowerup(ent, other);
 		break;
@@ -496,10 +472,6 @@
 		return;
 	}
 
-	// for ql timer pies
-	ent->s.time = level.time + respawn * 1000;
-	ent->s.time2 = respawn * 1000;
-
 	// play the normal pickup sound
 	if (predict) {
 		G_AddPredictableEvent( other, EV_ITEM_PICKUP, ent->s.modelindex );
@@ -560,14 +532,7 @@
 	// picked up items still stay around, they just don't
 	// draw anything.  This allows respawnable items
 	// to be placed on movers.
-
-	// ql timer pies..  send no draw items to client
-
-	// commenting this creates double pickup sounds if cg_predict.c isn't changed  -- 2019-02-14 added EF_NODRAW check in cg_predict.c
-	// ent->r.svFlags |= SVF_NOCLIENT;
-	if (ent->item->giType == IT_POWERUP) {
-		ent->r.svFlags |= SVF_BROADCAST;
-	}
+	ent->r.svFlags |= SVF_NOCLIENT;
 	ent->s.eFlags |= EF_NODRAW;
 	ent->r.contents = 0;
 
@@ -695,7 +660,7 @@
 
 	ent->r.contents = CONTENTS_TRIGGER;
 	ent->touch = Touch_Item;
-	// using an item causes it to respawn
+	// useing an item causes it to respawn
 	ent->use = Use_Item;
 
 	if ( ent->spawnflags & 1 ) {
@@ -717,8 +682,8 @@
 		G_SetOrigin( ent, tr.endpos );
 	}
 
-	// team members and targeted items aren't present at start
-	if ( ( ent->flags & FL_TEAMMEMBER ) || ent->targetname ) {
+	// team slaves and targeted items aren't present at start
+	if ( ( ent->flags & FL_TEAMSLAVE ) || ent->targetname ) {
 		ent->s.eFlags |= EF_NODRAW;
 		ent->r.contents = 0;
 		return;
@@ -759,11 +724,11 @@
 		// check for the two flags
 		item = BG_FindItem( "Red Flag" );
 		if ( !item || !itemRegistered[ item - bg_itemlist ] ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_redflag in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_redflag in map" );
 		}
 		item = BG_FindItem( "Blue Flag" );
 		if ( !item || !itemRegistered[ item - bg_itemlist ] ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_blueflag in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_blueflag in map" );
 		}
 	}
 #ifdef MISSIONPACK
@@ -773,15 +738,15 @@
 		// check for all three flags
 		item = BG_FindItem( "Red Flag" );
 		if ( !item || !itemRegistered[ item - bg_itemlist ] ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_redflag in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_redflag in map" );
 		}
 		item = BG_FindItem( "Blue Flag" );
 		if ( !item || !itemRegistered[ item - bg_itemlist ] ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_blueflag in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_blueflag in map" );
 		}
 		item = BG_FindItem( "Neutral Flag" );
 		if ( !item || !itemRegistered[ item - bg_itemlist ] ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_neutralflag in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_CTF_neutralflag in map" );
 		}
 	}
 
@@ -792,13 +757,13 @@
 		ent = NULL;
 		ent = G_Find( ent, FOFS(classname), "team_redobelisk" );
 		if( !ent ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_redobelisk in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_redobelisk in map" );
 		}
 
 		ent = NULL;
 		ent = G_Find( ent, FOFS(classname), "team_blueobelisk" );
 		if( !ent ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_blueobelisk in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_blueobelisk in map" );
 		}
 	}
 
@@ -809,19 +774,19 @@
 		ent = NULL;
 		ent = G_Find( ent, FOFS(classname), "team_redobelisk" );
 		if( !ent ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_redobelisk in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_redobelisk in map" );
 		}
 
 		ent = NULL;
 		ent = G_Find( ent, FOFS(classname), "team_blueobelisk" );
 		if( !ent ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_blueobelisk in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_blueobelisk in map" );
 		}
 
 		ent = NULL;
 		ent = G_Find( ent, FOFS(classname), "team_neutralobelisk" );
 		if( !ent ) {
-			G_Printf( S_COLOR_YELLOW "WARNING: No team_neutralobelisk in map\n" );
+			G_Printf( S_COLOR_YELLOW "WARNING: No team_neutralobelisk in map" );
 		}
 	}
 #endif
@@ -933,7 +898,7 @@
 		G_SpawnFloat( "noglobalsound", "0", &ent->speed);
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( item->giType == IT_PERSISTANT_POWERUP ) {
 		ent->s.generic1 = ent->spawnflags;
 	}
@@ -988,8 +953,8 @@
 	int			contents;
 	int			mask;
 
-	// if its groundentity has been set to none, it may have been pushed off an edge
-	if ( ent->s.groundEntityNum == ENTITYNUM_NONE  ) {
+	// if groundentity has been set to -1, it may have been pushed off an edge
+	if ( ent->s.groundEntityNum == -1 ) {
 		if ( ent->s.pos.trType != TR_GRAVITY ) {
 			ent->s.pos.trType = TR_GRAVITY;
 			ent->s.pos.trTime = level.time;

```

### `ioquake3`  — sha256 `d2167a8abb2a...`, 26516 bytes

_Diff stat: +23 / -50 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_items.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_items.c	2026-04-16 20:02:21.543355100 +0100
@@ -117,7 +117,7 @@
 
 //======================================================================
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Pickup_PersistantPowerup( gentity_t *ent, gentity_t *other ) {
 	int		clientNum;
 	char	userinfo[MAX_INFO_STRING];
@@ -127,7 +127,8 @@
 	other->client->ps.stats[STAT_PERSISTANT_POWERUP] = ent->item - bg_itemlist;
 	other->client->persistantPowerup = ent;
 
-	if (ent->item->giTag == PW_GUARD) {
+	switch( ent->item->giTag ) {
+	case PW_GUARD:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -141,7 +142,10 @@
 		other->client->ps.stats[STAT_MAX_HEALTH] = max;
 		other->client->ps.stats[STAT_ARMOR] = max;
 		other->client->pers.maxHealth = max;
-	} else if (ent->item->giTag == PW_SCOUT) {
+
+		break;
+
+	case PW_SCOUT:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -150,7 +154,9 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		other->client->ps.stats[STAT_ARMOR] = 0;
-	} else if (ent->item->giTag == PW_DOUBLER) {
+		break;
+
+	case PW_DOUBLER:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -158,7 +164,8 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
-	} else if (ent->item->giTag == PW_ARMORREGEN) {
+		break;
+	case PW_AMMOREGEN:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -167,7 +174,8 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		memset(other->client->ammoTimes, 0, sizeof(other->client->ammoTimes));
-	} else {
+		break;
+	default:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -175,6 +183,7 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
+		break;
 	}
 
 	return -1;
@@ -215,27 +224,7 @@
 		quantity = ent->item->quantity;
 	}
 
-	if (!Q_stricmp(ent->item->classname, "ammo_pack")) {
-		int i;
-
-		for (i = 0;  i < bg_numItems;  i++) {
-			const gitem_t *item;
-
-			item = &bg_itemlist[i];
-			if (item->giType != IT_AMMO) {
-				// skip
-				continue;
-			}
-			if (!Q_stricmp(item->classname, "ammo_pack")) {
-				// skip
-				continue;
-			}
-
-			Add_Ammo(other, item->giTag, item->quantity);
-		}
-	} else {
-		Add_Ammo (other, ent->item->giTag, quantity);
-	}
+	Add_Ammo (other, ent->item->giTag, quantity);
 
 	return RESPAWN_AMMO;
 }
@@ -291,7 +280,7 @@
 	int			quantity;
 
 	// small and mega healths will go over the max
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[other->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		max = other->client->ps.stats[STAT_MAX_HEALTH];
 	}
@@ -326,7 +315,7 @@
 //======================================================================
 
 int Pickup_Armor( gentity_t *ent, gentity_t *other ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int		upperBound;
 
 	other->client->ps.stats[STAT_ARMOR] += ent->item->quantity;
@@ -360,7 +349,6 @@
 */
 void RespawnItem( gentity_t *ent ) {
 	if (!ent) {
-		Com_Printf("^1ERROR RespawnItem ent == null\n");
 		return;
 	}
 
@@ -378,11 +366,7 @@
 		for (count = 0, ent = master; ent; ent = ent->teamchain, count++)
 			;
 
-		if (count) {
-			choice = rand() % count;
-		} else {
-			choice = 0;
-		}
+		choice = rand() % count;
 
 		for (count = 0, ent = master; ent && count < choice; ent = ent->teamchain, count++)
 			;
@@ -477,7 +461,7 @@
 		respawn = Pickup_Powerup(ent, other);
 		predict = qfalse;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case IT_PERSISTANT_POWERUP:
 		respawn = Pickup_PersistantPowerup(ent, other);
 		break;
@@ -496,10 +480,6 @@
 		return;
 	}
 
-	// for ql timer pies
-	ent->s.time = level.time + respawn * 1000;
-	ent->s.time2 = respawn * 1000;
-
 	// play the normal pickup sound
 	if (predict) {
 		G_AddPredictableEvent( other, EV_ITEM_PICKUP, ent->s.modelindex );
@@ -560,14 +540,7 @@
 	// picked up items still stay around, they just don't
 	// draw anything.  This allows respawnable items
 	// to be placed on movers.
-
-	// ql timer pies..  send no draw items to client
-
-	// commenting this creates double pickup sounds if cg_predict.c isn't changed  -- 2019-02-14 added EF_NODRAW check in cg_predict.c
-	// ent->r.svFlags |= SVF_NOCLIENT;
-	if (ent->item->giType == IT_POWERUP) {
-		ent->r.svFlags |= SVF_BROADCAST;
-	}
+	ent->r.svFlags |= SVF_NOCLIENT;
 	ent->s.eFlags |= EF_NODRAW;
 	ent->r.contents = 0;
 
@@ -933,7 +906,7 @@
 		G_SpawnFloat( "noglobalsound", "0", &ent->speed);
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( item->giType == IT_PERSISTANT_POWERUP ) {
 		ent->s.generic1 = ent->spawnflags;
 	}
@@ -989,7 +962,7 @@
 	int			mask;
 
 	// if its groundentity has been set to none, it may have been pushed off an edge
-	if ( ent->s.groundEntityNum == ENTITYNUM_NONE  ) {
+	if ( ent->s.groundEntityNum == ENTITYNUM_NONE ) {
 		if ( ent->s.pos.trType != TR_GRAVITY ) {
 			ent->s.pos.trType = TR_GRAVITY;
 			ent->s.pos.trTime = level.time;

```

### `openarena-engine`  — sha256 `19854894bf35...`, 26445 bytes

_Diff stat: +28 / -63 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_items.c	2026-04-16 20:02:25.194150900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_items.c	2026-04-16 22:48:25.746535800 +0100
@@ -32,7 +32,7 @@
 
   Respawnable items don't actually go away when picked up, they are
   just made invisible and untouchable.  This allows them to ride
-  movers and respawn appropriately.
+  movers and respawn apropriately.
 */
 
 
@@ -117,7 +117,7 @@
 
 //======================================================================
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 int Pickup_PersistantPowerup( gentity_t *ent, gentity_t *other ) {
 	int		clientNum;
 	char	userinfo[MAX_INFO_STRING];
@@ -127,7 +127,8 @@
 	other->client->ps.stats[STAT_PERSISTANT_POWERUP] = ent->item - bg_itemlist;
 	other->client->persistantPowerup = ent;
 
-	if (ent->item->giTag == PW_GUARD) {
+	switch( ent->item->giTag ) {
+	case PW_GUARD:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -141,7 +142,10 @@
 		other->client->ps.stats[STAT_MAX_HEALTH] = max;
 		other->client->ps.stats[STAT_ARMOR] = max;
 		other->client->pers.maxHealth = max;
-	} else if (ent->item->giTag == PW_SCOUT) {
+
+		break;
+
+	case PW_SCOUT:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -150,7 +154,9 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		other->client->ps.stats[STAT_ARMOR] = 0;
-	} else if (ent->item->giTag == PW_DOUBLER) {
+		break;
+
+	case PW_DOUBLER:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -158,7 +164,8 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
-	} else if (ent->item->giTag == PW_ARMORREGEN) {
+		break;
+	case PW_AMMOREGEN:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -167,7 +174,8 @@
 		}
 		other->client->pers.maxHealth = handicap;
 		memset(other->client->ammoTimes, 0, sizeof(other->client->ammoTimes));
-	} else {
+		break;
+	default:
 		clientNum = other->client->ps.clientNum;
 		trap_GetUserinfo( clientNum, userinfo, sizeof(userinfo) );
 		handicap = atof( Info_ValueForKey( userinfo, "handicap" ) );
@@ -175,6 +183,7 @@
 			handicap = 100.0f;
 		}
 		other->client->pers.maxHealth = handicap;
+		break;
 	}
 
 	return -1;
@@ -215,27 +224,7 @@
 		quantity = ent->item->quantity;
 	}
 
-	if (!Q_stricmp(ent->item->classname, "ammo_pack")) {
-		int i;
-
-		for (i = 0;  i < bg_numItems;  i++) {
-			const gitem_t *item;
-
-			item = &bg_itemlist[i];
-			if (item->giType != IT_AMMO) {
-				// skip
-				continue;
-			}
-			if (!Q_stricmp(item->classname, "ammo_pack")) {
-				// skip
-				continue;
-			}
-
-			Add_Ammo(other, item->giTag, item->quantity);
-		}
-	} else {
-		Add_Ammo (other, ent->item->giTag, quantity);
-	}
+	Add_Ammo (other, ent->item->giTag, quantity);
 
 	return RESPAWN_AMMO;
 }
@@ -291,7 +280,7 @@
 	int			quantity;
 
 	// small and mega healths will go over the max
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if( bg_itemlist[other->client->ps.stats[STAT_PERSISTANT_POWERUP]].giTag == PW_GUARD ) {
 		max = other->client->ps.stats[STAT_MAX_HEALTH];
 	}
@@ -326,7 +315,7 @@
 //======================================================================
 
 int Pickup_Armor( gentity_t *ent, gentity_t *other ) {
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int		upperBound;
 
 	other->client->ps.stats[STAT_ARMOR] += ent->item->quantity;
@@ -359,11 +348,6 @@
 ===============
 */
 void RespawnItem( gentity_t *ent ) {
-	if (!ent) {
-		Com_Printf("^1ERROR RespawnItem ent == null\n");
-		return;
-	}
-
 	// randomly select from teamed entities
 	if (ent->team) {
 		gentity_t	*master;
@@ -378,20 +362,12 @@
 		for (count = 0, ent = master; ent; ent = ent->teamchain, count++)
 			;
 
-		if (count) {
-			choice = rand() % count;
-		} else {
-			choice = 0;
-		}
+		choice = rand() % count;
 
-		for (count = 0, ent = master; ent && count < choice; ent = ent->teamchain, count++)
+		for (count = 0, ent = master; count < choice; ent = ent->teamchain, count++)
 			;
 	}
 
-	if (!ent) {
-		return;
-	}
-
 	ent->r.contents = CONTENTS_TRIGGER;
 	ent->s.eFlags &= ~EF_NODRAW;
 	ent->r.svFlags &= ~SVF_NOCLIENT;
@@ -477,7 +453,7 @@
 		respawn = Pickup_Powerup(ent, other);
 		predict = qfalse;
 		break;
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	case IT_PERSISTANT_POWERUP:
 		respawn = Pickup_PersistantPowerup(ent, other);
 		break;
@@ -496,10 +472,6 @@
 		return;
 	}
 
-	// for ql timer pies
-	ent->s.time = level.time + respawn * 1000;
-	ent->s.time2 = respawn * 1000;
-
 	// play the normal pickup sound
 	if (predict) {
 		G_AddPredictableEvent( other, EV_ITEM_PICKUP, ent->s.modelindex );
@@ -560,14 +532,7 @@
 	// picked up items still stay around, they just don't
 	// draw anything.  This allows respawnable items
 	// to be placed on movers.
-
-	// ql timer pies..  send no draw items to client
-
-	// commenting this creates double pickup sounds if cg_predict.c isn't changed  -- 2019-02-14 added EF_NODRAW check in cg_predict.c
-	// ent->r.svFlags |= SVF_NOCLIENT;
-	if (ent->item->giType == IT_POWERUP) {
-		ent->r.svFlags |= SVF_BROADCAST;
-	}
+	ent->r.svFlags |= SVF_NOCLIENT;
 	ent->s.eFlags |= EF_NODRAW;
 	ent->r.contents = 0;
 
@@ -695,7 +660,7 @@
 
 	ent->r.contents = CONTENTS_TRIGGER;
 	ent->touch = Touch_Item;
-	// using an item causes it to respawn
+	// useing an item causes it to respawn
 	ent->use = Use_Item;
 
 	if ( ent->spawnflags & 1 ) {
@@ -717,8 +682,8 @@
 		G_SetOrigin( ent, tr.endpos );
 	}
 
-	// team members and targeted items aren't present at start
-	if ( ( ent->flags & FL_TEAMMEMBER ) || ent->targetname ) {
+	// team slaves and targeted items aren't present at start
+	if ( ( ent->flags & FL_TEAMSLAVE ) || ent->targetname ) {
 		ent->s.eFlags |= EF_NODRAW;
 		ent->r.contents = 0;
 		return;
@@ -933,7 +898,7 @@
 		G_SpawnFloat( "noglobalsound", "0", &ent->speed);
 	}
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	if ( item->giType == IT_PERSISTANT_POWERUP ) {
 		ent->s.generic1 = ent->spawnflags;
 	}
@@ -989,7 +954,7 @@
 	int			mask;
 
 	// if its groundentity has been set to none, it may have been pushed off an edge
-	if ( ent->s.groundEntityNum == ENTITYNUM_NONE  ) {
+	if ( ent->s.groundEntityNum == ENTITYNUM_NONE ) {
 		if ( ent->s.pos.trType != TR_GRAVITY ) {
 			ent->s.pos.trType = TR_GRAVITY;
 			ent->s.pos.trTime = level.time;

```

### `openarena-gamecode`  — sha256 `3c98b5963629...`, 31698 bytes

_Diff stat: +250 / -147 lines_

_(full diff is 24415 bytes — see files directly)_
