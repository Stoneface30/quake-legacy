"""PANTHEON scene — the PRODUCTION layer subordinate to ``SceneRecipeV2``.

A ``SceneRecipeV2`` (scene_recipe.py) answers *what moment is this, and how
does demo time map to edit time*. It is the canonical, hashed truth, and it
is deliberately NOT extended here: adding a dataclass field to
``SceneRecipeV2`` changes ``recipe_id`` for every recipe that already exists
and breaks anything keyed on it. This module is the layer above it —
*how is that moment PHOTOGRAPHED* — and it references a recipe by
``recipe_id`` rather than forking or wrapping it.

    SceneRecipeV2   demo identity + TimeMap + semantic anchors   (WHAT/WHEN)
        |  recipe_id
        v
    PantheonScene   camera intent + fx stack + look + passes     (HOW IT LOOKS)
        |  camera_compilation.artifact_hash
        v
    camera_compilations (cam10_writer.py)   the compiled .cam10  (EXECUTION)

Three separate identities, three separate lifetimes. Recompiling a camera
under a newer compiler never changes ``scene_id``; re-lighting a scene never
changes ``recipe_id``.

Semantic anchoring (§12/§16). Nothing in a scene stores a raw millisecond
where a semantic reference would do. A camera stage or an FX cue says
"PROJECTILE_LAUNCH + 120 ms", and ``resolve_anchor`` turns that into demo
microseconds by looking the anchor up in the referenced recipe — whose
anchors carry their own ``EvidenceRef`` back to the recognition row that
produced them. Re-running recognition and getting a 25 ms-different impact
time therefore moves the camera and the FX together, automatically, instead
of leaving two hand-copied constants to drift apart.

The ``runfxat`` trap (§17). ``CG_RunFxAt_f`` (cg_consolecmds.c:7746-7817)
snapshots the view origin at PARSE time and bakes it into the deferred
command, so a bare ``runfxat <t> <name>`` issued from ``cgamepostinit.cfg``
fires at the map origin — measured as pure noise in
docs/reference/free_wins_proof.md proof 1. ``compile_fx_cfg_lines`` picks
the primitive for the caller: a cue with an explicit ``world_pos`` becomes
``runfxat <t> <name> <x> <y> <z>`` (coordinates supplied, nothing snapshot),
and every other cue becomes ``at <t> runfx <name>`` (origin resolved live at
fire time). The broken form is not reachable through this API.

Persistence: table ``pantheon_scenes`` in
``creative_suite/database/cinematic.db``, following the
``CREATE TABLE IF NOT EXISTS`` + canonical-JSON + sha256-id pattern that
``shot_plan.py`` and ``cam10_writer.py`` already use on that database. This
module only ever creates its own table; ``camera_compilations`` is REUSED
from cam10_writer.py rather than duplicated.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from creative_suite.engine import cam10_writer
from creative_suite.engine.shot_plan import DEFAULT_DB, canonical_json

SCENE_SCHEMA_VERSION = 1

# --- FX intensity ladder (§15) -------------------------------------------
# OFF is a real, addressable level, not the absence of a cue: an OFF cue
# still documents that the director considered an effect at that anchor and
# chose nothing, and it still renders a comparable frame in an A/B/C sheet.
INTENSITY_OFF = "OFF"
INTENSITY_SUBTLE = "SUBTLE"
INTENSITY_HERO = "HERO"
INTENSITY_LEVELS = (INTENSITY_OFF, INTENSITY_SUBTLE, INTENSITY_HERO)

# --- how an effect reaches the engine (see FxCue) -------------------------
BINDING_CUE = "CUE"      # fired once by `at <t> runfx <name> [x y z]`
BINDING_HOOK = "HOOK"    # armed by DEFINING an engine-bound script name
FX_BINDINGS = (BINDING_CUE, BINDING_HOOK)

# --- Visual look (§20/§22) ------------------------------------------------
LOOK_ORIGINAL = "ORIGINAL"      # stock QL assets, stock colorcorrect.fs
LOOK_UHD = "UHD"                # zzz_uhd_*.pk3 texture packs, stock grade
LOOK_PANTHEON = "PANTHEON"      # UHD packs + zzz_zz_pantheon_grade.pk3
VISUAL_LOOKS = (LOOK_ORIGINAL, LOOK_UHD, LOOK_PANTHEON)

# --- Camera arc stages (§11) ---------------------------------------------
# The vocabulary a scene may draw from. A scene is NOT required to use every
# stage — over-editing is a failure mode, so the stage list is a menu, and
# the recorded intent names only the stages actually used.
STAGE_FPV = "FPV"
STAGE_PROJECTILE_FOLLOW = "PROJECTILE_FOLLOW"
STAGE_SIDE_LEAD = "SIDE_LEAD"
STAGE_IMPACT_ORBIT = "IMPACT_ORBIT"
STAGE_IMPACT_HOLD = "IMPACT_HOLD"
STAGE_RELEASE = "RELEASE"
CAMERA_STAGES = (STAGE_FPV, STAGE_PROJECTILE_FOLLOW, STAGE_SIDE_LEAD,
                 STAGE_IMPACT_ORBIT, STAGE_IMPACT_HOLD, STAGE_RELEASE)


class AnchorResolutionError(ValueError):
    """A scene referenced an anchor the recipe cannot resolve.

    Deliberately loud. The whole point of semantic anchoring is that a
    moved/renamed/unresolved anchor breaks visibly at compile time instead
    of silently filming empty air at a stale millisecond.
    """


class FxCompileError(ValueError):
    """An FX cue cannot be compiled into a safe console primitive."""


# ---------------------------------------------------------------------------
# Semantic anchor resolution (§12/§16)
# ---------------------------------------------------------------------------

def find_anchor(recipe, anchor_id: str):
    """Return the recipe's ``EventAnchor`` with this id, or raise.

    Accepts either a ``SceneRecipeV2`` or its ``to_dict()`` form, so a scene
    can be resolved against a recipe loaded straight out of the database
    without reconstructing the dataclass.
    """
    anchors = (recipe.anchors if hasattr(recipe, "anchors")
               else recipe.get("anchors", ()))
    for anchor in anchors:
        aid = (anchor.anchor_id if hasattr(anchor, "anchor_id")
               else anchor["anchor_id"])
        if aid == anchor_id:
            return anchor
    known = sorted(a.anchor_id if hasattr(a, "anchor_id") else a["anchor_id"]
                   for a in anchors)
    raise AnchorResolutionError(
        f"anchor {anchor_id!r} is not in this recipe; known anchors: {known}")


def resolve_anchor(recipe, anchor_id: str, offset_us: int = 0) -> int:
    """``anchor_id`` + ``offset_us`` -> absolute demo microseconds.

    This is the ONLY sanctioned way for a scene to obtain a time. A scene
    that stores a raw millisecond instead has silently forked the evidence.
    """
    anchor = find_anchor(recipe, anchor_id)
    status = (anchor.status if hasattr(anchor, "status")
              else anchor.get("status", "resolved"))
    resolved = (anchor.resolved_demo_us if hasattr(anchor, "resolved_demo_us")
                else anchor.get("resolved_demo_us"))
    if status != "resolved" or resolved is None:
        raise AnchorResolutionError(
            f"anchor {anchor_id!r} has status {status!r} and resolved_demo_us "
            f"{resolved!r} — it cannot be used to place a camera or an effect")
    if isinstance(offset_us, bool) or not isinstance(offset_us, int):
        raise TypeError("offset_us must be a signed integer microsecond value")
    return int(resolved) + offset_us


def resolve_anchor_ms(recipe, anchor_id: str, offset_us: int = 0) -> int:
    """Demo milliseconds — what wolfcam's ``at`` / ``seekservertime`` want.

    Rounds half away from zero rather than truncating, so a cue authored at
    an anchor lands on the anchor's own millisecond instead of one before it.
    """
    us = resolve_anchor(recipe, anchor_id, offset_us)
    return (abs(us) + 500) // 1000 * (1 if us >= 0 else -1)


# ---------------------------------------------------------------------------
# Scene value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CameraIntent:
    """WHAT the camera should do, in semantic terms only.

    ``stages`` is an ordered list of dicts, each
    ``{"stage": <CAMERA_STAGES>, "start_anchor": <anchor_id>,
       "start_offset_us": int, "end_anchor": <anchor_id>,
       "end_offset_us": int, "params": {...}}``.

    No stage carries a raw millisecond — that is the point. ``params`` holds
    the geometric knobs (radius, height, arc_deg, trail_dist, ...) which are
    not times and are therefore safe to state literally.
    """
    mode: str
    stages: tuple[dict[str, Any], ...] = ()
    subject_anchor: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for entry in self.stages:
            stage = entry.get("stage")
            if stage not in CAMERA_STAGES:
                raise ValueError(
                    f"unknown camera stage {stage!r}; expected one of "
                    f"{list(CAMERA_STAGES)}")
            for key in ("start_anchor", "end_anchor"):
                if not entry.get(key):
                    raise ValueError(
                        f"camera stage {stage!r} is missing {key!r} — stages "
                        "are anchored semantically, never by raw time")
            for key in ("start_offset_us", "end_offset_us"):
                value = entry.get(key, 0)
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TypeError(f"{key} must be a signed integer µs value")

    def resolve_stage_window_us(self, recipe, entry: dict[str, Any]
                                ) -> tuple[int, int]:
        start = resolve_anchor(recipe, entry["start_anchor"],
                               int(entry.get("start_offset_us", 0)))
        end = resolve_anchor(recipe, entry["end_anchor"],
                             int(entry.get("end_offset_us", 0)))
        if end <= start:
            raise AnchorResolutionError(
                f"camera stage {entry['stage']!r} resolves to a non-positive "
                f"window ({start} -> {end} demo_us)")
        return start, end

    def resolve_window_us(self, recipe) -> tuple[int, int]:
        """The union window across every stage."""
        if not self.stages:
            raise AnchorResolutionError("camera intent has no stages")
        windows = [self.resolve_stage_window_us(recipe, e) for e in self.stages]
        return min(w[0] for w in windows), max(w[1] for w in windows)


@dataclass(frozen=True)
class CameraCompilation:
    """A POINTER to a row in ``camera_compilations`` (cam10_writer.py).

    Deliberately a reference, not a copy of the artifact: the compiled
    ``.cam10`` is an execution artifact with its own lifetime, and embedding
    it here would make ``scene_id`` change every time the compiler is
    upgraded. ``artifact_hash`` is the join key.
    """
    backend: str
    compiler_version: str
    artifact_hash: str
    runtime_version: str
    camera_name: str
    effective_hz: float
    sample_count: int
    collision_status: str

    def __post_init__(self) -> None:
        if self.backend not in (cam10_writer.BACKEND_NATIVE_CAM10,
                                "FREECAM_SAMPLED"):
            raise ValueError(f"unknown camera backend: {self.backend!r}")


@dataclass(frozen=True)
class FxCue:
    """One effect, anchored semantically, with an explicit intensity level.

    ``parameters["binding"]`` selects how the effect reaches the engine:

    * ``"CUE"`` (default) — an arbitrarily named script fired ONCE by
      ``at <t> runfx <name> [x y z]``.
    * ``"HOOK"`` — one of the fixed script names the engine calls every
      frame (``weapon/rocket/trail``, ``player/torso/trail``, ...,
      cg_fx_scripts.c:6940-7440). Defining the name IS what arms it; no
      console command exists or is needed, so this compiles to no cfg line.

    The distinction is load-bearing, not bookkeeping: a one-shot ``runfx``
    cannot produce a trail, because ``interval``/``distance`` sub-emitters
    need successive frames to run over. Modelling a trail as a CUE yields a
    single puff at the muzzle that is easy to mistake for a working trail.
    """
    effect_type: str
    semantic_anchor: str
    offset_us: int = 0
    duration_us: int = 0
    intensity_level: str = INTENSITY_SUBTLE
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def binding(self) -> str:
        return self.parameters.get("binding", BINDING_CUE)

    def __post_init__(self) -> None:
        binding = self.parameters.get("binding", BINDING_CUE)
        if binding not in FX_BINDINGS:
            raise ValueError(
                f"parameters['binding'] must be one of {list(FX_BINDINGS)}, "
                f"got {binding!r}")
        if binding == BINDING_HOOK and self.parameters.get("world_pos"):
            raise ValueError(
                "a HOOK effect cannot take world_pos — the engine supplies "
                "the hooked entity's own origin every frame")
        if self.intensity_level not in INTENSITY_LEVELS:
            raise ValueError(
                f"intensity_level must be one of {list(INTENSITY_LEVELS)}, "
                f"got {self.intensity_level!r}")
        for name in ("offset_us", "duration_us"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be a signed integer µs value")
        if self.duration_us < 0:
            raise ValueError("duration_us must not be negative")


@dataclass(frozen=True)
class OutputPasses:
    """Which render streams this scene wants (§23).

    ``depth`` maps to ``mme_saveDepth`` — an archived cvar that silently
    attaches a companion stream to EVERY later capture once set, which is
    exactly why it lives in ``pantheon_runtime.RUNTIME_BASELINE`` and is
    declared per-scene here rather than assumed.
    """
    beauty: bool = True
    depth: bool = False
    depth_range: int = 2000
    depth_focus: int = 0

    def __post_init__(self) -> None:
        if not self.beauty and not self.depth:
            raise ValueError("a scene must request at least one output pass")


@dataclass(frozen=True)
class PantheonScene:
    recipe_id: str
    camera_intent: CameraIntent
    camera_compilation: CameraCompilation | None = None
    fx_stack: tuple[FxCue, ...] = ()
    visual_look: str = LOOK_ORIGINAL
    output_passes: OutputPasses = field(default_factory=OutputPasses)
    hud_policy: str = "TR4SH_MASTER_POV_CLEAN"
    runtime_baseline_hash: str = ""
    music_anchor_slots: tuple[str, ...] = ()
    scene_schema_version: int = SCENE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.visual_look not in VISUAL_LOOKS:
            raise ValueError(
                f"visual_look must be one of {list(VISUAL_LOOKS)}, "
                f"got {self.visual_look!r}")
        if not self.recipe_id:
            raise ValueError("a scene must reference a recipe_id")
        if self.scene_schema_version != SCENE_SCHEMA_VERSION:
            raise ValueError(
                f"PantheonScene requires scene_schema_version="
                f"{SCENE_SCHEMA_VERSION}")

    # -- identity ---------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """The exact public JSON shape that gets hashed and persisted."""
        return json.loads(canonical_json(asdict(self)))

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @property
    def scene_id(self) -> str:
        return hashlib.sha256(
            self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PantheonScene":
        intent_raw = value["camera_intent"]
        intent = CameraIntent(
            mode=intent_raw["mode"],
            stages=tuple(intent_raw.get("stages") or ()),
            subject_anchor=intent_raw.get("subject_anchor"),
            params=dict(intent_raw.get("params") or {}),
        )
        comp_raw = value.get("camera_compilation")
        passes_raw = value.get("output_passes") or {}
        return cls(
            recipe_id=value["recipe_id"],
            camera_intent=intent,
            camera_compilation=(CameraCompilation(**comp_raw)
                                if comp_raw else None),
            fx_stack=tuple(
                FxCue(effect_type=c["effect_type"],
                      semantic_anchor=c["semantic_anchor"],
                      offset_us=int(c.get("offset_us", 0)),
                      duration_us=int(c.get("duration_us", 0)),
                      intensity_level=c.get("intensity_level",
                                            INTENSITY_SUBTLE),
                      parameters=dict(c.get("parameters") or {}))
                for c in value.get("fx_stack") or ()),
            visual_look=value.get("visual_look", LOOK_ORIGINAL),
            output_passes=OutputPasses(**passes_raw) if passes_raw
            else OutputPasses(),
            hud_policy=value.get("hud_policy", "TR4SH_MASTER_POV_CLEAN"),
            runtime_baseline_hash=value.get("runtime_baseline_hash", ""),
            music_anchor_slots=tuple(value.get("music_anchor_slots") or ()),
            scene_schema_version=int(
                value.get("scene_schema_version", SCENE_SCHEMA_VERSION)),
        )

    @classmethod
    def from_json(cls, blob: str) -> "PantheonScene":
        return cls.from_dict(json.loads(blob))

    # -- derived views ----------------------------------------------------

    def at_intensity(self, level: str) -> "PantheonScene":
        """The same scene with every non-OFF cue forced to ``level``.

        This is what makes an OFF/SUBTLE/HERO comparison honest: the three
        variants differ ONLY in ``intensity_level``, so camera, time, look
        and passes are provably identical (their ``scene_id`` differs, but
        ``camera_compilation.artifact_hash`` does not).
        """
        if level not in INTENSITY_LEVELS:
            raise ValueError(f"unknown intensity level: {level!r}")
        from dataclasses import replace
        return replace(self, fx_stack=tuple(
            replace(cue, intensity_level=level) for cue in self.fx_stack))


# ---------------------------------------------------------------------------
# FX compilation — the primitive choice the caller must never have to make
# ---------------------------------------------------------------------------

def compile_fx_cfg_lines(scene: PantheonScene, recipe) -> list[str]:
    """Turn the scene's fx stack into wolfcam console lines.

    Primitive selection (§17, free_wins_proof.md proof 1). Both console
    commands take the SAME optional trailing coordinates —
    ``CG_RunFx_f`` (cg_consolecmds.c:7662-7728) and ``CG_RunFxAt_f``
    (:7746-7817) each read ``[origin0..2] [dir0..2] [velocity0..2]`` from
    their arguments and fall back to a view snapshot for whatever is
    missing. The difference is WHEN that fallback snapshot is taken:

    * ``at <t> runfx <name>`` — the whole command is deferred, so the
      snapshot happens at FIRE time. Measured PASS.
    * ``runfxat <t> <name>`` — executes immediately and only re-emits
      ``at <t> runfx <name> <baked floats>``, so the snapshot happens at
      PARSE time. From ``cgamepostinit.cfg`` that is before the demo has
      even been seeked, i.e. the map origin. Measured as pure noise.

    Since ``runfx`` already accepts explicit coordinates, ``runfxat`` has
    no remaining advantage and this compiler never emits it at all:

    * cue carries ``parameters["world_pos"] = [x, y, z]``
      -> ``at <t> runfx <name> <x> <y> <z>`` (plus ``world_dir`` if given)
         — deferred AND explicit, so no snapshot is consulted for origin.
    * otherwise
      -> ``at <t> runfx <name>`` — origin resolved live at fire time.

    ``OFF`` cues emit nothing but are still anchor-resolved first, so an
    OFF variant fails on a broken anchor exactly like a HERO variant would.
    """
    lines: list[str] = []
    for cue in scene.fx_stack:
        # Resolved for every cue, including OFF and HOOK, so a broken anchor
        # fails identically at every intensity and binding.
        fire_ms = resolve_anchor_ms(recipe, cue.semantic_anchor, cue.offset_us)
        if cue.intensity_level == INTENSITY_OFF:
            continue
        if cue.binding == BINDING_HOOK:
            # Armed by the .fx script's mere existence (pantheon_fx.py).
            # There is no console command to emit, and inventing one would
            # be worse than emitting nothing.
            continue
        name = cue.parameters.get("fx_name")
        if not name:
            raise FxCompileError(
                f"fx cue {cue.effect_type!r} has no parameters['fx_name'] — "
                "there is no effect script to fire")
        _validate_fx_token(name)
        parts = [f"at {fire_ms} runfx {name}"]
        world = cue.parameters.get("world_pos")
        if world is not None:
            if len(world) != 3:
                raise FxCompileError(
                    f"fx cue {cue.effect_type!r} world_pos must be [x, y, z]")
            parts.append(" ".join(f"{float(v):.2f}" for v in world))
            direction = cue.parameters.get("world_dir")
            if direction is not None:
                if len(direction) != 3:
                    raise FxCompileError(
                        f"fx cue {cue.effect_type!r} world_dir must be "
                        "[x, y, z]")
                parts.append(" ".join(f"{float(v):.4f}" for v in direction))
        elif cue.parameters.get("world_dir") is not None:
            # dir is positional argument 5-7; it cannot be supplied without
            # origin, and silently dropping it would be a lie.
            raise FxCompileError(
                f"fx cue {cue.effect_type!r} sets world_dir without "
                "world_pos — dir is positional and requires origin first")
        lines.append(" ".join(parts))
    return lines


def _validate_fx_token(token: str) -> str:
    """CS-5: an fx name reaches a cfg oneliner, so it must not smuggle."""
    if any(ch in token for ch in (";", "\n", "\r", '"', " ")):
        raise FxCompileError(f"unsafe fx script name: {token!r}")
    return token


# ---------------------------------------------------------------------------
# Persistence — pantheon_scenes in cinematic.db
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pantheon_scenes (
    scene_id        TEXT PRIMARY KEY,
    recipe_id       TEXT NOT NULL,
    visual_look     TEXT NOT NULL,
    camera_backend  TEXT,
    camera_artifact TEXT,
    created_utc     TEXT NOT NULL,
    scene_json      TEXT NOT NULL
)
"""


