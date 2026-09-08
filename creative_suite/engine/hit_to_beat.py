"""HITS ARE BEATS — exact frag-to-beat placement for demo-derived clips.

For V2 generated clips the frag offsets are exact parser truth (charter §13),
so no audio inference is involved:

    timeline_clip_start = chosen_music_beat - primary_frag_offset

Multikill placement scores EVERY kill offset against the beat grid (§17 of
the original charter): the primary kill is anchored to a strong beat, and the
alignment that also lands secondary kills near beats/half-beats wins. Natural
gameplay timing is never altered — only WHERE the clip starts on the timeline.

Downbeats from music_analysis.db are every-4th-beat estimates, NOT proven
meter. They are consumed here strictly as BAR_GRID_ESTIMATE: a mild bonus,
never a hard constraint.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PRIMARY_WEIGHT = 4.0
SECONDARY_WEIGHT = 1.0
HALF_BEAT_FACTOR = 0.5      # half-beat hits score half of an on-beat hit
BAR_GRID_BONUS = 0.25       # mild: the bar grid is an ESTIMATE


@dataclass
class Placement:
    timeline_start_s: float
    anchor_beat_s: float
    score: float
    per_kill: list = field(default_factory=list)  # (offset_ms, nearest_gap_ms)


def _nearest(t: float, grid: list[float]) -> float:
    """Distance in seconds from t to the nearest grid point."""
    if not grid:
        return float("inf")
    lo, hi = 0, len(grid) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if grid[mid] < t:
            lo = mid + 1
        else:
            hi = mid
    best = abs(grid[lo] - t)
    if lo > 0:
        best = min(best, abs(grid[lo - 1] - t))
    return best


def kill_alignment_score(kill_times_s: list[float], primary_idx: int,
                         beats: list[float],
                         bar_grid_estimate: list[float] | None = None) -> float:
    """Score an absolute timeline alignment of a clip's kills vs a beat grid.

    Full weight when a kill sits on a beat, decaying linearly to zero at half
    a beat interval away; half-beat positions score HALF_BEAT_FACTOR.
    """
    if len(beats) < 2:
        return 0.0
    interval = (beats[-1] - beats[0]) / (len(beats) - 1)
    half_grid = [b + interval / 2 for b in beats[:-1]]
    total = 0.0
    for i, t in enumerate(kill_times_s):
        w = PRIMARY_WEIGHT if i == primary_idx else SECONDARY_WEIGHT
        d_beat = _nearest(t, beats)
        d_half = _nearest(t, half_grid)
        on_beat = max(0.0, 1.0 - d_beat / (interval / 2))
        on_half = max(0.0, 1.0 - d_half / (interval / 2)) * HALF_BEAT_FACTOR
        s = max(on_beat, on_half)
        if bar_grid_estimate and i == primary_idx:
            if _nearest(t, bar_grid_estimate) < interval / 4:
                s += BAR_GRID_BONUS
        total += w * s
    return total


def place_clip(frag_offsets_ms: list[int], primary_offset_ms: int,
               beats_s: list[float],
               bar_grid_estimate_s: list[float] | None = None,
               search_window_s: tuple[float, float] | None = None,
               clip_duration_ms: int | None = None) -> Placement | None:
    """Choose the beat that anchors the primary frag, maximising whole-chain
    alignment. Returns the winning Placement (timeline_start >= 0 enforced).

    search_window_s restricts candidate anchor beats (e.g. to a drop section).
    """
    if not beats_s or not frag_offsets_ms:
        return None
    primary_s = primary_offset_ms / 1000.0
    offsets_s = [o / 1000.0 for o in frag_offsets_ms]
    try:
        primary_idx = frag_offsets_ms.index(primary_offset_ms)
    except ValueError:
        primary_idx = 0

    best: Placement | None = None
    for b in beats_s:
        if search_window_s and not (search_window_s[0] <= b <= search_window_s[1]):
            continue
        start = b - primary_s
        if start < 0:
            continue
        kill_abs = [start + o for o in offsets_s]
        score = kill_alignment_score(kill_abs, primary_idx, beats_s,
                                     bar_grid_estimate_s)
        if best is None or score > best.score:
            per_kill = [(int(o * 1000),
                         int(_nearest(start + o, beats_s) * 1000))
                        for o in offsets_s]
            best = Placement(timeline_start_s=start, anchor_beat_s=b,
                             score=score, per_kill=per_kill)
    return best
