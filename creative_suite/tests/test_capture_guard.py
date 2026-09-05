"""A capture must never take the screen from someone playing.

"its fucking alt tabing my game everytime you start a session."

The path that did it: server startup -> `review_proxy._ensure_worker()` ->
reclaim orphaned jobs -> worker drains them -> `capture_demo` opens a
wolfcam window -> Windows gives the new window the foreground -> the user
loses the round they are in.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import capture_guard as cg


# ── deciding whether it is safe to open a window ────────────────────────────

def test_a_running_game_is_detected(monkeypatch):
    monkeypatch.delenv(cg._ENV_ANYTIME, raising=False)
    monkeypatch.setattr(cg, "watched_games", lambda: ("quakelive_steam.exe",))

    class P:
        info = {"name": "QuakeLive_steam.exe"}   # case must not matter

    monkeypatch.setattr("psutil.process_iter", lambda attrs=None: [P()])
    assert cg.game_is_running() is True


def test_nothing_running_means_it_is_safe(monkeypatch):
    monkeypatch.delenv(cg._ENV_ANYTIME, raising=False)
    monkeypatch.setattr("psutil.process_iter", lambda attrs=None: [])
    assert cg.game_is_running() is False


def test_an_unreadable_process_list_waits(monkeypatch):
    """FAILS TOWARDS THE USER.

    A delayed clip costs nothing. A stolen foreground costs a round, so an
    unanswerable question is answered "they are playing".
    """
    monkeypatch.delenv(cg._ENV_ANYTIME, raising=False)

    def boom(attrs=None):
        raise OSError("no access")

    monkeypatch.setattr("psutil.process_iter", boom)
    assert cg.game_is_running() is True


def test_the_user_can_override(monkeypatch):
    monkeypatch.setenv(cg._ENV_ANYTIME, "1")
    monkeypatch.setattr("psutil.process_iter",
                        lambda attrs=None: (_ for _ in ()).throw(OSError()))
    assert cg.game_is_running() is False


def test_the_watch_list_is_configurable(monkeypatch):
    monkeypatch.setenv(cg._ENV_GAMES, "SomeGame.exe, other.exe")
    assert cg.watched_games() == ("somegame.exe", "other.exe")


# ── how the window is opened ────────────────────────────────────────────────

@pytest.mark.skipif(sys.platform != "win32", reason="Windows startup flags")
def test_capture_windows_are_minimized_and_not_activated():
    si = cg.quiet_startup_info()
    assert si is not None
    assert si.dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert si.wShowWindow == 7, "SW_SHOWMINNOACTIVE"


def test_every_wolfcam_launch_asks_for_a_quiet_window():
    """Both spawn sites, not just the one that was reported."""
    for rel in ("creative_suite/engine/wolfcam_capture.py",
                "creative_suite/engine/director_preview.py"):
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        i = src.index("wolfcam_cmd(")
        while i != -1:
            head = src.rfind("subprocess.Popen(", 0, i)
            if head != -1 and i - head < 200:
                block = src[head:src.index(")\n", i) + 2]
                assert "startupinfo=" in block, f"{rel}: activating launch"
            i = src.find("wolfcam_cmd(", i + 1)


# ── and the queue defers rather than failing ────────────────────────────────

def test_the_worker_parks_a_job_while_a_game_is_running():
    """Deferred, never FAILED: the reviewer keeps a spinner, not an error,
    and the clip appears once the game closes."""
    src = (REPO_ROOT / "creative_suite" / "engine"
           / "review_proxy.py").read_text(encoding="utf-8")
    i = src.index("def _worker_loop")
    block = src[i:i + 2000]
    assert "capture_guard.game_is_running()" in block
    # It goes back on the queue; it is not marked FAILED.
    j = block.index("game_is_running()")
    park = block[j:j + 300]
    assert "_queue.put(job)" in park and "FAILED" not in park
