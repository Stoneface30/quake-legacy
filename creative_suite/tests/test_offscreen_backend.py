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
    application is foreground; afterwards that application must still be
    foreground and the process must have shown no window on this desktop."""
    r = O.probe_isolation(dwell=1.5)
    assert r.ran, r.detail
    assert r.visible_windows == [], f"a window appeared on the user's desktop: {r.visible_windows}"
    assert r.foreground_before["hwnd"] == r.foreground_after["hwnd"], \
        "the foreground moved while a hidden-desktop process ran"
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
