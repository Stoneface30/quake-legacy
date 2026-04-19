from __future__ import annotations

import asyncio

import pytest

from creative_suite.api._render_worker import JobQueue


async def _job_quick(emit):
    await emit("phase-a", 10, "hi")
    await emit("phase-a", 100, "done")


@pytest.mark.asyncio
async def test_single_worker_runs_one_job_at_a_time() -> None:
    q = JobQueue()
    await q.start()
    try:
        jid = q.submit(_job_quick)
        assert jid
        with pytest.raises(RuntimeError, match="busy"):
            q.submit(_job_quick)
        for _ in range(50):
            await asyncio.sleep(0.02)
            if q.status(jid) == "done":
                break
        assert q.status(jid) == "done"
        events = q.events(jid)
        assert events[-1]["phase"] == "phase-a"
        assert events[-1]["pct"] == 100
    finally:
        await q.stop()


@pytest.mark.asyncio
async def test_failed_job_marks_failed() -> None:
    async def bad(emit):
        await emit("start", 0, "")
        raise RuntimeError("nope")
    q = JobQueue()
    await q.start()
    try:
        jid = q.submit(bad)
        for _ in range(50):
            await asyncio.sleep(0.02)
            if q.status(jid) in ("done", "failed"):
                break
        assert q.status(jid) == "failed"
    finally:
        await q.stop()
