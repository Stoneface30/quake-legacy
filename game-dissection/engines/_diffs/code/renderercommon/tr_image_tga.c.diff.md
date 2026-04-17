# Diff: `code/renderercommon/tr_image_tga.c`
**Canonical:** `wolfcamql-src` (sha256 `6fff25ee7a70...`, 8942 bytes)

## Variants

### `ioquake3`  — sha256 `e58459f9438c...`, 8941 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_tga.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_image_tga.c	2026-04-16 20:02:21.577618400 +0100
@@ -42,7 +42,7 @@
 {
 	unsigned	columns, rows, numPixels;
 	byte	*pixbuf;
-	int		row, column;
+	int	row, column;
 	byte	*buf_p;
 	byte	*end;
 	union {

```

### `quake3e`  — sha256 `5512e6d66106...`, 9404 bytes

_Diff stat: +65 / -60 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_tga.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_image_tga.c	2026-04-16 20:02:27.344319500 +0100
@@ -20,7 +20,8 @@
 ===========================================================================
 */
 
-#include "tr_common.h"
+#include "../qcommon/q_shared.h"
+#include "../renderercommon/tr_public.h"
 
 /*
 ========================================================================
@@ -79,7 +80,7 @@
 	targa_header.id_length = buf_p[0];
 	targa_header.colormap_type = buf_p[1];
 	targa_header.image_type = buf_p[2];
-	
+
 	memcpy(&targa_header.colormap_index, &buf_p[3], 2);
 	memcpy(&targa_header.colormap_length, &buf_p[5], 2);
 	targa_header.colormap_size = buf_p[7];
@@ -99,9 +100,9 @@
 
 	buf_p += 18;
 
-	if (targa_header.image_type!=2 
+	if (targa_header.image_type!=2
 		&& targa_header.image_type!=10
-		&& targa_header.image_type != 3 ) 
+		&& targa_header.image_type != 3 )
 	{
 		ri.Error (ERR_DROP, "LoadTGA: Only type 2 (RGB), 3 (gray), and 10 (RGB) TGA images supported");
 	}
@@ -135,63 +136,66 @@
 
 		buf_p += targa_header.id_length;  // skip TARGA image comment
 	}
-	
-	if ( targa_header.image_type==2 || targa_header.image_type == 3 )
-	{ 
-		if(buf_p + columns*rows*targa_header.pixel_size/8 > end)
+
+	if ( targa_header.image_type == 2 || targa_header.image_type == 3 )
+	{
+		if ( buf_p + columns * rows * targa_header.pixel_size / 8 > end )
 		{
-			ri.Error (ERR_DROP, "LoadTGA: file truncated (%s)", name);
+			ri.Error( ERR_DROP, "LoadTGA: file truncated (%s)", name );
 		}
-
 		// Uncompressed RGB or gray scale image
-		for(row=rows-1; row>=0; row--) 
-		{
-			pixbuf = targa_rgba + row*columns*4;
-			for(column=0; column<columns; column++) 
-			{
-				unsigned char red,green,blue,alphabyte;
-				switch (targa_header.pixel_size) 
-				{
-					
-				case 8:
-					blue = *buf_p++;
-					green = blue;
-					red = blue;
-					*pixbuf++ = red;
-					*pixbuf++ = green;
-					*pixbuf++ = blue;
-					*pixbuf++ = 255;
-					break;
-
-				case 24:
-					blue = *buf_p++;
-					green = *buf_p++;
-					red = *buf_p++;
-					*pixbuf++ = red;
-					*pixbuf++ = green;
-					*pixbuf++ = blue;
-					*pixbuf++ = 255;
-					break;
-				case 32:
-					blue = *buf_p++;
-					green = *buf_p++;
-					red = *buf_p++;
-					alphabyte = *buf_p++;
-					*pixbuf++ = red;
-					*pixbuf++ = green;
-					*pixbuf++ = blue;
-					*pixbuf++ = alphabyte;
-					break;
-				default:
-					ri.Error( ERR_DROP, "LoadTGA: illegal pixel_size '%d' in file '%s'", targa_header.pixel_size, name );
-					break;
+		switch ( targa_header.pixel_size ) {
+			case 8:
+				for ( row = rows - 1; row >= 0; row-- )	{
+					pixbuf = targa_rgba + row * columns * 4;
+					for ( column = 0; column < columns; column++ ) {
+						byte red, green, blue;
+						red = green = blue = *buf_p++;
+						*pixbuf++ = red;
+						*pixbuf++ = green;
+						*pixbuf++ = blue;
+						*pixbuf++ = 255;
+					}
 				}
-			}
+				break;
+			case 24:
+				for ( row = rows - 1; row >= 0; row-- ) {
+					pixbuf = targa_rgba + row * columns * 4;
+					for ( column = 0; column < columns; column++ ) {
+						byte red, green, blue;
+						blue = *buf_p++;
+						green = *buf_p++;
+						red = *buf_p++;
+						*pixbuf++ = red;
+						*pixbuf++ = green;
+						*pixbuf++ = blue;
+						*pixbuf++ = 255;
+					}
+				}
+				break;
+			case 32:
+				for ( row = rows - 1; row >= 0; row-- ) {
+					pixbuf = targa_rgba + row * columns * 4;
+					for ( column = 0; column < columns; column++ ) {
+						byte red, green, blue, alpha;
+						blue = *buf_p++;
+						green = *buf_p++;
+						red = *buf_p++;
+						alpha = *buf_p++;
+						*pixbuf++ = red;
+						*pixbuf++ = green;
+						*pixbuf++ = blue;
+						*pixbuf++ = alpha;
+					}
+				}
+				break;
+			default:
+				ri.Error( ERR_DROP, "LoadTGA: illegal pixel_size '%d' in file '%s'", targa_header.pixel_size, name );
+				break;
 		}
 	}
 	else if (targa_header.image_type==10) {   // Runlength encoded RGB images
-		unsigned char red = 0, green = 0, blue = 0, alphabyte = 0;
-		unsigned char packetHeader, packetSize, j;
+		unsigned char red,green,blue,alphabyte,packetHeader,packetSize,j;
 
 		for(row=rows-1; row>=0; row--) {
 			pixbuf = targa_rgba + row*columns*4;
@@ -218,16 +222,17 @@
 								break;
 						default:
 							ri.Error( ERR_DROP, "LoadTGA: illegal pixel_size '%d' in file '%s'", targa_header.pixel_size, name );
+							red = green = blue = alphabyte = 0; // silence compiler warning
 							break;
 					}
-	
+
 					for(j=0;j<packetSize;j++) {
 						*pixbuf++=red;
 						*pixbuf++=green;
 						*pixbuf++=blue;
 						*pixbuf++=alphabyte;
 						column++;
-						if (column==(int)columns) { // run spans across rows
+						if ((unsigned int)column==columns) { // run spans across rows
 							column=0;
 							if (row>0)
 								row--;
@@ -267,14 +272,14 @@
 								break;
 						}
 						column++;
-						if (column==(int)columns) { // pixel packet run spans across rows
+						if ((unsigned int)column==columns) { // pixel packet run spans across rows
 							column=0;
 							if (row>0)
 								row--;
 							else
 								goto breakOut;
 							pixbuf = targa_rgba + row*columns*4;
-						}						
+						}
 					}
 				}
 			}
@@ -282,8 +287,8 @@
 		}
 	}
 
-#if 0 
-  // TTimo: this is the chunk of code to ensure a behavior that meets TGA specs 
+#if 0
+  // TTimo: this is the chunk of code to ensure a behavior that meets TGA specs
   // bit 5 set => top-down
   if (targa_header.attributes & 0x20) {
     unsigned char *flip = (unsigned char*)malloc (columns*4);

```

### `openarena-engine`  — sha256 `b7e97e1fac98...`, 9308 bytes

_Diff stat: +16 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_tga.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_image_tga.c	2026-04-16 22:48:25.932966000 +0100
@@ -103,17 +103,25 @@
 		&& targa_header.image_type!=10
 		&& targa_header.image_type != 3 ) 
 	{
-		ri.Error (ERR_DROP, "LoadTGA: Only type 2 (RGB), 3 (gray), and 10 (RGB) TGA images supported");
+		// leilei - made these far less fatal and more informative
+		ri.Printf( PRINT_WARNING, "LoadTGA: '%s' Only type 2 (RGB), 3 (gray), and 10 (RGB) TGA images supported\n", name);
+		//ri.Error (ERR_DROP, "LoadTGA: Only type 2 (RGB), 3 (gray), and 10 (RGB) TGA images supported");
+		return;
 	}
 
-	if ( targa_header.colormap_type != 0 )
+	else if ( targa_header.colormap_type != 0 )
 	{
-		ri.Error( ERR_DROP, "LoadTGA: colormaps not supported" );
+		ri.Printf( PRINT_WARNING, "LoadTGA: '%s' colormaps not supported\n", name);
+
+		//ri.Error( ERR_DROP, "LoadTGA: colormaps not supported" );
+		return;
 	}
 
-	if ( ( targa_header.pixel_size != 32 && targa_header.pixel_size != 24 ) && targa_header.image_type != 3 )
+	else if ( ( targa_header.pixel_size != 32 && targa_header.pixel_size != 24 ) && targa_header.image_type != 3 )
 	{
-		ri.Error (ERR_DROP, "LoadTGA: Only 32 or 24 bit images supported (no colormaps)");
+		ri.Printf( PRINT_WARNING, "LoadTGA: '%s' Only 32 or 24 bit images supported (no colormaps)\n", name);
+//		ri.Error (ERR_DROP, "LoadTGA: Only 32 or 24 bit images supported (no colormaps)");
+		return;
 	}
 
 	columns = targa_header.width;
@@ -190,8 +198,7 @@
 		}
 	}
 	else if (targa_header.image_type==10) {   // Runlength encoded RGB images
-		unsigned char red = 0, green = 0, blue = 0, alphabyte = 0;
-		unsigned char packetHeader, packetSize, j;
+		unsigned char red,green,blue,alphabyte,packetHeader,packetSize,j;
 
 		for(row=rows-1; row>=0; row--) {
 			pixbuf = targa_rgba + row*columns*4;
@@ -227,7 +234,7 @@
 						*pixbuf++=blue;
 						*pixbuf++=alphabyte;
 						column++;
-						if (column==(int)columns) { // run spans across rows
+						if (column==columns) { // run spans across rows
 							column=0;
 							if (row>0)
 								row--;
@@ -267,7 +274,7 @@
 								break;
 						}
 						column++;
-						if (column==(int)columns) { // pixel packet run spans across rows
+						if (column==columns) { // pixel packet run spans across rows
 							column=0;
 							if (row>0)
 								row--;

```
