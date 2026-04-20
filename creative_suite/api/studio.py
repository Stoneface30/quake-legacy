# creative_suite/api/studio.py
"""Studio router — /api/studio

Serves metadata for the /studio editor UI:
  GET /api/studio/status            health check
  GET /api/studio/parts             list available parts with metadata
  GET /api/studio/part/{n}/clips    clip list for a specific part
  GET /api/studio/part/{n}/flow     flow_plan.json for a specific part
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from creative_suite.config import REPO_ROOT, CS_ROOT

router = APIRouter(prefix="/api/studio", tags=["studio"])

# ── helpers ──────────────────────────────────────────────────────────────────

_PART_RE = re.compile(r"^part(\d{2})\.txt$")

# Music lives in creative_suite/engine/music/ (confirmed from directory scan)
_MUSIC_ROOT = CS_ROOT / "engine" / "music"
_CLIP_LISTS_ROOT = CS_ROOT / "engine" / "clip_lists"
_OUTPUT_ROOT = REPO_ROOT / "output"


def _clip_lists_dir(request: Request) -> Path:
    """Use Config property so tests can monkeypatch it."""
    return request.app.state.cfg.phase1_clip_lists


def _output_dir(request: Request) -> Path:
    """Use Config property so tests can monkeypatch it."""
    return request.app.state.cfg.phase1_output_dir


def _count_clips(path: Path) -> int:
    """Count non-empty, non-comment lines in a clip list file."""
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def _has_music(part: int) -> bool:
    """True if any partNN_music.* file exists in the music directory."""
    nn = f"{part:02d}"
    if not _MUSIC_ROOT.exists():
        return False
    return any(_MUSIC_ROOT.glob(f"part{nn}_music*"))


def _parse_tier(path: str) -> str:
    """Extract T1/T2/T3 from a clip path; default 'T2' if none found."""
    upper = path.upper()
    for tier in ("T1", "T2", "T3"):
        if tier in upper:
            return tier
    return "T2"


def _is_fl(path: str) -> bool:
    """True if path contains /FL/ or _FL (case-insensitive)."""
    upper = path.upper()
    return "/FL/" in upper or "_FL" in upper


def _parse_clip_line(raw: str, idx: int) -> dict[str, Any]:
    """Parse one clip list line into a clip metadata dict."""
    has_pair = ">" in raw
    # Primary path is the left side of >, or the whole line
    primary = raw.split(">")[0].strip() if has_pair else raw.strip()
    return {
        "idx": idx,
        "raw": raw,
        "path": primary,
        "tier": _parse_tier(primary),
        "is_fl": _is_fl(primary),
        "has_pair": has_pair,
    }


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
def status() -> dict[str, str]:
    return {"status": "ok", "version": "studio/v1"}


@router.get("/parts")
def list_parts(request: Request) -> list[dict[str, Any]]:
    clip_lists = _clip_lists_dir(request)
    out = _output_dir(request)

    if not clip_lists.exists():
        return []

    results: list[dict[str, Any]] = []
    for f in sorted(clip_lists.glob("part??.txt")):
        m = _PART_RE.match(f.name)
        if not m:
            continue
        part = int(m.group(1))
        nn = f"{part:02d}"

        # has_flow_plan: output/partNN/flow_plan.json OR output/partNN_flow_plan.json
        # Check both layouts — the phase1 router uses flat files; keep compatible.
        flow_flat = out / f"part{nn}_flow_plan.json"
        flow_subdir = out / f"part{nn}" / "flow_plan.json"
        has_flow_plan = flow_flat.exists() or flow_subdir.exists()

        render_flat = out / f"part{nn}" / f"part{nn}_final.mp4"
        render_exists = render_flat.exists()

        results.append({
            "part": part,
            "clip_count": _count_clips(f),
            "has_flow_plan": has_flow_plan,
            "has_music": _has_music(part),
            "render_exists": render_exists,
        })

    return results


@router.get("/part/{part_num}/clips")
def get_clips(part_num: int, request: Request) -> dict[str, Any]:
    clip_lists = _clip_lists_dir(request)
    clip_file = clip_lists / f"part{part_num:02d}.txt"

    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"No clip list for part {part_num}")

    clips: list[dict[str, Any]] = []
    idx = 0
    for line in clip_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        clips.append(_parse_clip_line(stripped, idx))
        idx += 1

    return {"part": part_num, "clips": clips}


@router.get("/part/{part_num}/flow")
def get_flow(part_num: int, request: Request) -> Any:
    out = _output_dir(request)
    nn = f"{part_num:02d}"

    # Check flat layout first (matches phase1 router convention), then subdir
    candidates = [
        out / f"part{nn}_flow_plan.json",
        out / f"part{nn}" / "flow_plan.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise HTTPException(status_code=500, detail=f"Malformed flow plan: {exc}") from exc

    raise HTTPException(status_code=404, detail=f"No flow plan for part {part_num}")
