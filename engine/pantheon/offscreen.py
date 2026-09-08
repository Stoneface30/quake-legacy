"""PANTHEON_QUAKE_OFFSCREEN — run the Quake client where nobody can see it.

THE PROBLEM. WolfcamQL is a game client: starting one creates a top-level
window, Windows hands a new top-level window the foreground, and the user
loses the round they were playing. `SW_SHOWMINNOACTIVE` helped, but a
minimised window is still on the user's desktop and in the taskbar, and the
user has been explicit that minimised is not headless.

THE MECHANISM, AND WHY IT IS NOT A RENDERER REWRITE. We do not touch the
renderer. Windows lets a process be started on a DIFFERENT DESKTOP inside
the same window station (`CreateDesktopW`, then `STARTUPINFOW.lpDesktop`).
A window created there cannot appear on the interactive desktop, cannot
enter its taskbar, and cannot take its foreground -- not by policy but by
construction, because those are properties of a desktop object and the
process is on another one. The client still gets a real window, a real GL
context and the real GPU; it is simply drawing somewhere nobody is looking.

    PANTHEON owns HOW the renderer is invoked and fed.
    The renderer stays exactly the binary we already validate against.

WHAT THIS DOES NOT PROMISE. Whether a GL driver will create a hardware
context on a non-interactive desktop is a property of the driver, not of
this code, and it is not knowable from reading. `probe_isolation()` settles
the desktop half with a harmless GUI process; `probe_gl()` settles the
driver half, and only that one needs the engine. Until both pass on a
machine, `HIDDEN_OFFSCREEN_CONTEXT` stays UNKNOWN in the capability
registry, and the reviewer keeps whatever backend it has.

RENDER PERMIT STILL APPLIES. Offscreen removes the stolen foreground, not
the GPU and disk contention, so a protected game running still defers.
"""
from __future__ import annotations

import contextlib
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DESKTOP_NAME = "pantheon_render"


# A HIDDEN RENDER HAS NO BUSINESS OWNING THE POINTER.
#
# Measured 2026-09-06 on a real capture, after the operator reported the mouse
# being boxed into the invisible window: as shipped, GetClipCursor came back
# (107, 130, 2027, 1210) throughout the run -- the render window's rectangle,
# on a 3000x1440 desktop. `in_nograb 1` and `in_mouse 0` each released it on
# their own, and each still filmed. Both are set, because they say two
# different things and the render wants both: do not grab, and do not read
# the mouse at all.
OFFSCREEN_SETS = {"in_nograb": 1, "in_mouse": 0}


def ENGINE_ENV() -> dict[str, str]:
    """SDL's default video-driver probe fails on this machine ("No available
    video device") and the engine answers by reverting to SAFE VALUES --
    which silently drops a 1920x1080 request to mode 11, 856x480. Naming the
    driver makes the first attempt succeed. An offscreen capture that films
    a quarter of the requested frame is not a capture."""
    return dict(os.environ, SDL_VIDEODRIVER="windib")

# CreateProcess flags
CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200
NORMAL_PRIORITY_CLASS = 0x00000020
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0
GENERIC_ALL = 0x10000000
DESKTOP_CREATEWINDOW = 0x0002


class OffscreenUnavailable(RuntimeError):
    """This platform cannot host a hidden desktop. Never a reason to fall
    back to a visible window: the caller decides, loudly."""


# ── Win32 plumbing ─────────────────────────────────────────────────────────

if sys.platform == "win32":
    class _STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
            ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE)]

    class _PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                    ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def _u32():
    return ctypes.WinDLL("user32", use_last_error=True)


def _k32():
    return ctypes.WinDLL("kernel32", use_last_error=True)


