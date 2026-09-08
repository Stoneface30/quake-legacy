"""What the user's first fifty verdicts say, once there are fifty.

Section 20: "At 50 genuine USER_FRAGS: produce a curation analysis. Do not
automatically change the queue."

BOTH HALVES ARE THE POINT. The analysis is worth having, and it is not
allowed to act. A system that reads a few dozen human decisions and then
quietly reorders the queue to match them stops showing the user anything
that would change their mind -- the fiftieth verdict would shape the next
thousand clips they are offered, and the sample would never be corrected.
So this module returns a report. It has no writer, and it takes no
argument that would let it become one.

GENUINE MEANS HUMAN. Only verdicts the user actually recorded count.
Imported legacy decisions, test rows and machine suggestions are excluded
from the denominator, because a checkpoint whose sample is partly synthetic
is a checkpoint about nothing.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# DATA, not code: in a worktree these differ, and opening a database
# under the wrong one silently creates an empty file. See
# engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()

# The user's number. Below it there is not enough signal to say anything
# that would not be an accident of which clips happened to come first.
CHECKPOINT_AT = 50


@dataclass
class Checkpoint:
    reviewed: int
    due: bool
    roles: dict[str, int] = field(default_factory=dict)
    tags: dict[str, int] = field(default_factory=dict)
    golden: int = 0
    maps: dict[str, int] = field(default_factory=dict)
    regions: dict[str, int] = field(default_factory=dict)
    weapons: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"reviewed": self.reviewed, "due": self.due,
                "checkpoint_at": CHECKPOINT_AT, "roles": self.roles,
                "tags": self.tags, "golden": self.golden, "maps": self.maps,
                "regions": self.regions, "weapons": self.weapons,
                "notes": self.notes}


def analyse() -> Checkpoint:
    """Read-only. Returns a report and changes nothing, ever."""
    from creative_suite.engine import review_corpus as rc

    prog = rc.progress("USER_FRAG")
    reviewed = int(prog.get("reviewed", 0))
    cp = Checkpoint(reviewed=reviewed, due=reviewed >= CHECKPOINT_AT,
                    roles=dict(prog.get("roles", {})))
    if not cp.due:
        cp.notes.append(
            f"not due: {reviewed} of {CHECKPOINT_AT} genuine human verdicts")
        return cp

    occ = _reviewed_occurrences()
    cp.golden = _golden_count()
    cp.tags = _tag_counts()
    for o in occ:
        for key, store in ((o.get("map"), cp.maps),
                           (o.get("weapon"), cp.weapons),
                           (o.get("region"), cp.regions)):
            if key:
                store[key] = store.get(key, 0) + 1

    kept = sum(n for r, n in cp.roles.items() if not r.startswith("T5"))
    if reviewed:
        cp.notes.append(
            f"{kept} of {reviewed} kept above filler "
            f"({100 * kept / reviewed:.0f}%)")
    if cp.regions:
        top = max(cp.regions.items(), key=lambda kv: kv[1])
        cp.notes.append(f"most kept region: {top[0]} ({top[1]})")
    cp.notes.append("THE QUEUE IS UNCHANGED. This is a reading, not a rule.")
    return cp


def _reviewed_occurrences() -> list[dict[str, Any]]:
    from creative_suite.engine import review_corpus as rc
    db = getattr(rc, "RECOGNITION_DB", None)
    if db is None:
        return []
    rows: list[dict[str, Any]] = []
    try:
        with sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro",
                             uri=True) as c:
            c.row_factory = sqlite3.Row
            ids = human_reviewed_occurrence_ids()
            if not ids:
                return []
            qs = ",".join("?" * len(ids))
            for r in c.execute(
                    "SELECT o.occurrence_id, k.map, k.mod_name FROM "
                    "kill_occurrences_v1 o JOIN kill_events_v1 k ON "
                    "k.kill_event_id=o.best_observation_id WHERE "
                    "o.occurrence_id IN (" + qs + ")", ids):
                d = {"occurrence_id": int(r["occurrence_id"]),
                     "map": r["map"], "weapon": r["mod_name"]}
                d["region"] = _region_of(d["occurrence_id"])
                rows.append(d)
    except sqlite3.Error:
        return []
    return rows


def _region_of(occurrence_id: int) -> str | None:
    try:
        from engine.pantheon import map_context as mc
        ctx = mc.context_for_kill(occurrence_id)
    except Exception:                                          # noqa: BLE001
        return None
    if not ctx or not ctx.get("location"):
        return None
    return f"{ctx['map']}/{ctx['location']['region_id']}"


def human_reviewed_occurrence_ids() -> list[int]:
    """The occurrences the USER actually judged.

    Read straight from the review table with the provenance filter applied,
    because a checkpoint whose sample includes test rows or machine
    suggestions is a checkpoint about nothing.
    """
    from creative_suite.engine import review_corpus as rc
    c = rc.conn()
    try:
        return [int(r["source_id"]) for r in c.execute(
            "SELECT DISTINCT source_id FROM human_reviews WHERE "
            "item_type='USER_FRAG' AND provenance=? ORDER BY source_id",
            (rc.HUMAN_USER,))]
    finally:
        c.close()


def _golden_count() -> int:
    from creative_suite.engine import review_tags as rt
    return len(rt.golden_occurrence_ids())


def _tag_counts() -> dict[str, int]:
    from creative_suite.engine import review_tags as rt
    return dict(rt.counts(human_only=True))
