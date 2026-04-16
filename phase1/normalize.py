"""Normalize AVI clips to CFR MP4 (60fps, 1920x1080) for consistent pipeline input."""
from pathlib import Path
from typing import List
import subprocess
from tqdm import tqdm
from phase1.config import Config


# I7 fix: removed dead is_already_normalized() — normalize_clip checks dst.exists() directly

def normalize_clip(src: Path, dst: Path, cfg: Config, force: bool = False) -> Path:
    """
    Convert AVI to CFR 60fps 1920x1080 MP4.
    Skips if dst already exists (unless force=True).
    Returns dst path.
    """
    if dst.exists() and not force:
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(src),
        "-vf", f"fps={cfg.target_fps},scale={cfg.target_width}:{cfg.target_height}:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "16",           # high quality intermediate
        "-preset", "fast",      # fast encode for normalization pass
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


def normalize_part(part: int, clips: List[Path], cfg: Config, force: bool = False) -> List[Path]:
    """Normalize all clips for a Part. Returns list of normalized paths."""
    print(f"\nNormalizing Part {part} ({len(clips)} clips)...")
    normalized = []
    for clip in tqdm(clips, desc=f"Part {part}"):
        dst = cfg.normalize_path(clip)
        normalize_clip(clip, dst, cfg, force=force)
        normalized.append(dst)
    return normalized
