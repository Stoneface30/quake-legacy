from pathlib import Path

from fastapi.testclient import TestClient

from creative_suite.app import create_app


def test_health(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "version": "0.1.0"}
