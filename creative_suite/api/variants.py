"""Variant endpoints — read + approval loop.

Task 5 ships:
  - GET  /api/variants/{id}        — single row
  - GET  /api/variants/{id}/png    — render the output PNG
  - GET  /api/variants?asset_id=N  — list variants for an asset

Task 6 extends with:
  - POST /api/variants/{id}/approve — status=approved, approved_at=now
  - POST /api/variants/{id}/reject  — status=rejected
  - POST /api/variants/{id}/reroll  — spawn a new ComfyUI job with same
    asset + prompt + a fresh seed, returns the new variant id.

Reroll relies on the app-level ComfyClient and the same background-thread
machinery as POST /api/comfy/queue. It intentionally does NOT import the
router directly — cycles confuse FastAPI test wiring. Instead, it calls
`creative_suite.api.comfy.queue_variant` directly (same module, same
semantics, same test hook for sync execution).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from creative_suite.db.migrate import connect

router = APIRouter(prefix="/api/variants", tags=["variants"])


_VALID_TARGET_STATES = {"approved", "rejected"}


@router.get("")
def list_variants(
    request: Request, asset_id: int = Query(...)
) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        rows = con.execute(
            "SELECT id, asset_id, user_prompt, final_prompt, seed, "
            "       comfy_job_id, png_path, status, approved_at, "
            "       width, height, created_at "
            "FROM variants WHERE asset_id = ? ORDER BY id DESC",
            (asset_id,),
        ).fetchall()
    return {
        "asset_id": asset_id,
        "variants": [
            {
                **dict(r),
                "png_url": (
                    f"/api/variants/{r['id']}/png" if r["png_path"] else None
                ),
            }
            for r in rows
        ],
    }


@router.get("/{variant_id}")
def get_variant(variant_id: int, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT * FROM variants WHERE id = ?", (variant_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"variant {variant_id} not found")
    out = dict(row)
    if out.get("png_path"):
        out["png_url"] = f"/api/variants/{variant_id}/png"
    return out


@router.get("/{variant_id}/png")
def get_variant_png(variant_id: int, request: Request) -> FileResponse:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT png_path FROM variants WHERE id = ?", (variant_id,),
        ).fetchone()
    if row is None or not row["png_path"]:
        raise HTTPException(404, "variant PNG not written yet")
    p = Path(row["png_path"])
    if not p.exists():
        raise HTTPException(410, "variant file missing on disk")
    return FileResponse(p, media_type="image/png")


# ---------------------------------------------------------------------- #
# Task 6 — approve / reject / reroll
# ---------------------------------------------------------------------- #


def _set_status(
    cfg: Any,
    variant_id: int,
    status: str,
    *,
    stamp_approved: bool = False,
) -> dict[str, Any]:
    """Update status (+ approved_at on approve) and return the new row.

    Raises HTTPException(404) if the variant does not exist.
    """
    if status not in _VALID_TARGET_STATES:
        raise HTTPException(400, f"invalid target status: {status}")
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    with connect(cfg) as con:
        cur = con.execute("SELECT id FROM variants WHERE id = ?", (variant_id,))
        if cur.fetchone() is None:
            raise HTTPException(404, f"variant {variant_id} not found")
        if stamp_approved:
            con.execute(
                "UPDATE variants SET status = ?, approved_at = ? WHERE id = ?",
                (status, now, variant_id),
            )
        else:
            # Rejecting an already-approved variant clears approved_at so
            # Gate CS-1 counts (approved-only) stay accurate.
            con.execute(
                "UPDATE variants SET status = ?, approved_at = NULL WHERE id = ?",
                (status, variant_id),
            )
        row = con.execute(
            "SELECT id, asset_id, status, approved_at, png_path "
            "FROM variants WHERE id = ?",
            (variant_id,),
        ).fetchone()
    out = dict(row)
    if out.get("png_path"):
        out["png_url"] = f"/api/variants/{variant_id}/png"
    return out


@router.post("/{variant_id}/approve")
def approve_variant(variant_id: int, request: Request) -> dict[str, Any]:
    return _set_status(
        request.app.state.cfg, variant_id, "approved", stamp_approved=True
    )


@router.post("/{variant_id}/reject")
def reject_variant(variant_id: int, request: Request) -> dict[str, Any]:
    return _set_status(request.app.state.cfg, variant_id, "rejected")


@router.post("/{variant_id}/reroll")
def reroll_variant(variant_id: int, request: Request) -> dict[str, Any]:
    """Queue a new ComfyUI job reusing the same asset_id + user_prompt.

    A fresh seed is chosen by the queue handler (seed=None path). The new
    variant starts in status='pending' and progresses via the same runner
    thread as the original POST /api/comfy/queue.
    """
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT asset_id, user_prompt, denoise_override "
            "FROM variants WHERE id = ?"
            if _schema_has_denoise_override(con)
            else "SELECT asset_id, user_prompt FROM variants WHERE id = ?",
            (variant_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"variant {variant_id} not found")

    # Late import to avoid circular dep at module load time.
    from creative_suite.api.comfy import QueueRequest, queue_variant

    req = QueueRequest(
        asset_id=int(row["asset_id"]),
        user_prompt=(row["user_prompt"] or ""),
        seed=None,  # fresh seed on reroll
    )
    out = queue_variant(req, request)
    return {
        "source_variant_id": variant_id,
        "new_variant_id": out.variant_id,
        "asset_id": out.asset_id,
        "final_prompt": out.final_prompt,
        "seed": out.seed,
        "status": out.status,
    }


def _schema_has_denoise_override(con: Any) -> bool:
    """Forward-compat probe — returns True if the variants table includes a
    `denoise_override` column. Current schema does not; this just keeps the
    reroll query extensible when Task 9 adds per-variant knobs."""
    cols = {r["name"] for r in con.execute("PRAGMA table_info(variants)")}
    return "denoise_override" in cols
