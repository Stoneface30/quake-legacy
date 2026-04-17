# Diff: `code/client/cl_curl.h`
**Canonical:** `wolfcamql-src` (sha256 `9daa2951c060...`, 3744 bytes)

## Variants

### `quake3e`  — sha256 `b023932fcbff...`, 4930 bytes

_Diff stat: +50 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_curl.h	2026-04-16 20:02:25.169218800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\cl_curl.h	2026-04-16 20:02:26.910506600 +0100
@@ -24,28 +24,27 @@
 #ifndef __QCURL_H__
 #define __QCURL_H__
 
-#include "../qcommon/q_shared.h"
-#include "../qcommon/qcommon.h"
-
 #ifdef USE_LOCAL_HEADERS
-  #include "../curl-8.15.0/include/curl/curl.h"
+#include "curl/curl.h"
 #else
-  #include <curl/curl.h>
+#include <curl/curl.h>
 #endif
 
-#ifdef USE_CURL_DLOPEN
-#ifdef WIN32
-  #define DEFAULT_CURL_LIB "libcurl-4.dll"
-  #define ALTERNATE_CURL_LIB "libcurl-3.dll"
+#include "../qcommon/q_shared.h"
+#include "../qcommon/qcommon.h"
+
+#ifdef _WIN32
+#define DEFAULT_CURL_LIB "libcurl-3.dll"
 #elif defined(__APPLE__)
-  #define DEFAULT_CURL_LIB "libcurl.dylib"
+#define DEFAULT_CURL_LIB "libcurl.dylib"
 #else
-  #define DEFAULT_CURL_LIB "libcurl.so.4"
-  #define ALTERNATE_CURL_LIB "libcurl.so.3"
+#define DEFAULT_CURL_LIB "libcurl.so.4"
+#define ALTERNATE_CURL_LIB "libcurl.so.3"
 #endif
 
 extern cvar_t *cl_cURLLib;
 
+#ifdef USE_CURL_DLOPEN
 extern char* (*qcurl_version)(void);
 
 extern CURL* (*qcurl_easy_init)(void);
@@ -99,4 +98,43 @@
 void CL_cURL_BeginDownload( const char *localName, const char *remoteURL );
 void CL_cURL_PerformDownload( void );
 void CL_cURL_Cleanup( void );
+
+typedef struct download_s {
+	char		URL[MAX_OSPATH];
+	char		Name[MAX_OSPATH];
+	char		gameDir[MAX_OSPATH];
+	char		TempName[MAX_OSPATH*2 + 14]; // gameDir + PATH_SEP + Name + ".00000000.tmp"
+	char		progress[MAX_OSPATH+64];
+	CURL		*cURL;
+	CURLM		*cURLM;
+	fileHandle_t fHandle;
+	int			Size;
+	int			Count;
+	qboolean	headerCheck;
+	qboolean	mapAutoDownload;
+
+	struct func_s {
+		char*		(*version)(void);
+		char *		(*easy_escape)(CURL *curl, const char *string, int length);
+		void		(*free)(char *ptr);
+
+		CURL*		(*easy_init)(void);
+		CURLcode	(*easy_setopt)(CURL *curl, CURLoption option, ...);
+		CURLcode	(*easy_perform)(CURL *curl);
+		void		(*easy_cleanup)(CURL *curl);
+		CURLcode	(*easy_getinfo)(CURL *curl, CURLINFO info, ...);
+		const char *(*easy_strerror)(CURLcode);
+
+		CURLM*		(*multi_init)(void);
+		CURLMcode	(*multi_add_handle)(CURLM *multi_handle, CURL *curl_handle);
+		CURLMcode	(*multi_remove_handle)(CURLM *multi_handle, CURL *curl_handle);
+		CURLMcode	(*multi_perform)(CURLM *multi_handle, int *running_handles);
+		CURLMcode	(*multi_cleanup)(CURLM *multi_handle);
+		CURLMsg		*(*multi_info_read)(CURLM *multi_handle, int *msgs_in_queue);
+		const char	*(*multi_strerror)(CURLMcode);
+
+		void		*lib;
+	} func;
+} download_t;
+
 #endif	// __QCURL_H__

```

### `openarena-engine`  — sha256 `56460f1a23f9...`, 3737 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_curl.h	2026-04-16 20:02:25.169218800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_curl.h	2026-04-16 22:48:25.730201700 +0100
@@ -28,7 +28,7 @@
 #include "../qcommon/qcommon.h"
 
 #ifdef USE_LOCAL_HEADERS
-  #include "../curl-8.15.0/include/curl/curl.h"
+  #include "../libcurl-7.35.0/curl/curl.h"
 #else
   #include <curl/curl.h>
 #endif
@@ -37,7 +37,7 @@
 #ifdef WIN32
   #define DEFAULT_CURL_LIB "libcurl-4.dll"
   #define ALTERNATE_CURL_LIB "libcurl-3.dll"
-#elif defined(__APPLE__)
+#elif defined(MACOS_X)
   #define DEFAULT_CURL_LIB "libcurl.dylib"
 #else
   #define DEFAULT_CURL_LIB "libcurl.so.4"

```
