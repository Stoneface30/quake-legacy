from pathlib import Path

from fastapi.testclient import TestClient

from creative_suite.app import create_app


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    return TestClient(create_app())


def test_create_and_list(tmp_path: Path, monkeypatch) -> None:
    c = _client(tmp_path, monkeypatch)
    body = {
        "part": 4, "mp4_time": 17.5,
        "description": "test", "avi_effect": "slowmo",
        "dream_effect": "killcam", "tags": ["peak"],
    }
    r = c.post("/api/annotations", json=body)
    assert r.status_code == 200
    ann_id = r.json()["id"]
    lst = c.get("/api/annotations?part=4").json()
    assert len(lst) == 1 and lst[0]["id"] == ann_id


def test_patch_and_delete(tmp_path: Path, monkeypatch) -> None:
    c = _client(tmp_path, monkeypatch)
    r = c.post("/api/annotations", json={
        "part": 4, "mp4_time": 1.0, "description": "x",
        "avi_effect": None, "dream_effect": None, "tags": [],
    })
    ann_id = r.json()["id"]
    c.patch(f"/api/annotations/{ann_id}", json={"description": "y"})
    assert c.get("/api/annotations?part=4").json()[0]["description"] == "y"
    c.delete(f"/api/annotations/{ann_id}")
    assert c.get("/api/annotations?part=4").json() == []


def test_health_still_works(tmp_path: Path, monkeypatch) -> None:
    c = _client(tmp_path, monkeypatch)
    assert c.get("/health").json() == {"ok": True, "version": "0.1.0"}


def test_list_parts_does_not_crash(tmp_path: Path, monkeypatch) -> None:
    c = _client(tmp_path, monkeypatch)
    r = c.get("/api/parts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
