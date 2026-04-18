from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request

from creative_suite.config import Config

router = APIRouter()


def stem_to_part(stem: str) -> int | None:
    """'Part4', 'Part4_v10_3_review' → 4. None on any other shape."""
    if not stem.lower().startswith("part"):
        return None
    head = stem[4:].split("_", 1)[0]
    try:
        return int(head)
    except ValueError:
        return None


def pick_mp4_per_part(out_dir: Path) -> dict[int, Path]:
    """Prefer `PartN.mp4`, else newest `PartN_*.mp4` by mtime.

    The renderer sometimes lands its output as `Part4_v10_3_review.mp4`
    (review builds) and sometimes as plain `Part4.mp4`. We treat the newest
    mtime as authoritative so the annotate UI loads the freshest cut.
    """
    buckets: dict[int, list[Path]] = {}
    for mp4 in out_dir.glob("Part*.mp4"):
        part = stem_to_part(mp4.stem)
        if part is None:
            continue
        buckets.setdefault(part, []).append(mp4)
    picked: dict[int, Path] = {}
    for part, candidates in buckets.items():
        # Exact `PartN.mp4` always wins — it is the canonical rendered output.
        exact = [p for p in candidates if p.stem == f"Part{part}"]
        if exact:
            picked[part] = exact[0]
            continue
        # Otherwise newest by mtime.
        picked[part] = max(candidates, key=lambda p: p.stat().st_mtime)
    return picked


def resolve_clip_list(cfg: Config, part: int, mp4: Path) -> str | None:
    """Resolve the clip-list path for a Part, manifest-first, styleb fallback.

    Order of authority (spec §3.3):
      1. `<mp4>.render_manifest.json` → `clip_list` field.
      2. `phase1/clip_lists/partNN_styleb.txt` (current Rule P1-K default).
      3. `phase1/clip_lists/partNN.txt` (legacy).
    Returns absolute string path or `None` if none exist on disk.
    """
    manifest = mp4.with_suffix(".render_manifest.json")
    if manifest.exists():
        try:
            cl = json.loads(manifest.read_text(encoding="utf-8"))["clip_list"]
            if Path(cl).exists():
                return str(Path(cl))
        except Exception:
            pass
    styleb = cfg.phase1_clip_lists / f"part{part:02d}_styleb.txt"
    if styleb.exists():
        return str(styleb)
    legacy = cfg.phase1_clip_lists / f"part{part:02d}.txt"
    if legacy.exists():
        return str(legacy)
    return None


@router.get("/api/parts")
def list_parts(request: Request) -> list[dict[str, object]]:
    cfg: Config = request.app.state.cfg
    out: list[dict[str, object]] = []
    if not cfg.phase1_output_dir.exists():
        return out
    picked = pick_mp4_per_part(cfg.phase1_output_dir)
    for part in sorted(picked.keys()):
        mp4 = picked[part]
        manifest = mp4.with_suffix(".render_manifest.json")
        cl = resolve_clip_list(cfg, part, mp4)
        out.append({
            "part": part,
            "mp4_name": mp4.name,
            "mp4_url": f"/media/{mp4.name}",
            "clip_list": cl,
            "has_manifest": manifest.exists(),
        })
    return out
