"""Tests for plan_flow_cuts_v2 — event-driven ordering + event-anchored seams.

Validates Rule P1-CC v2 + P1-Z v2 wiring: clip recognition drives body order
(drop events into drop sections) and seam placement (event peak lands on
nearest music downbeat minus anticipation lead).
"""
from __future__ import annotations

from pathlib import Path

from phase1.audio_onsets import GameEvent, EVENT_WEIGHTS
from phase1.beat_sync import (
    PlannedClip,
    plan_flow_cuts_v2,
    snap_seams_to_events,
    write_flow_plan_json,
)
from phase1.config import Config


def _evt(etype: str, t: float = 1.0, conf: float = 0.85) -> GameEvent:
    return GameEvent(
        t=t,
        event_type=etype,
        confidence=conf,
        weight=EVENT_WEIGHTS.get(etype, 0.3),
    )


def _make_structure(downbeats_t: list[float], drop_t: float | None = None,
                    duration: float = 200.0) -> dict:
    """Build a minimal music_structure dict sufficient for the planner."""
    # Two sections: first half build, second half "drop" (via drop timestamp).
    if drop_t is None:
        sections = [{"start": 0.0, "end": duration, "label": "A"}]
        drops: list[dict] = []
    else:
        mid = drop_t - 5.0
        sections = [
            {"start": 0.0, "end": mid, "label": "A"},                 # build
            {"start": mid, "end": duration, "label": "B"},            # drop
        ]
        drops = [{"t": drop_t, "strength": 0.95}]
    return {
        "duration_s": duration,
        "bpm_global": 120.0,
        "beat_grid": [float(t) for t in downbeats_t],
        "downbeats": [{"t": float(t), "bar": i, "salience": 0.8}
                      for i, t in enumerate(downbeats_t)],
        "sections": sections,
        "drops": drops,
        "cut_candidates": {"strong": downbeats_t, "medium": [], "soft": []},
    }


# --- ORDERING ---------------------------------------------------------------


def test_drop_event_routed_to_drop_section():
    """Clip with player_death lands in the drop bucket; silent clip in build."""
    cfg = Config()
    structure = _make_structure(downbeats_t=[10.0, 13.0, 16.0], drop_t=13.0)
    chunks_with_events = [
        (Path("clip_A_silent.mp4"), 5.0, "T3", []),
        (Path("clip_B_rocket.mp4"), 5.0, "T2", [_evt("rocket_fire", t=0.8)]),
        (Path("clip_C_death.mp4"),  5.0, "T1", [_evt("player_death", t=1.5)]),
    ]
    reordered, _ = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    roles = {pc.chunk.name: pc.section_role for pc in reordered}
    assert roles["clip_C_death.mp4"] == "drop"
    assert roles["clip_A_silent.mp4"] == "build"
    # rocket_fire is NOT a high-weight drop type (only rocket_impact is) —
    # so clip_B goes to build.
    assert roles["clip_B_rocket.mp4"] == "build"


def test_high_weight_rocket_impact_also_drops():
    cfg = Config()
    structure = _make_structure(downbeats_t=[10.0, 13.0, 16.0], drop_t=13.0)
    chunks_with_events = [
        (Path("clip_X.mp4"), 5.0, "T2", [_evt("rocket_impact", t=0.5)]),
        (Path("clip_Y.mp4"), 5.0, "T3", []),
    ]
    reordered, _ = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    roles = {pc.chunk.name: pc.section_role for pc in reordered}
    assert roles["clip_X.mp4"] == "drop"


def test_no_event_goes_to_build_or_break():
    cfg = Config()
    structure = _make_structure(downbeats_t=[10.0, 13.0], drop_t=None)
    chunks_with_events = [
        (Path("silent1.mp4"), 5.0, "T3", []),
        (Path("silent2.mp4"), 5.0, "T3", []),
    ]
    reordered, _ = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    for pc in reordered:
        assert pc.top_event is None
        assert pc.section_role in ("build", "break")


# --- SEAM PLACEMENT ---------------------------------------------------------


