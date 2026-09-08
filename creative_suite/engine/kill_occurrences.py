"""Canonical kill occurrences: the historical event, not the recording of it.

A kill happened once. Several people may have been recording when it did, and
each of their demos contains a separate observation of that one event. The
corpus has been counting observations and calling them kills, which inflates
every total and would have shown the user the same frag three times and asked
them to judge it as three different moments.

THE EVIDENCE, AND WHY A FINGERPRINT ALONE IS NOT AN ID.

`kill_fingerprint` is (map, server time, killer slot, victim slot, mod). Two
demos of the same match agree on all five because they are watching the same
server. But server times recur across matches and slots are reused, so two
UNRELATED matches can collide by chance, and treating the fingerprint as an
identity would silently merge two different historical kills.

So the fingerprint is a candidate, and the decision needs corroboration. Two
independent signals were measured across all 6,863 duplicated fingerprints:

  PAIR STRENGTH -- how many fingerprints a given pair of demos shares. One
  shared fingerprint is a coincidence; forty is two people recording the same
  match.

  NAME AGREEMENT -- whether the killer and victim NAMES match across the
  observations, which slots alone do not guarantee.

They corroborate almost perfectly:

    pair strength   names agree   names disagree
    1                        64              208
    2-4                   1,972                8
    5-19                  4,068                7
    20+                     536                0

At strength 1 the names mostly DISAGREE -- those are collisions between
different matches, and collapsing them would have destroyed real events. From
strength 2 upward agreement is 99.6% and better. Nothing here was assumed;
the threshold sits where the data separates.

WHAT IS REFUSED. Ambiguity is not resolved by picking the answer that lowers
the count. A group whose evidence is weak keeps its observations as separate
occurrences and is labelled AMBIGUOUS, because inventing a merge is worse
than carrying a duplicate the user can see.

NOTHING IS DELETED. Every observation keeps its row and its provenance. An
occurrence points at the best one to show and remembers the rest.
"""
from __future__ import annotations

import collections
import sqlite3
from pathlib import Path
from typing import Any

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

OCCURRENCE_VERSION = "kill-occurrences-v1.0.0"

# Where the two signals separate. Measured, not chosen: at one shared
# fingerprint the names disagree 208 times out of 272, and from two upward
# they agree 6,576 times out of 6,591.
MIN_PAIR_STRENGTH = 2

SINGLE = "SINGLE_OBSERVATION"          # only one demo saw it; nothing to merge
HIGH = "HIGH_CONFIDENCE_SAME"          # both signals agree
AMBIGUOUS = "AMBIGUOUS"                # signals conflict -- kept apart
DISTINCT = "DISTINCT_COLLISION"        # fingerprint collision, different kills

# How an observation is chosen for review. The actor's own camera first,
# because that is the shot the moment was made in. Then the victim's, which
# at least points at the actor. Then a stable fallback so the choice does not
# wander between runs.
POV_ACTOR = "ACTOR_POV"
POV_VICTIM = "VICTIM_POV"
POV_OTHER = "OTHER_POV"

SCHEMA = """
CREATE TABLE IF NOT EXISTS kill_occurrences_v1(
  occurrence_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  kill_fingerprint  TEXT NOT NULL,
  map               TEXT,
  server_time_ms    INTEGER NOT NULL,
  round             INTEGER,
  killer_client     INTEGER,
  victim_client     INTEGER,
  mod               INTEGER,
  mod_name          TEXT,
  killer_class      TEXT NOT NULL,
  death_cause       TEXT NOT NULL,
  killer_name_norm  TEXT,
  victim_name_norm  TEXT,
  n_observations    INTEGER NOT NULL,
  actor_pov_available INTEGER NOT NULL DEFAULT 0,
  best_observation_id INTEGER,
  best_observation_pov TEXT,
  -- The observation recorded BY THE VICTIM, when one exists. The death queue
  -- wants the dying player's own camera; the frag queue wants the killer's.
  -- One occurrence, two legitimate viewpoints, chosen by what is being asked.
  victim_pov_observation_id INTEGER,
  merge_confidence  TEXT NOT NULL,
  merge_evidence    TEXT);
CREATE INDEX IF NOT EXISTS ix_occ_fp ON kill_occurrences_v1(kill_fingerprint);
CREATE INDEX IF NOT EXISTS ix_occ_killer ON kill_occurrences_v1(killer_name_norm);
CREATE INDEX IF NOT EXISTS ix_occ_class ON kill_occurrences_v1(killer_class);
CREATE INDEX IF NOT EXISTS ix_occ_conf ON kill_occurrences_v1(merge_confidence);
CREATE TABLE IF NOT EXISTS kill_occurrence_runs_v1(
  version TEXT PRIMARY KEY, built_at TEXT NOT NULL, observations INTEGER,
  occurrences INTEGER, multi INTEGER, ambiguous INTEGER, distinct_collisions INTEGER);
"""


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(db, timeout=180)
    c.row_factory = sqlite3.Row
    return c


