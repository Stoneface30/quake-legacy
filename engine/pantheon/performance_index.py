"""PerformanceIndex v2 — discovery over every demo, without duplicating truth.

THE FIRST INDEX FILLED A DRIVE. Every action row carried its whole
PerformanceTrace as JSON, ~45 KB, two million times: 94 GB, and it never
finished. Action indexing and trace storage are two problems; this module
solves the first and refuses to solve the second by copying.

    PerformanceIndex  = DISCOVERY   lightweight rows: who, when, what, how fast
    PerformanceTrace  = TRUTH       reconstructed from the demo on demand,
                                    exactly as headless.extract_performance
                                    already does, from the same parsed
                                    authority
    trace cache       = OPTIONAL    content-addressed, compressed, for the
                                    traces worth keeping (templates, golden
                                    cases, chosen performances); one copy per
                                    distinct trace, never one per action

WHAT A ROW HOLDS. The stable identity, the window, the kind, the outcome,
summary movement / aim / projectile features, the event chain as a few small
tuples, the grounded path as packed 64-unit cells (so map geography needs no
trace at all), provenance, and a `trace_locator` that names the demo, client
and window from which the trace is rebuilt.

STABLE IDENTITY. `PERF:<kind>:<demo_hash>:<client>:<t_ms>` -- the source
demo, the actor slot, the event tick, the index kind. A rebuild of unchanged
demos produces identical ids; the SQLite rowid is internal and never leaves
the database.

ALL 4,292 DISTINCT DEMOS. The first index only accepted CA/DUEL/FFA/TDM and
the parser labels team games TEAM, so 38 demos (15 TEAM, 21 CTF, 1
ATTACK_AND_DEFEND, 1 REDROVER) were never eligible. There is no gametype
filter here: a performance is a performance in any mode. Byte-identical
copies are already collapsed by the corpus catalogue (one row per content
hash), so nothing is indexed twice.

RESUMABLE, CHECKPOINTED, VERSIONED. Every demo row carries the index version;
a run skips demos already at the current version and records a checkpoint
per demo, so a crash or a full disk loses one demo, not a night.

NOTHING IDENTIFYING. Rows carry demo hash and client slot. Names never enter
the database.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import struct
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence

from engine.pantheon import store as S

MAIN = S.REPO_ROOT
if str(MAIN) not in sys.path:
    sys.path.insert(0, str(MAIN))

from engine.pantheon.performance import (  # noqa: E402
    PerformanceTrace, _parse_with_anims, demo_hash, extract_performance,
    recorder_client)

INDEX_VERSION = "performance-index-v2.0.0"
PRE_MS, POST_MS = 1500, 2000
LAUNCH_VZ = 200.0
CELL = 64.0
WEAPON_KIND = {4: "GRENADE", 5: "ROCKET", 7: "RAIL", 6: "LG", 8: "PLASMA"}
INDEX_KINDS = ("JUMP_PAD", "FIRE_ROCKET", "FIRE_RAIL", "FIRE_GRENADE", "KILL",
               "TELEPORT", "WEAPON_CHANGE")

SCHEMA = """
create table if not exists demos (
  demo_hash text primary key, content_hash text, path text, map text, gametype text,
  recorder_client integer, snapshots integer, clients integer,
  indexed_at real, seconds real, version text, error text);
create table if not exists actions (
  performance_id text primary key,
  demo_hash text not null, client integer not null, is_pov integer not null,
  kind text not null, t_ms integer not null, start_ms integer not null, end_ms integer not null,
  weapon text, map text,
  outcome text, outcome_ms integer, victim integer,
  samples integer, gap_ms integer,
  max_speed real, mean_speed real, airborne_ms integer, distance_u real, heading_delta_deg real,
  max_yaw_rate real, yaw_travel_deg real,
  projectile_n integer, projectile_weapon text, projectile_samples integer,
  events_json text, path_cells blob, origin_x real, origin_y real, origin_z real,
  landing_x real, landing_y real, landing_z real,
  provenance text not null, trace_locator text not null);
create index if not exists ix_actions_kind_map on actions(kind, map);
create index if not exists ix_actions_demo on actions(demo_hash, client, t_ms);
create index if not exists ix_actions_map on actions(map, kind);
create table if not exists checkpoints (
  run_id text, at real, demos_done integer, actions integer, version text);
