# Diff: `code/q3_ui/ui_startserver.c`
**Canonical:** `wolfcamql-src` (sha256 `1091574340c3...`, 61605 bytes)

## Variants

### `quake3-source`  — sha256 `3ab94c98b4c1...`, 60978 bytes

_Diff stat: +73 / -71 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_startserver.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_startserver.c	2026-04-16 20:02:19.955611800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -51,7 +51,11 @@
 #define MAX_MAPCOLS		2
 #define MAX_MAPSPERPAGE	4
 
+#define	MAX_SERVERSTEXT	8192
+
+#define MAX_SERVERMAPS	64
 #define MAX_NAMELENGTH	16
+
 #define ID_GAMETYPE				10
 #define ID_PICTURES				11	// 12, 13, 14
 #define ID_PREVPAGE				15
@@ -83,7 +87,8 @@
 	int				nummaps;
 	int				page;
 	int				maxpages;
-	int 			maplist[MAX_ARENAS];
+	char			maplist[MAX_SERVERMAPS][MAX_NAMELENGTH];
+	int				mapGamebits[MAX_SERVERMAPS];
 } startserver_t;
 
 static startserver_t s_startserver;
@@ -93,11 +98,10 @@
 	"Team Deathmatch",
 	"Tournament",
 	"Capture the Flag",
-	NULL
+	0
 };
 
-//static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
-static int gametype_remap[] = { 0, 3, 1, 5 };  //FIXME
+static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
 static int gametype_remap2[] = {0, 2, 0, 1, 3};
 
 // use ui_servers2.c definition
