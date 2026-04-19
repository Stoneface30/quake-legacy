# Diff: `code/qcommon/huffman.c`
**Canonical:** `wolfcamql-src` (sha256 `d3643e27642e...`, 11626 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `8c05d4033677...`, 11326 bytes

_Diff stat: +17 / -34 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\huffman.c	2026-04-16 20:02:25.222226900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\huffman.c	2026-04-16 20:02:19.960609700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -24,7 +24,7 @@
  * Compression book.  The ranks are not actually stored, but implicitly defined
  * by the location of a node within a doubly-linked list */
 
-#include "q_shared.h"
+#include "../game/q_shared.h"
 #include "qcommon.h"
 
 static int			bloc = 0;
@@ -39,16 +39,6 @@
 	*offset = bloc;
 }
 
-int		Huff_getBloc(void)
-{
-	return bloc;
-}
-
-void	Huff_setBloc(int _bloc)
-{
-	bloc = _bloc;
-}
-
 int		Huff_getBit( byte *fin, int *offset) {
 	int t;
 	bloc = *offset;
@@ -273,20 +263,15 @@
 	}
 	if (!node) {
 		return 0;
-//		Com_Error(ERR_DROP, "Illegal tree!");
+//		Com_Error(ERR_DROP, "Illegal tree!\n");
 	}
 	return (*ch = node->symbol);
 }
 
 /* Get a symbol */
