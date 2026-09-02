"""Demo numbers are gameplay truth; matching them to music is arithmetic."""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (demo_truth as dt, editorial_sync_bias as eb,
                                   event_truth as et, numeric_match as nm,
                                   sync_contract, temporal_footprint as tf)


def _ev(**kw):
    base = dict(demo_us=1_000_000, kind=et.MY_FRAG, owner=et.OWNER_ME,
                evidence=dt.POV_AUTHORITATIVE)
    base.update(kw)
    return dt.DemoEvent(**base)


# ── evidence classes ────────────────────────────────────────────────────────

def test_every_event_declares_how_well_it_is_known():
    assert _ev().evidence in dt.EVIDENCE_CLASSES
    with pytest.raises(ValueError):
        _ev(evidence="PROBABLY")


def test_the_recorders_own_state_outranks_a_reconstruction():
    assert (dt.EVIDENCE_RANK[dt.POV_AUTHORITATIVE]
            < dt.EVIDENCE_RANK[dt.GEOMETRY_RECONSTRUCTED])
    assert _ev().is_authoritative
    assert not _ev(evidence=dt.GEOMETRY_RECONSTRUCTED).is_authoritative
    assert not _ev(evidence=dt.PHYSICS_RECONSTRUCTED).is_authoritative
    # Recorded in ANOTHER demo of the same match is still recorded.
    assert _ev(evidence=dt.MULTI_DEMO_RECOVERED).is_authoritative
    assert not _ev(evidence=dt.CINEMATIC_SYNTHETIC).is_authoritative


def test_unknown_kinds_are_rejected():
    with pytest.raises(ValueError):
        _ev(kind="VIBES")


def test_casting_to_edit_time_preserves_the_offset_from_the_hero():
    contact = _ev(demo_us=990_000, kind=et.MY_LG_CONTACT)
    cast = contact.to_edit(hero_demo_us=1_000_000, hero_edit_us=8_875_000)
    assert cast.edit_us == 8_865_000
    assert cast.layer == et.GAME_EVENT_TRUTH
    assert dt.POV_AUTHORITATIVE in cast.evidence


# ── projectile numbers ──────────────────────────────────────────────────────

def _track(**kw):
    base = dict(entity_kind="rocket", launch_us=0, impact_us=1_125_000,
                launch_pos=(0.0, 0.0, 0.0), impact_pos=(1125.0, 0.0, 0.0),
                points=tuple((i * 25_000, i * 25.0, 0.0, 0.0)
                             for i in range(46)),
                confidence="CONFIRMED")
    base.update(kw)
    return dt.ProjectileTrack(**base)


def test_flight_and_distance_come_from_the_track():
    t = _track()
    assert t.flight_us == 1_125_000
    assert t.distance_units == 1125.0


def test_speed_is_measured_from_the_point_series():
    """Not from the scalar launch/impact times, which can share a tick."""
    t = _track()
    assert t.speed_units_per_s == pytest.approx(1000.0, rel=0.02)


def test_a_single_point_yields_no_speed_rather_than_infinity():
    assert _track(points=((0, 0.0, 0.0, 0.0),)).speed_units_per_s is None
    assert _track(points=()).speed_units_per_s is None


def test_a_zero_span_series_yields_no_speed():
    flat = ((0, 0.0, 0.0, 0.0), (0, 10.0, 0.0, 0.0))
    assert _track(points=flat).speed_units_per_s is None


# ── derived numerics ────────────────────────────────────────────────────────

def test_derived_values_only_appear_when_the_evidence_does():
    assert dt.derive({}, None, []) == ()
    d = dict(dt.derive({"killer_speed": 300.0}, None, []))
    assert d["ATTACKER_SPEED"] == 300.0
    assert "RELATIVE_SPEED" not in d          # needs both speeds


def test_relative_speed_needs_both_sides():
    d = dict(dt.derive({"killer_speed": 300.0, "victim_speed": 637.4},
                       None, []))
    assert d["RELATIVE_SPEED"] == 937.4


