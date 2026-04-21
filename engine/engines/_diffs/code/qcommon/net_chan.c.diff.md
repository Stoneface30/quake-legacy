# Diff: `code/qcommon/net_chan.c`
**Canonical:** `wolfcamql-src` (sha256 `bc3d3257da60...`, 19517 bytes)

## Variants

### `quake3-source`  — sha256 `7581447ec16a...`, 18550 bytes

_Diff stat: +132 / -166 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\net_chan.c	2026-04-16 20:02:25.224226800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\net_chan.c	2026-04-16 20:02:19.961607100 +0100
@@ -15,12 +15,12 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
-#include "q_shared.h"
+#include "../game/q_shared.h"
 #include "qcommon.h"
 
 /*
@@ -52,11 +52,11 @@
 #define	FRAGMENT_SIZE			(MAX_PACKETLEN - 100)
 #define	PACKET_HEADER			10			// two ints and a short
 
-#define	FRAGMENT_BIT	(1U<<31)
+#define	FRAGMENT_BIT	(1<<31)
 
 cvar_t		*showpackets;
 cvar_t		*showdrop;
-cvar_t		*net_qport;
+cvar_t		*qport;
 
 static char *netsrcString[2] = {
 	"client",
@@ -73,7 +73,7 @@
 	port &= 0xffff;
 	showpackets = Cvar_Get ("showpackets", "0", CVAR_TEMP );
 	showdrop = Cvar_Get ("showdrop", "0", CVAR_TEMP );
-	net_qport = Cvar_Get ("net_qport", va("%i", port), CVAR_INIT );
+	qport = Cvar_Get ("net_qport", va("%i", port), CVAR_INIT );
 }
 
 /*
@@ -83,8 +83,7 @@
 called to open a channel to a remote system
 ==============
 */
