"""PerformanceIndex — every demo, every player, every notable action, in a DB.

WHY THE WHOLE CORPUS. "Find me a clean jump-pad rocket" is a query, not a
scan. Parsing 6,465 demos once and keeping the traces around every notable
action lets that question -- and every later one (rail flick, LG duel, last
man, teleport intercept) -- be answered in milliseconds against SQLite instead
of forty minutes of re-parsing.

WHAT IS INDEXED, per demo, per client:
  * JUMP_PAD   -- an EV_JUMP_PAD *validated by the transform*: the body must
                  actually launch (vel_z > 200 within 150ms). The event alone
                  proved unreliable for the POV client, whose playerstate
                  events carry no clientNum.
  * ROCKET / RAIL / GRENADE fires (EV_FIRE_WEAPON by weapon)
  * KILLS      -- obituaries, keyed by killer, with MOD
  * DEATHS     -- obituaries, keyed by victim
and for each, a PerformanceTrace window (-1.5s .. +2.0s) stored as JSON, plus
derived features a query can filter on: max speed, airborne ms, max yaw rate,
projectile samples, and the outcome chain that follows within 2.5s.

NOTHING IDENTIFYING. Rows carry demo hash and client slot. Names never enter
the database. The .db is gitignored like every other .db in this project.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

MAIN = Path("G:/QUAKE_LEGACY")
if str(MAIN) not in sys.path:
    sys.path.insert(0, str(MAIN))

from engine.pantheon.performance import (  # noqa: E402
    FRAGS_DB, PerformanceTrace, _parse_with_anims, demo_hash,
    extract_performance, recorder_client)

INDEX_DB = MAIN / "creative_suite/database/performance_index.db"
PRE_MS, POST_MS = 1500, 2000
LAUNCH_VZ = 200.0

WEAPON_KIND = {4: "GRENADE", 5: "ROCKET", 7: "RAIL", 6: "LG"}
SCHEMA = """
create table if not exists demos (
  demo_hash text primary key, path text, map text, gametype text,
  recorder_client integer, snapshots integer, indexed_at real, error text);
create table if not exists actions (
  id integer primary key,
  demo_hash text, map text, client integer, is_pov integer,
  kind text, t_ms integer, weapon integer,
  start_ms integer, end_ms integer,
  max_speed real, mean_speed real, airborne_ms integer, max_yaw_rate real,
  projectile_samples integer, samples integer,
  outcome text, outcome_ms integer, victim integer,
  trace_json text);
create index if not exists ix_actions_kind on actions(kind, map);
create index if not exists ix_actions_demo on actions(demo_hash);
"""


def _open() -> sqlite3.Connection:
    INDEX_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(INDEX_DB, timeout=60)
    con.executescript(SCHEMA)
    return con


def _launched(tr: PerformanceTrace, t: int) -> bool:
    """Did the body actually leave the ground at `t`?"""
    return any(abs(s.t - t) <= 150 and s.velocity[2] > LAUNCH_VZ
               for s in tr.transform)


def _outcome(out: dict, client: int, rec: int | None, t: int) -> tuple:
    """What followed a fire within 2.5s, from the server's own events."""
    best = None
    for e in out["events"]:
        dt = e["server_time_ms"] - t
        if not 0 < dt <= 2500:
            continue
        if e["type"] == "obituary" and e.get("killer_client") == client:
            return ("KILL", dt, e.get("victim_client"))
        c = e.get("client_num") if e.get("client_num") is not None else rec
        if e["type"] == "missile_hit" and c == client and best is None:
            best = ("HIT", dt, None)
    return best or ("NONE", None, None)


