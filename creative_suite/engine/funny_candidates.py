"""Unusual moments, found by machine and judged by a person.

A DISCOVERY LABEL, NOT A QUALITY CLASS. "Funny/weird" says a moment has an
unusual shape. It says nothing about how much it matters. A rocket that
passes a hand's width from someone's head is odd AND may deserve one of the
largest treatments in the film, so nothing here downgrades anything: the five
buttons decide, and this only decides what gets looked at.

TAGS, NOT NEW ITEMS. Every candidate here is an occurrence that already
exists -- a frag, a death, a telefrag. Attaching a signal to it must not
create a second review item, or a moment with five interesting properties
becomes five things to judge and the same footage is watched five times. So
this writes tags keyed BY OCCURRENCE and surfaces them as a FILTER over the
queues that already exist.

CHAT IS WEAK EVIDENCE. People type "lol" for many reasons and say nothing at
all through the best moments of a match. A reaction nearby raises interest;
it never establishes that something was funny, and no candidate exists on
chat alone.

WHAT IS REFUSED. A category is not populated because it appears in a
specification. Every signal below is a query over evidence the corpus
actually holds, and one that returns nothing is reported as returning
nothing.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

FUNNY_VERSION = "funny-candidates-v1.0.0"

# How close a kill and the killer's own death must be to read as one comic
# beat rather than two things that happened in the same minute.
HERO_THEN_DEATH_MS = 3000
INSTANT_DEATH_MS = 1000
TRADE_MS = 400

# Chat window either side. Wide enough for someone to react, narrow enough
# that a joke about the previous round does not attach itself here.
CHAT_PRE_MS = 6000
CHAT_POST_MS = 10000
REACTION = re.compile(
    r"(?<![a-z])(lol|lmao|lmfao|haha+|hehe|wtf|omg|omfg|wow|nice|ns|gg|"
    r"noob|rofl|xd|jesus|holy)(?![a-z])", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS funny_candidates_v1(
  occurrence_id INTEGER PRIMARY KEY,
  signals       TEXT NOT NULL,
  strength      REAL NOT NULL,
  chat_hits     INTEGER NOT NULL DEFAULT 0,
  detail        TEXT NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS ix_fc_strength ON funny_candidates_v1(strength);
CREATE TABLE IF NOT EXISTS funny_runs_v1(
  version TEXT PRIMARY KEY, built_at TEXT NOT NULL, candidates INTEGER,
  by_signal TEXT NOT NULL);
"""

# Each signal: a name, a weight, and the evidence that produces it. Weights
# ORDER the candidate list. They never remove anything, and they are not a
# claim about how good a moment is.
GAUNTLET = "GAUNTLET_KILL"
TELEFRAG = "TELEFRAG"
ENVIRONMENTAL = "ENVIRONMENTAL_DEATH"
SELF_KILL = "SELF_DAMAGE_DEATH"
HERO_THEN_DEATH = "HERO_THEN_DEATH"
INSTANT_TRADE = "INSTANT_TRADE"
KILL_THEN_DEATH = "KILL_THEN_DEATH_FAST"
CHAT_REACTION = "CHAT_REACTION_NEARBY"

WEIGHTS = {
    GAUNTLET: 3.0,          # the humiliation weapon; rare and always notable
    TELEFRAG: 2.5,
    HERO_THEN_DEATH: 2.0,
    INSTANT_TRADE: 2.0,
    KILL_THEN_DEATH: 1.5,
    SELF_KILL: 1.5,
    ENVIRONMENTAL: 1.0,
    CHAT_REACTION: 0.75,    # supporting only, and deliberately the smallest
}


def _conn(db: Path = RECOGNITION_DB, ro: bool = False) -> sqlite3.Connection:
    uri = f"file:{db}?mode=ro" if ro else str(db)
    c = sqlite3.connect(uri, uri=ro, timeout=180)
    c.row_factory = sqlite3.Row
    return c