-void Netchan_Setup(netsrc_t sock, netchan_t *chan, netadr_t adr, int qport, int challenge, qboolean compat)
-{
+void Netchan_Setup( netsrc_t sock, netchan_t *chan, netadr_t adr, int qport ) {
 	Com_Memset (chan, 0, sizeof(*chan));
 	
 	chan->sock = sock;
@@ -92,11 +91,6 @@
 	chan->qport = qport;
 	chan->incomingSequence = 0;
 	chan->outgoingSequence = 1;
-	chan->challenge = challenge;
-
-#ifdef LEGACY_PROTOCOL
-	chan->compat = compat;
-#endif
 }
 
 // TTimo: unused, commenting out to make gcc happy
@@ -196,24 +190,17 @@
 	msg_t		send;
 	byte		send_buf[MAX_PACKETLEN];
 	int			fragmentLength;
-	int			outgoingSequence;
 
 	// write the packet header
 	MSG_InitOOB (&send, send_buf, sizeof(send_buf));				// <-- only do the oob here
 
-	outgoingSequence = chan->outgoingSequence | FRAGMENT_BIT;
-	MSG_WriteLong(&send, outgoingSequence);
+	MSG_WriteLong( &send, chan->outgoingSequence | FRAGMENT_BIT );
 
 	// send the qport if we are a client
 	if ( chan->sock == NS_CLIENT ) {
-		MSG_WriteShort( &send, net_qport->integer );
+		MSG_WriteShort( &send, qport->integer );
 	}
 
-#ifdef LEGACY_PROTOCOL
-	if(!chan->compat)
-#endif
-		MSG_WriteLong(&send, NETCHAN_GENCHECKSUM(chan->challenge, chan->outgoingSequence));
-
 	// copy the reliable message to the packet first
 	fragmentLength = FRAGMENT_SIZE;
 	if ( chan->unsentFragmentStart  + fragmentLength > chan->unsentLength ) {
@@ -225,11 +212,7 @@
 	MSG_WriteData( &send, chan->unsentBuffer + chan->unsentFragmentStart, fragmentLength );
 
 	// send the datagram
-	NET_SendPacket(chan->sock, send.cursize, send.data, chan->remoteAddress);
-
-	// Store send time and size of this packet for rate control
-	chan->lastSentTime = Sys_Milliseconds();
-	chan->lastSentSize = send.cursize;
+	NET_SendPacket( chan->sock, send.cursize, send.data, chan->remoteAddress );
 
 	if ( showpackets->integer ) {
 		Com_Printf ("%s send %4i : s=%i fragment=%i,%i\n"
@@ -285,27 +268,18 @@
 	MSG_InitOOB (&send, send_buf, sizeof(send_buf));
 
 	MSG_WriteLong( &send, chan->outgoingSequence );
+	chan->outgoingSequence++;
 
 	// send the qport if we are a client
-	if(chan->sock == NS_CLIENT)
-		MSG_WriteShort(&send, net_qport->integer);
-
-#ifdef LEGACY_PROTOCOL
-	if(!chan->compat)
-#endif
-		MSG_WriteLong(&send, NETCHAN_GENCHECKSUM(chan->challenge, chan->outgoingSequence));
-
-	chan->outgoingSequence++;
+	if ( chan->sock == NS_CLIENT ) {
+		MSG_WriteShort( &send, qport->integer );
+	}
 
 	MSG_WriteData( &send, data, length );
 
 	// send the datagram
 	NET_SendPacket( chan->sock, send.cursize, send.data, chan->remoteAddress );
 
-	// Store send time and size of this packet for rate control
-	chan->lastSentTime = Sys_Milliseconds();
-	chan->lastSentSize = send.cursize;
-
 	if ( showpackets->integer ) {
 		Com_Printf( "%s send %4i : s=%i ack=%i\n"
 			, netsrcString[ chan->sock ]
@@ -329,6 +303,7 @@
 */
 qboolean Netchan_Process( netchan_t *chan, msg_t *msg ) {
 	int			sequence;
+	int			qport;
 	int			fragmentStart, fragmentLength;
 	qboolean	fragmented;
 
@@ -349,18 +324,7 @@
 
 	// read the qport if we are a server
 	if ( chan->sock == NS_SERVER ) {
-		MSG_ReadShort( msg );
-	}
-
-#ifdef LEGACY_PROTOCOL
-	if(!chan->compat)
-#endif
-	{
-		int checksum = MSG_ReadLong(msg);
-
-		// UDP spoofing protection
-		if(NETCHAN_GENCHECKSUM(chan->challenge, sequence) != checksum)
-			return qfalse;
+		qport = MSG_ReadShort( msg );
 	}
 
 	// read the fragment information
@@ -433,7 +397,8 @@
 		if ( fragmentStart != chan->fragmentLength ) {
 			if ( showdrop->integer || showpackets->integer ) {
 				Com_Printf( "%s:Dropped a message fragment\n"
-				, NET_AdrToString( chan->remoteAddress ));
+				, NET_AdrToString( chan->remoteAddress )
+				, sequence);
 			}
 			// we can still keep the part that we have so far,
 			// so we don't need to clear chan->fragmentLength
@@ -496,6 +461,93 @@
 
 //==============================================================================
 
+/*
+===================
+NET_CompareBaseAdr
+
+Compares without the port
+===================
+*/
+qboolean	NET_CompareBaseAdr (netadr_t a, netadr_t b)
+{
+	if (a.type != b.type)
+		return qfalse;
+
+	if (a.type == NA_LOOPBACK)
+		return qtrue;
+
+	if (a.type == NA_IP)
+	{
+		if (a.ip[0] == b.ip[0] && a.ip[1] == b.ip[1] && a.ip[2] == b.ip[2] && a.ip[3] == b.ip[3])
+			return qtrue;
+		return qfalse;
+	}
+
+	if (a.type == NA_IPX)
+	{
+		if ((memcmp(a.ipx, b.ipx, 10) == 0))
+			return qtrue;
+		return qfalse;
+	}
+
+
+	Com_Printf ("NET_CompareBaseAdr: bad address type\n");
+	return qfalse;
+}
+
+const char	*NET_AdrToString (netadr_t a)
+{
+	static	char	s[64];
+
+	if (a.type == NA_LOOPBACK) {
+		Com_sprintf (s, sizeof(s), "loopback");
+	} else if (a.type == NA_BOT) {
+		Com_sprintf (s, sizeof(s), "bot");
+	} else if (a.type == NA_IP) {
+		Com_sprintf (s, sizeof(s), "%i.%i.%i.%i:%hu",
+			a.ip[0], a.ip[1], a.ip[2], a.ip[3], BigShort(a.port));
+	} else {
+		Com_sprintf (s, sizeof(s), "%02x%02x%02x%02x.%02x%02x%02x%02x%02x%02x:%hu",
+		a.ipx[0], a.ipx[1], a.ipx[2], a.ipx[3], a.ipx[4], a.ipx[5], a.ipx[6], a.ipx[7], a.ipx[8], a.ipx[9], 
+		BigShort(a.port));
+	}
+
+	return s;
+}
+
+
+qboolean	NET_CompareAdr (netadr_t a, netadr_t b)
+{
+	if (a.type != b.type)
+		return qfalse;
+
+	if (a.type == NA_LOOPBACK)
+		return qtrue;
+
+	if (a.type == NA_IP)
+	{
+		if (a.ip[0] == b.ip[0] && a.ip[1] == b.ip[1] && a.ip[2] == b.ip[2] && a.ip[3] == b.ip[3] && a.port == b.port)
+			return qtrue;
+		return qfalse;
+	}
+
+	if (a.type == NA_IPX)
+	{
+		if ((memcmp(a.ipx, b.ipx, 10) == 0) && a.port == b.port)
+			return qtrue;
+		return qfalse;
+	}
+
+	Com_Printf ("NET_CompareAdr: bad address type\n");
+	return qfalse;
+}
+
+
+qboolean	NET_IsLocalAddress( netadr_t adr ) {
+	return adr.type == NA_LOOPBACK;
+}
+
+
 
 /*
 =============================================================================
@@ -563,62 +615,6 @@
 
 //=============================================================================
 
-typedef struct packetQueue_s {
-        struct packetQueue_s *next;
-        int length;
-        byte *data;
-        netadr_t to;
-        int release;
-} packetQueue_t;
-
-packetQueue_t *packetQueue = NULL;
-
-static void NET_QueuePacket( int length, const void *data, netadr_t to,
-	int offset )
-{
-	packetQueue_t *new, *next = packetQueue;
-
-	if(offset > 999)
-		offset = 999;
-
-	new = S_Malloc(sizeof(packetQueue_t));
-	new->data = S_Malloc(length);
-	Com_Memcpy(new->data, data, length);
-	new->length = length;
-	new->to = to;
-	new->release = Sys_Milliseconds() + (int)((float)offset / com_timescale->value);	
-	new->next = NULL;
-
-	if(!packetQueue) {
-		packetQueue = new;
-		return;
-	}
-	while(next) {
-		if(!next->next) {
-			next->next = new;
-			return;
-		}
-		next = next->next;
-	}
-}
-
-void NET_FlushPacketQueue(void)
-{
-	packetQueue_t *last;
-	int now;
-
-	while(packetQueue) {
-		now = Sys_Milliseconds();
-		if(packetQueue->release >= now)
-			break;
-		Sys_SendPacket(packetQueue->length, packetQueue->data,
-			packetQueue->to);
-		last = packetQueue;
-		packetQueue = packetQueue->next;
-		Z_Free(last->data);
-		Z_Free(last);
-	}
-}
 
 void NET_SendPacket( netsrc_t sock, int length, const void *data, netadr_t to ) {
 
@@ -638,15 +634,7 @@
 		return;
 	}
 
-	if ( sock == NS_CLIENT && cl_packetdelay->integer > 0 ) {
-		NET_QueuePacket( length, data, to, cl_packetdelay->integer );
-	}
-	else if ( sock == NS_SERVER && sv_packetdelay->integer > 0 ) {
-		NET_QueuePacket( length, data, to, sv_packetdelay->integer );
-	}
-	else {
-		Sys_SendPacket( length, data, to );
-	}
+	Sys_SendPacket( length, data, to );
 }
 
 /*
@@ -668,7 +656,7 @@
 	string[3] = -1;
 
 	va_start( argptr, format );
-	Q_vsnprintf( string+4, sizeof(string)-4, format, argptr );
+	vsprintf( string+4, format, argptr );
 	va_end( argptr );
 
 	// send the datagram
@@ -709,68 +697,46 @@
 NET_StringToAdr
 
 Traps "localhost" for loopback, passes everything else to system
-return 0 on address not found, 1 on address found with port, 2 on address found without port.
 =============
 */
-int NET_StringToAdr( const char *s, netadr_t *a, netadrtype_t family )
-{
-	char	base[MAX_STRING_CHARS], *search;
-	char	*port = NULL;
+qboolean	NET_StringToAdr( const char *s, netadr_t *a ) {
+	qboolean	r;
+	char	base[MAX_STRING_CHARS];
+	char	*port;
 
 	if (!strcmp (s, "localhost")) {
 		Com_Memset (a, 0, sizeof(*a));
 		a->type = NA_LOOPBACK;
-// as NA_LOOPBACK doesn't require ports report port was given.
-		return 1;
+		return qtrue;
 	}
 
+	// look for a port number
 	Q_strncpyz( base, s, sizeof( base ) );
-	
-	if(*base == '[' || Q_CountChar(base, ':') > 1)
-	{
-		// This is an ipv6 address, handle it specially.
-		search = strchr(base, ']');
-		if(search)
-		{
-			*search = '\0';
-			search++;
-
-			if(*search == ':')
-				port = search + 1;
-		}
-		
-		if(*base == '[')
-			search = base + 1;
-		else
-			search = base;
-	}
-	else
-	{
-		// look for a port number
-		port = strchr( base, ':' );
-		
-		if ( port ) {
-			*port = '\0';
-			port++;
-		}
-		
-		search = base;
+	port = strstr( base, ":" );
+	if ( port ) {
+		*port = 0;
+		port++;
 	}
 
-	if(!Sys_StringToAdr(search, a, family))
-	{
+	r = Sys_StringToAdr( base, a );
+
+	if ( !r ) {
 		a->type = NA_BAD;
-		return 0;
+		return qfalse;
 	}
 
-	if(port)
-	{
-		a->port = BigShort((short) atoi(port));
-		return 1;
+	// inet_addr returns this if out of range
+	if ( a->ip[0] == 255 && a->ip[1] == 255 && a->ip[2] == 255 && a->ip[3] == 255 ) {
+		a->type = NA_BAD;
+		return qfalse;
 	}
-	else
-	{
-		a->port = BigShort(PORT_SERVER);
-		return 2;
+
+	if ( port ) {
+		a->port = BigShort( (short)atoi( port ) );
+	} else {
+		a->port = BigShort( PORT_SERVER );
 	}
+
+	return qtrue;
 }
+

```

### `ioquake3`  — sha256 `faa39c57d5ef...`, 17478 bytes

_Diff stat: +1 / -87 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\net_chan.c	2026-04-16 20:02:25.224226800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\net_chan.c	2026-04-16 20:02:21.569107300 +0100
@@ -99,92 +99,6 @@
 #endif
 }
 
-// TTimo: unused, commenting out to make gcc happy
-#if 0
-/*
-==============
-Netchan_ScramblePacket
-
-A probably futile attempt to make proxy hacking somewhat
-more difficult.
-==============
-*/
-#define	SCRAMBLE_START	6
-static void Netchan_ScramblePacket( msg_t *buf ) {
-	unsigned	seed;
-	int			i, j, c, mask, temp;
-	int			seq[MAX_PACKETLEN];
-
-	seed = ( LittleLong( *(unsigned *)buf->data ) * 3 ) ^ ( buf->cursize * 123 );
-	c = buf->cursize;
-	if ( c <= SCRAMBLE_START ) {
-		return;
-	}
-	if ( c > MAX_PACKETLEN ) {
-		Com_Error( ERR_DROP, "MAX_PACKETLEN" );
-	}
-
-	// generate a sequence of "random" numbers
-	for (i = 0 ; i < c ; i++) {
-		seed = (119 * seed + 1);
-		seq[i] = seed;
-	}
-
-	// transpose each character
-	for ( mask = 1 ; mask < c-SCRAMBLE_START ; mask = ( mask << 1 ) + 1 ) {
-	}
-	mask >>= 1;
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		j = SCRAMBLE_START + ( seq[i] & mask );
-		temp = buf->data[j];
-		buf->data[j] = buf->data[i];
-		buf->data[i] = temp;
-	}
-
-	// byte xor the data after the header
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		buf->data[i] ^= seq[i];
-	}
-}
-
-static void Netchan_UnScramblePacket( msg_t *buf ) {
-	unsigned	seed;
-	int			i, j, c, mask, temp;
-	int			seq[MAX_PACKETLEN];
-
-	seed = ( LittleLong( *(unsigned *)buf->data ) * 3 ) ^ ( buf->cursize * 123 );
-	c = buf->cursize;
-	if ( c <= SCRAMBLE_START ) {
-		return;
-	}
-	if ( c > MAX_PACKETLEN ) {
-		Com_Error( ERR_DROP, "MAX_PACKETLEN" );
-	}
-
-	// generate a sequence of "random" numbers
-	for (i = 0 ; i < c ; i++) {
-		seed = (119 * seed + 1);
-		seq[i] = seed;
-	}
-
-	// byte xor the data after the header
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		buf->data[i] ^= seq[i];
-	}
-
-	// transpose each character in reverse order
-	for ( mask = 1 ; mask < c-SCRAMBLE_START ; mask = ( mask << 1 ) + 1 ) {
-	}
-	mask >>= 1;
-	for (i = c-1 ; i >= SCRAMBLE_START ; i--) {
-		j = SCRAMBLE_START + ( seq[i] & mask );
-		temp = buf->data[j];
-		buf->data[j] = buf->data[i];
-		buf->data[i] = temp;
-	}
-}
-#endif
-
 /*
 =================
 Netchan_TransmitNextFragment
@@ -226,7 +140,7 @@
 
 	// send the datagram
 	NET_SendPacket(chan->sock, send.cursize, send.data, chan->remoteAddress);
-
+	
 	// Store send time and size of this packet for rate control
 	chan->lastSentTime = Sys_Milliseconds();
 	chan->lastSentSize = send.cursize;

```

### `quake3e`  — sha256 `aa9ff07e9b3b...`, 21755 bytes

_Diff stat: +269 / -204 lines_

_(full diff is 20869 bytes — see files directly)_

### `openarena-engine`  — sha256 `abdfb6faf297...`, 17461 bytes

_Diff stat: +6 / -92 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\net_chan.c	2026-04-16 20:02:25.224226800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\net_chan.c	2026-04-16 22:48:25.910297500 +0100
@@ -52,11 +52,11 @@
 #define	FRAGMENT_SIZE			(MAX_PACKETLEN - 100)
 #define	PACKET_HEADER			10			// two ints and a short
 
-#define	FRAGMENT_BIT	(1U<<31)
+#define	FRAGMENT_BIT	(1<<31)
 
 cvar_t		*showpackets;
 cvar_t		*showdrop;
-cvar_t		*net_qport;
+cvar_t		*qport;
 
 static char *netsrcString[2] = {
 	"client",
@@ -73,7 +73,7 @@
 	port &= 0xffff;
 	showpackets = Cvar_Get ("showpackets", "0", CVAR_TEMP );
 	showdrop = Cvar_Get ("showdrop", "0", CVAR_TEMP );
-	net_qport = Cvar_Get ("net_qport", va("%i", port), CVAR_INIT );
+	qport = Cvar_Get ("net_qport", va("%i", port), CVAR_INIT );
 }
 
 /*
@@ -99,92 +99,6 @@
 #endif
 }
 
-// TTimo: unused, commenting out to make gcc happy
-#if 0
-/*
-==============
-Netchan_ScramblePacket
-
-A probably futile attempt to make proxy hacking somewhat
-more difficult.
-==============
-*/
-#define	SCRAMBLE_START	6
-static void Netchan_ScramblePacket( msg_t *buf ) {
-	unsigned	seed;
-	int			i, j, c, mask, temp;
-	int			seq[MAX_PACKETLEN];
-
-	seed = ( LittleLong( *(unsigned *)buf->data ) * 3 ) ^ ( buf->cursize * 123 );
-	c = buf->cursize;
-	if ( c <= SCRAMBLE_START ) {
-		return;
-	}
-	if ( c > MAX_PACKETLEN ) {
-		Com_Error( ERR_DROP, "MAX_PACKETLEN" );
-	}
-
-	// generate a sequence of "random" numbers
-	for (i = 0 ; i < c ; i++) {
-		seed = (119 * seed + 1);
-		seq[i] = seed;
-	}
-
-	// transpose each character
-	for ( mask = 1 ; mask < c-SCRAMBLE_START ; mask = ( mask << 1 ) + 1 ) {
-	}
-	mask >>= 1;
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		j = SCRAMBLE_START + ( seq[i] & mask );
-		temp = buf->data[j];
-		buf->data[j] = buf->data[i];
-		buf->data[i] = temp;
-	}
-
-	// byte xor the data after the header
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		buf->data[i] ^= seq[i];
-	}
-}
-
-static void Netchan_UnScramblePacket( msg_t *buf ) {
-	unsigned	seed;
-	int			i, j, c, mask, temp;
-	int			seq[MAX_PACKETLEN];
-
-	seed = ( LittleLong( *(unsigned *)buf->data ) * 3 ) ^ ( buf->cursize * 123 );
-	c = buf->cursize;
-	if ( c <= SCRAMBLE_START ) {
-		return;
-	}
-	if ( c > MAX_PACKETLEN ) {
-		Com_Error( ERR_DROP, "MAX_PACKETLEN" );
-	}
-
-	// generate a sequence of "random" numbers
-	for (i = 0 ; i < c ; i++) {
-		seed = (119 * seed + 1);
-		seq[i] = seed;
-	}
-
-	// byte xor the data after the header
-	for (i = SCRAMBLE_START ; i < c ; i++) {
-		buf->data[i] ^= seq[i];
-	}
-
-	// transpose each character in reverse order
-	for ( mask = 1 ; mask < c-SCRAMBLE_START ; mask = ( mask << 1 ) + 1 ) {
-	}
-	mask >>= 1;
-	for (i = c-1 ; i >= SCRAMBLE_START ; i--) {
-		j = SCRAMBLE_START + ( seq[i] & mask );
-		temp = buf->data[j];
-		buf->data[j] = buf->data[i];
-		buf->data[i] = temp;
-	}
-}
-#endif
-
 /*
 =================
 Netchan_TransmitNextFragment
@@ -206,7 +120,7 @@
 
 	// send the qport if we are a client
 	if ( chan->sock == NS_CLIENT ) {
-		MSG_WriteShort( &send, net_qport->integer );
+		MSG_WriteShort( &send, qport->integer );
 	}
 
 #ifdef LEGACY_PROTOCOL
@@ -226,7 +140,7 @@
 
 	// send the datagram
 	NET_SendPacket(chan->sock, send.cursize, send.data, chan->remoteAddress);
-
+	
 	// Store send time and size of this packet for rate control
 	chan->lastSentTime = Sys_Milliseconds();
 	chan->lastSentSize = send.cursize;
@@ -288,7 +202,7 @@
 
 	// send the qport if we are a client
 	if(chan->sock == NS_CLIENT)
-		MSG_WriteShort(&send, net_qport->integer);
+		MSG_WriteShort(&send, qport->integer);
 
 #ifdef LEGACY_PROTOCOL
 	if(!chan->compat)

```
