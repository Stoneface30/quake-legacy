# Diff: `code/tools/lcc/cpp/lex.c`
**Canonical:** `wolfcamql-src` (sha256 `47025c09f532...`, 13842 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `efb3aabd3ca6...`, 13449 bytes
Also identical in: openarena-gamecode

_Diff stat: +0 / -20 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\lex.c	2026-04-16 20:02:25.764111400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\lex.c	2026-04-16 22:48:25.945078500 +0100
@@ -511,25 +511,6 @@
 	return 0;
 }
 
-// This doesn't have proper tracking across read() to only remove \r from \r\n sequence.
-// The lexer doesn't correctly handle standalone \r anyway though.
-int
-crlf_to_lf(unsigned char *buf, int n) {
-	int i, count;
-
-	count = 0;
-
-	for (i = 0; i < n; i++) {
-		if (buf[i] == '\r') {
-			continue;
-		}
-
-		buf[count++] = buf[i];
-	}
-
-	return count;
-}
-
 int
 fillbuf(Source *s)
 {
@@ -540,7 +521,6 @@
 		error(FATAL, "Input buffer overflow");
 	if (s->fd<0 || (n=read(s->fd, (char *)s->inl, INS/8)) <= 0)
 		n = 0;
-	n = crlf_to_lf(s->inl, n);
 	if ((*s->inp&0xff) == EOB) /* sentinel character appears in input */
 		*s->inp = EOFC;
 	s->inl += n;

```
