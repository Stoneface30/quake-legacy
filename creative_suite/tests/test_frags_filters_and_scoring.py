"""Tests for the combinable multi-select filter groups, the min_speed
numeric filter, and the on-the-fly custom_weights scoring system on
GET /api/frags. See docs/reference/frag-taxonomy-review.md for the class
taxonomy these groups are drawn from, and the module docstring on
_FILTER_GROUPS in creative_suite/api/frags.py for the exact grouping choice.

Read-only endpoint, same as test_frags_api.py — frag_recognition.db /
demo_v2.db are never written by any of this.
"""
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

    def row(id_, classes, score, killer_speed):
        return (
            id_, "demoA.dm_73", 1000 * id_, 1, "ROCKET", 4,
            json.dumps([{"name": c, "confidence": "CONFIRMED"} for c in classes]),
            json.dumps({"mode_pool": "MAIN_CA", "killer_speed": killer_speed}),
            score, json.dumps([]),
        )

    rows = [
        row(1, ["AIR_ROCKET"], 5.0, 320),
        row(2, ["CLUTCH_1V2"], 8.0, 150),
        row(3, ["RAIL_FRAG", "CLEAN_FLICK"], 6.0, 400),
        row(4, ["WEAPON_COMBO"], 3.0, 100),
        row(5, ["HIGH_SPEED_FRAG"], 4.0, 500),
        row(6, ["AIR_ROCKET", "CLUTCH_1V2"], 7.0, 200),
    ]
    conn.executemany(
        "INSERT INTO recognized_frags (id, demo_name, server_time_ms, round,"
        " weapon_name, victim_client, classes, attributes, highlight_score,"
        " reasons) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
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
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db)
    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    frags_mod._classes_cache.clear()
    frags_mod._taxonomy_cache.clear()
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


# --------------------------------------------------------------- backward compat

def test_default_list_unaffected_by_new_params(client: TestClient) -> None:
    """No group/min_speed/custom_weights params supplied -> behaves exactly
    like the pre-existing endpoint: default mode_pool + score-desc sort."""
    data = client.get("/api/frags").json()
    assert data["total"] == 6
    # highlight_score desc: 8(2), 7(6), 6(3), 5(1), 4(5), 3(4)
    assert [it["id"] for it in data["items"]] == [2, 6, 3, 1, 5, 4]
    # new fields are present but don't change shape of existing ones
    assert "killer_speed" in data["items"][0]
    assert "custom_score" not in data["items"][0]


# --------------------------------------------------------------- multi-select groups

def test_group_or_within(client: TestClient) -> None:
    data = client.get(
        "/api/frags", params={"skill_group": "AIR_ROCKET,RAIL_FRAG"}
    ).json()
    assert {it["id"] for it in data["items"]} == {1, 3, 6}


def test_group_comma_list_and_repeated_params_are_equivalent(client: TestClient) -> None:
    comma = client.get(
        "/api/frags", params={"skill_group": "AIR_ROCKET,RAIL_FRAG"}
    ).json()
    repeated = client.get(
        "/api/frags",
        params=[("skill_group", "AIR_ROCKET"), ("skill_group", "RAIL_FRAG")],
    ).json()
    assert {it["id"] for it in comma["items"]} == {it["id"] for it in repeated["items"]}


def test_group_and_across(client: TestClient) -> None:
    # AND across groups: must have AIR_ROCKET (skill) AND CLUTCH_1V2 (context)
    data = client.get(
        "/api/frags",
        params={"skill_group": "AIR_ROCKET", "context_group": "CLUTCH_1V2"},
    ).json()
    assert [it["id"] for it in data["items"]] == [6]


def test_group_no_selection_means_all(client: TestClient) -> None:
    # Omitting a group param entirely = "All" for that group (no constraint)
    data = client.get("/api/frags", params={"context_group": "CLUTCH_1V2"}).json()
    assert {it["id"] for it in data["items"]} == {2, 6}


def test_movement_and_craft_groups(client: TestClient) -> None:
    data = client.get("/api/frags", params={"movement_group": "HIGH_SPEED_FRAG"}).json()
    assert [it["id"] for it in data["items"]] == [5]
    data = client.get("/api/frags", params={"craft_group": "WEAPON_COMBO"}).json()
    assert [it["id"] for it in data["items"]] == [4]


def test_existing_single_class_filter_still_works_alongside_groups(client: TestClient) -> None:
    # Old `class` substring filter AND'd with a new group filter
    data = client.get(
        "/api/frags",
        params={"class": "CLEAN_FLICK", "skill_group": "RAIL_FRAG,CLEAN_FLICK"},
    ).json()
    assert [it["id"] for it in data["items"]] == [3]


