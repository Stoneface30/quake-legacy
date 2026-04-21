"""audit_library.py — find truncated / suspicious tracks in phase1/music/library/.

WHY
---
The 848 MP3s in `library/` were all fetched via spotdl's YouTube backend.
That backend regularly ships 2-minute radio-edits or previews where the
actual Spotify track is 3+ minutes (MAKEBA TECHNO = 3:08 on Spotify, but
library had 2:01). We need to mark every suspect file so the zotify
re-download pass knows what to replace.

HEURISTICS (no Spotify API call needed)
---------------------------------------
  TRUNCATED  : duration < 140s (2:20) — almost certainly a preview clip
  SUSPECT    : 140s <= duration < 180s (3:00) — maybe a radio edit
  OK         : duration >= 180s

We don't try to match filename → MusicLibrary.json URI here — spotdl's slug
rules differ from zotify's and the mapping is brittle. Instead we dump a
report; the zotify pipeline (download_library.py) will overwrite the MP3s
with OGG counterparts keyed by Spotify URI, then we delete any leftover
orphan MP3 that isn't in the playlist.

OUTPUT
------
  library/_audit_report.json:
    { "audited_at": "2026-04-19T...",
      "total": 848,
      "truncated": [{ "file": "...", "duration": 95.3 }, ...],
      "suspect":   [...],
      "ok":        [...] }

CLI
---
    python phase1/music/audit_library.py           # full audit + write report
    python phase1/music/audit_library.py --summary # just print buckets
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = PROJECT_ROOT / "phase1" / "music" / "library"
FFPROBE = PROJECT_ROOT / "tools" / "ffmpeg" / "ffprobe.exe"
REPORT_PATH = LIB_DIR / "_audit_report.json"

TRUNCATED_UNDER_S = 140.0   # < 2:20 — preview clip almost certainly
SUSPECT_UNDER_S = 180.0     # < 3:00 — maybe radio edit


def probe_duration(path: Path) -> float:
    """Return duration in seconds (0.0 on failure — don't raise)."""
    try:
        result = subprocess.run(
            [str(FFPROBE), "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(path)],
            capture_output=True, text=True, timeout=20,
        )
        return float(result.stdout.strip() or "0")
    except Exception:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true",
                    help="Print bucket counts only (no file list).")
    ap.add_argument("--ext", default="mp3,ogg",
                    help="Comma-separated extensions to audit.")
    args = ap.parse_args()

    if not LIB_DIR.exists():
        print(f"[audit] no library dir at {LIB_DIR}", file=sys.stderr)
        return 2

    exts = tuple("." + e.strip().lower() for e in args.ext.split(","))
    files = sorted(p for p in LIB_DIR.iterdir()
                   if p.is_file() and p.suffix.lower() in exts)
    if not files:
        print(f"[audit] no {exts} files in {LIB_DIR}")
        return 0

    print(f"[audit] probing {len(files)} files...", flush=True)
    truncated, suspect, ok = [], [], []
    for i, f in enumerate(files, 1):
        dur = probe_duration(f)
        entry = {"file": f.name, "duration": round(dur, 2),
                 "size_kb": round(f.stat().st_size / 1024, 1)}
        if dur < TRUNCATED_UNDER_S:
            truncated.append(entry)
        elif dur < SUSPECT_UNDER_S:
            suspect.append(entry)
        else:
            ok.append(entry)
        if i % 50 == 0:
            print(f"  ... {i}/{len(files)}", flush=True)

    report = {
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "library_dir": str(LIB_DIR),
        "total": len(files),
        "thresholds_s": {"truncated_under": TRUNCATED_UNDER_S,
                         "suspect_under": SUSPECT_UNDER_S},
        "bucket_counts": {
            "truncated": len(truncated),
            "suspect": len(suspect),
            "ok": len(ok),
        },
        "truncated": truncated,
        "suspect": suspect,
        "ok": ok if not args.summary else [],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("")
    print("=" * 60)
    print(f"TOTAL:     {len(files)}")
    print(f"TRUNCATED: {len(truncated):4d}  (< {TRUNCATED_UNDER_S:.0f}s — delete these)")
    print(f"SUSPECT:   {len(suspect):4d}  (< {SUSPECT_UNDER_S:.0f}s — review)")
    print(f"OK:        {len(ok):4d}  (>= {SUSPECT_UNDER_S:.0f}s)")
    print("=" * 60)
    print(f"report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
