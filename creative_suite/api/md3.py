"""MD3 model endpoint — serves raw MD3 bytes to the in-browser md3viewer.

Task 4: thin wrapper around the `assets` table.

    GET /api/md3/{asset_id}  -> application/octet-stream raw MD3 bytes

Resolution order for the bytes:
  1. `assets.extracted_path` if set and the file exists on disk.
  2. Fall back to reading `internal_path` directly out of `source_pk3`.

404s if the asset row is not an MD3 (category != 'model' OR internal_path
does not end in `.md3`). 410 if the source pk3 / extracted file is gone.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from creative_suite.db.migrate import connect

router = APIRouter(prefix="/api/md3", tags=["md3"])


@router.get("/{asset_id}")
def get_md3(asset_id: int, request: Request) -> Response:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        row = con.execute(
            "SELECT id, category, internal_path, source_pk3, extracted_path "
            "FROM assets WHERE id = ?",
            (asset_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")

    internal_path = row["internal_path"] or ""
    category = (row["category"] or "").lower()
    if not internal_path.lower().endswith(".md3") or (
        category and category != "model"
    ):
        raise HTTPException(404, f"asset {asset_id} is not an MD3")

    # Prefer already-extracted file on disk.
    extracted = row["extracted_path"]
    if extracted:
        p = Path(extracted)
        if p.exists() and p.is_file():
            return FileResponse(p, media_type="application/octet-stream")
        # Fall through to pk3 read below — extracted path was stale.

    source_pk3 = row["source_pk3"]
    if not source_pk3 or not Path(source_pk3).exists():
        raise HTTPException(404, "md3 bytes unavailable (no extracted file and no source pk3)")
    try:
        with zipfile.ZipFile(source_pk3) as z:
            data = z.read(internal_path)
    except (KeyError, zipfile.BadZipFile) as exc:
        raise HTTPException(404, f"md3 bytes unavailable: {exc}") from exc
    return Response(content=data, media_type="application/octet-stream")
