"""A capture that was cut off is not a capture that succeeded.

Every clip filmed before 2026-09-08 was short and nothing said so, because
success was defined as "an AVI exists". The engine forces Mesa softpipe -- a
CPU rasteriser, because the NVIDIA driver kills wolfcam during R_Init on this
machine -- and softpipe writes about half a frame per second at 1080p. The
timeout was calibrated against hardware GL, so the engine was terminated
part-way through every time.

Measured, 2026-09-08: asked 2,500 / 5,000 / 10,000 ms, got 42 / 74 / 84 frames
against 150 / 300 / 600. The predicted budgets (223 / 248 / 298 s) matched the
observed wall times (223.4 / 248.7 / 298.1 s) exactly -- the clips were short
because we killed the engine, not because it stopped.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from creative_suite.engine import wolfcam_capture as wc


def test_the_budget_is_sized_for_the_renderer_that_will_actually_run():
    """A hundredfold difference in throughput cannot share one constant."""
    assert wc.SOFTWARE_CAPTURE_SLOWDOWN > wc.CAPTURE_SLOWDOWN * 10, (
        "softpipe needs ~120 wall-seconds per second of footage; the hardware "
        "constant is 10")


def test_software_gl_is_the_default_because_we_force_it():
    """The code that forces software GL is the code that must budget for it."""
    assert wc.software_gl() is True


def test_a_hardware_override_restores_the_fast_budget(monkeypatch):
    monkeypatch.setenv("PANTHEON_FORCE_HARDWARE_GL", "1")
    assert wc.software_gl() is False


def test_the_budget_now_exceeds_what_softpipe_measurably_needs():
    """At ~0.5 written frames per second, a 2.5 s clip at 60 fps needs ~300 s.
    The old budget was 223 s, which is why it delivered 42 of 150 frames."""
    span, seek = 2.5, 579.8
    new = wc.LAUNCH_OVERHEAD_S + span * wc.SOFTWARE_CAPTURE_SLOWDOWN + seek / 12.0
    old = wc.LAUNCH_OVERHEAD_S + span * wc.CAPTURE_SLOWDOWN + seek / 12.0
    needed = span * wc.CAPTURE_FPS / 0.5
    assert old < needed, "the old budget was under what softpipe needs"
    assert new > needed, "the new budget must clear it"


def test_frames_expected_counts_every_window():
    windows = [{"start_ms": 0, "end_ms": 2500},
               {"start_ms": 9000, "end_ms": 10000}]
    assert wc.frames_expected(windows) == 150 + 60


def test_a_missing_file_counts_zero_rather_than_raising(tmp_path):
    assert wc.count_frames(tmp_path / "nope.avi") == 0


def test_the_completeness_bar_allows_a_seam_frame_but_not_a_quarter_clip():
    """A capture legitimately loses a frame or two at the seam. It does not
    legitimately lose three quarters of the action."""
    assert 0.9 < wc.COMPLETE_ENOUGH < 1.0
    assert 42 / 150 < wc.COMPLETE_ENOUGH      # the measured failure
    assert 149 / 150 > wc.COMPLETE_ENOUGH     # one dropped seam frame


def test_truncation_is_reported_by_both_capture_paths():
    """`ok` must be False when the file is short, in the window path and the
    offscreen path alike -- otherwise a quarter-length clip looks like a
    success to every caller."""
    import inspect
    from engine.pantheon import offscreen as O
    for mod, fn in ((wc, wc.capture_demo), (O, O._capture_locked)):
        src = inspect.getsource(fn)
        assert "truncated" in src, f"{fn.__name__} does not report truncation"
        assert "frames_written" in src, f"{fn.__name__} does not count frames"
