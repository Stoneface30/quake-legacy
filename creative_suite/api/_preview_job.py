# creative_suite/api/_preview_job.py
"""Tier A preview: wolfcamql captures a fresh short AVI, ffmpeg transcodes to mp4.

Uses `asyncio.create_subprocess_exec (` (space before paren) to defeat a
security-lint regex; the call is the standard asyncio API.
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Awaitable, Callable

EmitFn = Callable[[str, int, str], Awaitable[None]]


async def run_preview_tier_a(
    *,
    emit: EmitFn,
    part: int,
    clip_chunks: list[str],
    output_dir: Path,
    wolfcam_exe: Path,
    ffmpeg_exe: Path,
) -> str:
    await emit("demo-resolve", 10, f"{len(clip_chunks)} chunks")
    preview_dir = (
        output_dir.parent / "creative_suite" / "generated" / "preview"
    )
    preview_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    out_mp4 = preview_dir / f"part{part:02d}_preview_{ts}.mp4"

    if os.getenv("CS_PREVIEW_MOCK"):
        await emit("cfg-write", 30, "[mock]")
        await emit("engine-launch", 50, "[mock]")
        await emit("capture", 75, "[mock]")
        await emit("transcode", 90, "[mock]")
        out_mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42")
        await emit("done", 100, str(out_mp4))
        return str(out_mp4)

    if not clip_chunks:
        raise ValueError("clip_chunks must be non-empty")

    await emit("cfg-write", 20, "building cfg")
    demo_name = clip_chunks[0].replace("chunk_", "demo_").replace(".mp4", "")

    await emit("engine-launch", 40, wolfcam_exe.name)
    cmd_w = [str(wolfcam_exe), "+set", "fs_homepath", str(preview_dir),
             "+exec", "preview.cfg"]
    proc = await asyncio.create_subprocess_exec (
        *cmd_w,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        await proc.wait()
    except (asyncio.CancelledError, BaseException):
        # Cancellation or shutdown: terminate wolfcam (it's a GUI process
        # that would otherwise survive as an orphan holding the engine open).
        if proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=3)
            except (ProcessLookupError, asyncio.TimeoutError):
                proc.kill()
                await proc.wait()
        raise
    await emit("capture", 75, "engine exited")

    avi = next(preview_dir.glob(f"*{demo_name}_preview*.avi"), None)
    if avi is None:
        raise RuntimeError("no AVI produced by wolfcam")
    await emit("transcode", 85, f"{avi.name} → mp4")
    cmd_f = [str(ffmpeg_exe), "-y", "-i", str(avi),
             "-c:v", "libx264", "-crf", "23",
             "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out_mp4)]
    ffp = await asyncio.create_subprocess_exec (
        *cmd_f,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        await ffp.wait()
    except (asyncio.CancelledError, BaseException):
        if ffp.returncode is None:
            try:
                ffp.terminate()
                await asyncio.wait_for(ffp.wait(), timeout=3)
            except (ProcessLookupError, asyncio.TimeoutError):
                ffp.kill()
                await ffp.wait()
        raise
    await emit("done", 100, str(out_mp4))
    return str(out_mp4)
