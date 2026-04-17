from __future__ import annotations

import json

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/parts")
def list_parts(request: Request) -> list[dict[str, object]]:
    cfg = request.app.state.cfg
    out: list[dict[str, object]] = []
    if not cfg.phase1_output_dir.exists():
        return out
    for mp4 in sorted(cfg.phase1_output_dir.glob("Part*.mp4")):
        try:
            part = int(mp4.stem.replace("Part", "").split("_")[0])
        except ValueError:
            continue
        manifest = mp4.with_suffix(".render_manifest.json")
        cl: str | None = None
        if manifest.exists():
            cl = json.loads(manifest.read_text())["clip_list"]
        out.append({
            "part": part,
            "mp4_name": mp4.name,
            "mp4_url": f"/media/{mp4.name}",
            "clip_list": cl,
            "has_manifest": manifest.exists(),
        })
    return out
