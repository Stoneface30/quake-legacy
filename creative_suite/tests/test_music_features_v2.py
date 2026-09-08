from __future__ import annotations

import hashlib
import sqlite3

import pytest

from creative_suite.engine.music_features_v2 import (
    MusicFeatureStore,
    MusicFeatureV2,
    MusicRegionV2,
    rank_regions_for_anchor,
    migrate_legacy_cache,
)


def feature(track_hash: str = "a" * 64) -> MusicFeatureV2:
    return MusicFeatureV2(
        track_hash=track_hash,
        path="library/example.mp3",
        duration_us=180_000_000,
        sample_rate=48_000,
        channels=2,
        extractor_version="legacy-music-beatmatch@1",
        schema_version=2,
        status="MIGRATED_TRUSTWORTHY",
        bpm=128.0,
        bpm_confidence=None,
        beats_us=(0, 468_750, 937_500),
        beat_confidence=None,
        onset_curve=(),
        energy_curve=(),
        loudness_curve=(),
        spectral_curve=(),
        bar_grid_estimate_us=(0, 1_875_000),
        section_boundary_estimates_us=(30_000_000,),
        phrase_boundary_estimates_us=(15_000_000, 30_000_000),
        regions=(MusicRegionV2("DROP_CANDIDATE", 29_000_000, 37_000_000, 0.9),),
    )


def test_full_hash_reads_the_entire_file(tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    prefix = b"x" * (1024 * 1024)
    a.write_bytes(prefix + b"A")
    b.write_bytes(prefix + b"B")
    assert MusicFeatureStore.full_content_hash(a) == hashlib.sha256(prefix + b"A").hexdigest()
    assert MusicFeatureStore.full_content_hash(a) != MusicFeatureStore.full_content_hash(b)


def test_feature_rejects_fake_downbeat_semantics():
    with pytest.raises(ValueError, match="BAR_GRID_ESTIMATE"):
        MusicFeatureV2.from_dict({**feature().to_dict(), "downbeats_us": [0]})


def test_feature_rejects_non_hex_full_hash():
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        feature("z" * 64)


def test_store_roundtrip_is_canonical_and_review_is_upserted(tmp_path):
    store = MusicFeatureStore(tmp_path / "features.db")
    original = feature()
    store.put(original)
    assert store.get(original.track_hash) == original
    store.save_review(5979, original.track_hash, 29_000_000, "favorite", "impact fits")
    store.save_review(5979, original.track_hash, 29_000_000, "reject", "too busy")
    assert store.get_reviews(5979) == [{
        "frag_id": 5979, "track_hash": original.track_hash,
        "region_start_us": 29_000_000, "decision": "reject", "notes": "too busy",
    }]


def test_region_ranking_places_semantic_anchor_in_edit_time():
    candidates = rank_regions_for_anchor(
        feature(), anchor_edit_us=5_250_000, scene_duration_us=9_250_000,
        event_kind="IMPACT", limit=3,
    )
    assert candidates[0].anchor_edit_us == 5_250_000
    assert candidates[0].music_anchor_us == 30_000_000
    assert candidates[0].placement.source_start_us == 24_750_000
    assert candidates[0].placement.edit_to_music(5_250_000) == 30_000_000
    assert candidates[0].score > 0


def test_region_ranking_filters_placements_outside_track():
    f = feature()
    bad = MusicRegionV2("DROP_CANDIDATE", 1_000_000, 2_000_000, .9)
    f = MusicFeatureV2(**{**f.__dict__, "regions": (bad,)})
    assert rank_regions_for_anchor(
        f, anchor_edit_us=5_000_000, scene_duration_us=9_000_000,
        event_kind="IMPACT") == []


def test_legacy_migration_renames_downbeats_and_does_not_extract(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"not decoded")
    legacy = tmp_path / "legacy.db"
    with sqlite3.connect(legacy) as db:
        db.execute("CREATE TABLE songs(content_id TEXT, path TEXT, name TEXT, duration_s REAL, "
                   "bpm REAL, beat_times TEXT, downbeats TEXT, rms_mean REAL, rms_p90 REAL, "
                   "onset_rate REAL, centroid REAL, error TEXT)")
        db.execute("INSERT INTO songs VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)",
                   ("partial", str(audio), "track", 2.0, 120.0, "[0.0,0.5]", "[0.0]",
                    .1, .2, 2.0, 2000.0))
    store = MusicFeatureStore(tmp_path / "v2.db")
    report = migrate_legacy_cache(legacy, store, canonical_root=tmp_path)
    assert report == {"legacy_rows": 1, "migrated": 1, "missing": 0, "outside_canonical": 0}
    track_hash = MusicFeatureStore.full_content_hash(audio)
    migrated = store.get(track_hash)
    assert migrated is not None
    assert migrated.bar_grid_estimate_us == (0,)
    assert migrated.status == "MIGRATED_PARTIAL_NO_REANALYSIS"
