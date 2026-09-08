"""The song is the score: duration, footprints, intensity, plan identity."""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (score_timeline as st, sequence_score_plan as ssp,
                                   temporal_footprint as tf)
from creative_suite.engine.music_features_v2 import (MusicEventV2, MusicFeatureV2,
                                                     MusicRegionV2)


def _feature(duration_us=240_000_000, beats=None):
    beats = (tuple(range(0, duration_us, 500_000)) if beats is None else beats)
    return MusicFeatureV2(
        track_hash="a" * 64, path="song.mp3", duration_us=duration_us,
        sample_rate=44100, channels=2, extractor_version="test",
        schema_version=2, status="ENRICHED_V2", bpm=120.0, bpm_confidence=None,
        beats_us=beats, beat_confidence=None,
        onset_curve=(), energy_curve=tuple(
            (t, 0.5) for t in range(0, duration_us, 1_000_000)),
        loudness_curve=(), spectral_curve=(),
        bar_grid_estimate_us=tuple(range(0, duration_us, 2_000_000)),
        section_boundary_estimates_us=(0, 60_000_000, 120_000_000,
                                       180_000_000, duration_us),
        phrase_boundary_estimates_us=(0, 30_000_000),
        regions=(MusicRegionV2("HIGH_ENERGY_REGION", 0, duration_us, None),),
        salient_events=(MusicEventV2("ACCENT", 1_000_000, 1.0, 1.0),))


def _timeline(**kw):
    return st.build_timeline(_feature(**kw))


# ── the song's duration IS the movie's duration ─────────────────────────────

def test_the_score_is_exactly_as_long_as_the_song():
    for dur in (227_328_000, 312_650_000, 258_000_000):
        assert _timeline(duration_us=dur).duration_us == dur


def test_the_timecode_reports_the_real_length():
    assert _timeline(duration_us=227_328_000).timecode == "3:47.328"


def test_a_plan_must_be_the_length_of_its_song():
    tl = _timeline()
    good = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us)
    assert not [f for f in good.check(timeline=tl) if f["severity"] == "ERROR"]
    short = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us - 5_000_000)
    assert any(f["check"] == ssp.PLAN_DURATION_MISMATCH
               for f in short.check(timeline=tl))


def test_a_song_is_never_padded_or_trimmed_to_a_target():
    """No Part template imposes five minutes on a 3:47 song."""
    tl = _timeline(duration_us=227_328_000)
    plan = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us)
    assert plan.score_duration_us == 227_328_000
    assert plan.duration_timecode == "3:47.328"


# ── eligibility ─────────────────────────────────────────────────────────────

def test_a_long_song_is_not_eligible():
    e = st.check_eligibility(_feature(duration_us=7 * 60 * 1_000_000))
    assert not e.eligible and any("ceiling" in r for r in e.reasons)
    with pytest.raises(st.SongNotEligible):
        e.raise_if_ineligible()


def test_a_song_without_a_beat_grid_is_not_eligible():
    assert not st.check_eligibility(_feature(beats=(0, 1))).eligible


def test_a_truncated_beat_grid_warns_but_does_not_block():
    """The cached grids in this library stop early; that must be visible."""
    f = _feature(beats=tuple(range(0, 90_000_000, 500_000)))
    e = st.check_eligibility(f)
    assert e.eligible
    assert any("beat grid covers only" in w for w in e.warnings)


def test_the_timeline_reports_its_grid_coverage():
    tl = st.build_timeline(_feature(beats=tuple(range(0, 120_000_000, 500_000))))
    assert 0.45 < tl.beat_grid_coverage < 0.55
    assert tl.grid_covers(100_000_000)
    assert not tl.grid_covers(200_000_000)


def test_a_slot_says_whether_its_beat_count_means_anything():
    tl = st.build_timeline(_feature(beats=tuple(range(0, 60_000_000, 500_000))))
    slots = st.derive_slots(tl)
    assert any(not s.evidence.beat_grid_covered for s in slots)


# ── clocks ──────────────────────────────────────────────────────────────────

def test_score_and_edit_run_one_to_one():
    for us in (0, 1_234_567, 258_000_000):
        assert st.score_to_edit(us) == us
        assert st.edit_to_score(st.score_to_edit(us)) == us


# ── slots ───────────────────────────────────────────────────────────────────

