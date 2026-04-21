# creative_suite/api/studio.py
"""Studio router — /api/studio

Serves metadata for the /studio editor UI:
  GET  /api/studio/status                        health check
  GET  /api/studio/parts                         list available parts with metadata
  GET  /api/studio/part/{n}/clips                clips from T1 manifest + T2/T3 dirs
  PUT  /api/studio/part/{n}/clips                save working clip order
  GET  /api/studio/part/{n}/flow                 flow_plan.json for a specific part
  GET  /api/studio/part/{n}/music                music tracks + match % for a part
  GET  /api/studio/part/{n}/music_contract       full-length contract coverage check
  GET  /api/studio/music/library                 all music tracks across all parts
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

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


def _scan_tier_dir(tier_dir: Path, tier: str, idx_start: int) -> list[dict[str, Any]]:
    """Scan a T2/T3 directory and return clip dicts."""
    if not tier_dir.exists():
        return []
    clips = []
    for f in sorted(tier_dir.iterdir()):
        if f.suffix.lower() == ".avi":
            clips.append({
                "idx": idx_start + len(clips),
                "name": f.name,
                "raw": f.name,
                "path": str(f),
                "tier": tier,
                "is_fl": True,   # T2/T3 are always FL (free-look) angles
                "has_pair": False,
            })
    return clips


def _load_order_file(clip_lists: Path, part: int) -> list[dict[str, Any]] | None:
    """Load a saved working-order JSON for a part, or return None."""
    p = clip_lists / f"part{part:02d}_order.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@router.get("/parts")
def list_parts(request: Request) -> list[dict[str, Any]]:
    cfg = request.app.state.cfg
    clip_lists = _clip_lists_dir(request)
    out = _output_dir(request)
    qv = cfg.quake_video_dir

    if not clip_lists.exists():
        return []

    results: list[dict[str, Any]] = []
    for f in sorted(clip_lists.glob("part??.txt")):
        m = _PART_RE.match(f.name)
        if not m:
            continue
        part = int(m.group(1))
        nn = f"{part:02d}"

        flow_flat = out / f"part{nn}_flow_plan.json"
        flow_subdir = out / f"part{nn}" / "flow_plan.json"
        has_flow_plan = flow_flat.exists() or flow_subdir.exists()

        render_exists = (out / f"part{nn}" / f"part{nn}_final.mp4").exists()

        # Count clips across all three tiers
        t1_count = _count_clips(f)
        t2_count = sum(1 for x in (qv / "T2" / f"Part{part}").glob("*.avi") if qv.exists()) if qv.exists() else 0
        t3_count = sum(1 for x in (qv / "T3" / f"Part{part}").glob("*.avi") if qv.exists()) if qv.exists() else 0

        results.append({
            "part": part,
            "clip_count": t1_count + t2_count + t3_count,
            "t1_count": t1_count,
            "t2_count": t2_count,
            "t3_count": t3_count,
            "has_flow_plan": has_flow_plan,
            "has_music": _has_music(part, cfg.phase1_music_dir),
            "render_exists": render_exists,
        })

    return results


@router.get("/part/{part_num}/clips")
def get_clips(part_num: int, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    clip_lists = _clip_lists_dir(request)
    clip_file = clip_lists / f"part{part_num:02d}.txt"
    qv = cfg.quake_video_dir

    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"No clip list for part {part_num}")

    # If a saved working order exists, return it directly
    saved = _load_order_file(clip_lists, part_num)
    if saved is not None:
        return {"part": part_num, "clips": saved, "has_saved_order": True}

    # Build default order: T1 (from manifest), then T2 (dir scan), then T3 (dir scan)
    clips: list[dict[str, Any]] = []
    qv_part = qv / "T1" / f"Part{part_num}"
    for line in clip_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        c = _parse_clip_line(stripped, len(clips))
        # Manifest lines are T1 — force tier and resolve full path
        c["tier"] = "T1"
        c["is_fl"] = False
        name = Path(c["path"]).name
        c["name"] = name
        if not Path(c["path"]).is_absolute():
            c["path"] = str(qv_part / name)
        clips.append(c)

    t2_clips = _scan_tier_dir(qv / "T2" / f"Part{part_num}", "T2", len(clips))
    t3_clips = _scan_tier_dir(qv / "T3" / f"Part{part_num}", "T3", len(clips) + len(t2_clips))

    return {
        "part": part_num,
        "clips": clips + t2_clips + t3_clips,
        "has_saved_order": False,
    }


class _ClipItem(BaseModel):
    name: str
    tier: str
    path: str = ""
    idx: int = 0
    raw: str = ""
    is_fl: bool = False
    has_pair: bool = False


class ClipOrderBody(BaseModel):
    clips: list[_ClipItem]


@router.put("/part/{part_num}/clips")
def save_clip_order(part_num: int, body: ClipOrderBody, request: Request) -> dict[str, Any]:
    """Persist a user-reordered clip list. Saves a JSON working-order file and
    also rewrites the T1 .txt manifest to reflect the new T1 order."""
    clip_lists = _clip_lists_dir(request)
    clip_file = clip_lists / f"part{part_num:02d}.txt"
    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"No clip list for part {part_num}")

    # Renumber and save full order as JSON
    ordered = [c.model_dump() for c in body.clips]
    for i, c in enumerate(ordered):
        c["idx"] = i
    order_path = clip_lists / f"part{part_num:02d}_order.json"
    order_path.write_text(json.dumps(ordered, indent=2), encoding="utf-8")

    # Rewrite .txt manifest with T1 clips in their new order
    t1_clips = [c for c in ordered if c.get("tier", "T1") == "T1"]
    nn = f"{part_num:02d}"
    lines = [
        f"# Part {part_num} clip list — saved from STUDIO CLIPS editor",
        f"# {len(t1_clips)} T1 clips",
    ]
    lines += [c["name"] for c in t1_clips]
    clip_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"saved": True, "total": len(ordered), "t1": len(t1_clips)}


_VALID_PARTS = range(1, 13)  # parts 1-12 inclusive

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


@router.get("/music/browse")
def browse_music_library(request: Request) -> list[dict[str, Any]]:
    """Scan engine/music/library/ for all downloaded tracks.

    Filename convention: ARTIST__Track_Title.mp3  (double-underscore separator).
    Returns artist + title parsed from stem, plus duration when mutagen is available.
    """
    cfg = request.app.state.cfg
    library_dir: Path = cfg.phase1_music_dir / "library"
    if not library_dir.exists():
        return []

    tracks: list[dict[str, Any]] = []
    for f in sorted(library_dir.iterdir()):
        if f.suffix.lower() not in _MUSIC_EXTS:
            continue
        stem = f.stem
        if "__" in stem:
            raw_artist, raw_title = stem.split("__", 1)
            artist = raw_artist.replace("_", " ").strip()
            title  = raw_title.replace("_", " ").replace("-", " ").strip()
        else:
            artist = ""
            title  = stem.replace("_", " ").replace("-", " ").strip()

        duration = _get_track_duration(f)
        tracks.append({
            "id":         f.stem,
            "filename":   f.name,
            "artist":     artist,
            "title":      title,
            "duration_s": round(duration, 3) if duration is not None else None,
            "path":       "library/" + f.name,
        })
    return tracks


@router.get("/music/file/{filename}")
def serve_music_file(filename: str, request: Request) -> FileResponse:
    """Serve a single music file from engine/music/library/.

    Only files inside the library directory are served (no path traversal).
    """
    cfg = request.app.state.cfg
    library_dir: Path = cfg.phase1_music_dir / "library"
    # Sanitise: strip any directory components supplied by the caller
    safe_name = Path(filename).name
    target = library_dir / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Track not found: {safe_name}")
    return FileResponse(str(target), media_type="audio/mpeg")


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


# ═══════════════════════════════════════════════════════════════════════════════
# NLE Studio DB endpoints
# ═══════════════════════════════════════════════════════════════════════════════

import math as _math
import random as _random

from creative_suite.database import nle_db as _nle_db_mod
from creative_suite.engine import music_chain as _music_chain


def _nle_db(request: Request):
    return request.app.state.cfg.nle_db_path


# ── Pydantic models ───────────────────────────────────────────────────────────

class _ArrangementClip(BaseModel):
    clip_path: str
    role: str = "body"
    tier: str = "T2"
    is_fl: bool = False
    pair_path: Optional[str] = None
    duration_s: Optional[float] = None


class ArrangementBody(BaseModel):
    clips: list[_ArrangementClip]


class _FxParams(BaseModel):
    effect_type: str
    params: dict = {}
    position: int = 0


class _FxUpdate(BaseModel):
    params: dict = {}
    enabled: bool = True


class _MusicAssignment(BaseModel):
    role: str
    track_filename: str
    artist: Optional[str] = None
    title: Optional[str] = None
    bpm: Optional[float] = None
    duration_s: Optional[float] = None
    position: int = 0
    transition_out: dict = {}


# ── Arrangement ───────────────────────────────────────────────────────────────

@router.get("/part/{part_num}/arrangement")
def get_arrangement(part_num: int, request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    rows = _nle_db_mod.get_arrangement(db, part_num)
    for row in rows:
        row["effects"] = _nle_db_mod.get_clip_effects(db, row["id"])
    return {"part": part_num, "clips": rows}


@router.put("/part/{part_num}/arrangement")
def save_arrangement(part_num: int, body: ArrangementBody,
                     request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    clips = [c.model_dump() for c in body.clips]
    _nle_db_mod.bulk_replace_arrangement(db, part_num, clips)
    return {"saved": True, "total": len(clips)}


@router.post("/part/{part_num}/arrangement/import")
def import_from_clip_list(part_num: int, request: Request) -> dict[str, Any]:
    """Seed clip_arrangements from the existing partNN.txt manifest + T2/T3 dirs."""
    cfg = request.app.state.cfg
    db = _nle_db(request)

    clip_lists = _clip_lists_dir(request)
    clip_file = clip_lists / f"part{part_num:02d}.txt"
    if not clip_file.exists():
        raise HTTPException(404, f"No clip list for part {part_num}")

    saved = _load_order_file(clip_lists, part_num)
    if saved is not None:
        raw_clips = saved
    else:
        raw_clips = []
        qv_part = cfg.quake_video_dir / "T1" / f"Part{part_num}"
        for line in clip_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            c = _parse_clip_line(stripped, len(raw_clips))
            c["tier"] = "T1"
            c["is_fl"] = False
            name = Path(c["path"]).name
            c["name"] = name
            if not Path(c["path"]).is_absolute():
                c["path"] = str(qv_part / name)
            raw_clips.append(c)
        raw_clips += _scan_tier_dir(
            cfg.quake_video_dir / "T2" / f"Part{part_num}", "T2", len(raw_clips))
        raw_clips += _scan_tier_dir(
            cfg.quake_video_dir / "T3" / f"Part{part_num}", "T3", len(raw_clips))

    db_clips = [
        {
            "clip_path": c.get("path", c.get("name", "")),
            "role": "body",
            "tier": c.get("tier", "T2"),
            "is_fl": c.get("is_fl", False),
            "pair_path": None,
            "duration_s": None,
        }
        for c in raw_clips
    ]
    _nle_db_mod.bulk_replace_arrangement(db, part_num, db_clips)
    return {"imported": len(db_clips), "part": part_num}


# ── Clip FX ───────────────────────────────────────────────────────────────────

@router.post("/part/{part_num}/arrangement/{clip_id}/fx")
def add_fx(part_num: int, clip_id: int, body: _FxParams,
           request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    arr = _nle_db_mod.get_arrangement(db, part_num)
    if clip_id not in [r["id"] for r in arr]:
        raise HTTPException(404, f"Clip {clip_id} not in part {part_num}")
    fx_id = _nle_db_mod.add_clip_effect(db, clip_id, body.effect_type,
                                         body.params, body.position)
    return {"fx_id": fx_id}


@router.put("/part/{part_num}/arrangement/{clip_id}/fx/{fx_id}")
def update_fx(part_num: int, clip_id: int, fx_id: int,
              body: _FxUpdate, request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    _nle_db_mod.update_clip_effect(db, fx_id, body.params, body.enabled)
    return {"updated": True}


@router.delete("/part/{part_num}/arrangement/{clip_id}/fx/{fx_id}")
def delete_fx(part_num: int, clip_id: int, fx_id: int,
              request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    _nle_db_mod.delete_clip_effect(db, fx_id)
    return {"deleted": True}


# ── Randomizer ────────────────────────────────────────────────────────────────

@router.post("/part/{part_num}/randomize")
def randomize_body(part_num: int, request: Request) -> dict[str, Any]:
    """Return a re-ordered body clip list. Does NOT write to DB — UI confirms."""
    db = _nle_db(request)
    rows = _nle_db_mod.get_arrangement(db, part_num)

    pinned = [r for r in rows if r["role"] in ("intro", "outro")]
    body   = [r for r in rows if r["role"] == "body"]

    t1 = [c for c in body if c["tier"] == "T1"]
    t2 = [c for c in body if c["tier"] == "T2"]
    t3 = [c for c in body if c["tier"] == "T3"]

    _random.shuffle(t1)
    _random.shuffle(t2)
    _random.shuffle(t3)

    total    = len(body)
    t1_slots = max(1, round(total * 0.25)) if t1 else 0
    t3_slots = max(1, round(total * 0.15)) if t3 else 0
    t2_slots = total - t1_slots - t3_slots

    def _fill(pool: list, n: int) -> list:
        if not pool or n <= 0:
            return []
        return (pool * _math.ceil(n / len(pool)))[:n]

    t1_out = _fill(t1, t1_slots)
    t2_out = _fill(t2, t2_slots)
    t3_out = _fill(t3, t3_slots)

    interleaved: list = []
    t3_it = iter(t3_out)
    t1_it = iter(t1_out)
    t2_it = iter(t2_out)

    # Cinematic T3 opener if available
    first = next(t3_it, None) or next(t2_it, None)
    if first:
        interleaved.append(first)

    for i in range(total - len(interleaved)):
        if i % 4 == 3:
            c = next(t1_it, None) or next(t2_it, None)
        elif i % 6 == 5:
            c = next(t3_it, None) or next(t2_it, None)
        else:
            c = next(t2_it, None) or next(t1_it, None)
        if c:
            interleaved.append(c)

    for rem in list(t1_it) + list(t2_it) + list(t3_it):
        if len(interleaved) < total:
            interleaved.append(rem)

    return {"part": part_num, "body_clips": interleaved, "pinned": pinned}


# ── Music recommendations ─────────────────────────────────────────────────────

@router.get("/part/{part_num}/music_recommend")
def music_recommend(part_num: int, request: Request,
                    prev_role: Optional[str] = None) -> dict[str, Any]:
    cfg = request.app.state.cfg
    db  = _nle_db(request)

    library_dir = cfg.phase1_music_dir / "library"
    tracks = _music_chain.load_library(library_dir)

    rows = _nle_db_mod.get_arrangement(db, part_num)
    body_dur = sum(r["duration_s"] or 5.0 for r in rows if r["role"] == "body")

    prev_track = None
    if prev_role:
        for m in _nle_db_mod.get_music_assignments(db, part_num):
            if m["role"] == prev_role:
                prev_track = m
                break

    ranked = _music_chain.score_tracks(tracks, body_dur,
                                        video_bpm=None,
                                        prev_track=prev_track,
                                        top_n=10)
    return {"part": part_num, "recommendations": ranked}


# ── Music assignment ──────────────────────────────────────────────────────────

@router.put("/part/{part_num}/music_assignment")
def save_music_assignment(part_num: int, body: _MusicAssignment,
                          request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    _nle_db_mod.upsert_music_assignment(
        db, part_num, body.role, body.track_filename,
        body.artist, body.title, body.bpm, body.duration_s,
        body.position, transition_out=body.transition_out,
    )
    return {"saved": True}


@router.delete("/part/{part_num}/music_assignment/{role}")
def clear_music_assignment(part_num: int, role: str,
                           request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    _nle_db_mod.delete_music_assignment(db, part_num, role)
    return {"deleted": True}


# ── Audio FX ──────────────────────────────────────────────────────────────────

@router.get("/audio_fx")
def list_audio_fx(request: Request, part: int = 4) -> dict[str, Any]:
    db = _nle_db(request)
    return {"audio_fx": _nle_db_mod.get_audio_fx(db, part)}


@router.put("/audio_fx/{fx_id}")
def update_audio_fx_preset(fx_id: int, body: _FxUpdate,
                           request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    _nle_db_mod.update_audio_fx(db, fx_id, body.params, body.enabled)
    return {"updated": True}


# ── Manifest generate ─────────────────────────────────────────────────────────

@router.post("/part/{part_num}/generate_manifest")
def generate_manifest_endpoint(part_num: int, request: Request) -> dict[str, Any]:
    from creative_suite.engine import manifest_generator as _mg
    cfg = request.app.state.cfg
    return _mg.generate_manifest(part_num, cfg)
