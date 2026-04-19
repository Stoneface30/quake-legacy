# Diff: `code/game/g_spawn.c`
**Canonical:** `wolfcamql-src` (sha256 `144029a3c21e...`, 21828 bytes)

## Variants

### `quake3-source`  — sha256 `611d4c13b779...`, 17198 bytes

_Diff stat: +38 / -179 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_spawn.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_spawn.c	2026-04-16 20:02:19.909574100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -75,40 +75,47 @@
 // fields are needed for spawning from the entity string
 //
 typedef enum {
-	F_INT,
+	F_INT, 
 	F_FLOAT,
-	F_STRING,
+	F_LSTRING,			// string on disk, pointer in memory, TAG_LEVEL
+	F_GSTRING,			// string on disk, pointer in memory, TAG_GAME
 	F_VECTOR,
-	F_ANGLEHACK
+	F_ANGLEHACK,
+	F_ENTITY,			// index on disk, pointer in memory
+	F_ITEM,				// index on disk, pointer in memory
+	F_CLIENT,			// index on disk, pointer in memory
+	F_IGNORE
 } fieldtype_t;
 
 typedef struct
 {
 	char	*name;
-	size_t		ofs;
+	int		ofs;
 	fieldtype_t	type;
+	int		flags;
 } field_t;
 
 field_t fields[] = {
-	{"classname", FOFS(classname), F_STRING},
+	{"classname", FOFS(classname), F_LSTRING},
 	{"origin", FOFS(s.origin), F_VECTOR},
-	{"model", FOFS(model), F_STRING},
-	{"model2", FOFS(model2), F_STRING},
+	{"model", FOFS(model), F_LSTRING},
+	{"model2", FOFS(model2), F_LSTRING},
 	{"spawnflags", FOFS(spawnflags), F_INT},
 	{"speed", FOFS(speed), F_FLOAT},
-	{"target", FOFS(target), F_STRING},
-	{"targetname", FOFS(targetname), F_STRING},
-	{"message", FOFS(message), F_STRING},
-	{"team", FOFS(team), F_STRING},
+	{"target", FOFS(target), F_LSTRING},
+	{"targetname", FOFS(targetname), F_LSTRING},
+	{"message", FOFS(message), F_LSTRING},
+	{"team", FOFS(team), F_LSTRING},
 	{"wait", FOFS(wait), F_FLOAT},
 	{"random", FOFS(random), F_FLOAT},
 	{"count", FOFS(count), F_INT},
 	{"health", FOFS(health), F_INT},
+	{"light", 0, F_IGNORE},
 	{"dmg", FOFS(damage), F_INT},
 	{"angles", FOFS(s.angles), F_VECTOR},
 	{"angle", FOFS(s.angles), F_ANGLEHACK},
-	{"targetShaderName", FOFS(targetShaderName), F_STRING},
-	{"targetShaderNewName", FOFS(targetShaderNewName), F_STRING},
+	{"targetShaderName", FOFS(targetShaderName), F_LSTRING},
+	{"targetShaderNewName", FOFS(targetShaderNewName), F_LSTRING},
 
 	{NULL}
 };
@@ -122,6 +129,10 @@
 void SP_info_player_start (gentity_t *ent);
 void SP_info_player_deathmatch (gentity_t *ent);
 void SP_info_player_intermission (gentity_t *ent);
+void SP_info_firstplace(gentity_t *ent);
+void SP_info_secondplace(gentity_t *ent);
+void SP_info_thirdplace(gentity_t *ent);
+void SP_info_podium(gentity_t *ent);
 
 void SP_func_plat (gentity_t *ent);
 void SP_func_static (gentity_t *ent);
@@ -145,6 +156,7 @@
 void SP_target_speaker (gentity_t *ent);
 void SP_target_print (gentity_t *ent);
 void SP_target_laser (gentity_t *self);
+void SP_target_character (gentity_t *ent);
 void SP_target_score( gentity_t *ent );
 void SP_target_teleporter( gentity_t *ent );
 void SP_target_relay (gentity_t *ent);
@@ -179,9 +191,7 @@
 void SP_team_redobelisk( gentity_t *ent );
 void SP_team_neutralobelisk( gentity_t *ent );
 #endif
-void SP_item_botroam( gentity_t *ent ) { }
-
-void SP_ignore (gentity_t *ent) { }
+void SP_item_botroam( gentity_t *ent ) {};
 
 spawn_t	spawns[] = {
 	// info entities don't do anything at all, but provide positional
@@ -255,9 +265,8 @@
 	{"team_neutralobelisk", SP_team_neutralobelisk},
 #endif
 	{"item_botroam", SP_item_botroam},
-	{"advertisement", SP_ignore},
 
-	{NULL, 0}
+	{0, 0}
 };
 
 /*
@@ -355,7 +364,7 @@
 			b = (byte *)ent;
 
 			switch( f->type ) {
-			case F_STRING:
+			case F_LSTRING:
 				*(char **)(b+f->ofs) = G_NewString (value);
 				break;
 			case F_VECTOR:
@@ -377,6 +386,7 @@
 				((float *)(b+f->ofs))[2] = 0;
 				break;
 			default:
+			case F_IGNORE:
 				break;
 			}
 			return;
@@ -384,26 +394,22 @@
 	}
 }
 
-#define ADJUST_AREAPORTAL() \
-	if(ent->s.eType == ET_MOVER) \
-	{ \
-		trap_LinkEntity(ent);					\
-		trap_AdjustAreaPortalState(ent, qtrue); \
-	}
+
+
 
 /*
 ===================
 G_SpawnGEntityFromSpawnVars
 
 Spawn an entity and fill in all of the level fields from
-level.spawnVars[], then call the class specific spawn function
+level.spawnVars[], then call the class specfic spawn function
 ===================
 */
 void G_SpawnGEntityFromSpawnVars( void ) {
 	int			i;
 	gentity_t	*ent;
 	char		*s, *value, *gametypeName;
-	static char *gametypeNames[] = { "ffa", "tournament" /* ql now uses 'duel' so you need extra checks */, "race", "team" /* ql now uses 'tdm' so you need extra checks */, "ca", "ctf", "oneflag" /* ql now uses '1f' so you need extra checks */, "obelisk" /* ql now uses 'ob' so you need extra checks */, "harvester" /* ql now uses 'har' so you need extra checks */, "ft", "dom", "ad", "rr", "ntf" /* cpma never used */, "twovstwo" /* cpma never used */, "hm" /* cpma never used */, "single" };
+	static char *gametypeNames[] = {"ffa", "tournament", "single", "team", "ctf", "oneflag", "obelisk", "harvester", "teamtournament"};
 
 	// get the next free entity
 	ent = G_Spawn();
@@ -412,37 +418,10 @@
 		G_ParseField( level.spawnVars[i][0], level.spawnVars[i][1], ent );
 	}
 
