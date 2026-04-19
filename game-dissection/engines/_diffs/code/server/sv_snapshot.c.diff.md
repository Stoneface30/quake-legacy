# Diff: `code/server/sv_snapshot.c`
**Canonical:** `wolfcamql-src` (sha256 `2a29251f5735...`, 19524 bytes)

## Variants

### `quake3-source`  — sha256 `35c13dc46913...`, 19486 bytes

_Diff stat: +91 / -94 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_snapshot.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\server\sv_snapshot.c	2026-04-16 20:02:19.979632700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -87,7 +87,7 @@
 		if ( newnum == oldnum ) {
 			// delta update from old position
 			// because the force parm is qfalse, this will not result
-			// in any bytes being emitted if the entity has not changed at all
+			// in any bytes being emited if the entity has not changed at all
 			MSG_WriteDeltaEntity (msg, oldent, newent, qfalse );
 			oldindex++;
 			newindex++;
@@ -160,17 +160,7 @@
 
 	// send over the current server time so the client can drift
 	// its view of time to try to match
-	if( client->oldServerTime ) {
-		// The server has not yet got an acknowledgement of the
-		// new gamestate from this client, so continue to send it
-		// a time as if the server has not restarted. Note from
-		// the client's perspective this time is strictly speaking
-		// incorrect, but since it'll be busy loading a map at
-		// the time it doesn't really matter.
-		MSG_WriteLong (msg, sv.time + client->oldServerTime);
-	} else {
-		MSG_WriteLong (msg, sv.time);
-	}
+	MSG_WriteLong (msg, svs.time);
 
 	// what we are delta'ing from
 	MSG_WriteByte (msg, lastframe);
@@ -235,6 +225,7 @@
 =============================================================================
 */
 
+#define	MAX_SNAPSHOT_ENTITIES	1024
 typedef struct {
 	int		numSnapshotEntities;
 	int		snapshotEntities[MAX_SNAPSHOT_ENTITIES];	
@@ -297,6 +288,7 @@
 	int		l;
 	int		clientarea, clientcluster;
 	int		leafnum;
+	int		c_fullsend;
 	byte	*clientpvs;
 	byte	*bitvector;
 
@@ -316,6 +308,8 @@
 
 	clientpvs = CM_ClusterPVS (clientcluster);
 
+	c_fullsend = 0;
+
 	for ( e = 0 ; e < sv.num_entities ; e++ ) {
 		ent = SV_GentityNum(e);
 
@@ -349,7 +343,7 @@
 		// entities can be flagged to be sent to a given mask of clients
 		if ( ent->r.svFlags & SVF_CLIENTMASK ) {
 			if (frame->ps.clientNum >= 32)
-				Com_Error( ERR_DROP, "SVF_CLIENTMASK: clientNum >= 32" );
+				Com_Error( ERR_DROP, "SVF_CLIENTMASK: cientNum > 32\n" );
 			if (~ent->r.singleClient & (1 << frame->ps.clientNum))
 				continue;
 		}
@@ -362,7 +356,7 @@
 		}
 
 		// broadcast entities are always sent
-		if ( sv_broadcastAll->integer  ||  ent->r.svFlags & SVF_BROADCAST ) {
+		if ( ent->r.svFlags & SVF_BROADCAST ) {
 			SV_AddEntToSnapshot( svEnt, ent, eNums );
 			continue;
 		}
@@ -411,7 +405,7 @@
 		// add it
 		SV_AddEntToSnapshot( svEnt, ent, eNums );
 
-		// if it's a portal entity, add everything visible from its camera position
+		// if its a portal entity, add everything visible from its camera position
 		if ( ent->r.svFlags & SVF_PORTAL ) {
 			if ( ent->s.generic1 ) {
 				vec3_t dir;
@@ -520,52 +514,37 @@
 	}
 }
 
-#ifdef USE_VOIP
+
 /*
-==================
-SV_WriteVoipToClient
+====================
+SV_RateMsec
 
-Check to see if there is any VoIP queued for a client, and send if there is.
-==================
+Return the number of msec a given size message is supposed
+to take to clear, based on the current rate
+====================
 */
-static void SV_WriteVoipToClient(client_t *cl, msg_t *msg)
-{
-	int totalbytes = 0;
-	int i;
-	voipServerPacket_t *packet;
-
-	if(cl->queuedVoipPackets)
-	{
-		// Write as many VoIP packets as we reasonably can...
-		for(i = 0; i < cl->queuedVoipPackets; i++)
-		{
-			packet = cl->voipPacket[(i + cl->queuedVoipIndex) % ARRAY_LEN(cl->voipPacket)];
-
-			if(!*cl->downloadName)
-			{
-        			totalbytes += packet->len;
-	        		if (totalbytes > (msg->maxsize - msg->cursize) / 2)
-		        		break;
-
-        			MSG_WriteByte(msg, svc_voip);
-        			MSG_WriteShort(msg, packet->sender);
-	        		MSG_WriteByte(msg, (byte) packet->generation);
-		        	MSG_WriteLong(msg, packet->sequence);
-		        	MSG_WriteByte(msg, packet->frames);
-        			MSG_WriteShort(msg, packet->len);
-        			MSG_WriteBits(msg, packet->flags, VOIP_FLAGCNT);
-	        		MSG_WriteData(msg, packet->data, packet->len);
-                        }
-
-			Z_Free(packet);
-		}
-
-		cl->queuedVoipPackets -= i;
-		cl->queuedVoipIndex += i;
-		cl->queuedVoipIndex %= ARRAY_LEN(cl->voipPacket);
+#define	HEADER_RATE_BYTES	48		// include our header, IP header, and some overhead
+static int SV_RateMsec( client_t *client, int messageSize ) {
+	int		rate;
+	int		rateMsec;
+
+	// individual messages will never be larger than fragment size
+	if ( messageSize > 1500 ) {
+		messageSize = 1500;
 	}
+	rate = client->rate;
+	if ( sv_maxRate->integer ) {
+		if ( sv_maxRate->integer < 1000 ) {
+			Cvar_Set( "sv_MaxRate", "1000" );
+		}
+		if ( sv_maxRate->integer < rate ) {
+			rate = sv_maxRate->integer;
+		}
+	}
+	rateMsec = ( messageSize + HEADER_RATE_BYTES ) * 1000 / rate;
+
+	return rateMsec;
 }
-#endif
 
 /*
 =======================
@@ -574,15 +553,49 @@
 Called by SV_SendClientSnapshot and SV_SendClientGameState
 =======================
 */
-void SV_SendMessageToClient(msg_t *msg, client_t *client)
-{
+void SV_SendMessageToClient( msg_t *msg, client_t *client ) {
+	int			rateMsec;
+
 	// record information about the message
 	client->frames[client->netchan.outgoingSequence & PACKET_MASK].messageSize = msg->cursize;
 	client->frames[client->netchan.outgoingSequence & PACKET_MASK].messageSent = svs.time;
 	client->frames[client->netchan.outgoingSequence & PACKET_MASK].messageAcked = -1;
 
 	// send the datagram
-	SV_Netchan_Transmit(client, msg);
+	SV_Netchan_Transmit( client, msg );	//msg->cursize, msg->data );
+
+	// set nextSnapshotTime based on rate and requested number of updates
+
+	// local clients get snapshots every frame
+	// TTimo - https://zerowing.idsoftware.com/bugzilla/show_bug.cgi?id=491
+	// added sv_lanForceRate check
+	if ( client->netchan.remoteAddress.type == NA_LOOPBACK || (sv_lanForceRate->integer && Sys_IsLANAddress (client->netchan.remoteAddress)) ) {
+		client->nextSnapshotTime = svs.time - 1;
+		return;
+	}
+	
+	// normal rate / snapshotMsec calculation
+	rateMsec = SV_RateMsec( client, msg->cursize );
+
+	if ( rateMsec < client->snapshotMsec ) {
+		// never send more packets than this, no matter what the rate is at
+		rateMsec = client->snapshotMsec;
+		client->rateDelayed = qfalse;
+	} else {
+		client->rateDelayed = qtrue;
+	}
+
+	client->nextSnapshotTime = svs.time + rateMsec;
+
+	// don't pile up empty snapshots while connecting
+	if ( client->state != CS_ACTIVE ) {
+		// a gigantic connection message may have already put the nextSnapshotTime
+		// more than a second away, so don't shorten it
+		// do shorten if client is downloading
+		if ( !*client->downloadName && client->nextSnapshotTime < svs.time + 1000 ) {
+			client->nextSnapshotTime = svs.time + 1000;
+		}
+	}
 }
 
 
@@ -621,9 +634,8 @@
 	// and the playerState_t
 	SV_WriteSnapshotToClient( client, &msg );
 
-#ifdef USE_VOIP
-	SV_WriteVoipToClient( client, &msg );
-#endif
+	// Add any download data if the client is downloading
+	SV_WriteDownloadToClient( client, &msg );
 
 	// check for overflow
 	if ( msg.overflowed ) {
@@ -640,46 +652,31 @@
 SV_SendClientMessages
 =======================
 */
-void SV_SendClientMessages(void)
-{
+void SV_SendClientMessages( void ) {
 	int			i;
 	client_t	*c;
 
 	// send a message to each connected client
-	for(i=0; i < sv_maxclients->integer; i++)
-	{
-		c = &svs.clients[i];
-
-		if(!c->state)
+	for (i=0, c = svs.clients ; i < sv_maxclients->integer ; i++, c++) {
+		if (!c->state) {
 			continue;		// not connected
+		}
 
-		if(svs.time - c->lastSnapshotTime < c->snapshotMsec * com_timescale->value)
-			continue;               // It's not time yet
-
-		if(*c->downloadName)
-			continue;		// Client is downloading, don't send snapshots
+		if ( svs.time < c->nextSnapshotTime ) {
+			continue;		// not time yet
+		}
 
-		if(c->netchan.unsentFragments || c->netchan_start_queue)
-		{
-			c->rateDelayed = qtrue;
-			continue;				// Drop this snapshot if the packet queue is still full or delta compression will break
-		}
-
-		if(!(c->netchan.remoteAddress.type == NA_LOOPBACK ||
-			 (sv_lanForceRate->integer && Sys_IsLANAddress(c->netchan.remoteAddress))))
-		{
-			// rate control for clients not on LAN
-			if(SV_RateMsec(c) > 0)
-			{
-				// Not enough time since last packet passed through the line
-				c->rateDelayed = qtrue;
-				continue;
-			}
+		// send additional message fragments if the last message
+		// was too large to send at once
+		if ( c->netchan.unsentFragments ) {
+			c->nextSnapshotTime = svs.time + 
+				SV_RateMsec( c, c->netchan.unsentLength - c->netchan.unsentFragmentStart );
+			SV_Netchan_TransmitNextFragment( c );
+			continue;
 		}
 
 		// generate and send a new message
-		SV_SendClientSnapshot(c);
-		c->lastSnapshotTime = svs.time;
-		c->rateDelayed = qfalse;
+		SV_SendClientSnapshot( c );
 	}
 }
+

```

### `ioquake3`  — sha256 `77a702cacc8b...`, 19488 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_snapshot.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\server\sv_snapshot.c	2026-04-16 20:02:21.620759400 +0100
@@ -362,7 +362,7 @@
 		}
 
 		// broadcast entities are always sent
-		if ( sv_broadcastAll->integer  ||  ent->r.svFlags & SVF_BROADCAST ) {
+		if ( ent->r.svFlags & SVF_BROADCAST ) {
 			SV_AddEntToSnapshot( svEnt, ent, eNums );
 			continue;
 		}
@@ -547,7 +547,7 @@
 	        		if (totalbytes > (msg->maxsize - msg->cursize) / 2)
 		        		break;
 
-        			MSG_WriteByte(msg, svc_voip);
+        			MSG_WriteByte(msg, svc_voipOpus);
         			MSG_WriteShort(msg, packet->sender);
 	        		MSG_WriteByte(msg, (byte) packet->generation);
 		        	MSG_WriteLong(msg, packet->sequence);
@@ -642,19 +642,19 @@
 */
 void SV_SendClientMessages(void)
 {
-	int			i;
+	int		i;
 	client_t	*c;
 
 	// send a message to each connected client
 	for(i=0; i < sv_maxclients->integer; i++)
 	{
 		c = &svs.clients[i];
-
+		
 		if(!c->state)
 			continue;		// not connected
 
 		if(svs.time - c->lastSnapshotTime < c->snapshotMsec * com_timescale->value)
-			continue;               // It's not time yet
+			continue;		// It's not time yet
 
 		if(*c->downloadName)
 			continue;		// Client is downloading, don't send snapshots
@@ -662,13 +662,13 @@
 		if(c->netchan.unsentFragments || c->netchan_start_queue)
 		{
 			c->rateDelayed = qtrue;
-			continue;				// Drop this snapshot if the packet queue is still full or delta compression will break
+			continue;		// Drop this snapshot if the packet queue is still full or delta compression will break
 		}
 
 		if(!(c->netchan.remoteAddress.type == NA_LOOPBACK ||
-			 (sv_lanForceRate->integer && Sys_IsLANAddress(c->netchan.remoteAddress))))
+		     (sv_lanForceRate->integer && Sys_IsLANAddress(c->netchan.remoteAddress))))
 		{
-			// rate control for clients not on LAN
+			// rate control for clients not on LAN 
 			if(SV_RateMsec(c) > 0)
 			{
 				// Not enough time since last packet passed through the line

```

### `quake3e`  — sha256 `847df160fa78...`, 22172 bytes

_Diff stat: +304 / -190 lines_

_(full diff is 23957 bytes — see files directly)_

### `openarena-engine`  — sha256 `f61ff2e3a069...`, 19490 bytes

_Diff stat: +11 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\server\sv_snapshot.c	2026-04-16 20:02:25.270780900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\server\sv_snapshot.c	2026-04-16 22:48:25.937963500 +0100
@@ -87,7 +87,7 @@
 		if ( newnum == oldnum ) {
 			// delta update from old position
 			// because the force parm is qfalse, this will not result
-			// in any bytes being emitted if the entity has not changed at all
+			// in any bytes being emited if the entity has not changed at all
 			MSG_WriteDeltaEntity (msg, oldent, newent, qfalse );
 			oldindex++;
 			newindex++;
@@ -362,7 +362,7 @@
 		}
 
 		// broadcast entities are always sent
-		if ( sv_broadcastAll->integer  ||  ent->r.svFlags & SVF_BROADCAST ) {
+		if ( ent->r.svFlags & SVF_BROADCAST ) {
 			SV_AddEntToSnapshot( svEnt, ent, eNums );
 			continue;
 		}
@@ -642,33 +642,34 @@
 */
 void SV_SendClientMessages(void)
 {
-	int			i;
+	int		i;
 	client_t	*c;
 
 	// send a message to each connected client
 	for(i=0; i < sv_maxclients->integer; i++)
 	{
 		c = &svs.clients[i];
-
+		
 		if(!c->state)
 			continue;		// not connected
 
-		if(svs.time - c->lastSnapshotTime < c->snapshotMsec * com_timescale->value)
-			continue;               // It's not time yet
-
 		if(*c->downloadName)
 			continue;		// Client is downloading, don't send snapshots
 
 		if(c->netchan.unsentFragments || c->netchan_start_queue)
 		{
 			c->rateDelayed = qtrue;
-			continue;				// Drop this snapshot if the packet queue is still full or delta compression will break
+			continue;		// Drop this snapshot if the packet queue is still full or delta compression will break
 		}
 
 		if(!(c->netchan.remoteAddress.type == NA_LOOPBACK ||
-			 (sv_lanForceRate->integer && Sys_IsLANAddress(c->netchan.remoteAddress))))
+		     (sv_lanForceRate->integer && Sys_IsLANAddress(c->netchan.remoteAddress))))
 		{
-			// rate control for clients not on LAN
+			// rate control for clients not on LAN 
+			
+			if(svs.time - c->lastSnapshotTime < c->snapshotMsec * com_timescale->value)
+				continue;		// It's not time yet
+
 			if(SV_RateMsec(c) > 0)
 			{
 				// Not enough time since last packet passed through the line

```
