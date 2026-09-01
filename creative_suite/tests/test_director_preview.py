"""DIRECTOR preview — CHANGE IT / REFRESH IT / SEE IT (directive §11-13, §38).

Covers the five properties the milestone actually stands on:

1. **Preview key stability and reuse (§12).** The same draft produces the
   same key; irrelevant panel bookkeeping does not change it; a READY
   artifact is returned without re-running the pipeline.
2. **The generation guard (§12).** Two overlapping jobs, the OLD one
   finishing LAST. Its artifact is still cached, but it must not become the
   frag's current preview and its own state must report ``stale``.
3. **Previewing never saves (§11).** No shot_plan row, no scene recipe, and
   the recognition databases are not written.
4. **Music-only change keeps the camera artifact (§38).** Same gameplay,
   TimeMap, camera, FX and look with only the MusicPlacement differing must
   produce a different audio path and a byte-identical ``.cam10``.
5. **Trim to exact TimeMap duration.** The mock capture deliberately renders
   a raw file with the guard margin AND a non-deterministic-looking tail; the
   delivered mp4 must still land on the TimeMap's edit duration.

Everything runs under ``CS_PREVIEW_DIRECTOR_MOCK=1`` — real ffmpeg, no
wolfcam — so the state machine, the trim and the mux are exercised for real.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import director_draft as dd_mod
from creative_suite.api import frags as frags_mod
from creative_suite.app import create_app
from creative_suite.engine import director_preview as dp
from creative_suite.engine import review_proxy

DEMO = "CA-preview-demo.dm_73"
IMPACT_MS = 291650
WINDOW_PRE, WINDOW_POST = 4000, 3000


def _build_frag_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """CREATE TABLE recognized_frags (
            id INTEGER PRIMARY KEY,
            demo_name TEXT, content_hash TEXT, server_time_ms INTEGER,
            round INTEGER, mod INTEGER, weapon_name TEXT, victim_client INTEGER,
            classes TEXT, attributes TEXT,
            highlight_score REAL DEFAULT 0, reasons TEXT,
            recognition_version INTEGER DEFAULT 2,
            clutch_score REAL DEFAULT 0, drama_score REAL DEFAULT 0);
        CREATE TABLE recognition_projectile_paths (
            demo_name TEXT, server_time_ms INTEGER, version INTEGER, path TEXT);
        """)
    attributes = {"mode_pool": "MAIN_CA", "projectile_impact_t": IMPACT_MS,
                  "projectile_path_confidence": "CONFIRMED", "map": "quarantine"}
    conn.execute(
        "INSERT INTO recognized_frags (id, demo_name, content_hash,"
        " server_time_ms, round, weapon_name, victim_client, classes,"
        " attributes, highlight_score, reasons)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (1, DEMO, "a" * 64, IMPACT_MS, 8, "ROCKET", 4,
         json.dumps([{"name": "DIRECT_ROCKET", "confidence": "CONFIRMED"}]),
         json.dumps(attributes), 40.9, json.dumps([])))
    # A real-shaped 1125 ms rocket flight (the canary's geometry, rounded):
    # enough points and enough flight for a projectile camera to be usable.
    launch_t = IMPACT_MS - 1125
    points = [[int(1125 * i / 45), 751.1 + (1499.0 - 751.1) * i / 45,
               1018.2 + (141.0 - 1018.2) * i / 45,
               632.1 + (668.0 - 632.1) * i / 45] for i in range(46)]
    conn.execute(
        "INSERT INTO recognition_projectile_paths VALUES (?,?,?,?)",
        (DEMO, IMPACT_MS, 1, json.dumps({
            "launch": {"t": launch_t, "pos": [751.1, 1018.2, 632.1],
                       "dir": [0.6489, -0.7608, 0.0091]},
            "impact": {"t": IMPACT_MS, "pos": [1499.0, 141.0, 668.0]},
            "points": points, "confidence": "CONFIRMED"})))
    conn.commit()
    conn.close()


def _build_demo_v2_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE generated_clips (
            generated_clip_id INTEGER PRIMARY KEY,
            demo_name TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
            capture_start_ms INTEGER NOT NULL, capture_end_ms INTEGER NOT NULL,
            frag_offsets_ms TEXT, tier TEXT, class TEXT,
            qa_status TEXT DEFAULT 'PENDING', avi_path TEXT,
            rank_score REAL, map TEXT, victims TEXT, mods TEXT)""")
    conn.commit()
    conn.close()


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    frag_db = tmp_path / "frag_recognition.db"
    demo_db = tmp_path / "demo_v2.db"
    plan_db = tmp_path / "cinematic.db"
    _build_frag_db(frag_db)
    _build_demo_v2_db(demo_db)
    monkeypatch.setattr(frags_mod, "FRAG_DB_PATH", frag_db)
    monkeypatch.setattr(frags_mod, "DEMO_V2_DB_PATH", demo_db)
    monkeypatch.setattr(dd_mod, "SHOT_PLAN_DB_PATH", plan_db)
    monkeypatch.setattr(review_proxy, "EDITORIAL_DB_PATH",
                        tmp_path / "editorial.db")
    monkeypatch.setattr(review_proxy, "FRAGS_REBUILT_DB_PATH",
                        tmp_path / "frags_rebuilt.db")
    monkeypatch.setattr(dp, "PREVIEW_DIR", tmp_path / "previews")
    monkeypatch.setattr(dp, "MUSIC_FEATURE_DB_PATH", tmp_path / "music.db")
    monkeypatch.setenv("CS_PREVIEW_DIRECTOR_MOCK", "1")
    frags_mod._classes_cache.clear()
    frags_mod._taxonomy_cache.clear()
    dd_mod.reset_store()
    return {"frag_db": frag_db, "demo_db": demo_db, "plan_db": plan_db,
            "tmp": tmp_path}


