# Diff: `code/server/server.h`
**Canonical:** `wolfcamql-src` (sha256 `58d266136ed0...`, 16879 bytes)

## Variants

### `quake3-source`  — sha256 `b8190c64aecf...`, 14557 bytes

_Diff stat: +24 / -119 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\server.h	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\server.h	2026-04-16 20:02:19.975633600 +0100
@@ -15,13 +15,13 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // server.h
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "../qcommon/qcommon.h"
 #include "../game/g_public.h"
 #include "../game/bg_public.h"
@@ -33,21 +33,6 @@
 
 #define	MAX_ENT_CLUSTERS	16
 
-#ifdef USE_VOIP
-#define VOIP_QUEUE_LENGTH 64
-
-typedef struct voipServerPacket_s
-{
-	int generation;
-	int sequence;
-	int frames;
-	int len;
-	int sender;
-	int flags;
-	byte data[4000];
-} voipServerPacket_t;
-#endif
-
 typedef struct svEntity_s {
 	struct worldSector_s *worldSector;
 	struct svEntity_s *nextEntityInWorldSector;
@@ -78,6 +63,7 @@
 	int				snapshotCounter;	// incremented for each snapshot built
 	int				timeResidual;		// <= 1000 / sv_frame->value
 	int				nextFrameTime;		// when time > nextFrameTime, process world
+	struct cmodel_s	*models[MAX_MODELS];
 	char			*configstrings[MAX_CONFIGSTRINGS];
 	svEntity_t		svEntities[MAX_GENTITIES];
 
@@ -92,7 +78,6 @@
 	int				gameClientSize;		// will be > sizeof(playerState_t) due to game private data
 
 	int				restartTime;
-	int				time;
 } server_t;
 
 
@@ -124,9 +109,6 @@
 typedef struct netchan_buffer_s {
 	msg_t           msg;
 	byte            msgBuffer[MAX_MSGLEN];
-#ifdef LEGACY_PROTOCOL
-	char			clientCommandString[MAX_STRING_CHARS];  // valid command string for SV_Netchan_Encode
-#endif
 	struct netchan_buffer_s *next;
 } netchan_buffer_t;
 
@@ -135,9 +117,9 @@
 	char			userinfo[MAX_INFO_STRING];		// name, etc
 
 	char			reliableCommands[MAX_RELIABLE_COMMANDS][MAX_STRING_CHARS];
-	int				reliableSequence;		// last added reliable message, not necessarily sent or acknowledged yet
+	int				reliableSequence;		// last added reliable message, not necesarily sent or acknowledged yet
 	int				reliableAcknowledge;	// last acknowledged reliable message
-	int				reliableSent;			// last sent reliable message, not necessarily acknowledged yet
+	int				reliableSent;			// last sent reliable message, not necesarily acknowledged yet
 	int				messageAcknowledge;
 
 	int				gamestateMessageNum;	// netchan->outgoingSequence of gamestate
@@ -167,7 +149,7 @@
 	int				nextReliableTime;	// svs.time when another reliable command will be allowed
 	int				lastPacketTime;		// svs.time when packet was last received
 	int				lastConnectTime;	// svs.time when connection started
-	int				lastSnapshotTime;	// svs.time of last sent snapshot
+	int				nextSnapshotTime;	// send another snapshot when svs.time >= nextSnapshotTime
 	qboolean		rateDelayed;		// true if nextSnapshotTime was set based on rate instead of snapshotMsec
 	int				timeoutCount;		// must timeout a few frames in a row so debugging doesn't break
 	clientSnapshot_t	frames[PACKET_BACKUP];	// updates can be delta'd from here
@@ -183,22 +165,6 @@
 	// buffer them into this queue, and hand them out to netchan as needed
 	netchan_buffer_t *netchan_start_queue;
 	netchan_buffer_t **netchan_end_queue;
-
-#ifdef USE_VOIP
-	qboolean hasVoip;
-	qboolean muteAllVoip;
-	qboolean ignoreVoipFromClient[MAX_CLIENTS];
-	voipServerPacket_t *voipPacket[VOIP_QUEUE_LENGTH];
-	int queuedVoipPackets;
-	int queuedVoipIndex;
-#endif
-
-	int				oldServerTime;
-	qboolean		csUpdated[MAX_CONFIGSTRINGS];
-
-#ifdef LEGACY_PROTOCOL
-	qboolean	compat;
-#endif
 } client_t;
 
 //=============================================================================
@@ -207,25 +173,23 @@
 // MAX_CHALLENGES is made large to prevent a denial
 // of service attack that could cycle all of them
 // out before legitimate users connected
-#define	MAX_CHALLENGES	2048
-// Allow a certain amount of challenges to have the same IP address
-// to make it a bit harder to DOS one single IP address from connecting
-// while not allowing a single ip to grab all challenge resources
-#define MAX_CHALLENGES_MULTI (MAX_CHALLENGES / 2)
+#define	MAX_CHALLENGES	1024
 
 #define	AUTHORIZE_TIMEOUT	5000
 
 typedef struct {
 	netadr_t	adr;
 	int			challenge;
-	int			clientChallenge;		// challenge number coming from the client
 	int			time;				// time the last packet was sent to the autherize server
 	int			pingTime;			// time the challenge response was sent to client
 	int			firstTime;			// time the adr was first used, for authorize timeout checks
-	qboolean	wasrefused;
 	qboolean	connected;
 } challenge_t;
 
