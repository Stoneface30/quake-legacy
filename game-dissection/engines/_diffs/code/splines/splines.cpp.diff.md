# Diff: `code/splines/splines.cpp`
**Canonical:** `wolfcamql-src` (sha256 `1305c19922d4...`, 31475 bytes)

## Variants

### `quake3-source`  — sha256 `59727160366c...`, 30958 bytes

_Diff stat: +10 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\splines.cpp	2026-04-16 20:02:25.274288200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\splines.cpp	2026-04-16 20:02:19.982634200 +0100
@@ -30,7 +30,7 @@
 int FS_Write( const void *buffer, int len, fileHandle_t h );
 int FS_ReadFile( const char *qpath, void **buffer );
 void FS_FreeFile( void *buffer );
-fileHandle_t FS_FOpenFileWrite_HomeData( const char *filename );
+fileHandle_t FS_FOpenFileWrite( const char *filename );
 void FS_FCloseFile( fileHandle_t f );
 }
 
@@ -182,12 +182,7 @@
 void idSplineList::buildSpline() {
 	//int start = Sys_Milliseconds();
 	clearSpline();
-        for (int i = 2;  i < 3;  i++) {
-          //Com_Printf("control point (%d): %f %f %f\n", i, controlPoints[i]->x, controlPoints[i]->y, controlPoints[i]->z);
-        }
-
 	for(int i = 3; i < controlPoints.Num(); i++) {
-          Com_Printf("control point (%d): %f %f %f\n", i, controlPoints[i]->x, controlPoints[i]->y, controlPoints[i]->z);
 		for (float tension = 0.0f; tension < 1.001f; tension += granularity) {
 			float x = 0;
 			float y = 0;
@@ -198,7 +193,6 @@
 				z += controlPoints[i - (3 - j)]->z * calcSpline(j, tension);
 			}
 			splinePoints.Append(new idVec3_t(x, y, z));
-                        Com_Printf("    pt %f %f %f\n", x, y, z);
 		}
 	}
 	dirty = false;
@@ -361,7 +355,7 @@
 		return &zero;
 	}
 
-	//Com_Printf("Time: %d\n", t);
+	Com_Printf("Time: %d\n", t);
 	assert(splineTime.Num() == splinePoints.Num());
 
 	while (activeSegment < count) {
@@ -435,7 +429,7 @@
 }
 
 void idSplineList::write(fileHandle_t file, const char *p) {
-        idStr s = va("\t\t%s {\n", p);
+	idStr s = va("\t\t%s {\n", p);
 	FS_Write(s.c_str(), s.length(), file);
 	//s = va("\t\tname %s\n", name.c_str());
 	//FS_Write(s.c_str(), s.length(), file);
@@ -655,7 +649,6 @@
 	//for (int i = 0; i < targetPositions.Num(); i++) {
 	//	targetPositions[i]->
 	//}
-        fov.start(t);
 	startTime = t;
 	cameraRunning = true;
 }
@@ -733,7 +726,6 @@
 	char *buf;
 	const char *buf_p;
 	//int length = 
-
   FS_ReadFile( filename, (void **)&buf );
 	if ( !buf ) {
 		return qfalse;
@@ -750,7 +742,7 @@
 }
 
 void idCameraDef::save(const char *filename) {
-	fileHandle_t file = FS_FOpenFileWrite_HomeData(filename);
+	fileHandle_t file = FS_FOpenFileWrite(filename);
 	if (file) {
 		int i;
 		idStr s = "cameraPathDef { \n"; 
@@ -1018,8 +1010,7 @@
 			Com_UngetToken();
 			idStr key = Com_ParseOnLine(text);
 			
-			//const char *token = Com_Parse(text);
-			Com_Parse(text);
+			const char *token = Com_Parse(text);
 			if (Q_stricmp(key.c_str(), "pos") == 0) {
 				Com_UngetToken();
 				Com_Parse1DMatrix( text, 3, pos );
@@ -1064,8 +1055,7 @@
 			Com_UngetToken();
 			idStr key = Com_ParseOnLine(text);
 			
-			//const char *token = Com_Parse(text);
-			Com_Parse(text);
+			const char *token = Com_Parse(text);
 			if (Q_stricmp(key.c_str(), "startPos") == 0) {
 				Com_UngetToken();
 				Com_Parse1DMatrix( text, 3, startPos );
@@ -1114,8 +1104,7 @@
 			Com_UngetToken();
 			idStr key = Com_ParseOnLine(text);
 			
-			//const char *token = Com_Parse(text);
-			Com_Parse(text);
+			const char *token = Com_Parse(text);
 			if (Q_stricmp(key.c_str(), "target") == 0) {
 				target.parse(text);
 			} else {
@@ -1235,13 +1224,13 @@
   return static_cast<qboolean>(camera.load(name));
 }
 
-  qboolean getCameraInfo(int time, float *origin, float*angles, float *fov) {
+qboolean getCameraInfo(int time, float *origin, float*angles) {
 	idVec3_t dir, org;
 	org[0] = origin[0];
 	org[1] = origin[1];
 	org[2] = origin[2];
-	//float fov = 90;
-	if (camera.getCameraInfo(time, org, dir, fov)) {  //&fov)) {
+	float fov = 90;
+	if (camera.getCameraInfo(time, org, dir, &fov)) {
 		origin[0] = org[0];
 		origin[1] = org[1];
 		origin[2] = org[2];

```
