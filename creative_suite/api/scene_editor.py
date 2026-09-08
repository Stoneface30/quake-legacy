"""Scene Editor API — the cinematic workspace's read-mostly data plane.

Division of labour with ``/frags``: the frag browser is DISCOVERY (filter,
audition A/B/C, quick draft). This module serves the deep timeline
workspace at ``/scene-editor/<key>`` — one scene, every lane, three clocks.

WHAT THIS MODULE DOES NOT DO
============================
* No wolfcam capture. The capture staging directory is owned by another
  workstream this cycle; nothing here spawns a process or writes a frame.
* No score recalculation. Component scores come verbatim from the matcher's
  own output (``semantic-region-matcher@2.0.0``). The backend is authority;
  JavaScript renders numbers it is given (§33).
* No second music analyzer. The waveform envelope is downsampled from the
  cached ``energy_curve``; no audio is decoded here or in the browser.
* No writes to ``frag_recognition.db`` / ``demo_v2.db``. Read-only, always.

DRAFT DISCIPLINE (§53)
======================
Editor edits mutate an in-memory UNSAVED draft. ``SAVE RECIPE`` is the only
call that persists (into ``scene_recipes_v2`` + ``pantheon_scenes``).
Preview never auto-saves. Undo (§54) is a flat stack — music placement,
timewarp, camera, FX level, look — no branching history.

UI STATE IS NOT RECIPE STATE (§52)
==================================
Zoom, scroll, expanded lanes and panel widths ride along on the draft so a
reload restores the workspace, and they are provably excluded from both
``recipe_id`` and ``scene_id`` — see ``test_scene_editor.py``.
"""
from __future__ import annotations

import copy
import json
import re
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from creative_suite.engine import scene_editor_projection as proj
from creative_suite.engine.music_features_v2 import MusicFeatureStore
from creative_suite.engine.pantheon_scene import (CAMERA_STAGES, CameraIntent,
                                                  FxCue, PantheonScene,
                                                  VISUAL_LOOKS, persist_scene)
from creative_suite.engine.scene_recipe import (MusicPlacement, SceneRecipeV2,
                                                persist_scene_recipe)

router = APIRouter()

_DB_DIR = Path(__file__).parent.parent / "database"
# Module-level so tests can monkeypatch every path this router touches.
FRAG_DB_PATH = _DB_DIR / "frag_recognition.db"
DEMO_V2_DB_PATH = _DB_DIR / "demo_v2.db"
MUSIC_FEATURE_DB_PATH = _DB_DIR / "music_features_v2.db"
CINEMATIC_DB_PATH: Path | None = None      # None -> shot_plan.DEFAULT_DB
SCENE_RECIPE_DB_PATH = _DB_DIR / "cinematic.db"
MUSIC_AUDITION_DIR = Path(__file__).parents[2] / "output" / "demo_v2" / "music_auditions"

FX_LEVELS = ("OFF", "SUBTLE", "HERO")
CAMERA_MODES = ("FPV", "ORBIT", "CHASE", "PROJECTILE", "FREECAM")
# Semantic FX vocabulary. Director words only — no engine script names, no
# cvars, and emphatically no ``.cam10`` anywhere in the UI surface.
FX_TYPES = ("ROCKET_TRAIL", "IMPACT_ACCENT", "GHOST_TRAIL", "MUZZLE_BLOOM",
            "SPEED_STREAK", "DUST_KICK")

# Reason tags (§7). Stored against the review identity, never auto-trained
# on — they are the editor's memory of WHY, not a gradient signal.
REASON_TAGS = ("GREAT_BUILD", "GREAT_IMPACT", "GOOD_RHYTHM", "TOO_BUSY",
               "TOO_FLAT", "WRONG_STYLE", "BAD_VOCAL", "GAME_AUDIO_LOST",
               "GREAT_PHRASING", "WRONG_ENERGY")

_UNDO_DEPTH = 40
_TRACK_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

# frag_id -> draft. In-memory by design: a draft is scratch space, and a
# server restart should not resurrect half-finished experiments.
_DRAFTS: dict[int, dict[str, Any]] = {}


def reset_store() -> None:
    """Test hook — drop every in-memory draft and the envelope cache."""
    _DRAFTS.clear()
    proj.clear_envelope_cache()


