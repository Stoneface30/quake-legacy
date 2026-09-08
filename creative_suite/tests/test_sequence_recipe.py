"""SequenceRecipe: the fourth clock stage, and the invariants it protects.

A sequence adds ``edit_us -> sequence_edit_us`` and nothing else. The tests
that matter are that a scene's own clock is never disturbed, that the
programme cannot express a hole or an overlap, and that identity is stable.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import sequence_recipe as sq


def _specs():
    return [
        {"recipe_id": "a" * 64, "use_start_us": 2_200_000,
         "use_end_us": 4_000_000, "label": "projectile",
         "transition_id": "t" * 64},
        {"recipe_id": "b" * 64, "use_start_us": 2_650_000,
         "use_end_us": 5_000_000, "label": "bridge target"},
        {"recipe_id": "c" * 64, "use_start_us": 1_000_000,
         "use_end_us": 4_500_000, "label": "lg tracking"},
    ]


def _seq(**kw):
    return sq.SequenceRecipe(scenes=sq.lay_out(_specs()), **kw)


# ── layout is derived, so holes are unrepresentable ─────────────────────────

def test_lay_out_packs_scenes_back_to_back():
    scenes = sq.lay_out(_specs())
    assert scenes[0].seq_start_us == 0
    for prev, nxt in zip(scenes, scenes[1:]):
        assert nxt.seq_start_us == prev.seq_end_us


def test_duration_is_the_sum_of_the_played_spans():
    seq = _seq()
    assert seq.duration_us == sum(s.duration_us for s in seq.scenes)
    assert seq.duration_us == (1_800_000 + 2_350_000 + 3_500_000)


def test_a_gap_is_rejected():
    scenes = list(sq.lay_out(_specs()))
    bad = sq.SequenceScene(recipe_id="b" * 64, order=1,
                           use_start_us=0, use_end_us=1_000_000,
                           seq_start_us=scenes[0].seq_end_us + 1)
    with pytest.raises(ValueError, match="previous scene ends"):
        sq.SequenceRecipe(scenes=(scenes[0], bad))


def test_an_overlap_is_rejected():
    scenes = list(sq.lay_out(_specs()))
    bad = sq.SequenceScene(recipe_id="b" * 64, order=1,
                           use_start_us=0, use_end_us=1_000_000,
                           seq_start_us=scenes[0].seq_end_us - 1)
    with pytest.raises(ValueError):
        sq.SequenceRecipe(scenes=(scenes[0], bad))


def test_sequence_must_start_at_zero():
    s = sq.SequenceScene(recipe_id="a" * 64, order=0, use_start_us=0,
                         use_end_us=1_000_000, seq_start_us=5)
    with pytest.raises(ValueError, match="start the sequence clock"):
        sq.SequenceRecipe(scenes=(s,))


def test_order_must_be_strictly_increasing():
    a = sq.SequenceScene(recipe_id="a" * 64, order=1, use_start_us=0,
                         use_end_us=1_000_000, seq_start_us=0)
    b = sq.SequenceScene(recipe_id="b" * 64, order=1, use_start_us=0,
                         use_end_us=1_000_000, seq_start_us=1_000_000)
    with pytest.raises(ValueError, match="strictly increasing"):
        sq.SequenceRecipe(scenes=(a, b))


def test_empty_sequence_is_rejected():
    with pytest.raises(ValueError):
        sq.SequenceRecipe(scenes=())


def test_a_scene_must_play_a_positive_span():
    with pytest.raises(ValueError):
        sq.SequenceScene(recipe_id="a" * 64, order=0, use_start_us=1000,
                         use_end_us=1000, seq_start_us=0)


# ── the fourth clock stage ──────────────────────────────────────────────────

def test_scene_clock_maps_into_the_sequence_clock():
    scenes = sq.lay_out(_specs())
    second = scenes[1]
    # the scene's own edit clock is untouched: its start still reads as its
    # own use_start_us, and maps to where the sequence places it
    assert second.to_sequence_us(second.use_start_us) == second.seq_start_us
    assert second.to_sequence_us(second.use_end_us) == second.seq_end_us


def test_mapping_is_a_pure_offset_never_a_rescale():
    scene = sq.lay_out(_specs())[2]
    a = scene.to_sequence_us(scene.use_start_us + 250_000)
    b = scene.to_sequence_us(scene.use_start_us + 1_250_000)
    assert b - a == 1_000_000       # one second of scene is one of sequence


def test_mapping_rejects_floats():
    scene = sq.lay_out(_specs())[0]
    with pytest.raises(ValueError):
        scene.to_sequence_us(1.5)


# ── identity ────────────────────────────────────────────────────────────────

def test_sequence_id_is_deterministic():
    assert _seq().sequence_id == _seq().sequence_id


def test_sequence_id_tracks_scene_order():
    forward = _seq()
    specs = _specs()
    specs[0], specs[1] = specs[1], specs[0]
    reordered = sq.SequenceRecipe(scenes=sq.lay_out(specs))
    assert forward.sequence_id != reordered.sequence_id


def test_sequence_id_tracks_the_audio_contract():
    assert _seq().sequence_id != _seq(mix_trim=0.5).sequence_id
    assert _seq().sequence_id != _seq(music_volume=0.5).sequence_id


def test_canonical_roundtrip_preserves_identity():
    seq = _seq(title="MICRO_SEQUENCE_V2_REVIEW",
               music_track_hashes=("f" * 64,))
    assert sq.from_canonical(seq.canonical()) == seq
    assert sq.from_canonical(seq.canonical()).sequence_id == seq.sequence_id


def test_persist_and_reload(tmp_path):
    db = tmp_path / "sequences.db"
    seq = _seq(title="MICRO")
    sid = sq.persist(seq, db)
    assert sq.load(sid, db) == seq
    assert sq.load("0" * 64, db) is None


def test_counts_are_reported():
    seq = _seq()
    assert seq.scene_count == 3
    assert seq.transition_count == 1     # only the first scene has one


def test_unknown_output_profile_rejected():
    with pytest.raises(ValueError):
        _seq(output_profile="VHS")


def test_scene_recipe_v2_is_untouched_by_this_module():
    """A sequence REFERENCES scenes; it must not import or mutate them."""
    src = (REPO_ROOT / "creative_suite" / "engine"
           / "sequence_recipe.py").read_text(encoding="utf-8")
    assert "SceneRecipeV2" not in src.split('"""', 2)[2]


def test_from_canonical_fallbacks_match_the_dataclass_defaults():
    """A dict missing an optional field must round-trip to the SAME value the
    dataclass would have chosen, or identity silently depends on which path
    built the object."""
    full = sq.SequenceRecipe(scenes=sq.lay_out(_specs()))
    trimmed = {k: v for k, v in full.canonical().items()
               if k not in {"true_peak_ceiling", "mix_trim", "music_volume",
                            "game_volume", "output_profile"}}
    assert sq.from_canonical(trimmed) == full
    assert sq.from_canonical(trimmed).sequence_id == full.sequence_id


def test_audio_contract_records_the_measured_ceiling():
    # 0.74 measured -0.9 dBTP post-AAC on the first micro-sequence: a fail.
    assert sq.SequenceRecipe(scenes=sq.lay_out(_specs())).true_peak_ceiling == 0.66
