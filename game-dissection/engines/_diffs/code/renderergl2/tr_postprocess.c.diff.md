# Diff: `code/renderergl2/tr_postprocess.c`
**Canonical:** `wolfcamql-src` (sha256 `39b552a6e77b...`, 14557 bytes)

## Variants

### `ioquake3`  — sha256 `ca8d5eaaeee6...`, 14201 bytes

_Diff stat: +1 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_postprocess.c	2026-04-16 20:02:25.262261400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_postprocess.c	2026-04-16 20:02:21.614755200 +0100
@@ -289,7 +289,7 @@
 
 		ri.Printf(PRINT_DEVELOPER, "Waited %d iterations\n", iter);
 	}
-
+	
 	// Note: On desktop OpenGL this is a sample count (glRefConfig.occlusionQueryTarget == GL_SAMPLES_PASSED)
 	// but on OpenGL ES this is a boolean (glRefConfig.occlusionQueryTarget == GL_ANY_SAMPLES_PASSED)
 	qglGetQueryObjectuiv(tr.sunFlareQuery[tr.sunFlareQueryIndex], GL_QUERY_RESULT, &sampleCount);
@@ -480,14 +480,6 @@
 		VectorSet4(srcBox, 0, 0, tr.textureScratchFbo[0]->width, tr.textureScratchFbo[0]->height);
 		VectorSet4(dstBox, 0, 0, glConfig.vidWidth,              glConfig.vidHeight);
 		color[3] = factor;
-
-		/*
-		if (tr.usingFinalFrameBufferObject) {
-			FBO_Blit(tr.textureScratchFbo[0], srcBox, NULL, tr.finalFbo, dstBox, NULL, color, GLS_SRCBLEND_SRC_ALPHA | GLS_DSTBLEND_ONE_MINUS_SRC_ALPHA);
-		} else {
-			FBO_Blit(tr.textureScratchFbo[0], srcBox, NULL, NULL, dstBox, NULL, color, GLS_SRCBLEND_SRC_ALPHA | GLS_DSTBLEND_ONE_MINUS_SRC_ALPHA);
-		}
-		*/
 		FBO_Blit(tr.textureScratchFbo[0], srcBox, NULL, dstFbo, dstBox, NULL, color, GLS_SRCBLEND_SRC_ALPHA | GLS_DSTBLEND_ONE_MINUS_SRC_ALPHA);
 	}
 }

```
