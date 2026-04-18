"""
Beat-sync v10 — tier-aware downbeat placement with anticipation cut.

Rewritten per Rule P1-Z / P1-CC and docs/research/*:
    - docs/research/audio-montage-2026-04-18.md §C
    - docs/research/beatmaker-2026-04-18.md §F, §G

The old (v9) module snapped seams to the nearest music *beat* grid. v10:
    * consumes `partNN_music_structure.json` (downbeats + drops + salience)
    * consumes `partNN_clip_peaks.json` (per-clip action-peak times)
    * pins each clip's action peak to the nearest tier-appropriate downbeat:
        T1 -> drops[]  (strongest-first)
        T2 -> cut_candidates.strong[]
        T3 -> cut_candidates.medium[]
    * uses the 33 ms (2 frame @ 60 fps) anticipation cut at every seam
    * absorbs alignment shift into trim adjustments, NOT speed changes
    * caps shift at ±0.4 s. Beyond that -> WEAK_ALIGN tag, fallback to nearest half-beat.

Public API:
    plan_beat_cuts(structure: dict, peaks: dict[str, float|None],
                   clips: list[dict]) -> list[dict]

`clips` is a list of {"path": str, "tier": "T1"|"T2"|"T3", "duration": float,
"head_trim": float, "tail_trim": float}. `peaks` maps clip path -> peak seconds
(or None if undetected).

Each returned seam dict:
    {
        "clip": str,
        "tier": str,
        "target_downbeat": float | None,   # music-absolute seconds
        "peak": float | None,              # clip-relative seconds
        "shift": float,                    # seconds, +right shifts later
        "head_trim_adjust": float,         # delta to clip.head_trim
        "tail_trim_adjust_prev": float,    # delta to previous clip.tail_trim
        "seam_cut_music_t": float | None,  # target_downbeat - 0.033
        "tag": "TIGHT" | "WEAK_ALIGN" | "SKIP_ALIGN",
    }

Legacy helpers `load_beats / snap_xfade_offsets / snap_to_beat / find_beats_file`
remain exported for back-compat with the v8 body-xfade code path.
"""
from __future__ import annotations

import bisect
import json
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Legacy API (v8/v9 — kept for back-compat with render_part_v6.py)
# ---------------------------------------------------------------------------


def load_beats(beats_json_path: Path) -> list[float]:
    data = json.loads(Path(beats_json_path).read_text(encoding="utf-8"))
    beats = list(data.get("beat_times") or [])
    if not beats:
        raise ValueError(f"{beats_json_path} has empty beat_times")
    return beats


def nearest_beat(t: float, beats: list[float]) -> float:
    if not beats:
        return t
    i = bisect.bisect_left(beats, t)
    candidates: list[float] = []
    if i < len(beats):
        candidates.append(beats[i])
    if i > 0:
        candidates.append(beats[i - 1])
    return min(candidates, key=lambda b: abs(b - t))


def snap_to_beat(
    t: float, beats: list[float], max_shift: float = 0.300
) -> tuple[float, bool]:
    if not beats:
        return t, False
    b = nearest_beat(t, beats)
    if abs(b - t) <= max_shift:
        return b, True
    return t, False


def snap_xfade_offsets(
    durs: list[float],
    beats: list[float],
    xfade: float,
    intro_offset: float = 15.0,
    max_shift: float = 0.300,
    min_clip_visible: float = 1.0,
) -> tuple[list[float], dict[str, Any]]:
    N = len(durs)
    if N < 2:
        return [], {"n_seams": 0, "snapped": 0, "total_shift": 0.0}
    offsets: list[float] = []
    snapped_count = 0
    total_shift = 0.0
    prev_offset = 0.0
    for i in range(1, N):
        if i == 1:
            natural = durs[0] - xfade
        else:
            natural = prev_offset + durs[i - 1] - xfade
        music_t = intro_offset + natural
        snapped_music, did_snap = snap_to_beat(music_t, beats, max_shift)
        target = snapped_music - intro_offset
        EPS = 0.02
        lo = prev_offset + min_clip_visible
        hi = prev_offset + durs[i - 1] - xfade - EPS
        if i == 1:
            hi = durs[0] - xfade - EPS
            lo = max(min_clip_visible, 0.0)
        clamped = max(lo, min(target, hi))
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


