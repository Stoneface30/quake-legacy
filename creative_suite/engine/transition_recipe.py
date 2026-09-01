"""Persisted, reproducible scene-to-scene transitions (directive 8-9, 14).

A transition is a RECIPE, not an ffmpeg invocation. The same three clocks
the rest of the system uses still apply -- ``demo_us -> edit_us ->
music_us`` -- and a transition adds no fourth one. It only says WHERE in
each scene's own edit clock the cut lands, and what treatment rides on it.

WHY ANCHORS RATHER THAN TIMESTAMPS. A PROJECTILE_BRIDGE cuts on the frame
the rocket lands; that instant is recognition evidence, not a number
someone typed. Anchors resolve against the scene's cached projectile path
at build time, so re-running a recipe after the recognition data improves
moves the cut to the newly-correct instant instead of leaving it where it
happened to be authored. ``cut_edit_us`` is a RESOLVED value recorded for
reproducibility, not the authority.

IDENTITY. ``transition_id`` is a sha256 over the canonical form, matching
``SceneRecipeV2.recipe_id``. UI-only state (panel expansion, selection,
scrub position) never enters it, so a transition that looks the same in
the editor IS the same transition on disk.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

TRANSITION_SCHEMA_VERSION = 1

# The only production transition type today. Others (TELEPORTER_PASS,
# MODEL_MORPH, DEPTH_TRANSITION, ...) plug into this same contract when
# they are built; nothing here is projectile-specific except the anchors
# a PROJECTILE_BRIDGE happens to choose.
TYPE_PROJECTILE_BRIDGE = "PROJECTILE_BRIDGE"
TRANSITION_TYPES = (TYPE_PROJECTILE_BRIDGE,)

# Semantic anchors (directive 2). Every one resolves from cached
# recognition evidence; none is a magic constant.
A_LAUNCH = "SCENE_A_PROJECTILE_LAUNCH"
A_IMPACT = "SCENE_A_PROJECTILE_IMPACT"
ENTRY = "TRANSITION_ENTRY"
CUT = "TRANSITION_CUT"
B_LAUNCH = "SCENE_B_PROJECTILE_LAUNCH"
B_HERO = "SCENE_B_HERO_EVENT"
B_RELEASE = "SCENE_B_RELEASE"
ANCHORS = (A_LAUNCH, A_IMPACT, ENTRY, CUT, B_LAUNCH, B_HERO, B_RELEASE)

# Visual variants (directive 10). All keep the real 3D projectile motion
# as the foundation; none is a 2D zoompan.
VISUAL_HARD_CUT = "HARD_CUT"
VISUAL_IMPACT_FLASH = "IMPACT_FLASH"
VISUAL_GRADE_LERP = "GRADE_LERP"
VISUAL_VARIANTS = (VISUAL_HARD_CUT, VISUAL_IMPACT_FLASH, VISUAL_GRADE_LERP)

MUSIC_CONTINUOUS = "CONTINUOUS"
MUSIC_STRUCTURED = "STRUCTURED"
MUSIC_SAME_TRACK_REGION = "SAME_TRACK_REGION"
MUSIC_STRATEGIES = (MUSIC_CONTINUOUS, MUSIC_STRUCTURED,
                    MUSIC_SAME_TRACK_REGION)


def canonical_json(obj: Any) -> str:
    """Byte-stable JSON, matching shot_plan.canonical_json."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


