# uberdemotools — Architecture

**Upstream:** https://github.com/mightycow/uberdemotools
**Size (original):** 298 MB (full clone, includes test binaries and demos)
**Role in our project:** C++ demo parser with JSON export. Authoritative ground-truth for our FT-1 custom parser's correctness.

## Module map
UDT_DLL/
├── include/uberdemotools.h      — public C API
├── src/
│   ├── apps/
│   │   └── app_demo_json.cpp    — full demo → JSON export
│   ├── analysis_obituaries.cpp  — kill feed parser
│   ├── analysis_captures.cpp    — CTF captures
│   ├── analysis_pattern_frag_run.cpp
│   ├── analysis_pattern_mid_air.cpp
│   ├── analysis_pattern_multi_rail.cpp
│   └── api.cpp                  — C API implementation
├── TECHNICAL_NOTES.md           — protocol docs (READ FIRST)
└── CUSTOM_PARSING.md            — extension guide
research/Huffman/huffman.cpp     — reference impl with explanatory comments

## Key files
- `UDT_DLL/TECHNICAL_NOTES.md` — Best-in-class Q3/QL protocol docs. Read before writing any parser.
- `UDT_DLL/CUSTOM_PARSING.md` — Extension guide — how to add a new event analyzer
- `UDT_DLL/src/apps/app_demo_json.cpp` — Full-demo JSON export — shape of our output
- `UDT_DLL/src/analysis_obituaries.cpp` — Frag extraction reference
- `UDT_DLL/src/analysis_pattern_*.cpp` — Multi-kill / airshot / mid-air / multi-rail pattern detection

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/uberdemotools/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