def find_beats_file(music_path: Path) -> Path | None:
    sidecar = music_path.with_suffix(music_path.suffix + ".beats.json")
    return sidecar if sidecar.exists() else None


# ---------------------------------------------------------------------------
# v10 API
# ---------------------------------------------------------------------------

ANTICIPATION_OFFSET = 0.033  # 2 frames @ 60 fps
MAX_SHIFT = 0.4
SHIFT_TRIM_CAP = 0.4


def _extract_pool(structure: dict[str, Any], tier: str) -> list[float]:
    """Return the pool of candidate music times for a given clip tier."""
    if tier == "T1":
        drops = structure.get("drops") or []
        # strongest first
        ordered = sorted(drops, key=lambda d: -float(d.get("strength", 0.0)))
        return [float(d["t"]) for d in ordered]
    cand = structure.get("cut_candidates") or {}
    if tier == "T2":
        return [float(t) for t in cand.get("strong", [])]
    if tier == "T3":
        return [float(t) for t in cand.get("medium", [])]
    # default: soft pool
    return [float(t) for t in cand.get("soft", [])]


def _all_beats(structure: dict[str, Any]) -> list[float]:
    return [float(b) for b in structure.get("beat_grid", [])]


def _pick_next(pool: list[float], used: set[float], after: float) -> float | None:
    """Pick the first unused candidate at or after `after` seconds."""
    best: float | None = None
    for t in sorted(pool):
        if t in used:
            continue
        if t >= after - 0.05:
            best = t
            break
    return best


def _half_beat_fallback(beats: list[float], target: float) -> float | None:
    """Return nearest half-beat to target, if beats available."""
    if len(beats) < 2:
        return None
    # Expand grid with half-beat midpoints
    extended: list[float] = []
    for i in range(len(beats) - 1):
        extended.append(beats[i])
        extended.append(0.5 * (beats[i] + beats[i + 1]))
    extended.append(beats[-1])
    return min(extended, key=lambda b: abs(b - target))


