"""Performance templates — real, anonymous movement fragments, mined not made.

RUN_IN_STOP_TURN is the first: a player runs on the ground for a while,
decelerates to a real stop, stands, and turns on the spot. That is exactly
what a presenter walking into a frozen scene and facing the camera IS, and
the corpus has it thousands of times over. Nothing here synthesises motion:
a template is a PerformanceTrace window cut out of a real one, scored for
cleanliness, with the player's identity reduced to a demo hash and a slot.

The index (performance_index.db) already stores a 4.3s trace around every
notable action; those windows are mined here. A template's clock is the real
serverTime; retargeting moves it in space, never in time.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path

from engine.pantheon.performance import (AimSample, AnimSample, PerformanceTrace,
                                         TransformSample, WeaponSample)

INDEX_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/performance_index.db")
TEMPLATE_DIR = Path("docs/reference/performance_templates")

LEGS_RUN = {15, 16}          # LEGS_RUN, LEGS_BACK
LEGS_IDLE = {22}             # LEGS_IDLE
LEGS_TURN = 20               # LEGS_TURN


@dataclass
class TemplateScore:
    demo_hash: str
    client: int
    start_ms: int             # trace-relative cut
    end_ms: int
    run_ms: int
    run_speed_mean: float
    decel_ms: int
    stop_ms: int
    turn_deg: float
    turn_ms: int
    straightness: float       # 1.0 = a straight run
    legs_run_ok: bool         # legs in RUN while running
    legs_idle_ok: bool        # legs left RUN once stopped
    score: float


def trace_from_json(d: dict) -> PerformanceTrace:
    tr = PerformanceTrace(d["demo_hash"], d["map"], d["gametype"], d["client"],
                          d["start_ms"], d["end_ms"])
    tr.transform = [TransformSample(**{k: (tuple(v) if isinstance(v, list) else v)
                                       for k, v in s.items()}) for s in d["transform"]]
    tr.aim = [AimSample(**s) for s in d["aim"]]
    tr.animation = [AnimSample(**s) for s in d["animation"]]
    tr.weapon = [WeaponSample(**s) for s in d["weapon"]]
    tr.pov = d.get("pov", False)
    return tr


def cut(tr: PerformanceTrace, t0: int, t1: int) -> PerformanceTrace:
    """A sub-window of a trace, same clock."""
    out = PerformanceTrace(tr.demo_hash, tr.map, tr.gametype, tr.client, t0, t1)
    out.transform = [s for s in tr.transform if t0 <= s.t <= t1]
    out.aim = [s for s in tr.aim if t0 <= s.t <= t1]
    out.animation = [s for s in tr.animation if t0 <= s.t <= t1]
    out.weapon = list(tr.weapon)
    out.pov = tr.pov
    return out


def find_run_in_stop_turn(tr: PerformanceTrace, *, min_run_ms: int = 700,
                          min_stop_ms: int = 500, min_turn_deg: float = 60.0,
                          max_turn_deg: float = 200.0) -> TemplateScore | None:
    """Score one trace for the RUN -> STOP -> TURN shape, or None."""
    T = tr.transform
    if len(T) < 40 or any(s.airborne for s in T):
        return None
    # a recording with a teleport, respawn or PVS pop inside it is not a
    # performance: 25ms at 400 u/s is 10 units, so a 40-unit step is a cut
    if any(math.dist(a.origin, b.origin) > 40 for a, b in zip(T, T[1:])):
        return None
    if max(s.origin[2] for s in T) - min(s.origin[2] for s in T) > 24:
        return None                       # the entrance must be on one floor
    an = {a.t: a for a in tr.animation}
    aim = {a.t: a for a in tr.aim}
    sp = [s.speed for s in T]
    # the run: the longest stretch above 250 u/s on the ground
    best = None
    i = 0
    while i < len(T):
        if sp[i] > 250:
            j = i
            while j < len(T) and sp[j] > 250:
                j += 1
            if best is None or (T[j - 1].t - T[i].t) > (T[best[1] - 1].t - T[best[0]].t):
                best = (i, j)
            i = j
        i += 1
    if best is None:
        return None
    r0, r1 = best
    run_ms = T[r1 - 1].t - T[r0].t
    if run_ms < min_run_ms:
        return None
    # the stop: speed falls under 30 within 600ms of the run's end and stays
    k = r1
    while k < len(T) and sp[k] >= 30:
        k += 1
    if k >= len(T) or T[k].t - T[r1 - 1].t > 600:
        return None
    s0 = k
    s1 = s0
    while s1 < len(T) and sp[s1] < 30:
        s1 += 1
    stop_ms = T[s1 - 1].t - T[s0].t
    if stop_ms < min_stop_ms:
        return None
    # the turn: yaw travelled while stopped
    yaws = [aim[T[m].t].yaw for m in range(s0, s1) if T[m].t in aim]
    if len(yaws) < 4:
        return None
    turn = 0.0
    for a, b in zip(yaws, yaws[1:]):
        turn += abs((b - a + 180) % 360 - 180)
    if not min_turn_deg <= turn <= max_turn_deg:
        return None
    turn_ms = T[s1 - 1].t - T[s0].t
    # animation coherence: RUN while running, not-RUN once stopped
    run_legs = [an[T[m].t].legs for m in range(r0, r1) if T[m].t in an]
    stop_legs = [an[T[m].t].legs for m in range(s0 + 8, s1) if T[m].t in an]
    legs_run_ok = bool(run_legs) and sum(l in LEGS_RUN for l in run_legs) / len(run_legs) > 0.85
    legs_idle_ok = bool(stop_legs) and sum(l not in LEGS_RUN for l in stop_legs) / len(stop_legs) > 0.85
    # straightness of the run
    a, b = T[r0].origin, T[r1 - 1].origin
    chord = math.dist(a, b)
    path = sum(math.dist(T[m].origin, T[m + 1].origin) for m in range(r0, r1 - 1))
    straight = chord / path if path else 0.0
    score = (min(run_ms, 1500) / 1500 + min(stop_ms, 1200) / 1200 + straight
             + (1.0 if legs_run_ok else 0) + (1.0 if legs_idle_ok else 0)
             + (0.5 if 80 <= turn <= 180 else 0))
    return TemplateScore(tr.demo_hash, tr.client, T[r0].t, T[s1 - 1].t, run_ms,
                         sum(sp[r0:r1]) / (r1 - r0), T[s0].t - T[r1 - 1].t,
                         stop_ms, round(turn, 1), turn_ms, round(straight, 3),
                         legs_run_ok, legs_idle_ok, round(score, 3))


def mine_templates(limit_rows: int = 20000, *, kinds=("FIRE_RAIL", "KILL", "FIRE_ROCKET"),
                   maps=("overkill", "campgrounds", "asylum")) -> list[tuple[TemplateScore, dict]]:
    """Scan stored index traces for the shape; return (score, trace_json)."""
    con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True)
    q = ("select trace_json from actions where kind in (%s) and map in (%s) "
         "and airborne_ms = 0 and max_speed > 280 limit ?"
         % (",".join("?" * len(kinds)), ",".join("?" * len(maps))))
    out = []
    for (j,) in con.execute(q, (*kinds, *maps, limit_rows)):
        d = json.loads(j)
        tr = trace_from_json(d)
        sc = find_run_in_stop_turn(tr)
        if sc and sc.legs_run_ok and sc.legs_idle_ok:
            out.append((sc, d))
    con.close()
    out.sort(key=lambda x: -x[0].score)
    return out


def save_template(name: str, sc: TemplateScore, d: dict) -> Path:
    """Persist the cut window as an anonymous template."""
    tr = cut(trace_from_json(d), sc.start_ms, sc.end_ms)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    body = tr.as_dict()
    body["template"] = name
    body["score"] = asdict(sc)
    body["provenance"] = "REAL_RECORDED_PERFORMANCE, anonymous (demo hash + slot)"
    p = TEMPLATE_DIR / f"{name}.json"
    p.write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")
    return p


def load_template(name: str) -> PerformanceTrace:
    d = json.loads((TEMPLATE_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return trace_from_json(d)