def test_filter_groups_endpoint(client: TestClient) -> None:
    data = client.get("/api/frags/filter-groups").json()
    ids = {g["id"] for g in data["groups"]}
    assert ids == {"skill", "context", "movement", "craft"}
    skill = next(g for g in data["groups"] if g["id"] == "skill")
    assert skill["query_param"] == "skill_group"
    names = {c["name"]: c["count"] for c in skill["classes"]}
    assert names["AIR_ROCKET"] == 2  # frags 1 and 6
    assert names["RAIL_FRAG"] == 1


# --------------------------------------------------------------- min_speed

def test_min_speed_filter(client: TestClient) -> None:
    # killer_speed: 1=320, 2=150, 3=400, 4=100, 5=500, 6=200
    data = client.get("/api/frags", params={"min_speed": 300}).json()
    assert {it["id"] for it in data["items"]} == {1, 3, 5}


def test_sort_speed(client: TestClient) -> None:
    data = client.get("/api/frags", params={"sort": "speed"}).json()
    assert [it["id"] for it in data["items"]] == [5, 3, 1, 6, 2, 4]  # 500..100


# --------------------------------------------------------------- custom_weights scoring

def test_custom_weights_requires_sort_custom_to_reorder(client: TestClient) -> None:
    weights = json.dumps({"AIR_ROCKET": 10, "CLUTCH_1V2": 1})
    data = client.get(
        "/api/frags", params={"custom_weights": weights}
    ).json()
    # sort still defaults to score desc — custom_weights alone doesn't reorder
    assert [it["id"] for it in data["items"]] == [2, 6, 3, 1, 5, 4]
    by_id = {it["id"]: it["custom_score"] for it in data["items"]}
    assert by_id[1] == pytest.approx(5.0 + 10)          # AIR_ROCKET
    assert by_id[6] == pytest.approx(7.0 + 10 + 1)       # AIR_ROCKET + CLUTCH_1V2
    assert by_id[2] == pytest.approx(8.0 + 1)            # CLUTCH_1V2
    assert by_id[4] == pytest.approx(3.0)                # no matching class -> unchanged


def test_custom_weights_never_touch_stored_highlight_score(client: TestClient) -> None:
    weights = json.dumps({"AIR_ROCKET": 10})
    client.get("/api/frags", params={"custom_weights": weights, "sort": "custom"})
    # re-fetch plain (no weights) and confirm highlight_score is untouched
    plain = client.get("/api/frags").json()
    by_id = {it["id"]: it["highlight_score"] for it in plain["items"]}
    assert by_id[1] == 5.0
    assert by_id[6] == 7.0


def test_sort_custom_reorders_by_custom_score(client: TestClient) -> None:
    weights = json.dumps({"AIR_ROCKET": 10, "CLUTCH_1V2": 1})
    data = client.get(
        "/api/frags", params={"custom_weights": weights, "sort": "custom"}
    ).json()
    # expected custom_score: 6->18, 1->15, 2->9, 3->6, 5->4, 4->3
    assert [it["id"] for it in data["items"]] == [6, 1, 2, 3, 5, 4]
    assert data["items"][0]["custom_score"] == pytest.approx(18.0)
    assert data["items"][0]["highlight_score"] == 7.0  # unchanged machine score


def test_sort_custom_respects_pagination(client: TestClient) -> None:
    weights = json.dumps({"AIR_ROCKET": 10, "CLUTCH_1V2": 1})
    page1 = client.get(
        "/api/frags",
        params={"custom_weights": weights, "sort": "custom", "limit": 2, "offset": 0},
    ).json()
    page2 = client.get(
        "/api/frags",
        params={"custom_weights": weights, "sort": "custom", "limit": 2, "offset": 2},
    ).json()
    assert [it["id"] for it in page1["items"]] == [6, 1]
    assert [it["id"] for it in page2["items"]] == [2, 3]
    assert page1["total"] == page2["total"] == 6


def test_sort_custom_without_weights_is_422(client: TestClient) -> None:
    r = client.get("/api/frags", params={"sort": "custom"})
    assert r.status_code == 422


def test_custom_weights_invalid_json_is_422(client: TestClient) -> None:
    r = client.get("/api/frags", params={"custom_weights": "not json"})
    assert r.status_code == 422


def test_custom_weights_combines_with_group_filters(client: TestClient) -> None:
    weights = json.dumps({"CLUTCH_1V2": 5})
    data = client.get(
        "/api/frags",
        params={
            "context_group": "CLUTCH_1V2",
            "custom_weights": weights,
            "sort": "custom",
        },
    ).json()
    assert {it["id"] for it in data["items"]} == {2, 6}
    by_id = {it["id"]: it["custom_score"] for it in data["items"]}
    assert by_id[2] == pytest.approx(13.0)
    assert by_id[6] == pytest.approx(12.0)
