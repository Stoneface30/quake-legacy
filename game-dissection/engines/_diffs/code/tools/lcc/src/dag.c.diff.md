# Diff: `code/tools/lcc/src/dag.c`
**Canonical:** `wolfcamql-src` (sha256 `13e979baefc0...`, 22872 bytes)
Also identical in: ioquake3

## Variants

### `openarena-engine`  — sha256 `e456ae47f210...`, 22875 bytes

_Diff stat: +1 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\tools\lcc\src\dag.c	2026-04-16 20:02:25.808414500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\tools\lcc\src\dag.c	2026-04-16 22:48:25.951096500 +0100
@@ -519,8 +519,7 @@
 			       	(*IR->stabline)(&cp->u.point.src); swtoseg(CODE); } break;
 		case Gen: case Jump:
 		case Label:    if (cp->u.forest)
-				(*IR->emit)(cp->u.forest);
-			break;
+			       	(*IR->emit)(cp->u.forest); break;
 		case Local:    if (glevel && IR->stabsym) {
 			       	(*IR->stabsym)(cp->u.var);
 			       	swtoseg(CODE);

```

### `openarena-gamecode`  — sha256 `dd1ba25c24f0...`, 22254 bytes

_Diff stat: +477 / -363 lines_

_(full diff is 33736 bytes — see files directly)_
