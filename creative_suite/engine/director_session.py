"""Live director session — Path A of the replay runtime feasibility doc.

See docs/reference/replay-runtime-feasibility.md for why this exists: wolfcamql
has no IPC surface, so there is no way for a browser to remote-control a
running engine window. The only real "live" control available today is a
human physically at the keyboard flying freecam inside a VISIBLE wolfcam
window — that is ordinary local input handling, not IPC, and it already
works with zero engine changes.

The mechanism (source-verified against cg_consolecmds.c / qcommon/common.c):

  - ``viewpos`` (CG_Viewpos_f, cg_consolecmds.c:8420) prints
    ``(%f %f %f) %f %f %f %i`` = worldspace x y z (viewheight-corrected),
    pitch, yaw, roll, cg.time (demo serverTime) to the console.
  - ``logfile 2`` (qcommon/common.c:3087, semantics at common.c:119/339)
    makes every console print flush to ``qconsole.log`` immediately.
  - Binding a key to ``viewpos`` therefore turns every keypress into one
    parseable keyframe line, with no engine modification.

Flow: launch_session() opens a VISIBLE wolfcam window seeked to a moment with
freecam armed and the keybind live. The user flies the camera for real, at
the keyboard, pressing the bound key to mark keyframes. poll_keyframes()
tails qconsole.log and returns camera_paths._kf-shaped dicts. stop_session()
tears the window down (CS-4 cascade). save_recipe() takes everything
captured so far and drops it straight into the existing
camera_paths/timeline/shot_plan pipeline, returning a scene_recipe_id.

This module deliberately uses its OWN staging install
(``output/demo_v2/_wolfcam_director_staging/``), separate from the batch
capture / review-proxy staging dir (``wolfcam_capture.STAGING``). A director
session is a human flying a camera for an open-ended amount of time — sharing
a staging dir (and its single ``cgamepostinit.cfg``/``qconsole.log``) with a
concurrently-running batch capture or review-proxy job would corrupt both.
Only one director session may be live at a time (see ``_reject_if_live``),
mirroring the CS-1 "single controlled writer" rule for the batch pipeline.

CS_DIRECTOR_MOCK=1 skips spawning wolfcam entirely and writes a couple of
fake viewpos-shaped lines directly into a fake qconsole.log, so the whole
launch -> poll -> stop -> save_recipe loop is testable headlessly (pattern:
CS_CAPTURE_MOCK in wolfcam_capture.py, CS_PROXY_MOCK in review_proxy.py).
"""
from __future__ import annotations

import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from creative_suite.engine import master_profile
from engine.pantheon import render_permit
from creative_suite.engine import shot_plan
from creative_suite.engine import wolfcam_capture as wc
from creative_suite.engine.camera_paths import _kf
from creative_suite.engine.timeline import Timeline

DIRECTOR_STAGING = wc.REPO_ROOT / "output" / "demo_v2" / "_wolfcam_director_staging"

# F9 is unused by defaultwolfcam.cfg's default bind set (verified against
# engine/engines/_canonical/package-files/wolfcam-ql/defaultwolfcam.cfg):
# ENTER=freecam toggle, F2=toggle in_nograb, F4=quit, F6=echopopupcvar,
# F11=screenshotPNG, digits 0/9/2/3/4/5 are seek/camera-path toggles,
# [ ] o v BACKSPACE i are camera-point editing, CTRL/SHIFT/alt/./e/q/f are
# freecam movement modifiers. F9 collides with none of it.
DIRECTOR_KEYBIND = "F9"

DEFAULT_FOV = 110.0

_VIEWPOS_RE = re.compile(
    r"\(([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s+([-\d.]+) ([-\d.]+) ([-\d.]+) (\d+)"
)

# session_id -> {state, proc, qconsole_path, staging, demo_path, safe_demo,
#                seek_ms, fov, started_at}
_sessions: dict[str, dict[str, Any]] = {}


def _reject_if_live() -> None:
    """Only one director session may run at a time (shared staging dir,
    shared qconsole.log, and physically only one human at the keyboard)."""
    for sess in _sessions.values():
        if sess["state"] == "STOPPED":
            continue
        proc = sess.get("proc")
        if proc is None or proc.poll() is None:
            raise RuntimeError("a director session is already running")


