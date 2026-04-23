"""creative_suite/database/nle_db.py — SQLite access layer for studio_nle.db.

WAL mode, thread-local connections, context manager helper.
CRUD helpers for all 4 NLE tables.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

_SCHEMA_SQL = Path(__file__).with_name("nle_schema.sql")

_local = threading.local()


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def _migrate(db_path: Path) -> None:
    """Add columns introduced after initial schema. Safe to call on every startup."""
    with get_db(db_path) as con:
        cols = {row[1] for row in con.execute("PRAGMA table_info(clip_arrangements)")}
        if "trashed" not in cols:
            con.execute(
                "ALTER TABLE clip_arrangements ADD COLUMN trashed INTEGER NOT NULL DEFAULT 0"
            )


def init_db(db_path: Path) -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = _connect(db_path)
    con.executescript(_SCHEMA_SQL.read_text(encoding="utf-8"))
    con.commit()
    con.close()
    _migrate(db_path)  # run after schema creation to handle existing DBs


@contextmanager
def get_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Thread-local connection context manager. Auto-commits on success."""
    if not hasattr(_local, "con") or getattr(_local, "db_path", None) != str(db_path):
        _local.con = _connect(db_path)
        _local.db_path = str(db_path)
    con = _local.con
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


# ── clip_arrangements ──────────────────────────────────────────────────────────

def get_arrangement(db_path: Path, part: int) -> list[dict[str, Any]]:
    """Get active (non-trashed) clips for a part, ordered by position."""
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM clip_arrangements WHERE part=? AND trashed=0 ORDER BY position",
            (part,),
        ).fetchall()
        clips = [_row_to_dict(r) for r in rows]
        ids = [c["id"] for c in clips]
        fx_rows: list[dict] = []
        if ids:
            placeholders = ",".join("?" * len(ids))
            fx_rows = [_row_to_dict(r) for r in con.execute(
                f"SELECT * FROM clip_effects WHERE arrangement_id IN ({placeholders}) ORDER BY position",
                ids,
            ).fetchall()]
    fx_by_clip: dict[int, list] = {c["id"]: [] for c in clips}
    for fx in fx_rows:
        aid = fx["arrangement_id"]
        if aid in fx_by_clip:
            fx_by_clip[aid].append(fx)
    for c in clips:
        c["effects"] = fx_by_clip[c["id"]]
    return clips


