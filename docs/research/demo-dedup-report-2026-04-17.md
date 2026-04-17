# Demo Dedup Report - 2026-04-17

Authority: full-permission cleanup per Part 4 review section 11 + user directive 2026-04-17.

User quote: "you have full permission to skin the drive and archive 7z files, [I'd] like to have my demo in one place and all the duplicate removed."

## Summary
- Demos found across G:\ (pre-dedup): **6546**
- Unique demos by SHA-256: **4292**
- Duplicate copies removed: **2254**
- Demos in canonical home `G:/QUAKE_LEGACY/demos/` after run: **4292**
- Bytes before (all copies): 14,392,415,917 (14.39 GB)
- Bytes in canonical home after: 7,873,603,238 (7.87 GB)
- Bytes freed by dedup (duplicate copies removed): 6,518,812,679 (6.52 GB)

Note: difference between 4292 unique-by-sha and 4292 files in canonical home is explained by some demos remaining in non-archived source dirs (locked/in-use) or filename collisions. See `_archive/` for the originals.

## Authority order applied (winner selection)
1. `G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL/wolfcam-ql/demos/` (PRIMARY_CORPUS)
2. Other paths under `G:/QUAKE_LEGACY/`
3. Other locations on G:\

Within an authority bucket, earliest mtime wins.

## Archived Sources
- `G_QUAKE_LEGACY_tools_quake-source_uberdemotools_demo_files.7z` (169.1 MB)
- `G_QUAKE_LEGACY_tools_quake-source_wolfcamql-src_package-files_wolfcam-ql_demos.7z` (1.4 MB)
- `G_QUAKE_LEGACY_WOLF WHISPERER_WolfcamQL_wolfcam-ql_demos.7z` (2662.4 MB)
- `G_QUAKE_LEGACY_WOLF WHISPERER_WolfcamQL_wolfcam-ql_demos_DEMO EXTRACTED ACTIONS.7z` (0.0 MB)

## Rules Honored
- Steam paths (`C:/Program Files (x86)/Steam/...`) untouched (read-only per project CLAUDE.md)
- No `.dm_73` deleted without SHA-256 dup confirmation
- No demo binaries committed to git (`.dm_73` is gitignored)
- Filename collisions on different sha would have been suffixed `-2`, `-3`; no such collisions occurred

## Files Committed
- `docs/research/demo-inventory-2026-04-17.json` - full per-file inventory (path, size, mtime, sha256)
- `docs/research/demo-dedup-report-2026-04-17.md` - this report
- `scripts/demo_inventory.py` - walker / hasher
- `scripts/demo_dedup_move.py` - dedup / move / archive
- `scripts/finalize_report.py` - report writer (used after first run hit a cp1252 encoding error on a unicode arrow)

## Status
- Canonical demo home established: `G:/QUAKE_LEGACY/demos/`
- Archives in: `G:/QUAKE_LEGACY/demos/_archive/`
- All operations completed; no BLOCKED states.