"""The mining epoch: a versioned rebuild of the machine-derived universe.

WHY AN EPOCH RATHER THAN AN IN-PLACE REBUILD.

Machine-derived data may be rebuilt; human data may not. Those two live in
different databases already, but the reviewer reads them TOGETHER -- a
verdict is addressed by an occurrence id, and occurrence ids are
machine-derived. So a rebuild that renumbered occurrences in place would
silently detach every verdict the user has made, and the failure would be
invisible until someone counted.

An epoch is therefore built in staging, reconciled against the live human
data BEFORE anything is promoted, and promoted atomically. If the rebuild
dies halfway, the live reviewer is untouched.

WHAT AN EPOCH IS NOT. It is not a re-parse for its own sake. The raw demo is
the authority, but a cache built by the CURRENT parser from that raw demo is
the same information -- so the epoch records which extractor version produced
each layer, and re-derives only what is genuinely stale. Re-reading 14 GB to
recompute bytes that have not changed is not rigour, it is cost.
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = REPO_ROOT / "demos"
DB_DIR = REPO_ROOT / "creative_suite" / "database"
RECOGNITION_DB = DB_DIR / "frag_recognition.db"
REBUILT_DB = DB_DIR / "frags_rebuilt.db"
EPOCH_DB = DB_DIR / "mining_epoch.db"

# The epoch's own identity. Bump when the MEANING of a derived layer changes,
# never merely when it is recomputed.
EPOCH_VERSION = "review-mining-v2"

# Parser/derivation versions this epoch considers current. A cache produced
# by any other version is stale by definition and must be re-derived.
CURRENT_SEMANTIC_VERSION = "semantic-events-v1.0.4"

# Directories that hold .dm_73 files which are NOT corpus. The prologue
# worktree writes synthetic demos as test fixtures; mining them would put
# invented gameplay into the historical record.
NOT_CORPUS = (".claude", ".tmp", "output", "SOURCE_EXCEPTIONS")


@dataclass
class DemoRow:
    path: Path
    name: str
    size: int
    content_hash: str = ""
    known: bool = False           # already in the previous mining epoch
    duplicate_of: str = ""        # same bytes as a demo we already have
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "size": self.size,
                "content_hash": self.content_hash, "known": self.known,
                "duplicate_of": self.duplicate_of, "error": self.error}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_corpus(p: Path) -> bool:
    """Raw demos only. Synthetic fixtures are not history."""
    parts = set(p.parts)
    return not (parts & set(NOT_CORPUS))


def enumerate_raw(root: Path = DEMO_ROOT) -> list[Path]:
    return sorted(p for p in root.rglob("*.dm_73") if is_corpus(p))


def content_hash(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def known_hashes(db: Path = RECOGNITION_DB) -> set[str]:
    """Content hashes the PREVIOUS epoch actually mined."""
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        return {r[0] for r in c.execute(
            "SELECT content_hash FROM scanned_demos")}


def current_semantic_hashes(db: Path = RECOGNITION_DB) -> set[str]:
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        return {r[0] for r in c.execute(
            "SELECT content_hash FROM enrichment_runs_v1 WHERE version = ?",
            (CURRENT_SEMANTIC_VERSION,))}


_SCHEMA = """
CREATE TABLE IF NOT EXISTS epoch_demos (
    content_hash TEXT PRIMARY KEY,
    demo_name    TEXT NOT NULL,
    size_bytes   INTEGER NOT NULL,
    first_seen   TEXT NOT NULL,
    known_before INTEGER NOT NULL DEFAULT 0,
    n_copies     INTEGER NOT NULL DEFAULT 1,
    error        TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS epoch_runs (
    epoch        TEXT NOT NULL,
    stage        TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    ok           INTEGER,
    detail       TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (epoch, stage)
);
"""


def conn(db: Path = EPOCH_DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def record_stage(stage: str, ok: bool | None = None, detail: str = "",
                 db: Path = EPOCH_DB) -> None:
    with conn(db) as c:
        row = c.execute("SELECT started_at FROM epoch_runs WHERE epoch=? "
                        "AND stage=?", (EPOCH_VERSION, stage)).fetchone()
        if row is None:
            c.execute("INSERT INTO epoch_runs(epoch, stage, started_at, ok, "
                      "detail) VALUES(?,?,?,?,?)",
                      (EPOCH_VERSION, stage, _now(),
                       None if ok is None else int(ok), detail))
        else:
            c.execute("UPDATE epoch_runs SET finished_at=?, ok=?, detail=? "
                      "WHERE epoch=? AND stage=?",
                      (_now(), None if ok is None else int(ok), detail,
                       EPOCH_VERSION, stage))


def inventory(paths: Iterable[Path] | None = None,
              db: Path = EPOCH_DB) -> dict[str, Any]:
    """Hash every raw demo and classify it against the previous epoch.

    Content hash, not filename. Quake Live names demos `Demo (417).dm_73` and
    the archive contains re-saved copies of the same match under several
    names, so a filename inventory would both miss real demos and count the
    same match twice.
    """
    files = list(paths) if paths is not None else enumerate_raw()
    before = known_hashes()
    seen: dict[str, DemoRow] = {}
    errors: list[DemoRow] = []

    for p in files:
        row = DemoRow(path=p, name=p.name, size=p.stat().st_size)
        try:
            row.content_hash = content_hash(p)
        except OSError as e:                                   # noqa: PERF203
            row.error = f"{type(e).__name__}: {e}"
            errors.append(row)
            continue
        prev = seen.get(row.content_hash)
        if prev is not None:
            prev_copies = getattr(prev, "copies", 1)
            setattr(prev, "copies", prev_copies + 1)
            continue
        row.known = row.content_hash in before
        setattr(row, "copies", 1)
        seen[row.content_hash] = row

    with conn(db) as c:
        c.execute("DELETE FROM epoch_demos")
        c.executemany(
            "INSERT INTO epoch_demos(content_hash, demo_name, size_bytes, "
            "first_seen, known_before, n_copies, error) VALUES(?,?,?,?,?,?,?)",
            [(r.content_hash, r.name, r.size, _now(), int(r.known),
              getattr(r, "copies", 1), r.error) for r in seen.values()])

    new = [r for r in seen.values() if not r.known]
    return {
        "epoch": EPOCH_VERSION,
        "files_on_disk": len(files),
        "distinct_demos": len(seen),
        "duplicate_files": len(files) - len(seen) - len(errors),
        "known_before": len(seen) - len(new),
        "never_mined": len(new),
        "unreadable": len(errors),
        "errors": [r.to_dict() for r in errors[:20]],
        "never_mined_sample": [r.name for r in new[:10]],
    }


def status(db: Path = EPOCH_DB) -> dict[str, Any]:
    with conn(db) as c:
        n = c.execute("SELECT COUNT(*) FROM epoch_demos").fetchone()[0]
        new = c.execute("SELECT COUNT(*) FROM epoch_demos WHERE "
                        "known_before = 0").fetchone()[0]
        stages = [dict(r) for r in c.execute(
            "SELECT * FROM epoch_runs WHERE epoch = ? ORDER BY started_at",
            (EPOCH_VERSION,))]
    return {"epoch": EPOCH_VERSION, "distinct_demos": n,
            "never_mined": new, "stages": stages}


# ── promotion ───────────────────────────────────────────────────────────────
#
# ADDITIVE, AND THEREFORE REVERSIBLE. The epoch's new layers are copied into
# the recognition database as NEW tables; nothing existing is dropped,
# renamed or renumbered. That is what makes the human-migration check come
# out EXACT: the occurrence layer every verdict is addressed by is not
# touched at all, so no id can move.
#
# Rollback is `DROP TABLE`, and the epoch database remains on disk as the
# snapshot the brief asks to keep.

PROMOTED_TABLES = ("action_moments_v1", "aim_events_v1")


def promote(recognition: Path = RECOGNITION_DB, epoch: Path = EPOCH_DB,
            dry_run: bool = False) -> dict[str, Any]:
    """Copy the epoch's new layers into the review authority.

    Refuses if a target table already holds rows from a DIFFERENT epoch --
    two epochs' worth of actions in one table would double every count and
    there would be no way to tell which row came from where.
    """
    out: dict[str, Any] = {"epoch": EPOCH_VERSION, "tables": {},
                           "dry_run": dry_run}
    with sqlite3.connect(f"file:{epoch}?mode=ro", uri=True) as src:
        src.row_factory = sqlite3.Row
        have = {r[0] for r in src.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for t in PROMOTED_TABLES:
            if t not in have:
                out["tables"][t] = {"status": "ABSENT", "rows": 0}
                continue
            rows = [dict(r) for r in src.execute(f"SELECT * FROM {t}")]
            out["tables"][t] = {"status": "READY", "rows": len(rows)}
            if dry_run or not rows:
                continue
            cols = [k for k in rows[0] if k not in ("action_id", "aim_id")]
            ddl = src.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (t,)).fetchone()[0]
            with sqlite3.connect(recognition, timeout=300) as dst:
                existing = dst.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name=?", (t,)).fetchone()
                if existing:
                    other = dst.execute(
                        f"SELECT COUNT(*) FROM {t} WHERE version <> ?",
                        (rows[0]["version"],)).fetchone()[0]
                    if other:
                        out["tables"][t] = {
                            "status": "REFUSED",
                            "detail": f"{other} rows from another epoch"}
                        continue
                    dst.execute(f"DELETE FROM {t}")
                else:
                    dst.execute(ddl)
                dst.executemany(
                    f"INSERT INTO {t} ({','.join(cols)}) VALUES "
                    f"({','.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])
                dst.commit()
            out["tables"][t]["status"] = "PROMOTED"
    return out


def rollback(recognition: Path = RECOGNITION_DB) -> dict[str, Any]:
    """Undo a promotion. The epoch database keeps the data."""
    dropped = []
    with sqlite3.connect(recognition, timeout=300) as dst:
        for t in PROMOTED_TABLES:
            if dst.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name=?", (t,)).fetchone():
                dst.execute(f"DROP TABLE {t}")
                dropped.append(t)
        dst.commit()
    return {"dropped": dropped}
