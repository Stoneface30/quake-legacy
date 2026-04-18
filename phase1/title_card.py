"""
Title card renderer — Rule P1-N (Part 4 review 2026-04-17).

Every Part intro sequence is:
    0s  → 7s   PANTHEON (IntroPart2.mp4 first 7s — handled elsewhere)
    7s  → 10s  "QUAKE TRIBUTE" letter-by-letter reveal   (seconds 0-3 of card)
   10s → 12s  "Part N"                                   (seconds 3-5 of card)
   12s → 14s  "By Tr4sH"                                 (seconds 5-7 of card)
   14s → 15s  Fade to black → content begins             (second 7-8 of card)

This module renders the 8-second title card as a standalone MP4 that the pipeline
concatenates after the PANTHEON intro and before the first clip.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from phase1.config import Config


# Windows font path escaped for ffmpeg drawtext.
_FONT_PATH = "C\\:/Windows/Fonts/impact.ttf"


def _drawtext_letter_reveal(text: str, start: float, per_letter: float,
                            y: str, fontsize: int) -> str:
    """Build a chain of drawtext filters revealing `text` one letter at a time."""
    filters = []
    end_t = 3.0  # "QUAKE TRIBUTE" window ends at 3s of card timeline
    for i in range(1, len(text) + 1):
        prefix = text[:i]
        t_in = start + (i - 1) * per_letter
        escaped = prefix.replace(":", "\\:").replace("'", "\\'")
        filters.append(
            f"drawtext=fontfile='{_FONT_PATH}':"
            f"text='{escaped}':"
            f"fontsize={fontsize}:fontcolor=white:"
            f"x=(w-text_w)/2:y={y}:"
            f"enable='between(t,{t_in:.3f},{end_t:.3f})'"
        )
    return ",".join(filters)


def render_title_card(
    part: int,
    output_path: Path,
    cfg: Config,
    duration: float = 8.0,
    credit: str = "By Tr4sH",
    main_title: str = "QUAKE TRIBUTE",
) -> Path:
    """
    Render the 8-second title card (Rule P1-N).

    Layout on the card's 0-8s timeline:
        0.0 → 3.0   "QUAKE TRIBUTE" letter-by-letter (centered)
        3.0 → 5.0   "Part N"                         (centered)
        5.0 → 7.0   "By Tr4sH"                       (centered)
        7.0 → 8.0   Fade to black
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    w, h, fps = cfg.target_width, cfg.target_height, cfg.target_fps
    y_center = "(h-text_h)/2"

    reveal_duration = 3.0
    part_start, part_end = 3.0, 5.0
    credit_start, credit_end = 5.0, 7.0
    fade_start = 7.0
    fade_dur = duration - fade_start

    per_letter = reveal_duration / max(len(main_title), 1) * 0.7
    reveal_chain = _drawtext_letter_reveal(
        main_title, start=0.0, per_letter=per_letter,
        y=y_center, fontsize=140,
    )

    part_text = f"Part {part}"
    part_escaped = part_text.replace(":", "\\:")
    part_filter = (
        f"drawtext=fontfile='{_FONT_PATH}':text='{part_escaped}':"
        f"fontsize=120:fontcolor=white:"
        f"x=(w-text_w)/2:y={y_center}:"
        f"enable='between(t,{part_start},{part_end})'"
    )

    credit_escaped = credit.replace(":", "\\:").replace("'", "\\'")
    credit_filter = (
        f"drawtext=fontfile='{_FONT_PATH}':text='{credit_escaped}':"
        f"fontsize=90:fontcolor=white:"
        f"x=(w-text_w)/2:y={y_center}:"
        f"enable='between(t,{credit_start},{credit_end})'"
    )

    fade_filter = f"fade=t=out:st={fade_start}:d={fade_dur}:color=black"

    vf = ",".join([reveal_chain, part_filter, credit_filter, fade_filter])

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}:d={duration}",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", f"{duration}",
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]

    print(f"  Rendering title card: Part {part} -> {output_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Title card render failed:\n{result.stderr[-800:]}")

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render a Part title card")
    parser.add_argument("--part", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cfg = Config()
    render_title_card(args.part, args.out, cfg)
    print(f"OK: {args.out}")
