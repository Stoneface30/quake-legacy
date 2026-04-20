# gtkradiant — Architecture

**Upstream:** https://github.com/TTimo/GtkRadiant
**Size (original):** 50.5 MB
**Role in our project:** idtech2/3/4 level editor. Reference for BSP compile pipeline.

## Module map
radiant/          — editor core
tools/            — q3map2 (BSP compiler), q3data, q3map
plugins/          — format plugins for various id games

## Key files
- `tools/quake3/q3map2/` — BSP compiler — how .map files become .bsp
- `radiant/` — Editor main

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/gtkradiant/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
