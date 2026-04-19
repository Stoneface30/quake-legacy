# yamagi-quake2 — Architecture

**Upstream:** https://github.com/yquake2/yquake2
**Size (original):** 8.9 MB (shallow)
**Role in our project:** Modern Q2 community port. Reference for how a legacy engine is modernized without losing compatibility.

## Module map
Structurally similar to quake2-source with extensive modernization layers.

## Key files
- `src/` — Modernized src tree — CMake-driven
- `CMakeLists.txt` — Build reference
- `README.md` — Extensive porting notes

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/yamagi-quake2/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
