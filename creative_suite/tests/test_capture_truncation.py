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


# ── the rate, which is a different defect from the length ──────────────────
#
# `cl_aviFrameRate` is frames per second of DEMO time: it decides temporal
# resolution, not how much of the action is covered. A capture can write half
# the frames the rate implies, cover the whole window, and be COMPLETE -- and
# still be unusable, because the header declares a rate it did not achieve and
# the clip plays at double speed.
#
# Confirmed by eye on 2026-09-08: the 77-frame clip's first frame is the jump
# pad at the start of the window and its last frame is the kill at the end.
# Nothing was missing. The clock was wrong.


def test_the_true_rate_comes_from_the_window_the_clip_covered():
    w = [{"start_ms": 0, "end_ms": 2500}]
    assert wc.true_frame_rate(w, 150) == pytest.approx(60.0)
    assert wc.true_frame_rate(w, 77) == pytest.approx(30.8)


def test_a_clip_that_covers_its_window_at_half_the_rate_plays_twice_too_fast():
    w = [{"start_ms": 0, "end_ms": 2500}]
    assert wc.playback_error(w, 150) == pytest.approx(1.0)
    assert wc.playback_error(w, 77) == pytest.approx(1.95, abs=0.02)


def test_an_empty_capture_reports_no_rate_rather_than_dividing_by_zero():
    w = [{"start_ms": 0, "end_ms": 2500}]
    assert wc.true_frame_rate(w, 0) == 0.0
    assert wc.playback_error(w, 0) == 0.0
    assert wc.true_frame_rate([], 10) == 0.0


def test_retiming_is_a_remux_and_keeps_every_frame(tmp_path):
    """The frames are the truth; only the clock was wrong. Re-encoding would
    cost a generation of quality to fix a container field."""
    src = tmp_path / "in.avi"
    import subprocess as sp
    sp.run([str(wc.FFMPEG), "-v", "error", "-y", "-f", "lavfi",
            "-i", "testsrc=size=160x90:rate=60:duration=1",
            "-c:v", "mjpeg", str(src)], check=True, timeout=180)
    before = wc.count_frames(src)
    assert before == 60
    wc.retime(src, 30.0)
    assert wc.count_frames(src) == before, "retiming must not drop frames"


def test_the_speed_check_and_the_coverage_check_are_different_questions():
    """Conflating them is how a complete clip got reported as truncated."""
    import inspect
    src = inspect.getsource(wc.capture_demo)
    assert "played_too_fast_by" in src
    assert "under_sampled" in src, (
        "coverage is still worth reporting -- it is just not the same thing "
        "as the rate")


def test_both_capture_paths_measure_the_rate():
    import inspect
    from engine.pantheon import offscreen as O
    for fn in (wc.capture_demo, O._capture_locked):
        src = inspect.getsource(fn)
        assert "played_too_fast_by" in src, f"{fn.__name__} ignores the rate"
        assert "retime" in src, f"{fn.__name__} does not repair the clock"


def test_the_computed_verdict_is_not_overwritten_by_the_process_result():
    """`**run.as_dict()` carries its own "ok" and was spread LAST, so the
    verdict computed from windows, quiet and truncation never survived. A
    capture that wrote a quarter of its frames reported ok=True."""
    import inspect
    from engine.pantheon import offscreen as O
    src = inspect.getsource(O._capture_locked)
    spread = src.index("run.as_dict()")
    verdict = src.index('"ok": bool(avis)')
    assert spread < verdict, (
        "the process dict must be spread BEFORE the computed verdict, or it "
        "overwrites it")
    assert "engine_ok" in src, "the process-level result should still be "                               "available, under a name that says what it is"
