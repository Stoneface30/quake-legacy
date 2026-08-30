"""Capture report (§22): batch outcome, durations, disk, tiers, top paths.

Usage:
    python -u creative_suite/engine/capture_report.py
Writes output/demo_v2/capture_report.json and prints the summary.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.database import demo_v2_db

FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
OUT = REPO_ROOT / "output" / "demo_v2" / "capture_report.json"


def run() -> dict:
    conn = demo_v2_db.connect()
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM generated_clips")]
    conn.close()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    sizes = {n: s for n, s in fconn.execute("SELECT name, size_bytes FROM demos")}
    fconn.close()

    captured = [r for r in rows if r["avi_path"] and r["qa_status"] == "PASS"]
    failed_qa = [r for r in rows if r["avi_path"] and r["qa_status"] == "FAIL"]
    rejected = [r for r in rows if r["promotion_status"] == "REJECTED"]
    pending = [r for r in rows if r["avi_path"] is None
               and r["promotion_status"] == "CANDIDATE"]

    def dur_s(r):
        return (r["capture_end_ms"] - r["capture_start_ms"]) / 1000.0

    total_bytes = 0
    for r in captured:
        p = Path(r["avi_path"])
        if p.exists():
            total_bytes += p.stat().st_size

    tiers = {}
    for r in captured:
        tiers[r["tier"] or "?"] = tiers.get(r["tier"] or "?", 0) + 1

    semantic_flagged = [r for r in captured
                        if r["semantic_qa"] and json.loads(r["semantic_qa"])]

    report = {
        "candidates_total": len(rows),
        "captured_pass": len(captured),
        "captured_qa_fail": len(failed_qa),
        "capture_rejected": len(rejected),
        "still_pending": len(pending),
        "small_demo_captures": sum(
            1 for r in captured
            if sizes.get(r["demo_name"], 1 << 30) < 800 * 1024),
        "clutch_captures": sum(1 for r in captured if r["clutch_context"]),
        "tiers": tiers,
        "alt_angle_worthy_captured": sum(
            1 for r in captured if r["alt_angle_worthy"]),
        "semantic_flagged": len(semantic_flagged),
        "semantic_flags": sorted({f for r in semantic_flagged
                                  for f in json.loads(r["semantic_qa"])}),
        "total_capture_duration_s": round(sum(dur_s(r) for r in captured), 1),
        "avg_capture_duration_s": round(
            sum(dur_s(r) for r in captured) / len(captured), 2) if captured else 0,
        "disk_usage_gb": round(total_bytes / 1e9, 2),
        "top20_paths": [
            {"clip": f"c{r['generated_clip_id']:05d}", "tier": r["tier"],
             "score": r["rank_score"], "path": r["avi_path"]}
            for r in sorted(captured, key=lambda r: -(r["rank_score"] or 0))[:20]],
    }
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: v for k, v in r.items() if k != "top20_paths"},
                     indent=1))
