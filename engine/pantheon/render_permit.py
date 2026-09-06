"""One authority on whether anything may open a renderer window.

THE LAW THIS ENFORCES: the review website must never alt tab the user, and
serving the reviewer is NOT permission to render.

Those are two different things and they were one thing before. Starting the
review origin drained the capture queue, which launched WolfcamQL, which
took the foreground off a live game. The origin has every right to run while
the user plays -- it serves metadata, dossiers, notes, tags, the queue and
every clip that is already on disk without touching the screen. What it may
not do is decide, on its own, to film something.

WHY THE PERMIT LIVES HERE AND NOT IN THE REVIEWER. PANTHEON is the engine;
the reviewer is one of its consumers, and so is the director preview, and so
will be the beauty pass. A per-consumer "allow renders" switch means the next
consumer invents its own, and the user has to find all of them. There is one
gate, it lives with the backends it guards, and every launch path asks it.

WHAT DENIAL MEANS. Denial is never an error and never a failure state. A
denied job stays QUEUED and the reviewer says RENDER DEFERRED. Nothing is
dropped, nothing is marked FAILED, and the work runs when the permit opens --
overnight, or the moment the game closes.

THE THREE ANSWERS:

    GRANTED   render now
    DEFERRED  do not render now; ask again later, keep the job
    DENIED    do not render at all in this configuration

DEFERRED and DENIED both mean "do not launch". They are distinct because the
reviewer shows them differently: DEFERRED is a queue state the user can wait
out, DENIED is a decision the user made.

RESOLUTION ORDER, most specific first:

    1. PANTHEON_RENDER=off|on|auto   the user's explicit decision
    2. a game is running             DEFERRED, always, whatever else says
    3. not enough free disk          DEFERRED
    4. otherwise                     GRANTED

`on` still yields to a running game. There is no value that says "film over
the top of my match", because there is no situation in which that is what
someone wanted. It yields to a full disk too: on 2026-09-06 the headless
performance index took G: to 1.4 MB free, and a capture started in that
state cannot even record its own failure.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class Permit(Enum):
    GRANTED = "GRANTED"
    DEFERRED = "DEFERRED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class Decision:
    permit: Permit
    reason: str

    @property
    def may_render(self) -> bool:
        return self.permit is Permit.GRANTED

    @property
    def deferred(self) -> bool:
        """Ask again later and keep the job. Not a failure."""
        return self.permit is Permit.DEFERRED


# The user's decision. `auto` (the default) means "render when I am not
# playing" -- which is what an overnight machine wants without being told.
ENV_MODE = "PANTHEON_RENDER"
MODE_OFF = "off"
MODE_ON = "on"
MODE_AUTO = "auto"
_MODES = (MODE_OFF, MODE_ON, MODE_AUTO)

# Superseded. It only ever meant "ignore the running game", which is the one
# thing no mode is now allowed to mean. Kept readable so an old shell that
# still exports it gets an explanation instead of silence.
LEGACY_ENV = "CS_CAPTURE_ANYTIME"


def mode() -> str:
    raw = (os.getenv(ENV_MODE) or MODE_AUTO).strip().lower()
    return raw if raw in _MODES else MODE_AUTO


def legacy_override_present() -> bool:
    return os.getenv(LEGACY_ENV) == "1"


def check(*, purpose: str = "render",
          batch: bool = False) -> Decision:
    """May `purpose` open a renderer window right now?

    Callers pass their own name so the reason string reads as an answer to
    the question that was actually asked. `batch=True` asks for the headroom
    a whole run needs rather than one clip's worth.
    """
    if mode() == MODE_OFF:
        return Decision(Permit.DENIED,
                        f"{purpose} denied: {ENV_MODE}=off")

    # A running game outranks everything, including an explicit `on`. See
    # the module docstring: nobody ever wanted a capture window over a live
    # match, so no configuration is allowed to ask for one.
    from creative_suite.engine import capture_guard
    if capture_guard.game_is_running():
        return Decision(Permit.DEFERRED,
                        f"{purpose} deferred: a game is running")

    # NO ROOM IS NOT PERMISSION EITHER. A capture that cannot finish leaves
    # broken media and a system with no space to record that it broke. This
    # is DEFERRED, not DENIED: the user has not decided anything, the disk
    # has, and it becomes runnable again the moment space is freed.
    from creative_suite.engine import operator_health as oh
    free = oh.free_gb()
    floor = oh.BATCH_FLOOR_GB if batch else oh.SINGLE_FLOOR_GB
    if 0 <= free < floor:
        return Decision(Permit.DEFERRED,
                        f"{purpose} deferred: {free:.1f} GB free, "
                        f"{floor:.0f} GB needed")

    return Decision(Permit.GRANTED, f"{purpose} granted: nothing to disturb")


def require(purpose: str = "render") -> Decision:
    """`check`, but raises on anything other than GRANTED.

    For the launch paths that have no queue to fall back on. A path that CAN
    defer should call `check` and defer -- a raised exception there would
    turn a postponed clip into a failed one.
    """
    d = check(purpose=purpose)
    if not d.may_render:
        raise RenderNotPermitted(d)
    return d


class RenderNotPermitted(RuntimeError):
    def __init__(self, decision: Decision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


def status() -> dict[str, object]:
    """What the reviewer shows the user, in one call."""
    d = check(purpose="render")
    return {"permit": d.permit.value, "reason": d.reason,
            "mode": mode(),
            "legacy_override_ignored": legacy_override_present()}
