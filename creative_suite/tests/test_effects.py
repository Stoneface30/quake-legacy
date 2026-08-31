"""Tests for the P1-Q speed-effect engine.

This module did not exist until 2026-08-28; renders shipped with no effects at
all. These pin the arithmetic so a silent regression can't recur.
"""
import pytest

from creative_suite.engine.effects import speed_ramp as effects
from creative_suite.engine.effects.speed_ramp import SpeedPlan


def _plan(**kw):
    base = dict(src_start=0.0, peak_t=4.0, src_end=6.0)
    base.update(kw)
    return SpeedPlan(**base)


def test_windows_bracket_the_peak():
    p = _plan()
    assert p.a == pytest.approx(4.0 - effects.SLOW_PRE_S)
    assert p.b == pytest.approx(4.0 + effects.SLOW_POST_S)
    assert p.a < p.peak_t < p.b


def test_slow_window_lengthens_playback():
    """The money shot must occupy MORE screen time than its source seconds."""
    p = _plan()
    src_slow = p.b - p.a
    out_slow = src_slow / p.slow_rate
    assert out_slow > src_slow


def test_speedup_shortens_the_approach():
    p = _plan()
    assert p.has_speedup
    approach_src = p.a - p.src_start
    assert approach_src / p.speedup_rate < approach_src


def test_output_duration_sums_all_three_stages():
    p = _plan()
    expected = ((p.a - p.src_start) / p.speedup_rate
                + (p.b - p.a) / p.slow_rate
                + (p.src_end - p.b))
    assert p.output_duration() == pytest.approx(expected)


def test_short_clip_has_no_speedup_stage():
    """A clip that is all action has no dead time to compress."""
    p = _plan(peak_t=0.4, src_end=2.0)
    assert not p.has_speedup


def test_fit_to_duration_hits_reachable_target():
    p = _plan(src_end=10.0, peak_t=7.0)
    fitted = effects.fit_to_duration(p, 8.5)
    assert fitted.output_duration() == pytest.approx(8.5, abs=0.05)


def test_fit_cannot_go_below_the_slow_window_floor():
    """The slow window + tail set a minimum frag length.

    Only the approach is compressible, so asking for less than
    (slow/rate + tail) is unreachable -- fit clamps instead of lying. This floor
    is what bounds how many frags fit in a 5-minute reel.
    """
    p = _plan(src_end=10.0, peak_t=7.0)
    floor = (p.b - p.a) / p.slow_rate + (p.src_end - p.b)
    fitted = effects.fit_to_duration(p, 1.0)
    assert fitted.output_duration() > floor
    assert fitted.speedup_rate == pytest.approx(3.2)


def test_fit_never_touches_the_slow_window():
    """Bending pace must not alter the money shot's rate."""
    p = _plan(src_end=10.0, peak_t=7.0)
    fitted = effects.fit_to_duration(p, 6.0)
    assert fitted.slow_rate == p.slow_rate
    assert (fitted.a, fitted.b) == (p.a, p.b)


def test_fit_is_clamped():
    p = _plan(src_end=10.0, peak_t=7.0)
    assert effects.fit_to_duration(p, 0.01).speedup_rate <= 3.2


def test_filter_emits_labels_and_all_stages():
    f = effects.build_filter(_plan())
    assert "[vout]" in f and "[aout]" in f
    assert f.count("[0:v]trim=") == 3   # atrim= would also match a bare "trim="
    assert "concat=n=3:v=1:a=0" in f


def test_filter_without_audio_omits_aout():
    f = effects.build_filter(_plan(), ain=None)
    assert "[aout]" not in f and "atrim" not in f


def test_atempo_chains_below_ffmpeg_minimum():
    """atempo accepts 0.5..100 per stage, so 0.3 must become a chain."""
    chain = effects._atempo_chain(0.3)
    assert chain.count("atempo=") >= 2
    product = 1.0
    for part in chain.split(","):
        product *= float(part.split("=")[1])
    assert product == pytest.approx(0.3, rel=1e-3)


def test_atempo_single_stage_when_in_range():
    assert effects._atempo_chain(0.75) == "atempo=0.7500"


def test_snap_to_beat_picks_next_beat():
    beats = [0.0, 1.0, 2.0, 3.0]
    assert effects.snap_to_beat(1.2, beats) == 2.0
    assert effects.snap_to_beat(5.0, beats) == 5.0
    assert effects.snap_to_beat(0.0, beats) == 0.0
