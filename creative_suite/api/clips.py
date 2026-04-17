from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from creative_suite.clips.ffprobe import probe_duration
from creative_suite.clips.parser import parse_clip_list
from creative_suite.clips.resolver import resolve_clip
from creative_suite.config import REPO_ROOT

router = APIRouter()


@router.get("/api/clips/resolve")
def resolve(part: int, time: float, request: Request) -> dict[str, object]:
    cfg = request.app.state.cfg
    # Find mp4 for this part (prefer Part{part}.mp4; else first match).
    mp4 = cfg.phase1_output_dir / f"Part{part}.mp4"
    if not mp4.exists():
        candidates = list(cfg.phase1_output_dir.glob(f"Part{part}*.mp4"))
        if not candidates:
            raise HTTPException(404, f"no mp4 for Part{part}")
        mp4 = candidates[0]
    manifest = mp4.with_suffix(".render_manifest.json")
    if not manifest.exists():
        raise HTTPException(404, f"no manifest for {mp4.name}")
    cl = json.loads(manifest.read_text())["clip_list"]
    entries = parse_clip_list(Path(cl))
    if not entries:
        raise HTTPException(500, f"clip list empty: {cl}")
    durations: list[float] = []
    search_root = REPO_ROOT / "QUAKE VIDEO"
    for e in entries:
        found = next(search_root.rglob(e.filename), None) if search_root.exists() else None
        if found is None:
            durations.append(0.0)
            continue
        try:
            durations.append(probe_duration(cfg, found))
        except Exception:
            durations.append(0.0)
    r = resolve_clip(entries, durations, time, cfg.pre_content_offset_s)
    if r is None:
        return {
            "clip_index": None, "clip_filename": None, "demo_hint": None,
            "mp4_offset": None, "clip_offset": None,
            "note": "inside PANTHEON + title card offset",
        }
    return {
        "clip_index": r.clip_index,
        "clip_filename": r.clip_filename,
        "demo_hint": r.demo_hint,
        "mp4_offset": r.mp4_offset,
        "clip_offset": r.clip_offset,
    }
