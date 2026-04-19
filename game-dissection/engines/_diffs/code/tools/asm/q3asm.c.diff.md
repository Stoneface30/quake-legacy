# Diff: `code/tools/asm/q3asm.c`
**Canonical:** `wolfcamql-src` (sha256 `39f43733932b...`, 36168 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `6166c3aeed8a...`, 36129 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\q3asm.c	2026-04-16 20:02:25.761112800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\asm\q3asm.c	2026-04-16 22:48:25.943075700 +0100
@@ -477,7 +477,7 @@
     acc = (acc << 2) | (acc >> 30);
     acc &= 0xffffffffU;
     }
-    return acc;
+    return abs(acc);
 }
 
 
@@ -546,7 +546,7 @@
 
 	// add the file prefix to local symbols to guarantee unique
 	if ( sym[0] == '$' ) {
-		snprintf( expanded, sizeof(expanded), "%s_%i", sym, currentFileIndex );
+		sprintf( expanded, "%s_%i", sym, currentFileIndex );
 		sym = expanded;
 	}
 
@@ -592,7 +592,7 @@
 */
 static int LookupSymbol( char *sym ) {
 	symbol_t	*s;
-	char		expanded[MAX_LINE_LENGTH * 2];
+	char		expanded[MAX_LINE_LENGTH];
 	int			hash;
 	hashchain_t *hc;
 
@@ -602,7 +602,7 @@
 
 	// add the file prefix to local symbols to guarantee unique
 	if ( sym[0] == '$' ) {
-		snprintf( expanded, sizeof(expanded), "%s_%i", sym, currentFileIndex );
+		sprintf( expanded, "%s_%i", sym, currentFileIndex );
 		sym = expanded;
 	}
 
@@ -788,7 +788,7 @@
 
 BIG HACK: I want to put all 32 bit values in the data
 segment so they can be byte swapped, and all char data in the lit
-segment, but switch jump tables are emitted in the lit segment and
+segment, but switch jump tables are emited in the lit segment and
 initialized strng variables are put in the data segment.
 
 I can change segments here, but I also need to fixup the
@@ -1129,7 +1129,7 @@
 	return 0;
 }
 
-	// code labels are emitted as instruction counts, not byte offsets,
+	// code labels are emited as instruction counts, not byte offsets,
 	// because the physical size of the code will change with
 	// different run time compilers and we want to minimize the
 	// size of the required translation table
