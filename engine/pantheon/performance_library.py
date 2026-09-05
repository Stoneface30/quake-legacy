"""PerformanceLibrary — reusable, anonymous performance references.

A director asks for "a jump-pad rocket on campgrounds" and gets back a list
of PERF references, each a real recorded action, none of them a person:

    PERF:JUMPPAD_ROCKET:4db16c445bcaafce:5:1198725

That is category, demo hash (16 hex), client slot and serverTime. Loading a
reference yields the PerformanceTrace the index stored; casting it onto a
character is `headless.compile_performance(trace, cast=...)`. The trace never
carried a name and this module never adds one.

TWO SPEEDS. Coarse categories come straight out of the index in SQL -- they
are relations between rows the index already keyed (a JUMP_PAD followed by a
FIRE_ROCKET by the same client while airborne) -- so a full-corpus count is a
query. Fine categories (RAIL_FLICK, TURN_AND_FIRE, COMBAT_STRAFE, ...) need
the trace read through ActionGraph and are computed per reference on demand.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from engine.pantheon import action_graph as AG
from engine.pantheon.performance import PerformanceTrace

INDEX_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/performance_index.db")
PREFIX = "PERF"

# category -> SQL over `actions` (a AS the anchor row). Every rule names the
# index rows it relates; none reads a label alone.
COARSE_SQL = {
    "JUMP_PAD": "a.kind='JUMP_PAD'",
    "JUMP_PAD_KILL": "a.kind='JUMP_PAD' and a.outcome='KILL'",
    "JUMP_PAD_ROCKET": ("a.kind='JUMP_PAD' and exists (select 1 from actions f where "
                        "f.demo_hash=a.demo_hash and f.client=a.client and f.kind='FIRE_ROCKET' "
                        "and f.t_ms between a.t_ms and a.t_ms + 2500)"),
    "ROCKET_AIR_ACTION": "a.kind='FIRE_ROCKET' and a.airborne_ms >= 400 and a.outcome in ('HIT','KILL')",
    "ROCKET_PREDICTION": "a.kind='FIRE_ROCKET' and a.outcome='KILL' and a.outcome_ms >= 600",
    "RAIL_FLICK": "a.kind='FIRE_RAIL' and a.max_yaw_rate >= 360 and a.outcome in ('HIT','KILL')",
    "HIGH_SPEED": "a.max_speed >= 600",
    "WEAPON_SWITCH_ATTACK": "a.kind like 'FIRE_%' and a.outcome in ('HIT','KILL') and a.projectile_samples >= 0 and a.weapon is not null and exists (select 1 from actions w where w.demo_hash=a.demo_hash and w.client=a.client and w.kind like 'FIRE_%' and w.weapon<>a.weapon and w.t_ms between a.t_ms-1500 and a.t_ms-1)",
}
FINE = ("TURN_AND_FIRE", "COMBAT_STRAFE", "TELEPORT_ATTACK", "RETREAT", "CHASE")


@dataclass(frozen=True)
class PerformanceRef:
    category: str
    demo_hash: str
    client: int
    t_ms: int
    map: str = ""
    features: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def id(self) -> str:
        return f"{PREFIX}:{self.category}:{self.demo_hash}:{self.client}:{self.t_ms}"

    @classmethod
    def parse(cls, ref: str) -> "PerformanceRef":
        parts = ref.split(":")
        if len(parts) != 5 or parts[0] != PREFIX:
            raise ValueError(f"not a performance reference: {ref!r}")
        return cls(parts[1], parts[2], int(parts[3]), int(parts[4]))

    def as_dict(self) -> dict:
        return {"id": self.id, "category": self.category, "demo_hash": self.demo_hash,
                "client": self.client, "t_ms": self.t_ms, "map": self.map,
                "features": self.features}


def _open() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=30)


def find(category: str, *, map_name: str | None = None, limit: int = 20,
         pov_only: bool = False) -> list[PerformanceRef]:
    """References for a coarse category, best-featured first."""
    if category not in COARSE_SQL:
        raise KeyError(f"{category}: not a coarse category; fine categories "
                       f"{FINE} are read per trace with categorize()")
    where = COARSE_SQL[category]
    args: list = []
    if map_name:
        where += " and a.map=?"; args.append(map_name)
    if pov_only:
        where += " and a.is_pov=1"
    order = ("a.outcome='KILL' desc, a.airborne_ms desc, a.max_yaw_rate desc"
             if category.startswith("JUMP") else "a.outcome='KILL' desc, a.max_yaw_rate desc")
    con = _open()
    rows = con.execute(
        f"select a.demo_hash, a.client, a.t_ms, a.map, a.kind, a.outcome, a.outcome_ms, "
        f"a.max_speed, a.airborne_ms, a.max_yaw_rate, a.projectile_samples, a.is_pov "
        f"from actions a where {where} order by {order} limit ?", (*args, limit)).fetchall()
    con.close()
    return [PerformanceRef(category, r[0], r[1], r[2], r[3],
                           {"kind": r[4], "outcome": r[5], "outcome_ms": r[6],
                            "max_speed": r[7], "airborne_ms": r[8],
                            "max_yaw_rate": r[9], "projectile_samples": r[10],
                            "pov": bool(r[11])})
            for r in rows]


def load(ref: PerformanceRef | str) -> PerformanceTrace:
    """The stored trace for a reference: the nearest indexed window of that
    client in that demo to the reference time."""
    if isinstance(ref, str):
        ref = PerformanceRef.parse(ref)
    con = _open()
    row = con.execute(
        "select trace_json from actions where demo_hash=? and client=? "
        "order by abs(t_ms-?) limit 1", (ref.demo_hash, ref.client, ref.t_ms)).fetchone()
    con.close()
    if row is None:
        raise KeyError(f"{ref.id}: not in the index")
    return PerformanceTrace.from_dict(json.loads(row[0]))


def demo_path(demo_hash: str) -> Path:
    con = _open()
    row = con.execute("select path from demos where demo_hash=?", (demo_hash,)).fetchone()
    con.close()
    if row is None:
        raise KeyError(demo_hash)
    return Path(row[0])


def categorize(trace: PerformanceTrace) -> set[str]:
    """Fine categories, from the ActionGraph of the trace."""
    return AG.categories(AG.build(trace))


def counts(*, map_name: str | None = None) -> dict:
    """Full-corpus counts per coarse category, straight from SQL."""
    con = _open()
    out: dict = {"demos_indexed": con.execute(
        "select count(*) from demos where error is null").fetchone()[0],
        "actions": con.execute("select count(*) from actions").fetchone()[0],
        "by_kind": dict(con.execute("select kind, count(*) from actions group by 1").fetchall()),
        "by_kind_outcome": {f"{k}:{o}": n for k, o, n in con.execute(
            "select kind, outcome, count(*) from actions group by 1, 2")},
        "categories": {}}
    for cat, where in COARSE_SQL.items():
        args: list = []
        w = where
        if map_name:
            w += " and a.map=?"; args.append(map_name)
        out["categories"][cat] = con.execute(
            f"select count(*) from actions a where {w}", args).fetchone()[0]
    con.close()
    return out


def sample_fine_categories(*, limit: int = 200, map_name: str | None = None) -> dict:
    """Fine-category counts over a sample of stored traces, read through the
    ActionGraph. A sample, and labelled as one: the full-corpus number needs
    the materialised pass (`--materialize`), which is a batch job."""
    con = _open()
    q = "select trace_json from actions"
    args: list = []
    if map_name:
        q += " where map=?"; args.append(map_name)
    q += " order by id desc limit ?"; args.append(limit)
    tally: dict[str, int] = {}
    n = 0
    for (tj,) in con.execute(q, args):
        tr = PerformanceTrace.from_dict(json.loads(tj))
        n += 1
        for c in categorize(tr):
            tally[c] = tally.get(c, 0) + 1
    con.close()
    return {"sampled": n, "categories": dict(sorted(tally.items()))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("category", nargs="?")
    ap.add_argument("--map")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--sample-fine", type=int, default=0)
    a = ap.parse_args()
    if a.counts:
        print(json.dumps(counts(map_name=a.map), indent=1))
    if a.sample_fine:
        print(json.dumps(sample_fine_categories(limit=a.sample_fine, map_name=a.map), indent=1))
    if a.category:
        for r in find(a.category, map_name=a.map, limit=a.limit):
            print(r.id, r.map, r.features)
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
