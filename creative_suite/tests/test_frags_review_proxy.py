"""Review proxies + editorial state for the /frags control room.

Covers: proxy state machine under CS_PROXY_MOCK=1 (queue -> READY, cache-hit,
FAILED path), review PUT/GET roundtrip, and that recognition DBs are never
opened writable.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import frags as frags_mod
from creative_suite.app import create_app
from creative_suite.engine import review_proxy


def _build_frag_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE recognized_frags (
            id INTEGER PRIMARY KEY, demo_name TEXT, server_time_ms INTEGER,
            round INTEGER, weapon_name TEXT, victim_client INTEGER,
            classes TEXT, attributes TEXT, highlight_score REAL DEFAULT 0,
            reasons TEXT, recognition_version INTEGER DEFAULT 2
        )"""
    )
    conn.execute(
        "INSERT INTO recognized_frags (id, demo_name, server_time_ms, round,"
        " weapon_name, classes, attributes, highlight_score, reasons)"
        " VALUES (1, 'demoA.dm_73', 100000, 1, 'ROCKET',"
        " '[{\"name\": \"AIRSHOT\"}]',"
        " '{\"mode_pool\": \"MAIN_CA\"}', 12.0, '[\"+ airshot\"]')"
    )
    conn.execute(
        "INSERT INTO recognized_frags (id, demo_name, server_time_ms, round,"
        " weapon_name, classes, attributes, highlight_score, reasons)"
        " VALUES (2, 'ghost.dm_73', 50000, 1, 'RAILGUN', '[]',"
        " '{\"mode_pool\": \"MAIN_CA\"}', 3.0, '[]')"
    )
    conn.commit()
    conn.close()


