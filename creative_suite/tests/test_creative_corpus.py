"""Beat grids, opportunity projection, gestures, episode intent, drafts."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (beat_grid_repair as bg, episode_intent as ei,
                                   music_gesture as mg, opportunity_graph as og,
                                   score_timeline as st, sequence_score_plan as ssp,
                                   temporal_footprint as tf)


# ── beat grids ──────────────────────────────────────────────────────────────

def _grid(**kw):
    base = dict(track_hash="a" * 64, duration_us=240_000_000,
                beats_us=tuple(range(0, 238_000_000, 500_000)),
                bars_us=tuple(range(0, 238_000_000, 2_000_000)), bpm=120.0,
                status=bg.STATUS_FULL, first_covered_us=0,
                last_covered_us=237_500_000)
    base.update(kw)
    return bg.BeatGridV1(**base)


def test_a_grid_reaching_the_end_is_full():
    assert _grid().is_full
    assert _grid().coverage > 0.98


def test_a_truncated_grid_cannot_call_itself_full():
    """The exact defect: beats stopping at 41% must be visible as PARTIAL."""
    status = bg.status_for(98_000_000, 240_000_000)
    assert status == bg.STATUS_PARTIAL
    grid = _grid(status=status, last_covered_us=98_000_000,
                 beats_us=tuple(range(0, 98_000_000, 500_000)))
    assert not grid.is_full
    assert grid.coverage < 0.45


def test_a_grid_knows_where_it_stops_covering():
    grid = _grid(last_covered_us=98_000_000,
                 beats_us=tuple(range(0, 98_000_000, 500_000)),
                 status=bg.STATUS_PARTIAL)
    assert grid.covers(50_000_000)
    assert not grid.covers(200_000_000)


def test_a_grid_status_must_be_known():
    with pytest.raises(ValueError):
        _grid(status="PROBABLY_FINE")


def test_a_non_failed_grid_needs_beats():
    with pytest.raises(ValueError):
        _grid(beats_us=(), bars_us=())


def test_beats_past_the_cached_duration_expose_a_wrong_duration():
    """Coverage above 1.0 means the cached duration is too short."""
    grid = _grid(duration_us=100_000_000, last_covered_us=237_500_000)
    assert grid.duration_suspect
    assert grid.duration_mismatch_us > 0


def test_a_measured_audio_duration_is_used_when_present():
    grid = _grid(duration_us=240_000_000, audio_duration_us=240_100_000)
    assert not grid.duration_suspect
    assert grid.duration_mismatch_us == 100_000


def test_subdivisions_are_derived_midpoints():
    grid = _grid(beats_us=(0, 1_000_000, 2_000_000))
    assert grid.subdivisions_us() == (500_000, 1_500_000)


def test_bars_stay_labelled_as_an_estimate():
    assert _grid().bar_semantics == "BAR_GRID_ESTIMATE"


def test_a_grid_round_trips(tmp_path):
    store = bg.BeatGridStore(tmp_path / "g.db")
    grid = _grid()
    store.put(grid)
    assert store.get(grid.track_hash) == grid


def test_a_grid_from_another_analyzer_version_is_not_served(tmp_path):
    """An old truncated row must never look like new complete evidence."""
    store = bg.BeatGridStore(tmp_path / "g.db")
    store.put(_grid())
    assert store.get("a" * 64, analyzer_version="beat-grid-v0.0.1") is None
    assert store.get("a" * 64, params="deadbeef") is None
    assert store.get("a" * 64) is not None


def test_the_coverage_report_counts_partials(tmp_path):
    store = bg.BeatGridStore(tmp_path / "g.db")
    store.put(_grid())
    store.put(_grid(track_hash="b" * 64, status=bg.STATUS_PARTIAL,
                    last_covered_us=90_000_000,
                    beats_us=tuple(range(0, 90_000_000, 500_000))))
    rep = store.coverage_report()
    assert rep["tracks"] == 2 and rep["full"] == 1 and rep["partial"] == 1


# ── opportunity projection ──────────────────────────────────────────────────

def _feature(duration_us=240_000_000):
    from creative_suite.engine.music_features_v2 import (MusicFeatureV2,
                                                         MusicRegionV2)
    return MusicFeatureV2(
        track_hash="a" * 64, path="s.mp3", duration_us=duration_us,
        sample_rate=44100, channels=2, extractor_version="t", schema_version=2,
        status="ENRICHED_V2", bpm=120.0, bpm_confidence=None,
        beats_us=tuple(range(0, duration_us, 500_000)), beat_confidence=None,
        onset_curve=(), energy_curve=tuple((t, 0.5) for t in
                                           range(0, duration_us, 1_000_000)),
        loudness_curve=(), spectral_curve=(),
        bar_grid_estimate_us=(), section_boundary_estimates_us=(
            0, 60_000_000, 120_000_000, 180_000_000, duration_us),
        phrase_boundary_estimates_us=(),
        regions=(MusicRegionV2("HIGH_ENERGY_REGION", 0, duration_us, None),))


def _slot(role=st.SLOT_TRACKING, dur=10_000_000, **ev):
    base = dict(duration_us=dur, mean_energy=0.25, energy_shape="FLAT",
                onset_density_per_s=1.5, percussive_density_per_s=1.0,
                hard_anchor_count=1, negative_space_us=0, beat_count=20,
                beat_grid_covered=True, structural_role="SECTION")
    base.update(ev)
    return st.ScoreSlot(0, dur, role, st.SlotEvidence(**base))


def _cand(**kw):
    base = dict(frag_id=1, scene_kind=og.KIND_LG_TRACKING,
                useful_duration_us=10_000_000, hero_event_kind="MY_FRAG",
                hero_offset_us=8_875_000)
    base.update(kw)
    return og.MomentCandidate(**base)


def test_unknown_evidence_stays_unknown():
    c = _cand()
    assert c.weapon == og.UNKNOWN and c.map_name == og.UNKNOWN
    assert c.enemy_count is None and c.damage_dealt is None


def test_a_fit_keeps_every_component():
    fit = og.score_candidate(_cand(), _slot())
    for name in og.FIT_COMPONENTS:
        assert name in dict(fit.components)
    assert fit.why


def test_a_sustained_scene_prefers_quiet_music():
    quiet = og.score_candidate(_cand(), _slot(mean_energy=0.15,
                                              onset_density_per_s=1.0))
    busy = og.score_candidate(_cand(), _slot(mean_energy=0.9,
                                             onset_density_per_s=6.0))
    assert quiet.component("ENERGY_FIT") > busy.component("ENERGY_FIT")
    assert quiet.component("RHYTHM_FIT") > busy.component("RHYTHM_FIT")


def test_an_instant_payoff_needs_a_hard_anchor():
    rocket = _cand(scene_kind=og.KIND_ROCKET_IMPACT, useful_duration_us=3_000_000)
    with_anchor = og.score_candidate(rocket, _slot(st.SLOT_HERO, 3_000_000,
                                                   hard_anchor_count=3))
    without = og.score_candidate(rocket, _slot(st.SLOT_HERO, 3_000_000,
                                               hard_anchor_count=0))
    assert with_anchor.component("HERO_ANCHOR_FIT") > without.component(
        "HERO_ANCHOR_FIT")


def test_duration_mismatch_lowers_the_fit():
    good = og.score_candidate(_cand(useful_duration_us=10_000_000), _slot())
    long = og.score_candidate(_cand(useful_duration_us=40_000_000), _slot())
    assert good.component("DURATION_FIT") > long.component("DURATION_FIT")


def test_a_consumed_moment_is_excluded_and_says_why():
    used = _cand(moment_state="USED")
    fit = og.score_candidate(used, _slot())
    assert not fit.eligible
    assert "cannot be planned again" in fit.blocked_reason
    assert og.rank_candidates([used], _slot()) == []
    assert len(og.rank_candidates([used], _slot(), include_blocked=True)) == 1


def test_shortlisted_moments_remain_available():
    assert _cand(moment_state="SHORTLISTED").available
    assert _cand(moment_state="AVAILABLE").available


def test_ranking_returns_the_best_first_with_reasons():
    fits = og.rank_candidates(
        [_cand(frag_id=1, useful_duration_us=10_000_000),
         _cand(frag_id=2, useful_duration_us=60_000_000)], _slot())
    assert fits[0].frag_id == 1
    assert all(f.why for f in fits)


def test_faster_motion_earns_a_deeper_retime_envelope():
    slow_min, _ = og.retime_envelope_for_speed(300.0)
    fast_min, _ = og.retime_envelope_for_speed(1400.0)
    assert fast_min < slow_min
    assert og.retime_envelope_for_speed(None) == (0.55, 1.0)


def test_speed_widens_the_envelope_but_never_picks_the_rate():
    lo, hi = og.retime_envelope_for_speed(2000.0)
    assert lo >= 0.25 and hi == 1.0        # a range, not a chosen rate


def test_montage_groups_need_several_distinct_moments():
    cands = [_cand(frag_id=i, motif_key="doorway_a") for i in range(5)]
    cands.append(_cand(frag_id=99, motif_key="lonely"))
    groups = og.montage_groups(cands)
    assert "doorway_a" in groups and len(groups["doorway_a"]) == 5
    assert "lonely" not in groups


# ── musical gestures ────────────────────────────────────────────────────────

class _Anchor:
    def __init__(self, us, component="PERCUSSIVE", attack="FAST", conf=0.9):
        self.perceptual_anchor_us = us
        self.component = component
        self.attack_class = attack
        self.pcenter_confidence = conf
        self.band_energy = (("MID_HIGH", 1.0),)


def test_a_regular_three_hit_figure_is_detected():
    anchors = [_Anchor(1_000_000), _Anchor(1_200_000), _Anchor(1_400_000)]
    gestures = mg.detect_gestures(anchors)
    assert len(gestures) == 1
    g = gestures[0]
    assert g.attack_count == 3
    assert g.iois_us == (200_000, 200_000)


def test_irregular_spacing_is_not_a_figure():
    anchors = [_Anchor(1_000_000), _Anchor(1_050_000), _Anchor(1_600_000)]
    assert mg.detect_gestures(anchors) == []


def test_a_different_timbre_breaks_the_run():
    anchors = [_Anchor(1_000_000), _Anchor(1_200_000, component="HARMONIC"),
               _Anchor(1_400_000)]
    assert mg.detect_gestures(anchors) == []


def test_the_instrument_is_never_claimed():
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000),
                            _Anchor(400_000)])[0]
    prov = dict(g.provenance)
    assert "NOT identified" in prov["instrument"]
    assert "TRUMPET" not in g.label.upper()
    assert g.tag_source == mg.TAG_SOURCE_DETECTED


def test_a_human_tag_is_authoritative_and_says_who_said_so():
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000),
                            _Anchor(400_000)])[0]
    tagged = g.tagged("TRUMPET_STUTTER")
    assert tagged.label == "TRUMPET_STUTTER"
    assert tagged.tag_source == mg.TAG_SOURCE_USER
    assert dict(tagged.provenance)["tagged_by"] == "director"
    assert g.label != "TRUMPET_STUTTER"        # the original is unchanged


def test_gesture_identity_comes_from_its_shape():
    a = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    b = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    c = mg.detect_gestures([_Anchor(0), _Anchor(250_000), _Anchor(500_000)])[0]
    assert a.gesture_id == b.gesture_id
    assert a.gesture_id != c.gesture_id


def test_a_response_quotes_the_figures_rhythm_exactly():
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    r = mg.respond(g, mg.FRAME_STUTTER)
    assert len(r.responses) == g.attack_count
    assert r.iois_us == g.iois_us
    assert mg.preserves_rhythm(g, r)


def test_a_stutter_lands_on_the_attack_not_ahead_of_it():
    """The -15 ms hero lead is not a universal constant."""
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    assert mg.respond(g, mg.FRAME_STUTTER).bias_ms == 0.0
    assert mg.respond(g, mg.CAMERA_JOLT).bias_ms < 0.0


def test_an_explicit_bias_shifts_the_whole_pattern_together():
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    r = mg.respond(g, mg.FRAME_STUTTER, bias_ms=-20.0)
    assert [x.at_us for x in r.responses] == [-20_000, 180_000, 380_000]
    assert mg.preserves_rhythm(g, r)


def test_an_unknown_response_pattern_is_rejected():
    g = mg.detect_gestures([_Anchor(0), _Anchor(200_000), _Anchor(400_000)])[0]
    with pytest.raises(ValueError):
        mg.respond(g, "SPARKLES")


# ── episode intent ──────────────────────────────────────────────────────────

def test_episode_one_is_an_initiation_with_all_six_beats():
    e = ei.EPISODE_1_INITIATION
    assert e.beats == (ei.PROJECT_INTRO, ei.ACTION_PROOF, ei.CA_EXPLAINER,
                       ei.TEAMPLAY, ei.HERO, ei.QUAKE_TRIBUTE)
    assert "tribute" in e.purpose.lower()
    assert "not Part 1" in e.notes


def test_an_unknown_beat_is_rejected():
    with pytest.raises(ValueError):
        ei.EpisodeIntent("x", "y", ("VIBES",))
    with pytest.raises(ValueError):
        ei.EpisodeIntent("x", "y", ())


def test_narrative_beats_run_forward_and_reach_the_end():
    tl = st.build_timeline(_feature())
    slots = st.derive_slots(tl)
    beats = ei.project_narrative(ei.EPISODE_1_INITIATION, tl, slots)
    assert beats
    for a, b in zip(beats, beats[1:]):
        assert b.score_start_us >= a.score_end_us
    assert beats[-1].score_end_us == tl.duration_us
    assert beats[-1].beat == ei.QUAKE_TRIBUTE


def test_a_narrative_beat_needs_positive_duration():
    with pytest.raises(ValueError):
        ei.NarrativeBeatPlacement(ei.HERO, 100, 100)


def test_every_beat_says_what_gameplay_it_wants():
    tl = st.build_timeline(_feature())
    for b in ei.project_narrative(ei.EPISODE_1_INITIATION, tl,
                                  st.derive_slots(tl)):
        assert b.why
        assert set(b.wants) <= set(og.SCENE_KINDS)


# ── song profiles ───────────────────────────────────────────────────────────

def test_a_profile_keeps_its_dimensions_visible():
    tl = st.build_timeline(_feature())
    prof = ei.profile_song(tl, st.derive_slots(tl))
    for dim in ei.PROFILE_DIMENSIONS:
        assert dim in dict(prof.dimensions)
    assert prof.headline


def test_episode_fit_is_the_weakest_link_not_an_average():
    tl = st.build_timeline(_feature())
    prof = ei.profile_song(tl, st.derive_slots(tl))
    needed = [prof.value(d) for d in ("INTRO_POTENTIAL", "HERO_POTENTIAL",
                                      "LG_POTENTIAL", "SPECTACLE_POTENTIAL",
                                      "OUTRO_POTENTIAL")]
    assert prof.fit_for(ei.EPISODE_1_INITIATION.name) == pytest.approx(
        min(needed), abs=1e-4)


def test_gestures_raise_the_motif_dimension():
    tl = st.build_timeline(_feature())
    slots = st.derive_slots(tl)
    none = ei.profile_song(tl, slots)
    many = ei.profile_song(tl, slots, gestures=[object()] * 8)
    assert many.value("MOTIF_GESTURE_POTENTIAL") > none.value(
        "MOTIF_GESTURE_POTENTIAL")


# ── composition draft ───────────────────────────────────────────────────────

def _planned_gesture(**kw):
    base = dict(gesture_id="g1", label="3x figure", score_start_us=1_000_000,
                score_end_us=1_400_000, attack_count=3,
                iois_us=(200_000, 200_000), response_pattern=mg.FRAME_STUTTER,
                response_us=(1_000_000, 1_200_000, 1_400_000), bias_ms=0.0)
    base.update(kw)
    return ssp.PlannedGesture(**base)


def test_a_draft_hashes_deterministically():
    plan = ssp.SequenceScorePlanV1("a" * 64, 240_000_000)
    a = ssp.CompositionDraftV1(plan, ei.EPISODE_1_INITIATION.name)
    b = ssp.CompositionDraftV1(plan, ei.EPISODE_1_INITIATION.name)
    assert a.draft_hash == b.draft_hash
    with_g = ssp.CompositionDraftV1(plan, ei.EPISODE_1_INITIATION.name,
                                    gestures=(_planned_gesture(),))
    assert with_g.draft_hash != a.draft_hash


def test_a_response_that_breaks_the_rhythm_is_an_error():
    plan = ssp.SequenceScorePlanV1("a" * 64, 240_000_000)
    bad = _planned_gesture(response_us=(1_000_000, 1_250_000, 1_400_000))
    assert not bad.rhythm_preserved
    draft = ssp.CompositionDraftV1(plan, gestures=(bad,))
    assert any(f["check"] == ssp.GESTURE_RHYTHM_BROKEN for f in draft.check())
    assert not draft.valid


def test_a_preserved_rhythm_passes():
    plan = ssp.SequenceScorePlanV1("a" * 64, 240_000_000)
    draft = ssp.CompositionDraftV1(plan, gestures=(_planned_gesture(),))
    assert draft.valid


def test_an_effect_without_a_purpose_is_flagged():
    plan = ssp.SequenceScorePlanV1(
        "a" * 64, 240_000_000,
        effects=(ssp.PlannedEffect("X", 0, 1, 2, "trigger", purpose="NONE"),))
    draft = ssp.CompositionDraftV1(plan)
    assert any(f["check"] == ssp.EFFECT_WITHOUT_PURPOSE
               for f in draft.check())


def test_effect_for_effects_sake_is_not_a_purpose():
    assert "EFFECT_FOR_EFFECTS_SAKE" in ssp.BANNED_PURPOSES
