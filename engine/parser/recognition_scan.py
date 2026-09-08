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

import frag_recognition as _fr        # noqa: E402  (after sys.path insert)

FRAGS_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DB = REPO / "creative_suite" / "database" / "frag_recognition.db"
OUT_DIR = REPO / "output" / "demo_v2" / "recognition"
NORMS_JSON = OUT_DIR / "norms.json"

RECOGNITION_VERSION = _fr.RECOGNITION_VERSION
COMP_COLS = list(_fr.COMPONENT_NAMES)

TOP_N = 50
TOP_N_BIG = 100      # the Q1 speed/reaction lists ship deeper

# class name -> export csv (third field: per-list cap; rows are capped by
# what actually exists -- "top 100" of 30 rows is 30 rows)
EXPORTS = [
    ("top_air_rockets.csv", ["AIR_ROCKET"], TOP_N),
    ("top_air_grenades.csv", ["AIR_GRENADE"], TOP_N),
    ("top_pixel_shots.csv", ["PIXEL_SHOT_CANDIDATE"], TOP_N),
    ("top_flick_shots.csv", ["FLICK_SHOT"], TOP_N),
    ("top_lg_tracking.csv", ["LG_TRACKING", "LG_HIGH_ACCURACY"], TOP_N),
    ("top_multikills.csv", ["MULTIKILL_DOUBLE", "MULTIKILL_TRIPLE",
                            "MULTIKILL_QUAD", "MULTIKILL_PENTA",
                            "MULTIKILL_HEXA", "MULTIKILL_HEPTA",
                            "MULTIKILL_OCTA", "MULTIKILL_MEGA"], TOP_N),
    ("top_direct_rockets.csv", ["DIRECT_ROCKET"], TOP_N),
    ("top_rail_frags.csv", ["RAIL_AIR", "RAIL_FLICK", "RAIL_CONSECUTIVE",
                            "PIXEL_SHOT_CANDIDATE"], TOP_N),
    ("top_weapon_combos.csv", ["WEAPON_COMBO", "COMBO_KILL"], TOP_N),
    # Q1 additions (taxonomy v2)
    ("top_fast_multikills.csv", ["HIGH_SPEED_MULTIKILL",
                                 "RAPID_MULTIKILL"], TOP_N_BIG),
    ("top_high_speed_frags.csv", ["HIGH_SPEED_FRAG", "HIGH_SPEED_AIR_FRAG",
                                  "SPEED_TARGET_FRAG"], TOP_N_BIG),
    ("top_rocket_jump_frags.csv", ["ROCKET_JUMP_FRAG",
                                   "ROCKET_JUMP_ENTRY"], TOP_N_BIG),
    ("top_reaction_candidates.csv", ["REACTION_SHOT_CANDIDATE"], TOP_N_BIG),
    ("top_target_transfers.csv", ["TARGET_TRANSFER", "LG_TRANSFER"], TOP_N_BIG),
    ("top_combo_kills.csv", ["COMBO_KILL", "POPUP_COMBO",
                             "MULTI_WEAPON_CHAIN",
                             "WEAPON_SWITCH_FINISH"], TOP_N_BIG),
    ("top_movement_frags.csv", ["STRAFE_CHAIN_FRAG", "VERTICAL_ACTION",
                                "DODGE_AND_KILL",
                                "ESCAPE_TURNAROUND"], TOP_N_BIG),
    ("top_clutch_drama.csv", ["LOW_HEALTH_WIN", "LAST_HP_FRAG"], TOP_N_BIG),
]


def connect_out(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db), timeout=120)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    comp_ddl = ",\n        ".join(f"{c} REAL DEFAULT 0" for c in COMP_COLS)
    con.executescript(f"""
    CREATE TABLE IF NOT EXISTS scanned_demos (
        content_hash TEXT PRIMARY KEY,
        demo_name    TEXT,
        recorder_client INTEGER,
        n_frags      INTEGER,
        error        TEXT,
        scanned_at   TEXT,
        recognition_version INTEGER DEFAULT {RECOGNITION_VERSION});

    CREATE TABLE IF NOT EXISTS recognized_frags (
        id INTEGER PRIMARY KEY,
        demo_name    TEXT,
        content_hash TEXT,
        server_time_ms INTEGER,
        round        INTEGER,
        mod          INTEGER,
        weapon_name  TEXT,
        victim_client INTEGER,
        classes      TEXT,      -- JSON [{{name, confidence, detail}}]
        attributes   TEXT,      -- JSON numeric attrs
        {comp_ddl},
        highlight_score REAL DEFAULT 0,
        reasons      TEXT,      -- JSON [str]
        recognition_version INTEGER DEFAULT {RECOGNITION_VERSION});

    CREATE INDEX IF NOT EXISTS ix_rec_hash ON recognized_frags(content_hash);
    CREATE INDEX IF NOT EXISTS ix_rec_score ON recognized_frags(highlight_score);
    """)
    _ensure_columns(con)
    con.commit()
    return con


def _ensure_columns(con: sqlite3.Connection) -> None:
    """Migrate a v1 db in place: add version + any new component columns.

    Legacy v1 component columns (accuracy_score, distance_score, ...) are
    left untouched -- rows are rewritten wholesale when their demo is
    re-scanned at the current RECOGNITION_VERSION.
    """
    for table in ("scanned_demos", "recognized_frags"):
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if "recognition_version" not in have:
            con.execute(f"ALTER TABLE {table} ADD COLUMN"
                        " recognition_version INTEGER DEFAULT 1")
    have = {r[1] for r in con.execute("PRAGMA table_info(recognized_frags)")}
    for c in COMP_COLS:
        if c not in have:
            con.execute(f"ALTER TABLE recognized_frags ADD COLUMN"
                        f" {c} REAL DEFAULT 0")


