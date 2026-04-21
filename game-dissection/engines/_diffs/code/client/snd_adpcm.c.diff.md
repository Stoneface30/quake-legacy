# Diff: `code/client/snd_adpcm.c`
**Canonical:** `wolfcamql-src` (sha256 `c0ff3c8dd109...`, 9198 bytes)

## Variants

### `quake3-source`  — sha256 `2748989a3194...`, 9132 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_adpcm.c	2026-04-16 20:02:25.175948600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\snd_adpcm.c	2026-04-16 20:02:19.894095900 +0100
@@ -25,7 +25,7 @@
 /*
 ** Intel/DVI ADPCM coder/decoder.
 **
-** The algorithm for this coder was taken from the IMA Compatibility Project
+** The algorithm for this coder was taken from the IMA Compatability Project
 ** proceedings, Vol 2, Number 2; May 1992.
 **
 ** Version 1.2, 18-Dec-92.
@@ -53,8 +53,8 @@
 };
 
    
-void S_AdpcmEncode( const short indata[], char outdata[], int len, struct adpcm_state *state ) {
-    const short *inp;			/* Input buffer pointer */
+void S_AdpcmEncode( short indata[], char outdata[], int len, struct adpcm_state *state ) {
+    short *inp;			/* Input buffer pointer */
     signed char *outp;		/* output buffer pointer */
     int val;			/* Current input sample value */
     int sign;			/* Current adpcm sign bit */
@@ -153,7 +153,7 @@
 
 
 /* static */ void S_AdpcmDecode( const char indata[], short *outdata, int len, struct adpcm_state *state ) {
-    const signed char *inp;		/* Input buffer pointer */
+    signed char *inp;		/* Input buffer pointer */
     int outp;			/* output buffer pointer */
     int sign;			/* Current adpcm sign bit */
     int delta;			/* Current adpcm output value */
@@ -165,7 +165,7 @@
     int bufferstep;		/* toggle between inputbuffer/input */
 
     outp = 0;
-    inp = (const signed char *)indata;
+    inp = (signed char *)indata;
 
     valpred = state->sample;
     index = state->index;
@@ -268,7 +268,7 @@
 S_AdpcmGetSamples
 ====================
 */
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to) {
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to) {
 	adpcm_state_t	state;
 	byte			*out;
 
@@ -278,7 +278,7 @@
 
 	out = (byte *)chunk->sndChunk;
 	// get samples
-	S_AdpcmDecode((char *) out, to, SND_CHUNK_SIZE_BYTE*2, &state );
+	S_AdpcmDecode( out, to, SND_CHUNK_SIZE_BYTE*2, &state );
 }
 
 
@@ -310,7 +310,7 @@
 		newchunk = SND_malloc();
 		if (sfx->soundData == NULL) {
 			sfx->soundData = newchunk;
-		} else if (chunk != NULL) {
+		} else {
 			chunk->next = newchunk;
 		}
 		chunk = newchunk;
@@ -322,7 +322,7 @@
 		out = (byte *)chunk->sndChunk;
 
 		// encode the samples
-		S_AdpcmEncode( samples + inOffset, (char *) out, n, &state );
+		S_AdpcmEncode( samples + inOffset, out, n, &state );
 
 		inOffset += n;
 		count -= n;

```

### `quake3e`  — sha256 `6bb80cc958c3...`, 9168 bytes
Also identical in: ioquake3

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_adpcm.c	2026-04-16 20:02:25.175948600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_adpcm.c	2026-04-16 20:02:26.915520500 +0100
@@ -53,8 +53,8 @@
 };
 
    
-void S_AdpcmEncode( const short indata[], char outdata[], int len, struct adpcm_state *state ) {
-    const short *inp;			/* Input buffer pointer */
+void S_AdpcmEncode( short indata[], char outdata[], int len, struct adpcm_state *state ) {
+    short *inp;			/* Input buffer pointer */
     signed char *outp;		/* output buffer pointer */
     int val;			/* Current input sample value */
     int sign;			/* Current adpcm sign bit */
@@ -153,7 +153,7 @@
 
 
 /* static */ void S_AdpcmDecode( const char indata[], short *outdata, int len, struct adpcm_state *state ) {
-    const signed char *inp;		/* Input buffer pointer */
+    signed char *inp;		/* Input buffer pointer */
     int outp;			/* output buffer pointer */
     int sign;			/* Current adpcm sign bit */
     int delta;			/* Current adpcm output value */
@@ -165,7 +165,7 @@
     int bufferstep;		/* toggle between inputbuffer/input */
 
     outp = 0;
-    inp = (const signed char *)indata;
+    inp = (signed char *)indata;
 
     valpred = state->sample;
     index = state->index;
@@ -268,7 +268,7 @@
 S_AdpcmGetSamples
 ====================
 */
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to) {
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to) {
 	adpcm_state_t	state;
 	byte			*out;
 

```

### `openarena-engine`  — sha256 `8d8a16e48df5...`, 9168 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_adpcm.c	2026-04-16 20:02:25.175948600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_adpcm.c	2026-04-16 22:48:25.734378800 +0100
@@ -25,7 +25,7 @@
 /*
 ** Intel/DVI ADPCM coder/decoder.
 **
-** The algorithm for this coder was taken from the IMA Compatibility Project
+** The algorithm for this coder was taken from the IMA Compatability Project
 ** proceedings, Vol 2, Number 2; May 1992.
 **
 ** Version 1.2, 18-Dec-92.
@@ -53,8 +53,8 @@
 };
 
    
-void S_AdpcmEncode( const short indata[], char outdata[], int len, struct adpcm_state *state ) {
-    const short *inp;			/* Input buffer pointer */
+void S_AdpcmEncode( short indata[], char outdata[], int len, struct adpcm_state *state ) {
+    short *inp;			/* Input buffer pointer */
     signed char *outp;		/* output buffer pointer */
     int val;			/* Current input sample value */
     int sign;			/* Current adpcm sign bit */
@@ -153,7 +153,7 @@
 
 
 /* static */ void S_AdpcmDecode( const char indata[], short *outdata, int len, struct adpcm_state *state ) {
-    const signed char *inp;		/* Input buffer pointer */
+    signed char *inp;		/* Input buffer pointer */
     int outp;			/* output buffer pointer */
     int sign;			/* Current adpcm sign bit */
     int delta;			/* Current adpcm output value */
@@ -165,7 +165,7 @@
     int bufferstep;		/* toggle between inputbuffer/input */
 
     outp = 0;
-    inp = (const signed char *)indata;
+    inp = (signed char *)indata;
 
     valpred = state->sample;
     index = state->index;
@@ -268,7 +268,7 @@
 S_AdpcmGetSamples
 ====================
 */
-void S_AdpcmGetSamples(const sndBuffer *chunk, short *to) {
+void S_AdpcmGetSamples(sndBuffer *chunk, short *to) {
 	adpcm_state_t	state;
 	byte			*out;
 

```
