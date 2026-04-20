"""creative_suite/engine/music_contract.py

Enforce the music full-length contract (Rules P1-R + P1-AA).

Every Part must have music that covers the FULL body duration.  If the
selected tracks are shorter than the body, additional tracks must be queued
until coverage is complete.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from creative_suite.music_match import compute_match, get_track_duration


def validate_music_coverage(
    music_files: list[Path],
    body_duration_s: float,
) -> dict[str, Any]:
    """Check that music_files provide full coverage of body_duration_s.

    Returns:
        {
          "covered": bool,
          "total_music_s": float,
          "body_duration_s": float,
          "full_length_pct": float,
          "needs_truncation": bool,  # True if last track extends past body end
          "tracks": [
            {"path": str, "duration_s": float, "starts_at_s": float,
             "full_length_pct": float}
          ],
          "coverage_gap_s": float,   # seconds uncovered (0 if covered)
          "warnings": [str],
        }
    """
    warnings: list[str] = []
    tracks: list[dict[str, Any]] = []
    total_music_s: float = 0.0

    for f in music_files:
        duration = get_track_duration(f)

        if duration is None:
            warnings.append(
                f"Could not read duration for {f.name} "
                "(mutagen may not be installed or file is unreadable)"
            )
            track_entry: dict[str, Any] = {
                "path": str(f),
                "duration_s": None,
                "starts_at_s": total_music_s,
                "full_length_pct": None,
            }
        else:
            track_pct = (
                compute_match(duration, body_duration_s)["full_length_pct"]
                if body_duration_s > 0
                else None
            )
            track_entry = {
                "path": str(f),
                "duration_s": round(duration, 3),
                "starts_at_s": round(total_music_s, 3),
                "full_length_pct": track_pct,
            }
            total_music_s += duration

        tracks.append(track_entry)

        # Stop accumulating once we have enough coverage
        if total_music_s >= body_duration_s:
            break

    covered = total_music_s >= body_duration_s
    coverage_gap_s = max(0.0, body_duration_s - total_music_s)
    needs_truncation = total_music_s > body_duration_s

    full_length_pct: Optional[float] = None
    if body_duration_s > 0:
        full_length_pct = round(total_music_s / body_duration_s * 100, 1)

    return {
        "covered": covered,
        "total_music_s": round(total_music_s, 3),
        "body_duration_s": body_duration_s,
        "full_length_pct": full_length_pct,
        "needs_truncation": needs_truncation,
        "tracks": tracks,
        "coverage_gap_s": round(coverage_gap_s, 3),
        "warnings": warnings,
    }


def _read_body_duration(part: int, output_dir: Path) -> Optional[float]:
    """Read body_duration from flow_plan.json (flat or subdir layout)."""
    nn = f"{part:02d}"
    candidates = [
        output_dir / f"part{nn}_flow_plan.json",
        output_dir / f"part{nn}" / "flow_plan.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                val = data.get("body_duration")
                if val is not None:
                    return float(val)
            except (OSError, ValueError, TypeError):
                pass
    return None


def _resolve_music_files(part: int, music_dir: Path) -> list[Path]:
    """Collect ordered music files for a part (intro, main, outro)."""
    if not music_dir.exists():
        return []

    import re
    nn = f"{part:02d}"
    music_exts = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    pattern = re.compile(
        r"^part(\d{2})_(intro_music|outro_music|music)(?:_.+)?$",
        re.IGNORECASE,
    )

    # Bucket by role so ordering is deterministic: intro → main → outro
    role_order = {"intro_music": 0, "music": 1, "outro_music": 2}
    found: list[tuple[int, Path]] = []

    for f in sorted(music_dir.iterdir()):
        if f.suffix.lower() not in music_exts:
            continue
        m = pattern.match(f.stem)
        if not m:
            continue
        if int(m.group(1)) != part:
            continue
        role_key = m.group(2).lower()
        found.append((role_order.get(role_key, 1), f))

    found.sort(key=lambda x: x[0])
    return [f for _, f in found]


def check_part_music(part: int, config: Any) -> dict[str, Any]:
    """Read music files for part from config; check coverage against body_duration.

    Returns same shape as validate_music_coverage, or {"error": "..."} if
    required data is missing.
    """
    music_dir: Path = config.phase1_music_dir

    output_dir_override = os.getenv("CS_PHASE1_OUTPUT_DIR")
    if output_dir_override:
        output_dir = Path(output_dir_override)
    else:
        output_dir = config.phase1_output_dir

    body_duration = _read_body_duration(part, output_dir)
    if body_duration is None:
        return {"error": "no flow plan"}

    music_files = _resolve_music_files(part, music_dir)
    return validate_music_coverage(music_files, body_duration)