def get_arrangement_all(db_path: Path, part: int) -> list[dict[str, Any]]:
    """Get ALL clips for a part including trashed, ordered by position."""
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM clip_arrangements WHERE part=? ORDER BY position",
            (part,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def upsert_arrangement_clip(db_path: Path, part: int, position: int, role: str,
                             clip_path: str, tier: str, is_fl: bool,
                             pair_path: str | None, duration_s: float | None,
                             clip_id: int | None = None) -> int:
    now = time.time()
    with get_db(db_path) as con:
        if clip_id is not None:
            con.execute(
                """UPDATE clip_arrangements
                   SET position=?, role=?, clip_path=?, tier=?, is_fl=?,
                       pair_path=?, duration_s=?, updated_at=?
                   WHERE id=?""",
                (position, role, clip_path, tier, int(is_fl),
                 pair_path, duration_s, now, clip_id),
            )
            return clip_id
        cur = con.execute(
            """INSERT INTO clip_arrangements
               (part, position, role, clip_path, tier, is_fl, pair_path, duration_s, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (part, position, role, clip_path, tier, int(is_fl),
             pair_path, duration_s, now),
        )
        return cur.lastrowid  # type: ignore[return-value]


def bulk_replace_arrangement(db_path: Path, part: int,
                              clips: list[dict[str, Any]]) -> None:
    """Delete all clips for a part and re-insert in new order.

    Preserves two things that a naive DELETE+INSERT would silently destroy:
    1. clip_effects rows (CASCADE-deleted with old arrangement_id) — snapshotted
       before DELETE and restored by clip_path match after re-INSERT.
    2. Soft-deleted (trashed) clips — re-appended after the new order so they
       survive the next drag/reorder and can still be restored or recovered.
    """
    now = time.time()
    with get_db(db_path) as con:
        # ── Snapshot effects keyed by clip_path before CASCADE delete ──────────
        fx_rows = con.execute(
            """SELECT ca.clip_path, ce.effect_type, ce.params, ce.position, ce.enabled
               FROM clip_arrangements ca
               JOIN clip_effects ce ON ce.arrangement_id = ca.id
               WHERE ca.part=?""",
            (part,),
        ).fetchall()
        effects_by_path: dict[str, list[tuple]] = {}
        for r in fx_rows:
            effects_by_path.setdefault(r[0], []).append(r[1:])

        # ── Snapshot trashed clips so they survive the replacement ─────────────
        trashed_rows = con.execute(
            """SELECT clip_path, role, tier, is_fl, pair_path, duration_s
               FROM clip_arrangements WHERE part=? AND trashed=1""",
            (part,),
        ).fetchall()

        con.execute("DELETE FROM clip_arrangements WHERE part=?", (part,))

        def _insert_clip(i: int, clip_path: str, role: str, tier: str,
                         is_fl: int, pair_path: Any, duration_s: Any,
                         trashed: int) -> int:
            cur = con.execute(
                """INSERT INTO clip_arrangements
                   (part, position, role, clip_path, tier, is_fl, pair_path,
                    duration_s, trashed, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (part, i, role, clip_path, tier, is_fl, pair_path,
                 duration_s, trashed, now),
            )
            return cur.lastrowid  # type: ignore[return-value]

        def _restore_effects(new_id: int, clip_path: str) -> None:
            for etype, params, pos, enabled in effects_by_path.get(clip_path, []):
                con.execute(
                    """INSERT INTO clip_effects
                       (arrangement_id, effect_type, params, position, enabled)
                       VALUES (?,?,?,?,?)""",
                    (new_id, etype, params, pos, enabled),
                )

        # ── Re-insert active clips in new order ────────────────────────────────
        for i, c in enumerate(clips):
            cp = c["clip_path"]
            new_id = _insert_clip(
                i, cp, c.get("role", "body"), c.get("tier", "T2"),
                int(c.get("is_fl", False)), c.get("pair_path"),
                c.get("duration_s"), 0,
            )
            _restore_effects(new_id, cp)

        # ── Re-append trashed clips (de-duped) at end ──────────────────────────
        active_paths = {c["clip_path"] for c in clips}
        offset = len(clips)
        for j, (cp, role, tier, is_fl, pair_path, duration_s) in enumerate(trashed_rows):
            if cp in active_paths:
                continue  # active version takes precedence; don't double-insert
            new_id = _insert_clip(
                offset + j, cp, role or "body", tier or "T2",
                int(is_fl or 0), pair_path, duration_s, 1,
            )
            _restore_effects(new_id, cp)


def delete_arrangement_clip(db_path: Path, clip_id: int) -> None:
    with get_db(db_path) as con:
        con.execute("DELETE FROM clip_arrangements WHERE id=?", (clip_id,))


def trash_clip(db_path: Path, clip_id: int) -> None:
    """Soft-delete: set trashed=1. Clip stays in DB and on disk."""
    with get_db(db_path) as con:
        con.execute(
            "UPDATE clip_arrangements SET trashed=1, updated_at=? WHERE id=?",
            (time.time(), clip_id),
        )


def restore_clip(db_path: Path, clip_id: int) -> None:
    """Un-trash a clip: set trashed=0."""
    with get_db(db_path) as con:
        con.execute(
            "UPDATE clip_arrangements SET trashed=0, updated_at=? WHERE id=?",
            (time.time(), clip_id),
        )


# ── clip_effects ───────────────────────────────────────────────────────────────

def get_clip_effects(db_path: Path, arrangement_id: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM clip_effects WHERE arrangement_id=? ORDER BY position",
            (arrangement_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def add_clip_effect(db_path: Path, arrangement_id: int, effect_type: str,
                    params: dict, position: int) -> int:
    with get_db(db_path) as con:
        cur = con.execute(
            """INSERT INTO clip_effects (arrangement_id, effect_type, params, position, enabled)
               VALUES (?,?,?,?,1)""",
            (arrangement_id, effect_type, json.dumps(params), position),
        )
        return cur.lastrowid  # type: ignore[return-value]


def update_clip_effect(db_path: Path, fx_id: int, params: dict,
                       enabled: bool) -> None:
    with get_db(db_path) as con:
        con.execute(
            "UPDATE clip_effects SET params=?, enabled=? WHERE id=?",
            (json.dumps(params), int(enabled), fx_id),
        )


def delete_clip_effect(db_path: Path, fx_id: int) -> None:
    with get_db(db_path) as con:
        con.execute("DELETE FROM clip_effects WHERE id=?", (fx_id,))


# ── music_assignments ──────────────────────────────────────────────────────────

def get_music_assignments(db_path: Path, part: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM music_assignments WHERE part=? ORDER BY position",
            (part,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def upsert_music_assignment(db_path: Path, part: int, role: str,
                             track_filename: str, artist: str | None,
                             title: str | None, bpm: float | None,
                             duration_s: float | None, position: int,
                             transition_in: dict | None = None,
                             transition_out: dict | None = None,
                             chain_score: float = 0.0) -> None:
    with get_db(db_path) as con:
        con.execute(
            """INSERT INTO music_assignments
               (part, role, track_filename, artist, title, bpm, duration_s,
                transition_in, transition_out, chain_score, position)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(part, role) DO UPDATE SET
                 track_filename=excluded.track_filename,
                 artist=excluded.artist, title=excluded.title,
                 bpm=excluded.bpm, duration_s=excluded.duration_s,
                 transition_in=excluded.transition_in,
                 transition_out=excluded.transition_out,
                 chain_score=excluded.chain_score,
                 position=excluded.position""",
            (part, role, track_filename, artist, title, bpm, duration_s,
             json.dumps(transition_in or {}), json.dumps(transition_out or {}),
             chain_score, position),
        )


def delete_music_assignment(db_path: Path, part: int, role: str) -> None:
    with get_db(db_path) as con:
        con.execute(
            "DELETE FROM music_assignments WHERE part=? AND role=?",
            (part, role),
        )


# ── audio_fx ──────────────────────────────────────────────────────────────────

def get_audio_fx(db_path: Path, part: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM audio_fx WHERE part=? ORDER BY id", (part,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_audio_fx(db_path: Path, fx_id: int, params: dict,
                    enabled: bool) -> None:
    with get_db(db_path) as con:
        con.execute(
            "UPDATE audio_fx SET params=?, enabled=? WHERE id=?",
            (json.dumps(params), int(enabled), fx_id),
        )
