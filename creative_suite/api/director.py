"""Live director session endpoints for /frags — Path A launcher.

See docs/reference/replay-runtime-feasibility.md: wolfcamql has no IPC
surface, so a browser cannot remote-control an already-running engine
window. What these endpoints do instead is open a VISIBLE wolfcamql window
seeked to a frag's moment with freecam armed, so the user can fly the camera
live at the keyboard. The frontend polls for captured keyframes (marked by
pressing creative_suite.engine.director_session.DIRECTOR_KEYBIND in the
wolfcam window) and, when done, asks this router to fold everything captured
into a shot_plans row via the existing camera_paths/timeline/shot_plan
pipeline.

Not a review-proxy job: no MP4 comes out of this flow, only a
scene_recipe_id. Kept as its own router (rather than growing frags.py
further) since it is a distinct feature surface with its own state.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from creative_suite.api.frags import _load_frag_with_master
from creative_suite.engine import director_session, review_proxy, shot_plan

router = APIRouter()

# session_id -> {frag_id, demo_name, demo_path, server_time_ms} captured at
# launch time so save_recipe (session-scoped, no frag_id in its own URL or
# body per the API contract) can rebuild the event/demo_sha256 later.
_LAUNCH_CONTEXT: dict[str, dict[str, Any]] = {}


@router.post("/api/frags/{frag_id}/director/launch")
def launch_director(frag_id: int,
                    body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    frag = _load_frag_with_master(frag_id)
    demo_name = frag["demo_name"]
    demo_path, _content_hash = review_proxy.demo_source(demo_name)
    if demo_path is None:
        raise HTTPException(status_code=404,
                            detail=f"demo not found in frags_rebuilt.db: {demo_name}")
    fov = float(body.get("fov") or director_session.DEFAULT_FOV)
    server_time_ms = int(frag["server_time_ms"])
    try:
        result = director_session.launch_session(demo_path, server_time_ms, fov=fov)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    session_id = result["session_id"]
    _LAUNCH_CONTEXT[session_id] = {
        "frag_id": frag_id,
        "demo_name": demo_name,
        "demo_path": str(demo_path),
        "server_time_ms": server_time_ms,
    }
    return {
        "session_id": session_id,
        "qconsole_path": str(result["qconsole_path"]),
        "frag_id": frag_id,
        "demo_name": demo_name,
        "seek_ms": server_time_ms,
        "fov": fov,
        "keybind": director_session.DIRECTOR_KEYBIND,
    }


@router.get("/api/director/{session_id}/keyframes")
def poll_director_keyframes(session_id: str,
                            since: int = Query(default=0, ge=0)) -> dict[str, Any]:
    try:
        return director_session.poll_keyframes(session_id, since_byte_offset=since)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail="unknown director session") from None


@router.post("/api/director/{session_id}/stop")
def stop_director(session_id: str) -> dict[str, Any]:
    try:
        result = director_session.stop_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail="unknown director session") from None
    return {"session_id": result["session_id"], "state": result["state"]}


@router.post("/api/director/{session_id}/save_recipe")
def save_director_recipe(session_id: str,
                         body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    if director_session.session_info(session_id) is None:
        raise HTTPException(status_code=404,
                            detail="unknown director session")
    ctx = _LAUNCH_CONTEXT.get(session_id, {})
    demo_path = ctx.get("demo_path")
    demo_sha256 = shot_plan.hash_demo(demo_path) if demo_path else ""
    event = {
        "type": "director_session",
        "t_ms": ctx.get("server_time_ms", 0),
        "frag_id": ctx.get("frag_id"),
        "demo_name": ctx.get("demo_name"),
    }
    try:
        scene_recipe_id = director_session.save_recipe(
            session_id, demo_sha256, event,
            effect_ids=body.get("effect_ids") or (),
            asset_pack_ids=body.get("asset_pack_ids") or (),
        )
    except KeyError:
        raise HTTPException(status_code=404,
                            detail="unknown director session") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return {"scene_recipe_id": scene_recipe_id}


# ── planning input ──────────────────────────────────────────────────────────
#
# The production side of the reviewer. Everything the director typed while
# curating -- the T1-T5 roles, the note beside a frag, the note on a jump
# pad, the note on the round -- is addressed here by scene_id and returned as
# planning input, loaded from storage.
#
# This endpoint is the reason the bridge is integration rather than a
# library. Before it existed the only caller was a test holding a Scene it
# had annotated itself, which could never have caught `build_scene` failing
# to load notes at all.

@router.get("/api/director/choreography_input/{scene_id}")
def choreography_input_for_scene(scene_id: str) -> dict[str, Any]:
    """Scene + ActionTruth + the director's own words, for one scene."""
    from creative_suite.engine import production_contract as pc
    try:
        ci = pc.build_choreography_input_for_scene(scene_id)
    except pc.SceneNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return ci.to_dict()
