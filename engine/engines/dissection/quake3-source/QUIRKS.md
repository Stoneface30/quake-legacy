# quake3-source — Quirks and Gotchas

- **Reference tree only** — we do not build or run this, we only read it.
- Source is release-1999 C; some constructs are pre-C99 (no stdint.h).
- `cgame/g_*.c` and similar files are NOT in this tree — Q3A was the first id release to ship only the engine source + gamecode separately; gamecode lives in `code/game/` not under `code/`.
- Licensing: GPL-2.0. Our forks must preserve headers.

## See also
- `_docs/quake3-source/ARCHITECTURE.md`
- `_docs/quake3-source/EXTENSION_POINTS.md`
