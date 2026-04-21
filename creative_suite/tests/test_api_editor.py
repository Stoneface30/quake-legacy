"""Editor API integration tests (FastAPI TestClient)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


def _seed_flow_plan(out: Path, part: int, n_clips: int = 3) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fp = out / f"part{part:02d}_flow_plan.json"
    fp.write_text(json.dumps({
        "part": part,
        "clips": [
            {
                "chunk": f"chunk_{i:04d}.mp4",
                "tier": "T2",
                "section_role": "build",
                "duration": 3.0 + i * 0.5,
            }
            for i in range(n_clips)
        ],
    }), encoding="utf-8")


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    out = tmp_path / "output"
    out.mkdir()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(out))
    return TestClient(create_app()), out


def test_get_state_hydrates_from_flow_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 2)
    with client as c:
        r = c.get("/api/editor/state/4")
        assert r.status_code == 200
        body = r.json()
        assert body["part"] == 4
        assert body["version"] == 1
        assert len(body["clips"]) == 2
        assert body["clips"][0]["chunk"] == "chunk_0000.mp4"
        assert body["clips"][0]["in_s"] == 0.0
        assert body["clips"][0]["out_s"] == 3.0


def test_patch_state_sets_removed_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 5, 3)
    with client as c:
        r = c.patch("/api/editor/state/5", json={"ops": [
            {"op": "replace", "path": "/clips/1/removed", "value": True},
        ]})
        assert r.status_code == 200
        assert r.json()["clips"][1]["removed"] is True

        # Confirm persisted to disk + visible on next GET
        sp = out / "part05_editor_state.json"
        assert sp.exists()
        r2 = c.get("/api/editor/state/5")
        assert r2.json()["clips"][1]["removed"] is True


def test_patch_invalid_returns_400(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 1)
    with client as c:
        r = c.patch("/api/editor/state/4", json={"ops": [
            {"op": "replace", "path": "/clips/99/removed", "value": True},
        ]})
        assert r.status_code == 400


def test_put_state_replaces_whole_doc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 6, 2)
    with client as c:
        r = c.put("/api/editor/state/6", json={"state": {
            "part": 6,
            "version": 1,
            "clips": [{
                "chunk": "new.mp4", "tier": "T1", "section_role": None,
                "duration": 1.0, "in_s": 0.0, "out_s": 1.0, "removed": False,
                "slow": None, "slow_window_s": None, "notes": "from PUT",
            }],
        }})
        assert r.status_code == 200
        body = r.json()
        assert len(body["clips"]) == 1
        assert body["clips"][0]["chunk"] == "new.mp4"


def test_put_state_rejects_part_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    with client as c:
        r = c.put("/api/editor/state/4", json={"state": {
            "part": 7,
            "version": 1,
            "clips": [],
        }})
        assert r.status_code == 400


def test_chunks_list_returns_rows_with_exists_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 2)
    (out / "_part04_v6_body_chunks").mkdir(parents=True)
    (out / "_part04_v6_body_chunks" / "chunk_0000.mp4").write_bytes(b"A" * 16)
    with client as c:
        r = c.get("/api/editor/chunks/4")
        body = r.json()
        assert body["count"] == 2
        rows = {c["chunk"]: c for c in body["chunks"]}
        assert rows["chunk_0000.mp4"]["exists"] is True
        assert rows["chunk_0000.mp4"]["size"] == 16
        assert rows["chunk_0001.mp4"]["exists"] is False


def test_get_otio_writes_file_and_downloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 2)
    with client as c:
        r = c.get("/api/editor/otio/4")
        assert r.status_code == 200
        # OTIO files are JSON
        data = json.loads(r.content)
        assert data.get("OTIO_SCHEMA", "").startswith("Timeline")
    assert (out / "part04.otio").exists()


def test_proxy_uses_mock_and_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 5, 1)
    chunks = out / "_part05_v6_body_chunks"
    chunks.mkdir()
    (chunks / "chunk_0000.mp4").write_bytes(b"fake source")
    monkeypatch.setenv("CS_FFMPEG_MOCK", "1")
    with client as c:
        r = c.get("/api/editor/proxy/5/chunk_0000.mp4")
        assert r.status_code == 200
        assert r.content.startswith(b"PROXY")
    assert (out / "_proxies" / "part05" / "chunk_0000.proxy.mp4").exists()


def test_proxy_404_when_source_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    with client as c:
        r = c.get("/api/editor/proxy/9/nope.mp4")
        assert r.status_code == 404


def test_render_preview_projects_state_to_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 3)
    monkeypatch.setenv("CS_REBUILD_MOCK", "1")
    with client as c:
        # Mark clip 1 removed + add a slow-mo to clip 2 via PATCH first
        c.patch("/api/editor/state/4", json={"ops": [
            {"op": "replace", "path": "/clips/1/removed", "value": True},
            {"op": "replace", "path": "/clips/2/slow", "value": 0.5},
        ]})
        r = c.post("/api/editor/render/4?mode=preview")
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == "preview"
        assert body["n_clips"] == 3
        assert body["n_removed"] == 1
        # Overrides file should now exist with removed=true for clip_0001
        assert (out / "part04_overrides.txt").exists()
        text = (out / "part04_overrides.txt").read_text(encoding="utf-8")
        assert "chunk_0001.mp4" in text
        assert "removed=true" in text
        assert "slow=0.5" in text


def test_render_rejects_invalid_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out = _client(tmp_path, monkeypatch)
    _seed_flow_plan(out, 4, 1)
    with client as c:
        r = c.post("/api/editor/render/4?mode=wat")
        assert r.status_code == 400
