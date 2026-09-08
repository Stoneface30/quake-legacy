"""Versioned, provenance-honest music features and edit-time matching."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

from creative_suite.engine.scene_recipe import MusicPlacement


@dataclass(frozen=True)
class MusicRegionV2:
    kind: str
    start_us: int
    end_us: int
    confidence: float | None


@dataclass(frozen=True)
class MusicEventV2:
    event_type: str
    music_us: int
    strength: float
    confidence: float | None


@dataclass(frozen=True)
class MusicFeatureV2:
    track_hash: str
    path: str
    duration_us: int
    sample_rate: int | None
    channels: int | None
    extractor_version: str
    schema_version: int
    status: str
    bpm: float | None
    bpm_confidence: float | None
    beats_us: tuple[int, ...]
    beat_confidence: float | None
    onset_curve: tuple[tuple[int, float], ...]
    energy_curve: tuple[tuple[int, float], ...]
    loudness_curve: tuple[tuple[int, float], ...]
    spectral_curve: tuple[tuple[int, float], ...]
    bar_grid_estimate_us: tuple[int, ...]
    section_boundary_estimates_us: tuple[int, ...]
    phrase_boundary_estimates_us: tuple[int, ...]
    regions: tuple[MusicRegionV2, ...]
    salient_events: tuple[MusicEventV2, ...] = ()
    analysis_provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != 2:
            raise ValueError("MusicFeatureV2 requires schema_version=2")
        if re.fullmatch(r"[0-9a-f]{64}", self.track_hash) is None:
            raise ValueError("track_hash must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MusicFeatureV2":
        if "downbeats_us" in value or "downbeats" in value:
            raise ValueError("unverified downbeats must be named BAR_GRID_ESTIMATE")
        data = dict(value)
        for key in ("beats_us", "onset_curve", "energy_curve", "loudness_curve",
                    "spectral_curve", "bar_grid_estimate_us",
                    "section_boundary_estimates_us", "phrase_boundary_estimates_us"):
            data[key] = tuple(tuple(x) if isinstance(x, list) else x for x in data.get(key, ()))
        data["regions"] = tuple(
            x if isinstance(x, MusicRegionV2) else MusicRegionV2(**x)
            for x in data.get("regions", ())
        )
        data["salient_events"] = tuple(
            x if isinstance(x, MusicEventV2) else MusicEventV2(**x)
            for x in data.get("salient_events", ())
        )
        data["analysis_provenance"] = tuple(
            tuple(x) for x in data.get("analysis_provenance", ())
        )
        return cls(**data)


@dataclass(frozen=True)
class RegionMatch:
    region: MusicRegionV2
    anchor_edit_us: int
    music_anchor_us: int
    score: float
    placement: MusicPlacement


def rank_regions_for_anchor(feature: MusicFeatureV2, *, anchor_edit_us: int,
                            scene_duration_us: int, event_kind: str,
                            limit: int = 3) -> list[RegionMatch]:
    weights = {"DROP_CANDIDATE": 1.0, "BUILD_CANDIDATE": 0.72,
               "BREAKDOWN_CANDIDATE": 0.45}
    if anchor_edit_us < 0 or scene_duration_us <= 0:
        raise ValueError("edit anchor must be non-negative and scene duration positive")
    matches: list[RegionMatch] = []
    for region in feature.regions:
        if region.start_us < 0 or region.end_us <= region.start_us or region.end_us > feature.duration_us:
            continue
        music_anchor = region.start_us + min(1_000_000, (region.end_us - region.start_us) // 4)
        confidence = region.confidence if region.confidence is not None else 0.5
        score = weights.get(region.kind, 0.3) * confidence
        source_start = music_anchor - anchor_edit_us
        source_end = source_start + scene_duration_us
        if source_start < 0 or source_end > feature.duration_us:
            continue
        placement = MusicPlacement(feature.track_hash, source_start, 0, source_end)
        matches.append(RegionMatch(region, anchor_edit_us, music_anchor, round(score, 6), placement))
    return sorted(matches, key=lambda x: (-x.score, x.region.start_us))[:limit]


class MusicFeatureStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS music_features_v2(
              track_hash TEXT PRIMARY KEY, canonical_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS music_region_reviews(
              frag_id INTEGER NOT NULL, track_hash TEXT NOT NULL,
              region_start_us INTEGER NOT NULL, decision TEXT NOT NULL,
              notes TEXT NOT NULL DEFAULT '',
              PRIMARY KEY(frag_id, track_hash, region_start_us));
            CREATE TABLE IF NOT EXISTS music_region_reviews_v2(
              frag_id INTEGER NOT NULL, track_hash TEXT NOT NULL,
              region_start_us INTEGER NOT NULL, scene_recipe_id TEXT NOT NULL,
              matcher_version TEXT NOT NULL, decision TEXT NOT NULL,
              notes TEXT NOT NULL DEFAULT '',
              PRIMARY KEY(frag_id, track_hash, region_start_us,
                          scene_recipe_id, matcher_version));
            CREATE TABLE IF NOT EXISTS scene_music_profiles(
              frag_id INTEGER PRIMARY KEY, profile_json TEXT NOT NULL,
              derivation_version TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS music_track_usage(
              track_hash TEXT NOT NULL, context_id TEXT NOT NULL,
              used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              texture_label TEXT, artist_key TEXT,
              PRIMARY KEY(track_hash, context_id));
            """)

    @staticmethod
    def full_content_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def put(self, feature: MusicFeatureV2) -> None:
        payload = json.dumps(feature.to_dict(), ensure_ascii=False,
                             sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO music_features_v2 VALUES (?,?)",
                       (feature.track_hash, payload))

    def get(self, track_hash: str) -> MusicFeatureV2 | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT canonical_json FROM music_features_v2 WHERE track_hash=?",
                             (track_hash,)).fetchone()
        return None if row is None else MusicFeatureV2.from_dict(json.loads(row[0]))

    def all_features(self) -> list[MusicFeatureV2]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT canonical_json FROM music_features_v2 ORDER BY track_hash").fetchall()
        return [MusicFeatureV2.from_dict(json.loads(row[0])) for row in rows]

    def save_review(self, frag_id: int, track_hash: str, region_start_us: int,
                    decision: str, notes: str = "", *,
                    scene_recipe_id: str | None = None,
                    matcher_version: str | None = None) -> None:
        if decision not in {"favorite", "reject", "undecided"}:
            raise ValueError("unsupported music region decision")
        with sqlite3.connect(self.path) as db:
            if scene_recipe_id and matcher_version:
                db.execute("INSERT OR REPLACE INTO music_region_reviews_v2 VALUES (?,?,?,?,?,?,?)",
                           (frag_id, track_hash, region_start_us, scene_recipe_id,
                            matcher_version, decision, notes))
            else:
                db.execute("INSERT OR REPLACE INTO music_region_reviews VALUES (?,?,?,?,?)",
                           (frag_id, track_hash, region_start_us, decision, notes))

    def get_reviews(self, frag_id: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as db:
            rows_v2 = db.execute(
                "SELECT frag_id,track_hash,region_start_us,decision,notes,"
                "scene_recipe_id,matcher_version FROM music_region_reviews_v2 "
                "WHERE frag_id=? ORDER BY region_start_us", (frag_id,)).fetchall()
            rows = db.execute("SELECT frag_id,track_hash,region_start_us,decision,notes "
                              "FROM music_region_reviews WHERE frag_id=? ORDER BY region_start_us",
                              (frag_id,)).fetchall()
        keys = ("frag_id", "track_hash", "region_start_us", "decision", "notes")
        keys_v2 = (*keys, "scene_recipe_id", "matcher_version")
        return ([dict(zip(keys_v2, row)) for row in rows_v2] +
                [dict(zip(keys, row)) for row in rows])

    def put_scene_profile(self, frag_id: int, profile: dict[str, Any],
                          derivation_version: str) -> None:
        payload = json.dumps(profile, sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO scene_music_profiles VALUES (?,?,?)",
                       (frag_id, payload, derivation_version))

    def get_scene_profile(self, frag_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT profile_json FROM scene_music_profiles WHERE frag_id=?",
                             (frag_id,)).fetchone()
        return None if row is None else json.loads(row[0])


def migrate_legacy_cache(legacy_db: Path, store: MusicFeatureStore, *,
                         canonical_root: Path) -> dict[str, int]:
    """Migrate trustworthy scalar/grids; never decode or extract audio."""
    report = {"legacy_rows": 0, "migrated": 0, "missing": 0, "outside_canonical": 0}
    root = Path(canonical_root).resolve()
    with sqlite3.connect(legacy_db) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("SELECT * FROM songs WHERE error IS NULL").fetchall()
    report["legacy_rows"] = len(rows)
    for row in rows:
        data = dict(row)
        path = Path(data["path"])
        if not path.exists():
            report["missing"] += 1
            continue
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except ValueError:
            report["outside_canonical"] += 1
            continue
        beats = tuple(round(float(x) * 1_000_000) for x in json.loads(data.get("beat_times") or "[]"))
        bars = tuple(round(float(x) * 1_000_000) for x in json.loads(data.get("downbeats") or "[]"))
        duration_us = round(float(data.get("duration_s") or 0) * 1_000_000)
        track_hash = store.full_content_hash(path)
        store.put(MusicFeatureV2(
            track_hash, relative, duration_us, None, None,
            "legacy-music-beatmatch@1", 2, "MIGRATED_PARTIAL_NO_REANALYSIS",
            data.get("bpm"), None, beats, None, (), (), (), (), bars, (), (), (),
        ))
        report["migrated"] += 1
    return report
