"""rotate_fresh_stems.py — pick 5 fresh tracks from library/ for Part N.

Picks by seeded-random from duration-gated candidates (150-360s). Mixes
Hardtek (HARDTEK_ prefix) and SoundCloud pool. Copies selected files to
phase1/music/partNN_music_01..05.{ext}. Stitcher (P1-R/P1-AA) auto-detects
these by the partNN_music_NN.* pattern.

CLI
---
    python phase1/music/rotate_fresh_stems.py --part 5
    python phase1/music/rotate_fresh_stems.py --part 5 --seed 42
    python phase1/music/rotate_fresh_stems.py --part 5 --dry-run
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "phase1" / "music" / "library"
MUSIC = ROOT / "phase1" / "music"
FFPROBE = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"
MIN_S, MAX_S = 150.0, 360.0
SLOTS = 5


def probe_dur(p: Path) -> float:
    try:
        r = subprocess.run(
            [str(FFPROBE), "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip() or "0")
    except Exception:
        return 0.0


def build_candidates() -> list[tuple[Path, float]]:
    cache_path = LIB / "_durations.json"
    cache: dict[str, float] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            cache = {}
    out: list[tuple[Path, float]] = []
    for p in LIB.glob("*.mp3"):
        key = p.name
        d = cache.get(key)
        if d is None or d <= 0:
            d = probe_dur(p)
            cache[key] = d
        if MIN_S <= d <= MAX_S:
            out.append((p, d))
    cache_path.write_text(json.dumps(cache, indent=2))
    return out


def pick_slots(part: int, seed: int | None) -> list[tuple[Path, float]]:
    cands = build_candidates()
    if len(cands) < SLOTS:
        raise RuntimeError(f"only {len(cands)} candidates, need {SLOTS}")
    r = random.Random(seed if seed is not None else part * 7919)
    # 60/40 bias: for each slot, pick from hardtek pool or full pool
    hardtek = [c for c in cands if c[0].name.startswith("HARDTEK_")]
    rest = [c for c in cands if not c[0].name.startswith("HARDTEK_")]
    picks: list[tuple[Path, float]] = []
    used: set[Path] = set()
    for i in range(SLOTS):
        pool = hardtek if (i % 2 == 0 and hardtek) else rest
        pool = [c for c in pool if c[0] not in used]
        if not pool:
            pool = [c for c in cands if c[0] not in used]
        pick = r.choice(pool)
        picks.append(pick)
        used.add(pick[0])
    return picks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    picks = pick_slots(a.part, a.seed)
    print(f"[rotate] Part {a.part} picks:")
    for i, (p, d) in enumerate(picks, 1):
        print(f"  slot {i:02d}  {d:5.1f}s  {p.name}")

    if a.dry_run:
        print("[rotate] dry-run: no files written")
        return 0

    manifest = []
    for i, (p, d) in enumerate(picks, 1):
        dst = MUSIC / f"part{a.part:02d}_music_{i:02d}.mp3"
        shutil.copy2(p, dst)
        manifest.append({"slot": i, "src": p.name, "dur_s": round(d, 2),
                         "dst": dst.name})
        # bust any cached beats.json for that slot (stitcher will recompute)
        for stale in MUSIC.glob(f"part{a.part:02d}_music_{i:02d}*.beats.json"):
            stale.unlink(missing_ok=True)
    man_path = MUSIC / f"part{a.part:02d}_fresh_stems.json"
    man_path.write_text(json.dumps({"part": a.part, "seed": a.seed,
                                    "picks": manifest}, indent=2))
    # Also bust the stitched cache so stitcher rebuilds
    for stale in (MUSIC / "_stitched").glob(f"part{a.part:02d}_*"):
        stale.unlink(missing_ok=True)
    print(f"[rotate] wrote 5 stems + manifest {man_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