def test_slots_stay_inside_the_score_and_do_not_overlap():
    tl = _timeline()
    slots = st.derive_slots(tl)
    assert slots
    for s in slots:
        assert 0 <= s.start_us < s.end_us <= tl.duration_us
    for a, b in zip(slots, slots[1:]):
        assert b.start_us >= a.end_us


def test_a_slot_carries_evidence_not_a_single_score():
    slot = st.derive_slots(_timeline())[0]
    ev = slot.evidence.to_dict()
    for field in ("duration_us", "mean_energy", "energy_shape",
                  "onset_density_per_s", "percussive_density_per_s",
                  "hard_anchor_count", "negative_space_us", "beat_count"):
        assert field in ev


def test_slot_roles_and_intensities_are_known_values():
    for s in st.derive_slots(_timeline()):
        assert s.role in st.SLOT_ROLES
        assert s.intensity in st.INTENSITIES


def test_a_slot_needs_positive_duration_and_a_real_role():
    ev = st.SlotEvidence(1, 0.0, "FLAT", 0.0, 0.0, 0, 0, 0, True, "NONE")
    with pytest.raises(ValueError):
        st.ScoreSlot(100, 100, st.SLOT_HERO, ev)
    with pytest.raises(ValueError):
        st.ScoreSlot(0, 10, "VIBES", ev)


# ── intensity ───────────────────────────────────────────────────────────────

def test_the_intensity_curve_follows_the_slots():
    slots = st.derive_slots(_timeline())
    curve = st.intensity_curve(slots)
    assert len(curve) == len(slots)
    assert all(name in st.INTENSITIES for _, name in curve)


def test_unbroken_spectacle_is_warned_about():
    ev = st.SlotEvidence(1_000_000, 0.9, "FLAT", 5.0, 5.0, 3, 0, 4, True, "NONE")
    slots = [st.ScoreSlot(i * 1_000_000, (i + 1) * 1_000_000, st.SLOT_HERO, ev,
                          st.INTENSITY_SPECTACLE) for i in range(4)]
    warns = st.spectacle_saturation(slots)
    assert warns and warns[0]["check"] == st.SPECTACLE_SATURATION
    assert warns[0]["severity"] == "WARN"


def test_contrast_between_peaks_is_not_warned_about():
    ev = st.SlotEvidence(1_000_000, 0.9, "FLAT", 5.0, 5.0, 3, 0, 4, True, "NONE")
    slots = [st.ScoreSlot(0, 1_000_000, st.SLOT_HERO, ev, st.INTENSITY_SPECTACLE),
             st.ScoreSlot(1_000_000, 2_000_000, st.SLOT_BREATH, ev,
                          st.INTENSITY_RESTRAINT),
             st.ScoreSlot(2_000_000, 3_000_000, st.SLOT_HERO, ev,
                          st.INTENSITY_SPECTACLE)]
    assert st.spectacle_saturation(slots) == []


# ── temporal footprints ─────────────────────────────────────────────────────

def test_a_footprint_totals_everything_it_occupies():
    fp = tf.TimeFootprint(pre_roll_us=300_000, active_us=900_000,
                          peak_offset_us=700_000, release_us=200_000)
    assert fp.total_occupied_us == 1_400_000


def test_a_footprint_places_itself_around_a_musical_peak():
    fp = tf.TimeFootprint(pre_roll_us=300_000, active_us=900_000,
                          peak_offset_us=700_000, release_us=200_000)
    at = fp.place_at_peak(10_000_000)
    assert at["peak_us"] == 10_000_000
    assert at["active_start_us"] == 9_300_000
    assert at["start_us"] == 9_000_000
    assert at["end_us"] == 10_400_000
    assert at["end_us"] - at["start_us"] == fp.total_occupied_us


def test_the_peak_must_fall_inside_the_active_span():
    with pytest.raises(ValueError):
        tf.TimeFootprint(active_us=100, peak_offset_us=500)


def test_a_freeze_occupies_score_time():
    """350 ms of freeze makes the movie 350 ms longer. That is allowed."""
    fp = tf.TimeFootprint(active_us=350_000)
    assert fp.total_occupied_us == 350_000


# ── retime ──────────────────────────────────────────────────────────────────

def test_slow_motion_lengthens_the_edit_and_owes_nothing():
    seg = tf.RetimeSegment(0, 1_125_000, Fraction(379, 1000), "flight")
    assert seg.edit_span_us > seg.src_span_us
    assert tf.check_no_temporal_debt([seg]) == []


