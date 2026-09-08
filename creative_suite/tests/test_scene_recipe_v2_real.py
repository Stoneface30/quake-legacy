"""Real-corpus SceneRecipeV2 proof using an existing /frags candidate."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from creative_suite.api import frags as frags_api
from creative_suite.engine import scene_recipe as sr
from creative_suite.engine import shot_plan


REAL_FRAG_ID = 5979


def _real_frag() -> dict:
    if not frags_api.FRAG_DB_PATH.exists():
        pytest.skip("real frag recognition database is not available")
    connection = sqlite3.connect(
        f"file:{frags_api.FRAG_DB_PATH.as_posix()}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT id,demo_name,content_hash,server_time_ms,weapon_name,classes,attributes,"
            " recognition_version FROM recognized_frags WHERE id = ?",
            (REAL_FRAG_ID,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        pytest.skip(f"real frag {REAL_FRAG_ID} is not present")
    value = dict(row)
    value["classes"] = json.loads(value["classes"])
    value["attributes"] = json.loads(value["attributes"])
    value["window"] = {"start_ms": 548_575, "end_ms": 557_075}
    return value


def test_real_frag_recipe_roundtrip_and_legacy_projection(tmp_path: Path) -> None:
    """Catches losing real impact provenance, timing, exclusions, or identity."""
    frag = _real_frag()
    recipe = sr.build_frag_scene_recipe(
        frag, slow_pre_us=500_000, freeze_us=250_000,
    )

    impact = next(a for a in recipe.anchors if a.event_type == "ROCKET_IMPACT")
    frag_anchor = next(a for a in recipe.anchors if a.event_type == "FRAG")
    assert impact.resolved_demo_us == 553_075_000
    assert frag_anchor.resolved_demo_us == 553_075_000
    assert impact.evidence.dataset == "recognized_frags"
    assert impact.evidence.record_id == str(REAL_FRAG_ID)
    assert impact.evidence.version == "recognition-v2"
    assert "DEATH" in recipe.exclusions.event_types

    mapping = recipe.time_map_object()
    assert mapping.demo_to_edit(552_575_000) == 4_000_000
    assert mapping.demo_to_edit(553_075_000, bias="left") == 5_000_000
    assert mapping.demo_to_edit(553_075_000, bias="right") == 5_250_000
    assert mapping.edit_to_demo(5_125_000) == 553_075_000
    assert mapping.demo_to_edit(554_075_000) == 6_250_000

    db = tmp_path / "cinematic.db"
    canonical_before = recipe.canonical_json()
    recipe_id = sr.persist_scene_recipe(recipe, db)
    loaded = sr.load_scene_recipe(recipe_id, db)
    assert loaded is not None
    assert loaded.canonical_json() == canonical_before
    assert loaded.recipe_id == recipe_id
    for demo_us in (548_575_000, 552_575_000, 553_075_000, 554_075_000,
                    557_075_000):
        assert loaded.time_map_object().demo_to_edit(
            demo_us, bias="right"
        ) == mapping.demo_to_edit(demo_us, bias="right")

    projected = sr.project_to_shot_plan(
        loaded, profile_id="MOVIE_CANDIDATE_V3",
        camera={"name": "fp", "params": {"mode": "first_person"}},
        keyframes=[], effect_ids=["impact_freeze"],
    )
    assert projected["event"]["scene_recipe_id"] == recipe_id
    assert projected["event"]["type"] == "ROCKET_IMPACT"
    assert projected["event"]["t_ms"] == 553_075
    plan_id = shot_plan.persist_shot_plan(projected, db)
    assert shot_plan.load_shot_plan(plan_id, db) == projected
