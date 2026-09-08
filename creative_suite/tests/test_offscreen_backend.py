"""The reviewer must never take the screen again.

These are the acceptance criteria for PANTHEON_QUAKE_OFFSCREEN, written as
tests. The mechanism check runs anywhere Windows does and uses a HARMLESS
GUI process, never the game: if hidden desktops did not work we would learn
it without putting a Quake window on the user's screen.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from engine.pantheon import offscreen as O

windows_only = pytest.mark.skipif(sys.platform != "win32",
                                  reason="hidden desktops are a Windows mechanism")


@windows_only
def test_a_gui_process_on_the_hidden_desktop_is_invisible_and_takes_no_focus():
    """THE acceptance test. A GUI process is started while another
    application is foreground; afterwards the process must have shown no
    window on this desktop and must not own the foreground.

    IT ASKS WHO HAS THE FOREGROUND, NOT WHETHER IT MOVED. The earlier reading
    demanded the foreground window be identical before and after, and on
    2026-09-07 it failed because the operator changed windows during the one
    and a half seconds it ran. An operator switching app is not the render's
    doing, which is the distinction OffscreenRun.stole_focus already draws.
    """
    r = O.probe_isolation(dwell=1.5)
    assert r.ran, r.detail
    assert r.visible_windows == [], f"a window appeared on the user's desktop: {r.visible_windows}"
    assert not r.stole_focus, "the hidden-desktop process took the foreground"
    assert r.isolated


@windows_only
def test_the_desktop_is_created_and_closed_rather_than_leaked():
    with O.HiddenDesktop() as d:
        assert d.handle
    assert d.handle is None


@windows_only
def test_a_spawn_needs_its_desktop_and_the_process_is_reaped():
    with O.HiddenDesktop():
        p = O.spawn_on_desktop(["cmd.exe", "/c", "exit", "7"])
        try:
            assert p.wait(20) == 7
        finally:
            p.close()


def test_focus_is_blamed_on_the_render_only_when_the_render_holds_it():
    """A foreground change is not by itself a stolen screen: the operator may
    switch app mid-capture, and a test that cried wolf at that would be
    switched off. The question is whether the foreground BELONGS to the
    render process."""
    moved_but_not_ours = O.OffscreenRun(
        True, 0, 1.0, [], {"hwnd": 1, "pid": 100}, {"hwnd": 2, "pid": 200},
        render_pid=999, foreground_during=[{"hwnd": 2, "pid": 200}])
    assert moved_but_not_ours.foreground_moved
    assert not moved_but_not_ours.stole_focus

    ours = O.OffscreenRun(
        True, 0, 1.0, [], {"hwnd": 1, "pid": 100}, {"hwnd": 1, "pid": 100},
        render_pid=999, foreground_during=[{"hwnd": 5, "pid": 999}])
    assert ours.stole_focus, "a mid-capture grab that ended before we looked must still fail"


def test_the_engine_environment_names_the_video_driver():
    """SDL's default probe fails on this machine and the engine answers by
    reverting to safe values -- 856x480 instead of the requested frame. An
    offscreen capture that films a quarter of the frame is not a capture."""
    assert O.ENGINE_ENV()["SDL_VIDEODRIVER"] == "windib"


def test_running_the_engine_asks_the_render_permit(monkeypatch):
    """Offscreen removes the stolen foreground, not GPU and disk contention.
    A protected game running still defers."""
    from engine.pantheon import render_permit as rp
    from creative_suite.engine import capture_guard
    monkeypatch.setattr(capture_guard, "game_is_running", lambda: True)
    monkeypatch.setattr(O, "spawn_on_desktop",
                        lambda *a, **k: pytest.fail("spawned despite a running game"))
    with pytest.raises(rp.RenderNotPermitted):
        O.run_engine(["cmd.exe"], cwd=Path("."), timeout=1)


# ── the asset set is not a manual step ──────────────────────────────────────

@pytest.fixture
def free_lock(tmp_path, monkeypatch):
    """A private capture lock, so a test never queues behind the real
    renderer -- or takes the install away from it."""
    from engine.pantheon import capture_lock as CL
    monkeypatch.setattr(CL, "lock_path", lambda: tmp_path / "_capture.lock")
    return tmp_path


def test_a_capture_installs_the_default_asset_set(monkeypatch, tmp_path, free_lock):
    """assets.py existed for a session before anything called it. Every
    render before that call filmed against whatever pk3s happened to be
    sitting in the gamedir, which is the exact failure the module exists to
    end -- so a capture must not depend on a caller remembering the CLI."""
    from engine.pantheon import assets as A
    from engine.pantheon import offscreen as O

    calls = []
    monkeypatch.setattr(A, "install", lambda name, staging: (
        calls.append((name, staging)),
        {"set": name, "linked": [], "already_present": [], "removed": [],
         "missing": [], "ok": True})[1])
    monkeypatch.setattr(O, "run_engine", lambda *a, **k: O.OffscreenRun(
        True, 0, 1.0, [], {}, {}, render_pid=1))

    from creative_suite.engine import wolfcam_capture as wc
    monkeypatch.setattr(wc, "write_capture_cfg", lambda *a, **k: "exec x.cfg\n")
    monkeypatch.setattr(wc, "write_engine_file", lambda *a, **k: None)
    monkeypatch.setattr(wc, "wolfcam_cmd", lambda *a, **k: ["wolfcamql.exe"])

    O.capture("safe.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1}],
             staging=tmp_path)
    assert calls == [(O.DEFAULT_ASSET_SET, tmp_path)]


def test_a_caller_can_opt_out_of_asset_management(monkeypatch, tmp_path, free_lock):
    from engine.pantheon import assets as A
    from engine.pantheon import offscreen as O

    monkeypatch.setattr(A, "install", lambda *a, **k: pytest.fail(
        "install() called despite asset_set=None"))
    monkeypatch.setattr(O, "run_engine", lambda *a, **k: O.OffscreenRun(
        True, 0, 1.0, [], {}, {}, render_pid=1))
    from creative_suite.engine import wolfcam_capture as wc
    monkeypatch.setattr(wc, "write_capture_cfg", lambda *a, **k: "exec x.cfg\n")
    monkeypatch.setattr(wc, "write_engine_file", lambda *a, **k: None)
    monkeypatch.setattr(wc, "wolfcam_cmd", lambda *a, **k: ["wolfcamql.exe"])

    O.capture("safe.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1}],
             staging=tmp_path, asset_set=None)


def test_the_result_names_the_asset_set_that_was_used(monkeypatch, tmp_path, free_lock):
    from engine.pantheon import assets as A
    from engine.pantheon import offscreen as O

    monkeypatch.setattr(A, "install", lambda name, staging: {
        "set": name, "linked": [], "already_present": [], "removed": [],
        "missing": [], "ok": True})
    monkeypatch.setattr(O, "run_engine", lambda *a, **k: O.OffscreenRun(
        True, 0, 1.0, [], {}, {}, render_pid=1))
    from creative_suite.engine import wolfcam_capture as wc
    monkeypatch.setattr(wc, "write_capture_cfg", lambda *a, **k: "exec x.cfg\n")
    monkeypatch.setattr(wc, "write_engine_file", lambda *a, **k: None)
    monkeypatch.setattr(wc, "wolfcam_cmd", lambda *a, **k: ["wolfcamql.exe"])

    res = O.capture("safe.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1}],
                    staging=tmp_path, asset_set="STOCK")
    assert res["asset_set"] == "STOCK"


# ── one engine at a time ────────────────────────────────────────────────────

def test_a_capture_refuses_while_another_renderer_holds_the_install(
        monkeypatch, tmp_path):
    """2026-09-07: a headless capture launched while the review proxy held the
    staging install. The cfg on disk turned out to be the proxy's, the engine
    exited rc=1 in two seconds, and the console log recorded somebody else's
    run. Both paths now use one lock."""
    import os

    from engine.pantheon import capture_lock as CL
    from engine.pantheon import offscreen as O

    lock = tmp_path / "_capture.lock"
    monkeypatch.setattr(CL, "lock_path", lambda: lock)
    monkeypatch.setattr(CL, "_alive", lambda pid: True)
    lock.write_text(str(os.getpid() + 1))          # a live stranger

    monkeypatch.setattr(O, "run_engine", lambda *a, **k: pytest.fail(
        "launched the engine while another renderer held the install"))
    with pytest.raises(CL.CaptureBusy):
        O.capture("safe.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1}],
                  staging=tmp_path, asset_set=None)


def test_a_dead_holder_does_not_block_forever(monkeypatch, tmp_path):
    """A crashed renderer must not lock the install out of use."""
    import os

    from engine.pantheon import capture_lock as CL

    lock = tmp_path / "_capture.lock"
    monkeypatch.setattr(CL, "lock_path", lambda: lock)
    monkeypatch.setattr(CL, "_alive", lambda pid: False)
    lock.write_text(str(os.getpid() + 1))
    assert CL.holder() is None
    assert CL.try_acquire()
    CL.release()
    assert not lock.exists()


def test_the_lock_is_released_even_when_the_capture_raises(monkeypatch, tmp_path):
    from engine.pantheon import capture_lock as CL

    lock = tmp_path / "_capture.lock"
    monkeypatch.setattr(CL, "lock_path", lambda: lock)
    with pytest.raises(ValueError):
        with CL.held(purpose="test"):
            assert lock.exists()
            raise ValueError("boom")
    assert not lock.exists(), "a failed capture kept the install locked"