+
+#define	MAX_MASTERS	8				// max recipients for heartbeat packets
+
+
 // this structure will be cleared only when the game dll changes
 typedef struct {
 	qboolean	initialized;				// sv_init has completed
@@ -235,28 +199,15 @@
 	int			snapFlagServerBit;			// ^= SNAPFLAG_SERVERCOUNT every SV_SpawnServer()
 
 	client_t	*clients;					// [sv_maxclients->integer];
-	int      numSnapshotEntities;    // sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
+	int			numSnapshotEntities;		// sv_maxclients->integer*PACKET_BACKUP*MAX_PACKET_ENTITIES
 	int			nextSnapshotEntities;		// next snapshotEntities to use
 	entityState_t	*snapshotEntities;		// [numSnapshotEntities]
 	int			nextHeartbeatTime;
 	challenge_t	challenges[MAX_CHALLENGES];	// to prevent invalid IPs from connecting
 	netadr_t	redirectAddress;			// for rcon return messages
-#ifndef STANDALONE
-	netadr_t	authorizeAddress;			// authorize server address
-#endif
-	int			masterResolveTime[MAX_MASTER_SERVERS]; // next svs.time that server should do dns lookup for master server
-} serverStatic_t;
 
-#define SERVER_MAXBANS	1024
-// Structure for managing bans
-typedef struct
-{
-	netadr_t ip;
-	// For a CIDR-Notation type suffix
-	int subnet;
-	
-	qboolean isexception;
-} serverBan_t;
+	netadr_t	authorizeAddress;			// for rcon return messages
+} serverStatic_t;
 
 //=============================================================================
 
@@ -264,6 +215,8 @@
 extern	server_t		sv;					// cleared each map
 extern	vm_t			*gvm;				// game virtual machine
 
+#define	MAX_MASTER_SERVERS	5
+
 extern	cvar_t	*sv_fps;
 extern	cvar_t	*sv_timeout;
 extern	cvar_t	*sv_zombietime;
@@ -282,70 +235,31 @@
 extern	cvar_t	*sv_mapname;
 extern	cvar_t	*sv_mapChecksum;
 extern	cvar_t	*sv_serverid;
-extern	cvar_t	*sv_minRate;
 extern	cvar_t	*sv_maxRate;
-extern 	cvar_t	*sv_dlRate;
 extern	cvar_t	*sv_minPing;
 extern	cvar_t	*sv_maxPing;
 extern	cvar_t	*sv_gametype;
 extern	cvar_t	*sv_pure;
 extern	cvar_t	*sv_floodProtect;
 extern	cvar_t	*sv_lanForceRate;
-#ifndef STANDALONE
 extern	cvar_t	*sv_strictAuth;
-#endif
-extern	cvar_t	*sv_banFile;
-
-extern cvar_t *sv_broadcastAll;
-
-extern	serverBan_t serverBans[SERVER_MAXBANS];
-extern	int serverBansCount;
-
-#ifdef USE_VOIP
-extern	cvar_t	*sv_voip;
-extern 	cvar_t	*sv_voipProtocol;
-#endif
-
-extern cvar_t *sv_randomClientSlot;
-
 
 //===========================================================
 
 //
 // sv_main.c
 //
-typedef struct leakyBucket_s leakyBucket_t;
-struct leakyBucket_s {
-	netadrtype_t	type;
-
-	union {
-		byte	_4[4];
-		byte	_6[16];
-	} ipv;
-
-	int						lastTime;
-	signed char		burst;
-
-	long					hash;
-
-	leakyBucket_t *prev, *next;
-};
-
-extern leakyBucket_t outboundLeakyBucket;
-
-qboolean SVC_RateLimit( leakyBucket_t *bucket, int burst, int period );
-qboolean SVC_RateLimitAddress( netadr_t from, int burst, int period );
-
 void SV_FinalMessage (char *message);
-void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...);
 
 
 void SV_AddOperatorCommands (void);
 void SV_RemoveOperatorCommands (void);
 
 
+void SV_MasterHeartbeat (void);
 void SV_MasterShutdown (void);
-int SV_RateMsec(client_t *client);
+
 
 
 
@@ -354,7 +268,6 @@
 //
 void SV_SetConfigstring( int index, const char *val );
 void SV_GetConfigstring( int index, char *buffer, int bufferSize );
-void SV_UpdateConfigstrings( client_t *client );
 
 void SV_SetUserinfo( int index, const char *val );
 void SV_GetUserinfo( int index, char *buffer, int bufferSize );
@@ -367,28 +280,22 @@
 //
 // sv_client.c
 //
-void SV_GetChallenge(netadr_t from);
+void SV_GetChallenge( netadr_t from );
 
 void SV_DirectConnect( netadr_t from );
 
