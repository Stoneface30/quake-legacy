"""Is this demo a whole recording, or a slice cut out of another one?

WHY EXACT HASHING IS NOT ENOUGH. The corpus inventory found 2,153 files that
are byte-identical re-saves, and concluded the archive was complete. That is
true and it is not the whole question: a demo can also be a SUBSEQUENCE of
another -- a hand-cut frag extract, a partial replay, a segment saved out of
a longer match. Its bytes differ, so SHA-256 says it is a new demo, and it
then competes to be the source for a round it only contains a sliver of.

A FRAGMENT CANNOT DEFINE A ROUND. It has no round start, no round end and
often one kill. Letting it be the authority is how a round gets rendered
from four seconds of footage.

HOW CONTAINMENT IS DETECTED. Not by filename -- `Demo (417).dm_73` says
nothing -- and not by comparing bytes, which differ by construction. By the
events themselves: an obituary carries (server time, killer slot, victim
slot, means of death), and that tuple is a fingerprint of a moment in a
specific match. If every obituary of demo B appears in demo A at the same
server times, B is a window onto the same match A recorded.

Server time is the shared clock: both demos were watching the same server,
so the same kill carries the same timestamp in both. That is what makes the
comparison possible at all.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# DATA, not code: in a worktree these differ, and opening a database
# under the wrong one silently creates an empty file. See
# engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
EPOCH_DB = REPO_ROOT / "creative_suite" / "database" / "mining_epoch.db"

LINEAGE_VERSION = "demo-lineage-v1.0.0"

# Classes. A demo is described by what it CONTAINS, never by its name.
FULL_RECORDING = "FULL_RECORDING"      # nothing else contains it
FRAGMENT_OF = "FRAGMENT_OF"            # every event of it lives inside another
UNIQUE_FRAGMENT = "UNIQUE_FRAGMENT"    # short, but no container found
UNKNOWN = "UNKNOWN"                    # too little signal to say

# Below this a demo cannot carry a round's structure whatever it contains.
SHORT_KILLS = 6

# How much of a demo's event set must be present in another for containment.
# Not 100%: the shorter demo can hold an obituary the longer one missed
# through packet loss, and demanding perfection would call a real fragment
# independent.
CONTAINMENT = 0.95

_SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_lineage_v1 (
    content_hash   TEXT PRIMARY KEY,
    lineage        TEXT NOT NULL,
    container_hash TEXT,
    kills          INTEGER NOT NULL,
    rounds         INTEGER NOT NULL,
    span_ms        INTEGER NOT NULL,
    covered_frac   REAL,
    round_starts   INTEGER NOT NULL DEFAULT 0,
    version        TEXT NOT NULL,
    computed_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_dl_lineage ON demo_lineage_v1(lineage);
CREATE INDEX IF NOT EXISTS ix_dl_container ON demo_lineage_v1(container_hash);
"""


@dataclass(frozen=True)
class Lineage:
    content_hash: str
    lineage: str
    container_hash: str | None
    kills: int
    rounds: int
    span_ms: int
    covered_frac: float | None
    round_starts: int

    @property
    def can_define_a_round(self) -> bool:
        """May this demo be the authority for a round's bounds and media?

        A fragment cannot: it has no round start, no round end, and usually
        one kill. It remains a perfectly good OBSERVATION of the moments it
        does contain.
        """
        return self.lineage in (FULL_RECORDING, UNIQUE_FRAGMENT) and \
            self.kills >= SHORT_KILLS

    def to_dict(self) -> dict[str, Any]:
        d = {"lineage": self.lineage, "kills": self.kills,
             "rounds": self.rounds, "span_ms": self.span_ms,
             "covered_frac": self.covered_frac,
             "round_starts": self.round_starts,
             "can_define_a_round": self.can_define_a_round}
        return d


def conn(db: Path = EPOCH_DB) -> sqlite3.Connection:
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


def event_sets(db: Path = RECOG_DB) -> dict[str, set[tuple]]:
    """The obituary fingerprint of every demo.

    (server time, killer slot, victim slot, mod) identifies a moment in a
    match. Map is carried separately: two demos of different maps can never
    contain one another and are separated before any comparison.
    """
    out: dict[str, set[tuple]] = defaultdict(set)
    with _ro(db) as c:
        for r in c.execute(
                "SELECT content_hash, server_time_ms, killer_client, "
                "victim_client, mod FROM kill_events_v1"):
            out[r["content_hash"]].add(
                (int(r["server_time_ms"]), r["killer_client"],
                 r["victim_client"], r["mod"]))
    return dict(out)