def _fail(detail: str, status: int = 422) -> None:
    raise HTTPException(status_code=status, detail=detail)


# ---------------------------------------------------------------------------
# draft construction
# ---------------------------------------------------------------------------

def _evidence(frag_id: int) -> proj.SceneEvidence:
    try:
        return proj.SceneEvidence(frag_id, frag_db=FRAG_DB_PATH,
                                  demo_v2_db=DEMO_V2_DB_PATH)
    except KeyError:
        raise HTTPException(status_code=404, detail="frag not found") from None
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _default_draft(frag_id: int) -> dict[str, Any]:
    evidence = _evidence(frag_id)
    recipe = evidence.recipe()
    intent = proj.default_camera_intent(recipe)
    recommended, recommended_meta = _recommended_placement(frag_id)
    draft: dict[str, Any] = {
        "frag_id": frag_id,
        # --- recipe state: these five WILL move the hash ---
        "time_map": proj.segment_specs(recipe.time_map),
        "music_placement": copy.deepcopy(recommended),
        "camera_intent": _camera_payload(intent),
        "fx_stack": [],
        "visual_look": "ORIGINAL",
        "transition": {},
        # --- provenance for the placement (§6): recommended vs overridden ---
        "music_placement_recommended": copy.deepcopy(recommended),
        "music_placement_source": "RECOMMENDED" if recommended else "NONE",
        "music_audition_id": recommended_meta.get("display_slot"),
        "music_region_start_us": recommended_meta.get("region_start_us"),
        "music_matcher_version": recommended_meta.get("matcher_version"),
        # --- UI state: NEVER in the hash ---
        "zoom": 1.0, "scroll_us": 0, "expanded_lanes": list(proj.LANE_ORDER),
        "panel_widths": {"inspector": 340, "lanes": 148},
        "hidden_event_kinds": list(proj.DEFAULT_HIDDEN_EVENT_KINDS),
        "snap_enabled": False, "selected_lane": None,
        "selected_item_id": None, "playhead_us": 0,
        # --- bookkeeping ---
        "status": "CLEAN", "saved_recipe_id": None, "saved_scene_id": None,
        "undo": [],
    }
    return draft


def _get_or_create(frag_id: int) -> dict[str, Any]:
    draft = _DRAFTS.get(frag_id)
    if draft is None:
        draft = _default_draft(frag_id)
        _DRAFTS[frag_id] = draft
    return draft


def _push_undo(draft: dict[str, Any], label: str) -> None:
    """Snapshot RECIPE state only — undo restores the edit, not the view."""
    draft["undo"].append({"label": label,
                          "state": copy.deepcopy(proj.recipe_state(draft))})
    if len(draft["undo"]) > _UNDO_DEPTH:
        draft["undo"].pop(0)


def _placement_from(value: dict[str, Any] | None) -> MusicPlacement | None:
    if not value:
        return None
    try:
        return MusicPlacement(
            track_id=str(value["track_id"]),
            source_start_us=int(value["source_start_us"]),
            program_edit_start_us=int(value.get("program_edit_start_us", 0)),
            source_end_us=(None if value.get("source_end_us") is None
                           else int(value["source_end_us"])))
    except (KeyError, TypeError, ValueError) as exc:
        _fail(f"invalid music placement: {exc}")
        raise  # unreachable; keeps the type checker honest


def _camera_from(value: Any) -> CameraIntent:
    if not isinstance(value, dict):
        _fail("camera_intent must be an object")
    try:
        return CameraIntent(mode=str(value.get("mode", "FPV")),
                            stages=tuple(value.get("stages") or ()),
                            subject_anchor=value.get("subject_anchor"),
                            params=dict(value.get("params") or {}))
    except (TypeError, ValueError) as exc:
        _fail(f"invalid camera intent: {exc}")
        raise


def _camera_payload(intent: CameraIntent) -> dict[str, Any]:
    """The NORMALIZED draft shape for a camera intent.

    A partial patch (``{"mode": "ORBIT"}``) is legal on the wire and must
    stay legal, so the draft always stores the completed object rather than
    whatever the client happened to send. Storing the raw body instead let a
    later ``draft["camera_intent"]["stages"]`` raise KeyError and turn a
    perfectly reasonable request into a 500.
    """
    return {"mode": intent.mode, "stages": [dict(s) for s in intent.stages],
            "subject_anchor": intent.subject_anchor,
            "params": dict(intent.params)}