@@ -120,7 +124,7 @@
 	p = string;
 	while( 1 ) {
 		token = COM_ParseExt( &p, qfalse );
-		if ( !token[0] ) {
+		if( token[0] == 0 ) {
 			break;
 		}
 
@@ -163,8 +167,6 @@
 	int				i;
 	int				top;
 	static	char	picname[MAX_MAPSPERPAGE][64];
-	const char		*info;
-	char			mapname[MAX_NAMELENGTH];
 
 	top = s_startserver.page*MAX_MAPSPERPAGE;
 
@@ -172,12 +174,8 @@
 	{
 		if (top+i >= s_startserver.nummaps)
 			break;
-		
-		info = UI_GetArenaInfoByNumber( s_startserver.maplist[ top + i ]);
-		Q_strncpyz( mapname, Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
-		Q_strupr( mapname );
 
-		Com_sprintf( picname[i], sizeof(picname[i]), "levelshots/%s", mapname );
+		Com_sprintf( picname[i], sizeof(picname[i]), "levelshots/%s", s_startserver.maplist[top+i] );
 
 		s_startserver.mappics[i].generic.flags &= ~QMF_HIGHLIGHT;
 		s_startserver.mappics[i].generic.name   = picname[i];
@@ -218,8 +216,7 @@
 		}
 
 		// set the map name
-		info = UI_GetArenaInfoByNumber( s_startserver.maplist[ s_startserver.currentmap ]);
-		Q_strncpyz( s_startserver.mapname.string, Info_ValueForKey( info, "map" ), MAX_NAMELENGTH);
+		strcpy( s_startserver.mapname.string, s_startserver.maplist[s_startserver.currentmap] );
 	}
 	
 	Q_strupr( s_startserver.mapname.string );
@@ -265,13 +262,15 @@
 	}
 	for( i = 0; i < count; i++ ) {
 		info = UI_GetArenaInfoByNumber( i );
-	
+
 		gamebits = GametypeBits( Info_ValueForKey( info, "type") );
 		if( !( gamebits & matchbits ) ) {
 			continue;
 		}
 
-		s_startserver.maplist[ s_startserver.nummaps ] = i;
+		Q_strncpyz( s_startserver.maplist[s_startserver.nummaps], Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
+		Q_strupr( s_startserver.maplist[s_startserver.nummaps] );
+		s_startserver.mapGamebits[s_startserver.nummaps] = gamebits;
 		s_startserver.nummaps++;
 	}
 	s_startserver.maxpages = (s_startserver.nummaps + MAX_MAPSPERPAGE-1)/MAX_MAPSPERPAGE;
@@ -331,8 +330,6 @@
 	int				w;
 	int				h;
 	int				n;
-	const char		*info;
-	char			mapname[ MAX_NAMELENGTH ];
 
 	b = (menubitmap_s *)self;
 
@@ -366,11 +363,7 @@
 	x += b->width / 2;
 	y += 4;
 	n = s_startserver.page * MAX_MAPSPERPAGE + b->generic.id - ID_PICTURES;
-
-	info = UI_GetArenaInfoByNumber( s_startserver.maplist[ n ]);
-	Q_strncpyz( mapname, Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
-	Q_strupr( mapname );
-	UI_DrawString( x, y, mapname, UI_CENTER|UI_SMALLFONT, color_orange );
+	UI_DrawString( x, y, s_startserver.maplist[n], UI_CENTER|UI_SMALLFONT, color_orange );
 
 	x = b->generic.x;
 	y = b->generic.y;
@@ -563,7 +556,6 @@
 	const char		*info;
 	qboolean		precache;
 	char			picname[64];
-	char			mapname[ MAX_NAMELENGTH ];
 
 	trap_R_RegisterShaderNoMip( GAMESERVER_BACK0 );	
 	trap_R_RegisterShaderNoMip( GAMESERVER_BACK1 );	
@@ -580,16 +572,22 @@
 
 	precache = trap_Cvar_VariableValue("com_buildscript");
 
-	if( precache ) {
-		for( i = 0; i < UI_GetNumArenas(); i++ ) {
-			info = UI_GetArenaInfoByNumber( i );
-			Q_strncpyz( mapname, Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
-			Q_strupr( mapname );
-	
-			Com_sprintf( picname, sizeof(picname), "levelshots/%s", mapname );
+	s_startserver.nummaps = UI_GetNumArenas();
+
+	for( i = 0; i < s_startserver.nummaps; i++ ) {
+		info = UI_GetArenaInfoByNumber( i );
+
+		Q_strncpyz( s_startserver.maplist[i], Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
+		Q_strupr( s_startserver.maplist[i] );
+		s_startserver.mapGamebits[i] = GametypeBits( Info_ValueForKey( info, "type") );
+
+		if( precache ) {
+			Com_sprintf( picname, sizeof(picname), "levelshots/%s", s_startserver.maplist[i] );
 			trap_R_RegisterShaderNoMip(picname);
 		}
 	}
+
+	s_startserver.maxpages = (s_startserver.nummaps + MAX_MAPSPERPAGE-1)/MAX_MAPSPERPAGE;
 }
 
 
@@ -667,20 +665,20 @@
 	"No",
 	"LAN",
 	"Internet",
-	NULL
+	0
 };
 
 static const char *playerType_list[] = {
 	"Open",
 	"Bot",
 	"----",
-	NULL
+	0
 };
 
 static const char *playerTeam_list[] = {
 	"Blue",
 	"Red",
-	NULL
+	0
 };
 
 static const char *botSkill_list[] = {
@@ -689,7 +687,7 @@
 	"Hurt Me Plenty",
 	"Hardcore",
 	"Nightmare!",
-	NULL
+	0
 };
 
 
@@ -734,7 +732,7 @@
 	int		skill;
 	int		n;
 	char	buf[64];
-	const char *info;
+
 
 	timelimit	 = atoi( s_serveroptions.timelimit.field.buffer );
 	fraglimit	 = atoi( s_serveroptions.fraglimit.field.buffer );
@@ -755,20 +753,29 @@
 		maxclients++;
 	}
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
+		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		break;
+
+	case GT_TOURNAMENT:
 		trap_Cvar_SetValue( "ui_tourney_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_tourney_timelimit", timelimit );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		trap_Cvar_SetValue( "ui_team_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_team_timelimit", timelimit );
-		trap_Cvar_SetValue( "ui_team_friendly", friendlyfire );
-	} else if (s_serveroptions.gametype == GT_CTF) {
-		trap_Cvar_SetValue( "ui_ctf_capturelimit", fraglimit );
+		trap_Cvar_SetValue( "ui_team_friendlt", friendlyfire );
+		break;
+
+	case GT_CTF:
+		trap_Cvar_SetValue( "ui_ctf_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_ctf_timelimit", timelimit );
-		trap_Cvar_SetValue( "ui_ctf_friendly", friendlyfire );
-	} else {
-		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
-		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		trap_Cvar_SetValue( "ui_ctf_friendlt", friendlyfire );
+		break;
 	}
 
 	trap_Cvar_SetValue( "sv_maxclients", Com_Clamp( 0, 12, maxclients ) );
@@ -783,8 +790,7 @@
 	trap_Cvar_SetValue( "sv_punkbuster", s_serveroptions.punkbuster.curvalue );
 
 	// the wait commands will allow the dedicated to take effect
-	info = UI_GetArenaInfoByNumber( s_startserver.maplist[ s_startserver.currentmap ]);
-	trap_Cmd_ExecuteText( EXEC_APPEND, va( "wait ; wait ; map %s\n", Info_ValueForKey( info, "map" )));
+	trap_Cmd_ExecuteText( EXEC_APPEND, va( "wait ; wait ; map %s\n", s_startserver.maplist[s_startserver.currentmap] ) );
 
 	// add bots
 	trap_Cmd_ExecuteText( EXEC_APPEND, "wait 3\n" );
@@ -810,11 +816,7 @@
 
 	// set player's team
 	if( dedicated == 0 && s_serveroptions.gametype >= GT_TEAM ) {
-		// send team command for vanilla q3 game qvm
 		trap_Cmd_ExecuteText( EXEC_APPEND, va( "wait 5; team %s\n", playerTeam_list[s_serveroptions.playerTeam[0].curvalue] ) );
-
-		// set g_localTeamPref for ioq3 game qvm
-		trap_Cvar_Set( "g_localTeamPref", playerTeam_list[s_serveroptions.playerTeam[0].curvalue] );
 	}
 }
 
@@ -1075,7 +1077,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 
@@ -1091,10 +1093,6 @@
 		}
 
 		botInfo = UI_GetBotInfoByName( bot );
-		if( !botInfo )
-		{
-			botInfo = UI_GetBotInfoByNumber( count );
-		}
 		bot = Info_ValueForKey( botInfo, "name" );
 
 		Q_strncpyz( s_serveroptions.playerNameBuffers[count], bot, sizeof(s_serveroptions.playerNameBuffers[count]) );
@@ -1127,33 +1125,37 @@
 */
 static void ServerOptions_SetMenuItems( void ) {
 	static char picname[64];
-	char		mapname[MAX_NAMELENGTH];
-	const char	*info;
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
+		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
+
+	case GT_TOURNAMENT:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_timelimit" ) ) );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_team_friendly" ) );
-	} else if (s_serveroptions.gametype == GT_CTF) {
+		break;
+
+	case GT_CTF:
 		Com_sprintf( s_serveroptions.flaglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 100, trap_Cvar_VariableValue( "ui_ctf_capturelimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ctf_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_ctf_friendly" ) );
-	} else {
-		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
-		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
 	}
 
 	Q_strncpyz( s_serveroptions.hostname.field.buffer, UI_Cvar_VariableString( "sv_hostname" ), sizeof( s_serveroptions.hostname.field.buffer ) );
 	s_serveroptions.pure.curvalue = Com_Clamp( 0, 1, trap_Cvar_VariableValue( "sv_pure" ) );
 
 	// set the map pic