-#ifndef STANDALONE
 void SV_AuthorizeIpPacket( netadr_t from );
-#endif
 
 void SV_ExecuteClientMessage( client_t *cl, msg_t *msg );
 void SV_UserinfoChanged( client_t *cl );
 
 void SV_ClientEnterWorld( client_t *client, usercmd_t *cmd );
-void SV_FreeClient(client_t *client);
 void SV_DropClient( client_t *drop, const char *reason );
 
 void SV_ExecuteClientCommand( client_t *cl, const char *s, qboolean clientOK );
 void SV_ClientThink (client_t *cl, usercmd_t *cmd);
 
-int SV_WriteDownloadToClient(client_t *cl , msg_t *msg);
-int SV_SendDownloadMessages(void);
-int SV_SendQueuedMessages(void);
-
+void SV_WriteDownloadToClient( client_t *cl , msg_t *msg );
 
 //
 // sv_ccmds.c
@@ -434,8 +341,6 @@
 int BotImport_DebugPolygonCreate(int color, int numPoints, vec3_t *points);
 void BotImport_DebugPolygonDelete(int id);
 
-void SV_BotInitBotLib(void);
-
 //============================================================
 //
 // high level object sorting to reduce interaction tests
@@ -451,7 +356,7 @@
 void SV_LinkEntity( sharedEntity_t *ent );
 // Needs to be called any time an entity changes origin, mins, maxs,
 // or solid.  Automatically unlinks if needed.
-// sets ent->r.absmin and ent->r.absmax
+// sets ent->v.absmin and ent->v.absmax
 // sets ent->leafnums[] for pvs determination even if the entity
 // is not solid
 
@@ -494,6 +399,6 @@
 // sv_net_chan.c
 //
 void SV_Netchan_Transmit( client_t *client, msg_t *msg);
-int SV_Netchan_TransmitNextFragment(client_t *client);
+void SV_Netchan_TransmitNextFragment( client_t *client );
 qboolean SV_Netchan_Process( client_t *client, msg_t *msg );
-void SV_Netchan_FreeQueue(client_t *client);
+

```

### `ioquake3`  — sha256 `3029740b6b22...`, 16798 bytes

_Diff stat: +6 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\server.h	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\server.h	2026-04-16 20:02:21.618758900 +0100
@@ -125,7 +125,7 @@
 	msg_t           msg;
 	byte            msgBuffer[MAX_MSGLEN];
 #ifdef LEGACY_PROTOCOL
-	char			clientCommandString[MAX_STRING_CHARS];  // valid command string for SV_Netchan_Encode
+	char		clientCommandString[MAX_STRING_CHARS];	// valid command string for SV_Netchan_Encode
 #endif
 	struct netchan_buffer_s *next;
 } netchan_buffer_t;
@@ -195,9 +195,9 @@
 
 	int				oldServerTime;
 	qboolean		csUpdated[MAX_CONFIGSTRINGS];
-
+	
 #ifdef LEGACY_PROTOCOL
-	qboolean	compat;
+	qboolean		compat;
 #endif
 } client_t;
 
@@ -235,7 +235,7 @@
 	int			snapFlagServerBit;			// ^= SNAPFLAG_SERVERCOUNT every SV_SpawnServer()
 
 	client_t	*clients;					// [sv_maxclients->integer];
-	int      numSnapshotEntities;    // sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
+	int			numSnapshotEntities;		// sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
 	int			nextSnapshotEntities;		// next snapshotEntities to use
 	entityState_t	*snapshotEntities;		// [numSnapshotEntities]
 	int			nextHeartbeatTime;
@@ -284,7 +284,7 @@
 extern	cvar_t	*sv_serverid;
 extern	cvar_t	*sv_minRate;
 extern	cvar_t	*sv_maxRate;
-extern 	cvar_t	*sv_dlRate;
+extern	cvar_t	*sv_dlRate;
 extern	cvar_t	*sv_minPing;
 extern	cvar_t	*sv_maxPing;
 extern	cvar_t	*sv_gametype;
@@ -296,18 +296,14 @@
 #endif
 extern	cvar_t	*sv_banFile;
 
-extern cvar_t *sv_broadcastAll;
-
 extern	serverBan_t serverBans[SERVER_MAXBANS];
 extern	int serverBansCount;
 
 #ifdef USE_VOIP
 extern	cvar_t	*sv_voip;
-extern 	cvar_t	*sv_voipProtocol;
+extern	cvar_t	*sv_voipProtocol;
 #endif
 
-extern cvar_t *sv_randomClientSlot;
-
 
 //===========================================================
 

```

### `quake3e`  — sha256 `cd8f896c0e8e...`, 17388 bytes

_Diff stat: +146 / -145 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\server.h	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\server\server.h	2026-04-16 20:02:27.365920300 +0100
@@ -23,6 +23,7 @@
 
 #include "../qcommon/q_shared.h"
 #include "../qcommon/qcommon.h"
+#include "../qcommon/vm_local.h"
 #include "../game/g_public.h"
 #include "../game/bg_public.h"
 
