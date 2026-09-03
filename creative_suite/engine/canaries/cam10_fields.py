"""CAM10 core field proof: viewEnt, offset, commandStr. Three questions.

Can one camera point truthfully mean "at this moment, look at THIS entity,
from THIS derived position, and fire THIS visual event" -- with delivered
timing we have measured rather than assumed?

Each experiment is a pair or a small set of captures that differ in exactly
one authored field, through the production runner. Nothing is inferred from
the source alone: the source says what the engine intends, and only a frame
says what it delivered.

    viewEnt      does the engine aim for us, and what happens when the
                 entity it was aiming at is removed on impact
    offset       is the offset applied, and does the derived position clip
                 geometry the authored path never touched
    commandStr   how many frames after the camera point does the effect
                 appear, and is that number stable

Usage:  cam10_fields.py <out_dir> [viewent|offset|command|all]
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("G:/QUAKE_LEGACY")
sys.path.insert(0, str(REPO))
os.environ["CS_PREVIEW_KEEP_RAW"] = "1"

import numpy as np                                                    # noqa: E402
from creative_suite.api import director_draft as dd, frags as fr      # noqa: E402
from creative_suite.engine import (cam10_writer as cw, camera_paths,   # noqa: E402
                                   camera_compiler_v2 as v2,
                                   director_preview as dp, review_proxy)

FFMPEG = REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"
FRAG_ID = 24326
ROCKET_ENT = 174           # missile_samples_v1: weapon 5, 290525..291675
FPS = 60.0
FRAME_MS = 1000.0 / FPS

dp._set_state = lambda *a, **k: None       # a probe writes no cache rows

# The master profile turns centerprint off (master_profile.py:215), so a
# commandStr firing one would draw nothing and the experiment would measure
# the profile rather than the port. Re-enabled for the command captures only,
# and stated rather than smuggled.
_ENABLE_CENTERPRINT = "seta cg_drawCenterPrint 1"
# THE GATE. cg_view.c:2964 fires a camera point's command only when
# `cg_cameraQue.integer > 1`, and the runtime baseline pins cg_cameraQue at
# exactly 1 (pantheon_runtime.py). The first five firings produced nothing
# for that reason alone: the file was correct, the port was shut.
_OPEN_COMMAND_GATE = "seta cg_cameraQue 2"

_orig_cfg = dp.build_capture_cfg
_extra: list[str] = []


def _cfg_with_extra(plan, camera_cfg_lines, clip_name, fx_level):
    cfg = _orig_cfg(plan, camera_cfg_lines, clip_name, fx_level)
    if not _extra:
        return cfg
    out = []
    for line in cfg.splitlines():
        out.append(line)
        if line.startswith("exec wolfcam_"):
            out.extend(_extra)
    return "\n".join(out) + "\n"


dp.build_capture_cfg = _cfg_with_extra


def log(m: str) -> None:
    print(m, flush=True)


def _v(a):
    return np.asarray(a, dtype=float)


# ── the fixture, once ───────────────────────────────────────────────────────

def scene() -> dict:
    import sqlite3
    c = sqlite3.connect(
        "file:G:/QUAKE_LEGACY/creative_suite/database/frag_recognition.db"
        "?mode=ro", uri=True)
    demo_name, hero_ms = c.execute(
        "SELECT demo_name, server_time_ms FROM recognized_frags WHERE id=?",
        (FRAG_ID,)).fetchone()
    path = dp._projectile_path(demo_name, hero_ms)
    frag = fr._load_frag_with_master(FRAG_ID)
    frag["content_hash"] = c.execute(
        "SELECT content_hash FROM recognized_frags WHERE id=?",
        (FRAG_ID,)).fetchone()[0]
    frag["window"] = fr._frag_window(frag)
    win = int(frag["window"]["start_ms"])
    launch, impact = path["launch"], path["impact"]
    # A vantage abeam the flight, from the corridor screen that came back
    # clean at the compiler's own clearance.
    fpv = _v(launch["pos"])
    imp = _v(impact["pos"])
    lat = np.cross(imp - fpv, np.array([0.0, 0.0, 1.0]))
    lat = lat / max(float(np.linalg.norm(lat)), 1e-9)
    cam = fpv + (imp - fpv) * 0.5 + lat * 240.0 + np.array([0.0, 0.0, 120.0])
    tracer = None
    try:
        tracer = camera_paths.bsp_tracer("quarantine")
    except Exception:
        tracer = None
    return {"demo_name": demo_name, "hero_ms": hero_ms, "frag": frag,
            "win_start": win, "total_ms": int(frag["window"]["end_ms"]) - win,
            "launch_rel": int(launch["t"]) - win,
            "impact_rel": int(impact["t"]) - win,
            "cam": cam, "aim": imp, "tracer": tracer,
            "track": [(int(p[0]) + int(launch["t"]) - win,
                       float(p[1]), float(p[2]), float(p[3]))
                      for p in path["points"]]}


def capture(sc: dict, key: str, keyframes: list[dict], out: Path,
            extra_cfg: list[str] | None = None) -> dict:
    """One capture with an authored .cam10, through the production runner."""
    draft = dd._default_draft(FRAG_ID)
    draft["camera"]["mode"] = "FREECAM"
    demo_path, _ = review_proxy.demo_source(sc["demo_name"])
    plan = dp.build_plan(sc["frag"], draft, demo_path=str(demo_path))
    plan = dataclasses.replace(plan, keyframes=tuple(keyframes))

    gamedir = dp.wolfcam_capture.ensure_install() / "wolfcam-ql"
    name = f"prev_{key[:16]}"
    content = cw.write_cam10(keyframes, sc["win_start"])
    (gamedir / "cameras").mkdir(parents=True, exist_ok=True)
    dp.wolfcam_capture.write_engine_file(
        gamedir / "cameras" / f"{name}.cam10", content)

    # bypass build_camera_artifact: it recompiles from keyframes and would
    # discard the per-point fields this experiment exists to test
    cfg_lines = ["freecam", f"loadcamera {name}", "playcamera"]
    real_build = dp.build_camera_artifact
    dp.build_camera_artifact = lambda *a, **k: {
        "status": "VALID", "cfg_lines": cfg_lines,
        "cam10_hash": cw.cam10_hash(content), "cam10_path": None,
        "used_sample_count": len(keyframes), "coverage": "FULL",
        "collision_report": {}, "camera_fallback": None}
    _extra.clear()
    _extra.extend(extra_cfg or [])
    t0 = time.time()
    try:
        dp._real_capture({"preview_key": key}, plan,
                         out / f"{key}.tmp.mp4", out / f"{key}.visual.mp4",
                         sc["total_ms"] / 1000.0)
        err = None
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    finally:
        dp.build_camera_artifact = real_build
        _extra.clear()
    raw = dp.PREVIEW_DIR / f"{key}.raw.avi"
    kept = out / f"{key}.raw.avi"
    if raw.exists():
        raw.replace(kept)
    log(f"[{key}] {'ok' if not err else err} {time.time()-t0:.0f}s "
        f"points={len(keyframes)} raw={'yes' if kept.exists() else 'no'}")
    return {"key": key, "error": err,
            "media": str(out / f"{key}.visual.mp4")
            if (out / f"{key}.visual.mp4").exists() else None,
            "points": len(keyframes)}


# ── frames ──────────────────────────────────────────────────────────────────

def frames(video: Path, work: Path, count: int, start: int = 0,
           size: str = "128:72") -> list[np.ndarray]:
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("*.pgm"):
        old.unlink()
    r = subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(video),
         "-vf", f"select='gte(n\\,{start})',scale={size},format=gray",
         "-vsync", "0", "-frames:v", str(count), str(work / "f%05d.pgm")],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-800:])
    out = []
    for p in sorted(work.glob("*.pgm")):
        raw = p.read_bytes()
        i = raw.index(bytes([50, 53, 53, 10])) + 4
        out.append(np.frombuffer(raw[i:], dtype=np.uint8)
                   .astype(np.float64).reshape(72, 128))
    return out


def _kf(t_ms, pos, angles, fov=100.0, **extra):
    d = {"t_ms": float(t_ms), "pos": tuple(pos), "angles": tuple(angles),
         "fov": float(fov)}
    d.update(extra)
    return d


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "output/demo_v2/_cam10"
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    out.mkdir(parents=True, exist_ok=True)
    sc = scene()
    total = sc["total_ms"]
    cam = sc["cam"]
    aim = camera_paths.look_at_angles(tuple(cam), tuple(sc["aim"]))
    log(f"fixture frag {FRAG_ID} rocket entity {ROCKET_ENT}  "
        f"launch_rel={sc['launch_rel']} impact_rel={sc['impact_rel']} "
        f"window={total}ms")
    log(f"camera {np.round(cam,1)}  aim {tuple(round(x,1) for x in aim)}")
    result: dict = {"fixture": {"frag": FRAG_ID, "entity": ROCKET_ENT,
                               "launch_rel_ms": sc["launch_rel"],
                               "impact_rel_ms": sc["impact_rel"]},
                    "captures": []}

    # ── 1. viewEnt: the engine aims, or it does not ────────────────────────
    if which in ("all", "viewent"):
        log("\n== 1. viewEnt ==")
        fixed = [_kf(-dp.GUARD_MS, cam, aim), _kf(total + dp.GUARD_MS, cam, aim)]
        tracked = [_kf(-dp.GUARD_MS, cam, aim, view_ent=ROCKET_ENT,
                       view_type=cw.CAMERA_ANGLES_ENT),
                   _kf(total + dp.GUARD_MS, cam, aim, view_ent=ROCKET_ENT,
                       view_type=cw.CAMERA_ANGLES_ENT)]
        result["captures"].append(capture(sc, "veFixed", fixed, out))
        result["captures"].append(capture(sc, "veTrack", tracked, out))

    # ── 2. offset: applied, and where it puts the camera ───────────────────
    if which in ("all", "offset"):
        log("\n== 2. offset ==")
        for name, off in (("ctr", (0.0, 0.0, 0.0)),
                          ("lat", (140.0, 0.0, 0.0)),
                          ("vert", (0.0, 0.0, 140.0)),
                          ("both", (140.0, 0.0, 140.0))):
            kfs = [_kf(-dp.GUARD_MS, cam, aim, view_ent=ROCKET_ENT,
                       view_type=cw.CAMERA_ANGLES_ENT, offset=off),
                   _kf(total + dp.GUARD_MS, cam, aim, view_ent=ROCKET_ENT,
                       view_type=cw.CAMERA_ANGLES_ENT, offset=off)]
            r = capture(sc, f"off{name}", kfs, out)
            r["offset"] = list(off)
            # the derived position, and whether IT clears geometry -- the
            # authored point clearing is not the same claim
            derived = cam + _v(off)
            clear = None
            if sc["tracer"] is not None:
                clear = bool(camera_paths.point_in_open_space(sc["tracer"],
                                                              tuple(derived)))
            r["derived_position"] = [round(float(x), 1) for x in derived]
            r["derived_in_open_space"] = clear
            result["captures"].append(r)

    # ── 3. commandStr: how many frames late, and is it stable ──────────────
    if which in ("all", "command"):
        log("\n== 3. commandStr ==")
        base = [_kf(-dp.GUARD_MS, cam, aim), _kf(total + dp.GUARD_MS, cam, aim)]
        result["captures"].append(
            capture(sc, "cmdBase", base, out,
                    [_ENABLE_CENTERPRINT, _OPEN_COMMAND_GATE]))
        for i, at in enumerate((2000, 3000, 4000, 5000, 6000)):
            # r_gamma, not centerprint. centerprint has to survive
            # cg_drawCenterPrint, cg.centerPrintTime and a display-duration
            # check before a pixel changes, so a null result would not say
            # whether the PORT fired or the DRAW was refused. r_gamma is
            # already measured CAPTURE_VISIBLE at 88.8 grey levels and has
            # no draw gate at all, which isolates the port.
            kfs = [_kf(-dp.GUARD_MS, cam, aim),
                   _kf(at, cam, aim, command="r_gamma 1.8"),
                   _kf(total + dp.GUARD_MS, cam, aim)]
            r = capture(sc, f"cmd{at}", kfs, out,
                        [_ENABLE_CENTERPRINT, _OPEN_COMMAND_GATE])
            r["requested_at_ms"] = at
            result["captures"].append(r)

    (out / "cam10_fields.json").write_text(json.dumps(result, indent=2),
                                           encoding="utf-8")
    log(f"\nDONE {out / 'cam10_fields.json'}")


if __name__ == "__main__":
    main()
