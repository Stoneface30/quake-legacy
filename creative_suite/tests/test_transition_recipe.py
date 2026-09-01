"""TransitionRecipe identity/persistence and bridge music strategy.

The two properties that matter: a transition is REPRODUCIBLE (same inputs
-> same id, survives save/reload, UI state never enters identity), and a
music strategy is EVIDENCE, not judgement.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import bridge_music as bm
from creative_suite.engine import transition_recipe as tr

MUSIC_DB = REPO_ROOT / "creative_suite" / "database" / "music_features_v2.db"

# Frag 13114 launch 2700 / impact 4000 ms; Frag 27622 launch 2650 / 4000 ms.
TRACK_A = [(2700, 0.0, 0.0, 0.0), (3300, 5.0, 0.0, 0.0), (4000, 9.0, 0.0, 0.0)]
TRACK_B = [(2650, 0.0, 0.0, 0.0), (3300, 5.0, 0.0, 0.0), (4000, 9.0, 0.0, 0.0)]


def _bridge(**kw):
    return tr.build_projectile_bridge(
        scene_a_recipe_id="a" * 64, scene_b_recipe_id="b" * 64,
        scene_a_track=TRACK_A, scene_b_track=TRACK_B, **kw)


# ── anchors are evidence, not constants ─────────────────────────────────────

def test_anchors_resolve_from_the_projectile_track():
    a = tr.resolve_projectile_anchors(TRACK_A)
    assert a[tr.A_LAUNCH] == 2_700_000
    assert a[tr.A_IMPACT] == 4_000_000


def test_anchors_absent_rather_than_invented_without_a_track():
    assert tr.resolve_projectile_anchors([]) == {}
    assert tr.resolve_projectile_anchors([(0, 0, 0, 0)]) == {}


def test_bridge_cuts_on_impact_and_enters_on_launch():
    t = _bridge()
    assert t.scene_a_anchor == tr.A_IMPACT
    assert t.scene_b_anchor == tr.B_LAUNCH
    assert t.cut_edit_us == 4_000_000
    assert t.scene_b_entry_us == 2_650_000


def test_bridge_requires_both_tracks():
    with pytest.raises(ValueError):
        tr.build_projectile_bridge(scene_a_recipe_id="a" * 64,
                                   scene_b_recipe_id="b" * 64,
                                   scene_a_track=TRACK_A, scene_b_track=[])


# ── identity ────────────────────────────────────────────────────────────────

def test_transition_id_is_deterministic():
    assert _bridge().transition_id == _bridge().transition_id


def test_transition_id_changes_with_a_meaningful_field():
    base = _bridge()
    other = _bridge(visual_variant=tr.VISUAL_IMPACT_FLASH)
    assert base.transition_id != other.transition_id


def test_music_strategy_is_part_of_identity():
    assert (_bridge(music_strategy=tr.MUSIC_CONTINUOUS).transition_id
            != _bridge(music_strategy=tr.MUSIC_STRUCTURED).transition_id)


def test_canonical_roundtrip_preserves_identity():
    t = _bridge(visual_variant=tr.VISUAL_GRADE_LERP, fx=("impact_flash",))
    assert tr.from_canonical(t.canonical()) == t
    assert tr.from_canonical(t.canonical()).transition_id == t.transition_id


def test_persist_and_reload_is_identical(tmp_path):
    db = tmp_path / "transitions.db"
    t = _bridge(music_strategy=tr.MUSIC_STRUCTURED)
    tid = tr.persist(t, db)
    assert tr.load(tid, db) == t
    assert tr.load("0" * 64, db) is None
    tr.persist(t, db)                       # upsert, no duplicate row
    assert len(tr.list_transitions(db)) == 1


def test_rejects_nonsense():
    with pytest.raises(ValueError):
        _bridge(visual_variant="SWIRLY_WIPE")
    with pytest.raises(ValueError):
        _bridge(music_strategy="VIBES")
    with pytest.raises(ValueError):
        tr.SceneTransition(type="NOT_A_TYPE", scene_a_recipe_id="a" * 64,
                           scene_b_recipe_id="b" * 64,
                           scene_a_anchor=tr.A_IMPACT,
                           scene_b_anchor=tr.B_LAUNCH,
                           cut_edit_us=1, scene_b_entry_us=1)
    with pytest.raises(ValueError):
        tr.SceneTransition(type=tr.TYPE_PROJECTILE_BRIDGE,
                           scene_a_recipe_id="a" * 64,
                           scene_b_recipe_id="a" * 64,      # bridges to itself
                           scene_a_anchor=tr.A_IMPACT,
                           scene_b_anchor=tr.B_LAUNCH,
                           cut_edit_us=1, scene_b_entry_us=1)


def test_microsecond_fields_reject_floats():
    with pytest.raises(ValueError):
        tr.SceneTransition(type=tr.TYPE_PROJECTILE_BRIDGE,
                           scene_a_recipe_id="a" * 64,
                           scene_b_recipe_id="b" * 64,
                           scene_a_anchor=tr.A_IMPACT,
                           scene_b_anchor=tr.B_LAUNCH,
                           cut_edit_us=1.5, scene_b_entry_us=1)


# ── bridge segmentation onto one sequence clock ─────────────────────────────

def test_segments_place_the_cut_on_scene_a_impact():
    t = _bridge()
    a, b = bm.bridge_segments(t, scene_a_track=TRACK_A, scene_b_track=TRACK_B,
                              a_lead_us=1_800_000, b_tail_us=1_000_000)
    assert a.seq_start_us == 0 and a.impact_us == 1_800_000
    assert b.seq_start_us == a.seq_end_us == 1_800_000   # no gap, no overlap
    assert b.impact_us == 1_800_000 + (4_000_000 - 2_650_000)
    assert b.seq_end_us == b.impact_us + 1_000_000


def test_segments_never_leave_a_hole_in_the_sequence_clock():
    t = _bridge()
    a, b = bm.bridge_segments(t, scene_a_track=TRACK_A, scene_b_track=TRACK_B,
                              a_lead_us=900_000, b_tail_us=250_000)
    assert a.seq_end_us == b.seq_start_us
    assert a.duration_us > 0 and b.duration_us > 0


# ── music strategy is evidence, against the real catalog ────────────────────

@pytest.fixture(scope="module")
def catalog():
    if not MUSIC_DB.exists():
        pytest.skip("music_features_v2.db not present")
    feats = bm.load_features(MUSIC_DB)
    if not feats:
        pytest.skip("empty music catalog")
    return feats


@pytest.fixture(scope="module")
def segs():
    t = _bridge()
    return bm.bridge_segments(t, scene_a_track=TRACK_A, scene_b_track=TRACK_B,
                              a_lead_us=1_800_000, b_tail_us=1_000_000)


def test_continuous_returns_ranked_candidates(catalog, segs):
    a, b = segs
    rows = bm.strategy_continuous(a, b, catalog, top_n=3)
    assert rows
    totals = [r["total"] for r in rows]
    assert totals == sorted(totals, reverse=True)
    for r in rows:
        assert r["music_source_start_us"] >= 0


def test_structured_prefers_phrase_placed_regions(catalog, segs):
    """The directive's requirement: a music change at the cut must be
    placed on musical structure, not dropped there with a crossfade."""
    a, b = segs
    out = bm.strategy_structured(a, b, catalog, top_n=3)
    assert out["scene_a"] and out["scene_b"]
    top = out["scene_b"][0]
    assert "phrase_boundary_delta_us" in top
    if top["structurally_placed"]:
        assert abs(top["phrase_boundary_delta_us"]) <= bm.STRUCTURAL_TOLERANCE_US
    # structurally placed candidates must sort ahead of unplaced ones
    flags = [r["structurally_placed"] for r in out["scene_b"]]
    assert flags == sorted(flags, reverse=True)


def test_evidence_report_uses_the_music_clock(catalog, segs):
    a, b = segs
    row = bm.strategy_continuous(a, b, catalog, top_n=1)[0]
    feature = next(f for f in catalog if f.track_hash == row["track_hash"])
    ev = bm.evidence_report(a, b, row, feature)
    place = bm.placement_for(row, 0, b.seq_end_us)
    assert ev["music_us_at_cut"] == place.edit_to_music(a.impact_us)
    assert ev["music_us_at_hero"] == place.edit_to_music(b.impact_us)
    # a report states measurements, never a verdict
    assert "better" not in ev and "recommended" not in ev


def test_evidence_report_reports_bpm_confidence_honestly(catalog, segs):
    a, b = segs
    row = bm.strategy_continuous(a, b, catalog, top_n=1)[0]
    feature = next(f for f in catalog if f.track_hash == row["track_hash"])
    ev = bm.evidence_report(a, b, row, feature)
    assert "bpm" in ev and "bpm_confidence" in ev
    assert ev["bpm_confidence"] == feature.bpm_confidence


def test_placement_maps_edit_to_music_affinely(catalog, segs):
    a, b = segs
    row = bm.strategy_continuous(a, b, catalog, top_n=1)[0]
    place = bm.placement_for(row, 0, b.seq_end_us)
    assert place.edit_to_music(0) == int(row["music_source_start_us"])
    step = place.edit_to_music(1_000_000) - place.edit_to_music(0)
    assert step == 1_000_000        # no time-stretch; music is never resampled
