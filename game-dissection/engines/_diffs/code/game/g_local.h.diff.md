# Diff: `code/game/g_local.h`
**Canonical:** `wolfcamql-src` (sha256 `d1a1ad993174...`, 35859 bytes)

## Variants

### `quake3-source`  — sha256 `10ad6b773202...`, 35517 bytes

_Diff stat: +49 / -47 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_local.h	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_local.h	2026-04-16 20:02:19.906577000 +0100
@@ -15,21 +15,21 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 //
 // g_local.h -- local definitions for game module
 
-#include "../qcommon/q_shared.h"
+#include "q_shared.h"
 #include "bg_public.h"
 #include "g_public.h"
 
 //==================================================================
 
 // the "gameversion" client command will print this plus compile date
-#define	GAMEVERSION	BASEGAME
+#define	GAMEVERSION	"baseq3"
 
 #define BODY_QUEUE_SIZE		8
 
@@ -45,7 +45,7 @@
 // gentity->flags
 #define	FL_GODMODE				0x00000010
 #define	FL_NOTARGET				0x00000020
-#define	FL_TEAMMEMBER			0x00000400	// not the first on the team
+#define	FL_TEAMSLAVE			0x00000400	// not the first on the team
 #define FL_NO_KNOCKBACK			0x00000800
 #define FL_DROPPED_ITEM			0x00001000
 #define FL_NO_BOTS				0x00002000	// spawn point not for bot use
@@ -118,6 +118,7 @@
 
 	int			timestamp;		// body queue sinking, etc
 
+	float		angle;			// set in editor, -1 = up, -2 = down
 	char		*target;
 	char		*targetname;
 	char		*team;
@@ -159,7 +160,7 @@
 	gentity_t	*teamchain;		// next entity in team
 	gentity_t	*teammaster;	// master of the team
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			kamikazeTime;
 	int			kamikazeShockTime;
 #endif
@@ -213,13 +214,18 @@
 	float		lastfraggedcarrier;
 } playerTeamState_t;
 
+// the auto following clients don't follow a specific client
+// number, but instead follow the first two active players
+#define	FOLLOW_ACTIVE1	-1
+#define	FOLLOW_ACTIVE2	-2
+
 // client data that stays across multiple levels or tournament restarts
 // this is achieved by writing all the data to cvar strings at game shutdown
 // time and reading them back at connection time.  Anything added here
 // MUST be dealt with in G_InitSessionData() / G_ReadSessionData() / G_WriteSessionData()
 typedef struct {
 	team_t		sessionTeam;
-	int                     spectatorNum;           // for determining next-in-line to play
+	int			spectatorTime;		// for determining next-in-line to play
 	spectatorState_t	spectatorState;
 	int			spectatorClient;	// for chasecam and follow mode
 	int			wins, losses;		// tournament stats
@@ -309,10 +315,10 @@
 	// like health / armor countdowns and regeneration
 	int			timeResidual;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	gentity_t	*persistantPowerup;
 	int			portalID;
-	int			ammoTimes[WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS];
+	int			ammoTimes[WP_NUM_WEAPONS];
 	int			invulnerabilityTime;
 #endif
 
@@ -331,7 +337,7 @@
 
 	struct gentity_s	*gentities;
 	int			gentitySize;
-	int                   num_entities;           // MAX_CLIENTS <= num_entities <= ENTITYNUM_MAX_NORMAL
+	int			num_entities;		// current number, <= MAX_GENTITIES
 
 	int			warmupTime;			// restart match at this time
 
@@ -404,12 +410,9 @@
 	gentity_t	*locationHead;			// head of the location list
 	int			bodyQueIndex;			// dead bodies
 	gentity_t	*bodyQue[BODY_QUEUE_SIZE];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			portalSequence;
 #endif
-	char serverSound[MAX_QPATH];
-	vec3_t serverSoundOrigin;
-	gentity_t *serverSoundEnt;
 } level_locals_t;
 
 
@@ -430,7 +433,7 @@
 void Cmd_Score_f (gentity_t *ent);
 void StopFollowing( gentity_t *ent );
 void BroadcastTeamChange( gclient_t *client, int oldTeam );
