"""Tests for Rule P1-EE event-localized speed effects."""
from __future__ import annotations

import pytest


def test_build_filter_returns_two_strings():
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    v, a = build_event_localized_slow_filter(event_t=2.5, slow_rate=0.5,
                                              window_s=0.8)
    assert isinstance(v, str) and v
    assert isinstance(a, str) and a


def test_video_filter_contains_setpts():
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    v, _ = build_event_localized_slow_filter(event_t=3.0, slow_rate=0.5,
                                              window_s=0.5)
    assert "setpts=" in v


def test_parens_balanced_in_video_filter():
    """Regression: old versions emitted unbalanced parens that crashed ffmpeg."""
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    v, _ = build_event_localized_slow_filter(event_t=3.0, slow_rate=0.5,
                                              window_s=0.8)
    assert v.count("(") == v.count(")")


def test_window_clamped_to_clip_duration():
    """If event_t + window_s exceeds clip_duration, the upper bound clamps."""
    from creative_suite.engine.effects.event_localized import (
        build_event_localized_slow_filter,
        _clamp_window,
    )
    # Direct test of the clamp math:
    w0, w1 = _clamp_window(event_t=4.9, window_s=0.8, clip_duration=5.0)
    assert 0.0 <= w0 < w1 <= 5.0 + 1e-6
    # Also checks that below-zero events clamp to 0.
    w0, w1 = _clamp_window(event_t=0.1, window_s=0.8, clip_duration=3.0)
    assert w0 == 0.0


def test_select_audio_mode_player_death_is_mute():
    from creative_suite.engine.effects.event_localized import select_audio_mode
    assert select_audio_mode("player_death") == "mute"


def test_select_audio_mode_weapon_is_speed_comp():
    from creative_suite.engine.effects.event_localized import select_audio_mode
    assert select_audio_mode("rail_fire") == "speed_comp"
    assert select_audio_mode("rocket_impact") == "speed_comp"
    assert select_audio_mode("grenade_direct") == "speed_comp"


def test_select_audio_mode_multi_kill_is_natural_quiet():
    from creative_suite.engine.effects.event_localized import select_audio_mode
    assert select_audio_mode("multi_kill") == "natural_quiet"


def test_audio_filter_mute_contains_volume_zero():
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    _, a = build_event_localized_slow_filter(event_t=2.0, slow_rate=0.5,
                                              window_s=0.5,
                                              audio_mode="mute")
    assert "volume=0" in a


def test_audio_filter_speed_comp_uses_atempo():
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    _, a = build_event_localized_slow_filter(event_t=2.0, slow_rate=0.5,
                                              window_s=0.5,
                                              audio_mode="speed_comp")
    assert "atempo=" in a


def test_requires_event_t():
    from creative_suite.engine.effects.event_localized import build_event_localized_slow_filter
    with pytest.raises(ValueError):
        build_event_localized_slow_filter(event_t=None, slow_rate=0.5,  # type: ignore[arg-type]
                                          window_s=0.5)