@@ -33,25 +34,10 @@
 
 #define	MAX_ENT_CLUSTERS	16
 
-#ifdef USE_VOIP
-#define VOIP_QUEUE_LENGTH 64
-
-typedef struct voipServerPacket_s
-{
-	int generation;
-	int sequence;
-	int frames;
-	int len;
-	int sender;
-	int flags;
-	byte data[4000];
-} voipServerPacket_t;
-#endif
-
 typedef struct svEntity_s {
 	struct worldSector_s *worldSector;
 	struct svEntity_s *nextEntityInWorldSector;
-	
+
 	entityState_t	baseline;		// for delta compression of initial sighting
 	int			numClusters;		// if -1, use headnode instead
 	int			clusternums[MAX_ENT_CLUSTERS];
@@ -66,22 +52,31 @@
 	SS_GAME				// actively running
 } serverState_t;
 
+// we might not use all MAX_GENTITIES every frame
+// so leave more room for slow-snaps clients etc.
+#define NUM_SNAPSHOT_FRAMES (PACKET_BACKUP*4)
+
+typedef struct snapshotFrame_s {
+	entityState_t *ents[ MAX_GENTITIES ];
+	int	frameNum;
+	int start;
+	int count;
+} snapshotFrame_t;
+
 typedef struct {
 	serverState_t	state;
 	qboolean		restarting;			// if true, send configstring changes during SS_LOADING
+	int				pure;				// fixed at level spawn
+	int				maxclients;			// fixed at level spawn
 	int				serverId;			// changes each server start
-	int				restartedServerId;	// serverId before a map_restart
+	int				restartedServerId;	// changes each map restart
 	int				checksumFeed;		// the feed key that we use to compute the pure checksum strings
-	// https://zerowing.idsoftware.com/bugzilla/show_bug.cgi?id=475
-	// the serverId associated with the current checksumFeed (always <= serverId)
-	int       checksumFeedServerId;	
 	int				snapshotCounter;	// incremented for each snapshot built
 	int				timeResidual;		// <= 1000 / sv_frame->value
-	int				nextFrameTime;		// when time > nextFrameTime, process world
 	char			*configstrings[MAX_CONFIGSTRINGS];
 	svEntity_t		svEntities[MAX_GENTITIES];
 
-	char			*entityParsePoint;	// used during game VM init
+	const char		*entityParsePoint;	// used during game VM init
 
 	// the game virtual machine will update these on init and changes
 	sharedEntity_t	*gentities;
@@ -93,30 +88,34 @@
 
 	int				restartTime;
 	int				time;
-} server_t;
-
-
-
 
+	byte			baselineUsed[ MAX_GENTITIES ];
+} server_t;
 
 typedef struct {
 	int				areabytes;
 	byte			areabits[MAX_MAP_AREA_BYTES];		// portalarea visibility bits
 	playerState_t	ps;
 	int				num_entities;
+#if 0
 	int				first_entity;		// into the circular sv_packet_entities[]
 										// the entities MUST be in increasing state number
 										// order, otherwise the delta compression will fail
+#endif
 	int				messageSent;		// time the message was transmitted
 	int				messageAcked;		// time the message was acked
 	int				messageSize;		// used to rate drop packets
+
+	int				frameNum;			// from snapshot storage to compare with last valid
+	entityState_t	*ents[ MAX_SNAPSHOT_ENTITIES ];
+
 } clientSnapshot_t;
 
 typedef enum {
-	CS_FREE,		// can be reused for a new connection
+	CS_FREE = 0,	// can be reused for a new connection
 	CS_ZOMBIE,		// client has been disconnected, but don't reuse
 					// connection for a couple seconds
-	CS_CONNECTED,	// has been assigned to a client_t, but no gamestate yet
+	CS_CONNECTED,	// has been assigned to a client_t, but no gamestate yet or downloading
 	CS_PRIMED,		// gamestate has been sent, but client hasn't sent a usercmd
 	CS_ACTIVE		// client is fully in game
 } clientState_t;
@@ -124,12 +123,39 @@
 typedef struct netchan_buffer_s {
 	msg_t           msg;
 	byte            msgBuffer[MAX_MSGLEN];
-#ifdef LEGACY_PROTOCOL
-	char			clientCommandString[MAX_STRING_CHARS];  // valid command string for SV_Netchan_Encode
-#endif
+	char		clientCommandString[MAX_STRING_CHARS];	// valid command string for SV_Netchan_Encode
 	struct netchan_buffer_s *next;
 } netchan_buffer_t;
 