def _write_director_cfg(gamedir: Path, seek_target_ms: int, fov: float) -> str:
    """cgamepostinit.cfg for this launch: exec the frozen director profile,
    pin fov to the caller's request (the profile's own cg_fov is only a
    baseline and would otherwise win the exec race), seek, then arm freecam
    and bind the keyframe-mark key. Every token is CS-5 validated."""
    profile_cfg = master_profile._CFG_FILES[master_profile.DIRECTOR_PROFILE_NAME]
    seek_token = wc._validate_cfg_token(str(int(seek_target_ms)))
    fov_token = wc._validate_cfg_token("{:.2f}".format(float(fov)))
    bind_key = wc._validate_cfg_token(DIRECTOR_KEYBIND)
    lines = [
        f"exec {profile_cfg}",
        f"cg_fov {fov_token}",
        f"seekservertime {seek_token}",
        "freecam",
        f"bind {bind_key} viewpos",
    ]
    cfg = "\n".join(lines) + "\n"
    wc.write_engine_file(gamedir / "cgamepostinit.cfg", cfg)
    return cfg


def _write_mock_console_lines(qconsole_path: Path, base_ms: int) -> None:
    """CS_DIRECTOR_MOCK: a few viewpos-shaped lines standing in for keypresses."""
    qconsole_path.parent.mkdir(parents=True, exist_ok=True)
    samples = [
        (100.0, 200.0, 40.0, 0.0, 90.0, 0.0, base_ms),
        (150.0, 220.0, 45.0, -5.0, 95.0, 0.0, base_ms + 500),
        (200.0, 240.0, 50.0, -8.0, 100.0, 0.0, base_ms + 1000),
    ]
    lines = [
        "({:.6f} {:.6f} {:.6f}) {:.6f} {:.6f} {:.6f} {}".format(
            x, y, z, pitch, yaw, roll, t)
        for (x, y, z, pitch, yaw, roll, t) in samples
    ]
    qconsole_path.write_text("\n".join(lines) + "\n", encoding="ascii")


def launch_session(demo_path: str | Path, seek_ms: int,
                   fov: float = DEFAULT_FOV,
                   staging: Path = DIRECTOR_STAGING) -> dict[str, Any]:
    """Stage the demo, arm freecam at seek_ms, launch wolfcam VISIBLE.

    Does not wait for the process to exit — the whole point is a human
    watches and flies the window live. Returns immediately with the Popen
    handle (None under CS_DIRECTOR_MOCK).
    """
    _reject_if_live()
    demo_path = Path(demo_path)
    mock = bool(os.getenv("CS_DIRECTOR_MOCK"))
    gamedir = staging / "wolfcam-ql"

    if mock:
        (gamedir / "demos").mkdir(parents=True, exist_ok=True)
        safe = (wc.stage_demo(demo_path, staging=staging)
               if demo_path.exists() else "mockdemo")
    else:
        wc.ensure_install(staging)
        safe = wc.stage_demo(demo_path, staging=staging)

    qconsole_path = gamedir / "qconsole.log"
    if qconsole_path.exists():
        qconsole_path.unlink()  # fresh session starts at byte offset 0

    seek_target = max(0, int(seek_ms) - wc.SEEK_SETTLE_MS)
    _write_director_cfg(gamedir, seek_target, fov)

    if mock:
        proc = None
        _write_mock_console_lines(qconsole_path, seek_target)
    else:
        extra_sets = {"logfile": 2}
        cmd = wc.wolfcam_cmd(safe, staging=staging, extra_sets=extra_sets)
        # VISIBLE on purpose: no CREATE_NO_WINDOW, no stdout/stderr capture.
        # A human needs to see and fly this window -- and asked for it, which
        # the permit checks: PANTHEON_RENDER is not off, no protected game up.
        render_permit.require("director_session")
        proc = subprocess.Popen(cmd, cwd=staging)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "state": "FLYING",
        "proc": proc,
        "qconsole_path": qconsole_path,
        "staging": staging,
        "demo_path": demo_path,
        "safe_demo": safe,
        "seek_ms": int(seek_ms),
        "fov": float(fov),
        "started_at": time.time(),
    }
    return {"session_id": session_id, "qconsole_path": qconsole_path, "proc": proc}


