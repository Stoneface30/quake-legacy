# Diff: `code/splines/math_vector.cpp`
**Canonical:** `wolfcamql-src` (sha256 `8a7bab00bf1b...`, 3223 bytes)

## Variants

### `quake3-source`  — sha256 `64bf0f3ee608...`, 3204 bytes

_Diff stat: +3 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\math_vector.cpp	2026-04-16 20:02:25.272780200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\math_vector.cpp	2026-04-16 20:02:19.980636700 +0100
@@ -30,9 +30,7 @@
 #include <time.h>
 #include <ctype.h>
 
-#ifndef M_PI
 #define M_PI		3.14159265358979323846	// matches value in gcc v2 math.h
-#endif
 
 #define LERP_DELTA 1e-6
 
@@ -42,7 +40,7 @@
 
 float idVec3_t::toYaw( void ) {
 	float yaw;
-
+	
 	if ( ( y == 0 ) && ( x == 0 ) ) {
 		yaw = 0;
 	} else {
@@ -58,7 +56,7 @@
 float idVec3_t::toPitch( void ) {
 	float	forward;
 	float	pitch;
-
+	
 	if ( ( x == 0 ) && ( y == 0 ) ) {
 		if ( z > 0 ) {
 			pitch = 90;
@@ -81,7 +79,7 @@
 	float forward;
 	float yaw;
 	float pitch;
-
+	
 	if ( ( x == 0 ) && ( y == 0 ) ) {
 		yaw = 0;
 		if ( z > 0 ) {

```