-	if (g_ammoPackHack.integer) {
-		// substitute ammo_ with ammo_pack
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			ent->classname = G_NewString("ammo_pack");
-		}
-	} else if (g_ammoPack.integer) {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			// pass, add it
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			// ignore other types of ammo
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	} else {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	}
-
 	// check for "notsingle" flag
 	if ( g_gametype.integer == GT_SINGLE_PLAYER ) {
 		G_SpawnInt( "notsingle", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
@@ -451,137 +430,37 @@
 	if ( g_gametype.integer >= GT_TEAM ) {
 		G_SpawnInt( "notteam", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
 	} else {
 		G_SpawnInt( "notfree", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
 	}
 
-	// quake live addition
-	if (G_SpawnString("not_gametype", NULL, &value)) {
-		qboolean isDigitString;
-		int j;
-
-		// 2019-01-31 older quake live maps used numbers instead of
-		// strings for the gametypes.  Ex (2009 map):
-		//    qzca1.bsp:"not_gametype" "1"
-		//    qzca1.bsp:"not_gametype" "0 2 3 4 5"
-
-		// check for all digit string so you don't trip up with '1f'
-		isDigitString = qtrue;
-		for (j = 0;  j < strlen(value);  j++) {
-			if (!isdigit(value[j])  &&  value[j] != ' ') {
-				isDigitString = qfalse;
-				break;
-			}
-		}
-
-		if (isDigitString) {
-			if (g_gametype.integer >= 0  &&  g_gametype.integer <= 9) {
-				s = strstr(value, g_gametype.string);
-				if (s) {
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			} else {
-				// single player (not valid in ql) or gametypes that didn't exist when map was created (domination, red rover, etc..)
-
-				// pass
-			}
-		} else {  // string
-			if (g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE) {
-				gametypeName = gametypeNames[g_gametype.integer];
-
-				s = strstr(value, gametypeName);
-				if (!s) {
-					// try alternate quake live gametype names
-					if (g_gametype.integer == GT_TEAM) {
-						s = strstr(value, "tdm");
-					} else if (g_gametype.integer == GT_TOURNAMENT) {
-						s = strstr(value, "duel");
-					} else if (g_gametype.integer == GT_HARVESTER) {
-						s = strstr(value, "har");
-					} else if (g_gametype.integer == GT_1FCTF) {
-						s = strstr(value, "1f");
-					} else if (g_gametype.integer == GT_OBELISK) {
-						s = strstr(value, "ob");
-						// 2019-02-02 also 'overload', don't know if this is a map bug
-                        // overgrowth.bsp:"gametype" "harvester, overload"
-                        if (!s) {
-                            s = strstr(value, "overload");
-                        }
-					}
-				}
-
-				if (s) {
-					//G_Printf("skipping item, in not_gametype string: '%s'\n", value);
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			}
-		}
-	}
-
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	G_SpawnInt( "notta", "0", &i );
 	if ( i ) {
-		ADJUST_AREAPORTAL();
 		G_FreeEntity( ent );
 		return;
 	}
 #else
 	G_SpawnInt( "notq3a", "0", &i );
 	if ( i ) {
-		ADJUST_AREAPORTAL();
 		G_FreeEntity( ent );
 		return;
 	}
 #endif
 
 	if( G_SpawnString( "gametype", NULL, &value ) ) {
-		//Com_Printf("^5gametype: %s\n", value);
-
-		// 2019-02-02 quake live sometimes uses comma separated list:
-		//    theoldendomain.bsp:"gametype" "ffa,tournament,single"
-		//    solid.bsp:"gametype" "ffa tdm ft"
-
 		if( g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE ) {
 			gametypeName = gametypeNames[g_gametype.integer];
 
 			s = strstr( value, gametypeName );
 			if( !s ) {
-				// try alternate quake live gametype names
-				if (g_gametype.integer == GT_TEAM) {
-					s = strstr(value, "tdm");
-				} else if (g_gametype.integer == GT_TOURNAMENT) {
-					s = strstr(value, "duel");
-				} else if (g_gametype.integer == GT_HARVESTER) {
-					s = strstr(value, "har");
-				} else if (g_gametype.integer == GT_1FCTF) {
-					s = strstr(value, "1f");
-				} else if (g_gametype.integer == GT_OBELISK) {
-					s = strstr(value, "ob");
-					// 2019-02-02 also 'overload', don't know if this is a map bug
-					// overgrowth.bsp:"gametype" "harvester, overload"
-					if (!s) {
-						s = strstr(value, "overload");
-					}
-				}
-			}
-
-			if (!s) {
-				//G_Printf("skipping item, not in gametype string: '%s'\n", value);
-				ADJUST_AREAPORTAL();
 				G_FreeEntity( ent );
 				return;
 			}
@@ -611,7 +490,7 @@
 
 	l = strlen( string );
 	if ( level.numSpawnVarChars + l + 1 > MAX_SPAWN_VARS_CHARS ) {
-		G_Error( "G_AddSpawnVarToken: MAX_SPAWN_VARS_CHARS" );
+		G_Error( "G_AddSpawnVarToken: MAX_SPAWN_CHARS" );
 	}
 
 	dest = level.spawnVarChars + level.numSpawnVarChars;
@@ -672,9 +551,6 @@
 		}
 		level.spawnVars[ level.numSpawnVars ][0] = G_AddSpawnVarToken( keyname );
 		level.spawnVars[ level.numSpawnVars ][1] = G_AddSpawnVarToken( com_token );
-
-		//Com_Printf("^3'%s' : '%s'\n", level.spawnVars[level.numSpawnVars][0], level.spawnVars[level.numSpawnVars][1]);
-
 		level.numSpawnVars++;
 	}
 
@@ -692,7 +568,6 @@
 */
 void SP_worldspawn( void ) {
 	char	*s;
-	char buf[MAX_QPATH];
 
 	G_SpawnString( "classname", "", &s );
 	if ( Q_stricmp( s, "worldspawn" ) ) {
@@ -700,9 +575,7 @@
 	}
 
 	// make some data visible to connecting client
-	//trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
-	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
-	trap_SetConfigstring(CS_GAME_VERSION, buf);
+	trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
 
 	trap_SetConfigstring( CS_LEVEL_START_TIME, va("%i", level.startTime ) );
 
@@ -712,15 +585,6 @@
 	G_SpawnString( "message", "", &s );
 	trap_SetConfigstring( CS_MESSAGE, s );				// map specific message
 
-	G_SpawnString("author", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR, s);
-	}
-	G_SpawnString("author2", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR2, s);
-	}
-
 	trap_SetConfigstring( CS_MOTD, g_motd.string );		// message of the day
 
 	G_SpawnString( "gravity", "800", &s );
@@ -733,13 +597,8 @@
 	trap_Cvar_Set( "g_enableBreath", s );
 
 	g_entities[ENTITYNUM_WORLD].s.number = ENTITYNUM_WORLD;
-	g_entities[ENTITYNUM_WORLD].r.ownerNum = ENTITYNUM_NONE;
 	g_entities[ENTITYNUM_WORLD].classname = "worldspawn";
 
-	g_entities[ENTITYNUM_NONE].s.number = ENTITYNUM_NONE;
-	g_entities[ENTITYNUM_NONE].r.ownerNum = ENTITYNUM_NONE;
-	g_entities[ENTITYNUM_NONE].classname = "nothing";
-
 	// see if we want a warmup time
 	trap_SetConfigstring( CS_WARMUP, "" );
 	if ( g_restarted.integer ) {
@@ -747,7 +606,7 @@
 		level.warmupTime = 0;
 	} else if ( g_doWarmup.integer ) { // Turn it on
 		level.warmupTime = -1;
-		trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+		trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 		G_LogPrintf( "Warmup:\n" );
 	}
 

```

### `ioquake3`  — sha256 `95ce28caa752...`, 17152 bytes

_Diff stat: +6 / -147 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_spawn.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_spawn.c	2026-04-16 20:02:21.547849900 +0100
@@ -85,7 +85,7 @@
 typedef struct
 {
 	char	*name;
-	size_t		ofs;
+	size_t	ofs;
 	fieldtype_t	type;
 } field_t;
 
@@ -181,8 +181,6 @@
 #endif
 void SP_item_botroam( gentity_t *ent ) { }
 
-void SP_ignore (gentity_t *ent) { }
-
 spawn_t	spawns[] = {
 	// info entities don't do anything at all, but provide positional
 	// information for things controlled by other processes
@@ -255,7 +253,6 @@
 	{"team_neutralobelisk", SP_team_neutralobelisk},
 #endif
 	{"item_botroam", SP_item_botroam},
-	{"advertisement", SP_ignore},
 
 	{NULL, 0}
 };
@@ -376,8 +373,6 @@
 				((float *)(b+f->ofs))[1] = v;
 				((float *)(b+f->ofs))[2] = 0;
 				break;
-			default:
-				break;
 			}
 			return;
 		}
@@ -387,7 +382,7 @@
 #define ADJUST_AREAPORTAL() \
 	if(ent->s.eType == ET_MOVER) \
 	{ \
-		trap_LinkEntity(ent);					\
+		trap_LinkEntity(ent); \
 		trap_AdjustAreaPortalState(ent, qtrue); \
 	}
 
@@ -403,7 +398,7 @@
 	int			i;
 	gentity_t	*ent;
 	char		*s, *value, *gametypeName;
-	static char *gametypeNames[] = { "ffa", "tournament" /* ql now uses 'duel' so you need extra checks */, "race", "team" /* ql now uses 'tdm' so you need extra checks */, "ca", "ctf", "oneflag" /* ql now uses '1f' so you need extra checks */, "obelisk" /* ql now uses 'ob' so you need extra checks */, "harvester" /* ql now uses 'har' so you need extra checks */, "ft", "dom", "ad", "rr", "ntf" /* cpma never used */, "twovstwo" /* cpma never used */, "hm" /* cpma never used */, "single" };
+	static char *gametypeNames[] = {"ffa", "tournament", "single", "team", "ctf", "oneflag", "obelisk", "harvester"};
 
 	// get the next free entity
 	ent = G_Spawn();
@@ -412,32 +407,6 @@
 		G_ParseField( level.spawnVars[i][0], level.spawnVars[i][1], ent );
 	}
 
-	if (g_ammoPackHack.integer) {
-		// substitute ammo_ with ammo_pack
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			ent->classname = G_NewString("ammo_pack");
-		}
-	} else if (g_ammoPack.integer) {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			// pass, add it
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			// ignore other types of ammo
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	} else {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	}
-
 	// check for "notsingle" flag
 	if ( g_gametype.integer == GT_SINGLE_PLAYER ) {
 		G_SpawnInt( "notsingle", "0", &i );
@@ -464,75 +433,7 @@
 		}
 	}
 
-	// quake live addition
-	if (G_SpawnString("not_gametype", NULL, &value)) {
-		qboolean isDigitString;
-		int j;
-
-		// 2019-01-31 older quake live maps used numbers instead of
-		// strings for the gametypes.  Ex (2009 map):
-		//    qzca1.bsp:"not_gametype" "1"
-		//    qzca1.bsp:"not_gametype" "0 2 3 4 5"
-
-		// check for all digit string so you don't trip up with '1f'
-		isDigitString = qtrue;
-		for (j = 0;  j < strlen(value);  j++) {
-			if (!isdigit(value[j])  &&  value[j] != ' ') {
-				isDigitString = qfalse;
-				break;
-			}
-		}
-
-		if (isDigitString) {
-			if (g_gametype.integer >= 0  &&  g_gametype.integer <= 9) {
-				s = strstr(value, g_gametype.string);
-				if (s) {
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			} else {
-				// single player (not valid in ql) or gametypes that didn't exist when map was created (domination, red rover, etc..)
-
-				// pass
-			}
-		} else {  // string
-			if (g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE) {
-				gametypeName = gametypeNames[g_gametype.integer];
-
-				s = strstr(value, gametypeName);
-				if (!s) {
-					// try alternate quake live gametype names
-					if (g_gametype.integer == GT_TEAM) {
-						s = strstr(value, "tdm");
-					} else if (g_gametype.integer == GT_TOURNAMENT) {
-						s = strstr(value, "duel");
-					} else if (g_gametype.integer == GT_HARVESTER) {
-						s = strstr(value, "har");
-					} else if (g_gametype.integer == GT_1FCTF) {
-						s = strstr(value, "1f");
-					} else if (g_gametype.integer == GT_OBELISK) {
-						s = strstr(value, "ob");
-						// 2019-02-02 also 'overload', don't know if this is a map bug
-                        // overgrowth.bsp:"gametype" "harvester, overload"
-                        if (!s) {
-                            s = strstr(value, "overload");
-                        }
-					}
-				}
-
-				if (s) {
-					//G_Printf("skipping item, in not_gametype string: '%s'\n", value);
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			}
-		}
-	}
-
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	G_SpawnInt( "notta", "0", &i );
 	if ( i ) {
 		ADJUST_AREAPORTAL();
@@ -549,38 +450,11 @@
 #endif
 
 	if( G_SpawnString( "gametype", NULL, &value ) ) {
-		//Com_Printf("^5gametype: %s\n", value);
-
-		// 2019-02-02 quake live sometimes uses comma separated list:
-		//    theoldendomain.bsp:"gametype" "ffa,tournament,single"
-		//    solid.bsp:"gametype" "ffa tdm ft"
-
 		if( g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE ) {
 			gametypeName = gametypeNames[g_gametype.integer];
 
 			s = strstr( value, gametypeName );
 			if( !s ) {
-				// try alternate quake live gametype names
-				if (g_gametype.integer == GT_TEAM) {
-					s = strstr(value, "tdm");
-				} else if (g_gametype.integer == GT_TOURNAMENT) {
-					s = strstr(value, "duel");
-				} else if (g_gametype.integer == GT_HARVESTER) {
-					s = strstr(value, "har");
-				} else if (g_gametype.integer == GT_1FCTF) {
-					s = strstr(value, "1f");
-				} else if (g_gametype.integer == GT_OBELISK) {
-					s = strstr(value, "ob");
-					// 2019-02-02 also 'overload', don't know if this is a map bug
-					// overgrowth.bsp:"gametype" "harvester, overload"
-					if (!s) {
-						s = strstr(value, "overload");
-					}
-				}
-			}
-
-			if (!s) {
-				//G_Printf("skipping item, not in gametype string: '%s'\n", value);
 				ADJUST_AREAPORTAL();
 				G_FreeEntity( ent );
 				return;
@@ -672,9 +546,6 @@
 		}
 		level.spawnVars[ level.numSpawnVars ][0] = G_AddSpawnVarToken( keyname );
 		level.spawnVars[ level.numSpawnVars ][1] = G_AddSpawnVarToken( com_token );
-
-		//Com_Printf("^3'%s' : '%s'\n", level.spawnVars[level.numSpawnVars][0], level.spawnVars[level.numSpawnVars][1]);
-
 		level.numSpawnVars++;
 	}
 
@@ -692,7 +563,6 @@
 */
 void SP_worldspawn( void ) {
 	char	*s;
-	char buf[MAX_QPATH];
 
 	G_SpawnString( "classname", "", &s );
 	if ( Q_stricmp( s, "worldspawn" ) ) {
@@ -700,9 +570,7 @@
 	}
 
 	// make some data visible to connecting client
-	//trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
-	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
-	trap_SetConfigstring(CS_GAME_VERSION, buf);
+	trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
 
 	trap_SetConfigstring( CS_LEVEL_START_TIME, va("%i", level.startTime ) );
 
@@ -712,15 +580,6 @@
 	G_SpawnString( "message", "", &s );
 	trap_SetConfigstring( CS_MESSAGE, s );				// map specific message
 
-	G_SpawnString("author", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR, s);
-	}
-	G_SpawnString("author2", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR2, s);
-	}
-
 	trap_SetConfigstring( CS_MOTD, g_motd.string );		// message of the day
 
 	G_SpawnString( "gravity", "800", &s );
@@ -747,7 +606,7 @@
 		level.warmupTime = 0;
 	} else if ( g_doWarmup.integer ) { // Turn it on
 		level.warmupTime = -1;
-		trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+		trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 		G_LogPrintf( "Warmup:\n" );
 	}
 

```

### `openarena-engine`  — sha256 `0d9324404ec5...`, 17151 bytes

_Diff stat: +7 / -148 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_spawn.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_spawn.c	2026-04-16 22:48:25.750042300 +0100
@@ -85,7 +85,7 @@
 typedef struct
 {
 	char	*name;
-	size_t		ofs;
+	size_t	ofs;
 	fieldtype_t	type;
 } field_t;
 
@@ -181,8 +181,6 @@
 #endif
 void SP_item_botroam( gentity_t *ent ) { }
 
-void SP_ignore (gentity_t *ent) { }
-
 spawn_t	spawns[] = {
 	// info entities don't do anything at all, but provide positional
 	// information for things controlled by other processes
@@ -255,7 +253,6 @@
 	{"team_neutralobelisk", SP_team_neutralobelisk},
 #endif
 	{"item_botroam", SP_item_botroam},
-	{"advertisement", SP_ignore},
 
 	{NULL, 0}
 };
@@ -376,8 +373,6 @@
 				((float *)(b+f->ofs))[1] = v;
 				((float *)(b+f->ofs))[2] = 0;
 				break;
-			default:
-				break;
 			}
 			return;
 		}
@@ -387,7 +382,7 @@
 #define ADJUST_AREAPORTAL() \
 	if(ent->s.eType == ET_MOVER) \
 	{ \
-		trap_LinkEntity(ent);					\
+		trap_LinkEntity(ent); \
 		trap_AdjustAreaPortalState(ent, qtrue); \
 	}
 
@@ -396,14 +391,14 @@
 G_SpawnGEntityFromSpawnVars
 
 Spawn an entity and fill in all of the level fields from
-level.spawnVars[], then call the class specific spawn function
+level.spawnVars[], then call the class specfic spawn function
 ===================
 */
 void G_SpawnGEntityFromSpawnVars( void ) {
 	int			i;
 	gentity_t	*ent;
 	char		*s, *value, *gametypeName;
-	static char *gametypeNames[] = { "ffa", "tournament" /* ql now uses 'duel' so you need extra checks */, "race", "team" /* ql now uses 'tdm' so you need extra checks */, "ca", "ctf", "oneflag" /* ql now uses '1f' so you need extra checks */, "obelisk" /* ql now uses 'ob' so you need extra checks */, "harvester" /* ql now uses 'har' so you need extra checks */, "ft", "dom", "ad", "rr", "ntf" /* cpma never used */, "twovstwo" /* cpma never used */, "hm" /* cpma never used */, "single" };
+	static char *gametypeNames[] = {"ffa", "tournament", "single", "team", "ctf", "oneflag", "obelisk", "harvester"};
 
 	// get the next free entity
 	ent = G_Spawn();
@@ -412,32 +407,6 @@
 		G_ParseField( level.spawnVars[i][0], level.spawnVars[i][1], ent );
 	}
 
-	if (g_ammoPackHack.integer) {
-		// substitute ammo_ with ammo_pack
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			ent->classname = G_NewString("ammo_pack");
-		}
-	} else if (g_ammoPack.integer) {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			// pass, add it
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			// ignore other types of ammo
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	} else {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	}
-
 	// check for "notsingle" flag
 	if ( g_gametype.integer == GT_SINGLE_PLAYER ) {
 		G_SpawnInt( "notsingle", "0", &i );
@@ -464,75 +433,7 @@
 		}
 	}
 
-	// quake live addition
-	if (G_SpawnString("not_gametype", NULL, &value)) {
-		qboolean isDigitString;
-		int j;
-
-		// 2019-01-31 older quake live maps used numbers instead of
-		// strings for the gametypes.  Ex (2009 map):
-		//    qzca1.bsp:"not_gametype" "1"
-		//    qzca1.bsp:"not_gametype" "0 2 3 4 5"
-
-		// check for all digit string so you don't trip up with '1f'
-		isDigitString = qtrue;
-		for (j = 0;  j < strlen(value);  j++) {
-			if (!isdigit(value[j])  &&  value[j] != ' ') {
-				isDigitString = qfalse;
-				break;
-			}
-		}
-
-		if (isDigitString) {
-			if (g_gametype.integer >= 0  &&  g_gametype.integer <= 9) {
-				s = strstr(value, g_gametype.string);
-				if (s) {
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			} else {
-				// single player (not valid in ql) or gametypes that didn't exist when map was created (domination, red rover, etc..)
-
-				// pass
-			}
-		} else {  // string
-			if (g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE) {
-				gametypeName = gametypeNames[g_gametype.integer];
-
-				s = strstr(value, gametypeName);
-				if (!s) {
-					// try alternate quake live gametype names
-					if (g_gametype.integer == GT_TEAM) {
-						s = strstr(value, "tdm");
-					} else if (g_gametype.integer == GT_TOURNAMENT) {
-						s = strstr(value, "duel");
-					} else if (g_gametype.integer == GT_HARVESTER) {
-						s = strstr(value, "har");
-					} else if (g_gametype.integer == GT_1FCTF) {
-						s = strstr(value, "1f");
-					} else if (g_gametype.integer == GT_OBELISK) {
-						s = strstr(value, "ob");
-						// 2019-02-02 also 'overload', don't know if this is a map bug
-                        // overgrowth.bsp:"gametype" "harvester, overload"
-                        if (!s) {
-                            s = strstr(value, "overload");
-                        }
-					}
-				}
-
-				if (s) {
-					//G_Printf("skipping item, in not_gametype string: '%s'\n", value);
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			}
-		}
-	}
-
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	G_SpawnInt( "notta", "0", &i );
 	if ( i ) {
 		ADJUST_AREAPORTAL();
@@ -549,38 +450,11 @@
 #endif
 
 	if( G_SpawnString( "gametype", NULL, &value ) ) {
-		//Com_Printf("^5gametype: %s\n", value);
-
-		// 2019-02-02 quake live sometimes uses comma separated list:
-		//    theoldendomain.bsp:"gametype" "ffa,tournament,single"
-		//    solid.bsp:"gametype" "ffa tdm ft"
-
 		if( g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE ) {
 			gametypeName = gametypeNames[g_gametype.integer];
 
 			s = strstr( value, gametypeName );
 			if( !s ) {
-				// try alternate quake live gametype names
-				if (g_gametype.integer == GT_TEAM) {
-					s = strstr(value, "tdm");
-				} else if (g_gametype.integer == GT_TOURNAMENT) {
-					s = strstr(value, "duel");
-				} else if (g_gametype.integer == GT_HARVESTER) {
-					s = strstr(value, "har");
-				} else if (g_gametype.integer == GT_1FCTF) {
-					s = strstr(value, "1f");
-				} else if (g_gametype.integer == GT_OBELISK) {
-					s = strstr(value, "ob");
-					// 2019-02-02 also 'overload', don't know if this is a map bug
-					// overgrowth.bsp:"gametype" "harvester, overload"
-					if (!s) {
-						s = strstr(value, "overload");
-					}
-				}
-			}
-
-			if (!s) {
-				//G_Printf("skipping item, not in gametype string: '%s'\n", value);
 				ADJUST_AREAPORTAL();
 				G_FreeEntity( ent );
 				return;
@@ -672,9 +546,6 @@
 		}
 		level.spawnVars[ level.numSpawnVars ][0] = G_AddSpawnVarToken( keyname );
 		level.spawnVars[ level.numSpawnVars ][1] = G_AddSpawnVarToken( com_token );
-
-		//Com_Printf("^3'%s' : '%s'\n", level.spawnVars[level.numSpawnVars][0], level.spawnVars[level.numSpawnVars][1]);
-
 		level.numSpawnVars++;
 	}
 
@@ -692,7 +563,6 @@
 */
 void SP_worldspawn( void ) {
 	char	*s;
-	char buf[MAX_QPATH];
 
 	G_SpawnString( "classname", "", &s );
 	if ( Q_stricmp( s, "worldspawn" ) ) {
@@ -700,9 +570,7 @@
 	}
 
 	// make some data visible to connecting client
-	//trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
-	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
-	trap_SetConfigstring(CS_GAME_VERSION, buf);
+	trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
 
 	trap_SetConfigstring( CS_LEVEL_START_TIME, va("%i", level.startTime ) );
 
@@ -712,15 +580,6 @@
 	G_SpawnString( "message", "", &s );
 	trap_SetConfigstring( CS_MESSAGE, s );				// map specific message
 
-	G_SpawnString("author", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR, s);
-	}
-	G_SpawnString("author2", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR2, s);
-	}
-
 	trap_SetConfigstring( CS_MOTD, g_motd.string );		// message of the day
 
 	G_SpawnString( "gravity", "800", &s );
@@ -747,7 +606,7 @@
 		level.warmupTime = 0;
 	} else if ( g_doWarmup.integer ) { // Turn it on
 		level.warmupTime = -1;
-		trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+		trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 		G_LogPrintf( "Warmup:\n" );
 	}
 

```

### `openarena-gamecode`  — sha256 `3e20da0c206d...`, 19146 bytes

_Diff stat: +101 / -189 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_spawn.c	2026-04-16 20:02:25.198157000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_spawn.c	2026-04-16 22:48:24.174987100 +0100
@@ -32,7 +32,7 @@
 	}
 
 	for ( i = 0 ; i < level.numSpawnVars ; i++ ) {
-		if ( !Q_stricmp( key, level.spawnVars[i][0] ) ) {
+		if ( Q_strequal( key, level.spawnVars[i][0] ) ) {
 			*out = level.spawnVars[i][1];
 			return qtrue;
 		}
@@ -75,40 +75,47 @@
 // fields are needed for spawning from the entity string
 //
 typedef enum {
-	F_INT,
+	F_INT, 
 	F_FLOAT,
-	F_STRING,
+	F_LSTRING,			// string on disk, pointer in memory, TAG_LEVEL
+	F_GSTRING,			// string on disk, pointer in memory, TAG_GAME
 	F_VECTOR,
-	F_ANGLEHACK
+	F_ANGLEHACK,
+	F_ENTITY,			// index on disk, pointer in memory
+	F_ITEM,				// index on disk, pointer in memory
+	F_CLIENT,			// index on disk, pointer in memory
+	F_IGNORE
 } fieldtype_t;
 
 typedef struct
 {
 	char	*name;
-	size_t		ofs;
+	int		ofs;
 	fieldtype_t	type;
+//	int		flags;
 } field_t;
 
 field_t fields[] = {
-	{"classname", FOFS(classname), F_STRING},
+	{"classname", FOFS(classname), F_LSTRING},
 	{"origin", FOFS(s.origin), F_VECTOR},
-	{"model", FOFS(model), F_STRING},
-	{"model2", FOFS(model2), F_STRING},
+	{"model", FOFS(model), F_LSTRING},
+	{"model2", FOFS(model2), F_LSTRING},
 	{"spawnflags", FOFS(spawnflags), F_INT},
 	{"speed", FOFS(speed), F_FLOAT},
-	{"target", FOFS(target), F_STRING},
-	{"targetname", FOFS(targetname), F_STRING},
-	{"message", FOFS(message), F_STRING},
-	{"team", FOFS(team), F_STRING},
+	{"target", FOFS(target), F_LSTRING},
+	{"targetname", FOFS(targetname), F_LSTRING},
+	{"message", FOFS(message), F_LSTRING},
+	{"team", FOFS(team), F_LSTRING},
 	{"wait", FOFS(wait), F_FLOAT},
 	{"random", FOFS(random), F_FLOAT},
 	{"count", FOFS(count), F_INT},
 	{"health", FOFS(health), F_INT},
+	{"light", 0, F_IGNORE},
 	{"dmg", FOFS(damage), F_INT},
 	{"angles", FOFS(s.angles), F_VECTOR},
 	{"angle", FOFS(s.angles), F_ANGLEHACK},
-	{"targetShaderName", FOFS(targetShaderName), F_STRING},
-	{"targetShaderNewName", FOFS(targetShaderNewName), F_STRING},
+	{"targetShaderName", FOFS(targetShaderName), F_LSTRING},
+	{"targetShaderNewName", FOFS(targetShaderNewName), F_LSTRING},
 
 	{NULL}
 };
@@ -122,6 +129,13 @@
 void SP_info_player_start (gentity_t *ent);
 void SP_info_player_deathmatch (gentity_t *ent);
 void SP_info_player_intermission (gentity_t *ent);
+//standard domination:
+void SP_domination_point ( gentity_t *ent);
+
+void SP_info_firstplace(gentity_t *ent);
+void SP_info_secondplace(gentity_t *ent);
+void SP_info_thirdplace(gentity_t *ent);
+void SP_info_podium(gentity_t *ent);
 
 void SP_func_plat (gentity_t *ent);
 void SP_func_static (gentity_t *ent);
@@ -145,6 +159,7 @@
 void SP_target_speaker (gentity_t *ent);
 void SP_target_print (gentity_t *ent);
 void SP_target_laser (gentity_t *self);
+void SP_target_character (gentity_t *ent);
 void SP_target_score( gentity_t *ent );
 void SP_target_teleporter( gentity_t *ent );
 void SP_target_relay (gentity_t *ent);
@@ -174,14 +189,11 @@
 void SP_team_CTF_redspawn( gentity_t *ent );
 void SP_team_CTF_bluespawn( gentity_t *ent );
 
-#ifdef MISSIONPACK
 void SP_team_blueobelisk( gentity_t *ent );
 void SP_team_redobelisk( gentity_t *ent );
 void SP_team_neutralobelisk( gentity_t *ent );
-#endif
-void SP_item_botroam( gentity_t *ent ) { }
 
-void SP_ignore (gentity_t *ent) { }
+void SP_item_botroam( gentity_t *ent ) { }
 
 spawn_t	spawns[] = {
 	// info entities don't do anything at all, but provide positional
@@ -189,6 +201,16 @@
 	{"info_player_start", SP_info_player_start},
 	{"info_player_deathmatch", SP_info_player_deathmatch},
 	{"info_player_intermission", SP_info_player_intermission},
+//Double Domination player spawn:
+	{"info_player_dd", SP_info_player_deathmatch},
+	{"info_player_dd_red", SP_info_player_deathmatch},
+	{"info_player_dd_blue", SP_info_player_deathmatch},
+//Standard Domination point spawn:
+	{"domination_point", SP_domination_point},
+	{"info_player_dom_red", SP_info_player_deathmatch},
+	{"info_player_dom_blue", SP_info_player_deathmatch},
+
+
 	{"info_null", SP_info_null},
 	{"info_notnull", SP_info_notnull},		// use target_position instead
 	{"info_camp", SP_info_camp},
@@ -249,13 +271,11 @@
 	{"team_CTF_redspawn", SP_team_CTF_redspawn},
 	{"team_CTF_bluespawn", SP_team_CTF_bluespawn},
 
-#ifdef MISSIONPACK
 	{"team_redobelisk", SP_team_redobelisk},
 	{"team_blueobelisk", SP_team_blueobelisk},
 	{"team_neutralobelisk", SP_team_neutralobelisk},
-#endif
+
 	{"item_botroam", SP_item_botroam},
-	{"advertisement", SP_ignore},
 
 	{NULL, 0}
 };
@@ -271,15 +291,28 @@
 qboolean G_CallSpawn( gentity_t *ent ) {
 	spawn_t	*s;
 	gitem_t	*item;
+	char cvarname[128];
+	char itemname[128];
+
+		//Construct a replace cvar:
+	Com_sprintf(cvarname, sizeof(cvarname), "replace_%s", ent->classname);
+
+		//Look an alternative item up:
+		trap_Cvar_VariableStringBuffer(cvarname,itemname,sizeof(itemname));
+		if(itemname[0]==0) //If nothing found use original
+			Com_sprintf(itemname, sizeof(itemname), "%s", ent->classname);
+		else
+			G_Printf ("%s replaced by %s\n", ent->classname, itemname);
 
-	if ( !ent->classname ) {
+
+	if ( itemname[0]==0) {
 		G_Printf ("G_CallSpawn: NULL classname\n");
 		return qfalse;
 	}
 
 	// check item spawn functions
 	for ( item=bg_itemlist+1 ; item->classname ; item++ ) {
-		if ( !strcmp(item->classname, ent->classname) ) {
+		if ( strequals(item->classname, itemname) ) {
 			G_SpawnItem( ent, item );
 			return qtrue;
 		}
@@ -287,13 +320,13 @@
 
 	// check normal spawn functions
 	for ( s=spawns ; s->name ; s++ ) {
-		if ( !strcmp(s->name, ent->classname) ) {
+		if ( strequals(s->name, itemname) ) {
 			// found it
 			s->spawn(ent);
 			return qtrue;
 		}
 	}
-	G_Printf ("%s doesn't have a spawn function\n", ent->classname);
+	G_Printf ("%s doesn't have a spawn function\n", itemname);
 	return qfalse;
 }
 
@@ -310,14 +343,14 @@
 	int		i,l;
 	
 	l = strlen(string) + 1;
-
-	newb = G_Alloc( l );
+	//KK-OAX Changed to Tremulous's BG_Alloc
+	newb = BG_Alloc( l );
 
 	new_p = newb;
 
 	// turn \n into a real linefeed
 	for ( i=0 ; i< l ; i++ ) {
-		if (string[i] == '\\' && i < l-1) {
+		if ((i < l-1) && (string[i] == '\\')) {
 			i++;
 			if (string[i] == 'n') {
 				*new_p++ = '\n';
@@ -350,12 +383,12 @@
 	vec3_t	vec;
 
 	for ( f=fields ; f->name ; f++ ) {
-		if ( !Q_stricmp(f->name, key) ) {
+		if ( Q_strequal(f->name, key) ) {
 			// found it
 			b = (byte *)ent;
 
 			switch( f->type ) {
-			case F_STRING:
+			case F_LSTRING:
 				*(char **)(b+f->ofs) = G_NewString (value);
 				break;
 			case F_VECTOR:
@@ -377,6 +410,7 @@
 				((float *)(b+f->ofs))[2] = 0;
 				break;
 			default:
+			case F_IGNORE:
 				break;
 			}
 			return;
@@ -384,26 +418,23 @@
 	}
 }
 
-#define ADJUST_AREAPORTAL() \
-	if(ent->s.eType == ET_MOVER) \
-	{ \
-		trap_LinkEntity(ent);					\
-		trap_AdjustAreaPortalState(ent, qtrue); \
-	}
+
+
 
 /*
 ===================
 G_SpawnGEntityFromSpawnVars
 
 Spawn an entity and fill in all of the level fields from
-level.spawnVars[], then call the class specific spawn function
+level.spawnVars[], then call the class specfic spawn function
 ===================
 */
 void G_SpawnGEntityFromSpawnVars( void ) {
 	int			i;
 	gentity_t	*ent;
 	char		*s, *value, *gametypeName;
-	static char *gametypeNames[] = { "ffa", "tournament" /* ql now uses 'duel' so you need extra checks */, "race", "team" /* ql now uses 'tdm' so you need extra checks */, "ca", "ctf", "oneflag" /* ql now uses '1f' so you need extra checks */, "obelisk" /* ql now uses 'ob' so you need extra checks */, "harvester" /* ql now uses 'har' so you need extra checks */, "ft", "dom", "ad", "rr", "ntf" /* cpma never used */, "twovstwo" /* cpma never used */, "hm" /* cpma never used */, "single" };
+	static char *gametypeNames[] = {"ffa", "tournament", "single", "team", "ctf", "oneflag", "obelisk", "harvester", 
+	"elimination", "ctf", "lms", "dd", "dom", "pos"};
 
 	// get the next free entity
 	ent = G_Spawn();
@@ -412,176 +443,62 @@
 		G_ParseField( level.spawnVars[i][0], level.spawnVars[i][1], ent );
 	}
 
-	if (g_ammoPackHack.integer) {
-		// substitute ammo_ with ammo_pack
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			ent->classname = G_NewString("ammo_pack");
-		}
-	} else if (g_ammoPack.integer) {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			// pass, add it
-		} else if (!Q_stricmpn(ent->classname, "ammo_", 5)) {
-			// ignore other types of ammo
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	} else {
-		if (!Q_stricmp(ent->classname, "ammo_pack")) {
-			ADJUST_AREAPORTAL();
-			G_FreeEntity( ent );
-			return;
-		}
-	}
-
 	// check for "notsingle" flag
 	if ( g_gametype.integer == GT_SINGLE_PLAYER ) {
 		G_SpawnInt( "notsingle", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
 	}
 	// check for "notteam" flag (GT_FFA, GT_TOURNAMENT, GT_SINGLE_PLAYER)
-	if ( g_gametype.integer >= GT_TEAM ) {
+	if ( g_gametype.integer >= GT_TEAM && !g_ffa_gt ) {
+/*	if ( g_gametype.integer!=GT_FFA && g_gametype.integer!=GT_TOURNAMENT && g_gametype.integer!=GT_LMS && g_gametype.integer!=GT_POSSESSION ) { */
 		G_SpawnInt( "notteam", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
 	} else {
 		G_SpawnInt( "notfree", "0", &i );
 		if ( i ) {
-			ADJUST_AREAPORTAL();
 			G_FreeEntity( ent );
 			return;
 		}
 	}
 
-	// quake live addition
-	if (G_SpawnString("not_gametype", NULL, &value)) {
-		qboolean isDigitString;
-		int j;
-
-		// 2019-01-31 older quake live maps used numbers instead of
-		// strings for the gametypes.  Ex (2009 map):
-		//    qzca1.bsp:"not_gametype" "1"
-		//    qzca1.bsp:"not_gametype" "0 2 3 4 5"
-
-		// check for all digit string so you don't trip up with '1f'
-		isDigitString = qtrue;
-		for (j = 0;  j < strlen(value);  j++) {
-			if (!isdigit(value[j])  &&  value[j] != ' ') {
-				isDigitString = qfalse;
-				break;
-			}
-		}
-
-		if (isDigitString) {
-			if (g_gametype.integer >= 0  &&  g_gametype.integer <= 9) {
-				s = strstr(value, g_gametype.string);
-				if (s) {
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			} else {
-				// single player (not valid in ql) or gametypes that didn't exist when map was created (domination, red rover, etc..)
-
-				// pass
-			}
-		} else {  // string
-			if (g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE) {
-				gametypeName = gametypeNames[g_gametype.integer];
-
-				s = strstr(value, gametypeName);
-				if (!s) {
-					// try alternate quake live gametype names
-					if (g_gametype.integer == GT_TEAM) {
-						s = strstr(value, "tdm");
-					} else if (g_gametype.integer == GT_TOURNAMENT) {
-						s = strstr(value, "duel");
-					} else if (g_gametype.integer == GT_HARVESTER) {
-						s = strstr(value, "har");
-					} else if (g_gametype.integer == GT_1FCTF) {
-						s = strstr(value, "1f");
-					} else if (g_gametype.integer == GT_OBELISK) {
-						s = strstr(value, "ob");
-						// 2019-02-02 also 'overload', don't know if this is a map bug
-                        // overgrowth.bsp:"gametype" "harvester, overload"
-                        if (!s) {
-                            s = strstr(value, "overload");
-                        }
-					}
-				}
-
-				if (s) {
-					//G_Printf("skipping item, in not_gametype string: '%s'\n", value);
-					ADJUST_AREAPORTAL();
-					G_FreeEntity(ent);
-					return;
-				}
-			}
-		}
-	}
-
-
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	G_SpawnInt( "notta", "0", &i );
 	if ( i ) {
-		ADJUST_AREAPORTAL();
 		G_FreeEntity( ent );
 		return;
 	}
 #else
 	G_SpawnInt( "notq3a", "0", &i );
 	if ( i ) {
-		ADJUST_AREAPORTAL();
 		G_FreeEntity( ent );
 		return;
 	}
 #endif
 
-	if( G_SpawnString( "gametype", NULL, &value ) ) {
-		//Com_Printf("^5gametype: %s\n", value);
+	if( G_SpawnString( "!gametype", NULL, &value ) ) {
+		if( g_gametype.integer >= GT_FFA && g_gametype.integer < ARRAY_LEN(gametypeNames) ) {
+			gametypeName = gametypeNames[g_gametype.integer];
 
-		// 2019-02-02 quake live sometimes uses comma separated list:
-		//    theoldendomain.bsp:"gametype" "ffa,tournament,single"
-		//    solid.bsp:"gametype" "ffa tdm ft"
+			s = strstr( value, gametypeName );
+			if( s ) {
+				G_FreeEntity( ent );
+				return;
+			}
+		}
+	}
 
-		if( g_gametype.integer >= GT_FFA && g_gametype.integer < GT_MAX_GAME_TYPE ) {
+	if( G_SpawnString( "gametype", NULL, &value ) ) {
+		if( g_gametype.integer >= GT_FFA && g_gametype.integer < ARRAY_LEN(gametypeNames) ) {
 			gametypeName = gametypeNames[g_gametype.integer];
 
 			s = strstr( value, gametypeName );
 			if( !s ) {
-				// try alternate quake live gametype names
-				if (g_gametype.integer == GT_TEAM) {
-					s = strstr(value, "tdm");
-				} else if (g_gametype.integer == GT_TOURNAMENT) {
-					s = strstr(value, "duel");
-				} else if (g_gametype.integer == GT_HARVESTER) {
-					s = strstr(value, "har");
-				} else if (g_gametype.integer == GT_1FCTF) {
-					s = strstr(value, "1f");
-				} else if (g_gametype.integer == GT_OBELISK) {
-					s = strstr(value, "ob");
-					// 2019-02-02 also 'overload', don't know if this is a map bug
-					// overgrowth.bsp:"gametype" "harvester, overload"
-					if (!s) {
-						s = strstr(value, "overload");
-					}
-				}
-			}
-
-			if (!s) {
-				//G_Printf("skipping item, not in gametype string: '%s'\n", value);
-				ADJUST_AREAPORTAL();
 				G_FreeEntity( ent );
 				return;
 			}
@@ -611,7 +528,7 @@
 
 	l = strlen( string );
 	if ( level.numSpawnVarChars + l + 1 > MAX_SPAWN_VARS_CHARS ) {
-		G_Error( "G_AddSpawnVarToken: MAX_SPAWN_VARS_CHARS" );
+		G_Error( "G_AddSpawnVarToken: MAX_SPAWN_VARS" );
 	}
 
 	dest = level.spawnVarChars + level.numSpawnVarChars;
@@ -672,9 +589,6 @@
 		}
 		level.spawnVars[ level.numSpawnVars ][0] = G_AddSpawnVarToken( keyname );
 		level.spawnVars[ level.numSpawnVars ][1] = G_AddSpawnVarToken( com_token );
-
-		//Com_Printf("^3'%s' : '%s'\n", level.spawnVars[level.numSpawnVars][0], level.spawnVars[level.numSpawnVars][1]);
-
 		level.numSpawnVars++;
 	}
 
@@ -692,46 +606,44 @@
 */
 void SP_worldspawn( void ) {
 	char	*s;
-	char buf[MAX_QPATH];
 
 	G_SpawnString( "classname", "", &s );
-	if ( Q_stricmp( s, "worldspawn" ) ) {
+	if ( !Q_strequal( s, "worldspawn" ) ) {
 		G_Error( "SP_worldspawn: The first entity isn't 'worldspawn'" );
 	}
 
 	// make some data visible to connecting client
-	//trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
-	trap_Cvar_VariableStringBuffer("fs_game", buf, sizeof(buf));
-	trap_SetConfigstring(CS_GAME_VERSION, buf);
+	trap_SetConfigstring( CS_GAME_VERSION, GAME_VERSION );
 
 	trap_SetConfigstring( CS_LEVEL_START_TIME, va("%i", level.startTime ) );
 
-	G_SpawnString( "music", "", &s );
-	trap_SetConfigstring( CS_MUSIC, s );
-
+	if ( *g_music.string && !Q_strequal( g_music.string, "none" ) ) {
+		trap_SetConfigstring( CS_MUSIC, g_music.string );
+	} else {
+		G_SpawnString( "music", "", &s );   
+		trap_SetConfigstring( CS_MUSIC, s );
+	}
+    
 	G_SpawnString( "message", "", &s );
 	trap_SetConfigstring( CS_MESSAGE, s );				// map specific message
 
-	G_SpawnString("author", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR, s);
-	}
-	G_SpawnString("author2", "", &s);
-	if (s  &&  *s) {
-		trap_SetConfigstring(CS91_AUTHOR2, s);
-	}
-
 	trap_SetConfigstring( CS_MOTD, g_motd.string );		// message of the day
 
 	G_SpawnString( "gravity", "800", &s );
 	trap_Cvar_Set( "g_gravity", s );
 
+	G_SpawnString( "enableFS", "0", &s );
+	trap_Cvar_Set( "g_enableFS", s );
+
 	G_SpawnString( "enableDust", "0", &s );
 	trap_Cvar_Set( "g_enableDust", s );
 
 	G_SpawnString( "enableBreath", "0", &s );
 	trap_Cvar_Set( "g_enableBreath", s );
 
+	G_SpawnString( "enableQ", "0", &s );
+	trap_Cvar_Set( "g_enableQ", s );
+
 	g_entities[ENTITYNUM_WORLD].s.number = ENTITYNUM_WORLD;
 	g_entities[ENTITYNUM_WORLD].r.ownerNum = ENTITYNUM_NONE;
 	g_entities[ENTITYNUM_WORLD].classname = "worldspawn";
@@ -747,7 +659,7 @@
 		level.warmupTime = 0;
 	} else if ( g_doWarmup.integer ) { // Turn it on
 		level.warmupTime = -1;
-		trap_SetConfigstring( CS_WARMUP, va("\\time\\%i", level.warmupTime) );
+		trap_SetConfigstring( CS_WARMUP, va("%i", level.warmupTime) );
 		G_LogPrintf( "Warmup:\n" );
 	}
 

```
