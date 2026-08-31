"""Variable slow-mo strength must land the cut on the music -- and nowhere else.

The accent's strength is solved, not assumed: the slow window is the only
elastic part of a segment, so the rate that makes the segment end on a beat can
be computed. Three things have to stay true for that to be worth anything, and
each is easy to break silently:

  * the duration model must match what the renderer actually builds. If the
    solver models a window the renderer does not produce, it returns a rate
    whose predicted landing is fiction.
  * the strength must stay inside a band a viewer reads as slow-motion. Solving
    for an exact landing with no bound would produce 0.05x crawls and 0.95x
    non-effects.
  * this must never ADD an accent. The user's constraint was "use existing
    slowmo dont make the video a yoyo" -- strength is tuned only on shots that
    were already chosen, and only on short single-frag clips.
"""
from __future__ import annotations

import pytest

from creative_suite.engine import render_highlight as RH
from creative_suite.engine.effects import speed_ramp as SR


def out_len(w0, a, b, w1, rate):
    """The renderer's three-segment accent, as a duration."""
    return (a - w0) + (b - a) / rate + (w1 - b)


class TestAccentWindow:
    def test_renderer_and_solver_share_one_window(self):
        # Not a tautology: it pins the window to a single definition. The bug
        # this prevents is the two drifting apart (they once used different
        # post-peak holds, 1.1s vs 0.9s).
        w0, w1, peak = 0.0, 7.0, 3.5
        a, b = RH.accent_window(w0, w1, peak)
        assert a == pytest.approx(peak - RH.SLOW_PRE_S)
        assert b == pytest.approx(peak + RH.SLOW_POST_S)
        assert w0 <= a < b <= w1

    def test_peak_at_the_very_edge_stays_inside_the_clip(self):
        for peak in (0.0, 7.0, -3.0, 99.0):
            a, b = RH.accent_window(0.0, 7.0, peak)
            assert 0.0 <= a < b <= 7.0


class TestLanding:
    def test_solved_rate_lands_on_the_chosen_beat(self):
        w0, w1 = 0.0, 7.0
        a, b = RH.accent_window(w0, w1, 3.5)
        beats = [round(0.5 * i, 3) for i in range(1, 80)]
        got = SR.accent_rate_for_landing(w0, a, b, w1, 12.0, beats)
        assert got is not None
        rate, land, _kind = got
        assert 12.0 + out_len(w0, a, b, w1, rate) == pytest.approx(land, abs=1e-6)

    def test_rate_stays_inside_the_strength_band(self):
        w0, w1 = 0.0, 7.0
        a, b = RH.accent_window(w0, w1, 3.5)
        beats = [round(0.05 * i, 3) for i in range(1, 900)]   # very dense grid
        rate, _land, _k = SR.accent_rate_for_landing(w0, a, b, w1, 0.0, beats)
        assert SR.SLOW_RATE_MIN <= rate <= SR.SLOW_RATE_MAX

    def test_prefers_a_drop_over_a_downbeat_over_a_plain_beat(self):
        w0, w1 = 0.0, 7.0
        a, b = RH.accent_window(w0, w1, 3.5)
        beats = [round(0.25 * i, 3) for i in range(1, 200)]
        plain = SR.accent_rate_for_landing(w0, a, b, w1, 0.0, beats)
        assert plain[2] == "beat"
        # promote one reachable beat to a downbeat, then to a drop
        cand = [t for t in beats
                if (r := (b - a) / max(1e-9, t - (a - w0) - (w1 - b)))
                and SR.SLOW_RATE_MIN <= r <= SR.SLOW_RATE_MAX]
        assert cand, "fixture must offer a reachable landing"
        pick = cand[len(cand) // 2]
        assert SR.accent_rate_for_landing(
            w0, a, b, w1, 0.0, beats, downbeats=[pick])[2] == "downbeat"
        assert SR.accent_rate_for_landing(
            w0, a, b, w1, 0.0, beats, downbeats=[pick], drops=[pick])[2] == "drop"

    def test_no_beats_means_no_lock(self):
        w0, w1 = 0.0, 7.0
        a, b = RH.accent_window(w0, w1, 3.5)
        assert SR.accent_rate_for_landing(w0, a, b, w1, 0.0, []) is None

    def test_unreachable_grid_returns_none_rather_than_distorting(self):
        # Every beat sits where only an absurd rate would land. The caller must
        # keep the default rate, not stretch the shot to chase the grid.
        w0, w1 = 0.0, 7.0
        a, b = RH.accent_window(w0, w1, 3.5)
        assert SR.accent_rate_for_landing(w0, a, b, w1, 0.0, [0.2, 0.4]) is None


class TestNoYoYo:
    def test_only_short_clips_are_eligible(self):
        # The guard the build loop applies. A long multi-kill keeps the
        # standard rate so the treatment stays consistent across a video.
        assert RH.SHORT_CLIP_SLOWMO_S == pytest.approx(7.0)
        assert 6.5 <= RH.SHORT_CLIP_SLOWMO_S
        assert not (29.15 <= RH.SHORT_CLIP_SLOWMO_S)

    def test_band_reads_as_slow_motion(self):
        # 30%-60% was the user's stated range; anything outside stops being an
        # accent and starts being a defect.
        assert 0.25 <= SR.SLOW_RATE_MIN <= 0.35
        assert 0.55 <= SR.SLOW_RATE_MAX <= 0.70
        assert SR.SLOW_RATE_MIN < SR.SLOW_RATE < SR.SLOW_RATE_MAX

    def test_a_rate_never_creates_an_accent(self):
        # slow_rate is inert unless slowmo was already chosen: the renderer's
        # non-slowmo branch has no rate term at all.
        import inspect
        src = inspect.getsource(RH.render_frag)
        head, _, tail = src.partition("else:")
        assert "rate" in head and "slow_rate" in head
        assert "rate" not in tail.split("filt +=")[0]
