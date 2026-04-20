# game-dissection/

Unified home for all Quake engine source, dissection docs, binary RE (Ghidra),
patch series, and wolfcam knowledge. Supersedes the old `tools/quake-source/`
scatter per `docs/research/engine-folder-unification-plan-2026-04-19.md`.

## Layout

- [`engines/README.md`](engines/README.md) — family tree, authority order, per-file diffs (was SYNTHESIS.md)
- [`engines/REPOS.md`](engines/REPOS.md) — 186-line rationale per fork (moved from tools/quake-source/REPOS.md)
- `engines/_canonical/` — SHA-256 deduped merged tree, authority-ordered
- `engines/_diffs/` — 513 per-file `.diff.md` patch docs for near-dup files
- `engines/dissection/` — per-engine ARCHITECTURE/QUIRKS/EXTENSION_POINTS notes (was `_docs/`)
- `engines/_manifest/` — inventory + canonical_map + build scripts
- `engines/variants/` — per-tree near-dup variant dirs (thin — files that differ from `_canonical/`)
- `engines/_forks/` — live writable source trees (q3mme proto-73 port base)
- `engines/wolfcam-knowledge/` — 7 curated docs + protocol-73 patch series + shipped-binary deltas
- `engines/ghidra/` — FT-4 binary RE outputs (decompilations, symbols, IPC maps)
- `engines/parsers/` — pointer-hub for `.dm_73` parsers (docs only; sources in phase2/)
- [`assets/`](assets/) — asset dissection (not engine-specific)
- [`graphify-out/`](graphify-out/) — knowledge graphs for engine trees

## Quick links

- Full plan: `docs/research/engine-folder-unification-plan-2026-04-19.md`
- Protocol-73 synthesis: `engines/wolfcam-knowledge/00-overview.md`
- FT-1 dm_73 parser: `phase2/dm73parser/`
- Steam-pak asset source (Rule ENG-1): `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3`
