# quake2-source — Architecture

**Upstream:** https://github.com/id-Software/Quake-2
**Size (original):** 6.2 MB (shallow)
**Role in our project:** Direct ancestor of Q3. Introduced modular renderer (ref_gl/), game DLL split, MOD_* constants.

## Module map
ref_gl/        — OpenGL renderer (direct ancestor of Q3's)
game/          — gamecode (separated from engine)
qcommon/       — shared code (ancestor of Q3's qcommon)
client/, server/

## Key files
- `ref_gl/` — OpenGL renderer — direct ancestor of Q3
- `game/g_combat.c` — Damage/kill logic, origin of MOD_* constants
- `qcommon/net_chan.c` — Network channel, ancestor of Q3's demo protocol
- `client/cl_demo.c` — Demo recording — compare with Q3's to trace format evolution

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/quake2-source/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
