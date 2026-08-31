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

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = REPO_ROOT / "engine" / "engines" / "ghidra" / "binaries"
CANONICAL_GAMEDIR = (REPO_ROOT / "engine" / "engines" / "_canonical"
                     / "package-files" / "wolfcam-ql")
STAGING = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
# Masters live on the big drive; provenance rows store absolute paths.
CLIPS_DIR = Path(os.getenv("QL_MASTERS_DIR",
                           r"D:\QUAKE_LEGACY_MASTERS\generated_clips"))
QL_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live")
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

WOLFCAM_VERSION = "wolfcamql-11.3"
FPS = 60
WIDTH, HEIGHT = 1920, 1080
SEEK_SETTLE_MS = 600        # let renderer settle between seek and record
INTER_WINDOW_MS = 300       # gap between stopvideo and next seek
LAUNCH_OVERHEAD_S = 150     # engine start + demo load + seeks
CAPTURE_SLOWDOWN = 10       # worst-case capture seconds per window second


class CfgInjectionError(ValueError):
    pass


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


def write_capture_cfg(windows: list[dict], staging: Path = STAGING) -> str:
    """One demo's capture script: chained seek/record/stop, then quit.

    windows: [{clip_name, start_ms, end_ms}], sorted ascending by start_ms.
    Executed via cgamepostinit.cfg (the reliable post-init hook the stock
    wolfcam automation scripts use).
    """
    lines = ["exec wolfcam_tr4sh_master_capture.cfg"]
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
    (gamedir / "capture.cfg").write_text(cfg, encoding="ascii")
    (gamedir / "cgamepostinit.cfg").write_text("exec capture.cfg\n",
                                               encoding="ascii")
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
                use_master_profile: bool = True) -> list[str]:
    if use_master_profile:
        from creative_suite.engine import master_profile
        merged = dict(master_profile.LAUNCH_SETS)
        merged.update(extra_sets or {})
        extra_sets = merged
    cmd = [
        str(staging / "wolfcamql.exe"),
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
             "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=30",
             "-f", "lavfi", "-i", "sine=frequency=440",
             "-t", f"{dur:.3f}", "-c:v", "mjpeg", "-c:a", "pcm_s16le",
             str(videos / f"{w['clip_name']}.avi")],
            check=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW)


def capture_demo(safe_demo: str, windows: list[dict],
                 staging: Path = STAGING) -> dict:
    """Run one wolfcam session capturing all windows of one demo.

    Returns {ok, returncode, elapsed_s, avis: {clip_name: path}, error}.
    """
    write_capture_cfg(windows, staging)
    videos = staging / "wolfcam-ql" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for w in windows:  # remove stale outputs so success detection is honest
        for old in videos.glob(f"{w['clip_name']}*.avi"):
            old.unlink()

    total_capture_s = sum(
        (int(w["end_ms"]) - int(w["start_ms"])) / 1000.0 for w in windows)
    # Seeks fast-forward-parse the demo (~50x realtime measured; budget 25x).
    max_seek_s = max(int(w["start_ms"]) for w in windows) / 1000.0
    timeout = (LAUNCH_OVERHEAD_S + total_capture_s * CAPTURE_SLOWDOWN
               + max_seek_s / 12.0)   # /25 timed out a slow-parsing demo (330)
    t0 = time.time()

    if os.getenv("CS_CAPTURE_MOCK"):
        _mock_capture(windows, staging)
        rc = 0
    else:
        proc = subprocess.Popen(
            wolfcam_cmd(safe_demo, staging), cwd=staging,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    return {"ok": len(avis) == len(windows), "returncode": rc,
            "elapsed_s": time.time() - t0, "avis": avis,
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
