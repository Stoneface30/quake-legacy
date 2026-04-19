"""Task 9.3 — POST /api/capture/gamestart.

Writes a max-quality wolfcam gamestart.cfg for Phase 2's re-render
launcher. The writer module (creative_suite.capture.gamestart) is also
importable directly for Phase 2 in-process use — this HTTP endpoint is
for out-of-process consumers (Phase 2 runs in its own process tree).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from creative_suite.capture.gamestart import write_gamestart_cfg

router = APIRouter(prefix="/api/capture", tags=["capture"])


class GamestartRequest(BaseModel):
    demo_name: str = Field(..., min_length=1)
    seek_clock: str = Field(..., description="wolfcam seekclock arg, e.g. '8:52'")
    quit_at: str = Field(..., description="wolfcam 'at X quit' arg, e.g. '9:05'")
    fp_view: bool = True


@router.post("/gamestart")
def post_gamestart(req: GamestartRequest, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    out_dir: Path = cfg.wolfcam_capture_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    # One cfg per demo — subsequent renders of the same demo overwrite.
    # Filename is capture-demo-specific so concurrent launchers don't stomp.
    out_path = out_dir / f"gamestart_{req.demo_name}.cfg"
    try:
        write_gamestart_cfg(
            out_path,
            demo_name=req.demo_name,
            seek_clock=req.seek_clock,
            quit_at=req.quit_at,
            fp_view=req.fp_view,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"cfg_path": str(out_path), "fp_view": req.fp_view}
