"""Tests for creative_suite.engine.effect_recommend."""
from __future__ import annotations

import pytest

from creative_suite.database import cinematic_db as cdb
from creative_suite.engine import effect_presets
from creative_suite.engine.effect_recommend import recommend


@pytest.fixture()
def conn(tmp_path):
    c = cdb.connect(tmp_path / "cinematic_rec.db")
    effect_presets.seed(c)
    yield c
    c.close()


def _names(recs):
    return [name for name, _, _ in recs]


def test_air_rocket_gets_orbit_and_projectile(conn):
    recs = recommend({"classes": ["AIR_ROCKET"],
                      "scores": {"composite": 95.0},
                      "mode_pool": "MAIN_CA"}, conn)
    names = _names(recs)
    assert names[0] == "AIR_ROCKET_ORBIT_V1"       # hero orbit wins at 95
    assert "AIR_ROCKET_PROJECTILE_V1" in names[:2]


def test_clutch_1v4_low_hp_full_package(conn):
    recs = recommend({"classes": ["CLUTCH_1V4"],
                      "attributes": {"health": 8},
                      "scores": {"composite": 92.0},
                      "mode_pool": "MAIN_CA"}, conn)
    names = _names(recs)
    assert names[0] == "CLUTCH_1V4_V1"
    assert "CRITICAL_HP_V1" in names
    assert "LOW_HP_V1" in names


def test_pixel_shot_gets_replay_zoom(conn):
    recs = recommend({"classes": ["PIXEL_SHOT"],
                      "scores": {"composite": 60.0},
                      "mode_pool": "MAIN_CA"}, conn)
    assert _names(recs)[0] == "PIXEL_REPLAY_ZOOM_V1"


def test_extreme_speed_gets_chase(conn):
    recs = recommend({"classes": ["EXTREME_SPEED"],
                      "scores": {"composite": 55.0},
                      "mode_pool": "MAIN_CA"}, conn)
    assert _names(recs)[0] == "HIGH_SPEED_CHASE_V1"


def test_rapid_multikill_aliases_to_escalate(conn):
    recs = recommend({"classes": ["RAPID_MULTIKILL"],
                      "scores": {"composite": 70.0},
                      "mode_pool": "MAIN_CA"}, conn)
    assert _names(recs)[0] == "MULTIKILL_ESCALATE_V1"


def test_hero_gated_below_threshold(conn):
    low = recommend({"classes": ["AIR_ROCKET"],
                     "scores": {"composite": 50.0},
                     "mode_pool": "MAIN_CA"}, conn)
    names = _names(low)
    assert "AIR_ROCKET_ORBIT_V1" not in names       # hero preset gated
    assert names[0] == "AIR_ROCKET_PROJECTILE_V1"   # medium fallback wins
    high = recommend({"classes": ["AIR_ROCKET"],
                      "scores": {"composite": 90.0},
                      "mode_pool": "MAIN_CA"}, conn)
    assert _names(high)[0] == "AIR_ROCKET_ORBIT_V1"


def test_mode_gating_blocks_clutch_outside_ca(conn):
    ca = recommend({"classes": ["CLUTCH_1V2"], "mode_pool": "MAIN_CA"}, conn)
    assert "CLUTCH_1V2_V1" in _names(ca)
    ffa = recommend({"classes": ["CLUTCH_1V2"], "mode_pool": "FFA"}, conn)
    assert "CLUTCH_1V2_V1" not in _names(ffa)
    none = recommend({"classes": ["CLUTCH_1V2"]}, conn)
    assert "CLUTCH_1V2_V1" not in _names(none)


def test_anti_fatigue_demotes_recently_used(conn):
    frag = {"classes": ["AIR_ROCKET"], "scores": {"composite": 95.0},
            "mode_pool": "MAIN_CA"}
    fresh = recommend(frag, conn, part_name="part04")
    assert _names(fresh)[0] == "AIR_ROCKET_ORBIT_V1"
    orbit_id = cdb.get_effect_by_name(conn, "AIR_ROCKET_ORBIT_V1")["effect_id"]
    cdb.record_usage(conn, "part04", orbit_id, "frag_1", used_at_ms=1000)
    tired = recommend(frag, conn, part_name="part04")
    names = _names(tired)
    assert names[0] == "AIR_ROCKET_PROJECTILE_V1"   # orbit demoted
    assert names[-1] == "AIR_ROCKET_ORBIT_V1"
    _, _, reason = tired[-1]
    assert "fatigue" in reason
    # a different part is unaffected
    other = recommend(frag, conn, part_name="part05")
    assert _names(other)[0] == "AIR_ROCKET_ORBIT_V1"


def test_deterministic_ordering(conn):
    frag = {"classes": ["AIR_ROCKET", "MULTIKILL", "PIXEL_SHOT"],
            "scores": {"composite": 95.0}, "mode_pool": "MAIN_CA"}
    assert recommend(frag, conn) == recommend(frag, conn)


def test_result_tuple_shape(conn):
    recs = recommend({"classes": ["FLICK_SHOT"],
                      "scores": {"composite": 40.0},
                      "mode_pool": "MAIN_CA"}, conn)
    assert recs
    for name, intensity, reason in recs:
        assert isinstance(name, str)
        assert intensity in ("subtle", "medium", "hero")
        assert isinstance(reason, str) and reason


def test_no_match_returns_empty(conn):
    assert recommend({"classes": ["UNKNOWN_CLASS"]}, conn) == []
