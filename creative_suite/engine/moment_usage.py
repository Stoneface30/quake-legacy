"""Project-scoped no-reuse foundation (directive 26-32).

TECHNICAL PROOF DOES NOT CONSUME A FRAG. Neither does a creative rejection
nor a shortlist. A moment leaves ordinary discovery only when it is
explicitly VALIDATED, ASSIGNED or USED in an accepted project context, and
a RELEASE returns it.

IDENTITY IS THE MOMENT, NOT THE FILE. The corpus stores the same kill under
several filenames with different content hashes (Frags 27622/34632 are one
trinity rocket; 7491/34699 one asylum rocket). A moment is therefore keyed
by the canonical gameplay signature -- arena, server clock, weapon, victim
-- which is the same dedup logic transition_match.event_signature uses.
Two copies of the same event are one row.

WHY NOT generated_clips. It is the proven CAPTURE ledger and carries
``used_in_part`` / ``promotion_status``, so it was inspected first. But it
has one row per captured clip (85 rows) and none for a moment that was only
ever shortlisted, and its identity is per file. This table references it
by canonical signature rather than duplicating it.

The project identifier lives in exactly one place (``DEFAULT_PROJECT``)
and is passed, not scattered.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

DEFAULT_PROJECT = "quake_legacy_main_movie"

AVAILABLE = "AVAILABLE"
SHORTLISTED = "SHORTLISTED"
VALIDATED = "VALIDATED"
ASSIGNED = "ASSIGNED"
USED = "USED"
REJECTED = "REJECTED"
STATES = (AVAILABLE, SHORTLISTED, VALIDATED, ASSIGNED, USED, REJECTED)

# The only states that take a moment out of ordinary discovery.
CONSUMING = frozenset({VALIDATED, ASSIGNED, USED})
# States a RELEASE may return to AVAILABLE. USED is deliberately absent: a
# moment that has been cut into an accepted movie does not silently come
# back; that needs a human, and a different verb.
RELEASABLE = frozenset({VALIDATED, ASSIGNED})


def moment_key(*, map_name: str, server_time_ms: int, weapon: str = "",
               victim_client: int | None = None) -> str:
    """Canonical moment identity. Case-folded arena, no filename anywhere."""
    payload = json.dumps({
        "map": str(map_name or "").lower(),
        "t": int(server_time_ms),
        "weapon": str(weapon or "").upper(),
        "victim": (None if victim_client is None else int(victim_client)),
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MomentState:
    project: str
    moment_key: str
    state: str
    destination: str | None
    note: str
    updated_at: str

    @property
    def consumed(self) -> bool:
        return self.state in CONSUMING

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["consumed"] = self.consumed
        return d


_SCHEMA = """
CREATE TABLE IF NOT EXISTS moment_usage (
    project     TEXT NOT NULL,
    moment_key  TEXT NOT NULL,
    state       TEXT NOT NULL,
    destination TEXT,
    note        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (project, moment_key)
);
CREATE TABLE IF NOT EXISTS moment_usage_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,
    moment_key  TEXT NOT NULL,
    from_state  TEXT,
    to_state    TEXT NOT NULL,
    destination TEXT,
    note        TEXT NOT NULL DEFAULT '',
    at          TEXT NOT NULL
);
"""


def _conn(db_path: Path | str) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get(db_path, key: str, *, project: str = DEFAULT_PROJECT
        ) -> MomentState | None:
    con = _conn(db_path)
    try:
        row = con.execute(
            "SELECT * FROM moment_usage WHERE project=? AND moment_key=?",
            (project, key)).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return MomentState(row["project"], row["moment_key"], row["state"],
                       row["destination"], row["note"], row["updated_at"])


def _set(db_path, key: str, state: str, *, project: str,
         destination: str | None, note: str) -> MomentState:
    if state not in STATES:
        raise ValueError("unknown state: " + str(state))
    con = _conn(db_path)
    try:
        prev = con.execute(
            "SELECT state FROM moment_usage WHERE project=? AND moment_key=?",
            (project, key)).fetchone()
        now = _now()
        con.execute(
            "INSERT INTO moment_usage (project, moment_key, state, destination,"
            " note, updated_at) VALUES (?,?,?,?,?,?)"
            " ON CONFLICT(project, moment_key) DO UPDATE SET state=excluded.state,"
            " destination=excluded.destination, note=excluded.note,"
            " updated_at=excluded.updated_at",
            (project, key, state, destination, note, now))
        con.execute(
            "INSERT INTO moment_usage_log (project, moment_key, from_state,"
            " to_state, destination, note, at) VALUES (?,?,?,?,?,?,?)",
            (project, key, prev["state"] if prev else None, state,
             destination, note, now))
        con.commit()
    finally:
        con.close()
    return MomentState(project, key, state, destination, note, now)


# ── the verbs (directive 28) ────────────────────────────────────────────────

def shortlist(db_path, key: str, *, project: str = DEFAULT_PROJECT,
              note: str = "") -> MomentState:
    """Does NOT consume."""
    cur = get(db_path, key, project=project)
    if cur is not None and cur.consumed:
        return cur          # never demote a reserved moment by shortlisting
    return _set(db_path, key, SHORTLISTED, project=project,
                destination=None, note=note)


def record_technical_proof(db_path, key: str, *, project: str = DEFAULT_PROJECT,
                           note: str = "") -> MomentState | None:
    """Explicitly a no-op on state. Logged so the history shows it happened."""
    cur = get(db_path, key, project=project)
    con = _conn(db_path)
    try:
        con.execute(
            "INSERT INTO moment_usage_log (project, moment_key, from_state,"
            " to_state, destination, note, at) VALUES (?,?,?,?,?,?,?)",
            (project, key, cur.state if cur else None,
             cur.state if cur else AVAILABLE, None,
             "TECHNICAL_PROOF: " + note, _now()))
        con.commit()
    finally:
        con.close()
    return cur


def reject(db_path, key: str, *, project: str = DEFAULT_PROJECT,
           note: str = "") -> MomentState:
    """Creative rejection. Does NOT consume, and does not override a
    reservation -- a rejected proof of a VALIDATED moment leaves it
    VALIDATED."""
    cur = get(db_path, key, project=project)
    if cur is not None and cur.consumed:
        return cur
    return _set(db_path, key, REJECTED, project=project,
                destination=None, note=note)


def validate(db_path, key: str, *, project: str = DEFAULT_PROJECT,
             note: str = "") -> MomentState:
    """Reserves. Requires a human decision upstream; this only records it."""
    return _set(db_path, key, VALIDATED, project=project,
                destination=None, note=note)


def assign(db_path, key: str, *, destination: str,
           project: str = DEFAULT_PROJECT, note: str = "") -> MomentState:
    """Reserves and records where it is going."""
    if not destination:
        raise ValueError("ASSIGNED needs a destination")
    return _set(db_path, key, ASSIGNED, project=project,
                destination=destination, note=note)


def mark_used(db_path, key: str, *, destination: str,
              project: str = DEFAULT_PROJECT, note: str = "") -> MomentState:
    if not destination:
        raise ValueError("USED needs a destination")
    return _set(db_path, key, USED, project=project,
                destination=destination, note=note)


def release(db_path, key: str, *, project: str = DEFAULT_PROJECT,
            note: str = "") -> MomentState:
    """Return a VALIDATED/ASSIGNED reservation to AVAILABLE. USED stays."""
    cur = get(db_path, key, project=project)
    if cur is None:
        raise ValueError("nothing to release")
    if cur.state not in RELEASABLE:
        raise ValueError(f"cannot release a {cur.state} moment")
    return _set(db_path, key, AVAILABLE, project=project,
                destination=None, note=note)


# ── discovery ───────────────────────────────────────────────────────────────

def excluded_keys(db_path, *, project: str = DEFAULT_PROJECT) -> set[str]:
    """Moments ordinary discovery must skip for this project."""
    con = _conn(db_path)
    try:
        return {r["moment_key"] for r in con.execute(
            "SELECT moment_key FROM moment_usage WHERE project=? AND state IN "
            "(?,?,?)", (project, VALIDATED, ASSIGNED, USED))}
    finally:
        con.close()


def filter_available(db_path, candidates: Iterable[dict], *,
                     project: str = DEFAULT_PROJECT) -> list[dict]:
    """Drop consumed moments from a candidate list.

    Candidates need ``map``, ``server_time_ms`` and optionally ``weapon`` /
    ``victim_client``; identity is computed here, so a candidate that is
    the same moment under a different filename is dropped too.
    """
    gone = excluded_keys(db_path, project=project)
    out = []
    for c in candidates:
        k = moment_key(map_name=c.get("map", ""),
                       server_time_ms=int(c["server_time_ms"]),
                       weapon=c.get("weapon", ""),
                       victim_client=c.get("victim_client"))
        if k not in gone:
            out.append(c)
    return out


def history(db_path, key: str, *, project: str = DEFAULT_PROJECT) -> list[dict]:
    con = _conn(db_path)
    try:
        return [dict(r) for r in con.execute(
            "SELECT * FROM moment_usage_log WHERE project=? AND moment_key=?"
            " ORDER BY id", (project, key))]
    finally:
        con.close()
