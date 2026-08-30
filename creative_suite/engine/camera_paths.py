"""Deterministic camera path construction for the programmable fragmovie system.

Mandate sections 10-14 (camera constructions), 49 (BSP collision validation),
50 (quality metrics), 51 (auto-cinematographer candidate generation).

Every generator is pure math: identical inputs -> byte-identical keyframe
lists.  No RNG anywhere; any jitter must arrive as an explicit seeded param.

Keyframe schema (the single currency of this module):

    {"t_ms": int,                    # demo serverTime, milliseconds
     "pos": (x, y, z),               # world units
     "angles": (pitch, yaw, roll),   # degrees, Q3 convention (+pitch = down)
     "fov": float}                   # horizontal fov degrees

Track inputs are time series ``[(t_ms, x, y, z), ...]`` sorted ascending,
straight from the parser entity stream.

Collision uses ``engine/parser/bsp_geometry.py`` (read-only import).  All
collision entry points take a *tracer* object exposing
``line_blocked(a, b) -> bool`` so tests can inject synthetic geometry;
``bsp_tracer(map_name)`` wraps the real BSP.
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

Vec3 = tuple[float, float, float]
Track = Sequence[tuple[float, float, float, float]]  # (t_ms, x, y, z)

DEFAULT_FOV = 90.0
SUBJECT_EYE_Z = 26.0            # DEFAULT_VIEWHEIGHT — where the camera aims
_MAX_PITCH = 89.0               # avoid gimbal singularity at straight down

# bsp_geometry is owned by another agent; import defensively (read-only).
try:
    from engine.parser import bsp_geometry as _bsp
    _BSP_IMPORT_ERROR: Exception | None = None
except Exception as _e:          # pragma: no cover - environment dependent
    _bsp = None
    _BSP_IMPORT_ERROR = _e


# ── small vector helpers ─────────────────────────────────────────────────────

def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _norm(a: Vec3) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _unit(a: Vec3, fallback: Vec3 = (1.0, 0.0, 0.0)) -> Vec3:
    n = _norm(a)
    if n < 1e-9:
        return fallback
    return (a[0] / n, a[1] / n, a[2] / n)


def look_at_angles(from_pos: Vec3, to_pos: Vec3) -> Vec3:
    """(pitch, yaw, roll) aiming from_pos -> to_pos, Q3 convention.

    Q3 AngleVectors has forward.z = -sin(pitch): positive pitch looks DOWN.
    """
    d = _sub(to_pos, from_pos)
    hyp = math.hypot(d[0], d[1])
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = -math.degrees(math.atan2(d[2], hyp)) if (hyp > 1e-9 or abs(d[2]) > 1e-9) else 0.0
    pitch = max(-_MAX_PITCH, min(_MAX_PITCH, pitch))
    return (pitch, yaw, 0.0)


def sample_track(track: Track, t_ms: float) -> Vec3:
    """Linear interpolation of an entity track at time t_ms (clamped ends)."""
    if not track:
        raise ValueError("empty track")
    if t_ms <= track[0][0]:
        return (track[0][1], track[0][2], track[0][3])
    if t_ms >= track[-1][0]:
        return (track[-1][1], track[-1][2], track[-1][3])
    # linear scan is fine at frag-window sizes (<= a few hundred samples)
    for i in range(1, len(track)):
        if track[i][0] >= t_ms:
            t0, x0, y0, z0 = track[i - 1]
            t1, x1, y1, z1 = track[i]
            if t1 <= t0:
                return (x1, y1, z1)
            f = (t_ms - t0) / (t1 - t0)
            return (x0 + f * (x1 - x0), y0 + f * (y1 - y0), z0 + f * (z1 - z0))
    return (track[-1][1], track[-1][2], track[-1][3])


def track_direction(track: Track, i: int) -> Vec3:
    """Unit motion direction at sample index i (central difference)."""
    j0 = max(0, i - 1)
    j1 = min(len(track) - 1, i + 1)
    if j1 == j0:
        return (1.0, 0.0, 0.0)
    a, b = track[j0], track[j1]
    return _unit((b[1] - a[1], b[2] - a[2], b[3] - a[3]))


def _kf(t_ms: float, pos: Vec3, angles: Vec3, fov: float) -> dict:
    return {"t_ms": int(round(t_ms)), "pos": tuple(pos),
            "angles": tuple(angles), "fov": float(fov)}


def _resolve_center(center_fn, t_ms: float) -> Vec3:
    if callable(center_fn):
        return tuple(center_fn(t_ms))
    return tuple(center_fn)


def _aim_point(subject_pos: Vec3) -> Vec3:
    return (subject_pos[0], subject_pos[1], subject_pos[2] + SUBJECT_EYE_Z)


# ── path generators (mandate 10-14) ─────────────────────────────────────────

def orbit(center_fn, radius: float, height: float, arc_deg: float,
          duration_ms: float, t0_ms: float = 0.0, start_deg: float = 0.0,
          fov: float = DEFAULT_FOV, steps: int | None = None) -> list[dict]:
    """Horizontal orbit around a (possibly moving) center, looking inward."""
    if steps is None:
        steps = max(8, int(abs(arc_deg) / 10.0))
    kfs = []
    for k in range(steps + 1):
        u = k / steps
        t = t0_ms + u * duration_ms
        c = _resolve_center(center_fn, t)
        az = math.radians(start_deg + u * arc_deg)
        pos = (c[0] + radius * math.cos(az), c[1] + radius * math.sin(az),
               c[2] + height)
        kfs.append(_kf(t, pos, look_at_angles(pos, _aim_point(c)), fov))
    return kfs


def vertical_orbit(center_fn, radius: float, arc_deg: float,
                   duration_ms: float, t0_ms: float = 0.0,
                   azimuth_deg: float = 0.0, start_elev_deg: float = 0.0,
                   fov: float = DEFAULT_FOV, steps: int | None = None) -> list[dict]:
    """Orbit in a vertical plane: sweeps elevation at a fixed azimuth."""
    if steps is None:
        steps = max(8, int(abs(arc_deg) / 10.0))
    az = math.radians(azimuth_deg)
    dxy = (math.cos(az), math.sin(az))
    kfs = []
    for k in range(steps + 1):
        u = k / steps
        t = t0_ms + u * duration_ms
        c = _resolve_center(center_fn, t)
        el = math.radians(start_elev_deg + u * arc_deg)
        el = max(math.radians(-_MAX_PITCH), min(math.radians(_MAX_PITCH), el))
        r_xy = radius * math.cos(el)
        pos = (c[0] + r_xy * dxy[0], c[1] + r_xy * dxy[1],
               c[2] + radius * math.sin(el))
        kfs.append(_kf(t, pos, look_at_angles(pos, _aim_point(c)), fov))
    return kfs


def follow_entity(track: Track, offset_vec: Vec3, look_at: bool = True,
                  fov: float = DEFAULT_FOV) -> list[dict]:
    """Camera rigidly offset from the entity; aims at the entity (or forward)."""
    kfs = []
    for i, (t, x, y, z) in enumerate(track):
        p = (x, y, z)
        pos = _add(p, tuple(offset_vec))
        if look_at:
            ang = look_at_angles(pos, _aim_point(p))
        else:
            d = track_direction(track, i)
            ang = look_at_angles(pos, _add(pos, _scale(d, 100.0)))
        kfs.append(_kf(t, pos, ang, fov))
    return kfs


def side_track(track: Track, lateral_offset: float, height: float = 24.0,
               look_at: bool = True, fov: float = DEFAULT_FOV) -> list[dict]:
    """Dolly alongside the entity, perpendicular to its motion in the XY plane."""
    kfs = []
    for i, (t, x, y, z) in enumerate(track):
        p = (x, y, z)
        d = track_direction(track, i)
        right = _unit((d[1], -d[0], 0.0), fallback=(0.0, -1.0, 0.0))
        pos = (p[0] + right[0] * lateral_offset,
               p[1] + right[1] * lateral_offset, p[2] + height)
        ang = look_at_angles(pos, _aim_point(p)) if look_at else \
            look_at_angles(pos, _add(pos, _scale(d, 100.0)))
        kfs.append(_kf(t, pos, ang, fov))
    return kfs


def chase(track: Track, behind_dist: float, up: float = 32.0,
          fov: float = DEFAULT_FOV) -> list[dict]:
    """Trail the entity along its own motion direction, looking at it."""
    kfs = []
    for i, (t, x, y, z) in enumerate(track):
        p = (x, y, z)
        d = track_direction(track, i)
        pos = (p[0] - d[0] * behind_dist, p[1] - d[1] * behind_dist,
               p[2] - d[2] * behind_dist + up)
        kfs.append(_kf(t, pos, look_at_angles(pos, _aim_point(p)), fov))
    return kfs


def top_down(center: Vec3, height: float, duration_ms: float,
             t0_ms: float = 0.0, fov: float = DEFAULT_FOV,
             steps: int = 8) -> list[dict]:
    """Static overhead shot looking straight down (pitch clamped to 89)."""
    pos = (center[0], center[1], center[2] + height)
    kfs = []
    for k in range(steps + 1):
        t = t0_ms + duration_ms * k / steps
        kfs.append(_kf(t, pos, (_MAX_PITCH, 0.0, 0.0), fov))
    return kfs


def projectile_follow(projectile_track: Track, trail_dist: float,
                      fov: float = DEFAULT_FOV) -> list[dict]:
    """Ride behind a projectile, looking along its flight direction."""
    kfs = []
    for i, (t, x, y, z) in enumerate(projectile_track):
        p = (x, y, z)
        d = track_direction(projectile_track, i)
        pos = (p[0] - d[0] * trail_dist, p[1] - d[1] * trail_dist,
               p[2] - d[2] * trail_dist)
        kfs.append(_kf(t, pos, look_at_angles(pos, p), fov))
    return kfs


def bullet_time_arc(impact_point: Vec3, start_angles: Vec3, arc_deg: float,
                    radius: float = 200.0, height: float = 40.0,
                    duration_ms: float = 800.0, t0_ms: float = 0.0,
                    fov: float = DEFAULT_FOV, steps: int | None = None) -> list[dict]:
    """Matrix-style arc around an impact point.

    Starts behind the given view direction (so the first frame matches what
    the POV was seeing) and sweeps arc_deg around the impact.
    """
    start_az = start_angles[1] + 180.0   # camera opposite the view direction
    return orbit(impact_point, radius, height, arc_deg, duration_ms,
                 t0_ms=t0_ms, start_deg=start_az, fov=fov, steps=steps)


def reverse_track(keyframes: list[dict]) -> list[dict]:
    """Time-reverse a keyframe path (POST-PRODUCTION helper only).

    Reverse playback of the demo is NOT a wolfcam feature; a reversed path
    is only meaningful applied to already-captured frames.  Timestamps are
    remapped so the reversed path spans the same [t0, t1] window.
    """
    if not keyframes:
        return []
    t0 = keyframes[0]["t_ms"]
    t1 = keyframes[-1]["t_ms"]
    out = []
    for kf in reversed(keyframes):
        out.append(_kf(t0 + (t1 - kf["t_ms"]), kf["pos"], kf["angles"],
                       kf["fov"]))
    return out


# ── collision validation (mandate 49) ────────────────────────────────────────

class BspTracer:
    """Adapter: BspMap -> line_blocked(a, b).  Point-in-solid uses a tiny
    vertical epsilon segment (a degenerate segment inside a brush clips as
    blocked in the slab test)."""

    def __init__(self, bsp_map):
        self.map = bsp_map

    def line_blocked(self, a: Vec3, b: Vec3) -> bool:
        return _bsp.line_blocked(self.map, a, b)


def bsp_tracer(map_name: str, pk3_path: str | None = None) -> BspTracer:
    """Load a real map into a tracer.  Raises if bsp_geometry is unavailable."""
    if _bsp is None:
        raise RuntimeError(f"bsp_geometry unavailable: {_BSP_IMPORT_ERROR}")
    return BspTracer(_bsp.load_map(map_name, pk3_path))


def point_in_open_space(tracer, pos: Vec3) -> bool:
    eps = (pos[0], pos[1], pos[2] + 0.25)
    return not tracer.line_blocked(pos, eps)


def validate_path(tracer, keyframes: list[dict]) -> tuple[bool, dict]:
    """Check every keyframe is in open space and every segment unobstructed.

    Returns (ok, report).  report = {"solid_keyframes": [idx], "blocked_segments":
    [(i, i+1)], "checked": n}.  tracer=None -> vacuous pass, flagged.
    """
    report: dict = {"solid_keyframes": [], "blocked_segments": [],
                    "checked": len(keyframes), "tracer": tracer is not None}
    if tracer is None or not keyframes:
        return (bool(keyframes) or True, report)
    for i, kf in enumerate(keyframes):
        if not point_in_open_space(tracer, kf["pos"]):
            report["solid_keyframes"].append(i)
    for i in range(len(keyframes) - 1):
        if tracer.line_blocked(keyframes[i]["pos"], keyframes[i + 1]["pos"]):
            report["blocked_segments"].append((i, i + 1))
    ok = not report["solid_keyframes"] and not report["blocked_segments"]
    return ok, report


def adjust_path(tracer, keyframes: list[dict], subject_track: Track | None,
                max_iterations: int = 25,
                pull_fraction: float = 0.12) -> tuple[bool, list[dict], dict]:
    """Pull offending keyframes toward the subject until the path clears.

    Deterministic bounded repair: each iteration moves every keyframe that is
    in solid, or borders a blocked segment, ``pull_fraction`` of the way
    toward the subject position at that keyframe's time (subject positions
    are what the camera is filming — by construction they sit in open space).
    Angles are recomputed to keep aiming at the original target point.

    Returns (ok, adjusted_keyframes, report).
    """
    kfs = [dict(kf) for kf in keyframes]
    if tracer is None or not kfs:
        ok, rep = validate_path(tracer, kfs)
        rep["iterations"] = 0
        return ok, kfs, rep

    def target_for(kf: dict) -> Vec3:
        if subject_track:
            return _aim_point(sample_track(subject_track, kf["t_ms"]))
        # fallback: path centroid
        n = len(kfs)
        return (sum(k["pos"][0] for k in kfs) / n,
                sum(k["pos"][1] for k in kfs) / n,
                sum(k["pos"][2] for k in kfs) / n)

    iterations = 0
    for iterations in range(1, max_iterations + 1):
        ok, rep = validate_path(tracer, kfs)
        if ok:
            rep["iterations"] = iterations - 1
            return True, kfs, rep
        offenders = set(rep["solid_keyframes"])
        for a, b in rep["blocked_segments"]:
            offenders.add(a)
            offenders.add(b)
        for i in sorted(offenders):
            kf = kfs[i]
            tgt = target_for(kf)
            new_pos = (kf["pos"][0] + (tgt[0] - kf["pos"][0]) * pull_fraction,
                       kf["pos"][1] + (tgt[1] - kf["pos"][1]) * pull_fraction,
                       kf["pos"][2] + (tgt[2] - kf["pos"][2]) * pull_fraction)
            kfs[i] = _kf(kf["t_ms"], new_pos,
                         look_at_angles(new_pos, tgt), kf["fov"])
    ok, rep = validate_path(tracer, kfs)
    rep["iterations"] = iterations
    return ok, kfs, rep


# ── quality metrics (mandate 50) ─────────────────────────────────────────────

SCORE_WEIGHTS = {
    "target_visibility": 0.30,
    "mean_distance_fit": 0.15,
    "smoothness": 0.20,
    "clearance": 0.15,
    "impact_visibility": 0.20,
}

_CLEARANCE_PROBES = ((32.0, 0, 0), (-32.0, 0, 0), (0, 32.0, 0),
                     (0, -32.0, 0), (0, 0, 32.0), (0, 0, -32.0))


def _smoothness(keyframes: list[dict]) -> float:
    if len(keyframes) < 3:
        return 1.0
    # positional jerk: second difference magnitude vs mean step length
    seg = [_sub(keyframes[i + 1]["pos"], keyframes[i]["pos"])
           for i in range(len(keyframes) - 1)]
    mean_step = sum(_norm(s) for s in seg) / len(seg)
    if mean_step < 1e-6:
        pos_j = 0.0
    else:
        acc = [_sub(seg[i + 1], seg[i]) for i in range(len(seg) - 1)]
        pos_j = sum(_norm(a) for a in acc) / len(acc) / mean_step
    # angular jerk on yaw/pitch (yaw unwrapped)
    yaws = []
    prev = None
    for kf in keyframes:
        y = kf["angles"][1]
        if prev is not None:
            while y - prev > 180.0:
                y -= 360.0
            while y - prev < -180.0:
                y += 360.0
        yaws.append(y)
        prev = y
    pitches = [kf["angles"][0] for kf in keyframes]
    ang_acc = 0.0
    for series in (yaws, pitches):
        d = [series[i + 1] - series[i] for i in range(len(series) - 1)]
        dd = [abs(d[i + 1] - d[i]) for i in range(len(d) - 1)]
        ang_acc += sum(dd) / len(dd)
    ang_j = ang_acc / 30.0          # 30 deg of angular jerk ~ score halving
    return 1.0 / (1.0 + pos_j + ang_j)


def score_path(tracer, keyframes: list[dict], subject_track: Track | None,
               extras: dict | None = None) -> dict:
    """Component scores in [0,1] + weighted total.  tracer=None gives
    visibility/clearance components a neutral 1.0 (flagged in the result)."""
    extras = extras or {}
    ideal = float(extras.get("ideal_distance", 300.0))
    impact_point = extras.get("impact_point")
    comp = {}

    if not keyframes:
        comp = {k: 0.0 for k in SCORE_WEIGHTS}
        comp["total"] = 0.0
        comp["traced"] = tracer is not None
        return comp

    # target visibility + distance fit
    vis = 0
    dist_fit = 0.0
    for kf in keyframes:
        if subject_track:
            aim = _aim_point(sample_track(subject_track, kf["t_ms"]))
        elif impact_point:
            aim = tuple(impact_point)
        else:
            aim = None
        if aim is None:
            vis += 1
            dist_fit += 1.0
            continue
        if tracer is None or not tracer.line_blocked(kf["pos"], aim):
            vis += 1
        d = _norm(_sub(aim, kf["pos"]))
        dist_fit += 1.0 / (1.0 + abs(d - ideal) / ideal)
    n = len(keyframes)
    comp["target_visibility"] = vis / n
    comp["mean_distance_fit"] = dist_fit / n
    comp["smoothness"] = _smoothness(keyframes)

    # clearance: fraction of open probe rays around each keyframe
    if tracer is None:
        comp["clearance"] = 1.0
    else:
        clear = 0
        total = 0
        for kf in keyframes:
            for probe in _CLEARANCE_PROBES:
                total += 1
                if not tracer.line_blocked(kf["pos"], _add(kf["pos"], probe)):
                    clear += 1
        comp["clearance"] = clear / total if total else 1.0

    # impact visibility
    if impact_point is None:
        comp["impact_visibility"] = comp["target_visibility"]
    elif tracer is None:
        comp["impact_visibility"] = 1.0
    else:
        iv = sum(1 for kf in keyframes
                 if not tracer.line_blocked(kf["pos"], tuple(impact_point)))
        comp["impact_visibility"] = iv / n

    comp["total"] = sum(SCORE_WEIGHTS[k] * comp[k] for k in SCORE_WEIGHTS)
    comp["traced"] = tracer is not None
    return comp


# ── auto-cinematographer (mandate 51) ───────────────────────────────────────

POV_BASELINE_SCORE = 0.60   # the no-op candidate: always valid, never great


def generate_candidates(frag_context: dict) -> list[dict]:
    """Build, validate, adjust, score and rank the standard constructions.

    frag_context keys:
        subject_track   [(t_ms,x,y,z)]  REQUIRED — entity the shot is about
        tracer          line_blocked provider (or None = no collision data)
        impact_point    (x,y,z) optional
        impact_t_ms     int optional
        projectile_track optional [(t_ms,x,y,z)]
        view_angles     (pitch,yaw,roll) at impact, optional (bullet-time)
        ideal_distance  float, default 300
        fov             float, default 90

    Returns candidates sorted by score desc:
        [{name, keyframes, valid, adjusted, score, components,
          post_production, report}]
    """
    track: Track = frag_context["subject_track"]
    if not track:
        raise ValueError("frag_context.subject_track is empty")
    tracer = frag_context.get("tracer")
    fov = float(frag_context.get("fov", DEFAULT_FOV))
    ideal = float(frag_context.get("ideal_distance", 300.0))
    impact_point = frag_context.get("impact_point")
    impact_t = frag_context.get("impact_t_ms", track[-1][0])
    extras = {"ideal_distance": ideal, "impact_point": impact_point}

    t0, t1 = track[0][0], track[-1][0]
    duration = max(1.0, t1 - t0)
    center_at_impact = sample_track(track, impact_t)

    raw: list[tuple[str, list[dict], bool]] = [
        ("side_track", side_track(track, lateral_offset=ideal * 0.6,
                                  height=32.0, fov=fov), False),
        ("target_orbit", orbit(lambda t: sample_track(track, t),
                               radius=ideal, height=56.0, arc_deg=120.0,
                               duration_ms=duration, t0_ms=t0, fov=fov), False),
    ]
    if frag_context.get("projectile_track"):
        raw.append(("projectile_follow",
                    projectile_follow(frag_context["projectile_track"],
                                      trail_dist=80.0, fov=fov), False))
    if impact_point is not None:
        va = frag_context.get("view_angles", (0.0, 0.0, 0.0))
        raw.append(("vertical_arc",
                    bullet_time_arc(tuple(impact_point), tuple(va),
                                    arc_deg=100.0, radius=ideal * 0.7,
                                    height=48.0, duration_ms=min(900.0, duration),
                                    t0_ms=max(t0, impact_t - 400), fov=fov),
                    False))
    else:
        raw.append(("vertical_arc",
                    vertical_orbit(lambda t: sample_track(track, t),
                                   radius=ideal, arc_deg=60.0,
                                   duration_ms=duration, t0_ms=t0,
                                   start_elev_deg=10.0, fov=fov), False))

    candidates: list[dict] = []
    for name, kfs, post in raw:
        ok, kfs2, report = adjust_path(tracer, kfs, track)
        comp = score_path(tracer, kfs2, track, extras)
        candidates.append({
            "name": name, "keyframes": kfs2, "valid": ok,
            "adjusted": kfs2 != kfs, "score": comp["total"],
            "components": comp, "post_production": post, "report": report,
        })

    candidates.append({
        "name": "pov", "keyframes": [], "valid": True, "adjusted": False,
        "score": POV_BASELINE_SCORE,
        "components": {"total": POV_BASELINE_SCORE, "traced": False},
        "post_production": False,
        "report": {"note": "no-op: use the demo's own first-person view"},
    })

    # invalid paths sink below any valid one; ties broken by name (stable)
    candidates.sort(key=lambda c: (c["valid"], c["score"], c["name"]),
                    reverse=True)
    return candidates
