"""Performance templates — reusable real motion, never a spline.

A director asks for "a RUN_IN that stops and turns to the viewer, about
200-350 units". The answer is a REAL recorded performance that does that,
chosen by its measured facts, not an average of many. Averaging real traces
into a template produces the robotic mean of a crowd; a single real trace
keeps one person's timing.

    TPL:<group>:<demo_hash>:<client>:<start_ms>

is a stable identity: the source demo, the actor slot, the segment start.
No insertion-order id, no name.

GROUPS (closed list, derived from the ActionGraph, never from a label):
    RUN_IN, RUN_STOP, RUN_IN_STOP_TURN, TURN_90, TURN_180, COMBAT_STRAFE,
    RETREAT, CHASE, JUMP, LAND, JUMP_PAD, JUMP_PAD_ROCKET, RAIL_FLICK,
    ROCKET_PREDICTION

Each template records the constraints a request can match on: distance
covered, heading delta, duration, ending stance, weapon, airborne time, and
the segment window inside the stored trace, so `load()` returns exactly the
motion and nothing around it.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Sequence

from engine.pantheon import action_graph as AG
from engine.pantheon.performance import PerformanceTrace

from engine.pantheon import performance_index as PI
from engine.pantheon import store as S
GROUPS = ("RUN_IN", "RUN_STOP", "RUN_IN_STOP_TURN", "TURN_90", "TURN_180",
          "COMBAT_STRAFE", "RETREAT", "CHASE", "JUMP", "LAND", "JUMP_PAD",
          "JUMP_PAD_ROCKET", "RAIL_FLICK", "ROCKET_PREDICTION")
STOP_SPEED = 50.0
STOP_HOLD_MS = 300

SCHEMA = """
create table if not exists templates (
  id text primary key, grp text, demo_hash text, client integer, map text,
  start_ms integer, end_ms integer, duration_ms integer,
  distance_u real, heading_delta_deg real, ending_stance text, weapon text,
  airborne_ms integer, grounded_fraction real, features text);
create index if not exists ix_tpl_grp on templates(grp, map);
create table if not exists build_runs (
  built_at real, scanned integer, templates integer, seconds real);
