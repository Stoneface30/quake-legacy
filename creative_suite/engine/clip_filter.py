# phase1/clip_filter.py
"""Tier 1 clip-removal: bridge between cinema suite overrides and render pipeline.

The cinema suite UI writes `output/part{NN}_overrides.txt` entries with
`removed=true` for clips the user wants dropped. This module reads those
entries and returns the set of chunk basenames to skip during body assembly.

Because music_stitcher sizes its queue from the filtered body duration
(render_part_v6.py line 1212+), removing clips automatically shortens the
music plan — no separate music regeneration step needed.
"""
from __future__ import annotations

from pathlib import Path

from creative_suite.overrides.file_io import read_overrides


def load_removed_chunks(part: int, output_dir: Path) -> set[str]:
    """Return the set of chunk basenames (e.g. `chunk_0014.mp4`) marked removed."""
    p = output_dir / f"part{part:02d}_overrides.txt"
    return {e.chunk for e in read_overrides(p) if e.removed}


def filter_chunks(chunks: list[Path], removed: set[str]) -> list[Path]:
    """Drop any Path whose .name is in `removed`. Preserves order of survivors."""
    if not removed:
        return list(chunks)
    return [c for c in chunks if c.name not in removed]
