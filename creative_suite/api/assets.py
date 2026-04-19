"""Asset browser endpoints.

- GET /api/assets             -> category->subcategory->assets tree
- GET /api/assets/{id}        -> single asset row
- GET /api/assets/{id}/raw    -> raw bytes pulled out of the source pk3
- GET /api/assets/{id}/thumbnail -> generated PNG thumbnail
"""
from __future__ import annotations

import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from creative_suite.db.migrate import connect

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("")
def list_tree(request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        rows = con.execute(
            "SELECT id, category, subcategory, source_pk3, internal_path, "
            "       thumbnail_path, width, height "
            "FROM assets ORDER BY category, subcategory, internal_path"
        ).fetchall()

    cats: dict[str, dict[str | None, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows:
        cats[r["category"]][r["subcategory"]].append({
            "id": r["id"],
            "internal_path": r["internal_path"],
            "thumbnail_url": (
                f"/api/assets/{r['id']}/thumbnail"
                if r["thumbnail_path"] else None
            ),
            "width": r["width"],
            "height": r["height"],
        })

    return {
        "categories": [
            {
                "name": cat,
                "subcategories": [
                    {"name": sub, "assets": assets}
                    for sub, assets in sorted(subs.items(), key=lambda kv: kv[0] or "")
                ],
            }
            for cat, subs in sorted(cats.items())
        ],
        "total": len(rows),
    }


@router.get("/{asset_id}")
def get_asset(asset_id: int, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")
    return dict(row)


@router.get("/{asset_id}/raw")
def get_asset_raw(asset_id: int, request: Request) -> Response:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT source_pk3, internal_path FROM assets WHERE id = ?",
            (asset_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")
    if not Path(row["source_pk3"]).exists():
        raise HTTPException(410, "source pk3 missing from disk")
    try:
        with zipfile.ZipFile(row["source_pk3"]) as z:
            data = z.read(row["internal_path"])
    except KeyError:
        raise HTTPException(404, "internal_path not in pk3")
    ext = row["internal_path"].rsplit(".", 1)[-1].lower()
    ctype = {
        "tga": "image/x-tga",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "md3": "application/octet-stream",
        "skin": "text/plain",
    }.get(ext, "application/octet-stream")
    return Response(content=data, media_type=ctype)


@router.get("/{asset_id}/thumbnail")
def get_thumbnail(asset_id: int, request: Request) -> FileResponse:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT thumbnail_path FROM assets WHERE id = ?", (asset_id,),
        ).fetchone()
    if row is None or not row["thumbnail_path"]:
        raise HTTPException(404, "thumbnail not generated")
    p = Path(row["thumbnail_path"])
    if not p.exists():
        raise HTTPException(410, "thumbnail file missing")
    return FileResponse(p, media_type="image/png")
