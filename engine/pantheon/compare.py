"""PerformanceDiff — a real performance against its reproduction, per track.

ONE INSTRUMENT. Both sides are PerformanceTraces produced by the SAME
extractor: the real one read off the source demo, the reproduction read off
the synthetic demo the compiler wrote. Comparing a trace against the raw
parser output of the synthetic (what the first proof did) measured the
reproduction with a different ruler than the original; comparing trace to
trace measures both with one.

ONE CLOCK, ONE TRANSFORM. The reproduction's serverTime is the real one plus a
constant offset (the compiler's base). Its positions are the real ones under
the Retarget that was applied. The comparison applies both to the real side
and then asks for equality, so EXACT_WORLD and LOCAL_FRAME are judged by the
same code path.

GAPS STAY GAPS. Where the source demo carried no sample of the player -- the
recorder lost sight of him, the entity left the snapshot -- there is nothing
to compare against and the track says UNOBSERVED for that span. Nothing is
interpolated across an absence and then called source truth.

Statuses, per track:
    MATCHED                 every real sample has a counterpart, error == 0
    WITHIN_TOLERANCE        every real sample has a counterpart, error <= tol
    INTENTIONAL_DIFFERENCE  the caller declared this track differs by design
    UNOBSERVED              the source carried nothing on this track
    MISSING                 the reproduction lacks samples the source has
    INVALID                 a counterpart exists and exceeds tolerance, or
                            the two traces cannot be aligned at all
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable

from engine.pantheon.performance import PerformanceTrace
from engine.pantheon.retarget import Retarget

# Two snapshots are 25 ms apart; a hole wider than two of them is an absence.
GAP_MS = 50


class Status(Enum):
    MATCHED = "MATCHED"
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
    INTENTIONAL_DIFFERENCE = "INTENTIONAL_DIFFERENCE"
    UNOBSERVED = "UNOBSERVED"
    MISSING = "MISSING"
    INVALID = "INVALID"


@dataclass(frozen=True)
class Tolerances:
    position_u: float = 1.0
    velocity_u: float = 1.0
    yaw_deg: float = 0.5
    pitch_deg: float = 0.5
    projectile_u: float = 1.0
    event_ms: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrackResult:
    track: str
    status: Status
    expected: int                       # samples/events on the real side
    compared: int                       # of those, found on the repro side
    max_error: float | None = None
    tolerance: float | None = None
    unobserved_spans_ms: list[tuple[int, int]] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class PerformanceDiff:
    real_demo: str
    real_client: int
    repro_client: int
    time_offset_ms: int
    retarget: dict
    tolerances: dict
    tracks: dict[str, TrackResult] = field(default_factory=dict)

    # -- verdict -------------------------------------------------------
    @property
    def semantic_fidelity(self) -> str:
        """PASS when nothing observed came back wrong or absent."""
        bad = {Status.MISSING, Status.INVALID}
        return "FAIL" if any(t.status in bad for t in self.tracks.values()) else "PASS"

    def statuses(self) -> dict[str, str]:
        return {k: v.status.value for k, v in self.tracks.items()}

    def as_dict(self) -> dict:
        return {"real_demo": self.real_demo, "real_client": self.real_client,
                "repro_client": self.repro_client,
                "time_offset_ms": self.time_offset_ms, "retarget": self.retarget,
                "tolerances": self.tolerances,
                "semantic_fidelity": self.semantic_fidelity,
                "tracks": {k: v.as_dict() for k, v in self.tracks.items()}}

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=1), encoding="utf-8")
        return path

    def summary(self) -> str:
        return " ".join(f"{k}={v.status.value}" for k, v in self.tracks.items())


# ── helpers ────────────────────────────────────────────────────────────────

def _gaps(times: list[int]) -> list[tuple[int, int]]:
    return [(a, b) for a, b in zip(times, times[1:]) if b - a > GAP_MS]


def _ang(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _status(expected: int, compared: int, max_err: float | None, tol: float,
            *, exact_zero: bool = True) -> Status:
    if expected == 0:
        return Status.UNOBSERVED
    if compared < expected:
        return Status.MISSING
    if max_err is None:
        return Status.MATCHED
    if max_err > tol:
        return Status.INVALID
    if exact_zero and max_err == 0.0:
        return Status.MATCHED
    return Status.WITHIN_TOLERANCE


def _sample_track(name: str, real_by_t: dict, repro_by_t: dict, offset: int,
                  err, tol: float, gaps: list[tuple[int, int]]) -> TrackResult:
    errs = []
    for t, r in real_by_t.items():
        s = repro_by_t.get(t + offset)
        if s is None:
            continue
        errs.append(err(r, s))
    max_err = round(max(errs), 4) if errs else None
    st = _status(len(real_by_t), len(errs), max_err, tol)
    return TrackResult(name, st, len(real_by_t), len(errs), max_err, tol, gaps)


# ── the comparison ─────────────────────────────────────────────────────────

def compare(real: PerformanceTrace, repro: PerformanceTrace, *,
            time_offset_ms: int | None = None,
            retarget: Retarget | None = None,
            tol: Tolerances = Tolerances(),
            intentional: Iterable[str] = ()) -> PerformanceDiff:
    """Every track of `real`, looked up in `repro` at real.t + offset.

    `time_offset_ms` defaults to the difference of the two windows' starts,
    which is what compile_performance produces. `retarget` is applied to the
    REAL side (positions, velocities, yaw) before comparing. `intentional`
    names tracks the caller knows differ by design; they are reported, not
    judged.
    """
    rt = retarget or Retarget.exact_world()
    off = (repro.start_ms - real.start_ms) if time_offset_ms is None else time_offset_ms
    intentional = set(intentional)
    diff = PerformanceDiff(real.demo_hash, real.client, repro.client, off,
                           rt.as_dict(), tol.as_dict())
    if real.map != repro.map:
        diff.tracks["map"] = TrackResult("map", Status.INVALID, 1, 0,
                                         detail={"real": real.map, "repro": repro.map})
        return diff

    gaps = _gaps([s.t for s in real.transform])

    # transform: position / velocity
    r_tr = {s.t: s for s in real.transform}
    p_tr = {s.t: s for s in repro.transform}
    diff.tracks["position"] = _sample_track(
        "position", r_tr, p_tr, off,
        lambda r, s: math.dist(rt.place(r.origin), s.origin), tol.position_u, gaps)
    diff.tracks["velocity"] = _sample_track(
        "velocity", r_tr, p_tr, off,
        lambda r, s: math.dist(rt.turn(r.velocity), s.velocity), tol.velocity_u, gaps)
    diff.tracks["airborne"] = _sample_track(
        "airborne", r_tr, p_tr, off,
        lambda r, s: 0.0 if r.airborne == s.airborne else 1.0, 0.0, gaps)

    # aim
    r_aim = {a.t: a for a in real.aim}
    p_aim = {a.t: a for a in repro.aim}
    diff.tracks["yaw"] = _sample_track(
        "yaw", r_aim, p_aim, off, lambda r, s: _ang(rt.yaw(r.yaw), s.yaw),
        tol.yaw_deg, gaps)
    diff.tracks["pitch"] = _sample_track(
        "pitch", r_aim, p_aim, off, lambda r, s: abs(r.pitch - s.pitch),
        tol.pitch_deg, gaps)

    # animation: equality of (legs, torso)
    r_an = {a.t: a for a in real.animation}
    p_an = {a.t: a for a in repro.animation}
    diff.tracks["animation"] = _sample_track(
        "animation", r_an, p_an, off,
        lambda r, s: 0.0 if (r.legs, r.torso) == (s.legs, s.torso) else 1.0,
        0.0, gaps)

    # weapon: the sequence of holdings, as (t, weapon)
    r_w = [(w.t + off, w.weapon) for w in real.weapon]
    p_w = [(w.t, w.weapon) for w in repro.weapon]
    if not r_w:
        diff.tracks["weapon"] = TrackResult("weapon", Status.UNOBSERVED, 0, 0)
    else:
        # the reproduction starts holding at its first sample, which may sit
        # a tick after the real switch time; compare the weapon sequence and
        # the switch times to within one snapshot
        seq_ok = [w for _, w in r_w] == [w for _, w in p_w]
        t_err = (max(abs(a[0] - b[0]) for a, b in zip(r_w, p_w)) if seq_ok else None)
        st = (Status.MATCHED if seq_ok and t_err == 0 else
              Status.WITHIN_TOLERANCE if seq_ok and t_err is not None and t_err <= 25
              else Status.MISSING if len(p_w) < len(r_w) else Status.INVALID)
        diff.tracks["weapon"] = TrackResult(
            "weapon", st, len(r_w), len(p_w), t_err, 25.0,
            detail={"real": r_w, "repro": p_w})

    # projectiles: every real sample at (t, entity-order) must come back
    r_pj: dict[tuple[int, int], object] = {}
    p_pj: dict[tuple[int, int], object] = {}
    for p in real.projectiles:
        r_pj[(p.t + off, _entity_rank(real.projectiles, p.entity))] = p
    for p in repro.projectiles:
        p_pj[(p.t, _entity_rank(repro.projectiles, p.entity))] = p
    errs = []
    for k, p in r_pj.items():
        s = p_pj.get(k)
        if s is None:
            continue
        errs.append(math.dist(rt.place(p.origin), s.origin))
    max_err = round(max(errs), 4) if errs else None
    diff.tracks["projectiles"] = TrackResult(
        "projectiles", _status(len(r_pj), len(errs), max_err, tol.projectile_u),
        len(r_pj), len(errs), max_err, tol.projectile_u,
        detail={"weapons": sorted({p.weapon for p in real.projectiles})})

    # events, per kind
    kinds = sorted({e.kind for e in real.events} | {e.kind for e in repro.events})
    for kind in kinds:
        name = f"event:{kind}"
        r_ev = sorted(e.t + off for e in real.events if e.kind == kind)
        p_ev = sorted(e.t for e in repro.events if e.kind == kind)
        if kind in intentional or "events" in intentional:
            diff.tracks[name] = TrackResult(name, Status.INTENTIONAL_DIFFERENCE,
                                            len(r_ev), len(p_ev),
                                            detail={"real": r_ev, "repro": p_ev})
            continue
        if not r_ev:
            # the reproduction emitted something the source never had
            diff.tracks[name] = TrackResult(name, Status.INVALID if p_ev else
                                            Status.UNOBSERVED, 0, len(p_ev),
                                            detail={"repro": p_ev})
            continue
        matched, t_errs, pool = 0, [], list(p_ev)
        for t in r_ev:
            best = min(pool, key=lambda x: abs(x - t), default=None)
            if best is not None and abs(best - t) <= tol.event_ms:
                matched += 1
                t_errs.append(abs(best - t))
                pool.remove(best)
        max_e = max(t_errs) if t_errs else None
        st = _status(len(r_ev), matched, float(max_e) if max_e is not None else None,
                     float(tol.event_ms))
        if st in (Status.MATCHED, Status.WITHIN_TOLERANCE) and pool:
            st = Status.INVALID          # extra events the source never had
        diff.tracks[name] = TrackResult(name, st, len(r_ev), matched, max_e,
                                        float(tol.event_ms),
                                        detail={"real": r_ev, "repro": p_ev,
                                                "unmatched_repro": pool})
    return diff


def _entity_rank(samples, entity: int) -> int:
    """Projectile slots differ between the source and the synthetic (the
    compiler renumbers into its own range), so a missile is identified by
    the ORDER in which distinct entities first appear, which the compiler
    preserves."""
    seen: list[int] = []
    for p in samples:
        if p.entity not in seen:
            seen.append(p.entity)
    return seen.index(entity)
