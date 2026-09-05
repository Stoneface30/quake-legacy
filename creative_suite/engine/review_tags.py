"""Orthogonal tags: what a moment is FOR, kept apart from how good it is.

WHY THIS IS SEPARATE FROM T1-T5.

The verdict is one axis and it is deliberately coarse, because a reviewer
making thousands of decisions needs one fast question. But six months from
now `T4_KEEP_NORMAL` tells an editor almost nothing, and the information that
would have told them everything -- that this is the clean-POV rocket
prediction they have been hunting for -- was available at review time and
thrown away.

    QUALITY  is the verdict.   T1..T5, exactly one, always.
    PURPOSE  is the tags.      Any number, including none.

They must not collapse into each other. A mechanically ordinary frag can be
`T3 + LEGACY + VOICE + KEEP_CONTEXT` and be one of the most valuable clips in
the archive; an astonishing frag can be `T4 + ALT_POV`, meaning go and find a
better camera for it. A taxonomy that forced either of those into a single
number would lose the sentence.

THE VOCABULARY IS FROZEN. Not because it is perfect, but because comparing
judgements across a thousand reviews requires that the words meant the same
thing throughout. Adding a tag later is safe; changing what one MEANS is not.

Two entries are structural rather than descriptive and carry behaviour:

    GOLDEN         a documentary anchor. Outside T1-T5 entirely, because it
                   is not a quality band -- it is an instruction that no
                   ranking, sampling or downselect may ever hide this.
    KEEP_CONTEXT   the frag is not the unit here; the sequence around it is.
                   A mediocre kill can sit inside an extraordinary fifteen
                   seconds, and the editor needs to be told which.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITORIAL_DB = REPO_ROOT / "creative_suite" / "database" / "editorial.db"

TAG_VERSION = "review-tags-v1"

# ── the frozen vocabulary ───────────────────────────────────────────────────
#
# Grouped only for the reviewer's eye. Nothing downstream may depend on a tag
# belonging to a group -- groups are presentation, tags are the data.

WEAPON = ("RAIL", "LG", "ROCKET", "GRENADE")
CRAFT = ("AIM", "PREDICTION", "MOVEMENT", "TEAMPLAY")
DRAMA = ("CLUTCH", "MULTIKILL", "FUNNY", "VOICE")
HISTORY = ("LEGACY", "ICONIC_PLAYER")
CAMERA = ("CLEAN_POV", "ALT_POV")
STRUCTURAL = ("KEEP_CONTEXT", "GOLDEN")

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("weapon", WEAPON), ("craft", CRAFT), ("drama", DRAMA),
    ("history", HISTORY), ("camera", CAMERA), ("structural", STRUCTURAL),
)

TAGS: tuple[str, ...] = WEAPON + CRAFT + DRAMA + HISTORY + CAMERA + STRUCTURAL

# Reserved names with behaviour attached. Kept in the same table as the
# descriptive tags because they are written by the same keystroke in the same
# moment of judgement, and splitting the storage would only mean two places
# to look for "what did the director say about this".
GOLDEN = "GOLDEN"
KEEP_CONTEXT = "KEEP_CONTEXT"

# Deliberately NOT in the vocabulary, and why:
#
#   AIR_ROCKET, MID_AIR   already machine traits on every occurrence. A human
#                         tag would duplicate a measurement and could
#                         disagree with it.
#   CAMERA_GOOD           CLEAN_POV says the same thing about the thing that
#                         matters, which is whether the action is watchable.
#   LEGACY_VALUE          LEGACY.
_NOT_TAGS = {"AIR_ROCKET", "MID_AIR", "CAMERA_GOOD", "LEGACY_VALUE"}

HUMAN_USER = "HUMAN_USER"
IMPORTED_LEGACY_HUMAN = "IMPORTED_LEGACY_HUMAN"
TEST = "TEST"
HUMAN_PROVENANCE = (HUMAN_USER, IMPORTED_LEGACY_HUMAN)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_tags (
    occurrence_id INTEGER NOT NULL,
    tag           TEXT NOT NULL,
    item_id       TEXT NOT NULL,
    provenance    TEXT NOT NULL DEFAULT 'HUMAN_USER',
    tagged_at     TEXT NOT NULL,
    version       TEXT NOT NULL,
    PRIMARY KEY (occurrence_id, tag)
);
CREATE INDEX IF NOT EXISTS ix_rt_tag ON review_tags(tag);
"""


