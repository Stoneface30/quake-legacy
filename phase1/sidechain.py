"""
Sidechain ducking helper per docs/research/audio-montage-2026-04-18.md §D.

Builds an ffmpeg filter_complex fragment that ducks `music_label` under every
transient in `game_label`, so grenade hits and rocket impacts punch through the
music bed without needing manual automation.

Public API:
    build_sidechain_filter_chain(music_label, game_label, threshold=0.05, ...)
        -> str          ffmpeg filter-complex fragment, ends with [mix] output
    auto_tune_threshold_from_ebur128(music_stem_path) -> float
        Map music integrated LUFS to a sensible sidechaincompress threshold.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from phase1.config import Config


def build_sidechain_filter_chain(
    music_label: str,
    game_label: str,
    threshold: float = 0.05,
    ratio: int = 8,
    attack_ms: int = 5,
    release_ms: int = 250,
) -> str:
    """Return a filter-complex string that mixes game + ducked music.

    Input labels should be used WITHOUT brackets (e.g. "music"), this helper
    wraps them. Output label is `[mix]`.

    Semantics:
        * level_sc=1.0 feeds the raw game signal as the sidechain key
        * duration=first lets the music define the duration (Rule P1-O)
          — caller is responsible for apad'ing game to match.
    """
    return (
        f"[{music_label}][{game_label}]sidechaincompress="
        f"threshold={threshold}:ratio={ratio}:"
        f"attack={attack_ms}:release={release_ms}:"
        f"makeup=1:level_sc=1.0[music_ducked];"
        f"[music_ducked][{game_label}]amix=inputs=2:duration=first:normalize=0[mix]"
    )


def _parse_integrated_lufs(stderr: str) -> float | None:
    """Extract `I:  -XX.X LUFS` from ffmpeg ebur128 stderr."""
    m = re.search(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", stderr)
    if m:
        return float(m.group(1))
    return None


def auto_tune_threshold_from_ebur128(music_stem_path: Path | str) -> float:
    """Map music LUFS to a sidechain threshold.

    Mapping (per audio-montage brief §D):
        quiet beds  (< -18 LUFS) -> 0.03     (gentler duck)
        normal                    -> 0.05
        loud hardtekk (> -10)    -> 0.08     (aggressive duck)

    Returns 0.05 (default) if measurement fails.
    """
    cfg = Config()
    p = Path(music_stem_path)
    if not p.exists():
        return 0.05
    try:
        proc = subprocess.run(
            [
                str(cfg.ffmpeg_bin),
                "-nostats",
                "-hide_banner",
                "-i",
                str(p),
                "-filter_complex",
                "ebur128=peak=true",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return 0.05
    lufs = _parse_integrated_lufs(proc.stderr)
    if lufs is None:
        return 0.05
    if lufs < -18.0:
        return 0.03
    if lufs > -10.0:
        return 0.08
    return 0.05


__all__ = [
    "build_sidechain_filter_chain",
    "auto_tune_threshold_from_ebur128",
]


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) >= 2:
        print(f"threshold={auto_tune_threshold_from_ebur128(sys.argv[1])}")
    else:
        print(build_sidechain_filter_chain("music", "game"))
