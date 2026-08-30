"""DB-only refinement of aim metrics from cached view timeseries.

The extractor's first pass measured flick duration as the whole -750ms
window and peak deg/s from raw single-frame steps (wrap spikes up to
13,000+ dps). The raw samples are cached in recognition_view_timeseries,
so this refinement never reopens a demo:

  onset detection : walk backward from the shot; the flick starts after the
                    last quiet frame (step < 1.5 deg per ~25ms frame).
  flick_deg_v2    : path displacement onset -> shot
  flick_ms_v2     : onset -> shot duration
  flick_dps_v2    : smoothed peak (3-frame moving average of step rate)
  settle_deg      : unchanged (already correct)

Writes *_v2 metrics into recognized_frags.attributes. Idempotent.
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

QUIET_STEP_DEG = 1.5


def _delta(a: float, b: float) -> float:
    return (b - a + 180.0) % 360.0 - 180.0


def refine(samples: list) -> dict | None:
    """samples: [(dt_ms, yaw, pitch)] with dt relative to the shot (<=0 pre)."""
    pre = [s for s in samples if s[0] <= 0]
    if len(pre) < 3:
        return None
    steps = []
    for i in range(1, len(pre)):
        dy = _delta(pre[i - 1][1], pre[i][1])
        dp = pre[i][2] - pre[i - 1][2]
        dt = max(1, pre[i][0] - pre[i - 1][0])
        steps.append((pre[i][0], math.hypot(dy, dp), dt))
    # onset: last quiet frame before the shot
    onset_idx = 0
    for i in range(len(steps) - 1, -1, -1):
        if steps[i][1] < QUIET_STEP_DEG:
            onset_idx = i + 1
            break
    active = steps[onset_idx:]
    if not active:
        return {"flick_deg_v2": 0.0, "flick_ms_v2": 0,
                "flick_dps_v2": 0.0}
    total = sum(s[1] for s in active)
    dur = active[-1][0] - (steps[onset_idx - 1][0] if onset_idx else pre[0][0])
    rates = [s[1] / s[2] * 1000.0 for s in active]
    smoothed = max(
        (sum(rates[i:i + 3]) / min(3, len(rates) - i)
         for i in range(len(rates))), default=0.0)
    # cleanliness: direction reversals in the active span (yaw sign flips
    # among meaningful steps) — a clean snap has 0-1; overshoot-correct has 2+.
    yaw_steps = []
    base = onset_idx if onset_idx else 1
    for i in range(base, len(pre)):
        dy = _delta(pre[i - 1][1], pre[i][1])
        if abs(dy) >= 1.0:
            yaw_steps.append(dy)
    reversals = sum(1 for i in range(1, len(yaw_steps))
                    if (yaw_steps[i] > 0) != (yaw_steps[i - 1] > 0))
    return {"flick_deg_v2": round(total, 1),
            "flick_ms_v2": int(dur),
            "flick_dps_v2": round(smoothed, 1),
            "flick_reversals": reversals}


def run() -> dict:
    conn = sqlite3.connect(RECOG_DB)
    conn.row_factory = sqlite3.Row
    t0 = time.time()
    rows = conn.execute(
        "SELECT v.demo_name, v.server_time_ms, v.samples, f.id, f.attributes"
        " FROM recognition_view_timeseries v JOIN recognized_frags f"
        " ON f.demo_name = v.demo_name AND"
        "    f.server_time_ms = v.server_time_ms").fetchall()
    updated = 0
    for r in rows:
        m = refine(json.loads(r["samples"]))
        if m is None:
            continue
        a = json.loads(r["attributes"] or "{}")
        if all(a.get(k) == v for k, v in m.items()):
            continue
        a.update(m)
        conn.execute("UPDATE recognized_frags SET attributes=? WHERE id=?",
                     (json.dumps(a), r["id"]))
        updated += 1
    conn.commit()
    conn.close()
    return {"rows": len(rows), "updated": updated,
            "wall_s": round(time.time() - t0, 1)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
