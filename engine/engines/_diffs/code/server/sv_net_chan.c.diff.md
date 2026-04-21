# Diff: `code/server/sv_net_chan.c`
**Canonical:** `wolfcamql-src` (sha256 `112c3dfd323a...`, 7209 bytes)

## Variants

### `quake3-source`  — sha256 `d482d76bc7ef...`, 6500 bytes

_Diff stat: +66 / -134 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_net_chan.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_net_chan.c	2026-04-16 20:02:19.978633600 +0100
@@ -15,16 +15,15 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "../qcommon/qcommon.h"
 #include "server.h"
 
-#ifdef LEGACY_PROTOCOL
 /*
 ==============
 SV_Netchan_Encode
@@ -34,32 +33,30 @@
 
 ==============
 */
-static void SV_Netchan_Encode(client_t *client, msg_t *msg, const char *clientCommandString)
-{
-	long i, index;
+static void SV_Netchan_Encode( client_t *client, msg_t *msg ) {
+	long reliableAcknowledge, i, index;
 	byte key, *string;
-	int	srdc, sbit;
-	qboolean soob;
-
+        int	srdc, sbit, soob;
+        
 	if ( msg->cursize < SV_ENCODE_START ) {
 		return;
 	}
 
-	srdc = msg->readcount;
-	sbit = msg->bit;
-	soob = msg->oob;
-
-	msg->bit = 0;
-	msg->readcount = 0;
-	msg->oob = qfalse;
-
-	/* reliableAcknowledge = */ MSG_ReadLong(msg);
-
-	msg->oob = soob;
-	msg->bit = sbit;
-	msg->readcount = srdc;
+        srdc = msg->readcount;
+        sbit = msg->bit;
+        soob = msg->oob;
+        
+        msg->bit = 0;
+        msg->readcount = 0;
+        msg->oob = 0;
+        
+	reliableAcknowledge = MSG_ReadLong(msg);
 
-	string = (byte *) clientCommandString;
+        msg->oob = soob;
+        msg->bit = sbit;
+        msg->readcount = srdc;
+        
+	string = (byte *)client->lastClientCommandString;
 	index = 0;
 	// xor the client challenge with the netchan sequence number
 	key = client->challenge ^ client->netchan.outgoingSequence;
@@ -92,24 +89,23 @@
 */
 static void SV_Netchan_Decode( client_t *client, msg_t *msg ) {
 	int serverId, messageAcknowledge, reliableAcknowledge;
-	int i, index, srdc, sbit;
-	qboolean soob;
+	int i, index, srdc, sbit, soob;
 	byte key, *string;
 
-	srdc = msg->readcount;
-	sbit = msg->bit;
-	soob = msg->oob;
-
-	msg->oob = qfalse;
-
-	serverId = MSG_ReadLong(msg);
+        srdc = msg->readcount;
+        sbit = msg->bit;
+        soob = msg->oob;
+        
+        msg->oob = 0;
+        
+        serverId = MSG_ReadLong(msg);
 	messageAcknowledge = MSG_ReadLong(msg);
 	reliableAcknowledge = MSG_ReadLong(msg);
 
-	msg->oob = soob;
-	msg->bit = sbit;
-	msg->readcount = srdc;
-
+        msg->oob = soob;
+        msg->bit = sbit;
+        msg->readcount = srdc;
+        
 	string = (byte *)client->reliableCommands[ reliableAcknowledge & (MAX_RELIABLE_COMMANDS-1) ];
 	index = 0;
 	//
@@ -129,84 +125,38 @@
 		*(msg->data + i) = *(msg->data + i) ^ key;
 	}
 }
-#endif
-
-
-
-/*
-=================
-SV_Netchan_FreeQueue
-=================
-*/
-void SV_Netchan_FreeQueue(client_t *client)
-{
-	netchan_buffer_t *netbuf, *next;
-
-	for(netbuf = client->netchan_start_queue; netbuf; netbuf = next)
-	{
-		next = netbuf->next;
-		Z_Free(netbuf);
-	}
-
-	client->netchan_start_queue = NULL;
-	client->netchan_end_queue = &client->netchan_start_queue;
-}
-
-/*
-=================
-SV_Netchan_TransmitNextInQueue
-=================
-*/
-void SV_Netchan_TransmitNextInQueue(client_t *client)
-{
-	netchan_buffer_t *netbuf;
-		
-	Com_DPrintf("#462 Netchan_TransmitNextFragment: popping a queued message for transmit\n");
-	netbuf = client->netchan_start_queue;
-
-#ifdef LEGACY_PROTOCOL
-	if(client->compat)
-		SV_Netchan_Encode(client, &netbuf->msg, netbuf->clientCommandString);
-#endif
-
-	Netchan_Transmit(&client->netchan, netbuf->msg.cursize, netbuf->msg.data);
-
-	// pop from queue
-	client->netchan_start_queue = netbuf->next;
-	if(!client->netchan_start_queue)
-	{
-		Com_DPrintf("#462 Netchan_TransmitNextFragment: emptied queue\n");
-		client->netchan_end_queue = &client->netchan_start_queue;
-	}
-	else
-		Com_DPrintf("#462 Netchan_TransmitNextFragment: remaining queued message\n");
-
-	Z_Free(netbuf);
-}
 
 /*
 =================
 SV_Netchan_TransmitNextFragment
-Transmit the next fragment and the next queued packet
-Return number of ms until next message can be sent based on throughput given by client rate,
--1 if no packet was sent.
 =================
 */
-
-int SV_Netchan_TransmitNextFragment(client_t *client)
-{
-	if(client->netchan.unsentFragments)
-	{
-		Netchan_TransmitNextFragment(&client->netchan);
-		return SV_RateMsec(client);
-	}
-	else if(client->netchan_start_queue)
-	{
-		SV_Netchan_TransmitNextInQueue(client);
-		return SV_RateMsec(client);
-	}
-	
-	return -1;
+void SV_Netchan_TransmitNextFragment( client_t *client ) {
+	Netchan_TransmitNextFragment( &client->netchan );
+	if (!client->netchan.unsentFragments)
+	{
+		// make sure the netchan queue has been properly initialized (you never know)
+		if (!client->netchan_end_queue) {
+			Com_Error(ERR_DROP, "netchan queue is not properly initialized in SV_Netchan_TransmitNextFragment\n");
+		}
+		// the last fragment was transmitted, check wether we have queued messages
+		if (client->netchan_start_queue) {
+			netchan_buffer_t *netbuf;
+			Com_DPrintf("#462 Netchan_TransmitNextFragment: popping a queued message for transmit\n");
+			netbuf = client->netchan_start_queue;
+			SV_Netchan_Encode( client, &netbuf->msg );
+			Netchan_Transmit( &client->netchan, netbuf->msg.cursize, netbuf->msg.data );
+			// pop from queue
+			client->netchan_start_queue = netbuf->next;
+			if (!client->netchan_start_queue) {
+				Com_DPrintf("#462 Netchan_TransmitNextFragment: emptied queue\n");
+				client->netchan_end_queue = &client->netchan_start_queue;
+			}
+			else
+				Com_DPrintf("#462 Netchan_TransmitNextFragment: remaining queued message\n");
+			Z_Free(netbuf);
+		} 
+	}	
 }
 
 
@@ -221,35 +171,22 @@
 ================
 */
 
-void SV_Netchan_Transmit( client_t *client, msg_t *msg)
-{
+void SV_Netchan_Transmit( client_t *client, msg_t *msg) {	//int length, const byte *data ) {
 	MSG_WriteByte( msg, svc_EOF );
-
-	if(client->netchan.unsentFragments || client->netchan_start_queue)
-	{
+	if (client->netchan.unsentFragments) {
 		netchan_buffer_t *netbuf;
 		Com_DPrintf("#462 SV_Netchan_Transmit: unsent fragments, stacked\n");
-		netbuf = (netchan_buffer_t *) Z_Malloc(sizeof(netchan_buffer_t));
+		netbuf = (netchan_buffer_t *)Z_Malloc(sizeof(netchan_buffer_t));
 		// store the msg, we can't store it encoded, as the encoding depends on stuff we still have to finish sending
 		MSG_Copy(&netbuf->msg, netbuf->msgBuffer, sizeof( netbuf->msgBuffer ), msg);
-#ifdef LEGACY_PROTOCOL
-		if(client->compat)
-		{
-			Q_strncpyz(netbuf->clientCommandString, client->lastClientCommandString,
-					   sizeof(netbuf->clientCommandString));
-		}
-#endif
 		netbuf->next = NULL;
 		// insert it in the queue, the message will be encoded and sent later
 		*client->netchan_end_queue = netbuf;
 		client->netchan_end_queue = &(*client->netchan_end_queue)->next;
-	}
-	else
-	{
-#ifdef LEGACY_PROTOCOL
-		if(client->compat)
-			SV_Netchan_Encode(client, msg, client->lastClientCommandString);
-#endif
+		// emit the next fragment of the current message for now
+		Netchan_TransmitNextFragment(&client->netchan);
+	} else {
+		SV_Netchan_Encode( client, msg );
 		Netchan_Transmit( &client->netchan, msg->cursize, msg->data );
 	}
 }
@@ -264,12 +201,7 @@
 	ret = Netchan_Process( &client->netchan, msg );
 	if (!ret)
 		return qfalse;
-
-#ifdef LEGACY_PROTOCOL
-	if(client->compat)
-		SV_Netchan_Decode(client, msg);
-#endif
-
+	SV_Netchan_Decode( client, msg );
 	return qtrue;
 }
 

```

### `openarena-engine`  — sha256 `806fe3da8057...`, 7210 bytes
Also identical in: ioquake3

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_net_chan.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_net_chan.c	2026-04-16 22:48:25.937963500 +0100
@@ -141,13 +141,13 @@
 void SV_Netchan_FreeQueue(client_t *client)
 {
 	netchan_buffer_t *netbuf, *next;
-
+	
 	for(netbuf = client->netchan_start_queue; netbuf; netbuf = next)
 	{
 		next = netbuf->next;
 		Z_Free(netbuf);
 	}
-
+	
 	client->netchan_start_queue = NULL;
 	client->netchan_end_queue = &client->netchan_start_queue;
 }
@@ -236,7 +236,7 @@
 		if(client->compat)
 		{
 			Q_strncpyz(netbuf->clientCommandString, client->lastClientCommandString,
-					   sizeof(netbuf->clientCommandString));
+				   sizeof(netbuf->clientCommandString));
 		}
 #endif
 		netbuf->next = NULL;

```

### `quake3e`  — sha256 `f8d51f3f734c...`, 7076 bytes

_Diff stat: +12 / -22 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_net_chan.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\server\sv_net_chan.c	2026-04-16 20:02:27.369041500 +0100
@@ -24,7 +24,6 @@
 #include "../qcommon/qcommon.h"
 #include "server.h"
 
-#ifdef LEGACY_PROTOCOL
 /*
 ==============
 SV_Netchan_Encode
@@ -129,8 +128,6 @@
 		*(msg->data + i) = *(msg->data + i) ^ key;
 	}
 }
-#endif
-
 
 
 /*
@@ -141,13 +138,13 @@
 void SV_Netchan_FreeQueue(client_t *client)
 {
 	netchan_buffer_t *netbuf, *next;
-
+	
 	for(netbuf = client->netchan_start_queue; netbuf; netbuf = next)
 	{
 		next = netbuf->next;
 		Z_Free(netbuf);
 	}
-
+	
 	client->netchan_start_queue = NULL;
 	client->netchan_end_queue = &client->netchan_start_queue;
 }
@@ -157,17 +154,15 @@
 SV_Netchan_TransmitNextInQueue
 =================
 */
-void SV_Netchan_TransmitNextInQueue(client_t *client)
+static void SV_Netchan_TransmitNextInQueue(client_t *client)
 {
 	netchan_buffer_t *netbuf;
 		
 	Com_DPrintf("#462 Netchan_TransmitNextFragment: popping a queued message for transmit\n");
 	netbuf = client->netchan_start_queue;
 
-#ifdef LEGACY_PROTOCOL
-	if(client->compat)
+	if( client->compat )
 		SV_Netchan_Encode(client, &netbuf->msg, netbuf->clientCommandString);
-#endif
 
 	Netchan_Transmit(&client->netchan, netbuf->msg.cursize, netbuf->msg.data);
 
@@ -232,13 +227,11 @@
 		netbuf = (netchan_buffer_t *) Z_Malloc(sizeof(netchan_buffer_t));
 		// store the msg, we can't store it encoded, as the encoding depends on stuff we still have to finish sending
 		MSG_Copy(&netbuf->msg, netbuf->msgBuffer, sizeof( netbuf->msgBuffer ), msg);
-#ifdef LEGACY_PROTOCOL
-		if(client->compat)
+		if ( client->compat ) 
 		{
 			Q_strncpyz(netbuf->clientCommandString, client->lastClientCommandString,
-					   sizeof(netbuf->clientCommandString));
+				sizeof(netbuf->clientCommandString));
 		}
-#endif
 		netbuf->next = NULL;
 		// insert it in the queue, the message will be encoded and sent later
 		*client->netchan_end_queue = netbuf;
@@ -246,10 +239,8 @@
 	}
 	else
 	{
-#ifdef LEGACY_PROTOCOL
-		if(client->compat)
+		if ( client->compat )
 			SV_Netchan_Encode(client, msg, client->lastClientCommandString);
-#endif
 		Netchan_Transmit( &client->netchan, msg->cursize, msg->data );
 	}
 }
@@ -260,15 +251,14 @@
 =================
 */
 qboolean SV_Netchan_Process( client_t *client, msg_t *msg ) {
-	int ret;
+	qboolean ret;
+	
 	ret = Netchan_Process( &client->netchan, msg );
-	if (!ret)
+	if ( !ret )
 		return qfalse;
 
-#ifdef LEGACY_PROTOCOL
-	if(client->compat)
-		SV_Netchan_Decode(client, msg);
-#endif
+	if ( client->compat )
+		SV_Netchan_Decode( client, msg );
 
 	return qtrue;
 }

```
