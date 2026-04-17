# Diff: `code/renderercommon/tr_image_bmp.c`
**Canonical:** `wolfcamql-src` (sha256 `9437aa901725...`, 6224 bytes)

## Variants

### `ioquake3`  — sha256 `37cbd7ad97ce...`, 6225 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_bmp.c	2026-04-16 20:02:25.234262100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_image_bmp.c	2026-04-16 20:02:21.576615700 +0100
@@ -164,7 +164,7 @@
 	numPixels = columns * rows;
 
 	if(columns <= 0 || !rows || numPixels > 0x1FFFFFFF // 4*1FFFFFFF == 0x7FFFFFFC < 0x7FFFFFFF
-	   || (((int)numPixels * 4) / columns) / 4 != rows)
+	    || (((int)numPixels * 4) / columns) / 4 != rows)
 	{
 	  ri.Error (ERR_DROP, "LoadBMP: %s has an invalid image size", name);
 	}

```

### `quake3e`  — sha256 `8c809923bac1...`, 6296 bytes

_Diff stat: +5 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_bmp.c	2026-04-16 20:02:25.234262100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_image_bmp.c	2026-04-16 20:02:27.343319600 +0100
@@ -20,7 +20,8 @@
 ===========================================================================
 */
 
-#include "tr_common.h"
+#include "../qcommon/q_shared.h"
+#include "../renderercommon/tr_public.h"
 
 typedef struct
 {
@@ -54,7 +55,7 @@
 		byte *b;
 		void *v;
 	} buffer;
-	unsigned	length;
+	int		length;
 	BMPHeader_t bmpHeader;
 	byte		*bmpRGBA;
 
@@ -132,7 +133,7 @@
 	{
 		ri.Error( ERR_DROP, "LoadBMP: only Windows-style BMP files supported (%s)", name );
 	}
-	if ( bmpHeader.fileSize != length )
+	if ( bmpHeader.fileSize != (unsigned int)length )
 	{
 		ri.Error( ERR_DROP, "LoadBMP: header size does not match file size (%u vs. %u) (%s)", bmpHeader.fileSize, length, name );
 	}
@@ -164,7 +165,7 @@
 	numPixels = columns * rows;
 
 	if(columns <= 0 || !rows || numPixels > 0x1FFFFFFF // 4*1FFFFFFF == 0x7FFFFFFC < 0x7FFFFFFF
-	   || (((int)numPixels * 4) / columns) / 4 != rows)
+	    || ((numPixels * 4) / columns) / 4 != (unsigned int)rows)
 	{
 	  ri.Error (ERR_DROP, "LoadBMP: %s has an invalid image size", name);
 	}

```

### `openarena-engine`  — sha256 `46b20684a476...`, 6216 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_bmp.c	2026-04-16 20:02:25.234262100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_image_bmp.c	2026-04-16 22:48:25.930957100 +0100
@@ -54,7 +54,7 @@
 		byte *b;
 		void *v;
 	} buffer;
-	unsigned	length;
+	int		length;
 	BMPHeader_t bmpHeader;
 	byte		*bmpRGBA;
 
@@ -164,7 +164,7 @@
 	numPixels = columns * rows;
 
 	if(columns <= 0 || !rows || numPixels > 0x1FFFFFFF // 4*1FFFFFFF == 0x7FFFFFFC < 0x7FFFFFFF
-	   || (((int)numPixels * 4) / columns) / 4 != rows)
+	    || ((numPixels * 4) / columns) / 4 != rows)
 	{
 	  ri.Error (ERR_DROP, "LoadBMP: %s has an invalid image size", name);
 	}

```