@dataclass
class HiddenDesktop:
    """A desktop object nobody is viewing. Processes started on it cannot
    reach the interactive desktop."""
    name: str = DESKTOP_NAME
    handle: int | None = None

    def __enter__(self) -> "HiddenDesktop":
        if sys.platform != "win32":
            raise OffscreenUnavailable("hidden desktops are a Windows mechanism")
        u = _u32()
        u.CreateDesktopW.restype = wintypes.HANDLE
        u.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR,
                                     ctypes.c_void_p, wintypes.DWORD,
                                     wintypes.DWORD, ctypes.c_void_p]
        h = u.CreateDesktopW(self.name, None, None, 0, GENERIC_ALL, None)
        if not h:
            raise OffscreenUnavailable(
                f"CreateDesktopW({self.name!r}) failed: {ctypes.get_last_error()}")
        self.handle = h
        return self

    def __exit__(self, *exc) -> None:
        if self.handle:
            u = _u32()
            u.CloseDesktop.argtypes = [wintypes.HANDLE]
            u.CloseDesktop(self.handle)
            self.handle = None


@dataclass
class OffscreenProcess:
    pid: int
    handle: int
    desktop: str

    def wait(self, timeout: float) -> int | None:
        """Exit code, or None on timeout."""
        k = _k32()
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        rc = k.WaitForSingleObject(self.handle, int(timeout * 1000))
        if rc != 0:
            return None
        code = wintypes.DWORD()
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetExitCodeProcess(self.handle, ctypes.byref(code))
        return int(code.value)

    def terminate(self) -> None:
        """CS-4: a GUI process left running holds file locks, and one on a
        hidden desktop is worse because nobody can see it to close it."""
        k = _k32()
        k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.TerminateProcess(self.handle, 1)
        k.WaitForSingleObject(self.handle, 5000)

    def close(self) -> None:
        k = _k32()
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle(self.handle)


INTERACTIVE: str | None = None
"""The operator's own desktop -- where WOLFCAM_REFERENCE has always run.
Passing it to run_engine gives the A leg of a backend A/B: the same staging,
the same cfg, the same command line, the same watcher, differing from
PANTHEON_QUAKE_OFFSCREEN in the ONE variable under test."""


@dataclass
class _VisibleProcess:
    """subprocess.Popen wearing OffscreenProcess's interface, so the two legs
    of a comparison are not two different pieces of code."""
    proc: subprocess.Popen

    @property
    def pid(self) -> int:
        return self.proc.pid

    def wait(self, timeout: float) -> int | None:
        try:
            return self.proc.wait(timeout)
        except subprocess.TimeoutExpired:
            return None

    def terminate(self) -> None:
        self.proc.terminate()                       # CS-4: never orphan a GUI proc
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()

    def close(self) -> None:
        return None


def spawn_visible(argv: Sequence[str], *, cwd: Path | str | None = None,
                  env: dict[str, str] | None = None) -> _VisibleProcess:
    """Start the client on the interactive desktop, minimised and not
    activated. This is the OLD behaviour, kept as the reference leg -- it is
    what the review path did before the hidden desktop existed."""
    from creative_suite.engine.capture_guard import quiet_startup_info
    return _VisibleProcess(subprocess.Popen(
        list(argv), cwd=str(cwd) if cwd else None, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        startupinfo=quiet_startup_info()))


