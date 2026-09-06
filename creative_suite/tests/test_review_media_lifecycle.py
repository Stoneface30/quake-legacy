"""Failed review jobs remain inspectable until an explicit retry."""
from queue import Queue

from creative_suite.engine import review_proxy as rp


def test_polling_does_not_requeue_failed_capture(tmp_path, monkeypatch):
    demo = tmp_path / "sample.dm_73"
    demo.write_bytes(b"synthetic test source")
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    monkeypatch.setattr(rp, "demo_source", lambda name: (demo, "test-hash"))
    monkeypatch.setattr(rp, "_profile_id", lambda: "test-profile")
    monkeypatch.setattr(rp, "_queue", Queue())
    monkeypatch.setattr(rp, "_ensure_worker", lambda: None)
    first = rp.request_proxy(1, demo.name, 0, 6000)
    assert first["state"] == "QUEUED", first
    rp._queue.get_nowait()
    rp._set_state(first["key"], "FAILED", error="test failure")
    polled = rp.request_proxy(1, demo.name, 0, 6000)
    assert polled["state"] == "FAILED"
    assert polled["error"] == "test failure"
    assert rp._queue.empty()
    retried = rp.request_proxy(1, demo.name, 0, 6000, retry=True)
    assert retried["state"] == "QUEUED"
    assert rp._queue.qsize() == 1


def test_annotation_offset_matches_the_render_intro() -> None:
    from creative_suite.config import Config
    from creative_suite.engine.config import Config as RenderConfig
    from creative_suite.engine.title_card import render_title_card
    import inspect
    title_duration = inspect.signature(render_title_card).parameters["duration"].default
    assert Config().pre_content_offset_s == RenderConfig().intro_clip_duration + title_duration


def test_scene_state_and_failure_are_exposed_without_video_retry(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from creative_suite.api import review
    app = FastAPI()
    app.include_router(review.router)
    monkeypatch.setattr(review, "_scene_proxy", lambda item_id: {
        "key": "synthetic-job", "state": "FAILED", "error": "synthetic failure"})
    with TestClient(app) as client:
        state = client.get("/api/review/media_state/scene/USER_FRAG:1")
        assert state.status_code == 200
        assert state.json()["ready"] is False
        assert state.json()["state"] == "FAILED"
        assert state.json()["job_id"] == "synthetic-job"
        media = client.get("/api/review/media/scene/USER_FRAG:1")
        assert media.status_code == 503
        assert media.json()["detail"]["error"] == "synthetic failure"


def test_preview_files_are_served_at_the_url_used_by_the_panel(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from creative_suite.app import create_app
    output = tmp_path / "output"
    output.mkdir()
    (output / "part04.mp4").write_bytes(b"output proof")
    preview = tmp_path / "creative_suite" / "generated" / "preview"
    preview.mkdir(parents=True)
    (preview / "draft.mp4").write_bytes(b"preview proof")
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(output))
    with TestClient(create_app()) as client:
        assert client.get("/media/phase1/part04.mp4").content == b"output proof"
        assert client.get("/media/preview/draft.mp4").content == b"preview proof"
        assert client.get("/media/part04.mp4").content == b"output proof"


# ── an old clip that plays beats a new one still rendering ──────────────────

def test_a_ready_older_profile_beats_a_pending_current_one(tmp_path,
                                                           monkeypatch):
    """Changing the review profile to 720p30 changed the cache key. Without
    a ladder, every clip already on disk turned into a spinner the moment a
    replacement was queued -- a strictly worse reviewer than the day before.

    Measured on the live store when this landed: 123 frags had media, 109
    were playable, and 81 of those played only because of this fallback.
    """
    from creative_suite.engine import review_proxy as rp
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "ed.db")
    monkeypatch.setattr(rp, "_profile_id", lambda: "NEWPROFILE")

    mp4 = tmp_path / "old.mp4"
    mp4.write_bytes(b"\x00" * 32)
    conn = rp.editorial_conn()
    try:
        conn.execute(
            "INSERT INTO review_proxies(key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state, mp4_path, created_at, updated_at)"
            " VALUES('old', 7, 'd', 0, 6000, 'OLDPROFILE', 'READY', ?,"
            " '2026-01-01 00:00:00', '2026-01-01 00:00:00')", (str(mp4),))
        conn.execute(
            "INSERT INTO review_proxies(key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state, mp4_path, created_at, updated_at)"
            " VALUES('new', 7, 'd', 0, 6000, 'NEWPROFILE', 'QUEUED', NULL,"
            " '2026-02-02 00:00:00', '2026-02-02 00:00:00')")
        conn.commit()
    finally:
        conn.close()

    st = rp.get_state(7)
    assert st["state"] == "READY", "the newer QUEUED row shadowed a playable clip"
    assert st["compatible_older_profile"] is True
    assert st["mp4_path"] == str(mp4)


def test_the_current_profile_wins_when_both_are_ready(tmp_path, monkeypatch):
    """The fallback is a floor, not a preference. Once the current profile
    has a clip, that is the one to serve."""
    from creative_suite.engine import review_proxy as rp
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "ed.db")
    monkeypatch.setattr(rp, "_profile_id", lambda: "NEWPROFILE")
    old, new = tmp_path / "o.mp4", tmp_path / "n.mp4"
    old.write_bytes(b"\x00" * 8); new.write_bytes(b"\x00" * 8)
    conn = rp.editorial_conn()
    try:
        for key, prof, path, when in (
                ("old", "OLDPROFILE", old, "2026-03-03 00:00:00"),
                ("new", "NEWPROFILE", new, "2026-01-01 00:00:00")):
            conn.execute(
                "INSERT INTO review_proxies(key, frag_id, demo_name, start_ms,"
                " end_ms, profile_id, state, mp4_path, created_at, updated_at)"
                " VALUES(?, 8, 'd', 0, 6000, ?, 'READY', ?, ?, ?)",
                (key, prof, str(path), when, when))
        conn.commit()
    finally:
        conn.close()
    st = rp.get_state(8)
    assert st["mp4_path"] == str(new), "an older clip outranked the current one"
    assert not st.get("compatible_older_profile")


def test_a_ready_row_whose_file_is_gone_is_not_offered(tmp_path, monkeypatch):
    from creative_suite.engine import review_proxy as rp
    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "ed.db")
    monkeypatch.setattr(rp, "_profile_id", lambda: "NEWPROFILE")
    conn = rp.editorial_conn()
    try:
        conn.execute(
            "INSERT INTO review_proxies(key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state, mp4_path, created_at, updated_at)"
            " VALUES('gone', 9, 'd', 0, 6000, 'OLDPROFILE', 'READY',"
            " ?, '2026-01-01 00:00:00', '2026-01-01 00:00:00')",
            (str(tmp_path / "missing.mp4"),))
        conn.commit()
    finally:
        conn.close()
    assert rp.get_state(9)["state"] == "FAILED"
