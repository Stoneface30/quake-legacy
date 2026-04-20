# Diff: `code/splines/math_matrix.h`
**Canonical:** `wolfcamql-src` (sha256 `9b9655e54f8c...`, 8345 bytes)

## Variants

### `quake3-source`  — sha256 `646a8ed8a983...`, 8108 bytes

_Diff stat: +1 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\splines\math_matrix.h	2026-04-16 20:02:25.272780200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\splines\math_matrix.h	2026-04-16 20:02:19.980636700 +0100
@@ -84,17 +84,7 @@
 }
 
 ID_INLINE mat3_t::mat3_t( float src[ 3 ][ 3 ] ) {
-	mat[ 0 ].x = src[ 0 ][ 0 ];
-	mat[ 0 ].y = src[ 0 ][ 1 ];
-	mat[ 0 ].z = src[ 0 ][ 2 ];
-
-	mat[ 1 ].x = src[ 1 ][ 0 ];
-	mat[ 1 ].y = src[ 1 ][ 1 ];
-	mat[ 1 ].z = src[ 1 ][ 2 ];
-
-	mat[ 2 ].x = src[ 2 ][ 0 ];
-	mat[ 2 ].y = src[ 2 ][ 1 ];
-	mat[ 2 ].x = src[ 2 ][ 2 ];
+	memcpy( mat, src, sizeof( src ) );
 }
 
 ID_INLINE mat3_t::mat3_t( idVec3_t const &x, idVec3_t const &y, idVec3_t const &z ) {

```