+typedef struct rateLimit_s {
+	int			lastTime;
+	int			burst;
+} rateLimit_t;
+
+typedef struct leakyBucket_s leakyBucket_t;
+struct leakyBucket_s {
+	netadrtype_t	type;
+
+	union {
+		byte	_4[4];
+		byte	_6[16];
+	} ipv;
+
+	rateLimit_t rate;
+
+	int			hash;
+	int			toxic;
+
+	leakyBucket_t *prev, *next;
+};
+
+typedef enum {
+	GSA_INIT = 0,	// gamestate never sent with current sv.serverId
+	GSA_SENT_ONCE,	// gamestate sent once, client can reply with any (messageAcknowledge - gamestateMessageNum) >= 0 and correct serverId
+	GSA_SENT_MANY,	// gamestate sent many times, client must reply with exact gamestateMessageNum == gamestateMessageNum and correct serverId
+	GSA_ACKED		// gamestate acknowledged, no retansmissions needed
+} gameStateAck_t;
+
 typedef struct client_s {
 	clientState_t	state;
 	char			userinfo[MAX_INFO_STRING];		// name, etc
@@ -137,19 +163,21 @@
 	char			reliableCommands[MAX_RELIABLE_COMMANDS][MAX_STRING_CHARS];
 	int				reliableSequence;		// last added reliable message, not necessarily sent or acknowledged yet
 	int				reliableAcknowledge;	// last acknowledged reliable message
-	int				reliableSent;			// last sent reliable message, not necessarily acknowledged yet
 	int				messageAcknowledge;
 
 	int				gamestateMessageNum;	// netchan->outgoingSequence of gamestate
 	int				challenge;
 
 	usercmd_t		lastUsercmd;
-	int				lastMessageNum;		// for delta compression
 	int				lastClientCommand;	// reliable client message sequence
 	char			lastClientCommandString[MAX_STRING_CHARS];
 	sharedEntity_t	*gentity;			// SV_GentityNum(clientnum)
 	char			name[MAX_NAME_LENGTH];			// extracted from userinfo, high bits masked
 
+	gameStateAck_t	gamestateAck;
+	qboolean		downloading;		// set at "download", reset at gamestate retransmission
+	// int				serverId;		// last acknowledged serverId
+
 	// downloading
 	char			downloadName[MAX_QPATH]; // if not empty string, we are downloading
 	fileHandle_t	download;			// file being downloaded
@@ -164,18 +192,18 @@
 	int				downloadSendTime;	// time we last got an ack from the client
 
 	int				deltaMessage;		// frame last client usercmd message
-	int				nextReliableTime;	// svs.time when another reliable command will be allowed
 	int				lastPacketTime;		// svs.time when packet was last received
 	int				lastConnectTime;	// svs.time when connection started
+	int				lastDisconnectTime;
 	int				lastSnapshotTime;	// svs.time of last sent snapshot
 	qboolean		rateDelayed;		// true if nextSnapshotTime was set based on rate instead of snapshotMsec
 	int				timeoutCount;		// must timeout a few frames in a row so debugging doesn't break
 	clientSnapshot_t	frames[PACKET_BACKUP];	// updates can be delta'd from here
 	int				ping;
-	int				rate;				// bytes / second
+	int				rate;				// bytes / second, 0 - unlimited
 	int				snapshotMsec;		// requests a snapshot every snapshotMsec unless rate choked
-	int				pureAuthentic;
-	qboolean  gotCP; // TTimo - additional flag to distinguish between a bad pure checksum, and no cp command at all
+	qboolean		pureAuthentic;
+	qboolean		gotCP;				// TTimo - additional flag to distinguish between a bad pure checksum, and no cp command at all
 	netchan_t		netchan;
 	// TTimo
 	// queuing outgoing fragmented messages to send them properly, without udp packet bursts
@@ -184,69 +212,57 @@
 	netchan_buffer_t *netchan_start_queue;
 	netchan_buffer_t **netchan_end_queue;
 
-#ifdef USE_VOIP
-	qboolean hasVoip;
-	qboolean muteAllVoip;
-	qboolean ignoreVoipFromClient[MAX_CLIENTS];
-	voipServerPacket_t *voipPacket[VOIP_QUEUE_LENGTH];
-	int queuedVoipPackets;
-	int queuedVoipIndex;
-#endif
-
 	int				oldServerTime;
 	qboolean		csUpdated[MAX_CONFIGSTRINGS];
+	qboolean		compat;
 
-#ifdef LEGACY_PROTOCOL
-	qboolean	compat;
-#endif
-} client_t;
+	// flood protection
+	rateLimit_t		cmd_rate;
+	rateLimit_t		info_rate;
+	rateLimit_t		gamestate_rate;
 
-//=============================================================================
+	// client can decode long strings
+	qboolean		longstr;
 
+	qboolean		justConnected;
 
-// MAX_CHALLENGES is made large to prevent a denial
-// of service attack that could cycle all of them
-// out before legitimate users connected
-#define	MAX_CHALLENGES	2048
-// Allow a certain amount of challenges to have the same IP address
-// to make it a bit harder to DOS one single IP address from connecting
-// while not allowing a single ip to grab all challenge resources
-#define MAX_CHALLENGES_MULTI (MAX_CHALLENGES / 2)
+	char			tld[3]; // "XX\0"
+	const char		*country;
 
-#define	AUTHORIZE_TIMEOUT	5000
+} client_t;
+
+//=============================================================================
 