def test_contacts_produce_a_damage_ledger_and_the_breath():
    events = [_ev(demo_us=1_000_000, kind=et.MY_LG_CONTACT, amount=7.0),
              _ev(demo_us=2_000_000, kind=et.MY_LG_CONTACT, amount=7.0),
              _ev(demo_us=2_875_000, kind=et.MY_FRAG)]
    d = dict(dt.derive({}, None, events))
    assert d["CONTACT_COUNT"] == 2
    assert d["DAMAGE_LEDGER"] == 14.0
    assert d["LAST_CONTACT_TO_FRAG_US"] == 875_000


def test_damage_received_is_summed_separately():
    events = [_ev(kind=et.MY_DAMAGE_RECEIVED, amount=25.0),
              _ev(kind=et.MY_DAMAGE_RECEIVED, amount=8.0)]
    assert dict(dt.derive({}, None, events))["DAMAGE_RECEIVED"] == 33.0


# ── the timeline ────────────────────────────────────────────────────────────

def _timeline(**kw):
    base = dict(frag_id=1, hero_demo_us=1_000_000, hero_kind=et.MY_FRAG,
                weapon="ROCKET", victim_client=3, round_index=2,
                events=(_ev(demo_us=900_000, kind=et.MY_LG_CONTACT),
                        _ev(demo_us=1_000_000)))
    base.update(kw)
    return dt.DemoTruthTimeline(**base)


def test_a_timeline_casts_into_edit_time_and_clips_to_the_scene():
    tl = _timeline()
    cast = tl.to_edit_timeline(hero_edit_us=8_875_000, scene_start_us=0,
                               scene_end_us=10_875_000)
    assert [e.edit_us for e in cast.events] == [8_775_000, 8_875_000]
    tight = tl.to_edit_timeline(hero_edit_us=8_875_000,
                                scene_start_us=8_800_000,
                                scene_end_us=10_875_000)
    assert len(tight.events) == 1


def test_the_timeline_never_carries_a_demo_filename():
    """Filenames embed player aliases and must not travel with the data."""
    d = _timeline().to_dict()
    assert "demo_name" not in d
    assert not any("demo_name" in str(k) for k in d)


def test_derived_values_are_addressable():
    tl = _timeline(derived=(("PROJECTILE_FLIGHT_US", 1_125_000),))
    assert tl.value("PROJECTILE_FLIGHT_US") == 1_125_000
    assert tl.value("NOT_MEASURED") is None


# ── coverage audit ──────────────────────────────────────────────────────────

def test_the_audit_classifies_every_stream():
    audit = dt.coverage_audit()
    assert audit["total_frags"] > 0
    for name, row in audit["streams"].items():
        assert row["status"] in (dt.COMPLETE, dt.PARTIAL, dt.MISSING)
        assert 0.0 <= row["share"] <= 1.0


def test_the_audit_knows_the_frag_event_is_complete():
    """If this ever regresses, nothing downstream can be trusted."""
    audit = dt.coverage_audit()
    assert audit["streams"]["FRAG_EVENT"]["status"] == dt.COMPLETE


@pytest.mark.skipif(not dt.RECOGNITION_DB.exists(),
                    reason="recognition database not on this machine")
def test_frag_2340_loads_its_numbers_without_touching_media():
    tl = dt.load(2340)
    assert tl.weapon == "LIGHTNING"
    assert tl.value("CONTACT_COUNT") == 33
    assert tl.value("LAST_CONTACT_TO_FRAG_US") == 875_000
    assert tl.value("DAMAGE_LEDGER") == 231.0
    assert all(e.evidence in dt.EVIDENCE_CLASSES for e in tl.events)


@pytest.mark.skipif(not dt.RECOGNITION_DB.exists(),
                    reason="recognition database not on this machine")
def test_a_rocket_frag_carries_a_measured_flight():
    tl = dt.load(24326)
    assert tl.projectile is not None
    assert tl.projectile.flight_us == 1_125_000
    assert 800 <= tl.projectile.speed_units_per_s <= 1400


# ── matching gameplay to music ──────────────────────────────────────────────

def test_the_target_anchor_is_the_event_plus_the_bias():
    assert nm.target_anchor_us(91_500_000, eb.DIRECT_HIT) == 91_485_000
    assert nm.target_anchor_us(0, eb.LG_CONTACT) is None


