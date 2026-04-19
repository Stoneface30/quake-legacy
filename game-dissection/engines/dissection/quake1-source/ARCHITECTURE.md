# quake1-source — Architecture

**Upstream:** https://github.com/id-Software/Quake
**Size (original):** 11.8 MB (shallow)
**Role in our project:** Root of the idtech lineage. Reference for EV_OBITUARY ancestry and BSP format origin.

## Module map
WinQuake/      — Windows renderer + sound
Quake/         — engine core (game logic, world, sv_main)
QW/            — QuakeWorld client/server (early network split)

## Key files
- `Quake/world.c` — Entity/physics world state — ancestor of Q3's entity system
- `Quake/sv_main.c` — Server loop origin — all idtech servers descend from this
- `WinQuake/bspfile.h` — BSP format — ancestor of Q3's BSP structure

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/quake1-source/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
