from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from creative_suite.api.parts import pick_mp4_per_part, resolve_clip_list
from creative_suite.clips.ffprobe import probe_duration
from creative_suite.clips.parser import parse_clip_list
from creative_suite.clips.resolver import resolve_clip
from creative_suite.config import REPO_ROOT, Config

router = APIRouter()


def _find_avi(filename: str, search_roots: list[Path]) -> Path | None:
    """Locate the AVI for a clip entry anywhere under QUAKE VIDEO/T{1,2,3}/."""
    for root in search_roots:
        if not root.exists():
            continue
        hit = next(root.rglob(filename), None)
        if hit is not None:
            return hit
    return None


@router.get("/api/clips/resolve")
def resolve(part: int, time: float, request: Request) -> dict[str, object]:
    cfg: Config = request.app.state.cfg
    picked = pick_mp4_per_part(cfg.phase1_output_dir)
    mp4 = picked.get(part)
    if mp4 is None:
        raise HTTPException(404, f"no mp4 for Part{part}")
    cl = resolve_clip_list(cfg, part, mp4)
    if cl is None:
        raise HTTPException(404, f"no clip list for Part{part}")
    entries = parse_clip_list(Path(cl))
    if not entries:
        raise HTTPException(500, f"clip list empty: {cl}")
    durations: list[float] = []
    search_roots = [REPO_ROOT / "QUAKE VIDEO"]
    for e in entries:
        found = _find_avi(e.filename, search_roots)
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