def test_the_nearest_qualifying_anchor_is_chosen_and_the_error_reported():
    sol = nm.solve_anchor(91_500_000,
                          [91_000_000, 91_483_000, 92_000_000],
                          eb.DIRECT_HIT)
    assert sol.chosen_music_us == 91_483_000
    assert sol.error_ms == -2.0
    assert sol.delivered_delta_ms == -17.0
    assert sol.absolute_tier == sync_contract.TIER_GOOD


def test_the_solution_says_exactly_how_far_to_move_the_music():
    sol = nm.solve_anchor(91_500_000, [91_400_000], eb.DIRECT_HIT,
                          max_search_us=200_000)
    assert sol.music_placement_shift_us == 85_000
    assert sol.chosen_music_us + sol.music_placement_shift_us == \
        sol.target_music_us


def test_no_anchor_within_the_search_budget_returns_nothing():
    assert nm.solve_anchor(91_500_000, [10_000_000], eb.DIRECT_HIT) is None
    assert nm.solve_anchor(91_500_000, [], eb.DIRECT_HIT) is None


def test_a_class_without_a_preference_takes_the_nearest_and_says_so():
    sol = nm.solve_anchor(1_000_000, [900_000, 1_200_000], eb.LG_CONTACT)
    assert sol.chosen_music_us == 900_000
    assert sol.direction_grade == eb.NO_PREFERENCE
    assert "no hard-sync preference" in sol.note


# ── rates ───────────────────────────────────────────────────────────────────

def test_beat_length_comes_from_bpm():
    assert nm.beat_us_for(120.0) == 500_000
    with pytest.raises(ValueError):
        nm.beat_us_for(0)


def test_every_returned_rate_is_legal_and_exact():
    env = tf.RetimeEnvelope(0.35, 1.0, 0.25, 1.0)
    for s in nm.solve_rate(1_125_000, 161.499, env):
        assert env.allows(float(s.rate))
        assert isinstance(s.rate, Fraction)
        assert abs(s.edit_span_us - s.beats * s.beat_us) <= 1


def test_a_rate_outside_the_envelope_is_not_offered():
    env = tf.RetimeEnvelope(0.9, 1.0, 0.9, 1.0)
    assert nm.solve_rate(1_125_000, 161.499, env, beat_range=(8,)) == []


def test_the_best_rate_is_the_slowest_the_footage_prefers():
    env = tf.RetimeEnvelope(0.35, 1.0, 0.25, 1.0)
    best = nm.best_rate(1_125_000, 161.499, env)
    assert best.within_preferred
    assert best.beats == 8
    assert 0.37 < best.rate_float < 0.38


def test_a_named_beat_span_can_be_requested():
    env = tf.RetimeEnvelope(0.35, 1.0, 0.25, 1.0)
    assert nm.best_rate(1_125_000, 161.499, env, prefer_beats=7).beats == 7


def test_a_zero_span_cannot_be_retimed():
    env = tf.RetimeEnvelope(0.35, 1.0, 0.25, 1.0)
    with pytest.raises(ValueError):
        nm.solve_rate(0, 120.0, env)


# ── scheduling and the ledger ───────────────────────────────────────────────

def test_elements_place_their_peak_on_the_hero_moment():
    scheduled = nm.schedule_around(91_500_000, [
        ("WORLD_STRIP", tf.WORLD_STRIP_1VX.footprint, "pre-drop",
         "SHOW_1VX_THREATS")])
    e = scheduled[0]
    assert e.peak_us == 91_500_000
    assert e.start_us < e.peak_us < e.end_us
    assert e.lead_us == tf.WORLD_STRIP_1VX.footprint.pre_roll_us + \
        tf.WORLD_STRIP_1VX.footprint.peak_offset_us


def test_scheduled_elements_come_back_in_time_order():
    out = nm.schedule_around(10_000_000, [
        ("B", tf.BLOOD_WIPE.footprint, "death", "TRANSITION_TO_NEXT_SCENE"),
        ("W", tf.WORLD_STRIP_1VX.footprint, "pre-drop", "SHOW_1VX_THREATS")])
    assert [e.name for e in out] == ["W", "B"]


def test_the_ledger_is_sorted_plain_text():
    lines = nm.numeric_timeline([(2_000_000, "FRAG"), (1_000_000, "anchor")])
    assert "anchor" in lines[0] and "FRAG" in lines[1]
    assert lines[0].strip().startswith("1.000000")