def session_info(session_id: str) -> dict[str, Any] | None:
    """Read-only snapshot of a session's tracked fields, or None if unknown."""
    sess = _sessions.get(session_id)
    if sess is None:
        return None
    return dict(sess)


def poll_keyframes(session_id: str, since_byte_offset: int = 0) -> dict[str, Any]:
    """Tail qconsole.log from since_byte_offset; parse every viewpos line.

    Returns {"keyframes": [...], "next_offset": int, "count": int}. Keyframes
    are camera_paths._kf-shaped with the RAW demo serverTime from the
    console line (not yet normalized to a shot-relative t_ms — save_recipe
    does that normalization once the flight is over).
    """
    sess = _sessions.get(session_id)
    if sess is None:
        raise KeyError(f"unknown director session: {session_id}")
    path = sess["qconsole_path"]
    if not path.exists():
        return {"keyframes": [], "next_offset": since_byte_offset, "count": 0}
    with open(path, "rb") as f:
        f.seek(since_byte_offset)
        chunk = f.read()
    next_offset = since_byte_offset + len(chunk)
    text = chunk.decode("utf-8", errors="replace")
    fov = sess.get("fov", DEFAULT_FOV)
    keyframes = []
    for line in text.splitlines():
        m = _VIEWPOS_RE.search(line)
        if not m:
            continue
        x, y, z, pitch, yaw, roll, t = m.groups()
        keyframes.append(_kf(int(t), (float(x), float(y), float(z)),
                             (float(pitch), float(yaw), float(roll)), fov))
    return {"keyframes": keyframes, "next_offset": next_offset,
            "count": len(keyframes)}


def stop_session(session_id: str) -> dict[str, Any]:
    """CS-4 terminate -> wait(3) -> kill cascade. Keeps qconsole.log on disk —
    save_recipe may run after stop."""
    sess = _sessions.get(session_id)
    if sess is None:
        raise KeyError(f"unknown director session: {session_id}")
    proc = sess.get("proc")
    if proc is not None:
        wc._terminate_cascade(proc)
    sess["state"] = "STOPPED"
    return {"session_id": session_id, "state": "STOPPED",
            "qconsole_path": sess["qconsole_path"]}


def save_recipe(session_id: str, demo_sha256: str, event: dict[str, Any],
                effect_ids: tuple[str, ...] | list[str] = (),
                asset_pack_ids: tuple[str, ...] | list[str] = ()) -> str:
    """Assemble + persist a shot plan from everything captured so far.

    Keyframes are normalized to be shot-relative (t_ms starts at 0, matching
    the convention every other camera_paths generator already produces —
    see camera_paths.py's module docstring and timeline.to_wolfcam_script's
    base_servertime parameter). The original absolute demo serverTime of the
    first keyframe is recorded in camera.params.base_servertime so a caller
    can reconstitute an absolute wolfcam script later via
    to_wolfcam_script(timeline, keyframes, base_servertime=...).
    """
    sess = _sessions.get(session_id)
    if sess is None:
        raise KeyError(f"unknown director session: {session_id}")
    polled = poll_keyframes(session_id, since_byte_offset=0)
    keyframes = polled["keyframes"]
    if not keyframes:
        raise ValueError("no keyframes captured for this director session — "
                         f"fly the camera and press {DIRECTOR_KEYBIND} at "
                         "least once before saving")
    t0 = keyframes[0]["t_ms"]
    rel_keyframes = [dict(kf, t_ms=kf["t_ms"] - t0) for kf in keyframes]
    profile_id = master_profile.profile_id(master_profile.DIRECTOR_PROFILE_NAME)
    camera = {
        "name": "freecam_recorded",
        "params": {
            "mode": "freecam_recorded",
            "base_servertime": t0,
            "fov": sess.get("fov", DEFAULT_FOV),
            "session_id": session_id,
        },
    }
    plan = shot_plan.assemble_shot_plan(
        demo_sha256=demo_sha256,
        event=dict(event),
        profile_id=profile_id,
        camera=camera,
        keyframes=rel_keyframes,
        timeline=Timeline(),   # minimal: no ramps unless the caller adds them
        effect_ids=list(effect_ids),
        asset_pack_ids=list(asset_pack_ids),
    )
    return shot_plan.persist_shot_plan(plan)