def index_demo(path: str) -> dict:
    """Parse one demo and return the rows for it (runs in a worker)."""
    p = Path(path)
    t0 = time.time()
    try:
        out, anims = _parse_with_anims(p)
    except Exception as exc:                        # pragma: no cover - corpus
        return {"demo": {"path": path, "error": repr(exc)[:200]}, "actions": []}
    h = demo_hash(p)
    rec = recorder_client(out)
    parsed = (out, anims)
    clients = {e["client_num"] for e in out["entities"] if e["client_num"] is not None}
    if rec is not None:
        clients.add(rec)

    def c_of(e):
        return e.get("client_num") if e.get("client_num") is not None else rec

    rows = []
    seen = set()
    for e in out["events"]:
        kind = None
        c = c_of(e)
        if e["type"] == "jump_pad":
            kind = "JUMP_PAD"
        elif e["type"] == "fire_weapon" and e.get("weapon") in WEAPON_KIND \
                and WEAPON_KIND[e["weapon"]] != "LG":
            kind = f"FIRE_{WEAPON_KIND[e['weapon']]}"
        elif e["type"] == "obituary":
            kind = "KILL"; c = e.get("killer_client")
        if kind is None or c is None or c not in clients:
            continue
        t = e["server_time_ms"]
        key = (c, kind, t // 250)          # one row per quarter second
        if key in seen:
            continue
        seen.add(key)
        try:
            tr = extract_performance(p, t - PRE_MS, t + POST_MS, c, parsed=parsed)
        except Exception:
            continue
        if len(tr.transform) < 10:
            continue
        if kind == "JUMP_PAD" and not _launched(tr, t):
            continue                                # the event lied
        sp = tr.speed_profile()
        outcome, o_ms, victim = _outcome(out, c, rec, t)
        if kind == "KILL":
            outcome, o_ms, victim = "KILL", 0, e.get("victim_client")
        rows.append({
            "demo_hash": h, "map": out["map"], "client": c,
            "is_pov": int(c == rec), "kind": kind, "t_ms": t,
            "weapon": e.get("weapon"),
            "start_ms": t - PRE_MS, "end_ms": t + POST_MS,
            "max_speed": sp.get("max"), "mean_speed": sp.get("mean"),
            "airborne_ms": sp.get("airborne_ms"),
            "max_yaw_rate": max((abs(a.yaw_rate) for a in tr.aim), default=0.0),
            "projectile_samples": len(tr.projectiles),
            "samples": len(tr.transform),
            "outcome": outcome, "outcome_ms": o_ms, "victim": victim,
            "trace_json": json.dumps(tr.as_dict(), separators=(",", ":")),
        })
    return {"demo": {"demo_hash": h, "path": path, "map": out["map"],
                     "gametype": out["gametype"], "recorder_client": rec,
                     "snapshots": out["snapshot_count"],
                     "indexed_at": time.time(), "error": None,
                     "seconds": round(time.time() - t0, 1)},
            "actions": rows}


def _store(con: sqlite3.Connection, res: dict) -> int:
    d = res["demo"]
    if d.get("error"):
        con.execute("insert or replace into demos(path, error, indexed_at) values(?,?,?)",
                    (d["path"], d["error"], time.time()))
        con.commit()
        return 0
    con.execute("delete from actions where demo_hash=?", (d["demo_hash"],))
    con.execute("""insert or replace into demos values(?,?,?,?,?,?,?,?)""",
                (d["demo_hash"], d["path"], d["map"], d["gametype"],
                 d["recorder_client"], d["snapshots"], d["indexed_at"], None))
    con.executemany("""insert into actions(demo_hash,map,client,is_pov,kind,t_ms,weapon,
        start_ms,end_ms,max_speed,mean_speed,airborne_ms,max_yaw_rate,
        projectile_samples,samples,outcome,outcome_ms,victim,trace_json)
        values(:demo_hash,:map,:client,:is_pov,:kind,:t_ms,:weapon,:start_ms,:end_ms,
        :max_speed,:mean_speed,:airborne_ms,:max_yaw_rate,:projectile_samples,
        :samples,:outcome,:outcome_ms,:victim,:trace_json)""", res["actions"])
    con.commit()
    return len(res["actions"])


def corpus_paths(limit: int | None = None, maps: tuple = ()) -> list[str]:
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    q = "select path from demos where gametype in ('CA','DUEL','FFA','TDM')"
    args: list = []
    if maps:
        q += " and map_name in (%s)" % ",".join("?" * len(maps)); args += list(maps)
    q += " order by size_bytes"
    if limit:
        q += " limit ?"; args.append(limit)
    rows = [r[0] for r in con.execute(q, args)]
    con.close()
    return [r for r in rows if Path(r).exists()]


def already_indexed() -> set[str]:
    con = _open()
    done = {r[0] for r in con.execute("select path from demos where error is null")}
    con.close()
    return done


def run(paths: list[str], *, workers: int = 6) -> None:
    con = _open()
    done = already_indexed()
    todo = [p for p in paths if p not in done]
    print(f"{len(paths)} demos, {len(todo)} to index, {workers} workers", flush=True)
    n_rows = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(index_demo, p): p for p in todo}
        for i, f in enumerate(as_completed(futs), 1):
            res = f.result()
            n_rows += _store(con, res)
            d = res["demo"]
            if i % 10 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] rows={n_rows} "
                      f"{(time.time() - t0) / 60:.1f} min "
                      f"last={d.get('map')} {d.get('seconds')}s "
                      f"{'ERR ' + d['error'] if d.get('error') else ''}", flush=True)
    con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--maps", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    run(corpus_paths(a.limit, tuple(a.maps)), workers=a.workers)
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
