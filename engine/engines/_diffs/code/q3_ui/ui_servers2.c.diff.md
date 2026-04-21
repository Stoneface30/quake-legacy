# Diff: `code/q3_ui/ui_servers2.c`
**Canonical:** `wolfcamql-src` (sha256 `872cc00d0c80...`, 47370 bytes)

## Variants

### `quake3-source`  — sha256 `99accdd4f660...`, 46626 bytes

_Diff stat: +145 / -151 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_servers2.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_servers2.c	2026-04-16 20:02:19.952185700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -80,42 +80,28 @@
 #define GR_LOGO				30
 #define GR_LETTERS			31
 
-#define UIAS_LOCAL			0
-#define UIAS_GLOBAL0                   1
-#define UIAS_GLOBAL1                   2
-#define UIAS_GLOBAL2                   3
-#define UIAS_GLOBAL3                   4
-#define UIAS_GLOBAL4                   5
-#define UIAS_GLOBAL5                   6
-#define UIAS_FAVORITES                 7
-#define UIAS_NUM_SOURCES               8
-
-#define UI_MAX_MASTER_SERVERS   6
+#define AS_LOCAL			0
+#define AS_MPLAYER			1
+#define AS_GLOBAL			2
+#define AS_FAVORITES		3
 
 #define SORT_HOST			0
 #define SORT_MAP			1
 #define SORT_CLIENTS		2
 #define SORT_GAME			3
 #define SORT_PING			4
-#define SORT_NUM_SORTS		5
 
 #define GAMES_ALL			0
 #define GAMES_FFA			1
 #define GAMES_TEAMPLAY		2
 #define GAMES_TOURNEY		3
 #define GAMES_CTF			4
-#define GAMES_NUM_GAMES		5
 
 static const char *master_items[] = {
 	"Local",
 	"Internet",
-	"Master1",
-	"Master2",
-	"Master3",
-	"Master4",
-	"Master5",
 	"Favorites",
-	NULL
+	0
 };
 
 static const char *servertype_items[] = {
@@ -124,7 +110,7 @@
 	"Team Deathmatch",
 	"Tournament",
 	"Capture the Flag",
-	NULL
+	0
 };
 
 static const char *sortkey_items[] = {
@@ -133,7 +119,7 @@
 	"Open Player Spots",
 	"Game Type",
 	"Ping Time",
-	NULL
+	0
 };
 
 static char* gamenames[] = {
@@ -150,13 +136,13 @@
 	"Urban Terror",		// Urban Terror
 	"OSP",						// Orange Smoothie Productions
 	"???",			// unknown
-	NULL
+	0
 };
 
 static char* netnames[] = {
-	"??? ",
-	"UDP ",
-	"UDP6",
+	"???",
+	"UDP",
+	"IPX",
 	NULL
 };
 
@@ -249,12 +235,14 @@
 static arenaservers_t	g_arenaservers;
 
 
-static servernode_t             g_globalserverlist[UI_MAX_MASTER_SERVERS][MAX_GLOBALSERVERS];
-static int                              g_numglobalservers[UI_MAX_MASTER_SERVERS];
+static servernode_t		g_globalserverlist[MAX_GLOBALSERVERS];
+static int				g_numglobalservers;
 static servernode_t		g_localserverlist[MAX_LOCALSERVERS];
 static int				g_numlocalservers;
 static servernode_t		g_favoriteserverlist[MAX_FAVORITESERVERS];
 static int				g_numfavoriteservers;
+static servernode_t		g_mplayerserverlist[MAX_GLOBALSERVERS];
+static int				g_nummplayerservers;
 static int				g_servertype;
 static int				g_gametype;
 static int				g_sortkey;
@@ -340,29 +328,6 @@
 	return 0;
 }
 
