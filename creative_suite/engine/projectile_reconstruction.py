"""Continue a projectile the client stopped seeing, by the game's own rules.

THE SITUATION. A client demo holds what the server sent that client. A
rocket or grenade the recorder fired can leave the snapshot stream before it
lands -- out of PVS, culled, or simply never echoed -- and then a hit or a
frag arrives that the stored path cannot show. The projectile did not stop
existing. Its motion was fully determined the moment it left the barrel:
launch state, the game's trajectory rules, gravity, the map, and a fuse.
Continuing it is arithmetic against the world geometry, not a guess.

WHAT THE RULES ARE, AND WHERE THEY COME FROM. Every constant below is read
from the canonical game source in this repository (g_missile.c, bg_misc.c,
g_main.c), not from feel:

    rocket    TR_LINEAR at g_weapon_rocket_speed, 15 s life, splash 120,
              explodes on any solid contact
    grenade   TR_GRAVITY at 700 u/s along the aim direction, gravity 800,
              EF_BOUNCE_HALF: reflect and scale by 0.65, come to rest when
              the surface is near-flat and the speed drops under 40,
              2.5 s fuse, splash 150

The rocket speed is a SERVER CVAR (canonical default 900; Quake Live servers
commonly run 1000). It is a parameter here, recorded in provenance, never a
silent assumption. The earlier extractor also gave grenades a +200 upward
toss that the source does not contain; that is not reproduced.

WHAT THIS DOES NOT DO. It does not bend physics to reach a later kill. When
a propagated path disagrees with a later authoritative event, the
disagreement is reported with its residual, and the honest explanations are
listed: a dynamic body the client never saw, wrong launch evidence, a
missing surface flag, a parse error. Fitting the path to the kill would turn
a reconstruction into a fabrication with a good alibi.

PROVENANCE. Points the client received stay RECORDED. Points this module
produces are PHYSICS_RECONSTRUCTED. Points selected because a later event
ruled others out are EVENT_CONSTRAINED. None of them ever becomes RECORDED.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
import math
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt

RECON_VERSION = "projectile-recon-v1.1.0"   # patch normals

# ── game constants, with their source lines ─────────────────────────────────

GRAVITY = 800.0                       # g_main.c g_gravity default; bg_public.h
ROCKET_SPEED_DEFAULT = 900.0          # g_main.c g_weapon_rocket_speed default
ROCKET_SPEED_QL = 1000.0              # Quake Live server convention; a cvar
ROCKET_LIFE_MS = 15_000               # g_missile.c fire_rocket nextthink
ROCKET_SPLASH = 120.0                 # g_missile.c fire_rocket splashRadius
GRENADE_SPEED = 700.0                 # g_missile.c fire_grenade VectorScale
GRENADE_FUSE_MS = 2_500               # g_missile.c fire_grenade nextthink
GRENADE_SPLASH = 150.0                # g_missile.c fire_grenade splashRadius
BOUNCE_DAMPING = 0.65                 # g_missile.c G_BounceMissile EF_BOUNCE_HALF
REST_NORMAL_Z = 0.2                   # g_missile.c: plane.normal[2] > 0.2
REST_SPEED = 40.0                     # g_missile.c: VectorLength(trDelta) < 40
PRESTEP_MS = 50                       # MISSILE_PRESTEP_TIME, g_local.h
STEP_MS = 10                          # integration step; the server runs 50 ms
                                      # frames but sub-steps make bounces exact

KIND_ROCKET = "rocket"
KIND_GRENADE = "grenade"

# ── confidence ──────────────────────────────────────────────────────────────

EXACT_DETERMINISTIC = "EXACT_DETERMINISTIC"
DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT = (
    "DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT")
EVENT_CONSTRAINED = "EVENT_CONSTRAINED"
AMBIGUOUS = "AMBIGUOUS"
UNSOLVABLE = "UNSOLVABLE"
CONFIDENCES = (EXACT_DETERMINISTIC,
               DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT,
               EVENT_CONSTRAINED, AMBIGUOUS, UNSOLVABLE)

Vec = tuple[float, float, float]


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec, s: float) -> Vec:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a: Vec) -> float:
    return math.sqrt(_dot(a, a))


def _normalize(a: Vec) -> Vec:
    n = _length(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 0 else (0.0, 0.0, 0.0)


# ── world contact, with the plane it happened on ────────────────────────────

@dataclass(frozen=True)
class Contact:
    """Where a segment first meets solid world, and which way the wall faces."""
    fraction: float
    point: Vec
    normal: Vec


def first_contact(bsp: Any, start: Vec, end: Vec) -> Contact | None:
    """Earliest solid-brush entry along start->end, with its plane normal.

    A bounce needs the plane, so a boolean tracer is not enough. This walks
    the same worldspawn brushes `bsp_geometry.line_blocked` walks, but keeps
    the entering plane of the earliest hit. Patches (curved surfaces) are
    tested as blockers only; their normal is not available, so a contact on
    a patch is reported with a zero normal and callers must treat it as an
    explosion, never a bounce.
    """
    from engine.parser import bsp_geometry as bg
    lo, hi = bsp.world_brush_range
    best: Contact | None = None
    checked: set[int] = set()
    stack = [(0, tuple(start), tuple(end))]
    eps = bg._EPS
    while stack:
        node_idx, p1, p2 = stack.pop()
        while node_idx >= 0:
            plane_idx, c0, c1 = bsp.nodes[node_idx]
            nx, ny, nz, dist = bsp.planes[plane_idx]
            d1 = p1[0] * nx + p1[1] * ny + p1[2] * nz - dist
            d2 = p2[0] * nx + p2[1] * ny + p2[2] * nz - dist
            if d1 >= -eps and d2 >= -eps:
                node_idx = c0
            elif d1 < eps and d2 < eps:
                node_idx = c1
            else:
                f = d1 / (d1 - d2)
                mid = (p1[0] + f * (p2[0] - p1[0]), p1[1] + f * (p2[1] - p1[1]),
                       p1[2] + f * (p2[2] - p1[2]))
                if d1 >= 0:
                    stack.append((c1, mid, p2))
                    node_idx = c0
                    p2 = mid
                else:
                    stack.append((c0, mid, p2))
                    node_idx = c1
                    p2 = mid
        lb_first, lb_num = bsp.leafs[-(node_idx + 1)]
        for i in range(lb_first, lb_first + lb_num):
            b = bsp.leafbrushes[i]
            if b in checked or not (lo <= b < hi):
                continue
            checked.add(b)
            hit = _brush_entry(bsp, b, start, end, eps)
            if hit is not None and (best is None or hit.fraction < best.fraction):
                best = hit
    # Curved surfaces. The boolean tracer only says "blocked"; a bounce needs
    # the plane, and a patch triangle gives one by cross product. When the
    # cell has no triangles (coarse AABB only) the contact keeps a zero
    # normal and callers treat it as an explosion.
    for aabb, tris in bsp.patch_cells:
        if not bg._segment_hits_aabb(aabb, start, end):
            continue
        if tris is None:
            if best is None:
                best = Contact(1.0, tuple(end), (0.0, 0.0, 0.0))
            continue
        for a, b, c in tris:
            hit = _triangle_entry(start, end, a, b, c)
            if hit is not None and (best is None or hit.fraction < best.fraction):
                best = hit
    return best


def _triangle_entry(p1: Vec, p2: Vec, a: Vec, b: Vec, c: Vec) -> Contact | None:
    """Moller-Trumbore segment/triangle hit with the face normal, facing the
    segment's origin so a bounce always reflects away from the surface."""
    d = _sub(p2, p1)
    e1, e2 = _sub(b, a), _sub(c, a)
    n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0])
    nl = _length(n)
    if nl < 1e-9:
        return None
    pvec = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2],
            d[0] * e2[1] - d[1] * e2[0])
    det = _dot(e1, pvec)
    if abs(det) < 1e-9:
        return None
    inv = 1.0 / det
    t = _sub(p1, a)
    u = _dot(t, pvec) * inv
    if u < -1e-6 or u > 1.0 + 1e-6:
        return None
    q = (t[1] * e1[2] - t[2] * e1[1], t[2] * e1[0] - t[0] * e1[2],
         t[0] * e1[1] - t[1] * e1[0])
    v = _dot(d, q) * inv
    if v < -1e-6 or u + v > 1.0 + 1e-6:
        return None
    f = _dot(e2, q) * inv
    if f < 0.0 or f > 1.0:
        return None
    normal = _scale(n, 1.0 / nl)
    if _dot(normal, d) > 0:            # face the incoming segment
        normal = _scale(normal, -1.0)
    return Contact(f, _add(p1, _scale(d, f)), normal)


