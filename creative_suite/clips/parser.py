from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FILE_RE = re.compile(r"^file\s+'([^']+)'\s*$")
_HINT_RE = re.compile(r"Demo\s*\((\d+)\)")
_FL_RE = re.compile(r"_(FL|fl)[_.]")


@dataclass(frozen=True)
class ClipEntry:
    index: int
    filename: str
    demo_hint: str | None
    is_fl: bool


def parse_clip_list(path: Path) -> list[ClipEntry]:
    out: list[ClipEntry] = []
    idx = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _FILE_RE.match(line)
        if not m:
            continue
        fn = m.group(1)
        hint_match = _HINT_RE.search(fn)
        out.append(ClipEntry(
            index=idx,
            filename=fn,
            demo_hint=hint_match.group(1) if hint_match else None,
            is_fl=bool(_FL_RE.search(fn)),
        ))
        idx += 1
    return out


def write_render_manifest(
    mp4_path: Path,
    clip_list_path: Path,
    extras: dict[str, Any] | None = None,
) -> Path:
    """Write {Part}.render_manifest.json next to the rendered mp4.

    Called by phase1/pipeline.py at the end of a successful render so the
    annotation tool knows which clip list was actually used.
    """
    manifest_path = mp4_path.with_suffix(".render_manifest.json")
    payload = {
        "mp4": str(mp4_path),
        "clip_list": str(clip_list_path),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "extras": extras or {},
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path
