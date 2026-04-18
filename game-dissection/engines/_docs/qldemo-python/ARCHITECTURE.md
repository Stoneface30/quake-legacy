# qldemo-python — Architecture

**Upstream:** https://github.com/Quakecon/qldemo-python
**Size (original):** 0.6 MB (full)
**Role in our project:** Pure-Python dm_73 parser. Reference implementation for FT-1's custom C++ parser.

## Module map
qldemo/           — parser library package
huffman/          — Huffman module (may be C extension for speed)
qldemo2json.py    — demo → JSON conversion script
qldemosummary.py  — summarize demo metadata

## Key files
- `qldemo/` — Parser library — the core protocol implementation
- `qldemo2json.py` — Entry point for demo-to-JSON conversion
- `qldemosummary.py` — Summary: players, scores, map, duration

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/qldemo-python/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
