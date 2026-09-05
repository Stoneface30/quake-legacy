"""RenderPermit — the one gate every game-process launch passes through.

A USER REQUIREMENT (2026-09-05): starting or resuming a Claude session must
never launch WolfcamQL. It had: a review origin coming up reclaimed queued
proxy jobs, a worker picked one, and a game window took the desktop away
from the game the user was playing. The window-hiding flags that followed
are defence in depth; a process that must not run should not be launched.

    DEFAULT: DENY.

Nothing launches a renderer because a server started, a worker reclaimed a
job, a test ran, a proof harness was imported, or a queue had work. The only
way to allow a launch is the operator setting

    PANTHEON_RENDER_ALLOWED=1

in the environment of the process that would launch. There is one setting;
do not add another.

    EVEN THEN: DEFER while a protected game is running.

If Quake Live (or any executable listed in PANTHEON_PROTECTED_GAMES,
';'-separated) has a process, the launch is deferred, not failed. A queue
keeps the job QUEUED/DEFERRED and the UI says RENDER DEFERRED; an existing
READY proxy keeps playing. `PANTHEON_RENDER_FORCE=1` is the explicit override
for the rare case the operator really wants both.

The process scan uses the Win32 toolhelp snapshot through ctypes: it never
spawns `tasklist` or a shell, because a console window popping up is itself
the fault this module exists to prevent.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum

ENV_ALLOW = "PANTHEON_RENDER_ALLOWED"
ENV_FORCE = "PANTHEON_RENDER_FORCE"
ENV_PROTECTED = "PANTHEON_PROTECTED_GAMES"
DEFAULT_PROTECTED = ("quakelive.exe", "quakelive_steam.exe", "quakelive_x64.exe",
                     "quake3.exe", "ioquake3.exe", "cnq3.exe")
TRUTHY = ("1", "true", "yes", "on")


class Decision(Enum):
    ALLOWED = "ALLOWED"
    DENIED_DEFAULT = "DENIED_DEFAULT"          # no operator permission
    DEFERRED_GAME_RUNNING = "DEFERRED_GAME_RUNNING"


@dataclass(frozen=True)
class Permit:
    decision: Decision
    purpose: str
    reason: str
    games: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.decision is Decision.ALLOWED

    @property
    def deferred(self) -> bool:
        return self.decision is Decision.DEFERRED_GAME_RUNNING

    def as_dict(self) -> dict:
        return {"decision": self.decision.value, "purpose": self.purpose,
                "reason": self.reason, "games": list(self.games)}


class RenderDenied(RuntimeError):
    """Raised by require(). Carries the Permit so a queue can DEFER."""

    def __init__(self, permit: Permit) -> None:
        super().__init__(f"render {permit.decision.value} ({permit.purpose}): {permit.reason}")
        self.permit = permit


# ── process scan, without spawning anything ────────────────────────────────

def protected_games() -> tuple[str, ...]:
    extra = tuple(x.strip().lower() for x in os.getenv(ENV_PROTECTED, "").split(";") if x.strip())
    return tuple(dict.fromkeys(DEFAULT_PROTECTED + extra))


def running_processes() -> list[str]:
    """Lower-cased image names of every process, via CreateToolhelp32Snapshot.
    Empty on non-Windows or on any failure -- a scan that cannot run must not
    block, but it must not pretend either (see running_games)."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        from ctypes import wintypes
        TH32CS_SNAPPROCESS = 0x00000002

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD),
                        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD),
                        ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                        ("szExeFile", ctypes.c_wchar * 260)]

        k32 = ctypes.windll.kernel32
        snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == wintypes.HANDLE(-1).value:
            return []
        names: list[str] = []
        try:
            e = PROCESSENTRY32W()
            e.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if k32.Process32FirstW(snap, ctypes.byref(e)):
                while True:
                    names.append(e.szExeFile.lower())
                    if not k32.Process32NextW(snap, ctypes.byref(e)):
                        break
        finally:
            k32.CloseHandle(snap)
        return names
    except Exception:
        return []


def running_games() -> tuple[str, ...]:
    prot = set(protected_games())
    return tuple(sorted({n for n in running_processes() if n in prot}))


# ── the decision ───────────────────────────────────────────────────────────

def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUTHY


def check(purpose: str, *, force: bool | None = None) -> Permit:
    """Decide, without side effects. `purpose` is what the caller wants the
    game process for (a capture, a probe, a director session); it goes in the
    log and in the reason a job shows as deferred."""
    if not _truthy(ENV_ALLOW):
        return Permit(Decision.DENIED_DEFAULT, purpose,
                      f"{ENV_ALLOW} is not set; rendering is denied by default")
    forced = _truthy(ENV_FORCE) if force is None else force
    games = () if forced else running_games()
    if games:
        return Permit(Decision.DEFERRED_GAME_RUNNING, purpose,
                      f"protected game running: {', '.join(games)}", games)
    return Permit(Decision.ALLOWED, purpose,
                  "operator permission set" + (", forced past a running game" if forced else ""))


def require(purpose: str, *, force: bool | None = None) -> Permit:
    """The call every launch site makes immediately before spawning."""
    p = check(purpose, force=force)
    if not p.ok:
        raise RenderDenied(p)
    return p


def allowed(purpose: str = "query") -> bool:
    return check(purpose).ok
