# Diff: `lcc/etc/lcc.c`
**Canonical:** `quake3-source` (sha256 `04b64641c9a5...`, 20292 bytes)

## Variants

### `q3vm`  — sha256 `726ffc32ba2c...`, 21525 bytes

_Diff stat: +101 / -37 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3-source\lcc\etc\lcc.c	2026-04-16 20:02:20.048698400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\q3vm\lcc\etc\lcc.c	2026-04-16 22:48:28.092134900 +0100
@@ -11,6 +11,12 @@
 #include <assert.h>
 #include <ctype.h>
 #include <signal.h>
+#ifdef WIN32
+#include <process.h> /* getpid() */
+#include <io.h> /* access() */
+#else
+#include <unistd.h>
+#endif
 
 #ifndef TEMPDIR
 #define TEMPDIR "/tmp"
@@ -24,7 +30,7 @@
 
 static void *alloc(int);
 static List append(char *,List);
-extern char *basepath(char *);
+extern char *basename(char *);
 static int callsys(char *[]);
 extern char *concat(char *, char *);
 static int compile(char *, char *);
@@ -47,15 +53,16 @@
 extern int suffix(char *, char *[], int);
 extern char *tempname(char *);
 
-extern int access(char *, int);
+#ifndef __sun
 extern int getpid(void);
+#endif
 
 extern char *cpp[], *include[], *com[], *as[],*ld[], inputs[], *suffixes[];
 extern int option(char *);
 
 static int errcnt;		/* number of errors */
 static int Eflag;		/* -E specified */
-static int Sflag;		/* -S specified */
+static int Sflag = 1;		/* -S specified */ //for Q3 we always generate asm
 static int cflag;		/* -c specified */
 static int verbose;		/* incremented for each -v */
 static List llist[2];		/* loader files, flags */
@@ -71,10 +78,15 @@
 static char *progname;
 static List lccinputs;		/* list of input directories */
 