@pytest.fixture
def client(env: dict[str, Path]) -> TestClient:
    return TestClient(create_app())


def _frag() -> dict:
    return dd_mod._preview_frag(1)


def _draft(**patch) -> dict:
    draft = dd_mod._default_draft(1)
    draft.update(patch)
    return draft


def _music(track_hash: str, start_us: int) -> dict:
    return {"track_hash": track_hash, "source_start_us": start_us,
            "program_edit_start_us": 0, "source_end_us": None}


# ------------------------------------------------------------ preview key

def test_preview_key_is_stable_for_the_same_draft(env) -> None:
    recipe = dp.build_preview_recipe(_frag())
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id,
                edit_duration_us=recipe.time_map[-1].edit_end_us)
    assert (dp.compute_preview_key(draft=_draft(), **args)
            == dp.compute_preview_key(draft=_draft(), **args))


def test_preview_key_ignores_panel_bookkeeping(env) -> None:
    """dirty / saved_recipe_id / preview do not change a single pixel."""
    frag = _frag()
    recipe = dp.build_preview_recipe(frag)
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id, edit_duration_us=7_000_000)
    clean = _draft()
    noisy = _draft(dirty=True, saved_recipe_id="deadbeef", preview="STALE")
    assert (dp.compute_preview_key(draft=clean, **args)
            == dp.compute_preview_key(draft=noisy, **args))


def test_preview_key_ignores_controls_the_mode_does_not_use(env) -> None:
    """ORBIT does not draw or consume side_offset — nudging it must not
    invalidate a perfectly good cached capture."""
    recipe = dp.build_preview_recipe(_frag())
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id, edit_duration_us=7_000_000)
    base = _draft()
    moved = _draft()
    moved["camera"] = {**base["camera"], "side_offset": 512.0}
    assert base["camera"]["mode"] == "ORBIT"
    assert (dp.compute_preview_key(draft=base, **args)
            == dp.compute_preview_key(draft=moved, **args))


