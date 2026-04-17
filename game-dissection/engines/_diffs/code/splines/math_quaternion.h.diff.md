# Diff: `code/splines/math_quaternion.h`
**Canonical:** `wolfcamql-src` (sha256 `21444679fbbf...`, 4442 bytes)

## Variants

### `quake3-source`  — sha256 `50e8a1dee1fe...`, 4357 bytes

_Diff stat: +1 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\math_quaternion.h	2026-04-16 20:02:25.272780200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\math_quaternion.h	2026-04-16 20:02:19.980636700 +0100
@@ -157,8 +157,7 @@
 }
 
 inline int operator!=( quat_t a, quat_t b ) {
-	//return ( ( a.x != b.x ) || ( a.y != b.y ) || ( a.z != b.z ) && ( a.w != b.w ) );
-	return ( ( a.x != b.x ) || ( a.y != b.y ) || ( a.z != b.z ) || ( a.w != b.w ) );
+	return ( ( a.x != b.x ) || ( a.y != b.y ) || ( a.z != b.z ) && ( a.w != b.w ) );
 }
 
 inline float quat_t::Length( void ) {

```
