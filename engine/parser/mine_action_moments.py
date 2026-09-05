"""ACTION_MOMENT: action worth watching that the obituary layer cannot see.

WHY THIS EXISTS. Every reviewable moment in the corpus is anchored to an
obituary. That was the right foundation -- an obituary is a server fact, true
for every player whether or not anyone filmed it -- but it means the archive
can only surface moments where somebody DIED.

Asked for directly: "when I do a high amount of damage in low time or while
doing a big mouse flick or clutch/pixel shot but even when I don't have the
kill -- this could help see rounds where we just see end frag but the action
was video worthy."

WHAT THIS IS NOT.

    not a frag        an ACTION has its own namespace and its own id. It is
                      never merged into the kill queue and never inflates a
                      frag count.
    not damage        Quake Live demos carry no damage figure for another
                      player. A pain event is throttled -- median gap 925 ms,
                      never under 100 ms -- so a pain COUNT is a lower bound
                      on hits and nothing more. Every field is named for what
                      it observed, not for what it implies.
    not authorship    a pain event proves damage, not WHOSE. In a crossfire
                      the victim's pain may be a teammate's rocket, so every
                      moment carries the actor's share of the shots in its
                      window and a confidence derived from it.

NO RE-PARSE. Every stream this reads was already extracted from the raw demo
by the current parser (`semantic-events-v1.0.4`, 34,316,804 rows over all
4,292 distinct demos). Re-reading 14 GB to recompute bytes that have not
changed is cost, not rigour.

Usage:
    python -u engine/parser/mine_action_moments.py --calibrate
    python -u engine/parser/mine_action_moments.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
EPOCH_DB = REPO_ROOT / "creative_suite" / "database" / "mining_epoch.db"

MINER_VERSION = "action-moments-v1.0.0"

# ── the window ──────────────────────────────────────────────────────────────
#
# Three seconds. Long enough to hold a burst of fire and the pain it caused,
# short enough that the previous fight is a separate moment. Calibrated
# against the real distribution rather than chosen: see --calibrate.
WINDOW_MS = 3000

# Pain arriving within this of a kill belongs to that kill's story, not to a
# separate no-kill moment. Slightly wider than the window so a burst that
# ENDS in a frag is recognised as buildup rather than as its own action.
KILL_LINK_MS = 4500

# Thresholds. A moment must clear BOTH, or it is one poke and a stray shot.
MIN_PAIN = 3          # observed pain events on enemies, in-window
MIN_SHOTS = 3         # the recorder's own trigger pulls, in-window

# Above this share of the shots in the window, the pain is attributable with
# reasonable confidence. Below it, someone else was shooting the same people.
#
# CALIBRATED, NOT CHOSEN. Measured over 40 demos / 638 moments: the actor's
# share of all shots fired in the window has p50 0.182 and p90 0.515 -- in a
# five-a-side fight most of the shooting is not yours, so a threshold picked
# by intuition (0.6 was the first guess) would have marked almost nothing
# HIGH and made the field useless. 0.5 is the measured p90: the actor fired
# at least half of everything that went off in those three seconds.
#
# The recorder's own shots are NOT double counted: `fire_weapon` from
# `entity` never carries the recorder (verified: 0 rows with
# entity_num = recorder_client), so the two streams are disjoint.
HIGH_CONF_SHARE = 0.5

CONF_HIGH = "HIGH"
CONF_AMBIGUOUS = "AMBIGUOUS"

# ── classes ─────────────────────────────────────────────────────────────────
TRUE_NO_KILL = "TRUE_NO_KILL_ACTION"     # nothing died; currently invisible
FRAG_BUILDUP = "FRAG_BUILDUP_CONTEXT"    # this is how the frag was set up
PRESSURE_BURST = "PRESSURE_BURST"        # sustained damage on several people
CLUTCH_ACTION = "CLUTCH_ACTION"          # outnumbered while doing it
NEAR_MISS = "PROJECTILE_NEAR_MISS"       # the rocket that should have hit
GRENADE_PRESSURE = "GRENADE_PRESSURE"
MULTI_TARGET = "MULTI_TARGET_PRESSURE"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS action_moments_v1 (
    action_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash    TEXT NOT NULL,
    server_time_ms  INTEGER NOT NULL,
    round           INTEGER,
    map             TEXT,
    actor_client    INTEGER,
    -- OBSERVED counts. Named for what was seen, never for damage.
    observed_pain   INTEGER NOT NULL,
    distinct_victims INTEGER NOT NULL,
    actor_shots     INTEGER NOT NULL,
    other_shots     INTEGER NOT NULL,
    missile_hits    INTEGER NOT NULL DEFAULT 0,
    missile_misses  INTEGER NOT NULL DEFAULT 0,
    window_ms       INTEGER NOT NULL,
    -- DERIVED
    shot_share      REAL,
    confidence      TEXT NOT NULL,
    classes         TEXT NOT NULL DEFAULT '[]',
    ends_in_kill    INTEGER NOT NULL DEFAULT 0,
    linked_occurrence_id INTEGER,
    version         TEXT NOT NULL,
    UNIQUE (content_hash, server_time_ms)
);
CREATE INDEX IF NOT EXISTS ix_am_hash ON action_moments_v1(content_hash, server_time_ms);
CREATE INDEX IF NOT EXISTS ix_am_link ON action_moments_v1(linked_occurrence_id);
CREATE TABLE IF NOT EXISTS action_runs_v1 (
    content_hash TEXT PRIMARY KEY,
    version      TEXT NOT NULL,
    mined_at     TEXT NOT NULL,
    moments      INTEGER NOT NULL DEFAULT 0,
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


def _ro(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=120)
    c.row_factory = sqlite3.Row
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def demo_list(limit: int | None = None) -> list[tuple[str, int]]:
    """(content_hash, recorder_client) for every demo with semantic events."""
    with _ro(RECOG_DB) as c:
        rows = c.execute(
            "SELECT s.content_hash, s.recorder_client FROM scanned_demos s "
            "WHERE EXISTS (SELECT 1 FROM enrichment_runs_v1 e "
            "WHERE e.content_hash = s.content_hash) "
            "ORDER BY s.content_hash").fetchall()
    out = [(r["content_hash"], r["recorder_client"]) for r in rows]
    return out[:limit] if limit else out


def mine_demo(content_hash: str, recorder: int | None) -> dict[str, Any]:
    """Every action moment in one demo. Pure read; returns rows to insert."""
    try:
        with _ro(RECOG_DB) as c:
            teams = {int(r["client"]): r["team"] for r in c.execute(
                "SELECT client, team FROM player_teams_v1 WHERE "
                "content_hash = ?", (content_hash,))}
            my_team = teams.get(int(recorder)) if recorder is not None else None

            shots = [int(r[0]) for r in c.execute(
                "SELECT server_time_ms FROM semantic_events_v1 WHERE "
                "content_hash=? AND type='fire_weapon' AND "
                "source='playerstate' ORDER BY 1", (content_hash,))]
            if not shots:
                return {"content_hash": content_hash, "rows": [], "error": ""}

            all_shots = [int(r[0]) for r in c.execute(
                "SELECT server_time_ms FROM semantic_events_v1 WHERE "
                "content_hash=? AND type='fire_weapon' AND source='entity' "
                "ORDER BY 1", (content_hash,))]

            pains = [(int(r[0]), int(r[1])) for r in c.execute(
                "SELECT server_time_ms, client_num FROM semantic_events_v1 "
                "WHERE content_hash=? AND type='pain' AND client_num IS NOT "
                "NULL ORDER BY 1", (content_hash,))]

            hits = [int(r[0]) for r in c.execute(
                "SELECT server_time_ms FROM semantic_events_v1 WHERE "
                "content_hash=? AND type='missile_hit' ORDER BY 1",
                (content_hash,))]
            misses = [int(r[0]) for r in c.execute(
                "SELECT server_time_ms FROM semantic_events_v1 WHERE "
                "content_hash=? AND type='missile_miss' ORDER BY 1",
                (content_hash,))]

            kills = [(int(r["server_time_ms"]), r["occurrence_id"],
                      r["killer_client"]) for r in c.execute(
                "SELECT server_time_ms, occurrence_id, killer_client FROM "
                "kill_events_v1 WHERE content_hash=? ORDER BY 1",
                (content_hash,))]
            rounds = [(int(r["server_time_ms"]), r["round"], r["map"])
                      for r in c.execute(
                "SELECT server_time_ms, round, map FROM kill_events_v1 "
                "WHERE content_hash=? ORDER BY 1", (content_hash,))]
    except sqlite3.Error as e:
        return {"content_hash": content_hash, "rows": [],
                "error": f"{type(e).__name__}: {e}"}

    # Only pain on players who are NOT the recorder's own side. Absence of
    # team data is not evidence of enmity: without it the victim is skipped
    # rather than assumed to be an enemy.
    def is_enemy(client: int) -> bool:
        if my_team is None:
            return client != recorder
        t = teams.get(client)
        return bool(t) and t != my_team

    enemy_pain = [(t, v) for t, v in pains if is_enemy(v)]
    if not enemy_pain:
        return {"content_hash": content_hash, "rows": [], "error": ""}

    kill_times = [k[0] for k in kills]
    round_times = [r[0] for r in rounds]

    def nearest_round(t: int) -> tuple[int | None, str | None]:
        if not rounds:
            return None, None
        i = min(bisect.bisect_left(round_times, t), len(rounds) - 1)
        return rounds[i][1], rounds[i][2]

    def count_between(seq: list[int], lo: int, hi: int) -> int:
        return bisect.bisect_right(seq, hi) - bisect.bisect_left(seq, lo)

    raw: list[dict[str, Any]] = []
    for i, (t, victim) in enumerate(enemy_pain):
        j = bisect.bisect_left(enemy_pain, (t + WINDOW_MS, -1), lo=i)
        group = enemy_pain[i:j]
        if len(group) < MIN_PAIN:
            continue
        lo, hi = t - 500, t + WINDOW_MS
        mine = count_between(shots, lo, hi)
        if mine < MIN_SHOTS:
            continue
        others = count_between(all_shots, lo, hi)
        total = mine + others
        share = (mine / total) if total else 0.0
        victims = {v for _, v in group}

        ki = bisect.bisect_left(kill_times, t - KILL_LINK_MS)
        near_kill = None
        while ki < len(kills) and kills[ki][0] <= t + KILL_LINK_MS:
            if recorder is None or kills[ki][2] == recorder:
                near_kill = kills[ki]
                break
            ki += 1

        rnd, mp = nearest_round(t)
        raw.append({
            "content_hash": content_hash, "server_time_ms": t,
            "round": rnd, "map": mp, "actor_client": recorder,
            "observed_pain": len(group), "distinct_victims": len(victims),
            "actor_shots": mine, "other_shots": others,
            "missile_hits": count_between(hits, lo, hi),
            "missile_misses": count_between(misses, lo, hi),
            "window_ms": WINDOW_MS, "shot_share": round(share, 3),
            "confidence": (CONF_HIGH if share >= HIGH_CONF_SHARE
                           else CONF_AMBIGUOUS),
            "ends_in_kill": int(near_kill is not None),
            "linked_occurrence_id": near_kill[1] if near_kill else None,
        })

    # Overlapping windows describe one moment. Keep the strongest.
    merged: list[dict[str, Any]] = []
    for r in raw:
        if merged and r["server_time_ms"] - merged[-1]["server_time_ms"] < WINDOW_MS:
            if r["observed_pain"] > merged[-1]["observed_pain"]:
                merged[-1] = r
            continue
        merged.append(r)

    for r in merged:
        cls = []
        if r["ends_in_kill"]:
            cls.append(FRAG_BUILDUP)
        else:
            cls.append(TRUE_NO_KILL)
        if r["observed_pain"] >= 6:
            cls.append(PRESSURE_BURST)
        if r["distinct_victims"] >= 3:
            cls.append(MULTI_TARGET)
        if r["missile_misses"] >= 3 and r["missile_hits"] == 0:
            cls.append(NEAR_MISS)
        r["classes"] = json.dumps(cls)
        r["version"] = MINER_VERSION
    return {"content_hash": content_hash, "rows": merged, "error": ""}


def _write(rows: list[dict[str, Any]], db: Path = EPOCH_DB) -> None:
    if not rows:
        return
    cols = ("content_hash", "server_time_ms", "round", "map", "actor_client",
            "observed_pain", "distinct_victims", "actor_shots", "other_shots",
            "missile_hits", "missile_misses", "window_ms", "shot_share",
            "confidence", "classes", "ends_in_kill", "linked_occurrence_id",
            "version")
    with epoch_conn(db) as c:
        c.executemany(
            f"INSERT OR REPLACE INTO action_moments_v1 ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})",
            [tuple(r[k] for k in cols) for r in rows])


def done_hashes(db: Path = EPOCH_DB) -> set[str]:
    with epoch_conn(db) as c:
        return {r[0] for r in c.execute(
            "SELECT content_hash FROM action_runs_v1 WHERE version = ?",
            (MINER_VERSION,))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--calibrate", action="store_true",
                    help="sample demos and report the real distribution")
    args = ap.parse_args()

    demos = demo_list(args.limit)
    if args.calibrate:
        sample = demos[::max(1, len(demos) // 40)][:40]
        pains, shares = [], []
        for h, rec in sample:
            out = mine_demo(h, rec)
            for r in out["rows"]:
                pains.append(r["observed_pain"])
                shares.append(r["shot_share"])
        pains.sort()
        shares.sort()
        def q(v, p):
            return v[int(len(v) * p)] if v else None
        print(json.dumps({
            "demos_sampled": len(sample), "moments": len(pains),
            "observed_pain": {"p50": q(pains, .5), "p90": q(pains, .9),
                              "p95": q(pains, .95), "p99": q(pains, .99),
                              "max": pains[-1] if pains else None},
            "shot_share": {"p10": q(shares, .1), "p50": q(shares, .5),
                           "p90": q(shares, .9)},
        }, indent=1))
        return 0

    already = done_hashes()
    todo = [(h, r) for h, r in demos if h not in already]
    print(f"{MINER_VERSION}: {len(todo)} demos to mine "
          f"({len(demos) - len(todo)} already done)", flush=True)
    t0 = time.time()
    total, failed = 0, 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(mine_demo, h, r): h for h, r in todo}
        for n, f in enumerate(as_completed(futs), 1):
            out = f.result()
            _write(out["rows"])
            with epoch_conn() as c:
                c.execute(
                    "INSERT OR REPLACE INTO action_runs_v1(content_hash, "
                    "version, mined_at, moments, error) VALUES(?,?,?,?,?)",
                    (out["content_hash"], MINER_VERSION, _now(),
                     len(out["rows"]), out["error"]))
            total += len(out["rows"])
            failed += bool(out["error"])
            if n % 200 == 0:
                print(f"  {n}/{len(todo)} demos, {total} moments, "
                      f"{time.time() - t0:.0f}s", flush=True)
    print(f"done: {total} action moments, {failed} failures, "
          f"{time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
