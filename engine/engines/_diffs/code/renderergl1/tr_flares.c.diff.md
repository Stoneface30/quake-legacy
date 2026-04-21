# Diff: `code/renderergl1/tr_flares.c`
**Canonical:** `wolfcamql-src` (sha256 `c75a571937f9...`, 15834 bytes)

## Variants

### `ioquake3`  — sha256 `f5b5f5eec710...`, 15525 bytes

_Diff stat: +5 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_flares.c	2026-04-16 20:02:25.242242100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_flares.c	2026-04-16 20:02:21.584123200 +0100
@@ -81,10 +81,10 @@
 
 #define		MAX_FLARES		256
 
-static flare_t		r_flareStructs[MAX_FLARES];
-static flare_t		*r_activeFlares, *r_inactiveFlares;
+flare_t		r_flareStructs[MAX_FLARES];
+flare_t		*r_activeFlares, *r_inactiveFlares;
 
-static int flareCoeff;
+int flareCoeff;
 
 /*
 ==================
@@ -143,9 +143,8 @@
 		d = DotProduct(local, normal);
 
 		// If the viewer is behind the flare don't add it.
-		if(d < 0) {
+		if(d < 0)
 			return;
-		}
 	}
 
 	// if the point is off the screen, don't bother adding it
@@ -314,8 +313,6 @@
 		fade = 1;
 	}
 
-	//ri.Printf(PRINT_ALL, "%p fade %f\n", f, fade);
-
 	f->drawIntensity = fade;
 }
 
@@ -332,13 +329,6 @@
 	float distance, intensity, factor;
 	byte fogFactors[3] = {255, 255, 255};
 
-	//FIXME maybe, prevents, somewhat, completely obscured flares drawing
-	// through surfaces.  so center point at least has to be visible
-
-	if (!f->visible) {
-		return;
-	}
-
 	backEnd.pc.c_flareRenders++;
 
 	// We don't want too big values anyways when dividing by distance.
@@ -484,11 +474,7 @@
 	backEnd.currentEntity = &tr.worldEntity;
 	backEnd.or = backEnd.viewParms.world;
 
-#if 1
-	if (r_flares->integer > 1) {
-		RB_AddDlightFlares();
-	}
-#endif
+//	RB_AddDlightFlares();
 
 	// perform z buffer readback on each flare in this view
 	draw = qfalse;

```
