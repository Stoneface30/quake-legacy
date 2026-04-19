# uberdemotools — Quirks and Gotchas

- **Pre-built binaries ship in the repo** (UDT_DLL_*.dll, UDT_json.exe) — these inflate the tree size to 619 MB originally.
- Most of the size is test .dm_73 / .dm_90 fixtures under tests/ — we can cull these in our dedup if we don't run UDT's own tests
- C++ API uses raw pointers + caller-manages-memory; Python wrapper must be careful
- Supports proto-66 (Q3 1.16n), proto-68 (Q3 1.32), proto-73 (QL 2010), proto-90 (QL 2015+)
- Our focus is proto-73, but UDT handles all of them — use for validation of FT-1 custom parser

## See also
- `_docs/uberdemotools/ARCHITECTURE.md`
- `_docs/uberdemotools/EXTENSION_POINTS.md`
