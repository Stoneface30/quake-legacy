"""Moments worth having that nobody actually filmed.

THE PROBLEM THIS EXISTS FOR. An obituary is a server fact: the kill happened,
and the archive knows who, when, where and with what. Whether any CAMERA saw
it is a completely separate question. Roughly three quarters of the corpus is
`OTHER_POV` -- somebody else's demo, pointed somewhere else -- and a
significant part of the rest shows the actor's own view of a wall while the
interesting thing happened off screen.

Those moments are not bad frags. They are unfilmed ones. Deleting them would
be wrong (they are real history), tagging them ALT_POV would be wrong (there
is no better camera to go and find), and leaving them in the queue means
judging a clip nobody can see.

So the reviewer gets a third answer: SEND TO WORKSHOP. It says "this is
worth having and the footage does not exist -- rebuild it." The workshop is
the synthetic demo writer, developed separately; this module only holds the
request and hands it over. Nothing here writes a demo, and nothing here
decides whether a reconstruction is possible.

WHAT IT IS NOT.

    not a verdict     T1-T5 judges a clip. This says there is no clip.
    not a deletion    a deletion hides a moment; this promotes one.
    not direction     the free-text reason is a hint for the workshop, not
                      an instruction to the film.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# DATA, not code: in a worktree these differ, and opening a database
# under the wrong one silently creates an empty file. See
# engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
EDITORIAL_DB = REPO_ROOT / "creative_suite" / "database" / "editorial.db"

REQUEST_VERSION = "reconstruction-v1"

# Why the footage is missing. The workshop needs this: a moment nobody
# recorded and a moment recorded from behind a wall are different rebuilds.
NO_CAMERA = "NO_CAMERA"          # no demo covers it at all
OFF_SCREEN = "OFF_SCREEN"        # filmed, but the action is not in frame
BAD_ANGLE = "BAD_ANGLE"          # visible, but from a useless position
OBSCURED = "OBSCURED"            # geometry, smoke, or effects in the way
UNSPECIFIED = "UNSPECIFIED"      # the reviewer did not say, and need not

REASONS = (NO_CAMERA, OFF_SCREEN, BAD_ANGLE, OBSCURED, UNSPECIFIED)

REASON_LABEL = {
    NO_CAMERA: "nobody filmed it",
    OFF_SCREEN: "filmed, but the action is off screen",
    BAD_ANGLE: "visible from a useless angle",
    OBSCURED: "something is in the way",
    UNSPECIFIED: "not seen -- reason not given",
}

QUEUED = "QUEUED"
ACCEPTED = "ACCEPTED"        # the workshop has taken it
BUILT = "BUILT"
REFUSED = "REFUSED"          # the workshop cannot rebuild it
STATES = (QUEUED, ACCEPTED, BUILT, REFUSED)

HUMAN_USER = "HUMAN_USER"
IMPORTED_LEGACY_HUMAN = "IMPORTED_LEGACY_HUMAN"
TEST = "TEST"
HUMAN_PROVENANCE = (HUMAN_USER, IMPORTED_LEGACY_HUMAN)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reconstruction_requests (
    occurrence_id INTEGER PRIMARY KEY,
    item_id       TEXT NOT NULL,
    reason        TEXT NOT NULL DEFAULT 'UNSPECIFIED',
    note          TEXT NOT NULL DEFAULT '',
    state         TEXT NOT NULL DEFAULT 'QUEUED',
    provenance    TEXT NOT NULL DEFAULT 'HUMAN_USER',
    requested_at  TEXT NOT NULL,
    version       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_rq_state ON reconstruction_requests(state);
"""


class UnknownReason(ValueError):
    """A reason outside the vocabulary the workshop understands."""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request(occurrence_id: int, item_id: str = "", reason: str = UNSPECIFIED,
            note: str = "", provenance: str = HUMAN_USER) -> dict[str, Any]:
    """Send one moment to the workshop. Idempotent; re-sending updates it."""
    r = str(reason or UNSPECIFIED).strip().upper()
    if r not in REASONS:
        raise UnknownReason(f"unknown reason {r!r}; expected one of "
                            f"{', '.join(REASONS)}")
    oid = int(occurrence_id)
    now = _now()
    with conn() as c:
        c.execute(
            "INSERT INTO reconstruction_requests(occurrence_id, item_id, "
            "reason, note, state, provenance, requested_at, version) "
            "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(occurrence_id) DO UPDATE SET "
            "reason=excluded.reason, note=excluded.note, "
            "requested_at=excluded.requested_at, "
            "provenance=excluded.provenance",
            (oid, item_id or "", r, note or "", QUEUED, provenance, now,
             REQUEST_VERSION))
    return {"occurrence_id": oid, "item_id": item_id, "reason": r,
            "reason_label": REASON_LABEL[r], "state": QUEUED,
            "requested_at": now}


def withdraw(occurrence_id: int) -> bool:
    with conn() as c:
        cur = c.execute("DELETE FROM reconstruction_requests WHERE "
                        "occurrence_id = ?", (int(occurrence_id),))
    return bool(cur.rowcount)


def get(occurrence_id: int) -> dict[str, Any] | None:
    with conn() as c:
        r = c.execute("SELECT * FROM reconstruction_requests WHERE "
                      "occurrence_id = ?", (int(occurrence_id),)).fetchone()
    return dict(r) if r else None


def set_state(occurrence_id: int, state: str) -> dict[str, Any] | None:
    """The workshop reporting back. Only it moves a request past QUEUED."""
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}")
    with conn() as c:
        c.execute("UPDATE reconstruction_requests SET state=? WHERE "
                  "occurrence_id=?", (state, int(occurrence_id)))
    return get(occurrence_id)


def pending(limit: int = 200, human_only: bool = True) -> list[dict[str, Any]]:
    """What the workshop should build next.

    Human requests only by default: a reconstruction costs real work, and a
    test row should never be able to order one.
    """
    sql = "SELECT * FROM reconstruction_requests WHERE state = ?"
    params: list[Any] = [QUEUED]
    if human_only:
        qs = ",".join("?" * len(HUMAN_PROVENANCE))
        sql += f" AND provenance IN ({qs})"
        params += list(HUMAN_PROVENANCE)
    sql += " ORDER BY requested_at ASC LIMIT ?"
    params.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, params)]


def status() -> dict[str, Any]:
    with conn() as c:
        by_state = {r["state"]: r["n"] for r in c.execute(
            "SELECT state, COUNT(*) n FROM reconstruction_requests "
            "GROUP BY 1")}
        by_reason = {r["reason"]: r["n"] for r in c.execute(
            "SELECT reason, COUNT(*) n FROM reconstruction_requests "
            "GROUP BY 1")}
    return {"version": REQUEST_VERSION, "by_state": by_state,
            "by_reason": by_reason, "reasons": list(REASONS),
            "reason_labels": REASON_LABEL,
            "pending": len(pending(limit=10_000))}
