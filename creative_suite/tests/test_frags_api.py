"""API contract tests for /api/frags (frag browser, read-only)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import frags as frags_mod
from creative_suite.app import create_app


def _build_frag_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE recognized_frags (
            id INTEGER PRIMARY KEY,
            demo_name TEXT, content_hash TEXT, server_time_ms INTEGER,
            round INTEGER, mod INTEGER, weapon_name TEXT, victim_client INTEGER,
            classes TEXT, attributes TEXT,
            highlight_score REAL DEFAULT 0, reasons TEXT,
            recognition_version INTEGER DEFAULT 2,
            clutch_score REAL DEFAULT 0, drama_score REAL DEFAULT 0
        )"""
    )
    rows = [
        # id 1: MAIN_CA rocket, has a master (falls inside capture window)
        (
            1, "demoA.dm_73", 100_000, 1, "ROCKET", 4,
            json.dumps([{"name": "AIRSHOT", "confidence": "CONFIRMED", "detail": "air"}]),
            json.dumps({"mode_pool": "MAIN_CA", "scene_score": 7.5}),
            12.0, json.dumps(["+ airshot (+4)"]),
        ),
        # id 2: MAIN_CA rail, no master
        (
            2, "demoA.dm_73", 500_000, 2, "RAILGUN", 3,
            json.dumps([{"name": "FLICK", "confidence": "LIKELY", "detail": ""}]),
            json.dumps({"mode_pool": "MAIN_CA", "scene_score": 2.0}),
            5.0, json.dumps(["+ flick (+2)"]),
        ),
        # id 3: SIDE_DUEL lightning — excluded by default mode_pool filter
        (
            3, "demoB.dm_73", 200_000, 1, "LIGHTNING", 2,
            json.dumps([{"name": "LG_TRACK", "confidence": "CONFIRMED", "detail": ""}]),
            json.dumps({"mode_pool": "SIDE_DUEL"}),
            9.0, json.dumps(["+ lg (+3)"]),
        ),
    ]
    conn.executemany(
        "INSERT INTO recognized_frags (id, demo_name, server_time_ms, round,"
        " weapon_name, victim_client, classes, attributes, highlight_score,"
        " reasons) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


def _build_demo_v2_db(path: Path, avi_path: str | None) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE generated_clips (
            generated_clip_id INTEGER PRIMARY KEY,
            demo_name TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
            capture_start_ms INTEGER NOT NULL, capture_end_ms INTEGER NOT NULL,
            frag_offsets_ms TEXT, tier TEXT, class TEXT,
            qa_status TEXT DEFAULT 'PENDING', avi_path TEXT,
            rank_score REAL, map TEXT, victims TEXT, mods TEXT
        )"""
    )
    conn.execute(
        "INSERT INTO generated_clips (generated_clip_id, demo_name,"
        " server_time_ms, capture_start_ms, capture_end_ms, frag_offsets_ms,"
        " tier, class, qa_status, avi_path, rank_score, map, victims, mods)"
        " VALUES (1, 'demoA.dm_73', 100000, 90000, 120000, '[10000]',"
        " 'S', 'FRAG_MASTER', 'PENDING', ?, 42.0, 'campgrounds',"
        " '[\"v1\"]', '[10]')",
        (avi_path,),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db, avi_path=None)
    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    frags_mod._classes_cache.clear()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


def test_list_default_filters_main_ca_sorted_by_score(client: TestClient) -> None:
    r = client.get("/api/frags")
    assert r.status_code == 200
    data = r.json()
    # id 3 is SIDE_DUEL — excluded by default mode_pool=MAIN_CA
    assert data["total"] == 2
    ids = [it["id"] for it in data["items"]]
    assert ids == [1, 2]  # score desc: 12.0 then 5.0
    top = data["items"][0]
    assert top["weapon_name"] == "ROCKET"
    assert top["scene_score"] == 7.5
    assert top["classes"] == ["AIRSHOT"]
    assert top["master"] is not None
    assert top["master"]["tier"] == "S"
    assert top["master"]["qa_status"] == "PENDING"
    assert data["items"][1]["master"] is None


def test_list_filters(client: TestClient) -> None:
    # mode_pool=all surfaces the duel frag too
    assert client.get("/api/frags", params={"mode_pool": "all"}).json()["total"] == 3
    # min_score
    data = client.get("/api/frags", params={"min_score": 10}).json()
    assert [it["id"] for it in data["items"]] == [1]
    # weapon
    data = client.get("/api/frags", params={"weapon": "RAILGUN"}).json()
    assert [it["id"] for it in data["items"]] == [2]
    # class substring
    data = client.get("/api/frags", params={"class": "FLICK"}).json()
    assert [it["id"] for it in data["items"]] == [2]
    # demo substring
    data = client.get("/api/frags", params={"demo": "demoB", "mode_pool": "all"}).json()
    assert [it["id"] for it in data["items"]] == [3]
    # has_master
    data = client.get("/api/frags", params={"has_master": "true"}).json()
    assert [it["id"] for it in data["items"]] == [1]
    data = client.get("/api/frags", params={"has_master": "false"}).json()
    assert [it["id"] for it in data["items"]] == [2]
    # sort by time
    data = client.get("/api/frags", params={"sort": "time"}).json()
    assert [it["id"] for it in data["items"]] == [1, 2]
    # pagination
    data = client.get("/api/frags", params={"limit": 1, "offset": 1}).json()
    assert data["total"] == 2
    assert [it["id"] for it in data["items"]] == [2]


def test_detail_200_with_master(client: TestClient) -> None:
    r = client.get("/api/frags/1")
    assert r.status_code == 200
    d = r.json()
    assert d["demo_name"] == "demoA.dm_73"
    assert d["classes"][0]["name"] == "AIRSHOT"
    assert d["attributes"]["mode_pool"] == "MAIN_CA"
    assert d["reasons"] == ["+ airshot (+4)"]
    assert d["master"]["generated_clip_id"] == 1
    assert d["master"]["avi_on_disk"] is False


def test_detail_404(client: TestClient) -> None:
    assert client.get("/api/frags/999").status_code == 404


def test_video_404_when_no_master(client: TestClient) -> None:
    r = client.get("/api/frags/2/video")
    assert r.status_code == 404
    assert "reason" in r.json()


def test_video_404_when_avi_missing_on_disk(client: TestClient) -> None:
    # frag 1 has a master row but avi_path is NULL
    r = client.get("/api/frags/1/video")
    assert r.status_code == 404
    assert "reason" in r.json()


def test_video_serves_avi_when_on_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    avi = tmp_path / "clip_0001.avi"
    avi.write_bytes(b"RIFFxxxxAVI fake")
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db, avi_path=str(avi))
    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    frags_mod._classes_cache.clear()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    client = TestClient(create_app())
    r = client.get("/api/frags/1/video")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("video/x-msvideo")
    assert r.content == b"RIFFxxxxAVI fake"


def test_classes_endpoint(client: TestClient) -> None:
    r = client.get("/api/frags/classes")
    assert r.status_code == 200
    names = {c["name"]: c["count"] for c in r.json()}
    assert names == {"AIRSHOT": 1, "FLICK": 1, "LG_TRACK": 1}


def test_frags_page_served(client: TestClient) -> None:
    r = client.get("/frags")
    assert r.status_code == 200
    assert b"FRAG CONTROL ROOM" in r.content
