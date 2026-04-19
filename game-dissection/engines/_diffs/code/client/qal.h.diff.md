# Diff: `code/client/qal.h`
**Canonical:** `wolfcamql-src` (sha256 `2dce1070e721...`, 9316 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `15af26690b37...`, 9342 bytes

_Diff stat: +6 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\qal.h	2026-04-16 20:02:25.175948600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\qal.h	2026-04-16 22:48:25.734378800 +0100
@@ -33,13 +33,12 @@
 #define ALC_NO_PROTOTYPES
 #endif
 
-#ifdef USE_INTERNAL_OPENAL_HEADERS
-#include "AL/al.h"
-#include "AL/alc.h"
+#ifdef USE_LOCAL_HEADERS
+#include "../AL/al.h"
+#include "../AL/alc.h"
 #else
-#if defined(_MSC_VER) || defined(__APPLE__)
+#ifdef _MSC_VER
   // MSVC users must install the OpenAL SDK which doesn't use the AL/*.h scheme.
-  // OSX framework also needs this
   #include <al.h>
   #include <alc.h>
 #else
@@ -126,6 +125,7 @@
 extern LPALGETBUFFER3I qalGetBuffer3i;
 extern LPALGETBUFFERIV qalGetBufferiv;
 extern LPALDOPPLERFACTOR qalDopplerFactor;
+extern LPALDOPPLERVELOCITY qalDopplerVelocity;
 extern LPALSPEEDOFSOUND qalSpeedOfSound;
 extern LPALDISTANCEMODEL qalDistanceModel;
 
@@ -220,6 +220,7 @@
 #define qalGetBuffer3i alGetBuffer3i
 #define qalGetBufferiv alGetBufferiv
 #define qalDopplerFactor alDopplerFactor
+#define qalDopplerVelocity alDopplerVelocity
 #define qalSpeedOfSound alSpeedOfSound
 #define qalDistanceModel alDistanceModel
 

```
