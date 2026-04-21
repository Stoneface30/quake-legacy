# Diff: `code/qcommon/surfaceflags.h`
**Canonical:** `wolfcamql-src` (sha256 `fa1b89d64133...`, 3757 bytes)

## Variants

### `ioquake3`  — sha256 `9364ef35daca...`, 3649 bytes

_Diff stat: +0 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\surfaceflags.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\surfaceflags.h	2026-04-16 20:02:21.571105600 +0100
@@ -78,6 +78,3 @@
 #define	SURF_ALPHASHADOW		0x10000	// do per-pixel light shadow casting in q3map
 #define	SURF_NODLIGHT			0x20000	// don't dlight even if solid (solid lava, skies)
 #define SURF_DUST				0x40000 // leave a dust trail when walking on this surface
-#define SURF_SNOW				0x80000
-#define SURF_WOOD               0x100000
-#define SURF_DMGTHROUGH			0x200000

```

### `quake3e`  — sha256 `ac4056c262de...`, 3693 bytes

_Diff stat: +1 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\surfaceflags.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\surfaceflags.h	2026-04-16 20:02:27.307463300 +0100
@@ -58,6 +58,7 @@
 #define	CONTENTS_TRANSLUCENT	0x20000000	// don't consume surface fragments inside
 #define	CONTENTS_TRIGGER		0x40000000
 #define	CONTENTS_NODROP			0x80000000	// don't leave bodies or items (death fog, lava)
+#define	CONTENTS_NODE           0xFFFFFFFF
 
 #define	SURF_NODAMAGE			0x1		// never give falling damage
 #define	SURF_SLICK				0x2		// effects game physics
@@ -78,6 +79,3 @@
 #define	SURF_ALPHASHADOW		0x10000	// do per-pixel light shadow casting in q3map
 #define	SURF_NODLIGHT			0x20000	// don't dlight even if solid (solid lava, skies)
 #define SURF_DUST				0x40000 // leave a dust trail when walking on this surface
-#define SURF_SNOW				0x80000
-#define SURF_WOOD               0x100000
-#define SURF_DMGTHROUGH			0x200000

```

### `openarena-engine`  — sha256 `9f033a7b4d37...`, 3649 bytes

_Diff stat: +1 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\surfaceflags.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\surfaceflags.h	2026-04-16 22:48:25.913366000 +0100
@@ -22,7 +22,7 @@
 //
 // This file must be identical in the quake and utils directories
 
-// contents flags are separate bits
+// contents flags are seperate bits
 // a given brush can contribute multiple content bits
 
 // these definitions also need to be in q_shared.h!
@@ -78,6 +78,3 @@
 #define	SURF_ALPHASHADOW		0x10000	// do per-pixel light shadow casting in q3map
 #define	SURF_NODLIGHT			0x20000	// don't dlight even if solid (solid lava, skies)
 #define SURF_DUST				0x40000 // leave a dust trail when walking on this surface
-#define SURF_SNOW				0x80000
-#define SURF_WOOD               0x100000
-#define SURF_DMGTHROUGH			0x200000

```

### `openarena-gamecode`  — sha256 `8c674237c1c0...`, 3902 bytes

_Diff stat: +9 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\surfaceflags.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\qcommon\surfaceflags.h	2026-04-16 22:48:24.195007000 +0100
@@ -22,7 +22,7 @@
 //
 // This file must be identical in the quake and utils directories
 
-// contents flags are separate bits
+// contents flags are seperate bits
 // a given brush can contribute multiple content bits
 
 // these definitions also need to be in q_shared.h!
@@ -78,6 +78,11 @@
 #define	SURF_ALPHASHADOW		0x10000	// do per-pixel light shadow casting in q3map
 #define	SURF_NODLIGHT			0x20000	// don't dlight even if solid (solid lava, skies)
 #define SURF_DUST				0x40000 // leave a dust trail when walking on this surface
-#define SURF_SNOW				0x80000
-#define SURF_WOOD               0x100000
-#define SURF_DMGTHROUGH			0x200000
+// leilei - new surfaceflags
+#define SURF_SNOW			0x80000 
+#define SURF_WOOD			0x100000 
+#define SURF_SAND			0x200000 
+#define SURF_GRAVEL			0x400000  
+#define SURF_ICE			0x800000 
+#define SURF_GLASS			0x1000000 
+#define SURF_LEAVES			0x2000000 

```
