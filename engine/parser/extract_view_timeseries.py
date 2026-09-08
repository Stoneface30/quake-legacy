"""Targeted extractor: recorder view-angle timeseries around aim events.

Candidates: rail/flick/transfer/precision rows (13,487 events / 3,415 demos
measured 2026-08-30). Window -750..+250 ms around the kill. Persists raw
samples to recognition_view_timeseries and derived TRUE flick metrics into
recognized_frags.attributes:
  view_samples (count), flick_true_deg, flick_true_ms, flick_peak_dps,
  settle_deg (aim movement in the final 100 ms — low = clean snap)
Resumable via view_extracted(content_hash, version).

Usage: python -u engine/parser/extract_view_timeseries.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

EXTRACTOR_VERSION = 1
PRE_MS, POST_MS = 750, 250
AIM_CLASSES = {"RAIL_FRAG", "FLICK_SHOT", "RAIL_FLICK", "RAIL_CONSECUTIVE",
               "TARGET_TRANSFER", "PIXEL_SHOT_CANDIDATE",
               "REACTION_SHOT_CANDIDATE"}
MIN_SCORE_HITSCAN = 6.0


def candidate_map() -> dict[str, list[int]]:
    c = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    out: dict[str, list[int]] = {}
    for r in c.execute("SELECT demo_name, weapon_name, server_time_ms,"
                       " classes, highlight_score, attributes"
                       " FROM recognized_frags"):
        a = json.loads(r["attributes"] or "{}")
        if a.get("view_samples") is not None:
            continue
        cl = {x["name"] if isinstance(x, dict) else x
              for x in json.loads(r["classes"] or "[]")}
        if ((cl & AIM_CLASSES)
                or (r["weapon_name"] in ("RAILGUN", "SHOTGUN")
                    and (r["highlight_score"] or 0) >= MIN_SCORE_HITSCAN)):
            out.setdefault(r["demo_name"], []).append(r["server_time_ms"])
    c.close()
    return out


def _ang_delta(a: float, b: float) -> float:
    d = (b - a + 180.0) % 360.0 - 180.0
    return d


def extract_one(demo_path: str, frag_times: list[int]) -> dict[int, dict]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from demo_parse import DM73Parser
    parsed = DM73Parser(Path(demo_path)).parse()
    series = []
    for s in parsed.get("snapshots", []):
        t = None
        for k in ("server_time", "server_time_ms", "serverTime", "t_ms", "t"):
            if s.get(k) is not None:
                t = int(s[k])
                break
        if t is None or s.get("angle_yaw") is None:
            continue
        series.append((t, float(s["angle_yaw"]),
                       float(s.get("angle_pitch") or 0.0)))
    series.sort()
    out: dict[int, dict] = {}
    for ft in frag_times:
        win = [(t, y, p) for t, y, p in series
               if ft - PRE_MS <= t <= ft + POST_MS]
        if len(win) < 3:
            continue
        # displacement along the path (wrap-aware), peak angular velocity
        total = 0.0
        peak_dps = 0.0
        for i in range(1, len(win)):
            dt = max(1, win[i][0] - win[i - 1][0])
            dy = _ang_delta(win[i - 1][1], win[i][1])
            dp = win[i][2] - win[i - 1][2]
            step = math.hypot(dy, dp)
            total += step
            peak_dps = max(peak_dps, step / dt * 1000.0)
        pre = [w for w in win if w[0] <= ft]
        settle = 0.0
        tail = [w for w in pre if w[0] >= ft - 100]
        for i in range(1, len(tail)):
            settle += math.hypot(_ang_delta(tail[i - 1][1], tail[i][1]),
                                 tail[i][2] - tail[i - 1][2])
        # true flick: displacement from window start to shot
        net = math.hypot(_ang_delta(pre[0][1], pre[-1][1]),
                         pre[-1][2] - pre[0][2]) if len(pre) >= 2 else 0.0
        out[ft] = {
            "metrics": {
                "view_samples": len(win),
                "flick_true_deg": round(net, 1),
                "flick_true_ms": pre[-1][0] - pre[0][0] if len(pre) >= 2 else 0,
                "flick_peak_dps": round(peak_dps, 1),
                "settle_deg": round(settle, 2),
            },
            "samples": [(t - ft, round(y, 2), round(p, 2))
                        for t, y, p in win],
        }
    return out


def run(limit: int | None = None, workers: int = 10) -> dict:
    conn = sqlite3.connect(RECOG_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS view_extracted ("
                 " content_hash TEXT PRIMARY KEY, demo_name TEXT,"
                 " version INTEGER, events INTEGER, status TEXT,"
                 " extracted_at TEXT DEFAULT (datetime('now')))")
    conn.execute("CREATE TABLE IF NOT EXISTS recognition_view_timeseries ("
                 " demo_name TEXT, server_time_ms INTEGER, version INTEGER,"
                 " samples TEXT, PRIMARY KEY (demo_name, server_time_ms))")
    conn.commit()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    meta = {n: (p, dup or h) for n, p, h, dup in fconn.execute(
        "SELECT name, path, content_hash, duplicate_of FROM demos")}
    fconn.close()

    done = {r[0] for r in conn.execute(
        "SELECT content_hash FROM view_extracted WHERE version=? AND"
        " status='ok'", (EXTRACTOR_VERSION,))}
    cands = candidate_map()
    todo = [(d, *meta[d], ts) for d, ts in cands.items()
            if d in meta and meta[d][1] not in done]
    if limit:
        todo = todo[:limit]

    stats = {"eligible_events": sum(len(t) for t in cands.values()),
             "demos_to_open": len(todo), "events_updated": 0, "failed": 0}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_one, path, ts): (demo, h, ts)
                for demo, path, h, ts in todo}
        n = 0
        for fut in as_completed(futs):
            demo, h, ts = futs[fut]
            n += 1
            try:
                res = fut.result()
            except Exception as e:   # noqa: BLE001 - per-demo isolation
                conn.execute("INSERT OR REPLACE INTO view_extracted VALUES"
                             " (?,?,?,?,?,datetime('now'))",
                             (h, demo, EXTRACTOR_VERSION, 0,
                              f"fail: {type(e).__name__}"))
                conn.commit()
                stats["failed"] += 1
                continue
            for ft, payload in res.items():
                row = conn.execute(
                    "SELECT id, attributes FROM recognized_frags WHERE"
                    " demo_name=? AND server_time_ms=?", (demo, ft)).fetchone()
                if row is None:
                    continue
                a = json.loads(row[1] or "{}")
                a.update(payload["metrics"])
                conn.execute("UPDATE recognized_frags SET attributes=?"
                             " WHERE id=?", (json.dumps(a), row[0]))
                conn.execute("INSERT OR REPLACE INTO"
                             " recognition_view_timeseries VALUES (?,?,?,?)",
                             (demo, ft, EXTRACTOR_VERSION,
                              json.dumps(payload["samples"])))
                stats["events_updated"] += 1
            conn.execute("INSERT OR REPLACE INTO view_extracted VALUES"
                         " (?,?,?,?, 'ok', datetime('now'))",
                         (h, demo, EXTRACTOR_VERSION, len(res)))
            conn.commit()
            if n % 200 == 0:
                print(f"[view] {n}/{len(todo)} demos,"
                      f" {stats['events_updated']} events,"
                      f" {time.time()-t0:.0f}s", flush=True)
    stats["wall_s"] = round(time.time() - t0, 1)
    conn.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    print(json.dumps(run(args.limit, args.workers), indent=1))