-typedef struct {
-	netadr_t	adr;
-	int			challenge;
-	int			clientChallenge;		// challenge number coming from the client
-	int			time;				// time the last packet was sent to the autherize server
-	int			pingTime;			// time the challenge response was sent to client
-	int			firstTime;			// time the adr was first used, for authorize timeout checks
-	qboolean	wasrefused;
-	qboolean	connected;
-} challenge_t;
 
 // this structure will be cleared only when the game dll changes
 typedef struct {
 	qboolean	initialized;				// sv_init has completed
 
 	int			time;						// will be strictly increasing across level changes
+	int			msgTime;					// will be used as precise sent time
 
 	int			snapFlagServerBit;			// ^= SNAPFLAG_SERVERCOUNT every SV_SpawnServer()
 
 	client_t	*clients;					// [sv_maxclients->integer];
-	int      numSnapshotEntities;    // sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
-	int			nextSnapshotEntities;		// next snapshotEntities to use
+	int			numSnapshotEntities;		// PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
 	entityState_t	*snapshotEntities;		// [numSnapshotEntities]
 	int			nextHeartbeatTime;
-	challenge_t	challenges[MAX_CHALLENGES];	// to prevent invalid IPs from connecting
-	netadr_t	redirectAddress;			// for rcon return messages
-#ifndef STANDALONE
-	netadr_t	authorizeAddress;			// authorize server address
-#endif
+
+	netadr_t	authorizeAddress;			// for rcon return messages
 	int			masterResolveTime[MAX_MASTER_SERVERS]; // next svs.time that server should do dns lookup for master server
+
+	// common snapshot storage
+	int			freeStorageEntities;
+	int			currentStoragePosition;	// next snapshotEntities to use
+	int			snapshotFrame;			// incremented with each common snapshot built
+	int			currentSnapshotFrame;	// for initializing empty frames
+	int			lastValidFrame;			// updated with each snapshot built
+	snapshotFrame_t	snapFrames[ NUM_SNAPSHOT_FRAMES ];
+	snapshotFrame_t	*currFrame; // current frame that clients can refer
+
 } serverStatic_t;
 
+#ifdef USE_BANS
 #define SERVER_MAXBANS	1024
 // Structure for managing bans
 typedef struct
@@ -254,9 +270,10 @@
 	netadr_t ip;
 	// For a CIDR-Notation type suffix
 	int subnet;
-	
+
 	qboolean isexception;
 } serverBan_t;
+#endif
 
 //=============================================================================
 
@@ -271,82 +288,54 @@
 extern	cvar_t	*sv_privatePassword;
 extern	cvar_t	*sv_allowDownload;
 extern	cvar_t	*sv_maxclients;
+extern	cvar_t	*sv_maxclientsPerIP;
+extern	cvar_t	*sv_clientTLD;
 
 extern	cvar_t	*sv_privateClients;
 extern	cvar_t	*sv_hostname;
 extern	cvar_t	*sv_master[MAX_MASTER_SERVERS];
 extern	cvar_t	*sv_reconnectlimit;
-extern	cvar_t	*sv_showloss;
 extern	cvar_t	*sv_padPackets;
 extern	cvar_t	*sv_killserver;
 extern	cvar_t	*sv_mapname;
 extern	cvar_t	*sv_mapChecksum;
+extern	cvar_t	*sv_referencedPakNames;
 extern	cvar_t	*sv_serverid;
 extern	cvar_t	*sv_minRate;
 extern	cvar_t	*sv_maxRate;
-extern 	cvar_t	*sv_dlRate;
-extern	cvar_t	*sv_minPing;
-extern	cvar_t	*sv_maxPing;
+extern	cvar_t	*sv_dlRate;
 extern	cvar_t	*sv_gametype;
 extern	cvar_t	*sv_pure;
 extern	cvar_t	*sv_floodProtect;
 extern	cvar_t	*sv_lanForceRate;
-#ifndef STANDALONE
-extern	cvar_t	*sv_strictAuth;
-#endif
-extern	cvar_t	*sv_banFile;
 
-extern cvar_t *sv_broadcastAll;
+extern	cvar_t *sv_levelTimeReset;
+extern	cvar_t *sv_filter;
 
+#ifdef USE_BANS
+extern	cvar_t	*sv_banFile;
 extern	serverBan_t serverBans[SERVER_MAXBANS];
 extern	int serverBansCount;
-
-#ifdef USE_VOIP
-extern	cvar_t	*sv_voip;
-extern 	cvar_t	*sv_voipProtocol;
 #endif
 
-extern cvar_t *sv_randomClientSlot;
-
-
 //===========================================================
 
 //
 // sv_main.c
 //
-typedef struct leakyBucket_s leakyBucket_t;
-struct leakyBucket_s {
-	netadrtype_t	type;
-
-	union {
-		byte	_4[4];
-		byte	_6[16];
-	} ipv;
-
-	int						lastTime;
-	signed char		burst;
-
-	long					hash;
-
-	leakyBucket_t *prev, *next;
-};
-
-extern leakyBucket_t outboundLeakyBucket;
-
-qboolean SVC_RateLimit( leakyBucket_t *bucket, int burst, int period );
-qboolean SVC_RateLimitAddress( netadr_t from, int burst, int period );
-
-void SV_FinalMessage (char *message);
-void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+qboolean SVC_RateLimit( rateLimit_t *bucket, int burst, int period );
+qboolean SVC_RateLimitAddress( const netadr_t *from, int burst, int period );
+void SVC_RateRestoreBurstAddress( const netadr_t *from, int burst, int period );
+void SVC_RateRestoreToxicAddress( const netadr_t *from, int burst, int period );
+void SVC_RateDropAddress( const netadr_t *from, int burst, int period );
 
