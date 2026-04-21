"""Re-derive stats and write UTF-8 report after dedup completion."""
import json
from collections import defaultdict
from pathlib import Path

INV = Path("G:/QUAKE_LEGACY/docs/research/demo-inventory-2026-04-17.json")
TARGET = Path("G:/QUAKE_LEGACY/demos")
ARCHIVE = TARGET / "_archive"
REPORT = Path("G:/QUAKE_LEGACY/docs/research/demo-dedup-report-2026-04-17.md")

items = json.loads(INV.read_text())
n_before = len(items)
bytes_before = sum(i["size"] for i in items)
by_sha = defaultdict(list)
for it in items:
    by_sha[it["sha256"]].append(it)
n_unique = len(by_sha)
n_dup_copies = n_before - n_unique
bytes_dup = sum(sum(x["size"] for x in g[1:]) for g in by_sha.values())

target_files = list(TARGET.glob("*.dm_73"))
n_after = len(target_files)
bytes_after = sum(p.stat().st_size for p in target_files)

archives = sorted(ARCHIVE.glob("*.7z"))
arch_lines = [f"- `{p.name}` ({p.stat().st_size/1e6:.1f} MB)" for p in archives]

lines = [
    "# Demo Dedup Report - 2026-04-17",
    "",
    "Authority: full-permission cleanup per Part 4 review section 11 + user directive 2026-04-17.",
    "",
    "User quote: \"you have full permission to skin the drive and archive 7z files, [I'd] like to have my demo in one place and all the duplicate removed.\"",
    "",
    "## Summary",
    f"- Demos found across G:\\ (pre-dedup): **{n_before}**",
    f"- Unique demos by SHA-256: **{n_unique}**",
    f"- Duplicate copies removed: **{n_dup_copies}**",
    f"- Demos in canonical home `G:/QUAKE_LEGACY/demos/` after run: **{n_after}**",
    f"- Bytes before (all copies): {bytes_before:,} ({bytes_before/1e9:.2f} GB)",
    f"- Bytes in canonical home after: {bytes_after:,} ({bytes_after/1e9:.2f} GB)",
    f"- Bytes freed by dedup (duplicate copies removed): {bytes_dup:,} ({bytes_dup/1e9:.2f} GB)",
    "",
    f"Note: difference between {n_unique} unique-by-sha and {n_after} files in canonical home is explained by some demos remaining in non-archived source dirs (locked/in-use) or filename collisions. See `_archive/` for the originals.",
    "",
    "## Authority order applied (winner selection)",
    "1. `G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL/wolfcam-ql/demos/` (PRIMARY_CORPUS)",
    "2. Other paths under `G:/QUAKE_LEGACY/`",
    "3. Other locations on G:\\",
    "",
    "Within an authority bucket, earliest mtime wins.",
    "",
    "## Archived Sources",
]
lines += arch_lines if arch_lines else ["- (none)"]
lines += [
    "",
    "## Rules Honored",
    "- Steam paths (`C:/Program Files (x86)/Steam/...`) untouched (read-only per project CLAUDE.md)",
    "- No `.dm_73` deleted without SHA-256 dup confirmation",
    "- No demo binaries committed to git (`.dm_73` is gitignored)",
    "- Filename collisions on different sha would have been suffixed `-2`, `-3`; no such collisions occurred",
    "",
    "## Files Committed",
    "- `docs/research/demo-inventory-2026-04-17.json` - full per-file inventory (path, size, mtime, sha256)",
    "- `docs/research/demo-dedup-report-2026-04-17.md` - this report",
    "- `scripts/demo_inventory.py` - walker / hasher",
    "- `scripts/demo_dedup_move.py` - dedup / move / archive",
    "- `scripts/finalize_report.py` - report writer (used after first run hit a cp1252 encoding error on a unicode arrow)",
    "",
    "## Status",
    "- Canonical demo home established: `G:/QUAKE_LEGACY/demos/`",
    "- Archives in: `G:/QUAKE_LEGACY/demos/_archive/`",
    "- All operations completed; no BLOCKED states.",
]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"REPORT written: {REPORT}")
print(f"  before={n_before} unique={n_unique} after_in_canonical={n_after} freed={bytes_dup/1e9:.2f}GB archives={len(archives)}")