def test_preview_key_changes_with_look_fx_and_camera(env) -> None:
    recipe = dp.build_preview_recipe(_frag())
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id, edit_duration_us=7_000_000)
    base = dp.compute_preview_key(draft=_draft(), **args)
    keys = {base}
    for patch in ({"look": {"look": "PANTHEON", "show_depth": False}},
                  {"fx": {"rocket_fx": "HERO", "ghost": "OFF"}},
                  {"camera": {**dd_mod.DEFAULT_CAMERA, "distance": 400.0}},
                  {"music": _music("b" * 64, 0)}):
        keys.add(dp.compute_preview_key(draft=_draft(**patch), **args))
    assert len(keys) == 5, "each of these changes the picture or the audio"


def test_preview_key_includes_runtime_baseline(env, monkeypatch) -> None:
    """A capture under a different runtime baseline IS a different picture —
    the canary proved it with cg_drawCameraPath."""
    recipe = dp.build_preview_recipe(_frag())
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id, edit_duration_us=7_000_000,
                draft=_draft())
    before = dp.compute_preview_key(**args)
    from creative_suite.engine import pantheon_runtime
    monkeypatch.setitem(pantheon_runtime.RUNTIME_BASELINE,
                        "cg_drawCameraPath", "1")
    assert dp.compute_preview_key(**args) != before


def test_ready_artifact_is_reused_without_recapture(client, env) -> None:
    first = client.post("/api/frags/1/director/preview").json()
    dp.drain_for_tests()
    assert client.get(f"/api/director/preview/{first['preview_key']}"
                      ).json()["state"] == "READY"
    mp4 = dp.media_path(first["preview_key"])
    stamp = mp4.stat().st_mtime_ns

    second = client.post("/api/frags/1/director/preview").json()
    assert second["preview_key"] == first["preview_key"]
    assert second["state"] == "READY"          # served from cache, not queued
    assert second["generation"] > first["generation"]
    assert dp.media_path(second["preview_key"]).stat().st_mtime_ns == stamp


# ----------------------------------------------------------- generations

def test_generation_increases_per_request(client, env) -> None:
    seen = [client.post("/api/frags/1/director/preview").json()["generation"]
            for _ in range(3)]
    assert seen == sorted(seen) and len(set(seen)) == 3


def test_old_job_finishing_last_does_not_become_current(env) -> None:
    """§12, the whole point, with two genuinely overlapping jobs.

    A (a fresh draft) starts capturing. While it is still in flight the user
    goes back to a draft that is already cached, so B completes IMMEDIATELY
    at a HIGHER generation and becomes the frag's current preview. A then
    finishes. Its artifact is legitimately cached under its own key — but it
    must not take the pointer back to the older draft, and its own state must
    report ``stale`` so a panel still polling it ignores the result.
    """
    frag = _frag()
    draft_b = _draft(look={"look": "PANTHEON", "show_depth": False})
    draft_a = _draft(camera={**dd_mod.DEFAULT_CAMERA, "distance": 512.0})

    # Warm B's artifact so a later request for it is an instant cache hit.
    warm = dp.request_preview(frag, draft_b)
    dp.drain_for_tests()
    assert dp.get_preview(warm["preview_key"])["state"] == "READY"

    gate = threading.Event()
    real_generate = dp._generate
    finished: list[int] = []

    def gated(job):
        assert gate.wait(60), "the gated job was never released"
        real_generate(job)
        finished.append(int(job["generation"]))

    dp._generate = gated
    try:
        a = dp.request_preview(frag, draft_a)          # queued, worker blocks
        assert a["state"] == "QUEUED"
        b = dp.request_preview(frag, draft_b)          # cache hit, publishes
        assert b["state"] == "READY"
        assert b["generation"] > a["generation"]
        assert dp.current_preview(1)["generation"] == b["generation"]
        gate.set()                                     # now let A finish LAST
        dp.drain_for_tests()
    finally:
        dp._generate = real_generate
        gate.set()

    assert finished == [a["generation"]], "A must be the one that finished last"
    current = dp.current_preview(1)
    assert current["preview_key"] == b["preview_key"]
    assert current["generation"] == b["generation"]

    state_a = dp.get_preview(a["preview_key"])
    assert state_a["state"] == "READY"          # its artifact is still valid
    assert state_a["stale"] is True             # but the panel must ignore it
    assert dp.get_preview(b["preview_key"])["stale"] is False


