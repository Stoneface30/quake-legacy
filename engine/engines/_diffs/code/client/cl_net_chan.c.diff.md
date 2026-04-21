# Diff: `code/client/cl_net_chan.c`
**Canonical:** `wolfcamql-src` (sha256 `d519d2c23fe7...`, 4777 bytes)

## Variants

### `quake3-source`  — sha256 `6a9112526213...`, 4426 bytes

_Diff stat: +12 / -32 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_net_chan.c	2026-04-16 20:02:25.172218400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\cl_net_chan.c	2026-04-16 20:02:19.891591700 +0100
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
 #include "client.h"
 
-#ifdef LEGACY_PROTOCOL
 /*
 ==============
 CL_Netchan_Encode
@@ -107,7 +106,7 @@
         msg->bit = sbit;
         msg->readcount = srdc;
 
-	string = (byte *) clc.reliableCommands[ reliableAcknowledge & (MAX_RELIABLE_COMMANDS-1) ];
+	string = clc.reliableCommands[ reliableAcknowledge & (MAX_RELIABLE_COMMANDS-1) ];
 	index = 0;
 	// xor the client challenge with the netchan sequence number (need something that changes every message)
 	key = clc.challenge ^ LittleLong( *(unsigned *)msg->data );
@@ -126,22 +125,14 @@
 		*(msg->data + i) = *(msg->data + i) ^ key;
 	}
 }
-#endif
 
 /*
 =================
 CL_Netchan_TransmitNextFragment
 =================
 */
-qboolean CL_Netchan_TransmitNextFragment(netchan_t *chan)
-{
-	if(chan->unsentFragments)
-	{
-		Netchan_TransmitNextFragment(chan);
-		return qtrue;
-	}
-
-	return qfalse;
+void CL_Netchan_TransmitNextFragment( netchan_t *chan ) {
+	Netchan_TransmitNextFragment( chan );
 }
 
 /*
@@ -152,20 +143,13 @@
 void CL_Netchan_Transmit( netchan_t *chan, msg_t* msg ) {
 	MSG_WriteByte( msg, clc_EOF );
 
-#ifdef LEGACY_PROTOCOL
-	if(chan->compat)
-		CL_Netchan_Encode(msg);
-#endif
-
-	Netchan_Transmit(chan, msg->cursize, msg->data);
-
-	// Transmit all fragments without delay
-	while(CL_Netchan_TransmitNextFragment(chan))
-	{
-		Com_DPrintf("WARNING: #462 unsent fragments (not supposed to happen!)\n");
-	}
+	CL_Netchan_Encode( msg );
+	Netchan_Transmit( chan, msg->cursize, msg->data );
 }
 
+extern 	int oldsize;
+int newsize = 0;
+
 /*
 =================
 CL_Netchan_Process
@@ -177,11 +161,7 @@
 	ret = Netchan_Process( chan, msg );
 	if (!ret)
 		return qfalse;
-
-#ifdef LEGACY_PROTOCOL
-	if(chan->compat)
-		CL_Netchan_Decode(msg);
-#endif
-
+	CL_Netchan_Decode( msg );
+	newsize += msg->cursize;
 	return qtrue;
 }

```

### `openarena-engine`  — sha256 `5b82b6b99eec...`, 4779 bytes
Also identical in: ioquake3

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_net_chan.c	2026-04-16 20:02:25.172218400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_net_chan.c	2026-04-16 22:48:25.732379000 +0100
@@ -140,7 +140,7 @@
 		Netchan_TransmitNextFragment(chan);
 		return qtrue;
 	}
-
+	
 	return qfalse;
 }
 
@@ -158,7 +158,7 @@
 #endif
 
 	Netchan_Transmit(chan, msg->cursize, msg->data);
-
+	
 	// Transmit all fragments without delay
 	while(CL_Netchan_TransmitNextFragment(chan))
 	{

```

### `quake3e`  — sha256 `4f096476bb56...`, 5125 bytes

_Diff stat: +70 / -46 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_net_chan.c	2026-04-16 20:02:25.172218400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\cl_net_chan.c	2026-04-16 20:02:26.913504400 +0100
@@ -24,7 +24,6 @@
 #include "../qcommon/qcommon.h"
 #include "client.h"
 
-#ifdef LEGACY_PROTOCOL
 /*
 ==============
 CL_Netchan_Encode
@@ -38,28 +37,29 @@
 */
 static void CL_Netchan_Encode( msg_t *msg ) {
 	int serverId, messageAcknowledge, reliableAcknowledge;
-	int i, index, srdc, sbit, soob;
+	int i, index, srdc, sbit;
 	byte key, *string;
+	qboolean soob;
 
 	if ( msg->cursize <= CL_ENCODE_START ) {
 		return;
 	}
 
-        srdc = msg->readcount;
-        sbit = msg->bit;
-        soob = msg->oob;
-        
-        msg->bit = 0;
-        msg->readcount = 0;
-        msg->oob = 0;
-        
-        serverId = MSG_ReadLong(msg);
+	srdc = msg->readcount;
+	sbit = msg->bit;
+	soob = msg->oob;
+
+	msg->bit = 0;
+	msg->readcount = 0;
+	msg->oob = qfalse;
+
+	serverId = MSG_ReadLong(msg);
 	messageAcknowledge = MSG_ReadLong(msg);
 	reliableAcknowledge = MSG_ReadLong(msg);
 
-        msg->oob = soob;
-        msg->bit = sbit;
-        msg->readcount = srdc;
+	msg->oob = soob;
+	msg->bit = sbit;
+	msg->readcount = srdc;
         
 	string = (byte *)clc.serverCommands[ reliableAcknowledge & (MAX_RELIABLE_COMMANDS-1) ];
 	index = 0;
@@ -81,6 +81,7 @@
 	}
 }
 
