"""Effect Lab, Camera Case A: FPV -> spline handoff -> SIDE, duration only.

ONE SCENE. ONE PATH. ONE VARIABLE.

The spatial control points are computed once and shared by every variant.
Only their timestamps change. This is exact rather than approximate because
`resample_dense` interpolates with UNIFORM Catmull-Rom (camera_compiler_v2
:163): the tangents come from the four surrounding POSITIONS and never from
their times. Re-timing a fixed point sequence therefore traces an identical
curve through space and only changes how fast the camera runs along it.

SAMPLING. 60 Hz was requested; the shot is 8.5 s plus 0.5 s of guard either
side, which at 60 Hz wants 571 camera points against a 509 ceiling, so the
compiler clamps to ~53.6 Hz and says so. That clamp is IDENTICAL for every
variant -- same span, same point count, 509 each -- so it costs nothing in
comparability. The camera grid is therefore slightly coarser than the 60 fps
delivery and the engine interpolates between points; a 100 ms handoff spans
about 5 camera points and an 800 ms one about 43. That difference is the
thing being measured, not an artefact.

MEASURING THE MOVE. The motion envelope is taken between poses interpolated
at the exact handoff boundaries, never between whichever samples happen to
fall inside them. Without that, a 100 ms move measured 540 u and an 800 ms
move 712 u along the same curve purely because the coarse grid clipped the
ends -- a sampling artefact that would have looked like the path changing
with duration.

FIXTURE. Frag 24326, chosen over 4121 on the evidence: 1125 ms of CONFIRMED
rocket flight over 1611 u with zero deviation, against 300 ms / 380 u. An
800 ms handoff is 0.7 of this flight and 2.7x the whole of 4121's, where
the move would outlast the action it exists to reveal.

The fixture is not consumed. Nothing here writes a preview-cache row, and
no moment is marked used.

Usage:  camera_case_a.py <out_dir> [--compile-only]
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
# The committed measurement. Written ONLY with --write-reference, so a
# diff here is always a decision and never a side effect of a run.
REFERENCE = REPO / "docs" / "reference" / "camera_case_a.json"
# Scratch destination for an ordinary run.
SCRATCH = REPO / ".tmp" / "canaries" / "camera_case_a.json"
sys.path.insert(0, str(REPO))
os.environ["CS_PREVIEW_KEEP_RAW"] = "1"

import numpy as np                                                    # noqa: E402
from creative_suite.api import director_draft as dd, frags as fr      # noqa: E402
from creative_suite.engine import (camera_compiler_v2 as v2,          # noqa: E402
                                   camera_paths, cam10_writer as cw,
                                   director_preview as dp, review_proxy)

FFMPEG = REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"
FRAG_ID = 24326
LADDER_MS = (100, 150, 200, 250, 300, 400, 500, 650, 800)
FRAME_MS = 1000.0 / 60.0
HZ = 60.0                      # the delivered frame grid; see module docstring
# The SIDE endpoint is not a free choice: it has to sit where the straight
# FPV->SIDE corridor is clear of level geometry, or the compiler repairs the
# path DIFFERENTLY for different durations (short handoffs came back
# SHORTENED at ~200 u while long ones came back PUSHED_OUT at ~715 u) and
# duration stops being the only variable. A geometric screen over both
# lateral signs and four heights found exactly one clear corridor on this
# map: 200 u to the far side, 280 u up. Everything on the near side is
# walled at about halfway.
SIDE_OFFSET_U = 240.0          # lateral stand-off from the flight line
SIDE_HEIGHT_U = 120.0
BOW_FRACTION = 0.0             # a bow pushes the move off the one clear line
ARC_POINTS = 12                # control points along the handoff, fixed

dp._set_state = lambda *a, **k: None      # a probe writes no cache rows


def log(m: str) -> None:
    print(m, flush=True)


# ── geometry helpers ────────────────────────────────────────────────────────

def _v(a):
    return np.asarray(a, dtype=float)


def _unit(a):
    n = float(np.linalg.norm(a))
    return a / n if n > 1e-9 else np.array([1.0, 0.0, 0.0])


def _ang_delta(a: float, b: float) -> float:
    """Shortest signed difference between two degrees."""
    return (b - a + 180.0) % 360.0 - 180.0


# ── the fixed shot ──────────────────────────────────────────────────────────

def build_scene() -> dict:
    """Everything that is the same for every variant."""
    import sqlite3
    c = sqlite3.connect(
        "file:G:/QUAKE_LEGACY/creative_suite/database/frag_recognition.db?mode=ro",
        uri=True)
    demo_name, hero_ms = c.execute(
        "SELECT demo_name, server_time_ms FROM recognized_frags WHERE id=?",
        (FRAG_ID,)).fetchone()
    path = dp._projectile_path(demo_name, hero_ms)
    if not dp._usable_projectile(path):
        raise SystemExit("fixture has no usable projectile path")

    frag = fr._load_frag_with_master(FRAG_ID)
    frag["content_hash"] = c.execute(
        "SELECT content_hash FROM recognized_frags WHERE id=?",
        (FRAG_ID,)).fetchone()[0]
    frag["window"] = fr._frag_window(frag)
    win_start = int(frag["window"]["start_ms"])
    win_end = int(frag["window"]["end_ms"])

    launch, impact = path["launch"], path["impact"]
    launch_rel = int(launch["t"]) - win_start
    impact_rel = int(impact["t"]) - win_start

    # the projectile, in shot-relative ms
    # flat (t, x, y, z), the shape camera_paths.sample_track reads
    track = [(int(p[0]) + launch_rel, float(p[1]), float(p[2]), float(p[3]))
             for p in path["points"]]

    map_name = str(frag.get("map") or "")
    fpv_pos = _v(launch["pos"])            # the shooter's muzzle == the eye

    # FPV aim comes from the rocket's own launch vector, which IS where the
    # player was pointing at the instant of the shot. The cached view
    # timeseries was tried and rejected: it starts 375 ms after this launch
    # and this frag is a FLICK_SHOT, so its nearest sample reads yaw -91.9
    # against the shot's actual -49.5. Aiming the FPV endpoint 42 degrees
    # off the rocket put the subject behind the camera and made subject
    # retention meaningless.
    fpv_ang = camera_paths.look_at_angles(tuple(fpv_pos),
                                          tuple(_v(impact["pos"])))

    # SIDE: a locked view abeam the flight line, framing the impact. Fixed
    # position AND fixed angles, so the endpoint is identical for every
    # variant -- a look-at evaluated at arrival time would not be.
    flight = _v(impact["pos"]) - fpv_pos
    fdir = _unit(flight)
    lateral = _unit(np.cross(fdir, np.array([0.0, 0.0, 1.0])))
    mid = fpv_pos + flight * 0.5
    side_pos = mid + lateral * SIDE_OFFSET_U + np.array([0.0, 0.0, SIDE_HEIGHT_U])
    side_ang = camera_paths.look_at_angles(tuple(side_pos), tuple(_v(impact["pos"])))

    # the handoff's spatial control points: a gentle bow off the chord so the
    # move reads as a camera rather than a dolly. Computed once, in space.
    chord = side_pos - fpv_pos
    bow_dir = _unit(np.cross(_unit(chord), np.array([0.0, 0.0, 1.0])))
    bow = float(np.linalg.norm(chord)) * BOW_FRACTION
    arc = []
    for i in range(ARC_POINTS + 1):
        u = i / ARC_POINTS
        pos = fpv_pos + chord * u + bow_dir * (bow * math.sin(math.pi * u))
        ang = (fpv_ang[0] + (side_ang[0] - fpv_ang[0]) * u,
               fpv_ang[1] + _ang_delta(fpv_ang[1], side_ang[1]) * u,
               0.0)
        arc.append((u, pos, ang))

    # NO pre-adjustment. The corridor is screened clean at the compiler's
    # own 8 u clearance before it is chosen, so there is nothing to repair.
    # Pushing points "to safety" first was tried and made things worse: it
    # moved control points OFF the one verified-clear line and back into the
    # geometry the screen had just avoided.
    tracer = None
    try:
        tracer = camera_paths.bsp_tracer(map_name or "quarantine")
    except Exception:
        tracer = None
    pushed = 0

    return {"demo_name": demo_name, "hero_ms": hero_ms, "frag": frag,
            "win_start": win_start, "win_end": win_end,
            "total_ms": win_end - win_start,
            "launch_rel": launch_rel, "impact_rel": impact_rel,
            "flight_ms": impact_rel - launch_rel,
            "track": track, "path": path,
            "fpv_pos": fpv_pos, "fpv_ang": fpv_ang,
            "side_pos": side_pos, "side_ang": side_ang, "arc": arc,
            "tracer": tracer, "control_points_pushed": pushed,
            "map_name": map_name, "fov": 100.0}


def keyframes_for(scene: dict, duration_ms: int) -> list[dict]:
    """The same points in space; only the clock changes."""
    start = scene["launch_rel"]
    fov = scene["fov"]
    kfs = [{"t_ms": 0.0, "pos": tuple(scene["fpv_pos"]),
            "angles": tuple(scene["fpv_ang"]), "fov": fov}]
    for u, pos, ang in scene["arc"]:
        kfs.append({"t_ms": float(start + u * duration_ms), "pos": tuple(pos),
                    "angles": tuple(ang), "fov": fov})
    kfs.append({"t_ms": float(scene["total_ms"]), "pos": tuple(scene["side_pos"]),
                "angles": tuple(scene["side_ang"]), "fov": fov})
    return kfs


# ── measurement from the compiled camera ────────────────────────────────────

def _pose_at(dense: list[dict], t_ms: float):
    """The camera pose at an exact instant, linearly between samples.

    The handoff boundaries almost never coincide with a camera point. Using
    the nearest ones instead would measure a different fraction of the same
    curve for every duration, which reads as the path changing when it has
    not.
    """
    if not dense:
        return None
    if t_ms <= dense[0]["t_ms"]:
        return dict(dense[0])
    if t_ms >= dense[-1]["t_ms"]:
        return dict(dense[-1])
    for x, y in zip(dense, dense[1:]):
        if x["t_ms"] <= t_ms <= y["t_ms"]:
            span = y["t_ms"] - x["t_ms"]
            u = 0.0 if span <= 0 else (t_ms - x["t_ms"]) / span
            pos = tuple(_v(x["pos"]) + (_v(y["pos"]) - _v(x["pos"])) * u)
            ang = tuple(x["angles"][i] + _ang_delta(x["angles"][i],
                                                    y["angles"][i]) * u
                        for i in range(3))
            fov = x.get("fov", 0) + (y.get("fov", 0) - x.get("fov", 0)) * u
            return {"t_ms": t_ms, "pos": pos, "angles": ang, "fov": fov}
    return None



def measure(scene: dict, dense: list[dict], duration_ms: int) -> dict:
    """The motion envelope, read off the samples the engine will play."""
    start, end = scene["launch_rel"], scene["launch_rel"] + duration_ms
    inside = [k for k in dense if start < k["t_ms"] < end]
    a, b = _pose_at(dense, start), _pose_at(dense, end)
    if a is None or b is None:
        return {"error": "handoff falls outside the compiled path"}
    seg = [a] + inside + [b]
    if len(seg) < 2:
        return {"samples_in_handoff": len(seg), "error": "too few samples"}

    pos = [_v(k["pos"]) for k in seg]
    ang = [k["angles"] for k in seg]
    dts = [(b["t_ms"] - a["t_ms"]) / 1000.0 for a, b in zip(seg, seg[1:])]
    steps = [float(np.linalg.norm(b - a)) for a, b in zip(pos, pos[1:])]
    path_len = sum(steps)
    translation = float(np.linalg.norm(pos[-1] - pos[0]))

    def ang_step(a, b):
        dy = _ang_delta(a[1], b[1])
        dp = _ang_delta(a[0], b[0])
        return math.hypot(dy, dp)

    asteps = [ang_step(a, b) for a, b in zip(ang, ang[1:])]
    ang_total = sum(asteps)
    ang_net = ang_step(ang[0], ang[-1])

    vel = [s / dt for s, dt in zip(steps, dts) if dt > 0]
    avel = [s / dt for s, dt in zip(asteps, dts) if dt > 0]
    accel = [abs(b - a) / dt for a, b, dt in zip(vel, vel[1:], dts[1:]) if dt > 0]

    # subject on screen: where the projectile sits in the frame, 0..1 from
    # centre, at each sample. > 0.5 is outside a 4:3-ish frame edge.
    def screen(cam_pos, cam_ang, target, fov_deg):
        pitch, yaw = math.radians(cam_ang[0]), math.radians(cam_ang[1])
        fwd = np.array([math.cos(pitch) * math.cos(yaw),
                        math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
        right = _unit(np.cross(fwd, np.array([0.0, 0.0, 1.0])))
        up = np.cross(right, fwd)
        d = _v(target) - _v(cam_pos)
        fz = float(np.dot(d, fwd))
        if fz <= 1.0:
            return None
        half = math.tan(math.radians(fov_deg) / 2.0)
        return (float(np.dot(d, right)) / (fz * half),
                float(np.dot(d, up)) / (fz * half * 0.75))

    scr, retained = [], 0
    for k in seg:
        tgt = camera_paths.sample_track(scene["track"], k["t_ms"])
        s = screen(k["pos"], k["angles"], tgt, k.get("fov", scene["fov"]))
        if s is not None:
            scr.append(s)
            if abs(s[0]) <= 1.0 and abs(s[1]) <= 1.0:
                retained += 1
    scr_disp = (float(np.hypot(scr[-1][0] - scr[0][0], scr[-1][1] - scr[0][1]))
                if len(scr) >= 2 else None)
    scr_vel = (scr_disp / (duration_ms / 1000.0)) if scr_disp is not None else None

    return {
        "camera_points_in_handoff": len(inside) + 2,
        "interior_samples": len(inside),
        "translation_u": round(translation, 1),
        "path_length_u": round(path_len, 1),
        "path_over_chord": round(path_len / translation, 3) if translation else None,
        "angular_net_deg": round(ang_net, 1),
        "angular_total_deg": round(ang_total, 1),
        "fov_delta_deg": round(seg[-1].get("fov", 0) - seg[0].get("fov", 0), 2),
        "peak_translational_u_s": round(max(vel), 1) if vel else None,
        "mean_translational_u_s": round(float(np.mean(vel)), 1) if vel else None,
        "peak_angular_deg_s": round(max(avel), 1) if avel else None,
        "peak_accel_u_s2": round(max(accel), 1) if accel else None,
        "smoothness_jerk_proxy": (round(float(np.std(vel)) / float(np.mean(vel)), 4)
                                  if vel and np.mean(vel) > 0 else None),
        "subject_screen_displacement": (round(scr_disp, 3)
                                        if scr_disp is not None else None),
        "subject_screen_velocity_per_s": (round(scr_vel, 3)
                                          if scr_vel is not None else None),
        "subject_retained_fraction": (round(retained / len(scr), 3)
                                      if scr else None),
    }


def event_times(scene: dict, duration_ms: int) -> dict:
    """Raw event timestamps, shot-relative ms. Not a SyncPort schema yet."""
    start = scene["launch_rel"]
    track = scene["track"]
    cam = scene["side_pos"]
    closest_t, closest_d = None, float("inf")
    for t_ms, x, y, z in track:
        d = float(np.linalg.norm(_v((x, y, z)) - cam))
        if d < closest_d:
            closest_t, closest_d = t_ms, d
    return {"FPV_EXIT": start, "SPLINE_START": start,
            "SPLINE_END": start + duration_ms,
            "SIDE_ESTABLISHED": start + duration_ms,
            "SUBJECT_ACQUIRED": start,
            "PROJECTILE_CLOSEST_APPROACH": closest_t,
            "projectile_closest_approach_u": round(closest_d, 1),
            "PROJECTILE_IMPACT": scene["impact_rel"],
            "HERO": scene["impact_rel"],
            "RETURN_START": None, "FPV_REESTABLISHED": None}


# ── capture ─────────────────────────────────────────────────────────────────

def capture(scene: dict, duration_ms: int, out: Path, compile_only: bool) -> dict:
    key = f"caseA{duration_ms:04d}"
    draft = dd._default_draft(FRAG_ID)
    draft["camera"]["mode"] = "FREECAM"
    draft["camera"]["fov"] = scene["fov"]
    demo_path, _ = review_proxy.demo_source(scene["demo_name"])
    plan = dp.build_plan(scene["frag"], draft, demo_path=str(demo_path))

    kfs = keyframes_for(scene, duration_ms)
    covered = dp._cover_window(tuple(kfs), scene["total_ms"])
    plan = dataclasses.replace(plan, keyframes=tuple(covered))

    gamedir = dp.wolfcam_capture.ensure_install() / "wolfcam-ql"
    comp = v2.compile_dense_camera(
        list(covered), base_servertime=scene["win_start"], gamedir=gamedir,
        camera_name=f"prev_{key}", hz=HZ, tracer=scene["tracer"],
        subject_track=scene["track"],
        scene_start_ms=-dp.GUARD_MS,
        scene_end_ms=scene["total_ms"] + dp.GUARD_MS)

    dense = comp.get("final_keyframes") or comp.get("dense_keyframes") or []
    row = {"requested_duration_ms": duration_ms,
           "requested_frames": round(duration_ms / FRAME_MS, 2),
           "compile_status": comp.get("status"),
           "points": comp.get("used_sample_count"),
           "hz_clamped": comp.get("hz_clamped"),
           "effective_hz": comp.get("effective_hz"),
           "cam10_hash": comp.get("cam10_hash"),
           "coverage": comp.get("coverage"),
           "min_clearance_u": comp.get("min_clearance_u"),
           "motion": measure(scene, dense, duration_ms),
           "events": event_times(scene, duration_ms)}
    log(f"[{key}] {comp.get('status')} pts={row['points']} "
        f"clamped={row['hz_clamped']} motion={row['motion'].get('translation_u')}u "
        f"/{row['motion'].get('angular_net_deg')}deg "
        f"peak={row['motion'].get('peak_translational_u_s')}u/s")
    if compile_only:
        return row

    duration_s = scene["total_ms"] / 1000.0
    final = out / f"{key}.visual.mp4"
    tmp = out / f"{key}.tmp.mp4"
    t0 = time.time()
    try:
        dp._real_capture({"preview_key": key}, plan, tmp, final, duration_s)
    except Exception as e:                       # keep the sweep going
        row["capture_error"] = f"{type(e).__name__}: {e}"
        log(f"[{key}] CAPTURE FAILED {row['capture_error']}")
        return row
    raw = dp.PREVIEW_DIR / f"{key}.raw.avi"
    kept = out / f"{key}.raw.avi"
    if raw.exists():
        raw.replace(kept)
    if kept.exists():
        p = subprocess.run(
            [str(FFMPEG).replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
             "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=nb_read_frames,r_frame_rate",
             "-of", "csv=p=0", str(kept)], capture_output=True, text=True)
        row["delivered"] = p.stdout.strip()
        row["raw"] = str(kept)
    row["capture_s"] = round(time.time() - t0, 1)
    log(f"[{key}] captured {row.get('capture_s')}s delivered={row.get('delivered')}")
    return row


def main(write_reference: bool = False) -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        REPO / "output/demo_v2/_case_a")
    compile_only = "--compile-only" in sys.argv
    out.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    log(f"fixture frag {FRAG_ID}: flight {scene['flight_ms']}ms "
        f"launch_rel={scene['launch_rel']} impact_rel={scene['impact_rel']} "
        f"window={scene['total_ms']}ms")
    log(f"FPV {np.round(scene['fpv_pos'],1)} ang {np.round(scene['fpv_ang'],1)}")
    log(f"SIDE {np.round(scene['side_pos'],1)} ang {np.round(scene['side_ang'],1)}")
    chord = float(np.linalg.norm(scene["side_pos"] - scene["fpv_pos"]))
    log(f"chord {chord:.0f}u  arc points {len(scene['arc'])}  hz {HZ}  "
        f"map {scene['map_name'] or '(from cache)'}  "
        f"control points pushed clear of geometry: {scene['control_points_pushed']}")

    rows = [capture(scene, d, out, compile_only) for d in LADDER_MS]
    result = {"fixture": {"frag_id": FRAG_ID, "flight_ms": scene["flight_ms"],
                          "flight_u": round(float(np.linalg.norm(
                              _v(scene["path"]["impact"]["pos"])
                              - _v(scene["path"]["launch"]["pos"]))), 1),
                          "chord_u": round(chord, 1),
                          "window_ms": scene["total_ms"]},
              "invariants": {"hz": HZ, "arc_control_points": len(scene["arc"]),
                             "same_spatial_path": True,
                             "cam10_usable_points": cw.CAM10_USABLE_POINTS},
              "ladder": rows}
    (out / "case_a.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _dest = REFERENCE if write_reference else SCRATCH
    _dest.parent.mkdir(parents=True, exist_ok=True)
    _dest.write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log(f"DONE {out/'case_a.json'}")


if __name__ == "__main__":
    import sys as _sys
    main(write_reference="--write-reference" in _sys.argv)
