"""Manifests, single-variable comparisons, and diagnostic-stem provenance."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (comparison_contract as cc, event_reference as er,
                                   event_truth as et, review_manifest as rm)


def _man(**kw) -> rm.ReviewManifest:
    base = dict(
        artifact="a.mp4", experiment_variable=cc.MUSIC_OFFSET,
        variant_name="A", frag_id=2340, scene_recipe_id="r",
        visual_capture_key="v", preview_assembly_key="p",
        demo_source_hash="d", timemap_hash="t", requested_rate="1",
        music_track_sha256="m", music_source_start_us=1_000_000,
        music_source_end_us=11_875_000, music_gain_db=-4.4, game_gain=0.85,
        limiter_ceiling=0.66, mix_trim=0.62, codec="x264/aac",
        scene_start_us=0, scene_end_us=10_875_000,
        hero_event_kind=et.MY_FRAG, hero_event_edit_us=8_875_000)
    base.update(kw)
    return rm.ReviewManifest(**base)


# ── manifest completeness and round trip ────────────────────────────────────

def test_a_manifest_round_trips_through_its_sidecar(tmp_path):
    man = _man(artifact=str(tmp_path / "a.mp4"))
    path = man.write()
    assert path.name == "a.manifest.json"
    assert rm.ReviewManifest.load(path) == man


def test_a_manifest_names_every_input_that_decides_content():
    man = _man()
    required = {"visual_capture_key", "preview_assembly_key", "timemap_hash",
                "requested_rate", "music_track_sha256", "music_source_start_us",
                "music_gain_db", "game_gain", "limiter_ceiling", "mix_trim",
                "codec", "hero_event_kind", "hero_event_edit_us",
                "analyzer_versions", "scene_recipe_id"}
    assert required <= set(man.to_dict())


def test_a_missing_artifact_is_a_provenance_error(tmp_path):
    man = _man(artifact=str(tmp_path / "nope.mp4"))
    rep = rm.verify(man, track_path=tmp_path / "t.mp3", check_music=False)
    assert not rep.reproducible
    assert rm.blocks_review(rep)
    with pytest.raises(rm.ProvenanceError):
        rep.raise_if_broken()


def test_a_changed_file_is_a_provenance_error(tmp_path):
    art = tmp_path / "a.mp4"
    art.write_bytes(b"one")
    man = _man(artifact=str(art), output_sha256=rm.file_sha256(art))
    assert rm.verify(man, track_path=art, check_music=False).reproducible
    art.write_bytes(b"two")               # the artifact moved on
    rep = rm.verify(man, track_path=art, check_music=False)
    assert not rep.reproducible
    assert any(f.check == rm.PROVENANCE_REPRODUCIBILITY_ERROR
               for f in rep.findings)


def test_a_manifest_without_an_output_hash_warns_but_does_not_block(tmp_path):
    art = tmp_path / "a.mp4"
    art.write_bytes(b"x")
    rep = rm.verify(_man(artifact=str(art)), track_path=art, check_music=False)
    assert rep.reproducible
    assert any(f.severity == "WARN" for f in rep.findings)


def test_the_extract_trim_is_part_of_the_recorded_music_position():
    man = _man(artifact="a.mp4", artifact_trim_start_us=6_400_000)
    assert man.artifact_trim_start_us == 6_400_000
    assert man.music_source_start_us + man.artifact_trim_start_us == 7_400_000


# ── one experiment, one variable ────────────────────────────────────────────

def test_a_timing_comparison_with_different_gains_is_rejected():
    comp = cc.Comparison("t", cc.MUSIC_OFFSET, (
        _man(variant_name="A", music_source_start_us=1_000_000),
        _man(variant_name="B", music_source_start_us=1_015_000,
             music_gain_db=-2.0)))
    checks = comp.check()
    assert not comp.valid
    assert any(f.check == cc.COMPARISON_MIX_DRIFT for f in checks)
    with pytest.raises(cc.ComparisonContractError):
        comp.raise_if_invalid()


def test_a_timing_comparison_with_a_frozen_mix_passes():
    comp = cc.Comparison("t", cc.MUSIC_OFFSET, (
        _man(variant_name="A", music_source_start_us=1_000_000),
        _man(variant_name="B", music_source_start_us=1_015_000),
        _man(variant_name="C", music_source_start_us=1_030_000)))
    assert comp.valid, comp.check()
    assert comp.to_dict()["frozen_mix"]["music_gain_db"] == -4.4


def test_a_second_moving_part_invalidates_the_comparison():
    comp = cc.Comparison("t", cc.MUSIC_OFFSET, (
        _man(variant_name="A", music_source_start_us=1_000_000),
        _man(variant_name="B", music_source_start_us=1_015_000,
             requested_rate="0.5")))
    assert any(f.check == cc.COMPARISON_MULTI_VARIABLE for f in comp.check())


def test_a_comparison_whose_variable_never_changes_is_rejected():
    comp = cc.Comparison("t", cc.MUSIC_OFFSET, (
        _man(variant_name="A"), _man(variant_name="B")))
    assert any(f.check == cc.COMPARISON_VARIABLE_STATIC for f in comp.check())


def test_gain_may_differ_only_when_mixing_is_the_experiment():
    members = (_man(variant_name="A", music_gain_db=-4.4),
               _man(variant_name="B", music_gain_db=-1.0))
    assert not cc.Comparison("t", cc.MUSIC_OFFSET, members).valid
    assert cc.Comparison("t", cc.MIX, members).valid


def test_the_hero_event_must_be_identical_across_a_comparison():
    comp = cc.Comparison("t", cc.MUSIC_OFFSET, (
        _man(variant_name="A", music_source_start_us=1_000_000),
        _man(variant_name="B", music_source_start_us=1_015_000,
             hero_event_edit_us=9_000_000)))
    assert not comp.valid


def test_levels_are_reported_and_never_corrected():
    out = cc.measured_levels([("A", -15.7, -3.6), ("B", -15.8, -5.0)])
    assert "never adjusted" in out["note"]
    assert set(out["members"][0]) == {"variant", "lufs", "dbtp"}
    assert "target" not in out and "correction" not in out


def test_a_comparison_needs_a_known_variable_and_two_members():
    with pytest.raises(ValueError):
        cc.Comparison("t", "VIBES", (_man(), _man()))
    with pytest.raises(ValueError):
        cc.Comparison("t", cc.MUSIC_OFFSET, (_man(),))


# ── derived stems must say what they are ────────────────────────────────────

def test_a_reconstruction_may_be_used_for_sync_claims():
    prov = er.StemProvenance(
        stem_name="MY_HITS_ONLY", method="assets at authoritative times",
        source_kind="RECONSTRUCTED", source_artifact="recognition evidence",
        source_span_us=(0, 1_000), event_kinds=(et.MY_LG_CONTACT,),
        event_count=33, events_hash="a", asset_hash="b",
        renderer_version=er.RENDERER_VERSION)
    assert prov.usable_for_sync_claims


def test_a_stem_separated_out_of_a_mix_may_not():
    """The lesson from the stem that reported a hole the source never had."""
    prov = er.StemProvenance(
        stem_name="music_only", method="source separation",
        source_kind="EXTRACTED", source_artifact="delivered mix",
        source_span_us=(0, 1_000), event_kinds=(), event_count=0,
        events_hash="a", asset_hash="b", renderer_version=er.RENDERER_VERSION)
    assert not prov.usable_for_sync_claims


def test_diagnostic_tracks_are_marked_so_they_cannot_ship(tmp_path):
    assert er.is_diagnostic_only(tmp_path / "DIAG_EVENT_REFERENCE.wav")
    assert not er.is_diagnostic_only(tmp_path / "PART04.mp4")
    with pytest.raises(er.DiagnosticAudioError):
        er.assert_never_shipped(tmp_path / "PART04.mp4")


def test_the_event_reference_refuses_non_authoritative_times(tmp_path):
    heard = et.GameEvent(kind=et.MY_FRAG, owner=et.OWNER_ME,
                         layer=et.FULL_GAME_AUDIO, edit_us=9_011_700)
    with pytest.raises(er.DiagnosticAudioError):
        er.render_event_reference([heard], 10_000_000, tmp_path / "r.wav")


def test_the_event_reference_places_a_click_at_every_truth_timestamp(tmp_path):
    import numpy as np
    import soundfile as sf
    events = [et.GameEvent(kind=et.MY_LG_CONTACT, owner=et.OWNER_ME,
                           layer=et.GAME_EVENT_TRUTH, edit_us=us)
              for us in (1_000_000, 2_000_000, 3_500_000)]
    path, prov = er.render_event_reference(events, 5_000_000,
                                           tmp_path / "ref.wav")
    assert path.name.startswith(er.DIAGNOSTIC_PREFIX)
    assert prov.event_count == 3
    y, sr = sf.read(str(path), dtype="float32")
    for us in (1_000_000, 2_000_000, 3_500_000):
        i = int(us * sr / 1e6)
        assert np.max(np.abs(y[i:i + int(sr * 0.01)])) > 0.1
    quiet = y[int(2.5 * sr):int(3.0 * sr)]
    assert np.max(np.abs(quiet)) < 0.05


def test_the_stem_definitions_name_only_known_event_kinds():
    for kinds in er.STEM_DEFINITIONS.values():
        for k in kinds:
            assert k in et.EVENT_KINDS