+void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 
-void SV_AddOperatorCommands (void);
-void SV_RemoveOperatorCommands (void);
-
-
-void SV_MasterShutdown (void);
-int SV_RateMsec(client_t *client);
+void SV_AddOperatorCommands( void );
+void SV_RemoveOperatorCommands( void );
 
+void SV_MasterShutdown( void );
+int SV_RateMsec( const client_t *client );
 
 
 //
@@ -359,52 +348,56 @@
 void SV_SetUserinfo( int index, const char *val );
 void SV_GetUserinfo( int index, char *buffer, int bufferSize );
 
-void SV_ChangeMaxClients( void );
-void SV_SpawnServer( char *server, qboolean killBots );
+void SV_SpawnServer( const char *mapname, qboolean killBots );
 
 
 
 //
 // sv_client.c
 //
-void SV_GetChallenge(netadr_t from);
+void SV_GetChallenge( const netadr_t *from );
+void SV_InitChallenger( void );
 
-void SV_DirectConnect( netadr_t from );
-
-#ifndef STANDALONE
-void SV_AuthorizeIpPacket( netadr_t from );
-#endif
+void SV_DirectConnect( const netadr_t *from );
+void SV_PrintClientStateChange( const client_t *cl, clientState_t newState );
 
 void SV_ExecuteClientMessage( client_t *cl, msg_t *msg );
-void SV_UserinfoChanged( client_t *cl );
+void SV_UserinfoChanged( client_t *cl, qboolean updateUserinfo, qboolean runFilter );
 
-void SV_ClientEnterWorld( client_t *client, usercmd_t *cmd );
-void SV_FreeClient(client_t *client);
+void SV_ClientEnterWorld( client_t *client );
+void SV_FreeClient( client_t *client );
 void SV_DropClient( client_t *drop, const char *reason );
 
-void SV_ExecuteClientCommand( client_t *cl, const char *s, qboolean clientOK );
-void SV_ClientThink (client_t *cl, usercmd_t *cmd);
+qboolean SV_ExecuteClientCommand( client_t *cl, const char *s );
+void SV_ClientThink( client_t *cl, usercmd_t *cmd );
 
-int SV_WriteDownloadToClient(client_t *cl , msg_t *msg);
-int SV_SendDownloadMessages(void);
-int SV_SendQueuedMessages(void);
+int SV_SendDownloadMessages( void );
+int SV_SendQueuedMessages( void );
 
+void SV_FreeIP4DB( void );
+void SV_PrintLocations_f( client_t *client );
 
 //
 // sv_ccmds.c
 //
 void SV_Heartbeat_f( void );
+client_t *SV_GetPlayerByHandle( void );
 
 //
 // sv_snapshot.c
 //
 void SV_AddServerCommand( client_t *client, const char *cmd );
 void SV_UpdateServerCommandsToClient( client_t *client, msg_t *msg );
-void SV_WriteFrameToClient (client_t *client, msg_t *msg);
+void SV_WriteFrameToClient( client_t *client, msg_t *msg );
 void SV_SendMessageToClient( msg_t *msg, client_t *client );
 void SV_SendClientMessages( void );
 void SV_SendClientSnapshot( client_t *client );
 
+void SV_InitSnapshotStorage( void );
+void SV_IssueNewSnapshot( void );
+
+int SV_RemainingGameState( void );
+
 //
 // sv_game.c
 //
@@ -475,7 +468,7 @@
 // returns the CONTENTS_* value from the world and all entities at the given point.
 
 
-void SV_Trace( trace_t *results, const vec3_t start, vec3_t mins, vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask, int capsule );
+void SV_Trace( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask, qboolean capsule );
 // mins and maxs are relative
 
 // if the entire move stays in a solid volume, trace.allsolid will be set,
@@ -487,13 +480,21 @@
 // passEntityNum is explicitly excluded from clipping checks (normally ENTITYNUM_NONE)
 
 
-void SV_ClipToEntity( trace_t *trace, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int entityNum, int contentmask, int capsule );
+void SV_ClipToEntity( trace_t *trace, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int entityNum, int contentmask, qboolean capsule );
 // clip to a specific entity
 
 //
 // sv_net_chan.c
 //
 void SV_Netchan_Transmit( client_t *client, msg_t *msg);
-int SV_Netchan_TransmitNextFragment(client_t *client);
+int SV_Netchan_TransmitNextFragment( client_t *client );
 qboolean SV_Netchan_Process( client_t *client, msg_t *msg );
