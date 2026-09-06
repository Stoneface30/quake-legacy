"""Does every human decision still point at the moment it was made about?

THE FAILURE THIS EXISTS TO CATCH IS SILENT. Human verdicts, tags, notes,
GOLDEN marks, workshop requests and usage states are all addressed by
OCCURRENCE ID -- a machine-derived number. Rebuild the canonical layer and
renumber it, and every one of those rows still exists, still says
`T4_KEEP_NORMAL`, and now describes a different kill. Nothing errors. The
count is unchanged. The reviewer looks fine.

So a rebuild is not allowed to promote until this has been run and every
human-touched target is EXACT.

WHAT MAKES A TARGET "THE SAME EVENT". Not the id -- the id is what is under
suspicion. The kill fingerprint is: map, server time, killer slot, victim
slot, means of death. If the id still resolves to a row with the same
fingerprint the human decision is intact; if it resolves to a different
fingerprint, or to nothing, it is not.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = REPO_ROOT / "creative_suite" / "database"
RECOGNITION_DB = DB_DIR / "frag_recognition.db"
EDITORIAL_DB = DB_DIR / "editorial.db"

EXACT = "EXACT"                # same id, same fingerprint: safe
MAPPED = "MAPPED"              # a PROVEN old -> new identity mapping exists
FINGERPRINT_CHANGED = "FINGERPRINT_CHANGED"
AMBIGUOUS = "AMBIGUOUS"
MISSING = "MISSING"

# ONLY TWO OUTCOMES ARE SAFE, and an integer id matching is not one of them.
#
# The first version had a status called CHANGED_ID_SAME_EVENT and did not
# block on it -- it asserted "same event" on the strength of the id being
# equal, which is exactly the thing a renumbering breaks. If the fingerprint
# moved, the id is now describing a different kill and the verdict attached
# to it is a statement about a moment nobody judged.
SAFE = (EXACT, MAPPED)
BLOCKING = (FINGERPRINT_CHANGED, AMBIGUOUS, MISSING)

# Every table in the editorial database that carries a human decision keyed
# by occurrence. Listed explicitly: a table added later and forgotten here
# would migrate silently and nobody would find out.
HUMAN_TABLES = (
    ("human_reviews", "source_id", "T1-T5 verdicts"),
    ("review_tags", "occurrence_id", "tags, GOLDEN, KEEP_CONTEXT"),
    ("dismissed_occurrences", "occurrence_id", "deletions"),
    ("reconstruction_requests", "occurrence_id", "workshop requests"),
    # SHORTLISTED / ASSIGNED / USED is the director deciding what the film
    # does with a moment. It looks like machine state and is not: a rebuild
    # that detached it would lose real editorial work with nothing to show
    # that it had.
    ("production_usage", "occurrence_id", "usage lifecycle"),
)

# Keyed by (content_hash, round) rather than occurrence, so they survive an
# occurrence renumber by construction -- but they are still counted, because
# "it cannot break" and "it did not break" are different claims.
SCOPED_TABLES = (
    ("round_annotations", "round notes"),
    ("scene_event_notes", "scene-event notes"),
)


@dataclass(frozen=True)
class TargetCheck:
    table: str
    key: int
    status: str
    detail: str = ""


def _ro(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _table_exists(c: sqlite3.Connection, name: str) -> bool:
    return bool(c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone())


def fingerprints(ids: list[int], db: Path = RECOGNITION_DB
                 ) -> dict[int, str]:
    """The identity of each occurrence, independent of its id."""
    if not ids:
        return {}
    out: dict[int, str] = {}
    with _ro(db) as c:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            qs = ",".join("?" * len(chunk))
            for r in c.execute(
                    f"SELECT occurrence_id, kill_fingerprint FROM "
                    f"kill_occurrences_v1 WHERE occurrence_id IN ({qs})",
                    chunk):
                out[int(r["occurrence_id"])] = r["kill_fingerprint"]
    return out


def human_targets(db: Path = EDITORIAL_DB) -> dict[str, list[int]]:
    """Every occurrence id a human has expressed an opinion about."""
    out: dict[str, list[int]] = {}
    with _ro(db) as c:
        for table, col, _label in HUMAN_TABLES:
            if not _table_exists(c, table):
                out[table] = []
                continue
            cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})")}
            where = ""
            if "provenance" in cols:
                # Only HUMAN truth is protected. A TEST row that fails to
                # migrate is not a reason to block a rebuild.
                where = ("WHERE provenance IN ('HUMAN_USER',"
                         "'IMPORTED_LEGACY_HUMAN')")
            out[table] = [int(r[0]) for r in c.execute(
                f"SELECT DISTINCT {col} FROM {table} {where}")]
    return out


def check(before_db: Path = RECOGNITION_DB, after_db: Path | None = None,
          editorial: Path = EDITORIAL_DB,
          mapping: dict[int, int] | None = None) -> dict[str, Any]:
    """Compare every human target against the epoch that is about to be live.

    `after_db` defaults to the same database, which is the honest answer when
    the canonical layer was NOT rebuilt: the check then proves that nothing
    moved rather than pretending a migration happened.
    """
    after = after_db or before_db
    targets = human_targets(editorial)
    all_ids = sorted({i for ids in targets.values() for i in ids})
    fp_before = fingerprints(all_ids, before_db)
    fp_after = fingerprints(all_ids, after)

    checks: list[TargetCheck] = []
    for table, ids in targets.items():
        for i in ids:
            b, a = fp_before.get(i), fp_after.get(i)
            if a is None:
                checks.append(TargetCheck(table, i, MISSING,
                                          "no occurrence with this id"))
            elif b is None:
                checks.append(TargetCheck(table, i, AMBIGUOUS,
                                          "not present before the rebuild"))
            elif a == b:
                checks.append(TargetCheck(table, i, EXACT))
            elif mapping and mapping.get(i) is not None:
                # An explicit, independently produced old -> new mapping is
                # the only other thing that makes a move safe.
                new_id = mapping[i]
                moved = fingerprints([new_id], after).get(new_id)
                checks.append(TargetCheck(
                    table, i, MAPPED if moved == b else AMBIGUOUS,
                    f"mapped to {new_id}"))
            else:
                checks.append(TargetCheck(
                    table, i, FINGERPRINT_CHANGED,
                    "this id now resolves to a DIFFERENT kill; the verdict "
                    "attached to it would describe a moment nobody judged"))

    scoped: dict[str, int] = {}
    with _ro(editorial) as c:
        for table, _label in SCOPED_TABLES:
            scoped[table] = (
                c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if _table_exists(c, table) else 0)

    by_status: dict[str, int] = {}
    for ch in checks:
        by_status[ch.status] = by_status.get(ch.status, 0) + 1
    blockers = [ch for ch in checks if ch.status not in SAFE]

    return {
        "human_targets": len(checks),
        "by_table": {t: len(ids) for t, ids in targets.items()},
        "by_status": by_status,
        "scoped_rows": scoped,
        "blocked": bool(blockers),
        "blockers": [{"table": b.table, "key": b.key, "status": b.status,
                      "detail": b.detail} for b in blockers[:50]],
    }


def counts(editorial: Path = EDITORIAL_DB) -> dict[str, Any]:
    """The numbers that must reconcile exactly across a promotion."""
    out: dict[str, Any] = {}
    with _ro(editorial) as c:
        if _table_exists(c, "human_reviews"):
            out["verdicts"] = {r[0]: r[1] for r in c.execute(
                "SELECT human_role, COUNT(*) FROM human_reviews WHERE "
                "provenance IN ('HUMAN_USER','IMPORTED_LEGACY_HUMAN') "
                "GROUP BY 1")}
            out["verdicts_total"] = sum(out["verdicts"].values())
        if _table_exists(c, "review_tags"):
            out["tags"] = {r[0]: r[1] for r in c.execute(
                "SELECT tag, COUNT(*) FROM review_tags WHERE provenance IN "
                "('HUMAN_USER','IMPORTED_LEGACY_HUMAN') GROUP BY 1")}
        for t, _l in SCOPED_TABLES:
            if _table_exists(c, t):
                out[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t, _c, _l in HUMAN_TABLES[2:]:
            if _table_exists(c, t):
                out[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    return out
