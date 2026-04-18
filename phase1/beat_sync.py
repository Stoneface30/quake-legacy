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
from typing import Any, Iterable, Optional

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
    # v11 (flow planner)
    "plan_flow_cuts",
    "classify_section_shape",
    "write_flow_plan_json",
    # legacy
    "load_beats",
    "nearest_beat",
    "snap_to_beat",
    "snap_xfade_offsets",
    "find_beats_file",
]


# ---------------------------------------------------------------------------
# v11 API — flow-driven, event-aware, tier is SOFT sort key (Rule P1-CC v2)
# ---------------------------------------------------------------------------

# Tier tie-break ordering (higher tier preferred on flow-fit ties).
_TIER_RANK = {"T1": 3, "T2": 2, "T3": 1}


def classify_section_shape(section: dict, drops: list[dict]) -> str:
    """Infer a section's role (build/drop/break/intro/outro/mid).

    msaf/librosa only give opaque labels ("A", "seg_0", ...). We project
    them onto Rule P1-CC v2 semantic shapes using:
      * explicit drop timestamps inside the section → "drop"
      * very early in track (first 15 %)            → "intro"
      * very late  in track (last 15 %)             → "outro"
      * otherwise use section length as proxy:
          > 45 s → "break"   (downtime)
          else   → "build"
    """
    s_start = float(section.get("start", 0.0))
    s_end = float(section.get("end", s_start))
    s_len = max(0.0, s_end - s_start)
    for d in drops or []:
        dt = float(d.get("t", -1.0))
        if s_start <= dt < s_end:
            return "drop"
    return "build" if s_len <= 45.0 else "break"


def _annotate_sections(structure: dict) -> list[dict]:
    """Return sections with a `shape` field added + intro/outro edge tags."""
    sections = list(structure.get("sections") or [])
    drops = list(structure.get("drops") or [])
    duration = float(structure.get("duration_s") or 0.0)
    if duration <= 0 and sections:
        duration = float(sections[-1].get("end", 0.0))
    annotated: list[dict] = []
    for i, s in enumerate(sections):
        shape = classify_section_shape(s, drops)
        # Intro/outro overrides based on position.
        if i == 0 and duration > 0 and float(s.get("end", 0.0)) <= 0.20 * duration:
            shape = "intro"
        elif i == len(sections) - 1 and duration > 0 and \
                float(s.get("start", 0.0)) >= 0.80 * duration:
            shape = "outro"
        annotated.append({**s, "shape": shape})
    return annotated


def _event_density(events: list) -> float:
    """Mean confidence-weighted event count per clip."""
    if not events:
        return 0.0
    return sum(getattr(e, "score", 0.0) for e in events) / max(1, len(events))


def _flow_fit(clip_events: list, shape: str) -> float:
    """Score a clip vs a section shape. Higher = better fit."""
    if not clip_events:
        # no recognized event → only good for break / outro / soft fills
        return {"break": 0.8, "outro": 0.7, "intro": 0.6, "build": 0.2, "drop": 0.0}\
            .get(shape, 0.3)
    top = clip_events[0]
    etype = top.event_type
    conf = top.confidence
    if shape == "drop":
        if etype in ("player_death", "rocket_impact", "grenade_direct",
                     "grenade_explode"):
            return 1.0 * conf
        if etype in ("rail_fire", "rocket_fire"):
            return 0.7 * conf
        return 0.3 * conf
    if shape == "build":
        if etype.endswith("_fire"):
            return 0.9 * conf
        if etype == "player_death":
            return 0.4 * conf  # waste a death on build — penalize
        return 0.5 * conf
    if shape == "break":
        # Reward quiet clips in break sections.
        density = _event_density(clip_events)
        return max(0.1, 1.0 - density)
    if shape == "intro":
        return 0.6
    if shape == "outro":
        return 0.6 + 0.3 * conf
    return 0.4


def _nearest_downbeat(t: float, downbeats: list[dict]) -> Optional[dict]:
    """Return the downbeat dict closest to `t`, or None."""
    if not downbeats:
        return None
    return min(downbeats, key=lambda d: abs(float(d.get("t", 0.0)) - t))


