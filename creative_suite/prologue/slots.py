"""Named holes in the prologue, and what human review must put in them.

WHY SLOTS EXIST. Human review is happening right now, and it decides what
every moment in the archive is FOR. A parallel creative workstream that reached
into the corpus and picked its own hero frags would be answering a question the
user is in the middle of answering, and would burn material the movie proper
may need more.

So the prologue is built with holes. A slot states a REQUIREMENT -- what shape
of moment the edit needs at that point -- and the code reports how many moments
currently satisfy it. It never picks one.

A slot is filled only when human review assigns a role AND, preferably, writes
an annotation naming it. `intro_candidates()` surfaces those; it still does not
assign them, because a candidate list is a suggestion and the user's click is
the decision.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from creative_suite.prologue import facts

# Annotation text that means "the user was thinking about the opening when
# they wrote this". Human annotation beats machine score, always -- so a frag
# the user tagged "good first shot" outranks anything a scorer liked.
INTRO_HINTS = re.compile(
    r"\b(intro|opening|opener|first shot|good first|explain quake|"
    r"ca explanation|clan arena explain|prologue|title)\b", re.I)

# The roles a slot will accept. A moment the user marked PASS is never pulled
# into the prologue -- PASS means "not primary gameplay material", and the
# opening of the film is the most primary place there is.
ACCEPTS_ROLES = ("T1_FEATURE_FX", "T2_TRANSITION", "T3_RHYTHM_MONTAGE")


@dataclass(frozen=True)
class Slot:
    key: str
    part: str
    requirement: str
    query: str | None          # SQL counting the pool, or None if underivable
    status: str = "OPEN"
    pool_size: int | None = None

    def sized(self) -> "Slot":
        """Return a copy carrying the current pool size."""
        if self.query is None:
            return self
        try:
            with sqlite3.connect(
                    f"file:{facts.RECOGNITION_DB.as_posix()}?mode=ro",
                    uri=True) as c:
                n = c.execute(self.query).fetchone()[0]
        except Exception:                       # pragma: no cover - env guard
            return self
        return Slot(self.key, self.part, self.requirement, self.query,
                    "OPEN" if n else "NO POOL", n)


_M = "from movement_moments_v1"
_K = "from kill_occurrences_v1"

_SLOTS: tuple[Slot, ...] = (
    Slot("SLOT_ACCEL", "P1",
         "one unbroken strafe run, 1.0-2.5 s, peak >= 700 ups, readable "
         "trajectory, no cut",
         f"select count(*) {_M} where kind='HIGH_SPEED_MOVEMENT' and "
         "duration_ms between 1000 and 2500 and peak_speed>=700"),
    Slot("SLOT_ACCEL_FRAG", "P1",
         "as SLOT_ACCEL but ending in a frag, for the second movement",
         f"select count(*) {_M} where kind='HIGH_SPEED_MOVEMENT' and "
         "duration_ms between 1000 and 2500 and peak_speed>=700 and "
         "traits like '%ENDS_IN_FRAG%'"),
    Slot("SLOT_ROCKET_JUMP", "P1",
         "rocket jump, health visibly traded for height/speed, <= 1.0 s",
         None),
    Slot("SLOT_RAIL_FLICK", "P1",
         "railgun, clean single impact, <= 0.6 s, no opponent name on HUD",
         f"select count(*) {_K} where mod_name='RAILGUN'"),
    Slot("SLOT_AIR_ROCKET", "P1",
         "direct rocket on an airborne victim (airshot)",
         None),
    Slot("SLOT_TELEFRAG", "P1", "telefrag, instant, <= 0.4 s",
         f"select count(*) {_K} where mod_name='TELEFRAG'"),
    Slot("SLOT_LG_TRACK", "P1",
         "sustained lightning contact >= 0.6 s, tracking legible",
         f"select count(*) {_K} where mod_name='LIGHTNING'"),
    Slot("SLOT_JUMPPAD", "P1", "jump pad launch, clean vertical routing",
         f"select count(*) {_M} where kind='JUMPPAD_ACTION'"),
    Slot("SLOT_TELEPORT", "P1", "confirmed teleport transit, in and out",
         "select count(*) from teleport_transits_v1"),
    Slot("SLOT_RHYTHM", "P1",
         "6 x short readable actions for the density ramp, cut to music",
         f"select count(*) {_K} where mod_name in "
         "('RAILGUN','ROCKET','LIGHTNING')"),
    Slot("SLOT_CLANWAR", "P3",
         "a full round story with team context, round won, tactical camera "
         "viable -- for the promise montage only",
         "select count(*) from round_kills_v1 where kills>=6"),
    Slot("SLOT_PROMISE", "P3",
         "5 x 1.5 s technique demonstrations, no repeats from the movie's "
         "own opening",
         None),
)

SLOTS: tuple[Slot, ...] = tuple(s.sized() for s in _SLOTS)


# The review workstation writes verdicts here. The table name is asserted
# rather than probed: a first draft of this module guessed "review_verdicts",
# found nothing, and returned an empty list that was indistinguishable from
# "the user has not annotated anything yet". A wrong table name must fail
# loudly, because a silent empty candidate list is how the prologue would
# quietly stop listening to human review.
VERDICT_TABLE = "human_reviews"
VERDICT_COLUMNS = {"item_id", "item_type", "human_role", "note", "provenance"}

# Only these count towards anything the user is said to have decided. TEST and
# SYSTEM rows exist in this table today and are not the user's judgement.
HUMAN_PROVENANCE = ("HUMAN_USER", "IMPORTED_LEGACY_HUMAN")


class ReviewSchemaChanged(RuntimeError):
    """The editorial store no longer looks the way this module expects."""


def intro_candidates(limit: int = 40) -> list[dict[str, Any]]:
    """Reviewed moments whose annotation mentions the opening.

    Human annotation beats machine score. This reads the editorial store the
    review workstation writes and returns what the user themselves flagged --
    ordered by nothing, because ordering would be a recommendation.

    Returns [] when nothing has been annotated that way yet, which is the
    expected state early in review. Raises `ReviewSchemaChanged` when the
    store's shape has moved, so that "no candidates" always means "the user
    has not flagged any", never "this module lost track of the schema".
    """
    db = facts.DB_ROOT / "editorial.db"
    if not db.exists():
        return []
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as c:
        tables = {r[0] for r in c.execute(
            "select name from sqlite_master where type='table'")}
        if VERDICT_TABLE not in tables:
            raise ReviewSchemaChanged(
                f"{VERDICT_TABLE!r} is gone from editorial.db; the prologue "
                f"cannot see human review. Found: {sorted(tables)}")
        cols = {r[1] for r in c.execute(f"PRAGMA table_info({VERDICT_TABLE})")}
        if missing := VERDICT_COLUMNS - cols:
            raise ReviewSchemaChanged(
                f"{VERDICT_TABLE} is missing {sorted(missing)}; got {sorted(cols)}")
        marks = ",".join("?" * len(HUMAN_PROVENANCE))
        rows = c.execute(
            f"select item_type, item_id, human_role, note from {VERDICT_TABLE} "
            f"where provenance in ({marks}) and note is not null and note != ''",
            HUMAN_PROVENANCE).fetchall()
    out = []
    for item_type, item_id, role, note in rows:
        if role in ACCEPTS_ROLES and INTRO_HINTS.search(note or ""):
            out.append({"item_type": item_type, "item_id": item_id,
                        "role": role, "note": note,
                        "why": "user annotation names the opening"})
        if len(out) >= limit:
            break
    return out


def report() -> dict[str, Any]:
    """Slot status plus anything review has flagged for the opening."""
    cands = intro_candidates()
    return {
        "slots": [{"key": s.key, "part": s.part, "requirement": s.requirement,
                   "pool_size": s.pool_size, "status": s.status}
                  for s in SLOTS],
        "open": sum(1 for s in SLOTS if s.status == "OPEN"),
        "candidates_from_review": cands,
        "rule": ("pools are counted, never picked. A slot is filled by a human "
                 "verdict, and PASS-marked material is never eligible"),
    }


if __name__ == "__main__":                      # pragma: no cover - CLI
    r = report()
    w = max(len(s["key"]) for s in r["slots"])
    for s in r["slots"]:
        pool = f"{s['pool_size']:,}" if s["pool_size"] is not None else "n/a"
        print(f"{s['key']:<{w}}  {s['part']}  pool={pool:>10}  {s['status']}")
    print(f"\n{r['open']} slots open, "
          f"{len(r['candidates_from_review'])} candidates from human review")
