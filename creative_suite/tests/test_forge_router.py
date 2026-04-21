"""P3-T7 — /api/forge/* router tests.

All tests run against the full FastAPI app via TestClient.  The FORGE
endpoints are stubs; no wolfcamql.exe / q3mme.exe is required.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


@pytest.fixture
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    with TestClient(create_app()) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/forge/status
# ---------------------------------------------------------------------------

def test_status_returns_200(client: TestClient) -> None:
    r = client.get("/api/forge/status")
    assert r.status_code == 200, r.text


def test_status_has_required_fields(client: TestClient) -> None:
    body = client.get("/api/forge/status").json()
    for field in ("forge_version", "wolfcam_available", "capabilities", "ready"):
        assert field in body, f"missing field: {field}"


def test_status_ready_is_bool(client: TestClient) -> None:
    body = client.get("/api/forge/status").json()
    assert isinstance(body["ready"], bool)


def test_status_capabilities_is_list(client: TestClient) -> None:
    body = client.get("/api/forge/status").json()
    assert isinstance(body["capabilities"], list)


def test_status_forge_version_is_string(client: TestClient) -> None:
    body = client.get("/api/forge/status").json()
    assert isinstance(body["forge_version"], str)
    assert len(body["forge_version"]) > 0


# ---------------------------------------------------------------------------
# POST /api/forge/intro
# ---------------------------------------------------------------------------

def test_intro_stub_returns_queued(client: TestClient) -> None:
    r = client.post("/api/forge/intro", json={"part": 4})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "queued"


def test_intro_has_job_id(client: TestClient) -> None:
    r = client.post("/api/forge/intro", json={"part": 4})
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert isinstance(body["job_id"], str)
    assert len(body["job_id"]) > 0


def test_intro_job_id_contains_part(client: TestClient) -> None:
    r = client.post("/api/forge/intro", json={"part": 7})
    assert r.status_code == 200
    assert "7" in r.json()["job_id"]


def test_intro_echoes_part_and_style(client: TestClient) -> None:
    r = client.post(
        "/api/forge/intro",
        json={"part": 5, "style": "cinematic", "duration_s": 10.0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["part"] == 5
    assert body["style"] == "cinematic"
    assert body["duration_s"] == 10.0


def test_intro_defaults_style_and_duration(client: TestClient) -> None:
    r = client.post("/api/forge/intro", json={"part": 4})
    assert r.status_code == 200
    body = r.json()
    assert body["style"] == "default"
    assert body["duration_s"] == 8.0


def test_intro_request_validation(client: TestClient) -> None:
    """Missing required `part` field → 422 Unprocessable Entity."""
    r = client.post("/api/forge/intro", json={"style": "default"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/forge/demo/extract
# ---------------------------------------------------------------------------

def test_extract_stub_returns_queued(client: TestClient) -> None:
    r = client.post(
        "/api/forge/demo/extract",
        json={"demo_path": "demos/test.dm_73"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "queued"


def test_extract_has_job_id(client: TestClient) -> None:
    r = client.post(
        "/api/forge/demo/extract",
        json={"demo_path": "demos/test.dm_73"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert isinstance(body["job_id"], str)
    assert len(body["job_id"]) > 0


def test_extract_echoes_request_fields(client: TestClient) -> None:
    r = client.post(
        "/api/forge/demo/extract",
        json={
            "demo_path": "demos/ca_test.dm_73",
            "extract_frags": True,
            "extract_positions": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["demo_path"] == "demos/ca_test.dm_73"
    assert body["extract_frags"] is True
    assert body["extract_positions"] is True


def test_extract_defaults_extract_frags_true(client: TestClient) -> None:
    r = client.post(
        "/api/forge/demo/extract",
        json={"demo_path": "demos/test.dm_73"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["extract_frags"] is True
    assert body["extract_positions"] is False


def test_extract_missing_demo_path_returns_422(client: TestClient) -> None:
    r = client.post("/api/forge/demo/extract", json={"extract_frags": True})
    assert r.status_code == 422