def test_a_speed_up_after_slow_motion_is_an_error():
    segs = [tf.RetimeSegment(0, 1_000_000, Fraction(1, 2), "slow"),
            tf.RetimeSegment(1_000_000, 2_000_000, Fraction(2, 1), "repay")]
    findings = tf.check_no_temporal_debt(segs)
    assert findings and findings[0]["check"] == tf.UNINTENDED_POST_SLOW_SPEEDUP
    assert "repaying slow-motion time" in findings[0]["detail"]


def test_an_authored_speed_up_is_allowed():
    segs = [tf.RetimeSegment(0, 1_000_000, Fraction(1, 2), "slow"),
            tf.RetimeSegment(1_000_000, 2_000_000, Fraction(2, 1), "whip",
                             authored_speedup=True)]
    assert tf.check_no_temporal_debt(segs) == []


def test_the_requested_rate_stays_exact():
    seg = tf.RetimeSegment(0, 1_000_000, Fraction(1, 1), "native")
    assert str(seg.requested_rate) == "1"
    assert seg.to_dict()["requested_rate"] == "1"


def test_the_envelope_limits_what_music_may_ask_for():
    env = tf.RetimeEnvelope(0.35, 1.0, 0.25, 1.0)
    assert env.prefers(0.5) and env.allows(0.3)
    assert not env.prefers(0.3)
    assert not env.allows(0.1)
    assert env.clamp(0.05) == 0.25


def test_bounds_must_be_ordered():
    with pytest.raises(ValueError):
        tf.RetimeEnvelope(0.9, 0.4, 0.2, 1.0)


def test_a_rate_can_be_derived_to_span_a_musical_interval():
    rate = tf.rate_for_span(1_125_000, 2_972_136)
    assert 0.37 < float(rate) < 0.39
    seg = tf.RetimeSegment(0, 1_125_000, rate, "flight")
    assert abs(seg.edit_span_us - 2_972_136) <= 1


# ── effects and transitions ─────────────────────────────────────────────────

def test_an_effect_profile_knows_where_it_belongs():
    prof = tf.WORLD_STRIP_1VX
    assert prof.fits_slot("BUILD", 2_000_000)
    assert not prof.fits_slot("OUTRO", 2_000_000)
    assert not prof.fits_slot("BUILD", 100_000)
    assert prof.has_evidence(["multi_enemy_positions", "one_v_x_context"])
    assert not prof.has_evidence(["multi_enemy_positions"])


def test_every_reference_effect_declares_a_purpose_and_a_footprint():
    for prof in tf.REFERENCE_EFFECTS:
        assert prof.purpose
        assert prof.footprint.total_occupied_us > 0
        assert prof.intensity in st.INTENSITIES


def test_a_transition_occupies_time_on_both_sides():
    t = tf.TransitionFootprint("PROJECTILE_BRIDGE", 1_000_000, 2_000_000,
                               start_us=1_600_000, peak_us=2_000_000,
                               handoff_us=2_100_000, end_us=2_400_000)
    assert t.duration_us == 800_000
    assert t.outgoing_overlap_us == 500_000
    assert t.incoming_overlap_us == 300_000


def test_transition_moments_must_be_ordered():
    with pytest.raises(ValueError):
        tf.TransitionFootprint("X", 0, 0, start_us=100, peak_us=50,
                               handoff_us=60, end_us=70)


# ── the plan ────────────────────────────────────────────────────────────────

def _scene(**kw):
    base = dict(slot_role=st.SLOT_HERO, frag_id=2340, scene_kind="LG",
                score_start_us=10_000_000, score_end_us=20_000_000,
                hero_event_kind="MY_FRAG", hero_score_us=18_000_000,
                why="because")
    base.update(kw)
    return ssp.PlannedScene(**base)


def test_the_hero_event_must_lie_inside_its_own_scene():
    with pytest.raises(ValueError):
        _scene(hero_score_us=99_000_000)


def test_a_consumed_moment_cannot_be_planned_again():
    tl = _timeline()
    plan = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us,
                                   scenes=(_scene(moment_state="USED"),))
    assert any(f["check"] == ssp.PLAN_CONSUMED_MOMENT for f in plan.check())
    ok = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us,
                                 scenes=(_scene(moment_state="SHORTLISTED"),))
    assert not any(f["check"] == ssp.PLAN_CONSUMED_MOMENT for f in ok.check())