def _connect(db_path: str | Path | None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(_SCHEMA)
    return con


def persist_scene(scene: PantheonScene,
                  db_path: str | Path | None = None) -> str:
    con = _connect(db_path)
    comp = scene.camera_compilation
    try:
        con.execute(
            "INSERT OR REPLACE INTO pantheon_scenes "
            "(scene_id, recipe_id, visual_look, camera_backend, "
            " camera_artifact, created_utc, scene_json) VALUES (?,?,?,?,?,?,?)",
            (scene.scene_id, scene.recipe_id, scene.visual_look,
             comp.backend if comp else None,
             comp.artifact_hash if comp else None,
             datetime.now(timezone.utc).isoformat(timespec="seconds"),
             scene.canonical_json()))
        con.commit()
    finally:
        con.close()
    return scene.scene_id


def load_scene(scene_id: str,
               db_path: str | Path | None = None) -> PantheonScene | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT scene_json FROM pantheon_scenes WHERE scene_id = ?",
            (scene_id,)).fetchone()
    finally:
        con.close()
    return PantheonScene.from_json(row[0]) if row else None


def list_scenes(db_path: str | Path | None = None) -> list[dict]:
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT scene_id, recipe_id, visual_look, camera_backend, "
            "camera_artifact, created_utc FROM pantheon_scenes "
            "ORDER BY created_utc, scene_id").fetchall()
    finally:
        con.close()
    keys = ("scene_id", "recipe_id", "visual_look", "camera_backend",
            "camera_artifact", "created_utc")
    return [dict(zip(keys, r)) for r in rows]
