"""Tests for creative_suite.database.cinematic_db + effect_presets seed."""
from __future__ import annotations

import json

import pytest

from creative_suite.database import cinematic_db as cdb
from creative_suite.engine import effect_presets

MANDATE_PRESETS = [
    "LOW_HP_V1", "CRITICAL_HP_V1", "NEAR_DEATH_V1",
    "CLUTCH_1V2_V1", "CLUTCH_1V3_V1", "CLUTCH_1V4_V1",
    "AIR_ROCKET_ORBIT_V1", "AIR_ROCKET_PROJECTILE_V1",
    "AIR_GRENADE_FOLLOW_V1", "PIXEL_REPLAY_ZOOM_V1", "FLICK_REPLAY_V1",
    "LG_TRACKING_V1", "HIGH_SPEED_CHASE_V1", "ROCKET_JUMP_CHASE_V1",
    "MULTIKILL_ESCALATE_V1", "FINAL_FRAG_HERO_V1",
]

EXPECTED_TABLES = {
    "cinematic_effects", "cinematic_recipes", "frag_effect_assignments",
    "camera_recipes", "audio_effects", "effect_usage_registry",
    "capture_profiles",
}


@pytest.fixture()
def conn(tmp_path):
    c = cdb.connect(tmp_path / "cinematic_test.db")
    yield c
    c.close()


def test_connect_creates_all_tables(conn):
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert EXPECTED_TABLES <= tables


def test_effect_round_trip(conn):
    eid = cdb.upsert_effect(conn, {
        "name": "RT_TEST", "category": "test", "intensity": "subtle",
        "trigger_types": ["FOO"], "allowed_game_modes": ["CA"],
        "parameters_json": {"b": 2, "a": 1},
    })
    row = cdb.get_effect_by_name(conn, "RT_TEST")
    assert row["effect_id"] == eid
    assert row["trigger_types"] == ["FOO"]
    assert row["allowed_game_modes"] == ["CA"]
    assert row["parameters_json"] == {"a": 1, "b": 2}
    assert row["intensity"] == "subtle"
    assert row["version"] == 1


def test_intensity_check_constraint(conn):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO cinematic_effects (name, category, intensity) "
            "VALUES ('BAD', 'x', 'ultra')")


def test_canonical_json_deterministic():
    a = cdb.canonical_json({"z": 1, "a": [3, 2], "m": {"y": 0, "x": 1}})
    b = cdb.canonical_json({"a": [3, 2], "m": {"x": 1, "y": 0}, "z": 1})
    assert a == b
    assert " " not in a  # compact separators


def test_seed_counts_and_mandate_presets(conn):
    counts = effect_presets.seed(conn)
    assert counts["cameras"] == 10
    assert counts["audio"] == 8
    assert counts["effects"] >= 16
    assert counts["recipes"] >= 16
    names = {r[0] for r in conn.execute(
        "SELECT name FROM cinematic_effects")}
    for preset in MANDATE_PRESETS:
        assert preset in names, preset
    intensities = {r[0] for r in conn.execute(
        "SELECT DISTINCT intensity FROM cinematic_effects")}
    assert intensities == {"subtle", "medium", "hero"}


def test_seed_idempotent(conn):
    c1 = effect_presets.seed(conn)
    versions1 = dict(conn.execute(
        "SELECT name, version FROM cinematic_effects"))
    c2 = effect_presets.seed(conn)
    versions2 = dict(conn.execute(
        "SELECT name, version FROM cinematic_effects"))
    assert c1 == c2
    assert versions1 == versions2  # no version bump on unchanged payload
    rec_versions = {r[0] for r in conn.execute(
        "SELECT version FROM cinematic_recipes")}
    assert rec_versions == {1}


def test_seed_recipe_json_deterministic(conn, tmp_path):
    effect_presets.seed(conn)
    conn2 = cdb.connect(tmp_path / "second.db")
    try:
        effect_presets.seed(conn2)
        rows1 = conn.execute(
            "SELECT name, timeline FROM cinematic_recipes ORDER BY name"
        ).fetchall()
        rows2 = conn2.execute(
            "SELECT name, timeline FROM cinematic_recipes ORDER BY name"
        ).fetchall()
        assert rows1 == rows2  # byte-identical canonical JSON
        for _, timeline in rows1:
            steps = json.loads(timeline)
            assert isinstance(steps, list) and steps
            for step in steps:
                assert {"t_rel_ms", "action", "params"} <= set(step)
    finally:
        conn2.close()


def test_upsert_bumps_version_only_on_change(conn):
    effect_presets.seed(conn)
    eff = dict(effect_presets.EFFECTS[0])
    eid = cdb.upsert_effect(conn, eff)
    v = conn.execute("SELECT version FROM cinematic_effects "
                     "WHERE effect_id=?", (eid,)).fetchone()[0]
    assert v == 1
    changed = dict(eff)
    changed["description"] = "changed description"
    cdb.upsert_effect(conn, changed)
    v2 = conn.execute("SELECT version FROM cinematic_effects "
                      "WHERE effect_id=?", (eid,)).fetchone()[0]
    assert v2 == 2


def test_usage_registry_recent_lookup(conn):
    effect_presets.seed(conn)
    eid = cdb.get_effect_by_name(conn, "LOW_HP_V1")["effect_id"]
    other = cdb.get_effect_by_name(conn, "FLICK_REPLAY_V1")["effect_id"]
    cdb.record_usage(conn, "part04", eid, "frag_1", used_at_ms=1000)
    for i in range(6):
        cdb.record_usage(conn, "part04", other, f"frag_{i+2}",
                         used_at_ms=2000 + i * 1000)
    assert cdb.effects_used_recently(conn, "part04", other, 3)
    assert not cdb.effects_used_recently(conn, "part04", eid, 3)
    assert cdb.effects_used_recently(conn, "part04", eid, 10)
    assert not cdb.effects_used_recently(conn, "part05", eid, 10)
    assert not cdb.effects_used_recently(conn, "part04", eid, 0)
