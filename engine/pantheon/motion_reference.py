"""MotionReference — how a real player moves, mined from real demos.

WHY. Synthetic actors were lerping between marks at constant speed, snapping
their yaw at the midpoint of a turn, and switching animation on the same tick
the position started changing. Watched live, that reads as robotic -- and it
is, because none of those numbers came from anywhere. This module reads them
off the corpus, the same way the CA round grammar and the animation numbers
were read: the demo is the executable specification.

WHAT IS MEASURED, per ET_PLAYER entity in the recorded snapshots (the other
players, whose entity state carries pos, trDelta, yaw, legsAnim and
torsoAnim; the recorder's own playerstate animation indices are not in the
parser's field map and are deliberately not guessed):

  * ground speed while the legs are in the run family;
  * acceleration: ms from standing to 90% of run speed, and the reverse;
  * yaw slew: degrees per second while turning on the spot and while running;
  * animation latency: ms between the body stopping and the legs leaving
    RUN, and between starting and the legs entering it;
  * gesture length: ms TORSO_GESTURE stays up.

Nothing here identifies a player. Only statistics leave this module.

    python -m engine.pantheon.motion_reference --map overkill
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path

from engine.parser import demo_parse as dp
from engine.parser.demo_parse import DM73Parser

FRAGS_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/frags_rebuilt.db")
OUT_DIR = Path("docs/reference")

MAX_CLIENTS = 64
ANIM_TOGGLE = 128
ES_TORSO_ANIM, ES_LEGS_ANIM = 13, 15
LEGS_RUN_FAMILY = {15, 16}        # LEGS_RUN, LEGS_BACK  (bg_public.h)
LEGS_IDLE = 22
TORSO_GESTURE = 6
RUN_FRACTION = 0.9


def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def mine(path: Path) -> dict:
    """Per-entity motion samples from one demo."""
    parser = DM73Parser(path)
    tracks: dict[int, list[dict]] = defaultdict(list)
    orig = parser._parse_snapshot

    def hook(s, events, snapshots):
        orig(s, events, snapshots)
        t = parser._last_server_time
        for num, st in parser._entity_states.items():
            if num >= MAX_CLIENTS or st.get(dp._F_ETYPE) != 1:
                continue
            tracks[num].append({
                "t": t,
                "x": st.get(dp._F_POS_X, 0.0), "y": st.get(dp._F_POS_Y, 0.0),
                "vx": st.get(dp._F_VEL_X, 0.0), "vy": st.get(dp._F_VEL_Y, 0.0),
                "yaw": st.get(dp._F_YAW, 0.0),
                "legs": int(st.get(ES_LEGS_ANIM, 0)) & ~ANIM_TOGGLE,
                "torso": int(st.get(ES_TORSO_ANIM, 0)) & ~ANIM_TOGGLE,
                "ground": st.get(dp._F_GROUND, 0),
            })

    parser._parse_snapshot = hook
    parser.parse()
    return {"map": parser._map_name if hasattr(parser, "_map_name") else None,
            "tracks": tracks}


def derive(tracks: dict[int, list[dict]]) -> dict:
    run_speed, accel_ms, decel_ms = [], [], []
    yaw_still, yaw_moving = [], []
    start_lag, stop_lag, gesture_ms, dt_ms = [], [], [], []
    for samples in tracks.values():
        s = [x for x in samples if x["ground"] != 1023]      # on the ground
        if len(s) < 20:
            continue
        for a, b in zip(s, s[1:]):
            dt = b["t"] - a["t"]
            if not 0 < dt <= 200:
                continue
            dt_ms.append(dt)
            sp = math.hypot(b["vx"], b["vy"])
            if b["legs"] in LEGS_RUN_FAMILY and sp > 50:
                run_speed.append(sp)
            dy = abs((b["yaw"] - a["yaw"] + 180) % 360 - 180)
            rate = dy / (dt / 1000.0)
            (yaw_moving if sp > 50 else yaw_still).append(rate)
        # ramps and lags
        top = _pct(run_speed, 0.5) or 320.0
        i = 0
        while i < len(s) - 1:
            sp0 = math.hypot(s[i]["vx"], s[i]["vy"])
            sp1 = math.hypot(s[i + 1]["vx"], s[i + 1]["vy"])
            if sp0 < 30 and sp1 >= 30:                    # started moving
                t0 = s[i + 1]["t"]
                j = i + 1
                while j < len(s) and math.hypot(s[j]["vx"], s[j]["vy"]) < RUN_FRACTION * top:
                    j += 1
                if j < len(s) and s[j]["t"] - t0 < 1500:
                    accel_ms.append(s[j]["t"] - t0)
                k = i + 1
                while k < len(s) and s[k]["legs"] not in LEGS_RUN_FAMILY:
                    k += 1
                if k < len(s) and s[k]["t"] - t0 < 1000:
                    start_lag.append(s[k]["t"] - t0)
            if sp0 >= RUN_FRACTION * top and sp1 < RUN_FRACTION * top:   # slowing
                t0 = s[i + 1]["t"]
                j = i + 1
                while j < len(s) and math.hypot(s[j]["vx"], s[j]["vy"]) > 30:
                    j += 1
                if j < len(s) and s[j]["t"] - t0 < 1500:
                    decel_ms.append(s[j]["t"] - t0)
                    k = j
                    while k < len(s) and s[k]["legs"] in LEGS_RUN_FAMILY:
                        k += 1
                    if k < len(s) and s[k]["t"] - s[j]["t"] < 1000:
                        stop_lag.append(s[k]["t"] - s[j]["t"])
            i += 1
        # gesture length
        i = 0
        while i < len(samples):
            if samples[i]["torso"] == TORSO_GESTURE:
                j = i
                while j < len(samples) and samples[j]["torso"] == TORSO_GESTURE:
                    j += 1
                if j < len(samples):
                    gesture_ms.append(samples[j]["t"] - samples[i]["t"])
                i = j
            i += 1

    def summary(xs, unit):
        return {"n": len(xs), "unit": unit,
                "p10": _pct(xs, 0.10), "p50": _pct(xs, 0.50), "p90": _pct(xs, 0.90),
                "mean": round(statistics.fmean(xs), 1) if xs else None}

    return {
        "snapshot_interval_ms": summary(dt_ms, "ms"),
        "run_speed": summary(run_speed, "units/s"),
        "accel_to_90pct": summary(accel_ms, "ms"),
        "decel_to_stop": summary(decel_ms, "ms"),
        "yaw_rate_standing": summary(yaw_still, "deg/s"),
        "yaw_rate_running": summary(yaw_moving, "deg/s"),
        "legs_run_start_lag": summary(start_lag, "ms"),
        "legs_run_stop_lag": summary(stop_lag, "ms"),
        "gesture_length": summary(gesture_ms, "ms"),
        "entities_sampled": len(tracks),
    }


def reference_demos(map_name: str, limit: int) -> list[Path]:
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        """select path from demos where map_name=? and gametype='CA'
           and accepted_frags > 10 order by size_bytes limit ?""",
        (map_name, limit)).fetchall()
    con.close()
    return [Path(r[0]) for r in rows]


def build(map_name: str, limit: int = 3) -> dict:
    merged: dict[int, list[dict]] = {}
    n = 0
    for i, p in enumerate(reference_demos(map_name, limit)):
        if not p.exists():
            continue
        t = mine(p)["tracks"]
        for k, v in t.items():
            merged[i * MAX_CLIENTS + k] = v
        n += 1
    out = {"map": map_name, "demos_used": n, **derive(merged)}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"motion_reference_{map_name}.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", default="overkill")
    ap.add_argument("--limit", type=int, default=3)
    a = ap.parse_args()
    out = build(a.map, a.limit)
    print(f"{a.map}: {out['demos_used']} demos, {out['entities_sampled']} tracks")
    for k, v in out.items():
        if isinstance(v, dict) and "p50" in v:
            print(f"  {k:24s} n={v['n']:6d}  p10={v['p10']}  p50={v['p50']}  "
                  f"p90={v['p90']}  {v['unit']}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