-	info = UI_GetArenaInfoByNumber( s_startserver.maplist[ s_startserver.currentmap ]);
-	Q_strncpyz( mapname, Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
-	Q_strupr( mapname );
-	Com_sprintf( picname, 64, "levelshots/%s", mapname );
+	Com_sprintf( picname, 64, "levelshots/%s", s_startserver.maplist[s_startserver.currentmap] );
 	s_serveroptions.mappic.generic.name = picname;
 
 	// set the map name
@@ -1229,7 +1231,7 @@
 
 	memset( &s_serveroptions, 0 ,sizeof(serveroptions_t) );
 	s_serveroptions.multiplayer = multiplayer;
-	s_serveroptions.gametype = (int) Com_Clamp(0, ARRAY_LEN(gametype_remap2) - 1, trap_Cvar_VariableValue("g_gametype"));
+	s_serveroptions.gametype = (int)Com_Clamp( 0, 5, trap_Cvar_VariableValue( "g_gameType" ) );
 	s_serveroptions.punkbuster.curvalue = Com_Clamp( 0, 1, trap_Cvar_VariableValue( "sv_punkbuster" ) );
 
 	ServerOptions_Cache();
@@ -1606,7 +1608,7 @@
 	char	model[MAX_QPATH];
 
 	Q_strncpyz( model, modelAndSkin, sizeof(model));
-	skin = strrchr( model, '/' );
+	skin = Q_strrchr( model, '/' );
 	if ( skin ) {
 		*skin++ = '\0';
 	}

```

### `ioquake3`  — sha256 `8e0bcc71cf0e...`, 61550 bytes

_Diff stat: +35 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_startserver.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_startserver.c	2026-04-16 20:02:21.561591900 +0100
@@ -96,8 +96,7 @@
 	NULL
 };
 
-//static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
-static int gametype_remap[] = { 0, 3, 1, 5 };  //FIXME
+static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
 static int gametype_remap2[] = {0, 2, 0, 1, 3};
 
 // use ui_servers2.c definition
@@ -755,20 +754,29 @@
 		maxclients++;
 	}
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
+		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		break;
+
+	case GT_TOURNAMENT:
 		trap_Cvar_SetValue( "ui_tourney_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_tourney_timelimit", timelimit );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		trap_Cvar_SetValue( "ui_team_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_team_timelimit", timelimit );
 		trap_Cvar_SetValue( "ui_team_friendly", friendlyfire );
-	} else if (s_serveroptions.gametype == GT_CTF) {
-		trap_Cvar_SetValue( "ui_ctf_capturelimit", fraglimit );
+		break;
+
+	case GT_CTF:
+		trap_Cvar_SetValue( "ui_ctf_capturelimit", flaglimit );
 		trap_Cvar_SetValue( "ui_ctf_timelimit", timelimit );
 		trap_Cvar_SetValue( "ui_ctf_friendly", friendlyfire );
-	} else {
-		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
-		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		break;
 	}
 
 	trap_Cvar_SetValue( "sv_maxclients", Com_Clamp( 0, 12, maxclients ) );
@@ -1130,20 +1138,29 @@
 	char		mapname[MAX_NAMELENGTH];
 	const char	*info;
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
+		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
+
+	case GT_TOURNAMENT:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_timelimit" ) ) );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_team_friendly" ) );
-	} else if (s_serveroptions.gametype == GT_CTF) {
+		break;
+
+	case GT_CTF:
 		Com_sprintf( s_serveroptions.flaglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 100, trap_Cvar_VariableValue( "ui_ctf_capturelimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ctf_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_ctf_friendly" ) );
-	} else {
-		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
-		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
 	}
 
 	Q_strncpyz( s_serveroptions.hostname.field.buffer, UI_Cvar_VariableString( "sv_hostname" ), sizeof( s_serveroptions.hostname.field.buffer ) );
@@ -1229,7 +1246,8 @@
 
 	memset( &s_serveroptions, 0 ,sizeof(serveroptions_t) );
 	s_serveroptions.multiplayer = multiplayer;
-	s_serveroptions.gametype = (int) Com_Clamp(0, ARRAY_LEN(gametype_remap2) - 1, trap_Cvar_VariableValue("g_gametype"));
+	s_serveroptions.gametype = (int) Com_Clamp(0, ARRAY_LEN(gametype_remap2) - 1,
+						trap_Cvar_VariableValue("g_gametype"));
 	s_serveroptions.punkbuster.curvalue = Com_Clamp( 0, 1, trap_Cvar_VariableValue( "sv_punkbuster" ) );
 
 	ServerOptions_Cache();
@@ -1344,7 +1362,7 @@
 	y = 80;
 	s_serveroptions.botSkill.generic.type			= MTYPE_SPINCONTROL;
 	s_serveroptions.botSkill.generic.flags			= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	s_serveroptions.botSkill.generic.name			= "Bot Skill:  ";
+	s_serveroptions.botSkill.generic.name			= "Bot Skill:";
 	s_serveroptions.botSkill.generic.x				= 32 + (strlen(s_serveroptions.botSkill.generic.name) + 2 ) * SMALLCHAR_WIDTH;
 	s_serveroptions.botSkill.generic.y				= y;
 	s_serveroptions.botSkill.itemnames				= botSkill_list;

```

### `openarena-engine`  — sha256 `b9322dc12e09...`, 61254 bytes

_Diff stat: +38 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_startserver.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_startserver.c	2026-04-16 22:48:25.903298800 +0100
@@ -96,8 +96,7 @@
 	NULL
 };
 
