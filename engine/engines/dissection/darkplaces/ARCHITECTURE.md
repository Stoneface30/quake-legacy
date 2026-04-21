# darkplaces — Architecture

**Upstream:** https://icculus.org/twilight/darkplaces/
**Size (original):** 8.5 MB (shallow)
**Role in our project:** Modern Q1 engine with CSQC, advanced renderer, DP_* extensions.

## Module map
Custom idtech1 fork with heavy renderer modifications. Not a Q3 ancestor — separate branch.

## Key files
- `cl_demo.c` — Demo format for Q1, not relevant to dm_73
- `csprogs.c` — CSQC — client-side QuakeC, interesting for custom game logic
- `model_brush.c` — BSP loader

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/darkplaces/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
