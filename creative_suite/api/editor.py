"""Editor API — state, OTIO export, proxies, render bridge.

GET    /api/editor/state/{part}             → full EditorState JSON
PUT    /api/editor/state/{part}             → replace (validated)
PATCH  /api/editor/state/{part}             → RFC 6902 jsonpatch
GET    /api/editor/otio/{part}              → OTIO `.otio` file download
GET    /api/editor/chunk/{part}/{name}      → serve body chunk (full-res)
GET    /api/editor/proxy/{part}/{name}      → serve body-chunk proxy (960x540,
                                              auto-generates if missing)
GET    /api/editor/chunks/{part}            → list all chunks + durations
POST   /api/editor/render/{part}?mode=      → reuses phase1 rebuild pipeline
                                              after projecting state →
                                              flow_plan.json + overrides.txt
                                              (mode=preview|ship, default preview)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from creative_suite.api._render_worker import JobQueue
from creative_suite.editor import state as editor_state_mod
from creative_suite.editor.otio_bridge import write_otio
from creative_suite.editor.proxies import ensure_proxy
from creative_suite.editor.state import (
    EditorState,
    apply_jsonpatch,
    load_state,
    save_state,
    state_from_dict,
    state_to_dict,
)

router = APIRouter(prefix="/api/editor", tags=["editor"])


def _output_dir(request: Request) -> Path:
    return request.app.state.cfg.phase1_output_dir


def _chunks_dir(output_dir: Path, part: int) -> Path:
    return output_dir / f"_part{part:02d}_v6_body_chunks"


def _proxies_dir(output_dir: Path, part: int) -> Path:
    return output_dir / "_proxies" / f"part{part:02d}"


@router.get("/state/{part}")
def get_state(part: int, request: Request) -> dict[str, Any]:
    state = load_state(_output_dir(request), part)
    return state_to_dict(state)


class StateReplaceBody(BaseModel):
    state: dict[str, Any]


@router.put("/state/{part}")
def put_state(part: int, body: StateReplaceBody, request: Request) -> dict[str, Any]:
    try:
        incoming = state_from_dict(body.state)
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(400, f"invalid state: {e}")
    if incoming.part != part:
        raise HTTPException(400, f"state.part={incoming.part} != url part={part}")
    save_state(_output_dir(request), incoming)
    return state_to_dict(incoming)


class PatchBody(BaseModel):
    ops: list[dict[str, Any]]


@router.patch("/state/{part}")
def patch_state(part: int, body: PatchBody, request: Request) -> dict[str, Any]:
    state = load_state(_output_dir(request), part)
    try:
        new_state = apply_jsonpatch(state, body.ops)
    except Exception as e:
        raise HTTPException(400, f"patch failed: {e}")
    save_state(_output_dir(request), new_state)
    return state_to_dict(new_state)


@router.get("/otio/{part}")
def get_otio(part: int, request: Request) -> Response:
    output_dir = _output_dir(request)
    state = load_state(output_dir, part)
    out_path = output_dir / f"part{part:02d}.otio"
    chunk_dir = _chunks_dir(output_dir, part)
    write_otio(state, out_path, chunk_dir if chunk_dir.exists() else None)
    return FileResponse(
        str(out_path),
        media_type="application/vnd.pixar.opentimelineio+json",
        filename=out_path.name,
    )


@router.get("/chunks/{part}")
def list_chunks(part: int, request: Request) -> dict[str, Any]:
    output_dir = _output_dir(request)
    state = load_state(output_dir, part)
    chunk_dir = _chunks_dir(output_dir, part)
    rows: list[dict[str, Any]] = []
    for c in state.clips:
        src = chunk_dir / c.chunk
        rows.append({
            "chunk": c.chunk,
            "tier": c.tier,
            "section_role": c.section_role,
            "duration": c.duration,
            "in_s": c.in_s,
            "out_s": c.out_s,
            "removed": c.removed,
            "slow": c.slow,
            "exists": src.exists(),
            "size": src.stat().st_size if src.exists() else 0,
        })
    return {
        "part": part,
        "chunk_dir": str(chunk_dir),
        "count": len(rows),
        "chunks": rows,
    }


@router.get("/chunk/{part}/{name}")
def serve_chunk(part: int, name: str, request: Request) -> FileResponse:
    # Basename-normalize + reject traversal
    safe = Path(name).name
    src = _chunks_dir(_output_dir(request), part) / safe
    if not src.exists():
        raise HTTPException(404, f"chunk not found: {safe}")
    return FileResponse(str(src), media_type="video/mp4")


@router.get("/proxy/{part}/{name}")
def serve_proxy(part: int, name: str, request: Request) -> FileResponse:
    safe = Path(name).name
    output_dir = _output_dir(request)
    src = _chunks_dir(output_dir, part) / safe
    if not src.exists():
        raise HTTPException(404, f"chunk not found: {safe}")
    proxies_dir = _proxies_dir(output_dir, part)
    try:
        proxy = ensure_proxy(src, proxies_dir)
    except FileNotFoundError as e:
        raise HTTPException(500, str(e))
    return FileResponse(str(proxy), media_type="video/mp4")


@router.post("/render/{part}")
async def render_part(
    part: int,
    request: Request,
    mode: str = "preview",
    tag: str | None = None,
) -> dict[str, Any]:
    """Project EditorState → `overrides.txt` (with removed/slow/head_trim
    per clip), then kick off the existing phase1 rebuild pipeline.
    `mode=preview` uses CRF 23 veryfast (Rule P1-J v2); `mode=ship` uses
    the final quality ceiling.
    """
    if mode not in ("preview", "ship"):
        raise HTTPException(400, "mode must be preview|ship")

    output_dir = _output_dir(request)
    state = load_state(output_dir, part)

    # Project editor state onto overrides.txt (Tier 1 render bridge).
    from creative_suite.overrides.file_io import ClipOverride, write_overrides
    entries: list[ClipOverride] = []
    for c in state.clips:
        head_trim = c.in_s if c.in_s > 0 else None
        tail_trim = (c.duration - c.out_s) if c.out_s < c.duration else None
        entries.append(ClipOverride(
            chunk=c.chunk,
            slow=c.slow,
            slow_window=c.slow_window_s,
            head_trim=head_trim,
            tail_trim=tail_trim,
            section_role=c.section_role,
            removed=c.removed,
        ))
    overrides_path = output_dir / f"part{part:02d}_overrides.txt"
    write_overrides(overrides_path, entries)

    # Kick the existing rebuild job (it honors overrides via
    # phase1/clip_filter.py — Tier 1 clip-removal filter already wired).
    from typing import Awaitable, Callable
    job_queue: JobQueue = request.app.state.job_queue
    from creative_suite.api._rebuild_job import rebuild_part as _rebuild_part

    cfg = request.app.state.cfg
    repo_root = Path(__file__).resolve().parents[2]

    async def _run(emit: Callable[[str, int, str], Awaitable[None]]) -> None:
        await _rebuild_part(
            emit=emit,
            part=part,
            tag=tag or f"editor_{mode}",
            notes=f"editor render, mode={mode}",
            mode=mode,
            output_dir=output_dir,
            db_path=cfg.db_path,
            repo_root=repo_root,
        )

    try:
        job_id = job_queue.submit(_run)
    except RuntimeError:
        raise HTTPException(409, "another render is running")
    return {
        "ok": True,
        "job_id": job_id,
        "part": part,
        "mode": mode,
        "overrides_written": str(overrides_path),
        "n_clips": len(entries),
        "n_removed": sum(1 for e in entries if e.removed),
    }
