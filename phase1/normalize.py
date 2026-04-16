"""Normalize AVI clips to CFR MP4 (60fps, 1920x1080) for consistent pipeline input.

Slow-motion: if slow=True, output runs at 0.25x speed (4x slow, 240fps source → 60fps out).
This is applied during normalization so the rest of the pipeline treats slow clips identically.

Slow-mo recipe:
  - video: setpts=4.0*PTS (4x slower)
  - audio: atempo=0.5,atempo=0.5 (two passes — atempo can only do 0.5-2.0 per stage)
  Result: 4x slowdown at full 60fps output.
"""
from pathlib import Path
from typing import List
import subprocess
from tqdm import tqdm
from phase1.config import Config


# I7 fix: removed dead is_already_normalized() — normalize_clip checks dst.exists() directly

SLOW_FACTOR = 4.0    # 0.25x playback speed (4x PTS stretch)


def normalize_clip(
    src: Path,
    dst: Path,
    cfg: Config,
    force: bool = False,
    slow: bool = False,
) -> Path:
    """
    Convert AVI to CFR 60fps 1920x1080 MP4.
    Skips if dst already exists (unless force=True).
    If slow=True, applies 4x slow-motion (0.25x speed).
    Returns dst path.
    """
    if dst.exists() and not force:
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)

    if slow:
        vf = (
            f"setpts={SLOW_FACTOR:.1f}*PTS,"
            f"fps={cfg.target_fps},"
            f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos"
        )
        # atempo range is 0.5-2.0 — chain two passes for 0.25x
        af = "atempo=0.5,atempo=0.5"
    else:
        vf = f"fps={cfg.target_fps},scale={cfg.target_width}:{cfg.target_height}:flags=lanczos"
        af = "aresample=async=1"   # fix audio drift in AVI sources

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(src),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-crf", "16",           # high quality intermediate
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(dst)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg normalize failed for {src.name}:\n{result.stderr[-500:]}")

    return dst


def slow_path(normal_path: Path) -> Path:
    """Return the slow-mo variant path for a normalized clip path."""
    return normal_path.parent / (normal_path.stem + "_slow" + normal_path.suffix)


def normalize_part(
    part: int,
    clips: List[Path],
    cfg: Config,
    force: bool = False,
    slow_clips: List[Path] = None,
) -> List[Path]:
    """
    Normalize all clips for a Part.
    slow_clips: list of source paths that should get slow-motion treatment.
    Returns list of normalized paths (slow clips get their _slow variant).
    """
    slow_set = set(str(p) for p in (slow_clips or []))
    print(f"\nNormalizing Part {part} ({len(clips)} clips)...")
    normalized = []
    for clip in tqdm(clips, desc=f"Part {part}"):
        is_slow = str(clip) in slow_set
        base_dst = cfg.normalize_path(clip)
        dst = slow_path(base_dst) if is_slow else base_dst
        normalize_clip(clip, dst, cfg, force=force, slow=is_slow)
        normalized.append(dst)
    return normalized
