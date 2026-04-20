"""960x540 all-intra H.264 proxy generator for timeline scrubbing.

Full-res 1920x1080 60fps chunks are 5-20 MB each; a 120-clip Part loads
gigabytes into the browser if played raw. Proxies are ~15% the size and
scrub-fast because keyframes every 1 frame.

Atomic: writes to `.partial` then `os.replace` (Rule L154). Caches by
mtime — proxy is fresh if `proxy.mtime >= source.mtime` and non-empty.

Respects `CS_FFMPEG_MOCK=1` env var for tests (writes an 8-byte stub
instead of invoking ffmpeg).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

FFMPEG_ENV_MOCK = "CS_FFMPEG_MOCK"


def _ffmpeg_bin() -> str:
    """Resolve ffmpeg binary path. Prefers `tools/ffmpeg/ffmpeg.exe` if
    present, else relies on PATH.
    """
    local = Path("tools/ffmpeg/ffmpeg.exe")
    if local.exists():
        return str(local.resolve())
    # Also try absolute path in the standard project location
    absolute = Path("G:/QUAKE_LEGACY/tools/ffmpeg/ffmpeg.exe")
    if absolute.exists():
        return str(absolute)
    which = shutil.which("ffmpeg")
    if which:
        return which
    raise FileNotFoundError(
        "ffmpeg not found — install to tools/ffmpeg/ffmpeg.exe or PATH"
    )


def proxy_path(proxies_dir: Path, chunk_name: str) -> Path:
    return proxies_dir / f"{Path(chunk_name).stem}.proxy.mp4"


def is_fresh(source: Path, proxy: Path) -> bool:
    if not proxy.exists() or proxy.stat().st_size == 0:
        return False
    try:
        return proxy.stat().st_mtime >= source.stat().st_mtime
    except FileNotFoundError:
        return False


def generate_proxy(source: Path, proxy: Path) -> Path:
    """Transcode one chunk → proxy. Atomic write; caller pre-checks cache.

    Proxy recipe:
      960x540 · 30fps · H.264 High · keyframe every 1 frame · yuv420p ·
      AAC 96k stereo. All-intra guarantees seekable frame-by-frame.
    """
    proxy.parent.mkdir(parents=True, exist_ok=True)
    partial = proxy.with_suffix(proxy.suffix + ".partial")

    if os.environ.get(FFMPEG_ENV_MOCK) == "1":
        # Test mode: emit an 8-byte stub, then atomically rename.
        partial.write_bytes(b"PROXY\x00\x00\x00")
        os.replace(partial, proxy)
        return proxy

    cmd = [
        _ffmpeg_bin(),
        "-y",
        "-loglevel", "error",
        "-i", str(source),
        "-vf", "scale=960:540:flags=bicubic,fps=30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-crf", "23",
        "-g", "1",           # all-intra for scrub perf
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        str(partial),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        os.replace(partial, proxy)
    except BaseException:
        try:
            partial.unlink()
        except OSError:
            pass
        raise
    return proxy


def ensure_proxy(source: Path, proxies_dir: Path) -> Path:
    """Return path to a fresh proxy; generate if missing/stale."""
    proxy = proxy_path(proxies_dir, source.name)
    if is_fresh(source, proxy):
        return proxy
    return generate_proxy(source, proxy)