def _brush_entry(bsp: Any, brush_idx: int, p1: Vec, p2: Vec,
                 eps: float) -> Contact | None:
    """Slab clip that remembers the plane the segment entered through."""
    from engine.parser import bsp_geometry as bg
    first, count, contents = bsp.brushes[brush_idx]
    if not (contents & bg.CONTENTS_SOLID):
        return None
    enter_f, leave_f = -1.0, 2.0
    enter_plane: tuple[float, float, float] | None = None
    for si in range(first, first + count):
        nx, ny, nz, dist = bsp.planes[bsp.brushsides[si]]
        d1 = p1[0] * nx + p1[1] * ny + p1[2] * nz - dist
        d2 = p2[0] * nx + p2[1] * ny + p2[2] * nz - dist
        if d1 > eps and d2 > eps:
            return None
        if d1 <= eps and d2 <= eps:
            continue
        f = d1 / (d1 - d2)
        if d1 > d2:
            if f > enter_f:
                enter_f, enter_plane = f, (nx, ny, nz)
        elif f < leave_f:
            leave_f = f
        if enter_f > leave_f:
            return None
    if enter_f > leave_f or enter_plane is None:
        return None
    f = max(0.0, enter_f)
    point = (p1[0] + f * (p2[0] - p1[0]), p1[1] + f * (p2[1] - p1[1]),
             p1[2] + f * (p2[2] - p1[2]))
    return Contact(f, point, enter_plane)


