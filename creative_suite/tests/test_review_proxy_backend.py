"""The review path films offscreen, records what made each file, and does not
quietly open a window when it cannot."""
from __future__ import annotations

import sqlite3

import pytest

from creative_suite.engine import review_proxy as rp


@pytest.fixture
def wired(tmp_path, monkeypatch):
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(rp, "PROXY_DIR", tmp_path / "proxies")
    monkeypatch.setattr(rp, "LOCK_PATH", tmp_path / "_capture.lock")
    monkeypatch.delenv("CS_PROXY_WINDOW", raising=False)
    return tmp_path


def _windows():
    return [{"clip_name": "rp_test", "start_ms": 96000, "end_ms": 103000}]


def test_the_default_backend_is_the_hidden_desktop(wired, monkeypatch):
    seen = {}

    def fake_offscreen_capture(safe, windows, **kw):
        seen.update(kw)
        return {"ok": True, "avis": {"rp_test": str(wired / "x.avi")},
                "returncode": 0, "seconds": 3.0, "visible_windows": [],
                "stole_focus": False}

    from engine.pantheon import offscreen
    monkeypatch.setattr(offscreen, "capture", fake_offscreen_capture)
    monkeypatch.setattr("creative_suite.engine.wolfcam_capture.capture_demo",
                        lambda *a, **k: pytest.fail("a window was opened"))
    res, backend = rp._film("safe.dm_73", _windows(), profile="TR4SH_REVIEW_V2")
    assert backend == rp.BACKEND_OFFSCREEN and res["ok"]
    assert seen["profile"] == "TR4SH_REVIEW_V2", \
        "the review master must be named, or the BATCH master is used"


def test_a_backend_that_produced_nothing_fails_instead_of_opening_a_window(
        wired, monkeypatch):
    from engine.pantheon import offscreen
    monkeypatch.setattr(offscreen, "capture", lambda *a, **k: {
        "ok": False, "avis": {}, "detail": "no GL context", "returncode": 1})
    monkeypatch.setattr("creative_suite.engine.wolfcam_capture.capture_demo",
                        lambda *a, **k: pytest.fail("fell back to a window"))
    res, backend = rp._film("safe.dm_73", _windows(), profile="TR4SH_REVIEW_V2")
    assert not res["ok"] and backend == rp.BACKEND_OFFSCREEN
    assert "no GL context" in res["error"]


def test_an_operator_can_ask_to_watch_one(wired, monkeypatch):
    monkeypatch.setenv("CS_PROXY_WINDOW", "1")
    monkeypatch.setattr("creative_suite.engine.wolfcam_capture.capture_demo",
                        lambda *a, **k: {"ok": True, "avis": {"rp_test": "x.avi"}})
    _res, backend = rp._film("safe.dm_73", _windows(), profile="TR4SH_REVIEW_V2")
    assert backend == rp.BACKEND_WINDOW


def test_the_cache_records_what_made_each_file(wired):
    conn = rp.editorial_conn()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(review_proxies)")}
        conn.execute(
            "INSERT INTO review_proxies (key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state) VALUES ('k',1,'d',0,1,'p','QUEUED')")
        conn.commit()
    finally:
        conn.close()
    assert {"backend", "engine_version", "source_demo"} <= cols

    rp._set_state("k", "READY", mp4_path="m.mp4",
                  manifest={"backend": rp.BACKEND_OFFSCREEN,
                            "engine_version": "profile123",
                            "source_demo": "demos/x.dm_73"})
    conn = sqlite3.connect(rp.EDITORIAL_DB_PATH)
    try:
        row = conn.execute("select backend, engine_version, source_demo, state"
                           " from review_proxies where key='k'").fetchone()
    finally:
        conn.close()
    assert row == (rp.BACKEND_OFFSCREEN, "profile123", "demos/x.dm_73", "READY")


def test_a_proxy_from_before_the_migration_stays_usable(wired):
    """The backend is deliberately NOT in the cache key, so every clip already
    READY keeps its key, its file and its state."""
    key_then = rp.proxy_key("hash", 1000, 8000, "profileA")
    key_now = rp.proxy_key("hash", 1000, 8000, "profileA")
    assert key_then == key_now

    conn = rp.editorial_conn()
    try:
        conn.execute(
            "INSERT INTO review_proxies (key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state, mp4_path) VALUES (?,1,'d',1000,8000,"
            "'profileA','READY','old.mp4')", (key_then,))
        conn.commit()
        row = dict(conn.execute("select * from review_proxies where key=?",
                                (key_then,)).fetchone())
    finally:
        conn.close()
    assert row["state"] == "READY" and row["mp4_path"] == "old.mp4"
    assert row["backend"] is None, \
        "a pre-migration row should read NULL, which is the truth about it"


def test_the_tools_resolve_from_the_checkout_that_owns_the_data():
    """A git worktree of the code has no tools/ under it; every proxy failed
    on a missing ffmpeg.exe until this resolved like the databases do."""
    from engine.pantheon import store as S
    assert rp.FFMPEG.is_relative_to(S.PROJECT_ROOT)
    assert rp.FFMPEG.exists(), f"ffmpeg not found at {rp.FFMPEG}"
