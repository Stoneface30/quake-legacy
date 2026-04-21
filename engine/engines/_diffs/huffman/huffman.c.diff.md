# Diff: `huffman/huffman.c`
**Canonical:** `demodumper` (sha256 `eeef753bd775...`, 14057 bytes)

## Variants

### `qldemo-python`  — sha256 `6fa9e349bb6f...`, 14083 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\huffman\huffman.c	2026-04-16 20:02:27.596241700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\huffman\huffman.c	2026-04-16 20:02:26.529759900 +0100
@@ -196,7 +196,7 @@
 
 void Huff_addRef( huff_t* huff, byte ch ) {
     node_t *tnode, *tnode2;
-    node_t *tt = huff->loc[ch];
+    //node_t *tt = huff->loc[ch];
     if (huff->loc[ch] == NULL) { /* if this is the first transmission of this node */
         tnode = &(huff->nodeList[huff->blocNode++]);
         tnode2 = &(huff->nodeList[huff->blocNode++]);
@@ -298,10 +298,10 @@
 /*        Com_Error(ERR_DROP, "Illegal tree!\n"); */
     }
 
-    if( node->symbol == 129 )
-    {
-      int a = 0;
-    }
+    /* if( node->symbol == 129 ) */
+    /* { */
+    /*   int a = 0; */
+    /* } */
 
     //fprintf( log, "%s, %d\n", s.c_str(), node->symbol );
     *ch = node->symbol;

```
