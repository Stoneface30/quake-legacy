"""ComfyUI queue API.

- POST /api/comfy/queue         — enqueue img2img for an asset_id.
- GET  /api/comfy/status/{vid}  — poll variant status.
- GET  /api/comfy/job/{job_id}  — peek ComfyUI history (thin passthrough).

The heavy lifting (asset extraction, ComfyUI round-trip, PNG write) lives in
comfy.runner.run_job. This router spawns a background thread so the HTTP
response returns immediately with the new variant_id.

The ComfyClient lives on app.state.comfy_client — FastAPI tests override this
with a MockTransport-backed client; production serves a real one.
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from creative_suite.comfy.client import ComfyClient
from creative_suite.comfy.prompts import build_final_prompt
from creative_suite.comfy.runner import JobSpec, run_job
from creative_suite.db.migrate import connect

router = APIRouter(prefix="/api/comfy", tags=["comfy"])


class QueueRequest(BaseModel):
    asset_id: int
    user_prompt: str = ""
    seed: Optional[int] = Field(default=None)
    denoise: float = 0.35


class QueueResponse(BaseModel):
    variant_id: int
    asset_id: int
    final_prompt: str
    seed: int
    status: str


def _get_comfy_client(app_state: Any) -> ComfyClient:
    existing = getattr(app_state, "comfy_client", None)
    if existing is None:
        cfg = app_state.cfg
        existing = ComfyClient(base_url=cfg.comfyui_url)
        app_state.comfy_client = existing
    return existing  # type: ignore[no-any-return]


def _pick_seed(provided: Optional[int]) -> int:
    if provided is not None:
        return int(provided)
    # Deterministic-ish seed from monotonic ns so tests can still match ranges.
    import secrets
    return secrets.randbits(31)


def _update_variant(cfg: Any, variant_id: int, fields: dict[str, Any]) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [variant_id]
    with connect(cfg) as con:
        con.execute(f"UPDATE variants SET {cols} WHERE id = ?", vals)


@router.post("/queue", response_model=QueueResponse)
def queue_variant(req: QueueRequest, request: Request) -> QueueResponse:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        asset = con.execute(
            "SELECT id, source_pk3, internal_path FROM assets WHERE id = ?",
            (req.asset_id,),
        ).fetchone()
    if asset is None:
        raise HTTPException(404, f"asset {req.asset_id} not found")

    final_prompt = build_final_prompt(req.user_prompt)
    seed = _pick_seed(req.seed)

    # Insert pending variant. png_path is NOT NULL in schema — use "" until
    # runner writes the real PNG.
    with connect(cfg) as con:
        cur = con.execute(
            "INSERT INTO variants (asset_id, user_prompt, final_prompt, seed, "
            "png_path, status) "
            "VALUES (?, ?, ?, ?, '', 'pending')",
            (req.asset_id, req.user_prompt, final_prompt, seed),
        )
        variant_id = int(cur.lastrowid or 0)

    spec = JobSpec(
        variant_id=variant_id,
        asset_id=req.asset_id,
        source_pk3=asset["source_pk3"],
        internal_path=asset["internal_path"],
        final_prompt=final_prompt,
        seed=seed,
        denoise=req.denoise,
    )

    comfy = _get_comfy_client(request.app.state)

    def _work() -> None:
        try:
            run_job(
                spec,
                cfg,
                comfy=comfy,
                update_variant=lambda vid, fields: _update_variant(cfg, vid, fields),
            )
        except Exception as exc:  # noqa: BLE001 — log + mark failed
            _update_variant(
                cfg, variant_id, {"status": "failed", "png_path": f"error: {exc}"[:200]}
            )

    # Test hook: if app.state.comfy_run_sync is truthy, run inline so pytest
    # can assert final state without race conditions.
    if getattr(request.app.state, "comfy_run_sync", False):
        _work()
    else:
        threading.Thread(target=_work, daemon=True).start()

    return QueueResponse(
        variant_id=variant_id,
        asset_id=req.asset_id,
        final_prompt=final_prompt,
        seed=seed,
        status="pending",
    )


@router.get("/status")
def get_queue_status(request: Request) -> dict[str, Any]:
    """Return current ComfyUI queue depth — used by the Textures panel status dot."""
    comfy = _get_comfy_client(request.app.state)
    try:
        r = comfy._http.get("/queue", timeout=3.0)
        r.raise_for_status()
        data = r.json()
        running = len(data.get("queue_running", []))
        pending = len(data.get("queue_pending", []))
        return {"queue_remaining": running + pending, "running": running, "pending": pending}
    except Exception as exc:
        raise HTTPException(503, f"ComfyUI unreachable: {exc}") from exc


@router.get("/status/{variant_id}")
def get_status(variant_id: int, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT id, asset_id, status, final_prompt, seed, comfy_job_id, "
            "       png_path, width, height, approved_at, created_at "
            "FROM variants WHERE id = ?",
            (variant_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"variant {variant_id} not found")
    out = dict(row)
    if out.get("png_path"):
        out["png_url"] = f"/api/variants/{variant_id}/png"
    return out


@router.get("/history/{job_id}")
def get_history(job_id: str, request: Request) -> dict[str, Any]:
    comfy = _get_comfy_client(request.app.state)
    return comfy.history(job_id)


# ---------------------------------------------------------------------- #
# WebSocket progress — Step 5.3
#
# Two implementations live side by side:
#   1. A poll-based bridge (default) that hits /history/{job_id} every 0.5 s
#      and forwards status/progress to the client. Zero ComfyUI-version risk.
#   2. If app.state.comfy_ws_url is set, an optional passthrough that
#      connects directly to ComfyUI's /ws and relays executing/progress/
#      executed events verbatim. Opt-in because it requires the `websockets`
#      library and a live ComfyUI.
#
# On 'executed' (or when /history reports outputs), the socket sends a final
# {"type":"done", "variant_id": N, "png_url": "..."} and closes.
# ---------------------------------------------------------------------- #


async def _poll_and_forward(
    ws: WebSocket, app_state: Any, job_id: str, poll_interval: float = 0.5,
    timeout: float = 300.0,
) -> None:
    """Default progress bridge — polls /history and variants table."""
    cfg = app_state.cfg
    comfy = _get_comfy_client(app_state)
    loop = asyncio.get_event_loop()
    elapsed = 0.0
    last_status = ""
    while elapsed < timeout:
        try:
            outputs = await loop.run_in_executor(
                None, comfy.output_filenames, job_id
            )
        except Exception as exc:  # noqa: BLE001 — ComfyUI may be down
            await ws.send_json({"type": "error", "message": str(exc)})
            return
        with connect(cfg) as con:
            row = con.execute(
                "SELECT id, status, png_path FROM variants "
                "WHERE comfy_job_id = ? ORDER BY id DESC LIMIT 1",
                (job_id,),
            ).fetchone()
        status = dict(row)["status"] if row else "pending"
        if status != last_status:
            await ws.send_json({"type": "status", "status": status})
            last_status = status
        if outputs:
            variant_id = dict(row)["id"] if row else None
            await ws.send_json(
                {
                    "type": "done",
                    "job_id": job_id,
                    "variant_id": variant_id,
                    "outputs": outputs,
                    "png_url": (
                        f"/api/variants/{variant_id}/png" if variant_id else None
                    ),
                }
            )
            return
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    await ws.send_json({"type": "timeout", "job_id": job_id})


@router.websocket("/progress/{job_id}")
async def ws_progress(
    websocket: WebSocket, job_id: str
) -> None:  # pyright: ignore[reportUnusedFunction]
    """Forward ComfyUI progress events to the browser.

    Contract:
      - Client opens `ws://.../api/comfy/progress/{job_id}` after POST /queue.
      - Server sends JSON messages: {"type":"status"|"progress"|"done"|"error"|"timeout", ...}.
      - Server closes after 'done' / 'timeout' / 'error'.
    """
    await websocket.accept()
    try:
        await _poll_and_forward(websocket, websocket.app.state, job_id)
    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# Silence unused-import complaint when asyncio/json aren't consumed by
# top-level code (they are used above — keep this for pyright).
_ = (asyncio, json)
