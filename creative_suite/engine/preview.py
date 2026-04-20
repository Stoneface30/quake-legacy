"""
Generate a 30-second preview render of a Part for human review.
Takes the first N clips and renders at preview quality (fast).
"""
from pathlib import Path
from typing import Optional
from creative_suite.engine.config import Config
from creative_suite.engine.clip_list import get_clip_paths
from creative_suite.engine.normalize import normalize_part
from creative_suite.engine.pipeline import assemble_part, GradePreset
import subprocess


def render_preview(
    part: int,
    cfg: Config,
    preview_seconds: int = 30,
    max_clips: int = 10,
    open_after: bool = True
) -> Path:
    """
    Render a quick preview of Part N:
    - Uses up to max_clips clips
    - Limits output to preview_seconds
    - Uses faster encode settings (crf=23, veryfast)
    - Optionally opens in default video player

    Returns path to preview file.
    """
    print(f"\n=== PREVIEW: Part {part} ===")
    clips = get_clip_paths(part, cfg)[:max_clips]
    print(f"Using {len(clips)} of available clips (first {max_clips})")

    normalized = normalize_part(part, clips, cfg)
    output = cfg.preview_path(part)

    # I5 fix: actually pass override values to assemble_part
    assemble_part(
        clips=normalized,
        output_path=output,
        cfg=cfg,
        preview_seconds=preview_seconds,
        crf_override=23,           # faster encode for preview
        preset_override="veryfast",
    )

    print(f"\nPreview saved: {output}")
    print(f"Duration: ~{preview_seconds}s")

    if open_after:
        _open_video(output)

    return output


def _open_video(path: Path):
    """Open video in default system player."""
    import os, sys
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception as e:
        print(f"Could not auto-open video: {e}")
        print(f"Open manually: {path}")


if __name__ == "__main__":
    import sys
    cfg = Config()
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    render_preview(part, cfg, open_after=True)
