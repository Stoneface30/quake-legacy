# wolfet-source — Architecture

**Upstream:** https://github.com/id-Software/Enemy-Territory
**Size (original):** 24.7 MB (shallow)
**Role in our project:** Wolfenstein: Enemy Territory — idtech3 derivative. Structural reference since wolfcam started as an ET mod.

## Module map
src/
├── cgame/        — client game (compare structure with wolfcamql's cgame)
├── client/       — cl_avi.c in ET variant
├── renderer/     — idtech3 renderer in ET form
├── game/         — server game, ET-specific classes and objectives
└── qcommon/      — shared code

## Key files
- `src/cgame/` — Compare structure with wolfcamql's cgame
- `src/client/cl_avi.c` — AVI capture in ET variant
- `src/game/g_combat.c` — Combat/kill system, ET variant of Q3's

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/wolfet-source/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