-/*
-=================
-ArenaServers_SourceForLAN
-
-Convert ui's g_servertype to AS_* used by trap calls.
-=================
-*/
-int ArenaServers_SourceForLAN(void) {
-	switch( g_servertype ) {
-	default:
-	case UIAS_LOCAL:
-		return AS_LOCAL;
-	case UIAS_GLOBAL0:
-	case UIAS_GLOBAL1:
-	case UIAS_GLOBAL2:
-	case UIAS_GLOBAL3:
-	case UIAS_GLOBAL4:
-	case UIAS_GLOBAL5:
-		return AS_GLOBAL;
-	case UIAS_FAVORITES:
-		return AS_FAVORITES;
-	}
-}
 
 /*
 =================
@@ -427,6 +392,7 @@
 		}
 		else {
 			// all servers pinged - enable controls
+			g_arenaservers.master.generic.flags		&= ~QMF_GRAYED;
 			g_arenaservers.gametype.generic.flags	&= ~QMF_GRAYED;
 			g_arenaservers.sortkey.generic.flags	&= ~QMF_GRAYED;
 			g_arenaservers.showempty.generic.flags	&= ~QMF_GRAYED;
@@ -437,7 +403,7 @@
 			g_arenaservers.punkbuster.generic.flags &= ~QMF_GRAYED;
 
 			// update status bar
-			if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+			if( g_servertype == AS_GLOBAL || g_servertype == AS_MPLAYER ) {
 				g_arenaservers.statusbar.string = quake3worldMessage;
 			}
 			else {
@@ -453,6 +419,7 @@
 			g_arenaservers.statusbar.string = "Press SPACE to stop";
 
 			// disable controls during refresh
+			g_arenaservers.master.generic.flags		|= QMF_GRAYED;
 			g_arenaservers.gametype.generic.flags	|= QMF_GRAYED;
 			g_arenaservers.sortkey.generic.flags	|= QMF_GRAYED;
 			g_arenaservers.showempty.generic.flags	|= QMF_GRAYED;
@@ -471,7 +438,7 @@
 			}
 
 			// update status bar
-			if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+			if( g_servertype == AS_GLOBAL || g_servertype == AS_MPLAYER ) {
 				g_arenaservers.statusbar.string = quake3worldMessage;
 			}
 			else {
@@ -562,7 +529,7 @@
 			pingColor = S_COLOR_RED;
 		}
 
-		Com_sprintf( buff, MAX_LISTBOXWIDTH, "%-20.20s %-12.12s %2d/%2d %-8.8s %4s%s%3d " S_COLOR_YELLOW "%s", 
+		Com_sprintf( buff, MAX_LISTBOXWIDTH, "%-20.20s %-12.12s %2d/%2d %-8.8s %3s %s%3d " S_COLOR_YELLOW "%s", 
 			servernodeptr->hostname, servernodeptr->mapname, servernodeptr->numclients,
  			servernodeptr->maxclients, servernodeptr->gamename,
 			netnames[servernodeptr->nettype], pingColor, servernodeptr->pingtime, servernodeptr->bPB ? "Yes" : "No" );
@@ -601,37 +568,34 @@
 
 	// find address in master list
 	for (i=0; i<g_arenaservers.numfavoriteaddresses; i++)
-	{
 		if (!Q_stricmp(g_arenaservers.favoriteaddresses[i],servernodeptr->adrstr))
+				break;
+
+	// delete address from master list
+	if (i <= g_arenaservers.numfavoriteaddresses-1)
+	{
+		if (i < g_arenaservers.numfavoriteaddresses-1)
 		{
-			// delete address from master list
-			if (i < g_arenaservers.numfavoriteaddresses-1)
-			{
-				// shift items up
-				memcpy( &g_arenaservers.favoriteaddresses[i], &g_arenaservers.favoriteaddresses[i+1], (g_arenaservers.numfavoriteaddresses - i - 1)* MAX_ADDRESSLENGTH );
-			}
-			g_arenaservers.numfavoriteaddresses--;
-			memset( &g_arenaservers.favoriteaddresses[g_arenaservers.numfavoriteaddresses], 0, MAX_ADDRESSLENGTH );
-			break;
+			// shift items up
+			memcpy( &g_arenaservers.favoriteaddresses[i], &g_arenaservers.favoriteaddresses[i+1], (g_arenaservers.numfavoriteaddresses - i - 1)*sizeof(MAX_ADDRESSLENGTH));
 		}
+		g_arenaservers.numfavoriteaddresses--;
 	}	
 
 	// find address in server list
 	for (i=0; i<g_numfavoriteservers; i++)
-	{
 		if (&g_favoriteserverlist[i] == servernodeptr)
-		{
+				break;
 
-			// delete address from server list
-			if (i < g_numfavoriteservers-1)
-			{
-				// shift items up
-				memcpy( &g_favoriteserverlist[i], &g_favoriteserverlist[i+1], (g_numfavoriteservers - i - 1)*sizeof(servernode_t));
-			}
-			g_numfavoriteservers--;
-			memset( &g_favoriteserverlist[ g_numfavoriteservers ], 0, sizeof(servernode_t));
-			break;
+	// delete address from server list
+	if (i <= g_numfavoriteservers-1)
+	{
+		if (i < g_numfavoriteservers-1)
+		{
+			// shift items up
+			memcpy( &g_favoriteserverlist[i], &g_favoriteserverlist[i+1], (g_numfavoriteservers - i - 1)*sizeof(servernode_t));
 		}
+		g_numfavoriteservers--;
 	}	
 
 	g_arenaservers.numqueriedservers = g_arenaservers.numfavoriteaddresses;
@@ -651,7 +615,7 @@
 	int				i;
 
 
-	if ((pingtime >= ArenaServers_MaxPing()) && (g_servertype != UIAS_FAVORITES))
+	if ((pingtime >= ArenaServers_MaxPing()) && (g_servertype != AS_FAVORITES))
 	{
 		// slow global or local servers do not get entered
 		return;
@@ -700,9 +664,6 @@
 	}
 	*/
 	servernodeptr->nettype = atoi(Info_ValueForKey(info, "nettype"));
-	if (servernodeptr->nettype < 0 || servernodeptr->nettype >= ARRAY_LEN(netnames) - 1) {
-		servernodeptr->nettype = 0;
-	}
 
 	s = Info_ValueForKey( info, "game");
 	i = atoi( Info_ValueForKey( info, "gametype") );