-main(int argc, char *argv[]) {
+extern void UpdatePaths( const char *lccBinary );
+
+int main(int argc, char *argv[]) {
 	int i, j, nf;
-	
+
 	progname = argv[0];
+
+	UpdatePaths( progname );
+
 	ac = argc + 50;
 	av = alloc(ac*sizeof(char *));
 	if (signal(SIGINT, SIG_IGN) != SIG_IGN)
@@ -93,7 +105,7 @@
 		tempdir = getenv("TMPDIR");
 	assert(tempdir);
 	i = strlen(tempdir);
-	for (; i > 0 && tempdir[i-1] == '/' || tempdir[i-1] == '\\'; i--)
+	for (; (i > 0 && tempdir[i-1] == '/') || tempdir[i-1] == '\\'; i--)
 		tempdir[i-1] = '\0';
 	if (argc <= 1) {
 		help();
@@ -149,7 +161,7 @@
 			char *name = exists(argv[i]);
 			if (name) {
 				if (strcmp(name, argv[i]) != 0
-				|| nf > 1 && suffix(name, suffixes, 3) >= 0)
+				|| (nf > 1 && suffix(name, suffixes, 3) >= 0))
 					fprintf(stderr, "%s:\n", name);
 				filename(name, 0);
 			} else
@@ -192,8 +204,8 @@
 	return p;
 }
 
-/* basepath - return base name for name, e.g. /usr/drh/foo.c => foo */
-char *basepath(char *name) {
+/* basename - return base name for name, e.g. /usr/drh/foo.c => foo */
+char *basename(char *name) {
 	char *s, *b, *t = 0;
 
 	for (b = s = name; *s; s++)
@@ -210,13 +222,74 @@
 
 #ifdef WIN32
 #include <process.h>
+
+static char *escapeDoubleQuotes(const char *string) {
+	int stringLength = strlen(string);
+	int bufferSize = stringLength + 1;
+	int i, j;
+	char *newString;
+
+	if (string == NULL)
+		return NULL;
+
+	for (i = 0; i < stringLength; i++) {
+		if (string[i] == '"')
+			bufferSize++;
+	}
+
+	newString = (char*)malloc(bufferSize);
+
+	if (newString == NULL)
+		return NULL;
+
+	for (i = 0, j = 0; i < stringLength; i++) {
+		if (string[i] == '"')
+			newString[j++] = '\\';
+
+		newString[j++] = string[i];
+	}
+
+	newString[j] = '\0';
+
+	return newString;
+}
+
+static int spawn(const char *cmdname, char **argv) {
+	int argc = 0;
+	char **newArgv = argv;
+	int i;
+	intptr_t exitStatus;
+
+	// _spawnvp removes double quotes from arguments, so we
+	// have to escape them manually
+	while (*newArgv++ != NULL)
+		argc++;
+
+	newArgv = (char **)malloc(sizeof(char*) * (argc + 1));
+
+	for (i = 0; i < argc; i++)
+		newArgv[i] = escapeDoubleQuotes(argv[i]);
+
+	newArgv[argc] = NULL;
+
+	exitStatus = _spawnvp(_P_WAIT, cmdname, (const char *const *)newArgv);
+
+	for (i = 0; i < argc; i++)
+		free(newArgv[i]);
+
+	free(newArgv);
+	return exitStatus;
+}
+
 #else
+
 #define _P_WAIT 0
+#ifndef __sun
 extern int fork(void);
+#endif
 extern int wait(int *);
-extern void execv(const char *, char *[]);
 
-static int _spawnvp(int mode, const char *cmdname, char *argv[]) {
+static int spawn(const char *cmdname, char **argv) {
 	int pid, n, status;
 
 	switch (pid = fork()) {
@@ -248,6 +321,7 @@
 	int i, status = 0;
 	static char **argv;
 	static int argc;
+	char *executable;
 
 	for (i = 0; av[i] != NULL; i++)
 		;
@@ -261,7 +335,7 @@
 	}
 	for (i = 0; status == 0 && av[i] != NULL; ) {
 		int j = 0;
-		char *s;
+		char *s = NULL;
 		for ( ; av[i] != NULL && (s = strchr(av[i], '\n')) == NULL; i++)
 			argv[j++] = av[i];
 		if (s != NULL) {
@@ -273,6 +347,8 @@
 				i++;
 		}
 		argv[j] = NULL;
+		executable = strsave( argv[0] );
+		argv[0] = stringf( "\"%s\"", argv[0] );
 		if (verbose > 0) {
 			int k;
 			fprintf(stderr, "%s", argv[0]);
@@ -281,7 +357,7 @@
 			fprintf(stderr, "\n");
 		}
 		if (verbose < 2)
-			status = _spawnvp(_P_WAIT, argv[0], argv);
+			status = spawn(executable, argv);
 		if (status == -1) {
 			fprintf(stderr, "%s: ", progname);
 			perror(argv[0]);
@@ -319,7 +395,7 @@
 		if (s && isdigit(s[1])) {
 			int k = s[1] - '0';
 			assert(k >=1 && k <= 3);
-			if (b = lists[k-1]) {
+			if ((b = lists[k-1])) {
 				b = b->link;
 				av[j] = alloc(strlen(cmd[i]) + strlen(b->str) - 1);
 				strncpy(av[j], cmd[i], s - cmd[i]);
@@ -391,7 +467,7 @@
 	static char *stemp, *itemp;
 
 	if (base == 0)
-		base = basepath(name);
+		base = basename(name);
 	switch (suffix(name, suffixes, 4)) {
 	case 0:	/* C source files */
 		compose(cpp, plist, append(name, 0), 0);
@@ -452,7 +528,7 @@
 static List find(char *str, List list) {
 	List b;
 	
-	if (b = list)
+	if ((b = list))
 		do {
 			if (strcmp(str, b->str) == 0)
 				return b;
@@ -508,26 +584,22 @@
 		if (strncmp("-tempdir", msgs[i], 8) == 0 && tempdir)
 			fprintf(stderr, "; default=%s", tempdir);
 	}
-#define xx(v) if (s = getenv(#v)) fprintf(stderr, #v "=%s\n", s)
+#define xx(v) if ((s = getenv(#v))) fprintf(stderr, #v "=%s\n", s)
 	xx(LCCINPUTS);
 	xx(LCCDIR);
-#ifdef WIN32
-	xx(include);
-	xx(lib);
-#endif
 #undef xx
 }
 
 /* initinputs - if LCCINPUTS or include is defined, use them to initialize various lists */
 static void initinputs(void) {
 	char *s = getenv("LCCINPUTS");
-	List list, b;
+	List b;
 
 	if (s == 0 || (s = inputs)[0] == 0)
 		s = ".";
 	if (s) {
 		lccinputs = path2list(s);
-		if (b = lccinputs)
+		if ((b = lccinputs))
 			do {
 				b = b->link;
 				if (strcmp(b->str, ".") != 0) {
@@ -538,13 +610,6 @@
 					b->str = "";
 			} while (b != lccinputs);
 	}
-#ifdef WIN32
-	if (list = b = path2list(getenv("include")))
-		do {
-			b = b->link;
-			ilist = append(stringf("-I\"%s\"", b->str), ilist);
-		} while (b != list);
-#endif
 }
 
 /* interrupt - catch interrupt signals */
@@ -571,7 +636,7 @@
 					clist = append(&arg[3], clist);
 					return;
 				}
-				break; /* and fall thru */
+				break; /* and fall through */
 			case 'a':
 				alist = append(&arg[3], alist);
 				return;
@@ -670,14 +735,14 @@
 			cflag++;
 			return;
 		case 'N':
-			if (strcmp(basepath(cpp[0]), "gcc-cpp") == 0)
+			if (strcmp(basename(cpp[0]), "gcc-cpp") == 0)
 				plist = append("-nostdinc", plist);
 			include[0] = 0;
 			ilist = 0;
 			return;
 		case 'v':
 			if (verbose++ == 0) {
-				if (strcmp(basepath(cpp[0]), "gcc-cpp") == 0)
+				if (strcmp(basename(cpp[0]), "gcc-cpp") == 0)
 					plist = append(arg, plist);
 				clist = append(arg, clist);
 				fprintf(stderr, "%s %s\n", progname, rcsid);
@@ -701,7 +766,7 @@
 		sep = ';';
 	while (*path) {
 		char *p, buf[512];
-		if (p = strchr(path, sep)) {
+		if ((p = strchr(path, sep))) {
 			assert(p - path < sizeof buf);
 			strncpy(buf, path, p - path);
 			buf[p-path] = '\0';
@@ -753,10 +818,9 @@
 char *stringf(const char *fmt, ...) {
 	char buf[1024];
 	va_list ap;
-	int n;
 
 	va_start(ap, fmt);
-	n = vsprintf(buf, fmt, ap);
+	vsprintf(buf, fmt, ap);
 	va_end(ap);
 	return strsave(buf);
 }
@@ -767,7 +831,7 @@
 
 	for (i = 0; i < n; i++) {
 		char *s = tails[i], *t;
-		for ( ; t = strchr(s, ';'); s = t + 1) {
+		for ( ; (t = strchr(s, ';')); s = t + 1) {
 			int m = t - s;
 			if (len > m && strncmp(&name[len-m], s, m) == 0)
 				return i;

```
