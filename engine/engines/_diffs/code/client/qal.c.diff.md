# Diff: `code/client/qal.c`
**Canonical:** `wolfcamql-src` (sha256 `7a70a7017a59...`, 9884 bytes)

## Variants

### `ioquake3`  — sha256 `16ed797a4807...`, 9878 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\qal.c	2026-04-16 20:02:25.175378100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\qal.c	2026-04-16 20:02:21.530570000 +0100
@@ -116,7 +116,7 @@
 GPA
 =================
 */
-static void *GPA(const char *str)
+static void *GPA(char *str)
 {
 	void *rv;
 

```

### `openarena-engine`  — sha256 `f0e4b5a9e820...`, 9893 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\qal.c	2026-04-16 20:02:25.175378100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\qal.c	2026-04-16 22:48:25.734378800 +0100
@@ -83,7 +83,7 @@
 LPALGETBUFFERF qalGetBufferf;
 LPALGETBUFFERI qalGetBufferi;
 LPALDOPPLERFACTOR qalDopplerFactor;
-LPALSPEEDOFSOUND qalSpeedOfSound;
+LPALDOPPLERVELOCITY qalDopplerVelocity;
 LPALDISTANCEMODEL qalDistanceModel;
 
 LPALCCREATECONTEXT qalcCreateContext;
@@ -116,7 +116,7 @@
 GPA
 =================
 */
-static void *GPA(const char *str)
+static void *GPA(char *str)
 {
 	void *rv;
 
@@ -201,7 +201,7 @@
 	qalGetBufferf = GPA("alGetBufferf");
 	qalGetBufferi = GPA("alGetBufferi");
 	qalDopplerFactor = GPA("alDopplerFactor");
-	qalSpeedOfSound = GPA("alSpeedOfSound");
+	qalDopplerVelocity = GPA("alDopplerVelocity");
 	qalDistanceModel = GPA("alDistanceModel");
 
 	qalcCreateContext = GPA("alcCreateContext");
@@ -300,7 +300,7 @@
 	qalGetBufferf = NULL;
 	qalGetBufferi = NULL;
 	qalDopplerFactor = NULL;
-	qalSpeedOfSound = NULL;
+	qalDopplerVelocity = NULL;
 	qalDistanceModel = NULL;
 
 	qalcCreateContext = NULL;

```
