"""Task 9.1 — POST /api/ollama/suggest.

Thin HTTP seam in front of OllamaClient. Body: ``{asset_id: int}``. We
read the asset's PNG/JPG/TGA bytes from disk (prefer thumbnail for
speed — gemma3:4b-vision processes the thumbnail just fine) and forward
to the Ollama client.

On ``OllamaUnavailable`` we return 503. Frontend disables the suggest
button for the session silently per spec §11.4.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from creative_suite.db.migrate import connect
from creative_suite.ollama.client import OllamaClient, OllamaUnavailable

router = APIRouter(prefix="/api/ollama", tags=["ollama"])


class SuggestRequest(BaseModel):
    asset_id: int


def _get_ollama_client(app_state: Any) -> OllamaClient:
    """Reuse a single OllamaClient across requests. Tests pre-seed this
    on app.state.ollama_client so no real HTTP hits the network."""
    existing = getattr(app_state, "ollama_client", None)
    if existing is None:
        cfg = app_state.cfg
        existing = OllamaClient(base_url=cfg.ollama_url)
        app_state.ollama_client = existing
    return existing


def _read_asset_bytes(con: Any, asset_id: int) -> tuple[bytes, str, str | None]:
    """Return (image_bytes, category, subcategory) for ``asset_id``.

    Prefers `thumbnail_path` (already PNG, small) → `extracted_path` →
    404 if neither is resolved yet."""
    row = con.execute(
        "SELECT thumbnail_path, extracted_path, category, subcategory "
        "FROM assets WHERE id = ?",
        (asset_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")

    for field in ("thumbnail_path", "extracted_path"):
        p = row[field]
        if p and Path(p).exists():
            return (Path(p).read_bytes(), row["category"], row["subcategory"])
    raise HTTPException(409, f"asset {asset_id} has no image on disk yet")


@router.post("/suggest")
def suggest(req: SuggestRequest, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        image_bytes, category, subcategory = _read_asset_bytes(con, req.asset_id)

    client = _get_ollama_client(request.app.state)
    try:
        suggestions = client.suggest_prompts(image_bytes, category, subcategory)
    except OllamaUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "unavailable", "reason": str(exc)},
        ) from exc

    return {
        "asset_id": req.asset_id,
        "category": category,
        "subcategory": subcategory,
        "suggestions": suggestions,
    }
