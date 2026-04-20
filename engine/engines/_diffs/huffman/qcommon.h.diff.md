# Diff: `huffman/qcommon.h`
**Canonical:** `demodumper` (sha256 `6d26bf1038a4...`, 34456 bytes)

## Variants

### `qldemo-python`  — sha256 `a08d64ae7acf...`, 34476 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\huffman\qcommon.h	2026-04-16 20:02:27.597241300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\huffman\qcommon.h	2026-04-16 20:02:26.531757500 +0100
@@ -532,7 +532,7 @@
 
 #define BASEGAME "baseq3"
 
-qboolean FS_Initialized();
+qboolean FS_Initialized(void);
 
 void	FS_InitFilesystem (void);
 void	FS_Shutdown( qboolean closemfp );
@@ -550,7 +550,7 @@
 
 qboolean FS_FileExists( const char *file );
 
-int		FS_LoadStack();
+int		FS_LoadStack(void);
 
 int		FS_GetFileList(  const char *path, const char *extension, char *listbuf, int bufsize );
 int		FS_GetModList(  char *listbuf, int bufsize );
@@ -907,7 +907,7 @@
  * UI interface
  */
 qboolean UI_GameCommand( void );
-qboolean UI_usesUniqueCDKey();
+qboolean UI_usesUniqueCDKey(void);
 
 /*
 ==============================================================
@@ -1021,8 +1021,8 @@
 void	Sys_BeginProfiling( void );
 void	Sys_EndProfiling( void );
 
-qboolean Sys_LowPhysicalMemory();
-unsigned int Sys_ProcessorCount();
+qboolean Sys_LowPhysicalMemory(void);
+unsigned int Sys_ProcessorCount(void);
 
 int Sys_MonkeyShouldBeSpanked( void );
 

```
