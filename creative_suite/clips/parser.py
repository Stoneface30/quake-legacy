from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FILE_RE = re.compile(r"^file\s+'([^']+)'\s*$")
_HINT_RE = re.compile(r"Demo\s*\((\d+)")
# Rule P1-K: FL angles appear either as `_FL_` / `_fl_` tokens OR as the
# wolfcam naming pattern `Demo (37FL1).avi`.
_FL_RE = re.compile(r"_(FL|fl)[_.]|Demo\s*\(\d+\s*(FL|fl)\d*\)", re.IGNORECASE)
_FLAG_RE = re.compile(r"\[(slow|intro|zoom|speedup|outro)\]", re.IGNORECASE)


@dataclass(frozen=True)
class ClipEntry:
    index: int
    filename: str
    demo_hint: str | None
    is_fl: bool
    # Optional extras (Rule P1-K multi-angle + effect flags). MVP resolver
    # only needs `filename`; the rest is breadcrumb for future callers.
    angles: tuple[str, ...] = field(default=())
    flags: tuple[str, ...] = field(default=())


def _parse_line(line: str, idx: int) -> ClipEntry | None:
    # Strip effect flags like [slow] [intro] [zoom] [speedup] [outro].
    flags = tuple(m.group(1).lower() for m in _FLAG_RE.finditer(line))
    cleaned = _FLAG_RE.sub("", line).strip()
    if not cleaned:
        return None

    # Concat-demuxer form: file 'foo.avi'
    m = _FILE_RE.match(cleaned)
    if m:
        fn = m.group(1).strip()
        angles = (fn,)
    else:
        # Rule P1-K grammar: "FP.avi > FL1.avi > FL2.avi" — take FP as primary.
        segments = [s.strip() for s in cleaned.split(">") if s.strip()]
        if not segments:
            return None
        # Strip optional wrapping quotes on bare filenames.
        segments = [s.strip("'\"") for s in segments]
        fn = segments[0]
        angles = tuple(segments)

    if not fn.lower().endswith(".avi") and not fn.lower().endswith(".mp4"):
        # Probably a stray directive (not a playable clip line). Skip.
        return None

    hint_match = _HINT_RE.search(fn)
    return ClipEntry(
        index=idx,
        filename=fn,
        demo_hint=hint_match.group(1) if hint_match else None,
        is_fl=bool(_FL_RE.search(fn)),
        angles=angles,
        flags=flags,
    )


def parse_clip_list(path: Path) -> list[ClipEntry]:
    out: list[ClipEntry] = []
    idx = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entry = _parse_line(line, idx)
        if entry is None:
            continue
        out.append(entry)
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
