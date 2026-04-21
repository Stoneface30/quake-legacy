# Diff: `code/q3_ui/ui_teamorders.c`
**Canonical:** `wolfcamql-src` (sha256 `f67c9d4895f1...`, 11451 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `474c983a2e7d...`, 11422 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_teamorders.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_teamorders.c	2026-04-16 20:02:19.955611800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -312,16 +312,16 @@
 	numPlayers = atoi( Info_ValueForKey( info, "sv_maxclients" ) );
 	teamOrdersMenuInfo.gametype = atoi( Info_ValueForKey( info, "g_gametype" ) );
 
-	trap_GetConfigString( CS_PLAYERS + cs.clientNum, info, MAX_INFO_STRING );
-	playerTeam = *Info_ValueForKey( info, "t" );
-
 	for( n = 0; n < numPlayers && teamOrdersMenuInfo.numBots < 9; n++ ) {
+		trap_GetConfigString( CS_PLAYERS + n, info, MAX_INFO_STRING );
+
+		playerTeam = TEAM_SPECTATOR; // bk001204 = possible uninit use
+
 		if( n == cs.clientNum ) {
+			playerTeam = *Info_ValueForKey( info, "t" );
 			continue;
 		}
 
-		trap_GetConfigString( CS_PLAYERS + n, info, MAX_INFO_STRING );
-
 		isBot = atoi( Info_ValueForKey( info, "skill" ) );
 		if( !isBot ) {
 			continue;

```

### `openarena-engine`  — sha256 `7015fe983087...`, 11381 bytes

_Diff stat: +4 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_teamorders.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_teamorders.c	2026-04-16 22:48:25.903298800 +0100
@@ -295,7 +295,7 @@
 	int		numPlayers;
 	int		isBot;
 	int		n;
-	char	playerTeam;
+	char	playerTeam = '3';
 	char	botTeam;
 	char	info[MAX_INFO_STRING];
 
@@ -312,16 +312,14 @@
 	numPlayers = atoi( Info_ValueForKey( info, "sv_maxclients" ) );
 	teamOrdersMenuInfo.gametype = atoi( Info_ValueForKey( info, "g_gametype" ) );
 
-	trap_GetConfigString( CS_PLAYERS + cs.clientNum, info, MAX_INFO_STRING );
-	playerTeam = *Info_ValueForKey( info, "t" );
-
 	for( n = 0; n < numPlayers && teamOrdersMenuInfo.numBots < 9; n++ ) {
+		trap_GetConfigString( CS_PLAYERS + n, info, MAX_INFO_STRING );
+
 		if( n == cs.clientNum ) {
+			playerTeam = *Info_ValueForKey( info, "t" );
 			continue;
 		}
 
-		trap_GetConfigString( CS_PLAYERS + n, info, MAX_INFO_STRING );
-
 		isBot = atoi( Info_ValueForKey( info, "skill" ) );
 		if( !isBot ) {
 			continue;

```

### `openarena-gamecode`  — sha256 `22ca621c5598...`, 14573 bytes

_Diff stat: +170 / -53 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_teamorders.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_teamorders.c	2026-04-16 22:48:24.191007600 +0100
@@ -32,13 +32,16 @@
 #include "ui_local.h"
 
 
-#define ART_FRAME		"menu/art/addbotframe"
-#define ART_BACK0		"menu/art/back_0"
-#define ART_BACK1		"menu/art/back_1"	
+#define ART_FRAME		"menu/" MENU_ART_DIR "/addbotframe"
+#define ART_BACK0		"menu/" MENU_ART_DIR "/back_0"
+#define ART_BACK1		"menu/" MENU_ART_DIR "/back_1"
 
 #define ID_LIST_BOTS		10
 #define ID_LIST_CTF_ORDERS	11
-#define ID_LIST_TEAM_ORDERS	12
+#define ID_LIST_CTF1F_ORDERS	12
+#define ID_LIST_BASE_ORDERS	13
+#define ID_LIST_TEAM_ORDERS	14
+#define ID_LIST_DD_ORDERS	15
 
 
 typedef struct {
@@ -75,7 +78,51 @@
 	"i am the leader",
 	"%s defend the base",
 	"%s follow me",
-	"%s get enemy flag",
+	"%s get the enemy flag",
+	"%s camp here",
+	"%s report",
+	"i stop being the leader",
+	NULL
+};
+
+#define NUM_CTF1F_ORDERS		7
+static const char *ctf1fOrders[] = {
+	"I Am the Leader",
+	"Defend the Base",
+	"Follow Me",
+	"Get The Flag",
+	"Camp Here",
+	"Report",
+	"I Relinquish Command",
+	NULL
+};
+static const char *ctf1fMessages[] = {
+	"i am the leader",
+	"%s defend the base",
+	"%s follow me",
+	"%s get the flag",
+	"%s camp here",
+	"%s report",
+	"i stop being the leader",
+	NULL
+};
+
+#define NUM_BASE_ORDERS		7
+static const char *baseOrders[] = {
+	"I Am the Leader",
+	"Defend the Base",
+	"Follow Me",
+	"Attack the Enemy Base",
+	"Camp Here",
+	"Report",
+	"I Relinquish Command",
+	NULL
+};
+static const char *baseMessages[] = {
+	"i am the leader",
+	"%s defend the base",
+	"%s follow me",
+	"%s attack the base",
 	"%s camp here",
 	"%s report",
 	"i stop being the leader",
@@ -102,13 +149,37 @@
 	NULL
 };
 
+#define NUM_DD_ORDERS		8
+static const char *ddOrders[] = {
+	"I Am the Leader",
+	"Follow Me",
+	"Roam",
+	"Dominate Point A",
+	"Dominate Point B",
+	"Camp Here",
+	"Report",
+	"I Relinquish Command",
+	NULL
+};
+static const char *ddMessages[] = {
+	"i am the leader",
+	"%s follow me",
+	"%s roam",
+	"%s dominate point A",
+	"%s dominate point B",
+	"%s camp here",
+	"%s report",
+	"i stop being the leader",
+	NULL
+};
 
 /*
 ===============
 UI_TeamOrdersMenu_BackEvent
 ===============
 */
-static void UI_TeamOrdersMenu_BackEvent( void *ptr, int event ) {
+static void UI_TeamOrdersMenu_BackEvent( void *ptr, int event )
+{
 	if( event != QM_ACTIVATED ) {
 		return;
 	}
@@ -121,14 +192,15 @@
 UI_TeamOrdersMenu_SetList
 ===============
 */
-static void UI_TeamOrdersMenu_SetList( int id ) {
+static void UI_TeamOrdersMenu_SetList( int id )
+{
 	switch( id ) {
 	default:
 	case ID_LIST_BOTS:
 		teamOrdersMenuInfo.list.generic.id = id;
 		teamOrdersMenuInfo.list.numitems = teamOrdersMenuInfo.numBots;
 		teamOrdersMenuInfo.list.itemnames = (const char **)teamOrdersMenuInfo.bots;
-		 break;
+		break;
 
 	case ID_LIST_CTF_ORDERS:
 		teamOrdersMenuInfo.list.generic.id = id;
@@ -136,11 +208,29 @@
 		teamOrdersMenuInfo.list.itemnames = ctfOrders;
 		break;
 
+	case ID_LIST_CTF1F_ORDERS:
+		teamOrdersMenuInfo.list.generic.id = id;
+		teamOrdersMenuInfo.list.numitems = NUM_CTF1F_ORDERS;
+		teamOrdersMenuInfo.list.itemnames = ctf1fOrders;
+		break;
+
+	case ID_LIST_BASE_ORDERS:
+		teamOrdersMenuInfo.list.generic.id = id;
+		teamOrdersMenuInfo.list.numitems = NUM_BASE_ORDERS;
+		teamOrdersMenuInfo.list.itemnames = baseOrders;
+		break;
+
 	case ID_LIST_TEAM_ORDERS:
 		teamOrdersMenuInfo.list.generic.id = id;
 		teamOrdersMenuInfo.list.numitems = NUM_TEAM_ORDERS;
 		teamOrdersMenuInfo.list.itemnames = teamOrders;
 		break;
+
+	case ID_LIST_DD_ORDERS:
+		teamOrdersMenuInfo.list.generic.id = id;
+		teamOrdersMenuInfo.list.numitems = NUM_DD_ORDERS;
+		teamOrdersMenuInfo.list.itemnames = ddOrders;
+		break;
 	}
 
 	teamOrdersMenuInfo.list.generic.bottom = teamOrdersMenuInfo.list.generic.top + teamOrdersMenuInfo.list.numitems * PROP_HEIGHT;
@@ -152,7 +242,8 @@
 UI_TeamOrdersMenu_Key
 =================
 */
-sfxHandle_t UI_TeamOrdersMenu_Key( int key ) {
+sfxHandle_t UI_TeamOrdersMenu_Key( int key )
+{
 	menulist_s	*l;
 	int	x;
 	int	y;
@@ -164,44 +255,44 @@
 	}
 
 	switch( key ) {
-		case K_MOUSE1:
-			x = l->generic.left;
-			y = l->generic.top;
-			if( UI_CursorInRect( x, y, l->generic.right - x, l->generic.bottom - y ) ) {
-				index = (uis.cursory - y) / PROP_HEIGHT;
-				l->oldvalue = l->curvalue;
-				l->curvalue = index;
-
-				if( l->generic.callback ) {
-					l->generic.callback( l, QM_ACTIVATED );
-					return menu_move_sound;
-				}
-			}
-			return menu_null_sound;
-
-		case K_KP_UPARROW:
-		case K_UPARROW:
+	case K_MOUSE1:
+		x = l->generic.left;
+		y = l->generic.top;
+		if( UI_CursorInRect( x, y, l->generic.right - x, l->generic.bottom - y ) ) {
+			index = (uis.cursory - y) / PROP_HEIGHT;
 			l->oldvalue = l->curvalue;
+			l->curvalue = index;
 
-			if( l->curvalue == 0 ) {
-				l->curvalue = l->numitems - 1;
-			}
-			else {
-				l->curvalue--;
+			if( l->generic.callback ) {
+				l->generic.callback( l, QM_ACTIVATED );
+				return menu_move_sound;
 			}
-			return menu_move_sound;
+		}
+		return menu_null_sound;
 
-		case K_KP_DOWNARROW:
-		case K_DOWNARROW:
-			l->oldvalue = l->curvalue;
+	case K_KP_UPARROW:
+	case K_UPARROW:
+		l->oldvalue = l->curvalue;
 
-			if( l->curvalue == l->numitems - 1 ) {
-				l->curvalue = 0;;
-			}
-			else {
-				l->curvalue++;
-			}
-			return menu_move_sound;
+		if( l->curvalue == 0 ) {
+			l->curvalue = l->numitems - 1;
+		}
+		else {
+			l->curvalue--;
+		}
+		return menu_move_sound;
+
+	case K_KP_DOWNARROW:
+	case K_DOWNARROW:
+		l->oldvalue = l->curvalue;
+
+		if( l->curvalue == l->numitems - 1 ) {
+			l->curvalue = 0;;
+		}
+		else {
+			l->curvalue++;
+		}
+		return menu_move_sound;
 	}
 
 	return Menu_DefaultKey( &teamOrdersMenuInfo.menu, key );
@@ -213,7 +304,8 @@
 UI_TeamOrdersMenu_ListDraw
 =================
 */
-static void UI_TeamOrdersMenu_ListDraw( void *self ) {
+static void UI_TeamOrdersMenu_ListDraw( void *self )
+{
 	menulist_s	*l;
 	int			x;
 	int			y;
@@ -251,7 +343,8 @@
 UI_TeamOrdersMenu_ListEvent
 ===============
 */
-static void UI_TeamOrdersMenu_ListEvent( void *ptr, int event ) {
+static void UI_TeamOrdersMenu_ListEvent( void *ptr, int event )
+{
 	int		id;
 	int		selection;
 	char	message[256];
@@ -264,21 +357,40 @@
 
 	if( id == ID_LIST_BOTS ) {
 		teamOrdersMenuInfo.selectedBot = selection;
-		if( teamOrdersMenuInfo.gametype == GT_CTF ) {
+		if( teamOrdersMenuInfo.gametype == GT_CTF || teamOrdersMenuInfo.gametype == GT_CTF_ELIMINATION ) {
 			UI_TeamOrdersMenu_SetList( ID_LIST_CTF_ORDERS );
 		}
-		else {
+		if( teamOrdersMenuInfo.gametype == GT_1FCTF ) {
+			UI_TeamOrdersMenu_SetList( ID_LIST_CTF1F_ORDERS );
+		}
+		if( teamOrdersMenuInfo.gametype == GT_OBELISK || teamOrdersMenuInfo.gametype == GT_HARVESTER ) {
+			UI_TeamOrdersMenu_SetList( ID_LIST_BASE_ORDERS );
+		}
+		if( teamOrdersMenuInfo.gametype == GT_TEAM || teamOrdersMenuInfo.gametype == GT_ELIMINATION || teamOrdersMenuInfo.gametype == GT_DOMINATION ) {
 			UI_TeamOrdersMenu_SetList( ID_LIST_TEAM_ORDERS );
 		}
+		if( teamOrdersMenuInfo.gametype == GT_DOUBLE_D ) {
+			UI_TeamOrdersMenu_SetList( ID_LIST_DD_ORDERS );
+		}
+
 		return;
 	}
 
 	if( id == ID_LIST_CTF_ORDERS ) {
 		Com_sprintf( message, sizeof(message), ctfMessages[selection], teamOrdersMenuInfo.botNames[teamOrdersMenuInfo.selectedBot] );
 	}
-	else {
+	if( id == ID_LIST_CTF1F_ORDERS ) {
+		Com_sprintf( message, sizeof(message), ctf1fMessages[selection], teamOrdersMenuInfo.botNames[teamOrdersMenuInfo.selectedBot] );
+	}
+	if( id == ID_LIST_BASE_ORDERS ) {
+		Com_sprintf( message, sizeof(message), baseMessages[selection], teamOrdersMenuInfo.botNames[teamOrdersMenuInfo.selectedBot] );
+	}
+	if( id == ID_LIST_TEAM_ORDERS ) {
 		Com_sprintf( message, sizeof(message), teamMessages[selection], teamOrdersMenuInfo.botNames[teamOrdersMenuInfo.selectedBot] );
 	}
+	if( id == ID_LIST_DD_ORDERS ) {
+		Com_sprintf( message, sizeof(message), ddMessages[selection], teamOrdersMenuInfo.botNames[teamOrdersMenuInfo.selectedBot] );
+	}
 
 	trap_Cmd_ExecuteText( EXEC_APPEND, va( "say_team \"%s\"\n", message ) );
 	UI_PopMenu();
@@ -290,7 +402,8 @@
 UI_TeamOrdersMenu_BuildBotList
 ===============
 */
-static void UI_TeamOrdersMenu_BuildBotList( void ) {
+static void UI_TeamOrdersMenu_BuildBotList( void )
+{
 	uiClientState_t	cs;
 	int		numPlayers;
 	int		isBot;
@@ -344,7 +457,8 @@
 UI_TeamOrdersMenu_Init
 ===============
 */
-static void UI_TeamOrdersMenu_Init( void ) {
+static void UI_TeamOrdersMenu_Init( void )
+{
 	UI_TeamOrdersMenu_Cache();
 
 	memset( &teamOrdersMenuInfo, 0, sizeof(teamOrdersMenuInfo) );
@@ -402,7 +516,8 @@
 UI_TeamOrdersMenu_Cache
 =================
 */
-void UI_TeamOrdersMenu_Cache( void ) {
+void UI_TeamOrdersMenu_Cache( void )
+{
 	trap_R_RegisterShaderNoMip( ART_FRAME );
 	trap_R_RegisterShaderNoMip( ART_BACK0 );
 	trap_R_RegisterShaderNoMip( ART_BACK1 );
@@ -414,7 +529,8 @@
 UI_TeamOrdersMenu
 ===============
 */
-void UI_TeamOrdersMenu( void ) {
+void UI_TeamOrdersMenu( void )
+{
 	UI_TeamOrdersMenu_Init();
 	UI_PushMenu( &teamOrdersMenuInfo.menu );
 }
@@ -425,7 +541,8 @@
 UI_TeamOrdersMenu_f
 ===============
 */
-void UI_TeamOrdersMenu_f( void ) {
+void UI_TeamOrdersMenu_f( void )
+{
 	uiClientState_t	cs;
 	char	info[MAX_INFO_STRING];
 	int		team;
@@ -433,7 +550,7 @@
 	// make sure it's a team game
 	trap_GetConfigString( CS_SERVERINFO, info, sizeof(info) );
 	teamOrdersMenuInfo.gametype = atoi( Info_ValueForKey( info, "g_gametype" ) );
-	if( teamOrdersMenuInfo.gametype < GT_TEAM ) {
+	if( teamOrdersMenuInfo.gametype < GT_TEAM || teamOrdersMenuInfo.gametype == GT_LMS || teamOrdersMenuInfo.gametype == GT_POSSESSION) {
 		return;
 	}
 

```
