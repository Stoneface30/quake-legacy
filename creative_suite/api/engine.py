"""Engine graph API stubs — /api/engine/*

Placeholder endpoints wired by the frontend (LabEngine panel).
Returns 501 until the graphify pipeline is automated end-to-end.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/engine", tags=["engine"])


@router.post("/graph/rebuild")
def graph_rebuild() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Graph rebuild not yet automated — run graphify manually."},
    )
