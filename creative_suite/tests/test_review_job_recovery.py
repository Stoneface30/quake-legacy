"""The media job state machine, and who is allowed to move it.

THE REVIEWER'S WORST FAILURE MODE IS A SPINNER THAT NEVER RESOLVES, and this
project has produced it two different ways:

1. Polling requeued failures. Observe FAILED -> requeue -> RENDERING -> fail
   -> observe -> requeue. The state oscillated forever and the page never
   showed a Retry button because it never saw a settled failure.

2. Jobs outliving the process that owned them. The queue is in memory, the
   state is in SQLite. After any restart -- deploy, crash, supervisor -- rows
   still marked QUEUED or GENERATING describe work no worker knows about.
   `request_proxy` returns them untouched, and the page polls a job that will
   never run. This one shows RENDERING, not FAILED, so there is not even a
   Retry to press.

Both are pinned here.

    STATE      set by
    MISSING    nobody -- the absence of a row
    QUEUED     request_proxy (first ask), explicit retry, reclaim at startup
    GENERATING the worker, when it picks the job up
    READY      the worker, after the mp4 exists on disk
    FAILED     the worker on error; reclaim when the demo is gone

A status READ never appears in that column, and that is the whole point.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import review_proxy as rp


@pytest.fixture()
def proxy_db(tmp_path, monkeypatch):
    """A private editorial database and a worker that never really captures."""
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(rp, "PROXY_DIR", tmp_path / "proxies")
    monkeypatch.setattr(rp, "LOCK_PATH", tmp_path / "capture.lock")
    monkeypatch.setattr(rp, "_profile_id", lambda: "testprofile")
    demo = tmp_path / "demo.dm_73"
    demo.write_bytes(b"not really a demo")
    monkeypatch.setattr(rp, "demo_source", lambda name: (demo, "hash" * 16))
    # No worker thread: these tests are about persisted state, and a real
    # worker would race the assertions.
    monkeypatch.setattr(rp, "_ensure_worker", lambda: None)
    # The queue and its in-flight key set are MODULE state, and
    # `Queue.unfinished_tasks` is invisible bookkeeping that survives a
    # drain. A leftover count makes `_queue.join()` in a later test block
    # forever -- which looks exactly like the production hang these tests
    # exist to prevent, and would be maddening to diagnose. A fresh queue
    # per test is the only isolation that actually isolates.
    import queue as _q
    monkeypatch.setattr(rp, "_queue", _q.Queue())
    monkeypatch.setattr(rp, "_queued_keys", set())
    return tmp_path


def _drain() -> None:
    """Simulate the death of the process that owned the queue.

    Both halves are in memory and both die together: the jobs themselves and
    the set of keys this process believed it was going to run. Clearing only
    one of them would leave a state no real restart can produce.
    """
    while not rp._queue.empty():
        rp._queue.get_nowait()
        rp._queue.task_done()
    with rp._queued_mutex:
        rp._queued_keys.clear()


def _row(key: str) -> dict:
    conn = rp.editorial_conn()
    try:
        r = conn.execute("SELECT * FROM review_proxies WHERE key=?",
                         (key,)).fetchone()
    finally:
        conn.close()
    return dict(r) if r else {}


def _request(**kw):
    return rp.request_proxy(frag_id=1, demo_name="demo.dm_73",
                            start_ms=1000, end_ms=7000, **kw)


# ── polling must not mutate ─────────────────────────────────────────────────

def test_observing_a_failed_job_does_not_restart_it(proxy_db):
    """OBSERVING FAILED MUST NOT RESTART THE JOB.

    The reviewer's page polls every two seconds. If each poll requeued the
    failure, the state would flip between FAILED and QUEUED forever and the
    user would watch a spinner instead of being offered a Retry.
    """
    st = _request()
    rp._set_state(st["key"], "FAILED", error="wolfcam said no")

    for _ in range(5):
        again = _request()
        assert again["state"] == "FAILED"
        assert again["error"] == "wolfcam said no"
    assert _row(st["key"])["state"] == "FAILED"


def test_an_explicit_retry_is_the_only_thing_that_revives_a_failure(proxy_db):
    st = _request()
    rp._set_state(st["key"], "FAILED", error="wolfcam said no")
    revived = _request(retry=True)
    assert revived["state"] == "QUEUED"
    assert _row(st["key"])["state"] == "QUEUED"


def test_a_ready_job_is_never_regenerated(proxy_db):
    """Forty seconds of wolfcam per clip. Never spend it twice."""
    st = _request()
    mp4 = proxy_db / "proxies" / f"{st['key']}.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"\x00" * 16)
    rp._set_state(st["key"], "READY", mp4_path=str(mp4))

    for retry in (False, True):
        again = _request(retry=retry)
        assert again["state"] == "READY", "a READY clip was requeued"
        assert again["mp4_path"] == str(mp4)


def test_a_ready_row_whose_file_vanished_is_reported_failed_not_ready(proxy_db):
    """A cache entry pointing at nothing must not serve a 404 as success."""
    st = _request()
    rp._set_state(st["key"], "READY", mp4_path=str(proxy_db / "gone.mp4"))
    assert rp.get_state(1)["state"] == "FAILED"


# ── surviving a restart ─────────────────────────────────────────────────────

def test_a_job_queued_before_a_restart_is_picked_up_again(proxy_db):
    """The endless-spinner case that no polling discipline can fix.

    The row says QUEUED. The in-memory queue that knew about it died with the
    previous process. Without reclaim, this item renders forever.
    """
    st = _request()
    assert st["state"] == "QUEUED"
    _drain()                              # the previous process's queue, gone

    reclaimed = rp.reclaim_orphaned_jobs()

    assert st["key"] in reclaimed
    assert rp._queue.qsize() == 1
    job = rp._queue.get_nowait()
    assert job["key"] == st["key"]
    # The worker needs every field, not just the key: a job missing
    # `lock_waits` or `demo_path` would explode on the worker thread and be
    # recorded as a capture failure.
    assert {"key", "frag_id", "demo_name", "demo_path", "start_ms", "end_ms",
            "lock_waits"} <= set(job)


def test_a_job_generating_when_the_process_died_is_requeued(proxy_db):
    """GENERATING is the worse case: its capture certainly did not survive."""
    st = _request()
    rp._set_state(st["key"], "GENERATING")
    _drain()

    assert st["key"] in rp.reclaim_orphaned_jobs()
    assert _row(st["key"])["state"] == "QUEUED"


def test_reclaim_settles_an_unrunnable_job_as_failed(proxy_db, monkeypatch):
    """A missing demo can never be captured.

    FAILED is honest and gives the reviewer a Retry button. QUEUED would be a
    lie that renders as a spinner forever.
    """
    st = _request()
    _drain()
    monkeypatch.setattr(rp, "demo_source", lambda name: (None, None))

    assert rp.reclaim_orphaned_jobs() == []
    row = _row(st["key"])
    assert row["state"] == "FAILED"
    assert row["error"]


def test_reclaim_ignores_jobs_from_another_capture_profile(proxy_db,
                                                           monkeypatch):
    """Old-profile rows describe footage nobody will ask for again.

    The cache key includes the profile id, so a row captured under a previous
    review profile can never be looked up. Re-capturing it would spend forty
    seconds of wolfcam on a clip no lookup can reach -- while the reviewer
    waits behind it for the clip they ARE looking at.
    """
    st = _request()
    conn = rp.editorial_conn()
    try:
        conn.execute("UPDATE review_proxies SET profile_id='oldprofile' "
                     "WHERE key=?", (st["key"],))
        conn.commit()
    finally:
        conn.close()
    _drain()

    assert rp.reclaim_orphaned_jobs() == []
    assert rp._queue.empty()
    assert _row(st["key"])["state"] == "QUEUED"      # left alone, not touched


def test_reclaim_is_idempotent(proxy_db):
    """It runs whenever a worker starts. Twice must not double-queue."""
    st = _request()
    _drain()
    rp.reclaim_orphaned_jobs()
    first = rp._queue.qsize()
    _drain()
    rp.reclaim_orphaned_jobs()
    assert rp._queue.qsize() == first == 1


def test_asking_about_a_queued_job_starts_a_worker_without_moving_it(tmp_path,
                                                                     monkeypatch):
    """The exact shape of the endless spinner, pinned.

    `request_proxy` returns early for a QUEUED row. That early return used to
    happen BEFORE `_ensure_worker()`, so once a process died holding the only
    copy of the queue, every later request short-circuited and no worker was
    ever started again. The row stayed QUEUED, the page polled forever, and
    because the state was never FAILED there was no Retry button either.

    Asking must therefore ensure a worker exists -- while leaving the job's
    own state exactly where it was.
    """
    import queue as _q
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(rp, "PROXY_DIR", tmp_path / "proxies")
    monkeypatch.setattr(rp, "_profile_id", lambda: "testprofile")
    monkeypatch.setattr(rp, "_queue", _q.Queue())
    monkeypatch.setattr(rp, "_queued_keys", set())
    demo = tmp_path / "demo.dm_73"
    demo.write_bytes(b"x")
    monkeypatch.setattr(rp, "demo_source", lambda name: (demo, "h" * 40))

    started: list[int] = []
    monkeypatch.setattr(rp, "_ensure_worker", lambda: started.append(1))

    first = rp.request_proxy(1, "demo.dm_73", 1000, 7000)
    assert first["state"] == "QUEUED"
    started.clear()

    again = rp.request_proxy(1, "demo.dm_73", 1000, 7000)

    assert again["state"] == "QUEUED", "the read moved the job"
    assert started, "asking about a queued job did not ensure a worker"


def test_reclaim_never_queues_a_job_this_process_already_holds(proxy_db):
    """Reclaim runs on every worker start; the queue may not be empty.

    Adopting a row that is already on this process's queue would capture the
    same forty seconds of wolfcam twice and, worse, let two workers fight
    over one output file.
    """
    st = _request()                      # already on the queue
    assert rp._queue.qsize() == 1

    assert rp.reclaim_orphaned_jobs() == []
    assert rp._queue.qsize() == 1


def test_the_worker_survives_a_skip_and_requeue(proxy_db, monkeypatch):
    """One task_done per get, on every path.

    A second call raises `ValueError: task_done() called too many times` on
    the worker thread -- which would kill the drain loop and turn every
    subsequent clip into an endless spinner.
    """
    import threading
    st = _request()
    holds = {"n": 0}

    def busy_then_free():
        holds["n"] += 1
        return holds["n"] > 1            # first call: lock held elsewhere

    monkeypatch.setattr(rp, "_try_acquire_lock", busy_then_free)
    monkeypatch.setattr(rp, "_release_lock", lambda: None)
    monkeypatch.setattr(rp, "_LOCK_RETRY_S", 0.01)
    monkeypatch.setattr(rp, "_generate", lambda job: rp._set_state(
        job["key"], "READY", mp4_path="x"))

    t = threading.Thread(target=rp._worker_loop, daemon=True)
    t.start()
    try:
        rp._queue.join()                 # raises here if task_done doubled
    finally:
        rp._queue.put(None)
        t.join(timeout=5)
    # A worker that outlives its own test keeps a reference to module state
    # that monkeypatch has already restored, and then mutates the REAL queue
    # underneath whatever runs next. Leaving one alive is how a green test
    # breaks a different file.
    assert not t.is_alive(), "the worker thread outlived its test"

    assert holds["n"] >= 2, "the job was never retried after the lock was busy"
    assert _row(st["key"])["state"] == "READY"
