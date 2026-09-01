"""The impact editorial clock: shape, invariants, and QA over it."""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import impact_canary as ic
from creative_suite.engine import presentation as pr

TRACK = [(3375, 0.0, 0.0, 0.0), (4000, 5.0, 0.0, 0.0), (4500, 9.0, 0.0, 0.0)]


def test_launch_resolves_from_the_track_not_a_constant():
    c = ic.from_projectile_track(TRACK)
    assert c.launch_us == -1_125_000
    assert c.impact_edit_us == 2_500_000
    assert c.edit(c.launch_us) == 1_375_000


def test_default_clock_matches_the_directive():
    c = ic.ImpactClock()
    assert c.scene_start_us == -2_500_000
    assert c.attention_us == -500_000
    assert c.fpv_return_us == -150_000
    assert c.tail_us == 300_000
    assert c.duration_us == 2_800_000


def test_attention_must_begin_before_impact():
    with pytest.raises(ValueError, match="BEFORE impact"):
        ic.ImpactClock(attention_us=0)
    with pytest.raises(ValueError, match="BEFORE impact"):
        ic.ImpactClock(attention_us=100_000)


def test_fpv_owns_the_impact():
    """The insert must end before the return; the original aim owns T."""
    with pytest.raises(ValueError, match="owns the impact"):
        ic.ImpactClock(insert_start_us=-100_000, fpv_return_us=-150_000)
    with pytest.raises(ValueError):
        ic.ImpactClock(fpv_return_us=50_000)


def test_insert_cannot_start_before_launch():
    with pytest.raises(ValueError, match="at or after launch"):
        ic.ImpactClock(insert_start_us=-1_200_000)


def test_insert_must_be_a_cinematic_camera():
    with pytest.raises(ValueError, match="cinematic camera"):
        ic.ImpactClock(insert_camera="FPV")


def test_no_corpse_camera():
    with pytest.raises(ValueError):
        ic.ImpactClock(tail_us=-1)


def test_segments_separate_camera_from_time():
    c = ic.ImpactClock()
    cams = [s for s in c.segments() if s["kind"] == "camera"]
    times = [s for s in c.segments() if s["kind"] == "time"]
    assert [s["camera"] for s in cams] == ["FPV", "PROJECTILE", "FPV"]
    assert cams[1]["presentation"] == pr.CINEMATIC_CLEAN
    assert cams[0]["presentation"] == cams[2]["presentation"] == pr.FPV_GAMEPLAY
    # camera spans are gapless and end at the programme end
    for a, b in zip(cams, cams[1:]):
        assert a["end_us"] == b["start_us"]
    assert cams[-1]["end_us"] == c.duration_us
    # the slow span is a separate fact and starts at T-500
    assert times == [{"kind": "time", "rate": "1/2",
                      "start_us": 2_000_000, "end_us": 2_350_000}]


def test_fpv_only_control_has_one_camera_span():
    c = ic.from_projectile_track(TRACK, insert=False)
    cams = [s for s in c.segments() if s["kind"] == "camera"]
    assert len(cams) == 1 and cams[0]["camera"] == "FPV"
    assert not c.has_insert


def test_impact_is_primary_and_fire_is_support():
    ev = dict((e, (t, p)) for e, t, p in ic.ImpactClock().sync_events())
    assert ev["ROCKET_IMPACT"][1] is True
    assert ev["PROJECTILE_LAUNCH"][1] is False
    assert ev["ROCKET_IMPACT"][0] == 2_500_000


def test_clock_id_is_deterministic_and_tracks_the_treatment():
    a, b = ic.ImpactClock(), ic.ImpactClock()
    assert a.clock_id == b.clock_id
    assert a.clock_id != ic.ImpactClock(attention_us=-400_000).clock_id
    assert a.clock_id != ic.ImpactClock(slow_rate=Fraction(2, 3)).clock_id


def test_qa_passes_the_default_clock():
    rep = ic.qa(ic.ImpactClock())
    assert rep["passes"]
    assert rep["errors"] == []
    assert rep["warnings"] == []          # 300 ms tail is inside the 350 allowance


def test_a_long_fpv_tail_is_not_a_corpse_camera():
    """Review asked for ~2 s after the frag to hear the music resolve. In FPV
    the live player is the subject, so POST_DEATH must not fire."""
    rep = ic.qa(ic.ImpactClock(tail_us=2_000_000))
    assert rep["passes"] and rep["warnings"] == []


def test_a_long_cinematic_tail_still_warns():
    """Same length, but ending on the cinematic camera: that IS the corpse cam."""
    c = ic.ImpactClock(tail_us=2_000_000)
    import dataclasses
    segs = c.segments()
    # simulate a programme whose last camera span is cinematic
    from creative_suite.engine import edit_qa
    f = edit_qa.check_post_death(c.impact_edit_us / 1000.0, c.duration_us / 1000.0)
    assert f and f[0].check == "POST_DEATH_CAMERA_TOO_LONG"


# ── review iteration: music decides the slow ────────────────────────────────

def test_beat_locked_rate_makes_the_flight_a_whole_number_of_beats():
    rate, k = ic.beat_locked_rate(1_125_000, 161.5, want=0.43)
    period = Fraction(60_000_000) / Fraction(161.5).limit_denominator(10_000)
    assert k == 7
    assert abs(float(Fraction(1_125_000) / rate / period) - 7) < 1e-6
    assert 0.40 < float(rate) < 0.47


def test_beat_locked_rate_respects_the_range():
    with pytest.raises(ValueError):
        ic.beat_locked_rate(1_125_000, 161.5, lo=0.99, hi=1.0)
    with pytest.raises(ValueError):
        ic.beat_locked_rate(0, 120.0)


def test_slow_span_defaults_to_the_v3_shape():
    c = ic.ImpactClock()
    assert c.slow_span_us == (c.attention_us, c.fpv_return_us)


def test_slow_span_can_cover_the_whole_flight():
    c = ic.ImpactClock(slow_start_us=-1_125_000, slow_end_us=0,
                       slow_rate=Fraction(13, 30), tail_us=2_000_000)
    t = next(s for s in c.segments() if s["kind"] == "time")
    assert (t["start_us"], t["end_us"]) == (c.edit(-1_125_000), c.edit(0))
    assert c.duration_us == 4_500_000


def test_slow_span_must_stay_inside_the_scene():
    with pytest.raises(ValueError, match="inside the scene"):
        ic.ImpactClock(slow_start_us=-9_000_000, slow_end_us=0)


def test_ordering_is_a_choice_not_a_rule():
    for o in ic.ORDERINGS:
        ic.ImpactClock(ordering=o)
    with pytest.raises(ValueError):
        ic.ImpactClock(ordering="RANDOM")


def test_ordering_and_slow_span_are_part_of_identity():
    base = ic.ImpactClock()
    assert base.clock_id != ic.ImpactClock(ordering="REPLAY_THEN_FPV").clock_id
    assert base.clock_id != ic.ImpactClock(slow_start_us=-1_125_000,
                                           slow_end_us=0).clock_id