@@ -725,6 +686,38 @@
 
 /*
 =================
+ArenaServers_InsertFavorites
+
+Insert nonresponsive address book entries into display lists.
+=================
+*/
+void ArenaServers_InsertFavorites( void )
+{
+	int		i;
+	int		j;
+	char	info[MAX_INFO_STRING];
+
+	// resync existing results with new or deleted cvars
+	info[0] = '\0';
+	Info_SetValueForKey( info, "hostname", "No Response" );
+	for (i=0; i<g_arenaservers.numfavoriteaddresses; i++)
+	{
+		// find favorite address in refresh list
+		for (j=0; j<g_numfavoriteservers; j++)
+			if (!Q_stricmp(g_arenaservers.favoriteaddresses[i],g_favoriteserverlist[j].adrstr))
+				break;
+
+		if ( j >= g_numfavoriteservers)
+		{
+			// not in list, add it
+			ArenaServers_Insert( g_arenaservers.favoriteaddresses[i], info, ArenaServers_MaxPing() );
+		}
+	}
+}
+
+
+/*
+=================
 ArenaServers_LoadFavorites
 
 Load cvar address book entries into local lists.
@@ -735,11 +728,13 @@
 	int				i;
 	int				j;
 	int				numtempitems;
+	char			emptyinfo[MAX_INFO_STRING];
 	char			adrstr[MAX_ADDRESSLENGTH];
 	servernode_t	templist[MAX_FAVORITESERVERS];
 	qboolean		found;
 
 	found        = qfalse;
+	emptyinfo[0] = '\0';
 
 	// copy the old
 	memcpy( templist, g_favoriteserverlist, sizeof(servernode_t)*MAX_FAVORITESERVERS );
@@ -756,6 +751,11 @@
 		if (!adrstr[0])
 			continue;
 
+		// quick sanity check to avoid slow domain name resolving
+		// first character must be numeric
+		if (adrstr[0] < '0' || adrstr[0] > '9')
+			continue;
+
 		// favorite server addresses must be maintained outside refresh list
 		// this mimics local and global netadr's stored in client
 		// these can be fetched to fill ping list
@@ -806,6 +806,12 @@
 
 	g_arenaservers.refreshservers = qfalse;
 
+	if (g_servertype == AS_FAVORITES)
+	{
+		// nonresponsive favorites must be shown
+		ArenaServers_InsertFavorites();
+	}
+
 	// final tally
 	if (g_arenaservers.numqueriedservers >= 0)
 	{
@@ -836,24 +842,17 @@
 
 	if (uis.realtime < g_arenaservers.refreshtime)
 	{
-	  if (g_servertype != UIAS_FAVORITES) {
-			if (g_servertype == UIAS_LOCAL) {
-				if (!trap_LAN_GetServerCount(AS_LOCAL)) {
+	  if (g_servertype != AS_FAVORITES) {
+			if (g_servertype == AS_LOCAL) {
+				if (!trap_LAN_GetServerCount(g_servertype)) {
 					return;
 				}
 			}
-			if (trap_LAN_GetServerCount(ArenaServers_SourceForLAN()) < 0) {
+			if (trap_LAN_GetServerCount(g_servertype) < 0) {
 			  // still waiting for response
 			  return;
 			}
 	  }
-	} else if (g_servertype == UIAS_LOCAL) {
-		if (!trap_LAN_GetServerCount(AS_LOCAL)) {
-			// no local servers found, check again
-			trap_Cmd_ExecuteText( EXEC_APPEND, "localservers\n" );
-			g_arenaservers.refreshtime = uis.realtime + 5000;
-			return;
-		}
 	}
 
 	if (uis.realtime < g_arenaservers.nextpingtime)
@@ -899,12 +898,6 @@
 				// stale it out
 				info[0] = '\0';
 				time    = maxPing;
-
-				// set hostname for nonresponsive favorite server
-				if (g_servertype == UIAS_FAVORITES) {
-					Info_SetValueForKey( info, "hostname", adrstr );
-					Info_SetValueForKey( info, "game", "???" );
-				}
 			}
 			else
 			{
@@ -924,10 +917,10 @@
 
 	// get results of servers query
 	// counts can increase as servers respond
-	if (g_servertype == UIAS_FAVORITES) {
+	if (g_servertype == AS_FAVORITES) {
 	  g_arenaservers.numqueriedservers = g_arenaservers.numfavoriteaddresses;
 	} else {
-		g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(ArenaServers_SourceForLAN());
+	  g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(g_servertype);
 	}
 
 //	if (g_arenaservers.numqueriedservers > g_arenaservers.maxservers)
@@ -954,10 +947,10 @@
 
 		// get an address to ping
 
-		if (g_servertype == UIAS_FAVORITES) {
+		if (g_servertype == AS_FAVORITES) {
 		  strcpy( adrstr, g_arenaservers.favoriteaddresses[g_arenaservers.currentping] ); 		
 		} else {
-			trap_LAN_GetServerAddressString(ArenaServers_SourceForLAN(), g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
+		  trap_LAN_GetServerAddressString(g_servertype, g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
 		}
 
 		strcpy( g_arenaservers.pinglist[j].adrstr, adrstr );
@@ -1011,12 +1004,19 @@
 	// place menu in zeroed state
 	ArenaServers_UpdateMenu();
 
-	if( g_servertype == UIAS_LOCAL ) {
+	if( g_servertype == AS_LOCAL ) {
 		trap_Cmd_ExecuteText( EXEC_APPEND, "localservers\n" );
 		return;
 	}
 
-	if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+	if( g_servertype == AS_GLOBAL || g_servertype == AS_MPLAYER ) {
+		if( g_servertype == AS_GLOBAL ) {
+			i = 0;
+		}
+		else {
+			i = 1;
+		}
+
 		switch( g_arenaservers.gametype.curvalue ) {
 		default:
 		case GAMES_ALL:
@@ -1052,10 +1052,10 @@
 		protocol[0] = '\0';
 		trap_Cvar_VariableStringBuffer( "debug_protocol", protocol, sizeof(protocol) );
 		if (strlen(protocol)) {
-			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %s%s\n", g_servertype - UIAS_GLOBAL0, protocol, myargs ));
+			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %s%s\n", i, protocol, myargs ));
 		}
 		else {
-			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %d%s\n", g_servertype - UIAS_GLOBAL0, (int)trap_Cvar_VariableValue( "protocol" ), myargs ) );
+			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %d%s\n", i, (int)trap_Cvar_VariableValue( "protocol" ), myargs ) );
 		}
 	}
 }
@@ -1098,62 +1098,43 @@
 ArenaServers_SetType
 =================
 */
