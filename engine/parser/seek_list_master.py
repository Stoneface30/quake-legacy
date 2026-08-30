"""Master seek list, built from the rebuilt frag database.

Supersedes `seek_list.py`, which parsed demos directly and gated them behind a
"looks trustworthy" obituary threshold. That gate existed only because the
pre-fix parser returned 0-3 kills on older builds; with the dispatch fix the
whole corpus decodes and the gate would now discard nothing but genuinely quiet
demos. Reading the database instead means the ranking runs in seconds and every
row carries the provenance of the build that produced it.

Ranking rewards what actually cuts well, in rough order of weight: several
kills inside one capture window, consecutive frags, the tags that mark a
highlight (airshot, multikill, combos), rail and rocket work, and frags by the
recorder -- the user is the player, so their own kills are the material.

    python engine/parser/seek_list_master.py
    python engine/parser/seek_list_master.py --recorder-only --top 40
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

DEFAULT_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"

CHAIN_MS = 4000        # two frags this close read as one sequence
CAPTURE_MS = 12000     # what one wolfcam capture window can hold

RAIL_MODS = {10}
ROCKET_MODS = {6, 7}

TAG_WEIGHT = {
    "air_combo": 6.0, "quadkill": 6.0, "air_rocket": 5.0,
    "airshot": 4.0, "multikill": 4.0, "air_shaft": 3.5,
    "air_nade": 3.5, "rocket_rail": 3.0, "shaft_rail": 3.0,
    "shaft_rocket": 3.0, "big_flick": 2.5, "air_speed_combo": 2.5,
    "pixel_shot": 2.5, "very_fast_kill": 2.0, "high_acc_shaft": 2.0,
    "rocketjump_frag": 2.0, "airborne_kill": 1.5, "fast_kill": 1.0,
    "preshot": 1.5,
}


def load(db: Path, recorder_only: bool):
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    q = """SELECT f.*, d.name AS demo, d.year, d.map_name, d.recorder_name
           FROM frags_dedup f JOIN demos d ON d.demo_id = f.demo_id"""
    if recorder_only:
        q += " WHERE f.by_recorder = 1"
    rows = [dict(r) for r in con.execute(q)]
    info = {k: v for k, v in con.execute("SELECT key, value FROM build_info")}
    con.close()
    return rows, info


def rank(rows):
    by_demo = defaultdict(list)
    for r in rows:
        by_demo[r["demo"]].append(r)

    out = []
    for demo, frs in by_demo.items():
        frs.sort(key=lambda r: r["server_time_ms"] or 0)
        times = [r["server_time_ms"] or 0 for r in frs]
        for i, r in enumerate(frs):
            t = times[i]
            prev_gap = (t - times[i - 1]) if i > 0 else None
            next_gap = (times[i + 1] - t) if i + 1 < len(times) else None
            in_window = sum(1 for x in times if 0 <= x - t <= CAPTURE_MS)

            score = 0.0
            reasons = []
            tags = [x for x in (r.get("tags") or "").split(",") if x]
            for tg in tags:
                w = TAG_WEIGHT.get(tg)
                if w:
                    score += w
                    reasons.append(tg)

            if prev_gap is not None and prev_gap <= CHAIN_MS:
                score += 2.5
                reasons.append("chain(-{}ms)".format(prev_gap))
            if next_gap is not None and next_gap <= CHAIN_MS:
                score += 2.5
                reasons.append("chain(+{}ms)".format(next_gap))
            if in_window >= 3:
                score += in_window
                reasons.append("{}kills/{}s".format(in_window,
                                                    CAPTURE_MS // 1000))
            mod = r.get("mod")
            if mod in RAIL_MODS:
                score += 1.5
                reasons.append("rail")
            elif mod in ROCKET_MODS:
                score += 1.5
                reasons.append("rocket")
            if r.get("by_recorder"):
                score += 2.0
                reasons.append("recorder-frag")

            out.append({
                "demo": demo,
                "year": r.get("year"),
                "map": r.get("map_name"),
                "server_time_ms": t,
                "timestamp": r.get("clock"),
                "seekclock": r.get("clock"),
                "round": r.get("round"),
                "attacker": r.get("attacker_client"),
                "attacker_name": r.get("attacker_name"),
                "victim": r.get("victim_client"),
                "victim_name": r.get("victim_name"),
                "MOD": mod,
                "weapon": r.get("weapon_name"),
                "by_recorder": r.get("by_recorder"),
                "ms_to_prev_frag": prev_gap,
                "ms_to_next_frag": next_gap,
                "kills_in_capture_window": in_window,
                "multikill_context": in_window >= 3,
                "tags": ",".join(tags),
                "rank_score": round(score, 2),
                "rank_reasons": ",".join(reasons[:8]),
            })
    out.sort(key=lambda r: -r["rank_score"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--recorder-only", action="store_true")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out-dir", default=str(REPO / "output"))
    a = ap.parse_args()

    db = Path(a.db)
    if not db.exists():
        print("ERROR: {} does not exist -- run rebuild_corpus.py first"
              .format(db))
        return 1

    rows, info = load(db, a.recorder_only)
    if not rows:
        print("ERROR: no frags in {}".format(db))
        return 1
    ranked = rank(rows)

    demos = {r["demo"] for r in rows}
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "seek_list_master" + ("_recorder" if a.recorder_only else "")

    payload = {
        "label": "MASTER SEEK LIST -- built from the certified parser rebuild",
        "parser_commit": info.get("parser_commit"),
        "schema_version": info.get("schema_version"),
        "corpus_root": info.get("corpus_root"),
        "demos_unique": info.get("demos_unique"),
        "demos_failed": info.get("demos_failed"),
        "demos_contributing": len(demos),
        "recorder_only": bool(a.recorder_only),
        "total_candidates": len(ranked),
        "candidates": ranked,
    }
    (out_dir / (stem + ".json")).write_text(json.dumps(payload, indent=2),
                                            encoding="utf-8")
    cols = ["demo", "year", "map", "server_time_ms", "timestamp", "seekclock",
            "round", "attacker", "attacker_name", "victim", "victim_name",
            "MOD", "weapon", "by_recorder", "ms_to_prev_frag",
            "ms_to_next_frag", "kills_in_capture_window", "multikill_context",
            "tags", "rank_score", "rank_reasons"]
    with (out_dir / (stem + ".csv")).open("w", newline="",
                                          encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in ranked:
            w.writerow(r)

    print(payload["label"])
    print("  parser commit      : {}".format(info.get("parser_commit")))
    print("  demos in database  : {}".format(info.get("demos_unique")))
    print("  demos contributing : {}".format(len(demos)))
    print("  frag candidates    : {}".format(len(ranked)))
    print("  wrote {}".format(out_dir / (stem + ".csv")))
    print("        {}".format(out_dir / (stem + ".json")))
    print("")
    print("  top {}:".format(a.top))
    print("    {:>6} {:32} {:>7} {:>4} {:11} {:>3} {:>3}  reasons".format(
        "score", "demo", "clock", "rnd", "weapon", "atk", "vic"))
    for r in ranked[:a.top]:
        print("    {:>6.1f} {:32} {:>7} {:>4} {:11} {:>3} {:>3}  {}".format(
            r["rank_score"], (r["demo"] or "")[:32], r["timestamp"] or "",
            r["round"] if r["round"] is not None else "",
            (r["weapon"] or "")[:11],
            r["attacker"] if r["attacker"] is not None else "",
            r["victim"] if r["victim"] is not None else "",
            r["rank_reasons"][:52]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
