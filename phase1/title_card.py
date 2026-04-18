"""
Title card renderer — Rule P1-N (Part 4 review 2026-04-17)
                   + Rule P1-T (Part 4 v6 review 2026-04-18).

Every Part intro sequence is:
    0s  → 7s   PANTHEON (IntroPart2.mp4 first 7s — handled elsewhere)
    7s  → 10s  "QUAKE TRIBUTE" letter-by-letter reveal   (card seconds 0-3)
   10s → 12s  "Part N"                                   (card seconds 3-5)
   12s → 14s  "By Tr4sH"                                 (card seconds 5-7)
   14s → 15s  HOLD credit (no fade to black — hard cut into content)

Rule P1-T (2026-04-18): title card is FL-backdropped, never a black void.
Unused FL gameplay angles are concatenated, desaturated, and darkened
to form the backdrop for the title text. Removes the "pure black screen"
feedback from Part 4 v6 review.

Letter-reveal bug (v6): previous implementation centered each growing
prefix at `x=(w-text_w)/2`, which put every letter stack on the same
midpoint → 13 stacked drawtext layers → unreadable hash. v7 anchors each
character at a pre-computed left-aligned x so letters type in place
cleanly, like a typewriter.
"""
from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Optional, Sequence

from phase1.config import Config, ROOT


# Windows font path escaped for ffmpeg drawtext.
_FONT_PATH = "C\\:/Windows/Fonts/impact.ttf"

# Impact character-width approximation at a given fontsize.
# Empirically: Impact's average glyph is ~0.55 × fontsize wide.
_IMPACT_CHAR_W_RATIO = 0.55


def _typewriter_reveal(
    text: str,
    reveal_start: float,
    reveal_end: float,
    hold_until: float,
    w: int,
    fontsize: int,
    y_expr: str,
) -> str:
    """
    Build a left-aligned typewriter reveal where each character has its own
    pre-computed x position. Avoids the v6 bug where centered prefixes
    overlapped into unreadable hash.
    """
    n = len(text)
    per_letter = (reveal_end - reveal_start) / max(n, 1) * 0.7
    char_w = int(fontsize * _IMPACT_CHAR_W_RATIO)
    total_w = char_w * n
    base_x = (w - total_w) // 2

    filters: list[str] = []
    for i, ch in enumerate(text):
        t_in = reveal_start + i * per_letter
        x = base_x + i * char_w
        escaped = ch.replace(":", "\\:").replace("'", "\\'").replace("\\", "\\\\")
        if escaped == " ":
            continue
        filters.append(
            f"drawtext=fontfile='{_FONT_PATH}':"
            f"text='{escaped}':"
            f"fontsize={fontsize}:fontcolor=white:"
            f"borderw=4:bordercolor=black@0.9:"
            f"x={x}:y={y_expr}:"
            f"enable='between(t,{t_in:.3f},{hold_until:.3f})'"
        )
    return ",".join(filters)


def pick_intro_backdrop_fls(
    part: int, cfg: Config, count: int = 4, seed: int = 0
) -> list[Path]:
    """
    Collect unused-candidate FL clips to back the title card.

    Priority: T3 first (Rule P1-B — lower-tier intros), then T2, then T1.
    We sample deterministically per-part so re-renders are stable.
    """
    rng = random.Random(f"part{part}-titlebg-v7-{seed}")
    candidates: list[Path] = []
    for tier in ("T3", "T2", "T1"):
        tier_dir = ROOT / "QUAKE VIDEO" / tier / f"Part{part}"
        if not tier_dir.exists():
            continue
        found = sorted(tier_dir.rglob("*FL*.avi"))
        rng.shuffle(found)
        candidates.extend(found)
    # Dedup by path while preserving order.
    seen: set[Path] = set()
    unique = [p for p in candidates if not (p in seen or seen.add(p))]
    return unique[:count]


