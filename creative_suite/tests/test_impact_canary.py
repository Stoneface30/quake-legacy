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


def test_no_fpv_return_keeps_the_cinematic_camera_through_the_tail():
    """Review: the FPV return before impact was messy; the camera should keep
    the shooter in view through impact and the tail."""
    c = ic.ImpactClock(return_to_fpv=False, insert_camera="CHASE",
                       tail_us=2_000_000)
    cams = [s for s in c.segments() if s["kind"] == "camera"]
    assert [s["camera"] for s in cams] == ["FPV", "CHASE"]
    assert cams[-1]["end_us"] == c.duration_us
    assert cams[-1]["presentation"] == pr.CINEMATIC_CLEAN
    # and a corpse-camera check now applies, since the tail IS cinematic
    rep = ic.qa(c)
    assert rep["passes"]
    assert rep["warnings"] and rep["warnings"][0]["check"] == "POST_DEATH_CAMERA_TOO_LONG"


def test_return_to_fpv_is_part_of_identity():
    assert ic.ImpactClock().clock_id != ic.ImpactClock(return_to_fpv=False).clock_id


# ── V3E hero grammar: the piecewise TimeMap carries no temporal debt ────────

from creative_suite.engine import impact_canary_render as icr  # noqa: E402


def _hero(rate=Fraction(2284, 5657)):
    return icr.HeroCut(scene_in_s=2.0, launch_s=3.375, T_s=4.5,
                       pass1_out_s=4.894, tail_s=2.0, slow_rate=rate)


def test_hero_timemap_is_fpv_replay_fpv():
    tm = _hero().timemap()
    assert [p["label"] for p in tm] == ["PASS1_FPV", "REPLAY_SIDE", "TAIL_FPV"]
    assert [p["rate"] for p in tm] == [1.0, pytest.approx(0.4037, abs=1e-3), 1.0]


def test_hero_timemap_is_gapless_and_the_slow_lengthens_the_movie():
    h = _hero(); tm = h.timemap()
    for a, b in zip(tm, tm[1:]):
        assert a["edit_out_s"] == b["edit_in_s"]
    source_total = sum(p["src_out_s"] - p["src_in_s"] for p in tm)
    assert h.edit_duration_s > source_total          # longer, never shorter
    assert tm[1]["edit_duration_s"] == pytest.approx(1.125 / 0.4037, abs=0.01)


def test_hero_tail_resumes_the_fpv_timeline_where_pass1_stopped():
    tm = _hero().timemap()
    assert tm[2]["src_in_s"] == tm[0]["src_out_s"]


def test_hero_timemap_passes_the_temporal_debt_check():
    from creative_suite.engine import edit_qa
    assert edit_qa.check_temporal_debt(_hero().timemap()) == []


def test_first_impact_is_natural_speed_and_replay_impact_is_later():
    h = _hero()
    assert h.first_impact_edit_s == 2.5
    assert h.replay_impact_edit_s > h.replay_start_edit_s > h.first_impact_edit_s


def test_replay_may_keep_the_explosion_past_the_tick():
    h = icr.HeroCut(scene_in_s=2.0, launch_s=3.375, T_s=4.5, pass1_out_s=4.9,
                    tail_s=2.0, slow_rate=Fraction(2284, 5657), replay_out_s=4.75)
    assert h.first_impact_edit_s == 2.5                 # the tick, not the replay end
    tm = h.timemap()[1]
    assert tm["src_out_s"] == 4.75
    assert h.replay_impact_edit_s < h.replay_end_edit_s
    assert h.replay_impact_edit_s == pytest.approx(tm["edit_in_s"] + 1.125 / 0.4037, abs=0.01)


def test_requested_rate_is_exact_and_distinct_from_measurement():
    """The original FPV is requested at exactly 1/1. A measured 0.995x is
    frame quantization and must never be reported as the rate."""
    tm = _hero().timemap()
    assert tm[0]["requested_rate"] == "1"
    assert tm[2]["requested_rate"] == "1"
    assert tm[1]["requested_rate"] == str(Fraction(2284, 5657))
    assert "measured_effective_rate" not in tm[0]     # only measurement adds it


def test_tail_never_skips_or_replays_source_time():
    h = _hero(); tm = h.timemap()
    assert tm[2]["src_in_s"] == tm[0]["src_out_s"]           # continues exactly
    assert tm[2]["src_out_s"] - tm[2]["src_in_s"] == h.tail_s
