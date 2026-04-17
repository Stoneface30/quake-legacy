from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from creative_suite.annotations.store import AnnotationInput, AnnotationStore

router = APIRouter()


class AnnotationBody(BaseModel):
    part: int
    mp4_time: float
    description: str
    avi_effect: str | None = None
    dream_effect: str | None = None
    tags: list[str] = []


class AnnotationPatch(BaseModel):
    description: str | None = None
    avi_effect: str | None = None
    dream_effect: str | None = None
    tags: list[str] | None = None
    mp4_time: float | None = None


def _store(request: Request) -> AnnotationStore:
    return AnnotationStore(request.app.state.cfg)


@router.get("/api/annotations")
def list_annotations(part: int, request: Request) -> list[dict[str, Any]]:
    return [asdict(a) for a in _store(request).list_for_part(part)]


@router.post("/api/annotations")
def create_annotation(body: AnnotationBody, request: Request) -> dict[str, Any]:
    # Best-effort clip resolution — don't fail if unavailable.
    resolved: dict[str, Any] = {
        "clip_index": None, "clip_filename": None, "demo_hint": None,
    }
    try:
        from creative_suite.api.clips import resolve
        r = resolve(body.part, body.mp4_time, request)
        resolved["clip_index"] = r.get("clip_index")
        resolved["clip_filename"] = r.get("clip_filename")
        resolved["demo_hint"] = r.get("demo_hint")
    except HTTPException:
        pass
    except Exception:
        pass
    ann = _store(request).create(AnnotationInput(
        part=body.part, mp4_time=body.mp4_time,
        description=body.description,
        avi_effect=body.avi_effect, dream_effect=body.dream_effect,
        tags=body.tags,
        clip_index=resolved["clip_index"],
        clip_filename=resolved["clip_filename"],
        demo_hint=resolved["demo_hint"],
    ))
    return asdict(ann)


@router.patch("/api/annotations/{ann_id}")
def patch_annotation(
    ann_id: str, body: AnnotationPatch, request: Request,
) -> dict[str, Any]:
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        ann = _store(request).update(ann_id, **changes)
    except KeyError:
        raise HTTPException(404, ann_id)
    return asdict(ann)


@router.delete("/api/annotations/{ann_id}")
def delete_annotation(ann_id: str, request: Request) -> dict[str, bool]:
    try:
        _store(request).delete(ann_id)
    except KeyError:
        raise HTTPException(404, ann_id)
    return {"ok": True}
