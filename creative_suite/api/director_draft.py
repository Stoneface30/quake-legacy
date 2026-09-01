"""DIRECTOR panel draft state — directive §31-40.

The /frags DIRECTOR panel lets the user dial a camera / FX / look recipe for
one frag *before* anything is captured. Directive §37-38 is explicit that
experimentation must be cheap and reversible: every knob turn edits an
UNSAVED DRAFT, and only an explicit SAVE RECIPE commits. Nothing here writes
a file, spawns wolfcam, or renders an MP4 (§40 — no permanent artifact spam);
drafts live in process memory and die with the server.

Honesty contract (§39): none of these controls hot-swap a video that is
already on screen. A wolfcam capture is the only thing that can realize a
camera/FX/look change, and this cycle the capture staging dir is owned by
another workstream — so the API reports, per section, whether the change is
LIVE or needs a CAPTURE_REFRESH, and the panel says "UPDATING PREVIEW /
capture refresh required" rather than implying the picture already changed.

Persistence on SAVE goes through the existing shot_plan pipeline
(cinematic.db), the same store director.py's save_recipe already uses.
frag_recognition.db and demo_v2.db are never opened for writing anywhere in
this module — they are read-only by project hard rule.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse

from creative_suite.api.frags import _frag_window, _load_frag_with_master
from creative_suite.engine import (cam10_writer, camera_compiler_v2,
                                   director_preview, master_profile,
                                   review_proxy, shot_plan)
from creative_suite.engine.timeline import Timeline

router = APIRouter()

# Tests point this at a tmp cinematic.db; None = shot_plan.DEFAULT_DB.
SHOT_PLAN_DB_PATH: Path | None = None

# --------------------------------------------------------------------------
# Vocabulary. Deliberately a small, human vocabulary — §32 forbids exposing
# raw engine command strings or cvars to the panel. "damping" is a director
# word; "cg_camera*" is not, and never leaves the engine layer.
# --------------------------------------------------------------------------
CAMERA_MODES: tuple[str, ...] = ("FPV", "ORBIT", "CHASE", "PROJECTILE", "FREECAM")
FX_LEVELS: tuple[str, ...] = ("OFF", "SUBTLE", "HERO")
LOOKS: tuple[str, ...] = ("ORIGINAL", "UHD", "PANTHEON")

# §33: NATIVE_CAM10 is the runtime backend a normal user gets. The
# FREECAM_SAMPLED fallback stays selectable, but only behind the panel's
# developer toggle — it is not a creative choice.
DEFAULT_BACKEND = cam10_writer.BACKEND_NATIVE_CAM10
BACKENDS: tuple[str, ...] = (cam10_writer.BACKEND_NATIVE_CAM10,
                             camera_compiler_v2.BACKEND_FREECAM_SAMPLED)

# Per-mode control visibility — the panel only draws what the mode actually
# uses (§32: "expose only useful controls").
MODE_CONTROLS: dict[str, tuple[str, ...]] = {
    "FPV": ("fov",),
    "ORBIT": ("distance", "height", "fov", "damping"),
    "CHASE": ("distance", "height", "side_offset", "fov", "damping"),
    "PROJECTILE": ("distance", "height", "fov", "damping"),
    "FREECAM": ("fov", "damping"),
}

# name -> (label, unit, min, max, step)
CONTROL_SPECS: dict[str, tuple[str, str, float, float, float]] = {
    "distance": ("Distance", "u", 0.0, 2048.0, 8.0),
    "height": ("Height", "u", -512.0, 1024.0, 4.0),
    "side_offset": ("Side offset", "u", -1024.0, 1024.0, 4.0),
    "fov": ("FOV", "deg", 30.0, 140.0, 1.0),
    "damping": ("Damping", "", 0.0, 1.0, 0.05),
}

DEFAULT_CAMERA: dict[str, Any] = {
    "mode": "ORBIT", "distance": 220.0, "height": 64.0,
    "side_offset": 0.0, "fov": 90.0, "damping": 0.35,
}
DEFAULT_FX: dict[str, Any] = {"rocket_fx": "OFF", "ghost": "OFF"}
DEFAULT_LOOK: dict[str, Any] = {"look": "ORIGINAL", "show_depth": False}

DEFAULT_MUSIC: dict[str, Any] | None = None   # game audio only

SECTIONS: tuple[str, ...] = ("camera", "fx", "look", "music", "scene")

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

# §39 honesty map: what actually happens when a section changes. Nothing in
# the current pipeline hot-swaps — a wolfcam capture is the only renderer —
# so every section is CAPTURE_REFRESH and the UI says so out loud. If a live
# hot-swap path ever lands for one of these, flip its value to "LIVE" here
# and the panel's wording follows automatically.
REFRESH_MODEL: dict[str, dict[str, str]] = {
    "camera": {"mode": "CAPTURE_REFRESH",
               "note": "Camera changes need a new wolfcam capture."},
    "fx": {"mode": "CAPTURE_REFRESH",
           "note": "Rocket FX / ghost are baked at capture time."},
    "look": {"mode": "CAPTURE_REFRESH",
             "note": "Look packs are pk3 overrides — engine reload + capture."},
    "music": {"mode": "CAPTURE_REFRESH",
              "note": "Music is muxed into the preview render."},
}


def _default_draft(frag_id: int) -> dict[str, Any]:
    return {
        "frag_id": frag_id,
        "camera": dict(DEFAULT_CAMERA),
        "fx": dict(DEFAULT_FX),
        "look": dict(DEFAULT_LOOK),
        "music": DEFAULT_MUSIC,
        "backend": DEFAULT_BACKEND,
        "dirty": False,
        "saved_recipe_id": None,
        "preview": "CLEAN",
    }


# frag_id -> draft dict. In-memory by design (§37): a draft is scratch space,
# not a record. Nothing persists until POST .../draft/save.
_DRAFTS: dict[int, dict[str, Any]] = {}


def reset_store() -> None:
    """Test hook — drop every in-memory draft."""
    _DRAFTS.clear()


def _get_or_create(frag_id: int) -> dict[str, Any]:
    draft = _DRAFTS.get(frag_id)
    if draft is None:
        draft = _default_draft(frag_id)
        _DRAFTS[frag_id] = draft
    return draft


def _fail(detail: str) -> None:
    raise HTTPException(status_code=422, detail=detail)


def _apply_camera(camera: dict[str, Any], patch: dict[str, Any]) -> None:
    if not isinstance(patch, dict):
        _fail("camera patch must be an object")
    for key, value in patch.items():
        if key == "mode":
            if value not in CAMERA_MODES:
                _fail(f"unknown camera mode: {value}")
            camera["mode"] = value
            continue
        spec = CONTROL_SPECS.get(key)
        if spec is None:
            _fail(f"unknown camera control: {key}")
        try:
            num = float(value)
        except (TypeError, ValueError):
            _fail(f"{key} must be a number")
        lo, hi = spec[2], spec[3]
        if not (lo <= num <= hi):
            _fail(f"{key} out of range [{lo}, {hi}]: {num}")
        camera[key] = num


def _apply_fx(fx: dict[str, Any], patch: dict[str, Any]) -> None:
    if not isinstance(patch, dict):
        _fail("fx patch must be an object")
    for key, value in patch.items():
        if key not in DEFAULT_FX:
            _fail(f"unknown fx control: {key}")
        if value not in FX_LEVELS:
            _fail(f"invalid fx level for {key}: {value}")
        fx[key] = value


def _apply_look(look: dict[str, Any], patch: dict[str, Any]) -> None:
    if not isinstance(patch, dict):
        _fail("look patch must be an object")
    for key, value in patch.items():
        if key == "look":
            if value not in LOOKS:
                _fail(f"unknown look: {value}")
            look["look"] = value
        elif key == "show_depth":
            # §36: developer debug overlay, never a movie effect.
            if not isinstance(value, bool):
                _fail("show_depth must be a boolean")
            look["show_depth"] = value
        else:
            _fail(f"unknown look control: {key}")


def _apply_music(draft: dict[str, Any], patch: Any) -> None:
    """Select a MusicPlacement region from Music Intelligence V2 (§13).

    ``null`` clears it back to game audio only. Nothing here analyses,
    caches or re-derives music: the payload names a track by its existing
    ``track_hash`` and a source offset, which is exactly what
    ``scene_recipe.MusicPlacement`` already models.
    """
    if patch is None:
        draft["music"] = None
        return
    if not isinstance(patch, dict):
        _fail("music patch must be an object or null")
    unknown = set(patch) - {"track_hash", "source_start_us",
                            "program_edit_start_us", "source_end_us"}
    if unknown:
        _fail(f"unknown music field(s): {sorted(unknown)}")
    track_hash = str(patch.get("track_hash") or "")
    if _HASH_RE.match(track_hash) is None:
        _fail("music track_hash must be a lowercase sha256 digest")
    out: dict[str, Any] = {"track_hash": track_hash}
    for key, default in (("source_start_us", 0),
                         ("program_edit_start_us", 0)):
        value = patch.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(f"music {key} must be a non-negative integer")
        out[key] = value
    end = patch.get("source_end_us")
    if end is not None:
        if isinstance(end, bool) or not isinstance(end, int):
            _fail("music source_end_us must be an integer or null")
        if end <= out["source_start_us"]:
            _fail("music source region must have positive duration")
    out["source_end_us"] = end
    draft["music"] = out


def _public(draft: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(draft)
    out["controls"] = list(MODE_CONTROLS.get(draft["camera"]["mode"], ()))
    out["refresh"] = REFRESH_MODEL
    out["backend_is_default"] = draft["backend"] == DEFAULT_BACKEND
    return out


# --------------------------------------------------------------------------
# Schema endpoint — the panel builds itself from this, so the vocabulary
# lives in exactly one place (here) instead of being duplicated in JS.
# --------------------------------------------------------------------------

@router.get("/api/director/schema")
def director_schema() -> dict[str, Any]:
    return {
        "camera_modes": list(CAMERA_MODES),
        "mode_controls": {k: list(v) for k, v in MODE_CONTROLS.items()},
        "controls": [
            {"name": name, "label": label, "unit": unit,
             "min": lo, "max": hi, "step": step}
            for name, (label, unit, lo, hi, step) in CONTROL_SPECS.items()
        ],
        "fx_levels": list(FX_LEVELS),
        "fx_controls": [{"name": "rocket_fx", "label": "Rocket FX"},
                        {"name": "ghost", "label": "Ghost"}],
        "looks": list(LOOKS),
        "backends": list(BACKENDS),
        "default_backend": DEFAULT_BACKEND,
        "sections": list(SECTIONS),
        "refresh": REFRESH_MODEL,
        "defaults": {"camera": dict(DEFAULT_CAMERA), "fx": dict(DEFAULT_FX),
                     "look": dict(DEFAULT_LOOK)},
    }


# ------------------------------------------------------------------- draft

@router.get("/api/frags/{frag_id}/director/draft")
def get_draft(frag_id: int) -> dict[str, Any]:
    _load_frag_with_master(frag_id)   # 404 on unknown frag
    return _public(_get_or_create(frag_id))


@router.put("/api/frags/{frag_id}/director/draft")
def put_draft(frag_id: int,
              body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    _load_frag_with_master(frag_id)
    draft = _get_or_create(frag_id)
    if not isinstance(body, dict):
        _fail("draft patch must be an object")
    unknown = set(body) - {"camera", "fx", "look", "music", "backend"}
    if unknown:
        _fail(f"unknown draft section(s): {sorted(unknown)}")
    # Validate against a copy first so a rejected patch leaves the draft
    # untouched (a half-applied draft is worse than no change).
    staged = copy.deepcopy(draft)
    if "camera" in body:
        _apply_camera(staged["camera"], body["camera"])
    if "fx" in body:
        _apply_fx(staged["fx"], body["fx"])
    if "look" in body:
        _apply_look(staged["look"], body["look"])
    if "music" in body:
        _apply_music(staged, body["music"])
    if "backend" in body:
        if body["backend"] not in BACKENDS:
            _fail(f"unknown camera backend: {body['backend']}")
        staged["backend"] = body["backend"]
    staged["dirty"] = True
    staged["preview"] = "STALE"
    _DRAFTS[frag_id] = staged
    return _public(staged)


@router.post("/api/frags/{frag_id}/director/draft/reset")
def reset_draft(frag_id: int,
                body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """RESET CAMERA / FX / LOOK / SCENE (§38). ``scene`` resets everything,
    including the backend toggle, and clears the dirty flag."""
    _load_frag_with_master(frag_id)
    section = body.get("section", "scene")
    if section not in SECTIONS:
        _fail(f"unknown section: {section}")
    draft = _get_or_create(frag_id)
    if section == "scene":
        fresh = _default_draft(frag_id)
        fresh["saved_recipe_id"] = draft.get("saved_recipe_id")
        _DRAFTS[frag_id] = fresh
        return _public(fresh)
    if section == "music":
        draft["music"] = DEFAULT_MUSIC
    else:
        draft[section] = dict(
            {"camera": DEFAULT_CAMERA, "fx": DEFAULT_FX,
             "look": DEFAULT_LOOK}[section])
    draft["dirty"] = True
    draft["preview"] = "STALE"
    return _public(draft)


@router.post("/api/frags/{frag_id}/director/draft/save")
def save_draft(frag_id: int,
               body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """SAVE RECIPE (§37) — the ONLY endpoint here that persists anything.

    The draft becomes a shot_plans row in cinematic.db via the existing
    assemble/persist pipeline. Keyframes are intentionally empty: the
    resolved camera path is produced by camera_paths/camera_compiler_v2 at
    capture time from the subject tracks, and this cycle no capture is run
    from the browser (§40). What is committed is the RECIPE — mode plus its
    parameters, FX levels, look, backend — which is exactly what a later
    capture pass needs to reproduce the shot.
    """
    frag = _load_frag_with_master(frag_id)
    draft = _get_or_create(frag_id)

    demo_name = frag.get("demo_name") or ""
    demo_path, content_hash = review_proxy.demo_source(demo_name)
    if content_hash:
        demo_sha256 = str(content_hash)
    elif demo_path is not None and Path(demo_path).is_file():
        demo_sha256 = shot_plan.hash_demo(demo_path)
    else:
        demo_sha256 = ""

    mode = draft["camera"]["mode"]
    params = {k: draft["camera"][k] for k in MODE_CONTROLS.get(mode, ())}
    params.update({
        "mode": mode,
        "backend": draft["backend"],
        "rocket_fx": draft["fx"]["rocket_fx"],
        "ghost": draft["fx"]["ghost"],
        "look": draft["look"]["look"],
        "show_depth": bool(draft["look"]["show_depth"]),
        "source": "director_panel",
    })
    plan = shot_plan.assemble_shot_plan(
        demo_sha256=demo_sha256,
        event={"type": "director_panel", "t_ms": int(frag["server_time_ms"]),
               "frag_id": frag_id, "demo_name": demo_name},
        profile_id=master_profile.profile_id(
            master_profile.DIRECTOR_PROFILE_NAME),
        camera={"name": f"director_{mode.lower()}", "params": params},
        keyframes=[],
        timeline=Timeline(),
        effect_ids=list(body.get("effect_ids") or []),
        asset_pack_ids=list(body.get("asset_pack_ids") or []),
        base_fov=float(draft["camera"]["fov"]),
    )
    recipe_id = shot_plan.persist_shot_plan(plan, SHOT_PLAN_DB_PATH)
    draft["saved_recipe_id"] = recipe_id
    draft["dirty"] = False
    out = _public(draft)
    out["scene_recipe_id"] = recipe_id
    return out


# --------------------------------------------------------------- preview
# CHANGE IT -> REFRESH IT -> SEE IT (§12-13). These three endpoints are the
# contract the panel is written against; the engine work lives in
# creative_suite/engine/director_preview.py.
#
# §11 still holds: NOTHING here persists a recipe. Previewing writes an mp4
# and a row in editorial.db's director_previews; only SAVE RECIPE above
# commits a SceneRecipe.

def _preview_frag(frag_id: int) -> dict[str, Any]:
    """The frag record the preview pipeline needs, read-only."""
    from creative_suite.api.frags import _connect
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, demo_name, content_hash, server_time_ms, weapon_name,"
            " attributes, recognition_version FROM recognized_frags "
            "WHERE id = ?", (frag_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="frag not found")
    frag = dict(row)
    import json as _json
    try:
        frag["attributes"] = _json.loads(frag.get("attributes") or "{}")
    except (TypeError, ValueError):
        frag["attributes"] = {}
    frag["master"] = _load_frag_with_master(frag_id).get("master")
    frag["window"] = _frag_window(frag)
    # The map name lives on the master clip row for captured frags and in the
    # recognition attributes otherwise; it is only used to load a BSP tracer
    # for collision checking, so an empty string degrades to "no check".
    frag["map"] = ((frag["attributes"] or {}).get("map")
                   or (frag["master"] or {}).get("map") or "")
    return frag


@router.post("/api/frags/{frag_id}/director/preview")
def request_preview(frag_id: int,
                    body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """REFRESH PREVIEW. Returns {preview_key, generation, state}.

    ``generation`` is the guard (§12): the caller polls its own key and must
    ignore a result whose generation is no longer the frag's latest. A cached
    READY artifact for this exact key comes straight back as READY without
    touching the engine.
    """
    frag = _preview_frag(frag_id)
    draft = _get_or_create(frag_id)
    demo_path, _hash = review_proxy.demo_source(str(frag["demo_name"]))
    try:
        result = director_preview.request_preview(
            frag, draft, demo_path=str(demo_path) if demo_path else None)
    except director_preview.PreviewBuildError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"preview_key": result["preview_key"],
            "generation": result["generation"], "state": result["state"]}


@router.get("/api/director/preview/{preview_key}")
def preview_state(preview_key: str) -> dict[str, Any]:
    state = director_preview.get_preview(preview_key)
    if state is None:
        raise HTTPException(status_code=404, detail="unknown preview key")
    return {"state": state["state"], "generation": state["generation"],
            "media_url": state["media_url"], "error": state["error"],
            "stale": state["stale"]}


@router.get("/api/director/preview/{preview_key}/media")
def preview_media(preview_key: str):
    path = director_preview.media_path(preview_key)
    if path is None:
        raise HTTPException(status_code=404, detail="preview media not ready")
    # FileResponse serves Range requests, which is what lets the browser
    # scrub the preview instead of re-downloading it.
    return FileResponse(str(path), media_type="video/mp4", filename=path.name)
