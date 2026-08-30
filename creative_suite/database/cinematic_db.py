"""Cinematic effect/recipe database (programmable fragmovie system).

Owns creative_suite/database/cinematic.db. Schema is created at connect();
later columns are added via ALTER TABLE migrations, following the house
pattern in demo_v2_db.py. Never touches demo_v2.db or frags*.db.

All JSON columns are stored in canonical form (sort_keys, compact
separators) so identical payloads are byte-identical — see canonical_json().
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "cinematic.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cinematic_effects (
    effect_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    trigger_types TEXT,            -- JSON list of frag classifications/tags
    allowed_game_modes TEXT,       -- JSON list; NULL/[] = all modes
    camera_recipe TEXT,            -- JSON
    time_recipe TEXT,              -- JSON
    tracking_recipe TEXT,          -- JSON
    fx_recipe TEXT,                -- JSON
    audio_recipe TEXT,             -- JSON
    hud_recipe TEXT,               -- JSON
    color_recipe TEXT,             -- JSON
    parameters_json TEXT,          -- JSON free-form tunables
    intensity TEXT NOT NULL DEFAULT 'medium'
        CHECK (intensity IN ('subtle', 'medium', 'hero')),
    quality_level TEXT,
    engine_requirements TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cinematic_recipes (
    recipe_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    frag_classes TEXT,             -- JSON list
    timeline TEXT NOT NULL,        -- JSON ordered steps [{t_rel_ms, action, params}]
    description TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS frag_effect_assignments (
    assignment_id INTEGER PRIMARY KEY,
    demo_name TEXT NOT NULL,
    server_time_ms INTEGER NOT NULL,
    victim_client INTEGER,
    classification TEXT,
    effect_id INTEGER NOT NULL REFERENCES cinematic_effects(effect_id),
    priority INTEGER NOT NULL DEFAULT 0,
    parameter_overrides TEXT,      -- JSON
    camera_target TEXT,
    start_offset_ms INTEGER NOT NULL DEFAULT 0,
    end_offset_ms INTEGER NOT NULL DEFAULT 0,
    confidence REAL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'selected', 'rendered', 'rejected')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fea_demo
    ON frag_effect_assignments(demo_name, server_time_ms);
CREATE INDEX IF NOT EXISTS idx_fea_status
    ON frag_effect_assignments(status);

CREATE TABLE IF NOT EXISTS camera_recipes (
    camera_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN (
        'orbit', 'follow', 'side_track', 'vertical_orbit', 'top_down',
        'reverse_track', 'projectile_follow', 'behind_projectile',
        'chase', 'bullet_time_arc', 'enemy_pov')),
    params TEXT,                   -- JSON
    collision_policy TEXT NOT NULL DEFAULT 'pull_in',
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audio_effects (
    audio_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    treatment TEXT NOT NULL,       -- JSON
    description TEXT
);

CREATE TABLE IF NOT EXISTS effect_usage_registry (
    usage_id INTEGER PRIMARY KEY,
    part_name TEXT NOT NULL,
    effect_id INTEGER NOT NULL REFERENCES cinematic_effects(effect_id),
    frag_ref TEXT,
    used_at_ms INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_usage_part
    ON effect_usage_registry(part_name, used_at_ms);

CREATE TABLE IF NOT EXISTS capture_profiles (
    profile_name TEXT PRIMARY KEY,
    capture_profile_id TEXT,
    cvars TEXT,                    -- JSON
    frozen_at TEXT
);
"""

# table -> {column: DDL}; applied via ALTER TABLE at connect() (house pattern).
_MIGRATION_COLUMNS: dict[str, dict[str, str]] = {
    "cinematic_effects": {},
    "cinematic_recipes": {},
    "frag_effect_assignments": {},
    "camera_recipes": {},
    "audio_effects": {},
    "effect_usage_registry": {},
    "capture_profiles": {},
}


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: same input -> byte-identical output."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open (creating if needed) the cinematic database with schema applied."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    for table, cols in _MIGRATION_COLUMNS.items():
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col, decl in cols.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


# ---------------------------------------------------------------- upserts

_EFFECT_JSON_FIELDS = (
    "trigger_types", "allowed_game_modes", "camera_recipe", "time_recipe",
    "tracking_recipe", "fx_recipe", "audio_recipe", "hud_recipe",
    "color_recipe", "parameters_json",
)
_EFFECT_SCALAR_FIELDS = (
    "category", "description", "intensity", "quality_level",
    "engine_requirements", "enabled",
)


def _effect_payload(effect: dict) -> dict:
    row: dict[str, Any] = {}
    for f in _EFFECT_JSON_FIELDS:
        v = effect.get(f)
        row[f] = canonical_json(v) if v is not None else None
    for f in _EFFECT_SCALAR_FIELDS:
        row[f] = effect.get(f, 1 if f == "enabled" else None)
    if row["intensity"] is None:
        row["intensity"] = "medium"
    return row