-int ArenaServers_SetType( int type )
+void ArenaServers_SetType( int type )
 {
-	ArenaServers_StopRefresh();
-
-	if(type >= UIAS_GLOBAL1 && type <= UIAS_GLOBAL5)
-	{
-		char masterstr[2], cvarname[sizeof("sv_master1")];
-		int direction;
-
-		if (type == g_servertype || type == ((g_servertype+1) % UIAS_NUM_SOURCES)) {
-			direction = 1;
-		} else {
-			direction = -1;
-		}
-
-		while(type >= UIAS_GLOBAL1 && type <= UIAS_GLOBAL5)
-		{
-			Com_sprintf(cvarname, sizeof(cvarname), "sv_master%d", type - UIAS_GLOBAL0);
-			trap_Cvar_VariableStringBuffer(cvarname, masterstr, sizeof(masterstr));
-			if(*masterstr)
-				break;
-			
-			type += direction;
-		}
-	}
+	if (g_servertype == type)
+		return;
 
 	g_servertype = type;
 
 	switch( type ) {
 	default:
-	case UIAS_LOCAL:
+	case AS_LOCAL:
 		g_arenaservers.remove.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
 		g_arenaservers.serverlist = g_localserverlist;
 		g_arenaservers.numservers = &g_numlocalservers;
 		g_arenaservers.maxservers = MAX_LOCALSERVERS;
 		break;
 
-	case UIAS_GLOBAL0:
-	case UIAS_GLOBAL1:
-	case UIAS_GLOBAL2:
-	case UIAS_GLOBAL3:
-	case UIAS_GLOBAL4:
-	case UIAS_GLOBAL5:
+	case AS_GLOBAL:
 		g_arenaservers.remove.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
-		g_arenaservers.serverlist = g_globalserverlist[type-UIAS_GLOBAL0];
-		g_arenaservers.numservers = &g_numglobalservers[type-UIAS_GLOBAL0];
+		g_arenaservers.serverlist = g_globalserverlist;
+		g_arenaservers.numservers = &g_numglobalservers;
 		g_arenaservers.maxservers = MAX_GLOBALSERVERS;
 		break;
 
-	case UIAS_FAVORITES:
+	case AS_FAVORITES:
 		g_arenaservers.remove.generic.flags &= ~(QMF_INACTIVE|QMF_HIDDEN);
 		g_arenaservers.serverlist = g_favoriteserverlist;
 		g_arenaservers.numservers = &g_numfavoriteservers;
 		g_arenaservers.maxservers = MAX_FAVORITESERVERS;
 		break;
 
+	case AS_MPLAYER:
+		g_arenaservers.remove.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
+		g_arenaservers.serverlist = g_mplayerserverlist;
+		g_arenaservers.numservers = &g_nummplayerservers;
+		g_arenaservers.maxservers = MAX_GLOBALSERVERS;
+		break;
+		
 	}
 
 	if( !*g_arenaservers.numservers ) {
@@ -1164,10 +1145,8 @@
 		g_arenaservers.currentping       = *g_arenaservers.numservers;
 		g_arenaservers.numqueriedservers = *g_arenaservers.numservers; 
 		ArenaServers_UpdateMenu();
-		strcpy(g_arenaservers.status.string,"hit refresh to update");
 	}
-
-	return type;
+	strcpy(g_arenaservers.status.string,"hit refresh to update");
 }
 
 /*
@@ -1199,6 +1178,7 @@
 */
 static void ArenaServers_Event( void* ptr, int event ) {
 	int		id;
+	int value;
 
 	id = ((menucommon_s*)ptr)->id;
 
@@ -1208,8 +1188,13 @@
 
 	switch( id ) {
 	case ID_MASTER:
-		g_arenaservers.master.curvalue = ArenaServers_SetType(g_arenaservers.master.curvalue);
-		trap_Cvar_SetValue( "ui_browserMaster", g_arenaservers.master.curvalue);
+		value = g_arenaservers.master.curvalue;
+		if (value >= 1)
+		{
+			value++;
+		}
+		trap_Cvar_SetValue( "ui_browserMaster", value );
+		ArenaServers_SetType( value );
 		break;
 
 	case ID_GAMETYPE:
@@ -1280,11 +1265,11 @@
 	case ID_PUNKBUSTER:
 		if (g_arenaservers.punkbuster.curvalue)			
 		{
-			UI_ConfirmMenu_Style( "Enable Punkbuster?",  UI_CENTER|UI_INVERSE|UI_SMALLFONT, 0, Punkbuster_ConfirmEnable );
+			UI_ConfirmMenu_Style( "Enable Punkbuster?",  UI_CENTER|UI_INVERSE|UI_SMALLFONT, (voidfunc_f)NULL, Punkbuster_ConfirmEnable );
 		}
 		else
 		{
-			UI_ConfirmMenu_Style( "Disable Punkbuster?", UI_CENTER|UI_INVERSE|UI_SMALLFONT, 0, Punkbuster_ConfirmDisable );
+			UI_ConfirmMenu_Style( "Disable Punkbuster?", UI_CENTER|UI_INVERSE|UI_SMALLFONT, (voidfunc_f)NULL, Punkbuster_ConfirmDisable );
 		}
 		break;
 	}
@@ -1316,7 +1301,7 @@
 		return menu_move_sound;
 	}
 
