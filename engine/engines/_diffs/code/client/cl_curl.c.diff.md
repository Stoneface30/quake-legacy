# Diff: `code/client/cl_curl.c`
**Canonical:** `wolfcamql-src` (sha256 `067367afb236...`, 11300 bytes)

## Variants

### `quake3e`  — sha256 `b9bc6f18b831...`, 29926 bytes

_Diff stat: +826 / -46 lines_

_(full diff is 25684 bytes — see files directly)_

### `openarena-engine`  — sha256 `542c70010e22...`, 9784 bytes

_Diff stat: +24 / -67 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_curl.c	2026-04-16 20:02:25.169218800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_curl.c	2026-04-16 22:48:25.730201700 +0100
@@ -63,7 +63,7 @@
 GPA
 =================
 */
-static void *GPA(const char *str)
+static void *GPA(char *str)
 {
 	void *rv;
 
@@ -101,7 +101,7 @@
 		// On some linux distributions there is no libcurl.so.3, but only libcurl.so.4. That one works too.
 		if(!(cURLLib = Sys_LoadDll(ALTERNATE_CURL_LIB, qtrue)))
 #endif
-		return qfalse;
+			return qfalse;
 	}
 
 	clc.cURLEnabled = qtrue;
@@ -177,20 +177,12 @@
 void CL_cURL_Cleanup(void)
 {
 	if(clc.downloadCURLM) {
-		CURLMcode result;
-
 		if(clc.downloadCURL) {
-			result = qcurl_multi_remove_handle(clc.downloadCURLM,
+			qcurl_multi_remove_handle(clc.downloadCURLM,
 				clc.downloadCURL);
-			if(result != CURLM_OK) {
-				Com_DPrintf("qcurl_multi_remove_handle failed: %s\n", qcurl_multi_strerror(result));
-			}
 			qcurl_easy_cleanup(clc.downloadCURL);
 		}
-		result = qcurl_multi_cleanup(clc.downloadCURLM);
-		if(result != CURLM_OK) {
-			Com_DPrintf("CL_cURL_Cleanup: qcurl_multi_cleanup failed: %s\n", qcurl_multi_strerror(result));
-		}
+		qcurl_multi_cleanup(clc.downloadCURLM);
 		clc.downloadCURLM = NULL;
 		clc.downloadCURL = NULL;
 	}
@@ -200,8 +192,8 @@
 	}
 }
 
-static int CL_cURL_CallbackProgress(void *clientp, curl_off_t dltotal, curl_off_t dlnow,
-	curl_off_t ultotal, curl_off_t ulnow)
+static int CL_cURL_CallbackProgress( void *dummy, double dltotal, double dlnow,
+	double ultotal, double ulnow )
 {
 	clc.downloadSize = (int)dltotal;
 	Cvar_SetValue( "cl_downloadSize", clc.downloadSize );
@@ -210,43 +202,15 @@
 	return 0;
 }
 
-static size_t CL_cURL_CallbackWrite(const void *buffer, size_t size, size_t nmemb,
-	const void *stream)
+static size_t CL_cURL_CallbackWrite(void *buffer, size_t size, size_t nmemb,
+	void *stream)
 {
 	FS_Write( buffer, size*nmemb, ((fileHandle_t*)stream)[0] );
 	return size*nmemb;
 }
 
-CURLcode qcurl_easy_setopt_warn(CURL *curl, CURLoption option, ...)
-{
-	CURLcode result;
-
-	va_list argp;
-	va_start(argp, option);
-
-	if(option < CURLOPTTYPE_OBJECTPOINT) {
-		long longValue = va_arg(argp, long);
-		result = qcurl_easy_setopt(curl, option, longValue);
-	} else if(option < CURLOPTTYPE_OFF_T) {
-		void *pointerValue = va_arg(argp, void *);
-		result = qcurl_easy_setopt(curl, option, pointerValue);
-	} else {
-		curl_off_t offsetValue = va_arg(argp, curl_off_t);
-		result = qcurl_easy_setopt(curl, option, offsetValue);
-	}
-
-	if(result != CURLE_OK) {
-		Com_DPrintf("qcurl_easy_setopt failed: %s\n", qcurl_easy_strerror(result));
-	}
-	va_end(argp);
-
-	return result;
-}
-
 void CL_cURL_BeginDownload( const char *localName, const char *remoteURL )
 {
-	CURLMcode result;
-
 	clc.cURLUsed = qtrue;
 	Com_Printf("URL: %s\n", remoteURL);
 	Com_DPrintf("***** CL_cURL_BeginDownload *****\n"
@@ -280,27 +244,26 @@
 			"%s for writing", clc.downloadTempName);
 		return;
 	}
+
 	if(com_developer->integer)
-		qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_VERBOSE, 1);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_URL, clc.downloadURL);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_TRANSFERTEXT, 0);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_REFERER, va("ioQ3://%s",
+		qcurl_easy_setopt(clc.downloadCURL, CURLOPT_VERBOSE, 1);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_URL, clc.downloadURL);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_TRANSFERTEXT, 0);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_REFERER, va("ioQ3://%s",
 		NET_AdrToString(clc.serverAddress)));
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_USERAGENT, va("%s %s",
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_USERAGENT, va("%s %s",
 		Q3_VERSION, qcurl_version()));
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_WRITEFUNCTION,
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_WRITEFUNCTION,
 		CL_cURL_CallbackWrite);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_WRITEDATA, &clc.download);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_NOPROGRESS, 0);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_XFERINFOFUNCTION,
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_WRITEDATA, &clc.download);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_NOPROGRESS, 0);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_PROGRESSFUNCTION,
 		CL_cURL_CallbackProgress);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_PROGRESSDATA, NULL);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_FAILONERROR, 1);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_FOLLOWLOCATION, 1);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_MAXREDIRS, 5);
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_PROTOCOLS_STR, "http,https");
-	qcurl_easy_setopt_warn(clc.downloadCURL, CURLOPT_BUFFERSIZE, CURL_MAX_READ_SIZE);
-	clc.downloadCURLM = qcurl_multi_init();
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_PROGRESSDATA, NULL);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_FAILONERROR, 1);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_FOLLOWLOCATION, 1);
+	qcurl_easy_setopt(clc.downloadCURL, CURLOPT_MAXREDIRS, 5);
+	clc.downloadCURLM = qcurl_multi_init();	
 	if(!clc.downloadCURLM) {
 		qcurl_easy_cleanup(clc.downloadCURL);
 		clc.downloadCURL = NULL;
@@ -308,13 +271,7 @@
 			"failed");
 		return;
 	}
-	result = qcurl_multi_add_handle(clc.downloadCURLM, clc.downloadCURL);
-	if(result != CURLM_OK) {
-		qcurl_easy_cleanup(clc.downloadCURL);
-		clc.downloadCURL = NULL;
-		Com_Error(ERR_DROP,"CL_cURL_BeginDownload: qcurl_multi_add_handle() failed: %s", qcurl_multi_strerror(result));
-		return;
-	}
+	qcurl_multi_add_handle(clc.downloadCURLM, clc.downloadCURL);
 
 	if(!(clc.sv_allowDownload & DLF_NO_DISCONNECT) &&
 		!clc.cURLDisconnected) {

```
