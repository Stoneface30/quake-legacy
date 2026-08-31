"""Regression: action-peak detection must ignore a clip's own edge transients.

Measured 2026-08-28 across Part 4 T1 frags: find_action_peak() returned 0.02 s
on several clips (the very first frame) and 17.59/18.00 s on others (the very
last). That is the signature of onset detection firing on the hard cut in/out
of the clip rather than on game audio.

Consequences observed by the user: "all the frag are skipped", "the cuts are
from the end of clips that need to be cut off", and POV/third-person angles that
look like different frags because each landed on a different bogus moment.
"""
import numpy as np
import pytest

from creative_suite.engine import peak_guard


def _env(n, spikes):
    """Envelope of length n with unit spikes at the given sample indices."""
    e = np.full(n, 0.01, dtype=float)
    for i, amp in spikes:
        e[i] = amp
    return e


def test_ignores_leading_edge_transient():
    """A huge spike on frame 0 is the cut-in, not the frag."""
    env = _env(1000, [(0, 1.0), (600, 0.5)])
    t = peak_guard.peak_from_envelope(env, duration=10.0)
    assert t == pytest.approx(6.0, abs=0.2)


def test_ignores_trailing_edge_transient():
    """A spike in the final frames is the cut-out / round-end, not the frag."""
    env = _env(1000, [(999, 1.0), (400, 0.5)])
    t = peak_guard.peak_from_envelope(env, duration=10.0)
    assert t == pytest.approx(4.0, abs=0.2)


def test_picks_genuine_interior_peak():
    env = _env(1000, [(0, 0.9), (999, 0.9), (300, 0.4), (750, 0.8)])
    t = peak_guard.peak_from_envelope(env, duration=10.0)
    assert t == pytest.approx(7.5, abs=0.2)


def test_result_is_inside_the_guarded_region():
    env = _env(1000, [(0, 1.0)])
    d = 10.0
    t = peak_guard.peak_from_envelope(env, duration=d)
    lo, hi = peak_guard.guard_bounds(d)
    assert lo <= t <= hi


def test_short_clip_still_returns_a_usable_peak():
    """Guards must never collapse to an empty search window."""
    env = _env(120, [(60, 1.0)])
    t = peak_guard.peak_from_envelope(env, duration=1.2)
    assert 0.0 < t < 1.2


def test_guard_bounds_scale_with_duration():
    lo_s, hi_s = peak_guard.guard_bounds(3.0)
    lo_l, hi_l = peak_guard.guard_bounds(30.0)
    assert lo_s >= 0 and hi_s <= 3.0
    assert hi_l <= 30.0
    # A long clip must still exclude the trailing round-end region.
    assert hi_l < 30.0 - 1.0


def test_empty_envelope_falls_back_to_fraction():
    t = peak_guard.peak_from_envelope(np.array([]), duration=8.0)
    assert t == pytest.approx(8.0 * peak_guard.FALLBACK_FRACTION, abs=0.01)
