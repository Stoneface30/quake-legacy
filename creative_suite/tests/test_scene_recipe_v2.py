"""Canonical SceneRecipeV2 clocks, anchors, persistence, and legacy projection."""
from __future__ import annotations

import pytest

from creative_suite.engine import scene_recipe as sr
from creative_suite.engine import shot_plan


def _recipe() -> sr.SceneRecipeV2:
    return sr.SceneRecipeV2(
        demo=sr.DemoRef(
            sha256="ab" * 32,
            name="fixture.dm_73",
            window_start_us=-1_000_000,
            window_end_us=3_000_000,
        ),
        time_map=(
            sr.TimeSegment("normal", -1_000_000, 0, 0, 1_000_000, 1, 1),
            sr.TimeSegment("slow", 0, 1_000_000, 1_000_000, 3_000_000, 1, 2),
            sr.TimeSegment("freeze", 1_000_000, 1_000_000,
                           3_000_000, 3_250_000, 0, 1),
            sr.TimeSegment("normal", 1_000_000, 3_000_000,
                           3_250_000, 5_250_000, 1, 1),
        ),
        anchors=(
            sr.EventAnchor(
                anchor_id="hero-impact",
                event_type="ROCKET_IMPACT",
                ordinal=0,
                actor_scope="recorder",
                resolved_demo_us=1_000_000,
                evidence=sr.EvidenceRef(
                    dataset="recognized_frags",
                    record_id="5979",
                    version="recognition-v3",
                ),
                confidence="CONFIRMED",
            ),
        ),
        exclusions=sr.ExclusionPolicy(
            event_types=("DEATH",),
            ranges=(sr.ExclusionRange(1_500_000, 2_000_000,
                                      "post-death editorial cut"),),
        ),
        music=sr.MusicPlacement(
            track_id="track-content-id",
            source_start_us=12_000_000,
            program_edit_start_us=500_000,
        ),
    )


def test_forward_mapping_uses_exact_rational_rates() -> None:
    """Catches treating 0.5x as a float or failing to double edit duration."""
    time_map = sr.resolve_time_map(_recipe().time_map)
    assert time_map.demo_to_edit(-500_000) == 500_000
    assert time_map.demo_to_edit(500_000) == 2_000_000
    assert time_map.demo_to_edit(2_000_000) == 4_250_000


def test_inverse_mapping_roundtrips_non_freeze_points() -> None:
    """Catches edit/demo axes being conflated after slow motion."""
    time_map = sr.resolve_time_map(_recipe().time_map)
    for demo_us in (-750_000, 250_000, 1_250_000, 2_750_000):
        edit_us = time_map.demo_to_edit(demo_us)
        assert time_map.edit_to_demo(edit_us) == demo_us


def test_freeze_boundary_requires_explicit_left_or_right_bias() -> None:
    """Catches silently choosing one edit time for a duplicated demo instant."""
    time_map = sr.resolve_time_map(_recipe().time_map)
    with pytest.raises(ValueError, match="ambiguous"):
        time_map.demo_to_edit(1_000_000)
    assert time_map.demo_to_edit(1_000_000, bias="left") == 3_000_000
    assert time_map.demo_to_edit(1_000_000, bias="right") == 3_250_000
    assert time_map.edit_to_demo(3_125_000, bias="left") == 1_000_000
    assert time_map.edit_to_demo(3_125_000, bias="right") == 1_000_000


def test_signed_microseconds_are_preserved() -> None:
    """Catches clamping legitimate pre-anchor demo times to zero."""
    restored = sr.SceneRecipeV2.from_json(_recipe().canonical_json())
    assert restored.demo.window_start_us == -1_000_000
    assert restored.time_map[0].demo_start_us == -1_000_000


def test_anchor_keeps_semantic_identity_and_evidence_provenance() -> None:
    """Catches reducing an anchor to an anonymous resolved timestamp."""
    anchor = _recipe().anchors[0]
    assert anchor.event_type == "ROCKET_IMPACT"
    assert anchor.actor_scope == "recorder"
    assert anchor.evidence.dataset == "recognized_frags"
    assert anchor.evidence.record_id == "5979"
    assert anchor.evidence.version == "recognition-v3"


