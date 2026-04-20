# Diff: `code/tools/asm/cmdlib.c`
**Canonical:** `wolfcamql-src` (sha256 `f3022c287652...`, 21573 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `e4edf40c79c1...`, 21480 bytes

_Diff stat: +11 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\cmdlib.c	2026-04-16 20:02:25.757603800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\asm\cmdlib.c	2026-04-16 22:48:25.942077400 +0100
@@ -65,7 +65,7 @@
 	struct _finddata_t fileinfo;
 	intptr_t	handle;
 	int		i;
-	char	filename[2048];
+	char	filename[1024];
 	char	filebase[1024];
 	char	*path;
 
@@ -88,7 +88,7 @@
 
 		do
 		{
-			snprintf (filename, sizeof(filename), "%s%s", filebase, fileinfo.name);
+			sprintf (filename, "%s%s", filebase, fileinfo.name);
 			ex_argv[ex_argc++] = copystring (filename);
 		} while (_findnext( handle, &fileinfo ) != -1);
 
@@ -126,7 +126,7 @@
 	vsprintf (text, error,argptr);
 	va_end (argptr);
 
-	snprintf (text2, sizeof(text2), "%s\nGetLastError() = %i", text, err);
+	sprintf (text2, "%s\nGetLastError() = %i", text, err);
     MessageBox(NULL, text2, "Error", 0 /* MB_OK */ );
 
 	exit (1);
@@ -318,7 +318,7 @@
 		strcpy( full, path );
 		return full;
 	}
-	snprintf (full, sizeof(full), "%s%s", qdir, path);
+	sprintf (full, "%s%s", qdir, path);
 	return full;
 }
 
@@ -331,20 +331,20 @@
 		strcpy( full, path );
 		return full;
 	}
-	snprintf (full, sizeof(full), "%s%s", gamedir, path);
+	sprintf (full, "%s%s", gamedir, path);
 	return full;
 }
 
 char *ExpandPathAndArchive (const char *path)
 {
 	char	*expanded;
-	char	archivename[2048];
+	char	archivename[1024];
 
 	expanded = ExpandPath (path);
 
 	if (archive)
 	{
-		snprintf (archivename, sizeof(archivename), "%s/%s", archivedir, path);
+		sprintf (archivename, "%s/%s", archivedir, path);
 		QCopyFile (expanded, archivename);
 	}
 	return expanded;
@@ -559,7 +559,7 @@
 }
 
 
-char *Q_strupr (char *start)
+char *strupr (char *start)
 {
 	char	*in;
 	in = start;
@@ -571,7 +571,7 @@
 	return start;
 }
 
-char *Q_strlower (char *start)
+char *strlower (char *start)
 {
 	char	*in;
 	in = start;
@@ -734,7 +734,7 @@
 ==============
 LoadFileBlock
 -
-rounds up memory allocation to 4K boundary
+rounds up memory allocation to 4K boundry
 -
 ==============
 */
@@ -810,7 +810,7 @@
 {
 	char    *src;
 //
-// if path doesn't have a .EXT, append extension
+// if path doesnt have a .EXT, append extension
 // (extension should include the .)
 //
 	src = path + strlen(path) - 1;

```

### `openarena-gamecode`  — sha256 `abe1d10c4963...`, 21376 bytes

_Diff stat: +17 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\asm\cmdlib.c	2026-04-16 20:02:25.757603800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\asm\cmdlib.c	2026-04-16 22:48:24.196008800 +0100
@@ -63,9 +63,9 @@
 void ExpandWildcards( int *argc, char ***argv )
 {
 	struct _finddata_t fileinfo;
-	intptr_t	handle;
+	int		handle;
 	int		i;
-	char	filename[2048];
+	char	filename[1024];
 	char	filebase[1024];
 	char	*path;
 
@@ -88,7 +88,7 @@
 
 		do
 		{
-			snprintf (filename, sizeof(filename), "%s%s", filebase, fileinfo.name);
+			sprintf (filename, "%s%s", filebase, fileinfo.name);
 			ex_argv[ex_argc++] = copystring (filename);
 		} while (_findnext( handle, &fileinfo ) != -1);
 
@@ -126,7 +126,7 @@
 	vsprintf (text, error,argptr);
 	va_end (argptr);
 
-	snprintf (text2, sizeof(text2), "%s\nGetLastError() = %i", text, err);
+	sprintf (text2, "%s\nGetLastError() = %i", text, err);
     MessageBox(NULL, text2, "Error", 0 /* MB_OK */ );
 
 	exit (1);
@@ -177,7 +177,7 @@
 
 void _printf( const char *format, ... ) {
 	va_list argptr;
-  char text[4096];
+	char text[4096];
 #ifdef WIN32
   ATOM a;
 #endif
@@ -185,7 +185,7 @@
 	vsprintf (text, format, argptr);
 	va_end (argptr);
 
-  printf("%s", text);
+	printf("%s", text);
 
 #ifdef WIN32
   if (!lookedForServer) {
@@ -318,7 +318,7 @@
 		strcpy( full, path );
 		return full;
 	}
-	snprintf (full, sizeof(full), "%s%s", qdir, path);
+	sprintf (full, "%s%s", qdir, path);
 	return full;
 }
 
@@ -331,20 +331,20 @@
 		strcpy( full, path );
 		return full;
 	}
-	snprintf (full, sizeof(full), "%s%s", gamedir, path);
+	sprintf (full, "%s%s", gamedir, path);
 	return full;
 }
 
 char *ExpandPathAndArchive (const char *path)
 {
 	char	*expanded;
-	char	archivename[2048];
+	char	archivename[1024];
 
 	expanded = ExpandPath (path);
 
 	if (archive)
 	{
-		snprintf (archivename, sizeof(archivename), "%s/%s", archivedir, path);
+		sprintf (archivename, "%s/%s", archivedir, path);
 		QCopyFile (expanded, archivename);
 	}
 	return expanded;
@@ -396,12 +396,10 @@
 	int i = 0;
 
 #ifdef WIN32
-   if (_getcwd (out, 256) == NULL)
-     strcpy(out, ".");  /* shrug */
+   _getcwd (out, 256);
    strcat (out, "\\");
 #else
-   if (getcwd (out, 256) == NULL)
-     strcpy(out, ".");  /* shrug */
+   getcwd (out, 256);
    strcat (out, "/");
 #endif
 
@@ -559,7 +557,7 @@
 }
 
 
-char *Q_strupr (char *start)
+char *strupr (char *start)
 {
 	char	*in;
 	in = start;
@@ -571,7 +569,7 @@
 	return start;
 }
 
-char *Q_strlower (char *start)
+char *strlower (char *start)
 {
 	char	*in;
 	in = start;
@@ -607,7 +605,7 @@
 
 	for (i = 1;i<myargc;i++)
 	{
-		if ( !Q_stricmp(check, myargv[i]) )
+		if ( Q_strequal(check, myargv[i]) )
 			return i;
 	}
 
@@ -734,7 +732,7 @@
 ==============
 LoadFileBlock
 -
-rounds up memory allocation to 4K boundary
+rounds up memory allocation to 4K boundry
 -
 ==============
 */
@@ -810,7 +808,7 @@
 {
 	char    *src;
 //
-// if path doesn't have a .EXT, append extension
+// if path doesnt have a .EXT, append extension
 // (extension should include the .)
 //
 	src = path + strlen(path) - 1;

```
