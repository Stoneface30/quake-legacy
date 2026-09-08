"""WolfcamQL capture engine for demo-derived V2 clips.

Design (capture-phase charter §11-§14):
- One staging install under output/demo_v2/_wolfcam_staging/ assembled from
  the archival binaries + canonical wolfcam-ql game dir. QL assets come from
  the read-only Steam install via +set fs_quakelivedir (ENG-1/ENG-4: never
  written).
- Demos are staged under short safe names (dNNNN.dm_73): MAX_QPATH is 64 and
  archive names carry spaces/semicolons (CS-5 injection surface).
- All seeking uses RAW serverTime (seekservertime / at <ms>) — never the CA
  display clock.
- Multiple windows in one demo are captured in ONE wolfcam launch via chained
  at-commands (pattern from docs/reference/wolfcam-commands.md).
- Single controlled writer; every subprocess follows the CS-4
  terminate -> wait(3) -> kill cascade. No orphans, no held demo locks.
- CS_CAPTURE_MOCK=1 replaces wolfcam with an ffmpeg testsrc render so the
  whole pipeline (including QA) is testable without the GUI engine.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
BIN_DIR = REPO_ROOT / "engine" / "engines" / "ghidra" / "binaries"
CANONICAL_GAMEDIR = (REPO_ROOT / "engine" / "engines" / "_canonical"
                     / "package-files" / "wolfcam-ql")
STAGING = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
# Masters live on the big drive; provenance rows store absolute paths.
CLIPS_DIR = Path(os.getenv("QL_MASTERS_DIR",
                           r"D:\QUAKE_LEGACY_MASTERS\generated_clips"))
QL_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live")
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = FFMPEG.parent / "ffprobe.exe"

WOLFCAM_VERSION = "wolfcamql-11.3"
FPS = 60
WIDTH, HEIGHT = 1920, 1080
SEEK_SETTLE_MS = 600        # let renderer settle between seek and record
INTER_WINDOW_MS = 300       # gap between stopvideo and next seek
LAUNCH_OVERHEAD_S = 150     # engine start + demo load + seeks
CAPTURE_SLOWDOWN = 10       # worst-case capture seconds per window second

# THE SAME NUMBER, FOR A RENDERER A HUNDRED TIMES SLOWER.
#
# This process forces Mesa softpipe (see capture_demo) because the NVIDIA
# driver kills wolfcam during R_Init on this machine. Softpipe is a CPU
# rasteriser: measured on 2026-09-08 it wrote about HALF A FRAME PER SECOND of
# wall clock at 1920x1080, i.e. ~120 wall-seconds per second of 60 fps footage.
#
# `CAPTURE_SLOWDOWN = 10` was calibrated against hardware GL, so every capture
# was being terminated at its own deadline part-way through. Measured against
# the probe in docs/visual-record/2026-09-08/capture_length/: budgets of
# 223 / 248 / 298 s predicted the observed wall times of 223.4 / 248.7 /
# 298.1 s exactly. The clips were not short because the engine stopped early;
# they were short because WE killed it.
SOFTWARE_CAPTURE_SLOWDOWN = 150     # measured ~120, plus margin
CAPTURE_FPS = 60                    # what the master cfg records at


class CfgInjectionError(ValueError):
    pass


def write_engine_file(path: Path, text: str, encoding: str = "ascii") -> None:
    """Write a file the Quake engine will parse, with LF line endings.

    ALWAYS use this instead of ``Path.write_text`` for anything the engine
    reads. On Windows ``write_text`` applies universal-newline translation
    and silently turns every ``\\n`` into ``\\r\\n``.

    How much that matters depends on the reader, and both cases are now
    established empirically rather than assumed:

    * ``.cam10`` camera files — FATAL. ``CG_LoadCamera_f``
      (cg_consolecmds.c:2401) is a line-positional ``sscanf`` reader; a
      trailing ``\\r`` corrupts the parse and the engine loads 0 points,
      reporting ``^1ERROR corrupt camera file``. This cost real
      investigation time on 2026-09-01 and was initially misdiagnosed as
      an engine bug in ``playcamera``.
    * ``.cfg`` scripts — HARMLESS in practice. The Cbuf tokenizer treats
      ``\\r`` as whitespace. Proof: the frozen master profile cfg
      (``wolfcam_tr4sh_master_capture.cfg``) contained 96 CRLF pairs while
      driving every successful capture of this session.

    So this helper is hardening, not a bug fix, for cfg writers — but the
    cost is zero and the failure mode, when a line-positional format does
    appear, is silent and expensive. One code path, one guarantee.
    """
    path.write_text(text, encoding=encoding, newline="")


def _validate_cfg_token(token: str) -> str:
    """CS-5: any string entering a cfg must not smuggle commands."""
    if any(c in token for c in (";", "\n", "\r", '"')):
        raise CfgInjectionError(f"unsafe cfg token: {token!r}")
    return token


def ensure_install(staging: Path = STAGING) -> Path:
    """Assemble a runnable wolfcam install once; idempotent."""
    exe = staging / "wolfcamql.exe"
    gamedir = staging / "wolfcam-ql"
    if exe.exists() and (gamedir / "cgamex86.dll").exists():
        # The binaries are in place, but the PROFILE CFGS are not part of
        # "installed" -- they change whenever a capture profile changes, and
        # this early return used to skip writing them. A new profile's cfg
        # was therefore never created, capture.cfg exec'd a file that did not
        # exist, and the capture silently ran with none of its cvars. The
        # only reason it looked partly fixed was that the command-line launch
        # sets still applied. Rewriting them is cheap and idempotent.
        from creative_suite.engine import master_profile
        master_profile.write(gamedir)
        return staging
    staging.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BIN_DIR / "wolfcamql-11.3.exe", exe)
    shutil.copy2(BIN_DIR / "wolfcamql-11.3_SDL.dll", staging / "SDL.dll")
    shutil.copy2(BIN_DIR / "wolfcamql-11.3_backtrace.dll",
                 staging / "backtrace.dll")
    gamedir.mkdir(exist_ok=True)
    for src in CANONICAL_GAMEDIR.iterdir():
        dst = gamedir / src.name
        if src.is_dir():
            if not dst.exists():
                shutil.copytree(src, dst)
        elif not dst.exists():
            shutil.copy2(src, dst)
    for dll in ("cgamex86.dll", "uix86.dll", "qagamex86.dll"):
        shutil.copy2(BIN_DIR / f"wolfcamql-11.3_{dll}", gamedir / dll)
    from creative_suite.engine import master_profile
    master_profile.write(gamedir)
    (gamedir / "demos").mkdir(exist_ok=True)
    (gamedir / "videos").mkdir(exist_ok=True)
    # QL assets: fs_quakelivedir is ignored by this build (verified in
    # qconsole.log — no Steam entries in the search path), so the paks are
    # copied into staging/baseq3, which IS searched. Steam originals are
    # never touched (ENG-4).
    baseq3 = staging / "baseq3"
    baseq3.mkdir(exist_ok=True)
    for pak in ("pak00.pk3", "bin.pk3"):
        src, dst = QL_DIR / "baseq3" / pak, baseq3 / pak
        if src.exists() and (not dst.exists()
                             or dst.stat().st_size != src.stat().st_size):
            shutil.copy2(src, dst)
    return staging


def stage_demo(demo_path: Path, idx: int = 0, staging: Path = STAGING) -> str:
    """Copy a demo under a short, cfg-safe, COLLISION-FREE name.

    The name is derived from the demo file's content (first 64KB + size), not
    a loop index: index-based names silently aliased different demos across
    runs, so a capture could seek into the WRONG demo (found 2026-08-30 via a
    validation frame showing another match's scoreboard). idx is retained for
    call compatibility and ignored.
    """
    import hashlib
    h = hashlib.sha256()
    h.update(str(demo_path.stat().st_size).encode())
    with open(demo_path, "rb") as f:
        h.update(f.read(65536))
    safe = f"d{h.hexdigest()[:10]}"
    dst = staging / "wolfcam-ql" / "demos" / f"{safe}.dm_73"
    if not dst.exists() or dst.stat().st_size != demo_path.stat().st_size:
        shutil.copy2(demo_path, dst)
    return safe


def write_capture_cfg(windows: list[dict], staging: Path = STAGING,
                      profile: str | None = None) -> str:
    """One demo's capture script: chained seek/record/stop, then quit.

    windows: [{clip_name, start_ms, end_ms}], sorted ascending by start_ms.
    Executed via cgamepostinit.cfg (the reliable post-init hook the stock
    wolfcam automation scripts use).
    """
    from creative_suite.engine import master_profile as _mp
    cfg_name = _mp._CFG_FILES.get(profile or _mp.PROFILE_NAME,
                                  "wolfcam_tr4sh_master_capture.cfg")
    lines = [f"exec {cfg_name}"]
    prev_end = None
    for w in sorted(windows, key=lambda w: w["start_ms"]):
        name = _validate_cfg_token(str(w["clip_name"]))
        start, end = int(w["start_ms"]), int(w["end_ms"])
        if prev_end is None:
            lines.append(f"seekservertime {start - SEEK_SETTLE_MS}")
            lines.append(f"at {start} video avi name {name}")
        else:
            t = prev_end + INTER_WINDOW_MS
            lines.append(f"at {t} seekservertime {start - SEEK_SETTLE_MS}")
            lines.append(f"at {start} video avi name {name}")
        lines.append(f"at {end} stopvideo")
        prev_end = end
    lines.append(f"at {prev_end + INTER_WINDOW_MS} quit")
    cfg = "\n".join(lines) + "\n"
    gamedir = staging / "wolfcam-ql"
    write_engine_file(gamedir / "capture.cfg", cfg)
    write_engine_file(gamedir / "cgamepostinit.cfg", "exec capture.cfg\n")
    return cfg


def _terminate_cascade(proc: subprocess.Popen) -> None:
    """CS-4: terminate -> wait(3) -> kill -> wait."""
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except (subprocess.TimeoutExpired, OSError):
        try:
            proc.kill()
            proc.wait(timeout=10)
        except (subprocess.TimeoutExpired, OSError):
            pass


def wolfcam_cmd(safe_demo: str, staging: Path = STAGING,
                extra_sets: dict | None = None,
                width: int = WIDTH, height: int = HEIGHT,
                use_master_profile: bool = True,
                profile: str | None = None) -> list[str]:
    if use_master_profile:
        from creative_suite.engine import master_profile
        # Which launch sets depends on the profile: the review capture needs
        # different LATCHED renderer cvars (exposure), and those only take
        # effect from the command line.
        merged = dict(master_profile.launch_sets_for(profile))
        merged.update(extra_sets or {})
        extra_sets = merged
    cmd = [
        str(engine_exe(staging)),
        "+set", "fs_homepath", str(staging),
        "+set", "fs_basepath", str(staging),
        "+set", "fs_quakelivedir", str(QL_DIR),
        "+set", "r_mode", "-1",
        "+set", "r_customwidth", str(width),
        "+set", "r_customheight", str(height),
        "+set", "r_fullscreen", "0",
        "+set", "s_backend", "base",
    ]
    for k, v in (extra_sets or {}).items():
        cmd += ["+set", str(k), str(v)]
    cmd += ["+demo", safe_demo]
    return cmd


def _mock_capture(windows: list[dict], staging: Path) -> None:
    """CS_CAPTURE_MOCK: render real (tiny) AVIs so QA paths run for real."""
    videos = staging / "wolfcam-ql" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for w in windows:
        dur = max(0.5, (int(w["end_ms"]) - int(w["start_ms"])) / 1000.0)
        subprocess.run(
            [str(FFMPEG), "-y", "-loglevel", "error",
             # AT THE CAPTURE RATE. A mock that writes half the frames of a
             # real capture is a mock of a BROKEN capture, and the truncation
             # check correctly flags it.
             "-f", "lavfi", "-i", f"testsrc=size=320x180:rate={CAPTURE_FPS}",
             "-f", "lavfi", "-i", "sine=frequency=440",
             "-t", f"{dur:.3f}", "-c:v", "mjpeg", "-c:a", "pcm_s16le",
             str(videos / f"{w['clip_name']}.avi")],
            check=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW)


# THE TWO FILES THAT DECIDE WHICH RENDERER RUNS.
#
# Windows resolves `opengl32.dll` from the executable's own directory before
# anywhere else. Mesa is staged beside `wolfcamql.exe`, so the engine has been
# getting Mesa -- and, with llvmpipe absent from this MinGW x86 build, the
# softpipe reference rasteriser at about half a frame per second.
#
# Running the SAME executable from a directory without these two files gets
# the system NVIDIA ICD instead. Measured 2026-09-08 on one 2,500 ms window:
#
#     softpipe   303.4 s   77 frames   30.8 fps captured
#     NVIDIA      22.4 s  150 frames   60.0 fps captured
#
# 13.5x faster, the full frame count, and the "capture writes 30 fps when the
# cfg asks for 60" defect turns out to have been softpipe dropping frames it
# could not render in time. It was never an engine bug.
MESA_DLLS = ("opengl32.dll", "libgallium_wgl.dll")

#: `native` uses the GPU. `software` reinstates Mesa, which is how this ran
#: until the NVIDIA path was actually tried.
GL_MODE_ENV = "PANTHEON_GL"


def gl_mode() -> str:
    mode = os.getenv(GL_MODE_ENV, "native").strip().lower()
    if mode not in ("native", "software"):
        raise ValueError(f"{GL_MODE_ENV} must be native or software, "
                         f"not {mode!r}")
    return mode


def software_gl() -> bool:
    """Whether this capture will run on the CPU rasteriser."""
    return gl_mode() == "software"


def native_gl_dir(staging: Path = STAGING) -> Path:
    """A view of the engine with Mesa left out, built by hard link.

    Not a second install: every file is a link to the one in staging, so there
    is no copy to keep in step and no gigabytes duplicated. The engine still
    reads all its assets from staging through fs_basepath -- the only thing
    this directory changes is which `opengl32.dll` Windows finds first.
    """
    staging = Path(staging)
    d = staging / "_native_gl"
    d.mkdir(parents=True, exist_ok=True)
    skip = {n.lower() for n in MESA_DLLS}
    for src in list(staging.glob("*.dll")) + [staging / "wolfcamql.exe"]:
        if not src.is_file() or src.name.lower() in skip:
            continue
        dst = d / src.name
        if dst.exists():
            if dst.stat().st_size == src.stat().st_size:
                continue
            dst.unlink()
        try:
            os.link(src, dst)
        except OSError:
            import shutil
            shutil.copy2(src, dst)
    for name in MESA_DLLS:                # never let one linger here
        (d / name).unlink(missing_ok=True)
    return d


def engine_exe(staging: Path = STAGING) -> Path:
    """The executable to launch, for the renderer this run wants."""
    if software_gl():
        return Path(staging) / "wolfcamql.exe"
    return native_gl_dir(staging) / "wolfcamql.exe"


def frames_expected(windows: list[dict], fps: int = CAPTURE_FPS) -> int:
    return sum(int(round((int(w["end_ms"]) - int(w["start_ms"])) / 1000.0 * fps))
               for w in windows)


def count_frames(avi: Path) -> int:
    """Frames in the video stream, counted rather than trusted.

    A truncated capture is a well-formed AVI: it opens, it plays, and its
    header says 60 fps. Nothing about the file announces that it holds a
    quarter of the action, which is why this has to be counted.
    """
    import re as _re
    try:
        r = subprocess.run(
            [str(FFPROBE), "-v", "error", "-count_frames",
             "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
             "-of", "default=nw=1:nk=1", str(avi)],
            capture_output=True, text=True, timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return 0
    nums = [int(x) for x in _re.findall(r"\d+", r.stdout)]
    return nums[0] if nums else 0


#: Below this share of the requested frames the clip is not what was asked for.
#: Not 1.0: a capture legitimately loses a frame or two at the seam.
COMPLETE_ENOUGH = 0.95


def true_frame_rate(windows: list[dict], frames: int) -> float:
    """The rate the engine ACTUALLY captured at, from the window it covered.

    THE HEADER CAN BE HONEST AND STILL WRONG. `cl_aviFrameRate` is frames
    written per second of DEMO time -- it decides temporal resolution, not how
    much of the action is covered. The engine writes that number into the AVI
    header (`afd.frameRate = cl_aviFrameRate->integer`). If it then writes
    fewer frames than the rate implies while still covering the whole window,
    the file is COMPLETE but plays too fast.

    Measured 2026-09-08: a 2,500 ms window produced 77 frames in a file
    declaring 60 fps -- 1.28 s of playback for 2.5 s of action, i.e. double
    speed. Checked by eye: the first frame is the jump pad at the start of the
    window and the last frame is the kill at the end of it. Nothing was
    missing; the clock was wrong.
    """
    span_s = sum((int(w["end_ms"]) - int(w["start_ms"])) / 1000.0
                 for w in windows)
    return frames / span_s if span_s > 0 else 0.0


def playback_error(windows: list[dict], frames: int,
                   declared_fps: int = CAPTURE_FPS) -> float:
    """How many times too fast the clip plays. 1.0 is correct.

    2.0 means the action runs at double speed, which is a sync defect an
    editor cannot see in a thumbnail and will not notice until the cut is on
    a beat.
    """
    actual = true_frame_rate(windows, frames)
    return declared_fps / actual if actual > 0 else 0.0


def retime(avi: Path, fps: float, dest: Path | None = None) -> Path:
    """Rewrite the container so the declared rate matches what was captured.

    The frames are untouched -- this is a remux, not a re-encode. A clip
    captured at 30 fps and labelled 60 becomes a 30 fps clip that plays at the
    right speed, with 30 fps of smoothness, which is the truth about it.
    """
    dest = Path(dest) if dest else avi
    tmp = avi.with_suffix(".retimed.avi")
    r = subprocess.run(
        [str(FFMPEG), "-v", "error", "-y", "-r", f"{fps:.6f}", "-i", str(avi),
         "-c", "copy", str(tmp)],
        capture_output=True, timeout=900,
        creationflags=subprocess.CREATE_NO_WINDOW)
    if r.returncode != 0 or not tmp.exists():
        raise RuntimeError(f"retime failed: {r.stderr.decode('utf-8','replace')[:200]}")
    tmp.replace(dest)
    return dest


def capture_demo(safe_demo: str, windows: list[dict],
                 staging: Path = STAGING, profile: str | None = None) -> dict:
    """Run one wolfcam session capturing all windows of one demo.

    Returns {ok, returncode, elapsed_s, avis: {clip_name: path}, error}.
    """
    write_capture_cfg(windows, staging, profile)
    videos = staging / "wolfcam-ql" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for w in windows:  # remove stale outputs so success detection is honest
        for old in videos.glob(f"{w['clip_name']}*.avi"):
            old.unlink()

    total_capture_s = sum(
        (int(w["end_ms"]) - int(w["start_ms"])) / 1000.0 for w in windows)
    # Seeks fast-forward-parse the demo (~50x realtime measured; budget 25x).
    max_seek_s = max(int(w["start_ms"]) for w in windows) / 1000.0
    # Budget for the renderer we are ACTUALLY going to use, not the one the
    # constant was calibrated against.
    slowdown = (SOFTWARE_CAPTURE_SLOWDOWN if software_gl() else
                CAPTURE_SLOWDOWN)
    timeout = (LAUNCH_OVERHEAD_S + total_capture_s * slowdown
               + max_seek_s / 12.0)   # /25 timed out a slow-parsing demo (330)
    t0 = time.time()

    if os.getenv("CS_CAPTURE_MOCK"):
        _mock_capture(windows, staging)
        rc = 0
    else:
        # Minimized and NOT activated. Wolfcam is a game client: a new
        # top-level window takes the foreground, and doing that to someone
        # mid-round costs them the round. See capture_guard.
        from creative_suite.engine.capture_guard import quiet_startup_info
        # ASK THE ONE AUTHORITY, even though every queue already did: this
        # is the process that opens the window, and it must not be reachable
        # by a caller that forgot. Raises RenderNotPermitted; a queue turns
        # that into QUEUED + RENDER DEFERRED, never FAILED.
        from engine.pantheon import render_permit
        render_permit.require(f"capture_demo:{safe_demo}")
        # SOFTWARE GL. This driver kills wolfcam during R_Init -- the same
        # NVIDIA 32-bit blocker documented for PANTHEON's own renderer, on the
        # same GPU. Mesa is staged BESIDE wolfcamql.exe (Windows resolves
        # opengl32.dll from the executable's own directory first), so this
        # process gets softpipe and every other process on the machine is
        # untouched. Nothing in System32 was modified and no driver setting
        # was changed. GALLIUM_DRIVER must be set explicitly: the default
        # Zink probe crashes before it can fall back.
        env = dict(os.environ)
        if software_gl():
            env["GALLIUM_DRIVER"] = "softpipe"
        proc = subprocess.Popen(
            wolfcam_cmd(safe_demo, staging, profile=profile), cwd=staging,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=env, startupinfo=quiet_startup_info())
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_cascade(proc)
            return {"ok": False, "returncode": None,
                    "elapsed_s": time.time() - t0, "avis": {},
                    "error": f"TIMEOUT after {timeout:.0f}s"}
        except BaseException:
            _terminate_cascade(proc)
            raise

    avis = {}
    for w in windows:
        cand = sorted(videos.glob(f"{w['clip_name']}*.avi"))
        if cand:
            avis[w["clip_name"]] = cand[0]

    # THE FILE CAN BE COMPLETE AND STILL WRONG. Count the frames, work out the
    # rate that actually implies, and RETIME the container so the declared
    # rate is the truth. The frames are not touched.
    want = frames_expected(windows)
    got = sum(count_frames(a) for a in avis.values())
    speed = playback_error(windows, got) if got else 0.0
    retimed = []
    if got and abs(speed - 1.0) > 0.05:
        actual = true_frame_rate(windows, got)
        for a in avis.values():
            try:
                retime(Path(a), actual)
                retimed.append(str(a))
            except (RuntimeError, OSError):
                pass
    short = bool(avis) and want > 0 and got < want * COMPLETE_ENOUGH
    return {"ok": len(avis) == len(windows), "returncode": rc,
            "elapsed_s": time.time() - t0, "avis": avis,
            "frames_expected": want, "frames_written": got,
            "capture_fps": round(true_frame_rate(windows, got), 2) if got else 0,
            "played_too_fast_by": round(speed, 2),
            "retimed": retimed,
            "under_sampled": short,
            "error": None if len(avis) == len(windows)
            else f"missing {len(windows) - len(avis)} AVIs"}


def publish_avi(avi: Path, tier: str, clip_name: str) -> Path:
    """Move a captured AVI into generated_clips/<tier>/. One physical file
    per clip; multiple labels live in the DB, not the filesystem."""
    dest_dir = CLIPS_DIR / tier
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{clip_name}.avi"
    if dest.exists():
        dest.unlink()
    shutil.move(str(avi), dest)
    return dest