-//static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
-static int gametype_remap[] = { 0, 3, 1, 5 };  //FIXME
+static int gametype_remap[] = {GT_FFA, GT_TEAM, GT_TOURNAMENT, GT_CTF};
 static int gametype_remap2[] = {0, 2, 0, 1, 3};
 
 // use ui_servers2.c definition
@@ -120,7 +119,7 @@
 	p = string;
 	while( 1 ) {
 		token = COM_ParseExt( &p, qfalse );
-		if ( !token[0] ) {
+		if( token[0] == 0 ) {
 			break;
 		}
 
@@ -332,7 +331,6 @@
 	int				h;
 	int				n;
 	const char		*info;
-	char			mapname[ MAX_NAMELENGTH ];
 
 	b = (menubitmap_s *)self;
 
@@ -368,9 +366,7 @@
 	n = s_startserver.page * MAX_MAPSPERPAGE + b->generic.id - ID_PICTURES;
 
 	info = UI_GetArenaInfoByNumber( s_startserver.maplist[ n ]);
-	Q_strncpyz( mapname, Info_ValueForKey( info, "map"), MAX_NAMELENGTH );
-	Q_strupr( mapname );
-	UI_DrawString( x, y, mapname, UI_CENTER|UI_SMALLFONT, color_orange );
+	UI_DrawString( x, y, Info_ValueForKey( info, "map" ), UI_CENTER|UI_SMALLFONT, color_orange );
 
 	x = b->generic.x;
 	y = b->generic.y;
@@ -755,20 +751,29 @@
 		maxclients++;
 	}
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
+		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		break;
+
+	case GT_TOURNAMENT:
 		trap_Cvar_SetValue( "ui_tourney_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_tourney_timelimit", timelimit );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		trap_Cvar_SetValue( "ui_team_fraglimit", fraglimit );
 		trap_Cvar_SetValue( "ui_team_timelimit", timelimit );
 		trap_Cvar_SetValue( "ui_team_friendly", friendlyfire );
-	} else if (s_serveroptions.gametype == GT_CTF) {
-		trap_Cvar_SetValue( "ui_ctf_capturelimit", fraglimit );
+		break;
+
+	case GT_CTF:
+		trap_Cvar_SetValue( "ui_ctf_capturelimit", flaglimit );
 		trap_Cvar_SetValue( "ui_ctf_timelimit", timelimit );
 		trap_Cvar_SetValue( "ui_ctf_friendly", friendlyfire );
-	} else {
-		trap_Cvar_SetValue( "ui_ffa_fraglimit", fraglimit );
-		trap_Cvar_SetValue( "ui_ffa_timelimit", timelimit );
+		break;
 	}
 
 	trap_Cvar_SetValue( "sv_maxclients", Com_Clamp( 0, 12, maxclients ) );