def _fx_from(items: list[dict[str, Any]]) -> tuple[FxCue, ...]:
    cues = []
    for raw in items:
        try:
            cues.append(FxCue(
                effect_type=str(raw["effect_type"]),
                semantic_anchor=str(raw["semantic_anchor"]),
                offset_us=int(raw.get("offset_us", 0)),
                duration_us=int(raw.get("duration_us", 0)),
                intensity_level=str(raw.get("intensity_level", "SUBTLE")),
                parameters=dict(raw.get("parameters") or {})))
        except (KeyError, TypeError, ValueError) as exc:
            _fail(f"invalid fx cue: {exc}")
    return tuple(cues)


def _recipe_for(draft: dict[str, Any]) -> SceneRecipeV2:
    """The draft's canonical recipe. Its ``recipe_id`` is the hash under test.

    UI state is not read here at all — that is the §52 guarantee expressed
    as code rather than as a promise.
    """
    evidence = _evidence(draft["frag_id"])
    base = evidence.recipe()
    try:
        time_map = proj.rebuild_time_map(draft["time_map"])
    except ValueError as exc:
        _fail(f"invalid time map: {exc}")
        raise
    return replace(
        base,
        time_map=time_map,
        music=_placement_from(draft["music_placement"]),
        camera=_camera_payload(_camera_from(draft["camera_intent"])),
        effects=tuple(dict(x) for x in draft["fx_stack"]),
        transition=dict(draft["transition"]),
    )


def _scene_for(draft: dict[str, Any], recipe: SceneRecipeV2) -> PantheonScene:
    return PantheonScene(recipe_id=recipe.recipe_id,
                         camera_intent=_camera_from(draft["camera_intent"]),
                         fx_stack=_fx_from(draft["fx_stack"]),
                         visual_look=draft["visual_look"])


def _public(draft: dict[str, Any]) -> dict[str, Any]:
    recipe = _recipe_for(draft)
    scene = _scene_for(draft, recipe)
    out = {k: copy.deepcopy(v) for k, v in draft.items() if k != "undo"}
    out["recipe_id"] = recipe.recipe_id
    out["scene_id"] = scene.scene_id
    out["duration_us"] = recipe.time_map[-1].edit_end_us
    out["undo_depth"] = len(draft["undo"])
    out["undo_next"] = draft["undo"][-1]["label"] if draft["undo"] else None
    # The exact key partition, served to the browser so the UI cannot drift
    # from the backend's idea of what is and is not identity.
    out["state_partition"] = {"recipe": list(proj.RECIPE_STATE_KEYS),
                              "ui": list(proj.UI_STATE_KEYS)}
    return out


# ---------------------------------------------------------------------------
# auditions — read straight from the matcher's manifest, never re-scored
# ---------------------------------------------------------------------------

def _manifest() -> dict[str, Any]:
    path = MUSIC_AUDITION_DIR / "manifest.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _auditions(frag_id: int) -> list[dict[str, Any]]:
    items = _manifest().get("items") or []
    rows = [x for x in items
            if isinstance(x, dict) and x.get("frag_id") == frag_id
            and x.get("audition_id") in {"A", "B", "C"}
            and isinstance(x.get("track_hash"), str)
            and _TRACK_HASH_RE.match(x["track_hash"])]
    rows.sort(key=lambda x: x["audition_id"])
    return rows