def demo_facts(db: Path = RECOG_DB) -> dict[str, dict[str, Any]]:
    with _ro(db) as c:
        rows = c.execute(
            "SELECT content_hash, COUNT(*) kills, "
            "COUNT(DISTINCT round) rounds, MIN(server_time_ms) a, "
            "MAX(server_time_ms) b, MIN(map) map FROM kill_events_v1 "
            "GROUP BY content_hash").fetchall()
        starts = {r["content_hash"]: r["n"] for r in c.execute(
            "SELECT content_hash, COUNT(*) n FROM round_state_v1 "
            "WHERE cs=661 GROUP BY content_hash")}
    return {r["content_hash"]: {
        "kills": int(r["kills"]), "rounds": int(r["rounds"]),
        "span_ms": int(r["b"]) - int(r["a"]), "map": r["map"],
        "round_starts": int(starts.get(r["content_hash"], 0))}
        for r in rows}


def classify(db: Path = RECOG_DB) -> list[Lineage]:
    """Every demo, described by what it contains.

    Comparison is bucketed by map and by overlapping time, so a demo is only
    ever compared with the handful of others that could possibly contain it
    -- not with all 4,291 of them.
    """
    events = event_sets(db)
    facts = demo_facts(db)

    by_map: dict[str, list[str]] = defaultdict(list)
    for h, f in facts.items():
        by_map[f["map"] or ""].append(h)

    out: list[Lineage] = []
    for h, f in facts.items():
        ev = events.get(h, set())
        if not ev:
            out.append(Lineage(h, UNKNOWN, None, 0, 0, 0, None,
                               f["round_starts"]))
            continue
        best: tuple[str, float] | None = None
        for other in by_map[f["map"] or ""]:
            if other == h:
                continue
            oev = events.get(other, set())
            # Only a STRICTLY larger recording can contain this one. Equal
            # sets are the same match recorded twice, not containment.
            if len(oev) <= len(ev):
                continue
            covered = len(ev & oev) / len(ev)
            if covered >= CONTAINMENT and (best is None or covered > best[1]):
                best = (other, covered)
        if best is not None:
            out.append(Lineage(h, FRAGMENT_OF, best[0], f["kills"],
                               f["rounds"], f["span_ms"], round(best[1], 4),
                               f["round_starts"]))
        elif f["kills"] < SHORT_KILLS:
            out.append(Lineage(h, UNIQUE_FRAGMENT, None, f["kills"],
                               f["rounds"], f["span_ms"], None,
                               f["round_starts"]))
        else:
            out.append(Lineage(h, FULL_RECORDING, None, f["kills"],
                               f["rounds"], f["span_ms"], None,
                               f["round_starts"]))
    return out


def build(db: Path = RECOG_DB, epoch: Path = EPOCH_DB) -> dict[str, Any]:
    rows = classify(db)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn(epoch) as c:
        c.execute("DELETE FROM demo_lineage_v1")
        c.executemany(
            "INSERT INTO demo_lineage_v1(content_hash, lineage, "
            "container_hash, kills, rounds, span_ms, covered_frac, "
            "round_starts, version, computed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            [(r.content_hash, r.lineage, r.container_hash, r.kills, r.rounds,
              r.span_ms, r.covered_frac, r.round_starts, LINEAGE_VERSION, now)
             for r in rows])
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.lineage] = counts.get(r.lineage, 0) + 1
    return {"version": LINEAGE_VERSION, "demos": len(rows),
            "by_lineage": counts,
            "cannot_define_a_round": sum(1 for r in rows
                                         if not r.can_define_a_round)}


def lineage_of(content_hash: str, epoch: Path = EPOCH_DB) -> Lineage | None:
    with conn(epoch) as c:
        r = c.execute("SELECT * FROM demo_lineage_v1 WHERE content_hash=?",
                      (content_hash,)).fetchone()
    if r is None:
        return None
    return Lineage(r["content_hash"], r["lineage"], r["container_hash"],
                   r["kills"], r["rounds"], r["span_ms"], r["covered_frac"],
                   r["round_starts"])


# ── choosing which recording speaks for a round ─────────────────────────────

def better_source_for(occurrence_id: int, recog: Path = RECOG_DB,
                      epoch: Path = EPOCH_DB) -> str | None:
    """The fullest demo that observed this kill, if a better one exists.

    THE CANONICAL EVENT DOES NOT MOVE. This changes which recording is read
    for the round around it, never the occurrence id -- so every human
    verdict, tag and note stays attached to exactly the moment it was made
    about, and simply gets a better camera and real round boundaries.
    """
    with _ro(recog) as c:
        obs = [r["content_hash"] for r in c.execute(
            "SELECT content_hash FROM kill_events_v1 WHERE occurrence_id=?",
            (int(occurrence_id),))]
        best_now = c.execute(
            "SELECT k.content_hash FROM kill_occurrences_v1 o JOIN "
            "kill_events_v1 k ON k.kill_event_id=o.best_observation_id "
            "WHERE o.occurrence_id=?", (int(occurrence_id),)).fetchone()
    if not obs or best_now is None:
        return None
    current = best_now["content_hash"]
    with conn(epoch) as c:
        qs = ",".join("?" * len(obs))
        lin = {r["content_hash"]: dict(r) for r in c.execute(
            f"SELECT * FROM demo_lineage_v1 WHERE content_hash IN ({qs})",
            obs)}
    cur = lin.get(current)
    if cur is None or cur["lineage"] != FRAGMENT_OF:
        return None            # already the best kind of source
    # Prefer a full recording; among those, the one that saw most of the
    # match, because that is the one most likely to hold the round's edges.
    cands = [d for h, d in lin.items()
             if h != current and d["lineage"] != FRAGMENT_OF]
    if not cands:
        return None
    best = max(cands, key=lambda d: (d["round_starts"], d["kills"]))
    return best["content_hash"]