-	if( ( key == K_DEL || key == K_KP_DEL ) && ( g_servertype == UIAS_FAVORITES ) &&
+	if( ( key == K_DEL || key == K_KP_DEL ) && ( g_servertype == AS_FAVORITES ) &&
 		( Menu_ItemAtCursor( &g_arenaservers.menu) == &g_arenaservers.list ) ) {
 		ArenaServers_Remove();
 		ArenaServers_UpdateMenu();
@@ -1340,7 +1325,9 @@
 */
 static void ArenaServers_MenuInit( void ) {
 	int			i;
+	int			type;
 	int			y;
+	int			value;
 	static char	statusbuffer[MAX_STATUSLENGTH];
 
 	// zero set all our globals
@@ -1569,12 +1556,12 @@
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.showempty );
 
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.mappic );
+	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.list );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.status );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.statusbar );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.arrows );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.up );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.down );
-	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.list );
 
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.remove );
 	Menu_AddItem( &g_arenaservers.menu, (void*) &g_arenaservers.back );
@@ -1588,12 +1575,17 @@
 	
 	ArenaServers_LoadFavorites();
 
-	g_arenaservers.master.curvalue = g_servertype = Com_Clamp( 0, UIAS_NUM_SOURCES-1, ui_browserMaster.integer );
+	g_servertype = Com_Clamp( 0, 3, ui_browserMaster.integer );
+	// hack to get rid of MPlayer stuff
+	value = g_servertype;
+	if (value >= 1)
+		value--;
+	g_arenaservers.master.curvalue = value;
 
-	g_gametype = Com_Clamp( 0, GAMES_NUM_GAMES-1, ui_browserGameType.integer );
+	g_gametype = Com_Clamp( 0, 4, ui_browserGameType.integer );
 	g_arenaservers.gametype.curvalue = g_gametype;
 
-	g_sortkey = Com_Clamp( 0, SORT_NUM_SORTS-1, ui_browserSortKey.integer );
+	g_sortkey = Com_Clamp( 0, 4, ui_browserSortKey.integer );
 	g_arenaservers.sortkey.curvalue = g_sortkey;
 
 	g_fullservers = Com_Clamp( 0, 1, ui_browserShowFull.integer );
@@ -1605,7 +1597,9 @@
 	g_arenaservers.punkbuster.curvalue = Com_Clamp( 0, 1, trap_Cvar_VariableValue( "cl_punkbuster" ) );
 
 	// force to initial state and refresh
-	g_arenaservers.master.curvalue = g_servertype = ArenaServers_SetType(g_servertype);
+	type = g_servertype;
+	g_servertype = -1;
+	ArenaServers_SetType( type );
 
 	trap_Cvar_Register(NULL, "debug_protocol", "", 0 );
 }