-void SV_Netchan_FreeQueue(client_t *client);
+void SV_Netchan_FreeQueue( client_t *client );
+
+//
+// sv_filter.c
+//
+void SV_LoadFilters( const char *filename );
+const char *SV_RunFilters( const char *userinfo, const netadr_t *addr );
+void SV_AddFilter_f( void );
+void SV_AddFilterCmd_f( void );

```

### `openarena-engine`  — sha256 `283e9d8db2ac...`, 16699 bytes

_Diff stat: +13 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\server.h	2026-04-16 20:02:25.267779500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\server.h	2026-04-16 22:48:25.934962600 +0100
@@ -44,7 +44,7 @@
 	int len;
 	int sender;
 	int flags;
-	byte data[4000];
+	byte data[1024];
 } voipServerPacket_t;
 #endif
 
@@ -125,7 +125,7 @@
 	msg_t           msg;
 	byte            msgBuffer[MAX_MSGLEN];
 #ifdef LEGACY_PROTOCOL
-	char			clientCommandString[MAX_STRING_CHARS];  // valid command string for SV_Netchan_Encode
+	char		clientCommandString[MAX_STRING_CHARS];	// valid command string for SV_Netchan_Encode
 #endif
 	struct netchan_buffer_s *next;
 } netchan_buffer_t;
@@ -135,9 +135,9 @@
 	char			userinfo[MAX_INFO_STRING];		// name, etc
 
 	char			reliableCommands[MAX_RELIABLE_COMMANDS][MAX_STRING_CHARS];
-	int				reliableSequence;		// last added reliable message, not necessarily sent or acknowledged yet
+	int				reliableSequence;		// last added reliable message, not necesarily sent or acknowledged yet
 	int				reliableAcknowledge;	// last acknowledged reliable message
-	int				reliableSent;			// last sent reliable message, not necessarily acknowledged yet
+	int				reliableSent;			// last sent reliable message, not necesarily acknowledged yet
 	int				messageAcknowledge;
 
 	int				gamestateMessageNum;	// netchan->outgoingSequence of gamestate
@@ -195,9 +195,9 @@
 
 	int				oldServerTime;
 	qboolean		csUpdated[MAX_CONFIGSTRINGS];
-
+	
 #ifdef LEGACY_PROTOCOL
-	qboolean	compat;
+	qboolean		compat;
 #endif
 } client_t;
 
@@ -235,16 +235,14 @@
 	int			snapFlagServerBit;			// ^= SNAPFLAG_SERVERCOUNT every SV_SpawnServer()
 
 	client_t	*clients;					// [sv_maxclients->integer];
-	int      numSnapshotEntities;    // sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
+	int			numSnapshotEntities;		// sv_maxclients->integer*PACKET_BACKUP*MAX_SNAPSHOT_ENTITIES
 	int			nextSnapshotEntities;		// next snapshotEntities to use
 	entityState_t	*snapshotEntities;		// [numSnapshotEntities]
 	int			nextHeartbeatTime;
 	challenge_t	challenges[MAX_CHALLENGES];	// to prevent invalid IPs from connecting
 	netadr_t	redirectAddress;			// for rcon return messages
-#ifndef STANDALONE
-	netadr_t	authorizeAddress;			// authorize server address
-#endif
-	int			masterResolveTime[MAX_MASTER_SERVERS]; // next svs.time that server should do dns lookup for master server
+
+	netadr_t	authorizeAddress;			// for rcon return messages
 } serverStatic_t;
 
 #define SERVER_MAXBANS	1024
@@ -284,30 +282,27 @@
 extern	cvar_t	*sv_serverid;
 extern	cvar_t	*sv_minRate;
 extern	cvar_t	*sv_maxRate;
-extern 	cvar_t	*sv_dlRate;
+extern	cvar_t	*sv_dlRate;
 extern	cvar_t	*sv_minPing;
 extern	cvar_t	*sv_maxPing;
 extern	cvar_t	*sv_gametype;
+extern	cvar_t	*sv_dorestart;
 extern	cvar_t	*sv_pure;
 extern	cvar_t	*sv_floodProtect;
 extern	cvar_t	*sv_lanForceRate;
 #ifndef STANDALONE
 extern	cvar_t	*sv_strictAuth;
 #endif
+extern	cvar_t	*sv_public;
 extern	cvar_t	*sv_banFile;
 
-extern cvar_t *sv_broadcastAll;
-
 extern	serverBan_t serverBans[SERVER_MAXBANS];
 extern	int serverBansCount;
 
 #ifdef USE_VOIP
 extern	cvar_t	*sv_voip;
-extern 	cvar_t	*sv_voipProtocol;
 #endif
 
-extern cvar_t *sv_randomClientSlot;
-
 
 //===========================================================
 
@@ -337,7 +332,7 @@
 qboolean SVC_RateLimitAddress( netadr_t from, int burst, int period );
 
 void SV_FinalMessage (char *message);
-void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...) Q_PRINTF_FUNC(2, 3);
+void QDECL SV_SendServerCommand( client_t *cl, const char *fmt, ...) __attribute__ ((format (printf, 2, 3)));
 
 
 void SV_AddOperatorCommands (void);

```