class UnknownTag(ValueError):
    """A tag outside the frozen vocabulary."""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate(tag: str) -> str:
    t = str(tag).strip().upper()
    if t in _NOT_TAGS:
        raise UnknownTag(
            f"{t} is deliberately not a tag; see review_tags._NOT_TAGS")
    if t not in TAGS:
        raise UnknownTag(f"unknown tag {t!r}; the vocabulary is frozen: "
                         f"{', '.join(TAGS)}")
    return t


def set_tag(occurrence_id: int, tag: str, on: bool = True,
            item_id: str = "", provenance: str = HUMAN_USER) -> dict[str, Any]:
    """Add or remove one tag. Idempotent in both directions."""
    t = validate(tag)
    oid = int(occurrence_id)
    with conn() as c:
        if on:
            c.execute(
                "INSERT INTO review_tags(occurrence_id, tag, item_id, "
                "provenance, tagged_at, version) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(occurrence_id, tag) DO UPDATE SET "
                "tagged_at=excluded.tagged_at, provenance=excluded.provenance",
                (oid, t, item_id or "", provenance, _now(), TAG_VERSION))
        else:
            c.execute("DELETE FROM review_tags WHERE occurrence_id=? AND tag=?",
                      (oid, t))
    return {"occurrence_id": oid, "tag": t, "on": bool(on)}


def tags_for(occurrence_id: int) -> list[str]:
    with conn() as c:
        return [r["tag"] for r in c.execute(
            "SELECT tag FROM review_tags WHERE occurrence_id=? ORDER BY tag",
            (int(occurrence_id),))]


def tags_for_many(occurrence_ids: Sequence[int]) -> dict[int, list[str]]:
    ids = [int(i) for i in occurrence_ids]
    if not ids:
        return {}
    out: dict[int, list[str]] = {}
    with conn() as c:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            qs = ",".join("?" * len(chunk))
            for r in c.execute(
                    f"SELECT occurrence_id, tag FROM review_tags WHERE "
                    f"occurrence_id IN ({qs}) ORDER BY tag", chunk):
                out.setdefault(int(r["occurrence_id"]), []).append(r["tag"])
    return out


def golden_occurrence_ids() -> list[int]:
    """Every documentary anchor.

    Read by anything that ranks, samples or downselects, so that GOLDEN can
    do the one job it exists for: never be hidden.
    """
    with conn() as c:
        return [int(r[0]) for r in c.execute(
            "SELECT occurrence_id FROM review_tags WHERE tag = ? "
            f"AND provenance IN ({','.join('?' * len(HUMAN_PROVENANCE))})",
            (GOLDEN, *HUMAN_PROVENANCE))]


def counts(human_only: bool = True) -> dict[str, int]:
    """How often each tag has been used. The calibration instrument."""
    sql = "SELECT tag, COUNT(*) n FROM review_tags"
    params: list[Any] = []
    if human_only:
        qs = ",".join("?" * len(HUMAN_PROVENANCE))
        sql += f" WHERE provenance IN ({qs})"
        params = list(HUMAN_PROVENANCE)
    sql += " GROUP BY 1 ORDER BY 2 DESC"
    with conn() as c:
        return {r["tag"]: r["n"] for r in c.execute(sql, params)}


def tagged_occurrences(tag: str, limit: int = 500) -> list[dict[str, Any]]:
    t = validate(tag)
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM review_tags WHERE tag=? ORDER BY tagged_at DESC "
            "LIMIT ?", (t, limit))]