-void SetTeam( gentity_t *ent, const char *s );
+void SetTeam( gentity_t *ent, char *s );
 void Cmd_FollowCycle_f( gentity_t *ent, int dir );
 
 //
@@ -476,6 +479,7 @@
 qboolean	G_EntitiesFree( void );
 
 void	G_TouchTriggers (gentity_t *ent);
+void	G_TouchSolids (gentity_t *ent);
 
 float	*tv (float x, float y, float z);
 char	*vtos( const vec3_t v );
@@ -486,7 +490,7 @@
 void G_AddEvent( gentity_t *ent, int event, int eventParm );
 void G_SetOrigin( gentity_t *ent, vec3_t origin );
 void AddRemap(const char *oldShader, const char *newShader, float timeOffset);
-const char *BuildShaderStateConfig( void );
+const char *BuildShaderStateConfig();
 
 //
 // g_combat.c
@@ -497,7 +501,7 @@
 int G_InvulnerabilityEffect( gentity_t *targ, vec3_t dir, vec3_t point, vec3_t impactpoint, vec3_t bouncedir );
 void body_die( gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int meansOfDeath );
 void TossClientItems( gentity_t *self );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void TossClientPersistantPowerups( gentity_t *self );
 #endif
 void TossClientCubes( gentity_t *self );
@@ -507,7 +511,7 @@
 #define DAMAGE_NO_ARMOR				0x00000002	// armour does not protect from this damage
 #define DAMAGE_NO_KNOCKBACK			0x00000004	// do not affect velocity, just view angles
 #define DAMAGE_NO_PROTECTION		0x00000008  // armor, shields, invulnerability, and godmode have no effect
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define DAMAGE_NO_TEAM_PROTECTION	0x00000010  // armor, shields, invulnerability, and godmode have no effect
 #endif
 
@@ -516,12 +520,13 @@
 //
 void G_RunMissile( gentity_t *ent );
 