# ── the canonical source ladder ─────────────────────────────────────────────

COMPLETE_SOURCE = "COMPLETE_SOURCE"      # a full recording, and it saw the kill
BEST_POV = "BEST_POV"                    # full recording, recorded by the user
ONLY_FRAGMENT = "ONLY_FRAGMENT"          # nothing fuller exists; use it anyway
UNCHANGED = "UNCHANGED"                  # the chosen observation was already best


@dataclass(frozen=True)
class Source:
    content_hash: str
    reason: str
    changed: bool


def canonical_source_for(occurrence_id: int, recog: Path = RECOG_DB,
                         epoch: Path = EPOCH_DB,
                         prefer_client: int | None = None) -> Source | None:
    """Which recording should speak for the round around this kill?

    THE LADDER, in order:

        1. a COMPLETE recording that also has the round's own start markers
        2. among equals, the one recorded from the user's point of view
        3. a fragment, but only when nothing fuller observed the moment

    Step 2 matters because two full demos of the same match are not equally
    useful: the one the user recorded is the one whose camera is theirs, and
    a round watched from someone else's eyes is a different clip even when
    it is the same round.

    A FRAGMENT IS NEVER DELETED and never disqualified as evidence. It stays
    a perfectly good observation of the moment it holds; it is simply not
    asked to describe boundaries it cannot see.

    THE OCCURRENCE ID DOES NOT MOVE. This picks a camera, not a moment, so
    every human verdict, tag and note stays attached to exactly what it was
    written about.
    """
    with _ro(recog) as c:
        obs = [dict(r) for r in c.execute(
            "SELECT content_hash, recorder_client, is_recorder_killer "
            "FROM kill_events_v1 WHERE occurrence_id=?",
            (int(occurrence_id),))]
        best_now = c.execute(
            "SELECT k.content_hash FROM kill_occurrences_v1 o JOIN "
            "kill_events_v1 k ON k.kill_event_id=o.best_observation_id "
            "WHERE o.occurrence_id=?", (int(occurrence_id),)).fetchone()
    if not obs or best_now is None:
        return None
    current = best_now["content_hash"]

    hashes = sorted({o["content_hash"] for o in obs})
    with conn(epoch) as c:
        qs = ",".join("?" * len(hashes))
        lin = {r["content_hash"]: dict(r) for r in c.execute(
            "SELECT * FROM demo_lineage_v1 WHERE content_hash IN (" + qs + ")",
            hashes)}
    if not lin:
        return Source(current, UNCHANGED, False)

    def usable(h: str) -> bool:
        d = lin.get(h)
        if d is None:
            return False
        return d["lineage"] in (FULL_RECORDING, UNIQUE_FRAGMENT) and \
            d["kills"] >= SHORT_KILLS

    pov = {o["content_hash"]: bool(o["is_recorder_killer"]) for o in obs}
    full = [h for h in hashes if usable(h)]
    if not full:
        # Every observation is a fragment. Keep the one already chosen: a
        # different fragment is not an improvement, only a different sliver.
        return Source(current, ONLY_FRAGMENT, False)

    # Rank: the user's own point of view first, then the demo that saw most
    # of the match (round markers, then kills), then the hash for stability.
    def rank(h: str) -> tuple:
        d = lin[h]
        return (0 if pov.get(h) else 1, -int(d["round_starts"]),
                -int(d["kills"]), h)

    best = min(full, key=rank)
    reason = BEST_POV if pov.get(best) else COMPLETE_SOURCE
    if best == current:
        return Source(current, UNCHANGED, False)
    return Source(best, reason, True)


def demo_name_of(content_hash: str, recog: Path = RECOG_DB) -> str | None:
    """Local filename for a hash. Local data only -- never persisted into a
    tracked file, never printed into a public artefact."""
    with _ro(recog) as c:
        r = c.execute("SELECT demo_name FROM scanned_demos WHERE "
                      "content_hash=?", (content_hash,)).fetchone()
    return r["demo_name"] if r else None
