# Diff: `code/game/g_svcmds.c`
**Canonical:** `wolfcamql-src` (sha256 `6a04eccfafcc...`, 10554 bytes)

## Variants

### `quake3-source`  — sha256 `78a98e098823...`, 10410 bytes

_Diff stat: +11 / -16 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_svcmds.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_svcmds.c	2026-04-16 20:02:19.909574100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -132,11 +132,11 @@
 */
 static void UpdateIPBans (void)
 {
-	byte	b[4] = {0};
-	byte	m[4] = {0};
+	byte	b[4];
+	byte	m[4];
 	int		i,j;
-	char	iplist_final[MAX_CVAR_VALUE_STRING] = {0};
-	char	ip[64] = {0};
+	char	iplist_final[MAX_CVAR_VALUE_STRING];
+	char	ip[64];
 
 	*iplist_final = 0;
 	for (i = 0 ; i < numIPFilters ; i++)
@@ -178,7 +178,7 @@
 {
 	int		i;
 	unsigned	in;
-	byte m[4] = {0};
+	byte m[4];
 	char *p;
 
 	i = 0;
@@ -288,7 +288,7 @@
 	char		str[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() < 2 ) {
-		G_Printf("Usage: removeip <ip-mask>\n");
+		G_Printf("Usage:  sv removeip <ip-mask>\n");
 		return;
 	}
 
@@ -320,8 +320,8 @@
 	int			e;
 	gentity_t		*check;
 
-	check = g_entities;
-	for (e = 0; e < level.num_entities ; e++, check++) {
+	check = g_entities+1;
+	for (e = 1; e < level.num_entities ; e++, check++) {
 		if ( !check->inuse ) {
 			continue;
 		}
@@ -423,11 +423,6 @@
 	gclient_t	*cl;
 	char		str[MAX_TOKEN_CHARS];
 
-	if ( trap_Argc() < 3 ) {
-		G_Printf("Usage: forceteam <player> <team>\n");
-		return;
-	}
-
 	// find the player
 	trap_Argv( 1, str, sizeof( str ) );
 	cl = ClientForString( str );
@@ -500,11 +495,11 @@
 
 	if (g_dedicated.integer) {
 		if (Q_stricmp (cmd, "say") == 0) {
-			trap_SendServerCommand( -1, va("print \"server: %s\n\"", ConcatArgs(1) ) );
+			trap_SendServerCommand( -1, va("print \"server: %s\"", ConcatArgs(1) ) );
 			return qtrue;
 		}
 		// everything else will also be printed as a say command
-		trap_SendServerCommand( -1, va("print \"server: %s\n\"", ConcatArgs(0) ) );
+		trap_SendServerCommand( -1, va("print \"server: %s\"", ConcatArgs(0) ) );
 		return qtrue;
 	}
 

```

### `ioquake3`  — sha256 `424fc05bc7a1...`, 10553 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_svcmds.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_svcmds.c	2026-04-16 20:02:21.547849900 +0100
@@ -266,7 +266,7 @@
 	char		str[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() < 2 ) {
-		G_Printf("Usage:  addip <ip-mask>\n");
+		G_Printf("Usage: addip <ip-mask>\n");
 		return;
 	}
 

```

### `openarena-engine`  — sha256 `0636499f40c1...`, 10525 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_svcmds.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_svcmds.c	2026-04-16 22:48:25.750042300 +0100
@@ -132,11 +132,11 @@
 */
 static void UpdateIPBans (void)
 {
-	byte	b[4] = {0};
-	byte	m[4] = {0};
+	byte	b[4];
+	byte	m[4];
 	int		i,j;
-	char	iplist_final[MAX_CVAR_VALUE_STRING] = {0};
-	char	ip[64] = {0};
+	char	iplist_final[MAX_CVAR_VALUE_STRING];
+	char	ip[64];
 
 	*iplist_final = 0;
 	for (i = 0 ; i < numIPFilters ; i++)
@@ -178,7 +178,7 @@
 {
 	int		i;
 	unsigned	in;
-	byte m[4] = {0};
+	byte m[4];
 	char *p;
 
 	i = 0;
@@ -266,7 +266,7 @@
 	char		str[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() < 2 ) {
-		G_Printf("Usage:  addip <ip-mask>\n");
+		G_Printf("Usage: addip <ip-mask>\n");
 		return;
 	}
 
@@ -320,8 +320,8 @@
 	int			e;
 	gentity_t		*check;
 
-	check = g_entities;
-	for (e = 0; e < level.num_entities ; e++, check++) {
+	check = g_entities+1;
+	for (e = 1; e < level.num_entities ; e++, check++) {
 		if ( !check->inuse ) {
 			continue;
 		}

```

### `openarena-gamecode`  — sha256 `2c63279f100d...`, 11941 bytes

_Diff stat: +122 / -103 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_svcmds.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_svcmds.c	2026-04-16 22:48:24.174987100 +0100
@@ -30,7 +30,7 @@
 ==============================================================================
 
 PACKET FILTERING
- 
+
 
 You can add or remove addresses from the filter list with:
 
@@ -59,8 +59,7 @@
 ==============================================================================
 */
 
-typedef struct ipFilter_s
-{
+typedef struct ipFilter_s {
 	unsigned	mask;
 	unsigned	compare;
 } ipFilter_t;
@@ -81,19 +80,15 @@
 	int		i, j;
 	byte	b[4];
 	byte	m[4];
-	
-	for (i=0 ; i<4 ; i++)
-	{
+
+	for (i=0 ; i<4 ; i++) {
 		b[i] = 0;
 		m[i] = 0;
 	}
-	
-	for (i=0 ; i<4 ; i++)
-	{
-		if (*s < '0' || *s > '9')
-		{
-			if (*s == '*') // 'match any'
-			{
+
+	for (i=0 ; i<4 ; i++) {
+		if (*s < '0' || *s > '9') {
+			if (*s == '*') { // 'match any'
 				// b[i] and m[i] to 0
 				s++;
 				if (!*s)
@@ -104,10 +99,9 @@
 			G_Printf( "Bad filter address: %s\n", s );
 			return qfalse;
 		}
-		
+
 		j = 0;
-		while (*s >= '0' && *s <= '9')
-		{
+		while (*s >= '0' && *s <= '9') {
 			num[j++] = *s++;
 		}
 		num[j] = 0;
@@ -118,10 +112,10 @@
 			break;
 		s++;
 	}
-	
+
 	f->mask = *(unsigned *)m;
 	f->compare = *(unsigned *)b;
-	
+
 	return qtrue;
 }
 
@@ -132,35 +126,31 @@
 */
 static void UpdateIPBans (void)
 {
-	byte	b[4] = {0};
-	byte	m[4] = {0};
+	byte	b[4];
+	byte	m[4];
 	int		i,j;
-	char	iplist_final[MAX_CVAR_VALUE_STRING] = {0};
-	char	ip[64] = {0};
+	char	iplist_final[MAX_CVAR_VALUE_STRING];
+	char	ip[64];
 
 	*iplist_final = 0;
-	for (i = 0 ; i < numIPFilters ; i++)
-	{
+	for (i = 0 ; i < numIPFilters ; i++) {
 		if (ipFilters[i].compare == 0xffffffff)
 			continue;
 
 		*(unsigned *)b = ipFilters[i].compare;
 		*(unsigned *)m = ipFilters[i].mask;
 		*ip = 0;
-		for (j = 0 ; j < 4 ; j++)
-		{
+		for (j = 0 ; j < 4 ; j++) {
 			if (m[j]!=255)
 				Q_strcat(ip, sizeof(ip), "*");
 			else
 				Q_strcat(ip, sizeof(ip), va("%i", b[j]));
 			Q_strcat(ip, sizeof(ip), (j<3) ? "." : " ");
-		}		
-		if (strlen(iplist_final)+strlen(ip) < MAX_CVAR_VALUE_STRING)
-		{
+		}
+		if (strlen(iplist_final)+strlen(ip) < MAX_CVAR_VALUE_STRING) {
 			Q_strcat( iplist_final, sizeof(iplist_final), ip);
 		}
-		else
-		{
+		else {
 			Com_Printf("g_banIPs overflowed at MAX_CVAR_VALUE_STRING\n");
 			break;
 		}
@@ -178,7 +168,7 @@
 {
 	int		i;
 	unsigned	in;
-	byte m[4] = {0};
+	byte m[4];
 	char *p;
 
 	i = 0;
@@ -193,7 +183,7 @@
 			break;
 		i++, p++;
 	}
-	
+
 	in = *(unsigned *)m;
 
 	for (i=0 ; i<numIPFilters ; i++)
@@ -215,16 +205,14 @@
 	for (i = 0 ; i < numIPFilters ; i++)
 		if (ipFilters[i].compare == 0xffffffff)
 			break;		// free spot
-	if (i == numIPFilters)
-	{
-		if (numIPFilters == MAX_IPFILTERS)
-		{
+	if (i == numIPFilters) {
+		if (numIPFilters == MAX_IPFILTERS) {
 			G_Printf ("IP filter list is full\n");
 			return;
 		}
 		numIPFilters++;
 	}
-	
+
 	if (!StringToFilter (str, &ipFilters[i]))
 		ipFilters[i].compare = 0xffffffffu;
 
@@ -236,7 +224,7 @@
 G_ProcessIPBans
 =================
 */
-void G_ProcessIPBans(void) 
+void G_ProcessIPBans(void)
 {
 	char *s, *t;
 	char		str[MAX_CVAR_VALUE_STRING];
@@ -288,7 +276,7 @@
 	char		str[MAX_TOKEN_CHARS];
 
 	if ( trap_Argc() < 2 ) {
-		G_Printf("Usage: removeip <ip-mask>\n");
+		G_Printf("Usage:  sv removeip <ip-mask>\n");
 		return;
 	}
 
@@ -299,7 +287,7 @@
 
 	for (i=0 ; i<numIPFilters ; i++) {
 		if (ipFilters[i].mask == f.mask	&&
-			ipFilters[i].compare == f.compare) {
+		        ipFilters[i].compare == f.compare) {
 			ipFilters[i].compare = 0xffffffffu;
 			G_Printf ("Removed.\n");
 
@@ -307,7 +295,6 @@
 			return;
 		}
 	}
-
 	G_Printf ( "Didn't find %s.\n", str );
 }
 
@@ -316,7 +303,8 @@
 Svcmd_EntityList_f
 ===================
 */
-void	Svcmd_EntityList_f (void) {
+void	Svcmd_EntityList_f (void)
+{
 	int			e;
 	gentity_t		*check;
 
@@ -367,7 +355,6 @@
 			G_Printf("%3i                 ", check->s.eType);
 			break;
 		}
-
 		if ( check->classname ) {
 			G_Printf("%s", check->classname);
 		}
@@ -375,7 +362,8 @@
 	}
 }
 
-gclient_t	*ClientForString( const char *s ) {
+gclient_t	*ClientForString( const char *s )
+{
 	gclient_t	*cl;
 	int			i;
 	int			idnum;
@@ -402,11 +390,10 @@
 		if ( cl->pers.connected == CON_DISCONNECTED ) {
 			continue;
 		}
-		if ( !Q_stricmp( cl->pers.netname, s ) ) {
+		if ( Q_strequal( cl->pers.netname, s ) ) {
 			return cl;
 		}
 	}
-
 	G_Printf( "User %s is not on the server\n", s );
 
 	return NULL;
@@ -419,15 +406,11 @@
 forceteam <player> <team>
 ===================
 */
-void	Svcmd_ForceTeam_f( void ) {
+void	Svcmd_ForceTeam_f( void )
+{
 	gclient_t	*cl;
 	char		str[MAX_TOKEN_CHARS];
 
-	if ( trap_Argc() < 3 ) {
-		G_Printf("Usage: forceteam <player> <team>\n");
-		return;
-	}
-
 	// find the player
 	trap_Argv( 1, str, sizeof( str ) );
 	cl = ClientForString( str );
@@ -440,73 +423,109 @@
 	SetTeam( &g_entities[cl - level.clients], str );
 }
 
-char	*ConcatArgs( int start );
+void	ClientKick_f( void )
+{
+	int idnum, i;
+	char	str[MAX_TOKEN_CHARS];
 
-/*
-=================
-ConsoleCommand
+	trap_Argv( 1, str, sizeof( str ) );
 
-=================
-*/
-qboolean	ConsoleCommand( void ) {
-	char	cmd[MAX_TOKEN_CHARS];
+	for (i = 0; str[i]; i++) {
+		if (str[i] < '0' || str[i] > '9') {
+			G_Printf("not a valid client number: \"%s\"\n",str);
+			return;
+		}
+	}
 
-	trap_Argv( 0, cmd, sizeof( cmd ) );
+	idnum = atoi( str );
 
-	if ( Q_stricmp (cmd, "entitylist") == 0 ) {
-		Svcmd_EntityList_f();
-		return qtrue;
+	//Local client
+	if ( strequals( level.clients[idnum].pers.ip, "localhost" ) ) {
+		G_Printf("Kick failed - local player\n");
+		return;
 	}
 
-	if ( Q_stricmp (cmd, "forceteam") == 0 ) {
-		Svcmd_ForceTeam_f();
-		return qtrue;
-	}
+	//Now clientkick has been moved into game, but we still need to find the idnum the server expects....
+	//FIXME: To fix this, we need a relieble way to generate difference between the server's client number and the game's client numbers
+	//FIXME: This should not depend on the engine's clientkick at all
+	trap_DropClient( idnum, "was kicked" );
+	//trap_SendConsoleCommand( EXEC_INSERT, va("clientkick %d\n", level.clients[idnum].ps.clientNum) );
 
-	if (Q_stricmp (cmd, "game_memory") == 0) {
-		Svcmd_GameMem_f();
-		return qtrue;
-	}
+}
 
-	if (Q_stricmp (cmd, "addbot") == 0) {
-		Svcmd_AddBot_f();
-		return qtrue;
-	}
+void EndGame_f ( void )
+{
+	ExitLevel();
+}
 
-	if (Q_stricmp (cmd, "botlist") == 0) {
-		Svcmd_BotList_f();
-		return qtrue;
-	}
+//KK-OAX Moved this Declaration to g_local.h
+//char	*ConcatArgs( int start );
 
-	if (Q_stricmp (cmd, "abort_podium") == 0) {
-		Svcmd_AbortPodium_f();
-		return qtrue;
-	}
+/*KK-OAX
+===============
+Server Command Table
+Not Worth Listing Elsewhere
+================
+*/
+struct {
+	char      *cmd;
+	qboolean  dedicated; //if it has to be entered from a dedicated server or RCON
+	void      ( *function )( void );
+} svcmds[ ] = {
+
+	{ "entityList", qfalse, Svcmd_EntityList_f },
+	{ "forceTeam", qfalse, Svcmd_ForceTeam_f },
+	{ "game_memory", qfalse, Svcmd_GameMem_f },
+	{ "addbot", qfalse, Svcmd_AddBot_f },
+	{ "botlist", qfalse, Svcmd_BotList_f },
+	{ "abort_podium", qfalse, Svcmd_AbortPodium_f },
+	{ "addip", qfalse, Svcmd_AddIP_f },
+	{ "removeip", qfalse, Svcmd_RemoveIP_f },
+
+	//KK-OAX Uses wrapper in g_svccmds_ext.c
+	{ "listip", qfalse, Svcmd_ListIP_f },
+	//KK-OAX New
+	{ "status", qfalse, Svcmd_Status_f },
+	{ "eject", qfalse, Svcmd_EjectClient_f },
+	{ "dumpuser", qfalse, Svcmd_DumpUser_f },
+	// don't handle communication commands unless dedicated
+	{ "cp", qtrue, Svcmd_CenterPrint_f },
+	{ "say_team", qtrue, Svcmd_TeamMessage_f },
+	{ "say", qtrue, Svcmd_MessageWrapper },
+	{ "chat", qtrue, Svcmd_Chat_f },
+	//Kicks a player by number in the game logic rather than the server number
+	{ "clientkick_game", qfalse, ClientKick_f },
+	{ "endgamenow", qfalse, EndGame_f },
+};
 
-	if (Q_stricmp (cmd, "addip") == 0) {
-		Svcmd_AddIP_f();
-		return qtrue;
-	}
+/*
+=================
+ConsoleCommand
 
-	if (Q_stricmp (cmd, "removeip") == 0) {
-		Svcmd_RemoveIP_f();
-		return qtrue;
-	}
+=================
+*/
+qboolean  ConsoleCommand( void )
+{
+	char cmd[ MAX_TOKEN_CHARS ];
+	int  i;
 
-	if (Q_stricmp (cmd, "listip") == 0) {
-		trap_SendConsoleCommand( EXEC_NOW, "g_banIPs\n" );
-		return qtrue;
-	}
+	trap_Argv( 0, cmd, sizeof( cmd ) );
 
-	if (g_dedicated.integer) {
-		if (Q_stricmp (cmd, "say") == 0) {
-			trap_SendServerCommand( -1, va("print \"server: %s\n\"", ConcatArgs(1) ) );
+	for( i = 0; i < sizeof( svcmds ) / sizeof( svcmds[ 0 ] ); i++ ) {
+		if( Q_strequal( cmd, svcmds[ i ].cmd ) ) {
+			if( svcmds[ i ].dedicated && !g_dedicated.integer )
+				return qfalse;
+			svcmds[ i ].function( );
 			return qtrue;
 		}
-		// everything else will also be printed as a say command
-		trap_SendServerCommand( -1, va("print \"server: %s\n\"", ConcatArgs(0) ) );
-		return qtrue;
 	}
+	// KK-OAX Will be enabled when admin is added.
+	// see if this is an admin command
+	if( G_admin_cmd_check( NULL, qfalse ) )
+		return qtrue;
+
+	if( g_dedicated.integer )
+		G_Printf( "unknown command: %s\n", cmd );
 
 	return qfalse;
 }

```