@dataclass(frozen=True)
class SceneTransition:
    """One transition between two SceneRecipeV2 scenes."""
    type: str
    scene_a_recipe_id: str
    scene_b_recipe_id: str
    scene_a_anchor: str
    scene_b_anchor: str
    cut_edit_us: int          # resolved offset in SCENE A's edit clock
    scene_b_entry_us: int     # resolved offset in SCENE B's edit clock
    duration_us: int = 0      # 0 for a hard cut
    visual_variant: str = VISUAL_HARD_CUT
    visual_parameters: tuple = ()
    camera_continuity: tuple = ()
    fx: tuple = ()
    look_modulation: tuple = ()
    music_strategy: str = MUSIC_CONTINUOUS
    schema_version: int = TRANSITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.type not in TRANSITION_TYPES:
            raise ValueError("unknown transition type: " + str(self.type))
        for anchor in (self.scene_a_anchor, self.scene_b_anchor):
            if anchor not in ANCHORS:
                raise ValueError("unknown anchor: " + str(anchor))
        if self.visual_variant not in VISUAL_VARIANTS:
            raise ValueError("unknown visual variant: "
                             + str(self.visual_variant))
        if self.music_strategy not in MUSIC_STRATEGIES:
            raise ValueError("unknown music strategy: "
                             + str(self.music_strategy))
        for name in ("cut_edit_us", "scene_b_entry_us", "duration_us"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(name + " must be an int (microseconds)")
        if self.cut_edit_us < 0 or self.scene_b_entry_us < 0:
            raise ValueError("anchor offsets must be non-negative")
        if self.duration_us < 0:
            raise ValueError("duration_us must be non-negative")
        if self.scene_a_recipe_id == self.scene_b_recipe_id:
            raise ValueError("a scene cannot bridge to itself")

    def canonical(self) -> dict:
        d = asdict(self)
        for k in ("visual_parameters", "camera_continuity",
                  "look_modulation"):
            d[k] = {a: b for a, b in getattr(self, k)}
        d["fx"] = list(self.fx)
        return d

    def canonical_json(self) -> str:
        return canonical_json(self.canonical())

    @property
    def transition_id(self) -> str:
        return hashlib.sha256(
            self.canonical_json().encode("utf-8")).hexdigest()


def resolve_projectile_anchors(subject_track) -> dict:
    """Launch/impact offsets in a scene's own edit clock, in microseconds.

    ``subject_track`` is the cached projectile point series the camera
    compiler already consumes: ``(t_ms, x, y, z)`` tuples in scene edit
    time. Returns {} when there is no usable track, so a caller must
    decide rather than receive an invented anchor.
    """
    if not subject_track or len(subject_track) < 2:
        return {}
    launch_us = int(subject_track[0][0]) * 1000
    impact_us = int(subject_track[-1][0]) * 1000
    return {A_LAUNCH: launch_us, A_IMPACT: impact_us,
            B_LAUNCH: launch_us, B_HERO: impact_us}


def build_projectile_bridge(*, scene_a_recipe_id: str,
                            scene_b_recipe_id: str,
                            scene_a_track, scene_b_track,
                            visual_variant: str = VISUAL_HARD_CUT,
                            music_strategy: str = MUSIC_CONTINUOUS,
                            fx: tuple = (),
                            duration_us: int = 0,
                            visual_parameters: dict | None = None
                            ) -> SceneTransition:
    """A PROJECTILE_BRIDGE cutting on A's impact into B's launch."""
    a = resolve_projectile_anchors(scene_a_track)
    b = resolve_projectile_anchors(scene_b_track)
    if not a or not b:
        raise ValueError("both scenes need a usable projectile track")
    params = tuple(sorted((visual_parameters or {}).items()))
    return SceneTransition(
        type=TYPE_PROJECTILE_BRIDGE,
        scene_a_recipe_id=scene_a_recipe_id,
        scene_b_recipe_id=scene_b_recipe_id,
        scene_a_anchor=A_IMPACT, scene_b_anchor=B_LAUNCH,
        cut_edit_us=a[A_IMPACT], scene_b_entry_us=b[B_LAUNCH],
        duration_us=duration_us, visual_variant=visual_variant,
        visual_parameters=params, fx=tuple(fx),
        music_strategy=music_strategy)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS scene_transitions (
    transition_id     TEXT PRIMARY KEY,
    type              TEXT NOT NULL,
    scene_a_recipe_id TEXT NOT NULL,
    scene_b_recipe_id TEXT NOT NULL,
    transition_json   TEXT NOT NULL
)
"""


def _conn(db_path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute(_SCHEMA)
    return con


def persist(transition: SceneTransition, db_path) -> str:
    con = _conn(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO scene_transitions (transition_id, type,"
            " scene_a_recipe_id, scene_b_recipe_id, transition_json)"
            " VALUES (?,?,?,?,?)",
            (transition.transition_id, transition.type,
             transition.scene_a_recipe_id, transition.scene_b_recipe_id,
             transition.canonical_json()))
        con.commit()
    finally:
        con.close()
    return transition.transition_id


def from_canonical(d: dict) -> SceneTransition:
    return SceneTransition(
        type=d["type"],
        scene_a_recipe_id=d["scene_a_recipe_id"],
        scene_b_recipe_id=d["scene_b_recipe_id"],
        scene_a_anchor=d["scene_a_anchor"],
        scene_b_anchor=d["scene_b_anchor"],
        cut_edit_us=int(d["cut_edit_us"]),
        scene_b_entry_us=int(d["scene_b_entry_us"]),
        duration_us=int(d.get("duration_us", 0)),
        visual_variant=d.get("visual_variant", VISUAL_HARD_CUT),
        visual_parameters=tuple(
            sorted((d.get("visual_parameters") or {}).items())),
        camera_continuity=tuple(
            sorted((d.get("camera_continuity") or {}).items())),
        fx=tuple(d.get("fx") or ()),
        look_modulation=tuple(
            sorted((d.get("look_modulation") or {}).items())),
        music_strategy=d.get("music_strategy", MUSIC_CONTINUOUS),
        schema_version=int(d.get("schema_version",
                                 TRANSITION_SCHEMA_VERSION)))


def load(transition_id: str, db_path) -> SceneTransition | None:
    con = _conn(db_path)
    try:
        row = con.execute(
            "SELECT transition_json FROM scene_transitions"
            " WHERE transition_id = ?", (transition_id,)).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return from_canonical(json.loads(row[0]))


def list_transitions(db_path) -> list:
    con = _conn(db_path)
    try:
        return [dict(r) for r in con.execute(
            "SELECT transition_id, type, scene_a_recipe_id,"
            " scene_b_recipe_id FROM scene_transitions"
            " ORDER BY transition_id")]
    finally:
        con.close()