def plan_beat_cuts(
    structure: dict[str, Any],
    peaks: dict[str, float | None],
    clips: list[dict[str, Any]],
    intro_offset: float = 13.0,
) -> list[dict[str, Any]]:
    """Compute the per-seam plan.

    Args:
        structure: output of analyze_music() — must contain downbeats/drops/cut_candidates.
        peaks:     dict clip_path -> clip-relative peak seconds (or None).
        clips:     ordered list with tier metadata. Each dict needs
                   {path, tier, duration, head_trim, tail_trim}.
        intro_offset: PANTHEON + title card offset before the body starts
                      (seconds). Default 13 (Rule P1-X: 5 + 8).

    Returns: list of seam dicts (one per clip). Iteration order matches input.
    """
    all_beats = _all_beats(structure)
    t_cursor = intro_offset
    seams: list[dict[str, Any]] = []
    used_targets: set[float] = set()

    # Per-clip pools are independent: T1 may use a drop; T2 may grab a strong
    # downbeat even if it's earlier than the next T1 drop. We still require
    # monotonicity in clip order by gating with `after=t_cursor` at pick time.
    pools: dict[str, list[float]] = {
        "T1": _extract_pool(structure, "T1"),
        "T2": _extract_pool(structure, "T2"),
        "T3": _extract_pool(structure, "T3"),
    }

    for idx, clip in enumerate(clips):
        path = str(clip["path"])
        tier = str(clip.get("tier", "T2"))
        dur = float(clip["duration"])
        head = float(clip.get("head_trim", 0.0))
        tail = float(clip.get("tail_trim", 0.0))
        peak = peaks.get(path)

        playable_start = t_cursor
        if peak is None:
            # No detectable peak — can't align. Skip alignment but advance cursor.
            seams.append(
                {
                    "clip": path,
                    "tier": tier,
                    "target_downbeat": None,
                    "peak": None,
                    "shift": 0.0,
                    "head_trim_adjust": 0.0,
                    "tail_trim_adjust_prev": 0.0,
                    "seam_cut_music_t": None,
                    "tag": "SKIP_ALIGN",
                }
            )
            t_cursor += max(0.0, dur - head - tail)
            continue

        playable_action = playable_start + (peak - head)
        pool = pools.get(tier, []) or pools["T2"]
        target = _pick_next(pool, used_targets, after=playable_action - MAX_SHIFT)
        if target is None:
            # Fallback: nearest half-beat across the full grid
            hb = _half_beat_fallback(all_beats, playable_action)
            tag = "WEAK_ALIGN" if hb is not None else "SKIP_ALIGN"
            if hb is None:
                seams.append(
                    {
                        "clip": path,
                        "tier": tier,
                        "target_downbeat": None,
                        "peak": float(peak),
                        "shift": 0.0,
                        "head_trim_adjust": 0.0,
                        "tail_trim_adjust_prev": 0.0,
                        "seam_cut_music_t": None,
                        "tag": "SKIP_ALIGN",
                    }
                )
                t_cursor += max(0.0, dur - head - tail)
                continue
            target = hb
        else:
            tag = "TIGHT"

        shift = target - playable_action
        if abs(shift) > MAX_SHIFT:
            # shift too large — try half-beat fallback
            hb = _half_beat_fallback(all_beats, playable_action)
            if hb is not None and abs(hb - playable_action) < abs(shift):
                target = hb
                shift = target - playable_action
            tag = "WEAK_ALIGN"

        # Absorb shift into trims (bounded by SHIFT_TRIM_CAP).
        head_adjust = 0.0
        tail_adjust_prev = 0.0
        if shift > 0:
            # clip must start later -> trim MORE head on this clip
            head_adjust = min(shift, SHIFT_TRIM_CAP)
        else:
            # clip must start earlier -> trim MORE tail on previous clip
            tail_adjust_prev = min(-shift, SHIFT_TRIM_CAP)

        used_targets.add(target)
        seam_cut_music_t = target - ANTICIPATION_OFFSET

        seams.append(
            {
                "clip": path,
                "tier": tier,
                "target_downbeat": float(target),
                "peak": float(peak),
                "shift": float(shift),
                "head_trim_adjust": float(head_adjust),
                "tail_trim_adjust_prev": float(tail_adjust_prev),
                "seam_cut_music_t": float(seam_cut_music_t),
                "tag": tag,
            }
        )

        # Update cursor using the (adjusted) effective clip duration.
        effective_dur = max(0.0, dur - (head + head_adjust) - tail)
        t_cursor = playable_start + effective_dur

    return seams


def write_beats_json(
    seams: list[dict[str, Any]],
    part: int,
    out_dir: Path | str | None = None,
) -> Path:
    """Write seams to `output/partNN_beats.json` and return the path."""
    out_dir = Path(out_dir) if out_dir else (Path(__file__).resolve().parent.parent / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"part{part:02d}_beats.json"
    summary = {
        "part": part,
        "seams": seams,
        "stats": {
            "total": len(seams),
            "tight": sum(1 for s in seams if s["tag"] == "TIGHT"),
            "weak": sum(1 for s in seams if s["tag"] == "WEAK_ALIGN"),
            "skip": sum(1 for s in seams if s["tag"] == "SKIP_ALIGN"),
        },
    }
    out.write_text(json.dumps(summary, indent=2))
    return out


__all__ = [
    # v10
    "plan_beat_cuts",
    "write_beats_json",
    "ANTICIPATION_OFFSET",
    # legacy
    "load_beats",
    "nearest_beat",
    "snap_to_beat",
    "snap_xfade_offsets",
    "find_beats_file",
]


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", required=True)
    ap.add_argument("--peaks", required=True)
    ap.add_argument("--clips", required=True, help="JSON list of clip dicts")
    ap.add_argument("--part", type=int, required=True)
    args = ap.parse_args()
    structure = json.loads(Path(args.structure).read_text())
    peaks = json.loads(Path(args.peaks).read_text())
    clips = json.loads(Path(args.clips).read_text())
    seams = plan_beat_cuts(structure, peaks, clips)
    path = write_beats_json(seams, args.part)
    print(f"wrote {path}")
