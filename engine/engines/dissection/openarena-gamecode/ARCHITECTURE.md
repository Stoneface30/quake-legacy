# openarena-gamecode — Architecture

**Upstream:** https://github.com/OpenArena/gamecode
**Size (original):** 6.4 MB (shallow)
**Role in our project:** Q3-compatible gamecode with open-licensed weapons/items. Relevant for Phase 4 public CLI bundled-asset fallback.

## Module map
code/game/         — server game VM
code/cgame/        — client game VM
code/ui/           — menu VM
code/game/bg_*.c   — shared between game/cgame

## Key files
- `code/game/g_combat.c` — Kill/damage with OpenArena weapon additions
- `code/game/g_weapon.c` — Weapon fire logic
- `code/game/bg_misc.c` — Item/powerup definitions

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/openarena-gamecode/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
