"""Variant endpoints — minimal Task 5 slice.

Task 5 ships:
  - GET /api/variants/{id}        — single row
  - GET /api/variants/{id}/png    — render the output PNG
  - GET /api/variants?asset_id=N  — list variants for an asset

Task 6 will extend with POST /approve, /reject, /reroll.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from creative_suite.db.migrate import connect

router = APIRouter(prefix="/api/variants", tags=["variants"])


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
