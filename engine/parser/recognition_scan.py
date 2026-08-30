"""Corpus-wide recognition scan -> frag_recognition.db + per-class top lists.

Walks every UNIQUE demo (frags_rebuilt.db demos where duplicate_of IS NULL),
parses it with the certified dm73 parser, runs the frag_recognition taxonomy
on the RECORDER's frags (parser client identity, never name matching), and
writes one row per recorder frag into creative_suite/database/
frag_recognition.db.

Resumable: scanned demos are keyed by content hash and skipped on rerun.
frags_rebuilt.db is opened READ-ONLY and never modified.

    python -u engine/parser/recognition_scan.py --limit 50 --workers 8
    python -u engine/parser/recognition_scan.py --workers 10          # full
    python -u engine/parser/recognition_scan.py --export-only        # just CSVs
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

FRAGS_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DB = REPO / "creative_suite" / "database" / "frag_recognition.db"
OUT_DIR = REPO / "output" / "demo_v2" / "recognition"

TOP_N = 50

# class name (or prefix match) -> export csv
EXPORTS = [
    ("top_air_rockets.csv", ["AIR_ROCKET"]),
    ("top_air_grenades.csv", ["AIR_GRENADE"]),
    ("top_pixel_shots.csv", ["PIXEL_SHOT_CANDIDATE"]),
    ("top_flick_shots.csv", ["FLICK_SHOT"]),
    ("top_lg_tracking.csv", ["LG_TRACKING", "LG_HIGH_ACCURACY"]),
    ("top_multikills.csv", ["MULTIKILL_DOUBLE", "MULTIKILL_TRIPLE",
                            "MULTIKILL_QUAD", "MULTIKILL_MEGA"]),
    ("top_direct_rockets.csv", ["DIRECT_ROCKET"]),
    ("top_rail_frags.csv", ["RAIL_AIR", "RAIL_FLICK", "RAIL_CONSECUTIVE",
                            "PIXEL_SHOT_CANDIDATE"]),
    ("top_weapon_combos.csv", ["WEAPON_COMBO"]),
]


def connect_out(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db), timeout=120)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS scanned_demos (
        content_hash TEXT PRIMARY KEY,
        demo_name    TEXT,
        recorder_client INTEGER,
        n_frags      INTEGER,
        error        TEXT,
        scanned_at   TEXT);

    CREATE TABLE IF NOT EXISTS recognized_frags (
        id INTEGER PRIMARY KEY,
        demo_name    TEXT,
        content_hash TEXT,
        server_time_ms INTEGER,
        round        INTEGER,
        mod          INTEGER,
        weapon_name  TEXT,
        victim_client INTEGER,
        classes      TEXT,      -- JSON [{name, confidence, detail}]
        attributes   TEXT,      -- JSON numeric attrs
        multikill_score REAL DEFAULT 0,
        air_score REAL DEFAULT 0,
        accuracy_score REAL DEFAULT 0,
        flick_score REAL DEFAULT 0,
        distance_score REAL DEFAULT 0,
        visibility_difficulty REAL DEFAULT 0,
        weapon_combo_score REAL DEFAULT 0,
        prediction_score REAL DEFAULT 0,
        movement_score REAL DEFAULT 0,
        highlight_score REAL DEFAULT 0,
        reasons      TEXT);     -- JSON [str]

    CREATE INDEX IF NOT EXISTS ix_rec_hash ON recognized_frags(content_hash);
    CREATE INDEX IF NOT EXISTS ix_rec_score ON recognized_frags(highlight_score);
    """)
    con.commit()
    return con