def test_state_endpoint_reports_generation_and_staleness(client, env) -> None:
    first = client.post("/api/frags/1/director/preview").json()
    dp.drain_for_tests()
    client.put("/api/frags/1/director/draft",
               json={"look": {"look": "PANTHEON"}})
    second = client.post("/api/frags/1/director/preview").json()
    dp.drain_for_tests()
    old = client.get(f"/api/director/preview/{first['preview_key']}").json()
    new = client.get(f"/api/director/preview/{second['preview_key']}").json()
    assert set(old) == {"state", "generation", "media_url", "error", "stale"}
    assert old["stale"] is True and new["stale"] is False
    assert old["generation"] < new["generation"]


def test_unknown_preview_key_404(client, env) -> None:
    assert client.get("/api/director/preview/" + "0" * 64).status_code == 404
    assert client.get("/api/director/preview/" + "0" * 64 + "/media"
                      ).status_code == 404


# -------------------------------------------------------------- no saving

def test_preview_never_persists_a_recipe(client, env) -> None:
    """§11: only SAVE RECIPE writes. A preview must leave cinematic.db and the
    read-only recognition databases untouched."""
    plan_db = env["plan_db"]
    frag_mtime = env["frag_db"].stat().st_mtime_ns
    demo_mtime = env["demo_db"].stat().st_mtime_ns

    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "PROJECTILE"}})
    client.post("/api/frags/1/director/preview")
    dp.drain_for_tests()

    assert not plan_db.exists(), "preview must not create the shot-plan store"
    assert env["frag_db"].stat().st_mtime_ns == frag_mtime
    assert env["demo_db"].stat().st_mtime_ns == demo_mtime
    assert client.get("/api/frags/1/director/draft").json()[
        "saved_recipe_id"] is None


def test_save_recipe_still_persists(client, env) -> None:
    client.put("/api/frags/1/director/draft", json={"camera": {"mode": "ORBIT"}})
    client.post("/api/frags/1/director/preview")
    dp.drain_for_tests()
    saved = client.post("/api/frags/1/director/draft/save", json={}).json()
    assert saved["scene_recipe_id"]
    assert env["plan_db"].exists()


# ---------------------------------------------------------------- music

def test_music_only_change_keeps_the_same_camera_artifact(env) -> None:
    """§38 architecture test. Same gameplay, TimeMap, camera, FX and look;
    ONLY the MusicPlacement differs. The compiled .cam10 must be byte
    identical — proof the audio path cannot reach the video path."""
    frag = _frag()
    a = dp.build_plan(frag, _draft(music=_music("a" * 64, 0)))
    b = dp.build_plan(frag, _draft(music=_music("b" * 64, 30_000_000)))

    assert a.music != b.music
    assert a.recipe.recipe_id == b.recipe.recipe_id
    out = env["tmp"] / "cams"
    cam_a = dp.build_camera_artifact(a, out, "arch_a", tracer=None)
    cam_b = dp.build_camera_artifact(b, out, "arch_b", tracer=None)
    assert cam_a["cam10_hash"] is not None
    assert cam_a["cam10_hash"] == cam_b["cam10_hash"]
    assert (Path(cam_a["cam10_path"]).read_bytes()
            == Path(cam_b["cam10_path"]).read_bytes())


