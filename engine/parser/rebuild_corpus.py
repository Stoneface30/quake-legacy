"""Rebuild the frag database from the whole demo corpus with the certified parser.

The existing frags.db was built before the packet-dispatch fix, when `_dispatch`
consumed only the first service message of each packet and every snapshot that
followed a serverCommand was discarded. Old demos yielded 0-3 kills where they
actually hold 100-300. That database is not repairable by patching; it is
rebuilt from zero.

Design notes that matter:

  DEDUPE BY CONTENT.  The corpus contains byte-identical demos under different
  names ("Demo (4).dm_73" and "Demo (4)_1.dm_73" produce identical output). A
  path-keyed rebuild would double-count them into the statistics.

  WORKERS PARSE, MAIN WRITES.  SQLite does not want concurrent writers, so the
  pool returns compact records and this process performs every insert.

  RESUMABLE.  Demos already recorded for this parser version are skipped, so an
  interrupted overnight run continues instead of restarting.

  FAILURES ARE DATA.  A demo that will not parse is recorded with its error and
  surfaced in the outlier report, never silently dropped.

    python engine/parser/rebuild_corpus.py --workers 8
    python engine/parser/rebuild_corpus.py --limit 50 --db /tmp/test.db
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

DEFAULT_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"
DEMO_ROOT = REPO / "demos"
SCHEMA_VERSION = "frags-rebuild-2"

_COLOR = re.compile(r"\^\d")


def strip_colors(name) -> str:
    return _COLOR.sub("", name or "").strip()


def parser_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                              capture_output=True, text=True,
                              timeout=30).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def demo_year(name: str) -> str:
    m = re.search(r"(20\d\d)[_-]", name)
    return m.group(1) if m else "unknown"


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while True:
                b = fh.read(1 << 20)
                if not b:
                    break
                h.update(b)
    except OSError:
        return ""
    return h.hexdigest()


# ------------------------------------------------------------------ schema
def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db), timeout=120)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS build_info (
        key TEXT PRIMARY KEY, value TEXT);

    CREATE TABLE IF NOT EXISTS demos (
        demo_id       INTEGER PRIMARY KEY,
        content_hash  TEXT UNIQUE,
        path          TEXT,
        name          TEXT,
        size_bytes    INTEGER,
        year          TEXT,
        build         TEXT,
        protocol      TEXT,
        map_name      TEXT,
        gametype      TEXT,
        duration_ms   INTEGER,
        rounds        INTEGER,
        players       INTEGER,
        recorder_client INTEGER,
        recorder_name TEXT,
        raw_obituaries INTEGER,
        accepted_frags INTEGER,
        packet_errors INTEGER,
        first_packet_error TEXT,
        parse_error   TEXT,
        parser_commit TEXT,
        schema_version TEXT,
        parsed_at     TEXT,
        duplicate_of  TEXT);

    CREATE TABLE IF NOT EXISTS frags (
        frag_id       INTEGER PRIMARY KEY,
        demo_id       INTEGER NOT NULL,
        demo_name     TEXT,
        server_time_ms INTEGER,
        clock         TEXT,
        round         INTEGER,
        attacker_client INTEGER,
        attacker_name TEXT,
        victim_client INTEGER,
        victim_name   TEXT,
        mod           INTEGER,
        weapon_name   TEXT,
        by_recorder   INTEGER,
        tags          TEXT,
        score         REAL,
        ms_to_prev    INTEGER,
        ms_to_next    INTEGER,
        FOREIGN KEY(demo_id) REFERENCES demos(demo_id));

    CREATE INDEX IF NOT EXISTS ix_frags_demo ON frags(demo_id);
    CREATE INDEX IF NOT EXISTS ix_frags_time ON frags(server_time_ms);
    CREATE INDEX IF NOT EXISTS ix_frags_recorder ON frags(by_recorder);
    """)
    con.commit()
    return con


