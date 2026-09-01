"""Derive SceneMusicProfile from cached recognition evidence and SceneRecipe clocks."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from creative_suite.engine.music_features_v2 import MusicFeatureStore
from creative_suite.engine.music_intelligence_v2 import (
    SceneMusicProfile, derive_scene_music_profile,
)
from creative_suite.engine.scene_recipe import build_frag_scene_recipe

DERIVATION_VERSION = "scene-music-profile@2.0.0"


def _json(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def load_scene_music_profile(
    frag_id: int, *, frag_db: Path, demo_v2_db: Path,
    store: MusicFeatureStore | None = None,
) -> tuple[SceneMusicProfile, dict[str, Any]]:
    with sqlite3.connect(f"file:{Path(frag_db).as_posix()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM recognized_frags WHERE id=?", (frag_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown frag {frag_id}")
        frag = dict(row)
        frag["classes"] = [x.get("name") if isinstance(x, dict) else x
                           for x in _json(frag.get("classes"), [])]
        frag["attributes"] = _json(frag.get("attributes"), {})
        lg_row = db.execute(
            "SELECT series FROM recognition_lg_engagements WHERE demo_name=? AND server_time_ms=?",
            (frag["demo_name"], frag["server_time_ms"]),
        ).fetchone()
        lg_series = _json(lg_row[0], {}) if lg_row else {}

        with sqlite3.connect(f"file:{Path(demo_v2_db).as_posix()}?mode=ro", uri=True) as clips:
            clips.row_factory = sqlite3.Row
            master = clips.execute(
                "SELECT * FROM generated_clips WHERE demo_name=? AND ? BETWEEN "
                "capture_start_ms AND capture_end_ms ORDER BY generated_clip_id LIMIT 1",
                (frag["demo_name"], frag["server_time_ms"]),
            ).fetchone()
        if master:
            start_ms, end_ms = int(master["capture_start_ms"]), int(master["capture_end_ms"])
        else:
            start_ms, end_ms = int(frag["server_time_ms"])-4000, int(frag["server_time_ms"])+3000
        related = db.execute(
            "SELECT id,server_time_ms,weapon_name,classes,attributes FROM recognized_frags "
            "WHERE demo_name=? AND server_time_ms BETWEEN ? AND ? ORDER BY server_time_ms",
            (frag["demo_name"], start_ms, end_ms),
        ).fetchall()

    build_input = dict(frag)
    build_input["window"] = {"start_ms": start_ms, "end_ms": end_ms}
    recipe = build_frag_scene_recipe(build_input)
    time_map = recipe.time_map_object()
    anchors: list[dict[str, Any]] = []
    projectile_flights: list[int] = []
    attributes = frag["attributes"]
    launch_ms, impact_ms = attributes.get("projectile_launch_t"), attributes.get("projectile_impact_t")
    if launch_ms is not None and impact_ms is not None:
        evidence_flight_ms = int(attributes.get("projectile_flight_ms") or 0)
        if int(launch_ms) >= int(impact_ms) and evidence_flight_ms > 0:
            launch_ms = int(impact_ms) - evidence_flight_ms
        launch_edit = time_map.demo_to_edit(int(launch_ms)*1000, bias="left")
        impact_entry_edit = time_map.demo_to_edit(int(impact_ms)*1000, bias="left")
        impact_edit = time_map.demo_to_edit(int(impact_ms)*1000, bias="right")
        anchors.extend(({"kind": "PROJECTILE_LAUNCH", "edit_us": launch_edit},
                        {"kind": "PROJECTILE_IMPACT", "edit_us": impact_edit}))
        projectile_flights.append(max(0, impact_entry_edit-launch_edit))
    for item in related:
        edit_us = time_map.demo_to_edit(int(item["server_time_ms"])*1000,
                                       bias="right" if int(item["id"]) == frag_id else "left")
        anchors.append({"kind": "FRAG", "edit_us": edit_us,
                        "evidence_record_id": int(item["id"])})
    contacts = []
    for offset_ms, _damage in lg_series.get("dealt", []):
        demo_us = (int(frag["server_time_ms"])+int(offset_ms))*1000
        try:
            contacts.append(time_map.demo_to_edit(demo_us, bias="left"))
        except ValueError:
            continue
    evidence = {
        "weapon": frag["weapon_name"], "classes": frag["classes"],
        "duration_us": recipe.time_map[-1].edit_end_us, "anchors": anchors,
        "contact_times_us": contacts, "projectile_flights_us": projectile_flights,
        "excluded_event_types": list(recipe.exclusions.event_types),
        "excluded_edit_ranges": [
            [time_map.demo_to_edit(x.demo_start_us, bias="right"),
             time_map.demo_to_edit(x.demo_end_us, bias="left")]
            for x in recipe.exclusions.ranges
        ],
    }
    profile = derive_scene_music_profile(evidence)
    proof = {"frag_id": frag_id, "raw_demo_hero_us": int(frag["server_time_ms"])*1000,
             "mapped_edit_hero_us": profile.hero_anchor_us,
             "scene_recipe_id": recipe.recipe_id,
             "derivation_version": DERIVATION_VERSION,
             "anchor_count": len(anchors), "contact_count": len(contacts)}
    if store is not None:
        store.put_scene_profile(frag_id, profile.to_dict(), DERIVATION_VERSION)
    return profile, proof
