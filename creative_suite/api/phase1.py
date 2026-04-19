# creative_suite/api/phase1.py
"""Phase 1 Cinema Suite API — Phase A ships GET endpoints only.

Editing (PUT flow-plan, rebuild), preview, and engine WebSocket land in
Phase B/C/D.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from creative_suite.api._waveform import compute_peaks
from creative_suite.api._render_worker import JobQueue
from creative_suite.api._rebuild_job import rebuild_part

router = APIRouter(prefix="/api/phase1", tags=["phase1"])

_ARTIFACT_KEYS = (
    "flow_plan", "music_structure", "music_plan", "beats",
    "sync_audit", "levels", "event_diversity",
)


def _output_dir(request: Request) -> Path:
    return request.app.state.cfg.phase1_output_dir


def _read_json_or_none(p: Path) -> Any:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@router.get("/parts")
def list_parts(request: Request) -> list[dict[str, Any]]:
    out = _output_dir(request)
    if not out.exists():
        return []
    parts: list[dict[str, Any]] = []
    for f in sorted(out.glob("part??_flow_plan.json")):
        try:
            n = int(f.name[4:6])
        except ValueError:
            continue
        parts.append({
            "part": n,
            "has_flow_plan": True,
            "flow_plan_path": str(f),
        })
    return parts


@router.get("/parts/{n}/artifacts")
def get_artifacts(n: int, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    return {key: _read_json_or_none(out / f"part{n:02d}_{key}.json") for key in _ARTIFACT_KEYS}


@router.get("/parts/{n}/flow-plan")
def get_flow_plan(n: int, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    p = out / f"part{n:02d}_flow_plan.json"
    if not p.exists():
        raise HTTPException(404, f"No flow plan for part {n}")
    return json.loads(p.read_text(encoding="utf-8"))


@router.get("/parts/{n}/versions")
def list_versions(n: int, request: Request) -> list[dict[str, Any]]:
    cfg = request.app.state.cfg
    con = sqlite3.connect(str(cfg.db_path))
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT * FROM render_versions WHERE part = ? ORDER BY created_at DESC",
            (n,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


@router.get("/parts/{n}/waveform")
def get_waveform(n: int, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    candidates = [
        out / f"part{n:02d}_stitched.wav",
        out / f"part{n:02d}_music.wav",
    ]
    wav = next((c for c in candidates if c.exists()), None)
    if wav is None:
        raise HTTPException(404, f"No wav for part {n}")
    peaks = compute_peaks(wav, target=6000)
    return {"peaks": peaks, "count": len(peaks), "source": wav.name}


class FlowPlanBody(BaseModel):
    clips: list[dict[str, Any]]
    seams: list[dict[str, Any]] = []
    notes: str = ""
    beat_snapped_offsets: list[dict[str, Any]] = []
    section_role_overrides: dict[str, str] = {}


@router.put("/parts/{n}/flow-plan")
def put_flow_plan(n: int, body: FlowPlanBody, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    jpath = out / f"part{n:02d}_flow_plan.json"
    jpath.write_text(json.dumps(body.model_dump(), indent=2), encoding="utf-8")
    return {"saved": True, "path": str(jpath)}


class RebuildBody(BaseModel):
    tag: str
    notes: str = ""
    mode: str = "ship"


@router.post("/parts/{n}/rebuild")
async def post_rebuild(
    n: int, body: RebuildBody, request: Request, response: Response
) -> dict[str, Any]:
    cfg = request.app.state.cfg
    q: JobQueue = request.app.state.job_queue
    output_dir = cfg.phase1_output_dir
    db_path = cfg.db_path
    repo_root = Path(__file__).resolve().parents[2]

    async def run(emit: Callable[[str, int, str], Awaitable[None]]) -> None:
        await rebuild_part(
            emit=emit, part=n, tag=body.tag, notes=body.notes, mode=body.mode,
            output_dir=output_dir, db_path=db_path, repo_root=repo_root,
        )

    try:
        jid = q.submit(run)
    except RuntimeError:
        response.status_code = 409
        return {"error": "busy"}
    return {"job_id": jid}


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str, request: Request) -> StreamingResponse:
    q: JobQueue = request.app.state.job_queue

    async def gen():
        last_idx = 0
        for _ in range(1200):  # ~10 min cap @ 500 ms
            evts = q.events(job_id)
            while last_idx < len(evts):
                yield f"data: {json.dumps(evts[last_idx])}\n\n"
                last_idx += 1
            status = q.status(job_id)
            if status in ("done", "failed"):
                final = {"phase": status, "pct": 100, "msg": "end"}
                yield f"data: {json.dumps(final)}\n\n"
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream")
