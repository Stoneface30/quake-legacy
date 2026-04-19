# Diff: `code/renderercommon/tr_image_png.c`
**Canonical:** `wolfcamql-src` (sha256 `611fffe2b0fc...`, 51220 bytes)

## Variants

### `ioquake3`  — sha256 `07829a1eb14c...`, 43331 bytes

_Diff stat: +0 / -336 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_png.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderercommon\tr_image_png.c	2026-04-16 20:02:21.577618400 +0100
@@ -23,14 +23,6 @@
 
 #include "puff.h"
 
-#ifdef USE_LOCAL_HEADERS
-  #include "../zlib-1.3.1/zlib.h"
-#else
-  #include <zlib.h>
-#endif
-
-extern cvar_t *r_pngZlibCompression;
-
 // we could limit the png size to a lower value here
 #ifndef INT_MAX
 #define INT_MAX 0x1fffffff
@@ -2491,331 +2483,3 @@
 
 	CloseBufferedFile(ThePNG);
 }
-
-// png saving from jedi academy gpl source code
-
-//typedef unsigned long ulong;
-//FIXME just refs below
-#define ulong uint32_t
-
-// Outputs a crc'd chunk of PNG data
-
-qboolean PNG_OutputChunk (fileHandle_t fp, ulong type, byte *data, ulong size)
-{
-	ulong crc, little, outcount;
-
-	// Output a standard PNG chunk - length, type, data, crc
-	little = BigLong(size);
-	outcount = ri.FS_Write(&little, sizeof(little), fp);
-
-	little = BigLong(type);
-	crc = crc32(0, (byte *)&little, sizeof(little));
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(size)
-	{
-		crc = crc32(crc, data, size);
-		outcount += ri.FS_Write(data, size, fp);
-	}
-
-	little = BigLong(crc);
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(outcount != (size + 12))
-	{
-		//png_error = PNG_ERROR_WRITE;
-		ri.Printf(PRINT_ALL, "^1error creating output chunk for png\n");
-		return qfalse;
-	}
-	return qtrue;
-}
-
-// Pack up the image data line by line
-
-//FIXME
-#define MAX_PNG_WIDTH (4096 * 4)
-#define MAX_PNG_DEPTH (4)
-
-// Filter values
-
-#define PNG_FILTER_VALUE_NONE   0
-#define PNG_FILTER_VALUE_SUB    1
-#define PNG_FILTER_VALUE_UP             2
-#define PNG_FILTER_VALUE_AVG    3
-#define PNG_FILTER_VALUE_PAETH  4
-#define PNG_FILTER_NUM                  5
-
-// Filter a row of data
-
-void PNG_Filter (byte *out, byte filter, const byte *in, const byte *lastline, ulong rowbytes, ulong bpp)
-{
-	ulong		i;
-
-	switch(filter)
-	{
-	case PNG_FILTER_VALUE_NONE:
-		memcpy(out, in, rowbytes);
-		break;
-	case PNG_FILTER_VALUE_SUB:
-		for(i = 0; i < bpp; i++)
-		{
-			*out++ = *in++;
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			*out++ = *in - *(in - bpp);
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_UP:
-		for(i = 0; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		break;
-	case PNG_FILTER_VALUE_AVG:
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - (*lastline++ >> 1);
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in - ((*lastline++ + *(in - bpp)) >> 1);
-			}
-			else
-			{
-				*out++ = *in - (*(in - bpp) >> 1);
-			}
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_PAETH: {
-		int			a, b, c;
-		int			pa, pb, pc, p;
-
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			a = *(in - bpp);
-			c = 0;
-			b = 0;
-			if(lastline)
-			{
-				c = *(lastline - bpp);
-				b = *lastline++;
-			}
-
-			p = b - c;
-			pc = a - c;
-
-			pa = p < 0 ? -p : p;
-			pb = pc < 0 ? -pc : pc;
-			pc = (p + pc) < 0 ? -(p + pc) : p + pc;
-
-			p = (pa <= pb && pa <= pc) ? a : (pb <= pc) ? b : c;
-
-			*out++ = *in++ - p;
-		}
-		break;
-	}
-	}
-}
-
-qboolean PNG_Pack (byte *out, ulong *size, ulong maxsize, byte *data, int width, int height, int bytedepth)
-{
-	z_stream		zdata;
-	ulong			rowbytes;
-	ulong			y;
-	const byte		*lastline, *source;
-	// Storage for filter type and filtered row
-	byte			workline[(MAX_PNG_WIDTH * MAX_PNG_DEPTH) + 1];
-	int zlibCompression;
-
-	switch (r_pngZlibCompression->integer) {
-	case 0:
-		zlibCompression = Z_NO_COMPRESSION;
-		break;
-	case 1:
-		zlibCompression = Z_BEST_SPEED;
-		break;
-	case 9:
-		zlibCompression = Z_BEST_COMPRESSION;
-		break;
-	default:
-		zlibCompression = Z_DEFAULT_COMPRESSION;
-		break;
-	}
-
-	// Number of bytes per row
-	rowbytes = width * bytedepth;
-
-	memset(&zdata, 0, sizeof(z_stream));
-	if (deflateInit(&zdata, zlibCompression) != Z_OK) {
-		//png_error = PNG_ERROR_COMP;
-		ri.Printf(PRINT_ALL, "^1couldn't initialize zlib\n");
-		return qfalse;
-	}
-
-	zdata.next_out = out;
-	zdata.avail_out = maxsize;
-
-	lastline = NULL;
-	source = data + ((height - 1) * rowbytes);
-	for (y = 0;  y < height;  y++) {
-		// Refilter using the most compressable filter algo
-		// Assume paeth to speed things up
-		workline[0] = (byte)PNG_FILTER_VALUE_PAETH;
-		PNG_Filter(workline + 1, (byte)PNG_FILTER_VALUE_PAETH, source, lastline, rowbytes, bytedepth);
-
-		zdata.next_in = workline;
-		zdata.avail_in = rowbytes + 1;
-		if (deflate(&zdata, Z_SYNC_FLUSH) != Z_OK) {
-			ri.Printf(PRINT_ALL, "^1couldn't refilter data\n");
-			deflateEnd(&zdata);
-			//png_error = PNG_ERROR_COMP;
-			return qfalse;
-		}
-		lastline = source;
-		source -= rowbytes;
-	}
-	if (deflate(&zdata, Z_FINISH) != Z_STREAM_END) {
-		ri.Printf(PRINT_ALL, "^1couldn't finish data\n");
-		//png_error = PNG_ERROR_COMP;
-		return qfalse;
-	}
-	*size = zdata.total_out;
-	deflateEnd(&zdata);
-	return qtrue;
-}
-
-// Saves a PNG format compressed image
-
-//FIXME  PNG_ChunkType_*
-
-#if 0
-#define PNG_IHDR 'IHDR'
-#define PNG_IDAT                'IDAT'
-#define PNG_IEND                'IEND'
-#define PNG_tEXt                'tEXt'
-#endif
-
-qboolean SavePNG (const char *name, byte *data, int width, int height, int bytedepth)
-{
-	byte *work;
-	fileHandle_t fp;
-	int maxsize;
-	ulong size, outcount;
-	struct PNG_Chunk_IHDR header;
-
-	//png_error = PNG_ERROR_OK;
-
-	fp = ri.FS_FOpenFileWrite(name);
-	if (!fp) {
-		ri.Printf(PRINT_ALL, "^1couldn't open png file for saving: '%s'\n", name);
-		//png_error = PNG_ERROR_CREATE_FAIL;
-		return qfalse;
-	}
-	// Write out the PNG signature
-	outcount = ri.FS_Write(PNG_Signature, strlen(PNG_Signature), fp);
-	if (outcount != strlen(PNG_Signature)) {
-		ri.FS_FCloseFile(fp);
-		ri.Printf(PRINT_ALL, "^1couldn't write png signature\n");
-		//png_error = PNG_ERROR_WRITE;
-		return qfalse;
-	}
-	// Create and output a valid header
-	//PNG_CreateHeader(&png_header, width, height, bytedepth);
-	header.Width = BigLong(width);
-	header.Height = BigLong(height);
-	header.BitDepth = 8;
-	// rgb is 2?  rgba is 6?
-	if (bytedepth == 3) {
-		header.ColourType = 2;
-	}
-	if (bytedepth == 4) {
-		header.ColourType = 6;
-	}
-
-	header.CompressionMethod = 0;  // compression type will be included in scanlines
-	header.FilterMethod = 0;
-	header.InterlaceMethod = 0;
-
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IHDR, (byte *)&header, PNG_Chunk_IHDR_Size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write png header\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	//ri.Printf(PRINT_ALL, "^2test done width: %lu   height: %lu\n", header.Width, header.Height);
-	//ri.FS_FCloseFile(fp);
-	//return qtrue;
-
-#if 0
-	// Create and output the copyright info
- 	if(!PNG_OutputChunk(fp, PNG_ChunkType_TEXT, (byte *)png_copyright, sizeof(png_copyright))) {
-		ri.Printf(PRINT_ALL, "^1couldn't write copyright info\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-#endif
-
-	// Max size of compressed image (source size + 0.1% + 12)
-	maxsize = (width * height * bytedepth) + 4096;
-	work = (byte *)ri.Malloc(maxsize);
-
-	if (!work) {
-		ri.Printf(PRINT_ALL, "^1error: couldn't allocate buffer for png saving\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	// Pack up the image data
-	if (!PNG_Pack(work, &size, maxsize, data, width, height, bytedepth)) {
-		ri.Printf(PRINT_ALL, "^1couldn't pack png image data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	// Write out the compressed image data
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IDAT, (byte *)work, size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write compressed data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.Free(work);
-	// Output terminating chunk
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IEND, NULL, 0)) {
-		ri.Printf(PRINT_ALL, "^1couldn't ouptut terminating marker\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.FS_FCloseFile(fp);
-	return qtrue;
-}

```

### `quake3e`  — sha256 `a07529fd251a...`, 43494 bytes

_Diff stat: +24 / -357 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_png.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\renderercommon\tr_image_png.c	2026-04-16 20:02:27.343319600 +0100
@@ -19,17 +19,9 @@
 ===========================================================================
 */
 
-#include "tr_common.h"
-
-#include "puff.h"
-
-#ifdef USE_LOCAL_HEADERS
-  #include "../zlib-1.3.1/zlib.h"
-#else
-  #include <zlib.h>
-#endif
-
-extern cvar_t *r_pngZlibCompression;
+#include "../qcommon/q_shared.h"
+#include "../renderercommon/tr_public.h"
+#include "../qcommon/puff.h"
 
 // we could limit the png size to a lower value here
 #ifndef INT_MAX
@@ -540,7 +532,7 @@
 
 	if(!(BF && Buffer))
 	{
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	/*
@@ -548,6 +540,7 @@
 	 */
 
 	DecompressedData = NULL;
+	DecompressedDataLength = 0;
 	*Buffer = DecompressedData;
 
 	CompressedData = NULL;
@@ -561,7 +554,7 @@
 
 	if(!FindChunk(BF, PNG_ChunkType_IDAT))
 	{
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	/*
@@ -584,7 +577,7 @@
 
 			BufferedFileRewind(BF, BytesToRewind);
 
-			return((uint32_t)-1);
+			return((unsigned)-1);
 		}
 
 		/*
@@ -621,7 +614,7 @@
 			{
 				BufferedFileRewind(BF, BytesToRewind);
 
-				return((uint32_t)-1);
+				return((unsigned)-1);
 			}
 
 			BytesToRewind += Length + PNG_ChunkCRC_Size;
@@ -634,7 +627,7 @@
 	CompressedData = ri.Malloc(CompressedDataLength);
 	if(!CompressedData)
 	{
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	CompressedDataPtr = CompressedData;
@@ -654,7 +647,7 @@
 		{
 			ri.Free(CompressedData); 
 
-			return((uint32_t)-1);
+			return((unsigned)-1);
 		}
 
 		/*
@@ -688,14 +681,14 @@
 			{
 				ri.Free(CompressedData); 
 
-				return((uint32_t)-1);
+				return((unsigned)-1);
 			}
 
 			if(!BufferedFileSkip(BF, PNG_ChunkCRC_Size))
 			{
 				ri.Free(CompressedData); 
 
-				return((uint32_t)-1);
+				return((unsigned)-1);
 			}
 
 			memcpy(CompressedDataPtr, OrigCompressedData, Length);
@@ -726,7 +719,7 @@
 	{
 		ri.Free(CompressedData);
 
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	/*
@@ -738,7 +731,7 @@
 	{
 		ri.Free(CompressedData);
 
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	/*
@@ -769,7 +762,7 @@
 	{
 		ri.Free(DecompressedData);
 
-		return((uint32_t)-1);
+		return((unsigned)-1);
 	}
 
 	/*
@@ -1971,10 +1964,10 @@
 	if(!ThePNG)
 	{
 		return;
-	}           
+	}
 
 	/*
-	 *  Read the siganture of the file.
+	 *  Read the signature of the file.
 	 */
 
 	Signature = BufferedFileRead(ThePNG, PNG_Signature_Size);
@@ -2282,7 +2275,7 @@
 		{
 			case PNG_ColourType_Grey :
 			{
-				if(ChunkHeaderLength != 2)
+				if( ChunkHeaderLength != 2 )
 				{
 					CloseBufferedFile(ThePNG);
 
@@ -2304,7 +2297,7 @@
 
 			case PNG_ColourType_True :
 			{
-				if(ChunkHeaderLength != 6)
+				if( ChunkHeaderLength != 6 )
 				{
 					CloseBufferedFile(ThePNG);
 
@@ -2372,7 +2365,7 @@
 	 *  Rewind to the start of the file.
 	 */
 
-	if(!BufferedFileRewind(ThePNG, (unsigned)-1))
+	if(!BufferedFileRewind(ThePNG,(unsigned)-1))
 	{
 		CloseBufferedFile(ThePNG);
 
@@ -2395,10 +2388,12 @@
 	 */
 
 	DecompressedDataLength = DecompressIDATs(ThePNG, &DecompressedData);
-	if(!(DecompressedDataLength && DecompressedData))
+	if ( DecompressedDataLength == (unsigned)-1 )
+		DecompressedDataLength = 0;
+
+	if( !DecompressedDataLength || !DecompressedData )
 	{
 		CloseBufferedFile(ThePNG);
-
 		return;
 	}
 
@@ -2491,331 +2486,3 @@
 
 	CloseBufferedFile(ThePNG);
 }
-
-// png saving from jedi academy gpl source code
-
-//typedef unsigned long ulong;
-//FIXME just refs below
-#define ulong uint32_t
-
-// Outputs a crc'd chunk of PNG data
-
-qboolean PNG_OutputChunk (fileHandle_t fp, ulong type, byte *data, ulong size)
-{
-	ulong crc, little, outcount;
-
-	// Output a standard PNG chunk - length, type, data, crc
-	little = BigLong(size);
-	outcount = ri.FS_Write(&little, sizeof(little), fp);
-
-	little = BigLong(type);
-	crc = crc32(0, (byte *)&little, sizeof(little));
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(size)
-	{
-		crc = crc32(crc, data, size);
-		outcount += ri.FS_Write(data, size, fp);
-	}
-
-	little = BigLong(crc);
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(outcount != (size + 12))
-	{
-		//png_error = PNG_ERROR_WRITE;
-		ri.Printf(PRINT_ALL, "^1error creating output chunk for png\n");
-		return qfalse;
-	}
-	return qtrue;
-}
-
-// Pack up the image data line by line
-
-//FIXME
-#define MAX_PNG_WIDTH (4096 * 4)
-#define MAX_PNG_DEPTH (4)
-
-// Filter values
-
-#define PNG_FILTER_VALUE_NONE   0
-#define PNG_FILTER_VALUE_SUB    1
-#define PNG_FILTER_VALUE_UP             2
-#define PNG_FILTER_VALUE_AVG    3
-#define PNG_FILTER_VALUE_PAETH  4
-#define PNG_FILTER_NUM                  5
-
-// Filter a row of data
-
-void PNG_Filter (byte *out, byte filter, const byte *in, const byte *lastline, ulong rowbytes, ulong bpp)
-{
-	ulong		i;
-
-	switch(filter)
-	{
-	case PNG_FILTER_VALUE_NONE:
-		memcpy(out, in, rowbytes);
-		break;
-	case PNG_FILTER_VALUE_SUB:
-		for(i = 0; i < bpp; i++)
-		{
-			*out++ = *in++;
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			*out++ = *in - *(in - bpp);
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_UP:
-		for(i = 0; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		break;
-	case PNG_FILTER_VALUE_AVG:
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - (*lastline++ >> 1);
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in - ((*lastline++ + *(in - bpp)) >> 1);
-			}
-			else
-			{
-				*out++ = *in - (*(in - bpp) >> 1);
-			}
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_PAETH: {
-		int			a, b, c;
-		int			pa, pb, pc, p;
-
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			a = *(in - bpp);
-			c = 0;
-			b = 0;
-			if(lastline)
-			{
-				c = *(lastline - bpp);
-				b = *lastline++;
-			}
-
-			p = b - c;
-			pc = a - c;
-
-			pa = p < 0 ? -p : p;
-			pb = pc < 0 ? -pc : pc;
-			pc = (p + pc) < 0 ? -(p + pc) : p + pc;
-
-			p = (pa <= pb && pa <= pc) ? a : (pb <= pc) ? b : c;
-
-			*out++ = *in++ - p;
-		}
-		break;
-	}
-	}
-}
-
-qboolean PNG_Pack (byte *out, ulong *size, ulong maxsize, byte *data, int width, int height, int bytedepth)
-{
-	z_stream		zdata;
-	ulong			rowbytes;
-	ulong			y;
-	const byte		*lastline, *source;
-	// Storage for filter type and filtered row
-	byte			workline[(MAX_PNG_WIDTH * MAX_PNG_DEPTH) + 1];
-	int zlibCompression;
-
-	switch (r_pngZlibCompression->integer) {
-	case 0:
-		zlibCompression = Z_NO_COMPRESSION;
-		break;
-	case 1:
-		zlibCompression = Z_BEST_SPEED;
-		break;
-	case 9:
-		zlibCompression = Z_BEST_COMPRESSION;
-		break;
-	default:
-		zlibCompression = Z_DEFAULT_COMPRESSION;
-		break;
-	}
-
-	// Number of bytes per row
-	rowbytes = width * bytedepth;
-
-	memset(&zdata, 0, sizeof(z_stream));
-	if (deflateInit(&zdata, zlibCompression) != Z_OK) {
-		//png_error = PNG_ERROR_COMP;
-		ri.Printf(PRINT_ALL, "^1couldn't initialize zlib\n");
-		return qfalse;
-	}
-
-	zdata.next_out = out;
-	zdata.avail_out = maxsize;
-
-	lastline = NULL;
-	source = data + ((height - 1) * rowbytes);
-	for (y = 0;  y < height;  y++) {
-		// Refilter using the most compressable filter algo
-		// Assume paeth to speed things up
-		workline[0] = (byte)PNG_FILTER_VALUE_PAETH;
-		PNG_Filter(workline + 1, (byte)PNG_FILTER_VALUE_PAETH, source, lastline, rowbytes, bytedepth);
-
-		zdata.next_in = workline;
-		zdata.avail_in = rowbytes + 1;
-		if (deflate(&zdata, Z_SYNC_FLUSH) != Z_OK) {
-			ri.Printf(PRINT_ALL, "^1couldn't refilter data\n");
-			deflateEnd(&zdata);
-			//png_error = PNG_ERROR_COMP;
-			return qfalse;
-		}
-		lastline = source;
-		source -= rowbytes;
-	}
-	if (deflate(&zdata, Z_FINISH) != Z_STREAM_END) {
-		ri.Printf(PRINT_ALL, "^1couldn't finish data\n");
-		//png_error = PNG_ERROR_COMP;
-		return qfalse;
-	}
-	*size = zdata.total_out;
-	deflateEnd(&zdata);
-	return qtrue;
-}
-
-// Saves a PNG format compressed image
-
-//FIXME  PNG_ChunkType_*
-
-#if 0
-#define PNG_IHDR 'IHDR'
-#define PNG_IDAT                'IDAT'
-#define PNG_IEND                'IEND'
-#define PNG_tEXt                'tEXt'
-#endif
-
-qboolean SavePNG (const char *name, byte *data, int width, int height, int bytedepth)
-{
-	byte *work;
-	fileHandle_t fp;
-	int maxsize;
-	ulong size, outcount;
-	struct PNG_Chunk_IHDR header;
-
-	//png_error = PNG_ERROR_OK;
-
-	fp = ri.FS_FOpenFileWrite(name);
-	if (!fp) {
-		ri.Printf(PRINT_ALL, "^1couldn't open png file for saving: '%s'\n", name);
-		//png_error = PNG_ERROR_CREATE_FAIL;
-		return qfalse;
-	}
-	// Write out the PNG signature
-	outcount = ri.FS_Write(PNG_Signature, strlen(PNG_Signature), fp);
-	if (outcount != strlen(PNG_Signature)) {
-		ri.FS_FCloseFile(fp);
-		ri.Printf(PRINT_ALL, "^1couldn't write png signature\n");
-		//png_error = PNG_ERROR_WRITE;
-		return qfalse;
-	}
-	// Create and output a valid header
-	//PNG_CreateHeader(&png_header, width, height, bytedepth);
-	header.Width = BigLong(width);
-	header.Height = BigLong(height);
-	header.BitDepth = 8;
-	// rgb is 2?  rgba is 6?
-	if (bytedepth == 3) {
-		header.ColourType = 2;
-	}
-	if (bytedepth == 4) {
-		header.ColourType = 6;
-	}
-
-	header.CompressionMethod = 0;  // compression type will be included in scanlines
-	header.FilterMethod = 0;
-	header.InterlaceMethod = 0;
-
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IHDR, (byte *)&header, PNG_Chunk_IHDR_Size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write png header\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	//ri.Printf(PRINT_ALL, "^2test done width: %lu   height: %lu\n", header.Width, header.Height);
-	//ri.FS_FCloseFile(fp);
-	//return qtrue;
-
-#if 0
-	// Create and output the copyright info
- 	if(!PNG_OutputChunk(fp, PNG_ChunkType_TEXT, (byte *)png_copyright, sizeof(png_copyright))) {
-		ri.Printf(PRINT_ALL, "^1couldn't write copyright info\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-#endif
-
-	// Max size of compressed image (source size + 0.1% + 12)
-	maxsize = (width * height * bytedepth) + 4096;
-	work = (byte *)ri.Malloc(maxsize);
-
-	if (!work) {
-		ri.Printf(PRINT_ALL, "^1error: couldn't allocate buffer for png saving\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	// Pack up the image data
-	if (!PNG_Pack(work, &size, maxsize, data, width, height, bytedepth)) {
-		ri.Printf(PRINT_ALL, "^1couldn't pack png image data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	// Write out the compressed image data
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IDAT, (byte *)work, size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write compressed data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.Free(work);
-	// Output terminating chunk
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IEND, NULL, 0)) {
-		ri.Printf(PRINT_ALL, "^1couldn't ouptut terminating marker\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.FS_FCloseFile(fp);
-	return qtrue;
-}

```

### `openarena-engine`  — sha256 `542f43bd9c73...`, 43224 bytes

_Diff stat: +15 / -351 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderercommon\tr_image_png.c	2026-04-16 20:02:25.235331200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\renderercommon\tr_image_png.c	2026-04-16 22:48:25.932966000 +0100
@@ -21,15 +21,7 @@
 
 #include "tr_common.h"
 
-#include "puff.h"
-
-#ifdef USE_LOCAL_HEADERS
-  #include "../zlib-1.3.1/zlib.h"
-#else
-  #include <zlib.h>
-#endif
-
-extern cvar_t *r_pngZlibCompression;
+#include "../qcommon/puff.h"
 
 // we could limit the png size to a lower value here
 #ifndef INT_MAX
@@ -540,7 +532,7 @@
 
 	if(!(BF && Buffer))
 	{
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	/*
@@ -561,7 +553,7 @@
 
 	if(!FindChunk(BF, PNG_ChunkType_IDAT))
 	{
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	/*
@@ -579,12 +571,12 @@
 		{
 			/*
 			 *  Rewind to the start of this adventure
-			 *  and return unsuccessful
+			 *  and return unsuccessfull
 			 */
 
 			BufferedFileRewind(BF, BytesToRewind);
 
-			return((uint32_t)-1);
+			return(-1);
 		}
 
 		/*
@@ -621,7 +613,7 @@
 			{
 				BufferedFileRewind(BF, BytesToRewind);
 
-				return((uint32_t)-1);
+				return(-1);
 			}
 
 			BytesToRewind += Length + PNG_ChunkCRC_Size;
@@ -634,7 +626,7 @@
 	CompressedData = ri.Malloc(CompressedDataLength);
 	if(!CompressedData)
 	{
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	CompressedDataPtr = CompressedData;
@@ -654,7 +646,7 @@
 		{
 			ri.Free(CompressedData); 
 
-			return((uint32_t)-1);
+			return(-1);
 		}
 
 		/*
@@ -688,14 +680,14 @@
 			{
 				ri.Free(CompressedData); 
 
-				return((uint32_t)-1);
+				return(-1);
 			}
 
 			if(!BufferedFileSkip(BF, PNG_ChunkCRC_Size))
 			{
 				ri.Free(CompressedData); 
 
-				return((uint32_t)-1);
+				return(-1);
 			}
 
 			memcpy(CompressedDataPtr, OrigCompressedData, Length);
@@ -726,7 +718,7 @@
 	{
 		ri.Free(CompressedData);
 
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	/*
@@ -738,7 +730,7 @@
 	{
 		ri.Free(CompressedData);
 
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	/*
@@ -762,14 +754,14 @@
 	ri.Free(CompressedData);
 
 	/*
-	 *  Check if the last puff() was successful.
+	 *  Check if the last puff() was successfull.
 	 */
 
 	if(!((puffResult == 0) && (puffDestLen > 0)))
 	{
 		ri.Free(DecompressedData);
 
-		return((uint32_t)-1);
+		return(-1);
 	}
 
 	/*
@@ -2372,7 +2364,7 @@
 	 *  Rewind to the start of the file.
 	 */
 
-	if(!BufferedFileRewind(ThePNG, (unsigned)-1))
+	if(!BufferedFileRewind(ThePNG, -1))
 	{
 		CloseBufferedFile(ThePNG);
 
@@ -2491,331 +2483,3 @@
 
 	CloseBufferedFile(ThePNG);
 }
-
-// png saving from jedi academy gpl source code
-
-//typedef unsigned long ulong;
-//FIXME just refs below
-#define ulong uint32_t
-
-// Outputs a crc'd chunk of PNG data
-
-qboolean PNG_OutputChunk (fileHandle_t fp, ulong type, byte *data, ulong size)
-{
-	ulong crc, little, outcount;
-
-	// Output a standard PNG chunk - length, type, data, crc
-	little = BigLong(size);
-	outcount = ri.FS_Write(&little, sizeof(little), fp);
-
-	little = BigLong(type);
-	crc = crc32(0, (byte *)&little, sizeof(little));
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(size)
-	{
-		crc = crc32(crc, data, size);
-		outcount += ri.FS_Write(data, size, fp);
-	}
-
-	little = BigLong(crc);
-	outcount += ri.FS_Write(&little, sizeof(little), fp);
-
-	if(outcount != (size + 12))
-	{
-		//png_error = PNG_ERROR_WRITE;
-		ri.Printf(PRINT_ALL, "^1error creating output chunk for png\n");
-		return qfalse;
-	}
-	return qtrue;
-}
-
-// Pack up the image data line by line
-
-//FIXME
-#define MAX_PNG_WIDTH (4096 * 4)
-#define MAX_PNG_DEPTH (4)
-
-// Filter values
-
-#define PNG_FILTER_VALUE_NONE   0
-#define PNG_FILTER_VALUE_SUB    1
-#define PNG_FILTER_VALUE_UP             2
-#define PNG_FILTER_VALUE_AVG    3
-#define PNG_FILTER_VALUE_PAETH  4
-#define PNG_FILTER_NUM                  5
-
-// Filter a row of data
-
-void PNG_Filter (byte *out, byte filter, const byte *in, const byte *lastline, ulong rowbytes, ulong bpp)
-{
-	ulong		i;
-
-	switch(filter)
-	{
-	case PNG_FILTER_VALUE_NONE:
-		memcpy(out, in, rowbytes);
-		break;
-	case PNG_FILTER_VALUE_SUB:
-		for(i = 0; i < bpp; i++)
-		{
-			*out++ = *in++;
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			*out++ = *in - *(in - bpp);
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_UP:
-		for(i = 0; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		break;
-	case PNG_FILTER_VALUE_AVG:
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - (*lastline++ >> 1);
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in - ((*lastline++ + *(in - bpp)) >> 1);
-			}
-			else
-			{
-				*out++ = *in - (*(in - bpp) >> 1);
-			}
-			in++;
-		}
-		break;
-	case PNG_FILTER_VALUE_PAETH: {
-		int			a, b, c;
-		int			pa, pb, pc, p;
-
-		for(i = 0; i < bpp; i++)
-		{
-			if(lastline)
-			{
-				*out++ = *in++ - *lastline++;
-			}
-			else
-			{
-				*out++ = *in++;
-			}
-		}
-		for(i = bpp; i < rowbytes; i++)
-		{
-			a = *(in - bpp);
-			c = 0;
-			b = 0;
-			if(lastline)
-			{
-				c = *(lastline - bpp);
-				b = *lastline++;
-			}
-
-			p = b - c;
-			pc = a - c;
-
-			pa = p < 0 ? -p : p;
-			pb = pc < 0 ? -pc : pc;
-			pc = (p + pc) < 0 ? -(p + pc) : p + pc;
-
-			p = (pa <= pb && pa <= pc) ? a : (pb <= pc) ? b : c;
-
-			*out++ = *in++ - p;
-		}
-		break;
-	}
-	}
-}
-
-qboolean PNG_Pack (byte *out, ulong *size, ulong maxsize, byte *data, int width, int height, int bytedepth)
-{
-	z_stream		zdata;
-	ulong			rowbytes;
-	ulong			y;
-	const byte		*lastline, *source;
-	// Storage for filter type and filtered row
-	byte			workline[(MAX_PNG_WIDTH * MAX_PNG_DEPTH) + 1];
-	int zlibCompression;
-
-	switch (r_pngZlibCompression->integer) {
-	case 0:
-		zlibCompression = Z_NO_COMPRESSION;
-		break;
-	case 1:
-		zlibCompression = Z_BEST_SPEED;
-		break;
-	case 9:
-		zlibCompression = Z_BEST_COMPRESSION;
-		break;
-	default:
-		zlibCompression = Z_DEFAULT_COMPRESSION;
-		break;
-	}
-
-	// Number of bytes per row
-	rowbytes = width * bytedepth;
-
-	memset(&zdata, 0, sizeof(z_stream));
-	if (deflateInit(&zdata, zlibCompression) != Z_OK) {
-		//png_error = PNG_ERROR_COMP;
-		ri.Printf(PRINT_ALL, "^1couldn't initialize zlib\n");
-		return qfalse;
-	}
-
-	zdata.next_out = out;
-	zdata.avail_out = maxsize;
-
-	lastline = NULL;
-	source = data + ((height - 1) * rowbytes);
-	for (y = 0;  y < height;  y++) {
-		// Refilter using the most compressable filter algo
-		// Assume paeth to speed things up
-		workline[0] = (byte)PNG_FILTER_VALUE_PAETH;
-		PNG_Filter(workline + 1, (byte)PNG_FILTER_VALUE_PAETH, source, lastline, rowbytes, bytedepth);
-
-		zdata.next_in = workline;
-		zdata.avail_in = rowbytes + 1;
-		if (deflate(&zdata, Z_SYNC_FLUSH) != Z_OK) {
-			ri.Printf(PRINT_ALL, "^1couldn't refilter data\n");
-			deflateEnd(&zdata);
-			//png_error = PNG_ERROR_COMP;
-			return qfalse;
-		}
-		lastline = source;
-		source -= rowbytes;
-	}
-	if (deflate(&zdata, Z_FINISH) != Z_STREAM_END) {
-		ri.Printf(PRINT_ALL, "^1couldn't finish data\n");
-		//png_error = PNG_ERROR_COMP;
-		return qfalse;
-	}
-	*size = zdata.total_out;
-	deflateEnd(&zdata);
-	return qtrue;
-}
-
-// Saves a PNG format compressed image
-
-//FIXME  PNG_ChunkType_*
-
-#if 0
-#define PNG_IHDR 'IHDR'
-#define PNG_IDAT                'IDAT'
-#define PNG_IEND                'IEND'
-#define PNG_tEXt                'tEXt'
-#endif
-
-qboolean SavePNG (const char *name, byte *data, int width, int height, int bytedepth)
-{
-	byte *work;
-	fileHandle_t fp;
-	int maxsize;
-	ulong size, outcount;
-	struct PNG_Chunk_IHDR header;
-
-	//png_error = PNG_ERROR_OK;
-
-	fp = ri.FS_FOpenFileWrite(name);
-	if (!fp) {
-		ri.Printf(PRINT_ALL, "^1couldn't open png file for saving: '%s'\n", name);
-		//png_error = PNG_ERROR_CREATE_FAIL;
-		return qfalse;
-	}
-	// Write out the PNG signature
-	outcount = ri.FS_Write(PNG_Signature, strlen(PNG_Signature), fp);
-	if (outcount != strlen(PNG_Signature)) {
-		ri.FS_FCloseFile(fp);
-		ri.Printf(PRINT_ALL, "^1couldn't write png signature\n");
-		//png_error = PNG_ERROR_WRITE;
-		return qfalse;
-	}
-	// Create and output a valid header
-	//PNG_CreateHeader(&png_header, width, height, bytedepth);
-	header.Width = BigLong(width);
-	header.Height = BigLong(height);
-	header.BitDepth = 8;
-	// rgb is 2?  rgba is 6?
-	if (bytedepth == 3) {
-		header.ColourType = 2;
-	}
-	if (bytedepth == 4) {
-		header.ColourType = 6;
-	}
-
-	header.CompressionMethod = 0;  // compression type will be included in scanlines
-	header.FilterMethod = 0;
-	header.InterlaceMethod = 0;
-
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IHDR, (byte *)&header, PNG_Chunk_IHDR_Size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write png header\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	//ri.Printf(PRINT_ALL, "^2test done width: %lu   height: %lu\n", header.Width, header.Height);
-	//ri.FS_FCloseFile(fp);
-	//return qtrue;
-
-#if 0
-	// Create and output the copyright info
- 	if(!PNG_OutputChunk(fp, PNG_ChunkType_TEXT, (byte *)png_copyright, sizeof(png_copyright))) {
-		ri.Printf(PRINT_ALL, "^1couldn't write copyright info\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-#endif
-
-	// Max size of compressed image (source size + 0.1% + 12)
-	maxsize = (width * height * bytedepth) + 4096;
-	work = (byte *)ri.Malloc(maxsize);
-
-	if (!work) {
-		ri.Printf(PRINT_ALL, "^1error: couldn't allocate buffer for png saving\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-
-	// Pack up the image data
-	if (!PNG_Pack(work, &size, maxsize, data, width, height, bytedepth)) {
-		ri.Printf(PRINT_ALL, "^1couldn't pack png image data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	// Write out the compressed image data
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IDAT, (byte *)work, size)) {
-		ri.Printf(PRINT_ALL, "^1couldn't write compressed data\n");
-		ri.Free(work);
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.Free(work);
-	// Output terminating chunk
-	if(!PNG_OutputChunk(fp, PNG_ChunkType_IEND, NULL, 0)) {
-		ri.Printf(PRINT_ALL, "^1couldn't ouptut terminating marker\n");
-		ri.FS_FCloseFile(fp);
-		return qfalse;
-	}
-	ri.FS_FCloseFile(fp);
-	return qtrue;
-}

```
