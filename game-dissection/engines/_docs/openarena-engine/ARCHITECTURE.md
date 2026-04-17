# openarena-engine — Architecture

**Upstream:** https://github.com/OpenArena/engine
**Size (original):** 26.9 MB (shallow)
**Role in our project:** OpenArena engine fork of ioquake3. Second reference point for AVI capture and demo playback.

## Module map
Same as ioquake3 with community patches layered on top.

## Key files
- `code/client/cl_avi.c` — AVI capture (compare with ioquake3 and wolfcamql)
- `code/renderer/` — Renderer modifications (minor)
- `code/client/cl_demo.c` — Demo playback patches

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/openarena-engine/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