# ── the propagated path ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class PathPoint:
    t_us: int
    pos: Vec
    vel: Vec
    evidence: str                     # a demo_truth evidence class

    def to_dict(self) -> dict[str, Any]:
        return {"t_us": self.t_us, "pos": list(self.pos), "vel": list(self.vel),
                "evidence": self.evidence}


@dataclass(frozen=True)
class Bounce:
    t_us: int
    point: Vec
    normal: Vec
    speed_before: float
    speed_after: float


@dataclass(frozen=True)
class LaunchState:
    """What the projectile was at t0. Its evidence class travels with it."""
    kind: str
    t_us: int
    pos: Vec
    direction: Vec
    evidence: str
    rocket_speed: float = ROCKET_SPEED_QL

    @property
    def velocity(self) -> Vec:
        d = _normalize(self.direction)
        speed = self.rocket_speed if self.kind == KIND_ROCKET else GRENADE_SPEED
        return _scale(d, speed)


@dataclass(frozen=True)
class Continuation:
    """A projectile carried forward by physics until the world stops it."""
    kind: str
    launch: LaunchState
    points: tuple[PathPoint, ...]
    end_t_us: int
    end_reason: str                   # IMPACT | FUSE | LIFETIME | REST | PATCH
    end_pos: Vec
    bounces: tuple[Bounce, ...] = ()
    confidence: str = EXACT_DETERMINISTIC
    notes: tuple[str, ...] = ()
    params: tuple[tuple[str, str], ...] = ()

    @property
    def flight_us(self) -> int:
        return self.end_t_us - self.launch.t_us

    @property
    def recon_id(self) -> str:
        payload = json.dumps({"kind": self.kind, "t": self.launch.t_us,
                              "pos": self.launch.pos, "dir": self.launch.direction,
                              "params": self.params, "v": RECON_VERSION},
                             sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "recon_id": self.recon_id,
                "launch": {"t_us": self.launch.t_us, "pos": list(self.launch.pos),
                           "direction": list(self.launch.direction),
                           "evidence": self.launch.evidence},
                "points": len(self.points), "end_t_us": self.end_t_us,
                "end_reason": self.end_reason, "end_pos": list(self.end_pos),
                "flight_us": self.flight_us,
                "bounces": [asdict(b) for b in self.bounces],
                "confidence": self.confidence, "notes": list(self.notes),
                "params": dict(self.params)}


