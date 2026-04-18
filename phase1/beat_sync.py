"""
Beat-sync — Rule P1-V (Part 6 v8, 2026-04-18).

Reads pre-computed librosa beat grids (phase1/music/<track>.beats.json) and
snaps body-chunk xfade seams to the nearest music beat so that transitions
land on-beat.

Core entry points:
    load_beats(beats_json_path)           -> list[float]          beat times in music-absolute seconds
    snap_xfade_offsets(durs, beats, xfade, intro_offset, max_shift)
                                          -> list[float]          per-seam xfade offsets (body-absolute)

Golden rule (P1-S): beat-sync lives on the JOIN, not inside the clip.
Chunk durations are NEVER modified by this module. Only the xfade offset
parameter (where the seam falls visually) is shifted ±max_shift seconds.

The ffmpeg xfade chain built in render_part_v6.assemble_body_with_xfades
uses cumulative body-absolute offsets. snap_xfade_offsets returns the same
shape, rounded to the nearest beat whenever a beat exists within
±max_shift of the natural seam.

Bounds are enforced so the offsets stay monotonic and each chunk keeps
at least 1.0 s of exclusive screen time.
"""
from __future__ import annotations

import bisect
import json
from pathlib import Path
from typing import List, Optional


def load_beats(beats_json_path: Path) -> List[float]:
    """Load pre-computed beat times (music-absolute seconds) from a sidecar JSON.

    Sidecar format (produced by phase1/music/beat_cache.py or librosa dump):
        {
            "track_path": "...",
            "duration": 313.85,
            "tempo": 117.45,
            "beat_times": [0.74, 1.28, ...]
        }
    """
    data = json.loads(Path(beats_json_path).read_text(encoding="utf-8"))
    beats = list(data.get("beat_times") or [])
    if not beats:
        raise ValueError(f"{beats_json_path} has empty beat_times")
    return beats


def nearest_beat(t: float, beats: List[float]) -> float:
    """Return the beat time closest to t (no distance limit)."""
    if not beats:
        return t
    i = bisect.bisect_left(beats, t)
    candidates = []
    if i < len(beats):
        candidates.append(beats[i])
    if i > 0:
        candidates.append(beats[i - 1])
    return min(candidates, key=lambda b: abs(b - t))


def snap_to_beat(
    t: float,
    beats: List[float],
    max_shift: float = 0.300,
) -> tuple[float, bool]:
    """Snap t to nearest beat if within ±max_shift seconds.

    Returns (snapped_t, did_snap). did_snap is False when no beat was
    inside the window, in which case snapped_t == t.
    """
    if not beats:
        return t, False
    b = nearest_beat(t, beats)
    if abs(b - t) <= max_shift:
        return b, True
    return t, False


def snap_xfade_offsets(
    durs: List[float],
    beats: List[float],
    xfade: float,
    intro_offset: float = 15.0,
    max_shift: float = 0.300,
    min_clip_visible: float = 1.0,
) -> tuple[List[float], dict]:
    """Compute beat-snapped xfade offsets for an N-chunk body.

    Args:
        durs: chunk durations in seconds (len N).
        beats: music beat times (music-absolute seconds).
        xfade: crossfade length (seconds, same for every seam).
        intro_offset: seconds before the body starts (PANTHEON + title card).
        max_shift: maximum ±snap window in seconds.
        min_clip_visible: minimum exclusive screen time per chunk after snap.

    Returns:
        (offsets, stats) where offsets is a list of N-1 body-absolute xfade
        start times (matches the cumulative-offset convention used by
        assemble_body_with_xfades), and stats is a dict with snap hit-rate.

    Logic: for each seam i (1..N-1), compute the natural body-absolute offset
    O_i = sum(durs[0..i-1]) - i*xfade. Add intro_offset to get music time,
    snap to nearest beat within ±max_shift, subtract intro_offset back, then
    clamp so the offset stays inside [prev_offset + min_clip_visible,
    prev_offset + durs[i] - xfade - 0.1].
    """
    N = len(durs)
    if N < 2:
        return [], {"n_seams": 0, "snapped": 0, "total_shift": 0.0}

    offsets: List[float] = []
    snapped_count = 0
    total_shift = 0.0
    prev_offset = 0.0

    for i in range(1, N):
        # Natural seam position is relative to the PREVIOUS seam so that snaps
        # compound correctly. Chunk i-1 occupies [prev_offset, natural], so the
        # next natural xfade-in is prev_offset + durs[i-1] - xfade.
        if i == 1:
            natural = durs[0] - xfade
        else:
            natural = prev_offset + durs[i - 1] - xfade
        music_t = intro_offset + natural
        snapped_music, did_snap = snap_to_beat(music_t, beats, max_shift)
        target = snapped_music - intro_offset

        # Monotonicity + visibility bounds.
        # Seam i sits between chunk i-1 and chunk i. Between prev_offset (seam
        # i-1) and this seam, chunk i-1 occupies the screen — so the duration
        # that bounds this seam is durs[i-1], NOT durs[i]. A tiny epsilon keeps
        # the xfade input from running off the end of the source.
        EPS = 0.02
        lo = prev_offset + min_clip_visible
        hi = prev_offset + durs[i - 1] - xfade - EPS
        if i == 1:
            # For the first seam, prev_offset is 0 so hi collapses to
            # durs[0] - xfade - EPS, which equals the natural offset minus EPS.
            # Give the snapper a little headroom by allowing up to durs[0] - xfade.
            hi = durs[0] - xfade - EPS
            lo = max(min_clip_visible, 0.0)
        clamped = max(lo, min(target, hi))

        # If clamping killed the snap, mark as non-snap
        if did_snap and abs(clamped - target) > 0.01:
            did_snap = False

        if did_snap:
            snapped_count += 1
            total_shift += abs(clamped - natural)

        offsets.append(clamped)
        prev_offset = clamped

    stats = {
        "n_seams": N - 1,
        "snapped": snapped_count,
        "snap_rate": snapped_count / max(1, N - 1),
        "total_shift": total_shift,
    }
    return offsets, stats


def find_beats_file(music_path: Path) -> Optional[Path]:
    """Locate the sidecar beats.json for a given music file.

    Convention: `<music_path>.beats.json` sits next to the track. Returns None
    if the sidecar is missing (caller falls back to hard cuts).
    """
    sidecar = music_path.with_suffix(music_path.suffix + ".beats.json")
    return sidecar if sidecar.exists() else None


__all__ = [
    "load_beats",
    "nearest_beat",
    "snap_to_beat",
    "snap_xfade_offsets",
    "find_beats_file",
]