def _recommended_placement(frag_id: int
                           ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """(placement, provenance) for the matcher's own top pick.

    The placement stays a clean ``MusicPlacement`` payload — provenance is
    returned ALONGSIDE it, never smuggled inside, so nothing decorative can
    leak into the hashed recipe.

    ``A`` is the first row of ONE ranking run, not a persistent name: the
    identity that travels with a review is (scene, track, region, matcher).
    """
    rows = _auditions(frag_id)
    if not rows:
        return None, {}
    best = rows[0]
    placement = {"track_id": best["track_hash"],
                 "source_start_us": int(best["music_source_start_us"]),
                 "program_edit_start_us": 0, "source_end_us": None}
    meta = {"display_slot": best["audition_id"],
            "region_start_us": int(best["region_start_us"]),
            "matcher_version": best.get("matcher_version")}
    return placement, meta


def _audition_payload(frag_id: int, recipe_id: str) -> list[dict[str, Any]]:
    store = MusicFeatureStore(MUSIC_FEATURE_DB_PATH)
    tags = _read_reason_tags(frag_id)
    reviews = {(r["track_hash"], r["region_start_us"]): r
               for r in store.get_reviews(frag_id)}
    out = []
    for row in _auditions(frag_id):
        matcher = row.get("matcher_version", "")
        identity = proj.review_identity(
            frag_id=frag_id, track_hash=row["track_hash"],
            region_start_us=int(row["region_start_us"]),
            scene_recipe_id=str(row.get("scene_recipe_id") or recipe_id),
            matcher_version=str(matcher))
        review = reviews.get((row["track_hash"], int(row["region_start_us"])))
        out.append({
            # Display order only. Never the review key (§39).
            "display_slot": row["audition_id"],
            "review_identity": identity,
            "track_hash": row["track_hash"],
            "track_label": row.get("track_label"),
            "region_kind": row.get("region_kind"),
            "region_start_us": int(row["region_start_us"]),
            "region_end_us": row.get("region_end_us"),
            "matcher_version": matcher,
            "profile_derivation_version": row.get("profile_derivation_version"),
            "profile_type": row.get("profile_type"),
            # Verbatim from the matcher. Nothing here is recomputed (§33).
            "score": row.get("score", row.get("total")),
            "components": row.get("components") or {},
            "music_anchor_us": row.get("music_anchor_us"),
            "aligned_delta_us": row.get("aligned_delta_us"),
            "alignment_shift_us": row.get("alignment_shift_us"),
            "signed_delta_us": row.get("signed_delta_us"),
            "placement": {"track_id": row["track_hash"],
                          "source_start_us": int(row["music_source_start_us"]),
                          "program_edit_start_us": 0, "source_end_us": None},
            "video_url": f"/api/frags/{frag_id}/music-auditions/"
                         f"{row['audition_id']}/video",
            "decision": (review or {}).get("decision"),
            "notes": (review or {}).get("notes"),
            "reason_tags": sorted(tags.get(identity, ())),
        })
    return out


# --- reason tags ------------------------------------------------------------
# Stored on the SAME identity the music review already uses. Not a second
# verdict store: LOVE/KEEP/MAYBE/DROP stays in editorial_reviews, and the
# per-region favourite/reject stays in music_region_reviews_v2. This table
# only answers "why", and nothing trains on it automatically.
_TAG_SCHEMA = """
CREATE TABLE IF NOT EXISTS music_region_reason_tags (
    review_identity TEXT NOT NULL,
    frag_id         INTEGER NOT NULL,
    track_hash      TEXT NOT NULL,
    region_start_us INTEGER NOT NULL,
    scene_recipe_id TEXT NOT NULL,
    matcher_version TEXT NOT NULL,
    tag             TEXT NOT NULL,
    PRIMARY KEY (review_identity, tag)
)
"""


def _tag_conn() -> sqlite3.Connection:
    MUSIC_FEATURE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(MUSIC_FEATURE_DB_PATH, timeout=15)
    conn.execute(_TAG_SCHEMA)
    return conn


def _read_reason_tags(frag_id: int) -> dict[str, set[str]]:
    conn = _tag_conn()
    try:
        rows = conn.execute(
            "SELECT review_identity, tag FROM music_region_reason_tags "
            "WHERE frag_id = ?", (frag_id,)).fetchall()
    finally:
        conn.close()
    out: dict[str, set[str]] = {}
    for identity, tag in rows:
        out.setdefault(identity, set()).add(tag)
    return out


# ===========================================================================
# endpoints
# ===========================================================================

@router.get("/api/scene-editor/schema")
def scene_editor_schema() -> dict[str, Any]:
    """The editor builds its vocabulary from here, so it lives in one place."""
    return {
        "lane_order": list(proj.LANE_ORDER),
        "game_event_kinds": [{"kind": k, "source": s,
                              "hidden_by_default": k in proj.DEFAULT_HIDDEN_EVENT_KINDS}
                             for k, s in proj.GAME_EVENT_KINDS],
        "music_event_kinds": list(proj.MUSIC_EVENT_KINDS),
        "snap_target_kinds": list(proj.SNAP_TARGET_KINDS),
        "guide_pairs": [list(p) for p in proj.GUIDE_PAIRS],
        "camera_modes": list(CAMERA_MODES),
        "camera_stages": list(CAMERA_STAGES),
        "fx_types": list(FX_TYPES), "fx_levels": list(FX_LEVELS),
        "looks": list(VISUAL_LOOKS),
        "rates": [{"num": n, "den": d,
                   "label": "1.0" if (n, d) == (1, 1) else
                            ("0.75" if (n, d) == (3, 4) else "0.5")}
                  for n, d in proj.ALLOWED_RATES],
        "freeze_bounds_us": [proj.MIN_FREEZE_US, proj.MAX_FREEZE_US],
        "reason_tags": list(REASON_TAGS),
        "state_partition": {"recipe": list(proj.RECIPE_STATE_KEYS),
                            "ui": list(proj.UI_STATE_KEYS)},
        "projection_version": proj.PROJECTION_VERSION,
        # §31: these are unavailable for every migrated track. The UI must
        # print "unavailable", not a fabricated number.
        "confidence_availability": {
            "bpm_confidence": "UNAVAILABLE_FOR_MIGRATED_TRACKS",
            "beat_confidence": "UNAVAILABLE_FOR_MIGRATED_TRACKS"},
    }


@router.get("/api/scene-editor/resolve/{scene_key}")
def resolve_scene_key(scene_key: str) -> dict[str, Any]:
    """``frag-<id>`` / ``recipe-<sha256>`` / bare id -> the frag it edits.

    The URL carries identity, never state. A saved scene links itself as
    ``recipe-<sha>``; that hash is resolved back to its source frag through
    the recipe's own ``filters.source_frag_id``, which
    ``build_frag_scene_recipe`` writes and the hash therefore covers.
    """
    key = str(scene_key)
    if key.startswith("frag-"):
        key = key[5:]
    if key.isdigit():
        return {"scene_key": scene_key, "frag_id": int(key), "recipe_id": None}
    if key.startswith("recipe-"):
        key = key[7:]
    if not re.fullmatch(r"[0-9a-f]{64}", key):
        raise HTTPException(status_code=422,
                            detail="scene key must be frag-<id> or recipe-<sha256>")
    from creative_suite.engine.scene_recipe import load_scene_recipe
    recipe = load_scene_recipe(key, SCENE_RECIPE_DB_PATH)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    frag_id = (recipe.filters or {}).get("source_frag_id")
    if frag_id is None:
        raise HTTPException(
            status_code=422,
            detail="this recipe records no source frag; open it from /frags")
    return {"scene_key": scene_key, "frag_id": int(frag_id), "recipe_id": key}


@router.get("/api/scene-editor/{frag_id}")
def scene_editor_state(frag_id: int,
                       envelope_buckets: int = Query(
                           default=proj.DEFAULT_ENVELOPE_BUCKETS, ge=1,
                           le=proj.MAX_ENVELOPE_BUCKETS)) -> dict[str, Any]:
    """Everything the workspace needs for one scene, in one round trip."""
    draft = _get_or_create(frag_id)
    recipe = _recipe_for(draft)
    projection = proj.build_projection(
        frag_id, frag_db=FRAG_DB_PATH, demo_v2_db=DEMO_V2_DB_PATH,
        music_db=MUSIC_FEATURE_DB_PATH,
        recipe=recipe,
        camera_intent=_camera_from(draft["camera_intent"]),
        fx_cues=_fx_from(draft["fx_stack"]),
        visual_look=draft["visual_look"],
        envelope_buckets=envelope_buckets)
    return {
        "frag_id": frag_id,
        "projection": projection,
        "draft": _public(draft),
        "auditions": _audition_payload(frag_id, recipe.recipe_id),
        "why_this_matches": _why_this_matches(frag_id, recipe.recipe_id),
    }


def _why_this_matches(frag_id: int, recipe_id: str) -> dict[str, Any]:
    """§33 — surface the BACKEND's component scores. Nothing is computed.

    The component set differs per profile because the matcher weights them
    differently: a rocket scene lives or dies on the impact landing with an
    accent; an LG scene lives on cadence. Showing all nine components for
    every scene would bury that.
    """
    rows = _audition_payload(frag_id, recipe_id)
    if not rows:
        return {"available": False,
                "reason": "no ranked auditions for this scene yet"}
    profile_type = rows[0].get("profile_type") or "UNKNOWN"
    headline = {
        "IMPACT_PROJECTILE": ("anchor_fit", "structure_fit",
                              "energy_shape_fit", "phrase_fit"),
        "RHYTHMIC_TRACKING": ("rhythm_fit", "cadence_fit", "structure_fit",
                              "anchor_fit"),
        "TENSION_RELEASE": ("energy_shape_fit", "structure_fit",
                            "cadence_fit", "phrase_fit"),
    }.get(profile_type, ("anchor_fit", "structure_fit", "energy_shape_fit"))
    store = MusicFeatureStore(MUSIC_FEATURE_DB_PATH)
    profile = store.get_scene_profile(frag_id)
    evidence: dict[str, Any] = {}
    if profile:
        evidence = {
            "dominant_type": profile.get("dominant_type"),
            "duration_us": profile.get("duration_us"),
            "hero_anchor_us": profile.get("hero_anchor_us"),
            "hit_burst_count": len(profile.get("hit_bursts") or []),
            "contact_gap_count": len(profile.get("hit_cadence_us") or []),
            "projectile_flights_us": profile.get("projectile_flights_us") or [],
            "frag_count": len(profile.get("frag_cadence_us") or []) + 1,
            "round_win_us": profile.get("round_win_us"),
        }
    return {
        "available": True, "profile_type": profile_type,
        "headline_components": list(headline),
        "matcher_version": rows[0].get("matcher_version"),
        "profile_derivation_version": rows[0].get("profile_derivation_version"),
        "scene_evidence": evidence,
        "candidates": [{"display_slot": r["display_slot"],
                        "track_label": r["track_label"],
                        "score": r["score"], "components": r["components"],
                        "region_kind": r["region_kind"]} for r in rows],
        "authority": "backend (semantic-region-matcher); never recomputed in JS",
    }


# ------------------------------------------------------------------- draft

@router.get("/api/scene-editor/{frag_id}/draft")
def get_draft(frag_id: int) -> dict[str, Any]:
    return _public(_get_or_create(frag_id))


@router.put("/api/scene-editor/{frag_id}/draft")
def put_draft(frag_id: int,
              body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """Patch the draft. Recipe keys dirty it; UI keys never do (§52/§53)."""
    if not isinstance(body, dict):
        _fail("draft patch must be an object")
    draft = _get_or_create(frag_id)
    allowed = set(proj.RECIPE_STATE_KEYS) | set(proj.UI_STATE_KEYS)
    unknown = set(body) - allowed
    if unknown:
        _fail(f"unknown draft key(s): {sorted(unknown)}")
    touches_recipe = bool(set(body) & set(proj.RECIPE_STATE_KEYS))
    staged = copy.deepcopy(draft)
    if "visual_look" in body and body["visual_look"] not in VISUAL_LOOKS:
        _fail(f"unknown look: {body['visual_look']}")
    if "fx_stack" in body:
        if not isinstance(body["fx_stack"], list):
            _fail("fx_stack must be a list")
        _fx_from(body["fx_stack"])
    if "music_placement" in body:
        candidate = _placement_from(body["music_placement"])
        if candidate is not None:
            _validate_placement_window(
                candidate, _recipe_for(draft).time_map[-1].edit_end_us)
    if "transition" in body and not isinstance(body["transition"], dict):
        _fail("transition must be an object")
    if "time_map" in body:
        if not isinstance(body["time_map"], list):
            _fail("time_map must be a list of segment specs")
        try:
            proj.rebuild_time_map(body["time_map"])
        except (ValueError, TypeError, KeyError) as exc:
            _fail(f"invalid time map: {exc}")
    staged.update(copy.deepcopy(body))
    if "camera_intent" in body:
        # Normalize rather than trusting the wire shape — see _camera_payload.
        staged["camera_intent"] = _camera_payload(_camera_from(body["camera_intent"]))
    if "music_placement" in body:
        recommended = staged.get("music_placement_recommended")
        current = staged.get("music_placement")
        staged["music_placement_source"] = _placement_source(recommended, current)
    if touches_recipe:
        _push_undo(draft, ", ".join(sorted(set(body) & set(proj.RECIPE_STATE_KEYS))))
        staged["undo"] = draft["undo"]
        staged["status"] = "UNSAVED"
    else:
        staged["undo"] = draft["undo"]
    _DRAFTS[frag_id] = staged
    return _public(staged)


def _validate_placement_window(placement: MusicPlacement,
                               duration_us: int) -> None:
    """The scene's whole edit window must land inside the actual track.

    Dragging far enough left produced a negative ``source_start_us``, which
    the schema accepts (it only asks for an integer) but no renderer can
    honour — the scene would open on audio that does not exist. Refused
    here with the legal range spelled out, so the browser can clamp instead
    of guessing.
    """
    feature = MusicFeatureStore(MUSIC_FEATURE_DB_PATH).get(placement.track_id)
    if feature is None:
        return                      # unknown track: nothing to bound against
    start = placement.source_start_us - placement.program_edit_start_us
    end = start + duration_us
    if start < 0 or end > feature.duration_us:
        _fail(f"placement puts the scene outside the track: "
              f"[{start}, {end}] us is not inside [0, {feature.duration_us}] us")


def _placement_source(recommended: dict[str, Any] | None,
                      current: dict[str, Any] | None) -> str:
    """RECOMMENDED vs USER_OVERRIDDEN — both are kept, never one or other."""
    if current is None:
        return "NONE"
    if not recommended:
        return "USER_OVERRIDDEN"
    same = (str(recommended.get("track_id")) == str(current.get("track_id"))
            and int(recommended.get("source_start_us", -1))
            == int(current.get("source_start_us", -2))
            and int(recommended.get("program_edit_start_us", 0))
            == int(current.get("program_edit_start_us", 0)))
    return "RECOMMENDED" if same else "USER_OVERRIDDEN"


@router.post("/api/scene-editor/{frag_id}/draft/undo")
def undo_draft(frag_id: int) -> dict[str, Any]:
    """Flat undo (§54). No branching history — this is an edit bay, not git."""
    draft = _get_or_create(frag_id)
    if not draft["undo"]:
        _fail("nothing to undo", status=409)
    snapshot = draft["undo"].pop()
    draft.update(copy.deepcopy(snapshot["state"]))
    draft["music_placement_source"] = _placement_source(
        draft.get("music_placement_recommended"), draft.get("music_placement"))
    draft["status"] = "UNSAVED" if draft["undo"] else "CLEAN"
    return _public(draft)


@router.post("/api/scene-editor/{frag_id}/draft/reset")
def reset_draft(frag_id: int) -> dict[str, Any]:
    _DRAFTS.pop(frag_id, None)
    return _public(_get_or_create(frag_id))


@router.post("/api/scene-editor/{frag_id}/draft/save")
def save_draft(frag_id: int) -> dict[str, Any]:
    """SAVE RECIPE — the ONLY call in this module that persists anything.

    Two rows, two identities: the canonical recipe (WHAT/WHEN) and the
    PANTHEON scene (HOW IT LOOKS). Neither is a copy of the other.
    """
    draft = _get_or_create(frag_id)
    recipe = _recipe_for(draft)
    scene = _scene_for(draft, recipe)
    recipe_id = persist_scene_recipe(recipe, SCENE_RECIPE_DB_PATH)
    scene_id = persist_scene(scene, CINEMATIC_DB_PATH)
    draft["saved_recipe_id"] = recipe_id
    draft["saved_scene_id"] = scene_id
    draft["status"] = "CLEAN"
    draft["undo"] = []
    return _public(draft)


# ------------------------------------------------------------ music control

@router.post("/api/scene-editor/{frag_id}/music/select")
def select_audition(frag_id: int,
                    body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """A/B/C switching (§38) — the hard architecture test, as an endpoint.

    ONLY ``music_placement`` moves. Source window, TimeMap, camera, FX, look
    and transition are untouched, so the gameplay edit is byte-identical
    across all three. If that ever stops being true, the test that compares
    two projections' TimeMaps fails loudly.
    """
    slot = body.get("display_slot")
    rows = _auditions(frag_id)
    row = next((r for r in rows if r["audition_id"] == slot), None)
    if row is None:
        _fail(f"no audition in display slot {slot!r}")
        raise
    draft = _get_or_create(frag_id)
    _push_undo(draft, "music placement")
    draft["music_placement"] = {
        "track_id": row["track_hash"],
        "source_start_us": int(row["music_source_start_us"]),
        "program_edit_start_us": 0, "source_end_us": None}
    draft["music_audition_id"] = slot
    draft["music_region_start_us"] = int(row["region_start_us"])
    draft["music_placement_source"] = _placement_source(
        draft.get("music_placement_recommended"), draft["music_placement"])
    draft["status"] = "UNSAVED"
    return _public(draft)


@router.put("/api/scene-editor/{frag_id}/music/placement")
def set_placement(frag_id: int,
                  body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Drag the music. This changes MusicPlacement and NOTHING ELSE (§29).

    Gameplay timing is not a function of where the music sits, and this
    endpoint has no access to the TimeMap to make it one.
    """
    placement = _placement_from(body.get("placement") or body)
    if placement is None:
        _fail("a placement is required")
        raise
    draft = _get_or_create(frag_id)
    _validate_placement_window(placement, _recipe_for(draft).time_map[-1].edit_end_us)
    _push_undo(draft, "music placement")
    draft["music_placement"] = {
        "track_id": placement.track_id,
        "source_start_us": placement.source_start_us,
        "program_edit_start_us": placement.program_edit_start_us,
        "source_end_us": placement.source_end_us}
    draft["music_placement_source"] = _placement_source(
        draft.get("music_placement_recommended"), draft["music_placement"])
    draft["status"] = "UNSAVED"
    return _public(draft)


@router.get("/api/scene-editor/music/{track_hash}/envelope")
def track_envelope(track_hash: str,
                   buckets: int = Query(default=proj.DEFAULT_ENVELOPE_BUCKETS,
                                        ge=1, le=proj.MAX_ENVELOPE_BUCKETS)
                   ) -> dict[str, Any]:
    """Browser-sized envelope, cached on (track hash, feature version)."""
    if not _TRACK_HASH_RE.match(track_hash):
        _fail("track_hash must be a lowercase sha256 digest")
    feature = MusicFeatureStore(MUSIC_FEATURE_DB_PATH).get(track_hash)
    if feature is None:
        raise HTTPException(status_code=404, detail="track not analyzed")
    return {"track_hash": track_hash,
            "extractor_version": feature.extractor_version,
            "duration_us": feature.duration_us,
            "source": "cached energy_curve (no audio decoded)",
            "buckets": buckets,
            "envelope": proj.waveform_envelope(feature, buckets)}


# ------------------------------------------------------------- reason tags

@router.get("/api/scene-editor/{frag_id}/reason-tags")
def get_reason_tags(frag_id: int) -> dict[str, Any]:
    return {"frag_id": frag_id, "vocabulary": list(REASON_TAGS),
            "tags": {k: sorted(v) for k, v in _read_reason_tags(frag_id).items()}}


@router.put("/api/scene-editor/{frag_id}/reason-tags")
def put_reason_tags(frag_id: int,
                    body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Tag a review IDENTITY, never a letter (§39).

    The identity is (scene, track hash, region, matcher version). Re-rank
    tomorrow and the same track/region carries the same tags even if it
    lands in a different slot.
    """
    identity = body.get("review_identity")
    tags = body.get("tags")
    if not isinstance(identity, str) or identity.count(":") != 4:
        _fail("review_identity must be "
              "'frag:track_hash:region_start_us:scene_recipe_id:matcher'")
    if not isinstance(tags, list) or any(t not in REASON_TAGS for t in tags):
        _fail(f"tags must be a subset of {list(REASON_TAGS)}")
    parts = str(identity).split(":")
    if int(parts[0]) != frag_id:
        _fail("review_identity does not belong to this frag")
    conn = _tag_conn()
    try:
        conn.execute("DELETE FROM music_region_reason_tags "
                     "WHERE review_identity = ?", (identity,))
        conn.executemany(
            "INSERT OR REPLACE INTO music_region_reason_tags VALUES "
            "(?,?,?,?,?,?,?)",
            [(identity, frag_id, parts[1], int(parts[2]), parts[3], parts[4],
              tag) for tag in tags])
        conn.commit()
    finally:
        conn.close()
    return {"frag_id": frag_id, "review_identity": identity,
            "tags": sorted(set(tags))}
