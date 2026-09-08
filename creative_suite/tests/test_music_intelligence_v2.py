from __future__ import annotations

from creative_suite.engine.music_features_v2 import MusicFeatureV2, MusicRegionV2
from creative_suite.engine.music_intelligence_v2 import (
    MusicEventV2,
    derive_scene_music_profile,
    energy_shape_fit,
    score_region,
    select_diverse_matches,
    match_catalog,
)
from creative_suite.engine.music_enrichment_v2 import enrich_feature


def scene(weapon: str, classes: list[str], anchors: list[dict], **extra):
    return {"weapon": weapon, "classes": classes, "duration_us": 10_000_000,
            "anchors": anchors, **extra}


def feature(track: str, energy, onsets, events, regions):
    return MusicFeatureV2(
        track_hash=track * 64, path=f"{track}.mp3", duration_us=60_000_000,
        sample_rate=48_000, channels=2, extractor_version="test@2",
        schema_version=2, status="READY", bpm=128, bpm_confidence=.8,
        beats_us=(), beat_confidence=.8, onset_curve=tuple(onsets),
        energy_curve=tuple(energy), loudness_curve=(), spectral_curve=(),
        bar_grid_estimate_us=(), section_boundary_estimates_us=(10_000_000,),
        phrase_boundary_estimates_us=(10_000_000, 20_000_000),
        regions=tuple(regions), salient_events=tuple(events),
    )


def test_profiles_are_derived_from_gameplay_evidence_not_ids():
    rocket = derive_scene_music_profile(scene(
        "ROCKET", ["DIRECT_ROCKET"],
        [{"kind": "PROJECTILE_LAUNCH", "edit_us": 4_900_000},
         {"kind": "PROJECTILE_IMPACT", "edit_us": 5_250_000}],
        projectile_flights_us=[350_000]))
    lg = derive_scene_music_profile(scene(
        "LIGHTNING", ["LG_TRACKING", "LG_HIGH_PRESSURE"],
        [{"kind": "FRAG", "edit_us": 4_750_000}],
        contact_times_us=[1_000_000, 1_040_000, 1_090_000, 2_000_000, 2_060_000]))
    clutch = derive_scene_music_profile(scene(
        "ROCKET_SPLASH", ["CLUTCH_1V4_PLUS"],
        [{"kind": "FRAG", "edit_us": 5_000_000},
         {"kind": "FRAG", "edit_us": 8_000_000},
         {"kind": "ROUND_WIN", "edit_us": 9_000_000}]))
    assert rocket.dominant_type == "IMPACT_PROJECTILE"
    assert rocket.projectile_flights_us == (350_000,)
    assert lg.dominant_type == "RHYTHMIC_TRACKING"
    assert len(lg.hit_bursts) == 2
    assert clutch.dominant_type == "TENSION_RELEASE"
    assert clutch.desired_energy_shape == (0.25, 0.5, 0.8, 1.0, 0.35)


def test_excluded_death_and_ranges_do_not_influence_profile():
    profile = derive_scene_music_profile(scene(
        "ROCKET", ["DIRECT_ROCKET"],
        [{"kind": "FRAG", "edit_us": 3_000_000},
         {"kind": "DEATH", "edit_us": 4_000_000},
         {"kind": "FRAG", "edit_us": 8_000_000}],
        excluded_event_types=["DEATH"], excluded_edit_ranges=[[7_500_000, 8_500_000]]))
    assert profile.secondary_anchor_us == ()
    assert profile.hero_anchor_us == 3_000_000


def test_energy_shape_compares_shape_not_mean():
    scene_shape = (0.2, 0.4, 0.8, 1.0, 0.3)
    assert energy_shape_fit(scene_shape, (0.1, 0.3, 0.7, 0.9, 0.2)) > .9
    assert energy_shape_fit(scene_shape, (0.6, 0.6, 0.6, 0.6, 0.6)) < .5