def pair_strengths(groups: dict[str, list[sqlite3.Row]]
                   ) -> collections.Counter:
    """How many candidate fingerprints each pair of demos shares.

    This is the signal that separates "two people recorded this match" from
    "two unrelated kills happened to line up".
    """
    pair: collections.Counter = collections.Counter()
    for rows in groups.values():
        hs = sorted({r["content_hash"] for r in rows})
        for i in range(len(hs)):
            for j in range(i + 1, len(hs)):
                pair[(hs[i], hs[j])] += 1
    return pair


def classify_group(rows: list[sqlite3.Row],
                   pair: collections.Counter) -> tuple[str, str]:
    """Decide whether these observations are one historical kill.

    Returns (confidence, evidence). Both signals must point the same way for
    a merge; when they disagree the observations stay separate.
    """
    hashes = sorted({r["content_hash"] for r in rows})
    if len(hashes) == 1:
        return SINGLE, "one demo"
    strength = max(pair[(hashes[i], hashes[j])]
                   for i in range(len(hashes))
                   for j in range(i + 1, len(hashes)))
    names = {(r["killer_name_norm"], r["victim_name_norm"]) for r in rows}
    agree = len(names) == 1
    ev = f"pair_strength={strength} names_agree={agree} demos={len(hashes)}"
    if agree and strength >= MIN_PAIR_STRENGTH:
        return HIGH, ev
    if not agree and strength < MIN_PAIR_STRENGTH:
        # Different names AND no corroborating match evidence: two different
        # kills that collided on (map, time, slots, mod). Merging these would
        # delete a real event.
        return DISTINCT, ev
    return AMBIGUOUS, ev


def pick_best(rows: list[sqlite3.Row]) -> tuple[int, str]:
    """Which observation to show a human.

    The actor's own camera is the shot the moment was made in. Failing that
    the victim's camera at least points at the actor. Anything else is a
    bystander. The tie-break is the lowest event id so the choice is stable
    across rebuilds rather than wandering with row order.
    """
    def rank(r: sqlite3.Row) -> tuple[int, int]:
        if r["is_recorder_killer"]:
            return (0, r["kill_event_id"])
        if r["is_recorder_victim"]:
            return (1, r["kill_event_id"])
        return (2, r["kill_event_id"])

    best = min(rows, key=rank)
    pov = (POV_ACTOR if best["is_recorder_killer"]
           else POV_VICTIM if best["is_recorder_victim"] else POV_OTHER)
    return int(best["kill_event_id"]), pov


def pick_victim_pov(rows: list[sqlite3.Row]) -> int | None:
    """The observation recorded by the player who died, if we hold it."""
    cand = [r for r in rows if r["is_recorder_victim"]]
    return min((int(r["kill_event_id"]) for r in cand), default=None)


