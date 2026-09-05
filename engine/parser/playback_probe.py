"""Ask WolfcamQL whether it will actually play a synthetic demo.

WHY. Our parser agreeing with our writer is necessary and not sufficient --
both could share a misreading of the format. The engine is the independent
validator, and the only question that matters is whether it opens the file,
advances its timeline and draws players.

ISOLATION. The staging install is used READ-ONLY as `fs_basepath`; a scratch
directory is `fs_homepath`, so our cfg and demo win the search path without
touching `output/demo_v2/_wolfcam_staging/wolfcam-ql/capture.cfg`, which the
review session may be using. The shared capture lock is taken for the whole
launch and released in a finally: human review owns this machine.

    python -m engine.parser.playback_probe <demo.dm_73> [--seconds 8]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _main_checkout() -> Path:
    """The primary checkout, not this git worktree.

    The staged WolfcamQL install -- its DLLs, its paks -- lives once, in the
    main checkout. Resolving it relative to this file put `fs_basepath` inside
    the worktree, where a partial copy of the staging directory happened to
    exist with the .exe but no `uix86.dll` and no `pak00.pk3`. The engine
    launched, failed every RE_RegisterShader, then died on
    `VM_Create on UI failed` -- a confusing error a long way from its cause.
    """
    override = os.environ.get("QL_REPO_ROOT")
    if override:
        return Path(override)
    try:
        common = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=20).stdout.strip()
        if common:
            p = Path(common)
            if not p.is_absolute():
                p = (REPO / p).resolve()
            return p.parent
    except Exception:                             # pragma: no cover - env
        pass
    return REPO


MAIN = _main_checkout()
STAGING = Path(os.environ.get("QL_WOLFCAM_STAGING",
                              MAIN / "output/demo_v2/_wolfcam_staging"))
LOCK = MAIN / "output/demo_v2/_capture.lock"
QL_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live")

# What a usable staging install must contain. Checked before launch so a
# missing file is named directly instead of surfacing as a VM error.
REQUIRED = ("wolfcamql.exe", "wolfcam-ql/uix86.dll", "wolfcam-ql/cgamex86.dll",
            "baseq3/pak00.pk3")


def check_staging(staging: Path = STAGING) -> list[str]:
    return [r for r in REQUIRED if not (staging / r).exists()]

# Screenshot beats, in seconds of demo time. Spread so a still timeline and a
# moving one look different.
SHOT_TIMES = (1.0, 3.0, 5.0, 7.0)


def acquire_lock() -> None:
    """Same protocol as capture_batch_run.acquire_lock -- PID file, with a
    liveness check so a crashed run does not block the machine forever."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        pid = LOCK.read_text().strip()
        alive = False
        try:
            os.kill(int(pid), 0)
            alive = True
        except (OSError, ValueError, SystemError):
            alive = False          # not a pid, or gone: a stale lock
        if alive:
            raise SystemExit(f"capture busy (pid {pid}) -- review has priority")
    LOCK.write_text(str(os.getpid()))


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def build_cfg(shots: tuple[float, ...], quit_at: float,
              extra: dict | None = None) -> str:
    """Console script the engine runs after cgame init.

    `cg_draw2D 1` is not optional: with it at 0 the engine suppresses every
    2D element, which is how a working readout can look like a broken one.
    `condump` is what turns a failed launch into a diagnosable one.
    """
    lines = [
        "set cg_draw2D 1",
        "set cg_drawFPS 1",
        "set cg_drawSpeed 1",           # the real cvar, per the runtime test
        "set cg_drawTeamOverlay 1",
        "set r_drawSun 0",
        "set com_maxfps 60",
        "set cl_freezeDemo 0",
        "set timescale 1",
    ]
    for k, v in (extra or {}).items():
        lines.append(f"set {k} {v}")
    for i, t in enumerate(shots):
        m, s = divmod(t, 60)
        lines.append(f"at {int(m)}:{s:05.2f} screenshotJPEG shot_{i}")
    m, s = divmod(quit_at, 60)
    lines.append(f"at {int(m)}:{s:05.2f} condump probe_console.txt")
    lines.append(f"at {int(m)}:{s + 0.5:05.2f} quit")
    return "\n".join(lines) + "\n"


def probe(demo: Path, *, seconds: float = 8.0, timeout: float = 180.0,
          scratch: Path | None = None, extra_cvars: dict | None = None) -> dict:
    scratch = scratch or (REPO / ".tmp/playback_probe")
    if scratch.exists():
        shutil.rmtree(scratch, ignore_errors=True)
    home = scratch / "wolfcam-ql"
    (home / "demos").mkdir(parents=True, exist_ok=True)
    (home / "screenshots").mkdir(parents=True, exist_ok=True)

    safe = demo.stem
    shutil.copy2(demo, home / "demos" / demo.name)
    (home / "cgamepostinit.cfg").write_text(
        build_cfg(SHOT_TIMES, seconds, extra_cvars), encoding="ascii")

    missing = check_staging()
    if missing:
        return {"launched": False,
                "error": f"staging at {STAGING} is missing {missing}"}
    exe = STAGING / "wolfcamql.exe"

    cmd = [
        str(exe),
        "+set", "fs_homepath", str(scratch),
        "+set", "fs_basepath", str(STAGING),
        "+set", "fs_quakelivedir", str(QL_DIR),
        "+set", "r_mode", "-1",
        "+set", "r_customwidth", "1280",
        "+set", "r_customheight", "720",
        "+set", "r_fullscreen", "0",
        "+set", "s_initsound", "0",
        "+set", "com_maxfps", "60",
        "+demo", safe,
    ]
    t0 = time.time()
    from creative_suite.engine import render_permit
    render_permit.require("playback_probe")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    try:
        out, _ = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        # CS-4: a GUI process left running holds the desktop and file locks.
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        out, rc = b"", "TIMEOUT"
    elapsed = time.time() - t0

    shots = sorted((home / "screenshots").glob("*"))
    console = home / "probe_console.txt"
    stderr_log = scratch / "stderr.txt"
    engine_log = (stderr_log.read_text("latin-1", "replace")
                  if stderr_log.exists() else "")
    return {
        "launched": True,
        "returncode": rc,
        "elapsed_s": round(elapsed, 1),
        "stdout_tail": out.decode("latin-1", "replace")[-4000:] if out else "",
        "screenshots": [str(p) for p in shots],
        "console": str(console) if console.exists() else None,
        "console_text": (console.read_text("latin-1", "replace")
                         if console.exists() else ""),
        "engine_log_tail": engine_log[-3000:],
        "scratch": str(scratch),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("demo", type=Path)
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--timeout", type=float, default=180.0)
    args = ap.parse_args()

    acquire_lock()
    try:
        result = probe(args.demo, seconds=args.seconds, timeout=args.timeout)
    finally:
        release_lock()

    print(f"launched   : {result.get('launched')}")
    print(f"returncode : {result.get('returncode')}  in {result.get('elapsed_s')}s")
    print(f"screenshots: {len(result.get('screenshots') or [])}")
    for p in result.get("screenshots") or []:
        print(f"   {p}")
    if result.get("stdout_tail"):
        print("--- stdout tail ---")
        print(result["stdout_tail"][-2500:])
    if result.get("error"):
        print(f"ERROR: {result['error']}")
    if result.get("engine_log_tail"):
        print("--- engine stderr tail ---")
        print(result["engine_log_tail"][-2000:])
    if result.get("console_text"):
        print("--- console dump tail ---")
        print(result["console_text"][-2500:])
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
