# Diff: `code/qcommon/puff.c`
**Canonical:** `quake3e` (sha256 `414c536f85bc...`, 35634 bytes)

## Variants

### `openarena-engine`  — sha256 `aaed7e413739...`, 35569 bytes

_Diff stat: +6 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\puff.c	2026-04-16 20:02:27.305466300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\puff.c	2026-04-16 22:48:25.911365000 +0100
@@ -23,7 +23,7 @@
  * All dynamically allocated memory comes from the stack.  The stack required
  * is less than 2K bytes.  This code is compatible with 16-bit int's and
  * assumes that long's are at least 32 bits.  puff.c uses the short data type,
- * assumed to be 16 bits, for arrays in order to conserve memory.  The code
+ * assumed to be 16 bits, for arrays in order to to conserve memory.  The code
  * works whether integers are stored big endian or little endian.
  *
  * In the comments below are "Format notes" that describe the inflate process
@@ -120,7 +120,7 @@
     /* load at least need bits into val */
     val = s->bitbuf;
     while (s->bitcnt < need) {
-        if (s->incnt == s->inlen) Q_longjmp(s->env, 1);   /* out of input */
+        if (s->incnt == s->inlen) longjmp(s->env, 1);   /* out of input */
         val |= (int32_t)(s->in[s->incnt++]) << s->bitcnt;  /* load eight bits */
         s->bitcnt += 8;
     }
@@ -252,7 +252,7 @@
         }
         left = (MAXBITS+1) - len;
         if (left == 0) break;
-        if (s->incnt == s->inlen) Q_longjmp(s->env, 1);   /* out of input */
+        if (s->incnt == s->inlen) longjmp(s->env, 1);   /* out of input */
         bitbuf = s->in[s->incnt++];
         if (left > 8) left = 8;
     }
@@ -606,8 +606,8 @@
     int16_t lengths[MAXCODES];            /* descriptor code lengths */
     int16_t lencnt[MAXBITS+1], lensym[MAXLCODES];         /* lencode memory */
     int16_t distcnt[MAXBITS+1], distsym[MAXDCODES];       /* distcode memory */
-    struct huffman lencode;				/* length code */
-    struct huffman distcode;			/* distance code */
+    struct huffman lencode = {lencnt, lensym};          /* length code */
+    struct huffman distcode = {distcnt, distsym};       /* distance code */
     static const int16_t order[19] =      /* permutation of code length codes */
         {16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15};
 
@@ -615,12 +615,6 @@
     nlen = bits(s, 5) + 257;
     ndist = bits(s, 5) + 1;
     ncode = bits(s, 4) + 4;
-
-	lencode.count = lencnt;
-	lencode.symbol = lensym;
-	distcode.count = distcnt;
-	distcode.symbol = distsym;
-
     if (nlen > MAXLCODES || ndist > MAXDCODES)
         return -3;                      /* bad counts */
 
@@ -740,7 +734,7 @@
     s.bitcnt = 0;
 
     /* return if bits() or decode() tries to read past available input */
-    if ( Q_setjmp( s.env ) != 0 )       /* if came back here via longjmp() */
+    if (setjmp(s.env) != 0)             /* if came back here via longjmp() */
         err = 2;                        /* then skip do-loop, return error */
     else {
         /* process blocks until last block or error */

```