def test_seam_places_event_peak_near_downbeat():
    """After plan_flow_cuts_v2, clip B's event peak should land within 50 ms
    of the nearest downbeat minus 33 ms anticipation."""
    cfg = Config()
    # Downbeats at 15, 18, 21 seconds (music-absolute, i.e. relative to t=0
    # at the start of the song which starts at intro_offset=13 in the output).
    # Body-absolute = music-absolute - intro_offset.
    # Naive seam for a 5s clip_A, xfade=0.4 → body-offset 4.6. Music-abs 17.6.
    # Event at t=1.0 in clip_B → music-abs of peak = 17.6 + 1.0 = 18.6 → nearest
    # downbeat 18.0 → shift = -0.6 (too big? shift is 0.6s > 0.4 max).
    # Use downbeats 18.6 to keep within max_shift:
    downbeats = [15.0, 18.6, 22.0]
    structure = _make_structure(downbeats_t=downbeats, drop_t=None)

    chunks_with_events = [
        (Path("A.mp4"), 5.0, "T2", [_evt("rocket_fire", t=1.2)]),
        (Path("B.mp4"), 5.0, "T1", [_evt("player_death", t=1.0)]),
    ]
    reordered, seam_offsets = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
        anticipation_ms=33,
    )
    assert len(seam_offsets) == 1
    seam = seam_offsets[0]
    assert seam is not None
    # B's peak in music-absolute = intro_offset + seam + event_t
    b = next(pc for pc in reordered if pc.chunk.name == "B.mp4")
    assert b.top_event is not None
    music_peak_t = 13.0 + seam + b.top_event.t
    # Should be near 18.6 - 0.033 = 18.567
    nearest_db = min(downbeats, key=lambda d: abs(d - music_peak_t))
    assert abs(music_peak_t - (nearest_db - 0.033)) < 0.05, \
        f"music_peak_t={music_peak_t} nearest_db={nearest_db}"


def test_seam_falls_back_to_naive_when_no_event():
    """When the clip after the seam has no recognized event, fall back to
    naive cumulative seam placement."""
    cfg = Config()
    structure = _make_structure(downbeats_t=[10.0, 13.0], drop_t=None)
    chunks_with_events = [
        (Path("A.mp4"), 5.0, "T2", [_evt("rocket_fire", t=1.2)]),
        (Path("B.mp4"), 5.0, "T3", []),  # no event
    ]
    reordered, seam_offsets = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    # Naive seam = clip_A.duration - xfade = 5.0 - 0.4 = 4.6 (clamped by EPS=0.02
    # to 4.58). Anchor must be "naive" since no event is anchorable.
    assert 4.55 <= seam_offsets[0] <= 4.61
    # And its meta should be naive.
    anchor = getattr(reordered[0], "_seam_meta", {}).get("anchor")
    assert anchor == "naive"


def test_seam_falls_back_when_no_downbeats():
    """No downbeats → naive only."""
    cfg = Config()
    structure = _make_structure(downbeats_t=[], drop_t=None)
    chunks_with_events = [
        (Path("A.mp4"), 5.0, "T2", [_evt("rocket_fire", t=1.2)]),
        (Path("B.mp4"), 5.0, "T1", [_evt("player_death", t=1.0)]),
    ]
    _, seam_offsets = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    assert 4.55 <= seam_offsets[0] <= 4.61


# --- JSON SCHEMA ------------------------------------------------------------


def test_flow_plan_json_v2_schema(tmp_path: Path):
    cfg = Config()
    structure = _make_structure(downbeats_t=[15.0, 18.6, 22.0], drop_t=18.6)
    chunks_with_events = [
        (Path("A.mp4"), 5.0, "T2", [_evt("rocket_fire", t=1.2)]),
        (Path("B.mp4"), 5.0, "T1", [_evt("player_death", t=1.0)]),
    ]
    reordered, seam_offsets = plan_flow_cuts_v2(
        chunks_with_events, structure, cfg,
        intro_offset=13.0, xfade=0.4,
    )
    path = write_flow_plan_json(reordered, seam_offsets, 99, tmp_path)
    assert path.exists()
    import json as _j
    data = _j.loads(path.read_text())
    assert data["part"] == 99
    assert len(data["clips"]) == 2
    assert all("top_event" in c and "tier" in c and "section_role" in c
               for c in data["clips"])
    assert len(data["seams"]) == 1
    assert "anchor" in data["seams"][0]


# --- BACK-COMPAT: legacy plan_flow_cuts still writes old schema -------------


def test_write_flow_plan_json_v1_back_compat(tmp_path: Path):
    """Old signature (cuts, part, out_dir) still works."""
    cuts = [{"clip": "x.mp4", "tag": "TIGHT", "section_shape": "drop"}]
    path = write_flow_plan_json(cuts, 42, tmp_path)  # v1 signature
    assert path.exists()
    import json as _j
    data = _j.loads(path.read_text())
    assert data["part"] == 42
    assert data["cuts"] == cuts
    assert "stats" in data
