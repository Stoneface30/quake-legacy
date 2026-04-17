from __future__ import annotations

import sqlite3
from pathlib import Path

from creative_suite.config import Config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def migrate(cfg: Config) -> None:
    cfg.ensure_dirs()
    con = sqlite3.connect(cfg.db_path)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        con.commit()
    finally:
        con.close()


def connect(cfg: Config) -> sqlite3.Connection:
    con = sqlite3.connect(cfg.db_path, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con
