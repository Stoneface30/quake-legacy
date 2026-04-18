import sqlite3
from pathlib import Path

from creative_suite.config import Config
from creative_suite.db.migrate import migrate


def test_migrate_creates_all_tables(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    con = sqlite3.connect(cfg.db_path)
    try:
        names = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert {"assets", "variants", "pack_builds", "annotations", "clip_durations"} <= names
        mode = con.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        con.close()


def test_migrate_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    migrate(cfg)  # second call must not raise
