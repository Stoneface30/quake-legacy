# Diff: `code/tools/lcc/src/output.c`
**Canonical:** `wolfcamql-src` (sha256 `b9f8af6a4551...`, 3439 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `a8738953ea99...`, 3427 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\output.c	2026-04-16 20:02:25.813417600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\output.c	2026-04-16 22:48:25.955097100 +0100
@@ -80,7 +80,7 @@
 				  	static char format[] = "%f";
 				  	char buf[128];
 				  	format[1] = *fmt;
-					snprintf(buf, sizeof(buf), format, va_arg(ap, double));
+				  	sprintf(buf, format, va_arg(ap, double));
 				  	bp = outs(buf, f, bp);
 				  }
 ; break;

```
