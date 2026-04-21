# Diff: `code/tools/lcc/cpp/tokens.c`
**Canonical:** `wolfcamql-src` (sha256 `c8aca64e0ba8...`, 7190 bytes)

## Variants

### `ioquake3`  — sha256 `3fbc2b954d5b...`, 7191 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\tokens.c	2026-04-16 20:02:25.766695400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\tools\lcc\cpp\tokens.c	2026-04-16 20:02:21.799416300 +0100
@@ -308,7 +308,7 @@
 				write(1, wbuf, wbp-wbuf);
 			write(1, (char *)p, len);
 			wbp = wbuf;
-		} else {
+		} else {	
 			memcpy(wbp, p, len);
 			wbp += len;
 		}

```

### `openarena-engine`  — sha256 `aef8c2ed9876...`, 7190 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\tokens.c	2026-04-16 20:02:25.766695400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\cpp\tokens.c	2026-04-16 22:48:25.946077500 +0100
@@ -308,14 +308,14 @@
 				write(1, wbuf, wbp-wbuf);
 			write(1, (char *)p, len);
 			wbp = wbuf;
-		} else {
+		} else {	
 			memcpy(wbp, p, len);
 			wbp += len;
 		}
 		if (wbp >= &wbuf[OBS]) {
 			write(1, wbuf, OBS);
 			if (wbp > &wbuf[OBS])
-				memmove(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
+				memcpy(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
 			wbp -= OBS;
 		}
 	}

```

### `openarena-gamecode`  — sha256 `8afcd9d89142...`, 7181 bytes

_Diff stat: +5 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\cpp\tokens.c	2026-04-16 20:02:25.766695400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\tools\lcc\cpp\tokens.c	2026-04-16 22:48:24.201077900 +0100
@@ -266,8 +266,9 @@
 	flushout();
 	if (str)
 		fprintf(stderr, "%s ", str);
-	if (tp<trp->bp || tp>trp->lp)
-		fprintf(stderr, "(tp offset %ld) ", (long int) (tp - trp->bp));
+	if (tp<trp->bp || tp>trp->lp) {
+		fprintf(stderr, "(tp offset %ld) ", tp-trp->bp);
+	}
 	for (tp=trp->bp; tp<trp->lp && tp<trp->bp+32; tp++) {
 		if (tp->type!=NL) {
 			int c = tp->t[tp->len];
@@ -308,14 +309,14 @@
 				write(1, wbuf, wbp-wbuf);
 			write(1, (char *)p, len);
 			wbp = wbuf;
-		} else {
+		} else {	
 			memcpy(wbp, p, len);
 			wbp += len;
 		}
 		if (wbp >= &wbuf[OBS]) {
 			write(1, wbuf, OBS);
 			if (wbp > &wbuf[OBS])
-				memmove(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
+				memcpy(wbuf, wbuf+OBS, wbp - &wbuf[OBS]);
 			wbp -= OBS;
 		}
 	}

```
