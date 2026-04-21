# Diff: `code/server/sv_bot.c`
**Canonical:** `wolfcamql-src` (sha256 `40ffaf0f870b...`, 17004 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `c696684f40bd...`, 16846 bytes

_Diff stat: +27 / -27 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_bot.c	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_bot.c	2026-04-16 20:02:19.976636800 +0100
@@ -15,14 +15,14 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // sv_bot.c
 
 #include "server.h"
-#include "../botlib/botlib.h"
+#include "../game/botlib.h"
 
 typedef struct bot_debugpoly_s
 {
@@ -133,13 +133,13 @@
 BotImport_Print
 ==================
 */
-static Q_PRINTF_FUNC(2, 3) void QDECL BotImport_Print(int type, char *fmt, ...)
+void QDECL BotImport_Print(int type, char *fmt, ...)
 {
 	char str[2048];
 	va_list ap;
 
 	va_start(ap, fmt);
-	Q_vsnprintf(str, sizeof(str), fmt, ap);
+	vsprintf(str, fmt, ap);
 	va_end(ap);
 
 	switch(type) {
@@ -175,7 +175,7 @@
 BotImport_Trace
 ==================
 */
-static void BotImport_Trace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask) {
+void BotImport_Trace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int passent, int contentmask) {
 	trace_t trace;
 
 	SV_Trace(&trace, start, mins, maxs, end, passent, contentmask, qfalse);
@@ -188,8 +188,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -201,7 +200,7 @@
 BotImport_EntityTrace
 ==================
 */
-static void BotImport_EntityTrace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int entnum, int contentmask) {
+void BotImport_EntityTrace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int entnum, int contentmask) {
 	trace_t trace;
 
 	SV_ClipToEntity(&trace, start, mins, maxs, end, entnum, contentmask, qfalse);
@@ -214,8 +213,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -228,7 +226,7 @@
 BotImport_PointContents
 ==================
 */
-static int BotImport_PointContents(vec3_t point) {
+int BotImport_PointContents(vec3_t point) {
 	return SV_PointContents(point, -1);
 }
 
@@ -237,7 +235,7 @@
 BotImport_inPVS
 ==================
 */
-static int BotImport_inPVS(vec3_t p1, vec3_t p2) {
+int BotImport_inPVS(vec3_t p1, vec3_t p2) {
 	return SV_inPVS (p1, p2);
 }
 
@@ -246,7 +244,7 @@
 BotImport_BSPEntityData
 ==================
 */
-static char *BotImport_BSPEntityData(void) {
+char *BotImport_BSPEntityData(void) {
 	return CM_EntityString();
 }
 
@@ -255,7 +253,7 @@
 BotImport_BSPModelMinsMaxsOrigin
 ==================
 */
-static void BotImport_BSPModelMinsMaxsOrigin(int modelnum, vec3_t angles, vec3_t outmins, vec3_t outmaxs, vec3_t origin) {
+void BotImport_BSPModelMinsMaxsOrigin(int modelnum, vec3_t angles, vec3_t outmins, vec3_t outmaxs, vec3_t origin) {
 	clipHandle_t h;
 	vec3_t mins, maxs;
 	float max;
@@ -283,7 +281,7 @@
 BotImport_GetMemory
 ==================
 */
-static void *BotImport_GetMemory(int size) {
+void *BotImport_GetMemory(int size) {
 	void *ptr;
 
 	ptr = Z_TagMalloc( size, TAG_BOTLIB );
@@ -295,7 +293,7 @@
 BotImport_FreeMemory
 ==================
 */
-static void BotImport_FreeMemory(void *ptr) {
+void BotImport_FreeMemory(void *ptr) {
 	Z_Free(ptr);
 }
 
@@ -304,9 +302,9 @@
 BotImport_HunkAlloc
 =================
 */
-static void *BotImport_HunkAlloc( int size ) {
+void *BotImport_HunkAlloc( int size ) {
 	if( Hunk_CheckMark() ) {
-		Com_Error( ERR_DROP, "SV_Bot_HunkAlloc: Alloc with marks already set" );
+		Com_Error( ERR_DROP, "SV_Bot_HunkAlloc: Alloc with marks already set\n" );
 	}
 	return Hunk_Alloc( size, h_high );
 }
@@ -343,7 +341,7 @@
 BotImport_DebugPolygonShow
 ==================
 */
-static void BotImport_DebugPolygonShow(int id, int color, int numPoints, vec3_t *points) {
+void BotImport_DebugPolygonShow(int id, int color, int numPoints, vec3_t *points) {
 	bot_debugpoly_t *poly;
 
 	if (!debugpolygons) return;
@@ -370,7 +368,7 @@
 BotImport_DebugLineCreate
 ==================
 */
-static int BotImport_DebugLineCreate(void) {
+int BotImport_DebugLineCreate(void) {
 	vec3_t points[1];
 	return BotImport_DebugPolygonCreate(0, 0, points);
 }
@@ -380,7 +378,7 @@
 BotImport_DebugLineDelete
 ==================
 */
-static void BotImport_DebugLineDelete(int line) {
+void BotImport_DebugLineDelete(int line) {
 	BotImport_DebugPolygonDelete(line);
 }
 
@@ -389,7 +387,7 @@
 BotImport_DebugLineShow
 ==================
 */
-static void BotImport_DebugLineShow(int line, vec3_t start, vec3_t end, int color) {
+void BotImport_DebugLineShow(int line, vec3_t start, vec3_t end, int color) {
 	vec3_t points[4], dir, cross, up = {0, 0, 1};
 	float dot;
 
@@ -422,7 +420,7 @@
 SV_BotClientCommand
 ==================
 */
-static void BotClientCommand( int client, char *command ) {
+void BotClientCommand( int client, char *command ) {
 	SV_ExecuteClientCommand( &svs.clients[client], command, qtrue );
 }
 
@@ -453,8 +451,6 @@
 		return -1;
 	}
 
-	botlib_export->BotLibVarSet( "basegame", com_basegame->string );
-
 	return botlib_export->BotLibSetup();
 }
 
@@ -522,6 +518,10 @@
 void SV_BotInitBotLib(void) {
 	botlib_import_t	botlib_import;
 
+	if ( !Cvar_VariableValue("fs_restrict") && !Sys_CheckCD() ) {
+		Com_Error( ERR_NEED_CD, "Game CD not in drive" );
+	}
+
 	if (debugpolygons) Z_Free(debugpolygons);
 	bot_maxdebugpolys = Cvar_VariableIntegerValue("bot_maxdebugpolys");
 	debugpolygons = Z_Malloc(sizeof(bot_debugpoly_t) * bot_maxdebugpolys);
@@ -543,7 +543,7 @@
 
 	// file system access
 	botlib_import.FS_FOpenFile = FS_FOpenFileByMode;
-	botlib_import.FS_Read = FS_Read;
+	botlib_import.FS_Read = FS_Read2;
 	botlib_import.FS_Write = FS_Write;
 	botlib_import.FS_FCloseFile = FS_FCloseFile;
 	botlib_import.FS_Seek = FS_Seek;
@@ -558,7 +558,7 @@
 	botlib_import.DebugPolygonDelete = BotImport_DebugPolygonDelete;
 
 	botlib_export = (botlib_export_t *)GetBotLibAPI( BOTLIB_API_VERSION, &botlib_import );
-	assert(botlib_export); 	// somehow we end up with a zero import.
+	assert(botlib_export); 	// bk001129 - somehow we end up with a zero import.
 }
 
 

```

### `quake3e`  — sha256 `c9a93ec30fd2...`, 17529 bytes

_Diff stat: +78 / -46 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_bot.c	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\server\sv_bot.c	2026-04-16 20:02:27.366441100 +0100
@@ -33,7 +33,7 @@
 } bot_debugpoly_t;
 
 static bot_debugpoly_t *debugpolygons;
-int bot_maxdebugpolys;
+static int bot_maxdebugpolys;
 
 extern botlib_export_t	*botlib_export;
 int	bot_enable;
@@ -44,18 +44,18 @@
 SV_BotAllocateClient
 ==================
 */
-int SV_BotAllocateClient(void) {
+int SV_BotAllocateClient( void ) {
 	int			i;
 	client_t	*cl;
 
 	// find a client slot
-	for ( i = 0, cl = svs.clients; i < sv_maxclients->integer; i++, cl++ ) {
+	for ( i = 0, cl = svs.clients; i < sv.maxclients; i++, cl++ ) {
 		if ( cl->state == CS_FREE ) {
 			break;
 		}
 	}
 
-	if ( i == sv_maxclients->integer ) {
+	if ( i == sv.maxclients ) {
 		return -1;
 	}
 
@@ -63,12 +63,17 @@
 	cl->gentity->s.number = i;
 	cl->state = CS_ACTIVE;
 	cl->lastPacketTime = svs.time;
+	cl->snapshotMsec = 1000 / sv_fps->integer;
 	cl->netchan.remoteAddress.type = NA_BOT;
-	cl->rate = 16384;
+	cl->rate = 0;
+
+	cl->tld[0] = '\0';
+	cl->country = "BOT";
 
 	return i;
 }
 
+
 /*
 ==================
 SV_BotFreeClient
@@ -77,17 +82,19 @@
 void SV_BotFreeClient( int clientNum ) {
 	client_t	*cl;
 
-	if ( clientNum < 0 || clientNum >= sv_maxclients->integer ) {
+	if ( (unsigned) clientNum >= sv.maxclients ) {
 		Com_Error( ERR_DROP, "SV_BotFreeClient: bad clientNum: %i", clientNum );
 	}
+
 	cl = &svs.clients[clientNum];
 	cl->state = CS_FREE;
-	cl->name[0] = 0;
+	cl->name[0] = '\0';
 	if ( cl->gentity ) {
 		cl->gentity->r.svFlags &= ~SVF_BOT;
 	}
 }
 
+
 /*
 ==================
 BotDrawDebugPolygons
@@ -133,7 +140,7 @@
 BotImport_Print
 ==================
 */
-static Q_PRINTF_FUNC(2, 3) void QDECL BotImport_Print(int type, char *fmt, ...)
+static __attribute__ ((format (printf, 2, 3))) void QDECL BotImport_Print(int type, const char *fmt, ...)
 {
 	char str[2048];
 	va_list ap;
@@ -148,19 +155,19 @@
 			break;
 		}
 		case PRT_WARNING: {
-			Com_Printf(S_COLOR_YELLOW "Warning: %s", str);
+			Com_Printf(S_COLOR_WARNING "Warning: %s", str);
 			break;
 		}
 		case PRT_ERROR: {
-			Com_Printf(S_COLOR_RED "Error: %s", str);
+			Com_Printf(S_COLOR_ERROR "Error: %s", str);
 			break;
 		}
 		case PRT_FATAL: {
-			Com_Printf(S_COLOR_RED "Fatal: %s", str);
+			Com_Printf(S_COLOR_ERROR "Fatal: %s", str);
 			break;
 		}
 		case PRT_EXIT: {
-			Com_Error(ERR_DROP, S_COLOR_RED "Exit: %s", str);
+			Com_Error(ERR_DROP, S_COLOR_ERROR "Exit: %s", str);
 			break;
 		}
 		default: {
@@ -204,6 +211,10 @@
 static void BotImport_EntityTrace(bsp_trace_t *bsptrace, vec3_t start, vec3_t mins, vec3_t maxs, vec3_t end, int entnum, int contentmask) {
 	trace_t trace;
 
+	if ( (unsigned)entnum > MAX_GENTITIES - 1 ) {
+		entnum = ENTITYNUM_NONE;
+	}
+
 	SV_ClipToEntity(&trace, start, mins, maxs, end, entnum, contentmask, qfalse);
 	//copy the trace information
 	bsptrace->allsolid = trace.allsolid;
@@ -283,7 +294,7 @@
 BotImport_GetMemory
 ==================
 */
-static void *BotImport_GetMemory(int size) {
+static void *BotImport_GetMemory(size_t size) {
 	void *ptr;
 
 	ptr = Z_TagMalloc( size, TAG_BOTLIB );
@@ -304,9 +315,9 @@
 BotImport_HunkAlloc
 =================
 */
-static void *BotImport_HunkAlloc( int size ) {
+static void *BotImport_HunkAlloc( size_t size ) {
 	if( Hunk_CheckMark() ) {
-		Com_Error( ERR_DROP, "SV_Bot_HunkAlloc: Alloc with marks already set" );
+		Com_Error( ERR_DROP, "%s(): Alloc with marks already set", __func__ );
 	}
 	return Hunk_Alloc( size, h_high );
 }
@@ -346,7 +357,12 @@
 static void BotImport_DebugPolygonShow(int id, int color, int numPoints, vec3_t *points) {
 	bot_debugpoly_t *poly;
 
-	if (!debugpolygons) return;
+	if ( !debugpolygons )
+		return;
+
+	if ( (unsigned) id >= bot_maxdebugpolys )
+		return;
+
 	poly = &debugpolygons[id];
 	poly->inuse = qtrue;
 	poly->color = color;
@@ -361,7 +377,12 @@
 */
 void BotImport_DebugPolygonDelete(int id)
 {
-	if (!debugpolygons) return;
+	if ( !debugpolygons )
+		return;
+
+	if ( (unsigned) id >= bot_maxdebugpolys )
+		return;
+
 	debugpolygons[id].inuse = qfalse;
 }
 
@@ -422,8 +443,10 @@
 SV_BotClientCommand
 ==================
 */
-static void BotClientCommand( int client, char *command ) {
-	SV_ExecuteClientCommand( &svs.clients[client], command, qtrue );
+static void BotClientCommand( int client, const char *command ) {
+	if ( (unsigned) client < sv.maxclients ) {
+		SV_ExecuteClientCommand( &svs.clients[client], command );
+	}
 }
 
 /*
@@ -435,7 +458,7 @@
 	if (!bot_enable) return;
 	//NOTE: maybe the game is already shutdown
 	if (!gvm) return;
-	VM_Call( gvm, BOTAI_START_FRAME, time );
+	VM_Call( gvm, 1, BOTAI_START_FRAME, time );
 }
 
 /*
@@ -449,12 +472,10 @@
 	}
 
 	if ( !botlib_export ) {
-		Com_Printf( S_COLOR_RED "Error: SV_BotLibSetup without SV_BotInitBotLib\n" );
+		Com_Printf( S_COLOR_ERROR "Error: SV_BotLibSetup without SV_BotInitBotLib\n" );
 		return -1;
 	}
 
-	botlib_export->BotLibVarSet( "basegame", com_basegame->string );
-
 	return botlib_export->BotLibSetup();
 }
 
@@ -481,11 +502,12 @@
 ==================
 */
 void SV_BotInitCvars(void) {
+	cvar_t *cv;
 
 	Cvar_Get("bot_enable", "1", 0);						//enable the bot
 	Cvar_Get("bot_developer", "0", CVAR_CHEAT);			//bot developer mode
 	Cvar_Get("bot_debug", "0", CVAR_CHEAT);				//enable bot debugging
-	Cvar_Get("bot_maxdebugpolys", "2", 0);				//maximum number of debug polys
+	cv = Cvar_Get("bot_maxdebugpolys", "2", 0);			//maximum number of debug polys
 	Cvar_Get("bot_groundonly", "1", 0);					//only show ground faces of areas
 	Cvar_Get("bot_reachability", "0", 0);				//show all reachabilities to other areas
 	Cvar_Get("bot_visualizejumppads", "0", CVAR_CHEAT);	//show jumppads
@@ -494,7 +516,7 @@
 	Cvar_Get("bot_forcewrite", "0", 0);					//force writing aas file
 	Cvar_Get("bot_aasoptimize", "0", 0);				//no aas file optimisation
 	Cvar_Get("bot_saveroutingcache", "0", 0);			//save routing cache
-	Cvar_Get("bot_thinktime", "100", CVAR_CHEAT);		//msec the bots thinks
+	Cvar_Get("bot_thinktime", "100", 0);				//msec the bots thinks
 	Cvar_Get("bot_reloadcharacters", "0", 0);			//reload the bot characters each time
 	Cvar_Get("bot_testichat", "0", 0);					//test ichats
 	Cvar_Get("bot_testrchat", "0", 0);					//test rchats
@@ -512,6 +534,8 @@
 	Cvar_Get("bot_interbreedbots", "10", CVAR_CHEAT);	//number of bots used for interbreeding
 	Cvar_Get("bot_interbreedcycle", "20", CVAR_CHEAT);	//bot interbreeding cycle
 	Cvar_Get("bot_interbreedwrite", "", CVAR_CHEAT);	//write interbreeded bots to this file
+
+	Cvar_CheckRange(cv, "0", "65536", CV_INTEGER);
 }
 
 /*
@@ -557,6 +581,8 @@
 	botlib_import.DebugPolygonCreate = BotImport_DebugPolygonCreate;
 	botlib_import.DebugPolygonDelete = BotImport_DebugPolygonDelete;
 
+	botlib_import.Sys_Milliseconds = Sys_Milliseconds;
+
 	botlib_export = (botlib_export_t *)GetBotLibAPI( BOTLIB_API_VERSION, &botlib_import );
 	assert(botlib_export); 	// somehow we end up with a zero import.
 }
@@ -573,27 +599,32 @@
 */
 int SV_BotGetConsoleMessage( int client, char *buf, int size )
 {
-	client_t	*cl;
-	int			index;
+	if ( (unsigned) client < sv.maxclients ) {
+		client_t* cl;
+		int index;
 
-	cl = &svs.clients[client];
-	cl->lastPacketTime = svs.time;
+		cl = &svs.clients[client];
+		cl->lastPacketTime = svs.time;
 
-	if ( cl->reliableAcknowledge == cl->reliableSequence ) {
-		return qfalse;
-	}
+		if ( cl->reliableAcknowledge == cl->reliableSequence ) {
+			return qfalse;
+		}
+
+		cl->reliableAcknowledge++;
+		index = cl->reliableAcknowledge & ( MAX_RELIABLE_COMMANDS - 1 );
 
-	cl->reliableAcknowledge++;
-	index = cl->reliableAcknowledge & ( MAX_RELIABLE_COMMANDS - 1 );
+		if ( !cl->reliableCommands[index][0] ) {
+			return qfalse;
+		}
 
-	if ( !cl->reliableCommands[index][0] ) {
+		Q_strncpyz( buf, cl->reliableCommands[index], size );
+		return qtrue;
+	} else {
 		return qfalse;
 	}
-
-	Q_strncpyz( buf, cl->reliableCommands[index], size );
-	return qtrue;
 }
 
+
 #if 0
 /*
 ==================
@@ -616,20 +647,21 @@
 }
 #endif
 
+
 /*
 ==================
 SV_BotGetSnapshotEntity
 ==================
 */
 int SV_BotGetSnapshotEntity( int client, int sequence ) {
-	client_t			*cl;
-	clientSnapshot_t	*frame;
-
-	cl = &svs.clients[client];
-	frame = &cl->frames[cl->netchan.outgoingSequence & PACKET_MASK];
-	if (sequence < 0 || sequence >= frame->num_entities) {
+	if ( (unsigned) client < sv.maxclients ) {
+		const client_t* cl = &svs.clients[client];
+		const clientSnapshot_t* frame = &cl->frames[cl->netchan.outgoingSequence & PACKET_MASK];
+		if ( (unsigned) sequence >= frame->num_entities ) {
+			return -1;
+		}
+		return frame->ents[sequence]->number;
+	} else {
 		return -1;
 	}
-	return svs.snapshotEntities[(frame->first_entity + sequence) % svs.numSnapshotEntities].number;
 }
-

```

### `openarena-engine`  — sha256 `e42985c3f345...`, 16963 bytes

_Diff stat: +4 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_bot.c	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_bot.c	2026-04-16 22:48:25.935962700 +0100
@@ -133,7 +133,7 @@
 BotImport_Print
 ==================
 */
-static Q_PRINTF_FUNC(2, 3) void QDECL BotImport_Print(int type, char *fmt, ...)
+static __attribute__ ((format (printf, 2, 3))) void QDECL BotImport_Print(int type, char *fmt, ...)
 {
 	char str[2048];
 	va_list ap;
@@ -188,8 +188,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -214,8 +213,7 @@
 	VectorCopy(trace.plane.normal, bsptrace->plane.normal);
 	bsptrace->plane.signbits = trace.plane.signbits;
 	bsptrace->plane.type = trace.plane.type;
-	bsptrace->surface.value = 0;
-	bsptrace->surface.flags = trace.surfaceFlags;
+	bsptrace->surface.value = trace.surfaceFlags;
 	bsptrace->ent = trace.entityNum;
 	bsptrace->exp_dist = 0;
 	bsptrace->sidenum = 0;
@@ -543,7 +541,7 @@
 
 	// file system access
 	botlib_import.FS_FOpenFile = FS_FOpenFileByMode;
-	botlib_import.FS_Read = FS_Read;
+	botlib_import.FS_Read = FS_Read2;
 	botlib_import.FS_Write = FS_Write;
 	botlib_import.FS_FCloseFile = FS_FCloseFile;
 	botlib_import.FS_Seek = FS_Seek;

```
