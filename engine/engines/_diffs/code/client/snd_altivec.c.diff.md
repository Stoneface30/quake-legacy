# Diff: `code/client/snd_altivec.c`
**Canonical:** `wolfcamql-src` (sha256 `efe58b8eab32...`, 7463 bytes)

## Variants

### `ioquake3`  — sha256 `4089b0f5ae63...`, 7406 bytes

_Diff stat: +0 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_altivec.c	2026-04-16 20:02:25.175948600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_altivec.c	2026-04-16 20:02:21.531570600 +0100
@@ -35,7 +35,6 @@
 #include <altivec.h>
 #endif
 
-#if 0  // disabled wolfcam
 void S_PaintChannelFrom16_altivec( portable_samplepair_t paintbuffer[PAINTBUFFER_SIZE], int snd_vol, channel_t *ch, const sfx_t *sc, int count, int sampleOffset, int bufferOffset ) {
 	int						data, aoff, boff;
 	int						leftvol, rightvol;
@@ -228,4 +227,3 @@
 
 #endif
 
-#endif  // disabled wolfcam

```
