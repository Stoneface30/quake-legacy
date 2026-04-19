# creative_suite/tests/test_api_phase1.py
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from creative_suite.config import Config
from creative_suite.db.migrate import migrate


def test_migration_creates_render_versions_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    con = sqlite3.connect(str(cfg.db_path))
    try:
        cur = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='render_versions'"
        )
        assert cur.fetchone() is not None
        cur = con.execute("PRAGMA table_info(render_versions)")
        cols = {r[1] for r in cur.fetchall()}
        for required in (
            "id", "part", "tag", "notes", "flow_plan_git_sha", "flow_plan_path",
            "mp4_path", "body_dur_s", "level_pass", "level_delta_lu",
            "max_drift_ms", "render_time_s", "parent_version_id", "mode", "created_at",
        ):
            assert required in cols, f"missing column {required}"
    finally:
        con.close()
