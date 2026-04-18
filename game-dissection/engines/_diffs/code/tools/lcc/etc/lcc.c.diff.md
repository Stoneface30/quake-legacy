# Diff: `code/tools/lcc/etc/lcc.c`
**Canonical:** `wolfcamql-src` (sha256 `2f3e82c92841...`, 22283 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `21eaa30e43d9...`, 21424 bytes

_Diff stat: +45 / -73 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\etc\lcc.c	2026-04-16 20:02:25.804312000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\etc\lcc.c	2026-04-16 22:48:25.948078100 +0100
@@ -11,12 +11,7 @@
 #include <assert.h>
 #include <ctype.h>
 #include <signal.h>
-#ifdef WIN32
-#include <process.h> /* getpid() */
-#include <io.h> /* access() */
-#else
 #include <unistd.h>
-#endif
 
 #ifndef TEMPDIR
 #define TEMPDIR "/tmp"
@@ -53,6 +48,10 @@
 extern int suffix(char *, char *[], int);
 extern char *tempname(char *);
 
+#ifndef __sun
+extern int getpid(void);
+#endif
+
 extern char *cpp[], *include[], *com[], *as[],*ld[], inputs[], *suffixes[];
 extern int option(char *);
 
@@ -217,91 +216,64 @@
 }
 
 #ifdef WIN32
-#include <windows.h>
+#include <process.h>
 