@@ -810,11 +815,7 @@
 
 	// set player's team
 	if( dedicated == 0 && s_serveroptions.gametype >= GT_TEAM ) {
-		// send team command for vanilla q3 game qvm
 		trap_Cmd_ExecuteText( EXEC_APPEND, va( "wait 5; team %s\n", playerTeam_list[s_serveroptions.playerTeam[0].curvalue] ) );
-
-		// set g_localTeamPref for ioq3 game qvm
-		trap_Cvar_Set( "g_localTeamPref", playerTeam_list[s_serveroptions.playerTeam[0].curvalue] );
 	}
 }
 
@@ -1075,7 +1076,7 @@
 		while( *p && *p == ' ' ) {
 			p++;
 		}
-		if( !*p ) {
+		if( !p ) {
 			break;
 		}
 
@@ -1130,20 +1131,29 @@
 	char		mapname[MAX_NAMELENGTH];
 	const char	*info;
 
-	if (s_serveroptions.gametype == GT_TOURNAMENT) {
+	switch( s_serveroptions.gametype ) {
+	case GT_FFA:
+	default:
+		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
+		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
+
+	case GT_TOURNAMENT:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_tourney_timelimit" ) ) );
-	} else if (s_serveroptions.gametype == GT_TEAM) {
+		break;
+
+	case GT_TEAM:
 		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_fraglimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_team_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_team_friendly" ) );
-	} else if (s_serveroptions.gametype == GT_CTF) {
+		break;
+
+	case GT_CTF:
 		Com_sprintf( s_serveroptions.flaglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 100, trap_Cvar_VariableValue( "ui_ctf_capturelimit" ) ) );
 		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ctf_timelimit" ) ) );
 		s_serveroptions.friendlyfire.curvalue = (int)Com_Clamp( 0, 1, trap_Cvar_VariableValue( "ui_ctf_friendly" ) );
-	} else {
-		Com_sprintf( s_serveroptions.fraglimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_fraglimit" ) ) );
-		Com_sprintf( s_serveroptions.timelimit.field.buffer, 4, "%i", (int)Com_Clamp( 0, 999, trap_Cvar_VariableValue( "ui_ffa_timelimit" ) ) );
+		break;
 	}
 
 	Q_strncpyz( s_serveroptions.hostname.field.buffer, UI_Cvar_VariableString( "sv_hostname" ), sizeof( s_serveroptions.hostname.field.buffer ) );
@@ -1229,7 +1239,8 @@
 
 	memset( &s_serveroptions, 0 ,sizeof(serveroptions_t) );
 	s_serveroptions.multiplayer = multiplayer;
-	s_serveroptions.gametype = (int) Com_Clamp(0, ARRAY_LEN(gametype_remap2) - 1, trap_Cvar_VariableValue("g_gametype"));
+	s_serveroptions.gametype = (int) Com_Clamp(0, ARRAY_LEN(gametype_remap2) - 1,
+						trap_Cvar_VariableValue("g_gametype"));
 	s_serveroptions.punkbuster.curvalue = Com_Clamp( 0, 1, trap_Cvar_VariableValue( "sv_punkbuster" ) );
 
 	ServerOptions_Cache();
@@ -1344,7 +1355,7 @@
 	y = 80;
 	s_serveroptions.botSkill.generic.type			= MTYPE_SPINCONTROL;
 	s_serveroptions.botSkill.generic.flags			= QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	s_serveroptions.botSkill.generic.name			= "Bot Skill:  ";
+	s_serveroptions.botSkill.generic.name			= "Bot Skill:";
 	s_serveroptions.botSkill.generic.x				= 32 + (strlen(s_serveroptions.botSkill.generic.name) + 2 ) * SMALLCHAR_WIDTH;
 	s_serveroptions.botSkill.generic.y				= y;
 	s_serveroptions.botSkill.itemnames				= botSkill_list;

```

### `openarena-gamecode`  — sha256 `14014394481e...`, 80093 bytes

_Diff stat: +666 / -216 lines_

_(full diff is 54036 bytes — see files directly)_