```

### `ioquake3`  — sha256 `0cb7dcadf77e...`, 47213 bytes

_Diff stat: +15 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_servers2.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_servers2.c	2026-04-16 20:02:21.559592100 +0100
@@ -81,16 +81,16 @@
 #define GR_LETTERS			31
 
 #define UIAS_LOCAL			0
-#define UIAS_GLOBAL0                   1
-#define UIAS_GLOBAL1                   2
-#define UIAS_GLOBAL2                   3
-#define UIAS_GLOBAL3                   4
-#define UIAS_GLOBAL4                   5
-#define UIAS_GLOBAL5                   6
-#define UIAS_FAVORITES                 7
-#define UIAS_NUM_SOURCES               8
+#define UIAS_GLOBAL0			1
+#define UIAS_GLOBAL1			2
+#define UIAS_GLOBAL2			3
+#define UIAS_GLOBAL3			4
+#define UIAS_GLOBAL4			5
+#define UIAS_GLOBAL5			6
+#define UIAS_FAVORITES			7
+#define UIAS_NUM_SOURCES		8
 
-#define UI_MAX_MASTER_SERVERS   6
+#define UI_MAX_MASTER_SERVERS	6
 
 #define SORT_HOST			0
 #define SORT_MAP			1
@@ -249,8 +249,8 @@
 static arenaservers_t	g_arenaservers;
 
 
-static servernode_t             g_globalserverlist[UI_MAX_MASTER_SERVERS][MAX_GLOBALSERVERS];
-static int                              g_numglobalservers[UI_MAX_MASTER_SERVERS];
+static servernode_t		g_globalserverlist[UI_MAX_MASTER_SERVERS][MAX_GLOBALSERVERS];
+static int				g_numglobalservers[UI_MAX_MASTER_SERVERS];
 static servernode_t		g_localserverlist[MAX_LOCALSERVERS];
 static int				g_numlocalservers;
 static servernode_t		g_favoriteserverlist[MAX_FAVORITESERVERS];
@@ -927,7 +927,7 @@
 	if (g_servertype == UIAS_FAVORITES) {
 	  g_arenaservers.numqueriedservers = g_arenaservers.numfavoriteaddresses;
 	} else {
-		g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(ArenaServers_SourceForLAN());
+	  g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(ArenaServers_SourceForLAN());
 	}
 
 //	if (g_arenaservers.numqueriedservers > g_arenaservers.maxservers)
@@ -957,7 +957,7 @@
 		if (g_servertype == UIAS_FAVORITES) {
 		  strcpy( adrstr, g_arenaservers.favoriteaddresses[g_arenaservers.currentping] ); 		
 		} else {
-			trap_LAN_GetServerAddressString(ArenaServers_SourceForLAN(), g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
+		  trap_LAN_GetServerAddressString(ArenaServers_SourceForLAN(), g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
 		}
 
 		strcpy( g_arenaservers.pinglist[j].adrstr, adrstr );
@@ -1106,7 +1106,7 @@
 	{
 		char masterstr[2], cvarname[sizeof("sv_master1")];
 		int direction;
-
+		
 		if (type == g_servertype || type == ((g_servertype+1) % UIAS_NUM_SOURCES)) {
 			direction = 1;
 		} else {
@@ -1166,7 +1166,7 @@
 		ArenaServers_UpdateMenu();
 		strcpy(g_arenaservers.status.string,"hit refresh to update");
 	}
-
+	
 	return type;
 }
 

```

### `openarena-engine`  — sha256 `b3bdf29a7933...`, 47311 bytes

_Diff stat: +71 / -60 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_servers2.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_servers2.c	2026-04-16 22:48:25.900194200 +0100
@@ -81,39 +81,34 @@
 #define GR_LETTERS			31
 
 #define UIAS_LOCAL			0
-#define UIAS_GLOBAL0                   1
-#define UIAS_GLOBAL1                   2
-#define UIAS_GLOBAL2                   3
-#define UIAS_GLOBAL3                   4
-#define UIAS_GLOBAL4                   5
-#define UIAS_GLOBAL5                   6
-#define UIAS_FAVORITES                 7
-#define UIAS_NUM_SOURCES               8
+#define UIAS_GLOBAL1			1
+#define UIAS_GLOBAL2			2
+#define UIAS_GLOBAL3			3
+#define UIAS_GLOBAL4			4
+#define UIAS_GLOBAL5			5
+#define UIAS_FAVORITES			6
 
-#define UI_MAX_MASTER_SERVERS   6
+#define UI_MAX_MASTER_SERVERS	5
 
 #define SORT_HOST			0
 #define SORT_MAP			1
 #define SORT_CLIENTS		2
 #define SORT_GAME			3
 #define SORT_PING			4
-#define SORT_NUM_SORTS		5
 
 #define GAMES_ALL			0
 #define GAMES_FFA			1
 #define GAMES_TEAMPLAY		2
 #define GAMES_TOURNEY		3
 #define GAMES_CTF			4
-#define GAMES_NUM_GAMES		5
 
 static const char *master_items[] = {
 	"Local",
-	"Internet",
-	"Master1",
-	"Master2",
-	"Master3",
-	"Master4",
-	"Master5",
+	"Internet1",
+	"Internet2",
+	"Internet3",
+	"Internet4",
+	"Internet5",
 	"Favorites",
 	NULL
 };
@@ -249,8 +244,8 @@
 static arenaservers_t	g_arenaservers;
 
 
-static servernode_t             g_globalserverlist[UI_MAX_MASTER_SERVERS][MAX_GLOBALSERVERS];
-static int                              g_numglobalservers[UI_MAX_MASTER_SERVERS];
+static servernode_t		g_globalserverlist[UI_MAX_MASTER_SERVERS][MAX_GLOBALSERVERS];
+static int				g_numglobalservers[UI_MAX_MASTER_SERVERS];
 static servernode_t		g_localserverlist[MAX_LOCALSERVERS];
 static int				g_numlocalservers;
 static servernode_t		g_favoriteserverlist[MAX_FAVORITESERVERS];
