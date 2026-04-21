from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from creative_suite.config import REPO_ROOT

router = APIRouter(prefix="/api/forge", tags=["forge"])

_DEMOS_DIR: Path = REPO_ROOT / "demos"


def _parse_demo(path: Path) -> dict:
    parts = path.stem.split("-")
    map_name = parts[2] if len(parts) > 2 else "unknown"
    size_mb = round(path.stat().st_size / 1_048_576, 2)
    return {
        "name": path.stem,
        "map": map_name,
        "size_mb": size_mb,
        "state": "unprocessed",
    }


@router.get("/demos")
def list_demos() -> dict:
    if not _DEMOS_DIR.exists():
        return {"demos": []}
    demos = sorted(_DEMOS_DIR.glob("*.dm_73"), key=lambda p: p.name)
    return {"demos": [_parse_demo(p) for p in demos]}