def _build_backdrop_input(
    backdrop_paths: Sequence[Path],
    duration: float,
    w: int,
    h: int,
    fps: int,
) -> tuple[list[str], str]:
    """
    Returns (ffmpeg_inputs, video_chain_prefix).
    Each FL is trimmed to `per_clip` seconds, scaled, then vstack-concatenated,
    then desaturated 50% and darkened 35% for text legibility.
    """
    n = len(backdrop_paths)
    per_clip = max(duration / n, 1.5)

    inputs: list[str] = []
    concat_src: list[str] = []
    for i, path in enumerate(backdrop_paths):
        inputs.extend(["-t", f"{per_clip:.3f}", "-i", str(path)])
        # Each FL: scale to target, setpts, setsar, label as [vN]
        concat_src.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,setpts=PTS-STARTPTS,fps={fps},format=yuv420p[v{i}]"
        )
    labels = "".join(f"[v{i}]" for i in range(n))
    concat_filter = (
        ";".join(concat_src)
        + f";{labels}concat=n={n}:v=1:a=0[bgraw];"
        # Desaturate to 0.5, darken to 0.65, slight Gaussian blur for text legibility.
        f"[bgraw]hue=s=0.5,eq=brightness=-0.12:contrast=0.85,gblur=sigma=2,"
        f"trim=duration={duration},setpts=PTS-STARTPTS[bg]"
    )
    return inputs, concat_filter


def render_title_card(
    part: int,
    output_path: Path,
    cfg: Config,
    duration: float = 8.0,
    credit: str = "By Tr4sH",
    main_title: str = "QUAKE TRIBUTE",
    backdrop_paths: Optional[Sequence[Path]] = None,
) -> Path:
    """
    Render the 8-second title card (Rules P1-N + P1-T).

    Layout on the card's 0-8s timeline:
        0.0 → 3.0   "QUAKE TRIBUTE" typewriter reveal (holds until 3.0)
        3.0 → 5.0   "Part N"
        5.0 → 8.0   "By Tr4sH"   (holds through the end — no fade-out)
    Background: FL gameplay footage if `backdrop_paths` provided,
    otherwise pure black as a fallback.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    w, h, fps = cfg.target_width, cfg.target_height, cfg.target_fps
    y_center = "(h-text_h)/2"

    reveal_start, reveal_end = 0.0, 3.0
    part_start, part_end = 3.0, 5.0
    credit_start = 5.0
    credit_end = duration  # hold until the very end — no black fade

    # Autodiscover backdrop if caller didn't pass one.
    if backdrop_paths is None:
        try:
            backdrop_paths = pick_intro_backdrop_fls(part, cfg, count=4)
        except Exception as exc:
            print(f"  [title_card] backdrop autodiscover failed: {exc}")
            backdrop_paths = []

    if backdrop_paths:
        print(f"  [title_card] using {len(backdrop_paths)} FL backdrops:")
        for p in backdrop_paths:
            print(f"     - {p.name}")
        video_inputs, bg_chain = _build_backdrop_input(
            list(backdrop_paths), duration, w, h, fps
        )
    else:
        # Fallback to black lavfi.
        video_inputs = ["-f", "lavfi", "-i",
                        f"color=c=black:s={w}x{h}:r={fps}:d={duration}"]
        bg_chain = "[0:v]null[bg]"

    # Typewriter reveal for main title — fixed left-anchored x per char.
    reveal_chain = _typewriter_reveal(
        main_title,
        reveal_start=reveal_start,
        reveal_end=reveal_end,
        hold_until=reveal_end,
        w=w,
        fontsize=140,
        y_expr=y_center,
    )

    part_text = f"Part {part}"
    part_escaped = part_text.replace(":", "\\:")
    part_filter = (
        f"drawtext=fontfile='{_FONT_PATH}':text='{part_escaped}':"
        f"fontsize=120:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.9:"
        f"x=(w-text_w)/2:y={y_center}:"
        f"enable='between(t,{part_start},{part_end})'"
    )

    credit_escaped = credit.replace(":", "\\:").replace("'", "\\'")
    credit_filter = (
        f"drawtext=fontfile='{_FONT_PATH}':text='{credit_escaped}':"
        f"fontsize=90:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.9:"
        f"x=(w-text_w)/2:y={y_center}:"
        f"enable='between(t,{credit_start},{credit_end})'"
    )

    # Chain: [bg] → reveal → part → credit → [v]
    text_chain = f"[bg]{reveal_chain},{part_filter},{credit_filter}[v]"
    filter_complex = f"{bg_chain};{text_chain}"

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        *video_inputs,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", f"{len(backdrop_paths) if backdrop_paths else 1}:a",
        "-t", f"{duration}",
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
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Title card render failed:\n{result.stderr[-1200:]}")

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render a Part title card")
    parser.add_argument("--part", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-backdrop", action="store_true",
                        help="Render over black instead of FL gameplay")
    args = parser.parse_args()
    cfg = Config()
    backdrop = [] if args.no_backdrop else None
    render_title_card(args.part, args.out, cfg, backdrop_paths=backdrop)
    print(f"OK: {args.out}")