def test_semantic_profiles_score_different_music_reasoning():
    drop = MusicRegionV2("DROP_CANDIDATE", 10_000_000, 20_000_000, .9)
    drive = MusicRegionV2("HIGH_ENERGY_REGION", 10_000_000, 20_000_000, .8)
    impact_music = feature("a", [(10_000_000,.2),(15_000_000,1.0),(20_000_000,.3)],
        [(15_000_000,1.0)], [MusicEventV2("ACCENT",15_000_000,1.0,.9)], [drop])
    rhythm_music = feature("b", [(10_000_000,.8),(15_000_000,.82),(20_000_000,.8)],
        [(11_000_000,.8),(12_000_000,.8),(13_000_000,.8)],
        [MusicEventV2("BEAT",12_000_000,.8,.8)], [drive])
    rocket = derive_scene_music_profile(scene("ROCKET", ["DIRECT_ROCKET"],
        [{"kind":"PROJECTILE_IMPACT","edit_us":5_000_000}]))
    lg = derive_scene_music_profile(scene("LIGHTNING", ["LG_TRACKING"],
        [{"kind":"FRAG","edit_us":5_000_000}], contact_times_us=[1,50_000,100_000]))
    assert score_region(rocket, impact_music, drop).total > score_region(rocket, rhythm_music, drive).total
    assert score_region(lg, rhythm_music, drive).total > score_region(lg, impact_music, drop).total


def test_diversity_prefers_different_tracks_when_close():
    matches = [
        {"track_hash": "a", "region_start_us": n, "total": score}
        for n, score in [(1, .95), (2, .94), (3, .93)]
    ] + [{"track_hash": "b", "region_start_us": 1, "total": .92},
         {"track_hash": "c", "region_start_us": 1, "total": .91}]
    selected = select_diverse_matches(matches, limit=3, tolerance=.06)
    assert [m["track_hash"] for m in selected] == ["a", "b", "c"]


def test_enrichment_never_fabricates_migrated_confidence(monkeypatch, tmp_path):
    """Missing confidence remains missing when BPM/beats are deliberately reused."""
    import numpy as np
    import librosa
    import soundfile

    source = feature("d", (), (), (), ())
    source = source.__class__(**{
        **source.to_dict(), "bpm_confidence": None, "beat_confidence": None,
        "sample_rate": None, "channels": None,
    })
    decode_calls = []
    monkeypatch.setattr(librosa, "load", lambda *_a, **_k:
                        (decode_calls.append(1) or np.zeros(44_100), 22_050))
    monkeypatch.setattr(soundfile, "info", lambda *_a, **_k:
                        type("Info", (), {"samplerate": 48_000, "channels": 2})())
    monkeypatch.setattr(librosa.segment, "agglomerative", lambda *_a, **_k: np.array([0]))

    enriched = enrich_feature(source, tmp_path / "fixture.wav")

    assert len(decode_calls) == 1
    assert enriched.bpm == source.bpm
    assert enriched.beats_us == source.beats_us
    assert enriched.bpm_confidence is None
    assert enriched.beat_confidence is None


def test_catalog_alignment_is_bounded_costed_and_not_forced_perfect():
    region = MusicRegionV2("DROP_CANDIDATE", 10_000_000, 24_000_000, .9)
    music = feature("e", [(10_000_000,.2),(15_000_000,1.0),(24_000_000,.3)],
                    [(18_000_000,1.0)],
                    [MusicEventV2("ACCENT",18_000_000,1.0,.9)], [region])
    profile = derive_scene_music_profile(scene("ROCKET", ["DIRECT_ROCKET"],
        [{"kind":"PROJECTILE_IMPACT","edit_us":5_000_000}]))
    row = match_catalog(profile, [music], top_n=1)[0]
    expected = {"anchor_fit", "rhythm_fit", "cadence_fit", "energy_shape_fit",
                "phrase_fit", "structure_fit", "duration_fit",
                "diversity_adjustment", "alignment_cost"}
    assert set(row["components"]) == expected
    assert abs(row["alignment_shift_us"]) <= 750_000
    assert row["alignment_cost"] > 0
    assert row["aligned_delta_us"] != 0
