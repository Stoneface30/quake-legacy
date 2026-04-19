# creative_suite/engine/supervisor.py
"""Wolfcamql subprocess supervisor for Tier B live scrubbing.

Spawns the engine with demo loaded, writes `seekclock` commands to stdin,
grabs engine-window frames via PIL.ImageGrab at 4 Hz, pushes JPEG bytes
into an asyncio queue so the FastAPI WebSocket can await frames.
"""
from __future__ import annotations

import asyncio
from pathlib import Path


class EngineSupervisor:
    def __init__(
        self, *, engine_cmd: list[str], thumb_dir: Path, mock_grab: bool = False,
    ) -> None:
        self.engine_cmd = engine_cmd
        self.thumb_dir = thumb_dir
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.mock_grab = mock_grab
        self._proc: asyncio.subprocess.Process | None = None
        self._grab_task: asyncio.Task[None] | None = None
        self._frames: asyncio.Queue[bytes] = asyncio.Queue(maxsize=4)
        self._stop = False
        self.last_seek_ms: int | None = None

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec (
            *self.engine_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._grab_task = asyncio.create_task(self._grab_loop())

    async def stop(self) -> None:
        self._stop = True
        if self._proc and self._proc.returncode is None:
            try:
                self._proc.terminate()
                await asyncio.wait_for(self._proc.wait(), timeout=3)
            except (ProcessLookupError, asyncio.TimeoutError):
                self._proc.kill()
                await self._proc.wait()
        if self._grab_task:
            self._grab_task.cancel()
            try: await self._grab_task
            except asyncio.CancelledError: pass

    async def seek(self, *, ms: int) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("engine not started")
        total_s = ms / 1000
        m = int(total_s // 60)
        s = total_s - m * 60
        line = f"seekclock {m}:{s:.1f}\n".encode("utf-8")
        self._proc.stdin.write(line)
        await self._proc.stdin.drain()
        self.last_seek_ms = ms

    async def next_frame(self, timeout_s: float = 1.0) -> bytes | None:
        try:
            return await asyncio.wait_for(self._frames.get(), timeout=timeout_s)
        except asyncio.TimeoutError:
            return None

    async def _grab_loop(self) -> None:
        while not self._stop:
            await asyncio.sleep(0.25)
            jpeg = self._grab_once()
            if jpeg is None: continue
            if self._frames.full():
                try: self._frames.get_nowait()
                except asyncio.QueueEmpty: pass
            await self._frames.put(jpeg)

    def _grab_once(self) -> bytes | None:
        if self.mock_grab:
            return b"\xff\xd8\xff\xe0mockjpeg"
        try:
            from PIL import ImageGrab
            import io
        except ImportError:
            return None
        img = ImageGrab.grab(all_screens=False)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()
