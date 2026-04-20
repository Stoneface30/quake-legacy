# Diff: `code/renderergl2/tr_sky.c`
**Canonical:** `wolfcamql-src` (sha256 `b606ab56d5b2...`, 24372 bytes)

## Variants

### `ioquake3`  — sha256 `100b76099bba...`, 23661 bytes

_Diff stat: +1 / -25 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_sky.c	2026-04-16 20:02:25.264766300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_sky.c	2026-04-16 20:02:21.616761100 +0100
@@ -626,7 +626,7 @@
 			MIN_T = -HALF_SKY_SUBDIVISIONS;
 
 			// still don't want to draw the bottom, even if fullClouds
-			if ( i == 5   &&  !r_drawSkyFloor->integer)
+			if ( i == 5 )
 				continue;
 		}
 		else
@@ -752,10 +752,6 @@
 	vec3_t skyVec;
 	vec3_t v;
 
-	if (*r_cloudHeight->string) {
-		heightCloud = r_cloudHeight->value;
-	}
-
 	// init zfar so MakeSkyVec works even though
 	// a world hasn't been bounded
 	backEnd.viewParms.zFar = 1024;
@@ -864,27 +860,7 @@
 ================
 */
 void RB_StageIteratorSky( void ) {
-	int clearBits = 0;
-
 	if ( r_fastsky->integer ) {
-		if (r_fastsky->integer == 2  &&  !(backEnd.refdef.rdflags & RDF_NOWORLDMODEL)) {
-			clearBits |= GL_COLOR_BUFFER_BIT;	// FIXME: only if sky shaders have been used
-			if (*r_fastSkyColor->string) {
-				int v, sr, sg, sb;
-
-				v = r_fastSkyColor->integer;
-				sr = (v & 0xff0000) / 0x010000;
-				sg = (v & 0x00ff00) / 0x000100;
-				sb = (v & 0x0000ff) / 0x000001;
-
-				qglClearColor((float)sr / 255.0, (float)sg / 255.0, (float)sb / 255.0, 1.0);
-			} else {
-				qglClearColor(0.0f, 0.0f, 0.0f, 1.0f);	// FIXME: get color of sky
-			}
-
-			qglClear(clearBits);
-		}
-
 		return;
 	}
 

```
