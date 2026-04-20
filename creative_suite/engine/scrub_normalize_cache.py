"""scrub_normalize_cache.py — remove corrupt entries from output/normalized/.

L154 fix: ffprobe-validates every cached mp4, deletes those with missing
moov / zero duration / truncated streams. Prints summary.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "output" / "normalized"
FFPROBE = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"


def probe(p: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [str(FFPROBE), "-v", "error",
             "-show_entries", "format=duration",
             "-of", "csv=p=0", str(p)],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return False, (r.stderr or "rc!=0").strip().splitlines()[-1][:80]
        dur = float(r.stdout.strip() or "0")
        if dur < 0.5:
            return False, f"duration={dur}"
        return True, f"dur={dur:.1f}s"
    except Exception as e:
        return False, repr(e)[:80]


def main() -> int:
    if not CACHE.exists():
        print(f"no cache dir {CACHE}")
        return 0
    files = sorted(CACHE.glob("*.mp4"))
    ok = 0
    bad = 0
    bad_files: list[Path] = []
    for f in files:
        good, msg = probe(f)
        if good:
            ok += 1
        else:
            bad += 1
            bad_files.append(f)
            print(f"CORRUPT {f.name}  ({msg})")
    for f in bad_files:
        try:
            f.unlink()
        except Exception as e:
            print(f"  unlink fail {f.name}: {e}")
    print(f"\nscrubbed: {bad} corrupt / {ok} good / {len(files)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
