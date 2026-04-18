from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