def test_music_change_produces_a_different_preview_key(env) -> None:
    recipe = dp.build_preview_recipe(_frag())
    args = dict(frag_id=1, demo_sha256="a" * 64, demo_name=DEMO,
                recipe_id=recipe.recipe_id, edit_duration_us=7_000_000)
    k1 = dp.compute_preview_key(draft=_draft(music=_music("a" * 64, 0)), **args)
    k2 = dp.compute_preview_key(draft=_draft(music=_music("a" * 64, 5_000_000)),
                                **args)
    assert k1 != k2


def test_music_selection_validates(client, env) -> None:
    ok = client.put("/api/frags/1/director/draft",
                    json={"music": _music("c" * 64, 1_000_000)})
    assert ok.status_code == 200
    assert ok.json()["music"]["track_hash"] == "c" * 64
    assert client.put("/api/frags/1/director/draft",
                      json={"music": {"track_hash": "nope"}}).status_code == 422
    assert client.put("/api/frags/1/director/draft",
                      json={"music": {"track_hash": "c" * 64,
                                      "source_start_us": -1}}).status_code == 422
    cleared = client.put("/api/frags/1/director/draft", json={"music": None})
    assert cleared.json()["music"] is None


def test_music_is_muxed_into_the_preview(env, tmp_path, monkeypatch) -> None:
    """A selected region must actually reach the delivered mp4 — different
    audio, identical video path."""
    from creative_suite.engine.music_features_v2 import (MusicFeatureStore,
                                                         MusicFeatureV2)
    track = tmp_path / "track.wav"
    subprocess.run([str(dp.FFMPEG), "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", "sine=frequency=880",
                    "-t", "40", str(track)], check=True, timeout=180)
    track_hash = MusicFeatureStore.full_content_hash(track)
    store = MusicFeatureStore(tmp_path / "music.db")
    store.put(MusicFeatureV2(
        track_hash=track_hash, path=str(track), duration_us=40_000_000,
        sample_rate=44100, channels=1, extractor_version="test",
        schema_version=2, status="OK", bpm=None, bpm_confidence=None,
        beats_us=(), beat_confidence=None, onset_curve=(), energy_curve=(),
        loudness_curve=(), spectral_curve=(), bar_grid_estimate_us=(),
        section_boundary_estimates_us=(), phrase_boundary_estimates_us=(),
        regions=()))

    plan = dp.build_plan(_frag(), _draft(music=_music(track_hash, 2_000_000)))
    assert plan.music_path == str(track)

    frag = _frag()
    silent = dp.request_preview(frag, _draft())
    scored = dp.request_preview(frag, _draft(music=_music(track_hash, 2_000_000)))
    dp.drain_for_tests()
    a, b = dp.media_path(silent["preview_key"]), dp.media_path(scored["preview_key"])
    assert a is not None and b is not None and a != b
    assert _mean_volume(a) != _mean_volume(b)
    assert abs(dp.probe_duration_s(a) - dp.probe_duration_s(b)) < 0.05


def _mean_volume(path: Path) -> float:
    out = subprocess.run(
        [str(dp.FFMPEG), "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"], capture_output=True, timeout=180)
    for line in (out.stderr or b"").decode(errors="replace").splitlines():
        if "mean_volume:" in line:
            return round(float(line.split("mean_volume:")[1].split("dB")[0]), 2)
    return 0.0


# ----------------------------------------------------------------- trim

def test_preview_is_trimmed_to_the_exact_timemap_duration(env) -> None:
    """The raw capture carries the guard margin on both ends plus a ragged
    tail; the delivered file must be the TimeMap's edit duration, taken from
    the recipe and never from the captured file's own length."""
    frag = _frag()
    recipe = dp.build_preview_recipe(frag)
    expected = (recipe.time_map[-1].edit_end_us
                - recipe.time_map[0].edit_start_us) / 1_000_000.0
    assert expected == pytest.approx((WINDOW_PRE + WINDOW_POST) / 1000.0)

    res = dp.request_preview(frag, _draft())
    dp.drain_for_tests()
    mp4 = dp.media_path(res["preview_key"])
    assert mp4 is not None
    # <= 1 frame at the output rate. Total-duration matching is the trim
    # contract; hero-event placement is measured separately against the
    # engine (docs/reference/director_preview.md §hero-clock).
    assert abs(dp.probe_duration_s(mp4) - expected) <= 1.0 / dp.FPS


