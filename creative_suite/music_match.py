"""creative_suite/music_match.py

Music match % utility — importable + CLI.

Usage:
    python -m creative_suite.music_match <music_file> <body_duration_s>

Outputs JSON: { match_pct, full_length_pct, needs_truncation }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional


def compute_match(track_duration_s: float, body_duration_s: float) -> dict:
    """Return match_pct, full_length_pct, needs_truncation.

    match_pct      — overlap ratio: min(a,b)/max(a,b)*100.  100 = perfect fit.
    full_length_pct — track_duration / body_duration * 100.  >100 = track longer.
    needs_truncation — True when the track is shorter than the body.
    """
    if body_duration_s <= 0:
        return {"match_pct": None, "full_length_pct": None, "needs_truncation": None}
    match_pct = (
        min(track_duration_s, body_duration_s)
        / max(track_duration_s, body_duration_s)
        * 100
    )
    full_length_pct = track_duration_s / body_duration_s * 100
    needs_truncation = full_length_pct < 100.0
    return {
        "match_pct": round(match_pct, 1),
        "full_length_pct": round(full_length_pct, 1),
        "needs_truncation": needs_truncation,
    }


def get_track_duration(path: Path) -> Optional[float]:
    """Return audio duration in seconds using mutagen, or None on failure."""
    try:
        from mutagen import File as MutagenFile  # type: ignore[import-untyped]

        audio = MutagenFile(str(path))
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception:
        pass
    return None


# ── CLI entry point ──────────────────────────────────────────────────────────

def _main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python -m creative_suite.music_match <music_file> <body_duration_s>",
              file=sys.stderr)
        sys.exit(1)

    music_path = Path(sys.argv[1])
    try:
        body_duration_s = float(sys.argv[2])
    except ValueError:
        print(f"Error: body_duration_s must be a number, got {sys.argv[2]!r}", file=sys.stderr)
        sys.exit(1)

    duration = get_track_duration(music_path)
    if duration is None:
        print(f"Error: could not read duration from {music_path}", file=sys.stderr)
        sys.exit(1)

    result = compute_match(duration, body_duration_s)
    result["track_duration_s"] = round(duration, 3)
    result["body_duration_s"] = body_duration_s
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
