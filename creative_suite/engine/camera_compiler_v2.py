"""Camera V2 — dense sampling, decoupled look-at, and collision-checked
execution paths, compiled onto the runtime-proven FREECAM_SAMPLED backend.

Context (2026-09-01 camera-pipeline-recovery, continued): the 9-keyframe
canary proved the camera CAN move. It did not prove smooth cinematography —
9 samples across 4000ms means one `freecamsetpos` roughly every 445ms, a
visible step. This module is the production compiler that sits between
SceneRecipeV2 camera intent and the backend:

    SceneRecipe camera intent (sparse authored keyframes, or an analytic
    generator call from camera_paths.py)
        -> resample_dense()            Catmull-Rom position / slerp-lite
                                        angle / linear FOV, at a chosen Hz
        -> retarget_lookat() [optional] decouple orientation from position:
                                        camera follows one track, looks at
                                        a DIFFERENT (possibly moving) target
        -> collision_check_dense()     runs the EXISTING camera_paths
                                        validate_path/adjust_path machinery
                                        on the DENSE curve, not just the
                                        sparse authored points, so a fast
                                        camera cannot tunnel through a wall
                                        between two authored keyframes
        -> compile_dense_camera()      cam10_writer backend: .cam10 archival
                                        file + FREECAM_SAMPLED execution cfg

Backend naming (do not remove FREECAM_SAMPLED once NATIVE_CAM10 exists —
see cam10_runtime_contract.md "Known engine bug" and the 2026-09-01
camera-v2 directive section 2): this module always compiles to
BACKEND_FREECAM_SAMPLED. A future NATIVE_CAM10_EXPERIMENTAL backend would
consume the SAME dense, collision-checked keyframe list — the resampling
and collision logic here is backend-agnostic by construction.

Analytic generators (orbit/chase/side_track/projectile_follow/top_down in
camera_paths.py) are already continuous math — increasing their own
``steps`` parameter directly gives arbitrarily dense, keyframe-exact
sampling with NO spline-fitting needed. resample_dense() exists for the
other case: an already-fixed, possibly sparse keyframe list (human-authored
via director_session.py's viewpos marks, or a shot_plan loaded from disk)
that needs to become a smooth dense curve.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

from creative_suite.engine import cam10_writer
from creative_suite.engine.camera_paths import (Track, Vec3, _kf, _aim_point,
                                                adjust_path, look_at_angles,
                                                sample_track, validate_path)

BACKEND_FREECAM_SAMPLED = "FREECAM_SAMPLED"

# Candidate sampling rates (directive section 4) -- ASPIRATIONAL, capped by
# the hard budget below. Measured 2026-09-01: a naive 60Hz/4s shot (241
# freecamsetpos + 1 quit = 242 "at" commands) reproducibly hung capture --
# confirmed root cause, not a guess (qconsole.log showed "too many at
# commands" exactly 114 times = 242 - 128, matching MAX_AT_COMMANDS below
# exactly). Every "at" command (freecamsetpos, video, stopvideo, quit,
# freeze, timescale, fov ramps) shares ONE fixed-size sorted array
# (cg_local.h:923 `#define MAX_AT_COMMANDS 128`; insert logic at
# cg_consolecmds.c:6748-6781 `CG_AddAtFtimeCommand` -- once full, any NEW
# command whose time is later than every queued command is silently
# rejected, which is exactly why our LATER-scheduled stopvideo/quit lines
# vanished while earlier freecamsetpos samples queued fine). This is a
# real, fixed engine ceiling -- not tunable via a cvar -- so
# compile_dense_camera() clamps effective sample count to stay under it
# (see MAX_AT_COMMAND_BUDGET) rather than silently producing an
# uncapturable cfg.
PREVIEW_HZ = 30.0
CINEMATIC_HZ = 60.0
MASTER_HZ = 120.0

# Hard ceiling from cg_local.h:923. Reserve slots for the lifecycle
# commands every capture already needs (video/stopvideo/quit) plus a
# margin for Timeline steps (freeze/timescale/fov) a caller may also emit
# into the SAME cfg -- see RESERVED_COMMAND_SLOTS.
MAX_AT_COMMANDS = 128
RESERVED_COMMAND_SLOTS = 8
MAX_CAMERA_SAMPLES = MAX_AT_COMMANDS - RESERVED_COMMAND_SLOTS

# Collision response outcomes (directive section 11).
VALID = "VALID"
PUSHED_OUT = "PUSHED_OUT"
SHORTENED = "SHORTENED"
REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Dense resampling — Catmull-Rom on position, shortest-path-angle lerp on
# angles, linear on FOV. Deterministic: same input/hz always reproduces the
# same output (no RNG, no wall-clock).
# ---------------------------------------------------------------------------

def _catmull_rom(p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, u: float) -> Vec3:
    """Standard (uniform) Catmull-Rom — a TRUE interpolating spline: it
    passes through p1 (u=0) and p2 (u=1) exactly, unlike cg_camera.c's
    posBezier (a non-interpolating uniform B-spline, per the runtime-
    contract research this session). Used only in Python; never sent to
    the engine as a spline TYPE — the engine only ever receives discrete
    freecamsetpos samples that WE already interpolated."""
    u2, u3 = u * u, u * u * u

    def axis(a, b, c, d):
        return 0.5 * ((2 * b) + (-a + c) * u
                      + (2 * a - 5 * b + 4 * c - d) * u2
                      + (-a + 3 * b - 3 * c + d) * u3)
    return (axis(p0[0], p1[0], p2[0], p3[0]),
            axis(p0[1], p1[1], p2[1], p3[1]),
            axis(p0[2], p1[2], p2[2], p3[2]))


def _angle_lerp(a: float, b: float, u: float) -> float:
    """Shortest-path degree interpolation (handles the 359->1 wraparound)."""
    d = ((b - a + 180.0) % 360.0) - 180.0
    return a + d * u


def resample_dense(keyframes: list[dict], hz: float) -> list[dict]:
    """Turn a (possibly sparse) keyframe list into an evenly-sampled dense
    curve at ``hz`` samples/second. Position: Catmull-Rom through the
    authored points (clamped end tangents by duplicating the first/last
    point — standard boundary handling). Angles: shortest-path lerp.
    FOV: linear lerp. The FIRST and LAST authored keyframes are always
    exactly reproduced in the output (interpolation parameter u=0/1 at the
    segment boundaries), so authored keyframes are always visited, per the
    directive's "authored keyframes are visited" requirement.
    """
    if len(keyframes) < 2:
        return list(keyframes)
    kfs = sorted(keyframes, key=lambda k: k["t_ms"])
    t0, t1 = kfs[0]["t_ms"], kfs[-1]["t_ms"]
    duration_ms = t1 - t0
    if duration_ms <= 0:
        return list(kfs)
    step_ms = 1000.0 / hz
    n_samples = max(2, int(round(duration_ms / step_ms)) + 1)

    pos_pad = [kfs[0]["pos"]] + [k["pos"] for k in kfs] + [kfs[-1]["pos"]]

    out = []
    for s in range(n_samples):
        t = t0 + duration_ms * s / (n_samples - 1)
        # find the authored segment [i, i+1] containing t
        i = 0
        while i < len(kfs) - 2 and kfs[i + 1]["t_ms"] < t:
            i += 1
        seg_t0, seg_t1 = kfs[i]["t_ms"], kfs[i + 1]["t_ms"]
        u = 0.0 if seg_t1 == seg_t0 else (t - seg_t0) / (seg_t1 - seg_t0)
        p0, p1, p2, p3 = pos_pad[i], pos_pad[i + 1], pos_pad[i + 2], pos_pad[i + 3]
        pos = _catmull_rom(p0, p1, p2, p3, u)
        a0, a1 = kfs[i]["angles"], kfs[i + 1]["angles"]
        angles = tuple(_angle_lerp(a0[k], a1[k], u) for k in range(3))
        fov = kfs[i]["fov"] + (kfs[i + 1]["fov"] - kfs[i]["fov"]) * u
        out.append(_kf(t, pos, angles, fov))
    # exact endpoints (Catmull-Rom already reproduces these at u=0/1, but
    # pin explicitly so downstream code never sees float drift on the
    # authored boundary values).
    out[0] = dict(kfs[0])
    out[-1] = dict(kfs[-1])
    return out


def retarget_lookat(position_keyframes: list[dict], target_track: Track,
                    damping: float = 0.0, max_angular_speed_deg_s: float = 0.0
                    ) -> list[dict]:
    """Decouple orientation from position (directive section 7/8): keep
    each sample's ``pos``/``fov``, but recompute ``angles`` to aim at
    ``target_track`` sampled AT THAT SAMPLE'S TIME — the target can be
    moving independently of the camera (a projectile, a victim, a combat
    centroid track already computed by the caller).

    ``damping`` in [0,1): exponential smoothing of the raw look-at angle
    against the previous sample's angle (0 = no smoothing, matches the
    raw target exactly; closer to 1 = heavier lag). ``max_angular_speed_deg_s``
    caps the yaw/pitch rate of change per second (0 = unbounded) — both
    knobs affect PRESENTATION only; the underlying target_track coordinates
    (and thus the recipe's semantic truth) are never altered.
    """
    out = []
    prev_angles = None
    prev_t = None
    for kf in position_keyframes:
        target_pos = sample_track(target_track, kf["t_ms"])
        raw = look_at_angles(kf["pos"], _aim_point(target_pos))
        angles = raw
        if prev_angles is not None:
            if damping > 0.0:
                angles = tuple(_angle_lerp(prev_angles[i], raw[i], 1.0 - damping)
                              for i in range(3))
            if max_angular_speed_deg_s > 0.0 and prev_t is not None:
                dt_s = max(1e-3, (kf["t_ms"] - prev_t) / 1000.0)
                cap = max_angular_speed_deg_s * dt_s
                angles = tuple(
                    prev_angles[i] + max(-cap, min(cap, _angle_lerp(
                        prev_angles[i], angles[i], 1.0) - prev_angles[i]))
                    for i in range(3))
        out.append(_kf(kf["t_ms"], kf["pos"], angles, kf["fov"]))
        prev_angles = angles
        prev_t = kf["t_ms"]
    return out


# ---------------------------------------------------------------------------
# Collision on the DENSE path (directive section 10/11) — reuses the
# existing validate_path/adjust_path machinery unchanged; the only change
# is WHAT gets passed to it (the dense curve, not the sparse authored
# points), so short segments between adjacent samples are what gets
# checked — a fast camera cannot tunnel between two 16ms-apart samples
# without the segment check catching it.
# ---------------------------------------------------------------------------

def collision_check_dense(tracer, dense_keyframes: list[dict],
                          subject_track: Track | None = None,
                          min_clearance_u: float = 8.0,
                          max_iterations: int = 25) -> dict:
    """Classify the outcome as VALID / PUSHED_OUT / SHORTENED / REJECTED.

    - VALID: the dense path is already clear.
    - PUSHED_OUT: adjust_path() (pull-toward-subject repair) fully cleared
      it within max_iterations.
    - SHORTENED: repair could not fully clear it, but a clean PREFIX of the
      path (from t0 up to the first still-offending sample) is usable and
      long enough (>= 2 samples) to keep.
    - REJECTED: even the prefix is unusable (offense at/near the very
      first sample, or fewer than 2 clean samples survive).

    Returns {"status", "keyframes" (the ones to actually use),
    "min_clearance_u" (float or None), "report" (raw validate_path/
    adjust_path report), "original_count", "used_count"}.
    """
    if tracer is None or not dense_keyframes:
        ok, rep = validate_path(tracer, dense_keyframes)
        return {"status": VALID, "keyframes": dense_keyframes,
                "min_clearance_u": None, "report": rep,
                "original_count": len(dense_keyframes),
                "used_count": len(dense_keyframes)}

    ok, rep = validate_path(tracer, dense_keyframes)
    if ok:
        clearance = _min_clearance(tracer, dense_keyframes, min_clearance_u)
        return {"status": VALID, "keyframes": dense_keyframes,
                "min_clearance_u": clearance, "report": rep,
                "original_count": len(dense_keyframes),
                "used_count": len(dense_keyframes)}

    fixed_ok, fixed_kfs, fixed_rep = adjust_path(
        tracer, dense_keyframes, subject_track, max_iterations=max_iterations)
    if fixed_ok:
        clearance = _min_clearance(tracer, fixed_kfs, min_clearance_u)
        return {"status": PUSHED_OUT, "keyframes": fixed_kfs,
                "min_clearance_u": clearance, "report": fixed_rep,
                "original_count": len(dense_keyframes),
                "used_count": len(fixed_kfs)}

    # Could not fully clear — try a clean prefix.
    offenders = sorted(set(fixed_rep["solid_keyframes"])
                       | {b for _a, b in fixed_rep["blocked_segments"]})
    first_bad = offenders[0] if offenders else 0
    if first_bad < 2:
        return {"status": REJECTED, "keyframes": [],
                "min_clearance_u": None, "report": fixed_rep,
                "original_count": len(dense_keyframes), "used_count": 0}
    prefix = fixed_kfs[:first_bad]
    clearance = _min_clearance(tracer, prefix, min_clearance_u)
    return {"status": SHORTENED, "keyframes": prefix,
            "min_clearance_u": clearance, "report": fixed_rep,
            "original_count": len(dense_keyframes), "used_count": len(prefix)}


def _min_clearance(tracer, keyframes: list[dict], probe_u: float) -> float:
    """Approximate minimum wall clearance across all samples: probe 6
    axis-aligned rays of length probe_u from each sample; the shortest ray
    that hits something (binary-searched to ~1u) is that sample's
    clearance. Returns the minimum across the whole path (float('inf') if
    nothing hit within probe_u anywhere)."""
    from creative_suite.engine.camera_paths import _CLEARANCE_PROBES
    best = math.inf
    for kf in keyframes:
        p = kf["pos"]
        for d in _CLEARANCE_PROBES:
            lo, hi = 0.0, probe_u
            if not tracer.line_blocked(p, (p[0] + d[0], p[1] + d[1], p[2] + d[2])):
                continue
            for _ in range(6):
                mid = (lo + hi) / 2
                scale = mid / probe_u
                test = (p[0] + d[0] * scale, p[1] + d[1] * scale, p[2] + d[2] * scale)
                if tracer.line_blocked(p, test):
                    hi = mid
                else:
                    lo = mid
            best = min(best, lo)
    return best


# ---------------------------------------------------------------------------
# Compilation entrypoint — backend-agnostic dense/collision-checked
# keyframes, compiled today onto FREECAM_SAMPLED.
# ---------------------------------------------------------------------------

def _clamp_hz_to_budget(keyframes: list[dict], hz: float,
                        max_samples: int = MAX_CAMERA_SAMPLES
                        ) -> tuple[float, bool]:
    """Reduce hz so the resulting sample count fits MAX_CAMERA_SAMPLES.
    Returns (effective_hz, was_clamped). Never raises -- a caller who
    truly needs more samples than the engine's MAX_AT_COMMANDS budget
    allows for a given duration needs the chained-batch re-exec technique
    noted in this module's docstring (not yet implemented), not a bigger
    number here."""
    if len(keyframes) < 2:
        return hz, False
    duration_s = (max(k["t_ms"] for k in keyframes)
                 - min(k["t_ms"] for k in keyframes)) / 1000.0
    if duration_s <= 0:
        return hz, False
    requested_samples = int(round(duration_s * hz)) + 1
    if requested_samples <= max_samples:
        return hz, False
    # solve for the hz that yields exactly max_samples over this duration
    clamped_hz = (max_samples - 1) / duration_s
    return clamped_hz, True


def compile_dense_camera(keyframes: list[dict], base_servertime: int,
                         gamedir: Path, camera_name: str,
                         hz: float = CINEMATIC_HZ, tracer=None,
                         subject_track: Track | None = None,
                         min_clearance_u: float = 8.0) -> dict:
    """Full pipeline: resample -> collision-check -> compile. Returns a
    debug-friendly dict (directive section 12's diagnostic artifact):
    {"backend", "status", "requested_hz", "effective_hz", "hz_clamped",
    "authored_keyframes", "dense_keyframes", "final_keyframes",
    "min_clearance_u", "collision_report", "cam10_path", "cam10_hash",
    "cfg_lines"}. If status is REJECTED, cam10_path/cfg_lines are None —
    caller must not attempt capture.

    ``hz`` is silently-but-visibly clamped (``hz_clamped`` is reported,
    never hidden) so the compiled cfg never exceeds MAX_CAMERA_SAMPLES —
    see the MAX_AT_COMMANDS note above this function. A long/fast shot at
    a high requested Hz gets sparser sampling rather than an uncapturable
    cfg; callers that need both long duration AND high density must split
    the shot across multiple chained capture windows (not yet built).
    """
    effective_hz, clamped = _clamp_hz_to_budget(keyframes, hz)
    dense = resample_dense(keyframes, effective_hz)
    collision = collision_check_dense(tracer, dense, subject_track,
                                      min_clearance_u=min_clearance_u)
    result = {
        "backend": BACKEND_FREECAM_SAMPLED,
        "status": collision["status"],
        "requested_hz": hz,
        "effective_hz": effective_hz,
        "hz_clamped": clamped,
        "authored_keyframes": keyframes,
        "dense_keyframes": dense,
        "final_keyframes": collision["keyframes"],
        "min_clearance_u": collision["min_clearance_u"],
        "collision_report": collision["report"],
        "original_sample_count": collision["original_count"],
        "used_sample_count": collision["used_count"],
        "cam10_path": None, "cam10_hash": None, "cfg_lines": None,
    }
    if collision["status"] == REJECTED or not collision["keyframes"]:
        return result
    compiled = cam10_writer.compile_camera(
        collision["keyframes"], base_servertime, gamedir, camera_name)
    result["cam10_path"] = compiled["path"]
    result["cam10_hash"] = compiled["file_hash"]
    result["cfg_lines"] = compiled["cfg_lines"]
    return result


def projectile_track_from_recognition(path_json: dict, base_t_ms: int = None
                                      ) -> Track:
    """Adapt engine/parser/extract_projectile_paths.py's cached
    recognition_projectile_paths.path JSON ({"points": [[t_rel, x, y, z],
    ...], "launch": {...}, "impact": {...}}) into a camera_paths.Track
    ((t_ms, x, y, z) tuples). ``base_t_ms`` anchors t_rel=0 to an absolute
    demo serverTime; defaults to path_json["launch"]["t"] (flight start),
    matching how the extractor itself anchors the path."""
    if base_t_ms is None:
        base_t_ms = path_json["launch"]["t"]
    return [(base_t_ms + t_rel, x, y, z)
            for t_rel, x, y, z in path_json["points"]]
