"""demo_v2 provenance database + output scaffold (charter §2, §28).

Owns creative_suite/database/demo_v2.db and the output/demo_v2/ tree.
Never touches frags_rebuilt.db or the frozen V1 outputs.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "demo_v2.db"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"

SCHEMA = """
CREATE TABLE IF NOT EXISTS generated_clips (
    generated_clip_id INTEGER PRIMARY KEY,
    demo_name TEXT NOT NULL,
    canonical_demo_hash TEXT,
    server_time_ms INTEGER NOT NULL,
    round INTEGER,
    capture_start_ms INTEGER NOT NULL,
    capture_end_ms INTEGER NOT NULL,
    frag_offsets_ms TEXT NOT NULL,
    recorder_client INTEGER,
    weapon TEXT,
    tags TEXT,
    rank_score REAL,
    class TEXT NOT NULL,
    clutch_context TEXT,
    source_size_bytes INTEGER,
    source_quality TEXT,
    avi_path TEXT,
    qa_status TEXT NOT NULL DEFAULT 'PENDING',
    used_in_part TEXT,
    promotion_status TEXT NOT NULL DEFAULT 'CANDIDATE',
    promotion_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_gc_demo ON generated_clips(demo_name);
CREATE INDEX IF NOT EXISTS idx_gc_class ON generated_clips(class);
CREATE INDEX IF NOT EXISTS idx_gc_status ON generated_clips(promotion_status);
"""

# Columns added after the v1 schema — applied via ALTER TABLE migration.
_MIGRATION_COLUMNS = {
    "map": "TEXT",
    "match_group": "INTEGER",
    "tier": "TEXT",                      # S | A | B
    "alt_angle_worthy": "INTEGER DEFAULT 0",
    "victims": "TEXT",                   # JSON list, one per frag offset
    "mods": "TEXT",                      # JSON list of MOD_* ints, per offset
    "primary_frag_offset_ms": "INTEGER",
    "recorder_name": "TEXT",
    "clan": "TEXT",
    "capture_cmd": "TEXT",               # full wolfcam invocation + cfg
    "wolfcam_version": "TEXT",
    "semantic_qa": "TEXT",               # JSON list of flags, [] when clean
    "capture_profile_id": "TEXT",        # frozen master profile hash
}

_COLUMNS = {
    "demo_name", "canonical_demo_hash", "server_time_ms", "round",
    "capture_start_ms", "capture_end_ms", "frag_offsets_ms",
    "recorder_client", "weapon", "tags", "rank_score", "class",
    "clutch_context", "source_size_bytes", "source_quality", "avi_path",
    "qa_status", "used_in_part", "promotion_status", "promotion_reason",
    *_MIGRATION_COLUMNS,
}


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open (creating if needed) the demo_v2 database with schema applied."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    existing = {r[1] for r in conn.execute("PRAGMA table_info(generated_clips)")}
    for col, decl in _MIGRATION_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE generated_clips ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


def insert_candidate(conn: sqlite3.Connection, row: dict) -> int:
    """Insert one candidate clip row; returns generated_clip_id."""
    unknown = set(row) - _COLUMNS
    if unknown:
        raise ValueError(f"unknown generated_clips columns: {sorted(unknown)}")
    cols = list(row)
    sql = (
        f"INSERT INTO generated_clips ({', '.join(cols)}) "
        f"VALUES ({', '.join('?' for _ in cols)})"
    )
    cur = conn.execute(sql, [row[c] for c in cols])
    conn.commit()
    return cur.lastrowid


def ensure_output_tree(output_root: Path | str | None = None) -> Path:
    """Create output/demo_v2/{review,generated_clips,parts}; returns demo_v2 root."""
    base = Path(output_root) if output_root else DEFAULT_OUTPUT_ROOT
    root = base / "demo_v2"
    for sub in ("review", "generated_clips", "parts"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
