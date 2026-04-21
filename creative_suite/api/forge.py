"""FORGE backend API stubs — /api/forge/*

FORGE is the future engine handling 3D intro generation, demo extraction,
and automated re-recording. These stubs return the correct response shapes
so the frontend can wire against them before the full implementation lands.

Funded tracks: FT-3 (3D intro lab), FT-1 (dm73 parser), P3-A/P3-B
(highlight criteria + WolfcamQL command inventory).
"""
from __future__ import annotations

import asyncio
import datetime
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from creative_suite.config import REPO_ROOT

router = APIRouter(prefix="/api/forge", tags=["forge"])

# ---------------------------------------------------------------------------
# Candidate paths for engine binaries
# ---------------------------------------------------------------------------

_WOLFCAM_PATHS = [
    REPO_ROOT / "tools" / "wolfcamql" / "wolfcamql.exe",
    REPO_ROOT / "creative_suite" / "engine" / "wolfcam" / "wolfcamql.exe",
    REPO_ROOT / "engine" / "wolfcam" / "WolfcamQL" / "wolfcam-ql" / "wolfcamql.exe",
]

_Q3MME_PATHS = [
    REPO_ROOT / "tools" / "q3mme" / "q3mme.exe",
    REPO_ROOT / "engine" / "engines" / "_forks" / "q3mme" / "q3mme.exe",
    REPO_ROOT / "engine" / "engines" / "variants" / "q3mme" / "q3mme.exe",
]

_DEMOS_DIR = REPO_ROOT / "demos"


def _find_first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _count_demos(demos_dir: Path) -> int:
    if not demos_dir.exists():
        return 0
    return sum(1 for _ in demos_dir.rglob("*.dm_73"))


def _timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class IntroRequest(BaseModel):
    part: int
    style: str = "default"
    duration_s: float = 8.0


class ExtractRequest(BaseModel):
    demo_path: str
    extract_frags: bool = True
    extract_positions: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status() -> dict[str, Any]:
    """Return current FORGE engine readiness."""
    wolfcam_path = _find_first(_WOLFCAM_PATHS)
    q3mme_path = _find_first(_Q3MME_PATHS)

    wolfcam_available = wolfcam_path is not None
    q3mme_available = q3mme_path is not None

    demos_exists = _DEMOS_DIR.exists()
    demo_corpus_size = _count_demos(_DEMOS_DIR) if demos_exists else 0
    demo_corpus_path = str(_DEMOS_DIR) if demos_exists else None

    ready = wolfcam_available and q3mme_available

    return {
        "forge_version": "0.1.0-stub",
        "wolfcam_available": wolfcam_available,
        "wolfcam_path": str(wolfcam_path) if wolfcam_path else None,
        "q3mme_available": q3mme_available,
        "q3mme_path": str(q3mme_path) if q3mme_path else None,
        "demo_corpus_size": demo_corpus_size,
        "demo_corpus_path": demo_corpus_path,
        "capabilities": ["stub"],
        "ready": ready,
    }


@router.post("/intro")
def post_intro(req: IntroRequest) -> dict[str, Any]:
    """Stub: queue a FORGE 3D intro generation job (FT-3)."""
    job_id = f"forge-intro-{req.part}-{_timestamp()}"
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "FORGE intro generation not yet implemented — stub response",
        "part": req.part,
        "style": req.style,
        "duration_s": req.duration_s,
    }


@router.get("/job/{job_id}/events")
async def get_job_events(job_id: str) -> StreamingResponse:
    """SSE stream for FORGE job progress. Stub: emits queued→running→complete."""
    async def _stream():
        stages = [
            {"type": "queued",   "job_id": job_id, "progress": 0,   "message": "Job queued"},
            {"type": "running",  "job_id": job_id, "progress": 10,  "message": "Initialising engine"},
            {"type": "running",  "job_id": job_id, "progress": 50,  "message": "Processing (stub)"},
            {"type": "complete", "job_id": job_id, "progress": 100, "message": "Done (stub — FORGE not yet implemented)"},
        ]
        for evt in stages:
            yield f"data: {json.dumps(evt)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/demo/extract")
def post_demo_extract(req: ExtractRequest) -> dict[str, Any]:
    """Stub: queue a FORGE demo extraction job (FT-1)."""
    job_id = f"forge-extract-{_timestamp()}"
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "FORGE demo extraction not yet implemented — stub response",
        "demo_path": req.demo_path,
        "extract_frags": req.extract_frags,
        "extract_positions": req.extract_positions,
    }