def _build_demo_v2_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE generated_clips (
            generated_clip_id INTEGER PRIMARY KEY, demo_name TEXT,
            server_time_ms INTEGER, capture_start_ms INTEGER,
            capture_end_ms INTEGER, frag_offsets_ms TEXT, tier TEXT,
            class TEXT, qa_status TEXT, avi_path TEXT, rank_score REAL,
            map TEXT, victims TEXT, mods TEXT
        )"""
    )
    conn.commit()
    conn.close()


def _build_frags_rebuilt_db(path: Path, demo_file: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE demos (demo_id INTEGER PRIMARY KEY, content_hash TEXT,"
        " path TEXT, name TEXT)"
    )
    conn.execute(
        "INSERT INTO demos (demo_id, content_hash, path, name)"
        " VALUES (1, 'hash_demoA', ?, 'demoA.dm_73')",
        (str(demo_file),),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    rebuilt_db = tmp_path / "frags_rebuilt.db"
    demo_file = tmp_path / "demoA.dm_73"
    demo_file.write_bytes(b"fake demo bytes")
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db)
    _build_frags_rebuilt_db(rebuilt_db, demo_file)

    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    frags_mod._classes_cache.clear()
    monkeypatch.setattr(review_proxy, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(review_proxy, "FRAGS_REBUILT_DB_PATH", rebuilt_db)
    monkeypatch.setattr(review_proxy, "PROXY_DIR", tmp_path / "review_proxies")
    monkeypatch.setattr(review_proxy, "LOCK_PATH", tmp_path / "_capture.lock")
    monkeypatch.setenv("CS_PROXY_MOCK", "1")
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


def _wait_state(client: TestClient, frag_id: int, target: str,
                timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        last = client.get(f"/api/frags/{frag_id}/proxy").json()
        if last["state"] == target:
            return last
        if last["state"] == "FAILED" and target != "FAILED":
            raise AssertionError(f"proxy FAILED: {last.get('error')}")
        time.sleep(0.2)
    raise AssertionError(f"timeout waiting for {target}, last={last}")


def test_proxy_missing_then_queue_then_ready(client: TestClient) -> None:
    assert client.get("/api/frags/1/proxy").json()["state"] == "MISSING"
    # video 404s while no proxy exists
    r = client.get("/api/frags/1/proxy/video")
    assert r.status_code == 404
    assert "reason" in r.json()

    r = client.post("/api/frags/1/proxy")
    assert r.status_code == 200
    assert r.json()["state"] in ("QUEUED", "GENERATING", "READY")
    st = _wait_state(client, 1, "READY")
    assert st["url"] == "/api/frags/1/proxy/video"
    # window = server_time - 4000 .. + 3000 (no master row)
    assert st["start_ms"] == 96000
    assert st["end_ms"] == 103000

    v = client.get("/api/frags/1/proxy/video")
    assert v.status_code == 200
    assert v.headers["content-type"].startswith("video/mp4")
    assert v.content[4:8] == b"ftyp"  # mp4 container magic


def test_proxy_cache_hit_never_regenerates(client: TestClient) -> None:
    client.post("/api/frags/1/proxy")
    st = _wait_state(client, 1, "READY")
    assert st["state"] == "READY"
    mp4 = Path(review_proxy.get_state(1)["mp4_path"])
    mtime = mp4.stat().st_mtime_ns
    # second POST returns READY immediately, file untouched
    r = client.post("/api/frags/1/proxy")
    assert r.json()["state"] == "READY"
    assert mp4.stat().st_mtime_ns == mtime


def test_proxy_failed_when_demo_unknown(client: TestClient) -> None:
    # frag 2's demo is not in frags_rebuilt.db
    r = client.post("/api/frags/2/proxy")
    assert r.status_code == 200
    st = r.json()
    assert st["state"] in ("FAILED", "MISSING")
    # request_proxy returns FAILED synchronously but persists nothing
    direct = review_proxy.request_proxy(2, "ghost.dm_73", 0, 1000)
    assert direct["state"] == "FAILED"
    assert "not found" in direct["error"]


def test_proxy_failed_on_generation_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(job: dict) -> None:
        raise RuntimeError("synthetic ffmpeg explosion")

    monkeypatch.setattr(review_proxy, "_generate", boom)
    client.post("/api/frags/1/proxy")
    st = _wait_state(client, 1, "FAILED")
    assert "synthetic ffmpeg explosion" in st["error"]


def test_review_put_get_roundtrip(client: TestClient) -> None:
    r = client.get("/api/frags/1/review")
    assert r.status_code == 200
    assert r.json()["verdict"] is None

    r = client.put("/api/frags/1/review", json={"verdict": "LOVE"})
    assert r.status_code == 200
    assert r.json()["verdict"] == "LOVE"

    # partial update keeps prior fields
    r = client.put("/api/frags/1/review",
                   json={"user_tier": "S_PLUS", "notes": "opener candidate"})
    body = r.json()
    assert body["verdict"] == "LOVE"
    assert body["user_tier"] == "S_PLUS"
    assert body["notes"] == "opener candidate"

    r = client.get("/api/frags/1/review")
    assert r.json()["notes"] == "opener candidate"

    # invalid values rejected
    assert client.put("/api/frags/1/review", json={"verdict": "EPIC"}).status_code == 422
    r = client.put("/api/frags/1/review", json={"user_tier": "B"})
    assert r.status_code == 200
    assert r.json()["user_tier"] == "B"
    # unknown frag 404
    assert client.put("/api/frags/999/review", json={"verdict": "KEEP"}).status_code == 404

    # review surfaces in list rows
    items = client.get("/api/frags").json()["items"]
    row = next(it for it in items if it["id"] == 1)
    assert row["review"] == {"verdict": "LOVE", "user_tier": "B"}
    # detail carries review + proxy + window
    d = client.get("/api/frags/1").json()
    assert d["review"]["verdict"] == "LOVE"
    assert d["proxy"]["state"] in ("MISSING", "QUEUED", "GENERATING", "READY", "FAILED")
    assert d["window"] == {"start_ms": 96000, "end_ms": 103000}


def test_recognition_dbs_never_opened_writable(client: TestClient) -> None:
    # the router's connection helper must be read-only for both attached DBs
    conn = frags_mod._connect()
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO recognized_frags (id) VALUES (999)")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO dv.generated_clips (generated_clip_id, demo_name,"
                " server_time_ms, capture_start_ms, capture_end_ms)"
                " VALUES (99, 'x', 0, 0, 1)"
            )
    finally:
        conn.close()
    # review_proxy's demo lookup is read-only too: source inspection guard
    import inspect
    src = inspect.getsource(review_proxy.demo_source)
    assert "mode=ro" in src


def test_capture_lock_requeues(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A live foreign lock defers the job; releasing it lets it finish."""
    import os
    monkeypatch.setattr(review_proxy, "_LOCK_RETRY_S", 0.1)
    lock = review_proxy.LOCK_PATH
    lock.parent.mkdir(parents=True, exist_ok=True)
    # a live pid that is not us: use our parent-ish trick — spoof with our own
    # pid is skipped (same-pid locks are treated as ours), so use pid of the
    # current process's ppid if alive, else fall back to holding via any live pid.
    other = os.getppid()
    try:
        os.kill(other, 0)
    except OSError:
        pytest.skip("no live foreign pid available")
    lock.write_text(str(other))
    client.post("/api/frags/1/proxy")
    time.sleep(0.6)
    st = client.get("/api/frags/1/proxy").json()
    assert st["state"] == "QUEUED"  # deferred, not failed
    lock.unlink()
    _wait_state(client, 1, "READY")


def test_proxy_video_supports_http_range(client: TestClient) -> None:
    client.post("/api/frags/1/proxy")
    _wait_state(client, 1, "READY")
    r = client.get(
        "/api/frags/1/proxy/video",
        headers={"Range": "bytes=0-31"},
    )
    assert r.status_code == 206
    assert r.headers["accept-ranges"] == "bytes"
    assert r.headers["content-range"].startswith("bytes 0-31/")
    assert len(r.content) == 32