def upsert_effect(conn: sqlite3.Connection, effect: dict) -> int:
    """Insert or update by name; bump version only when payload changed.

    Returns effect_id.
    """
    name = effect["name"]
    row = _effect_payload(effect)
    cols = list(row)
    cur = conn.execute(
        f"SELECT effect_id, {', '.join(cols)} FROM cinematic_effects "
        "WHERE name = ?", (name,))
    existing = cur.fetchone()
    if existing is None:
        sql = (f"INSERT INTO cinematic_effects (name, {', '.join(cols)}) "
               f"VALUES (?{', ?' * len(cols)})")
        c = conn.execute(sql, [name] + [row[c] for c in cols])
        conn.commit()
        return c.lastrowid
    effect_id = existing[0]
    current = dict(zip(cols, existing[1:]))
    if current == row:
        return effect_id
    sets = ", ".join(f"{c} = ?" for c in cols)
    conn.execute(
        f"UPDATE cinematic_effects SET {sets}, version = version + 1 "
        "WHERE effect_id = ?",
        [row[c] for c in cols] + [effect_id])
    conn.commit()
    return effect_id


def upsert_recipe(conn: sqlite3.Connection, recipe: dict) -> int:
    """Insert or update a recipe by name; bump version only on change."""
    name = recipe["name"]
    timeline = canonical_json(recipe["timeline"])
    frag_classes = (canonical_json(recipe["frag_classes"])
                    if recipe.get("frag_classes") is not None else None)
    description = recipe.get("description")
    cur = conn.execute(
        "SELECT recipe_id, frag_classes, timeline, description "
        "FROM cinematic_recipes WHERE name = ?", (name,))
    existing = cur.fetchone()
    if existing is None:
        c = conn.execute(
            "INSERT INTO cinematic_recipes "
            "(name, frag_classes, timeline, description) VALUES (?, ?, ?, ?)",
            (name, frag_classes, timeline, description))
        conn.commit()
        return c.lastrowid
    recipe_id = existing[0]
    if existing[1:] == (frag_classes, timeline, description):
        return recipe_id
    conn.execute(
        "UPDATE cinematic_recipes SET frag_classes = ?, timeline = ?, "
        "description = ?, version = version + 1 WHERE recipe_id = ?",
        (frag_classes, timeline, description, recipe_id))
    conn.commit()
    return recipe_id


def upsert_camera(conn: sqlite3.Connection, camera: dict) -> int:
    """Insert or update a camera recipe by name; bump version on change."""
    name = camera["name"]
    kind = camera["kind"]
    params = (canonical_json(camera["params"])
              if camera.get("params") is not None else None)
    policy = camera.get("collision_policy", "pull_in")
    cur = conn.execute(
        "SELECT camera_id, kind, params, collision_policy "
        "FROM camera_recipes WHERE name = ?", (name,))
    existing = cur.fetchone()
    if existing is None:
        c = conn.execute(
            "INSERT INTO camera_recipes (name, kind, params, collision_policy)"
            " VALUES (?, ?, ?, ?)", (name, kind, params, policy))
        conn.commit()
        return c.lastrowid
    camera_id = existing[0]
    if existing[1:] == (kind, params, policy):
        return camera_id
    conn.execute(
        "UPDATE camera_recipes SET kind = ?, params = ?, "
        "collision_policy = ?, version = version + 1 WHERE camera_id = ?",
        (kind, params, policy, camera_id))
    conn.commit()
    return camera_id


def upsert_audio(conn: sqlite3.Connection, audio: dict) -> int:
    """Insert or update an audio effect by name (no version column)."""
    name = audio["name"]
    treatment = canonical_json(audio["treatment"])
    description = audio.get("description")
    cur = conn.execute(
        "SELECT audio_id, treatment, description FROM audio_effects "
        "WHERE name = ?", (name,))
    existing = cur.fetchone()
    if existing is None:
        c = conn.execute(
            "INSERT INTO audio_effects (name, treatment, description) "
            "VALUES (?, ?, ?)", (name, treatment, description))
        conn.commit()
        return c.lastrowid
    audio_id = existing[0]
    if existing[1:] != (treatment, description):
        conn.execute(
            "UPDATE audio_effects SET treatment = ?, description = ? "
            "WHERE audio_id = ?", (treatment, description, audio_id))
        conn.commit()
    return audio_id


# ------------------------------------------------------- usage registry

def record_usage(conn: sqlite3.Connection, part_name: str, effect_id: int,
                 frag_ref: str | None = None, used_at_ms: int = 0) -> int:
    """Log that an effect was used in a part (anti-fatigue registry)."""
    cur = conn.execute(
        "INSERT INTO effect_usage_registry "
        "(part_name, effect_id, frag_ref, used_at_ms) VALUES (?, ?, ?, ?)",
        (part_name, effect_id, frag_ref, used_at_ms))
    conn.commit()
    return cur.lastrowid


def effects_used_recently(conn: sqlite3.Connection, part_name: str,
                          effect_id: int, within_n: int) -> bool:
    """True if effect_id appears among the last within_n usages in this part."""
    if within_n <= 0:
        return False
    rows = conn.execute(
        "SELECT effect_id FROM effect_usage_registry WHERE part_name = ? "
        "ORDER BY used_at_ms DESC, usage_id DESC LIMIT ?",
        (part_name, within_n)).fetchall()
    return any(r[0] == effect_id for r in rows)


def get_effect_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    """Fetch one effect row as a dict (JSON columns decoded)."""
    cur = conn.execute("SELECT * FROM cinematic_effects WHERE name = ?",
                       (name,))
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    out = dict(zip(cols, row))
    for f in _EFFECT_JSON_FIELDS:
        if out.get(f):
            out[f] = json.loads(out[f])
    return out