def test_guard_margin_is_actually_discarded(env) -> None:
    """If the trim silently used the raw file, the duration would be the edit
    duration PLUS 2x the guard. Assert the difference is real, so a broken
    trim cannot pass the test above by accident."""
    recipe = dp.build_preview_recipe(_frag())
    expected = (recipe.time_map[-1].edit_end_us) / 1_000_000.0
    raw_if_untrimmed = expected + 2 * dp.GUARD_MS / 1000.0
    res = dp.request_preview(_frag(), _draft())
    dp.drain_for_tests()
    got = dp.probe_duration_s(dp.media_path(res["preview_key"]))
    assert abs(got - raw_if_untrimmed) > 0.5


# --------------------------------------------------------- plan / camera

def test_projectile_mode_uses_the_cached_flight(env) -> None:
    plan = dp.build_plan(_frag(), _draft(
        camera={**dd_mod.DEFAULT_CAMERA, "mode": "PROJECTILE"}))
    assert plan.camera_mode == "PROJECTILE"
    assert plan.camera_fallback is None
    assert len(plan.subject_track) == 46
    assert len(plan.keyframes) > 40


def test_unusable_projectile_path_falls_back_honestly(env, monkeypatch) -> None:
    """Frag 5979's real defect: 2 points, 0 ms of flight. A projectile camera
    built on that films nothing, so the plan must say so rather than pretend."""
    monkeypatch.setattr(dp, "_projectile_path", lambda *a, **k: {
        "launch": {"t": IMPACT_MS, "pos": [-355.6, 175.3, 684.1]},
        "impact": {"t": IMPACT_MS, "pos": [-374.0, 178.0, 718.0]},
        "points": [[0, -355.6, 175.3, 684.1], [0, -374.0, 178.0, 718.0]]})
    plan = dp.build_plan(_frag(), _draft(
        camera={**dd_mod.DEFAULT_CAMERA, "mode": "PROJECTILE"}))
    assert plan.camera_mode == "ORBIT"
    assert "flight" in (plan.camera_fallback or "")


def test_capture_cfg_starts_with_the_runtime_baseline(env) -> None:
    """§4. The reset must precede the profile, the camera and the video
    command, or it resets nothing that matters."""
    plan = dp.build_plan(_frag(), _draft())
    cfg = dp.build_capture_cfg(plan, ["freecam", "loadcamera x", "playcamera"],
                               "clip", "SUBTLE")
    lines = cfg.splitlines()
    baseline = dp.pantheon_runtime.baseline_lines(
        {"cg_fxfile": dp.pantheon_fx.SCRIPT_NAME, "mme_saveDepth": "0"})
    assert lines[:len(baseline)] == baseline
    body = "\n".join(lines[len(baseline):])
    assert "exec wolfcam_tr4sh_master_capture.cfg" in body
    assert 'seta cg_drawCameraPath 0' in cfg
    assert cfg.index("seta cg_drawCameraPath") < cfg.index("video avi name")
    assert cfg.isascii(), "capture cfgs are written encoding='ascii'"


def test_capture_cfg_records_the_guard_margin(env) -> None:
    plan = dp.build_plan(_frag(), _draft())
    cfg = dp.build_capture_cfg(plan, [], "clip", "OFF")
    assert f"at {plan.window_start_ms - dp.GUARD_MS} video avi name clip" in cfg
    assert f"at {plan.window_end_ms + dp.GUARD_MS} stopvideo" in cfg