-static int argumentNeedsQuoted(const char *arg) {
-	if (arg && *arg == '"' && arg[strlen(arg) - 1] == '"') {
-		// Assume that if it's already fully quoted, it doesn't
-		// need any further quoting or escaping
-		return 0;
-	}
+static char *escapeDoubleQuotes(const char *string) {
+	int stringLength = strlen(string);
+	int bufferSize = stringLength + 1;
+	int i, j;
+	char *newString;
 
-	return !*arg || strpbrk(arg, " \t\"");
-}
+	if (string == NULL)
+		return NULL;
 
-static char *quoteArgument(const char *arg) {
-	// Quote if it has spaces, tabs, or is empty
-	if(argumentNeedsQuoted(arg)) {
-		size_t length = strlen(arg);
-		size_t bufferSize = length * 2 + 3; // maximum escapes + quotes + terminator
-		char *buffer = (char *)malloc(bufferSize);
-		char *p = buffer;
+	for (i = 0; i < stringLength; i++) {
+		if (string[i] == '"')
+			bufferSize++;
+	}
 
-		*p++ = '"'; // Open quote
+	newString = (char*)malloc(bufferSize);
 
-		for(size_t i = 0; i < length; i++) {
-			if(arg[i] == '"') {
-				// Escape quotes
-				*p++ = '\\';
-				*p++ = '"';
-			} else {
-				// Everything else
-				*p++ = arg[i];
-			}
-		}
+	if (newString == NULL)
+		return NULL;
 
-		*p++ = '"'; // Close quote
-		*p = '\0';
+	for (i = 0, j = 0; i < stringLength; i++) {
+		if (string[i] == '"')
+			newString[j++] = '\\';
 
-		return buffer;
+		newString[j++] = string[i];
 	}
 
-	// Duping to make memory management easier
-	return _strdup(arg);
+	newString[j] = '\0';
+
+	return newString;
 }
 
 static int spawn(const char *cmdname, char **argv) {
-	size_t totalLength = 0;
-	for(int i = 0; argv[i] != NULL; i++) {
-		char *quotedArg = quoteArgument(argv[i]);
-		totalLength += strlen(quotedArg) + 1;
-		free(quotedArg);
-	}
-
-	char *cmdline = (char *)malloc(totalLength + 1);
-	cmdline[0] = '\0';
+	int argc = 0;
+	char **newArgv = argv;
+	int i;
+	intptr_t exitStatus;
 
-	for(int i = 0; argv[i] != NULL; i++) {
-		char *quotedArg = quoteArgument(argv[i]);
-		strcat(cmdline, quotedArg);
-		if(argv[i+1]) strcat(cmdline, " ");
-		free(quotedArg);
-	}
+	// _spawnvp removes double quotes from arguments, so we
+	// have to escape them manually
+	while (*newArgv++ != NULL)
+		argc++;
 
-	STARTUPINFOA si = { sizeof(si) };
-	PROCESS_INFORMATION pi;
-	BOOL result = CreateProcessA(
-		cmdname, cmdline,
-		NULL, NULL, FALSE,
-		0, NULL, NULL,
-		&si, &pi);
+	newArgv = (char **)malloc(sizeof(char*) * (argc + 1));
 
-	if(!result) {
-		fprintf(stderr, "CreateProcess failed (%lu)\n", GetLastError());
-		free(cmdline);
-		return -1;
-	}
+	for (i = 0; i < argc; i++)
+		newArgv[i] = escapeDoubleQuotes(argv[i]);
 
-	WaitForSingleObject(pi.hProcess, INFINITE);
+	newArgv[argc] = NULL;
 
-	DWORD exit_code;
-	GetExitCodeProcess(pi.hProcess, &exit_code);
+	exitStatus = _spawnvp(_P_WAIT, cmdname, (const char *const *)newArgv);
 
-	CloseHandle(pi.hProcess);
-	CloseHandle(pi.hThread);
-	free(cmdline);
+	for (i = 0; i < argc; i++)
+		free(newArgv[i]);
 
-	return (int)exit_code;
+	free(newArgv);
+	return exitStatus;
 }
 
 #else
@@ -460,7 +432,7 @@
 			b = b->link;
 			if (b->str[0]) {
 				char buf[1024];
-				snprintf(buf, sizeof(buf), "%s/%s", b->str, name);
+				sprintf(buf, "%s/%s", b->str, name);
 				if (access(buf, 4) == 0)
 					return strsave(buf);
 			} else if (access(name, 4) == 0)
@@ -659,7 +631,7 @@
 					clist = append(&arg[3], clist);
 					return;
 				}
-				break; /* and fall through */
+				break; /* and fall thru */
 			case 'a':
 				alist = append(&arg[3], alist);
 				return;

```

### `openarena-gamecode`  — sha256 `36d260f22b0a...`, 20403 bytes

_Diff stat: +14 / -98 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\etc\lcc.c	2026-04-16 20:02:25.804312000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\etc\lcc.c	2026-04-16 22:48:24.203077700 +0100
@@ -11,12 +11,7 @@
 #include <assert.h>
 #include <ctype.h>
 #include <signal.h>
-#ifdef WIN32
-#include <process.h> /* getpid() */
-#include <io.h> /* access() */
-#else
 #include <unistd.h>
-#endif
 
 #ifndef TEMPDIR
 #define TEMPDIR "/tmp"
@@ -53,6 +48,10 @@
 extern int suffix(char *, char *[], int);
 extern char *tempname(char *);
 
+#ifndef __sun
+extern int getpid(void);
+#endif
+
 extern char *cpp[], *include[], *com[], *as[],*ld[], inputs[], *suffixes[];
 extern int option(char *);
 
@@ -217,102 +216,15 @@
 }
 
 #ifdef WIN32
-#include <windows.h>
-
-static int argumentNeedsQuoted(const char *arg) {
-	if (arg && *arg == '"' && arg[strlen(arg) - 1] == '"') {
-		// Assume that if it's already fully quoted, it doesn't
-		// need any further quoting or escaping
-		return 0;
-	}
-
-	return !*arg || strpbrk(arg, " \t\"");
-}
-
-static char *quoteArgument(const char *arg) {
-	// Quote if it has spaces, tabs, or is empty
-	if(argumentNeedsQuoted(arg)) {
-		size_t length = strlen(arg);
-		size_t bufferSize = length * 2 + 3; // maximum escapes + quotes + terminator
-		char *buffer = (char *)malloc(bufferSize);
-		char *p = buffer;
-
-		*p++ = '"'; // Open quote
-
-		for(size_t i = 0; i < length; i++) {
-			if(arg[i] == '"') {
-				// Escape quotes
-				*p++ = '\\';
-				*p++ = '"';
-			} else {
-				// Everything else
-				*p++ = arg[i];
-			}
-		}
-
-		*p++ = '"'; // Close quote
-		*p = '\0';
-
-		return buffer;
-	}
-
-	// Duping to make memory management easier
-	return _strdup(arg);
-}
-
-static int spawn(const char *cmdname, char **argv) {
-	size_t totalLength = 0;
-	for(int i = 0; argv[i] != NULL; i++) {
-		char *quotedArg = quoteArgument(argv[i]);
-		totalLength += strlen(quotedArg) + 1;
-		free(quotedArg);
-	}
-
-	char *cmdline = (char *)malloc(totalLength + 1);
-	cmdline[0] = '\0';
-
-	for(int i = 0; argv[i] != NULL; i++) {
-		char *quotedArg = quoteArgument(argv[i]);
-		strcat(cmdline, quotedArg);
-		if(argv[i+1]) strcat(cmdline, " ");
-		free(quotedArg);
-	}
-
-	STARTUPINFOA si = { sizeof(si) };
-	PROCESS_INFORMATION pi;
-	BOOL result = CreateProcessA(
-		cmdname, cmdline,
-		NULL, NULL, FALSE,
-		0, NULL, NULL,
-		&si, &pi);
-
-	if(!result) {
-		fprintf(stderr, "CreateProcess failed (%lu)\n", GetLastError());
-		free(cmdline);
-		return -1;
-	}
-
-	WaitForSingleObject(pi.hProcess, INFINITE);
-
-	DWORD exit_code;
-	GetExitCodeProcess(pi.hProcess, &exit_code);
-
-	CloseHandle(pi.hProcess);
-	CloseHandle(pi.hThread);
-	free(cmdline);
-
-	return (int)exit_code;
-}
-
+#include <process.h>
 #else
-
 #define _P_WAIT 0
 #ifndef __sun
 extern int fork(void);
 #endif
 extern int wait(int *);
 
-static int spawn(const char *cmdname, char **argv) {
+static int _spawnvp(int mode, const char *cmdname, char *argv[]) {
 	int pid, n, status;
 
 	switch (pid = fork()) {
@@ -380,7 +292,11 @@
 			fprintf(stderr, "\n");
 		}
 		if (verbose < 2)
-			status = spawn(executable, argv);
+#ifndef WIN32
+			status = _spawnvp(_P_WAIT, executable, argv);
+#else
+			status = _spawnvp(_P_WAIT, executable, (const char* const*)argv);
+#endif
 		if (status == -1) {
 			fprintf(stderr, "%s: ", progname);
 			perror(argv[0]);
@@ -460,7 +376,7 @@
 			b = b->link;
 			if (b->str[0]) {
 				char buf[1024];
-				snprintf(buf, sizeof(buf), "%s/%s", b->str, name);
+				sprintf(buf, "%s/%s", b->str, name);
 				if (access(buf, 4) == 0)
 					return strsave(buf);
 			} else if (access(name, 4) == 0)
@@ -659,7 +575,7 @@
 					clist = append(&arg[3], clist);
 					return;
 				}
-				break; /* and fall through */
+				break; /* and fall thru */
 			case 'a':
 				alist = append(&arg[3], alist);
 				return;
@@ -843,7 +759,7 @@
 	va_list ap;
 
 	va_start(ap, fmt);
-	vsprintf(buf, fmt, ap);
+	vsnprintf(buf, sizeof(buf), fmt, ap);
 	va_end(ap);
 	return strsave(buf);
 }

```