def plan_flow_cuts(
    clip_events: dict,
    music_structure: dict,
    clip_tier_map: dict,
    intro_offset: float = 13.0,
    shift_cap: float = 0.4,
    min_playable_s: float = 2.0,
) -> list[dict]:
    """Flow-driven cut plan (Rule P1-CC v2).

    Walks music sections in time order. For each section, scores available
    clips by (flow_fit(clip_events, section.shape), tier_rank). Best clip
    is placed in that section. Downbeat target = downbeat closest to the
    section center (or section_start for drops).

    Args:
        clip_events:     { Path|str → list[GameEvent] } (top events first).
        music_structure: output of analyze_music() (sections, downbeats,
                         drops, cut_candidates, duration_s).
        clip_tier_map:   { Path|str → "T1" | "T2" | "T3" }
        intro_offset:    seconds of PANTHEON + title-card before body.
        shift_cap:       max absolute shift (seconds) absorbed into trims.
        min_playable_s:  min clip playable body after adjustments.

    Returns list[BeatCut] in TIME order (not clip order). Each BeatCut:
        {
          "clip":            str,
          "tier":            "T1"|"T2"|"T3"|None,
          "section_shape":   str,
          "section_start":   float,
          "event_type":      str | None,
          "event_conf":      float,
          "target_downbeat": float | None,   # absolute (music-timeline)
          "shift":           float,          # seconds; + = delay clip start
          "head_trim_adjust":float,
          "tail_trim_adjust_prev":float,
          "tag":             "TIGHT"|"WEAK_ALIGN"|"SKIP_ALIGN",
          "flow_fit":        float,
        }
    """
    sections = _annotate_sections(music_structure)
    downbeats = list(music_structure.get("downbeats") or [])
    duration = float(music_structure.get("duration_s") or 0.0)
    if not sections:
        # Degrade: synthesize one "mid" section covering the whole track.
        sections = [{"start": 0.0, "end": max(duration, 1.0),
                     "label": "all", "shape": "build"}]

    # Normalize keys to strings for lookups.
    events_by_str: dict[str, list] = {str(k): v for k, v in (clip_events or {}).items()}
    tier_by_str: dict[str, str] = {str(k): v for k, v in (clip_tier_map or {}).items()}

    available: set[str] = set(events_by_str.keys()) | set(tier_by_str.keys())
    cuts: list[dict] = []

    for section in sections:
        if not available:
            break
        shape = str(section.get("shape", "build"))
        s_start = float(section.get("start", 0.0))
        s_end = float(section.get("end", s_start))
        # Score every available clip vs this section.
        scored: list[tuple[float, int, str]] = []
        for path in available:
            events = events_by_str.get(path, [])
            tier = tier_by_str.get(path, "T2")
            fit = _flow_fit(events, shape)
            rank = _TIER_RANK.get(tier, 0)
            scored.append((fit, rank, path))
        if not scored:
            continue
        # Sort by flow_fit desc, then tier rank desc, then path for stability.
        scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
        best_fit, best_rank, best_path = scored[0]

        # Target downbeat: start of section for drops, center otherwise.
        anchor = s_start if shape in ("drop", "intro") else 0.5 * (s_start + s_end)
        # Absolute time in music timeline (sections already are in music time).
        target_db = _nearest_downbeat(anchor, downbeats)
        target_t: Optional[float] = (
            float(target_db["t"]) if target_db is not None else anchor
        )

        # Shift: we'd like the event peak to land on target_t. We don't know
        # where the clip sits in the body yet (that's the stitcher's job),
        # so we record target_t and shift=0 here; the render pass will
        # resolve it into trim deltas.
        events = events_by_str.get(best_path, [])
        etype: Optional[str] = events[0].event_type if events else None
        econf = float(events[0].confidence) if events else 0.0

        cuts.append({
            "clip": best_path,
            "tier": tier_by_str.get(best_path),
            "section_shape": shape,
            "section_start": s_start,
            "section_end": s_end,
            "event_type": etype,
            "event_conf": econf,
            "target_downbeat": target_t,
            "shift": 0.0,                    # resolved in render pass
            "head_trim_adjust": 0.0,
            "tail_trim_adjust_prev": 0.0,
            "tag": "TIGHT" if econf >= 0.72 else ("WEAK_ALIGN" if econf > 0.0 else "SKIP_ALIGN"),
            "flow_fit": float(best_fit),
        })
        available.discard(best_path)

    return cuts


def write_flow_plan_json(
    cuts: list[dict],
    part: int,
    out_dir: Path | str | None = None,
) -> Path:
    """Write the flow plan to `output/partNN_flow_plan.json`."""
    out_dir = Path(out_dir) if out_dir else (Path(__file__).resolve().parent.parent / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"part{part:02d}_flow_plan.json"
    tight = sum(1 for c in cuts if c.get("tag") == "TIGHT")
    summary = {
        "part": part,
        "cuts": cuts,
        "stats": {
            "total": len(cuts),
            "tight": tight,
            "weak": sum(1 for c in cuts if c.get("tag") == "WEAK_ALIGN"),
            "skip": sum(1 for c in cuts if c.get("tag") == "SKIP_ALIGN"),
            "by_shape": {
                shp: sum(1 for c in cuts if c.get("section_shape") == shp)
                for shp in ("intro", "build", "drop", "break", "outro")
            },
        },
    }
    out.write_text(json.dumps(summary, indent=2))
    return out


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