def propagate(launch: LaunchState, bsp: Any, *, gravity: float = GRAVITY,
              step_ms: int = STEP_MS,
              observed: Sequence[PathPoint] = ()) -> Continuation:
    """Run the game's trajectory rules forward from the launch state.

    ``observed`` points, if given, are kept verbatim as RECORDED and the
    reconstruction resumes from the last of them -- the boundary between
    what the client saw and what physics says is explicit in the output,
    never smoothed over.
    """
    kind = launch.kind
    if kind not in (KIND_ROCKET, KIND_GRENADE):
        raise ValueError(f"unknown projectile kind {kind!r}")
    life_ms = ROCKET_LIFE_MS if kind == KIND_ROCKET else GRENADE_FUSE_MS
    params = (("gravity", str(gravity)), ("step_ms", str(step_ms)),
              ("rocket_speed", str(launch.rocket_speed)),
              ("bounce_damping", str(BOUNCE_DAMPING)),
              ("source", "g_missile.c / bg_misc.c / g_main.c"))

    pts: list[PathPoint] = list(observed)
    notes: list[str] = []
    if observed:
        last = observed[-1]
        t, pos, vel = last.t_us, last.pos, last.vel
        notes.append(f"resumed from the last RECORDED sample at {t} us")
    else:
        t, pos, vel = launch.t_us, launch.pos, launch.velocity
        pts.append(PathPoint(t, pos, vel, launch.evidence))

    bounces: list[Bounce] = []
    end_t = launch.t_us + life_ms * 1000
    dt_s = step_ms / 1000.0          # seconds per step; `dt` is the module
    reason, confidence = "LIFETIME" if kind == KIND_ROCKET else "FUSE", EXACT_DETERMINISTIC
    while t < end_t:
        if kind == KIND_GRENADE:
            vel = (vel[0], vel[1], vel[2] - gravity * dt_s)
        nxt = _add(pos, _scale(vel, dt_s))
        hit = first_contact(bsp, pos, nxt)
        if hit is not None:
            t_hit = t + int(round(hit.fraction * step_ms * 1000))
            if kind == KIND_ROCKET or _length(hit.normal) == 0.0:
                pts.append(PathPoint(t_hit, hit.point, vel, dt.PHYSICS_RECONSTRUCTED))
                reason = "IMPACT" if kind == KIND_ROCKET else "PATCH"
                if _length(hit.normal) == 0.0 and kind == KIND_GRENADE:
                    notes.append("stopped on a curved-surface cell with no "
                                 "triangle data: no normal to bounce from")
                    confidence = AMBIGUOUS
                pos, t = hit.point, t_hit
                break
            # G_BounceMissile: reflect, damp, maybe come to rest.
            speed_before = _length(vel)
            d = _dot(vel, hit.normal)
            vel = _scale(_add(vel, _scale(hit.normal, -2.0 * d)), BOUNCE_DAMPING)
            bounces.append(Bounce(t_hit, hit.point, hit.normal, speed_before,
                                  _length(vel)))
            pos = _add(hit.point, hit.normal)          # VectorAdd(origin, normal)
            t = t_hit
            pts.append(PathPoint(t, pos, vel, dt.PHYSICS_RECONSTRUCTED))
            if hit.normal[2] > REST_NORMAL_Z and _length(vel) < REST_SPEED:
                reason = "REST"
                break
            continue
        pos, t = nxt, t + step_ms * 1000
        pts.append(PathPoint(t, pos, vel, dt.PHYSICS_RECONSTRUCTED))
    if reason in ("LIFETIME", "FUSE"):
        pos = pts[-1].pos
        t = min(t, end_t)
    notes.append("zero-width line trace; the server traces the missile's bbox, "
                 "so contacts at grazing angles can differ by a few units")
    notes.append("sky (SURF_NOIMPACT) is not distinguished; a rocket that "
                 "should fly out of the map is reported as an IMPACT")
    return Continuation(kind=kind, launch=launch, points=tuple(pts),
                        end_t_us=t, end_reason=reason, end_pos=pos,
                        bounces=tuple(bounces), confidence=confidence,
                        notes=tuple(notes), params=params)


# ── checking a path against what happened later ─────────────────────────────

@dataclass(frozen=True)
class ConstraintResult:
    """Does the physics agree with the later evidence? Report, don't fit."""
    event_kind: str
    event_t_us: int
    event_pos: Vec | None
    path_t_us: int
    path_pos: Vec
    time_residual_us: int
    space_residual_u: float | None
    compatible: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_pos"] = list(self.event_pos) if self.event_pos else None
        d["path_pos"] = list(self.path_pos)
        return d


