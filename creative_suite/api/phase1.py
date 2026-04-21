# creative_suite/api/phase1.py
"""Phase 1 Cinema Suite API — Phase A ships GET endpoints only.

Editing (PUT flow-plan, rebuild), preview, and engine WebSocket land in
Phase B/C/D.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from creative_suite.api._waveform import compute_peaks
from creative_suite.api._render_worker import JobQueue
from creative_suite.api._rebuild_job import rebuild_part
from creative_suite.api._preview_job import run_preview_tier_a
from creative_suite.engine.supervisor import EngineSupervisor
from creative_suite.overrides.file_io import (
    ClipOverride, read_overrides, write_overrides,
)

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


@router.get("/parts/{n}/overrides")
def get_overrides(n: int, request: Request) -> list[dict[str, Any]]:
    out = _output_dir(request)
    return [e.__dict__ for e in read_overrides(out / f"part{n:02d}_overrides.txt")]


class OverrideBody(BaseModel):
    entries: list[dict[str, Any]]


@router.put("/parts/{n}/overrides")
def put_overrides(n: int, body: OverrideBody, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    p = out / f"part{n:02d}_overrides.txt"
    entries: list[ClipOverride] = []
    for e in body.entries:
        chunk = e.get("chunk")
        if not chunk or not isinstance(chunk, str):
            continue
        # Normalize to basename so the render-side filter (creative_suite/engine/clip_filter.py)
        # can match by Path.name regardless of whether the UI passed a full path.
        chunk = Path(chunk.replace("\\", "/")).name
        entries.append(ClipOverride(
            chunk=chunk,
            slow=e.get("slow"),
            slow_window=e.get("slow_window"),
            head_trim=e.get("head_trim"),
            tail_trim=e.get("tail_trim"),
            section_role=e.get("section_role"),
            removed=bool(e.get("removed", False)),
        ))
    write_overrides(p, entries)
    return {"saved": True, "count": len(entries)}


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


@router.get("/parts/{n}/music-override")
def get_music_override(n: int, request: Request) -> dict[str, Any]:
    out = _output_dir(request)
    p = out / f"part{n:02d}_music_override.json"
    if not p.exists(): return {}
    return json.loads(p.read_text(encoding="utf-8"))


class MusicOverrideBody(BaseModel):
    intro: str | None = None
    main: list[str] = []
    outro: str | None = None


@router.put("/parts/{n}/music-override")
def put_music_override(
    n: int, body: MusicOverrideBody, request: Request
) -> dict[str, Any]:
    out = _output_dir(request)
    p = out / f"part{n:02d}_music_override.json"
    p.write_text(json.dumps(body.model_dump(), indent=2), encoding="utf-8")
    return {"saved": True}


@router.get("/music/tracks")
def list_tracks(request: Request) -> list[dict[str, Any]]:
    repo = Path(__file__).resolve().parents[2]
    music_dir = repo / "creative_suite" / "engine" / "music"
    if not music_dir.exists():
        return []
    tracks = []
    for f in music_dir.iterdir():
        if f.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg"):
            continue
        entry: dict[str, Any] = {"name": f.name, "path": str(f)}
        beats_file = music_dir / (f.name + ".beats.json")
        if beats_file.exists():
            try:
                bdata = json.loads(beats_file.read_text(encoding="utf-8"))
                if "tempo" in bdata:
                    entry["bpm"] = round(float(bdata["tempo"]), 1)
            except (OSError, ValueError, KeyError):
                pass
        tracks.append(entry)
    return sorted(tracks, key=lambda x: x["name"])


class PreviewBody(BaseModel):
    clip_chunks: list[str]
    tier: str = "A"


@router.post("/parts/{n}/preview")
async def post_preview(
    n: int, body: PreviewBody, request: Request, response: Response
) -> dict[str, Any]:
    cfg = request.app.state.cfg
    q: JobQueue = request.app.state.job_queue
    output_dir = cfg.phase1_output_dir
    repo_root = Path(__file__).resolve().parents[2]
    wolfcam = repo_root / "tools" / "wolfcamql" / "wolfcamql.exe"
    ffmpeg_exe = repo_root / "tools" / "ffmpeg" / "ffmpeg.exe"

    async def run(emit: Callable[[str, int, str], Awaitable[None]]) -> None:
        await run_preview_tier_a(
            emit=emit, part=n, clip_chunks=body.clip_chunks,
            output_dir=output_dir, wolfcam_exe=wolfcam, ffmpeg_exe=ffmpeg_exe,
        )

    try:
        jid = q.submit(run)
    except RuntimeError:
        response.status_code = 409
        return {"error": "busy"}
    return {"job_id": jid}


@router.websocket("/parts/{n}/engine")
async def engine_ws(websocket: WebSocket, n: int) -> None:
    await websocket.accept()
    cfg = websocket.app.state.cfg
    repo_root = Path(__file__).resolve().parents[2]
    wolfcam = repo_root / "tools" / "wolfcamql" / "wolfcamql.exe"
    thumb_dir = (
        cfg.phase1_output_dir.parent / "creative_suite" / "generated" / "engine_thumbs"
    )

    flow_plan_p = cfg.phase1_output_dir / f"part{n:02d}_flow_plan.json"
    fp: dict[str, Any] = (
        json.loads(flow_plan_p.read_text(encoding="utf-8"))
        if flow_plan_p.exists() else {}
    )
    clips: list[dict[str, Any]] = fp.get("clips") or [{}]
    demo = clips[0].get("demo")
    if demo is None:
        await websocket.send_json({"kind": "error", "msg": "no demo resolvable"})
        await websocket.close()
        return

    sup = EngineSupervisor(
        engine_cmd=[str(wolfcam), "+demo", demo, "+set", "cg_drawHUD", "0"],
        thumb_dir=thumb_dir,
        mock_grab=bool(os.getenv("CS_ENGINE_MOCK")),
    )
    await sup.start()
    try:
        async def fan_out() -> None:
            while True:
                frame = await sup.next_frame(timeout_s=2.0)
                if frame is None: continue
                try:
                    await websocket.send_json({
                        "kind": "frame",
                        "t_ms": sup.last_seek_ms,
                        "jpeg_b64": base64.b64encode(frame).decode("ascii"),
                    })
                except Exception:
                    return
        fan_task = asyncio.create_task(fan_out())
        try:
            while True:
                cmd = await websocket.receive_json()
                if cmd.get("cmd") == "seek":
                    await sup.seek(ms=int(cmd["t_ms"]))
                elif cmd.get("cmd") == "quit":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            fan_task.cancel()
    finally:
        await sup.stop()