create table if not exists meta (key text primary key, value text);
"""

CACHE_SCHEMA = """
create table if not exists traces (
  content_key text primary key,
  locator text not null, demo_hash text, client integer, start_ms integer, end_ms integer,
  samples integer, raw_bytes integer, blob blob not null, reason text, created_at real);
create index if not exists ix_traces_locator on traces(locator);
"""


# ── connections ────────────────────────────────────────────────────────────

def _open(path: Path | None = None) -> sqlite3.Connection:
    path = path or S.index_db()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=120)
    con.execute("pragma journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def _ro(path: Path | None = None) -> sqlite3.Connection:
    path = path or S.index_db()
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=120)


# ── identity ───────────────────────────────────────────────────────────────

def performance_id(kind: str, demo_hash_: str, client: int, t_ms: int) -> str:
    return f"PERF:{kind}:{demo_hash_}:{client}:{t_ms}"


def locator(demo_hash_: str, client: int, start_ms: int, end_ms: int) -> str:
    return f"demo:{demo_hash_}:{client}:{start_ms}:{end_ms}"


def parse_locator(loc: str) -> tuple[str, int, int, int]:
    p = loc.split(":")
    if len(p) != 5 or p[0] != "demo":
        raise ValueError(f"not a trace locator: {loc!r}")
    return p[1], int(p[2]), int(p[3]), int(p[4])


# ── summaries: what a row keeps instead of the trace ───────────────────────

def pack_cells(cells: Sequence[tuple[int, int, int]]) -> bytes:
    """Distinct grounded 64u cells in visiting order, as int16 triples."""
    out: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for c in cells:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return struct.pack(f"<{3 * len(out)}h", *[v for c in out for v in c])


def unpack_cells(blob: bytes | None) -> list[tuple[int, int, int]]:
    if not blob:
        return []
    n = len(blob) // 6
    vals = struct.unpack(f"<{3 * n}h", blob[:6 * n])
    return [(vals[i], vals[i + 1], vals[i + 2]) for i in range(0, 3 * n, 3)]


def summarize(tr: PerformanceTrace, t_ms: int) -> dict:
    tf = tr.transform
    if not tf:
        return {}
    speeds = [s.speed for s in tf]
    times = [s.t for s in tf]
    gap = max((b - a for a, b in zip(times, times[1:])), default=0)
    airborne = sum(b.t - a.t for a, b in zip(tf, tf[1:]) if a.airborne)
    heading = 0.0
    if tr.aim:
        heading = (tr.aim[-1].yaw - tr.aim[0].yaw + 180.0) % 360.0 - 180.0
    yaw_travel = sum(abs((b.yaw - a.yaw + 180.0) % 360.0 - 180.0)
                     for a, b in zip(tr.aim, tr.aim[1:]))
    cells = [(math.floor(s.origin[0] / CELL), math.floor(s.origin[1] / CELL),
              math.floor(s.origin[2] / CELL)) for s in tf if not s.airborne]
    at = min(tf, key=lambda s: abs(s.t - t_ms))
    landing = None
    launched = False
    for s in tf:
        if abs(s.t - t_ms) <= 150 and s.velocity[2] > LAUNCH_VZ:
            launched = True
        if launched and not s.airborne and s.t > t_ms + 150:
            landing = s.origin
            break
    pj_weapons = sorted({p.weapon for p in tr.projectiles})
    return {
        "samples": len(tf), "gap_ms": int(gap),
        "max_speed": round(max(speeds), 1), "mean_speed": round(sum(speeds) / len(speeds), 1),
        "airborne_ms": int(airborne),
        "distance_u": round(math.dist(tf[0].origin, tf[-1].origin), 1),
        "heading_delta_deg": round(heading, 1),
        "max_yaw_rate": round(max((abs(a.yaw_rate) for a in tr.aim), default=0.0), 1),
        "yaw_travel_deg": round(yaw_travel, 1),
        "projectile_n": len({p.entity for p in tr.projectiles}),
        "projectile_weapon": ",".join(WEAPON_KIND.get(w, str(w)) for w in pj_weapons) or None,
        "projectile_samples": len(tr.projectiles),
        "events_json": json.dumps([[e.t - tr.start_ms, e.kind, e.code] for e in tr.events],
                                  separators=(",", ":")),
        "path_cells": pack_cells(cells),
        "origin": at.origin, "landing": landing,
        "launched": launched,
        "provenance": "OBSERVED:playerstate" if tr.pov else "OBSERVED:entity",
    }


# ── one demo ───────────────────────────────────────────────────────────────

def index_demo(path: str) -> dict:
    """Parse one demo once; return lightweight rows (runs in a worker)."""
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

    anchors: list[tuple[str, int, int, dict]] = []      # (kind, client, t, event)
    for e in out["events"]:
        kind, c = None, c_of(e)
        if e["type"] == "jump_pad":
            kind = "JUMP_PAD"
        elif e["type"] == "fire_weapon" and e.get("weapon") in (4, 5, 7):
            kind = f"FIRE_{WEAPON_KIND[e['weapon']]}"
        elif e["type"] == "obituary":
            kind, c = "KILL", e.get("killer_client")
        elif e["type"] == "change_weapon":
            kind = "WEAPON_CHANGE"
        if kind and c is not None and c in clients:
            anchors.append((kind, c, e["server_time_ms"], e))
    # teleports: confirmed transits only, attributed by the traveller's own
    # discontinuity inside extract_performance; the anchor is the tick
    for te in out.get("temp_events", []):
        if te["code"] == 40 and te["client"] in clients:          # EV_PLAYER_TELEPORT_OUT
            anchors.append(("TELEPORT", te["client"], te["t"], {"weapon": None}))

    # PER-CLIENT VIEWS. extract_performance filters the whole demo by client
    # for every window; with ~800 anchors and ~50k entity rows per demo that
    # rescan was the entire cost of the first full build (55 s per demo).
    # The same rows, partitioned once, give the same trace at a fraction of
    # the work. Events and temp events stay whole: the extractor decides
    # whose they are.
    ents_by: dict[int, list] = {}
    for row in out["entities"]:
        if row["client_num"] is not None:
            ents_by.setdefault(row["client_num"], []).append(row)
    anims_by: dict[int, list] = {}
    for a in anims:
        anims_by.setdefault(a["client"], []).append(a)
    missiles_by: dict[int, list] = {}
    for m in out["missiles"]:
        missiles_by.setdefault(m.get("other"), []).append(m)
    import bisect
    # ...and per WINDOW: every list is sorted on serverTime, so an anchor's
    # window is two bisects, not a scan. The extractor still filters by
    # client and by window itself; it just receives only what can match.
    for lst in ents_by.values():
        lst.sort(key=lambda r: r["server_time_ms"])
    for lst in anims_by.values():
        lst.sort(key=lambda a: a["t"])
    for lst in missiles_by.values():
        lst.sort(key=lambda m: m["server_time_ms"])
    keyed = {
        c: ([r["server_time_ms"] for r in ents_by.get(c, [])],
            [a["t"] for a in anims_by.get(c, [])],
            [m["server_time_ms"] for m in missiles_by.get(c, [])])
        for c in clients}
    events_sorted = sorted(out["events"], key=lambda e: e["server_time_ms"])
    ev_times = [e["server_time_ms"] for e in events_sorted]
    temps_sorted = sorted(out.get("temp_events", []), key=lambda t: t["t"])
    temp_times = [t["t"] for t in temps_sorted]
    rec_track = out.get("recorder_track", [])
    rec_times = [r["t"] for r in rec_track]

    def window(lst, times, lo, hi):
        return lst[bisect.bisect_left(times, lo):bisect.bisect_right(times, hi)]

    def view(c: int, lo: int, hi: int) -> tuple:
        et, at, mt = keyed[c]
        o = dict(out)
        o["entities"] = window(ents_by.get(c, []), et, lo, hi)
        o["missiles"] = window(missiles_by.get(c, []), mt, lo, hi)
        o["events"] = window(events_sorted, ev_times, lo, hi)
        o["temp_events"] = window(temps_sorted, temp_times, lo, hi)
        # the recorder is identified from the FIRST playerstate row, which
        # may lie outside the window; keep it in front, windowed rows after
        o["recorder_track"] = rec_track[:1] + (window(rec_track, rec_times, lo, hi)
                                               if c == rec else [])
        return o, window(anims_by.get(c, []), at, lo, hi)

    def outcome_fast(c: int, t: int) -> tuple:
        i = bisect.bisect_right(ev_times, t)
        j = bisect.bisect_right(ev_times, t + 2500)
        best = None
        for e in events_sorted[i:j]:
            if e["type"] == "obituary" and e.get("killer_client") == c:
                return ("KILL", e["server_time_ms"] - t, e.get("victim_client"))
            cc = e.get("client_num") if e.get("client_num") is not None else rec
            if e["type"] == "missile_hit" and cc == c and best is None:
                best = ("HIT", e["server_time_ms"] - t, None)
        return best or ("NONE", None, None)

    rows, seen = [], set()
    for kind, c, t, e in sorted(anchors, key=lambda a: (a[2], a[0])):
        key = (c, kind, t // 250)
        if key in seen:
            continue
        seen.add(key)
        lo, hi = t - PRE_MS, t + POST_MS
        try:
            tr = extract_performance(p, lo, hi, c, parsed=view(c, lo, hi))
        except Exception:
            continue
        if len(tr.transform) < 10:
            continue
        sm = summarize(tr, t)
        if kind == "JUMP_PAD" and not sm["launched"]:
            continue                                # the event lied
        if kind == "TELEPORT" and not tr.of_kind("teleport_out"):
            continue                                # not this client's transit
        outcome, o_ms, victim = outcome_fast(c, t)
        if kind == "KILL":
            outcome, o_ms, victim = "KILL", 0, e.get("victim_client")
        rows.append({
            "performance_id": performance_id(kind, h, c, t),
            "demo_hash": h, "client": c, "is_pov": int(c == rec), "kind": kind, "t_ms": t,
            "start_ms": lo, "end_ms": hi,
            "weapon": WEAPON_KIND.get(e.get("weapon")) if e.get("weapon") in WEAPON_KIND else (
                str(e.get("weapon")) if e.get("weapon") is not None else None),
            "map": out["map"], "outcome": outcome, "outcome_ms": o_ms, "victim": victim,
            **{k: sm[k] for k in ("samples", "gap_ms", "max_speed", "mean_speed", "airborne_ms",
                                  "distance_u", "heading_delta_deg", "max_yaw_rate",
                                  "yaw_travel_deg", "projectile_n", "projectile_weapon",
                                  "projectile_samples", "events_json", "path_cells")},
            "origin_x": sm["origin"][0], "origin_y": sm["origin"][1], "origin_z": sm["origin"][2],
            "landing_x": sm["landing"][0] if sm["landing"] else None,
            "landing_y": sm["landing"][1] if sm["landing"] else None,
            "landing_z": sm["landing"][2] if sm["landing"] else None,
            "provenance": sm["provenance"],
            "trace_locator": locator(h, c, lo, hi),
        })
    return {"demo": {"demo_hash": h, "path": path, "map": out["map"],
                     "gametype": out["gametype"], "recorder_client": rec,
                     "snapshots": out["snapshot_count"], "clients": len(clients),
                     "indexed_at": time.time(), "seconds": round(time.time() - t0, 1),
                     "error": None},
            "actions": rows}


def _store(con: sqlite3.Connection, res: dict, content_hash: str | None) -> int:
    d = res["demo"]
    if d.get("error"):
        con.execute("insert or replace into demos(demo_hash, content_hash, path, error, indexed_at, version) "
                    "values(?,?,?,?,?,?)", ((content_hash or "")[:16] or d["path"], content_hash,
                                            d["path"], d["error"], time.time(), INDEX_VERSION))
        con.commit()
        return 0
    con.execute("delete from actions where demo_hash=?", (d["demo_hash"],))
    con.execute("insert or replace into demos values(?,?,?,?,?,?,?,?,?,?,?,?)",
                (d["demo_hash"], content_hash, d["path"], d["map"], d["gametype"],
                 d["recorder_client"], d["snapshots"], d["clients"], d["indexed_at"],
                 d["seconds"], INDEX_VERSION, None))
    cols = ["performance_id", "demo_hash", "client", "is_pov", "kind", "t_ms", "start_ms", "end_ms",
            "weapon", "map", "outcome", "outcome_ms", "victim", "samples", "gap_ms", "max_speed",
            "mean_speed", "airborne_ms", "distance_u", "heading_delta_deg", "max_yaw_rate",
            "yaw_travel_deg", "projectile_n", "projectile_weapon", "projectile_samples",
            "events_json", "path_cells", "origin_x", "origin_y", "origin_z",
            "landing_x", "landing_y", "landing_z", "provenance", "trace_locator"]
    con.executemany(f"insert or replace into actions({','.join(cols)}) values({','.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in res["actions"]])
    con.commit()
    return len(res["actions"])


# ── the corpus ─────────────────────────────────────────────────────────────

def corpus() -> list[tuple[str, str]]:
    """(content_hash, path) for every DISTINCT demo in the catalogue, any
    gametype. Missing files are reported by the caller, never skipped
    silently."""
    con = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute("select content_hash, path from demos where content_hash is not null "
                       "order by size_bytes").fetchall()
    con.close()
    return [(h, p) for h, p in rows]


def already_done(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute(
        "select content_hash from demos where error is null and version=?", (INDEX_VERSION,))}


def run(*, workers: int = 6, limit: int | None = None, maps: Sequence[str] = ()) -> dict:
    from engine.pantheon import disk_policy
    disk = disk_policy.large_build_safe(S.store_root(), required_bytes=disk_policy.LARGE_BUILD_SAFE // 4)
    if not disk.ok:
        raise RuntimeError(f"index build refused: {disk.reason}")
    con = _open()
    done = already_done(con)
    todo, missing = [], []
    for h, p in corpus():
        if h in done:
            continue
        if not Path(p).exists():
            missing.append((h, p))
            continue
        todo.append((h, p))
    if maps:
        fr = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True)
        ok = {r[0] for r in fr.execute(
            f"select content_hash from demos where map_name in ({','.join('?' * len(maps))})", maps)}
        fr.close()
        todo = [(h, p) for h, p in todo if h in ok]
    if limit:
        todo = todo[:limit]
    for h, p in missing:
        con.execute("insert or replace into demos(demo_hash, content_hash, path, error, indexed_at, version) "
                    "values(?,?,?,?,?,?)", (h[:16], h, p, "MISSING_FILE", time.time(), INDEX_VERSION))
    con.commit()
    run_id = hashlib.sha1(f"{time.time()}".encode()).hexdigest()[:8]
    print(f"{len(done)} done, {len(todo)} to index, {len(missing)} missing, {workers} workers "
          f"-> {S.index_db()}", flush=True)
    n_rows, t0 = 0, time.time()
    by_path = {p: h for h, p in todo}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(index_demo, p): p for _, p in todo}
        for i, f in enumerate(as_completed(futs), 1):
            res = f.result()
            n_rows += _store(con, res, by_path.get(futs[f]))
            if i % 10 == 0 or i == len(todo):
                con.execute("insert into checkpoints values(?,?,?,?,?)",
                            (run_id, time.time(), i, n_rows, INDEX_VERSION))
                con.commit()
                d = res["demo"]
                print(f"  [{i}/{len(todo)}] rows={n_rows} {(time.time() - t0) / 60:.1f} min "
                      f"last={d.get('map')} {d.get('seconds')}s "
                      f"{'ERR ' + d['error'] if d.get('error') else ''}", flush=True)
    con.close()
    return {"done_before": len(done), "indexed": len(todo), "missing": len(missing),
            "rows": n_rows, "seconds": round(time.time() - t0, 1)}


# ── traces: reconstructed, optionally cached ───────────────────────────────

_PARSE_CACHE: dict[str, tuple] = {}


def demo_path(demo_hash_: str) -> Path:
    con = _ro()
    row = con.execute("select path from demos where demo_hash=?", (demo_hash_,)).fetchone()
    con.close()
    if row is None:
        raise KeyError(demo_hash_)
    return Path(row[0])


def reconstruct(loc: str) -> PerformanceTrace:
    """The trace a locator names, from the demo itself (the truth), with the
    parse cached per process so one demo's many actions cost one parse."""
    h, client, lo, hi = parse_locator(loc)
    p = demo_path(h)
    key = str(p)
    if key not in _PARSE_CACHE:
        if len(_PARSE_CACHE) >= 4:
            _PARSE_CACHE.clear()
        _PARSE_CACHE[key] = _parse_with_anims(p)
    return extract_performance(p, lo, hi, client, parsed=_PARSE_CACHE[key])


