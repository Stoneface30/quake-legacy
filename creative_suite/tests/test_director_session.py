"""Live director session tests (Path A — replay-runtime-feasibility.md).

Covers the engine module under CS_DIRECTOR_MOCK=1: launch -> poll -> stop ->
save_recipe, the single-live-session guard, and the router endpoints wired
into /frags. No real wolfcam window is ever spawned here.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import director as director_api
from creative_suite.api import frags as frags_mod
from creative_suite.app import create_app
from creative_suite.engine import director_session, review_proxy, shot_plan


@pytest.fixture(autouse=True)
def _clean_sessions(monkeypatch: pytest.MonkeyPatch):
    # module-level session/launch-context dicts must not leak across tests
    director_session._sessions.clear()
    director_api._LAUNCH_CONTEXT.clear()
    monkeypatch.setenv("CS_DIRECTOR_MOCK", "1")
    yield
    director_session._sessions.clear()
    director_api._LAUNCH_CONTEXT.clear()


@pytest.fixture()
def staging(tmp_path: Path) -> Path:
    return tmp_path / "director_staging"


@pytest.fixture()
def demo_file(tmp_path: Path) -> Path:
    p = tmp_path / "demoA.dm_73"
    p.write_bytes(b"fake demo bytes" * 100)
    return p


@pytest.fixture()
def cinematic_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "cinematic.db"
    monkeypatch.setattr(shot_plan, "DEFAULT_DB", db)
    return db


# ── engine-level ─────────────────────────────────────────────────────────────

def test_launch_creates_mock_session(staging: Path, demo_file: Path) -> None:
    result = director_session.launch_session(demo_file, 150000, fov=100.0,
                                              staging=staging)
    assert result["proc"] is None   # CS_DIRECTOR_MOCK never spawns wolfcam
    assert result["qconsole_path"].exists()
    sess = director_session.session_info(result["session_id"])
    assert sess["state"] == "FLYING"
    assert sess["fov"] == 100.0


def test_launch_writes_director_cfg(staging: Path, demo_file: Path) -> None:
    director_session.launch_session(demo_file, 150000, fov=95.5, staging=staging)
    cfg = (staging / "wolfcam-ql" / "cgamepostinit.cfg").read_text()
    assert "exec wolfcam_tr4sh_director_session.cfg" in cfg
    assert "cg_fov 95.50" in cfg
    assert f"seekservertime {150000 - director_session.wc.SEEK_SETTLE_MS}" in cfg
    assert "freecam" in cfg
    assert f"bind {director_session.DIRECTOR_KEYBIND} viewpos" in cfg


def test_poll_keyframes_parses_viewpos_lines(staging: Path, demo_file: Path) -> None:
    result = director_session.launch_session(demo_file, 150000, staging=staging)
    polled = director_session.poll_keyframes(result["session_id"])
    assert polled["count"] == 3
    kf = polled["keyframes"][0]
    assert set(kf) == {"t_ms", "pos", "angles", "fov"}
    assert isinstance(kf["t_ms"], int)
    assert len(kf["pos"]) == 3 and len(kf["angles"]) == 3
    assert kf["fov"] == director_session.DEFAULT_FOV


def test_poll_since_offset_only_returns_new_lines(staging: Path, demo_file: Path) -> None:
    result = director_session.launch_session(demo_file, 150000, staging=staging)
    sid = result["session_id"]
    first = director_session.poll_keyframes(sid)
    assert first["count"] == 3
    again = director_session.poll_keyframes(sid, since_byte_offset=first["next_offset"])
    assert again["count"] == 0
    assert again["next_offset"] == first["next_offset"]
    # simulate one more keypress landing in qconsole.log
    path = result["qconsole_path"]
    with open(path, "a", encoding="ascii") as f:
        f.write("(250.000000 260.000000 55.000000) -10.000000 105.000000 0.000000 152000\n")
    more = director_session.poll_keyframes(sid, since_byte_offset=first["next_offset"])
    assert more["count"] == 1
    assert more["keyframes"][0]["t_ms"] == 152000


def test_unknown_session_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        director_session.poll_keyframes("nonexistent")
    with pytest.raises(KeyError):
        director_session.stop_session("nonexistent")
    with pytest.raises(KeyError):
        director_session.save_recipe("nonexistent", "ab" * 32, {"t_ms": 0})


def test_second_launch_rejected_while_live(staging: Path, demo_file: Path) -> None:
    director_session.launch_session(demo_file, 150000, staging=staging)
    with pytest.raises(RuntimeError):
        director_session.launch_session(demo_file, 200000, staging=staging)


def test_launch_allowed_again_after_stop(staging: Path, demo_file: Path) -> None:
    first = director_session.launch_session(demo_file, 150000, staging=staging)
    director_session.stop_session(first["session_id"])
    second = director_session.launch_session(demo_file, 200000, staging=staging)
    assert second["session_id"] != first["session_id"]


def test_stop_session_keeps_qconsole_log(staging: Path, demo_file: Path) -> None:
    result = director_session.launch_session(demo_file, 150000, staging=staging)
    stopped = director_session.stop_session(result["session_id"])
    assert stopped["state"] == "STOPPED"
    assert result["qconsole_path"].exists()


def test_save_recipe_normalizes_keyframes_and_roundtrips(
    staging: Path, demo_file: Path, cinematic_db: Path,
) -> None:
    result = director_session.launch_session(demo_file, 150000, fov=110.0,
                                              staging=staging)
    sid = result["session_id"]
    plan_id = director_session.save_recipe(
        sid, demo_sha256="ab" * 32,
        event={"type": "director_session", "t_ms": 150000, "frag_id": 1},
        effect_ids=["speed_ramp_default"], asset_pack_ids=["zzz_photoreal_d35"])
    loaded = shot_plan.load_shot_plan(plan_id)
    assert loaded is not None
    assert loaded["camera"]["name"] == "freecam_recorded"
    assert loaded["camera"]["params"]["mode"] == "freecam_recorded"
    kfs = loaded["keyframes"]
    assert len(kfs) == 3
    assert kfs[0]["t_ms"] == 0   # normalized shot-relative
    assert kfs[1]["t_ms"] == 500
    assert kfs[2]["t_ms"] == 1000
    assert loaded["effect_ids"] == ["speed_ramp_default"]
    assert loaded["profile_id"]   # non-empty, from master_profile.profile_id()


def test_save_recipe_without_keyframes_raises(staging: Path, demo_file: Path,
                                              cinematic_db: Path) -> None:
    result = director_session.launch_session(demo_file, 150000, staging=staging)
    (result["qconsole_path"]).write_text("", encoding="ascii")  # wipe fake lines
    with pytest.raises(ValueError):
        director_session.save_recipe(result["session_id"], "ab" * 32,
                                     {"t_ms": 150000})


# ── router-level ─────────────────────────────────────────────────────────────

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
        " VALUES (1, 'demoA.dm_73', 150000, 1, 'ROCKET', '[]', '{}', 9.0, '[]')"
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


@pytest.fixture()
def client(tmp_path: Path, demo_file: Path, staging: Path, cinematic_db: Path,
          monkeypatch: pytest.MonkeyPatch) -> TestClient:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    rebuilt_db = tmp_path / "frags_rebuilt.db"
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db)
    _build_frags_rebuilt_db(rebuilt_db, demo_file)

    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    frags_mod._classes_cache.clear()
    monkeypatch.setattr(review_proxy, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(review_proxy, "FRAGS_REBUILT_DB_PATH", rebuilt_db)
    monkeypatch.setattr(director_session, "DIRECTOR_STAGING", staging)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


def test_router_full_flow(client: TestClient) -> None:
    r = client.post("/api/frags/1/director/launch", json={"fov": 105.0})
    assert r.status_code == 200
    data = r.json()
    session_id = data["session_id"]
    assert data["keybind"] == director_session.DIRECTOR_KEYBIND
    assert data["fov"] == 105.0

    r = client.get(f"/api/director/{session_id}/keyframes?since=0")
    assert r.status_code == 200
    kf_data = r.json()
    assert kf_data["count"] == 3

    r = client.post(f"/api/director/{session_id}/stop")
    assert r.status_code == 200
    assert r.json()["state"] == "STOPPED"

    r = client.post(f"/api/director/{session_id}/save_recipe",
                    json={"effect_ids": ["speed_ramp_default"]})
    assert r.status_code == 200
    recipe_id = r.json()["scene_recipe_id"]
    assert recipe_id

    loaded = shot_plan.load_shot_plan(recipe_id)
    assert loaded is not None
    assert loaded["event"]["frag_id"] == 1
    assert loaded["event"]["demo_name"] == "demoA.dm_73"
    assert loaded["effect_ids"] == ["speed_ramp_default"]


def test_router_rejects_second_launch_with_409(client: TestClient) -> None:
    r1 = client.post("/api/frags/1/director/launch")
    assert r1.status_code == 200
    r2 = client.post("/api/frags/1/director/launch")
    assert r2.status_code == 409
    client.post(f"/api/director/{r1.json()['session_id']}/stop")


def test_router_404_on_unknown_frag(client: TestClient) -> None:
    r = client.post("/api/frags/999/director/launch")
    assert r.status_code == 404


def test_router_404_on_unknown_session(client: TestClient) -> None:
    assert client.get("/api/director/nope/keyframes").status_code == 404
    assert client.post("/api/director/nope/stop").status_code == 404
    assert client.post("/api/director/nope/save_recipe").status_code == 404


def test_router_save_recipe_422_without_keyframes(client: TestClient) -> None:
    r = client.post("/api/frags/1/director/launch")
    session_id = r.json()["session_id"]
    sess = director_session.session_info(session_id)
    sess["qconsole_path"].write_text("", encoding="ascii")
    r = client.post(f"/api/director/{session_id}/save_recipe")
    assert r.status_code == 422