def check_against_event(cont: Continuation, *, event_kind: str,
                        event_t_us: int, event_pos: Vec | None,
                        splash: float | None = None) -> ConstraintResult:
    """Compare the propagated end against a later authoritative event.

    Compatible means the path ends within the weapon's splash radius of the
    event, at a time the demo's tick quantisation allows. Incompatible is
    reported with the residuals and the honest list of causes. The path is
    never moved.
    """
    radius = splash if splash is not None else (
        ROCKET_SPLASH if cont.kind == KIND_ROCKET else GRENADE_SPLASH)
    t_res = cont.end_t_us - event_t_us
    s_res = (_length(_sub(cont.end_pos, event_pos))
             if event_pos is not None else None)
    time_ok = abs(t_res) <= 60_000                # one server frame + prestep
    space_ok = s_res is None or s_res <= radius
    ok = time_ok and space_ok
    if ok:
        why = (f"path ends {s_res:.0f}u from the {event_kind} inside the "
               f"{radius:.0f}u splash radius, {t_res / 1000:+.0f} ms from it"
               if s_res is not None else
               f"path ends {t_res / 1000:+.0f} ms from the {event_kind}")
    else:
        causes = ["an unobserved dynamic body (a player) stopped it earlier",
                  "the launch evidence is wrong (inferred, not recorded)",
                  "a surface flag the tracer cannot see (sky, non-solid)",
                  "a parse error in the launch or the event"]
        why = (f"path ends {t_res / 1000:+.0f} ms and "
               f"{'?' if s_res is None else f'{s_res:.0f}u'} from the "
               f"{event_kind}: physics and evidence disagree; possible causes: "
               + "; ".join(causes))
    return ConstraintResult(event_kind, event_t_us, event_pos, cont.end_t_us,
                            cont.end_pos, t_res, s_res, ok, why)


def constrain(cont: Continuation, result: ConstraintResult) -> Continuation:
    """Record that a later event was checked. Confidence moves DOWN or stays.

    A compatible check earns EVENT_CONSTRAINED provenance for the points --
    they were selected, not merely propagated. An incompatible one leaves the
    physics exactly where it was and marks the whole path AMBIGUOUS.
    """
    from dataclasses import replace
    if result.compatible:
        pts = tuple(replace(p, evidence=dt.EVENT_CONSTRAINED)
                    if p.evidence == dt.PHYSICS_RECONSTRUCTED else p
                    for p in cont.points)
        return replace(cont, points=pts, confidence=EVENT_CONSTRAINED,
                       notes=cont.notes + (f"consistent with later "
                                           f"{result.event_kind}",))
    return replace(cont, confidence=AMBIGUOUS,
                   notes=cont.notes + (result.explanation,))


# ── observation gaps ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ObservationGap:
    """An entity the client stopped receiving, and what bracketed the gap."""
    entity_id: int
    kind: str
    last_seen_t_us: int
    last_seen_pos: Vec
    last_seen_vel: Vec
    next_seen_t_us: int | None = None
    next_seen_pos: Vec | None = None
    map_name: str = ""
    later_events: tuple[tuple[str, int], ...] = ()

    @property
    def duration_us(self) -> int | None:
        return (None if self.next_seen_t_us is None
                else self.next_seen_t_us - self.last_seen_t_us)

    @property
    def closed(self) -> bool:
        return self.next_seen_t_us is not None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("last_seen_pos", "last_seen_vel", "next_seen_pos"):
            if d[k] is not None:
                d[k] = list(d[k])
        d.update(duration_us=self.duration_us, closed=self.closed)
        return d


def gaps_from_samples(entity_id: int, kind: str,
                      samples: Sequence[tuple[int, Vec, Vec]], *,
                      max_silence_us: int = 100_000,
                      map_name: str = "") -> list[ObservationGap]:
    """Find where a sample stream goes quiet for longer than one server frame."""
    out: list[ObservationGap] = []
    ordered = sorted(samples, key=lambda s: s[0])
    for (t0, p0, v0), (t1, p1, _v1) in zip(ordered, ordered[1:]):
        if t1 - t0 > max_silence_us:
            out.append(ObservationGap(entity_id, kind, t0, p0, v0, t1, p1,
                                      map_name))
    if ordered:
        t0, p0, v0 = ordered[-1]
        out.append(ObservationGap(entity_id, kind, t0, p0, v0, None, None,
                                  map_name))
    return out


