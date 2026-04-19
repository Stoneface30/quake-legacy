# creative_suite/tests/test_api_phase1.py
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app
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


def _seed_output(dir_: Path, part: int) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    names = [
        "flow_plan", "music_structure", "music_plan", "beats",
        "sync_audit", "levels", "event_diversity",
    ]
    for n in names:
        (dir_ / f"part{part:02d}_{n}.json").write_text(
            json.dumps({"name": n, "part": part}), encoding="utf-8"
        )


def test_artifacts_bundle_returns_all_seven_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "output"
    _seed_output(out, 4)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    with TestClient(create_app()) as c:
        r = c.get("/api/phase1/parts/4/artifacts")
        assert r.status_code == 200
        body = r.json()
        for k in (
            "flow_plan", "music_structure", "music_plan", "beats",
            "sync_audit", "levels", "event_diversity",
        ):
            assert k in body, f"missing key {k}"
            assert body[k]["part"] == 4


def test_artifacts_returns_null_for_missing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "output"
    out.mkdir()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    with TestClient(create_app()) as c:
        r = c.get("/api/phase1/parts/8/artifacts")
        assert r.status_code == 200
        body = r.json()
        assert body["flow_plan"] is None
        assert body["beats"] is None


def test_list_parts_returns_parts_with_flow_plans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "output"
    _seed_output(out, 4)
    _seed_output(out, 5)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    with TestClient(create_app()) as c:
        r = c.get("/api/phase1/parts")
        assert r.status_code == 200
        parts = r.json()
        nums = sorted(p["part"] for p in parts)
        assert nums == [4, 5]
        assert all(p["has_flow_plan"] for p in parts)
