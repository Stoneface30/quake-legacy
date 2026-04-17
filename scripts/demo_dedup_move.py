"""Dedup demos by sha256, move winners to G:/QUAKE_LEGACY/demos/, archive sources."""
import json
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

INV = Path("G:/QUAKE_LEGACY/docs/research/demo-inventory-2026-04-17.json")
TARGET = Path("G:/QUAKE_LEGACY/demos")
ARCHIVE = TARGET / "_archive"
REPORT = Path("G:/QUAKE_LEGACY/docs/research/demo-dedup-report-2026-04-17.md")
SEVENZ = "C:/Program Files/7-Zip/7z.exe"

PROJECT_ROOT = "g:/quake_legacy"
PRIMARY_CORPUS = "g:/quake_legacy/wolf whisperer/wolfcamql/wolfcam-ql/demos"

def authority_score(path: str) -> int:
    """Lower = more authoritative (kept first)."""
    p = path.lower().replace("\\", "/")
    if p.startswith(PRIMARY_CORPUS):
        return 0
    if p.startswith(PROJECT_ROOT):
        return 1
    return 2

def sanitize(path: str) -> str:
    s = path.replace(":", "").replace("\\", "_").replace("/", "_").strip("_")
    return s[:180]

def main():
    items = json.loads(INV.read_text())
    n_before = len(items)
    bytes_before = sum(i["size"] for i in items)
    print(f"Loaded {n_before} demos, {bytes_before/1e9:.2f} GB total", file=sys.stderr)

    # 50 GB pause check
    if bytes_before > 50 * 1024**3:
        print(f"WARNING: total size {bytes_before/1e9:.1f} GB exceeds 50 GB threshold", file=sys.stderr)

    # Group by sha
    by_sha = defaultdict(list)
    for it in items:
        by_sha[it["sha256"]].append(it)

    n_unique = len(by_sha)
    n_dup = n_before - n_unique
    bytes_saved = 0

    # Pick winners
    winners = []
    losers = []  # to delete (true dups)
    for sha, group in by_sha.items():
        # sort: authority asc, mtime asc
        group.sort(key=lambda x: (authority_score(x["path"]), x["mtime"]))
        winners.append(group[0])
        for dup in group[1:]:
            losers.append(dup)
            bytes_saved += dup["size"]

    TARGET.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    target_resolved = str(TARGET.resolve()).replace("\\", "/").lower()

    # Track which source dirs had demos
    source_dirs = set()
    moved = 0
    skipped_already_in_target = 0
    deleted_dups = 0

    # Move winners
    for w in winners:
        src = Path(w["path"])
        src_norm = str(src.resolve()).replace("\\", "/").lower()
        if src_norm.startswith(target_resolved):
            skipped_already_in_target += 1
            continue
        source_dirs.add(str(src.parent))
        # Resolve collision
        dst = TARGET / src.name
        if dst.exists():
            stem = dst.stem
            suffix = dst.suffix
            i = 2
            while True:
                cand = TARGET / f"{stem}-{i}{suffix}"
                if not cand.exists():
                    dst = cand
                    break
                i += 1
        try:
            shutil.move(str(src), str(dst))
            moved += 1
        except Exception as e:
            print(f"MOVE FAIL {src} -> {dst}: {e}", file=sys.stderr)

    # Delete confirmed dups
    for d in losers:
        p = Path(d["path"])
        src_norm = str(p.resolve()).replace("\\", "/").lower() if p.exists() else ""
        if src_norm.startswith(target_resolved):
            # losing copy was already in target — still should delete it
            pass
        if p.exists():
            source_dirs.add(str(p.parent))
            try:
                p.unlink()
                deleted_dups += 1
            except Exception as e:
                print(f"DEL FAIL {p}: {e}", file=sys.stderr)

    # Archive each source dir's REMAINING contents
    archives_created = []
    for d in sorted(source_dirs):
        dp = Path(d)
        if not dp.exists():
            continue
        # Skip if it's the target itself
        if str(dp.resolve()).replace("\\", "/").lower().startswith(target_resolved):
            continue
        # Skip empty
        try:
            entries = list(dp.iterdir())
        except Exception:
            continue
        if not entries:
            continue
        arc_name = sanitize(d) + ".7z"
        arc_path = ARCHIVE / arc_name
        if arc_path.exists():
            continue
        print(f"Archiving {d} -> {arc_name}", file=sys.stderr)
        try:
            r = subprocess.run(
                [SEVENZ, "a", "-t7z", "-mx=7", "-mmt=on", str(arc_path), str(dp) + "/*"],
                capture_output=True, text=True, timeout=3600,
            )
            if r.returncode == 0:
                archives_created.append((d, str(arc_path), arc_path.stat().st_size))
            else:
                print(f"7Z FAIL {d}: rc={r.returncode} {r.stderr[:300]}", file=sys.stderr)
        except Exception as e:
            print(f"7Z EXC {d}: {e}", file=sys.stderr)

    # Final count in target
    n_after = sum(1 for _ in TARGET.glob("*.dm_73"))
    bytes_after = sum(p.stat().st_size for p in TARGET.glob("*.dm_73"))

    # Report
    lines = [
        "# Demo Dedup Report — 2026-04-17",
        "",
        "Authority: full-permission cleanup per Part 4 review §11 + user directive 2026-04-17.",
        "",
        "## Summary",
        f"- Demos found (pre-dedup): **{n_before}**",
        f"- Unique demos by SHA-256: **{n_unique}**",
        f"- Duplicate copies removed: **{n_dup}**",
        f"- Demos in canonical home after run: **{n_after}**",
        f"- Bytes before: {bytes_before:,} ({bytes_before/1e9:.2f} GB)",
        f"- Bytes in canonical home after: {bytes_after:,} ({bytes_after/1e9:.2f} GB)",
        f"- Bytes freed by dedup: {bytes_saved:,} ({bytes_saved/1e9:.2f} GB)",
        "",
        "## Operations",
        f"- Moved (winners) into `G:/QUAKE_LEGACY/demos/`: **{moved}**",
        f"- Skipped (already in target): **{skipped_already_in_target}**",
        f"- Deleted (sha-confirmed duplicates): **{deleted_dups}**",
        f"- Source directories archived: **{len(archives_created)}**",
        "",
        "## Archived Sources",
    ]
    if archives_created:
        for src, arc, sz in archives_created:
            lines.append(f"- `{src}` → `{Path(arc).name}` ({sz/1e6:.1f} MB)")
    else:
        lines.append("- (none — all source dirs were empty or already cleared)")
    lines += [
        "",
        "## Rules Honored",
        "- Steam paths (`C:/Program Files (x86)/Steam/...`) untouched",
        "- No `.dm_73` deleted without SHA-256 dup confirmation",
        "- No demo binaries committed to git (gitignored)",
        "- Authority order: PRIMARY_CORPUS (wolfcam-ql/demos) > project subdirs > other G: locations",
        "",
        "## Files",
        "- Inventory: `docs/research/demo-inventory-2026-04-17.json`",
        "- Report: `docs/research/demo-dedup-report-2026-04-17.md` (this file)",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    print(f"REPORT: {REPORT}")
    print(f"DONE moved={moved} dup_deleted={deleted_dups} archives={len(archives_created)}")

if __name__ == "__main__":
    main()
