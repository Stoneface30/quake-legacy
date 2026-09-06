"""Never take the screen away from someone who is playing.

THE DEFECT, IN THE USER'S WORDS: "its fucking alt tabing my game everytime
you start a session."

Capture is not a background job. WolfcamQL is a full game client: starting
one creates a window, and Windows gives a newly created top-level window the
foreground. If the user is mid-round in Quake Live, that is a lost round.

The review proxy makes this worse by design. `reclaim_orphaned_jobs()` runs
at server startup so a restart does not leave the reviewer spinning forever
on jobs no worker owns -- which means every single server start can spawn a
capture, unprompted, at whatever moment the server happens to come up.

TWO INDEPENDENT PROTECTIONS, because either alone still loses a round:

1. DEFER WHILE A GAME IS RUNNING. A queued capture is not urgent; the round
   the user is playing is. The worker parks the job and tries again later.
   Nothing is dropped and nothing is failed -- the job stays QUEUED and runs
   the moment the game closes.

2. LAUNCH WITHOUT ACTIVATION. When a capture does run, the window is asked
   for minimized-and-not-activated (SW_SHOWMINNOACTIVE). Windows honours
   this for the initial show, so the capture no longer yanks the foreground
   from whatever the user is doing.

Protection 1 is the one that matters, and it is deliberately conservative:
if the process list cannot be read at all, we assume a game IS running and
wait, because a delayed clip costs nothing and a stolen foreground costs a
round.
"""
from __future__ import annotations

import os
import subprocess
import sys

# Processes whose presence means "the user is playing, do not touch the
# screen". Lower-cased, matched exactly against the executable name.
DEFAULT_GAMES = (
    "quakelive_steam.exe",
    "quakelive.exe",
    "quakelive_steam_x64.exe",
    "quakelive_x64.exe",
)

# CS_CAPTURE_GAMES overrides the watch list (comma separated). It changes
# WHICH processes count as "playing", never whether playing matters.
_ENV_GAMES = "CS_CAPTURE_GAMES"

# CS_CAPTURE_ANYTIME is GONE, deliberately and without a fallback. It meant
# "capture even while a game is running", which is the one thing the render
# permit forbids outright, and a second switch for the same decision is how
# the user ends up hunting for the one that is actually in effect. The single
# authority is engine.pantheon.render_permit; PANTHEON_RENDER=off is the way
# to turn rendering off, and nothing turns the running-game rule off.
#
# This function now answers ONLY "is a game on screen". Whether that means
# anything is the permit's decision, not this module's.


def watched_games() -> tuple[str, ...]:
    raw = os.getenv(_ENV_GAMES)
    if not raw:
        return DEFAULT_GAMES
    return tuple(p.strip().lower() for p in raw.split(",") if p.strip())


def game_is_running() -> bool:
    """Is something we must not interrupt on screen right now?

    FAILS TOWARDS THE USER. An unreadable process list returns True: we
    would rather delay a capture we could have run than steal the screen
    from a game we could not see.
    """
    names = watched_games()
    try:
        import psutil
    except ImportError:
        return _game_is_running_fallback(names)
    try:
        for p in psutil.process_iter(["name"]):
            n = (p.info.get("name") or "").lower()
            if n in names:
                return True
    except Exception:                                          # noqa: BLE001
        return True
    return False


def _game_is_running_fallback(names: tuple[str, ...]) -> bool:
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
            text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return True
    low = out.lower()
    return any(f'"{n}"' in low for n in names)


def quiet_startup_info() -> object | None:
    """Show a capture window minimized, and do not give it the foreground.

    Returns a STARTUPINFO on Windows and None elsewhere, so callers can pass
    it straight to Popen(startupinfo=...) on every platform.
    """
    if sys.platform != "win32":
        return None
    si = subprocess.STARTUPINFO()                # type: ignore[attr-defined]
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
    # 7 == SW_SHOWMINNOACTIVE: appear minimized, leave the foreground alone.
    si.wShowWindow = 7
    return si