"""


@dataclass(frozen=True)
class PerformanceTemplate:
    grp: str
    demo_hash: str
    client: int
    map: str
    start_ms: int
    end_ms: int
    duration_ms: int
    distance_u: float
    heading_delta_deg: float
    ending_stance: str            # IDLE | RUN | AIRBORNE
    weapon: str | None
    airborne_ms: int
    grounded_fraction: float
    features: dict

    @property
    def id(self) -> str:
        return f"TPL:{self.grp}:{self.demo_hash}:{self.client}:{self.start_ms}"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        return d


# ── deriving templates from one trace ──────────────────────────────────────

def _segment(tr: PerformanceTrace, t0: int, t1: int) -> PerformanceTrace:
    seg = PerformanceTrace(tr.demo_hash, tr.map, tr.gametype, tr.client, t0, t1, pov=tr.pov)
    seg.transform = [s for s in tr.transform if t0 <= s.t <= t1]
    seg.aim = [s for s in tr.aim if t0 <= s.t <= t1]
    seg.animation = [s for s in tr.animation if t0 <= s.t <= t1]
    seg.weapon = [w for w in tr.weapon if w.t <= t1]
    seg.projectiles = [p for p in tr.projectiles if t0 <= p.t <= t1]
    seg.events = [e for e in tr.events if t0 <= e.t <= t1]
    return seg


def _facts(tr: PerformanceTrace, t0: int, t1: int) -> dict:
    tf = [s for s in tr.transform if t0 <= s.t <= t1]
    aim = [a for a in tr.aim if t0 <= a.t <= t1]
    if len(tf) < 2:
        return {}
    dist = math.dist(tf[0].origin, tf[-1].origin)
    heading = 0.0
    if aim:
        heading = (aim[-1].yaw - aim[0].yaw + 180.0) % 360.0 - 180.0
    last = tf[-1]
    stance = "AIRBORNE" if last.airborne else ("RUN" if last.speed > STOP_SPEED else "IDLE")
    air = sum(b.t - a.t for a, b in zip(tf, tf[1:]) if a.airborne)
    weapon = None
    for w in tr.weapon:
        if w.t <= t1:
            weapon = AG.WEAPON_KIND.get(w.weapon, str(w.weapon))
    return {"distance_u": round(dist, 1), "heading_delta_deg": round(heading, 1),
            "duration_ms": t1 - t0, "ending_stance": stance, "weapon": weapon,
            "airborne_ms": int(air),
            "grounded_fraction": round(sum(1 for s in tf if not s.airborne) / len(tf), 3),
            "max_speed": round(max(s.speed for s in tf), 1)}


def derive(tr: PerformanceTrace) -> list[PerformanceTemplate]:
    """Every template one trace supports, read off its ActionGraph."""
    g = AG.build(tr)
    cats = AG.categories(g)
    out: list[PerformanceTemplate] = []

    def add(grp: str, t0: int, t1: int, **extra):
        f = _facts(tr, t0, t1)
        if not f or f["duration_ms"] < 100:
            return
        f.update(extra)
        out.append(PerformanceTemplate(
            grp, tr.demo_hash, tr.client, tr.map, t0, t1, f["duration_ms"],
            f["distance_u"], f["heading_delta_deg"], f["ending_stance"], f["weapon"],
            f["airborne_ms"], f["grounded_fraction"], f))

    tf = tr.transform
    for run in g.of_kind("RUN"):
        if run.duration_ms >= 500:
            add("RUN_IN", run.t_start, run.t_end)
        # RUN_STOP: the run ends and the body stays under STOP_SPEED for a hold
        after = [s for s in tf if run.t_end < s.t <= run.t_end + STOP_HOLD_MS]
        if after and all(s.speed <= STOP_SPEED and not s.airborne for s in after):
            add("RUN_STOP", run.t_start, after[-1].t)
            turn = [n for n in g.of_kind("TURN") + g.of_kind("FLICK")
                    if 0 <= n.t_start - run.t_end <= 800]
            if turn:
                add("RUN_IN_STOP_TURN", run.t_start, turn[0].t_end,
                    turn_deg=turn[0].attrs.get("degrees"))
    for n in g.of_kind("TURN") + g.of_kind("FLICK"):
        deg = float(n.attrs.get("degrees", 0.0))
        if 60 <= deg <= 120:
            add("TURN_90", n.t_start, n.t_end, turn_deg=deg)
        elif deg >= 150:
            add("TURN_180", n.t_start, n.t_end, turn_deg=deg)
    for n in g.of_kind("JUMP"):
        air = g.successors(n.id, "launches")
        add("JUMP", n.t_start, air[0].t_end if air else n.t_start + 400)
    for n in g.of_kind("LAND"):
        add("LAND", max(tr.start_ms, n.t_start - 300), min(tr.end_ms, n.t_start + 300))
    for n in g.of_kind("JUMP_PAD"):
        air = g.successors(n.id, "launches")
        end = air[0].t_end if air else n.t_start + 1000
        add("JUMP_PAD", max(tr.start_ms, n.t_start - 300), end, launch_vz=n.attrs.get("launch_vz"))
        if "JUMP_PAD_ROCKET" in cats:
            fires = [f for f in g.of_kind("FIRE") if n.t_start <= f.t_start <= end
                     and f.attrs.get("weapon") == "ROCKET"]
            if fires:
                add("JUMP_PAD_ROCKET", max(tr.start_ms, n.t_start - 300),
                    min(tr.end_ms, fires[-1].t_start + 500), fire_after_pad_ms=fires[0].t_start - n.t_start)
    for cat, grp in (("COMBAT_STRAFE", "COMBAT_STRAFE"), ("RETREAT", "RETREAT"),
                     ("CHASE", "CHASE"), ("RAIL_FLICK", "RAIL_FLICK"),
                     ("ROCKET_PREDICTION", "ROCKET_PREDICTION")):
        if cat in cats:
            nodes = [n for n in g.nodes if n.kind in ("RUN", "APPROACH", "WITHDRAW", "FLICK", "FIRE")]
            t0 = min(n.t_start for n in nodes) if nodes else tr.start_ms
            t1 = max(n.t_end for n in nodes) if nodes else tr.end_ms
            add(grp, t0, max(t1, t0 + 200))
    return out


# ── the library ────────────────────────────────────────────────────────────

def _open(path: Path | None = None) -> sqlite3.Connection:
    path = path or S.template_db()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=60)
    con.executescript(SCHEMA)
    return con


def build(*, limit: int = 3000, map_name: str | None = None,
          kinds: Sequence[str] = ("JUMP_PAD", "FIRE_ROCKET", "FIRE_RAIL", "KILL"),
          db: Path | None = None, verbose: bool = False) -> dict:
    """Derive templates from index traces (sampled per kind) into the
    template DB. Re-runnable: templates are keyed by their stable id."""
    t0 = time.time()
    src = PI._ro()
    con = _open(db)
    scanned = n_tpl = 0
    per_kind = max(1, limit // len(kinds))
    for kind in kinds:
        # grouped by demo so each demo is parsed once for all its windows
        q = "select trace_locator from actions where kind=?"
        args: list = [kind]
        if map_name:
            q += " and map=?"; args.append(map_name)
        q += " order by demo_hash, t_ms limit ?"; args.append(per_kind)
        for (loc,) in src.execute(q, args).fetchall():
            scanned += 1
            try:
                tr = PI.trace_for(loc)
                tpls = derive(tr)
            except Exception:
                continue
            if tpls:
                # a trace that yielded templates is worth keeping: one
                # compressed copy, however many templates point at it
                PI.cache_trace(tr, reason="template")
            for t in tpls:
                con.execute("""insert or replace into templates values
                    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (t.id, t.grp, t.demo_hash, t.client, t.map, t.start_ms, t.end_ms,
                             t.duration_ms, t.distance_u, t.heading_delta_deg, t.ending_stance,
                             t.weapon, t.airborne_ms, t.grounded_fraction,
                             json.dumps(t.features, separators=(",", ":"))))
                n_tpl += 1
        con.commit()
        if verbose:
            print(f"  {kind}: scanned {scanned}, templates {n_tpl}", flush=True)
    con.execute("insert into build_runs values (?,?,?,?)",
                (time.time(), scanned, n_tpl, round(time.time() - t0, 1)))
    con.commit()
    counts = dict(con.execute("select grp, count(*) from templates group by 1").fetchall())
    con.close(); src.close()
    return {"scanned": scanned, "templates": n_tpl, "by_group": counts,
            "seconds": round(time.time() - t0, 1)}