# ------------------------------------------------------------------ worker
def scan_one(job: tuple) -> dict:
    """(content_hash, path, name[, norms_path]) -> recognition rows.
    Worker process."""
    content_hash, path_str, name = job[0], job[1], job[2]
    norms_path = job[3] if len(job) > 3 else None
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import demo_parse as D
    import frag_recognition as fr
    import recognition_norms as rn

    norms = rn.load_norms(norms_path) if norms_path else None

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
        for r in fr.recognize(parsed, player=me, demo_name=name, norms=norms):
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
        "(content_hash, demo_name, recorder_client, n_frags, error,"
        " scanned_at, recognition_version) VALUES (?,?,?,?,?,?,?)",
        (rec["content_hash"], rec["demo_name"], rec["recorder_client"],
         len(rec["rows"]), rec["error"], time.strftime("%Y-%m-%d %H:%M:%S"),
         RECOGNITION_VERSION))
    # A demo re-scanned at a new taxonomy version replaces its old rows --
    # otherwise a version bump would double every frag.
    con.execute("DELETE FROM recognized_frags WHERE content_hash = ?",
                (rec["content_hash"],))
    con.executemany(
        "INSERT INTO recognized_frags (demo_name, content_hash,"
        " server_time_ms, round, mod, weapon_name, victim_client, classes,"
        " attributes, " + ",".join(COMP_COLS)
        + ", highlight_score, reasons, recognition_version)"
        " VALUES (?,?,?,?,?,?,?,?,?" + ",?" * (len(COMP_COLS) + 3) + ")",
        [(rec["demo_name"], rec["content_hash"], r["server_time_ms"],
          r["round"], r["mod"], r["weapon_name"], r["victim_client"],
          json.dumps(r["classes"]), json.dumps(r["attributes"]),
          *[r["components"].get(c, 0.0) for c in COMP_COLS],
          r["highlight_score"], json.dumps(r["reasons"]),
          RECOGNITION_VERSION)
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


def export(con: sqlite3.Connection,
           out_dir: Path = OUT_DIR) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
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

    def write_top(path: Path, subset: list[dict], cap: int = TOP_N) -> int:
        subset = sorted(subset, key=lambda r: -r["highlight_score"])[:cap]
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
    for fname, class_names, cap in EXPORTS:
        subset = [r for r in rows
                  if any(c["name"] in class_names for c in r["classes"])]
        counts[fname] = write_top(out_dir / fname, subset, cap)
    counts["top_overall_highlights.csv"] = write_top(
        out_dir / "top_overall_highlights.csv",
        [r for r in rows if r["highlight_score"] > 0], TOP_N_BIG)
    return counts


# ------------------------------------------------------------------ driver
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--db", default=str(OUT_DB))
    ap.add_argument("--norms", default=str(NORMS_JSON),
                    help="archive percentile tables (rule L); ignored when"
                         " the file does not exist")
    ap.add_argument("--out-dir", default=str(OUT_DIR),
                    help="where the top-list CSVs land (pilot runs should"
                         " point this away from the live export dir)")
    ap.add_argument("--min-bytes", type=int, default=0,
                    help="skip demos smaller than this many bytes; 512000 "
                         "drops connect-and-leave recordings")
    ap.add_argument("--export-only", action="store_true")
    a = ap.parse_args()

    con = connect_out(Path(a.db))
    norms_path = a.norms if a.norms and os.path.exists(a.norms) else None
    print(f"[recog] taxonomy v{RECOGNITION_VERSION}, norms="
          f"{norms_path or 'NONE (provisional thresholds)'}", flush=True)

    if not a.export_only:
        src = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
        demos = [(h, p, n, norms_path) for h, p, n in src.execute(
            "SELECT content_hash, path, name FROM demos"
            " WHERE duplicate_of IS NULL AND parse_error IS NULL"
            " AND path IS NOT NULL")]
        src.close()

        # Size floor. A tiny .dm_73 is a connect-and-leave or a truncated
        # recording: it carries no round worth mining, and scanning it costs
        # the same startup as a real match. Measured on this corpus, 1,491 of
        # 6,445 files sit under the default 500 KB.
        if a.min_bytes:
            import os as _os
            kept = []
            for row in demos:
                try:
                    if _os.path.getsize(row[1]) >= a.min_bytes:
                        kept.append(row)
                except OSError:
                    continue            # unreadable: not scannable either
            print(f"size filter >= {a.min_bytes} bytes: "
                  f"{len(kept)} of {len(demos)} demos", flush=True)
            demos = kept

        # only demos already scanned at the CURRENT taxonomy version skip;
        # a version bump makes the whole corpus due for recompute (resumable)
        done = {r[0] for r in con.execute(
            "SELECT content_hash FROM scanned_demos"
            " WHERE recognition_version >= ?", (RECOGNITION_VERSION,))}
        todo = [d for d in demos if d[0] not in done
                and os.path.exists(d[1])]
        if a.limit:
            todo = todo[:a.limit]
        print(f"[recog] {len(demos)} unique demos, {len(done)} already"
              f" scanned at v{RECOGNITION_VERSION}, {len(todo)} to do,"
              f" {a.workers} workers", flush=True)

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

    counts = export(con, Path(a.out_dir))
    print("[recog] exports ->", a.out_dir)
    for k, v in counts.items():
        print(f"  {k:32s} {v} rows")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
