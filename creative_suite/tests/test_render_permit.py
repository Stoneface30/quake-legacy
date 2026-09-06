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


# ── the three answers ───────────────────────────────────────────────────────

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


# ── one authority, not two ──────────────────────────────────────────────────

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


# ── what the reviewer does with a refusal ───────────────────────────────────

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