def _cache_open() -> sqlite3.Connection:
    path = S.trace_cache_db()
    con = sqlite3.connect(path, timeout=120)
    con.executescript(CACHE_SCHEMA)
    return con


def content_key(tr: PerformanceTrace) -> str:
    raw = json.dumps(tr.as_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha1(raw).hexdigest()


def cache_trace(tr: PerformanceTrace, *, reason: str) -> str:
    """Keep this trace: one compressed copy per distinct content, however
    many actions or templates point at it."""
    raw = json.dumps(tr.as_dict(), sort_keys=True, separators=(",", ":")).encode()
    key = hashlib.sha1(raw).hexdigest()
    con = _cache_open()
    if con.execute("select 1 from traces where content_key=?", (key,)).fetchone() is None:
        con.execute("insert into traces values(?,?,?,?,?,?,?,?,?,?,?)",
                    (key, locator(tr.demo_hash, tr.client, tr.start_ms, tr.end_ms), tr.demo_hash,
                     tr.client, tr.start_ms, tr.end_ms, len(tr.transform), len(raw),
                     zlib.compress(raw, 9), reason, time.time()))
        con.commit()
    con.close()
    return key


def cached(loc: str) -> PerformanceTrace | None:
    con = _cache_open()
    row = con.execute("select blob from traces where locator=? order by created_at desc limit 1",
                      (loc,)).fetchone()
    con.close()
    if row is None:
        return None
    return PerformanceTrace.from_dict(json.loads(zlib.decompress(row[0])))


def trace_for(loc: str, *, cache: bool = False, reason: str = "requested") -> PerformanceTrace:
    tr = cached(loc)
    if tr is not None:
        return tr
    tr = reconstruct(loc)
    if cache:
        cache_trace(tr, reason=reason)
    return tr


# ── measurement ────────────────────────────────────────────────────────────

def stats() -> dict:
    out: dict = {"index_db": str(S.index_db()), "trace_cache_db": str(S.trace_cache_db())}
    con = _ro()
    n = con.execute("select count(*) from actions").fetchone()[0]
    d = con.execute("select count(*) from demos where error is null").fetchone()[0]
    size = S.index_db().stat().st_size if S.index_db().exists() else 0
    wal = S.index_db().with_name(S.index_db().name + "-wal")
    size += wal.stat().st_size if wal.exists() else 0
    out.update({"demos": d, "actions": n, "index_bytes": size,
                "bytes_per_action": round(size / n, 1) if n else None})
    try:
        con.execute("select 1 from dbstat limit 1")
        out["largest"] = [(r[0], r[1]) for r in con.execute(
            "select name, sum(pgsize) b from dbstat group by name order by b desc limit 6")]
    except sqlite3.OperationalError:
        pass
    con.close()
    cache_path = S.trace_cache_db()
    if cache_path.exists():
        c = sqlite3.connect(f"file:{cache_path.as_posix()}?mode=ro", uri=True)
        k, raw, comp = c.execute("select count(*), coalesce(sum(raw_bytes),0), "
                                 "coalesce(sum(length(blob)),0) from traces").fetchone()
        c.close()
        out["trace_cache"] = {"traces": k, "raw_bytes": raw, "compressed_bytes": comp,
                              "ratio": round(raw / comp, 1) if comp else None,
                              "file_bytes": cache_path.stat().st_size}
    legacy = S.legacy_index_db()
    if legacy.exists():
        out["legacy_index_bytes"] = legacy.stat().st_size
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--maps", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.stats:
        print(json.dumps(stats(), indent=1))
        return 0
    print(json.dumps(run(workers=a.workers, limit=a.limit, maps=tuple(a.maps)), indent=1))
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