# ── cache identity ──────────────────────────────────────────────────────────

def cache_key(content_hash: str, entity_id: int, launch_t_us: int,
              bsp_hash: str, *, rocket_speed: float = ROCKET_SPEED_QL) -> str:
    """Same demo, entity, launch, map, physics and algorithm -> same key."""
    payload = json.dumps({"demo": content_hash, "entity": entity_id,
                          "t": launch_t_us, "bsp": bsp_hash,
                          "rocket_speed": rocket_speed, "gravity": GRAVITY,
                          "damping": BOUNCE_DAMPING, "step_ms": STEP_MS,
                          "version": RECON_VERSION},
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


# ── truncating at an authoritative contact the world trace cannot see ───────

def path_point_at(cont: Continuation, t_us: int) -> PathPoint | None:
    """The propagated position at a given time, by linear interpolation."""
    pts = cont.points
    if not pts or t_us < pts[0].t_us or t_us > pts[-1].t_us:
        return None
    for a, b in zip(pts, pts[1:]):
        if a.t_us <= t_us <= b.t_us:
            if b.t_us == a.t_us:
                return a
            f = (t_us - a.t_us) / (b.t_us - a.t_us)
            pos = _add(a.pos, _scale(_sub(b.pos, a.pos), f))
            return PathPoint(t_us, pos, a.vel, a.evidence)
    return pts[-1]


def truncate_at_event(cont: Continuation, *, event_kind: str, event_t_us: int,
                      event_pos: Vec | None, splash: float | None = None
                      ) -> tuple[Continuation, ConstraintResult]:
    """Stop the path where an authoritative hit says it stopped.

    A world-only trace cannot see players, so a rocket that hit one keeps
    flying in the simulation until it finds a wall. When a recorded hit or
    frag falls ON the propagated line before that wall, the honest result is
    the same path cut at that instant: nothing about the physics changes,
    only where it ends. If the event is NOT on the line, the path is left
    alone and the disagreement is reported -- that is a different fact, not
    a fitting problem.
    """
    from dataclasses import replace
    radius = splash if splash is not None else (
        ROCKET_SPLASH if cont.kind == KIND_ROCKET else GRENADE_SPLASH)
    at = path_point_at(cont, event_t_us)
    if at is None:
        res = ConstraintResult(event_kind, event_t_us, event_pos, cont.end_t_us,
                               cont.end_pos, cont.end_t_us - event_t_us, None,
                               False, f"the {event_kind} at {event_t_us} us lies "
                                      f"outside the propagated interval")
        return replace(cont, confidence=AMBIGUOUS,
                       notes=cont.notes + (res.explanation,)), res
    s_res = _length(_sub(at.pos, event_pos)) if event_pos is not None else None
    on_line = s_res is None or s_res <= radius
    res = ConstraintResult(event_kind, event_t_us, event_pos, at.t_us, at.pos, 0,
                           s_res, on_line,
                           (f"the {event_kind} sits {s_res:.0f}u from the path at its "
                            f"own time, inside the {radius:.0f}u splash radius; the "
                            f"path is cut there -- a body the world trace cannot see "
                            f"stopped it" if on_line and s_res is not None else
                            f"the {event_kind} is {s_res:.0f}u off the path at its own "
                            f"time: physics and evidence disagree; possible causes: "
                            f"wrong launch evidence; an earlier unobserved contact; a "
                            f"parse error" if s_res is not None else
                            f"the {event_kind} has no position; only its time is checked"))
    if not on_line:
        return replace(cont, confidence=AMBIGUOUS,
                       notes=cont.notes + (res.explanation,)), res
    # The recorded event lands where and when the world-only physics already
    # ended (fuse, wall, rest): nothing was unobserved at the end. That is the
    # strongest claim this module makes, and it keeps the world-only reason.
    if (cont.end_reason in ("FUSE", "IMPACT", "REST")
            and abs(cont.end_t_us - event_t_us) <= CONFIRM_WINDOW_US):
        why = (f"the recorded {event_kind} confirms the world-only end "
               f"({cont.end_reason} at {cont.end_t_us} us): "
               f"{'%.0fu' % s_res if s_res is not None else 'time'} agreement")
        res = replace(res, explanation=why)
        return replace(cont, confidence=EXACT_DETERMINISTIC,
                       notes=cont.notes + (why,)), res
    kept = tuple(p for p in cont.points if p.t_us < event_t_us)
    cut = replace(at, evidence=EVENT_CONSTRAINED_EVIDENCE)
    pts = tuple(replace(p, evidence=EVENT_CONSTRAINED_EVIDENCE)
                if p.evidence == dt.PHYSICS_RECONSTRUCTED else p for p in kept) + (cut,)
    return replace(cont, points=pts, end_t_us=event_t_us, end_pos=at.pos,
                   end_reason="DYNAMIC_CONTACT",
                   confidence=DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT,
                   notes=cont.notes + (res.explanation,)), res


EVENT_CONSTRAINED_EVIDENCE = dt.EVENT_CONSTRAINED
CONFIRM_WINDOW_US = 50_000     # two server frames: event and simulated end coincide


# ── segmented interval provenance ───────────────────────────────────────────
#
# A path is not one evidence class. Its first stretch was recorded, the rest
# was derived, and a cut at a recorded hit is event-constrained. Consumers
# (camera eligibility, scene evidence, UI text) need those runs as intervals
# with a fraction, never a single label for the whole flight.

@dataclass(frozen=True)
class ProvenanceSegment:
    start_us: int
    end_us: int
    evidence: str
    points: int

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_us"] = self.duration_us
        return d


def provenance_segments(cont: Continuation) -> tuple[ProvenanceSegment, ...]:
    """Maximal runs of equal evidence along the path, in time order. A run's
    end is the first instant of the next run (the interval is half-open), so
    the segments tile the flight exactly."""
    pts = sorted(cont.points, key=lambda p: p.t_us)
    if not pts:
        return ()
    out: list[ProvenanceSegment] = []
    run_start, run_ev, n = pts[0].t_us, pts[0].evidence, 0
    for i, p in enumerate(pts):
        if p.evidence != run_ev:
            out.append(ProvenanceSegment(run_start, p.t_us, run_ev, n))
            run_start, run_ev, n = p.t_us, p.evidence, 0
        n += 1
    out.append(ProvenanceSegment(run_start, max(cont.end_t_us, pts[-1].t_us), run_ev, n))
    return tuple(out)


def recorded_fraction(cont: Continuation) -> float:
    """Share of the flight's duration whose evidence is RECORDED."""
    segs = provenance_segments(cont)
    total = sum(s.duration_us for s in segs)
    if total <= 0:
        return 1.0 if segs and dt.is_recorded(segs[0].evidence) else 0.0
    return sum(s.duration_us for s in segs if dt.is_recorded(s.evidence)) / total


@dataclass(frozen=True)
class CameraEligibility:
    """What a projectile camera may claim about this flight. Derived from the
    reconstruction, never asserted by a scene."""
    projectile_path_available: bool
    reconstruction_class: str            # evidence of the dominant derived run, or RECORDED
    confidence: str
    recorded_fraction: float
    reconstructed_fraction: float
    segments: tuple[ProvenanceSegment, ...]
    eligible: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["segments"] = [s.to_dict() for s in self.segments]
        return d


PRESENTABLE = (EXACT_DETERMINISTIC, DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT)


def camera_eligibility(cont: Continuation | None) -> CameraEligibility:
    if cont is None or not cont.points:
        return CameraEligibility(False, "", "", 0.0, 0.0, (), False,
                                 "no projectile path")
    segs = provenance_segments(cont)
    rf = recorded_fraction(cont)
    derived = [s for s in segs if not dt.is_recorded(s.evidence)]
    klass = (max(derived, key=lambda s: s.duration_us).evidence if derived
             else dt.RECORDED)
    ok = cont.confidence in PRESENTABLE
    reason = (f"{cont.confidence}; {rf:.0%} recorded, {1 - rf:.0%} {klass}"
              if ok else f"confidence {cont.confidence} is below the presentation "
                         f"threshold; UNKNOWN or AMBIGUOUS never qualifies")
    return CameraEligibility(True, klass, cont.confidence, rf, 1.0 - rf, segs,
                             ok, reason)