def build(db: Path = RECOGNITION_DB, progress: bool = False) -> dict[str, Any]:
    """Build the occurrence layer from the observations. Idempotent."""
    con = _conn(db)
    con.executescript(SCHEMA)
    # The occurrence table is fully derived, so a schema change is a rebuild
    # rather than a migration -- but it must be an explicit one. A silent
    # CREATE IF NOT EXISTS against an older shape leaves the new column
    # missing and fails at insert time.
    occ_cols = {r[1] for r in con.execute(
        "PRAGMA table_info(kill_occurrences_v1)")}
    if occ_cols and "victim_pov_observation_id" not in occ_cols:
        con.executescript("DROP TABLE kill_occurrences_v1;")
        con.executescript(SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(kill_events_v1)")}
    if "occurrence_id" not in cols:
        con.execute("ALTER TABLE kill_events_v1 ADD COLUMN occurrence_id INTEGER")
    if "is_best_observation" not in cols:
        con.execute("ALTER TABLE kill_events_v1 ADD COLUMN "
                    "is_best_observation INTEGER NOT NULL DEFAULT 0")
    con.execute("CREATE INDEX IF NOT EXISTS ix_kill_occ "
                "ON kill_events_v1(occurrence_id)")

    rows = con.execute(
        "SELECT kill_event_id, content_hash, kill_fingerprint, map, "
        "server_time_ms, round, killer_client, victim_client, mod, mod_name, "
        "killer_class, death_cause, killer_name_norm, victim_name_norm, "
        "is_recorder_killer, is_recorder_victim FROM kill_events_v1").fetchall()
    groups: dict[str, list[sqlite3.Row]] = collections.defaultdict(list)
    for r in rows:
        groups[r["kill_fingerprint"]].append(r)
    if progress:
        print(f"  {len(rows):,} observations, {len(groups):,} fingerprints",
              flush=True)
    multi = {fp: v for fp, v in groups.items()
             if len({r["content_hash"] for r in v}) > 1}
    pair = pair_strengths(multi)
    if progress:
        print(f"  {len(multi):,} multi-demo fingerprints, "
              f"{len(pair):,} sharing demo pairs", flush=True)

    occ_rows, links = [], []
    stats = collections.Counter()
    for fp, v in groups.items():
        conf, ev = classify_group(v, pair)
        stats[conf] += 1
        # A merge produces ONE occurrence. Anything else keeps the
        # observations apart -- one occurrence each, so nothing is lost and
        # nothing is invented.
        parts = [v] if conf in (SINGLE, HIGH) else [[r] for r in v]
        for part in parts:
            best_id, pov = pick_best(part)
            victim_id = pick_victim_pov(part)
            head = part[0]
            occ_rows.append((
                fp, head["map"], head["server_time_ms"], head["round"],
                head["killer_client"], head["victim_client"], head["mod"],
                head["mod_name"], head["killer_class"], head["death_cause"],
                head["killer_name_norm"], head["victim_name_norm"],
                len(part),
                1 if any(r["is_recorder_killer"] for r in part) else 0,
                best_id, pov, victim_id, conf, ev))
            links.append((best_id, [int(r["kill_event_id"]) for r in part]))

    with con:
        con.execute("DELETE FROM kill_occurrences_v1")
        con.execute("UPDATE kill_events_v1 SET occurrence_id=NULL, "
                    "is_best_observation=0")
        con.executemany(
            "INSERT INTO kill_occurrences_v1(kill_fingerprint, map, "
            "server_time_ms, round, killer_client, victim_client, mod, "
            "mod_name, killer_class, death_cause, killer_name_norm, "
            "victim_name_norm, n_observations, actor_pov_available, "
            "best_observation_id, best_observation_pov, "
            "victim_pov_observation_id, merge_confidence, "
            "merge_evidence) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            occ_rows)
        # Link observations back. rowid order matches insertion order.
        first = con.execute("SELECT MIN(occurrence_id) FROM kill_occurrences_v1"
                            ).fetchone()[0]
        upd = []
        for i, (best_id, members) in enumerate(links):
            oid = first + i
            for m in members:
                upd.append((oid, 1 if m == best_id else 0, m))
        con.executemany("UPDATE kill_events_v1 SET occurrence_id=?, "
                        "is_best_observation=? WHERE kill_event_id=?", upd)
        con.execute(
            "INSERT OR REPLACE INTO kill_occurrence_runs_v1 VALUES "
            "(?,datetime('now'),?,?,?,?,?)",
            (OCCURRENCE_VERSION, len(rows), len(occ_rows),
             sum(1 for o in occ_rows if o[12] > 1), stats[AMBIGUOUS],
             stats[DISTINCT]))
    out = {"observations": len(rows), "occurrences": len(occ_rows),
           "multi_observation": sum(1 for o in occ_rows if o[12] > 1),
           "by_confidence": dict(stats),
           "collapsed": len(rows) - len(occ_rows)}
    con.close()
    return out


def summary(db: Path = RECOGNITION_DB) -> dict[str, Any]:
    with _conn(db) as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                         "name='kill_occurrences_v1'").fetchone():
            return {"built": False}
        row = c.execute("SELECT * FROM kill_occurrence_runs_v1 WHERE version=?",
                        (OCCURRENCE_VERSION,)).fetchone()
        conf = dict(c.execute("SELECT merge_confidence, COUNT(*) FROM "
                              "kill_occurrences_v1 GROUP BY 1").fetchall())
        pov = dict(c.execute("SELECT best_observation_pov, COUNT(*) FROM "
                             "kill_occurrences_v1 GROUP BY 1").fetchall())
    return {"built": row is not None, "version": OCCURRENCE_VERSION,
            "by_confidence": conf, "best_observation_pov": pov,
            **(dict(row) if row is not None else {})}


if __name__ == "__main__":
    import json
    print(json.dumps(build(progress=True), indent=2))
