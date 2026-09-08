"""Shot plan: the full reproducibility record for one cinematic shot.

A shot plan captures EVERYTHING needed to re-render a shot bit-for-bit:
demo identity (sha256), the event being filmed, the recognition profile,
the camera recipe (generator name + params + resolved keyframes), effect
preset ids, the effect timeline, the derived timescale/fov curves and the
asset pack ids active at capture time.  ``plan_id`` is the sha256 of the
canonical JSON — identical inputs always hash identically.

Persistence: table ``shot_plans`` in ``creative_suite/database/cinematic.db``.
This module only ever issues ``CREATE TABLE IF NOT EXISTS shot_plans`` —
other tables in that database belong to other modules.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from creative_suite.engine.timeline import Timeline, fov_curve, timescale_curve

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
DEFAULT_DB = REPO_ROOT / "creative_suite" / "database" / "cinematic.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS shot_plans (
    plan_id     TEXT PRIMARY KEY,
    demo_sha256 TEXT NOT NULL,
    event_t_ms  INTEGER NOT NULL,
    profile_id  TEXT NOT NULL,
    camera_name TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    plan_json   TEXT NOT NULL
)
"""


def canonical_json(obj) -> str:
    """Byte-stable JSON: sorted keys, tight separators, ascii only."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def hash_demo(demo_path: str | Path) -> str:
    h = hashlib.sha256()
    with open(demo_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assemble_shot_plan(*, demo_sha256: str, event: dict, profile_id: str,
                       camera: dict, keyframes: list[dict],
                       timeline: Timeline, effect_ids: list[str] | None = None,
                       asset_pack_ids: list[str] | None = None,
                       base_fov: float = 90.0) -> dict:
    """Build the reproducibility record + deterministic plan_id.

    camera = {"name": generator name, "params": {...}} — the recipe;
    keyframes = the resolved path (the recipe's output, frozen in the plan).
    ``created_utc`` is deliberately EXCLUDED from the hash.
    """
    plan = {
        "version": 1,
        "demo_sha256": str(demo_sha256),
        "event": dict(event),
        "profile_id": str(profile_id),
        "camera": {"name": str(camera["name"]),
                   "params": dict(camera.get("params", {}))},
        "keyframes": [
            {"t_ms": int(kf["t_ms"]), "pos": list(kf["pos"]),
             "angles": list(kf["angles"]), "fov": float(kf["fov"])}
            for kf in keyframes],
        "effect_ids": sorted(str(e) for e in (effect_ids or [])),
        "asset_pack_ids": sorted(str(a) for a in (asset_pack_ids or [])),
        "timeline": timeline.steps,
        "timescale_curve": [[t, v] for t, v in timescale_curve(timeline)],
        "fov_curve": [[t, v] for t, v in fov_curve(timeline, base_fov)],
    }
    plan["plan_id"] = hashlib.sha256(
        canonical_json(plan).encode("utf-8")).hexdigest()
    return plan


def _connect(db_path: str | Path | None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(_SCHEMA)
    return con


def persist_shot_plan(plan: dict, db_path: str | Path | None = None) -> str:
    """Upsert the plan row; returns plan_id."""
    event_t = int(plan["event"].get("t_ms", 0))
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO shot_plans "
            "(plan_id, demo_sha256, event_t_ms, profile_id, camera_name, "
            " created_utc, plan_json) VALUES (?,?,?,?,?,?,?)",
            (plan["plan_id"], plan["demo_sha256"], event_t,
             plan["profile_id"], plan["camera"]["name"],
             datetime.now(timezone.utc).isoformat(timespec="seconds"),
             canonical_json(plan)))
        con.commit()
    finally:
        con.close()
    return plan["plan_id"]


def load_shot_plan(plan_id: str, db_path: str | Path | None = None
                   ) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT plan_json FROM shot_plans WHERE plan_id = ?",
            (plan_id,)).fetchone()
    finally:
        con.close()
    return json.loads(row[0]) if row else None


def list_shot_plans(db_path: str | Path | None = None) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT plan_id, demo_sha256, event_t_ms, profile_id, "
            "camera_name, created_utc FROM shot_plans "
            "ORDER BY created_utc, plan_id").fetchall()
    finally:
        con.close()
    keys = ("plan_id", "demo_sha256", "event_t_ms", "profile_id",
            "camera_name", "created_utc")
    return [dict(zip(keys, r)) for r in rows]