# ------------------------------------------------------------------ worker
def scan_one(job: tuple[str, str, str]) -> dict:
    """(content_hash, path, name) -> recognition rows. Worker process."""
    content_hash, path_str, name = job
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import demo_parse as D
    import frag_recognition as fr

    out = {"content_hash": content_hash, "demo_name": name,
           "recorder_client": None, "rows": [], "error": None}
    try:
        D._get_huff()
        parsed = D.DM73Parser(path_str).parse()
        import frag_classify as fc
        me = fc.demo_taker(parsed)
        out["recorder_client"] = me
        if me is None:
            return out
        for r in fr.recognize(parsed, player=me, demo_name=name):
            out["rows"].append({
                "server_time_ms": r.time_ms,
                "round": r.round,
                "mod": r.weapon,
                "weapon_name": r.weapon_name,
                "victim_client": r.victim,
                "classes": r.classes,
                "attributes": r.attributes,
                "components": r.components,
                "highlight_score": r.highlight_score,
                "reasons": r.reasons,
            })
    except Exception as exc:                       # noqa: BLE001 - recorded
        out["error"] = "{}: {}".format(type(exc).__name__, exc)[:400]
    return out


def store(con: sqlite3.Connection, rec: dict) -> None:
    con.execute(
        "INSERT OR REPLACE INTO scanned_demos "
        "(content_hash, demo_name, recorder_client, n_frags, error, scanned_at)"
        " VALUES (?,?,?,?,?,?)",
        (rec["content_hash"], rec["demo_name"], rec["recorder_client"],
         len(rec["rows"]), rec["error"], time.strftime("%Y-%m-%d %H:%M:%S")))
    comp_cols = ["multikill_score", "air_score", "accuracy_score",
                 "flick_score", "distance_score", "visibility_difficulty",
                 "weapon_combo_score", "prediction_score", "movement_score"]
    con.executemany(
        "INSERT INTO recognized_frags (demo_name, content_hash,"
        " server_time_ms, round, mod, weapon_name, victim_client, classes,"
        " attributes, " + ",".join(comp_cols) + ", highlight_score, reasons)"
        " VALUES (?,?,?,?,?,?,?,?,?" + ",?" * (len(comp_cols) + 2) + ")",
        [(rec["demo_name"], rec["content_hash"], r["server_time_ms"],
          r["round"], r["mod"], r["weapon_name"], r["victim_client"],
          json.dumps(r["classes"]), json.dumps(r["attributes"]),
          *[r["components"].get(c, 0.0) for c in comp_cols],
          r["highlight_score"], json.dumps(r["reasons"]))
         for r in rec["rows"]])


# ------------------------------------------------------------------ export
def _load_match_groups() -> dict[str, int]:
    """Match-aware grouping over the READ-ONLY corpus db."""
    from capture_windows import build_match_groups, load_demo_frag_tuples
    con = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    demo_frags = load_demo_frag_tuples(con)
    con.close()
    return build_match_groups(demo_frags)


def dedupe_rows(rows: list[dict], match_group: dict[str, int]) -> list[dict]:
    """Same real moment recorded in several demo files -> one canonical row.

    Two rows are the same moment iff their demos are in one match group AND
    they share (server_time_ms, victim_client, mod) -- kill times are
    server-authoritative and identical across recordings of one match.
    Keeps the highest-scoring copy; provenance survives in `aliases`.
    """
    best: dict[tuple, dict] = {}
    for r in rows:
        g = match_group.get(r["demo_name"])
        key = ((g, r["server_time_ms"], r["victim_client"], r["mod"])
               if g is not None else ("solo", r["demo_name"],
                                      r["server_time_ms"], r["victim_client"]))
        cur = best.get(key)
        if cur is None:
            r = dict(r)
            r["aliases"] = []
            best[key] = r
        elif r["highlight_score"] > cur["highlight_score"]:
            r = dict(r)
            r["aliases"] = cur["aliases"] + [cur["demo_name"]]
            best[key] = r
        elif r["demo_name"] != cur["demo_name"]:
            cur["aliases"].append(r["demo_name"])
    return list(best.values())


