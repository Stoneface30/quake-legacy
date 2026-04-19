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


def test_versions_list_returns_db_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "output"
    _seed_output(out, 4)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    with TestClient(create_app()) as c:
        import sqlite3
        from creative_suite.config import Config
        cfg = Config()
        con = sqlite3.connect(str(cfg.db_path))
        con.execute(
            "INSERT INTO render_versions "
            "(part, tag, notes, flow_plan_git_sha, flow_plan_path, mp4_path, "
            "level_pass, level_delta_lu, max_drift_ms, mode) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (4, "v10.4-manual", "first real", "a" * 40,
             "output/part04_flow_plan.json", "output/Part4_v10.4_manual.mp4",
             1, -21.0, 7.0, "ship"),
        )
        con.commit()
        con.close()

        r = c.get("/api/phase1/parts/4/versions")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 1
        assert rows[0]["tag"] == "v10.4-manual"
        assert rows[0]["level_pass"] == 1
        assert rows[0]["mp4_path"].endswith(".mp4")


def test_put_flow_plan_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess as sp
    out = tmp_path / "output"
    out.mkdir()
    sp.run(["git", "init", "-q", str(out)], check=True)
    sp.run(["git", "-C", str(out), "config", "user.email", "t@t"], check=True)
    sp.run(["git", "-C", str(out), "config", "user.name", "t"], check=True)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    with TestClient(create_app()) as c:
        r = c.put("/api/phase1/parts/4/flow-plan",
                  json={"clips": [{"chunk": "chunk_0001.mp4"}], "seams": []})
        assert r.status_code == 200
        body = r.json()
        assert body["saved"] is True
        assert (out / "part04_flow_plan.json").exists()


def test_rebuild_returns_job_id_and_second_submit_409(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess as sp
    out = tmp_path / "output"
    out.mkdir()
    sp.run(["git", "init", "-q", str(out)], check=True)
    sp.run(["git", "-C", str(out), "config", "user.email", "t@t"], check=True)
    sp.run(["git", "-C", str(out), "config", "user.name", "t"], check=True)
    (out / "part04_flow_plan.json").write_text('{"clips":[]}', encoding="utf-8")
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    monkeypatch.setenv("CS_REBUILD_MOCK", "1")
    with TestClient(create_app()) as c:
        r = c.post("/api/phase1/parts/4/rebuild",
                   json={"tag": "v-test", "notes": "", "mode": "ship"})
        assert r.status_code == 200
        jid = r.json()["job_id"]
        # Immediately try again — should be 409 (mock still running in queue)
        r2 = c.post("/api/phase1/parts/4/rebuild",
                    json={"tag": "v-test-2", "notes": "", "mode": "ship"})
        assert r2.status_code == 409
