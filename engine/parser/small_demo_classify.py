"""Classify demos under 800 KB (charter §4).

Small demos are never auto-labelled broken: they may be short captured clips,
partial recordings, aborted demos, or genuinely corrupt. Classification uses
parser evidence already stored in frags_rebuilt.db — no re-parse.

Usage:
    python -u engine/parser/small_demo_classify.py
Writes output/demo_v2/small_demo_classification.{csv,json}.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DIR = REPO_ROOT / "output" / "demo_v2"
SIZE_LIMIT = 800 * 1024
SHORT_DURATION_MS = 120_000


def classify(row: dict) -> str:
    """Classify one demos-table row. NULLs are coerced to 0 first."""
    duration_ms = row.get("duration_ms") or 0
    rounds = row.get("rounds") or 0
    accepted_frags = row.get("accepted_frags") or 0
    packet_errors = row.get("packet_errors") or 0

    if row.get("parse_error"):
        return "CORRUPT_UNREADABLE"
    if packet_errors > 0 and accepted_frags > 0:
        return "CORRUPT_RECOVERABLE"
    if packet_errors > 0:
        return "TRUNCATED_BUT_PARSEABLE"
    if accepted_frags > 0 and (duration_ms <= SHORT_DURATION_MS or rounds <= 1):
        return "VALID_SHORT_CLIP"
    if accepted_frags > 0:
        return "VALID_PARTIAL_DEMO"
    if accepted_frags == 0:
        return "ABORTED_RECORDING"
    return "UNKNOWN"


def run(db_path: Path = DB_PATH, out_dir: Path = OUT_DIR) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    dup_count = conn.execute(
        "SELECT count(*) FROM demos WHERE size_bytes < ? AND duplicate_of IS NOT NULL",
        (SIZE_LIMIT,),
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT d.demo_id, d.name, d.size_bytes, d.year, d.map_name, d.gametype,
               d.duration_ms, d.rounds, d.players, d.accepted_frags,
               d.packet_errors, d.parse_error, d.recorder_name, d.recorder_is_alias,
               (SELECT count(*) FROM frags f
                 WHERE f.demo_id = d.demo_id AND f.by_recorder = 1) AS recorder_frags,
               (SELECT max(f.score) FROM frags f
                 WHERE f.demo_id = d.demo_id AND f.by_recorder = 1) AS max_recorder_score
        FROM demos d
        WHERE d.size_bytes < ? AND d.duplicate_of IS NULL
        ORDER BY d.size_bytes
        """,
        (SIZE_LIMIT,),
    ).fetchall()

    out_dir.mkdir(parents=True, exist_ok=True)
    counts: Counter = Counter()
    records = []
    for r in rows:
        d = dict(r)
        cls = classify(d)
        counts[cls] += 1
        d["classification"] = cls
        d["has_recorder_frags"] = int((d.get("recorder_frags") or 0) > 0)
        records.append(d)

    # Valuable-tiny surface (§4): small demos holding a high-score recorder frag
    valuable = sorted(
        (d for d in records if (d.get("max_recorder_score") or 0) >= 10),
        key=lambda d: d["max_recorder_score"], reverse=True,
    )

    fields = list(records[0].keys()) if records else []
    with open(out_dir / "small_demo_classification.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)

    summary = {
        "size_limit_bytes": SIZE_LIMIT,
        "unique_small_demos": len(records),
        "duplicate_small_files_skipped": dup_count,
        "class_counts": dict(counts),
        "valuable_small_demos": [
            {k: d[k] for k in ("name", "size_bytes", "classification",
                               "recorder_frags", "max_recorder_score")}
            for d in valuable[:50]
        ],
        "records": records,
    }
    with open(out_dir / "small_demo_classification.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)

    conn.close()
    return summary


if __name__ == "__main__":
    s = run()
    print(f"unique small demos: {s['unique_small_demos']} "
          f"(+{s['duplicate_small_files_skipped']} duplicate files skipped)")
    for k, v in sorted(s["class_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:24s} {v}")
    print(f"valuable (max recorder score >= 10): {len(s['valuable_small_demos'])} listed")
    sys.exit(0)