+gentity_t *fire_blaster (gentity_t *self, vec3_t start, vec3_t aimdir);
 gentity_t *fire_plasma (gentity_t *self, vec3_t start, vec3_t aimdir);
 gentity_t *fire_grenade (gentity_t *self, vec3_t start, vec3_t aimdir);
 gentity_t *fire_rocket (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_bfg (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_grapple (gentity_t *self, vec3_t start, vec3_t dir);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 gentity_t *fire_nail( gentity_t *self, vec3_t start, vec3_t forward, vec3_t right, vec3_t up );
 gentity_t *fire_prox( gentity_t *self, vec3_t start, vec3_t aimdir );
 #endif
@@ -543,7 +548,7 @@
 // g_misc.c
 //
 void TeleportPlayer( gentity_t *player, vec3_t origin, vec3_t angles );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void DropPortalSource( gentity_t *ent );
 void DropPortalDestination( gentity_t *ent );
 #endif
@@ -563,14 +568,16 @@
 //
 // g_client.c
 //
-int TeamCount( int ignoreClientNum, team_t team );
+team_t TeamCount( int ignoreClientNum, int team );
 int TeamLeader( int team );
 team_t PickTeam( int ignoreClientNum );
 void SetClientViewAngle( gentity_t *ent, vec3_t angle );
-gentity_t *SelectSpawnPoint (vec3_t avoidPoint, vec3_t origin, vec3_t angles, qboolean isbot);
+gentity_t *SelectSpawnPoint ( vec3_t avoidPoint, vec3_t origin, vec3_t angles );
 void CopyToBodyQue( gentity_t *ent );
-void ClientRespawn(gentity_t *ent);
+void respawn (gentity_t *ent);
 void BeginIntermission (void);
+void InitClientPersistant (gclient_t *client);
+void InitClientResp (gclient_t *client);
 void InitBodyQue (void);
 void ClientSpawn( gentity_t *ent );
 void player_die (gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int mod);
@@ -589,29 +596,37 @@
 // g_weapon.c
 //
 void FireWeapon( gentity_t *ent );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void G_StartKamikaze( gentity_t *ent );
 #endif
 
 //
+// p_hud.c
+//
+void MoveClientToIntermission (gentity_t *client);
+void G_SetStats (gentity_t *ent);
+void DeathmatchScoreboardMessage (gentity_t *client);
+
+//
 // g_cmds.c
 //
-void DeathmatchScoreboardMessage( gentity_t *ent );
-void DuelScores (gentity_t *client);
+
+//
+// g_pweapon.c
+//
+
 
 //
 // g_main.c
 //
-void MoveClientToIntermission( gentity_t *ent );
 void FindIntermissionPoint( void );
 void SetLeader(int team, int client);
 void CheckTeamLeader( int team );
 void G_RunThink (gentity_t *ent);
-void AddTournamentQueue(gclient_t *client);
-void QDECL G_LogPrintf( const char *fmt, ... ) Q_PRINTF_FUNC(1, 2);
+void QDECL G_LogPrintf( const char *fmt, ... );
 void SendScoreboardMessageToAllClients( void );
-void QDECL G_Printf( const char *fmt, ... ) Q_PRINTF_FUNC(1, 2);
-void QDECL G_Error( const char *fmt, ... ) Q_NO_RETURN Q_PRINTF_FUNC(1, 2);
+void QDECL G_Printf( const char *fmt, ... );
+void QDECL G_Error( const char *fmt, ... );
 
 //
 // g_client.c
@@ -680,6 +695,7 @@
 {
 	char characterfile[MAX_FILEPATH];
 	float skill;
+	char team[MAX_FILEPATH];
 } bot_settings_t;
 
 int BotAISetup( int restart );
@@ -696,7 +712,7 @@
 extern	level_locals_t	level;
 extern	gentity_t		g_entities[MAX_GENTITIES];
 
-#define	FOFS(x) ((size_t)&(((gentity_t *)0)->x))
+#define	FOFS(x) ((int)&(((gentity_t *)0)->x))
 
 extern	vmCvar_t	g_gametype;
 extern	vmCvar_t	g_dedicated;
@@ -748,23 +764,10 @@
 extern	vmCvar_t	g_enableBreath;
 extern	vmCvar_t	g_singlePlayer;
 extern	vmCvar_t	g_proxMineTimeout;
-extern	vmCvar_t	g_localTeamPref;
-extern vmCvar_t g_levelStartTime;
-
-extern vmCvar_t g_weapon_rocket_speed;
-
-extern vmCvar_t g_weapon_plasma_speed;
-//extern vmCvar_t g_weapon_plasma_rate;
-
-extern vmCvar_t g_debugPingValue;
-extern vmCvar_t g_ammoPack;
-extern vmCvar_t g_ammoPackHack;
-extern vmCvar_t g_wolfcamVersion;
 
-void	trap_Print( const char *text );
-void    trap_Error( const char *text ) Q_NO_RETURN;
+void	trap_Printf( const char *fmt );
+void	trap_Error( const char *fmt );
 int		trap_Milliseconds( void );
-int	trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
 int		trap_Argc( void );
 void	trap_Argv( int n, char *buffer, int bufferLength );
 void	trap_Args( char *buffer, int bufferLength );
@@ -966,4 +969,3 @@
 
 void	trap_SnapVector( float *v );
 
-void G_Say( gentity_t *ent, gentity_t *target, int mode, const char *chatText );

```

### `ioquake3`  — sha256 `3f53cf99d2ba...`, 35254 bytes

_Diff stat: +13 / -29 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_local.h	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_local.h	2026-04-16 20:02:21.544362900 +0100
@@ -159,7 +159,7 @@
 	gentity_t	*teamchain;		// next entity in team
 	gentity_t	*teammaster;	// master of the team
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			kamikazeTime;
 	int			kamikazeShockTime;
 #endif
@@ -219,7 +219,7 @@
 // MUST be dealt with in G_InitSessionData() / G_ReadSessionData() / G_WriteSessionData()
 typedef struct {
 	team_t		sessionTeam;
-	int                     spectatorNum;           // for determining next-in-line to play
+	int			spectatorNum;		// for determining next-in-line to play
 	spectatorState_t	spectatorState;
 	int			spectatorClient;	// for chasecam and follow mode
 	int			wins, losses;		// tournament stats
@@ -309,10 +309,10 @@
 	// like health / armor countdowns and regeneration
 	int			timeResidual;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	gentity_t	*persistantPowerup;
 	int			portalID;
-	int			ammoTimes[WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS];
+	int			ammoTimes[WP_NUM_WEAPONS];
 	int			invulnerabilityTime;
 #endif
 
@@ -331,7 +331,7 @@
 
 	struct gentity_s	*gentities;
 	int			gentitySize;
-	int                   num_entities;           // MAX_CLIENTS <= num_entities <= ENTITYNUM_MAX_NORMAL
+	int			num_entities;		// MAX_CLIENTS <= num_entities <= ENTITYNUM_MAX_NORMAL
 
 	int			warmupTime;			// restart match at this time
 
@@ -404,12 +404,9 @@
 	gentity_t	*locationHead;			// head of the location list
 	int			bodyQueIndex;			// dead bodies
 	gentity_t	*bodyQue[BODY_QUEUE_SIZE];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			portalSequence;
 #endif
-	char serverSound[MAX_QPATH];
-	vec3_t serverSoundOrigin;
-	gentity_t *serverSoundEnt;
 } level_locals_t;
 
 
@@ -497,7 +494,7 @@
 int G_InvulnerabilityEffect( gentity_t *targ, vec3_t dir, vec3_t point, vec3_t impactpoint, vec3_t bouncedir );
 void body_die( gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int meansOfDeath );
 void TossClientItems( gentity_t *self );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void TossClientPersistantPowerups( gentity_t *self );
 #endif
 void TossClientCubes( gentity_t *self );
@@ -507,7 +504,7 @@
 #define DAMAGE_NO_ARMOR				0x00000002	// armour does not protect from this damage
 #define DAMAGE_NO_KNOCKBACK			0x00000004	// do not affect velocity, just view angles
 #define DAMAGE_NO_PROTECTION		0x00000008  // armor, shields, invulnerability, and godmode have no effect
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define DAMAGE_NO_TEAM_PROTECTION	0x00000010  // armor, shields, invulnerability, and godmode have no effect
 #endif
 
@@ -521,7 +518,7 @@
 gentity_t *fire_rocket (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_bfg (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_grapple (gentity_t *self, vec3_t start, vec3_t dir);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 gentity_t *fire_nail( gentity_t *self, vec3_t start, vec3_t forward, vec3_t right, vec3_t up );
 gentity_t *fire_prox( gentity_t *self, vec3_t start, vec3_t aimdir );
 #endif
@@ -543,7 +540,7 @@
 // g_misc.c
 //
 void TeleportPlayer( gentity_t *player, vec3_t origin, vec3_t angles );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void DropPortalSource( gentity_t *ent );
 void DropPortalDestination( gentity_t *ent );
 #endif
@@ -589,7 +586,7 @@
 // g_weapon.c
 //
 void FireWeapon( gentity_t *ent );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void G_StartKamikaze( gentity_t *ent );
 #endif
 
@@ -597,7 +594,6 @@
 // g_cmds.c
 //
 void DeathmatchScoreboardMessage( gentity_t *ent );
-void DuelScores (gentity_t *client);
 
 //
 // g_main.c
@@ -749,22 +745,11 @@
 extern	vmCvar_t	g_singlePlayer;
 extern	vmCvar_t	g_proxMineTimeout;
 extern	vmCvar_t	g_localTeamPref;
-extern vmCvar_t g_levelStartTime;
-
-extern vmCvar_t g_weapon_rocket_speed;
-
-extern vmCvar_t g_weapon_plasma_speed;
-//extern vmCvar_t g_weapon_plasma_rate;
-
-extern vmCvar_t g_debugPingValue;
-extern vmCvar_t g_ammoPack;
-extern vmCvar_t g_ammoPackHack;
-extern vmCvar_t g_wolfcamVersion;
 
 void	trap_Print( const char *text );
-void    trap_Error( const char *text ) Q_NO_RETURN;
+void	trap_Error( const char *text ) Q_NO_RETURN;
 int		trap_Milliseconds( void );
-int	trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int	trap_RealTime( qtime_t *qtime );
 int		trap_Argc( void );
 void	trap_Argv( int n, char *buffer, int bufferLength );
 void	trap_Args( char *buffer, int bufferLength );
@@ -966,4 +951,3 @@
 
 void	trap_SnapVector( float *v );
 
-void G_Say( gentity_t *ent, gentity_t *target, int mode, const char *chatText );

```

### `openarena-engine`  — sha256 `388b5f616e41...`, 35312 bytes

_Diff stat: +19 / -35 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_local.h	2026-04-16 20:02:25.195156500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_local.h	2026-04-16 22:48:25.747535800 +0100
@@ -45,7 +45,7 @@
 // gentity->flags
 #define	FL_GODMODE				0x00000010
 #define	FL_NOTARGET				0x00000020
-#define	FL_TEAMMEMBER			0x00000400	// not the first on the team
+#define	FL_TEAMSLAVE			0x00000400	// not the first on the team
 #define FL_NO_KNOCKBACK			0x00000800
 #define FL_DROPPED_ITEM			0x00001000
 #define FL_NO_BOTS				0x00002000	// spawn point not for bot use
@@ -159,7 +159,7 @@
 	gentity_t	*teamchain;		// next entity in team
 	gentity_t	*teammaster;	// master of the team
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			kamikazeTime;
 	int			kamikazeShockTime;
 #endif
@@ -219,7 +219,7 @@
 // MUST be dealt with in G_InitSessionData() / G_ReadSessionData() / G_WriteSessionData()
 typedef struct {
 	team_t		sessionTeam;
-	int                     spectatorNum;           // for determining next-in-line to play
+	int			spectatorNum;		// for determining next-in-line to play
 	spectatorState_t	spectatorState;
 	int			spectatorClient;	// for chasecam and follow mode
 	int			wins, losses;		// tournament stats
@@ -309,10 +309,10 @@
 	// like health / armor countdowns and regeneration
 	int			timeResidual;
 
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	gentity_t	*persistantPowerup;
 	int			portalID;
-	int			ammoTimes[WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS];
+	int			ammoTimes[WP_NUM_WEAPONS];
 	int			invulnerabilityTime;
 #endif
 
@@ -331,7 +331,7 @@
 
 	struct gentity_s	*gentities;
 	int			gentitySize;
-	int                   num_entities;           // MAX_CLIENTS <= num_entities <= ENTITYNUM_MAX_NORMAL
+	int			num_entities;		// MAX_CLIENTS <= num_entities <= ENTITYNUM_MAX_NORMAL
 
 	int			warmupTime;			// restart match at this time
 
@@ -404,12 +404,9 @@
 	gentity_t	*locationHead;			// head of the location list
 	int			bodyQueIndex;			// dead bodies
 	gentity_t	*bodyQue[BODY_QUEUE_SIZE];
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 	int			portalSequence;
 #endif
-	char serverSound[MAX_QPATH];
-	vec3_t serverSoundOrigin;
-	gentity_t *serverSoundEnt;
 } level_locals_t;
 
 
@@ -430,7 +427,7 @@
 void Cmd_Score_f (gentity_t *ent);
 void StopFollowing( gentity_t *ent );
 void BroadcastTeamChange( gclient_t *client, int oldTeam );
-void SetTeam( gentity_t *ent, const char *s );
+void SetTeam( gentity_t *ent, char *s );
 void Cmd_FollowCycle_f( gentity_t *ent, int dir );
 
 //
@@ -497,7 +494,7 @@
 int G_InvulnerabilityEffect( gentity_t *targ, vec3_t dir, vec3_t point, vec3_t impactpoint, vec3_t bouncedir );
 void body_die( gentity_t *self, gentity_t *inflictor, gentity_t *attacker, int damage, int meansOfDeath );
 void TossClientItems( gentity_t *self );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void TossClientPersistantPowerups( gentity_t *self );
 #endif
 void TossClientCubes( gentity_t *self );
@@ -507,7 +504,7 @@
 #define DAMAGE_NO_ARMOR				0x00000002	// armour does not protect from this damage
 #define DAMAGE_NO_KNOCKBACK			0x00000004	// do not affect velocity, just view angles
 #define DAMAGE_NO_PROTECTION		0x00000008  // armor, shields, invulnerability, and godmode have no effect
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 #define DAMAGE_NO_TEAM_PROTECTION	0x00000010  // armor, shields, invulnerability, and godmode have no effect
 #endif
 
@@ -521,7 +518,7 @@
 gentity_t *fire_rocket (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_bfg (gentity_t *self, vec3_t start, vec3_t dir);
 gentity_t *fire_grapple (gentity_t *self, vec3_t start, vec3_t dir);
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 gentity_t *fire_nail( gentity_t *self, vec3_t start, vec3_t forward, vec3_t right, vec3_t up );
 gentity_t *fire_prox( gentity_t *self, vec3_t start, vec3_t aimdir );
 #endif
@@ -543,7 +540,7 @@
 // g_misc.c
 //
 void TeleportPlayer( gentity_t *player, vec3_t origin, vec3_t angles );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void DropPortalSource( gentity_t *ent );
 void DropPortalDestination( gentity_t *ent );
 #endif
@@ -589,7 +586,7 @@
 // g_weapon.c
 //
 void FireWeapon( gentity_t *ent );
-#if 1  //def MPACK
+#ifdef MISSIONPACK
 void G_StartKamikaze( gentity_t *ent );
 #endif
 
@@ -597,7 +594,6 @@
 // g_cmds.c
 //
 void DeathmatchScoreboardMessage( gentity_t *ent );
-void DuelScores (gentity_t *client);
 
 //
 // g_main.c
@@ -608,10 +604,10 @@
 void CheckTeamLeader( int team );
 void G_RunThink (gentity_t *ent);
 void AddTournamentQueue(gclient_t *client);
-void QDECL G_LogPrintf( const char *fmt, ... ) Q_PRINTF_FUNC(1, 2);
+void QDECL G_LogPrintf( const char *fmt, ... ) __attribute__ ((format (printf, 1, 2)));
 void SendScoreboardMessageToAllClients( void );
-void QDECL G_Printf( const char *fmt, ... ) Q_PRINTF_FUNC(1, 2);
-void QDECL G_Error( const char *fmt, ... ) Q_NO_RETURN Q_PRINTF_FUNC(1, 2);
+void QDECL G_Printf( const char *fmt, ... ) __attribute__ ((format (printf, 1, 2)));
+void QDECL G_Error( const char *fmt, ... ) __attribute__ ((noreturn, format (printf, 1, 2)));
 
 //
 // g_client.c
@@ -680,6 +676,7 @@
 {
 	char characterfile[MAX_FILEPATH];
 	float skill;
+	char team[MAX_FILEPATH];
 } bot_settings_t;
 
 int BotAISetup( int restart );
@@ -748,23 +745,11 @@
 extern	vmCvar_t	g_enableBreath;
 extern	vmCvar_t	g_singlePlayer;
 extern	vmCvar_t	g_proxMineTimeout;
-extern	vmCvar_t	g_localTeamPref;
-extern vmCvar_t g_levelStartTime;
-
-extern vmCvar_t g_weapon_rocket_speed;
-
-extern vmCvar_t g_weapon_plasma_speed;
-//extern vmCvar_t g_weapon_plasma_rate;
-
-extern vmCvar_t g_debugPingValue;
-extern vmCvar_t g_ammoPack;
-extern vmCvar_t g_ammoPackHack;
-extern vmCvar_t g_wolfcamVersion;
 
 void	trap_Print( const char *text );
-void    trap_Error( const char *text ) Q_NO_RETURN;
+void	trap_Error( const char *text ) __attribute__((noreturn));
 int		trap_Milliseconds( void );
-int	trap_RealTime (qtime_t *qtime, qboolean now, int convertTime);
+int	trap_RealTime( qtime_t *qtime );
 int		trap_Argc( void );
 void	trap_Argv( int n, char *buffer, int bufferLength );
 void	trap_Args( char *buffer, int bufferLength );
@@ -966,4 +951,3 @@
 
 void	trap_SnapVector( float *v );
 
-void G_Say( gentity_t *ent, gentity_t *target, int mode, const char *chatText );

```

### `openarena-gamecode`  — sha256 `caa2ebc19f0e...`, 53313 bytes

_Diff stat: +576 / -111 lines_

_(full diff is 33275 bytes — see files directly)_
