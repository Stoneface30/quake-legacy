"""Movement as an ACTION, not as a number.

A speed moment is a contiguous stretch of movement with a shape -- a run-up,
a fast section, a release. One sample above a threshold is not a moment, and
219,108 jump-pad events are not 219,108 things to review. This module turns
both into the smallest honest unit a person can actually judge.

WHERE THE MOVEMENT TRUTH IS. No dense player position stream is cached: the
view timeseries is frag-anchored and there is no playerstate trace table. But
`semantic_events_v1` holds 457,190 JUMP events sourced from the recorder's own
playerstate, each with a position. In Quake, moving fast MEANS jumping
continuously -- strafe jumping is the movement -- so consecutive jumps are a
real sampling of a real run, roughly two to three per second while it lasts.
That is the trace, and it needs no reparse.

THE THRESHOLD IS MEASURED, NOT CHOSEN. Across 175,035 inter-jump segments:

    p50  417   p75  464   p90  529   p95  587   p97  673   p99 1,449

HIGH_SPEED starts at the 95th percentile. The p97-to-p99 cliff is the
interesting part: 673 to 1,449 is not a faster player, it is a discontinuity
-- a teleport or a pad launch moving the position without the player
travelling. Those are detected and excluded rather than becoming the fastest
"runs" in the corpus, which is exactly what a naive maximum would have found.

ONE ACTION, MANY TAGS, ONE REVIEW ITEM. A run that ends in a frag is linked
to that frag's canonical occurrence; it does not invent a second historical
event. A pad launch that carries into a kill is one JUMPPAD_ACTION carrying
both tags, not two items. The five buttons judge the presentation
opportunity; the frag keeps its own identity.
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

MOVEMENT_VERSION = "movement-moments-v1.0.0"

# Segment plausibility. A gap longer than this is two separate actions, not
# one long one; a shorter one is the same jump landing twice.
MIN_DT_S = 0.05
MAX_DT_S = 1.2

# Above this, a "speed" is a position discontinuity rather than a player. The
# measured distribution has a cliff between p97 (673) and p99 (1,449) that no
# amount of skill accounts for.
IMPLAUSIBLE_UPS = 1200.0

# Merge two fast stretches separated by at most this much ordinary movement.
# Without it one run fragments into three moments over two slow jumps.
MERGE_GAP_MS = 900

# A single fast segment is a coincidence; a run has shape.
MIN_SEGMENTS = 2

# Media padding either side of the action. The event has its own duration and
# is not truncated to force a six-second clip.
PAD_PRE_MS = 1500
PAD_POST_MS = 1500
MAX_MEDIA_MS = 20000

# Jump-pad flight bounds. Beyond the upper one we have lost the player rather
# than watched a very long flight.
PAD_MAX_AIRTIME_MS = 6000

HIGH_SPEED = "HIGH_SPEED_MOVEMENT"
JUMPPAD_ACTION = "JUMPPAD_ACTION"
KINDS = (HIGH_SPEED, JUMPPAD_ACTION)

# Machine traits. Descriptive, and several may apply to one action.
T_STRAFE_CHAIN = "STRAFE_CHAIN"
T_PAD_EXIT = "HIGH_SPEED_PAD_EXIT"
T_ENDS_IN_FRAG = "ENDS_IN_FRAG"
T_ENDS_IN_DEATH = "ENDS_IN_DEATH"
T_ENGAGEMENT_ENTRY = "FAST_ENGAGEMENT_ENTRY"
T_ESCAPE = "ESCAPE"
T_LONG_RUN = "LONG_RUN"
T_BIG_AIRTIME = "BIG_AIRTIME"

RECORDER_PLAYERSTATE = "RECORDER_PLAYERSTATE_JUMPS"

SCHEMA = """
CREATE TABLE IF NOT EXISTS movement_moments_v1(
  moment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  content_hash   TEXT NOT NULL,
  kind           TEXT NOT NULL,
  start_ms       INTEGER NOT NULL,
  peak_ms        INTEGER NOT NULL,
  end_ms         INTEGER NOT NULL,
  duration_ms    INTEGER NOT NULL,
  peak_speed     REAL,
  mean_speed     REAL,
  entry_speed    REAL,
  exit_speed     REAL,
  segments       INTEGER,
  distance_units REAL,
  airtime_ms     INTEGER,
  map            TEXT,
  round          INTEGER,
  related_occurrence_id INTEGER,
  traits         TEXT NOT NULL DEFAULT '[]',
  speed_pctile   REAL,
  provenance     TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_mm_hash ON movement_moments_v1(content_hash, start_ms);
CREATE INDEX IF NOT EXISTS ix_mm_kind ON movement_moments_v1(kind);
CREATE INDEX IF NOT EXISTS ix_mm_occ ON movement_moments_v1(related_occurrence_id);
CREATE INDEX IF NOT EXISTS ix_mm_speed ON movement_moments_v1(peak_speed);
CREATE TABLE IF NOT EXISTS movement_runs_v1(
  version TEXT PRIMARY KEY, built_at TEXT NOT NULL, threshold_ups REAL,
  segments INTEGER, moments INTEGER, discontinuities INTEGER);
"""


def _conn(db: Path = RECOGNITION_DB, ro: bool = False) -> sqlite3.Connection:
    uri = f"file:{db}?mode=ro" if ro else str(db)
    c = sqlite3.connect(uri, uri=ro, timeout=180)
    c.row_factory = sqlite3.Row
    return c


@dataclass
class Segment:
    t0: int
    t1: int
    speed: float
    dist: float
    discontinuous: bool = False


def _dist(a: sqlite3.Row, b: sqlite3.Row) -> float | None:
    if None in (a["x"], a["y"], b["x"], b["y"]):
        return None
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def segments_for(jumps: list[sqlite3.Row],
                 teleport_times: Iterable[int] = ()) -> list[Segment]:
    """Inter-jump segments with discontinuities marked, not dropped silently.

    A teleport between two jumps produces a huge apparent speed. Marking it
    keeps the evidence -- the segment existed -- while stopping it becoming
    the fastest run in the corpus.
    """
    tps = sorted(teleport_times)
    out: list[Segment] = []
    for a, b in zip(jumps, jumps[1:]):
        dt = (b["server_time_ms"] - a["server_time_ms"]) / 1000.0
        if not (MIN_DT_S < dt <= MAX_DT_S):
            continue
        d = _dist(a, b)
        if d is None:
            continue
        v = d / dt
        disc = v > IMPLAUSIBLE_UPS or any(
            a["server_time_ms"] <= t <= b["server_time_ms"] for t in tps)
        out.append(Segment(a["server_time_ms"], b["server_time_ms"], v, d, disc))
    return out


def runs_from(segments: list[Segment], threshold: float) -> list[list[Segment]]:
    """Group fast segments into contiguous runs, merging small ordinary gaps.

    Without the merge, one continuous sprint fragments into three moments
    over two slower jumps -- the failure the brief names explicitly.
    """
    runs: list[list[Segment]] = []
    cur: list[Segment] = []
    last_end: int | None = None
    for s in segments:
        if s.discontinuous or s.speed < threshold:
            if cur and last_end is not None and s.t1 - last_end > MERGE_GAP_MS:
                runs.append(cur)
                cur = []
            continue
        if cur and last_end is not None and s.t0 - last_end > MERGE_GAP_MS:
            runs.append(cur)
            cur = []
        cur.append(s)
        last_end = s.t1
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= MIN_SEGMENTS]


def calibrate(db: Path = RECOGNITION_DB, pct: float = 95.0
              ) -> tuple[float, int, int]:
    """Return (threshold_ups, n_segments, n_discontinuities), measured."""
    with _conn(db, ro=True) as c:
        rows = c.execute(
            "SELECT content_hash, server_time_ms, x, y FROM semantic_events_v1 "
            "WHERE type='jump' AND source='playerstate' AND x IS NOT NULL "
            "AND y IS NOT NULL ORDER BY content_hash, server_time_ms").fetchall()
    speeds, disc = [], 0
    by_hash: dict[str, list] = {}
    for r in rows:
        by_hash.setdefault(r["content_hash"], []).append(r)
    for js in by_hash.values():
        for s in segments_for(js):
            if s.discontinuous:
                disc += 1
            else:
                speeds.append(s.speed)
    speeds.sort()
    thr = speeds[int(len(speeds) * pct / 100)] if speeds else 0.0
    return thr, len(speeds), disc


# Occurrences, loaded ONCE and matched in memory.
#
# The first version ran a per-moment query joining kill_occurrences to
# kill_events and ordering by ABS(time difference). There is no index that
# serves that shape, so SQLite scanned 206,268 occurrences for each of ~55,000
# moments. It ran for 35 minutes without finishing. Loading the whole table
# is 206k rows -- a few seconds and a modest amount of memory -- and turns the
# lookup into a bisect.
import bisect as _bisect                                       # noqa: E402


def load_occurrences(c: sqlite3.Connection) -> dict[str, tuple[list, list]]:
    """Per demo: sorted times, and the occurrence rows beside them."""
    out: dict[str, tuple[list, list]] = {}
    for r in c.execute(
            "SELECT k.content_hash h, o.server_time_ms t, o.occurrence_id, "
            "o.round, o.map, k.is_recorder_victim "
            "FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "ORDER BY k.content_hash, o.server_time_ms"):
        ts, rows = out.setdefault(r["h"], ([], []))
        ts.append(int(r["t"]))
        rows.append((int(r["occurrence_id"]), r["round"], r["map"],
                     bool(r["is_recorder_victim"])))
    return out


def _near_occurrence(index: dict[str, tuple[list, list]], chash: str,
                     t_end: int, window_ms: int = 4000
                     ) -> tuple[int | None, int | None, str | None, bool]:
    """The canonical frag this action ran into, if any. Linked, never copied."""
    got = index.get(chash)
    if not got:
        return None, None, None, False
    ts, rows = got
    i = _bisect.bisect_left(ts, t_end - 500)
    best = None
    while i < len(ts) and ts[i] <= t_end + window_ms:
        d = abs(ts[i] - t_end)
        if best is None or d < best[0]:
            best = (d, rows[i])
        i += 1
    if best is None:
        return None, None, None, False
    oid, rnd, mp, died = best[1]
    return oid, rnd, mp, died


def build(db: Path = RECOGNITION_DB, progress: bool = False) -> dict[str, Any]:
    """Derive movement moments. Idempotent; replaces the previous build."""
    thr, n_seg, n_disc = calibrate(db)
    if progress:
        print(f"  threshold {thr:.0f} ups from {n_seg:,} segments "
              f"({n_disc:,} discontinuities excluded)", flush=True)
    con = _conn(db)
    con.executescript(SCHEMA)

    with _conn(db, ro=True) as ro:
        jumps = ro.execute(
            "SELECT content_hash, server_time_ms, x, y, z FROM semantic_events_v1 "
            "WHERE type='jump' AND source='playerstate' AND x IS NOT NULL "
            "AND y IS NOT NULL ORDER BY content_hash, server_time_ms").fetchall()
        pads = ro.execute(
            "SELECT content_hash, server_time_ms, x, y, z FROM semantic_events_v1 "
            "WHERE type='jump_pad' AND source='playerstate' "
            "ORDER BY content_hash, server_time_ms").fetchall()
        tps: dict[str, list[int]] = {}
        for r in ro.execute(
                "SELECT content_hash, server_time_ms FROM teleport_transits_v1 "
                "WHERE outcome='TELEPORT_PLAYER_CONFIRMED'"):
            tps.setdefault(r["content_hash"], []).append(int(r["server_time_ms"]))

    by_hash: dict[str, list] = {}
    for r in jumps:
        by_hash.setdefault(r["content_hash"], []).append(r)
    pads_by: dict[str, list] = {}
    for r in pads:
        pads_by.setdefault(r["content_hash"], []).append(r)

    rows: list[tuple] = []
    all_peaks: list[float] = []
    for chash, js in by_hash.items():
        segs = segments_for(js, tps.get(chash, ()))
        for run in runs_from(segs, thr):
            peak = max(run, key=lambda s: s.speed)
            dist = sum(s.dist for s in run)
            dur = run[-1].t1 - run[0].t0
            mean = dist / (dur / 1000.0) if dur else peak.speed
            traits = [T_STRAFE_CHAIN]
            if len(run) >= 5:
                traits.append(T_LONG_RUN)
            all_peaks.append(peak.speed)
            rows.append([chash, HIGH_SPEED, run[0].t0, peak.t1, run[-1].t1,
                         dur, peak.speed, mean, run[0].speed, run[-1].speed,
                         len(run), dist, None, None, None, None, traits, None,
                         RECORDER_PLAYERSTATE])

    # Jump pads. One physical action per activation: the launch, the flight,
    # and the first thing that happens after it.
    for chash, ps in pads_by.items():
        js = by_hash.get(chash, [])
        for p in ps:
            t = int(p["server_time_ms"])
            nxt = next((j for j in js if j["server_time_ms"] > t + 200), None)
            air = (int(nxt["server_time_ms"]) - t) if nxt else None
            if air is not None and air > PAD_MAX_AIRTIME_MS:
                air = None
            d = _dist(p, nxt) if nxt is not None else None
            traits = [JUMPPAD_ACTION]
            if air and air >= 1500:
                traits.append(T_BIG_AIRTIME)
            # Displacement over airtime is a FLIGHT speed, and only when the
            # next jump is genuinely the landing. If the player ran on before
            # jumping again, the distance covers the run too and the figure
            # becomes nonsense -- an early build ranked pads by a 7,015 ups
            # "peak", which is not a speed anyone has ever moved at. Above the
            # plausibility ceiling no speed is recorded rather than a wrong
            # one, and the action is still a moment: airtime and distance
            # stand on their own.
            flight = (d / (air / 1000.0)) if (d and air) else None
            if flight is not None and flight > IMPLAUSIBLE_UPS:
                flight = None
            if flight is not None and flight >= thr:
                traits.append(T_PAD_EXIT)
            end = t + (air or 1200)
            rows.append([chash, JUMPPAD_ACTION, t, t, end, end - t,
                         flight, None, None, None, 1, d, air, None, None,
                         None, traits, None, RECORDER_PLAYERSTATE])

    all_peaks.sort()

    def pctile(v: float | None) -> float | None:
        if v is None or not all_peaks:
            return None
        lo, hi = 0, len(all_peaks)
        while lo < hi:
            mid = (lo + hi) // 2
            if all_peaks[mid] < v:
                lo = mid + 1
            else:
                hi = mid
        return round(lo / len(all_peaks) * 100, 1)

    occ_index = load_occurrences(con)
    # A movement moment has a map whether or not it ends in a kill. Without
    # this, every unlinked run showed a blank map in the reviewer.
    demo_map = {r["h"]: r["m"] for r in con.execute(
        "SELECT k.content_hash h, MIN(o.map) m FROM kill_occurrences_v1 o "
        "JOIN kill_events_v1 k ON k.kill_event_id = o.best_observation_id "
        "GROUP BY 1")}
    if progress:
        print(f"  {sum(len(v[0]) for v in occ_index.values()):,} occurrences "
              f"indexed for linking", flush=True)
    with con:
        con.execute("DELETE FROM movement_moments_v1")
        for r in rows:
            occ, rnd, mp, died = _near_occurrence(occ_index, r[0], r[4])
            mp = mp or demo_map.get(r[0])
            traits = list(r[16])
            if occ is not None:
                traits.append(T_ENDS_IN_DEATH if died else T_ENDS_IN_FRAG)
            con.execute(
                "INSERT INTO movement_moments_v1(content_hash, kind, start_ms,"
                " peak_ms, end_ms, duration_ms, peak_speed, mean_speed,"
                " entry_speed, exit_speed, segments, distance_units, airtime_ms,"
                " map, round, related_occurrence_id, traits, speed_pctile,"
                " provenance) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
                 r[10], r[11], r[12], mp, rnd, occ, json.dumps(traits),
                 pctile(r[6]), r[18]))
        con.execute("INSERT OR REPLACE INTO movement_runs_v1 VALUES "
                    "(?,datetime('now'),?,?,?,?)",
                    (MOVEMENT_VERSION, thr, n_seg, len(rows), n_disc))
    out = summary(db)
    con.close()
    return out


def media_window(start_ms: int, end_ms: int) -> tuple[int, int]:
    """Media bounds. The action keeps its own duration -- it is padded, not
    truncated to a fixed six seconds."""
    s = max(0, start_ms - PAD_PRE_MS)
    e = min(end_ms + PAD_POST_MS, s + MAX_MEDIA_MS)
    return s, e


def summary(db: Path = RECOGNITION_DB) -> dict[str, Any]:
    with _conn(db, ro=True) as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                         "name='movement_moments_v1'").fetchone():
            return {"built": False}
        run = c.execute("SELECT * FROM movement_runs_v1 WHERE version=?",
                        (MOVEMENT_VERSION,)).fetchone()
        kinds = dict(c.execute("SELECT kind, COUNT(*) FROM movement_moments_v1 "
                               "GROUP BY 1").fetchall())
        linked = c.execute("SELECT COUNT(*) FROM movement_moments_v1 WHERE "
                           "related_occurrence_id IS NOT NULL").fetchone()[0]
        peak = c.execute("SELECT MAX(peak_speed), AVG(peak_speed) FROM "
                         "movement_moments_v1 WHERE kind=?",
                         (HIGH_SPEED,)).fetchone()
    return {"built": run is not None, "version": MOVEMENT_VERSION,
            "by_kind": kinds, "linked_to_a_frag": linked,
            "peak_speed_max": round(peak[0] or 0, 1),
            "peak_speed_mean": round(peak[1] or 0, 1),
            **(dict(run) if run is not None else {})}


if __name__ == "__main__":
    print(json.dumps(build(progress=True), indent=2))
