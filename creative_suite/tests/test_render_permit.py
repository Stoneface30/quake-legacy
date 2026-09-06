"""Serving the reviewer is not permission to render.

Those were one thing, and that is why starting a session alt tabbed the
user's game: the review origin came up, drained its capture queue, and
WolfcamQL took the foreground off a live match.

The origin has every right to run while the user plays. It serves metadata,
dossiers, notes, tags, the queue and every clip already on disk without
touching the screen. What it may not do is decide, on its own, to film.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from engine.pantheon import render_permit as rp


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(rp.ENV_MODE, raising=False)
    monkeypatch.delenv(rp.LEGACY_ENV, raising=False)


def _quiet(monkeypatch, playing: bool):
    from creative_suite.engine import capture_guard
    monkeypatch.setattr(capture_guard, "game_is_running", lambda: playing)


# â”€â”€ the three answers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_granted_when_nothing_is_on_screen(monkeypatch):
    _quiet(monkeypatch, False)
    d = rp.check()
    assert d.permit is rp.Permit.GRANTED and d.may_render


def test_deferred_while_a_game_is_running(monkeypatch):
    _quiet(monkeypatch, True)
    d = rp.check()
    assert d.permit is rp.Permit.DEFERRED
    assert d.deferred and not d.may_render


def test_off_denies_even_on_an_idle_machine(monkeypatch):
    _quiet(monkeypatch, False)
    monkeypatch.setenv(rp.ENV_MODE, "off")
    assert rp.check().permit is rp.Permit.DENIED


def test_on_still_yields_to_a_running_game(monkeypatch):
    """There is no setting that means "film over the top of my match",
    because there is no situation in which that is what someone wanted."""
    _quiet(monkeypatch, True)
    monkeypatch.setenv(rp.ENV_MODE, "on")
    assert rp.check().permit is rp.Permit.DEFERRED


def test_an_unknown_mode_falls_back_to_auto(monkeypatch):
    monkeypatch.setenv(rp.ENV_MODE, "banana")
    assert rp.mode() == rp.MODE_AUTO


def test_the_reason_says_which_caller_was_refused(monkeypatch):
    _quiet(monkeypatch, True)
    assert "round render" in rp.check(purpose="round render").reason


def test_require_raises_only_when_there_is_no_queue_to_fall_back_on(
        monkeypatch):
    _quiet(monkeypatch, True)
    with pytest.raises(rp.RenderNotPermitted):
        rp.require("beauty pass")
    _quiet(monkeypatch, False)
    assert rp.require("beauty pass").may_render


# â”€â”€ one authority, not two â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_the_old_review_local_switch_no_longer_overrides_anything(
        monkeypatch):
    """CS_CAPTURE_ANYTIME meant exactly the thing no mode may mean. A second
    switch for one decision is how a user ends up hunting for the one that
    is actually in effect."""
    _quiet(monkeypatch, True)
    monkeypatch.setenv(rp.LEGACY_ENV, "1")
    assert rp.check().permit is rp.Permit.DEFERRED
    assert rp.status()["legacy_override_ignored"] is True

    from creative_suite.engine import capture_guard
    src = Path(capture_guard.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(
                getattr(node, "func", None), "attr", "") == "getenv":
            arg = node.args[0] if node.args else None
            if isinstance(arg, ast.Constant):
                assert arg.value != rp.LEGACY_ENV, \
                    "capture_guard still reads the retired switch"


def test_every_launch_path_asks_the_permit():
    """One gate, and all of them go through it. A launch path that does not
    ask becomes the next thing that alt tabs somebody."""
    for rel in ("creative_suite/engine/review_proxy.py",
                "creative_suite/engine/director_preview.py"):
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "render_permit" in src, f"{rel} launches without asking"


def test_nothing_else_invents_its_own_render_switch():
    """Grep is the point: a new allow-flag anywhere in the capture paths
    would silently become a second authority."""
    banned = ("CS_CAPTURE_ANYTIME", "ALLOW_RENDER", "FORCE_CAPTURE")
    for rel in ("creative_suite/engine/review_proxy.py",
                "creative_suite/engine/wolfcam_capture.py",
                "creative_suite/api/review.py"):
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for word in banned:
            assert word not in src, f"{rel} defines its own switch: {word}"


# â”€â”€ what the reviewer does with a refusal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_a_refused_job_is_deferred_and_never_failed():
    """DEFERRED is a queue state the user can wait out. FAILED would throw
    away work that is only waiting for the evening to end."""
    src = (REPO_ROOT / "creative_suite" / "engine"
           / "review_proxy.py").read_text(encoding="utf-8")
    i = src.index("def _worker_loop")
    block = src[i:i + 2200]
    assert "render_permit.check(" in block
    j = block.index("render_permit.check(")
    park = block[j:j + 400]
    assert "_queue.put(job)" in park
    assert "FAILED" not in park
    assert '"QUEUED"' in park


def test_the_api_reports_deferral_separately_from_failure():
    src = (REPO_ROOT / "creative_suite" / "api"
           / "review.py").read_text(encoding="utf-8")
    assert "render_deferred" in src
    assert '@router.get("/render_permit")' in src


def test_serving_the_reviewer_starts_no_capture(monkeypatch):
    """The origin comes up, the queue is reclaimed, and nothing is filmed
    while a game is on screen. This is the exact path that alt tabbed the
    user."""
    _quiet(monkeypatch, True)
    from creative_suite.engine import review_proxy as rpx
    captured: list[str] = []
    monkeypatch.setattr(rpx, "_generate",
                        lambda job: captured.append(job["key"]))
    monkeypatch.setattr(rpx, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(rpx.time, "sleep", lambda _s: None)

    job = {"key": "k1", "frag_id": 1, "demo_name": "d", "demo_path": "d",
           "start_ms": 0, "end_ms": 1000, "lock_waits": 0}
    seen: list[tuple] = []
    monkeypatch.setattr(rpx, "_set_state",
                        lambda *a, **k: seen.append((a, k)))
    rpx._queue.put(job)
    rpx._queue.put(None)                  # stop after one pass
    rpx._worker_loop()

    assert captured == [], "a capture ran while a game was on screen"
    assert any(a[1] == "QUEUED" for a, _k in seen), "job was not left queued"


# ── every launch site passes through the one gate ──────────────────────────

LAUNCH_SITES = {
    "creative_suite/engine/wolfcam_capture.py",
    "creative_suite/engine/director_preview.py",
    "creative_suite/engine/director_session.py",
    "creative_suite/api/_preview_job.py",
    "creative_suite/engine/supervisor.py",
    "engine/pantheon/shot.py",
    "engine/pantheon/offscreen.py",
    "engine/pantheon/cvar_probe.py",
    "engine/parser/playback_probe.py",
}


def _asks_the_permit(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("require", "check") \
                and getattr(node.func.value, "id", "") == "render_permit":
            return True
    return False


@pytest.mark.parametrize("site", sorted(LAUNCH_SITES))
def test_every_wolfcam_launch_site_asks_the_one_permit(site: str):
    src = (REPO_ROOT / site).read_text(encoding="utf-8")
    assert "from engine.pantheon import render_permit" in src, \
        f"{site} does not import the one authority (engine.pantheon.render_permit)"
    assert _asks_the_permit(REPO_ROOT / site), f"{site} launches a game process without asking"


def test_there_is_exactly_one_render_permit_module():
    assert not (REPO_ROOT / "creative_suite" / "engine" / "render_permit.py").exists()
    for base in ("creative_suite", "engine"):
        for p in (REPO_ROOT / base).rglob("*.py"):
            rel = p.relative_to(REPO_ROOT).as_posix()
            if "/tests/" in rel or "vendored" in rel or "/tools/" in rel:
                continue
            src = p.read_text(encoding="utf-8", errors="replace")
            assert "creative_suite.engine.render_permit" not in src, rel
            for word in ("PANTHEON_RENDER_ALLOWED", "PANTHEON_RENDER_FORCE"):
                assert word not in src, f"{rel} still names the retired switch {word}"


def test_no_wolfcam_launch_outside_the_known_sites():
    hits = []
    for base in ("creative_suite", "engine/pantheon", "engine/parser"):
        for p in (REPO_ROOT / base).rglob("*.py"):
            rel = p.relative_to(REPO_ROOT).as_posix()
            if "/tests/" in rel or "vendored" in rel or "/tools/" in rel:
                continue
            src = p.read_text(encoding="utf-8", errors="replace")
            if ("wolfcam_cmd(" in src or "wolfcamql.exe" in src) and \
                    ("Popen(" in src or "create_subprocess_exec" in src) and rel not in LAUNCH_SITES:
                hits.append(rel)
    assert not hits, f"unguarded launch sites: {hits}"


def test_the_process_scan_spawns_nothing(monkeypatch):
    """psutil or a toolhelp snapshot; never tasklist, never a shell."""
    import subprocess
    from creative_suite.engine import capture_guard
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    assert capture_guard.game_is_running() in (True, False)
    assert capture_guard._game_is_running_fallback(("nothing-of-that-name.exe",)) is False


# ── queues defer, they do not fail ─────────────────────────────────────────

def _refused(*a, **k):
    raise rp.RenderNotPermitted(rp.Decision(rp.Permit.DEFERRED, "test deferred: a game is running"))


def test_director_preview_worker_keeps_a_refused_job_queued(monkeypatch):
    from creative_suite.engine import director_preview as dpv
    from creative_suite.engine import review_proxy as revp
    states = []
    monkeypatch.setattr(dpv, "_set_state", lambda key, state, error=None, **kw:
                        states.append((key, state, error)))
    monkeypatch.setattr(revp, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(revp, "_release_lock", lambda: None)
    monkeypatch.setattr(revp, "_PERMIT_WAIT_S", 0.0)
    monkeypatch.setattr(dpv, "_generate", _refused)
    dpv._queue.put({"preview_key": "p1"})
    dpv._queue.put(None)
    dpv._worker_loop()
    assert any(s == dpv.STATE_QUEUED and str(e).startswith("RENDER DEFERRED") for _, s, e in states)
    assert not any(s == dpv.STATE_FAILED for _, s, _ in states)
    assert dpv._queue.get_nowait() == {"preview_key": "p1"}


@pytest.mark.asyncio
async def test_job_queue_marks_a_refused_job_deferred():
    import asyncio
    from creative_suite.api._render_worker import JobQueue
    q = JobQueue()
    await q.start()

    async def job(emit):
        _refused()

    jid = q.submit(job)
    for _ in range(50):
        await asyncio.sleep(0.02)
        if q.status(jid) in ("deferred", "failed", "done"):
            break
    await q.stop()
    assert q.status(jid) == "deferred"
    assert q.events(jid)[-1]["phase"] == "deferred"


def test_capture_demo_asks_before_any_process(monkeypatch, tmp_path):
    import subprocess
    from creative_suite.engine import wolfcam_capture as wc
    _quiet(monkeypatch, True)
    monkeypatch.delenv("CS_CAPTURE_MOCK", raising=False)
    monkeypatch.setattr(wc, "write_capture_cfg", lambda *a, **k: None)
    monkeypatch.setattr(subprocess, "Popen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    with pytest.raises(rp.RenderNotPermitted):
        wc.capture_demo("x.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1000}],
                        staging=tmp_path)


# ── disk policy: three thresholds, not one ─────────────────────────────────

def test_a_full_disk_defers_a_render_but_not_a_review_write(monkeypatch, tmp_path):
    from engine.pantheon import disk_policy as dp
    _quiet(monkeypatch, False)
    monkeypatch.setattr(dp, "free_bytes", lambda p: 300 * dp.MB)
    d = rp.check(purpose="proxy capture", output_dir=tmp_path)
    assert d.permit is rp.Permit.DEFERRED and "disk unsafe" in d.reason
    assert dp.review_db_write_safe(tmp_path).ok            # a verdict still fits
    assert not dp.large_build_safe(tmp_path).ok
    monkeypatch.setattr(dp, "free_bytes", lambda p: 10 * dp.GB)
    assert rp.check(purpose="proxy capture", output_dir=tmp_path).may_render
    # the job's own expected size counts
    assert not rp.check(purpose="beauty pass", output_dir=tmp_path,
                        expected_output_bytes=9 * dp.GB).may_render


def test_disk_policy_never_spawns(monkeypatch, tmp_path):
    import subprocess
    from engine.pantheon import disk_policy as dp
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    assert dp.free_bytes(tmp_path) >= 0


# ── the reviewer branch's vocabulary, against the same one permit ───────────

def test_a_batch_is_held_to_more_headroom_than_one_clip(monkeypatch, tmp_path):
    """The reviewer branch says check(batch=True); this branch says
    expected_output_bytes. Both must work, and batch must be the stricter of
    the two -- a whole run that fills the drive leaves broken media AND no
    space to record that it broke."""
    from engine.pantheon import disk_policy
    from engine.pantheon import render_permit as rp

    monkeypatch.setattr(rp, "mode", lambda: rp.MODE_AUTO)
    monkeypatch.setattr("creative_suite.engine.capture_guard.game_is_running",
                        lambda: False)
    # room for one clip, nowhere near room for a build
    one_job = disk_policy.RENDER_EXPECTED_DEFAULT + disk_policy.RENDER_MARGIN
    monkeypatch.setattr(disk_policy, "free_bytes", lambda path: one_job * 3)

    assert rp.check(purpose="one clip", output_dir=tmp_path).permit is rp.Permit.GRANTED
    assert rp.check(purpose="a whole run", output_dir=tmp_path,
                    batch=True).permit is rp.Permit.DEFERRED


def test_a_tiny_write_is_not_held_to_render_headroom(monkeypatch, tmp_path):
    """A verdict is a few bytes. Holding it to the space a capture needs is
    how a reviewer stops being able to record an opinion on a full disk."""
    from engine.pantheon import disk_policy

    monkeypatch.setattr(disk_policy, "free_bytes",
                        lambda path: disk_policy.REVIEW_DB_WRITE_SAFE * 2)
    assert disk_policy.REVIEW_DB_WRITE_SAFE * 2 < (
        disk_policy.RENDER_EXPECTED_DEFAULT + disk_policy.RENDER_MARGIN)
    assert disk_policy.review_db_write_safe(tmp_path).ok
    assert not disk_policy.render_job_safe(tmp_path).ok


# ── the leak that took six tests down with it ───────────────────────────────

def test_a_refused_review_job_is_requeued_and_leaves_no_residue(monkeypatch):
    """Deferring REQUEUES the job -- that is the whole point of DEFERRED --
    and `_queue` is module state shared with every other test in the suite.

    Kept from the reviewer branch because it cost real time: a test that
    proved the requeue and then left the job sitting there made six proxy
    tests fail later in the same run while passing in isolation, which is
    exactly how long that class of leak takes to explain.
    """
    from creative_suite.engine import review_proxy as rpx
    from engine.pantheon import render_permit as rp

    monkeypatch.setattr(rp, "check",
                        lambda **kw: rp.Decision(rp.Permit.DEFERRED, "test"))
    captured: list[str] = []
    monkeypatch.setattr(rpx, "_generate",
                        lambda job: captured.append(job["key"]))
    monkeypatch.setattr(rpx, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(rpx.time, "sleep", lambda _s: None)
    seen: list[tuple] = []
    monkeypatch.setattr(rpx, "_set_state",
                        lambda *a, **k: seen.append((a, k)))

    job = {"key": "leakprobe", "frag_id": 1, "demo_name": "d",
           "demo_path": "d", "start_ms": 0, "end_ms": 1000, "lock_waits": 0}
    rpx._queue.put(job)
    rpx._queue.put(None)
    try:
        rpx._worker_loop()
        assert captured == [], "a capture ran while the permit refused"
        assert any(a[1] == "QUEUED" for a, _k in seen), "job was not requeued"
    finally:
        while True:
            try:
                rpx._queue.get_nowait()
                rpx._queue.task_done()
            except Exception:                                  # noqa: BLE001
                break
        rpx._queued_keys.discard("leakprobe")
    assert rpx._queue.qsize() == 0, "the queue was left dirty for the suite"