def _row(r) -> PerformanceTemplate:
    return PerformanceTemplate(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
                               r[10], r[11], r[12], r[13], json.loads(r[14]))


def find(grp: str, *, distance: tuple[float, float] | None = None,
         heading_delta: tuple[float, float] | None = None,
         duration_ms: tuple[int, int] | None = None,
         ending_stance: str | None = None, weapon: str | None = None,
         airborne: bool | None = None, map_name: str | None = None,
         limit: int = 5, db: Path | None = None) -> list[PerformanceTemplate]:
    """The closest REAL performances to the constraints. Range constraints
    filter; the result is ranked by distance to each range's centre, in
    units of the range's half-width, so a request is answered by the trace
    that sits nearest the middle of what was asked."""
    if grp not in GROUPS:
        raise KeyError(f"{grp}: not a template group {GROUPS}")
    where, args = ["grp=?"], [grp]
    if map_name:
        where.append("map=?"); args.append(map_name)
    if ending_stance:
        where.append("ending_stance=?"); args.append(ending_stance)
    if weapon:
        where.append("weapon=?"); args.append(weapon)
    if airborne is not None:
        where.append("airborne_ms > 0" if airborne else "airborne_ms = 0")
    for col, rng in (("distance_u", distance), ("heading_delta_deg", heading_delta),
                     ("duration_ms", duration_ms)):
        if rng:
            where.append(f"{col} between ? and ?"); args += [rng[0], rng[1]]
    con = _open(db)
    rows = [_row(r) for r in con.execute(
        f"select * from templates where {' and '.join(where)}", args)]
    con.close()

    def score(t: PerformanceTemplate) -> float:
        s = 0.0
        for val, rng in ((t.distance_u, distance), (t.heading_delta_deg, heading_delta),
                         (t.duration_ms, duration_ms)):
            if rng:
                mid, half = (rng[0] + rng[1]) / 2.0, max(1e-6, (rng[1] - rng[0]) / 2.0)
                s += abs(val - mid) / half
        return s
    return sorted(rows, key=score)[:limit]


def load(tpl: PerformanceTemplate | str, db: Path | None = None) -> PerformanceTrace:
    """The exact segment of the stored trace this template names."""
    if isinstance(tpl, str):
        parts = tpl.split(":")
        if len(parts) != 5 or parts[0] != "TPL":
            raise ValueError(f"not a template id: {tpl!r}")
        con = _open(db)
        r = con.execute("select * from templates where id=?", (tpl,)).fetchone()
        con.close()
        if r is None:
            raise KeyError(tpl)
        tpl = _row(r)
    src = PI._ro()
    row = src.execute("select trace_locator from actions where demo_hash=? and client=? "
                      "and start_ms<=? and end_ms>=? order by abs(t_ms-?) limit 1",
                      (tpl.demo_hash, tpl.client, tpl.start_ms, tpl.end_ms, tpl.start_ms)).fetchone()
    src.close()
    if row is None:
        raise KeyError(f"{tpl.id}: source window no longer in the index")
    return _segment(PI.trace_for(row[0], cache=True, reason="template"), tpl.start_ms, tpl.end_ms)


def counts(db: Path | None = None) -> dict:
    con = _open(db)
    out = dict(con.execute("select grp, count(*) from templates group by 1").fetchall())
    con.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", type=int, default=0, help="derive from N index traces")
    ap.add_argument("--map")
    ap.add_argument("--find")
    ap.add_argument("--distance", nargs=2, type=float)
    ap.add_argument("--duration", nargs=2, type=int)
    ap.add_argument("--heading", nargs=2, type=float)
    ap.add_argument("--stance")
    a = ap.parse_args()
    if a.build:
        print(json.dumps(build(limit=a.build, map_name=a.map, verbose=True), indent=1))
    if a.find:
        for t in find(a.find, distance=tuple(a.distance) if a.distance else None,
                      duration_ms=tuple(a.duration) if a.duration else None,
                      heading_delta=tuple(a.heading) if a.heading else None,
                      ending_stance=a.stance, map_name=a.map):
            print(t.id, t.duration_ms, t.distance_u, t.heading_delta_deg, t.ending_stance, t.weapon)
    if not a.build and not a.find:
        print(json.dumps(counts(), indent=1))
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
