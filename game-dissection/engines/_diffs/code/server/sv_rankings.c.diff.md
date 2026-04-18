# Diff: `code/server/sv_rankings.c`
**Canonical:** `wolfcamql-src` (sha256 `12d5209a7c99...`, 37079 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `f6a0cfef0553...`, 37074 bytes

_Diff stat: +6 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_rankings.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_rankings.c	2026-04-16 20:02:19.978633600 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -68,7 +68,7 @@
 static uint64_t	SV_RankDecodePlayerID( const char* string );
 static void		SV_RankDecodePlayerKey( const char* string, GR_PLAYER_TOKEN key );
 static char*	SV_RankStatusString( GR_STATUS status );
-static void		SV_RankError( const char* fmt, ... ) Q_PRINTF_FUNC(1, 2);
+static void		SV_RankError( const char* fmt, ... );
 static char     SV_RankGameKey[64];
 
 /*
@@ -138,7 +138,8 @@
 
 	// initialize rankings
 	GRankLogLevel( GRLOG_OFF );
-	Q_strncpyz(SV_RankGameKey,gamekey,sizeof(SV_RankGameKey));
+	memset(SV_RankGameKey,0,sizeof(SV_RankGameKey));
+	strncpy(SV_RankGameKey,gamekey,sizeof(SV_RankGameKey)-1);
 	init = GRankInit( 1, SV_RankGameKey, GR_OPT_POLL, GR_OPT_END );
 	s_server_context = init.context;
 	s_rankings_contexts++;
@@ -1003,7 +1004,7 @@
 	}
 	else if( gr_newgame->status == GR_STATUS_BADLEAGUE )
 	{
-		SV_RankError( "SV_RankNewGameCBF: Invalid League name" );
+		SV_RankError( "SV_RankNewGameCBF: Invalid League name\n" );
 	}
 	else
 	{
@@ -1522,7 +1523,7 @@
 	char	text[1024];
 
 	va_start( arg_ptr, fmt );
-	Q_vsnprintf(text, sizeof(text), fmt, arg_ptr );
+	vsprintf( text, fmt, arg_ptr );
 	va_end( arg_ptr );
 
 	Com_DPrintf( "****************************************\n" );

```

### `quake3e`  — sha256 `6680ed125844...`, 37149 bytes
Also identical in: openarena-engine

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_rankings.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\server\sv_rankings.c	2026-04-16 20:02:27.369557000 +0100
@@ -68,7 +68,7 @@
 static uint64_t	SV_RankDecodePlayerID( const char* string );
 static void		SV_RankDecodePlayerKey( const char* string, GR_PLAYER_TOKEN key );
 static char*	SV_RankStatusString( GR_STATUS status );
-static void		SV_RankError( const char* fmt, ... ) Q_PRINTF_FUNC(1, 2);
+static void		SV_RankError( const char* fmt, ... ) __attribute__ ((format (printf, 1, 2)));
 static char     SV_RankGameKey[64];
 
 /*
@@ -138,7 +138,8 @@
 
 	// initialize rankings
 	GRankLogLevel( GRLOG_OFF );
-	Q_strncpyz(SV_RankGameKey,gamekey,sizeof(SV_RankGameKey));
+	memset(SV_RankGameKey,0,sizeof(SV_RankGameKey));
+	strncpy(SV_RankGameKey,gamekey,sizeof(SV_RankGameKey)-1);
 	init = GRankInit( 1, SV_RankGameKey, GR_OPT_POLL, GR_OPT_END );
 	s_server_context = init.context;
 	s_rankings_contexts++;

```