def test_exclusions_are_serialized_as_policy_without_mutating_anchors() -> None:
    """Catches destructive filtering or omission of explicit excluded ranges."""
    recipe = _recipe()
    payload = recipe.to_dict()
    assert payload["exclusions"]["event_types"] == ["DEATH"]
    assert payload["exclusions"]["ranges"][0]["reason"] == "post-death editorial cut"
    assert payload["anchors"][0]["resolved_demo_us"] == 1_000_000


def test_music_placement_is_independent_of_demo_time_map() -> None:
    """Catches stretching music when gameplay is slowed or frozen."""
    recipe = _recipe()
    assert recipe.music.edit_to_music(500_000) == 12_000_000
    assert recipe.music.edit_to_music(2_000_000) == 13_500_000
    assert recipe.music.edit_to_music(3_125_000) == 14_625_000


def test_canonical_bytes_and_hash_survive_save_reload(tmp_path) -> None:
    """Catches audit timestamps or key ordering changing recipe identity."""
    recipe = _recipe()
    before = recipe.canonical_json()
    recipe_id = sr.persist_scene_recipe(recipe, tmp_path / "cinematic.db")
    loaded = sr.load_scene_recipe(recipe_id, tmp_path / "cinematic.db")
    assert loaded is not None
    assert loaded.canonical_json() == before
    assert loaded.recipe_id == recipe.recipe_id == recipe_id
    assert loaded.time_map_object().demo_to_edit(500_000) == 2_000_000


def test_legacy_shot_plan_projection_preserves_recipe_identity(tmp_path) -> None:
    """Catches an adapter silently replacing the canonical SceneRecipeV2 authority."""
    recipe = _recipe()
    projected = sr.project_to_shot_plan(
        recipe,
        profile_id="taxonomy-v3",
        camera={"name": "fp", "params": {}},
        keyframes=[],
    )
    assert projected["event"]["scene_recipe_id"] == recipe.recipe_id
    assert projected["event"]["type"] == "ROCKET_IMPACT"
    assert projected["event"]["t_ms"] == 1_000
    assert any(step["type"] == "slow_to" for step in projected["timeline"])
    assert any(step["type"] == "freeze" for step in projected["timeline"])
    plan_id = shot_plan.persist_shot_plan(projected, tmp_path / "cinematic.db")
    assert shot_plan.load_shot_plan(plan_id, tmp_path / "cinematic.db") == projected


def test_reverse_segment_is_reserved_but_rejected_in_v2_slice() -> None:
    """Catches accidental reverse execution while keeping signed rate fields extensible."""
    try:
        sr.TimeSegment("reverse", 1_000_000, 0, 0, 1_000_000, -1, 1)
    except ValueError as exc:
        assert "reserved" in str(exc)
    else:
        raise AssertionError("reverse segment unexpectedly accepted")


def test_slow_segment_rejects_normal_or_fast_rates() -> None:
    """Catches admitting fast-forward under the slice's slow-only segment kind."""
    with pytest.raises(ValueError, match="below 1/1"):
        sr.TimeSegment("slow", 0, 2_000_000, 0, 1_000_000, 2, 1)
    with pytest.raises(ValueError, match="lowest terms"):
        sr.TimeSegment("slow", 0, 1_000_000, 0, 2_000_000, 2, 4)


def test_sub_millisecond_freeze_projects_to_nonzero_legacy_hold() -> None:
    """Catches valid microsecond freezes becoming invalid zero-ms legacy steps."""
    recipe = sr.SceneRecipeV2(
        demo=sr.DemoRef("ab" * 32, "fixture.dm_73", 0, 1_000_000),
        time_map=(
            sr.TimeSegment("normal", 0, 500_000, 0, 500_000, 1, 1),
            sr.TimeSegment("freeze", 500_000, 500_000, 500_000, 500_500, 0, 1),
            sr.TimeSegment("normal", 500_000, 1_000_000,
                           500_500, 1_000_500, 1, 1),
        ),
    )
    projected = sr.project_to_shot_plan(
        recipe, profile_id="p", camera={"name": "fp", "params": {}},
        keyframes=[],
    )
    freeze = next(step for step in projected["timeline"] if step["type"] == "freeze")
    assert freeze["hold_ms"] == 1