@@ -352,7 +347,6 @@
 	default:
 	case UIAS_LOCAL:
 		return AS_LOCAL;
-	case UIAS_GLOBAL0:
 	case UIAS_GLOBAL1:
 	case UIAS_GLOBAL2:
 	case UIAS_GLOBAL3:
@@ -427,6 +421,7 @@
 		}
 		else {
 			// all servers pinged - enable controls
+			g_arenaservers.master.generic.flags		&= ~QMF_GRAYED;
 			g_arenaservers.gametype.generic.flags	&= ~QMF_GRAYED;
 			g_arenaservers.sortkey.generic.flags	&= ~QMF_GRAYED;
 			g_arenaservers.showempty.generic.flags	&= ~QMF_GRAYED;
@@ -437,7 +432,7 @@
 			g_arenaservers.punkbuster.generic.flags &= ~QMF_GRAYED;
 
 			// update status bar
-			if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+			if( g_servertype >= UIAS_GLOBAL1 && g_servertype <= UIAS_GLOBAL5 ) {
 				g_arenaservers.statusbar.string = quake3worldMessage;
 			}
 			else {
@@ -453,6 +448,7 @@
 			g_arenaservers.statusbar.string = "Press SPACE to stop";
 
 			// disable controls during refresh
+			g_arenaservers.master.generic.flags		|= QMF_GRAYED;
 			g_arenaservers.gametype.generic.flags	|= QMF_GRAYED;
 			g_arenaservers.sortkey.generic.flags	|= QMF_GRAYED;
 			g_arenaservers.showempty.generic.flags	|= QMF_GRAYED;
@@ -471,7 +467,7 @@
 			}
 
 			// update status bar
-			if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+			if( g_servertype >= UIAS_GLOBAL1 && g_servertype <= UIAS_GLOBAL5 ) {
 				g_arenaservers.statusbar.string = quake3worldMessage;
 			}
 			else {
@@ -725,6 +721,38 @@
 
 /*
 =================
+ArenaServers_InsertFavorites
+
+Insert nonresponsive address book entries into display lists.
+=================
+*/
+void ArenaServers_InsertFavorites( void )
+{
+	int		i;
+	int		j;
+	char	info[MAX_INFO_STRING];
+
+	// resync existing results with new or deleted cvars
+	info[0] = '\0';
+	Info_SetValueForKey( info, "hostname", "No Response" );
+	for (i=0; i<g_arenaservers.numfavoriteaddresses; i++)
+	{
+		// find favorite address in refresh list
+		for (j=0; j<g_numfavoriteservers; j++)
+			if (!Q_stricmp(g_arenaservers.favoriteaddresses[i],g_favoriteserverlist[j].adrstr))
+				break;
+
+		if ( j >= g_numfavoriteservers)
+		{
+			// not in list, add it
+			ArenaServers_Insert( g_arenaservers.favoriteaddresses[i], info, ArenaServers_MaxPing() );
+		}
+	}
+}
+
+
+/*
+=================
 ArenaServers_LoadFavorites
 
 Load cvar address book entries into local lists.
@@ -806,6 +834,12 @@
 
 	g_arenaservers.refreshservers = qfalse;
 
+	if (g_servertype == UIAS_FAVORITES)
+	{
+		// nonresponsive favorites must be shown
+		ArenaServers_InsertFavorites();
+	}
+
 	// final tally
 	if (g_arenaservers.numqueriedservers >= 0)
 	{
@@ -847,13 +881,6 @@
 			  return;
 			}
 	  }
-	} else if (g_servertype == UIAS_LOCAL) {
-		if (!trap_LAN_GetServerCount(AS_LOCAL)) {
-			// no local servers found, check again
-			trap_Cmd_ExecuteText( EXEC_APPEND, "localservers\n" );
-			g_arenaservers.refreshtime = uis.realtime + 5000;
-			return;
-		}
 	}
 
 	if (uis.realtime < g_arenaservers.nextpingtime)
@@ -899,12 +926,6 @@
 				// stale it out
 				info[0] = '\0';
 				time    = maxPing;
-
-				// set hostname for nonresponsive favorite server
-				if (g_servertype == UIAS_FAVORITES) {
-					Info_SetValueForKey( info, "hostname", adrstr );
-					Info_SetValueForKey( info, "game", "???" );
-				}
 			}
 			else
 			{
@@ -927,7 +948,7 @@
 	if (g_servertype == UIAS_FAVORITES) {
 	  g_arenaservers.numqueriedservers = g_arenaservers.numfavoriteaddresses;
 	} else {
-		g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(ArenaServers_SourceForLAN());
+	  g_arenaservers.numqueriedservers = trap_LAN_GetServerCount(ArenaServers_SourceForLAN());
 	}
 
 //	if (g_arenaservers.numqueriedservers > g_arenaservers.maxservers)
@@ -957,7 +978,7 @@
 		if (g_servertype == UIAS_FAVORITES) {
 		  strcpy( adrstr, g_arenaservers.favoriteaddresses[g_arenaservers.currentping] ); 		
 		} else {
-			trap_LAN_GetServerAddressString(ArenaServers_SourceForLAN(), g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
+		  trap_LAN_GetServerAddressString(ArenaServers_SourceForLAN(), g_arenaservers.currentping, adrstr, MAX_ADDRESSLENGTH );
 		}
 
 		strcpy( g_arenaservers.pinglist[j].adrstr, adrstr );
@@ -1016,7 +1037,7 @@
 		return;
 	}
 
-	if( g_servertype >= UIAS_GLOBAL0 && g_servertype <= UIAS_GLOBAL5 ) {
+	if( g_servertype >= UIAS_GLOBAL1 && g_servertype <= UIAS_GLOBAL5 ) {
 		switch( g_arenaservers.gametype.curvalue ) {
 		default:
 		case GAMES_ALL:
@@ -1052,10 +1073,10 @@
 		protocol[0] = '\0';
 		trap_Cvar_VariableStringBuffer( "debug_protocol", protocol, sizeof(protocol) );
 		if (strlen(protocol)) {
-			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %s%s\n", g_servertype - UIAS_GLOBAL0, protocol, myargs ));
+			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %s%s\n", g_servertype - 1, protocol, myargs ));
 		}
 		else {
-			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %d%s\n", g_servertype - UIAS_GLOBAL0, (int)trap_Cvar_VariableValue( "protocol" ), myargs ) );
+			trap_Cmd_ExecuteText( EXEC_APPEND, va( "globalservers %d %d%s\n", g_servertype - 1, (int)trap_Cvar_VariableValue( "protocol" ), myargs ) );
 		}
 	}
 }
@@ -1100,27 +1121,18 @@
 */
 int ArenaServers_SetType( int type )
 {
-	ArenaServers_StopRefresh();
-
 	if(type >= UIAS_GLOBAL1 && type <= UIAS_GLOBAL5)
 	{
 		char masterstr[2], cvarname[sizeof("sv_master1")];
-		int direction;
-
-		if (type == g_servertype || type == ((g_servertype+1) % UIAS_NUM_SOURCES)) {
-			direction = 1;
-		} else {
-			direction = -1;
-		}
-
-		while(type >= UIAS_GLOBAL1 && type <= UIAS_GLOBAL5)
+		
+		while(type <= UIAS_GLOBAL5)
 		{
-			Com_sprintf(cvarname, sizeof(cvarname), "sv_master%d", type - UIAS_GLOBAL0);
+			Com_sprintf(cvarname, sizeof(cvarname), "sv_master%d", type);
 			trap_Cvar_VariableStringBuffer(cvarname, masterstr, sizeof(masterstr));
 			if(*masterstr)
 				break;
 			
-			type += direction;
+			type++;
 		}
 	}
 
@@ -1135,15 +1147,14 @@
 		g_arenaservers.maxservers = MAX_LOCALSERVERS;
 		break;
 
-	case UIAS_GLOBAL0:
 	case UIAS_GLOBAL1:
 	case UIAS_GLOBAL2:
 	case UIAS_GLOBAL3:
 	case UIAS_GLOBAL4:
 	case UIAS_GLOBAL5:
 		g_arenaservers.remove.generic.flags |= (QMF_INACTIVE|QMF_HIDDEN);
-		g_arenaservers.serverlist = g_globalserverlist[type-UIAS_GLOBAL0];
-		g_arenaservers.numservers = &g_numglobalservers[type-UIAS_GLOBAL0];
+		g_arenaservers.serverlist = g_globalserverlist[type-UIAS_GLOBAL1];
+		g_arenaservers.numservers = &g_numglobalservers[type-UIAS_GLOBAL1];
 		g_arenaservers.maxservers = MAX_GLOBALSERVERS;
 		break;
 
@@ -1166,7 +1177,7 @@
 		ArenaServers_UpdateMenu();
 		strcpy(g_arenaservers.status.string,"hit refresh to update");
 	}
-
+	
 	return type;
 }
 
@@ -1588,12 +1599,12 @@
 	
 	ArenaServers_LoadFavorites();
 
-	g_arenaservers.master.curvalue = g_servertype = Com_Clamp( 0, UIAS_NUM_SOURCES-1, ui_browserMaster.integer );
+	g_arenaservers.master.curvalue = g_servertype = Com_Clamp( 0, 6, ui_browserMaster.integer );
 
-	g_gametype = Com_Clamp( 0, GAMES_NUM_GAMES-1, ui_browserGameType.integer );
+	g_gametype = Com_Clamp( 0, 4, ui_browserGameType.integer );
 	g_arenaservers.gametype.curvalue = g_gametype;
 
-	g_sortkey = Com_Clamp( 0, SORT_NUM_SORTS-1, ui_browserSortKey.integer );
+	g_sortkey = Com_Clamp( 0, 4, ui_browserSortKey.integer );
 	g_arenaservers.sortkey.curvalue = g_sortkey;
 
 	g_fullservers = Com_Clamp( 0, 1, ui_browserShowFull.integer );

```

### `openarena-gamecode`  — sha256 `7bbd26afe87c...`, 54286 bytes

_Diff stat: +567 / -287 lines_

_(full diff is 43110 bytes — see files directly)_
