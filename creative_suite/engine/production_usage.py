"""Whether a moment is spoken for, kept apart from what the user thinks of it.

TWO DIFFERENT FACTS. "This is FEATURE material" is a creative judgement and
lives in `human_reviews`. "This is already in Episode 1, Scene 08" is a
production fact and lives here. Conflating them loses both: a moment can be
brilliant and unused, or ordinary and already cut into something.

THE FEAR THIS ANSWERS. The user's stated worry is watching or using the same
frag twice without noticing. The canonical occurrence layer makes that
detectable -- one historical kill has one id however many demos recorded it
-- and this makes it visible: the review UI shows a moment's usage before
asking anything about it, and a later composer can refuse to spend the same
occurrence twice.

BY OCCURRENCE, NEVER BY OBSERVATION. Reserving a clip from one camera does
not free the same kill seen from another. That is the same frag.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

# DATA, not code: in a worktree these differ, and opening a database
# under the wrong one silently creates an empty file. See
# engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
EDITORIAL_DB = REPO_ROOT / "creative_suite" / "database" / "editorial.db"

# The lifecycle. Deliberately short: anything longer becomes a project
# management tool nobody updates, and a stale state is worse than none.
AVAILABLE = "AVAILABLE"          # nothing has claimed it
SHORTLISTED = "SHORTLISTED"      # in a candidate pool for something
ASSIGNED = "ASSIGNED"            # chosen for a specific place
USED = "USED"                    # actually in a delivered cut
STATES = (AVAILABLE, SHORTLISTED, ASSIGNED, USED)

# States that mean "do not spend this again without knowing".
CLAIMED = (ASSIGNED, USED)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS production_usage (
    occurrence_id INTEGER PRIMARY KEY,
    state         TEXT NOT NULL,
    detail        TEXT NOT NULL DEFAULT '',
    updated_at    TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_pu_state ON production_usage(state);
CREATE TABLE IF NOT EXISTS production_usage_log (
    rowid_        INTEGER PRIMARY KEY AUTOINCREMENT,
    occurrence_id INTEGER NOT NULL,
    state         TEXT NOT NULL,
    detail        TEXT NOT NULL DEFAULT '',
    at            TEXT NOT NULL);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def states(occurrence_ids: Sequence[int]) -> dict[int, dict[str, Any]]:
    """Usage for these occurrences. Absent means AVAILABLE -- the default is
    a fact about the world, not a row somebody forgot to write."""
    ids = [int(i) for i in occurrence_ids]
    if not ids:
        return {}
    out: dict[int, dict[str, Any]] = {}
    with conn() as c:
        for chunk in (ids[i:i + 500] for i in range(0, len(ids), 500)):
            marks = ",".join("?" * len(chunk))
            for r in c.execute(
                    f"SELECT * FROM production_usage WHERE occurrence_id "
                    f"IN ({marks})", chunk):
                out[int(r["occurrence_id"])] = {"state": r["state"],
                                                "detail": r["detail"],
                                                "updated_at": r["updated_at"]}
    for i in ids:
        out.setdefault(i, {"state": AVAILABLE, "detail": ""})
    return out


def set_state(occurrence_id: int, state: str, detail: str = "") -> dict[str, Any]:
    """Claim, release or record use of one occurrence."""
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}; expected one of {STATES}")
    now = _now()
    with conn() as c:
        c.execute(
            "INSERT INTO production_usage(occurrence_id, state, detail, "
            "updated_at) VALUES (?,?,?,?) ON CONFLICT(occurrence_id) DO UPDATE "
            "SET state=excluded.state, detail=excluded.detail, "
            "updated_at=excluded.updated_at",
            (int(occurrence_id), state, detail, now))
        c.execute("INSERT INTO production_usage_log(occurrence_id, state, "
                  "detail, at) VALUES (?,?,?,?)",
                  (int(occurrence_id), state, detail, now))
    return {"occurrence_id": int(occurrence_id), "state": state,
            "detail": detail, "updated_at": now}


def claimed(occurrence_ids: Iterable[int]) -> set[int]:
    """Which of these are already assigned or used.

    This is the check a composer runs before spending a moment. It takes
    occurrence ids because a different camera angle on the same kill is the
    same frag, and asking by observation would let a duplicate through.
    """
    return {i for i, st in states(list(occurrence_ids)).items()
            if st["state"] in CLAIMED}


def summary() -> dict[str, Any]:
    with conn() as c:
        rows = dict(c.execute("SELECT state, COUNT(*) FROM production_usage "
                              "GROUP BY 1").fetchall())
    return {"by_state": {s: rows.get(s, 0) for s in STATES},
            "claimed": sum(rows.get(s, 0) for s in CLAIMED),
            "note": "an occurrence with no row is AVAILABLE"}
