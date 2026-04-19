# creative_suite/api/phase1.py
"""Phase 1 Cinema Suite API — Phase A ships GET endpoints only.

Editing (PUT flow-plan, rebuild), preview, and engine WebSocket land in
Phase B/C/D.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

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