def test_capture_cfg_rejects_injection(env) -> None:
    plan = dp.build_plan(_frag(), _draft())
    with pytest.raises(dp.wolfcam_capture.CfgInjectionError):
        dp.build_capture_cfg(plan, [], "clip; quit", "OFF")


# ------------------------------------------- engine contracts, regressed

@pytest.mark.parametrize("mode", ["PROJECTILE", "CHASE", "ORBIT", "FREECAM"])
def test_camera_path_covers_the_capture_including_the_guard(env, mode) -> None:
    """MEASURED ENGINE CONTRACT (docs/reference/director_preview.md §hero-clock).

    ``playcamera`` seeks the demo to the camera path's FIRST point, so any
    ``video`` command scheduled before that instant fires late and the head of
    the shot is silently lost — rc=0, empty log, plausible movie, hero event in
    the wrong place. A path that stops early loses the tail the same way.

    Measured twice on the canary frag before this was understood: an 8.50 s
    TimeMap produced a 5.13 s file (path started 3.375 s late), then a correct
    -length file with the frag 500 ms early (path started at the edit window
    instead of the guard boundary). Both are regressed here.
    """
    plan = dp.build_plan(_frag(), _draft(
        camera={**dd_mod.DEFAULT_CAMERA, "mode": mode}))
    if mode == "FPV" or not plan.keyframes:
        pytest.skip("no native camera path for this mode")
    total_ms = plan.edit_duration_us // 1000
    times = [k["t_ms"] for k in plan.keyframes]
    assert min(times) <= -dp.GUARD_MS
    assert max(times) >= total_ms + dp.GUARD_MS


def test_cover_window_is_a_no_op_when_already_covered(env) -> None:
    kfs = ({"t_ms": -dp.GUARD_MS, "pos": (0, 0, 0), "angles": (0, 0, 0),
            "fov": 90.0},
           {"t_ms": 1000 + dp.GUARD_MS, "pos": (1, 1, 1), "angles": (0, 0, 0),
            "fov": 90.0})
    assert dp._cover_window(kfs, 1000) == kfs


def test_overlay_cvars_are_baseline_and_not_overridable() -> None:
    """§4. cg_drawCameraPath / cg_drawCameraPointInfo default to 1, are
    CVAR_ARCHIVE, and render wolfcam's camera-authoring overlay into the movie.
    They must be in the baseline at 0 and must NOT be overridable, or the leak
    the baseline exists to prevent becomes reachable through its own API."""
    from creative_suite.engine import pantheon_runtime as pr
    for name in ("cg_drawCameraPath", "cg_drawCameraPathAngles",
                 "cg_drawCameraPointInfo"):
        assert pr.RUNTIME_BASELINE[name] == "0"
        assert name not in pr.OVERRIDABLE
        with pytest.raises(pr.UnknownCvarError):
            pr.baseline_lines({name: "1"})
    lines = pr.baseline_lines()
    assert 'seta cg_drawCameraPath 0' in lines
    assert 'seta cg_drawCameraPointInfo 0' in lines


def test_every_capture_cfg_resets_the_overlay_before_the_camera(env) -> None:
    """The runtime regression: whatever else a preview cfg contains, the
    overlay reset must be emitted before loadcamera/playcamera/video."""
    for mode in ("PROJECTILE", "ORBIT"):
        plan = dp.build_plan(_frag(), _draft(
            camera={**dd_mod.DEFAULT_CAMERA, "mode": mode}))
        cfg = dp.build_capture_cfg(
            plan, ["freecam", "loadcamera c", "playcamera"], "c", "HERO")
        for cvar in ("cg_drawCameraPath", "cg_drawCameraPointInfo"):
            assert f"seta {cvar} 0" in cfg
            assert cfg.index(f"seta {cvar} 0") < cfg.index("loadcamera")
            assert cfg.index(f"seta {cvar} 0") < cfg.index("video avi name")