-void Huff_offsetReceive (node_t *node, int *ch, byte *fin, int *offset, int maxoffset) {
+void Huff_offsetReceive (node_t *node, int *ch, byte *fin, int *offset) {
 	bloc = *offset;
 	while (node && node->symbol == INTERNAL_NODE) {
-		if (bloc >= maxoffset) {
-			*ch = 0;
-			*offset = maxoffset + 1;
-			return;
-		}
 		if (get_bit(fin)) {
 			node = node->right;
 		} else {
@@ -296,22 +281,18 @@
 	if (!node) {
 		*ch = 0;
 		return;
-//		Com_Error(ERR_DROP, "Illegal tree!");
+//		Com_Error(ERR_DROP, "Illegal tree!\n");
 	}
 	*ch = node->symbol;
 	*offset = bloc;
 }
 
 /* Send the prefix code for this node */
-static void send(node_t *node, node_t *child, byte *fout, int maxoffset) {
+static void send(node_t *node, node_t *child, byte *fout) {
 	if (node->parent) {
-		send(node->parent, node, fout, maxoffset);
+		send(node->parent, node, fout);
 	}
 	if (child) {
-		if (bloc >= maxoffset) {
-			bloc = maxoffset + 1;
-			return;
-		}
 		if (node->right == child) {
 			add_bit(1, fout);
 		} else {
@@ -321,22 +302,22 @@
 }
 
 /* Send a symbol */
-void Huff_transmit (huff_t *huff, int ch, byte *fout, int maxoffset) {
+void Huff_transmit (huff_t *huff, int ch, byte *fout) {
 	int i;
 	if (huff->loc[ch] == NULL) { 
 		/* node_t hasn't been transmitted, send a NYT, then the symbol */
-		Huff_transmit(huff, NYT, fout, maxoffset);
+		Huff_transmit(huff, NYT, fout);
 		for (i = 7; i >= 0; i--) {
 			add_bit((char)((ch >> i) & 0x1), fout);
 		}
 	} else {
-		send(huff->loc[ch], NULL, fout, maxoffset);
+		send(huff->loc[ch], NULL, fout);
 	}
 }
 
-void Huff_offsetTransmit (huff_t *huff, int ch, byte *fout, int *offset, int maxoffset) {
+void Huff_offsetTransmit (huff_t *huff, int ch, byte *fout, int *offset) {
 	bloc = *offset;
-	send(huff->loc[ch], NULL, fout, maxoffset);
+	send(huff->loc[ch], NULL, fout);
 	*offset = bloc;
 }
 
@@ -371,7 +352,7 @@
 	for ( j = 0; j < cch; j++ ) {
 		ch = 0;
 		// don't overflow reading from the messages
-		// FIXME: would it be better to have an overflow check in get_bit ?
+		// FIXME: would it be better to have a overflow check in get_bit ?
 		if ( (bloc >> 3) > size ) {
 			seq[j] = 0;
 			break;
@@ -401,7 +382,7 @@
 	huff_t		huff;
 
 	size = mbuf->cursize - offset;
-	buffer = mbuf->data + offset;
+	buffer = mbuf->data+ + offset;
 
 	if (size<=0) {
 		return;
@@ -414,6 +395,7 @@
 	huff.tree->weight = 0;
 	huff.lhead->next = huff.lhead->prev = NULL;
 	huff.tree->parent = huff.tree->left = huff.tree->right = NULL;
+	huff.loc[NYT] = huff.tree;
 
 	seq[0] = (size>>8);
 	seq[1] = size&0xff;
@@ -422,7 +404,7 @@
 
 	for (i=0; i<size; i++ ) {
 		ch = buffer[i];
-		Huff_transmit(&huff, ch, seq, size<<3);						/* Transmit symbol */
+		Huff_transmit(&huff, ch, seq);						/* Transmit symbol */
 		Huff_addRef(&huff, (byte)ch);								/* Do update */
 	}
 
@@ -450,5 +432,6 @@
 	huff->compressor.tree->weight = 0;
 	huff->compressor.lhead->next = huff->compressor.lhead->prev = NULL;
 	huff->compressor.tree->parent = huff->compressor.tree->left = huff->compressor.tree->right = NULL;
+	huff->compressor.loc[NYT] = huff->compressor.tree;
 }
 

```

### `quake3e`  — sha256 `dd4fe38b90cf...`, 11308 bytes

_Diff stat: +53 / -77 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\huffman.c	2026-04-16 20:02:25.222226900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\huffman.c	2026-04-16 20:02:27.303418100 +0100
@@ -27,36 +27,39 @@
 #include "q_shared.h"
 #include "qcommon.h"
 
-static int			bloc = 0;
+#define NYT HMAX					/* NYT = Not Yet Transmitted */
+#define INTERNAL_NODE (HMAX+1)
 
-void	Huff_putBit( int bit, byte *fout, int *offset) {
-	bloc = *offset;
-	if ((bloc&7) == 0) {
-		fout[(bloc>>3)] = 0;
-	}
-	fout[(bloc>>3)] |= bit << (bloc&7);
-	bloc++;
-	*offset = bloc;
-}
-
-int		Huff_getBloc(void)
-{
-	return bloc;
-}
-
-void	Huff_setBloc(int _bloc)
-{
-	bloc = _bloc;
-}
+typedef struct nodetype {
+	struct	nodetype *left, *right, *parent; /* tree structure */ 
+	struct	nodetype *next, *prev; /* doubly-linked list */
+	struct	nodetype **head; /* highest ranked node in block */
+	int		weight;
+	int		symbol;
+} node_t;
+
+#define HMAX 256 /* Maximum symbol */
+
+typedef struct {
+	int			blocNode;
+	int			blocPtrs;
+
+	node_t*		tree;
+	node_t*		lhead;
+	node_t*		ltail;
+	node_t*		loc[HMAX+1];
+	node_t**	freelist;
+
+	node_t		nodeList[768];
+	node_t*		nodePtrs[768];
+} huff_t;
+
+typedef struct {
+	huff_t		compressor;
+	huff_t		decompressor;
+} huffman_t;
 
-int		Huff_getBit( byte *fin, int *offset) {
-	int t;
-	bloc = *offset;
-	t = (fin[(bloc>>3)] >> (bloc&7)) & 0x1;
-	bloc++;
-	*offset = bloc;
-	return t;
-}
+static int			bloc = 0;
 
 /* Add a bit to the output file (buffered) */
 static void add_bit (char bit, byte *fout) {
@@ -193,7 +196,7 @@
 	}
 }
 
-void Huff_addRef(huff_t* huff, byte ch) {
+static void Huff_addRef(huff_t* huff, byte ch) {
 	node_t *tnode, *tnode2;
 	if (huff->loc[ch] == NULL) { /* if this is the first transmission of this node */
 		tnode = &(huff->nodeList[huff->blocNode++]);
@@ -263,7 +266,7 @@
 }
 
 /* Get a symbol */
-int Huff_Receive (node_t *node, int *ch, byte *fin) {
+static int Huff_Receive(node_t *node, int *ch, byte *fin) {
 	while (node && node->symbol == INTERNAL_NODE) {
 		if (get_bit(fin)) {
 			node = node->right;
@@ -278,40 +281,12 @@
 	return (*ch = node->symbol);
 }
 
-/* Get a symbol */
-void Huff_offsetReceive (node_t *node, int *ch, byte *fin, int *offset, int maxoffset) {
-	bloc = *offset;
-	while (node && node->symbol == INTERNAL_NODE) {
-		if (bloc >= maxoffset) {
-			*ch = 0;
-			*offset = maxoffset + 1;
-			return;
-		}
-		if (get_bit(fin)) {
-			node = node->right;
-		} else {
-			node = node->left;
-		}
-	}
-	if (!node) {
-		*ch = 0;
-		return;
-//		Com_Error(ERR_DROP, "Illegal tree!");
-	}
-	*ch = node->symbol;
-	*offset = bloc;
-}
-
 /* Send the prefix code for this node */
-static void send(node_t *node, node_t *child, byte *fout, int maxoffset) {
+static void send(node_t *node, node_t *child, byte *fout) {
 	if (node->parent) {
-		send(node->parent, node, fout, maxoffset);
+		send(node->parent, node, fout);
 	}
 	if (child) {
-		if (bloc >= maxoffset) {
-			bloc = maxoffset + 1;
-			return;
-		}
 		if (node->right == child) {
 			add_bit(1, fout);
 		} else {
@@ -321,35 +296,29 @@
 }
 
 /* Send a symbol */
-void Huff_transmit (huff_t *huff, int ch, byte *fout, int maxoffset) {
+static void Huff_transmit( huff_t *huff, int ch, byte *fout ) {
 	int i;
 	if (huff->loc[ch] == NULL) { 
 		/* node_t hasn't been transmitted, send a NYT, then the symbol */
-		Huff_transmit(huff, NYT, fout, maxoffset);
+		Huff_transmit(huff, NYT, fout);
 		for (i = 7; i >= 0; i--) {
 			add_bit((char)((ch >> i) & 0x1), fout);
 		}
 	} else {
-		send(huff->loc[ch], NULL, fout, maxoffset);
+		send(huff->loc[ch], NULL, fout);
 	}
 }
 
-void Huff_offsetTransmit (huff_t *huff, int ch, byte *fout, int *offset, int maxoffset) {
-	bloc = *offset;
-	send(huff->loc[ch], NULL, fout, maxoffset);
-	*offset = bloc;
-}
-
 void Huff_Decompress(msg_t *mbuf, int offset) {
 	int			ch, cch, i, j, size;
-	byte		seq[65536];
+	byte		seq[MAX_INFO_STRING*2];
 	byte*		buffer;
 	huff_t		huff;
 
 	size = mbuf->cursize - offset;
 	buffer = mbuf->data + offset;
 
-	if ( size <= 0 ) {
+	if ( size < 2 ) {
 		return;
 	}
 
@@ -366,6 +335,9 @@
 	if ( cch > mbuf->maxsize - offset ) {
 		cch = mbuf->maxsize - offset;
 	}
+	if ( cch > sizeof( seq ) ) {
+		cch = sizeof( seq );
+	}
 	bloc = 16;
 
 	for ( j = 0; j < cch; j++ ) {
@@ -383,7 +355,7 @@
 				ch = (ch<<1) + get_bit(buffer);
 			}
 		}
-    
+
 		seq[j] = ch;									/* Write symbol */
 
 		Huff_addRef(&huff, (byte)ch);								/* Increment node */
@@ -392,20 +364,23 @@
 	Com_Memcpy(mbuf->data + offset, seq, cch);
 }
 
-extern 	int oldsize;
 
 void Huff_Compress(msg_t *mbuf, int offset) {
 	int			i, ch, size;
-	byte		seq[65536];
+	// worst compression ratio is ~1.2x (rounded up to 2x) plus 2 plus 256 of possible NYT's
+	byte		seq[MAX_INFO_STRING*4 + 2 + 256];
 	byte*		buffer;
 	huff_t		huff;
 
 	size = mbuf->cursize - offset;
 	buffer = mbuf->data + offset;
 
-	if (size<=0) {
+	if ( size <= 0 ) {
 		return;
 	}
+	if ( size > MAX_INFO_STRING*2 ) {
+		size = MAX_INFO_STRING*2;
+	}
 
 	Com_Memset(&huff, 0, sizeof(huff_t));
 	// Add the NYT (not yet transmitted) node into the tree/list */
@@ -422,7 +397,7 @@
 
 	for (i=0; i<size; i++ ) {
 		ch = buffer[i];
-		Huff_transmit(&huff, ch, seq, size<<3);						/* Transmit symbol */
+		Huff_transmit(&huff, ch, seq);						/* Transmit symbol */
 		Huff_addRef(&huff, (byte)ch);								/* Do update */
 	}
 
@@ -432,6 +407,7 @@
 	Com_Memcpy(mbuf->data+offset, seq, (bloc>>3));
 }
 
+#if 0
 void Huff_Init(huffman_t *huff) {
 
 	Com_Memset(&huff->compressor, 0, sizeof(huff_t));
@@ -451,4 +427,4 @@
 	huff->compressor.lhead->next = huff->compressor.lhead->prev = NULL;
 	huff->compressor.tree->parent = huff->compressor.tree->left = huff->compressor.tree->right = NULL;
 }
-
+#endif

```

### `openarena-engine`  — sha256 `f45eb8f0920e...`, 11356 bytes

_Diff stat: +10 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\huffman.c	2026-04-16 20:02:25.222226900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\huffman.c	2026-04-16 22:48:25.908298000 +0100
@@ -279,14 +279,9 @@
 }
 
 /* Get a symbol */
-void Huff_offsetReceive (node_t *node, int *ch, byte *fin, int *offset, int maxoffset) {
+void Huff_offsetReceive (node_t *node, int *ch, byte *fin, int *offset) {
 	bloc = *offset;
 	while (node && node->symbol == INTERNAL_NODE) {
-		if (bloc >= maxoffset) {
-			*ch = 0;
-			*offset = maxoffset + 1;
-			return;
-		}
 		if (get_bit(fin)) {
 			node = node->right;
 		} else {
@@ -303,15 +298,11 @@
 }
 
 /* Send the prefix code for this node */
-static void send(node_t *node, node_t *child, byte *fout, int maxoffset) {
+static void send(node_t *node, node_t *child, byte *fout) {
 	if (node->parent) {
-		send(node->parent, node, fout, maxoffset);
+		send(node->parent, node, fout);
 	}
 	if (child) {
-		if (bloc >= maxoffset) {
-			bloc = maxoffset + 1;
-			return;
-		}
 		if (node->right == child) {
 			add_bit(1, fout);
 		} else {
@@ -321,22 +312,22 @@
 }
 
 /* Send a symbol */
-void Huff_transmit (huff_t *huff, int ch, byte *fout, int maxoffset) {
+void Huff_transmit (huff_t *huff, int ch, byte *fout) {
 	int i;
 	if (huff->loc[ch] == NULL) { 
 		/* node_t hasn't been transmitted, send a NYT, then the symbol */
-		Huff_transmit(huff, NYT, fout, maxoffset);
+		Huff_transmit(huff, NYT, fout);
 		for (i = 7; i >= 0; i--) {
 			add_bit((char)((ch >> i) & 0x1), fout);
 		}
 	} else {
-		send(huff->loc[ch], NULL, fout, maxoffset);
+		send(huff->loc[ch], NULL, fout);
 	}
 }
 
-void Huff_offsetTransmit (huff_t *huff, int ch, byte *fout, int *offset, int maxoffset) {
+void Huff_offsetTransmit (huff_t *huff, int ch, byte *fout, int *offset) {
 	bloc = *offset;
-	send(huff->loc[ch], NULL, fout, maxoffset);
+	send(huff->loc[ch], NULL, fout);
 	*offset = bloc;
 }
 
@@ -401,7 +392,7 @@
 	huff_t		huff;
 
 	size = mbuf->cursize - offset;
-	buffer = mbuf->data + offset;
+	buffer = mbuf->data+ + offset;
 
 	if (size<=0) {
 		return;
@@ -422,7 +413,7 @@
 
 	for (i=0; i<size; i++ ) {
 		ch = buffer[i];
-		Huff_transmit(&huff, ch, seq, size<<3);						/* Transmit symbol */
+		Huff_transmit(&huff, ch, seq);						/* Transmit symbol */
 		Huff_addRef(&huff, (byte)ch);								/* Do update */
 	}
 

```
