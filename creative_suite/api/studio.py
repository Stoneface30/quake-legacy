# creative_suite/api/studio.py
"""Studio router — /api/studio

Serves metadata for the /studio editor UI:
  GET /api/studio/status                         health check
  GET /api/studio/parts                          list available parts with metadata
  GET /api/studio/part/{n}/clips                 clip list for a specific part
  GET /api/studio/part/{n}/flow                  flow_plan.json for a specific part
  GET /api/studio/part/{n}/music                 music tracks + match % for a part
  GET /api/studio/part/{n}/music_contract        full-length contract coverage check
  GET /api/studio/music/library                  all music tracks across all parts
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/studio", tags=["studio"])

# ── helpers ──────────────────────────────────────────────────────────────────

_PART_RE = re.compile(r"^part(\d{2})\.txt$")


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


def _has_music(part: int, music_root: Path) -> bool:
    """True if any partNN_music.* file exists in the music directory."""
    if not music_root.exists():
        return False
    nn = f"{part:02d}"
    return any(music_root.glob(f"part{nn}_music*"))


def _parse_tier(path: str) -> str:
    """Extract T1/T2/T3 from a clip path; default 'T2' if none found."""
    upper = path.upper()
    for tier in ("T1", "T2", "T3"):
        if tier in upper:
            return tier
    return "T2"


def _is_fl(path: str) -> bool:
    """True if path contains /FL/ directory or _FL suffix/segment (case-insensitive)."""
    upper = path.upper()
    return (
        "/FL/" in upper
        or "_FL." in upper        # filename like frag_FL.avi
        or "_FL_" in upper        # like frag_FL_001.avi
        or upper.endswith("_FL")  # like frag_FL (no extension)
    )


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
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "studio/v1",
        "mlt_available": shutil.which("melt") is not None,
    }


@router.get("/parts")
def list_parts(request: Request) -> list[dict[str, Any]]:
    cfg = request.app.state.cfg
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
            "has_music": _has_music(part, cfg.phase1_music_dir),
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


_VALID_PARTS = range(4, 13)  # parts 4-12 inclusive

# ── music helpers ─────────────────────────────────────────────────────────────

_MUSIC_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

# Matches: part04_music.mp3  part04_intro_music.wav  part04_outro_music.ogg
# Also matches multi-numbered names like part04_music_01.mp3
_MUSIC_FILE_RE = re.compile(
    r"^part(\d{2})_(intro_music|outro_music|music)(?:_.+)?$",
    re.IGNORECASE,
)


def _assign_role(stem: str) -> str:
    """Return 'main', 'intro', or 'outro' for a music filename stem."""
    lower = stem.lower()
    if "intro_music" in lower:
        return "intro"
    if "outro_music" in lower:
        return "outro"
    return "main"


def _get_track_duration(path: Path) -> Optional[float]:
    """Return audio duration in seconds via mutagen, or None if unavailable."""
    try:
        from mutagen import File as MutagenFile  # type: ignore[import-untyped]

        audio = MutagenFile(str(path))
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception:
        pass
    return None


def _get_body_duration(part: int, output_dir: Path) -> Optional[float]:
    """Read body_duration from flow_plan.json if available."""
    nn = f"{part:02d}"
    candidates = [
        output_dir / f"part{nn}_flow_plan.json",
        output_dir / f"part{nn}" / "flow_plan.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                val = data.get("body_duration")
                if val is not None:
                    return float(val)
            except (OSError, ValueError, TypeError):
                pass
    return None


def _build_track_entry(
    f: Path,
    part: int,
    music_root: Path,
    body_duration: Optional[float],
) -> dict[str, Any]:
    """Build a single track dict from a music file path."""
    duration = _get_track_duration(f)

    match_pct: Optional[float] = None
    full_length_pct: Optional[float] = None
    needs_truncation: Optional[bool] = None

    if duration is not None and body_duration is not None and body_duration > 0:
        from creative_suite.music_match import compute_match

        m = compute_match(duration, body_duration)
        match_pct = m["match_pct"]
        full_length_pct = m["full_length_pct"]
        needs_truncation = m["needs_truncation"]

    rel = f.relative_to(music_root.parent.parent)  # relative to CS_ROOT parent

    title = f.stem.replace("_", " ").replace("-", " ").title()

    return {
        "id": f.stem,
        "title": title,
        "bpm": None,
        "duration_ms": round(duration * 1000) if duration is not None else None,
        "filename": f.name,
        "role": _assign_role(f.stem),
        "path": str(rel).replace("\\", "/"),
        "duration_s": round(duration, 3) if duration is not None else None,
        "match_pct": match_pct,
        "full_length_pct": full_length_pct,
        "needs_truncation": needs_truncation,
    }


def _scan_music_for_part(
    part: int, music_root: Path, output_dir: Path
) -> list[dict[str, Any]]:
    """Return a list of track dicts for the given part number."""
    if not music_root.exists():
        return []

    nn = f"{part:02d}"
    body_duration = _get_body_duration(part, output_dir)
    tracks: list[dict[str, Any]] = []

    for f in sorted(music_root.iterdir()):
        if f.suffix.lower() not in _MUSIC_EXTS:
            continue
        m = _MUSIC_FILE_RE.match(f.stem)
        if not m:
            continue
        if int(m.group(1)) != part:
            continue
        tracks.append(_build_track_entry(f, part, music_root, body_duration))

    return tracks


@router.get("/part/{part_num}/beats")
def get_beats(part_num: int, request: Request) -> dict[str, Any]:
    """Return beat and section data for a part.

    Reads output/partNN/partNN_beats.json (or flat output/partNN_beats.json).
    Returns 200 with empty beats/sections if the file is missing.
    Returns 404 only if part number is out of the valid range (4-12).
    """
    if part_num not in _VALID_PARTS:
        raise HTTPException(status_code=404, detail=f"Part {part_num} is not in range 4-12")

    out = _output_dir(request)
    nn = f"{part_num:02d}"

    candidates = [
        out / f"part{nn}" / f"part{nn}_beats.json",
        out / f"part{nn}_beats.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise HTTPException(
                    status_code=500, detail=f"Malformed beats file: {exc}"
                ) from exc

            # Extract known fields; fall back to empty lists if absent
            beats = raw.get("beats", [])
            sections = raw.get("sections", [])
            return {
                "part": part_num,
                "beats": beats,
                "sections": sections,
                "raw_beats": raw,
            }

    return {"part": part_num, "beats": [], "sections": [], "note": "no beats file found"}


@router.get("/part/{part_num}/flow")
def get_flow(part_num: int, request: Request) -> dict[str, Any]:
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


@router.get("/part/{part_num}/music")
def get_music(part_num: int, request: Request) -> dict[str, Any]:
    """Return music tracks and match % for a specific part.

    Returns 404 for part numbers outside 4-12.
    Returns 200 with empty tracks list if no music files are found.
    """
    if part_num not in _VALID_PARTS:
        raise HTTPException(status_code=404, detail=f"Part {part_num} is not in range 4-12")

    cfg = request.app.state.cfg
    music_root: Path = cfg.phase1_music_dir
    output_dir: Path = _output_dir(request)

    tracks = _scan_music_for_part(part_num, music_root, output_dir)
    return {"part": part_num, "tracks": tracks}


@router.get("/part/{part_num}/music_contract")
def get_music_contract(part_num: int, request: Request) -> dict[str, Any]:
    """Return full-length music contract coverage check for a specific part.

    Returns 404 for part numbers outside 4-12.
    Returns 200 with contract.error if the flow plan is missing.
    """
    if part_num not in _VALID_PARTS:
        raise HTTPException(status_code=404, detail=f"Part {part_num} is not in range 4-12")

    from creative_suite.engine.music_contract import validate_music_coverage

    cfg = request.app.state.cfg
    music_root: Path = cfg.phase1_music_dir
    output_dir: Path = _output_dir(request)

    # Determine body duration from flow_plan
    body_duration = _get_body_duration(part_num, output_dir)
    if body_duration is None:
        return {"part": part_num, "contract": {"error": "no flow plan"}}

    # Collect ordered music files for this part (intro → main → outro)
    tracks_sorted: list[Path] = []
    if music_root.exists():
        role_order = {"intro_music": 0, "music": 1, "outro_music": 2}
        found: list[tuple[int, Path]] = []
        for f in sorted(music_root.iterdir()):
            if f.suffix.lower() not in _MUSIC_EXTS:
                continue
            m = _MUSIC_FILE_RE.match(f.stem)
            if not m or int(m.group(1)) != part_num:
                continue
            role_key = m.group(2).lower()
            found.append((role_order.get(role_key, 1), f))
        found.sort(key=lambda x: x[0])
        tracks_sorted = [f for _, f in found]

    contract = validate_music_coverage(tracks_sorted, body_duration)
    return {"part": part_num, "contract": contract}


@router.get("/music/library")
def get_music_library(request: Request) -> list[dict[str, Any]]:
    """Return all music tracks across all parts (flat list).

    Each entry includes a `part` field.
    """
    cfg = request.app.state.cfg
    music_root: Path = cfg.phase1_music_dir
    output_dir: Path = _output_dir(request)

    results: list[dict[str, Any]] = []
    for part in _VALID_PARTS:
        for track in _scan_music_for_part(part, music_root, output_dir):
            track["part"] = part
            results.append(track)
    return results
