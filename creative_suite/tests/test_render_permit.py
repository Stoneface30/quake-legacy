"""RenderPermit: rendering is denied by default, deferred while a game runs,
and no launch site spawns a game process without it."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from creative_suite.engine import render_permit as rp

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in (rp.ENV_ALLOW, rp.ENV_FORCE, rp.ENV_PROTECTED):
        monkeypatch.delenv(k, raising=False)


def test_default_is_deny():
    p = rp.check("unit test")
    assert p.decision is rp.Decision.DENIED_DEFAULT and not p.ok
    with pytest.raises(rp.RenderDenied) as ei:
        rp.require("unit test")
    assert ei.value.permit.decision is rp.Decision.DENIED_DEFAULT


def test_operator_setting_allows(monkeypatch):
    monkeypatch.setenv(rp.ENV_ALLOW, "1")
    monkeypatch.setattr(rp, "running_games", lambda: ())
    assert rp.check("capture").ok
    assert rp.require("capture").decision is rp.Decision.ALLOWED


def test_a_running_game_defers_even_when_allowed(monkeypatch):
    monkeypatch.setenv(rp.ENV_ALLOW, "1")
    monkeypatch.setattr(rp, "running_processes", lambda: ["explorer.exe", "quakelive_steam.exe"])
    p = rp.check("capture")
    assert p.decision is rp.Decision.DEFERRED_GAME_RUNNING and p.deferred
    assert p.games == ("quakelive_steam.exe",)
    with pytest.raises(rp.RenderDenied) as ei:
        rp.require("capture")
    assert ei.value.permit.deferred


def test_force_is_a_separate_explicit_override(monkeypatch):
    monkeypatch.setenv(rp.ENV_ALLOW, "1")
    monkeypatch.setattr(rp, "running_processes", lambda: ["quakelive.exe"])
    assert rp.check("capture").deferred
    monkeypatch.setenv(rp.ENV_FORCE, "1")
    assert rp.check("capture").ok
    # force never substitutes for permission
    monkeypatch.delenv(rp.ENV_ALLOW)
    assert rp.check("capture").decision is rp.Decision.DENIED_DEFAULT


def test_protected_list_is_extensible(monkeypatch):
    monkeypatch.setenv(rp.ENV_PROTECTED, "Doom.exe; cs2.exe")
    assert {"doom.exe", "cs2.exe"} <= set(rp.protected_games())
    assert "quakelive.exe" in rp.protected_games()


def test_process_scan_spawns_nothing(monkeypatch):
    """The scan is a toolhelp snapshot, never `tasklist` or a shell."""
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    names = rp.running_processes()
    assert isinstance(names, list)


# ── every launch site passes through the gate ──────────────────────────────

LAUNCH_SITES = {
    "creative_suite/engine/wolfcam_capture.py",
    "creative_suite/engine/director_preview.py",
    "creative_suite/engine/director_session.py",
    "creative_suite/api/_preview_job.py",
    "creative_suite/engine/supervisor.py",
    "engine/pantheon/shot.py",
    "engine/pantheon/cvar_probe.py",
    "engine/parser/playback_probe.py",
}


def _calls_require(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name == "require" and isinstance(f, ast.Attribute) and \
                    getattr(f.value, "id", "") in ("render_permit", "rp"):
                return True
            if name == "render_require":
                return True
    return False


@pytest.mark.parametrize("site", sorted(LAUNCH_SITES))
def test_every_wolfcam_launch_site_asks_the_permit(site: str):
    assert _calls_require(REPO / site), f"{site} launches a game process without render_permit.require()"


def test_no_wolfcam_launch_outside_the_known_sites():
    """A new Popen of wolfcamql anywhere else is a new unguarded site."""
    hits = []
    for base in ("creative_suite", "engine/pantheon", "engine/parser"):
        for p in (REPO / base).rglob("*.py"):
            rel = p.relative_to(REPO).as_posix()
            if "/tests/" in rel or "vendored" in rel or "/tools/" in rel:
                continue
            src = p.read_text(encoding="utf-8", errors="replace")
            if ("wolfcam_cmd(" in src or "wolfcamql.exe" in src) and \
                    ("Popen(" in src or "create_subprocess_exec" in src) and rel not in LAUNCH_SITES:
                hits.append(rel)
    assert not hits, f"unguarded launch sites: {hits} -- route them through render_permit and list them here"


# ── queues defer, they do not fail ─────────────────────────────────────────

def _denied(*a, **k):
    raise rp.RenderDenied(rp.Permit(rp.Decision.DENIED_DEFAULT, "test", "not allowed"))


def test_review_proxy_worker_keeps_a_denied_job_queued(monkeypatch):
    from creative_suite.engine import review_proxy as revp
    states = []
    monkeypatch.setattr(revp, "_set_state", lambda key, state, error=None, mp4_path=None:
                        states.append((key, state, error)))
    monkeypatch.setattr(revp, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(revp, "_release_lock", lambda: None)
    monkeypatch.setattr(revp, "_generate", _denied)
    monkeypatch.setattr(revp, "_DEFER_RETRY_S", 0.0)
    revp._queue.put({"key": "k1"})
    revp._queue.put(None)
    revp._worker_loop()
    assert ("k1", "GENERATING", None) in states
    assert any(s == "QUEUED" and str(e).startswith("RENDER DEFERRED") for _, s, e in states)
    assert not any(s == "FAILED" for _, s, _ in states)
    assert revp._queue.get_nowait() == {"key": "k1"}       # offered again later


def test_director_preview_worker_keeps_a_denied_job_queued(monkeypatch):
    from creative_suite.engine import director_preview as dpv
    from creative_suite.engine import review_proxy as revp
    states = []
    monkeypatch.setattr(dpv, "_set_state", lambda key, state, error=None, **kw:
                        states.append((key, state, error)))
    monkeypatch.setattr(revp, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(revp, "_release_lock", lambda: None)
    monkeypatch.setattr(revp, "_DEFER_RETRY_S", 0.0)
    monkeypatch.setattr(dpv, "_generate", _denied)
    dpv._queue.put({"preview_key": "p1"})
    dpv._queue.put(None)
    dpv._worker_loop()
    assert any(s == dpv.STATE_QUEUED and str(e).startswith("RENDER DEFERRED") for _, s, e in states)
    assert not any(s == dpv.STATE_FAILED for _, s, _ in states)
    assert dpv._queue.get_nowait() == {"preview_key": "p1"}


@pytest.mark.asyncio
async def test_job_queue_marks_a_denied_job_deferred():
    import asyncio
    from creative_suite.api._render_worker import JobQueue
    q = JobQueue()
    await q.start()

    async def job(emit):
        _denied()

    jid = q.submit(job)
    for _ in range(50):
        await asyncio.sleep(0.02)
        if q.status(jid) in ("deferred", "failed", "done"):
            break
    await q.stop()
    assert q.status(jid) == "deferred"
    assert q.events(jid)[-1]["phase"] == "deferred"


def test_capture_demo_is_denied_before_any_process(monkeypatch, tmp_path):
    """The core capture path asks the permit before Popen; with the default
    environment it raises and nothing is spawned."""
    import subprocess
    from creative_suite.engine import wolfcam_capture as wc
    monkeypatch.delenv("CS_CAPTURE_MOCK", raising=False)
    monkeypatch.setattr(wc, "write_capture_cfg", lambda windows, staging: None)
    monkeypatch.setattr(subprocess, "Popen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned")))
    with pytest.raises(rp.RenderDenied):
        wc.capture_demo("x.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 1000}],
                        staging=tmp_path)
