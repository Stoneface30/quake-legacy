"""Single-worker asyncio job queue. Depth=1. Concurrent submit raises.

A job is an async callable taking one argument: `emit(phase, pct, msg)`.
Events are retained on the job for SSE consumers.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Awaitable, Callable


Job = Callable[[Callable[[str, int, str], Awaitable[None]]], Awaitable[None]]


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._current: str | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._pending: tuple[str, Job] | None = None
        self._wakeup = asyncio.Event()
        self._stop = False

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop = True
        self._wakeup.set()
        if self._worker_task is not None:
            await self._worker_task
            self._worker_task = None

    def submit(self, job: Job) -> str:
        if self._current is not None or self._pending is not None:
            raise RuntimeError("busy — another render is running")
        jid = uuid.uuid4().hex[:10]
        self._jobs[jid] = {
            "status": "queued",
            "events": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        self._pending = (jid, job)
        self._wakeup.set()
        return jid

    def status(self, jid: str) -> str:
        return self._jobs.get(jid, {}).get("status", "unknown")

    def events(self, jid: str) -> list[dict[str, Any]]:
        return list(self._jobs.get(jid, {}).get("events", []))

    async def _run(self) -> None:
        while not self._stop:
            await self._wakeup.wait()
            self._wakeup.clear()
            if self._stop:
                return
            if self._pending is None:
                continue
            jid, job = self._pending
            self._pending = None
            self._current = jid
            self._jobs[jid]["status"] = "running"

            async def emit(phase: str, pct: int, msg: str, _jid: str = jid) -> None:
                self._jobs[_jid]["events"].append({
                    "phase": phase, "pct": pct, "msg": msg,
                    "ts": datetime.utcnow().isoformat(),
                })

            try:
                await job(emit)
                self._jobs[jid]["status"] = "done"
            except Exception as exc:
                self._jobs[jid]["events"].append({
                    "phase": "failed", "pct": 100, "msg": str(exc),
                    "ts": datetime.utcnow().isoformat(),
                })
                self._jobs[jid]["status"] = "failed"
            finally:
                self._current = None
