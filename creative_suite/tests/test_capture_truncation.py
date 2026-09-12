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


def test_the_slow_budget_applies_only_when_software_gl_is_asked_for(
        monkeypatch):
    """Native GL is 13.5x faster, so budgeting for softpipe by default would
    let a genuinely hung capture run for a quarter of an hour."""
    monkeypatch.setenv(wc.GL_MODE_ENV, "native")
    assert wc.software_gl() is False
    monkeypatch.setenv(wc.GL_MODE_ENV, "software")
    assert wc.software_gl() is True


def test_the_software_budget_exceeds_what_softpipe_measurably_needs():
    """Kept because software mode still exists. At ~0.5 written frames per
    second a 2.5 s clip at 60 fps needs ~300 s; the old budget was 223 s,
    which is why it delivered 42 of 150 frames."""
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


# ── which renderer runs, which is what all of the above was really about ───

def test_native_gl_is_the_default():
    """Mesa softpipe was a workaround for a crash that does not reproduce.
    Measured on one 2,500 ms window: softpipe 303.4 s / 77 frames / 30.8 fps
    captured; NVIDIA 22.4 s / 150 frames / 60.0 fps."""
    assert wc.gl_mode() == "native"
    assert wc.software_gl() is False


def test_software_can_still_be_asked_for(monkeypatch):
    monkeypatch.setenv(wc.GL_MODE_ENV, "software")
    assert wc.software_gl() is True
    monkeypatch.setenv(wc.GL_MODE_ENV, "native")
    assert wc.software_gl() is False


def test_a_nonsense_gl_mode_is_refused(monkeypatch):
    monkeypatch.setenv(wc.GL_MODE_ENV, "turbo")
    with pytest.raises(ValueError, match="native or software"):
        wc.gl_mode()


def test_the_native_directory_holds_the_engine_and_no_mesa(tmp_path):
    """Windows resolves opengl32.dll from the executable's directory, so the
    ONLY thing that decides the renderer is whether those two files are
    beside the exe."""
    staging = tmp_path
    (staging / "wolfcamql.exe").write_bytes(b"exe")
    for name in wc.MESA_DLLS:
        (staging / name).write_bytes(b"mesa")
    (staging / "SDL.dll").write_bytes(b"sdl")

    d = wc.native_gl_dir(staging)
    assert (d / "wolfcamql.exe").exists()
    assert (d / "SDL.dll").exists(), "the engine's own dependencies must come"
    for name in wc.MESA_DLLS:
        assert not (d / name).exists(), f"{name} would put Mesa back in charge"


def test_a_mesa_dll_that_appears_later_is_removed(tmp_path):
    """Rebuilding the view must not leave a stale Mesa file behind."""
    staging = tmp_path
    (staging / "wolfcamql.exe").write_bytes(b"exe")
    d = wc.native_gl_dir(staging)
    (d / wc.MESA_DLLS[0]).write_bytes(b"sneaked in")
    wc.native_gl_dir(staging)
    assert not (d / wc.MESA_DLLS[0]).exists()


def test_the_exe_that_gets_launched_follows_the_mode(tmp_path, monkeypatch):
    staging = tmp_path
    (staging / "wolfcamql.exe").write_bytes(b"exe")
    monkeypatch.setenv(wc.GL_MODE_ENV, "software")
    assert wc.engine_exe(staging).parent == staging
    monkeypatch.setenv(wc.GL_MODE_ENV, "native")
    assert wc.engine_exe(staging).parent.name == "_native_gl"


def test_the_offscreen_path_launches_from_the_engine_directory():
    """cwd is part of the DLL search order; launching from staging could let
    Mesa back in through the side door."""
    import inspect
    from engine.pantheon import offscreen as O
    src = inspect.getsource(O._capture_locked)
    assert "Path(argv[0]).parent" in src


# ── the two bugs that stopped generation entirely (2026-09-08) ─────────────

def test_the_engine_path_and_the_staging_paths_are_all_absolute():
    """Launching the engine from ITS OWN directory (so Windows resolves
    opengl32.dll there) breaks every relative path in the argv. Measured:
    relative fs_basepath exits rc=1 in 0.1 s with NO stdout, NO stderr and
    nothing in any log -- which reads exactly like a hang and stopped clip
    generation dead."""
    from pathlib import Path
    argv = wc.wolfcam_cmd("safe", Path("output/demo_v2/_wolfcam_staging"))
    assert Path(argv[0]).is_absolute(), "argv[0] must be absolute"
    for i, a in enumerate(argv):
        if a in ("fs_homepath", "fs_basepath"):
            assert Path(argv[i + 1]).is_absolute(), f"{a} must be absolute"


def test_the_expected_frame_count_follows_the_profiles_own_rate():
    """Each profile captures at its OWN cl_aviFrameRate. Measuring a fast-review
    capture against the gameplay rate declares every fast-review clip
    under-sampled and 'too fast', then retimes a correct file.

    The rates are read from the profiles, never written here: this test once
    asserted a literal 30 and failed the day the fast-review master was made
    cheaper (20 fps) -- a test named "follows the profile" that froze a number."""
    from creative_suite.engine import master_profile as mp
    w = [{"start_ms": 0, "end_ms": 10000}]
    fast = int(mp.PROFILES[mp.FAST_REVIEW_PROFILE_NAME]["cl_aviFrameRate"])
    full = int(mp.PROFILES[mp.PROFILE_NAME]["cl_aviFrameRate"])
    assert fast != full, "the two masters must differ, or this test proves nothing"
    assert wc.profile_fps(mp.FAST_REVIEW_PROFILE_NAME) == fast
    assert wc.profile_fps(mp.PROFILE_NAME) == full
    assert wc.frames_expected(w, profile=mp.FAST_REVIEW_PROFILE_NAME) == 10 * fast
    assert wc.frames_expected(w, profile=mp.PROFILE_NAME) == 10 * full
    # a correct fast-review capture must not read as too fast
    rate = wc.profile_fps(mp.FAST_REVIEW_PROFILE_NAME)
    assert wc.playback_error(w, 300, rate) == pytest.approx(1.0)


def test_an_unknown_profile_falls_back_rather_than_raising():
    assert wc.profile_fps("NO_SUCH_PROFILE") == wc.CAPTURE_FPS