def spawn_on_desktop(argv: Sequence[str], *, cwd: Path | str | None = None,
                     env: dict[str, str] | None = None,
                     desktop: str = DESKTOP_NAME) -> OffscreenProcess:
    """Start a process on `desktop`. The caller must already hold that
    desktop open (see HiddenDesktop) for the lifetime of the process."""
    if sys.platform != "win32":
        raise OffscreenUnavailable("hidden desktops are a Windows mechanism")
    k = _k32()
    si = _STARTUPINFOW()
    si.cb = ctypes.sizeof(_STARTUPINFOW)
    si.lpDesktop = desktop
    # Belt to the desktop's brace: ask for hidden as well. On the hidden
    # desktop this changes nothing; if a future caller ever passes the
    # interactive desktop by mistake, it is one more thing in the way.
    si.dwFlags = STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    pi = _PROCESS_INFORMATION()

    block = None
    if env is not None:
        items = "".join(f"{k_}={v}\0" for k_, v in env.items()) + "\0"
        block = ctypes.create_unicode_buffer(items)

    k.CreateProcessW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
        wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(_STARTUPINFOW), ctypes.POINTER(_PROCESS_INFORMATION)]
    cmdline = subprocess.list2cmdline(list(argv))
    ok = k.CreateProcessW(
        None, ctypes.create_unicode_buffer(cmdline), None, None, False,
        NORMAL_PRIORITY_CLASS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        | (0x00000400 if block is not None else 0),          # CREATE_UNICODE_ENVIRONMENT
        ctypes.cast(block, ctypes.c_void_p) if block is not None else None,
        str(cwd) if cwd else None, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        raise OffscreenUnavailable(
            f"CreateProcessW failed ({ctypes.get_last_error()}): {cmdline[:120]}")
    k.CloseHandle(pi.hThread)
    return OffscreenProcess(int(pi.dwProcessId), int(pi.hProcess), desktop)


# ── what the operator sees, measured rather than asserted ──────────────────

@dataclass
class ForegroundState:
    hwnd: int
    pid: int
    title: str

    def as_dict(self) -> dict:
        return {"hwnd": self.hwnd, "pid": self.pid, "title": self.title}


def foreground() -> ForegroundState:
    """Whatever owns the user's screen right now."""
    if sys.platform != "win32":
        return ForegroundState(0, 0, "")
    u = _u32()
    u.GetForegroundWindow.restype = wintypes.HWND
    hwnd = u.GetForegroundWindow()
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    buf = ctypes.create_unicode_buffer(256)
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowTextW(hwnd, buf, 256)
    return ForegroundState(int(hwnd or 0), int(pid.value), buf.value)


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79


def virtual_screen() -> tuple[int, int, int, int]:
    """The whole desktop the operator can move a mouse across."""
    if sys.platform != "win32":
        return (0, 0, 0, 0)
    u = _u32()
    x, y = u.GetSystemMetrics(SM_XVIRTUALSCREEN), u.GetSystemMetrics(SM_YVIRTUALSCREEN)
    return (x, y, x + u.GetSystemMetrics(SM_CXVIRTUALSCREEN),
            y + u.GetSystemMetrics(SM_CYVIRTUALSCREEN))


def cursor_clip() -> tuple[int, int, int, int]:
    """Where the operator's mouse is allowed to go, right now.

    A Quake client grabs the mouse. The hidden desktop keeps its WINDOW off
    the screen, and the operator reported the pointer being confined anyway
    while a capture ran -- so this is measured on every run rather than
    assumed away, like the window and the foreground before it.
    """
    if sys.platform != "win32":
        return (0, 0, 0, 0)
    r = _RECT()
    _u32().GetClipCursor(ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def cursor_is_confined() -> bool:
    clip, screen = cursor_clip(), virtual_screen()
    if clip == (0, 0, 0, 0):
        return False
    return (clip[2] - clip[0]) < (screen[2] - screen[0]) or            (clip[3] - clip[1]) < (screen[3] - screen[1])


def release_cursor() -> bool:
    """Hand the pointer back. ClipCursor(NULL) frees it for the whole
    session; harmless when nothing had confined it."""
    if sys.platform != "win32":
        return False
    return bool(_u32().ClipCursor(None))


def visible_windows_of(pid: int) -> list[str]:
    """Titles of the process's windows ON THE INTERACTIVE DESKTOP. A process
    on another desktop contributes nothing here, which is the whole point:
    this enumerates the desktop we are running on."""
    if sys.platform != "win32":
        return []
    u = _u32()
    found: list[str] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _lparam):
        owner = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and u.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            u.GetWindowTextW(hwnd, buf, 256)
            found.append(buf.value or "<untitled>")
        return True

    u.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    u.EnumWindows(WNDENUMPROC(cb), 0)
    return found


@dataclass
class IsolationResult:
    ran: bool
    visible_windows: list[str] = field(default_factory=list)
    foreground_before: dict = field(default_factory=dict)
    foreground_after: dict = field(default_factory=dict)
    detail: str = ""
    probe_pid: int = 0

    @property
    def stole_focus(self) -> bool:
        """Did the PROBE take the screen? Not: did the screen change.

        The earlier reading demanded the foreground window be identical
        before and after, and on 2026-09-07 it reported a failure because the
        operator changed windows during the second and a half it ran. That is
        the same false alarm OffscreenRun.stole_focus was built to avoid: an
        operator switching app is not the render's doing.
        """
        pid = self.foreground_after.get("pid")
        return bool(self.probe_pid) and pid == self.probe_pid

    @property
    def foreground_moved(self) -> bool:
        """Reported for information; not a failure on its own."""
        return self.foreground_before.get("hwnd") != self.foreground_after.get("hwnd")

    @property
    def isolated(self) -> bool:
        return self.ran and not self.visible_windows and not self.stole_focus

    def as_dict(self) -> dict:
        return {"ran": self.ran, "isolated": self.isolated,
                "visible_windows": self.visible_windows,
                "foreground_before": self.foreground_before,
                "foreground_after": self.foreground_after, "detail": self.detail}


ISOLATION_PROBE_ARGV = ["notepad.exe"]


def probe_isolation(argv: Sequence[str] | None = None, *, dwell: float = 2.0
                    ) -> IsolationResult:
    """Does the hidden desktop actually hide a GUI process?

    Deliberately NOT the game: a harmless GUI process settles the desktop
    mechanism, and if the mechanism does not work we learn that without ever
    putting a Quake window on the user's screen.
    """
    before = foreground()
    argv = list(argv or ISOLATION_PROBE_ARGV)
    probe_pid = 0
    try:
        with HiddenDesktop() as _d:
            proc = spawn_on_desktop(argv)
            probe_pid = proc.pid
            try:
                time.sleep(dwell)                     # let it create its window
                windows = visible_windows_of(proc.pid)
                after = foreground()
            finally:
                proc.terminate()
                proc.close()
    except OffscreenUnavailable as exc:
        return IsolationResult(False, detail=str(exc),
                               foreground_before=before.as_dict(),
                               foreground_after=before.as_dict())
    return IsolationResult(True, windows, before.as_dict(), after.as_dict(),
                           f"probe: {' '.join(argv)}", probe_pid=probe_pid)


# ── running the engine there ───────────────────────────────────────────────

@dataclass
class OffscreenRun:
    ok: bool
    returncode: int | None
    seconds: float
    visible_windows: list[str]
    foreground_before: dict
    foreground_after: dict
    log_tail: str = ""
    detail: str = ""
    foreground_during: list = field(default_factory=list)
    cursor_clips: list = field(default_factory=list)

    render_pid: int = 0

    @property
    def stole_focus(self) -> bool:
        """Did the RENDER take the screen? A foreground change alone is not
        that: the operator may have switched app mid-capture, and blaming the
        renderer for it would make the regression test cry wolf forever. The
        question is whether the foreground BELONGS to the render process."""
        return any(f.get("pid") == self.render_pid and self.render_pid
                   for f in (self.foreground_during or []) + [self.foreground_after])

    @property
    def confined_cursor(self) -> bool:
        """Did the engine take the pointer at any point while this ran?

        TRUE DOES NOT MEAN THE OPERATOR IS STILL STUCK. The watcher clears it
        within a second of seeing it and again after the process dies; this
        records that the engine tried, which is worth knowing because the
        launch settings that were supposed to stop it did not.
        """
        return bool(self.cursor_clips)

    pointer_confined_before: bool = False

    @property
    def pointer_left_confined(self) -> bool:
        """The one that would actually hurt: did OUR run leave the operator's
        pointer boxed in? A pointer that was already grabbed when we started
        is not ours and is not counted."""
        return cursor_is_confined() and not self.pointer_confined_before

    @property
    def foreground_moved(self) -> bool:
        """Reported for information; not a failure on its own."""
        return self.foreground_before.get("hwnd") != self.foreground_after.get("hwnd")

    def as_dict(self) -> dict:
        return {"ok": self.ok, "returncode": self.returncode,
                "seconds": round(self.seconds, 1),
                "visible_windows": self.visible_windows,
                "stole_focus": self.stole_focus,
                "confined_cursor": self.confined_cursor,
                "pointer_confined_before": self.pointer_confined_before,
                "pointer_left_confined": self.pointer_left_confined,
                "cursor_clips": self.cursor_clips[:4],
                "foreground_moved": self.foreground_moved,
                "foreground_before": self.foreground_before,
                "foreground_after": self.foreground_after,
                "detail": self.detail, "log_tail": self.log_tail[-1500:]}


def run_engine(argv: Sequence[str], *, cwd: Path, timeout: float,
               purpose: str = "offscreen render", log: Path | None = None,
               poll: float = 1.0, env: dict[str, str] | None = None,
               desktop: str | None = DESKTOP_NAME) -> OffscreenRun:
    """Run the Quake client and report what the operator's screen did while
    it ran.

    `desktop` names the desktop object to host it on; INTERACTIVE (None) runs
    it on the operator's own, which is what the reference backend has always
    done and is kept so an A/B can change ONE thing.

    Asks the render permit first: offscreen removes the stolen foreground,
    not the GPU and disk contention a running game cares about.
    """
    from engine.pantheon import render_permit
    render_permit.require(purpose, output_dir=cwd)

    before = foreground()
    # The pointer's state BEFORE we start anything. Everything later is judged
    # against this: a clip that was already here is not ours.
    clip_before = cursor_clip()
    was_confined_before = cursor_is_confined()
    seen: list[str] = []
    during: list[dict] = []
    clips: list[tuple] = []
    pid = 0
    t0 = time.time()
    rc: int | None = None
    detail = ""
    try:
        with (HiddenDesktop(desktop) if desktop else contextlib.nullcontext()):
            proc = (spawn_on_desktop(argv, cwd=cwd, env=env, desktop=desktop)
                    if desktop else spawn_visible(argv, cwd=cwd, env=env))
            pid = proc.pid
            try:
                deadline = t0 + timeout
                while time.time() < deadline:
                    # WATCH THE USER'S DESKTOP THROUGHOUT, not only at the end:
                    # a window that appears and closes again still stole a
                    # round, and a check that only looks afterwards misses it.
                    seen.extend(w for w in visible_windows_of(proc.pid) if w not in seen)
                    during.append(foreground().as_dict())
                    # ONLY A CLIP WE CAUSED IS OURS TO CLEAR.
                    #
                    # An earlier version of this loop released the pointer
                    # every time it saw it confined. That was wrong and it was
                    # dangerous: on 2026-09-07 the confinement belonged to
                    # OVERWATCH, which the operator was playing, and releasing
                    # it would have pulled their mouse out of a live match
                    # once a second. A clip that was already there before we
                    # started is somebody else's, and we do not touch it.
                    now = cursor_clip()
                    if cursor_is_confined() and now != clip_before:
                        clips.append(now)
                    rc = proc.wait(poll)
                    if rc is not None:
                        break
                if rc is None:
                    detail = f"timeout after {timeout:.0f}s"
                    proc.terminate()
            finally:
                proc.close()
    except OffscreenUnavailable as exc:
        return OffscreenRun(False, None, time.time() - t0, [], before.as_dict(),
                            before.as_dict(), detail=str(exc))
    after = foreground()
    tail = ""
    if log and log.exists():
        tail = log.read_text(encoding="utf-8", errors="replace")
    # Give back only what we took. If the pointer was already confined when
    # this started, it belongs to whatever the operator is running and stays
    # exactly where it was.
    if clips and not was_confined_before:
        for _ in range(20):
            if not cursor_is_confined():
                break
            release_cursor()
            time.sleep(0.1)
    return OffscreenRun(rc == 0, rc, time.time() - t0, seen, before.as_dict(),
                        after.as_dict(), tail, detail, render_pid=pid,
                        foreground_during=during, cursor_clips=clips,
                        pointer_confined_before=was_confined_before)


def probe_gl(staging: Path, *, timeout: float = 120.0) -> dict:
    """Can the engine create a hardware GL context on a hidden desktop?

    The desktop half is settled by probe_isolation with a harmless process;
    this is the half only the engine can answer, and it is why
    HIDDEN_OFFSCREEN_CONTEXT stays UNKNOWN until it is run on a machine.
    Reads the renderer strings the client logs at startup.
    """
    exe = Path(staging) / "wolfcamql.exe"
    if not exe.exists():
        return {"ran": False, "detail": f"no engine at {exe}"}
    home = Path(staging) / "_offscreen_probe"
    home.mkdir(parents=True, exist_ok=True)
    console = home / "wolfcam-ql" / "qconsole.log"
    console.parent.mkdir(parents=True, exist_ok=True)
    if console.exists():
        console.unlink()
    argv = [str(exe), "+set", "fs_homepath", str(home), "+set", "fs_basepath",
            str(staging), "+set", "logfile", "2", "+set", "r_fullscreen", "0",
            "+set", "r_mode", "-1", "+set", "r_customwidth", "1280",
            "+set", "r_customheight", "720", "+set", "s_initsound", "0",
            "+set", "com_maxfps", "60",
            *[a for k, v in OFFSCREEN_SETS.items()
              for a in ("+set", str(k), str(v))],
            "+wait", "200", "+quit"]
    run = run_engine(argv, cwd=Path(staging), timeout=timeout, env=ENGINE_ENV(),
                     purpose="runtime capability proof: offscreen GL", log=console)
    text = run.log_tail
    renderer = next((ln.strip() for ln in text.splitlines()
                     if "GL_RENDERER" in ln or "GL_VERSION" in ln), "")
    return {"ran": True, "gl_initialised": bool(renderer),
            "renderer_line": renderer, **run.as_dict()}


# A CUE IS FILM WORDS; A PROFILE IS BACKEND VALUES. The translation lives
# here, in the backend layer, like every other cvar in this file. A
# ChoreographyPlan says XRAY_ON; what that costs in engine settings is not the
# plan's business, and the plan is forbidden from knowing.
CUE_PROFILE = {
    "XRAY_ON": "REVIEW_XRAY",
    "XRAY_OFF": "REVIEW",
    "NORMAL_ACTION": "REVIEW",
}


# THE ASSET SET IS NOT A MANUAL STEP.
#
# assets.py existed for a session before it was wired here, and in that
# session every render still filmed against whatever pk3s happened to be
# sitting in the gamedir -- which is exactly the "assets exist and are never
# in the picture" failure it was built to end. Every capture now asks for a
# set and gets it, cheaply (a handful of hard links, a no-op if already
# linked), instead of depending on someone having run the CLI first.
DEFAULT_ASSET_SET = "UHD"


def capture(safe_demo: str, windows: list[dict], *, staging: Path,
            profile_cvars: dict | None = None, timeout: float | None = None,
            purpose: str = "offscreen capture", profile: str | None = None,
            cues: list[dict] | None = None,
            asset_set: str | None = DEFAULT_ASSET_SET,
            lock_wait_s: float = 0.0,
            desktop: str | None = DESKTOP_NAME) -> dict:
    """One offscreen capture, through the project's own staging and cfg.

    Deliberately reuses `wolfcam_capture`'s cfg writer and command builder
    rather than reimplementing them, so every lesson already paid for --
    latched cvars on the command line, the 32 `+` group ceiling, the SDL
    video driver, the seek settle -- reaches this path automatically. The
    only difference from WOLFCAM_REFERENCE is WHERE the process lives.

    `asset_set=None` skips the install (a caller doing its own asset
    management); anything else is a name from `engine.pantheon.assets.SETS`,
    installed before the launch so the result always says what the picture
    was actually made of.

    Raises `capture_lock.CaptureBusy` when another renderer holds the staging
    install. `lock_wait_s` gives a batch a budget to wait its turn; the
    default of 0 fails fast, which is what an interactive caller wants.
    """
    from creative_suite.engine import wolfcam_capture as wc
    from engine.pantheon import capture_lock

    # ONE ENGINE AT A TIME. The staging install has one capture.cfg and one
    # videos directory; a second renderer does not queue behind us, it
    # overwrites us. The review proxy has always taken this lock and this
    # path never did, which is how a headless capture came to launch with a
    # review proxy's cfg on disk and exit rc=1 in two seconds.
    with capture_lock.held(purpose=purpose, wait_s=lock_wait_s):
        return _capture_locked(
            safe_demo, windows, staging=staging, profile_cvars=profile_cvars,
            timeout=timeout, purpose=purpose, profile=profile, cues=cues,
            asset_set=asset_set, desktop=desktop)


def _capture_locked(safe_demo: str, windows: list[dict], *, staging: Path,
                    profile_cvars: dict | None, timeout: float | None,
                    purpose: str, profile: str | None, cues: list[dict] | None,
                    asset_set: str | None, desktop: str | None) -> dict:
    """The body of `capture`, with the staging install already held."""
    from creative_suite.engine import wolfcam_capture as wc
    asset_state = None
    if asset_set is not None:
        from engine.pantheon import assets as A
        asset_state = A.install(asset_set, staging)
    videos = staging / "wolfcam-ql" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for w in windows:
        for old in videos.glob(f"{w['clip_name']}*.avi"):
            old.unlink()

    # WHICH MASTER LOOK. `None` is not "no profile" -- it is the BATCH master,
    # the one that once burned "You fragged <name>" into a public clip. A
    # caller filming for review must name the review master, so the choice is
    # a parameter rather than a default nobody reads.
    cfg = wc.write_capture_cfg(windows, staging, profile)
    timed: list[str] = []
    if cues:
        # Only what CHANGES is scheduled. Re-applying a whole profile at each
        # cue would re-send the enemy model mid-shot, and any cvar the engine
        # never registered would be re-sent as a silent no-op every time.
        from engine.pantheon import visual_profile as VP
        current = dict(profile_cvars or {})
        for cue in sorted(cues, key=lambda c: int(c["at_ms"])):
            name = CUE_PROFILE.get(cue["semantic"])
            if name is None:
                continue
            wanted = VP.profile(name).resolve()
            for k, v in wanted.items():
                if current.get(k) != v:
                    timed.append(f"at {int(cue['at_ms'])} set {k} {v}")
            current.update(wanted)
    if profile_cvars or timed:
        head, *rest = cfg.splitlines()
        look = [f"set {k} {v}" for k, v in (profile_cvars or {}).items()]
        seek, *later = rest
        wc.write_engine_file(staging / "wolfcam-ql" / "capture.cfg",
                             "".join(f"{ln}\n" for ln in
                                     [head, *look, seek, *timed, *later]))

    if timeout is None:
        span = sum((int(w["end_ms"]) - int(w["start_ms"])) / 1000.0 for w in windows)
        seek = max(int(w["start_ms"]) for w in windows) / 1000.0
        # Budget for the renderer that will actually run. This process forces
        # Mesa softpipe, which writes about half a frame per second at 1080p;
        # the hardware constant killed every capture part-way through and left
        # a well-formed AVI holding a quarter of the action.
        slowdown = (wc.SOFTWARE_CAPTURE_SLOWDOWN if wc.software_gl()
                    else wc.CAPTURE_SLOWDOWN)
        timeout = wc.LAUNCH_OVERHEAD_S + span * slowdown + seek / 12.0

    # The profile also decides the LATCHED launch cvars (the review exposure
    # among them), which only apply from the command line -- so it has to be
    # named here as well as in the cfg.
    argv = wc.wolfcam_cmd(safe_demo, staging, profile=profile,
                          extra_sets=dict(OFFSCREEN_SETS))
    console = staging / "wolfcam-ql" / "qconsole.log"
    run = run_engine(argv, cwd=staging, timeout=timeout, purpose=purpose,
                     log=console, env=ENGINE_ENV(), desktop=desktop)
    made = {w["clip_name"]: sorted(videos.glob(f"{w['clip_name']}*.avi"))
            for w in windows}
    avis = {k: str(v[0]) for k, v in made.items() if v}
    # The interactive leg is EXPECTED to put a window on the screen -- that is
    # the behaviour being replaced. Only the hidden leg is judged on it.
    quiet = desktop is None or (not run.visible_windows and not run.stole_focus
                                and not run.pointer_left_confined)
    # COUNT WHAT WAS WRITTEN. A capture cut off at its deadline produces a
    # file that opens and plays; only the frame count says it is short.
    want = wc.frames_expected(windows)
    got = sum(wc.count_frames(Path(a)) for a in avis.values())
    truncated = bool(avis) and want > 0 and got < want * wc.COMPLETE_ENOUGH
    return {"ok": bool(avis) and quiet and not truncated,
            "frames_expected": want, "frames_written": got,
            "truncated": truncated,
            "desktop": desktop or "interactive",
            "asset_set": asset_state["set"] if asset_state else None,
            "avis": avis, "missing": [k for k, v in made.items() if not v],
            **{k: v for k, v in run.as_dict().items() if k != "log_tail"}}