def set_build_info(con, **kw):
    for k, v in kw.items():
        con.execute("INSERT INTO build_info(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (k, str(v)))
    con.commit()


# ------------------------------------------------------------------ worker
def parse_one(path_str: str) -> dict:
    """Parse a demo into a compact record. Runs in a worker process."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import demo_parse as D
    import frag_classify as fc

    path = Path(path_str)
    out = {"path": str(path), "name": path.name,
           "size_bytes": path.stat().st_size if path.exists() else 0,
           "year": demo_year(path.name), "frags": [], "parse_error": None}
    try:
        D._get_huff()
        res = D.DM73Parser(path).parse()
        obits = [e for e in res.get("events", []) if e.get("type") == "obituary"]
        me = fc.demo_taker(res)
        frags = fc.classify(res)

        times = [f.time_ms for f in frags]
        rows = []
        for i, f in enumerate(frags):
            rows.append({
                "server_time_ms": f.time_ms,
                "clock": "{}:{:02d}".format(f.time_ms // 60000,
                                            (f.time_ms // 1000) % 60),
                "round": f.round,
                "attacker_client": f.killer,
                "attacker_name": strip_colors(f.killer_name),
                "victim_client": f.victim,
                "victim_name": strip_colors(f.victim_name),
                "mod": f.weapon,
                "weapon_name": f.weapon_name,
                "by_recorder": int(me is not None and f.killer == me),
                "tags": ",".join(f.tag_names),
                "score": float(f.score),
                "ms_to_prev": (f.time_ms - times[i - 1]) if i > 0 else None,
                "ms_to_next": (times[i + 1] - f.time_ms) if i + 1 < len(times) else None,
            })

        players = res.get("players") or {}
        out.update({
            "build": res.get("build") or res.get("version") or "",
            "protocol": str(res.get("protocol") or ""),
            "map_name": res.get("map") or res.get("mapname") or "",
            "gametype": str(res.get("gametype") or ""),
            "duration_ms": res.get("duration_ms"),
            "rounds": len(res.get("rounds") or []),
            "players": len(players) if isinstance(players, dict) else 0,
            "recorder_client": me,
            "recorder_name": strip_colors(
                (players.get(me) or {}).get("name") if isinstance(players, dict)
                and me is not None else ""),
            "raw_obituaries": len(obits),
            "accepted_frags": len(frags),
            "packet_errors": res.get("packet_errors"),
            "first_packet_error": res.get("first_packet_error"),
            "frags": rows,
        })
    except Exception as exc:                         # noqa: BLE001 - recorded
        out["parse_error"] = "{}: {}".format(type(exc).__name__, exc)[:400]
    return out


# ------------------------------------------------------------------ driver
def existing_hashes(con) -> set:
    return {r[0] for r in con.execute(
        "SELECT content_hash FROM demos WHERE content_hash IS NOT NULL")}


def store(con, rec: dict, commit_sha: str, dup_of=None) -> None:
    con.execute("""
        INSERT INTO demos (content_hash, path, name, size_bytes, year, build,
            protocol, map_name, gametype, duration_ms, rounds, players,
            recorder_client, recorder_name, raw_obituaries, accepted_frags,
            packet_errors, first_packet_error, parse_error, parser_commit,
            schema_version, parsed_at, duplicate_of)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(content_hash) DO NOTHING
        """, (rec.get("content_hash"), rec["path"], rec["name"],
              rec.get("size_bytes"), rec.get("year"), rec.get("build"),
              rec.get("protocol"), rec.get("map_name"), rec.get("gametype"),
              rec.get("duration_ms"), rec.get("rounds"), rec.get("players"),
              rec.get("recorder_client"), rec.get("recorder_name"),
              rec.get("raw_obituaries"), rec.get("accepted_frags"),
              rec.get("packet_errors"), rec.get("first_packet_error"),
              rec.get("parse_error"), commit_sha, SCHEMA_VERSION,
              time.strftime("%Y-%m-%d %H:%M:%S"), dup_of))
    row = con.execute("SELECT demo_id FROM demos WHERE content_hash=?",
                      (rec.get("content_hash"),)).fetchone()
    if not row:
        return
    demo_id = row[0]
    if rec.get("frags"):
        con.executemany("""
            INSERT INTO frags (demo_id, demo_name, server_time_ms, clock, round,
                attacker_client, attacker_name, victim_client, victim_name,
                mod, weapon_name, by_recorder, tags, score, ms_to_prev, ms_to_next)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [(demo_id, rec["name"], f["server_time_ms"], f["clock"],
                   f["round"], f["attacker_client"], f["attacker_name"],
                   f["victim_client"], f["victim_name"], f["mod"],
                   f["weapon_name"], f["by_recorder"], f["tags"], f["score"],
                   f["ms_to_prev"], f["ms_to_next"]) for f in rec["frags"]])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--root", default=str(DEMO_ROOT))
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 3))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    db = Path(a.db)
    con = connect(db)
    commit_sha = parser_commit()
    set_build_info(con, parser_commit=commit_sha,
                   schema_version=SCHEMA_VERSION,
                   corpus_root=str(a.root),
                   profile="ql-2012 (single table, QL_2011 deleted)",
                   build_started=time.strftime("%Y-%m-%d %H:%M:%S"))

    demos = sorted(Path(a.root).glob("*.dm_73"))
    print("[rebuild] {} demo file(s) discovered under {}".format(len(demos),
                                                                 a.root),
          flush=True)

    # Dedupe by content BEFORE parsing -- identical bytes cannot yield
    # different frags, and counting them twice would inflate every statistic.
    print("[rebuild] hashing for duplicates...", flush=True)
    by_hash = {}
    dup_count = 0
    for q in demos:
        h = content_hash(q)
        if not h:
            continue
        if h in by_hash:
            dup_count += 1
        else:
            by_hash[h] = q
    print("[rebuild] {} unique by content, {} duplicate file(s)".format(
        len(by_hash), dup_count), flush=True)

    done = existing_hashes(con)
    todo = [(h, q) for h, q in by_hash.items() if h not in done]
    if a.limit:
        todo = todo[:a.limit]
    print("[rebuild] {} to parse ({} already in db), {} workers".format(
        len(todo), len(done), a.workers), flush=True)

    t0 = time.time()
    ok = failed = 0
    total_obits = total_frags = total_pkt_err = 0
    by_year = collections.Counter()
    frags_by_year = collections.Counter()
    outliers = []

    if todo:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(parse_one, str(q)): h for h, q in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                h = futs[fut]
                try:
                    rec = fut.result()
                except Exception as exc:             # noqa: BLE001
                    print("  [rebuild] worker died: {}".format(exc), flush=True)
                    failed += 1
                    continue
                rec["content_hash"] = h
                store(con, rec, commit_sha)
                if rec.get("parse_error"):
                    failed += 1
                    outliers.append({"demo": rec["name"], "why": "parse_error",
                                     "detail": rec["parse_error"],
                                     "rounds": None, "frags": 0})
                else:
                    ok += 1
                    total_obits += rec.get("raw_obituaries") or 0
                    total_frags += rec.get("accepted_frags") or 0
                    total_pkt_err += rec.get("packet_errors") or 0
                    by_year[rec["year"]] += 1
                    frags_by_year[rec["year"]] += rec.get("accepted_frags") or 0
                    rounds = rec.get("rounds") or 0
                    nf = rec.get("accepted_frags") or 0
                    if rounds and nf == 0:
                        outliers.append({"demo": rec["name"],
                                         "why": "rounds_but_zero_frags",
                                         "detail": "{} rounds".format(rounds),
                                         "rounds": rounds, "frags": nf})
                    elif rounds and nf / rounds > 60:
                        outliers.append({"demo": rec["name"],
                                         "why": "very_high_frags_per_round",
                                         "detail": "{:.1f}/round".format(nf / rounds),
                                         "rounds": rounds, "frags": nf})
                    if (rec.get("packet_errors") or 0) > 0:
                        outliers.append({"demo": rec["name"],
                                         "why": "packet_errors",
                                         "detail": str(rec.get("first_packet_error")),
                                         "rounds": rounds, "frags": nf})
                if i % 100 == 0:
                    el = time.time() - t0
                    rate = i / el if el else 0
                    print("  [rebuild] {}/{}  ok={} failed={}  {:.1f}/s  "
                          "eta {:.0f} min".format(i, len(todo), ok, failed,
                                                  rate,
                                                  (len(todo) - i) / rate / 60
                                                  if rate else 0), flush=True)
                    con.commit()
    con.commit()

    set_build_info(con, build_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                   demos_discovered=len(demos),
                   demos_unique=len(by_hash),
                   demos_duplicate=dup_count,
                   demos_ok=ok, demos_failed=failed)
    # Say which parser built this. A database without the stamp reads as
    # STALE_PRE_PARSER_V2 for entity-derived data (engine/parser/corpus_status).
    import demo_parse as D
    import corpus_status as CS
    CS.stamp(db, D.PARSER_VERSION, git_commit=commit_sha,
             builder="engine/parser/rebuild_corpus.py")

    n_demos = con.execute("SELECT COUNT(*) FROM demos").fetchone()[0]
    n_frags = con.execute("SELECT COUNT(*) FROM frags").fetchone()[0]
    n_mine = con.execute("SELECT COUNT(*) FROM frags WHERE by_recorder=1"
                         ).fetchone()[0]

    print("")
    print("=" * 70)
    print("CORPUS REBUILD")
    print("=" * 70)
    print("  files discovered   : {}".format(len(demos)))
    print("  unique by content  : {}  ({} duplicates skipped)".format(
        len(by_hash), dup_count))
    print("  parsed OK          : {}".format(ok))
    print("  failed             : {}".format(failed))
    print("  raw obituaries     : {}".format(total_obits))
    print("  accepted frags     : {}".format(total_frags))
    print("  packet errors      : {}".format(total_pkt_err))
    print("  db demos / frags   : {} / {}  ({} by the recorder)".format(
        n_demos, n_frags, n_mine))
    print("")
    print("  frags by year:")
    for y in sorted(frags_by_year):
        print("     {:>8}  {:>5} demos  {:>7} frags".format(
            y, by_year[y], frags_by_year[y]))

    outp = Path(a.report or (REPO / "output" / "parser_outliers.csv"))
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["demo", "why", "detail", "rounds",
                                           "frags"])
        w.writeheader()
        for r in outliers:
            w.writerow(r)
    print("")
    print("  outliers: {} -> {}".format(len(outliers), outp))
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
