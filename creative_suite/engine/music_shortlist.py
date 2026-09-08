"""Rank the 1,483-track library for Quake fragmovie editing (§25).

Consumes the existing music_analysis.db cache — no re-analysis. The
per-track `downbeats` column is interpreted strictly as BAR_GRID_ESTIMATE
(§24): librosa fits a near-constant tempo, so beat-interval regularity is
near-perfect BY CONSTRUCTION and is deliberately NOT a ranking signal.

Signals that do discriminate:
  - BPM in the aggressive-editing sweet band (100-160, peak 120-150)
  - onset_rate: strong percussion / transient density
  - dynamics: rms_p90 vs rms_mean spread (usable drops vs wallpaper)
  - energy: absolute rms_p90
  - brightness: spectral centroid penalises muddy/ambient material
  - duration: 2-6 min usable structure

Output: output/demo_v2/music_shortlist.{csv,json} — the small curated pool
that deeper phrase/section analysis will run on later (NOT all 1,483).
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
DB_PATH = REPO_ROOT / "creative_suite" / "database" / "music_analysis.db"
OUT_DIR = REPO_ROOT / "output" / "demo_v2"
SHORTLIST_N = 60


def bpm_score(bpm: float | None) -> float:
    if not bpm:
        return 0.0
    b = bpm
    while b < 85 and b <= 200:      # half-time recorded tempo counts double
        b *= 2
    if 120 <= b <= 150:
        return 1.0
    if 100 <= b <= 165:
        return 0.7
    if 90 <= b <= 180:
        return 0.4
    return 0.1


def rank_track(row: dict) -> float:
    bpm = bpm_score(row.get("bpm"))
    onset = min(1.0, (row.get("onset_rate") or 0.0) / 3.0)
    rms_mean = row.get("rms_mean") or 0.0
    rms_p90 = row.get("rms_p90") or 0.0
    energy = min(1.0, rms_p90 / 0.30)
    dynamics = min(1.0, (rms_p90 - rms_mean) / 0.12) if rms_p90 > rms_mean else 0.0
    cent = row.get("centroid") or 0.0
    brightness = min(1.0, cent / 2500.0)
    dur = row.get("duration_s") or 0.0
    dur_ok = 1.0 if 120 <= dur <= 360 else (0.6 if 90 <= dur <= 480 else 0.2)
    return round(3.0 * bpm + 2.0 * onset + 2.0 * energy
                 + 1.5 * dynamics + 1.0 * brightness + 1.0 * dur_ok, 3)


def run(n: int = SHORTLIST_N) -> dict:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT content_id, path, name, duration_s, bpm, onset_rate,"
        " rms_mean, rms_p90, centroid FROM songs WHERE error IS NULL")]
    conn.close()

    for r in rows:
        r["frag_score"] = rank_track(r)
        r["bar_grid_note"] = "BAR_GRID_ESTIMATE"   # §24: not proven downbeats
    rows.sort(key=lambda r: -r["frag_score"])
    shortlist = rows[:n]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["frag_score", "name", "bpm", "duration_s", "onset_rate",
              "rms_mean", "rms_p90", "centroid", "bar_grid_note",
              "content_id", "path"]
    with open(OUT_DIR / "music_shortlist.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(shortlist)
    (OUT_DIR / "music_shortlist.json").write_text(
        json.dumps({"total_ranked": len(rows), "shortlist": shortlist},
                   indent=1), encoding="utf-8")
    return {"ranked": len(rows), "shortlist": len(shortlist),
            "top": [(r["name"], r["frag_score"]) for r in shortlist[:5]]}


if __name__ == "__main__":
    r = run()
    print(f"ranked {r['ranked']}, shortlist {r['shortlist']}")
    for name, s in r["top"]:
        print(f"  {s:6.2f}  {name}")
