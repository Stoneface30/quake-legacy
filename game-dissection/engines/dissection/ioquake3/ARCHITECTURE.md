# ioquake3 — Architecture

**Upstream:** https://github.com/ioquake/ioq3
**Size (original):** 40 MB (shallow)
**Role in our project:** Best-documented community Q3 baseline. Ancestor of wolfcamql, q3mme, quake3e, openarena-engine. Canonical cl_avi.c implementation.

## Module map
Same layout as quake3-source but with significant cleanups:
- SDL2 platform layer (code/sdl/)
- AVI capture: code/client/cl_avi.c (THE reference AVI writer)
- OpenGL 2 renderer stages (code/renderer/tr_glsl.c, bloom.c)
- 64-bit clean, modern C compatibility

## Key files
- `code/client/cl_avi.c` — AVI video capture — inherited by wolfcam, replaced by quake3e's ffmpeg pipe
- `code/qcommon/huffman.c` — Cleaner, better-commented variant of the Huffman codec
- `code/client/cl_demo.c` — Demo playback with additional error handling
- `code/renderer/tr_main.c` — Renderer frame submission, hook site for cl_avi capture

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/ioquake3/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
