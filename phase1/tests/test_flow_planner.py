"""Tests for Rule P1-CC v2 flow-driven plan_flow_cuts."""
from __future__ import annotations

from phase1.beat_sync import (
    plan_flow_cuts,
    classify_section_shape,
    write_flow_plan_json,
)
from phase1.audio_onsets import GameEvent, EVENT_WEIGHTS


def _evt(etype: str, conf: float = 0.85, t: float = 1.0) -> GameEvent:
    return GameEvent(t=t, event_type=etype, confidence=conf,
                     weight=EVENT_WEIGHTS.get(etype, 0.3))


def test_classify_drop_by_explicit_drop_timestamp():
    drops = [{"t": 90.0, "strength": 0.9}]
    section = {"start": 80.0, "end": 110.0}
    assert classify_section_shape(section, drops) == "drop"


def test_classify_build_when_no_drop_and_short():
    section = {"start": 0.0, "end": 30.0}
    assert classify_section_shape(section, []) == "build"


def test_classify_break_when_long():
    section = {"start": 0.0, "end": 90.0}
    assert classify_section_shape(section, []) == "break"


def test_drop_section_gets_player_death_clip():
    """Flow planner must send a player_death clip to the drop section."""
    structure = {
        "duration_s": 200.0,
        "sections": [
            {"start": 0.0,  "end": 60.0,  "label": "A"},   # build
            {"start": 60.0, "end": 120.0, "label": "B"},   # drop (has drop inside)
            {"start": 120.0,"end": 200.0, "label": "C"},   # break / outro
        ],
        "drops": [{"t": 80.0, "strength": 0.95}],
        "downbeats": [{"t": 10.0, "bar": 0, "salience": 0.5, "section": "A"},
                      {"t": 80.0, "bar": 8, "salience": 0.9, "section": "B"},
                      {"t": 160.0,"bar": 16,"salience": 0.3, "section": "C"}],
    }
    clip_events = {
        "clip_build.mp4": [_evt("rocket_fire", conf=0.85)],
        "clip_drop.mp4":  [_evt("player_death", conf=0.95)],
        "clip_break.mp4": [],  # silent / no event
        "clip_extra.mp4": [_evt("rail_fire", conf=0.80)],
    }
    clip_tiers = {
        "clip_build.mp4": "T2",
        "clip_drop.mp4":  "T1",
        "clip_break.mp4": "T3",
        "clip_extra.mp4": "T2",
    }
    cuts = plan_flow_cuts(clip_events, structure, clip_tiers)
    # Identify the drop-section cut
    drop_cuts = [c for c in cuts if c["section_shape"] == "drop"]
    assert drop_cuts, f"no drop cut produced: {cuts}"
    assert drop_cuts[0]["clip"] == "clip_drop.mp4"


def test_build_section_prefers_fire_only_clip():
    """Build sections should favor weapon_fire clips, not player_death."""
    structure = {
        "duration_s": 60.0,
        "sections": [
            {"start": 0.0,  "end": 30.0, "label": "A"},
            {"start": 30.0, "end": 60.0, "label": "B"},
        ],
        "drops": [],
        "downbeats": [],
    }
    clip_events = {
        "fire.mp4":  [_evt("rail_fire", conf=0.85)],
        "death.mp4": [_evt("player_death", conf=0.90)],
    }
    clip_tiers = {"fire.mp4": "T2", "death.mp4": "T1"}
    cuts = plan_flow_cuts(clip_events, structure, clip_tiers)
    # Sections are short (<45s) → shape=build; flow planner should pick the
    # fire clip over the death clip despite T1>T2 tier, because build-shape
    # flow_fit favors _fire event types (0.9) over player_death (0.4).
    build_cut = next(c for c in cuts if c["section_shape"] == "build")
    assert build_cut["clip"] == "fire.mp4"


def test_tier_breaks_ties_on_equal_flow_fit():
    """Two clips with equal flow fit -> higher tier wins."""
    structure = {
        "duration_s": 60.0,
        "sections": [{"start": 0.0, "end": 60.0, "label": "only"}],
        "drops": [],
        "downbeats": [],
    }
    # Both clips have identical events so flow fit should match.
    clip_events = {
        "a.mp4": [_evt("rail_fire", conf=0.80)],
        "b.mp4": [_evt("rail_fire", conf=0.80)],
    }
    tiers = {"a.mp4": "T3", "b.mp4": "T1"}
    cuts = plan_flow_cuts(clip_events, structure, tiers)
    assert cuts[0]["clip"] == "b.mp4"  # T1 wins tie


def test_empty_sections_degrades_gracefully():
    cuts = plan_flow_cuts(
        clip_events={"only.mp4": [_evt("rocket_fire")]},
        music_structure={"duration_s": 30.0, "sections": [], "drops": [], "downbeats": []},
        clip_tier_map={"only.mp4": "T2"},
    )
    # Synthetic 'all' section should allow placement.
    assert len(cuts) == 1


def test_write_flow_plan_json(tmp_path):
    cuts = [
        {"clip": "x", "tier": "T1", "section_shape": "drop",
         "section_start": 0.0, "section_end": 10.0,
         "event_type": "player_death", "event_conf": 0.9,
         "target_downbeat": 5.0, "shift": 0.0,
         "head_trim_adjust": 0.0, "tail_trim_adjust_prev": 0.0,
         "tag": "TIGHT", "flow_fit": 0.9},
    ]
    out = write_flow_plan_json(cuts, part=4, out_dir=tmp_path)
    assert out.exists()
    assert "part04_flow_plan.json" in str(out)
