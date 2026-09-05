"""Whole-corpus aim: flicks and tracking, with or without a kill.

WHY A NEW EXTRACTOR RATHER THAN A WIDER WINDOW ON THE OLD ONE.

`extract_view_timeseries` is candidate-driven: it takes rail/flick/transfer
frags scoring above a threshold and reads -750..+250 ms around each. That was
right for describing a frag, and it is exactly why the archive has 13,463
view rows over 3,415 demos and cannot answer "show me the big flicks that
did NOT end in a kill". Every sample it holds is anchored to a death.

This walks the WHOLE recorder view series of every demo and finds aim events
on their own terms. It is the only part of this rebuild that genuinely
requires re-reading the raw demos: view angles were never persisted for
anything but those windows.

DO NOT CALL EVERYTHING A FLICK. The threshold is measured, not chosen --
`--calibrate` reports the real distribution of angular speed across sampled
demos and the constants below record what it said. A "flick" that fires on
the median mouse movement is a label with no information in it.

WHAT IS STORED. Detected events only, never the raw series: sampling every
snapshot of 4,292 demos would be tens of millions of rows describing mostly
somebody standing still. The series is reduced online and thrown away.

Usage:
    python -u engine/parser/mine_aim_events.py --calibrate [--sample N]
    python -u engine/parser/mine_aim_events.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
REBUILT_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
EPOCH_DB = REPO_ROOT / "creative_suite" / "database" / "mining_epoch.db"

MINER_VERSION = "aim-events-v1.0.0"

# SPLIT ON STILLNESS, NOT ON TIME.
#
# The first version split gestures on a gap between samples, and there is no
# gap: Quake Live sends a snapshot every 40-50 ms for the whole match. Every
# demo therefore became ONE gesture covering about ten thousand degrees of
# travel at an impossible 14,000 deg/s. A gesture ends when the aim goes
# quiet, which is what a human would call the end of a movement.
MOVE_FLOOR_DPS = 60.0    # below this the hand is effectively still
QUIET_MS = 120           # stillness for this long ends the gesture

# A VIEW DISCONTINUITY IS NOT A FLICK. Respawning, spectating a different
# player and teleporting all snap the camera instantly. No hand moves a mouse
# 120 degrees inside one 40 ms snapshot, so a step that large is the engine
# repositioning the view and it breaks the gesture rather than becoming its
# peak -- the same reasoning that excludes pads and teleports from the
# movement-speed distribution.
MAX_STEP_DEG = 120.0

# A gesture must cover at least this much angle to be worth a row at all.
# Below it the archive would fill with the constant micro-movement of a hand.
MIN_TRAVEL_DEG = 25.0

# CALIBRATED FROM THE REAL DISTRIBUTION, 2026-09-05.
#
# 20 demos, 5,970 gestures. Peak angular speed: p50 390, p90 1163, p95 1715,
# p99 3976, max 4781 deg/s. Travel: p50 64.5 deg, p95 215 deg.
#
# The first guess was FLICK at 400 dps -- which is the MEDIAN gesture. It
# would have labelled half of all mouse movement in the archive a flick, and
# a tag that fires on the median carries no information at all. These are
# p95 and p99: a flick is in the fastest twentieth of movements, a high
# flick in the fastest hundredth.
FLICK_DPS = 1700.0       # p95 of gesture peak angular speed
HIGH_FLICK_DPS = 3900.0  # p99
MICRO_DEG = 8.0          # net travel this small is a correction, not a flick

_SCHEMA = """
CREATE TABLE IF NOT EXISTS aim_events_v1 (
    -- Stable semantic key, for the same reason actions have one: a rowid is
    -- a property of insertion order, not of the gesture.
    aim_key       TEXT PRIMARY KEY,
    content_hash  TEXT NOT NULL,
    start_ms      INTEGER NOT NULL,
    end_ms        INTEGER NOT NULL,
    travel_deg    REAL NOT NULL,
    net_deg       REAL NOT NULL,
    peak_dps      REAL NOT NULL,
    duration_ms   INTEGER NOT NULL,
    samples       INTEGER NOT NULL,
    settle_deg    REAL,
    classes       TEXT NOT NULL DEFAULT '[]',
    version       TEXT NOT NULL,
    UNIQUE (content_hash, start_ms)
);
CREATE INDEX IF NOT EXISTS ix_aim_hash ON aim_events_v1(content_hash, start_ms);
CREATE INDEX IF NOT EXISTS ix_aim_dps ON aim_events_v1(peak_dps);
CREATE TABLE IF NOT EXISTS aim_runs_v1 (
    content_hash TEXT PRIMARY KEY,
    version      TEXT NOT NULL,
    mined_at     TEXT NOT NULL,
    events       INTEGER NOT NULL DEFAULT 0,
    samples      INTEGER NOT NULL DEFAULT 0,
    parse_ms     INTEGER NOT NULL DEFAULT 0,
    error        TEXT NOT NULL DEFAULT ''
);
"""


def epoch_conn(db: Path = EPOCH_DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=120)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def aim_key(content_hash: str, start_ms: int) -> str:
    """Which demo, and when the gesture began. Nothing else."""
    return "AIM:" + hashlib.sha1(
        f"{content_hash}|{int(start_ms)}".encode()).hexdigest()[:16]


def _ang(a: float, b: float) -> float:
    return (b - a + 180.0) % 360.0 - 180.0


def demo_paths(limit: int | None = None) -> list[tuple[str, str]]:
    """(content_hash, path) for every mined demo whose file is present."""
    with sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True) as c:
        hashes = [r[0] for r in c.execute(
            "SELECT content_hash FROM scanned_demos ORDER BY content_hash")]
    with sqlite3.connect(f"file:{REBUILT_DB}?mode=ro", uri=True) as c:
        paths = {r[0]: r[1] for r in c.execute(
            "SELECT content_hash, path FROM demos")}
    out = [(h, paths[h]) for h in hashes if h in paths]
    return out[:limit] if limit else out


def gestures(series: list[tuple[int, float, float]]) -> list[dict[str, Any]]:
    """Split a view series into gestures and measure each one.

    A gesture is a run of continuous aim movement bounded by stillness, with
    engine view-snaps excluded rather than counted as its peak.
    """
    out: list[dict[str, Any]] = []
    run: list[tuple[int, float, float]] = []
    quiet_for = 0

    def flush() -> None:
        if len(run) < 3:
            return
        travel = 0.0
        peak = 0.0
        for i in range(1, len(run)):
            dt = max(1, run[i][0] - run[i - 1][0])
            step = math.hypot(_ang(run[i - 1][1], run[i][1]),
                              run[i][2] - run[i - 1][2])
            travel += step
            peak = max(peak, step / dt * 1000.0)
        if travel < MIN_TRAVEL_DEG:
            return
        net = math.hypot(_ang(run[0][1], run[-1][1]), run[-1][2] - run[0][2])
        tail = [w for w in run if w[0] >= run[-1][0] - 100]
        settle = 0.0
        for i in range(1, len(tail)):
            settle += math.hypot(_ang(tail[i - 1][1], tail[i][1]),
                                 tail[i][2] - tail[i - 1][2])
        out.append({"start_ms": run[0][0], "end_ms": run[-1][0],
                    "travel_deg": round(travel, 1), "net_deg": round(net, 1),
                    "peak_dps": round(peak, 1),
                    "duration_ms": run[-1][0] - run[0][0],
                    "samples": len(run), "settle_deg": round(settle, 2)})

    prev: tuple[int, float, float] | None = None
    for s in series:
        if prev is None:
            prev = s
            continue
        dt = max(1, s[0] - prev[0])
        step = math.hypot(_ang(prev[1], s[1]), s[2] - prev[2])
        if step > MAX_STEP_DEG:
            # The engine moved the camera. End whatever was happening and
            # start again on the far side; the snap itself is discarded.
            flush()
            run = []
            quiet_for = 0
            prev = s
            continue
        dps = step / dt * 1000.0
        if dps >= MOVE_FLOOR_DPS:
            if not run:
                run = [prev]
            run.append(s)
            quiet_for = 0
        else:
            if run:
                quiet_for += dt
                if quiet_for >= QUIET_MS:
                    flush()
                    run = []
                    quiet_for = 0
                else:
                    run.append(s)
        prev = s
    flush()
    return out


def extract_one(content_hash: str, demo_path: str) -> dict[str, Any]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    t0 = time.time()
    try:
        from demo_parse import DM73Parser
        parsed = DM73Parser(Path(demo_path)).parse()
    except Exception as e:                                     # noqa: BLE001
        # One unreadable demo must never abort the rebuild.
        return {"content_hash": content_hash, "events": [], "samples": 0,
                "parse_ms": int((time.time() - t0) * 1000),
                "error": f"{type(e).__name__}: {e}"[:300]}

    series: list[tuple[int, float, float]] = []
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
    ev = gestures(series)
    for e in ev:
        cls = []
        if e["peak_dps"] >= HIGH_FLICK_DPS:
            cls.append("HIGH_FLICK")
        elif e["peak_dps"] >= FLICK_DPS:
            cls.append("FLICK")
        if e["net_deg"] <= MICRO_DEG:
            cls.append("MICRO_CORRECTION")
        if e["duration_ms"] >= 800 and e["peak_dps"] < FLICK_DPS:
            cls.append("TRACKING")
        e["classes"] = json.dumps(cls)
        e["version"] = MINER_VERSION
        e["content_hash"] = content_hash
        e["aim_key"] = aim_key(content_hash, e["start_ms"])
    return {"content_hash": content_hash, "events": ev, "samples": len(series),
            "parse_ms": int((time.time() - t0) * 1000), "error": ""}


def _write(out: dict[str, Any], db: Path = EPOCH_DB) -> None:
    cols = ("aim_key", "content_hash", "start_ms", "end_ms", "travel_deg",
            "net_deg", "peak_dps", "duration_ms", "samples", "settle_deg",
            "classes", "version")
    with epoch_conn(db) as c:
        if out["events"]:
            c.executemany(
                f"INSERT OR REPLACE INTO aim_events_v1 ({','.join(cols)}) "
                f"VALUES ({','.join('?' * len(cols))})",
                [tuple(e[k] for k in cols) for e in out["events"]])
        c.execute("INSERT OR REPLACE INTO aim_runs_v1(content_hash, version, "
                  "mined_at, events, samples, parse_ms, error) "
                  "VALUES(?,?,?,?,?,?,?)",
                  (out["content_hash"], MINER_VERSION, _now(),
                   len(out["events"]), out["samples"], out["parse_ms"],
                   out["error"]))


def done_hashes(db: Path = EPOCH_DB) -> set[str]:
    with epoch_conn(db) as c:
        return {r[0] for r in c.execute(
            "SELECT content_hash FROM aim_runs_v1 WHERE version = ?",
            (MINER_VERSION,))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) - 2))
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()

    demos = demo_paths(args.limit)
    if args.calibrate:
        step = max(1, len(demos) // args.sample)
        sample = demos[::step][:args.sample]
        peaks, travels, per_demo = [], [], []
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            for f in as_completed([ex.submit(extract_one, h, p)
                                   for h, p in sample]):
                o = f.result()
                if o["error"]:
                    continue
                per_demo.append((o["parse_ms"], len(o["events"])))
                for e in o["events"]:
                    peaks.append(e["peak_dps"])
                    travels.append(e["travel_deg"])
        peaks.sort()
        travels.sort()

        def q(v, p):
            return round(v[int(len(v) * p)], 1) if v else None
        avg_ms = statistics.mean(x for x, _ in per_demo) if per_demo else 0
        print(json.dumps({
            "demos_sampled": len(per_demo),
            "gestures": len(peaks),
            "gestures_per_demo": round(len(peaks) / max(1, len(per_demo)), 1),
            "peak_dps": {"p50": q(peaks, .5), "p90": q(peaks, .9),
                         "p95": q(peaks, .95), "p99": q(peaks, .99),
                         "max": round(peaks[-1], 1) if peaks else None},
            "travel_deg": {"p50": q(travels, .5), "p95": q(travels, .95)},
            "avg_parse_ms": round(avg_ms),
            "projected_full_corpus_min": round(
                avg_ms * len(demos) / args.workers / 60000, 1),
        }, indent=1))
        return 0

    already = done_hashes()
    todo = [(h, p) for h, p in demos if h not in already]
    print(f"{MINER_VERSION}: {len(todo)} demos ({len(demos) - len(todo)} done)",
          flush=True)
    t0 = time.time()
    total = failed = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(extract_one, h, p) for h, p in todo]
        for n, f in enumerate(as_completed(futs), 1):
            o = f.result()
            _write(o)
            total += len(o["events"])
            failed += bool(o["error"])
            if n % 100 == 0:
                print(f"  {n}/{len(todo)} demos, {total} aim events, "
                      f"{failed} failed, {time.time() - t0:.0f}s", flush=True)
    print(f"done: {total} aim events, {failed} failures, "
          f"{time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