def test_shortlisting_does_not_consume():
    assert not _scene(moment_state="SHORTLISTED").consumes
    for state in ssp.CONSUMING_STATES:
        assert _scene(moment_state=state).consumes


def test_overlapping_scenes_need_a_transition_to_claim_the_time():
    tl = _timeline()
    a = _scene(frag_id=1, score_start_us=0, score_end_us=10_000_000,
               hero_score_us=9_000_000)
    b = _scene(frag_id=2, score_start_us=9_500_000, score_end_us=20_000_000,
               hero_score_us=19_000_000)
    bare = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us, scenes=(a, b))
    assert any(f["check"] == ssp.PLAN_OVERLAP for f in bare.check())
    covered = ssp.SequenceScorePlanV1(
        tl.track_hash, tl.duration_us, scenes=(a, b),
        transitions=(ssp.PlannedTransition(tf.TransitionFootprint(
            "BLOOD_WIPE", 10_000_000, 9_500_000, start_us=9_400_000,
            peak_us=9_700_000, handoff_us=9_800_000, end_us=10_100_000)),))
    assert not any(f["check"] == ssp.PLAN_OVERLAP for f in covered.check())


def test_a_scene_outside_the_score_is_an_error():
    tl = _timeline()
    plan = ssp.SequenceScorePlanV1(
        tl.track_hash, tl.duration_us,
        scenes=(_scene(score_start_us=tl.duration_us - 1_000,
                       score_end_us=tl.duration_us + 5_000_000,
                       hero_score_us=tl.duration_us),))
    assert any(f["check"] == ssp.PLAN_OUT_OF_SCORE for f in plan.check())


def test_the_plan_reports_coverage_and_what_stays_empty():
    tl = _timeline()
    slots = st.derive_slots(tl)
    scene = _scene()
    plan = ssp.SequenceScorePlanV1(
        tl.track_hash, tl.duration_us, slots=slots, scenes=(scene,),
        unresolved=ssp.unresolved_from(slots, [scene]))
    assert plan.occupied_us == scene.duration_us
    assert plan.unresolved_us == tl.duration_us - scene.duration_us
    assert 0.0 < plan.coverage < 0.1
    assert plan.unresolved                     # emptiness is reported


def test_unresolved_slots_say_what_they_want():
    tl = _timeline()
    slots = st.derive_slots(tl)
    unresolved = ssp.unresolved_from(slots, [])
    assert len(unresolved) == len(slots)
    assert all(u.wants for u in unresolved)


def test_every_placement_explains_itself():
    tl = _timeline()
    plan = ssp.SequenceScorePlanV1(
        tl.track_hash, tl.duration_us, scenes=(_scene(why="low density"),))
    text = " ".join(plan.explain())
    assert "low density" in text and "2340" in text


# ── plan identity ───────────────────────────────────────────────────────────

def test_the_same_plan_always_has_the_same_hash():
    tl = _timeline()
    a = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us, scenes=(_scene(),))
    b = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us, scenes=(_scene(),))
    assert a.plan_hash == b.plan_hash


def test_an_editorial_change_changes_the_hash():
    tl = _timeline()
    a = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us, scenes=(_scene(),))
    moved = ssp.SequenceScorePlanV1(
        tl.track_hash, tl.duration_us,
        scenes=(_scene(score_start_us=10_015_000, score_end_us=20_015_000),))
    assert a.plan_hash != moved.plan_hash


def test_plan_identity_holds_no_volatile_state():
    tl = _timeline()
    plan = ssp.SequenceScorePlanV1(tl.track_hash, tl.duration_us,
                                   scenes=(_scene(),))
    canonical = plan.canonical()
    for banned in ("generated_at", "created_at", "timestamp", "machine",
                   "selected", "cursor", "zoom", "session"):
        assert banned not in str(canonical).lower()


def test_the_hero_timing_preference_survives_into_the_plan():
    rel = ssp.SyncRelationship("frag", 10_000_000, 9_985_000, -15.0,
                               "LG_FINAL_KILL")
    assert rel.intended_delta_ms == -15.0
    assert rel.error_ms == 0.0
    late = ssp.SyncRelationship("frag", 10_000_000, 10_015_000, -15.0,
                                "LG_FINAL_KILL")
    assert late.error_ms == 30.0


def test_a_scene_reports_its_own_delivered_delta():
    scene = _scene(music_anchor_us=17_985_000, target_delta_ms=-15.0)
    assert scene.delivered_delta_ms == -15.0
