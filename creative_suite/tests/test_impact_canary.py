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


def test_qa_warns_on_a_long_tail():
    rep = ic.qa(ic.ImpactClock(tail_us=900_000))
    assert rep["passes"]                  # a warning, not an error
    assert rep["warnings"][0]["check"] == "POST_DEATH_CAMERA_TOO_LONG"
    assert rep["warnings"][0]["span_ms"] == 900.0
