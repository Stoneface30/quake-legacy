"""Backfill render_manifest.json for existing output/PartN.mp4 files.

Guesses the clip list used by preferring partNN.txt over partNN_styleX.txt.
If only styled variants exist, picks the newest by mtime and logs the guess.
"""
from __future__ import annotations

from pathlib import Path

from creative_suite.clips.parser import write_render_manifest
from creative_suite.config import Config


def guess_clip_list(part: int, clip_lists_dir: Path) -> Path | None:
    canonical = clip_lists_dir / f"part{part:02d}.txt"
    if canonical.exists():
        return canonical
    candidates = sorted(
        clip_lists_dir.glob(f"part{part:02d}_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main() -> None:
    cfg = Config()
    out = cfg.phase1_output_dir
    for mp4 in sorted(out.glob("Part*.mp4")):
        try:
            part = int(mp4.stem.replace("Part", "").split("_")[0])
        except ValueError:
            continue
        cl = guess_clip_list(part, cfg.phase1_clip_lists)
        if cl is None:
            print(f"SKIP {mp4.name}: no clip list found")
            continue
        m = write_render_manifest(mp4, cl, extras={"backfilled": True})
        print(f"OK   {mp4.name} -> {m.name} (from {cl.name})")


if __name__ == "__main__":
    main()
