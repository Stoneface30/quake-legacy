"""Normalize AVI clips to CFR MP4 (60fps, 1920x1080) for consistent pipeline input.

Speed effects (Rule P1-Q v2, 2026-04-19 — audio stays at natural rate per user):
  slow=True    → 0.5× video (setpts=2.0*PTS).  Audio plays at natural speed;
                 video is longer than audio → apad silences the tail.
  speedup=True → 1.5× video (setpts=PTS/1.5). Audio plays at natural speed;
                 audio longer than video → atrim truncates. (Used for quiet /
                 silent clips per Rule P1-V — no meaningful audio to lose.)
  zoom=True    → center-crop + scale (no speed change, no audio change).

The switch from atempo=0.5,0.5 (which made audio sound like a wet-towel
dragged across concrete) to natural-speed-audio was a direct user ask on
2026-04-19: "insure it apply to the video clip and not the audio we dont
want audio compressed or sped up or lower higher".
"""
from pathlib import Path
from typing import List
import os
import subprocess
from tqdm import tqdm
from phase1.config import Config


def _ffprobe_valid(p: Path, ffprobe_bin: Path) -> bool:
    """L154: True iff `p` is a complete mp4 (moov present, duration > 0).

    Scrubs corrupt cache entries so subsequent cache hits re-normalize
    instead of crashing the render. Non-existent file = False.
    """
    if not p.exists() or p.stat().st_size < 1024:
        return False
    try:
        r = subprocess.run(
            [str(ffprobe_bin), "-v", "error",
             "-show_entries", "format=duration",
             "-of", "csv=p=0", str(p)],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return False
        return float(r.stdout.strip() or "0") > 0.5
    except Exception:
        return False


# Speed factors — the PTS multiplier (>1 = slower video, <1 = faster video).
SLOW_PTS_FACTOR = 2.0         # 0.5× playback (cinematic slow-mo)
SPEEDUP_PTS_FACTOR = 1.0 / 1.5  # 1.5× playback (dead-time compress)
ZOOM_CROP_FACTOR = 0.75       # keep center 75% then rescale → 1.33× zoom


def _video_filter(cfg: Config, *, slow: bool, speedup: bool, zoom: bool) -> str:
    chain: list[str] = []
    if slow:
        chain.append(f"setpts={SLOW_PTS_FACTOR:.3f}*PTS")
    elif speedup:
        chain.append(f"setpts={SPEEDUP_PTS_FACTOR:.3f}*PTS")
    if zoom:
        # Center-crop then upscale back to target resolution.
        chain.append(
            f"crop=iw*{ZOOM_CROP_FACTOR}:ih*{ZOOM_CROP_FACTOR}"
        )
    chain.append(f"fps={cfg.target_fps}")
    chain.append(
        f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos"
    )
    return ",".join(chain)


def _audio_filter(cfg: Config, *, slow: bool, speedup: bool) -> str:
    """Natural-speed audio with pad-or-trim to match new video duration.

    Rule P1-Q audio handling (user 2026-04-19): never atempo, never pitch-shift.
    slow → audio plays 1× rate, apad silences the tail to reach video duration.
    speedup → audio plays 1× rate, atrim cuts at new (shorter) video duration.
    neither → just fix AVI drift.
    """
    if slow and cfg.speed_change_audio_natural:
        # Pad silence at the end — ffmpeg auto-ends at video duration via
        # -shortest=0 default; apad ensures audio never ends early.
        return "aresample=async=1,apad"
    if speedup and cfg.speed_change_audio_natural:
        # Truncate the leading tail; the original audio plays naturally for
        # the new (shorter) video window. No pitch change.
        return "aresample=async=1"
    return "aresample=async=1"


def normalize_clip(
    src: Path,
    dst: Path,
    cfg: Config,
    force: bool = False,
    slow: bool = False,
    speedup: bool = False,
    zoom: bool = False,
) -> Path:
    """
    Convert AVI to CFR 60fps 1920x1080 MP4 with optional video-only speed change.
    Skips if dst already exists (unless force=True).
    Returns dst path.
    """
    ffprobe_bin = cfg.ffmpeg_bin.parent / "ffprobe.exe"

    # L154: validate cache hit before trusting it. Corrupt entries
    # (partial writes from killed ffmpeg) are silently re-normalized.
    if dst.exists() and not force:
        if _ffprobe_valid(dst, ffprobe_bin):
            return dst
        # Corrupt — remove and re-encode
        try:
            dst.unlink()
        except OSError:
            pass

    dst.parent.mkdir(parents=True, exist_ok=True)

    vf = _video_filter(cfg, slow=slow, speedup=speedup, zoom=zoom)
    af = _audio_filter(cfg, slow=slow, speedup=speedup)

    # L154: write to .partial, rename on success only. A killed ffmpeg
    # leaves a .partial file that cache-hits never see.
    partial = dst.with_suffix(dst.suffix + ".partial")
    if partial.exists():
        try:
            partial.unlink()
        except OSError:
            pass

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
    ]
    if speedup and cfg.speed_change_audio_natural:
        # Stop output at shortest stream = video (which is now shorter than
        # the natural-rate audio). This is the "natural audio, truncated"
        # behavior user asked for.
        cmd.append("-shortest")

    # L156: ffmpeg cannot infer the muxer from the L154 `.partial` sentinel
    # suffix. Force `-f mp4` so the atomic-write pattern survives ffmpeg's
    # extension sniffing ("Unable to choose an output format for '*.partial'").
    cmd.extend(["-f", "mp4", str(partial)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # clean partial — don't poison the cache
        try:
            partial.unlink()
        except OSError:
            pass
        raise RuntimeError(
            f"FFmpeg normalize failed for {src.name} "
            f"(slow={slow}, speedup={speedup}, zoom={zoom}):\n"
            f"{result.stderr[-500:]}"
        )

    # Validate the partial BEFORE renaming to canonical
    if not _ffprobe_valid(partial, ffprobe_bin):
        try:
            partial.unlink()
        except OSError:
            pass
        raise RuntimeError(
            f"FFmpeg wrote unreadable mp4 for {src.name} "
            f"(slow={slow}, speedup={speedup}, zoom={zoom})"
        )

    # Atomic rename: os.replace is atomic on Windows + POSIX
    os.replace(str(partial), str(dst))
    return dst


def slow_path(normal_path: Path) -> Path:
    """Return the slow-mo variant path for a normalized clip path."""
    return normal_path.parent / (normal_path.stem + "_slow" + normal_path.suffix)


def speedup_path(normal_path: Path) -> Path:
    """Return the speed-up variant path for a normalized clip path."""
    return normal_path.parent / (normal_path.stem + "_fast" + normal_path.suffix)


def zoom_path(normal_path: Path) -> Path:
    """Return the zoom variant path for a normalized clip path."""
    return normal_path.parent / (normal_path.stem + "_zoom" + normal_path.suffix)


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
