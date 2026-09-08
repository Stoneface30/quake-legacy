"""ONE ENGINE AT A TIME, ACROSS EVERY RENDER PATH.

The staging install is a single directory with a single `capture.cfg`, a
single `videos/` and a single console log. Two renderers using it at once do
not queue -- they overwrite each other's config and collect each other's
files.

THIS IS NOT HYPOTHETICAL. On 2026-09-07 the headless A/B launched the engine
while the review proxy held the directory: the cfg on disk turned out to be a
proxy capture with a different seek, the headless process exited rc=1 in two
seconds, and the console log recorded somebody else's run. The review proxy
had taken a lock; the offscreen backend had never heard of it.

So both paths use the SAME file and the SAME convention: the lock holds a
PID, a lock whose holder is gone is stale and may be taken, and a caller that
cannot get it waits rather than barging in. The convention is deliberately
identical to `review_proxy._try_acquire_lock` -- matching behaviour matters
more than sharing code across a branch boundary, and the handoff notes say to
collapse the two once both branches are merged.
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

from engine.pantheon import store as S


class CaptureBusy(RuntimeError):
    """Another renderer holds the staging install."""


def lock_path() -> Path:
    return S.PROJECT_ROOT / "output" / "demo_v2" / "_capture.lock"


def _alive(pid: int) -> bool:
    try:
        from creative_suite.engine.process_liveness import process_alive
        return process_alive(pid)
    except Exception:                                          # noqa: BLE001
        return True          # cannot tell: assume the holder is real


def holder() -> int | None:
    """The PID currently holding the install, or None if nobody live does."""
    p = lock_path()
    if not p.exists():
        return None
    try:
        pid = int(p.read_text().strip())
    except (OSError, ValueError):
        return None
    if pid == os.getpid() or not _alive(pid):
        return None
    return pid


def try_acquire() -> bool:
    p = lock_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if holder() is not None:
        return False
    try:
        p.write_text(str(os.getpid()))
    except OSError:
        return False
    return True


def release() -> None:
    p = lock_path()
    try:
        if p.exists() and p.read_text().strip() == str(os.getpid()):
            p.unlink()
    except OSError:
        pass


@contextmanager
def held(*, purpose: str = "capture", wait_s: float = 0.0,
         poll_s: float = 2.0):
    """Hold the install for the duration of a capture.

    `wait_s=0` fails immediately, which is right for an interactive job that
    would rather report "busy" than block. A batch passes a real budget and
    waits its turn.
    """
    deadline = time.time() + max(wait_s, 0.0)
    while True:
        if try_acquire():
            break
        if time.time() >= deadline:
            raise CaptureBusy(
                f"{purpose}: the staging install is held by PID {holder()}; "
                f"another renderer is using it")
        time.sleep(poll_s)
    try:
        yield
    finally:
        release()