def export(con: sqlite3.Connection) -> dict[str, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for (demo_name, content_hash, t, rnd, mod, wname, victim, classes,
         attrs, score, reasons) in con.execute(
            "SELECT demo_name, content_hash, server_time_ms, round, mod,"
            " weapon_name, victim_client, classes, attributes,"
            " highlight_score, reasons FROM recognized_frags"):
        rows.append({
            "demo_name": demo_name, "content_hash": content_hash,
            "server_time_ms": t, "round": rnd, "mod": mod,
            "weapon_name": wname, "victim_client": victim,
            "classes": json.loads(classes), "attributes": json.loads(attrs),
            "highlight_score": score, "reasons": json.loads(reasons),
        })

    match_group = _load_match_groups()
    rows = dedupe_rows(rows, match_group)

    fields = ["rank", "demo_name", "server_time_ms", "round", "weapon_name",
              "highlight_score", "class_names", "class_confidences",
              "reasons", "attributes", "aliases"]

    def write_top(path: Path, subset: list[dict]) -> int:
        subset = sorted(subset, key=lambda r: -r["highlight_score"])[:TOP_N]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for i, r in enumerate(subset, 1):
                w.writerow({
                    "rank": i, "demo_name": r["demo_name"],
                    "server_time_ms": r["server_time_ms"], "round": r["round"],
                    "weapon_name": r["weapon_name"],
                    "highlight_score": r["highlight_score"],
                    "class_names": ";".join(c["name"] for c in r["classes"]),
                    "class_confidences": ";".join(
                        f"{c['name']}={c['confidence']}" for c in r["classes"]),
                    "reasons": " | ".join(r["reasons"]),
                    "attributes": json.dumps(r["attributes"]),
                    "aliases": ";".join(r["aliases"]),
                })
        return len(subset)

    counts: dict[str, int] = {}
    for fname, class_names in EXPORTS:
        subset = [r for r in rows
                  if any(c["name"] in class_names for c in r["classes"])]
        counts[fname] = write_top(OUT_DIR / fname, subset)
    counts["top_overall_highlights.csv"] = write_top(
        OUT_DIR / "top_overall_highlights.csv",
        [r for r in rows if r["highlight_score"] > 0])
    return counts


# ------------------------------------------------------------------ driver
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--db", default=str(OUT_DB))
    ap.add_argument("--export-only", action="store_true")
    a = ap.parse_args()

    con = connect_out(Path(a.db))

    if not a.export_only:
        src = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
        demos = [(h, p, n) for h, p, n in src.execute(
            "SELECT content_hash, path, name FROM demos"
            " WHERE duplicate_of IS NULL AND parse_error IS NULL"
            " AND path IS NOT NULL")]
        src.close()

        done = {r[0] for r in con.execute(
            "SELECT content_hash FROM scanned_demos")}
        todo = [d for d in demos if d[0] not in done
                and os.path.exists(d[1])]
        if a.limit:
            todo = todo[:a.limit]
        print(f"[recog] {len(demos)} unique demos, {len(done)} already"
              f" scanned, {len(todo)} to do, {a.workers} workers", flush=True)

        t0 = time.time()
        ok = failed = frag_total = 0
        if todo:
            with ProcessPoolExecutor(max_workers=a.workers) as ex:
                futs = {ex.submit(scan_one, d): d[0] for d in todo}
                for i, fut in enumerate(as_completed(futs), 1):
                    try:
                        rec = fut.result()
                    except Exception as exc:       # noqa: BLE001
                        print(f"  [recog] worker died: {exc}", flush=True)
                        failed += 1
                        continue
                    store(con, rec)
                    if rec["error"]:
                        failed += 1
                    else:
                        ok += 1
                        frag_total += len(rec["rows"])
                    if i % 50 == 0:
                        el = time.time() - t0
                        rate = i / el if el else 0
                        eta = (len(todo) - i) / rate / 60 if rate else 0
                        print(f"  [recog] {i}/{len(todo)} ok={ok}"
                              f" failed={failed} frags={frag_total}"
                              f" {rate:.1f}/s eta {eta:.0f} min", flush=True)
                        con.commit()
        con.commit()
        print(f"[recog] scan done: ok={ok} failed={failed}"
              f" recorder_frags={frag_total}", flush=True)

    counts = export(con)
    print("[recog] exports ->", OUT_DIR)
    for k, v in counts.items():
        print(f"  {k:32s} {v} rows")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