def build(db: Path = RECOGNITION_DB, progress: bool = False) -> dict[str, Any]:
    """Find candidates. Idempotent; replaces the previous build."""
    con = _conn(db)
    con.executescript(SCHEMA)
    sig: dict[int, set[str]] = {}
    detail: dict[int, dict[str, Any]] = {}

    def add(oid: int, name: str, **kw) -> None:
        sig.setdefault(int(oid), set()).add(name)
        if kw:
            detail.setdefault(int(oid), {}).update(kw)

    with _conn(db, ro=True) as c:
        for r in c.execute("SELECT occurrence_id FROM kill_occurrences_v1 "
                           "WHERE mod_name='GAUNTLET'"):
            add(r["occurrence_id"], GAUNTLET)
        for r in c.execute("SELECT occurrence_id FROM kill_occurrences_v1 "
                           "WHERE death_cause='TELEFRAG'"):
            add(r["occurrence_id"], TELEFRAG)
        for r in c.execute("SELECT occurrence_id FROM kill_occurrences_v1 "
                           "WHERE death_cause='ENVIRONMENT'"):
            add(r["occurrence_id"], ENVIRONMENTAL)
        for r in c.execute("SELECT occurrence_id FROM kill_occurrences_v1 "
                           "WHERE death_cause='SUICIDE'"):
            add(r["occurrence_id"], SELF_KILL)

        # A kill, then the killer dying almost immediately. Read off the
        # occurrence stream per demo rather than guessed at.
        rows = c.execute(
            "SELECT o.occurrence_id, k.content_hash, o.server_time_ms t, "
            "o.killer_name_norm ka, o.victim_name_norm va "
            "FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "WHERE o.killer_class='PLAYER' "
            "ORDER BY k.content_hash, o.server_time_ms").fetchall()
        by_demo: dict[str, list] = {}
        for r in rows:
            by_demo.setdefault(r["content_hash"], []).append(r)
        for seq in by_demo.values():
            for i, a in enumerate(seq):
                for b in seq[i + 1:]:
                    gap = b["t"] - a["t"]
                    if gap > HERO_THEN_DEATH_MS:
                        break
                    if b["va"] and b["va"] == a["ka"]:
                        # the killer is now the victim
                        if gap <= INSTANT_DEATH_MS:
                            add(a["occurrence_id"], KILL_THEN_DEATH,
                                death_gap_ms=gap)
                        else:
                            add(a["occurrence_id"], HERO_THEN_DEATH,
                                death_gap_ms=gap)
                        if gap <= TRADE_MS and b["ka"] == a["va"]:
                            # they killed each other, near-simultaneously
                            add(a["occurrence_id"], INSTANT_TRADE,
                                trade_gap_ms=gap)
                        break

        if progress:
            print(f"  {len(sig):,} occurrences carry a structural signal",
                  flush=True)

        # Chat, last, and only onto candidates that already exist. Chat alone
        # never creates one.
        if sig:
            ids = list(sig)
            marks = ",".join("?" * min(len(ids), 900))
            times = {}
            for chunk in (ids[i:i + 900] for i in range(0, len(ids), 900)):
                m = ",".join("?" * len(chunk))
                for r in c.execute(
                        f"SELECT o.occurrence_id, k.content_hash, "
                        f"o.server_time_ms t FROM kill_occurrences_v1 o "
                        f"JOIN kill_events_v1 k ON k.kill_event_id = "
                        f"o.best_observation_id WHERE o.occurrence_id IN ({m})",
                        chunk):
                    times[int(r["occurrence_id"])] = (r["content_hash"], r["t"])
            del marks
            chat: dict[str, list[tuple[int, str]]] = {}
            for r in c.execute("SELECT content_hash, server_time_ms, text "
                               "FROM server_text_v1 WHERE kind='chat'"):
                chat.setdefault(r["content_hash"], []).append(
                    (int(r["server_time_ms"]), r["text"] or ""))
            for oid, (ch, t) in times.items():
                hits = sum(1 for ts, tx in chat.get(ch, ())
                           if t - CHAT_PRE_MS <= ts <= t + CHAT_POST_MS
                           and REACTION.search(tx))
                if hits:
                    add(oid, CHAT_REACTION, chat_hits=hits)

    counts: dict[str, int] = {}
    with con:
        con.execute("DELETE FROM funny_candidates_v1")
        for oid, names in sig.items():
            for n in names:
                counts[n] = counts.get(n, 0) + 1
            d = detail.get(oid, {})
            strength = sum(WEIGHTS.get(n, 0.0) for n in names)
            con.execute(
                "INSERT INTO funny_candidates_v1(occurrence_id, signals, "
                "strength, chat_hits, detail) VALUES (?,?,?,?,?)",
                (oid, json.dumps(sorted(names)), round(strength, 2),
                 int(d.get("chat_hits", 0)), json.dumps(d)))
        con.execute("INSERT OR REPLACE INTO funny_runs_v1 VALUES "
                    "(?,datetime('now'),?,?)",
                    (FUNNY_VERSION, len(sig), json.dumps(counts)))
    con.close()
    return {"candidates": len(sig), "by_signal": counts,
            "version": FUNNY_VERSION}


def summary(db: Path = RECOGNITION_DB) -> dict[str, Any]:
    with _conn(db, ro=True) as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                         "name='funny_candidates_v1'").fetchone():
            return {"built": False}
        r = c.execute("SELECT * FROM funny_runs_v1 WHERE version=?",
                      (FUNNY_VERSION,)).fetchone()
        top = c.execute(
            "SELECT f.occurrence_id, f.signals, f.strength, f.chat_hits, "
            "o.mod_name, o.map, o.death_cause FROM funny_candidates_v1 f "
            "JOIN kill_occurrences_v1 o ON o.occurrence_id = f.occurrence_id "
            "ORDER BY f.strength DESC, f.chat_hits DESC LIMIT 10").fetchall()
    return {"built": r is not None, "version": FUNNY_VERSION,
            "candidates": r["candidates"] if r else 0,
            "by_signal": json.loads(r["by_signal"]) if r else {},
            "top": [dict(x) for x in top],
            "note": ("a discovery label, not a quality class: the five "
                     "buttons decide what a moment is worth")}


if __name__ == "__main__":
    print(json.dumps(build(progress=True), indent=2))