@@ -1564,7 +1564,7 @@
 
 		if ( !strcmp( argv[i], "-o" ) ) {
 			if ( i == argc - 1 ) {
-				Error( "-o must precede a filename" );
+				Error( "-o must preceed a filename" );
 			}
 /* Timbo of Tremulous pointed out -o not working; stock ID q3asm folded in the change. Yay. */
 			strcpy( outputFilename, argv[ i+1 ] );
@@ -1574,7 +1574,7 @@
 
 		if ( !strcmp( argv[i], "-f" ) ) {
 			if ( i == argc - 1 ) {
-				Error( "-f must precede a filename" );
+				Error( "-f must preceed a filename" );
 			}
 			ParseOptionFile( argv[ i+1 ] );
 			i++;

```

### `openarena-gamecode`  — sha256 `bbc6d8f324bb...`, 36062 bytes

_Diff stat: +22 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\q3asm.c	2026-04-16 20:02:25.761112800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\asm\q3asm.c	2026-04-16 22:48:24.198009300 +0100
@@ -250,6 +250,7 @@
 {
   H->buckets = buckets;
   H->table = calloc(H->buckets, sizeof(*(H->table)));
+  return;
 }
 
 static hashtable_t *hashtable_new (int buckets)
@@ -284,6 +285,7 @@
     }
   hc->data = datum;
   hc->next = 0;
+  return;
 }
 
 static hashchain_t *hashtable_get (hashtable_t *H, int hashvalue)
@@ -384,12 +386,8 @@
   symbol_t *s;
   symbol_t **symlist;
 
-  if(!symbols)
-  	return;
-
 //crumb("sort_symbols: Constructing symlist array\n");
   for (elems = 0, s = symbols; s; s = s->next, elems++) /* nop */ ;
-
   symlist = malloc(elems * sizeof(symbol_t*));
   for (i = 0, s = symbols; s; s = s->next, i++)
     {
@@ -477,7 +475,7 @@
     acc = (acc << 2) | (acc >> 30);
     acc &= 0xffffffffU;
     }
-    return acc;
+    return abs(acc);
 }
 
 
@@ -491,10 +489,10 @@
 
 	errorCount++;
 
-	fprintf( stderr, "%s:%i ", currentFileName, currentFileLine );
+	report( "%s:%i ", currentFileName, currentFileLine );
 
 	va_start( argptr,fmt );
-	vfprintf( stderr, fmt, argptr );
+	vprintf( fmt,argptr );
 	va_end( argptr );
 }
 
@@ -546,7 +544,7 @@
 
 	// add the file prefix to local symbols to guarantee unique
 	if ( sym[0] == '$' ) {
-		snprintf( expanded, sizeof(expanded), "%s_%i", sym, currentFileIndex );
+		sprintf( expanded, "%s_%i", sym, currentFileIndex );
 		sym = expanded;
 	}
 
@@ -592,7 +590,7 @@
 */
 static int LookupSymbol( char *sym ) {
 	symbol_t	*s;
-	char		expanded[MAX_LINE_LENGTH * 2];
+	char		expanded[MAX_LINE_LENGTH];
 	int			hash;
 	hashchain_t *hc;
 
@@ -602,7 +600,7 @@
 
 	// add the file prefix to local symbols to guarantee unique
 	if ( sym[0] == '$' ) {
-		snprintf( expanded, sizeof(expanded), "%s_%i", sym, currentFileIndex );
+		sprintf( expanded, "%s_%i", sym, currentFileIndex );
 		sym = expanded;
 	}
 
@@ -689,7 +687,9 @@
 	*token = 0;  /* Clear token. */
 
 	// skip whitespace
-	for (p = lineBuffer + lineParseOffset; *p && (*p <= ' '); p++) /* nop */ ;
+	for (p = lineBuffer + lineParseOffset; *p && (*p <= ' '); p++) {
+		/* nop */ 
+	}
 
 	// skip ; comments
 	/* die on end-of-string */
@@ -788,7 +788,7 @@
 
 BIG HACK: I want to put all 32 bit values in the data
 segment so they can be byte swapped, and all char data in the lit
-segment, but switch jump tables are emitted in the lit segment and
+segment, but switch jump tables are emited in the lit segment and
 initialized strng variables are put in the data segment.
 
 I can change segments here, but I also need to fixup the
@@ -1129,7 +1129,7 @@
 	return 0;
 }
 
-	// code labels are emitted as instruction counts, not byte offsets,
+	// code labels are emited as instruction counts, not byte offsets,
 	// because the physical size of the code will change with
 	// different run time compilers and we want to minimize the
 	// size of the required translation table
@@ -1521,13 +1521,12 @@
 	Error("Usage: %s [OPTION]... [FILES]...\n\
 Assemble LCC bytecode assembly to Q3VM bytecode.\n\
 \n\
-  -o OUTPUT      Write assembled output to file OUTPUT.qvm\n\
-  -f LISTFILE    Read options and list of files to assemble from LISTFILE.q3asm\n\
-  -b BUCKETS     Set symbol hash table to BUCKETS buckets\n\
-  -m             Generate a mapfile for each OUTPUT.qvm\n\
-  -v             Verbose compilation report\n\
-  -vq3           Produce a qvm file compatible with Q3 1.32b\n\
-  -h --help -?   Show this help\n\
+    -o OUTPUT      Write assembled output to file OUTPUT.qvm\n\
+    -f LISTFILE    Read options and list of files to assemble from LISTFILE.q3asm\n\
+    -b BUCKETS     Set symbol hash table to BUCKETS buckets\n\
+    -v             Verbose compilation report\n\
+    -vq3           Produce a qvm file compatible with Q3 1.32b\n\
+    -h --help -?   Show this help\n\
 ", argv0);
 }
 
@@ -1564,7 +1563,7 @@
 
 		if ( !strcmp( argv[i], "-o" ) ) {
 			if ( i == argc - 1 ) {
-				Error( "-o must precede a filename" );
+				Error( "-o must preceed a filename" );
 			}
 /* Timbo of Tremulous pointed out -o not working; stock ID q3asm folded in the change. Yay. */
 			strcpy( outputFilename, argv[ i+1 ] );
@@ -1574,7 +1573,7 @@
 
 		if ( !strcmp( argv[i], "-f" ) ) {
 			if ( i == argc - 1 ) {
-				Error( "-f must precede a filename" );
+				Error( "-f must preceed a filename" );
 			}
 			ParseOptionFile( argv[ i+1 ] );
 			i++;
@@ -1620,7 +1619,7 @@
 	}
 	// In some case it Segfault without this check
 	if ( numAsmFiles == 0 ) {
-		Error( "No file to assemble" );
+		Error( "No file to assemble\n" );
 	}
 
 	InitTables();

```
