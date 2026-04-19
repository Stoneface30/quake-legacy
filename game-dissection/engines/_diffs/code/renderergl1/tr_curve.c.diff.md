# Diff: `code/renderergl1/tr_curve.c`
**Canonical:** `wolfcamql-src` (sha256 `c2cd4a7b474c...`, 16553 bytes)

## Variants

### `ioquake3`  — sha256 `d07e9729621a...`, 16485 bytes

_Diff stat: +1 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_curve.c	2026-04-16 20:02:25.241466700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_curve.c	2026-04-16 20:02:21.580615500 +0100
@@ -202,7 +202,7 @@
 				VectorAdd( normal, sum, sum );
 			}
 			//if ( count == 0 ) {
-			//      printf("bad normal\n");
+			//	printf("bad normal\n");
 			//}
 			VectorNormalize2( sum, dv->normal );
 		}
@@ -328,7 +328,6 @@
 	// compute local origin and bounds
 	VectorAdd( grid->meshBounds[0], grid->meshBounds[1], grid->localOrigin );
 	VectorScale( grid->localOrigin, 0.5f, grid->localOrigin );
-	//VectorScale( grid->localOrigin, 1.0f, grid->localOrigin );
 	VectorSubtract( grid->meshBounds[0], grid->localOrigin, tmpVec );
 	grid->meshRadius = VectorLength( tmpVec );
 

```
