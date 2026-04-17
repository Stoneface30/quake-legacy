# Diff: `code/sys/sys_loadlib.h`
**Canonical:** `wolfcamql-src` (sha256 `ff5c7ab1c6e8...`, 2090 bytes)

## Variants

### `ioquake3`  — sha256 `d40a51efe1a4...`, 1918 bytes

_Diff stat: +0 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_loadlib.h	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sys\sys_loadlib.h	2026-04-16 20:02:21.622757900 +0100
@@ -28,9 +28,6 @@
 #		define Sys_LoadFunction(h,fn) (void*)GetProcAddress((HMODULE)h,fn)
 #		define Sys_LibraryError() "unknown"
 #	else
-#	ifndef _GNU_SOURCE  // wolfcam Linux backtracing
-#   	define _GNU_SOURCE
-#	endif
 #	include <dlfcn.h>
 #		define Sys_LoadLibrary(f) dlopen(f,RTLD_NOW)
 #		define Sys_UnloadLibrary(h) dlclose(h)
@@ -38,9 +35,6 @@
 #		define Sys_LibraryError() dlerror()
 #	endif
 #else
-#	ifndef _GNU_SOURCE  // wolfcam Linux backtracing
-#   	define _GNU_SOURCE
-#	endif
 #	ifdef USE_INTERNAL_SDL_HEADERS
 #		include "SDL.h"
 #		include "SDL_loadso.h"

```

### `openarena-engine`  — sha256 `ff6cf4e51624...`, 1911 bytes

_Diff stat: +1 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sys\sys_loadlib.h	2026-04-16 20:02:25.277294400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\sys\sys_loadlib.h	2026-04-16 22:48:25.939962600 +0100
@@ -28,9 +28,6 @@
 #		define Sys_LoadFunction(h,fn) (void*)GetProcAddress((HMODULE)h,fn)
 #		define Sys_LibraryError() "unknown"
 #	else
-#	ifndef _GNU_SOURCE  // wolfcam Linux backtracing
-#   	define _GNU_SOURCE
-#	endif
 #	include <dlfcn.h>
 #		define Sys_LoadLibrary(f) dlopen(f,RTLD_NOW)
 #		define Sys_UnloadLibrary(h) dlclose(h)
@@ -38,10 +35,7 @@
 #		define Sys_LibraryError() dlerror()
 #	endif
 #else
-#	ifndef _GNU_SOURCE  // wolfcam Linux backtracing
-#   	define _GNU_SOURCE
-#	endif
-#	ifdef USE_INTERNAL_SDL_HEADERS
+#	ifdef USE_LOCAL_HEADERS
 #		include "SDL.h"
 #		include "SDL_loadso.h"
 #	else

```
