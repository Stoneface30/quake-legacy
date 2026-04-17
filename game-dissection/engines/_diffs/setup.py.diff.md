# Diff: `setup.py`
**Canonical:** `demodumper` (sha256 `0e8c3cd000bf...`, 725 bytes)

## Variants

### `qldemo-python`  — sha256 `4505b75f03ef...`, 746 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\setup.py	2026-04-16 20:02:27.598239300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\setup.py	2026-04-16 20:02:26.532759700 +0100
@@ -6,10 +6,10 @@
               sources = ['huffman/huffman.c','huffman/pyhuffman.c'])
 
 setup (name = 'ql-demo',
-       version = '0.4.3',
+       version = '0.4.12',
        ext_modules = [m],
        packages = find_packages(),
-       scripts = ['demodumper.py','ez_setup.py'],
+       scripts = ['qldemo2json.py','ez_setup.py','qldemosummary.py'],
        author = "Shawn Nock",
        author_email = "nock@nocko.se",
        description = "Wrapper for Q3A Huffman Code Routines and QuakeLive Demo Utility Classes",

```
