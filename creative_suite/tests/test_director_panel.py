"""DIRECTOR panel — draft lifecycle + filter surfacing (directive §31-41).

Covers the contract the /frags panel depends on:
- a draft exists per frag, starts at the documented defaults, and is CLEAN
- every control change marks it dirty and persists NOTHING (§37)
- RESET CAMERA / FX / LOOK / SCENE (§38)
- SAVE RECIPE is the only write, and it goes to cinematic.db shot_plans —
  never to frag_recognition.db / demo_v2.db (read-only hard rule)
- NATIVE_CAM10 is the displayed default backend, FREECAM_SAMPLED is a
  developer-only override (§33)
- DODGE_HERO / RAIL_DODGE_HERO / PROJECTILE_DODGE_HERO surface as browsable
  movement filters with live counts, WITHOUT collapsing broad DODGE_TO_KILL
  into them (§41)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import director_draft as dd_mod
from creative_suite.api import frags as frags_mod
from creative_suite.app import create_app
from creative_suite.engine import cam10_writer, camera_compiler_v2

_DODGE_HERO_LABELS = ("DODGE_HERO", "RAIL_DODGE_HERO", "PROJECTILE_DODGE_HERO")


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
        (1, ["DODGE_TO_KILL"], 5.0),
        (2, ["DODGE_TO_KILL", "RAIL_DODGE_HERO", "DODGE_HERO"], 9.0),
        (3, ["PROJECTILE_DODGE_HERO", "DODGE_HERO"], 8.0),
        (4, ["AIR_ROCKET"], 4.0),
    ]
    conn.executemany(
        "INSERT INTO recognized_frags (id, demo_name, server_time_ms, round,"
        " weapon_name, victim_client, classes, attributes, highlight_score,"
        " reasons) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (i, "demoA.dm_73", 1000 * i, 1, "ROCKET", 4,
             json.dumps([{"name": c, "confidence": "CONFIRMED"} for c in classes]),
             json.dumps({"mode_pool": "MAIN_CA"}), score, json.dumps([]))
            for i, classes, score in rows
        ],
    )
    conn.commit()
    conn.close()


def _build_demo_v2_db(path: Path) -> None:
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
    conn.commit()
    conn.close()


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    plan_db = tmp_path / "cinematic.db"
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db)
    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    monkeypatch.setattr(dd_mod, "SHOT_PLAN_DB_PATH", plan_db)
    frags_mod._classes_cache.clear()
    frags_mod._taxonomy_cache.clear()
    dd_mod.reset_store()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return {"frag_db": frag_db, "demo_db": demo_db, "plan_db": plan_db}


@pytest.fixture
def client(paths: dict[str, Path]) -> TestClient:
    return TestClient(create_app())


def _mtimes(paths: dict[str, Path]) -> tuple[float, float]:
    return (paths["frag_db"].stat().st_mtime, paths["demo_db"].stat().st_mtime)


# ------------------------------------------------------------------ schema

def test_schema_exposes_panel_vocabulary(client: TestClient) -> None:
    s = client.get("/api/director/schema").json()
    assert s["camera_modes"] == ["FPV", "ORBIT", "CHASE", "PROJECTILE", "FREECAM"]
    assert s["fx_levels"] == ["OFF", "SUBTLE", "HERO"]
    assert [c["name"] for c in s["fx_controls"]] == ["rocket_fx", "ghost"]
    assert s["looks"] == ["ORIGINAL", "UHD", "PANTHEON"]
    assert s["sections"] == ["camera", "fx", "look", "music", "scene"]


def test_schema_exposes_no_engine_command_strings(client: TestClient) -> None:
    """§32: the panel must never surface raw cvars / console commands."""
    blob = json.dumps(client.get("/api/director/schema").json()).lower()
    for banned in ("cg_", "freecamsetpos", "loadcamera", "playcamera", "seekclock"):
        assert banned not in blob


def test_backend_display_default_is_native_cam10(client: TestClient) -> None:
    """§33: NATIVE_CAM10 is the runtime backend a normal user sees."""
    s = client.get("/api/director/schema").json()
    assert s["default_backend"] == cam10_writer.BACKEND_NATIVE_CAM10 == "NATIVE_CAM10"
    assert camera_compiler_v2.BACKEND_FREECAM_SAMPLED in s["backends"]
    draft = client.get("/api/frags/1/director/draft").json()
    assert draft["backend"] == "NATIVE_CAM10"
    assert draft["backend_is_default"] is True


def test_developer_can_select_freecam_sampled_fallback(client: TestClient) -> None:
    draft = client.put("/api/frags/1/director/draft",
                       json={"backend": "FREECAM_SAMPLED"}).json()
    assert draft["backend"] == "FREECAM_SAMPLED"
    assert draft["backend_is_default"] is False


def test_unknown_backend_rejected(client: TestClient) -> None:
    assert client.put("/api/frags/1/director/draft",
                      json={"backend": "MAGIC"}).status_code == 422


# ------------------------------------------------------------------- draft

def test_draft_starts_at_defaults_and_clean(client: TestClient) -> None:
    d = client.get("/api/frags/1/director/draft").json()
    assert d["camera"] == dd_mod.DEFAULT_CAMERA
    assert d["fx"] == {"rocket_fx": "OFF", "ghost": "OFF"}
    assert d["look"] == {"look": "ORIGINAL", "show_depth": False}
    assert d["dirty"] is False
    assert d["saved_recipe_id"] is None


def test_draft_unknown_frag_404(client: TestClient) -> None:
    assert client.get("/api/frags/999/director/draft").status_code == 404


def test_camera_change_updates_draft_and_marks_dirty(client: TestClient) -> None:
    d = client.put("/api/frags/1/director/draft",
                   json={"camera": {"mode": "CHASE", "distance": 300}}).json()
    assert d["camera"]["mode"] == "CHASE"
    assert d["camera"]["distance"] == 300.0
    assert d["dirty"] is True
    assert d["preview"] == "STALE"
    # persisted across a fresh GET (server-side draft, not client state)
    assert client.get("/api/frags/1/director/draft").json()["camera"]["mode"] == "CHASE"


def test_controls_follow_the_selected_mode(client: TestClient) -> None:
    fpv = client.put("/api/frags/1/director/draft",
                     json={"camera": {"mode": "FPV"}}).json()
    assert fpv["controls"] == ["fov"]
    chase = client.put("/api/frags/1/director/draft",
                       json={"camera": {"mode": "CHASE"}}).json()
    assert "side_offset" in chase["controls"]


def test_fx_and_look_changes(client: TestClient) -> None:
    d = client.put("/api/frags/1/director/draft",
                   json={"fx": {"rocket_fx": "HERO", "ghost": "SUBTLE"},
                         "look": {"look": "PANTHEON"}}).json()
    assert d["fx"] == {"rocket_fx": "HERO", "ghost": "SUBTLE"}
    assert d["look"]["look"] == "PANTHEON"


def test_depth_toggle_is_developer_debug_not_a_look(client: TestClient) -> None:
    """§36: SHOW DEPTH lives on the draft but is never one of the LOOKS."""
    d = client.put("/api/frags/1/director/draft",
                   json={"look": {"show_depth": True}}).json()
    assert d["look"]["show_depth"] is True
    assert d["look"]["look"] == "ORIGINAL"
    assert "DEPTH" not in client.get("/api/director/schema").json()["looks"]


def test_look_change_reports_capture_refresh_not_live(client: TestClient) -> None:
    """§39: the API must not imply a look change is already on screen."""
    d = client.put("/api/frags/1/director/draft",
                   json={"look": {"look": "UHD"}}).json()
    assert d["refresh"]["look"]["mode"] == "CAPTURE_REFRESH"
    assert d["preview"] == "STALE"


@pytest.mark.parametrize("patch", [
    {"camera": {"mode": "BIRD"}},
    {"camera": {"distance": 99999}},
    {"camera": {"cg_thirdperson": 1}},
    {"fx": {"rocket_fx": "MAXIMUM"}},
    {"fx": {"lens_flare": "HERO"}},
    {"look": {"look": "CRT"}},
    {"look": {"show_depth": "yes"}},
    {"lighting": {}},
])
def test_invalid_patches_rejected(client: TestClient, patch: dict) -> None:
    assert client.put("/api/frags/1/director/draft", json=patch).status_code == 422


def test_rejected_patch_leaves_draft_untouched(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "CHASE"}})
    client.put("/api/frags/1/director/draft",
               json={"camera": {"mode": "ORBIT", "distance": 999999}})
    assert client.get("/api/frags/1/director/draft").json()["camera"]["mode"] == "CHASE"


def test_drafts_are_isolated_per_frag(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "FPV"}})
    assert client.get("/api/frags/2/director/draft").json()["camera"]["mode"] == "ORBIT"


# ------------------------------------------------------------------- reset

def test_reset_camera_only(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft",
               json={"camera": {"mode": "CHASE", "distance": 400},
                     "fx": {"ghost": "HERO"}})
    d = client.post("/api/frags/1/director/draft/reset",
                    json={"section": "camera"}).json()
    assert d["camera"] == dd_mod.DEFAULT_CAMERA
    assert d["fx"]["ghost"] == "HERO"   # untouched


def test_reset_fx_and_look(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft",
               json={"fx": {"rocket_fx": "HERO"}, "look": {"look": "UHD"}})
    assert client.post("/api/frags/1/director/draft/reset",
                       json={"section": "fx"}).json()["fx"]["rocket_fx"] == "OFF"
    assert client.post("/api/frags/1/director/draft/reset",
                       json={"section": "look"}).json()["look"]["look"] == "ORIGINAL"


def test_reset_scene_clears_everything_including_dirty(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft",
               json={"camera": {"mode": "PROJECTILE"}, "fx": {"ghost": "HERO"},
                     "look": {"look": "PANTHEON"}, "backend": "FREECAM_SAMPLED"})
    d = client.post("/api/frags/1/director/draft/reset",
                    json={"section": "scene"}).json()
    assert d["camera"] == dd_mod.DEFAULT_CAMERA
    assert d["fx"] == dd_mod.DEFAULT_FX
    assert d["look"] == dd_mod.DEFAULT_LOOK
    assert d["backend"] == "NATIVE_CAM10"
    assert d["dirty"] is False


def test_reset_unknown_section_rejected(client: TestClient) -> None:
    assert client.post("/api/frags/1/director/draft/reset",
                       json={"section": "grade"}).status_code == 422


# -------------------------------------------------------------------- save

def test_draft_edits_persist_nothing_until_save(
        client: TestClient, paths: dict[str, Path]) -> None:
    """§37: experimentation is free — no shot_plans row, no artifact."""
    before = _mtimes(paths)
    client.put("/api/frags/1/director/draft",
               json={"camera": {"mode": "CHASE", "distance": 512},
                     "fx": {"rocket_fx": "HERO"}, "look": {"look": "PANTHEON"}})
    client.post("/api/frags/1/director/draft/reset", json={"section": "fx"})
    assert not paths["plan_db"].exists()      # nothing written anywhere
    assert _mtimes(paths) == before           # read-only DBs untouched


def test_save_recipe_commits_and_clears_dirty(
        client: TestClient, paths: dict[str, Path]) -> None:
    client.put("/api/frags/1/director/draft",
               json={"camera": {"mode": "ORBIT", "distance": 256, "height": 96},
                     "fx": {"rocket_fx": "HERO"}, "look": {"look": "PANTHEON"}})
    saved = client.post("/api/frags/1/director/draft/save", json={}).json()
    assert saved["scene_recipe_id"]
    assert saved["dirty"] is False
    assert saved["saved_recipe_id"] == saved["scene_recipe_id"]
    # committed to cinematic.db shot_plans, with the recipe in camera params
    rows = sqlite3.connect(paths["plan_db"]).execute(
        "SELECT camera_name, plan_json FROM shot_plans").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "director_orbit"
    params = json.loads(rows[0][1])["camera"]["params"]
    assert params["mode"] == "ORBIT"
    assert params["distance"] == 256.0
    assert params["rocket_fx"] == "HERO"
    assert params["look"] == "PANTHEON"
    assert params["backend"] == "NATIVE_CAM10"


def test_save_never_writes_the_read_only_databases(
        client: TestClient, paths: dict[str, Path]) -> None:
    before = _mtimes(paths)
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "FPV"}})
    client.post("/api/frags/1/director/draft/save", json={})
    assert _mtimes(paths) == before


def test_save_of_different_recipes_yields_different_ids(client: TestClient) -> None:
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "ORBIT"}})
    a = client.post("/api/frags/1/director/draft/save", json={}).json()
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "CHASE"}})
    b = client.post("/api/frags/1/director/draft/save", json={}).json()
    assert a["scene_recipe_id"] != b["scene_recipe_id"]


def test_save_unknown_frag_404(client: TestClient) -> None:
    assert client.post("/api/frags/999/director/draft/save",
                       json={}).status_code == 404


# ------------------------------------------------------- §41 dodge filters

def test_dodge_hero_labels_are_browsable_movement_filters(client: TestClient) -> None:
    groups = client.get("/api/frags/filter-groups").json()["groups"]
    movement = next(g for g in groups if g["id"] == "movement")
    names = [c["name"] for c in movement["classes"]]
    for label in _DODGE_HERO_LABELS:
        assert label in names, f"{label} missing from the movement filter panel"


def test_dodge_hero_filters_carry_live_counts(client: TestClient) -> None:
    movement = next(g for g in client.get("/api/frags/filter-groups").json()["groups"]
                    if g["id"] == "movement")
    counts = {c["name"]: c["count"] for c in movement["classes"]}
    assert counts["DODGE_HERO"] == 2
    assert counts["RAIL_DODGE_HERO"] == 1
    assert counts["PROJECTILE_DODGE_HERO"] == 1
    assert counts["DODGE_TO_KILL"] == 2


def test_broad_dodge_to_kill_stays_separate(client: TestClient) -> None:
    """§41: the hero tier must NOT swallow the broad evidence label — they
    are independently selectable and return different sets."""
    movement = next(g for g in client.get("/api/frags/filter-groups").json()["groups"]
                    if g["id"] == "movement")
    assert "DODGE_TO_KILL" in [c["name"] for c in movement["classes"]]
    broad = client.get("/api/frags",
                       params={"movement_group": "DODGE_TO_KILL"}).json()
    hero = client.get("/api/frags",
                      params={"movement_group": "DODGE_HERO"}).json()
    assert {it["id"] for it in broad["items"]} == {1, 2}
    assert {it["id"] for it in hero["items"]} == {2, 3}


def test_dodge_hero_filters_combine_or_within_group(client: TestClient) -> None:
    data = client.get(
        "/api/frags",
        params={"movement_group": "RAIL_DODGE_HERO,PROJECTILE_DODGE_HERO"}).json()
    assert {it["id"] for it in data["items"]} == {2, 3}
