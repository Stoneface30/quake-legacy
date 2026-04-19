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


def _coerce_int(v: object) -> int | None:
    return v if isinstance(v, int) else None


def _coerce_str(v: object) -> str | None:
    return v if isinstance(v, str) else None


@router.post("/api/annotations")
def create_annotation(body: AnnotationBody, request: Request) -> dict[str, Any]:
    # Best-effort clip resolution — don't fail if unavailable.
    clip_index: int | None = None
    clip_filename: str | None = None
    demo_hint: str | None = None
    try:
        from creative_suite.api.clips import resolve
        r = resolve(body.part, body.mp4_time, request)
        clip_index = _coerce_int(r.get("clip_index"))
        clip_filename = _coerce_str(r.get("clip_filename"))
        demo_hint = _coerce_str(r.get("demo_hint"))
    except HTTPException:
        pass
    except Exception:
        pass
    ann = _store(request).create(AnnotationInput(
        part=body.part, mp4_time=body.mp4_time,
        description=body.description,
        avi_effect=body.avi_effect, dream_effect=body.dream_effect,
        tags=body.tags,
        clip_index=clip_index,
        clip_filename=clip_filename,
        demo_hint=demo_hint,
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