+
 /*
 ==============
 CL_Netchan_Decode
@@ -93,19 +94,20 @@
 static void CL_Netchan_Decode( msg_t *msg ) {
 	long reliableAcknowledge, i, index;
 	byte key, *string;
-        int	srdc, sbit, soob;
+	int	srdc, sbit;
+	qboolean soob;
 
-        srdc = msg->readcount;
-        sbit = msg->bit;
-        soob = msg->oob;
-        
-        msg->oob = 0;
-        
-	reliableAcknowledge = MSG_ReadLong(msg);
+	srdc = msg->readcount;
+	sbit = msg->bit;
+	soob = msg->oob;
+
+	msg->oob = qfalse;
 
-        msg->oob = soob;
-        msg->bit = sbit;
-        msg->readcount = srdc;
+	reliableAcknowledge = MSG_ReadLong( msg );
+
+	msg->oob = soob;
+	msg->bit = sbit;
+	msg->readcount = srdc;
 
 	string = (byte *) clc.reliableCommands[ reliableAcknowledge & (MAX_RELIABLE_COMMANDS-1) ];
 	index = 0;
@@ -126,62 +128,84 @@
 		*(msg->data + i) = *(msg->data + i) ^ key;
 	}
 }
-#endif
+
 
 /*
 =================
 CL_Netchan_TransmitNextFragment
 =================
 */
-qboolean CL_Netchan_TransmitNextFragment(netchan_t *chan)
+static qboolean CL_Netchan_TransmitNextFragment( netchan_t *chan )
 {
-	if(chan->unsentFragments)
+	if ( chan->unsentFragments )
 	{
-		Netchan_TransmitNextFragment(chan);
+		Netchan_TransmitNextFragment( chan );
 		return qtrue;
 	}
-
+	
 	return qfalse;
 }
 
+
 /*
 ===============
 CL_Netchan_Transmit
 ================
 */
 void CL_Netchan_Transmit( netchan_t *chan, msg_t* msg ) {
-	MSG_WriteByte( msg, clc_EOF );
 
-#ifdef LEGACY_PROTOCOL
-	if(chan->compat)
-		CL_Netchan_Encode(msg);
-#endif
-
-	Netchan_Transmit(chan, msg->cursize, msg->data);
+	if ( chan->compat )
+		CL_Netchan_Encode( msg );
 
+	Netchan_Transmit( chan, msg->cursize, msg->data );
+	
 	// Transmit all fragments without delay
-	while(CL_Netchan_TransmitNextFragment(chan))
-	{
-		Com_DPrintf("WARNING: #462 unsent fragments (not supposed to happen!)\n");
+	while ( CL_Netchan_TransmitNextFragment( chan ) ) {
+		// might happen if server die silently but client continue adding/sending commands
+		Com_DPrintf( S_COLOR_YELLOW "%s: unsent fragments\n", __func__ );
 	}
 }
 
+
+/*
+===============
+CL_Netchan_Enqueue
+================
+*/
+void CL_Netchan_Enqueue( netchan_t *chan, msg_t* msg, int times ) {
+	int i;
+
+	// make sure we send all pending fragments to get correct chan->outgoingSequence
+	while ( CL_Netchan_TransmitNextFragment( chan ) ) {
+		;
+	}
+
+	if ( chan->compat ) {
+		CL_Netchan_Encode( msg );
+	}
+
+	for ( i = 0; i < times; i++ ) {
+		Netchan_Enqueue( chan, msg->cursize, msg->data );
+	}
+
+	chan->outgoingSequence++;
+}
+
+
 /*
 =================
 CL_Netchan_Process
 =================
 */
 qboolean CL_Netchan_Process( netchan_t *chan, msg_t *msg ) {
-	int ret;
+	qboolean ret;
 
 	ret = Netchan_Process( chan, msg );
-	if (!ret)
+	if ( !ret )
 		return qfalse;
 
-#ifdef LEGACY_PROTOCOL
-	if(chan->compat)
-		CL_Netchan_Decode(msg);
-#endif
+	if ( chan->compat )
+		CL_Netchan_Decode( msg );
 
 	return qtrue;
 }

```
